# Phase 1c · The First Release: tagging v0.1.0

[← Build guide](../../BUILD_GUIDE.md) · [README](../../README.md) · [Glossary](../00-glossary.md) · [Git workflow](../03-git-workflow.md)

**Prerequisites:** phases 1 and 1b complete and pushed; everything green
(`pytest -q`, `python scripts/preflight.py`).
**Learning goal:** after this page you know what a tag is and how it differs
from a branch, what semantic version numbers promise, what a GitHub Release
adds on top of a tag, and how to verify a release actually works — the part
almost everyone skips.
**Time:** about ten minutes.
**Checkpoint:** `git tag` lists `v0.1.0`; the tag is visible on GitHub with a
Release page; and the project installs directly from the tag on a machine that
has never seen your folder.

---

## 1. What a release is, and why bother for a project this young

Right now the project only exists as "whatever the latest commit is". That is
fine for you, and useless for anyone else. If someone reads about StableSeg
today and comes back in three months, "the latest commit" will be a different
project — more phases, changed interfaces, possibly mid-refactor.

A **release** is a named, frozen point: *this exact state, forever*. Someone
can install it, cite it, reproduce results against it, or diff their copy
against it, regardless of what happens to the project afterwards.

The everyday version: the project is a document you keep editing. A release is
printing a copy, writing "edition 1" on the cover, and putting it on the
shelf. The editing continues; the shelf copy does not move.

Why now, specifically: version 0.1.0 is "the skeleton, complete and
documented, before real data arrives". That is a clean, describable boundary.
Phase 2 changes the shape of the project; after it, this state would only be
reconstructable by digging through history.

## 2. Tags versus branches, in one table

Both are pointers to a commit. The difference is what they do afterwards.

| | Branch | Tag |
|---|---|---|
| Points at | a commit | a commit |
| When new commits arrive | **moves forward** with them | **never moves** |
| Everyday version | a bookmark in a book you are still writing | a page number printed in the index |
| In this project | `master`, `beta`, `develop` | `v0.1.0`, `v0.2.0`, ... |

We use **annotated tags** (`git tag -a`), which carry a message, an author and
a date — a proper label, not just a sticky note. The alternative
("lightweight" tags) stores only the pointer; for releases, always annotated.

## 3. What the version number promises

The scheme is **semantic versioning**: `MAJOR.MINOR.PATCH`.

| Number | Changes when | Example |
|---|---|---|
| PATCH (0.1.**0** → 0.1.**1**) | something was fixed; nothing new, nothing breaks | a typo in an error message |
| MINOR (0.**1**.0 → 0.**2**.0) | capability added; existing things still work | the perturbation bank arrives |
| MAJOR (**0**.x → **1**.0) | something existing changes incompatibly | the config format is finalised |

The leading `0.` is itself a statement: *interfaces may still change*. `1.0.0`
is the promise that a script written against the tool will keep working. That
promise should not be made until the config format and the function layer have
survived contact with real data — which is why 1.0 sits at the end of the
roadmap, not here.

The everyday version: 0.x is a restaurant in soft opening — the menu may
change next week, and the regulars know it. 1.0 is the printed menu.

## 4. The pre-release checklist

Five checks, in order. Each exists because skipping it has burned someone.

### 4.1 Everything is committed and pushed

```bash
git status
```
Expected: `nothing to commit, working tree clean` and
`Your branch is up to date with 'origin/develop'`. A tag on an unpushed or
dirty state labels something nobody else can see.

### 4.2 The version strings agree

The version lives in two places — `pyproject.toml` and
`src/stableseg/__init__.py` — and they must match. This is enforced by a test
rather than by memory:

```bash
pytest tests/test_version.py -q
```
Expected: `1 passed`. (It runs as part of the full suite too; running it alone
here makes the point that the release checklist is executable.)

### 4.3 The full verification sweep

```bash
ruff check .
pytest -q
python scripts/preflight.py
```
Expected: `All checks passed!`, `38 passed`, `Clear to commit and push.`

And if R is installed:
```bash
Rscript R/verify_setup.R
```
Expected last line: `R toolchain verified.`

### 4.4 The changelog has today's date

Open [`CHANGELOG.md`](../../CHANGELOG.md). The `[0.1.0]` heading must carry
the date the tag is actually created — a release note dated before its release
reads as carelessness. The content should already be complete, because the
changelog has been updated with each change rather than reconstructed now
(that is the entire point of keeping it as you go).

### 4.5 Continuous integration is green

The Actions tab on GitHub: the latest run on `master` shows six green jobs.
Tagging a red build publishes a broken edition.

## 5. Create the tag and push it

```bash
git switch develop
git tag -a v0.1.0 -m "StableSeg 0.1.0: skeleton, documentation set, R toolchain"
```

No output means success. Inspect what you made:

```bash
git tag
git show v0.1.0 --stat | head -15
```
Expected: `v0.1.0` in the list; then the tag message, your name, the date, and
the commit it points at.

The `v` prefix is convention (`v0.1.0`, not `0.1.0`) — tags share a namespace
with branches and files, and the prefix makes them unmistakable.

Now push everything, **with the tags flag** — this is the one phase where the
optional line in the standard block is used:

```bash
git push origin develop develop:beta develop:master --tags

## then switch back to local master and pull in the remote changes

git switch master
git pull --ff-only origin master
git switch develop
```

Expected in the push output, alongside the branch lines:
```
 * [new tag]         v0.1.0 -> v0.1.0
```

Tags are **not** pushed by default — a plain `git push` leaves them on your
machine. `--tags` is what publishes them. Forgetting it is the classic release
mistake, and the symptom is a Release page that cannot find your tag.

## 6. Turn the tag into a GitHub Release

