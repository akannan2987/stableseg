# 01 · Setup: R and RStudio (optional)

[← Build guide](../BUILD_GUIDE.md) · [README](../README.md) · [Glossary](00-glossary.md)

**Prerequisites:** the main setup done — Python, Git and the project installed
and verified on your machine.
**Learning goal:** after this page you have R and RStudio working, you know what
each one is and how they differ from Python and VS Code, and you have run the
project's R check successfully.
**Time:** about 30 minutes.
**Checkpoint:** `Rscript R/verify_setup.R` ends with `R toolchain verified.`

**This page is optional.** The project runs completely without R. Skip it if
you want to; nothing later breaks. Come back before phase 5, which is where R
starts earning its place.

---

## 1. What R is, and why a Python project uses it

### 1.1 R in one paragraph

**R** is a programming language built by statisticians, for statistics. Python
is a general-purpose language that acquired excellent scientific libraries; R
was designed from the start around data, models and plots. Both are free, both
are widely used, and in research they are the two languages you meet.

Everyday comparison: Python is a well-equipped workshop where you can build
almost anything. R is a specialist bench with every measuring instrument
already laid out. For the specific job of statistics, the specialist bench is
often faster and more trustworthy.

### 1.2 So why is this project written in Python?

Because the imaging tools live there. Reading a scan while preserving its
physical geometry, resampling a three-dimensional volume, training a
segmentation network — the mature libraries for all of that (`nibabel`,
`SimpleITK`, MONAI) are Python. There is no serious R equivalent, and
reimplementing them would be work with no payoff.

### 1.3 So why bring R in at all?

For one specific job, at phase 5: **checking the statistics a second time.**

The measurements this project ultimately reports — intraclass correlation,
Bland–Altman limits, the repeatability coefficient — are computed by formulas
written out by hand in Python, so that every step is visible and teachable. But
a formula written out by hand is a formula that can be written out wrongly.

R has mature, peer-reviewed packages for exactly these statistics (`irr`,
`psych`, `blandr`), written and checked by statisticians over many years. So
the same numbers get computed twice, by two unrelated implementations, and
**must agree to four decimal places.**

- If they agree, the formula is almost certainly right.
- If they diverge, one of them is wrong, and you now know to go and find out
  which — instead of publishing a confident wrong number.

Everyday comparison: two people independently adding up the same column of
figures. Agreement is real evidence. One person checking their own work twice
is not.

Most projects never do this. It is cheap, and it is the single strongest thing
you can do for confidence in a computed statistic.

### 1.4 What RStudio is

**RStudio** is an editor built specifically for R — the equivalent of VS Code
for Python. It shows your script, the console, the variables currently in
memory, and any plots, all in one window. You can use R without it (from a
terminal), but RStudio makes the exploratory parts far more comfortable.

It runs on Windows, macOS and RHEL 8.

---

## 2. Install R

R must be installed **before** RStudio. RStudio is only an editor — it needs
an R to drive, and it looks for one at startup.

### Windows

1. Open **https://cran.r-project.org/bin/windows/base/**
2. Click the large **Download R for Windows** link at the top.
3. Run the installer, accepting the defaults.
4. **Close and reopen PowerShell** so it picks up the new command.

Verify:
```powershell
Rscript --version
```
Expected: `Rscript (R) version 4.x.x ...`

**If `Rscript` is not recognised**, the installer did not add R to your PATH.
Either re-run it and tick that option, or use the full path:
`& "C:\Program Files\R\R-4.x.x\bin\Rscript.exe" --version`

### macOS

1. Open **https://cran.r-project.org/bin/macosx/**
2. Download the `.pkg` for your machine. Two are listed: **Apple silicon** for
   M-series Macs, **Intel** for older ones. If unsure, click the Apple menu →
   About This Mac and read the chip line.
3. Run the installer, accepting the defaults.

Verify:
```bash
Rscript --version
```
Expected: `Rscript (R) version 4.x.x ...`

