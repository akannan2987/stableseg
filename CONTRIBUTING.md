# Contributing to StableSeg

Unfamiliar terms are defined in [`docs/00-glossary.md`](docs/00-glossary.md).

This file describes how work moves through the repository: the branch model,
the everyday loop, the release flow, and the norms for reviewing each other's
work. It is written so that a first-time contributor can follow it without
asking. The full step-by-step version with expected terminal output is in
[`docs/03-git-workflow.md`](docs/03-git-workflow.md).

## Branch model

Three long-lived branches, all on the same remote (`origin`):

| Branch | Role | Who pushes to it |
|---|---|---|
| `master` | The released code. Always installable, always green in CI. Tags (`v0.1.0`, ...) live here. | Nobody directly; it is updated by the push in the phase block below. |
| `beta` | A pre-release mirror of what is about to become `master`. Useful for trying a build on a second machine. | Same push. |
| `develop` | Where all work happens. Every commit lands here first. | You, locally. |

The default branch on GitHub is **`master`**. `beta` and `develop` are both
created from `master`.

Why three branches for a small project? Because the habit costs nothing and
scales: today one person, one machine; later a second contributor can work on
`develop` while `master` stays stable, and `beta` gives a place to test a
release before tagging it.

## The everyday loop

1. Make sure you are on `develop`: `git switch develop`.
2. Edit, run the tests, run the linter (see below).
3. Commit with a message that says what changed and why.
4. Push `develop` and fan it out to `beta` and `master` (the block below).

Every documented phase ends with exactly this block:

```bash
git switch develop
git add -A
git commit -m "<phase-specific message>"
git push origin develop develop:beta develop:master
# add --tags only when a release tag was created in this phase
git switch master
git pull --ff-only origin master
git switch develop
```

`develop:beta` means "push my local `develop` to the remote branch `beta`".
`--ff-only` means "only move `master` forward if it can do so without merging";
if it refuses, something diverged and you should stop and read
`docs/03-git-workflow.md`, section "If the pull refuses".

## Before every commit

```bash
ruff format src tests     # formats code consistently
ruff check .              # catches unused imports, bugs, sorting
pytest -q                 # all tests must pass
```

CI runs the same three commands on Windows, macOS and Ubuntu. A commit that
fails locally will fail there too, so run them first.

## Before every push

```bash
python scripts/preflight.py
```

Pushing is easy to undo in principle and hard to undo in practice: once a
commit reaches a public host it has been copied and possibly indexed, and
rewriting history does not recall those copies. A leaked credential must be
treated as compromised even if the commit is deleted a minute later. So the
cheap moment to catch a mistake is before the push.

Preflight checks that you are on `develop`; that nothing `.gitignore` is meant
to exclude has been force-added; that no oversized file is about to enter the
history permanently; that no credential pattern appears in the content; that
no absolute home path leaks your username; and that line endings are
consistent. It changes nothing and exits non-zero if anything blocks.

Two escape hatches exist, because a check with no way to say "this is
deliberate" gets switched off the first time it is wrong:

- `# preflight: allow` on a line exempts that line
- `preflight: allow-file` anywhere in a file exempts the whole file

Both are visible in the diff. Use them with a comment saying why;
`tests/test_preflight.py` is the one file that currently needs one, since it
contains fake credentials as test inputs.

Optionally, keep a local `.preflight-words` file (one term per line, already
git-ignored) and preflight will also fail on any of those terms appearing in
the repository. The list stays out of git on purpose: a committed file naming
the terms you want to avoid would itself contain them.

### Making it automatic

Git can run this for you on every push. Hooks are not committed, so each clone
opts in:

```bash
printf '#!/bin/sh\nexec python scripts/preflight.py\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

On Windows, create `.git/hooks/pre-push` with the same two lines; Git for
Windows ships the shell needed to run it. Bypass in an emergency with
`git push --no-verify`, and then go back and fix whatever it found.

## Commit messages

One line, imperative mood, specific: `add DICOM series reader with synthetic
fixture`, not `updates`. If a longer explanation helps, add a blank line and
then prose. Reference the phase when it applies: `phase 3: perturbation bank`.

## Release flow

1. On `develop`, update `CHANGELOG.md`: move items from `[Unreleased]` into a
   new dated version section.
2. Bump `version` in `pyproject.toml` and `__version__` in
   `src/stableseg/__init__.py` (they must match; a test checks this).
3. Commit: `release 0.2.0`.
4. Tag: `git tag -a v0.2.0 -m "StableSeg 0.2.0"`.
5. Push with tags: the standard block, with `--tags` added to the push line.
6. On GitHub, create a Release from the tag and paste the changelog section.

Versioning is semantic: `0.x` while the interface may still change; `1.0.0`
when the config format and API are stable enough that changing them would
break someone else's script.

## Coding rules that keep the project reusable

- **Layering.** `cli.py` may import `api.py`; `api.py` may import core modules;
  core modules never import `api` or `cli`. Nothing in `src/` prints to the
  terminal except `cli.py`.
- **Paths.** Always `pathlib.Path`, never string concatenation, never a
  hard-coded `/` or `\`.
- **Randomness.** Every random process takes an explicit seed. No global seeds.
- **Config first.** A new setting goes into `config.py` with a description and
  a validator, then into the code. Never a magic number in a function body.
- **Storage.** Write outputs through `Storage`, never with a bare `open()` in
  core modules.
- **Tests before features.** A module without a test is not finished.
- **Docs are a deliverable.** A phase is not finished until its tutorial in
  `docs/04-phase-tutorials/` exists and every new term is in the glossary.

## Review norms

Review the work, not the person. Concretely:

- Say what you see and why it matters: "this loop re-reads the file for every
  case, which will be slow on 260 volumes" rather than "this is inefficient".
- Ask before assuming intent. A question is cheaper than a wrong correction.
- Praise specifically when something is done well; it teaches as much as a
  correction does.
- Anyone may point out a mistake in anyone's work, including the maintainer's.
  Being wrong in public here is normal and expected; the tests exist so that
  being wrong is cheap.
- Disagreements are settled with a measurement where possible (a benchmark, a
  test, a plot), and with a written decision in the relevant doc where not.

## Reporting a problem

Open a GitHub issue with: your operating system, the output of
`stableseg version`, the exact command you ran, and the full error text.
`docs/01-setup-<os>.md` has a troubleshooting section for the common cases.
