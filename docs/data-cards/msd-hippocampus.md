# Data card · Medical Segmentation Decathlon — Task04 Hippocampus

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | V — volumetric radiology |
| **Source** | Medical Segmentation Decathlon, Task04 Hippocampus (Simpson et al., 2019; Antonelli et al., 2022) |
| **Licence** | CC BY-SA 4.0 — credit the authors; share derived data under the same terms |
| **Size** | 28.4 MB as a tar archive; 390 T1-weighted MRI volumes in the archive — 260 with expert outlines (`imagesTr`/`labelsTr`) and 130 without (`imagesTs`). The original publication describes 394 / 263; the released archive holds 390 / 260, and the catalogue counts what is actually present. |
| **Resolution** | 1 mm isotropic in every case (observed); shapes range 30–43 × 40–59 × 24–47 voxels, each volume cropped to its own structure |
| **Download route** | `stableseg fetch msd_task04_hippocampus` — the MONAI project's public mirror, MD5 `9d24dba78a72977dbd1d2e110310f31b` verified before unpacking; a mismatch deletes the archive. Registry: `src/stableseg/datasets.py` |
| **Used from** | phase V2 ✅ |

## Observed on first fetch

`hippocampus_001`: 35 × 51 × 35 voxels, 8-bit intensities 2–139; expert
outline volumes 1,324 mm³ (anterior) and 1,624 mm³ (posterior). These are
real measurements from the loaded file, not values from the paper.

## What it contains

Small cropped MRI volumes around the hippocampus — the curved structure deep
in the brain important for memory, which shrinks in diseases such as
Alzheimer's — with expert-drawn outlines of its two parts (anterior and
posterior). Volumes are tiny, so everything trains and runs on an ordinary
processor in minutes.

## What this project uses it for

The real anatomy Track V audits: preprocessing, the MRI perturbation bank,
classical and deep segmentation, volume biomarkers, and the repeatability
statistics. Hippocampal volume is a real trial endpoint, so the audit question
is real rather than invented.

## What it cannot show

- **It is not a test–retest dataset.** Each subject was scanned once. Every
  "repeat scan" in Track V is simulated by the perturbation bank, and the
  README says so wherever a Track V number appears.
- **It carries almost no clinical covariates**, so the case-level joins planned
  for 0.4.0 cannot be demonstrated on it.
- **It is cropped**, so registration to a whole-head template and skull-related
  artefacts are out of scope on this data.

## Honesty note

Models trained here on a few hundred small volumes demonstrate workflow
competence, not clinical performance. The statistics are the contribution;
the segmenter is a component.
