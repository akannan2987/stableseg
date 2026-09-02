# 01 · Setup on RHEL 8 (and Rocky / Alma Linux 8), from a blank machine

[← START HERE](../START-HERE.md) · [README](../README.md) · [Glossary](00-glossary.md)

**Prerequisites:** a Red Hat Enterprise Linux 8 machine (or a Rocky Linux 8 /
AlmaLinux 8 clone), shell access, and `sudo` rights for the install steps.
If you do not have `sudo`, section 10 covers the no-root route.
**Learning goal:** after this page you have Python 3.12, Git and (optionally)
VS Code installed, and you have run StableSeg successfully.
**Time:** about 30 minutes.
**Checkpoint:** `stableseg phantom` prints `"mean_true_volume_mm3": 2269.75`.

---

## 1. The terminal

On a Linux server you are already in one; there is nothing to open. If you are
on a desktop RHEL install, open **Activities → Terminal**. If you are
connecting from another machine:

```bash
ssh yourname@your-rhel-host
```

Two commands before anything else:

```bash
pwd     # which folder am I standing in
ls      # what is in it
```

Confirm which system you are on:

```bash
cat /etc/redhat-release
```
Expected something like:
```
Red Hat Enterprise Linux release 8.10 (Ootpa)
```

---

## 2. Install Python 3.12

**The important background.** RHEL 8's own `python3` is version 3.6 or 3.9,
and system tools (including `dnf` itself) depend on it. **Never upgrade or
replace it.** Red Hat's answer is parallel installation: RHEL 8's AppStream
repository ships separate `python3.11` and `python3.12` package suites that
install alongside the system Python without touching it. That is what we use.

**Which version, and why.** This project supports **Python 3.12 and 3.13**,
and nothing else:

- **Not 3.11 or older.** The pinned versions of `numpy` and `scipy` in
  `requirements.lock` declare that they need 3.12 or newer. The project's own
  code would run on 3.11 perfectly well; its dependencies will not install
  there. The dependency floor wins.
- **Not 3.14 or newer.** Not yet verified against the imaging stack, and later
  phases add PyTorch and MONAI, which lag new Python releases.
- **On RHEL 8, take 3.12.** It is what Red Hat packages, and it is fully
  supported here. (macOS and Windows users take 3.13, because python.org no
  longer ships installers for 3.12; both versions work identically for this
  project.)

Check what is available:

```bash
dnf list python3.12 python3.11
```

Install Python 3.12 with pip and the development headers:

```bash
sudo dnf install -y python3.12 python3.12-pip python3.12-devel
```

Expected: a package list, then `Complete!`. It does not remove or change
`python3`.

Verify:

```bash
python3.12 --version
```
Expected:
```
Python 3.12.x
```

**If `dnf list` shows nothing for python3.12**, your AppStream repository is
not enabled or your system predates RHEL 8.6. Enable AppStream:

```bash
# the exact repository name varies by architecture, so list them first
sudo dnf repolist all | grep -i appstream
sudo subscription-manager repos --enable rhel-8-for-x86_64-appstream-rpms
```

**Do not fall back to `python3.11`.** RHEL 8 also packages 3.11, and it will
install cleanly, but the pinned `numpy` and `scipy` refuse to install on it —
you would get an error at the end of section 7 rather than here. If 3.12 is
genuinely unavailable on your system, that is a blocker to raise with your
administrator, not something to work around.

> **Use the versioned command.** On RHEL, plain `python` is deliberately
> ambiguous and may not exist at all. Always type `python3.12` until the
> virtual environment is active, after which plain `python` means the right
> one.

---

## 3. Install Git

**What Git is:** a save-game system for a folder of code. Every "commit" is a
snapshot you can return to.

```bash
git --version
```

If it is missing:

```bash
sudo dnf install -y git
```

