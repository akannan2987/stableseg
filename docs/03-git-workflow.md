# 03 · Git Workflow: `master` / `beta` / `develop`

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md)

**Prerequisites:** Git installed and configured (your OS setup guide, section "Git"). A GitHub account.
**Learning goal:** after this page you can create the repository with its three branches, make a commit, push it so all three branches update, and recover from the two mistakes everyone makes.
**Checkpoint:** `git branch -a` shows `develop`, `beta`, `master` locally and on `origin`; GitHub shows `master` as the default branch; one commit has arrived on all three.

Commands are shown for bash (macOS, Linux) and PowerShell (Windows) only where they differ. Git commands themselves are identical everywhere.

---

## 1. What Git is, in one paragraph

Git is a save-game system for a folder. Every time you *commit*, Git takes a snapshot of every file and gives it an ID. You can go back to any snapshot, compare two snapshots, and keep several parallel lines of snapshots called *branches*. GitHub is a website that stores a copy of your snapshots so other people (and other machines) can get them; that copy is called the *remote*, and by convention it is named `origin`.

Three verbs cover 90 % of daily use:

| Verb | Means | Analogy |
|---|---|---|
| `commit` | save a snapshot locally | pressing "save" in a game |
| `push` | send your snapshots to GitHub | uploading the save file to the cloud |
| `pull` | fetch snapshots from GitHub into your copy | downloading the save file |

---

## 2. The branch model

| Branch | Role |
|---|---|
| `master` | The released code. Always installable, always green. Tags such as `v0.1.0` are placed here. **Default branch on GitHub.** |
| `beta` | A pre-release mirror of what is about to become `master`. A place to try a build on a second machine before tagging. |
| `develop` | Where every commit is made. Work happens here and only here. |

`beta` and `develop` are both created from `master`, and after every phase all three point at the same commit. That may look redundant for one person; the value is the habit. A second contributor can work on `develop` while `master` stays stable, and `beta` gives a testing stage that costs nothing today.

---

## 3. Create the repository (once)

### 3.1 On GitHub

1. Open https://github.com/new.
2. Repository name: `stableseg`. Visibility: Public. **Do not** tick "Add a README", "Add .gitignore" or "Choose a license"; the project already has them. Click **Create repository**.
3. In the new repository's **Settings → General → Default branch**, confirm it says `master`. If it says `main`, change it after step 3.2 (GitHub only allows the switch once a `master` branch exists): click the pencil, choose `master`, confirm.

### 3.2 On your machine

You have the project folder from the setup guide (`~/projects/stableseg` on macOS/Linux, `C:\Users\<you>\projects\stableseg` on Windows). In a terminal inside that folder:

```bash
git init -b master
```
Expected: `Initialized empty Git repository in .../stableseg/.git/`

`-b master` names the first branch `master`. Older Git versions (< 2.28) don't accept `-b`; run `git init` then `git branch -M master` instead.

```bash
git add -A
git commit -m "phase 1: skeleton, config, storage, phantoms, CLI, tests, CI, docs"
```
Expected: a list of files with `create mode 100644 ...` and a first line like `[master (root-commit) 3f2a1c9] phase 1: ...`.

If Git complains `Author identity unknown`, set your name and email once (your setup guide shows this) and re-run the commit.

```bash
git remote add origin https://github.com/akannan2987/stableseg.git
git push -u origin master
```
Expected output ends with `branch 'master' set up to track 'origin/master'.`

On first push GitHub asks you to sign in. Use the browser flow if offered; if it asks for a password, it wants a **personal access token**, not your account password (see the setup guide, "GitHub authentication").

### 3.3 Create `beta` and `develop` from `master`

```bash
git switch -c beta
git push -u origin beta
git switch master
git switch -c develop
git push -u origin develop
```
Expected after each `push -u`: `branch '<name>' set up to track 'origin/<name>'.`

`git switch -c X` means "create branch X from where I am and move to it". Both new branches are created *from `master`*, which is why we switch back to `master` between them.

### 3.4 Verify

```bash
git branch -a
```
Expected:
```
  beta
* develop
  master
  remotes/origin/beta
  remotes/origin/develop
  remotes/origin/master
```
The `*` marks the branch you are on. From here on you always sit on `develop`.

---

## 4. The everyday loop

Work on `develop`. Before committing:

```bash
ruff format src tests
ruff check .
pytest -q
```
All three must be clean (`All checks passed!`, `N passed`).

