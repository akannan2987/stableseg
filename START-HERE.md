# START HERE

[README](README.md) · [**Glossary — every term, plain language**](docs/00-glossary.md)

*Hit a word you don't know at any point below? It is in the glossary. If it
isn't, that is a bug in these documents, not a gap in you — say so and it gets
fixed.*

You have a folder of files and no idea where to begin. This page is the
answer. Do these five things in order. Nothing else on this repository
matters until they are done.

**Total time from a blank machine: about 45 minutes**, most of it waiting for
downloads.

---

## Step 1 — Install the tools (25 minutes)

Open the guide for your machine and follow it top to bottom. Do not skip
ahead; each one ends with a verification you must see pass.

| Your machine | Guide |
|---|---|
| Windows 10 or 11 | [`docs/01-setup-windows.md`](docs/01-setup-windows.md) |
| Mac (Intel or Apple Silicon) | [`docs/01-setup-macos.md`](docs/01-setup-macos.md) |
| Red Hat Enterprise Linux 8 (or Rocky/Alma 8) | [`docs/01-setup-rhel8.md`](docs/01-setup-rhel8.md) |

You install three things: **Python** (the language), **Git** (the save-game
system for code) and **VS Code** (the editor). That is all.

This project runs on **Python 3.12 or 3.13**, and nothing else. Your guide
says which one to take and why — on macOS and Windows it is 3.13, on RHEL 8 it
is 3.12. If you already have one of them, you do not need to install anything
new.

**Do not continue until** the guide's final check prints a Python version and
a Git version.

---

## Step 2 — Put the project on your machine (5 minutes)

The project files are in the folder you downloaded. Move that folder somewhere
sensible and open a terminal inside it.

**Windows (PowerShell):**
```powershell
mkdir $HOME\projects -Force
# Move the unzipped 'stableseg' folder into $HOME\projects, then:
cd $HOME\projects\stableseg
dir
```

**macOS / Linux (Terminal):**
```bash
mkdir -p ~/projects
# Move the unzipped 'stableseg' folder into ~/projects, then:
cd ~/projects/stableseg
ls
```

Expected: you see `README.md`, `pyproject.toml`, `src`, `tests`, `docs`,
`configs`. If you do not, you are in the wrong folder.

---

## Step 3 — Build the project's private toolbox and install it (10 minutes)

Copy these commands one at a time. Every one is explained in
[`docs/04-phase-tutorials/phase-01-skeleton.md`](docs/04-phase-tutorials/phase-01-skeleton.md);
right now, just run them.

**Windows (PowerShell):**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version                 # must print 3.12.x or 3.13.x
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
```

**macOS / Linux (Terminal):**
```bash
python3.13 -m venv .venv         # RHEL 8: use python3.12
source .venv/bin/activate
python --version                 # must print 3.12.x or 3.13.x
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
```

After the second command your prompt gains a `(.venv)` prefix. That prefix
means the private toolbox is active. **If it is missing, nothing else will
work** — run the activate command again.

The third command is the one people skip. If it prints anything outside
3.12–3.13, stop and fix it now: `deactivate`, delete `.venv`, and create it
again naming the interpreter explicitly. Installing on the wrong version fails
several minutes later with a confusing error.

The `install -r requirements.lock` command downloads about 200 MB and takes
2–5 minutes. Expected
final line: `Successfully installed ...` followed by a long list.

---

## Step 4 — Prove it works (2 minutes)

Two of these commands need a word of introduction, because they produce files
you have not been told about yet.

**`stableseg phantom` generates test data.** A **phantom** is a stand-in for a
patient, used to check a measuring instrument — hospitals scan a plastic object
of known size to verify a scanner, because you cannot verify a scanner against
a person whose true anatomy nobody knows. This command makes the software
version: eight small 3-D images containing shapes whose exact volume the code
knows, because the code drew them. They let the tests run anywhere with no
download, and they give the pipeline a known right answer to be checked
against. **They are synthetic and are not scans of any person.** Real MRI
arrives in phase 2.

It writes `data/phantom/images/phantom_000.nii.gz` (the picture of case 0),
`data/phantom/labels/phantom_000.nii.gz` (its matching outline),
`manifest.csv` (the true volumes) and `runs/phantom-smoke/run.json` (the record
of what produced them). `.nii.gz` is the standard compressed format for a 3-D
scan. **`stableseg describe`** then reads one of those files back and prints
its size and geometry.

Fuller explanation in your setup guide, at the same step; every term in the
[glossary](docs/00-glossary.md); the generator taken apart in
[phase 1, section 5](docs/04-phase-tutorials/phase-01-skeleton.md).

```bash
pytest -q
stableseg version
stableseg phantom
stableseg describe data/phantom/images/phantom_000.nii.gz
```

Expected, in order:

```
36 passed in 0.6s

{ "stableseg": "0.1.0" }

{
  "data_root": ".../data/phantom",
  "n_cases": 8,
  "mean_true_volume_mm3": 2269.75,
  ...
}

{ "shape": [48, 64, 48], "spacing_mm": [1.0, 1.0, 1.0], ... }
```

`2269.75` must be exactly that number on every machine in the world. If it is,
the project is installed correctly and reproducibly.

**If any of these fail:** the "What could go wrong" table at the end of your
setup guide covers every common cause.

---

## Step 5 — Now learn what you just ran (2 hours, at your own pace)

In this order:

1. [`docs/02-architecture.md`](docs/02-architecture.md) — what the project is
   and what every part does. No commands, just understanding. Read this
   before the code makes any sense.
2. [`docs/04-phase-tutorials/phase-01-skeleton.md`](docs/04-phase-tutorials/phase-01-skeleton.md)
   — the guided tour of every file you just installed, with the reasoning
   behind each one. Three sessions of about 40 minutes.
3. [`docs/03-git-workflow.md`](docs/03-git-workflow.md) — creating the
   repository online and saving your work. Do this when you are ready to
   publish.

[`docs/00-glossary.md`](docs/00-glossary.md) is open beside you the whole
time. Every unfamiliar word is in it.

---

## What you will NOT find yet

This is version 0.1.0. It generates synthetic test data and proves the
machinery works. It does not yet download real MRI, perturb it, segment it or
compute repeatability statistics — those are phases 2 to 8, listed in the
Roadmap section of the README. The skeleton exists first because
every one of those phases plugs into it.

---

## If you are stuck

Every guide has a troubleshooting table. Beyond that, note down: your
operating system, the exact command you ran, and the complete error text.
Those three things are what anyone needs to help you, including yourself in
three weeks.
