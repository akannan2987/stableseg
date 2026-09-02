# 01 · Setup on macOS, from a blank machine

[← Build guide](../BUILD_GUIDE.md) · [README](../README.md) · [Glossary](00-glossary.md)

**Prerequisites:** a Mac (Intel or Apple Silicon) running macOS 12 or later, an
internet connection, and your account password for installations.
**Learning goal:** after this page you have Python 3.13, Git and VS Code installed,
you know what a terminal is, and you have run StableSeg successfully.
**Time:** about 45 minutes, mostly downloading.
**Checkpoint:** `stableseg phantom` prints `"mean_true_volume_mm3": 2269.75`.

---

## 1. What a terminal is, and how to open one

A **terminal** is a window where you type commands instead of clicking. You
type a line, press Enter, the computer does one thing and tells you what
happened.

1. Press **Command + Space**.
2. Type `terminal`.
3. Press Enter.

A window opens with a **prompt** like:

```
yourname@MacBook ~ %
```

The `~` is your home folder: the folder you are currently standing in. Two
commands before anything else:

```bash
pwd
```
Prints the folder you are standing in.

```bash
ls
```
Lists what is in it.

Try both. That is the whole skill.

---

## 2. Install Python 3.13

**Why not the Python already on your Mac?** macOS ships an old Python that
Apple's own tools depend on. Installing packages into it can break system
software, and its version is too old anyway (3.9, which reached end of life in
2025). We install a separate one and leave Apple's alone.

**Which version, and why.** This project supports **Python 3.12 and 3.13**,
and nothing else. The reasons for each bound are worth understanding, because
they are the kind of constraint you will meet in every project:

- **Not 3.11 or older.** The pinned versions of `numpy` and `scipy` in
  `requirements.lock` declare that they need 3.12 or newer. The project's own
  code would run on 3.11 perfectly well; its dependencies will not install
  there. The dependency floor wins.
- **Not 3.14 or newer.** The imaging stack has not been verified there yet,
  and later phases add PyTorch and MONAI, which typically lag a new Python
  release by months. Being one version behind the newest is normal and
  deliberate in scientific Python.
- **On macOS, take 3.13.** Python 3.12 has entered its "security fixes only"
  stage, which means python.org no longer publishes macOS installers for it —
  only source tarballs. 3.13 still has a proper installer, so it is the
  sensible choice here. (RHEL 8 users take 3.12, because that is what Red Hat
  packages; both work identically for this project.)

1. Open https://www.python.org/downloads/macos/ in a browser.
2. Find the newest **Python 3.13.x** release with files listed under it.
3. Click **macOS 64-bit universal2 installer**. "Universal2" works on both
   Intel and Apple Silicon Macs, so there is only one choice to make.
4. Open the downloaded `.pkg` file and click through, accepting the defaults.
   You will be asked for your password.
5. At the end, a Finder window opens. Double-click
   **`Install Certificates.command`** and let it run, then close the window
   it opens. This step lets Python download packages over HTTPS; skipping it
   causes an `SSL: CERTIFICATE_VERIFY_FAILED` error later.
6. **Close your Terminal window and open a new one.**

Verify:

```bash
python3.13 --version
```
Expected:
```
Python 3.13.x
```

See every version installed on your machine:

```bash
ls /Library/Frameworks/Python.framework/Versions/
```
Expected: a list including `3.13`. Other versions may sit beside it; that is
fine and normal. They do not interfere, because in section 6 we name the one
we want explicitly.

> **Note on the command name:** on macOS, plain `python` usually does not
> exist, and plain `python3` may point at Apple's copy or at whichever version
> you installed last. **Always type the full `python3.13`** until the virtual
> environment is active (section 6), after which plain `python` means the
> project's copy and nothing else. Naming the version explicitly is the single
> best habit for avoiding an afternoon of confusion.

**Already have 3.12 installed?** Use it: substitute `python3.12` wherever this
guide says `python3.13`. Both are supported.

---

## 3. Install Git

**What Git is:** a save-game system for a folder of code. Every "commit" is a
snapshot you can return to. You need it to publish the project and to keep
your own history.

macOS can install Git for you through Apple's command-line tools:

```bash
git --version
```

- If it prints a version (`git version 2.39.x` or similar), Git is already
  there. Skip to the configuration below.
- If a dialogue appears offering to install "command line developer tools",
  click **Install** and wait (5–10 minutes). Then run `git --version` again.