Then, before pushing:

```bash
python scripts/preflight.py
```
Expected last line: `Clear to commit and push.`

This is the safety gate. It looks for credentials, oversized files, anything
`.gitignore` should have excluded, and absolute paths containing your
username - the four ways a public push goes wrong. It reads only; it never
changes a file. If it reports a problem, fix it and run it again. Full
description in [`../CONTRIBUTING.md`](../CONTRIBUTING.md), section "Before
every push", including how to make Git run it automatically.

Why before the push and not after: history rewriting does not recall copies
that have already been fetched, cached or indexed. A key that reaches a public
repository is compromised, full stop, even if the commit is removed a minute
later. Checking first costs two seconds.

Then the fixed block that ends every phase:

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

What each line does:

| Line | Meaning |
|---|---|
| `git switch develop` | make sure you are on the work branch |
| `git add -A` | stage every change (new, edited, deleted files) |
| `git commit -m "..."` | snapshot |
| `git push origin develop develop:beta develop:master` | push `develop`; also push local `develop` *to* remote `beta` and remote `master`. Three remote branches move in one command. |
| `git switch master` / `git pull --ff-only origin master` | bring your local `master` up to what you just pushed. `--ff-only` refuses if it would need a merge; that refusal is a safety check. |
| `git switch develop` | back to work |

Expected output of the push line, three times over:
```
   3f2a1c9..8b4d2e0  develop -> develop
   3f2a1c9..8b4d2e0  develop -> beta
   3f2a1c9..8b4d2e0  develop -> master
```

Expected output of the pull: `Fast-forward` followed by a file summary, or `Already up to date.`

---

## 5. Releases and tags

A tag is a named, permanent pointer to one commit. Releases are tagged `vX.Y.Z`.

```bash
git switch develop
# ... update CHANGELOG.md, bump the version in pyproject.toml and __init__.py ...
git add -A
git commit -m "release 0.1.0"
git tag -a v0.1.0 -m "StableSeg 0.1.0: skeleton and documentation set"
git push origin develop develop:beta develop:master --tags
git switch master
git pull --ff-only origin master
git switch develop
```

Then on GitHub: **Releases → Draft a new release → choose tag `v0.1.0`**, paste the changelog section, publish.

`git tag` with no arguments lists tags. `git show v0.1.0` shows what the tag points at.

---

## 6. If the pull refuses

`git pull --ff-only origin master` prints `fatal: Not possible to fast-forward, aborting.`

This means remote `master` has a commit your local `master` does not, and vice versa. In a one-person project it almost always means you edited something on GitHub's website (a typo fix in the README, for example) and also committed locally. Resolution:

```bash
git switch develop
git fetch origin
git merge origin/master        # brings the website edit into develop
# resolve any conflict Git reports, then:
git add -A
git commit -m "merge remote edits into develop"
git push origin develop develop:beta develop:master
git switch master
git pull --ff-only origin master
git switch develop
```

Rule to avoid it: edit only on your machine, never on the website.

---

## 7. If you committed on the wrong branch

You made a commit while on `master` instead of `develop`.

```bash
git switch develop
git merge master           # develop now has the commit too
git switch master
git reset --hard origin/master   # local master back to what GitHub has
git switch develop
```

Then continue with the normal block. `reset --hard` throws away local changes on the current branch, which is exactly what you want here and dangerous anywhere else; double-check you are on `master` (`git branch` shows the `*`).

---

## 8. Reading your history

```bash
git log --oneline --graph --all -n 15
```
One line per commit, with the branch pointers drawn. When all three branches point at the same commit you will see `(HEAD -> develop, origin/master, origin/develop, origin/beta, master, beta)` on the top line. That is the healthy state at the end of every phase.

---

## 9. What NOT to commit

`.gitignore` already excludes `data/`, `runs/`, `.venv/` and `.env`. Reasons:

- `data/` and `runs/` are regenerated by the code. Committing them would bloat the repository and, worse, let a stale result outlive the code that produced it.
- `.venv/` is your local toolbox, hundreds of megabytes, machine-specific.
- `.env` will hold secrets in later phases. `.env.example` (committed) shows the shape without the values.

Check what a commit will contain before making it: `git status` lists changed files; `git diff --stat` summarises the edits.

---

Next: [`04-phase-tutorials/phase-01-skeleton.md`](04-phase-tutorials/phase-01-skeleton.md).
