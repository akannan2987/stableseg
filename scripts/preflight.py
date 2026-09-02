#!/usr/bin/env python3
"""Preflight: safety checks to run before pushing anything to a public repository.

Why this exists. Pushing is easy to undo in principle and very hard to undo in
practice: once a commit reaches a public host it has been copied, cached and
possibly indexed, and rewriting history does not recall those copies. A leaked
key must be treated as compromised even if the commit is deleted a minute
later. So the cheap moment to catch a mistake is before the push, not after.

What it checks, in order:

  1. Branch      - you are on the working branch, not on a release branch.
  2. Ignored     - nothing that .gitignore is meant to exclude is actually
                   tracked (data, run outputs, virtual environments, caches).
  3. Size        - no large file is about to enter the history, where it stays
                   for ever even if deleted later.
  4. Secrets     - no key, token, password or credential pattern in the content
                   about to be committed.
  5. Private paths - no absolute home directory paths, which leak your username
                   and machine layout into a public repository.
  6. Line endings - no stray CRLF that would make cross-platform diffs noisy.
  7. Vocabulary  - optional, only if a local, untracked word list exists.

It reads only what git reports and the files in the working tree. It changes
nothing. Exit code 0 means clear to push; 1 means at least one blocking
problem; warnings alone do not block.

Usage:
    python scripts/preflight.py
    python scripts/preflight.py --staged     # check only what is staged
    python scripts/preflight.py --max-kb 500 # tighten the size limit
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Branches that should never be committed to directly in this project.
PROTECTED_BRANCHES = {"master", "beta"}

# Directories that must never be tracked. Matched as path prefixes.
FORBIDDEN_DIRS = (
    "data/",
    "runs/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
)
# Exact filenames that must never be tracked. Matched on the file name only,
# so that `.env.example` (a committed template with no real values) is fine
# while `.env` (the real thing) is not. Prefix matching would confuse the two,
# which is exactly the kind of near-miss a safety check has to get right.
FORBIDDEN_FILES = (
    ".DS_Store",
    "Thumbs.db",
    ".env",
    ".coverage",
)
# Placeholder files that exist only to keep an empty directory in git.
FORBIDDEN_ALLOW_NAMES = (".gitkeep",)

# File extensions worth scanning for text problems. Binary files are skipped.
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".json",
    ".csv",
    ".sh",
    ".ps1",
    ".r",
    ".R",
    ".qmd",
    ".lock",
    "",
}

# Credential patterns, split into two tiers because they deserve different
# treatment.
#
# HIGH_CONFIDENCE patterns match a specific issuer's format. A string shaped
# like an AWS key id is almost certainly one, so these are ALWAYS reported -
# even on a line that looks like an example. That matters: documentation
# routinely contains keys labelled "EXAMPLE", and a scanner that silently
# skips anything containing the word "example" can be walked straight past by
# naming your variable well. If a real example must stay, mark the line.
HIGH_CONFIDENCE: list[tuple[str, re.Pattern[str]]] = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
]

# HEURISTIC patterns match a shape ("something called a password is being
# assigned a long string"), which is far more likely to be a false alarm. For
# these, and only these, an obvious placeholder value is accepted.
HEURISTIC: list[tuple[str, re.Pattern[str]]] = [
    ("generic bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{24,}")),
    (
        "assigned secret",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|password|passwd|token|access[_-]?key|private[_-]?key)\b"
            r"\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
        ),
    ),
]

# What counts as an obviously fake value. Note `your...` matches the whole
# token (`your_key_here_replace_me`), not just a prefix ending in a word
# boundary - an earlier version required a boundary after "here" and therefore
# flagged that very string as a real secret.
PLACEHOLDER = re.compile(
    r"(?i)(example|placeholder|dummy|sample|redacted|xxx+|<[a-z_]+>"
    r"|\byour[\w-]*|change[_-]?me|replace[_-]?me|fake[\w-]*|not[_-]?a[_-]?real)"
)

# Absolute home paths leak a username and the machine's layout.
PRIVATE_PATH_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("macOS home path", re.compile(r"/Users/(?!yourname\b|you\b)[A-Za-z0-9._-]+/")),
    ("Linux home path", re.compile(r"/home/(?!yourname\b|you\b|runner\b)[A-Za-z0-9._-]+/")),
    ("Windows home path", re.compile(r"[Cc]:\\\\?Users\\\\?(?!yourname\b|you\b)[A-Za-z0-9._-]+")),
]

# Files allowed to contain example home paths, because they teach with them.
PRIVATE_PATH_EXEMPT_SUFFIX = (".md",)


# Escape hatches. A safety check with no way to say "this one is deliberate"
# gets switched off entirely the first time it is wrong, so the hatch is part
# of the design - but it must be explicit, visible in the diff, and narrow:
#   - put `preflight: allow` on a single line to exempt that line
#   - put `preflight: allow-file` anywhere in a file to exempt the whole file
# Anything using these should say in a comment why.
ALLOW_LINE = "preflight: allow"
ALLOW_FILE = "preflight: allow-file"


class Report:
    """Collects findings so every check runs, rather than stopping at the first."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def git(*args: str) -> str:
    """Run a git command in the repository and return its output."""
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def scan_text_for_secrets(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, label, offending line) for every credential match.

    Pulled out as a plain function so it can be unit-tested without a
    repository, which is what tests/test_preflight.py does.
    """
    if ALLOW_FILE in text:
        return []
    findings: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if ALLOW_LINE in line:
            continue

        # Issuer-specific formats are reported regardless of how the line reads.
        matched = False
        for label, pattern in HIGH_CONFIDENCE:
            if pattern.search(line):
                findings.append((lineno, label, line.strip()[:120]))
                matched = True
                break
        if matched:
            continue

        # Shape-based guesses defer to an obvious placeholder value.
        if PLACEHOLDER.search(line):
            continue
        for label, pattern in HEURISTIC:
            if pattern.search(line):
                findings.append((lineno, label, line.strip()[:120]))
                break
    return findings


def scan_text_for_private_paths(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, label, offending line) for absolute home paths."""
    if ALLOW_FILE in text:
        return []
    findings: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if ALLOW_LINE in line:
            continue
        for label, pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(line):
                findings.append((lineno, label, line.strip()[:120]))
                break
    return findings


