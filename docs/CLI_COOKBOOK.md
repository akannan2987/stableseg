# CLI Cookbook: ready-to-paste commands

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md) · [Phase 1](04-phase-tutorials/phase-01-skeleton.md)

**Prerequisites:** the project installed and the environment active (your setup
guide). Your prompt must show `(.venv)`.
**Learning goal:** after this page you can drive every capability the project
has from the terminal, read its output, and do the same things from Python when
that is more convenient. You will also stop being afraid of the terminal, which
is worth more than any individual command.
**Checkpoint:** you can generate a dataset, inspect one of its files, and
explain what each field of the output means.

**Every recipe here has been run and its output pasted verbatim.** Where a
number appears, that is the number you should see. This file grows one section
per phase; recipes for phases not yet built are marked as such rather than
guessed at.

---

## How to use this page

Copy a block, paste it into your terminal, press Enter. Commands are identical
on Windows, macOS and Linux — the project uses no operating-system-specific
tricks. Where something genuinely differs, both forms are shown.

Two rules that prevent nine tenths of all problems:

1. **Be in the project folder.** `cd` to it first. Check with `pwd` (macOS,
   Linux) or `pwd` in PowerShell — both print where you are.
2. **Have the environment active.** Your prompt must start with `(.venv)`. If
   not: `source .venv/bin/activate` (macOS, Linux) or
   `.\.venv\Scripts\Activate.ps1` (Windows PowerShell).

Every session starts the same way:

```bash
cd ~/projects/stableseg          # Windows: cd $HOME\projects\stableseg
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
```

---

## 1 · Orientation

### 1.1 What commands exist?

```bash
stableseg --help
```

```
 Usage: stableseg [OPTIONS] COMMAND [ARGS]...

 StableSeg: audit how much an imaging biomarker moves when the patient has not changed.

╭─ Commands ───────────────────────────────────────────────────────────╮
│ version          Show the installed version.                         │
│ describe         Summarise a NIfTI volume: shape, voxel size, ...    │
│ phantom          Generate the synthetic phantom dataset ...          │
│ validate-config  Check that a config file is valid without running.  │
╰──────────────────────────────────────────────────────────────────────╯
```

**Why this is the first recipe.** `--help` is not a fallback for when you are
stuck; it is the manual, and it is generated from the code, so it cannot go out
of date. Every command has its own:

```bash
stableseg phantom --help
```

```
 Usage: stableseg phantom [OPTIONS]

 Generate the synthetic phantom dataset described in a config file.

╭─ Options ────────────────────────────────────────────────────────────╮
│ --config  -c   <path>  Run config (YAML). [default: configs/phantom.yaml] │
│ --help                 Show this message and exit.                   │
╰──────────────────────────────────────────────────────────────────────╯
```

Reading that: `--config` is an **option** — named, with a default, so you may
leave it out. `-c` is its short form. A parameter shown without dashes would be
an **argument**: positional and required.

### 1.2 Which version am I running?

```bash
stableseg version
```

```json
{
  "stableseg": "0.1.0"
}
```

**Why every command prints this shape.** The output is **JSON** — a plain-text
format for structured data, readable by people and by programs. That means the
same command can be read by you or piped into another tool, with no second
"machine-readable mode" to maintain. When you report a problem, this is the
first thing to include.

---

## 2 · Settings files

### 2.1 Check a settings file without running anything

```bash
stableseg validate-config configs/phantom.yaml
```

```json
{
  "valid": true,
  "name": "phantom-smoke",
  "config": {
    "name": "phantom-smoke",
    "data": {
      "source": "phantom",
      "root": "data/phantom",
      "phantom": {
        "n_cases": 8,
        "shape": [48, 64, 48],
        "spacing_mm": [1.0, 1.0, 1.0],
        "noise_sd": 0.05,
        "seed": 42
      }
    },
    "output": { "root": "runs", "run_name": "phantom-smoke" }
  }
}
```

