# Changelog

All notable changes to StableSeg are recorded here. Unfamiliar terms are
defined in [`docs/00-glossary.md`](docs/00-glossary.md). The format follows
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
- Test suite (36 tests) that needs no download, including checks that the
  declared Python range matches what the pinned dependencies actually require.
- `scripts/preflight.py`: a pre-push safety check for credentials, oversized
  files, force-added ignored paths, absolute home paths and mixed line
  endings, with explicit per-line and per-file escape markers.
- Continuous integration on Windows, macOS and Ubuntu with pinned dependencies.
- Documentation set: `START-HERE.md`, architecture, glossary, per-OS setup
  guides (Windows, macOS, RHEL 8), git workflow and phase tutorials.
- Roadmap (`docs/05-roadmap.md`) stating the build order and the dependency
  reasoning behind it.
- Product and technology roadmap (`docs/06-product-and-technology-roadmap.md`)
  judging nineteen infrastructure options with a verdict and the trigger that
  would change each one.
- CLI cookbook (`docs/CLI_COOKBOOK.md`), hosting comparison (`docs/HOSTING.md`)
  and uninstall guide (`docs/UNINSTALL.md`).

### Notes
- Supported interpreters are **Python 3.12 and 3.13**. The floor comes from
  the pinned `numpy` and `scipy`, which both require 3.12 or newer; the
  ceiling is caution pending verification of the imaging stack on 3.14.
  Continuous integration covers both versions on all three operating systems.
  On macOS and Windows, install 3.13 (python.org no longer ships installers
  for 3.12); on RHEL 8, install 3.12 from AppStream.

[Unreleased]: https://github.com/akannan2987/stableseg/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/akannan2987/stableseg/releases/tag/v0.1.0
