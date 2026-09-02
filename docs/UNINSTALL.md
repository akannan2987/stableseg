# Uninstall: removing StableSeg completely and safely

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md)

**Prerequisites:** none.
**Learning goal:** after this page you can remove any part of this project, or
all of it, and you understand what each thing you installed actually was and
where it lives. That second part is the useful half — knowing what a tool put
on your machine is how you stay in control of your own computer.
**Checkpoint:** you can say what a virtual environment removal does and does
not affect, and why deleting `data/` and `runs/` is safe.

**Nothing here is destructive by accident.** Every step says what it removes,
what it leaves, and how to undo it. Work top to bottom and stop whenever you
have removed enough — the sections go from "smallest, safest" to "everything".

---

## 1. First: what did you actually install?

Worth knowing before removing anything. Setting up StableSeg put four kinds of
thing on your machine, and they are independent of each other.

| What | Where it lives | Shared with other work? |
|---|---|---|
| **Generated data and results** | `data/` and `runs/` inside the project | No — this project only |
| **The private toolbox** (virtual environment) | `.venv/` inside the project | No — this project only |
| **The project itself** | your `stableseg` folder | No |
| **General tools** — Python, Git, VS Code | system-wide | **Yes** — other work may depend on them |

The everyday comparison: the first three are the ingredients and the mixing
bowl you bought for one recipe. The fourth is the oven. Throwing out leftovers
is trivial; removing the oven affects every future meal.

**Consequence, and the main thing to take from this page:** removing the first
three is completely safe. Removing the fourth needs thought.

---

## 2. Remove generated data and results

The smallest step, and the one worth doing regularly rather than only at the
end.

```bash
cd ~/projects/stableseg          # Windows: cd $HOME\projects\stableseg
rm -rf data runs
```
Windows PowerShell:
```powershell
Remove-Item -Recurse -Force data, runs
```

**What this removes.** The generated phantom images, any downloaded scans, and
every run's outputs.

**What it does not touch.** Code, documents, settings files, version history.

**Why it is safe.** Everything in those two folders is *derived* — produced by
code from a fixed seed or downloaded from a fixed source. Both folders are
excluded from version control precisely so that nothing irreplaceable can hide
in them.

**To undo:**
```bash
stableseg phantom
```
You get byte-identical data back, including the same `mean_true_volume_mm3` of
`2269.75`. That is not luck; it is what "reproducible" means, and this is the
cheapest way to see it demonstrated.

---

## 3. Remove the private toolbox (the virtual environment)

```bash
cd ~/projects/stableseg
deactivate                       # only if the prompt shows (.venv)
rm -rf .venv
```
Windows PowerShell:
```powershell
deactivate
Remove-Item -Recurse -Force .venv
```

**What a virtual environment is**, restated because this is where it matters: a
folder holding this project's own copies of the libraries it needs, isolated
from your system Python and from every other project. It is disposable by
design.

**What this removes.** Every library installed for this project — several
hundred megabytes — and the `stableseg` command itself.

**What it does not touch.** Your system Python. Any other project's
environment. This project's code.

**When you would do this.** More often than you might think: after an install
goes wrong, when switching Python versions, or to prove the setup instructions
work by following them from scratch.

**To undo** — the same three lines from your setup guide:
```bash
python3.13 -m venv .venv         # RHEL 8: python3.12 · Windows: py -3.13 -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
```

---

## 4. Remove the project folder

```bash
cd ~/projects
rm -rf stableseg
```
Windows PowerShell:
```powershell
cd $HOME\projects
Remove-Item -Recurse -Force stableseg
```

**What this removes.** Everything local: code, documents, settings, the
environment, the data, **and the local version history** in the hidden `.git`
folder.

**What it does not touch.** Anything you pushed to GitHub. Your copy on GitHub
is a complete copy, which is the entire point of pushing.

**Before you do this, one check** — has everything reached GitHub?

```bash
cd ~/projects/stableseg
git status
```

`nothing to commit, working tree clean` plus `Your branch is up to date with
'origin/develop'` means everything is safely on the remote. Anything else means
uncommitted work is about to be lost.

**To undo:**
```bash
cd ~/projects
git clone https://github.com/akannan2987/stableseg.git
cd stableseg
git switch develop
```
Then rebuild the environment as in section 3. This is exactly the round trip
the setup guides describe, and doing it occasionally is the only real proof
that your instructions work.

---

## 5. Remove things on GitHub

Not needed to free up your machine, and irreversible in a way local deletion is
not. Read before acting.

### 5.1 Remove the remote `beta` branch

If you never use it:

```bash
git push origin --delete beta
```

Then remove `develop:beta` from the push line in your habit, or it will be
recreated on the next push.

### 5.2 Turn off the automated checks

Delete `.github/workflows/ci.yml` and push. Existing run history stays visible
under the Actions tab; nothing new runs.

### 5.3 Delete the repository itself