Homebrew users can instead run `brew install r`, which works equally well.

### RHEL 8 (and Rocky / Alma 8)

R lives in the EPEL repository — a community-maintained collection of extra
packages for Red Hat systems.

```bash
sudo dnf install -y epel-release
sudo dnf install -y R
```

Verify:
```bash
Rscript --version
```

**If EPEL is not available on your machine** (some managed environments
restrict it), ask your administrator. Building R from source is possible but a
poor use of an afternoon — and remember this whole page is optional.

---

## 3. Install RStudio (optional, but recommended)

RStudio is optional even within this optional page: the script below runs fine
from a terminal.

1. Open **https://posit.co/download/rstudio-desktop/**
2. The page detects your system and offers the right installer. Choose the
   **free Desktop** version — there is a paid Pro edition you do not need.
3. Install it, then open it.

On first launch it should find your R automatically and show its version in the
console pane. If it reports that no R installation was found, R either is not
installed or was installed after RStudio last looked — reinstall R, then
restart RStudio.

### Opening the project in RStudio

The repository contains **`stableseg.Rproj`** — RStudio's project file. Use it:

**File → Open Project**, choose `stableseg.Rproj`. Or simply double-click the
file in your file browser.

**What a `.Rproj` file does.** It tells RStudio that this folder is a project,
and on opening it sets the working directory to the folder containing it. That
means scripts find `data/` and `R/` without anyone remembering
**Session → Set Working Directory**, which is the single most common cause of
"it worked yesterday" in R.

**The two settings inside it worth understanding**, because they are set
against RStudio's defaults on purpose:

```
RestoreWorkspace: No
SaveWorkspace: No
```

By default, RStudio saves every variable in memory to a hidden `.RData` file
when you quit, and reloads them when you start. That feels helpful and quietly
destroys reproducibility: a script appears to work because a variable is left
over from an hour ago, and then fails for everyone else — including you next
month.

Starting from an empty workspace every time means a script either works from
scratch or does not. The everyday version: cooking from the recipe each time,
rather than from half-prepared ingredients you left on the counter and have
now forgotten about.

Open `R/verify_setup.R` from the Files pane once the project is open.

### Using RStudio and VS Code at the same time

You can, and it is a sensible way to work on this project: VS Code for the
Python in `src/`, RStudio for the R in `R/`.

They do not conflict. Both are ordinary text editors reading the same folder;
neither locks files or claims ownership. Git does not care which one wrote a
change.

**One rule:** do not leave unsaved edits to the *same file* open in both.
Whichever saves last overwrites the other, without warning. Since the Python
and R live in separate folders, this should not come up.

Two small things that make the pairing smoother:

- Run the Python commands from VS Code's built-in terminal (it opens already in
  the project folder, with the environment activatable) and the R from
  RStudio's console.
- RStudio's Git pane works on the same repository as the command line. Use
  whichever you prefer; the branch model in
  [`03-git-workflow.md`](03-git-workflow.md) is unchanged either way.

---

## 4. Run the check

### 4.1 First, make sure the data exists

The R script reads a file the Python side produces. In a terminal, with the
Python environment active:

```bash
stableseg phantom
```

If you skip this, the R script will tell you so and print the command to run —
it fails helpfully rather than cryptically.

### 4.2 Run it from the terminal

From the project root:

```bash
Rscript R/verify_setup.R
```

Expected output:

```
StableSeg - R toolchain check
------------------------------------------------------------
R version   : R version 4.3.3 (2024-02-29)
Platform    : x86_64-pc-linux-gnu
Project root: /home/you/projects/stableseg

Manifest read: 8 cases, 6 columns

Total structure volume per case (cubic millimetres):
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max.
   1460    1684    2124    2270    2998    3126

Spread across cases:
  mean = 2269.75   sd = 699.77   coefficient of variation = 30.8%

Are the two label volumes related across cases?
  Pearson correlation (label 1 vs label 2) = 0.9998

Cross-check against the Python side:
  mean total volume computed in R: 2269.75 mm3
  value published by the Python tool: 2269.75 mm3
  -> match

Note: this data is SYNTHETIC - generated by code, not scanned from
anyone. It exists so the pipeline can be checked against a known
true answer, which real scans never have.

------------------------------------------------------------
R toolchain verified.
```

