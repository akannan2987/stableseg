# Data card · PanNuke (nucleus instances and classes)

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | P — digital pathology |
| **Source** | Gamper et al. (2019, 2020) |
| **Licence** | **CC BY-NC-SA 4.0 — non-commercial**; credit and share alike |
| **Size** | 7,901 tiles of 256 × 256 px at 0.25 µm/px across 19 tissue types, roughly two gigabytes in three folds |
| **Download route** | the authors' release page; the phase P3 script downloads one fold |
| **Used from** | phase P3 |

## What it contains

H&E tiles with every nucleus outlined and assigned one of five classes:
neoplastic, inflammatory, connective, dead, epithelial. Annotations were
produced semi-automatically and pathologist-checked, which the authors state
and this project repeats.

## What this project uses it for

Ground truth for nucleus detection and segmentation (classical detector versus
Cellpose), and for cell-phenotype counts from H&E alone, so that the
phenotype-density biomarkers have an answer key before they are audited for
stability.

## What it cannot show

- **Non-commercial.** Any figure, model weight or derived table produced from
  PanNuke inherits the restriction; the project marks them.
- **Semi-automatic annotations** carry their own error, which the accuracy
  numbers include.
- **No scanner or stain variation** — it is an accuracy set, not a
  repeatability set.
