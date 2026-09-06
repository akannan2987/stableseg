# Data card · BCI — paired H&E and HER2 immunohistochemistry

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | P — digital pathology |
| **Source** | Liu et al. (2022), Breast Cancer Immunohistochemical benchmark |
| **Licence** | **non-commercial research use**; the exact wording from the release page is copied into this card by the phase P3 download script before anything is used |
| **Size** | 4,873 registered pairs of 1024 × 1024 px tiles (3,896 train / 977 test) from 51 patients; several gigabytes |
| **Download route** | the authors' release page |
| **Used from** | phase P3 (IHC positivity, H-score), P6 (H&E → IHC multimodal component), P7 (stain translation comparison) |

## What it contains

For each region, an H&E tile and the **consecutive section** stained with
HER2 immunohistochemistry, aligned by registration, with the HER2 score
(0, 1+, 2+, 3+) — the score that decides a breast-cancer treatment.

## What this project uses it for

The IHC biomarkers — percent positive cells and the H-score — and their
stability under the perturbation bank; the paired data for the H&E → IHC
multimodal component; and the reference for the stain-translation comparison.

## What it cannot show

- **Consecutive sections are not the same cells.** The pair is two slices a
  few microns apart, registered; per-cell correspondence is approximate, and
  the multimodal audit says so.
- **One marker, one organ.** HER2 in breast; nothing about other IHC targets.
- **Non-commercial.** Derived outputs inherit the restriction.
