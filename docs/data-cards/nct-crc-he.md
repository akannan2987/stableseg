# Data card · NCT-CRC-HE-100K / CRC-VAL-HE-7K (colorectal tissue tiles)

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | P — digital pathology |
| **Source** | Kather, Halama & Marx (2018), Zenodo record 1214456 |
| **Licence** | **CC BY 4.0** |
| **Size** | 100,000 tiles (training set) and 7,180 tiles (validation set, separate patients), 224 × 224 px at 0.5 µm/px, nine tissue classes; a **NONORM** variant of the 100K set without colour normalisation |
| **Download route** | Zenodo (the 7K set is under a gigabyte; the 100K sets are around twelve) or Hugging Face streaming; the phase P1 script takes the 7K set and a seeded subset of NONORM |
| **Used from** | phase P1 (tissue-class tiles), P4 (foundation-model evaluation), P7 (stain-normalisation audit) |

## What it contains

Small H&E tiles from human colorectal cancer sections, each labelled with one
of nine tissue types: adipose, background, debris, lymphocytes, mucus, smooth
muscle, normal mucosa, cancer-associated stroma, tumour epithelium.

**One detail that matters here.** The standard 100K set was colour-normalised
by its authors (Macenko's method) before release, which removes exactly the
stain variation this project studies. The **NONORM** variant keeps the
original staining. The project uses NONORM wherever stain variation is the
question, and says which variant produced each figure.

## What this project uses it for

Tissue-class labels for the classical and foundation-model tissue classifiers;
a large, permissively licensed source of human tumour tiles for the
foundation-model benchmark; and the natural testbed for "does stain
normalisation reduce biomarker variability, and by how much?", because both
normalised and un-normalised versions exist.

## What it cannot show

- **No nucleus outlines**, so cell-level biomarkers are not evaluated here.
- **Tiles, not slides**: no whole-slide context, no spatial statistics beyond
  the tile.
- **One organ.** Colorectal only.