def check_branch(rep: Report) -> None:
    # Continuous integration checks out a detached HEAD or an arbitrary ref, so
    # the branch rule is a local-workflow rule only. Everything else in this
    # script still runs there, which is the part that protects the repository.
    if os.environ.get("CI"):
        rep.note("branch check skipped (running in continuous integration)")
        return
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch in PROTECTED_BRANCHES:
        rep.error(
            f"you are on '{branch}'. All work happens on 'develop'; "
            f"'{branch}' is updated by the push, never committed to directly. "
            f"Run: git switch develop"
        )
    elif branch != "develop":
        rep.warn(f"on branch '{branch}', not 'develop'. Intended?")
    else:
        rep.note(f"branch: {branch}")


def files_to_check(staged_only: bool) -> list[str]:
    """Tracked files plus untracked-but-not-ignored files (i.e. what a push would carry)."""
    if staged_only:
        out = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    else:
        tracked = git("ls-files")
        untracked = git("ls-files", "--others", "--exclude-standard")
        out = tracked + untracked
    return sorted({line for line in out.splitlines() if line.strip()})


def is_forbidden_path(path: str) -> bool:
    """Should this path never enter the repository?

    Directories match as prefixes anywhere in the path; files match on the
    final name only. Kept as a plain function so it can be unit-tested against
    the tricky cases (`.env` versus `.env.example`, `data/x` versus
    `metadata/x`) without needing a repository.
    """
    name = path.rsplit("/", 1)[-1]
    if name in FORBIDDEN_ALLOW_NAMES:
        return False
    if name in FORBIDDEN_FILES:
        return True
    parts = path.split("/")
    return any(f"{part}/" in FORBIDDEN_DIRS for part in parts)


def check_forbidden_tracked(rep: Report, paths: list[str]) -> None:
    offenders = [p for p in paths if is_forbidden_path(p)]
    if offenders:
        rep.error(
            "these paths should be excluded by .gitignore but would be pushed:\n      "
            + "\n      ".join(offenders[:20])
            + "\n    Fix: git rm --cached <path>  (keeps your local copy), then re-check."
        )
    else:
        rep.note("no ignored-by-design paths are tracked")


