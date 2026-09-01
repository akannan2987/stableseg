# Phase 1 · The Skeleton: package, config, storage, phantoms, CLI, tests, CI

[← README](../../README.md) · [All docs in order](../../README.md#the-tutorial-in-order) · [Glossary](../00-glossary.md) · [Architecture](../02-architecture.md)

**Prerequisites:** your OS setup guide completed (Python 3.12, Git, VS Code, a virtual environment that activates), and `03-git-workflow.md` sections 1–3.
**Learning goal:** after this phase you understand what an installable Python package is and why the code lives in `src/`; what a validated config is and why every run is a file; what a storage abstraction buys you; how a 3-D image carries its geometry; how a deterministic generator works; how a command-line tool wraps plain functions; what a unit test is; and what continuous integration does on every push.
**Time:** about 2 hours reading and typing, split into three sessions of 40 minutes if needed. Each section ends at a point where everything still works.
**Checkpoint:** `pytest -q` prints `18 passed`; `stableseg phantom` writes eight phantom files and a `run.json`; the CI badge on GitHub turns green on all three operating systems.

---

## 0. What we are building in this phase, and why first

Nothing in this phase measures a hippocampus. It builds the frame that every later phase hangs on:

- a **package** so the code can be installed and imported from anywhere;
- a **config** format so a run is a file, not a memory;
- a **storage** layer so results have one home and one provenance stamp;
- **volume I/O** that never separates the numbers from their geometry;
- a **phantom generator** so tests and first runs need no download;
- a **CLI** so a person can drive it, and an **API** so a program can;
- **tests** so being wrong is cheap;
- **CI** so "works on my machine" becomes "works on three operating systems".

Doing this first, before any science, is how professionals avoid rebuilding a project halfway through. The order of the rest of the file follows the order in which the pieces depend on each other.

Every file discussed below exists in the repository. Read this tutorial with the file open beside it.

---

## 1. Session A: the package (`pyproject.toml`, `src/stableseg/__init__.py`)

### 1.1 What a package is

A Python **package** is a folder of `.py` files that Python can import by name from anywhere once it is *installed*. Without installing, `import stableseg` only works if you happen to be standing in the right folder; with installing, it works from any folder, in tests, in a web app, in a notebook.

### 1.2 Why the code is under `src/`

Look at the tree: the code is in `src/stableseg/`, not in `stableseg/` at the top. This is the **src layout**. Its purpose is subtle and important: with the code one level down, Python *cannot* accidentally import it from the repository root. The tests are therefore forced to use the installed package, which is exactly what a user gets. Projects that skip this get tests that pass locally and fail after `pip install`.

### 1.3 Read `pyproject.toml`

Open it. Each section:

- `[project]`: name, version, description, the Python versions supported (`>=3.11,<3.13`: 3.13 is not yet safe for the imaging libraries; 3.10 lacks `tomllib`, which a test uses), and the **dependencies**: libraries the code imports. Only the core stack is listed. This is deliberate: the audit engine must run without PyTorch.
- `[project.optional-dependencies]`: three named bundles a user can add: `deep` (PyTorch, MONAI, TorchIO), `app` (Streamlit, Plotly), `dev` (pytest, ruff). `pip install -e ".[dev]"` installs the core plus the dev bundle.
- `[project.scripts]`: `stableseg = "stableseg.cli:app"` tells pip to create a command named `stableseg` that runs the `app` object in `cli.py`. That is how typing `stableseg version` works.
- `[tool.setuptools.packages.find] where = ["src"]`: the src layout, declared.
- `[tool.pytest.ini_options]` and `[tool.ruff]`: settings for the test runner and the linter, so every machine uses the same ones.

### 1.4 Install it in editable mode

In the activated virtual environment, from the repository root:

```bash
python -m pip install -e ".[dev]"
```

`-e` (editable) means pip links to your `src/` folder instead of copying it, so edits take effect immediately without reinstalling. Expected last line: `Successfully installed stableseg-0.1.0 ...` (plus dependencies on first run; that can take a couple of minutes because SimpleITK and scikit-image are large).

Verify:

```bash
python -c "import stableseg; print(stableseg.__version__)"
```
Expected: `0.1.0`

### 1.5 `__init__.py`

The file that makes a folder a package. Ours holds the version string and, in its docstring, the one rule the whole project obeys: `cli → api → core`, arrows only pointing down. Read the docstring; it is the shortest possible statement of the architecture.

**What could go wrong**

| Symptom | Cause | Fix |
|---|---|---|
| `No module named stableseg` | virtual environment not active, or install skipped | activate (`source .venv/bin/activate` / `.\.venv\Scripts\Activate.ps1`), reinstall |
| `pip` installs into the system Python | same | `which python` (macOS/Linux) or `Get-Command python` (Windows) must point inside `.venv` |
| `error: Microsoft Visual C++ 14.0 is required` on Windows | a dependency tried to compile from source | you are on an old Python or a 32-bit one; use 64-bit Python 3.12 so binary wheels are found |

---

## 2. Session A: the config (`config.py`, `configs/phantom.yaml`)

### 2.1 Why a run is a file

You will run this engine hundreds of times with different settings. If the settings live in your head or in command-line flags, you cannot reproduce a run from three weeks ago. If they live in a file, reproducing a run is pointing at the file. And any *program* that can write that file can drive the engine. This is the first of three contracts (config, storage, segmenter) that make the design reusable.

### 2.2 What pydantic does

`config.py` describes the file's shape with **pydantic models**: Python classes whose attributes have types, defaults, descriptions and rules. Think of a form with typed boxes. If a YAML file says `n_cases: eight`, pydantic refuses with a message naming the box:

```
1 validation error for AuditConfig
data.phantom.n_cases
  Input should be a valid integer, unable to parse string as an integer
```

Read the four classes: `PhantomSpec` (how to generate phantoms), `DataSpec` (where data comes from), `OutputSpec` (where results go), and `AuditConfig`, which nests them and adds `from_yaml` / `to_yaml`. The two `@field_validator` functions are custom rules: a phantom dimension under 16 voxels is refused; a run name with spaces or slashes is refused (it becomes a folder name).

### 2.3 Try it

```bash
stableseg validate-config configs/phantom.yaml
```
Expected: JSON starting with `"valid": true` and echoing the config with every default filled in. This is a useful habit: validate before running.

Now break it on purpose. Edit `configs/phantom.yaml`, set `n_cases: 0`, run the same command. Expected: a `ValidationError` naming `data.phantom.n_cases` and the rule (`greater than or equal to 1`). Put it back to 8.

### 2.4 Two ways to do the same thing

Everything in this project can be done from a script *and* from the CLI. From Python:

```python
from stableseg.config import AuditConfig
cfg = AuditConfig.from_yaml("configs/phantom.yaml")
print(cfg.data.phantom.n_cases)      # 8
print(cfg.model_dump(mode="json"))   # the whole validated document as a dict
```

Run that in `python` interactively or save it as `scratch.py` and run `python scratch.py`. The CLI command above does exactly this plus `json.dumps`.

---

## 3. Session B: storage and provenance (`storage.py`)

### 3.1 The problem it solves

Every phase writes results: masks, tables, statistics, figures. If each function opens files wherever it likes, you end up with outputs scattered across the disk and no record of which code produced which file. Two rules fix that:

1. All outputs go through one small **interface**, `Storage`, scoped to one run folder.
2. Every run writes `run.json` first: package version, timestamp, full config.

### 3.2 Interface versus implementation

`Storage` is an *abstract base class*: it lists the methods (`path`, `write_json`, `read_json`, `exists`, `list`) without implementing them. `LocalStorage` implements them for a folder on disk. Later, an object-store or database backend implements the same five methods, and *no other code changes*. This is what "storage abstraction" means in the roadmap.

### 3.3 Try it

```python
from stableseg.storage import LocalStorage, stamp_run
s = LocalStorage("runs", "scratch")
stamp_run(s, {"note": "trying storage"})
print(s.list())                 # ['run.json']
print(s.read_json("run.json")["stableseg_version"])   # 0.1.0
```

Look at `runs/scratch/run.json` in VS Code. That file is the answer to "what produced this folder?". Delete `runs/scratch/` afterwards; `runs/` is ignored by git anyway.

---

## 4. Session B: volumes with their geometry (`io.py`)

### 4.1 Why geometry travels with the numbers

A scan is a block of numbers, say 48 × 64 × 48 of them. On its own that block has no size: are the voxels 1 mm or 3 mm? The **affine** is a 4 × 4 matrix in the file header that maps voxel indices to millimetres in the scanner's coordinate system; its columns encode voxel size and orientation. Lose it and every volume you compute is wrong by an unknown factor. So `Volume` is a small class that holds `data` and `affine` together, and derives `spacing_mm` and `voxel_volume_mm3` from the affine rather than trusting a separate number.

### 4.2 The first biomarker

`label_volume_mm3(label, 1)` counts voxels equal to 1 and multiplies by the voxel volume. That is the whole biomarker the project audits: nothing more sophisticated is needed for the question to be hard.

### 4.3 Try it

```bash
stableseg describe data/phantom/images/phantom_000.nii.gz
```
(If `data/phantom/` does not exist yet, run `stableseg phantom` first; section 5.) Expected: JSON with `"shape": [48, 64, 48]`, `"spacing_mm": [1.0, 1.0, 1.0]`, `"voxel_volume_mm3": 1.0`, and intensity min/max/mean.

From Python:

```python
from stableseg.io import load_volume, label_volume_mm3
lbl = load_volume("data/phantom/labels/phantom_000.nii.gz")
print(lbl.spacing_mm, label_volume_mm3(lbl, 1), label_volume_mm3(lbl, 2))
```

Open `data/phantom/manifest.csv`: the two volumes you just printed appear in the row for `phantom_000`. The saved file and the generator's truth agree; test `test_dataset_roundtrip` checks exactly this.

---

## 5. Session B: the phantom generator (`phantom.py`)

### 5.1 Why synthetic data, and why it is disclosed

Three reasons, all stated in the module docstring: tests must run anywhere in seconds; a phantom has a *known* true volume, which real scans never do; and the same seed regenerates the same phantoms on every machine. The phantoms are labelled `synthetic: true` in their metadata and in the manifest, and every document calls them synthetic. They are a fixture, not a claim.

### 5.2 How determinism works

`np.random.default_rng([seed, case_index])` creates a random-number generator seeded by *both* the run seed and the case number. Case 3 with seed 42 is the same on your laptop and on the CI runner, and case 3 differs from case 4. This is the pattern used everywhere in the project: no global random state, an explicit seed at every call.

### 5.3 What a phantom looks like

Read `make_phantom_case`. A dim background at intensity 0.40; a brighter structure at 0.75 built from two touching ellipsoids: a round "head" (label 1) and an elongated "body" (label 2), mirroring the two-part labelling of the real hippocampus data; a subject-specific size (±20 %) and position jitter; a smooth multiplicative intensity gradient standing in for an MRI bias field; Gaussian noise. `_ellipsoid_mask` is the one piece of geometry: a voxel is inside an ellipsoid when the sum of its squared normalised distances from the centre is at most 1.

### 5.4 Run it

```bash
stableseg phantom --config configs/phantom.yaml
```
Expected:
```
{
  "data_root": ".../data/phantom",
  "n_cases": 8,
  "manifest": ".../data/phantom/manifest.csv",
  "run_dir": ".../runs/phantom-smoke",
  "mean_true_volume_mm3": 2269.75
}
```
The mean true volume is the same on every machine. If yours differs, something in NumPy's random stream changed; note the NumPy version and tell me in an issue.

Look at the output: `data/phantom/images/` and `labels/` hold eight `.nii.gz` files each; `runs/phantom-smoke/run.json` records the run.

### 5.5 See it

The figure in the README (`docs/img/phantom_case000.png`) was made from case 000 with matplotlib. To view a phantom interactively, install 3D Slicer (free; your setup guide, optional section), open `File → Add Data`, choose the image and the label, tick "LabelMap" for the label. Scroll through slices. This is the same viewer the real MRI will be checked in.

---

## 6. Session C: the API and the CLI (`api.py`, `cli.py`)

### 6.1 The layering, applied

`api.py` holds three plain functions: `version()`, `describe_volume(path)`, `generate_phantoms(config)`. Each takes typed inputs and returns a dictionary. `cli.py` holds four commands; each is one line of argument parsing plus one API call plus `json.dumps`. That is the entire relationship: the CLI adds nothing. When the explorer, the report, or a tool server arrive, they call `api.py` the same way.

### 6.2 Typer

Typer turns a Python function into a command by reading its signature: a parameter with a default becomes an option (`--config`), one without becomes a required argument. `exists=True` on a `Path` makes Typer check the file exists before the function runs, so a typo produces a clean message instead of a traceback.

```bash
stableseg --help
stableseg phantom --help
```
Read both. Every option's help text comes straight from the code.

---

## 7. Session C: tests (`tests/`)

### 7.1 What a unit test is

A tiny program that runs a piece of your code with a known input and asserts the output is what you claim. `pytest` finds every function named `test_*` in every file named `test_*.py`, runs them, and reports. A failing test tells you *what* broke and *where* before a user does.

### 7.2 Read the six files

- `conftest.py`: a shared **fixture**, `small_config`, a tiny two-phantom run in pytest's throwaway `tmp_path`, so every test that needs data gets fresh data and leaves nothing behind.
- `test_phantom.py`: determinism (same seed, identical arrays; different seed, different arrays), labels are exactly {0, 1, 2}, truth equals voxel count × voxel size, and a save/load roundtrip agrees with the manifest.
- `test_config.py`: defaults are valid, YAML roundtrips, the repository's own config loads, a tiny shape is refused, an unsafe run name is refused.
- `test_api_and_storage.py`: the API works without the CLI; the provenance stamp records version and config; `LocalStorage` stays inside its run folder.
- `test_cli.py`: every command exits 0 and prints JSON, using Typer's `CliRunner` so no subprocess is needed.
- `test_version.py`: `pyproject.toml` and `__init__.py` agree on the version; the release checklist made enforceable.

### 7.3 Run them

```bash
pytest -q
```
Expected: `18 passed in 0.5s` (time varies). `-q` is quiet; drop it to see each test's name. `pytest -q --cov=stableseg --cov-report=term-missing` adds a coverage table: which lines the tests exercised.

Break something on purpose: in `phantom.py`, change `label[head] = 1` to `label[head] = 3`. Run `pytest -q`. Expected: `test_labels_are_1_and_2_and_non_empty` fails with `assert {0, 2, 3} == {0, 1, 2}`. Put it back. That is the safety net doing its job.

### 7.4 The linter and formatter

```bash
ruff format src tests
ruff check .
```
`ruff format` rewrites files to one consistent style (line length 110, import order). `ruff check` finds unused imports, likely bugs, and outdated syntax. Both must be clean before a commit; CI runs both.

---

## 8. Session C: continuous integration (`.github/workflows/ci.yml`)

### 8.1 What CI is

Every time you push, GitHub starts three fresh virtual machines (Ubuntu, Windows, macOS), installs the project from `requirements.lock`, runs the linter, the formatter check, the tests, and a smoke run of the CLI. If anything fails on any machine, the commit gets a red ✗ and you get an email. "Works on my machine" becomes "works on three machines I do not own".

### 8.2 Read the workflow file

- `on:` — which events trigger it: pushes and pull requests to the three branches, and version tags.
- `strategy.matrix` — the three operating systems; `fail-fast: false` so a Windows failure does not cancel the macOS run and hide a second problem.
- `Install (pinned)` — `requirements.lock` first, then the package with `--no-deps`, so CI uses exactly the versions you tested with.
- The four check steps.

There is no hosted RHEL 8 runner; the Ubuntu job covers Linux and `01-setup-rhel8.md` is the tested RHEL path. This is stated in the file itself.

### 8.3 The lock file

`requirements.lock` is `pip freeze` from a working environment: every library, exact version. `pyproject.toml` says what the project *allows*; the lock says what was *tested*. Regenerate it when you deliberately upgrade something:

```bash
python -m pip install -e ".[dev]"
python -m pip freeze --exclude-editable > requirements.lock
```

---

## 9. Checkpoint

You are done with phase 1 when all of these are true:

- [ ] `python -c "import stableseg; print(stableseg.__version__)"` prints `0.1.0`
- [ ] `stableseg validate-config configs/phantom.yaml` prints `"valid": true`
- [ ] `stableseg phantom` prints `"mean_true_volume_mm3": 2269.75`
- [ ] `stableseg describe data/phantom/images/phantom_000.nii.gz` prints shape `[48, 64, 48]`
- [ ] `ruff check .` prints `All checks passed!` and `ruff format --check src tests` prints `... already formatted`
- [ ] `pytest -q` prints `18 passed`
- [ ] after the git block below, GitHub's Actions tab shows three green jobs

---

## 10. What could go wrong (phase-wide)

| Symptom | Likely cause | Fix |
|---|---|---|
| `stableseg: command not found` | the virtual environment is not active, or the package was installed into another Python | activate; `python -m pip install -e ".[dev]"`; on Windows, close and reopen the terminal after activating for the first time |
| `PermissionError` writing `data/` | the folder is on a synced drive (OneDrive, iCloud) that locks files | move the project to a plain local folder, e.g. `~/projects` |
| Tests pass locally, fail on Windows CI with a path error | a string path with `/` slipped in | use `pathlib.Path` everywhere; `Path("a") / "b"` works on all systems |
| `ruff format --check` fails in CI but not locally | different ruff versions | install from `requirements.lock`; do not `pip install ruff` separately |
| Different `mean_true_volume_mm3` than 2269.75 | a different NumPy major version changed the random stream | check `pip show numpy` against `requirements.lock`; reinstall from the lock |
| CI cannot find `requirements.lock` | file not committed | `git status`; `git add requirements.lock` |

---

## 11. Commit the phase

```bash
git switch develop
git add -A
git commit -m "phase 1: skeleton, config, storage, NIfTI I/O, phantom generator, CLI, tests, CI, docs"
git push origin develop develop:beta develop:master
# add --tags only when a release tag was created in this phase
git switch master
git pull --ff-only origin master
git switch develop
```

Then open the repository on GitHub, click **Actions**, and watch three jobs turn green. That green is the end of phase 1.

Next: [`phase-02-real-data.md`](phase-02-real-data.md) (arrives with 0.2.0), where the real hippocampus MRI lands.