**Why bother.** Two reasons. It catches a typo in half a second instead of
after a long run. And notice that the echoed settings contain fields the file
does not — every default filled in. That is the *actual* configuration that
would be used, which is not always what you assumed.

### 2.2 Watch it reject a bad value

Worth doing once, so the error is familiar when it is real. Edit
`configs/phantom.yaml`, set `n_cases: 0`, and run the same command:

```
ValidationError: 1 validation error for AuditConfig
data.phantom.n_cases
  Input should be greater than or equal to 1
  [type=greater_than_equal, input_value=0, input_type=int]
```

It names the exact field and the exact rule. Set it back to `8`.

**The lesson worth taking.** A good error message tells you *what* was wrong,
*where*, and *what was expected*. This one is not hand-written — it comes from
declaring the rule once, in `config.py`. Declaring rules beats writing checks.

### 2.3 Make your own settings file

```bash
cp configs/phantom.yaml configs/my-run.yaml
```
Windows PowerShell:
```powershell
Copy-Item configs\phantom.yaml configs\my-run.yaml
```

Open it in an editor and change what you like — say `n_cases: 20` and
`run_name: my-run` — then:

```bash
stableseg validate-config configs/my-run.yaml
stableseg phantom --config configs/my-run.yaml
```

**Why this is the whole point of settings files.** Your experiment is now a
file you can commit, share, and re-run months later to get the same result.
"What settings did I use?" stops being a memory problem.

---

## 3 · Generating data

### 3.1 Generate the phantom dataset

```bash
stableseg phantom
```

```json
{
  "data_root": ".../stableseg/data/phantom",
  "n_cases": 8,
  "manifest": ".../stableseg/data/phantom/manifest.csv",
  "run_dir": ".../stableseg/runs/phantom-smoke",
  "mean_true_volume_mm3": 2269.75
}
```

**That `2269.75` is a checkpoint, not decoration.** It is identical on every
machine, on Windows, macOS and Linux, on Python 3.12 and 3.13 — because the
generator is seeded. If you see it, your install is not merely working but
reproducing the reference result exactly. If you see something else, something
in the numerical stack differs and is worth investigating before trusting
anything downstream.

A reminder of what a **phantom** is, since it is the term people meet here
first: a stand-in for a patient used to check a measuring instrument. Hospitals
scan a plastic object of known size to verify a scanner. These are the software
version — generated images whose true volume the code knows exactly. They are
synthetic and are not scans of any person. Full entry in the
[glossary](00-glossary.md).

### 3.2 See what it produced

```bash
ls data/phantom
ls data/phantom/images
```
Windows PowerShell: use `dir` instead of `ls`.

```
images  labels  manifest.csv

phantom_000.nii.gz  phantom_001.nii.gz  phantom_002.nii.gz  phantom_003.nii.gz
phantom_004.nii.gz  phantom_005.nii.gz  phantom_006.nii.gz  phantom_007.nii.gz
```

Reading a filename: `phantom` means generated rather than scanned; `000` is the
case number, zero-padded so case 2 sorts before case 10; `.nii` is NIfTI, the
research format holding a whole 3-D volume plus its voxel size and orientation;
`.gz` means compressed, which tools read without unzipping.

`images/phantom_000.nii.gz` is case 0's picture. `labels/phantom_000.nii.gz` is
its matching outline. Same name, two folders — that pairing is the dataset
structure, and phase 2's real data uses the identical layout.

### 3.3 Read the answer key

```bash
cat data/phantom/manifest.csv
```
Windows PowerShell: `Get-Content data\phantom\manifest.csv`

```
case_id,true_volume_label1_mm3,true_volume_label2_mm3,true_volume_total_mm3,synthetic,seed
phantom_000,1446.0,1619.0,3065.0,True,42
phantom_001,764.0,830.0,1594.0,True,42
...
```

**Why a manifest exists.** Real scans have an expert's opinion about where the
structure is. Phantoms have arithmetic. This file is the truth the pipeline
will be checked against — and note the `synthetic` column, which travels with
the data so nobody downstream has to remember.

### 3.4 Regenerate somewhere else, without touching the original