Tell Git who you are (it stamps every snapshot; use the email attached to your
GitHub account):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch master
```

No output means success. Check with:

```bash
git config --global --list
```

---

## 4. Install VS Code (the editor)

**What an editor is:** a text editor built for code. It colours the syntax,
warns about mistakes, and has a terminal built in.

1. Open https://code.visualstudio.com/ and click **Download for macOS**.
2. Unzip the download and drag **Visual Studio Code** into `/Applications`.
3. Open it (right-click → Open the first time, if macOS warns about an
   unidentified developer).
4. Click the **Extensions** icon in the left bar (four squares), search for
   `Python`, install the one published by **Microsoft**. That is the only
   extension you need.
5. Optional but convenient: press **Command + Shift + P**, type
   `shell command`, and choose **Shell Command: Install 'code' command in
   PATH**. That lets you type `code .` in a terminal to open the current
   folder.

---

## 5. Put the project somewhere sensible

```bash
mkdir -p ~/projects
```

In Finder, drag the unzipped `stableseg` folder into your `projects` folder.
Then, in the terminal:

```bash
cd ~/projects/stableseg
ls
```
Expected: `README.md  configs  docs  pyproject.toml  requirements.lock  src  tests` and a few more.

**Do not put the project in iCloud Drive, Dropbox or Google Drive.** Those
services move and lock files while syncing, which produces permission errors
at random moments. `~/projects` is a plain local folder. (Note that `~/Desktop`
and `~/Documents` are inside iCloud Drive if "Desktop & Documents Folders" is
switched on in your iCloud settings — another reason to use `~/projects`.)

Open the project in the editor:

```bash
code .
```
VS Code opens with the file tree on the left. Its built-in terminal is
**Terminal → New Terminal**, and it opens already standing in the project
folder.

---

## 6. Create the virtual environment

**What it is and why:** a **virtual environment** is a private toolbox for one
project: its own Python, its own libraries. Two projects can then use
different, conflicting versions of the same library without fighting, and your
system Python stays untouched. Delete the folder and you have a clean slate.

```bash
python3.13 -m venv .venv
```
No output, about 10 seconds. A hidden `.venv` folder now exists (hidden
because it starts with a dot; `ls -a` shows it).

Naming `python3.13` here, rather than `python3`, is what decides which
interpreter the environment is built on. Get this wrong and the install in
section 7 fails with a version error.

Activate it:

```bash
source .venv/bin/activate
python --version
```
Expected: your prompt gains a `(.venv)` prefix, and the version printed is the
one you chose:
```
(.venv) yourname@MacBook stableseg %
Python 3.13.x
```

**Check that version before continuing.** If it says 3.11, 3.14 or anything
outside 3.12–3.13, stop: `deactivate`, `rm -rf .venv`, and redo this section
naming the interpreter explicitly.

> **The rule for the rest of your life with this project:** every new terminal
> starts *without* the toolbox. If a command fails with "command not found",
> check for the `(.venv)` prefix first. It is the cause nine times out of ten.

To leave the environment later: `deactivate`.

Inside an active environment, `python` and `pip` mean the project's copies, so
the rest of this guide drops the version suffix.

---

## 7. Install the project

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -r requirements.lock
```
Downloads roughly 200 MB, takes 2–5 minutes. `requirements.lock` lists every
library at an exact tested version, so you get precisely what the project was
built against. Expected final line: `Successfully installed` and a long list.

```bash
python -m pip install -e . --no-deps
```
Expected: `Successfully installed stableseg-0.1.0`.

`-e` means "editable": pip points at your `src` folder rather than copying it,
so edits take effect immediately. `--no-deps` means "do not re-resolve
dependencies, the pinned ones are already installed".

---

## 8. Prove it works

```bash
python -c "import stableseg; print(stableseg.__version__)"
```
Expected: `0.1.0`

```bash
pytest -q
```
Expected: `36 passed in 0.6s` (time varies).

```bash
stableseg version
```
Expected:
```
{
  "stableseg": "0.1.0"
}
```

> ### What is a "phantom", and why are we making one?
>
> A **phantom** is a stand-in for a patient, used to test a measuring
> instrument. Hospitals really do this: they scan a plastic object of known
> size to check the scanner is measuring correctly, because you cannot check a
> scanner against a person whose true anatomy nobody knows. A **digital
> phantom** is the same idea in software — an image generated by code,
> containing shapes whose exact true size the code knows.
>
> Think of the 1 kg calibration weight you put on a kitchen scale. You are not
> interested in the weight. You are checking the scale.
>
> `stableseg phantom` generates eight of them. Each one is a small 3-D image
> containing two touching blobs (standing in for the two parts of the brain
> structure this project will later measure on real scans), sitting in dim
> noisy "tissue", with a slight brightness gradient across it so it is not
> unrealistically clean. Because the code drew those blobs, it knows their true
> volume exactly.
>
> **Three reasons the project ships them:**
> 1. **The tests need data that is always there.** No download, no account, no
>    network — the suite runs in under a second on any machine.
> 2. **They have a known right answer.** Real scans only have an expert's
>    opinion. A phantom has arithmetic. That is how we prove the pipeline
>    measures what it claims before pointing it at data where nobody knows.
> 3. **They are reproducible.** The generator is seeded, so case 3 is
>    byte-for-byte identical on your machine and on mine. That is why
>    `2269.75` is the checkpoint below: if you see that number, your install is
>    not just working but reproducing the reference result exactly.
>
> **They are synthetic. They are not scans of any person.** Every file is
> marked `synthetic: true` internally, and every document says so. Real MRI
> arrives in phase 2.
>
> **Reading the files it produces:**
>
> | Path | What it is |
> |---|---|
> | `data/phantom/images/phantom_000.nii.gz` | the *picture* of case 0 — how bright each voxel is |
> | `data/phantom/labels/phantom_000.nii.gz` | the matching *outline* of case 0 — which structure each voxel belongs to |
> | `data/phantom/manifest.csv` | one row per case, with its known true volumes |
> | `runs/phantom-smoke/run.json` | the record of what produced all of the above |
>
> `phantom` = generated, not scanned. `000` = case number, zero-padded so case
> 2 sorts before case 10. `.nii` = NIfTI, the standard research format for a
> 3-D scan (one file holds the whole volume plus its voxel size and
> orientation). `.gz` = compressed; tools read it without unzipping. Image and
> label share a filename in two folders, which is how public imaging datasets
> pair them.
>
> Every term here is in the [glossary](00-glossary.md). The generator is taken
> apart line by line in
> [phase 1, section 5](04-phase-tutorials/phase-01-skeleton.md).

