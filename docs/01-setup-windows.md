# 01 · Setup on Windows (10 or 11), from a blank machine

[← Build guide](../BUILD_GUIDE.md) · [README](../README.md) · [Glossary](00-glossary.md)

**Prerequisites:** a Windows 10 or 11 machine, an internet connection, and
permission to install software. Nothing else.
**Learning goal:** after this page you have Python 3.13, Git and VS Code installed,
you know what a terminal is and how to open one, and you have run StableSeg
successfully.
**Time:** about 45 minutes, mostly downloading.
**Checkpoint:** `stableseg phantom` prints `"mean_true_volume_mm3": 2269.75`.

Every command below is shown exactly as you should type it, with the output
you should see. If your output differs, look at section 9.

---

## 1. What a terminal is, and how to open one

A **terminal** is a window where you type commands instead of clicking. It
looks intimidating and is not: you type a line, press Enter, and the computer
does one thing and tells you what happened. On Windows the terminal program is
**PowerShell**.

1. Press the **Windows key**.
2. Type `powershell`.
3. Click **Windows PowerShell** (the plain one, not "ISE", not "as
   Administrator" unless a step below says so).

A blue or black window opens showing something like:

```
PS C:\Users\yourname>
```

That is the **prompt**. `C:\Users\yourname` is the folder you are currently
"standing in". Two commands to know before anything else:

```powershell
pwd
```
Prints the folder you are standing in.

```powershell
dir
```
Lists what is in it.

Try both now. That is the whole skill.

---

## 2. Install Python 3.13

**Which version, and why.** This project supports **Python 3.12 and 3.13**,
and nothing else. Both bounds have a concrete reason, and they are the kind of
constraint you will meet in every project:

- **Not 3.11 or older.** The pinned versions of `numpy` and `scipy` in
  `requirements.lock` declare that they need 3.12 or newer. The project's own
  code would run on 3.11 perfectly well; its dependencies will not install
  there. The dependency floor wins.
- **Not 3.14 or newer.** The imaging stack has not been verified there yet,
  and later phases add PyTorch and MONAI, which typically lag a new Python
  release by months. On an unsupported version pip stops using ready-built
  packages and tries to compile from source, which needs a C compiler you do
  not have. Being one version behind the newest is normal and deliberate in
  scientific Python.
- **On Windows, take 3.13.** Python 3.12 has entered its "security fixes only"
  stage, so python.org no longer publishes Windows installers for it — only
  source tarballs. 3.13 still has a proper installer.

1. Open https://www.python.org/downloads/windows/ in a browser.
2. Find the newest **Python 3.13.x** release that lists files beneath it.
   (If a release says "No installers", it is source-only — go to the next
   newest 3.13.x.)
3. Click **Windows installer (64-bit)**. The file is about 25 MB.
4. Run the downloaded file.
5. **On the first screen, tick the box at the bottom: "Add python.exe to
   PATH".** This is the single most important click in this guide. Without it,
   your terminal will not find Python and every later command fails.
6. Click **Install Now**. Accept the permission prompt.
7. When it finishes, if you see a button labelled **Disable path length
   limit**, click it. Then close the installer.
8. **Close your PowerShell window and open a new one.** A terminal only reads
   the PATH when it starts, so an already-open window will not see Python.

Verify:

```powershell
python --version
```
Expected:
```
Python 3.13.x
```

```powershell
python -m pip --version
```
Expected something like:
```
pip 25.x from C:\Users\yourname\AppData\Local\Programs\Python\Python313\Lib\site-packages\pip (python 3.13)
```

**Already have 3.12 installed?** Use it instead; both are supported. Check
what you have with `py --list` (the `py` launcher ships with the installer and
lists every Python on the machine).

**If `python --version` opens the Microsoft Store instead**, Windows is
intercepting the command. Fix: press Windows key, type `manage app execution
aliases`, open it, and switch **off** both `python.exe` and `python3.exe`.
Close the terminal, open a new one, try again.

---

## 3. Install Git

**What Git is:** a save-game system for a folder of code. Every time you
"commit", it takes a snapshot you can return to. You need it to publish the
project and to keep your own history.

1. Open https://git-scm.com/download/win.
2. The 64-bit Standalone Installer downloads automatically. Run it.
3. Click through the installer accepting **every default**. There are about
   ten screens; the defaults are correct for this project. Two worth noticing
   as they pass:
   - "Choosing the default editor" — leave whatever it suggests; you will not
     use it.
   - "Adjusting your PATH environment" — leave the middle option
     ("Git from the command line and also from 3rd-party software").
4. Finish. **Close and reopen PowerShell.**

Verify:

```powershell
git --version
```
Expected:
```
git version 2.4x.x.windows.1
```

Tell Git who you are (it stamps every snapshot with this; use the email
attached to your GitHub account):

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch master
```

No output means success. Check with:

```powershell
git config --global --list
```

---

## 4. Install VS Code (the editor)

**What an editor is:** a text editor built for code. It colours the syntax,
warns about mistakes, and has a terminal built in.

1. Open https://code.visualstudio.com/ and click **Download for Windows**.
2. Run the installer. Accept the defaults, but on the "Select Additional
   Tasks" screen tick **"Add 'Open with Code' action to Windows Explorer
   directory context menu"** — it makes opening a project folder one click.
3. Launch VS Code.
4. Click the **Extensions** icon in the left bar (four squares). Search for
   `Python`, and install the one published by **Microsoft**. That is the only
   extension you need.

---

## 5. Put the project somewhere sensible

Create a projects folder and move the unzipped `stableseg` folder into it.

```powershell
mkdir $HOME\projects -Force
```

Now, in File Explorer, drag the unzipped `stableseg` folder into
`C:\Users\yourname\projects\`. Then, back in PowerShell:

```powershell
cd $HOME\projects\stableseg
dir
```
Expected: a listing containing `README.md`, `pyproject.toml`, `src`, `tests`,
`docs`, `configs`, `requirements.lock`.

**Do not put the project in OneDrive, Dropbox or Google Drive.** Those
services lock files while syncing, and Python will fail with permission errors
at random moments. `C:\Users\yourname\projects` is a plain local folder.

Open the project in the editor:

```powershell
code .
```
(The dot means "this folder".) VS Code opens with the file tree on the left.
Its built-in terminal is **Terminal → New Terminal**, and it opens already
standing in the project folder — from here on you can use that instead of
PowerShell.

---

## 6. Create the virtual environment

**What it is and why:** a **virtual environment** is a private toolbox for one
project: a folder holding its own copy of Python and its own libraries. Two
projects on the same machine can then use different, conflicting versions of
the same library without fighting. It also means you can delete the folder and
start over without touching your system.

```powershell
py -3.13 -m venv .venv
```
No output, about 10 seconds. A hidden `.venv` folder now exists.

`py -3.13` names the interpreter explicitly through the Python launcher, which
is what decides the version the environment is built on. Plain `python -m venv`
would use whichever Python happens to be first on your PATH, and on a machine
with several installed that is a coin toss. If you installed 3.12 instead, use
`py -3.12`.

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```
Expected: your prompt gains a green `(.venv)` prefix, and the version printed
is the one you chose:
```
(.venv) PS C:\Users\yourname\projects\stableseg>
Python 3.13.x
```

**Check that version before continuing.** If it is outside 3.12–3.13, stop:
`deactivate`, `Remove-Item -Recurse -Force .venv`, and redo this section with
`py -3.13`.

**If you see** `cannot be loaded because running scripts is disabled on this
system`: Windows blocks scripts by default. Run this once, then activate
again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Answer `Y`. This allows locally-created scripts to run for your user only; it
is the standard setting for development machines.

> **The rule for the rest of your life with this project:** every new terminal
> starts *without* the toolbox. If a command fails with "not recognized",
> check for the `(.venv)` prefix first. It is the cause nine times out of ten.

To leave the environment later: `deactivate`.

---

## 7. Install the project

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.lock
```
This downloads roughly 200 MB and takes 2–5 minutes. `requirements.lock` lists
every library at an exact tested version, so you get precisely what the
project was built against. Expected final line: `Successfully installed` and a
long list of names.

```powershell
python -m pip install -e . --no-deps
```
Expected: `Successfully installed stableseg-0.1.0`.

`-e` means "editable": pip points at your `src` folder rather than copying it,
so edits take effect immediately. `--no-deps` means "do not re-resolve
dependencies, I already installed the pinned ones".

---

## 8. Prove it works

```powershell
python -c "import stableseg; print(stableseg.__version__)"
```
Expected: `0.1.0`

```powershell
pytest -q
```
Expected: `38 passed in 0.6s` (the time varies).

```powershell
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

```powershell
stableseg phantom
```
Expected:
```
{
  "data_root": "C:\\Users\\yourname\\projects\\stableseg\\data\\phantom",
  "n_cases": 8,
  "manifest": "...\\manifest.csv",
  "run_dir": "...\\runs\\phantom-smoke",
  "mean_true_volume_mm3": 2269.75
}
```

```powershell
stableseg describe data\phantom\images\phantom_000.nii.gz
```
Expected: JSON beginning `"shape": [48, 64, 48]`.

**That `2269.75` is the checkpoint.** It is the same number on Windows, macOS
and Linux, because the data generator is seeded. Seeing it means your install
is correct *and* reproducible.

Look at what you made: in VS Code's file tree, open `data/phantom/` (eight
image files and eight label files) and `runs/phantom-smoke/run.json` (the
record of what produced them).