```bash
stableseg phantom --config configs/my-run.yaml
```

With `root: data/my-phantoms` in that file, the original set is untouched. Two
datasets, two settings files, no ambiguity about which produced what.

---

## 4 · Inspecting a volume

### 4.1 Summarise one file

```bash
stableseg describe data/phantom/images/phantom_000.nii.gz
```

```json
{
  "shape": [48, 64, 48],
  "dtype": "float32",
  "spacing_mm": [1.0, 1.0, 1.0],
  "voxel_volume_mm3": 1.0,
  "min": 0.12241370975971222,
  "max": 0.922661304473877,
  "mean": 0.40714359283447266,
  "n_nonzero": 147456,
  "path": "data/phantom/images/phantom_000.nii.gz"
}
```

Every field, in plain terms:

| Field | Meaning |
|---|---|
| `shape` | how many voxels along each axis: 48 × 64 × 48 |
| `dtype` | how each number is stored; `float32` means decimals |
| `spacing_mm` | the physical size of one voxel, in millimetres |
| `voxel_volume_mm3` | those three multiplied — the volume of one voxel |
| `min` / `max` / `mean` | the brightness range and average |
| `n_nonzero` | how many voxels are not exactly zero |
| `path` | the file this describes |

**Why `spacing_mm` is the field to care about.** It is the difference between a
correct measurement and a wrong one. A structure of 1,446 voxels is 1,446 mm³
at 1 mm spacing and 11,568 mm³ at 2 mm spacing — an eightfold error from one
overlooked number. This is why `io.py` keeps the geometry attached to the data
rather than in a separate variable someone can forget.

### 4.2 Describe every image at once

```bash
for f in data/phantom/images/*.nii.gz; do stableseg describe "$f"; done
```
Windows PowerShell:
```powershell
Get-ChildItem data\phantom\images\*.nii.gz | ForEach-Object { stableseg describe $_.FullName }
```

**What a loop is,** since this may be the first one you meet: "for each item in
this list, do this thing with it." The `*` is a wildcard meaning "any
characters", so `*.nii.gz` means every file ending in `.nii.gz`. That single
idea does most of the repetitive work in a terminal.

### 4.3 Look at a scan properly

The terminal gives you numbers. To see the picture, install **3D Slicer** (free,
from the Slicer download site), then **File → Add Data**, choose
`data/phantom/images/phantom_000.nii.gz` and `data/phantom/labels/phantom_000.nii.gz`,
ticking **LabelMap** for the label. Scroll with the mouse wheel.

**Why bother when the numbers look fine.** Because numbers hide things eyes
catch instantly — an outline in the wrong place, an image flipped along one
axis. Looking at the data is a habit, not a beginner's crutch.

---

## 5 · Running the same things from Python

Everything above is available as plain functions. Useful when you want to loop,
compare, or explore.

Start Python inside the active environment:

```bash
python
```

### 5.1 Read a settings file

```python
from stableseg.config import AuditConfig

cfg = AuditConfig.from_yaml("configs/phantom.yaml")
print(cfg.data.phantom.n_cases)        # 8
print(cfg.model_dump(mode="json"))     # the whole validated document
```

### 5.2 Generate data without the terminal

```python
from stableseg import api

result = api.generate_phantoms(cfg)
print(result["mean_true_volume_mm3"])  # 2269.75
```

**Notice what just happened.** That is the exact function `stableseg phantom`
calls. The command-line tool adds argument parsing and JSON printing —
*nothing else*. Every capability is reachable from a script, a notebook, or a
future web page without duplicating a single line. That is what the layering
rule in `__init__.py` buys.

### 5.3 Load a volume and measure a structure

```python
from stableseg.io import load_volume, label_volume_mm3

lbl = load_volume("data/phantom/labels/phantom_000.nii.gz")
print(lbl.spacing_mm)                      # (1.0, 1.0, 1.0)
print(label_volume_mm3(lbl, 1))            # 1446.0
print(label_volume_mm3(lbl, 2))            # 1619.0
```