Configure it (use the email attached to your GitHub account):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch master
```

RHEL 8's Git is version 2.31 or newer, which supports every command in
[`03-git-workflow.md`](03-git-workflow.md), including `git switch`.

Verify:

```bash
git config --global --list
```

---

## 4. An editor

If you are on a **server with no desktop**, you do not need VS Code. Edit with
`nano` (simple: arrow keys, Ctrl+O to save, Ctrl+X to exit) or `vim` if you
know it:

```bash
sudo dnf install -y nano
```

Better, if you work from a laptop: install **VS Code on the laptop** and use
its **Remote - SSH** extension to edit files on the RHEL machine as if they
were local. Install VS Code from https://code.visualstudio.com/, then install
the extensions **Remote - SSH** and **Python**, press `F1`, choose
**Remote-SSH: Connect to Host**, and enter `yourname@your-rhel-host`.

On a **RHEL desktop**, install VS Code directly:

```bash
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
sudo dnf install -y code
```

---

## 5. Put the project somewhere sensible

```bash
mkdir -p ~/projects
```

Move the unzipped `stableseg` folder into it. If the archive is on your laptop,
copy it across:

```bash
# run this on your LAPTOP, not on the RHEL machine
scp stableseg-phase-1a.zip yourname@your-rhel-host:~/projects/
```

Then on the RHEL machine:

```bash
cd ~/projects
unzip stableseg-phase-1a.zip        # sudo dnf install -y unzip, if missing
cd stableseg
ls
```
Expected: `README.md  configs  docs  pyproject.toml  requirements.lock  src  tests`

**Check your home directory is not on a restricted mount.** Some enterprise
builds mount `/home` with `noexec`, which stops a virtual environment from
running:

```bash
findmnt -no OPTIONS -T ~
```
If the output contains `noexec`, put the project on a normal filesystem
instead, for example `mkdir -p /var/tmp/$USER/projects` and work there. Ask
your administrator which path is intended for user work.

---

## 6. Create the virtual environment

**What it is and why:** a **virtual environment** is a private toolbox for one
project: its own libraries, isolated from the system. On RHEL this is not
optional politeness, it is the rule — installing packages into the system
Python with `sudo pip` can break `dnf` and other system tools.

```bash
python3.12 -m venv .venv
```
No output, about 10 seconds.

Activate it:

```bash
source .venv/bin/activate
python --version
```
Expected: your prompt gains a `(.venv)` prefix, and the version printed is
`Python 3.12.x`.

**Check that version before continuing.** If it is outside 3.12–3.13, stop:
`deactivate`, `rm -rf .venv`, and redo this section naming `python3.12`
explicitly.

> **The rule for the rest of your life with this project:** every new shell
> starts *without* the toolbox. If a command fails with "command not found",
> check for `(.venv)` first. It is the cause nine times out of ten.

To leave: `deactivate`.

**Red Hat's own note, worth repeating:** on RHEL 8, environments for Python
3.11 and 3.12 must be created with `venv` (as above), not with the older
`virtualenv` utility from `python3-virtualenv`, which is not compatible with
them.

---

## 7. Install the project

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -r requirements.lock
```
Downloads roughly 200 MB, 2–5 minutes. Expected final line: `Successfully
installed` and a long list.

```bash
python -m pip install -e . --no-deps
```
Expected: `Successfully installed stableseg-0.1.0`.

**If your machine is behind a corporate proxy**, pip needs to know:

```bash
export HTTPS_PROXY=http://proxy.yourcompany.com:8080
export HTTP_PROXY=http://proxy.yourcompany.com:8080
```
(Add those two lines to `~/.bashrc` to make them permanent.) If your site runs
an internal package mirror instead, ask for its URL and use
`python -m pip install -i https://your-mirror/simple -r requirements.lock`.

---

## 8. Prove it works

```bash
python -c "import stableseg; print(stableseg.__version__)"
```
Expected: `0.1.0`