```bash
stableseg phantom
```
Expected:
```
{
  "data_root": "/Users/yourname/projects/stableseg/data/phantom",
  "n_cases": 8,
  "manifest": ".../manifest.csv",
  "run_dir": ".../runs/phantom-smoke",
  "mean_true_volume_mm3": 2269.75
}
```

```bash
stableseg describe data/phantom/images/phantom_000.nii.gz
```
Expected: JSON beginning `"shape": [48, 64, 48]`.

**That `2269.75` is the checkpoint.** It is identical on macOS, Windows and
Linux because the generator is seeded. Seeing it means your install is correct
*and* reproducible.

Look at what you made: `ls data/phantom/images` shows eight files;
`cat runs/phantom-smoke/run.json` shows the record of what produced them.

---

## 9. What could go wrong

| What you see | What it means | Fix |
|---|---|---|
| `command not found: python` | on macOS there is no plain `python` until the environment is active | use `python3.13`, or activate the environment |
| `ERROR: Package 'stableseg' requires a different Python: 3.x.y not in '<3.14,>=3.12'` | the environment was built on an unsupported interpreter | `deactivate`, `rm -rf .venv`, redo section 6 naming `python3.13` explicitly |
| python.org shows "No installers" for the version you wanted | that release is in security-fix-only stage and ships source only | take the newest 3.13.x, which still has an installer |
| `SSL: CERTIFICATE_VERIFY_FAILED` during pip install | the certificate step was skipped | open `/Applications/Python 3.13/` in Finder and double-click `Install Certificates.command` |
| `which python3` shows `/usr/bin/python3` | Apple's old Python is winning | ignore it and always type `python3.13` explicitly |
| `command not found: stableseg` | environment not active, or step 7 skipped | check for `(.venv)`; `source .venv/bin/activate`; re-run step 7 |
| pip tries to build SimpleITK or scikit-image from source and fails | no ready-built package for your Python version | you are on 3.14 or newer; install 3.13, `rm -rf .venv`, redo sections 6–7 |
| `Operation not permitted` reading or writing files | project sits in iCloud/Desktop/Documents with sync on, or macOS privacy protection | move the project to `~/projects` |
| `xcrun: error: invalid active developer path` | command-line tools missing | `xcode-select --install` |
| `pytest` says `no tests ran` | wrong folder | `cd ~/projects/stableseg`, check `ls` shows `tests` |
| `mean_true_volume_mm3` is not 2269.75 | a different NumPy version | `python -m pip install -r requirements.lock --force-reinstall` |
| Everything worked yesterday, nothing works today | new terminal, environment not active | `cd ~/projects/stableseg && source .venv/bin/activate` |

**A note on Apple Silicon:** everything above works natively on M-series Macs;
the universal2 installer and the pinned packages all ship arm64 builds. No
Rosetta needed.

**A note on Intel Macs:** later phases train a small neural network. Intel
Macs have no usable GPU acceleration for it, which is exactly why this project
uses a dataset small enough to train on a processor in minutes. Nothing is
lost.

---

## 10. The short loop, from tomorrow onwards

Setup happens once. Every working session afterwards is three lines:

```bash
cd ~/projects/stableseg
source .venv/bin/activate
pytest -q
```

Then edit, run, and commit (see [`03-git-workflow.md`](03-git-workflow.md)).

---

## 11. Optional: 3D Slicer, for looking at scans

Not needed for any command above, but useful from phase 2 when real MRI
arrives. Free, from https://download.slicer.org/. Install it, then
**File → Add Data**, choose `data/phantom/images/phantom_000.nii.gz`, and
scroll through the slices.

---

Next: [`02-architecture.md`](02-architecture.md) — what you just installed and
why every piece exists.