---

## 9. What could go wrong

| What you see | What it means | Fix |
|---|---|---|
| `python : The term 'python' is not recognized` | PATH box unticked during install, or terminal opened before installing | Re-run the Python installer, choose **Modify**, tick "Add python.exe to PATH", finish. Open a **new** terminal. |
| The Microsoft Store opens when you type `python` | Windows app execution alias | Windows key → `manage app execution aliases` → switch off `python.exe` and `python3.exe` |
| `Activate.ps1 cannot be loaded ... running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, answer `Y` |
| `stableseg : The term 'stableseg' is not recognized` | virtual environment not active, or step 7 skipped | Look for `(.venv)` in the prompt; activate; re-run step 7 |
| `error: Microsoft Visual C++ 14.0 or greater is required` | pip is compiling from source because no ready-built package matches your Python | You are on 3.14+ or on 32-bit Python. Install 64-bit Python 3.13, delete `.venv`, redo sections 6–7. |
| `ERROR: Could not install packages due to an OSError: [WinError 5] Access is denied` | the project is in a synced folder, or an antivirus is holding a file | Move the project to `C:\Users\yourname\projects`; close VS Code and retry |
| Long-path errors mentioning 260 characters | Windows path limit | Re-run the Python installer and click "Disable path length limit"; keep the project path short |
| `ERROR: Package 'stableseg' requires a different Python: 3.x.y not in '<3.14,>=3.12'` | the environment was built on an unsupported interpreter | `deactivate`, `Remove-Item -Recurse -Force .venv`, redo section 6 with `py -3.13` |
| python.org shows "No installers" for the version you wanted | that release is in security-fix-only stage and ships source only | take the newest 3.13.x, which still has an installer |
| `pytest` says `no tests ran` | you are not standing in the project folder | `cd $HOME\projects\stableseg`, check with `dir` that `tests` is there |
| `mean_true_volume_mm3` is not 2269.75 | a different NumPy version | `python -m pip install -r requirements.lock --force-reinstall` |
| Everything worked yesterday, nothing works today | new terminal, environment not active | `cd $HOME\projects\stableseg` then `.\.venv\Scripts\Activate.ps1` |

---

## 10. The short loop, from tomorrow onwards

Setup happens once. Every working session afterwards is three lines:

```powershell
cd $HOME\projects\stableseg
.\.venv\Scripts\Activate.ps1
pytest -q
```

Then edit, run, and commit (see [`03-git-workflow.md`](03-git-workflow.md)).

---

## 11. Optional: 3D Slicer, for looking at scans

Not needed for any command above, but useful from phase 2 when real MRI
arrives. Free, from https://download.slicer.org/. Install it, then
**File → Add Data**, choose `data\phantom\images\phantom_000.nii.gz`, and
scroll through the slices with your mouse wheel.

---

Next: [`02-architecture.md`](02-architecture.md) — what you just installed and
why every piece exists.
