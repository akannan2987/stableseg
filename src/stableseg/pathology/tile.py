"""The Tile: a 2-D pathology picture that never forgets its physical size.

Track V has `Volume`: an array of voxels welded to the physical size of one
voxel, so a count can always be turned into a volume and never into the wrong
one. `Tile` is the same idea for pathology.

The geometry that matters here:

- **microns per pixel (mpp)** - the physical width of one pixel. A nucleus 40
  pixels across is 10 um at 0.25 mpp and 20 um at 0.5 mpp: a fourfold error in
  area from one forgotten number. This is the pathology voxel spacing.
- **channels** - what each colour plane means. For an H&E picture they are
  red, green and blue; for multiplex immunofluorescence they are marker names.
  Losing the channel names is losing which protein is which.
- **level** - which rung of the image pyramid the tile came from (0 = full
  resolution). The mpp already encodes the consequence, but the level is kept
  because readers ask for it.

Phase P1 generalises `Volume` and `Tile` under one base (`image.py`) so that
a 3-D volume, an RGB tile and a multichannel stack share the rule "numbers
and geometry travel together". Until then `Tile` stands alone and mirrors
`Volume` deliberately, so that unification is a rename rather than a rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Tile:
    """A 2-D image (H, W, C) with its physical geometry attached.

    `data` is height x width x channels. Dtype is whatever the source gives:
    uint8 for RGB pictures, float32 for optical-density or fluorescence
    intensities, int32 for label maps.
    """

    data: np.ndarray
    mpp: float  # microns per pixel, isotropic (square pixels)
    channels: tuple[str, ...] = ("R", "G", "B")
    level: int = 0
    synthetic: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.data.ndim == 2:
            # A single-channel image is still (H, W, 1) in this project, so
            # every function can assume three axes and never guess.
            object.__setattr__(self, "data", self.data[:, :, None])
        if self.data.ndim != 3:
            raise ValueError(f"Tile.data must be (H, W, C); got shape {self.data.shape}")
        if self.data.shape[2] != len(self.channels):
            raise ValueError(
                f"{self.data.shape[2]} channel planes but {len(self.channels)} channel names {self.channels}"
            )
        if not self.mpp > 0:
            raise ValueError("mpp must be a positive number of microns per pixel")

    # ---- geometry ----------------------------------------------------------
    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(int(s) for s in self.data.shape)  # type: ignore[return-value]

    @property
    def pixel_area_um2(self) -> float:
        """Physical area of one pixel in square microns - the number that turns counts into areas."""
        return float(self.mpp * self.mpp)

    @property
    def field_um(self) -> tuple[float, float]:
        """Physical width and height of the whole tile in microns."""
        h, w = self.data.shape[:2]
        return (float(w * self.mpp), float(h * self.mpp))

    def describe(self) -> dict[str, Any]:
        """A JSON-friendly summary: the same shape `Volume.describe()` returns."""
        d = self.data
        return {
            "shape": list(self.shape),
            "dtype": str(d.dtype),
            "mpp": self.mpp,
            "pixel_area_um2": self.pixel_area_um2,
            "field_um": list(self.field_um),
            "channels": list(self.channels),
            "level": self.level,
            "synthetic": self.synthetic,
            "min": float(d.min()),
            "max": float(d.max()),
            "mean": float(d.mean()),
        }


def save_tile(tile: Tile, path: str | Path) -> Path:
    """Write an RGB or single-channel uint8 tile as PNG, with the geometry as a sidecar.

    PNG is lossless, so what is written is exactly what is read back - the
    property every reproducibility check relies on. JPEG would silently
    change pixel values, which is precisely one of the disturbances phase P2
    will *deliberately* apply, and therefore must never happen by accident.

    The geometry (mpp, channels, level, synthetic flag) goes into a small JSON
    file beside the image, because PNG has no standard slot for microns per
    pixel. Phase P1 adds OME-TIFF, which carries geometry inside the file.
    """
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = tile.data
    if arr.dtype != np.uint8:
        raise ValueError("save_tile writes uint8 pictures; convert intensities first")
    if arr.shape[2] == 1:
        Image.fromarray(arr[:, :, 0], mode="L").save(path)
    elif arr.shape[2] == 3:
        Image.fromarray(arr, mode="RGB").save(path)
    else:
        raise ValueError("PNG holds 1 or 3 channels; multichannel tiles are written as OME-TIFF in phase P1")
    sidecar = {
        "mpp": tile.mpp,
        "channels": list(tile.channels),
        "level": tile.level,
        "synthetic": tile.synthetic,
        **tile.meta,
    }
    path.with_suffix(".json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return path


def load_tile(path: str | Path) -> Tile:
    """Read a PNG written by `save_tile`, restoring its geometry from the sidecar."""
    import json

    path = Path(path)
    arr = np.asarray(Image.open(path))
    sidecar_path = path.with_suffix(".json")
    if not sidecar_path.exists():
        raise FileNotFoundError(
            f"{path.name} has no geometry sidecar ({sidecar_path.name}). "
            "A picture without its microns-per-pixel cannot be measured; refusing to guess."
        )
    side = json.loads(sidecar_path.read_text(encoding="utf-8"))
    known = {"mpp", "channels", "level", "synthetic"}
    return Tile(
        data=arr,
        mpp=float(side["mpp"]),
        channels=tuple(side["channels"]),
        level=int(side.get("level", 0)),
        synthetic=bool(side.get("synthetic", False)),
        meta={k: v for k, v in side.items() if k not in known},
    )


def save_label_tile(labels: np.ndarray, mpp: float, path: str | Path, synthetic: bool = False) -> Path:
    """Write an integer label map (nucleus instance ids) as a 16-bit PNG with a sidecar."""
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if labels.ndim == 3:
        labels = labels[:, :, 0]
    if labels.max() > 65535:
        raise ValueError("more than 65535 instances; use OME-TIFF (phase P1)")
    # Pillow infers 16-bit greyscale from a uint16 array; passing mode= is
    # deprecated (removed in Pillow 13) and unnecessary.
    Image.fromarray(labels.astype(np.uint16)).save(path)
    path.with_suffix(".json").write_text(
        json.dumps({"mpp": mpp, "channels": ["label"], "level": 0, "synthetic": synthetic}, indent=2),
        encoding="utf-8",
    )
    return path


def load_label_tile(path: str | Path) -> np.ndarray:
    """Read a label map written by `save_label_tile` as int32 (H, W)."""
    return np.asarray(Image.open(Path(path))).astype(np.int32)
