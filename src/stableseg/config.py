"""Run configuration: one YAML file describes one audit run.

Why a config file at all? Because the same engine must be driven three ways
without changing its code: by a person typing a command, by a script running
many audits in a loop, and later by a service or a tool server. If every
setting lives in one validated document, all three callers speak the same
language, and a run can be reproduced months later by pointing at that file.

Pydantic does the validation. Think of a pydantic model as a form with typed
boxes: if someone writes "eight" in a box that must hold an integer, the form
refuses to submit and says exactly which box is wrong.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class PhantomSpec(BaseModel):
    """Settings for the synthetic phantom generator (the built-in fallback dataset)."""

    n_cases: int = Field(default=8, ge=1, le=500, description="How many phantom subjects to make.")
    shape: tuple[int, int, int] = Field(default=(48, 64, 48), description="Volume size in voxels (x, y, z).")
    spacing_mm: tuple[float, float, float] = Field(
        default=(1.0, 1.0, 1.0), description="Physical size of one voxel in millimetres."
    )
    noise_sd: float = Field(default=0.05, ge=0.0, description="Gaussian noise added to intensities.")
    seed: int = Field(default=42, description="Random seed; same seed, same phantoms, any machine.")

    @field_validator("shape")
    @classmethod
    def _shape_is_reasonable(cls, v: tuple[int, int, int]) -> tuple[int, int, int]:
        if any(s < 16 for s in v):
            raise ValueError("each phantom dimension must be at least 16 voxels")
        return v


class HEPhantomSpec(BaseModel):
    """Settings for the synthetic H&E phantom generator (Track P's built-in dataset).

    Mirrors PhantomSpec. Sizes are given in microns, not pixels, because a
    nucleus has a physical size and the pixel count follows from the mpp.
    """

    n_tiles: int = Field(default=8, ge=1, le=500, description="How many phantom tiles to make.")
    shape: tuple[int, int] = Field(default=(256, 256), description="Tile size in pixels (height, width).")
    mpp: float = Field(default=0.5, gt=0.0, description="Microns per pixel; 0.5 is a 20x scan.")
    n_nuclei: int = Field(default=60, ge=1, le=2000, description="Nuclei drawn per tile.")
    nucleus_radius_um: tuple[float, float] = Field(
        default=(3.0, 6.0), description="Range of nucleus semi-axis, in microns."
    )
    illumination_strength: float = Field(default=0.08, ge=0.0, description="Slow brightness gradient.")
    noise_sd: float = Field(default=0.02, ge=0.0, description="Noise on stain concentrations.")
    seed: int = Field(default=42, description="Random seed; same seed, same tiles, any machine.")

    @field_validator("shape")
    @classmethod
    def _shape_is_reasonable(cls, v: tuple[int, int]) -> tuple[int, int]:
        if any(s < 32 for s in v):
            raise ValueError("each tile dimension must be at least 32 pixels")
        return v


class DataSpec(BaseModel):
    """Where the images come from."""

    source: Literal["phantom", "nifti_folder", "he_phantom"] = Field(
        default="phantom",
        description=(
            "'phantom' generates MRI phantoms; 'nifti_folder' reads real NIfTI files "
            "(this project's images/labels layout or the Decathlon imagesTr/labelsTr layout); "
            "'he_phantom' generates synthetic H&E tiles (Track P)."
        ),
    )
    root: Path = Field(default=Path("data/phantom"), description="Folder holding images/ and labels/.")
    phantom: PhantomSpec = Field(default_factory=PhantomSpec)
    he_phantom: HEPhantomSpec = Field(default_factory=HEPhantomSpec)


class OutputSpec(BaseModel):
    """Where results go."""

    root: Path = Field(default=Path("runs"), description="Every run writes into a subfolder here.")
    run_name: str = Field(default="phantom-smoke", description="Subfolder name for this run.")

    @field_validator("run_name")
    @classmethod
    def _safe_name(cls, v: str) -> str:
        bad = set('/\\:*?"<>| ')
        if any(ch in bad for ch in v):
            raise ValueError("run_name must be a plain folder name (no spaces or path characters)")
        return v


class AuditConfig(BaseModel):
    """The whole run. Later phases add segmenter, perturbation and biomarker sections."""

    name: str = Field(default="stableseg-run", description="Human label for the run.")
    data: DataSpec = Field(default_factory=DataSpec)
    output: OutputSpec = Field(default_factory=OutputSpec)

    @classmethod
    def from_yaml(cls, path: str | Path) -> AuditConfig:
        """Load and validate a YAML config file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return cls.model_validate(raw)

    def to_yaml(self, path: str | Path) -> None:
        """Write the validated config back out (used to freeze a run's settings)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False)