A tag is a Git object; a **Release** is the page GitHub builds around one —
with notes, downloadable archives of the source at that point, and a stable
address. The tag is the fact; the Release is the announcement.

1. On the repository page, click **Releases** (right-hand column), then
   **Draft a new release**.
2. **Choose a tag** → select `v0.1.0`. (If it is missing, the tag was not
   pushed — see the `--tags` note above.)
3. **Release title:** `v0.1.0 — the skeleton`
4. **Description:** paste the `[0.1.0]` section from
   [`CHANGELOG.md`](../../CHANGELOG.md), from `First public release` to the
   end of the section. Do not rewrite it — one source of truth, quoted, means
   the two can never disagree.
5. Leave **Set as a pre-release** unticked. Pre-release means "unstable even
   by this project's standards"; 0.1.0 is exactly as stable as it claims.
6. **Publish release.**

The page now exists at a permanent address:
`https://github.com/akannan2987/stableseg/releases/tag/v0.1.0`.

## 7. Verify the release actually works

The step almost everyone skips. A release is a claim — *anyone can install
this exact state* — and a claim untested is a hope. Prove it, in a throwaway
folder, **without** your project or your virtual environment:

```bash
cd /tmp                                # Windows: cd $env:TEMP
python3.13 -m venv relcheck            # RHEL 8: python3.12 · Windows: py -3.13 -m venv relcheck
source relcheck/bin/activate           # Windows: .\relcheck\Scripts\Activate.ps1
python -m pip -q install "git+https://github.com/akannan2987/stableseg.git@v0.1.1"
stableseg version
stableseg phantom
```

Expected: `{ "stableseg": "0.1.1" }`, then a phantom run ending in
`"mean_true_volume_mm3": 2269.75`, with `data/` and `runs/` created in the
folder you ran from. (The command shows `v0.1.1` rather than `v0.1.0` for a
reason section 7b explains: the first run of this very check caught a release
bug.)

Read what just happened: pip fetched **the tag** — not the latest code, not
your folder — built it, and installed it into a fresh environment, and the
result reproduced the reference number. That is the release doing its one job.

Clean up:
```bash
deactivate
rm -rf relcheck                        # Windows: Remove-Item -Recurse -Force relcheck
cd ~/projects/stableseg                # Windows: cd $HOME\projects\stableseg
source .venv/bin/activate              # Windows: .\.venv\Scripts\Activate.ps1
```

(This install-from-tag route uses the pinned-compatible versions from
`pyproject.toml` ranges rather than `requirements.lock`, which is fine for a
smoke test; the lock file remains the reference for development installs.)

## 7b. What this verification caught, the first time it was run

Worth recording, because it is the whole argument for section 7 in one story.

Running exactly the check above against the freshly published `v0.1.0` failed:

```
Invalid value for '--config' / '-c': Path 'configs/phantom.yaml' does not exist.
```

The command's default configuration was a relative path into the repository.
Every test passed and every documented example worked, because both always ran
inside a project checkout, where that file exists. An installed package
carries code, not the repository's folders — so the very first run on a
machine that was not a checkout failed on the spot.

The response followed section 8's rule rather than fighting it: the published
tag stayed exactly where it was, and **v0.1.1** was released the same day with
the fix, two regression tests that run the command from an empty folder the
way an installed user would, and this note. The changelog entry for 0.1.1
records the details.

Two lessons that outlast the bug. First, a test suite that always runs inside
the checkout silently assumes the checkout; at least one test should stand
where an installed user stands. Second, the install-from-tag step is not
ceremony — it is the only check in the whole suite that stood outside the
project, and it caught what everything inside could not see.

## 8. What could go wrong

| Symptom | Cause | Fix |
|---|---|---|
| The Release page's tag dropdown does not show `v0.1.0` | tag not pushed | `git push origin --tags`, refresh |
| `git tag` shows the tag but `git show v0.1.0` errors | a typo created a second, empty tag | `git tag -d <wrong-name>` deletes a local tag |
| Tagged the wrong commit, **not yet pushed** | — | `git tag -d v0.1.0`, re-tag on the right commit |
| Tagged the wrong commit, **already pushed** | — | do not delete a published tag others may have fetched; release a corrected `v0.1.1` instead, and say why in its notes |
| `pip install git+...@v0.1.0` fails with a Python version error | the throwaway environment used an unsupported interpreter | recreate it naming `python3.13` / `py -3.13` explicitly |
| The install works but `stableseg version` prints something else | version strings diverged after tagging | this is what `tests/test_version.py` prevents when run *before* tagging; fix and release a patch |

## 9. The record

Release procedure in brief, for next time (it is also in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md), "Release flow", and
[`03-git-workflow.md`](../03-git-workflow.md), section 5):

1. Move changelog items from `[Unreleased]` into a dated version section.
2. Bump the version in `pyproject.toml` and `src/stableseg/__init__.py`.
3. Run the checklist in section 4.
4. Commit, tag, push with `--tags`.
5. Draft the GitHub Release from the tag; paste the changelog section.
6. Install from the tag in a clean environment and run the smoke test.

For v0.1.0 the version was already `0.1.0` everywhere, so steps 1–2 reduced to
correcting the changelog date.

## 10. Commit the phase

The documentation changes made for this release (changelog date, build guide
section, this file) travel with the tag:

```bash
git switch develop
git add -A
git commit -m "phase 1c: release v0.1.0 - changelog date, release tutorial, build guide section"
git tag -a v0.1.0 -m "StableSeg 0.1.0: skeleton, documentation set, R toolchain"
git push origin develop develop:beta develop:master --tags

## --tags is required in this phase: it is what publishes the release tag
## then switch back to local master and pull in the remote changes

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: back to the [build guide](../../BUILD_GUIDE.md), section 8 — real data.
