# 02 · Architecture, Explained From Scratch

[← README](../README.md) · [All docs in order](../README.md#the-tutorial-in-order) · [Glossary](00-glossary.md)

**Prerequisites:** none. This is the first thing to read after the README.
**Learning goal:** after this page you can say what every part of StableSeg does, why it exists, and how a scan travels from a file on disk to a sentence in a report, even if you have never built software before.
**Checkpoint:** you can explain, in your own words, the difference between a *backend*, a *frontend* and a *database*, name the nine boxes in the diagram, and say why the audit engine must not depend on any one segmentation model.

---

## 1. What is StableSeg, in one honest sentence?

StableSeg takes a piece of software that measures a structure in a medical scan, deliberately disturbs the scan in realistic ways, measures again and again, and reports how much the measurement wobbles when the patient has not changed, so that anyone relying on that measurement knows its noise floor before they trust it.

If you know nothing about medicine or software, here is the everyday version:

> You have a bathroom scale and you want to know if it is good enough to track a diet. You step on it fifty times in slightly different ways (left foot first, right foot first, slightly to the side, after moving it to the bathroom mat) and write down every reading. The spread of those readings is the scale's own wobble. If the wobble is two kilograms, the scale cannot tell you about a one-kilogram loss, however precise the display looks. StableSeg does this for a scan-measuring program instead of a scale.

---

## 2. The three words you must know first

Almost every confusing software conversation becomes clear once you know these three. The running analogy is a restaurant.

### Backend: the kitchen
Everything that happens behind the scenes: preparing ingredients, cooking, plating. Customers never enter the kitchen. In software, the backend is the code that does the real work. In StableSeg, the backend loads scans, perturbs them, segments them, measures them and computes statistics. Nobody "sees" it; they see its results.

### Frontend: the dining room
The part a person sits in and interacts with: the menu, the table, the plated dish. In software, the frontend is the screen someone looks at and clicks. StableSeg's frontend (a later phase) is a Streamlit web page where someone picks a perturbation and watches the biomarker move.

### Database: the pantry
An organised store you fetch from precisely, instead of rummaging through bags on the floor. You ask it questions in a language called SQL ("give me every case whose volume changed by more than five percent under motion"). StableSeg's database (phase 4) is a single DuckDB file.

> **Why a database, if we have files?** Because once every measurement lives in one place, the explorer, the report and the statistics all read from one trusted source instead of five slightly different copies. One pantry, not five half-empty cupboards.

---

## 3. A few more terms, defined once

- **Scan / volume.** A 3-D image: a stack of 2-D slices. Stored as a block of numbers plus a header saying how big each voxel is and which way is up.
- **Voxel.** A 3-D pixel. Multiply its three sides to get its volume in cubic millimetres.
- **Segmentation.** Drawing the outline of a structure on every slice. The result is a **mask**: a volume of the same size where each voxel says "inside (1)" or "outside (0)". Real hippocampus data uses 1 for the head and 2 for the body.
- **Biomarker.** A number computed from the mask that stands in for something about the patient. The first one here is volume in mm³.
- **Perturbation.** A deliberate, controlled change to a scan that imitates something real: patient movement, a noisier scanner, a different slice thickness. The scan changes; the patient did not.
- **Repeatability.** How close repeated measurements of the same thing are to each other. The statistics in phase 5 (ICC, wCV, Bland–Altman, repeatability coefficient, minimum detectable change) are different ways of putting a number on it. Each is explained from zero in that phase and in the glossary.
- **Pipeline.** A fixed sequence of steps, like an assembly line. StableSeg's is: load → preprocess → perturb → segment → measure → store → analyse → serve.
- **Artefact.** A saved output file: a table, a chart, a mask. Computed once, reused many times.
- **Provenance.** The record of what produced a result: which code version, which config, when. If a number is questioned, provenance is how you walk it back.

---

## 4. The nine boxes, and why each one exists

```mermaid
flowchart TD
    subgraph LAPTOP["🖥️  YOUR LAPTOP — CPU only, everything runs here"]
        A["1 · Data<br/>MSD hippocampus MRI (real, phase 2)<br/>synthetic phantoms (built in, phase 1)"]
        B["2 · Preprocess<br/>orientation · resample · normalise<br/>denoise? register? (audited, not assumed)"]
        C["3 · Perturbation bank<br/>noise · blur · bias field · motion ·<br/>ghosting · anisotropy · misalignment"]
        D["4 · Segment or import<br/>classical baseline · 3D U-Net (optional extra) ·<br/>masks from external tools"]
        E["5 · Biomarkers<br/>volume · surface area · sphericity<br/>one row per case per perturbation"]
        F[("6 · Store<br/>DuckDB, one file, SQL")]
        G["7 · Repeatability statistics<br/>ICC · wCV · Bland–Altman · RC ·<br/>minimum detectable change · sample size"]
    end
    subgraph SERVE["📊  SERVING — what a stakeholder sees"]
        H["8 · Explorer (Streamlit)"]
        I["9 · Report (Quarto)"]
    end
    X["(later) tool server<br/>other programs call the API"]
    A --> B --> C --> D --> E --> F --> G
    G --> H
    G --> I
    X -.-> G

    classDef laptop fill:#E8F0FE,stroke:#5B8DEF,color:#0B2545;
    classDef store fill:#FFF3CD,stroke:#C9A227,color:#4A3B00;
    classDef serve fill:#E6F4EA,stroke:#4CAF7D,color:#0B3D2E;
    classDef later fill:#F5F5F5,stroke:#B0B0B0,color:#555555,stroke-dasharray:4 3;
    class A,B,C,D,E,G laptop
    class F store
    class H,I serve
    class X later
    style LAPTOP fill:#F5F9FF,stroke:#B9D2FF,color:#0B2545
    style SERVE fill:#F2FBF5,stroke:#B7E4C7,color:#0B3D2E
```

*(Reading this as plain text? Top to bottom: data feeds preprocessing, which feeds the perturbation bank, which feeds segmentation, which feeds measurement, which fills the store; the statistics read the store and feed both the explorer and the report.)*

### Box 1 — Data · *backend*
**What:** the scans and, where available, the expert masks that go with them.
**Why two sources:** the synthetic phantoms (phase 1) have a *known* true volume and generate in seconds on any machine, so the tests and the first end-to-end run need no download and the pipeline can be checked against an answer key. The real MRI (phase 2) is where the audit becomes meaningful.
**Where:** `src/stableseg/phantom.py` today; a NIfTI-folder loader and a DICOM reader in phase 2.

### Box 2 — Preprocess · *backend*
**What:** put every scan into the same orientation, resample to the same voxel size, scale intensities to a common range.
**Why it exists:** a segmenter must see comparable inputs. Two further steps, denoising and rigid registration (re-aligning a moved scan), are treated as *experiments*: the audit runs with and without them and measures whether they reduce the wobble. Most pipelines assume they help; this one checks.

### Box 3 — Perturbation bank · *backend*, the heart of the project
**What:** a set of named, parameterised disturbances, each imitating one real-world cause of scan-to-scan difference. Organised by **modality profile**: the MRI profile today (noise, blur, intensity scaling, bias field, motion, ghosting, anisotropic resampling, small rotation/translation); a CT profile on the roadmap.
**Why it exists:** real repeat scans of the same person are rare in open data. Simulating the causes of difference, one at a time and in combination, is how we ask "which of these hurts the measurement, and how much?"
**Design rule:** the core bank is NumPy/SciPy only, so it runs everywhere. TorchIO (optional extra, phase 6) adds physics-grade k-space motion and ghosting.

### Box 4 — Segment or import · *backend*
**What:** turn a scan into a mask.
**Why three ways:** a classical baseline (threshold + morphology) proves the audit works before any deep learning exists and gives the U-Net something to beat; the MONAI 3D U-Net (optional extra) is the modern segmenter; the import path lets masks produced by *any other tool* be audited without retraining. That last one is what makes StableSeg a tool rather than a demo.
**The rule that makes the whole design work:** the audit engine sees a segmenter as one function, `segment(volume) -> mask`. It does not care what is inside.

### Box 5 — Biomarkers · *backend*
**What:** numbers from masks. Volume first; surface area, sphericity and bounding-box extents follow.
**Why several:** volume is what trials use; shape features move differently under perturbation and tell you *how* a mask went wrong, not just that it did.

### Box 6 — Store · *database*
**What:** one DuckDB file holding a row per case per perturbation per biomarker, plus the run ledger.
**Why:** joins and aggregations in SQL are how the statistics, the explorer and the report all read the same truth. It is also the seam where a clinical-covariates table would be joined later.

### Box 7 — Repeatability statistics · *backend*
**What:** the audit's verdict, in the vocabulary a trialist uses.
**Why each number:** ICC says how much of the total variation is real between-subject difference rather than measurement noise; wCV puts the noise as a percentage of the measurement; Bland–Altman shows whether the error depends on the size of the structure; the repeatability coefficient and the **minimum detectable change** answer "how big must a change be before I believe it?"; the sample-size calculator answers "how many subjects do I need to see a change of *x* percent?" Every formula is written out and unit-tested; an R cross-check confirms the ICC to four decimals.

### Box 8 — Explorer · *frontend*
**What:** a Streamlit page: choose a perturbation, watch the biomarker distribution move; list the cases whose measurement is unreliable; use the sample-size calculator.
**Why:** a stakeholder should not need Python to ask "what if the scanner is noisier?"

### Box 9 — Report · *the record*
**What:** a Quarto document that re-renders itself from the store: methods, figures, tables, the minimum detectable change, the stated limitations.
**Why:** an audit is only useful if there is a document someone can read and file. A dashboard alone is not a record.

### The dotted box — a tool server (roadmap)
Because every capability is a plain function in `api.py`, a small server can expose those functions to other programs. Nothing about it is built today; the API surface is shaped so that adding it later is additive, not a rewrite. Judged in `06-product-and-technology-roadmap.md`.

---

## 5. How the code is layered, and why that is not optional

```
stableseg cli   (cli.py)      ← argument parsing only; prints JSON
      │
      ▼
public API      (api.py)      ← plain functions; typed inputs; dictionary outputs
      │
      ▼
core modules    (config, storage, io, phantom, ...)   ← do the work; know nothing about callers
```

Arrows point down and never up. `cli.py` may import `api.py`; `api.py` may import the core; the core never imports `api` or `cli`. Nothing below `cli.py` prints to the terminal.

Why insist? Because the same engine must serve three callers without changing: a person at a terminal, a script looping over many audits, and later a web app or tool server. If behaviour lived in the CLI, the second and third callers would have to copy it. If it lives in `api.py`, they call it. Every future box in the diagram plugs into `api.py`.

Three more contracts do the same job at other seams:

- **Config** (`config.py`): one validated YAML document describes a run. Any caller that can produce that document can run the engine.
- **Storage** (`storage.py`): results are written through one small interface. A local folder today; swapping in a database or cloud bucket is one new class.
- **Segmenter** (phase 4): `segment(volume) -> mask`. Any tool that honours it can be audited.

---

## 6. The one design rule that makes it reproducible

Data flows **one way** (top to bottom in the diagram) and no step edits its own input. Every random process takes an explicit seed. Every run writes `run.json` with the package version and the full config. Consequence: delete `data/` and `runs/`, rerun, and you get the same numbers on any machine. That property is a baseline expectation in regulated analytics and a habit this project keeps from the first commit.

---

## 7. Where each phase of the build lives

| Phase | Tutorial | Boxes |
|---|---|---|
| 1 | `04-phase-tutorials/phase-01-skeleton.md` | the layering, config, storage, I/O, phantoms (box 1) |
| 2 | `phase-02-real-data.md` | box 1 (MSD + DICOM) |
| 3 | `phase-03-perturbation-bank.md` | box 3 |
| 4 | `phase-04-segment-and-measure.md` | boxes 2, 4, 5, 6 |
| 5 | `phase-05-repeatability-statistics.md` | box 7 |
| 6 | `phase-06-deep-segmenter.md` | box 4 (U-Net), box 3 (TorchIO) |
| 7 | `phase-07-explorer.md` | box 8 |
| 8 | `phase-08-report-and-release.md` | box 9, container, 0.2.0 |

Next: the setup guide for your operating system (`01-setup-windows.md`, `01-setup-macos.md` or `01-setup-rhel8.md`), then `03-git-workflow.md`, then phase 1.