Those two numbers are the first and second rows of `manifest.csv` for case 0.
The file you saved and the truth the generator recorded agree — which is what
`test_dataset_roundtrip` checks automatically on every push.

### 5.4 Compare every case against its truth

```python
import pandas as pd
from stableseg.io import load_volume, label_volume_mm3

manifest = pd.read_csv("data/phantom/manifest.csv")
for _, row in manifest.iterrows():
    lbl = load_volume(f"data/phantom/labels/{row.case_id}.nii.gz")
    measured = label_volume_mm3(lbl, 1) + label_volume_mm3(lbl, 2)
    print(f"{row.case_id}  truth={row.true_volume_total_mm3:8.1f}  "
          f"measured={measured:8.1f}  diff={measured - row.true_volume_total_mm3:+.1f}")
```

```
phantom_000  truth=  3065.0  measured=  3065.0  diff=+0.0
phantom_001  truth=  1594.0  measured=  1594.0  diff=+0.0
...
```

**Every difference is exactly zero, and that is the point.** No perturbation
has been applied and no segmenter has run — this only proves that saving and
reloading a file loses nothing. It is the baseline. From phase 3 onward those
differences stop being zero, and *how far* they move is the entire subject of
this project.

Leave Python with `exit()` or Ctrl-D.

---

## 5b · The R side

Optional. Skip this section entirely if you have not installed R
([`01-setup-r.md`](01-setup-r.md)); nothing else depends on it.

### 5b.1 Verify the R toolchain

```bash
Rscript R/verify_setup.R
```

The important lines:

```
Cross-check against the Python side:
  mean total volume computed in R: 2269.75 mm3
  value published by the Python tool: 2269.75 mm3
  -> match

R toolchain verified.
```

**What this proves, and why it is worth a whole script.** Python generated the
data and published a number. R read the saved file, independently, and got the
same number. That confirms the file was written correctly, read correctly, and
that both languages agree on the arithmetic — before either is trusted with
anything that matters.

It has been run on macOS with R 4.6 and on Linux with R 4.3, on different
processor architectures, producing identical digits. That is the shape of every
cross-check this project will make: **two implementations, one number.**

Note that this script uses **base R only** — no packages, so nothing to
download and nothing to fail behind a proxy. Package management arrives at the
statistics phase.

### 5b.2 The same thing from RStudio

Open `stableseg.Rproj` (double-click it, or **File → Open Project**). Opening
the project file rather than the script sets the working directory to the
project root automatically.

Then open `R/verify_setup.R` and click **Source** — or press **Ctrl+Shift+S**,
**Cmd+Shift+S** on a Mac. Same output, in the console pane.

### 5b.3 A one-off calculation without a script

```bash
Rscript -e 'm <- read.csv("data/phantom/manifest.csv"); print(mean(m$true_volume_total_mm3))'
```

```
[1] 2269.75
```

`-e` runs a single expression, the way `python -c` does. Useful for a quick
question you do not want to keep.

### 5b.4 Running both editors at once

VS Code and RStudio can be open on this project simultaneously, and it is a
reasonable way to work: VS Code for the Python, RStudio for the R.

They do not conflict — both are ordinary text editors reading the same folder.
The one rule: **do not leave unsaved edits to the same file in both.** Whichever
saves last wins, silently. Since Python lives in `src/` and R lives in `R/`,
that situation should not arise in practice.

---

## 6 · Development commands

### 6.1 The loop you will run hundreds of times

```bash
ruff format src tests scripts    # apply one consistent code style
ruff check .                     # find mistakes without running anything
pytest -q                        # run every automated check
```

```
16 files left unchanged
All checks passed!
36 passed in 0.6s
```

**What each is for.** `ruff format` rewrites files to one style, so nobody
argues about layout. `ruff check` is a spell-checker for code: unused imports,
likely bugs, outdated syntax. `pytest` runs the automated checks — small
programs that call your code with a known input and assert the answer.

### 6.2 See which lines the checks actually exercise

```bash
pytest -q --cov=stableseg --cov-report=term-missing
```