```bash
pytest -q
```
Expected: `36 passed in 0.6s`.

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
stableseg version
stableseg phantom
stableseg describe data/phantom/images/phantom_000.nii.gz
```

Expected from `stableseg phantom`:
```
{
  "data_root": "/home/yourname/projects/stableseg/data/phantom",
  "n_cases": 8,
  "manifest": ".../manifest.csv",
  "run_dir": ".../runs/phantom-smoke",
  "mean_true_volume_mm3": 2269.75
}
```

**That `2269.75` is the checkpoint.** Identical on RHEL, macOS and Windows,
because the generator is seeded. Seeing it means your install is correct *and*
reproducible.

```bash
ls data/phantom/images
cat runs/phantom-smoke/run.json
```

---

## 9. What could go wrong

| What you see | What it means | Fix |
|---|---|---|
| `bash: python: command not found` | RHEL has no unversioned `python` by design | use `python3.12`, or activate the environment |
| `No match for argument: python3.12` | AppStream not enabled, or RHEL older than 8.6 | see section 2; do not substitute 3.11, its dependencies will not install |
| `ERROR: Package 'stableseg' requires a different Python: 3.x.y not in '<3.14,>=3.12'` | the environment was built on 3.11 or on an unsupported version | `deactivate`, `rm -rf .venv`, redo section 6 naming `python3.12` |
| `Permission denied` running `.venv/bin/python` | the filesystem is mounted `noexec` | `findmnt -no OPTIONS -T ~`; move the project to a normal mount |
| pip tries to compile a package and fails on `Python.h` | development headers missing | `sudo dnf install -y python3.12-devel gcc` |
| pip hangs, then `Connection timed out` | corporate proxy | set `HTTPS_PROXY` / `HTTP_PROXY` (section 7) |
| `SSL: CERTIFICATE_VERIFY_FAILED` | corporate TLS inspection | ask for your organisation's CA bundle and `export PIP_CERT=/path/to/ca-bundle.crt` |
| `command not found: stableseg` | environment not active, or step 7 skipped | check for `(.venv)`; `source .venv/bin/activate`; re-run step 7 |
| `pytest: no tests ran` | wrong folder | `cd ~/projects/stableseg`, check `ls` shows `tests` |
| Something broke `dnf` after a pip install | packages went into the system Python | never use `sudo pip`; always work inside `.venv` |
| `mean_true_volume_mm3` is not 2269.75 | different NumPy version | `python -m pip install -r requirements.lock --force-reinstall` |
| Everything worked yesterday, nothing works today | new shell, environment not active | `cd ~/projects/stableseg && source .venv/bin/activate` |

---

## 10. If you have no `sudo` rights

You can still run the whole project, provided a Python **3.12 or 3.13** exists
on the machine:

```bash
ls /usr/bin/python3.1*
```

If 3.12 or 3.13 is there, use it directly — `venv` needs no root:

```bash
/usr/bin/python3.12 -m venv ~/projects/stableseg/.venv
```

A 3.11 on the list does not help; the pinned scientific packages require 3.12
or newer.

If none exists, ask your administrator to run the one command in section 2. It
installs alongside the system Python and changes nothing else, which is
usually an easy request to get approved. Building Python from source in your
home directory is possible but is a poor use of an afternoon; ask first.

---

## 11. The short loop, from tomorrow onwards

Setup happens once. Every working session afterwards is three lines:

```bash
cd ~/projects/stableseg
source .venv/bin/activate
pytest -q
```

Then edit, run, and commit (see [`03-git-workflow.md`](03-git-workflow.md)).

---

## 12. A note on continuous integration

The automated checks (`.github/workflows/ci.yml`) run on Ubuntu, Windows and
macOS, because those are the runners GitHub hosts; there is no hosted RHEL 8
runner. This guide is the tested RHEL path, and the project uses only
`pathlib` and pure-Python file handling precisely so that "passes on Ubuntu"
means "passes on RHEL". If you hit a RHEL-specific failure, that is a real bug
worth reporting.

---

Next: [`02-architecture.md`](02-architecture.md) — what you just installed and
why every piece exists.
