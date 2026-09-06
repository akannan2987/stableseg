# Data card · PLISM — Pathology Images of Scanners and Mobile phones

[← Data cards](README.md) · [Roadmap](../05-roadmap.md) · [Glossary](../00-glossary.md)

| | |
|---|---|
| **Track** | P — digital pathology |
| **Source** | Ochi, Komura, Onoyama & Ishikawa (2024), *Scientific Data*; registered tile release by Owkin on Hugging Face (`owkin/plism-dataset-tiles`), which registered the original whole-slide images with Elastix |
| **Licence** | **CC BY 4.0** (dataset and the registered release); a Hugging Face account and acceptance of the terms are needed to download |
| **Size** | 3,417 aligned tile groups × 91 scanner–stain combinations = 310,947 tiles of 512 × 512 px at 0.22–0.26 µm/px (40×); the project streams a few hundred groups rather than downloading everything |
| **Download route** | Hugging Face `datasets` with streaming, or the `plismbench` command; the phase P2 script takes a fixed, seeded subset |
| **Used from** | phase P2 (validating the perturbation bank), P4 (foundation-model stability) |

## What it contains

The same tissue — 46 tissue-microarray cores from many organs — stained under
**13 different H&E conditions** and digitised on **7 different slide
scanners**, then registered so that the same field of view is available in
all 91 combinations. In everyday terms: one photograph of the same room taken
with thirteen different lighting set-ups and seven different cameras, all
lined up pixel for pixel.

## What this project uses it for

**The real test–retest for Track P.** This is the only place in the project
where a simulated disturbance can be compared with a real one: the pathology
perturbation bank's stain shifts and scanner colour responses are tuned and
validated against these pairs, and every biomarker's wobble across real
scanners is a number the simulation must be able to reproduce. It is also the
natural bed for the foundation-model stability benchmark, and the harness
records how its biomarker-level metric relates to the embedding-similarity
metric used by the dataset's own benchmark.

## What it cannot show

- **Tissue-microarray cores, not diagnostic slides.** The tissue is small and
  mixed; there is no tumour endpoint, no survival outcome, no patient-level
  clinical variable.
- **No expert outlines.** Repeatability can be measured; accuracy against a
  pathologist's annotation cannot, on this set.
- **Stain conditions include deliberately extreme ones**, and the project
  states which are used.

## Honesty note

A robustness benchmark on this dataset already exists (Owkin's
`plismbench`). StableSeg's harness is deliberately different in its unit of
analysis — the downstream biomarker, expressed as a minimum detectable
change — and cites theirs. Where the two agree, that is evidence; where they
disagree, the disagreement is reported, not hidden.
