# 05 · Roadmap: what comes after 0.1.0

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md) · [Architecture](02-architecture.md)

**Prerequisites:** none, though [`02-architecture.md`](02-architecture.md) makes
the phase names mean something.
**Learning goal:** after this page you know what is built, what is not, in what
order the rest arrives, and — more useful than the list itself — *why* that
order. Sequencing work is a skill, and this page shows the reasoning rather
than just the outcome.
**Checkpoint:** you can say which phase must come before the deep-learning
segmenter, and why building the app early would have been a mistake.

---

## 1. Why a roadmap is part of the project, not a marketing page

Two reasons, and both are practical.

**It is a promise you can be held to.** A project that says "coming soon" about
everything is unfalsifiable. A project that says "0.2.0 adds real MRI, the
perturbation bank, the classical segmenter and the first repeatability
statistics" can be checked against reality later. Writing it down makes the
work honest.

**It stops you building the wrong thing next.** Everyone's instinct on a
project like this is to build the interesting part first — the neural network,
the dashboard. Both would have been mistakes here, for reasons explained
below. Deciding the order once, in writing, means you do not re-litigate it
every weekend.

Think of it like building a house. The instinct is to choose the kitchen
worktop, because that is the part you can picture. But the foundation, the
frame and the plumbing come first, and each one constrains the next. A roadmap
is the build sequence written down before enthusiasm rearranges it.

---

## 2. Where the project stands: version 0.1.0

**Released.** Everything below works, is tested, and runs on Windows, macOS
and Linux with Python 3.12 or 3.13.

| What exists | Where |
|---|---|
| Installable package with a strict layering rule (`cli → api → core`) | `src/stableseg/` |
| One validated settings file describes one run | `config.py`, `configs/phantom.yaml` |
| Storage layer with a provenance stamp on every run | `storage.py` |
| 3-D image loading that never separates the numbers from their geometry | `io.py` |
| The first biomarker: label volume in cubic millimetres | `io.label_volume_mm3` |
| Deterministic synthetic phantom generator with known true volumes | `phantom.py` |
| Command-line tool: `version`, `describe`, `phantom`, `validate-config` | `cli.py` |
| 38 automated checks, no download needed, under a second | `tests/` |
| Automated checks on 3 operating systems × 2 Python versions | `.github/workflows/ci.yml` |
| Pre-push safety check for credentials, oversized files, private paths | `scripts/preflight.py` |
| The complete beginner tutorial | `docs/` |

**What does not exist yet.** No real scan has been loaded. Nothing has been
perturbed, segmented or measured. There is no statistics module, no app, no
report. Version 0.1.0 is the frame of the house, not the house.

That is deliberate and worth defending: every later phase writes its outputs
through the storage layer, describes itself in the settings file, and is
driven through the same function layer. Building those first means no phase
has to be rewritten when the next one arrives.

---

## 3. The order, and the reason for it

Read this as a dependency chain. Each phase needs the one before it.

```
2 real data ──► 3 perturbations ──► 4 segment & measure ──► 5 statistics
                                            │                      │
                                            │                      ├──► 7 explorer
                                            └──► 6 deep segmenter  └──► 8 report
```

**Why data before perturbations.** You cannot write a realistic disturbance
without a real image to disturb. The phantoms are useful for testing the
machinery, but a noise level that looks plausible on a generated ellipsoid may
be absurd on an actual brain scan. Build the thing you are simulating first.

**Why perturbations before segmentation.** This is the one that surprises
people. The obvious order is "train the model, then test it". But the
perturbation bank is the *contribution* of this project, and the segmenter is
a component it consumes. Building the bank first forces the segmenter to be
pluggable from the start — the audit calls `segment(volume) -> mask` and does
not care what is behind it. Build it the other way round and the audit ends up
welded to one particular model, which is precisely the thing it must not be.

**Why a classical segmenter before a neural network.** Two reasons. First, a
threshold-and-morphology baseline is fifty lines of code with no training, so
the whole pipeline can run end to end weeks before any model exists — and a
pipeline you can run is a pipeline you can debug. Second, it is the honest
comparison: a deep model that cannot beat thresholding on this task has not
earned its complexity. Most projects never check.

**Why statistics before the app.** The app displays the statistics. Building
the display first means guessing at what it will display, then rebuilding it.
More subtly: if the statistics turn out to say something unexpected, the app's
whole shape changes. Let the answer decide the interface.

**Why the report at the end.** A report is a snapshot of finished work. There
is nothing to snapshot yet.

---

## 4. Version 0.2.0 — the audit actually runs

**Goal:** a complete measurement-system audit on real MRI, start to finish, on
a laptop, with no neural network involved.

| Phase | What it adds | Why it matters |
|---|---|---|
| **2 · Real data** | Download and load the Medical Segmentation Decathlon hippocampus set (394 real T1 brain MRI volumes, 263 with expert outlines, about 36 MB, freely licensed). A reader for DICOM, the hospital format, tested against a small generated series so no patient data is needed. Metadata carried through into provenance. | The audit question is only meaningful on real anatomy. DICOM support is what lets the tool meet data as hospitals actually store it. |
| **3 · Perturbation bank** | Named, adjustable disturbances organised by **modality profile**: for MRI — added noise, blur, intensity scaling, smooth brightness drift, small rotation and shift, anisotropic resampling. Each one documented with the real-world cause it imitates. | This is the heart of the project. Without it there is no simulated repeat scan. |
| **4 · Segment and measure** | Preprocessing (orientation, resampling, intensity normalisation), a classical segmenter, biomarker extraction (volume, surface area, sphericity), all written into a single-file database. | Turns images into a table of numbers — the raw material for every statistic that follows. |
| **5 · Repeatability statistics** | The agreement statistics, each implemented explicitly and checked against a worked example: intraclass correlation, within-subject coefficient of variation, Bland–Altman limits, repeatability coefficient, minimum detectable change, bootstrap confidence intervals. Plus the sample-size calculator. An independent cross-check of the intraclass correlation written in R must agree to four decimal places. | The verdict. This is where the project answers its own question. |

