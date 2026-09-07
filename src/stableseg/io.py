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

from stableseg.image import ImageBase


@dataclass
class Volume(ImageBase):
    """A 3-D image plus everything needed to interpret it physically.

    Inherits the project-wide geometry contract from `ImageBase`; `spacing_mm`
    and `describe()` are unchanged, and `spacing`/`unit` expose the same facts
    in the shared vocabulary a Track P `Tile` also speaks.
    """

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

    # -- the shared contract (ImageBase) --
    @property
    def unit(self) -> str:
        return "mm"

    @property
    def spacing(self) -> tuple[float, float, float]:
        return self.spacing_mm

    @property
    def is_synthetic(self) -> bool:
        return bool(self.meta.get("synthetic", False))

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


# --------------------------------------------------------------------------
# Cataloguing a folder of scans
# --------------------------------------------------------------------------


def scan_dataset_folder(root: str | Path, read_geometry: bool = True):
    """Catalogue a folder of NIfTI scans into one table: one row per case.

    Two folder layouts are understood, because both occur in practice:

    - `images/` + `labels/`            - this project's phantom layout
    - `imagesTr/` + `labelsTr/` + `imagesTs/` - the Medical Segmentation
      Decathlon layout ("Tr" = training, with expert outlines; "Ts" = test,
      images only)

    Images and labels are paired by identical filename, which is the
    convention every public imaging dataset this project touches follows.
    A case without a label is kept (with `label` empty), because unlabelled
    scans are still scans the audit can perturb and measure.

    With `read_geometry=True` each file's header is opened to record its shape
    and voxel spacing - cheap (headers only), and the single most useful
    sanity check on a new dataset: a spacing that is not what you expected is
    the first thing to find out, not the last.
    """
    import pandas as pd

    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(root)

    layouts = [("images", "labels"), ("imagesTr", "labelsTr")]
    img_dir = lbl_dir = None
    for img_name, lbl_name in layouts:
        if (root / img_name).is_dir():
            img_dir, lbl_dir = root / img_name, root / lbl_name
            break
    if img_dir is None:
        raise ValueError(f"{root} has neither images/ nor imagesTr/; is this the dataset root?")

    def is_scan(p: Path) -> bool:
        # Skip Mac resource-fork companions (._name) that ride along in some archives.
        return p.name.endswith((".nii", ".nii.gz")) and not p.name.startswith("._")

    rows = []
    for img in sorted(p for p in img_dir.iterdir() if is_scan(p)):
        case_id = img.name.removesuffix(".nii.gz").removesuffix(".nii")
        lbl = lbl_dir / img.name if lbl_dir.is_dir() and (lbl_dir / img.name).exists() else None
        row: dict = {
            "case_id": case_id,
            "image": str(img),
            "label": str(lbl) if lbl else "",
            "split": "train" if img_dir.name in ("images", "imagesTr") else "test",
        }
        if read_geometry:
            hdr = nib.load(str(img))
            shape = hdr.shape[:3]
            zooms = hdr.header.get_zooms()[:3]
            row.update(
                {
                    "shape_x": int(shape[0]),
                    "shape_y": int(shape[1]),
                    "shape_z": int(shape[2]),
                    "spacing_x_mm": float(zooms[0]),
                    "spacing_y_mm": float(zooms[1]),
                    "spacing_z_mm": float(zooms[2]),
                }
            )
        rows.append(row)

    # Test images (MSD layout), catalogued without labels.
    ts_dir = root / "imagesTs"
    if ts_dir.is_dir():
        for img in sorted(p for p in ts_dir.iterdir() if is_scan(p)):
            row = {
                "case_id": img.name.removesuffix(".nii.gz").removesuffix(".nii"),
                "image": str(img),
                "label": "",
                "split": "test",
            }
            if read_geometry:
                hdr = nib.load(str(img))
                shape, zooms = hdr.shape[:3], hdr.header.get_zooms()[:3]
                row.update(
                    {
                        "shape_x": int(shape[0]),
                        "shape_y": int(shape[1]),
                        "shape_z": int(shape[2]),
                        "spacing_x_mm": float(zooms[0]),
                        "spacing_y_mm": float(zooms[1]),
                        "spacing_z_mm": float(zooms[2]),
                    }
                )
            rows.append(row)

    return pd.DataFrame(rows)