On GitHub: **Settings → General → Danger Zone → Delete this repository**. You
must type the repository name to confirm.

**This is permanent.** Anything that existed only there is gone: the history,
the run history, any issues, and any address people had. If someone cloned it,
their copy survives; you have no way to recall it. Making the repository
private is usually the better move — same effect on visibility, fully
reversible.

---

## 6. Remove the general tools

Only if you have no other use for them. **Python and Git are used by an
enormous amount of other software**, including things you may not realise
depend on them.

### Do not remove these

| Tool | Why not |
|---|---|
| **macOS system Python** (`/usr/bin/python3`) | Apple's own tools use it. Removing it breaks parts of the operating system. |
| **RHEL system Python** (`/usr/bin/python3`) | The package manager `dnf` is written in it. Removing it breaks your ability to install anything, including a replacement. |
| **Git**, if you use any other repository | Everything version-controlled on your machine stops working. |

R and RStudio are safe to remove — nothing on a normal system depends on them
unless you installed them for other work.

### Removing a Python you installed yourself

**macOS** — the python.org installer places each version in its own folder, so
removing one leaves the others intact:

```bash
ls /Library/Frameworks/Python.framework/Versions/
sudo rm -rf /Library/Frameworks/Python.framework/Versions/3.13
sudo rm -rf "/Applications/Python 3.13"
```
Note the version number carefully. Removing the wrong folder removes the wrong
Python.

**Windows** — Settings → Apps → Installed apps → find "Python 3.13.x" →
Uninstall. There are usually two entries (the interpreter and its launcher);
removing the launcher affects every Python on the machine, so leave it unless
you are removing all of them.

**RHEL 8** — this removes only the parallel installation, never the system one:
```bash
sudo dnf remove python3.12 python3.12-pip python3.12-devel
```

### Removing VS Code

macOS: drag it from `/Applications` to the Trash. Its own settings folders sit
under your Library folder and in `~/.vscode`, if you want those gone too. Windows: Settings → Apps → Visual Studio Code → Uninstall. RHEL:
`sudo dnf remove code`.

### Removing R and RStudio

Both are optional extras for this project, and independent of everything else.
Remove RStudio first — it is only an editor, and removing the R underneath it
first would leave it unable to start.

**RStudio.** macOS: drag it from `/Applications` to the Trash. Windows:
Settings → Apps → RStudio → Uninstall. RHEL: `sudo dnf remove rstudio`, or
delete the folder if you installed it by hand.

**R.** macOS: `sudo rm -rf /Library/Frameworks/R.framework` and
`sudo rm -rf /Applications/R.app`, or `brew uninstall r` if you installed it
that way. Windows: Settings → Apps → find "R for Windows 4.x.x" → Uninstall.
RHEL: `sudo dnf remove R`.

**Installed R packages** live in your home directory, separately from R
itself, so they survive an uninstall unless removed. Find them with
`R -e '.libPaths()'` before removing R; afterwards, they are the
`R` folder inside your Library or home directory.

Nothing in the Python side of this project notices any of this. The R script
is committed and will simply not run until R is reinstalled.

### Removing 3D Slicer

Optional and independent of everything else. macOS: drag from `/Applications`.
Windows: Settings → Apps. Linux: delete the folder you extracted.

---

## 7. Removing everything, in order

For completeness, if you want the machine back exactly as it was:

```bash
# 1. Confirm nothing is unpushed
cd ~/projects/stableseg && git status

# 2. Remove the project entirely (environment, data and history included)
cd ~/projects && rm -rf stableseg

# 3. Optional: delete or make private the repository on GitHub

# 4. Optional: remove the Python you installed for it (section 6)

# 5. Optional: remove VS Code, R, RStudio and 3D Slicer if unused elsewhere
```

Windows equivalents are in the sections above.

---

## 8. The tidying that is not uninstalling

Two things that free space without removing anything you need.

**The download cache.** Pip keeps copies of everything it downloads so
reinstalling is fast. It can reach a gigabyte.
```bash
python -m pip cache purge
```
Safe. Reinstalling simply downloads again.

**Working caches.** The tools leave folders behind while they run:
```bash
rm -rf .pytest_cache .ruff_cache .coverage
find . -name "__pycache__" -type d -exec rm -rf {} +
```
Windows PowerShell:
```powershell
Remove-Item -Recurse -Force .pytest_cache, .ruff_cache, .coverage -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```
All regenerated automatically, all excluded from version control.

---

## 9. Committing changes to this document

```bash
git switch develop
git add -A
git commit -m "docs: update uninstall guide"
git push origin develop develop:beta develop:master

## --tags is optional, only when required

git switch master
git pull --ff-only origin master
git switch develop
```

---

That is the whole of it. Nothing this project installs is hidden, nothing hooks
into your system, and every piece can be removed independently — which is worth
expecting from anything you install, and worth documenting for anything you
publish.
