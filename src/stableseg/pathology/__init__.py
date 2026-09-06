"""Track P: digital pathology.

Everything in this subpackage works on 2-D pictures of stained tissue - tiles
cut from whole-slide images - measured in microns, where Track V works on 3-D
volumes measured in millimetres. The question asked is identical: how much
does a biomarker move when the sample has not changed?

The same layering rule applies here as everywhere in the package: modules in
this folder are core; they never import from `stableseg.api` or
`stableseg.cli`. The API layer imports them.

Phase P1a adds the synthetic H&E phantom. Phase P1 adds real-slide readers
(OpenSlide, OME-TIFF, spatial-transcriptomics tables) behind the optional
`[pathology]` extra, so the core install stays light.
"""
