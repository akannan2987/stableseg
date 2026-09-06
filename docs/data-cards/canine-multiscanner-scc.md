# Data card · Multi-scanner canine cutaneous squamous cell carcinoma

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | P — digital pathology |
| **Source** | Wilm, Fragoso, Bertram et al. (2023); extends the CATCH dataset |
| **Licence** | **CC BY 4.0** |
| **Size** | 220 whole-slide images: 44 samples × 5 scanners, distributed as pyramidal TIFFs downsampled to **4 µm/px** (a few gigabytes) |
| **Download route** | Zenodo record 7418555; the phase P1 script downloads one or two slides and streams tiles from them |
| **Used from** | phase P1 (whole-slide streaming demonstration), P2 (tissue-level scanner variation) |

## What it contains

The same 44 tissue sections scanned on five different commercial slide
scanners, with tissue-class annotations (tumour, epidermis, dermis, subcutis,
bone, cartilage, inflammation/necrosis) transferred across scanners by
registration. Canine skin tumours — veterinary, not human — chosen by the
authors because the same slides could be rescanned freely.

## What this project uses it for

Two things. First, **whole-slide handling**: the project's core audit runs on
tiles so it stays CPU-first, but it must demonstrate reading a real pyramidal
slide and streaming tiles from it, and this is the slide. Second, a **real
test–retest at tissue level**: tissue-fraction biomarkers (tumour area
fraction, stroma fraction) measured on the same section across five scanners.

## What it cannot show

- **Nothing at nuclear resolution.** At 4 µm/px a nucleus is a couple of
  pixels. Nucleus detection, cell phenotyping and cell-graph biomarkers cannot
  be evaluated on this set; PLISM covers that.
- **Veterinary tissue.** Findings are about scanner variation, not about
  human disease.
- **Registered annotations**, so small boundary differences between scanners
  partly reflect registration, and the card's user must remember that.
