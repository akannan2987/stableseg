# StableSeg 🧠📏🔁

<!-- Cover image goes here once the explorer exists:
[![StableSeg](docs/img/cover_stableseg.png)](docs/img/cover_stableseg.png) -->

**▶ Live explorer — coming with the app phase** · **v0.1.0**
· ![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)
![NIfTI](https://img.shields.io/badge/formats-NIfTI%20%7C%20DICOM-5C6BC0)
![tests](https://img.shields.io/badge/tests-18%20passing-brightgreen?logo=pytest&logoColor=white)
![ci](https://img.shields.io/badge/CI-Windows%20%7C%20macOS%20%7C%20Linux-informational?logo=githubactions&logoColor=white)
![data](https://img.shields.io/badge/data-MSD%20hippocampus%20%2B%20synthetic%20phantoms-6f42c1)
![license](https://img.shields.io/badge/license-MIT-blue)
![status](https://img.shields.io/badge/status-0.1.0%20skeleton%20released-orange)

**How much does a number measured from a medical scan move when the patient
has not changed at all? StableSeg measures that, for segmentation-based
imaging biomarkers, and reports it in the language a clinical trial needs.**

> Every term used anywhere in this repo, medical or technical, is defined in
> plain language in [`docs/00-glossary.md`](docs/00-glossary.md). If a word
> isn't there, that's a documentation bug.

---

## Contents

- [What is an imaging biomarker? (start here)](#what-is-an-imaging-biomarker-start-here)
- [The problem this project tackles](#the-problem-this-project-tackles)
- [How it works](#how-it-works)
- [The data at a glance](#the-data-at-a-glance)
- [Results, phase by phase](#results-phase-by-phase)
- [Build log](#build-log)
- [**The tutorial, in order**](#the-tutorial-in-order)
- [Roadmap](#roadmap)
- [About the data (honesty notes)](#about-the-data-honesty-notes)
- [Repository map](#repository-map)
- [How to run](#how-to-run)
- [How I work on this repo (branch model)](#how-i-work-on-this-repo-branch-model)
- [Why the documentation is so detailed](#why-the-documentation-is-so-detailed)
- [License](#license)

## What is an imaging biomarker? (start here)

Think of a bathroom scale. It gives you a number, and you make decisions on
it: the diet is working, or it isn't. Medicine does the same with scans. A
computer traces the outline of a structure on every slice of an MRI (that
tracing is called **segmentation**), counts the voxels inside (a voxel is a
3-D pixel), multiplies by the voxel size, and reports a volume in cubic
millimetres. That number is an **imaging biomarker**: a measurement from an
image that stands in for something about the patient.

The structure this project starts with is the **hippocampus**, a small,
curved region deep in the brain involved in memory. It shrinks in
neurodegenerative disease, and its volume measured from MRI is used as an
endpoint in clinical trials: if a drug slows the shrinking, the trial can see
it in this number.

Now the question nobody asks about the scale until it matters: **if you step
off and step back on, do you get the same number?** If the scale wobbles by
two kilograms between readings, a one-kilogram loss is invisible. In imaging,
"stepping back on" means the same patient scanned on another day, another
scanner, with slightly different settings, and the software reading a
slightly different picture. StableSeg is the tool that stands on the scale a
few hundred times and tells you how much it wobbles.

## The problem this project tackles

**The pain point.** Segmentation models are reported with an accuracy score
(Dice) that says how well they match a human tracing on one scan. It says
nothing about whether the number is *stable* across scanners, protocols and
days. Trials in neurodegeneration hunt for treatment effects of a few percent
of volume per year. If re-scanning alone shifts the measured volume by five
percent, a three-percent effect can never be seen, and the trial was lost
before it started. Teams usually discover this after the data are in.

**Why it matters.** A biomarker is only useful if a change in the number means
a change in the patient. Knowing the measurement's own noise floor, before
trusting it, is what separates a number you can act on from a number that
looks precise. The engineering world does this routinely for physical
instruments (gauge repeatability studies); the imaging world has the
vocabulary for it (the Quantitative Imaging Biomarkers Alliance publishes it)
but few open, beginner-reproducible examples of actually doing it for a
deep-learning pipeline.

**What StableSeg is.** A measurement-system audit for segmentation-based
biomarkers. It takes a segmentation pipeline (a classical baseline, a trained
3D U-Net, or masks imported from any external tool), applies a bank of
controlled, realistic acquisition perturbations to real hippocampal MRI
(noise, blur, intensity drift, bias field, motion, ghosting, resolution
change, small misalignment), re-runs the pipeline on every perturbed copy,
and reports the biomarker's repeatability as intraclass correlation,
within-subject coefficient of variation, Bland–Altman limits, the
repeatability coefficient, and the **minimum detectable change**: the
smallest real change that can be told apart from measurement noise. A
sample-size calculator turns that number into a study-design answer. Every
step is documented so a complete beginner can rebuild and understand it:
**the repository is the tutorial.**

## How it works

```mermaid
flowchart TD
    subgraph LAPTOP["🖥️ Your laptop, CPU only"]
        A["1 · Data<br/>MSD hippocampus MRI (real)<br/>or synthetic phantoms (built in)"]
        B["2 · Preprocess<br/>orientation · resample · normalise<br/>denoise? register? (audited, not assumed)"]
        C["3 · Perturbation bank<br/>noise · blur · bias field · motion ·<br/>ghosting · anisotropy · misalignment"]
        D["4 · Segment or import<br/>classical baseline · 3D U-Net (optional) ·<br/>masks from external tools"]
        E["5 · Biomarkers<br/>volume · surface · sphericity<br/>per case, per perturbation"]
        F[("6 · Store<br/>DuckDB · one queryable file")]
        G["7 · Repeatability statistics<br/>ICC · wCV · Bland–Altman · RC ·<br/>minimum detectable change · sample size"]
    end
    subgraph SERVE["📊 Serving"]
        H["8 · Explorer (Streamlit)<br/>which perturbations hurt · unreliable cases ·<br/>sample-size calculator"]
        I["9 · Report (Quarto)<br/>the audit record"]
    end
    A --> B --> C --> D --> E --> F --> G
    G --> H
    G --> I

    classDef laptop fill:#E8F0FE,stroke:#5B8DEF,color:#0B2545;
    classDef store fill:#FFF3CD,stroke:#C9A227,color:#4A3B00;
    classDef serve fill:#E6F4EA,stroke:#4CAF7D,color:#0B3D2E;
    class A,B,C,D,E,G laptop
    class F store
    class H,I serve
    style LAPTOP fill:#F5F9FF,stroke:#B9D2FF,color:#0B2545
    style SERVE fill:#F2FBF5,stroke:#B7E4C7,color:#0B3D2E
```

In words: load a scan, make many realistic variants of it, segment every
variant with the same pipeline, measure the biomarker on each, and look at
how much the measurements disagree with each other for the same patient.
That disagreement is the measurement noise. The statistics turn it into a
number a trialist can use.

Design rule that shapes everything: **the audit engine must run with
NumPy, SciPy, scikit-image and SimpleITK alone.** PyTorch, MONAI and TorchIO
are an optional extra (`pip install "stableseg[deep]"`). The audit is
independent of any one segmenter, so it can judge them all.

Full walkthrough: [`docs/02-architecture.md`](docs/02-architecture.md).

## The data at a glance

| Source | What | Status |
|---|---|---|
| **Synthetic phantoms** (built in) | Two-part ellipsoid structures in noisy, slightly uneven "tissue"; known true volumes; fixed seed; ~48×64×48 voxels. Generated by `src/stableseg/phantom.py`. **Synthetic, and labelled as such everywhere.** | ✅ v0.1.0 |
| **Medical Segmentation Decathlon, Task 04 (Hippocampus)** | 394 real T1 MRI volumes, 263 with expert labels (two parts: head and body), about 36 MB, CC-BY-SA 4.0, no account needed. Tiny volumes, so everything runs on a CPU. | ⬜ phase 2 |

![Phantom case 000](docs/img/phantom_case000.png)

*Phantom case 000 at v0.1.0: image, labels, overlay. Not a real scan.*

## Results, phase by phase

*Each phase leaves a visible artefact. One figure per phase appears here with
what it means. Nothing is shown before it exists.*

- **Phase 1 — Skeleton:** ✅ an installable package with a strict layering
  rule (`cli → api → core`), a validated config format, a storage
  abstraction with provenance stamps, geometry-preserving NIfTI I/O, the
  first biomarker (label volume in mm³), a deterministic phantom generator,
  a 4-command CLI, 18 tests that run in under a second with no download, and
  CI on three operating systems. The figure above is its output.
- **Phase 2 — Real data:** *(pending)* the hippocampus MRI lands, with a
  DICOM reader tested on a synthetic series.
- **Phase 3 — Perturbation bank:** *(pending)*
- **Phase 4 — Segment and measure:** *(pending)*
- **Phase 5 — Repeatability statistics:** *(pending)*
- **Phase 6 — Deep segmenter:** *(pending)*
- **Phase 7 — Explorer:** *(pending)*
- **Phase 8 — Report and packaging:** *(pending)*

## Build log

| Phase | Guide | Status |
|---|---|---|
| — | [Glossary — every term in plain words](docs/00-glossary.md) | 🔨 living document |
| 0 | [Setup — Windows](docs/01-setup-windows.md) · [macOS](docs/01-setup-macos.md) · [RHEL 8](docs/01-setup-rhel8.md) | ✅ |
| 0 | [Architecture — how it all fits together](docs/02-architecture.md) | ✅ |
| 0 | [Git workflow — master / beta / develop](docs/03-git-workflow.md) | ✅ |
| 1 | [Skeleton: package, config, storage, phantoms, CLI, tests, CI](docs/04-phase-tutorials/phase-01-skeleton.md) | ✅ |
| 2 | Real data: MSD hippocampus + DICOM reader | ⬜ planned |
| 3 | Perturbation bank (NumPy/SciPy) | ⬜ planned |
| 4 | Segment (classical) and measure (biomarkers) → DuckDB | ⬜ planned |
| 5 | Repeatability statistics + R cross-check | ⬜ planned |
| 6 | Deep segmenter (MONAI 3D U-Net) + TorchIO artefacts | ⬜ planned |
| 7 | The explorer (Streamlit) + sample-size calculator | ⬜ planned |
| 8 | Report (Quarto), container, 0.2.0 | ⬜ planned |
| — | [Roadmap](docs/05-roadmap.md) · [Product and technology roadmap](docs/06-product-and-technology-roadmap.md) | ✅ |

## The tutorial, in order

Everything is taught in `docs/`, written for a complete beginner, with every
term defined and every command shown with its expected output.

| # | Document | What you learn |
|---|---|---|
| 00 | [Glossary](docs/00-glossary.md) | Every term, plain language, with an everyday analogy |
| 01 | [Setup: Windows](docs/01-setup-windows.md) / [macOS](docs/01-setup-macos.md) / [RHEL 8](docs/01-setup-rhel8.md) | Blank machine → working workshop: Python, Git, a virtual environment, the verification habit |
| 02 | [Architecture](docs/02-architecture.md) | Backend / frontend / database in plain words; the nine boxes and why each exists |
| 03 | [Git workflow](docs/03-git-workflow.md) | Save-game for code; the `master`/`beta`/`develop` model step by step |
| 04 | [Phase tutorials](docs/04-phase-tutorials/) | One file per build phase: goal, why, exact steps, checkpoint, what could go wrong, git block |
| 05 | [Roadmap](docs/05-roadmap.md) | What comes after 0.1.0, in order, with reasons |
| 06 | [Product and technology roadmap](docs/06-product-and-technology-roadmap.md) | From a laptop tool to a hosted product: every technology judged, with verdicts and triggers |
| 07 | [Uninstall](docs/07-uninstall.md) | Removing everything cleanly |
| 08 | [Hosting](docs/08-hosting.md) | Every way to put the explorer and report online, compared |
| — | [CLI cookbook](docs/CLI_COOKBOOK.md) | Ready-to-paste commands, from first run to full audit |

## Roadmap

The short version; the reasoned version is
[`docs/05-roadmap.md`](docs/05-roadmap.md).

- **0.2.0** real MRI, perturbation bank, classical segmenter, biomarkers,
  DuckDB store, repeatability statistics with an R cross-check, CT
  perturbation profile, container image.
- **0.3.0** MONAI 3D U-Net as an optional segmenter, TorchIO physics
  artefacts, Streamlit explorer with sample-size calculator, Quarto report,
  import adapters for FreeSurfer/FSL mask exports.
- **0.4.0** tool server exposing the audit to other programs, language-model
  narration of the report grounded in computed numbers, foundation-model
  segmenters as plug-ins, clinical-covariate joins.

## About the data (honesty notes)

- The **phantoms are synthetic**. They exist so the tests run anywhere and so
  the pipeline can be checked against a known truth. They are not scans and
  are labelled `synthetic: true` in every file that contains them.
- The **MSD hippocampus data are real** de-identified MRI, but they contain
  **no repeat scans of the same person**. StableSeg's audit is therefore a
  *simulated* test–retest: the perturbations are realistic and documented, but
  they are not a second visit. That limitation is stated in every report the
  tool produces.
- Any model trained here on a few hundred hippocampi demonstrates workflow
  competence, not clinical performance.

## Repository map

```
stableseg/
├── README.md                      ← you are here
├── CHANGELOG.md                   ← release notes, Keep-a-Changelog format
├── CONTRIBUTING.md                ← branch model, release flow, review norms
├── LICENSE                        ← MIT
├── pyproject.toml                 ← package metadata, dependencies, tool config
├── requirements.lock              ← every dependency pinned to an exact version
├── .env.example                   ← template for local secrets (none needed yet)
├── .gitignore                     ← data/, runs/, .venv/ and friends stay out of git
├── .github/workflows/ci.yml       ← tests on Windows, macOS, Ubuntu on every push
├── configs/
│   └── phantom.yaml               ← a complete run config: generate phantoms
├── src/stableseg/                 ← the package (src layout: importable only when installed)
│   ├── __init__.py                ← version; the layering rule in its docstring
│   ├── config.py                  ← pydantic models: one YAML file = one run
│   ├── storage.py                 ← Storage interface + LocalStorage + run.json provenance
│   ├── io.py                      ← Volume (data + geometry), NIfTI load/save, label volume
│   ├── phantom.py                 ← deterministic synthetic phantom generator
│   ├── api.py                     ← plain functions: the contract every caller uses
│   ├── cli.py                     ← Typer commands: version, describe, phantom, validate-config
│   └── py.typed                   ← marks the package as type-annotated
├── tests/                         ← pytest; no downloads; < 1 s
│   ├── conftest.py                ← shared fixtures (a tiny run config)
│   ├── test_phantom.py            ← determinism, labels, truth = voxels × size
│   ├── test_config.py             ← valid files load, bad values refused
│   ├── test_api_and_storage.py    ← API without the CLI; provenance stamp
│   ├── test_cli.py                ← each command runs and prints JSON
│   └── test_version.py            ← pyproject and package versions agree
├── docs/                          ← the tutorial (the repo IS the tutorial)
│   ├── 00-glossary.md
│   ├── 01-setup-windows.md · 01-setup-macos.md · 01-setup-rhel8.md
│   ├── 02-architecture.md
│   ├── 03-git-workflow.md
│   ├── 04-phase-tutorials/phase-01-skeleton.md   (one file per phase)
│   ├── 05-roadmap.md
│   ├── 06-product-and-technology-roadmap.md
│   ├── 07-uninstall.md · 08-hosting.md · CLI_COOKBOOK.md
│   └── img/                       ← figures used in the docs
├── data/                          ← generated or downloaded; ignored by git
└── runs/                          ← outputs; ignored by git; each run has run.json
```

| Folder | Role |
|---|---|
| `src/stableseg/` | The engine. Layered so that a future web app, service or tool server calls `api.py` and nothing else. |
| `configs/` | Every run is a YAML file here. Reproducing a result means pointing at the same file. |
| `tests/` | The safety net. Grows every phase. |
| `docs/` | The teaching layer. Numbered to match the build order. |
| `data/`, `runs/` | Inputs and outputs. Regenerated by code, never committed. |

## How to run

With Python 3.12 and Git installed (the setup guides cover that from a blank machine):

```bash
git clone https://github.com/akannan2987/stableseg.git
cd stableseg
python -m venv .venv
# Windows PowerShell:   .\.venv\Scripts\Activate.ps1
# macOS / Linux:        source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
pytest -q                                   # expect: 18 passed
stableseg phantom                           # writes data/phantom/ and runs/phantom-smoke/
stableseg describe data/phantom/images/phantom_000.nii.gz
```

Every command's expected output, and what to do if it fails, is in the setup
guide for your OS and in the phase-1 tutorial.

## How I work on this repo (branch model)

Three branches: `master` (released, tagged), `beta` (pre-release mirror) and
`develop` (all work). The default branch is `master`. Each phase ends with one
fixed git block that pushes `develop` and fans it out to `beta` and `master`.
Details, with expected output for every command:
[`docs/03-git-workflow.md`](docs/03-git-workflow.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Why the documentation is so detailed

Two reasons. First, a measurement you cannot reproduce is not a measurement,
and a pipeline a stranger cannot rerun is not reproducible; documentation
quality is part of the science here, not decoration. Second, I am learning
the engineering as I go, and the clearest test of understanding something is
being able to explain it to someone who knows nothing about it. Every phase
tutorial is written to that standard: what, why, exact commands, expected
output, what could go wrong, and a checkpoint before moving on.

## License

MIT. See [`LICENSE`](LICENSE). The MSD dataset is CC-BY-SA 4.0 and is
credited where it is used.