def check_sizes(rep: Report, paths: list[str], max_kb: int) -> None:
    big: list[tuple[str, float]] = []
    for p in paths:
        f = REPO_ROOT / p
        if f.is_file():
            kb = f.stat().st_size / 1024
            if kb > max_kb:
                big.append((p, kb))
    for p, kb in sorted(big, key=lambda t: -t[1]):
        rep.error(
            f"{p} is {kb:.0f} KB (limit {max_kb} KB). Large files stay in git history "
            f"for ever, even if deleted later. Regenerate it from code instead, or add it to .gitignore."
        )
    if not big:
        rep.note(f"no file over {max_kb} KB")


def check_content(rep: Report, paths: list[str]) -> None:
    secrets_found = False
    paths_found = False
    crlf_found = []
    for p in paths:
        f = REPO_ROOT / p
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw[:4096]:  # binary
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            rep.warn(f"{p} is not valid UTF-8; skipped")
            continue

        for lineno, label, line in scan_text_for_secrets(text):
            secrets_found = True
            rep.error(f"possible {label} in {p}:{lineno}\n      {line}")

        if not p.endswith(PRIVATE_PATH_EXEMPT_SUFFIX):
            for lineno, label, line in scan_text_for_private_paths(text):
                paths_found = True
                rep.error(f"{label} in {p}:{lineno}\n      {line}")

        if b"\r\n" in raw:
            crlf_found.append(p)

    if not secrets_found:
        rep.note("no credential patterns found")
    if not paths_found:
        rep.note("no absolute home paths in code or config")
    if crlf_found:
        rep.warn(
            "Windows line endings (CRLF) in: "
            + ", ".join(crlf_found[:10])
            + " - harmless, but makes diffs noisy across systems."
        )


def check_vocabulary(rep: Report, paths: list[str]) -> None:
    """Optional check against a local, untracked word list.

    The list itself is deliberately NOT part of the repository: a file naming
    the terms you want to avoid would contain those very terms. Create
    `.preflight-words` (already git-ignored), one term per line, and this check
    switches itself on. Lines starting with # are comments.
    """
    wordfile = REPO_ROOT / ".preflight-words"
    if not wordfile.exists():
        rep.note("vocabulary check skipped (no local .preflight-words file)")
        return
    terms = [
        w.strip().lower()
        for w in wordfile.read_text(encoding="utf-8").splitlines()
        if w.strip() and not w.startswith("#")
    ]
    if not terms:
        return
    hits: list[str] = []
    for p in paths:
        f = REPO_ROOT / p
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = f.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", text):
                hits.append(f"{p}: '{term}'")
    if hits:
        rep.error("vocabulary check failed:\n      " + "\n      ".join(hits[:20]))
    else:
        rep.note(f"vocabulary check passed ({len(terms)} terms)")


def check_uncommitted(rep: Report) -> None:
    """A reminder, not a failure: unstaged work will not travel with the push."""
    status = git("status", "--porcelain")
    if status.strip():
        n = len(status.strip().splitlines())
        rep.note(f"{n} file(s) changed or untracked - remember 'git add -A' before committing")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safety checks before pushing.")
    parser.add_argument("--staged", action="store_true", help="check only staged files")
    parser.add_argument("--max-kb", type=int, default=1024, help="largest allowed file, in KB")
    args = parser.parse_args()

    rep = Report()
    try:
        paths = files_to_check(args.staged)
    except RuntimeError as exc:
        print(f"preflight could not run: {exc}")
        return 1

    check_branch(rep)
    check_forbidden_tracked(rep, paths)
    check_sizes(rep, paths, args.max_kb)
    check_content(rep, paths)
    check_vocabulary(rep, paths)
    check_uncommitted(rep)

    print(f"\nPreflight: examined {len(paths)} file(s)\n")
    for n in rep.notes:
        print(f"  ok    {n}")
    for w in rep.warnings:
        print(f"  warn  {w}")
    for e in rep.errors:
        print(f"  FAIL  {e}")

    print()
    if rep.errors:
        print(f"{len(rep.errors)} blocking problem(s). Nothing was changed. Fix them and re-run.")
        return 1
    print("Clear to commit and push.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Happens when the output is piped into something that stops reading
        # early, such as `preflight.py | head`. Not an error in the check.
        sys.stderr.close()
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