Prints a table of coverage per file and the line numbers never reached. Useful
for finding untested code — though high coverage means "this ran", not "this is
correct", and it is worth not confusing the two.

### 6.3 Run one test file, or one test

```bash
pytest tests/test_phantom.py -v
pytest tests/test_phantom.py::test_same_seed_same_phantom -v
```

`-v` prints each test name and its result. Invaluable when fixing one thing.

### 6.4 The pre-push safety check

```bash
python scripts/preflight.py
```

```
Preflight: examined 36 file(s)

  ok    branch: develop
  ok    no ignored-by-design paths are tracked
  ok    no file over 1024 KB
  ok    no credential patterns found
  ok    no absolute home paths in code or config
  ok    vocabulary check skipped (no local .preflight-words file)

Clear to commit and push.
```

Run it before every push. Details in [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

### 6.5 Start completely fresh

```bash
rm -rf data runs
stableseg phantom
```
Windows PowerShell:
```powershell
Remove-Item -Recurse -Force data, runs
stableseg phantom
```

Safe, and worth doing occasionally. `data/` and `runs/` are regenerated by
code and excluded from version control precisely so that deleting them proves
nothing important was hiding in them.

---

## 7 · Reading a run's provenance

Every run writes a record of itself.

```bash
cat runs/phantom-smoke/run.json
```
Windows PowerShell: `Get-Content runs\phantom-smoke\run.json`

```json
{
  "config": {
    "data": { "phantom": { "n_cases": 8, "seed": 42, ... }, ... },
    "name": "phantom-smoke",
    "output": { "root": "runs", "run_name": "phantom-smoke" }
  },
  "created_utc": "2026-09-01T10:15:33+00:00",
  "n_cases": 8,
  "stableseg_version": "0.1.0",
  "step": "generate_phantoms"
}
```

**Why this file exists.** Months from now, looking at a number, you will want
to know what produced it. This answers: which version of the code, with which
settings, when. In regulated analysis that trail is mandatory; everywhere else
it is merely the difference between a result and a rumour.

---

## 8 · Recipes for phases not yet built

Listed so you know what is coming and can see that nothing is being quietly
skipped. Each appears here, with real pasted output, when its phase lands.

| Phase | Commands it will add |
|---|---|
| 2 · Real data | `stableseg fetch-msd`, `stableseg describe` on a real scan, DICOM import |
| 3 · Perturbations | `stableseg perturb --profile mri`, listing available disturbances |
| 4 · Segment & measure | `stableseg segment`, `stableseg measure`, SQL queries against the results database |
| 5 · Statistics | `stableseg audit`, `stableseg sample-size --detect 5%`, and the R cross-check with `irr` / `psych` / `blandr` |
| 6 · Deep segmenter | `stableseg train`, `stableseg segment --model unet` |
| 7 · Explorer | `streamlit run app/explorer.py` |
| 8 · Report | `quarto render report/audit.qmd` |

---

## 9 · When something goes wrong

| What you see | What it means | Fix |
|---|---|---|
| `command not found: stableseg` | environment not active | Look for `(.venv)`; activate it |
| `No such file or directory: configs/phantom.yaml` | wrong folder | `cd` to the project root; `ls` should show `README.md` |
| `pytest: no tests ran` | wrong folder | Same fix |
| `ValidationError` | a settings value broke a rule | Read the field name in the message; the rule is in `config.py` |
| `mean_true_volume_mm3` is not `2269.75` | a different numerical library version | `python -m pip install -r requirements.lock --force-reinstall` |
| `PermissionError` writing `data/` | project sits in a synced folder | Move it to a plain local folder |

Your setup guide has a fuller table for installation problems specifically.

---

## 10 · Committing changes to this document

```bash
git switch develop
git add -A
git commit -m "docs: extend CLI cookbook"
git push origin develop develop:beta develop:master

## --tags is optional, only when required

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: [`UNINSTALL.md`](UNINSTALL.md) — removing everything cleanly, if you ever
want to.