Your R version and platform line will differ. **Every number should be
identical**, because the data is generated from a fixed seed.

### 4.3 Run it from RStudio

With `R/verify_setup.R` open, click **Source** (top right of the editor pane),
or press **Ctrl+Shift+S** — **Cmd+Shift+S** on a Mac. The same output appears
in the console below.

---

## 5. What the output actually says

Worth understanding rather than just seeing pass, because each part previews
something the statistics phase does properly.

**The summary table** is R's `summary()`: minimum, quartiles, median, mean and
maximum of the eight case volumes. A quartile is a cut point — the first
quartile is the value a quarter of the cases fall below. It is the fastest way
to see the shape of a set of numbers.

**The coefficient of variation** is the spread expressed as a percentage of the
average. Here it is about 31%, describing how much the *phantoms differ from
each other* — which is by design, since each is generated at a random size.

Note the connection: the same idea applied to **repeated measurements of the
same case** rather than across different cases is the *within-subject
coefficient of variation*, one of the headline numbers this project reports.
This is a preview of the arithmetic, not that statistic.

**The correlation** between the two label volumes is 0.9998 — almost perfect.
Expected, because each phantom is generated at one random size and both parts
scale together. A weak value here would mean the generator is not doing what it
claims, so this is a quiet check on the Python side.

**The cross-check** is the point of the whole script. `stableseg phantom`
prints `mean_true_volume_mm3: 2269.75`. R reads the saved file and computes
2269.75. That confirms three things at once: the file was written correctly,
read correctly, and both languages agree on the arithmetic.

**The synthetic note** appears in the output, not only in a document. Anyone
who runs this and pastes the result somewhere carries the disclosure with them.

---

## 6. What could go wrong

| What you see | What it means | Fix |
|---|---|---|
| `Rscript: command not found` | R not installed, or not on PATH | Section 2. On Windows, reopen the terminal after installing |
| `Could not find the project root` | run from outside the project | `cd` to your `stableseg` folder and run `Rscript R/verify_setup.R` |
| `The phantom manifest is missing` | the data has not been generated | Activate the Python environment and run `stableseg phantom` |
| `-> MISMATCH` in the cross-check | the two languages disagree on a number | Do not ignore this. Re-run `stableseg phantom`, then the script again. If it persists, report it with both outputs |
| RStudio says no R installation found | RStudio installed before R, or R was removed | Install R, restart RStudio |
| `No match for argument: R` on RHEL | EPEL not enabled | `sudo dnf install -y epel-release`, then retry |
| The summary numbers differ from those above | a non-default manifest | Regenerate with the default settings: `stableseg phantom --config configs/phantom.yaml` |

---

## 7. What comes next for R

Nothing until phase 5. When it arrives, this folder gains:

- **`renv`** — R's equivalent of the Python lock file, recording the exact
  version of every R package so anyone can recreate the environment. Its
  downloaded package library is excluded from version control, exactly as
  `.venv` is on the Python side; the lock file itself is committed.
- **The real cross-check** — intraclass correlation and Bland–Altman computed
  with `irr`, `psych` and `blandr`, required to agree with the Python
  implementation to four decimal places.
- **A short statistical write-up**, rendered with Quarto, which handles R and
  Python in the same document.

Everything R-related stays optional. The project must remain fully usable by
someone who never installs it.

---

## 8. Committing changes to this document

```bash
git switch develop
git add -A
git commit -m "docs: update R setup guide"
git push origin develop develop:beta develop:master

## --tags is optional, only when required
## then switch back to local master and pull in the remote changes

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: back to the [build guide](../BUILD_GUIDE.md), section 8 — real data.
