"""Reading and writing 3-D volumes with their geometry intact.

A medical image is not just a block of numbers. Each voxel (a 3-D pixel) has
a physical size, and the block has an orientation in space. Lose either and
every volume you compute is wrong. `Volume` carries the numbers AND the
geometry together so no function can accidentally separate them.

NIfTI (.nii / .nii.gz) is the research standard; that is the native format
here. DICOM support (the hospital format) arrives with its own reader in a
later phase, producing the same `Volume`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np


@dataclass
class Volume:
    """A 3-D image plus everything needed to interpret it physically."""

    data: np.ndarray  # shape (x, y, z)
    affine: np.ndarray  # 4x4 matrix mapping voxel indices to world millimetres
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def spacing_mm(self) -> tuple[float, float, float]:
        """Voxel size along each axis, derived from the affine (column lengths)."""
        s = np.sqrt((self.affine[:3, :3] ** 2).sum(axis=0))
        return (float(s[0]), float(s[1]), float(s[2]))

    @property
    def voxel_volume_mm3(self) -> float:
        sx, sy, sz = self.spacing_mm
        return sx * sy * sz

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(int(n) for n in self.data.shape)

    def describe(self) -> dict[str, Any]:
        """A small, JSON-safe summary. Used by the CLI and by tests."""
        d = self.data
        return {
            "shape": list(self.shape),
            "dtype": str(d.dtype),
            "spacing_mm": list(self.spacing_mm),
            "voxel_volume_mm3": self.voxel_volume_mm3,
            "min": float(np.nanmin(d)),
            "max": float(np.nanmax(d)),
            "mean": float(np.nanmean(d)),
            "n_nonzero": int(np.count_nonzero(d)),
        }


def load_volume(path: str | Path) -> Volume:
    """Load a NIfTI file. Data is returned as float32 for images, unchanged for labels.

    `np.asanyarray(img.dataobj)` reads lazily and respects scaling in the header.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    img = nib.load(str(path))
    data = np.asanyarray(img.dataobj)
    if data.ndim == 4 and data.shape[-1] == 1:  # some tools save a trailing channel
        data = data[..., 0]
    if data.ndim != 3:
        raise ValueError(f"expected a 3-D volume, got shape {data.shape} in {path.name}")
    meta = {"source": str(path), "header_dtype": str(img.get_data_dtype())}
    return Volume(data=data, affine=np.asarray(img.affine, dtype=np.float64), meta=meta)


def save_volume(vol: Volume, path: str | Path, dtype: np.dtype | type | None = None) -> Path:
    """Write a NIfTI file, creating parent folders. Returns the path written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = vol.data if dtype is None else vol.data.astype(dtype)
    img = nib.Nifti1Image(data, vol.affine)
    nib.save(img, str(path))
    return path


def label_volume_mm3(label: Volume, label_value: int = 1) -> float:
    """Physical volume of one label in cubic millimetres: count the voxels, multiply by voxel size.

    This is the simplest imaging biomarker there is, and the one this whole
    project audits.
    """
    n = int(np.count_nonzero(label.data == label_value))
    return n * label.voxel_volume_mm3