**Also in 0.2.0:** a CT perturbation profile, so the modality-aware design is
demonstrated rather than merely claimed; a container image, so the whole
environment can be reproduced anywhere in one command; and `QUERY_COOKBOOK.md`
— tested, explained SQL against the results database, including multi-part
queries, following the same convention as the sibling projects.

**On R and RStudio.** The statistics phase adds an `R/` folder, `renv` for
exact R package versions, and an independent implementation of the agreement
statistics using the established R packages (`irr`, `psych`, `blandr`). The two
implementations must agree to four decimal places. This is not duplicated work
for its own sake: two unrelated implementations agreeing is a far stronger
check on a formula than one careful implementation, and it is a check most
projects skip. RStudio is the natural editor for that side and runs on all
three supported systems. The R side stays optional throughout, so the project
remains fully usable Python-only.

**Honest expectation:** four weekends, and the statistics phase is the hard
one. Not because the formulas are difficult — they are arithmetic — but
because getting the *experimental design* right is subtle. Which cases are
independent? What exactly is being repeated? Those questions decide whether the
numbers mean anything, and no library answers them for you.

---

## 5. Version 0.3.0 — the modern layer

**Goal:** the deep-learning segmenter, the interactive explorer, and the
report.

| Phase | What it adds | Why it matters |
|---|---|---|
| **6 · Deep segmenter** | A 3D U-Net (the standard neural network design for medical image outlining) trained with MONAI, the medical-imaging toolkit. Physics-grade MRI artefacts — simulated patient movement, ghosting, magnetic-field distortion — via TorchIO. Both arrive as an optional add-on, so the audit engine still installs and runs without them. | The comparison the project exists to enable: does the modern model produce a *more stable* measurement than the simple one, not just a more accurate one? |
| **7 · Explorer** | A web page (built with Streamlit, which turns a Python script into an interactive page) where you pick a disturbance and watch the biomarker distribution move, list the cases whose measurement is unreliable, and use the sample-size calculator. | A person who does not write code should be able to ask "what if the scanner were noisier?" |
| **8 · Report and release** | A document that regenerates itself from the database: methods, figures, tables, the minimum detectable change, and the stated limitations. Then the 1.0 release. | An audit that produces no readable record is not an audit. |

**Also in 0.3.0:** import adapters, so outlines exported from other imaging
tools can be audited without retraining anything. That is the step that turns
StableSeg from a demonstration into something another person can point at
their own work.

---

## 6. Version 0.4.0 and beyond — deliberately vaguer

Further out, so stated with less confidence. Each of these is judged properly,
with a verdict and the trigger that would change it, in
[`06-product-and-technology-roadmap.md`](06-product-and-technology-roadmap.md).

- **A tool server**, so other programs can run an audit directly rather than
  through a person typing commands. The function layer was shaped for this
  from the first commit; adding it should be additive, not a rewrite.
- **Plain-language narration** of the report, generated from the computed
  numbers and strictly grounded in them.
- **Foundation-model segmenters** as plug-ins. General-purpose medical
  segmentation models are appearing; the interesting question is not whether
  they are accurate but whether they are *stable*, and this project is exactly
  the instrument for asking that.
- **Real test–retest data.** The honest limitation of everything above is that
  the repeat scans are simulated. Publicly available same-subject repeat
  imaging exists; incorporating it would upgrade the whole result. Any specific
  dataset will be named here only once verified, not assumed.
- **Clinical covariates.** The biomarker table is designed to join to a
  case-level table of subject characteristics. The current dataset ships none,
  which is stated rather than hidden.

---

## 7. What is deliberately *not* planned

A roadmap is more informative for what it excludes. None of these is planned,
and each exclusion has a reason:

- **A hospital-ready product.** Software used for clinical decisions is
  regulated medical-device software, with a quality system, formal validation
  and legal responsibility behind it. This is a research tool, and pretending
  otherwise would be dishonest.
- **A general-purpose segmentation library.** Others do that well. StableSeg
  audits segmenters; it does not compete with them.
- **A cloud service, for now.** Everything runs on a laptop deliberately.
  Cloud infrastructure is judged in the product roadmap, with the specific
  conditions that would justify it.
- **More segmentation targets than the question needs.** Hippocampus first, CT
  second, and only then breadth. A tool that audits one thing well is worth
  more than one that half-audits six.

---

## 8. How to read progress

The README's **Build log** table marks each phase ✅ or ⬜, and the **Results,
phase by phase** section carries one figure per completed phase. Neither shows
anything before it exists. If a phase is marked complete, its tutorial exists
in `docs/04-phase-tutorials/`, its code is in `src/`, and its checks are in
`tests/`.

`CHANGELOG.md` records what changed in each released version, in the order it
happened.

---

## 9. Committing changes to this document

The roadmap is a living document; it changes whenever reality does. Same
procedure as every other change in this project:

```bash
git switch develop
git add -A
git commit -m "docs: update roadmap"
git push origin develop develop:beta develop:master

## --tags is optional, only when required

git switch master
git pull --ff-only origin master
git switch develop
```

---

Next: [`06-product-and-technology-roadmap.md`](06-product-and-technology-roadmap.md)
— what it would take to turn this from a laptop tool into a hosted product,
and an honest verdict on every technology that could be involved.
