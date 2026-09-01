# Changelog

All notable changes to StableSeg are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`, where a new
MINOR adds capability and a new PATCH only fixes things.

## [Unreleased]

Planned for 0.2.0: real hippocampus MRI ingestion, the perturbation bank, the
classical segmenter, biomarker extraction, and the first repeatability
statistics. See `docs/05-roadmap.md`.

## [0.1.0] - 2026-09-01

First public release: a runnable skeleton with the full documentation set.

### Added
- Installable Python package (`src/stableseg`) with a strict layering rule:
  `cli -> api -> core modules`.
- Validated YAML run configuration (`config.py`, pydantic).
- Storage abstraction (`storage.py`) with a local-folder backend and per-run
  provenance stamps (`run.json`).
- Volume I/O with geometry preserved (`io.py`, NIfTI via nibabel), including
  the first biomarker: label volume in cubic millimetres.
- Deterministic synthetic phantom generator (`phantom.py`) writing NIfTI
  images, labels and a manifest with known true volumes.
- Command-line interface: `version`, `describe`, `phantom`, `validate-config`.
- Test suite (17 tests) that needs no download; runs in under a second.
- Continuous integration on Windows, macOS and Ubuntu with pinned dependencies.
- Documentation set: architecture, glossary, per-OS setup guides, git
  workflow, phase tutorials, roadmap, product and technology roadmap,
  uninstall and hosting notes.

[Unreleased]: https://github.com/akannan2987/stableseg/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/akannan2987/stableseg/releases/tag/v0.1.0
