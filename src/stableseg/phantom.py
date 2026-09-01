"""Synthetic phantoms: a small, fully controlled stand-in for real MRI.

Why generate data at all? Three reasons.

1. The tests must run on any machine in seconds, without downloading anything.
2. A phantom has a KNOWN true volume. Real scans never do. With a known truth
   we can check that the whole pipeline measures what it claims to measure
   before pointing it at data where nobody knows the answer.
3. Anyone who clones the repository regenerates the identical phantoms from
   the same seed, so results are comparable across machines and months.

What a phantom looks like: a dim, slightly uneven "tissue" background, and a
brighter structure made of two touching ellipsoids labelled 1 and 2 (mirroring
the two-part labelling of the real hippocampus data used later). Each subject
gets its own size and position. Gaussian noise and a smooth intensity gradient
(a crude "bias field") are added so the image is not unrealistically clean.

Everything here is NumPy only. The generator is disclosed as synthetic in
every document that mentions it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from stableseg.io import Volume, label_volume_mm3, save_volume

BACKGROUND_INTENSITY = 0.40
STRUCTURE_INTENSITY = 0.75


@dataclass(frozen=True)
class PhantomCase:
    """One generated subject and its ground truth."""

    case_id: str
    image: Volume
    label: Volume
    true_volume_mm3: dict[int, float]  # per label value


def _ellipsoid_mask(shape: tuple[int, int, int], center: np.ndarray, radii: np.ndarray) -> np.ndarray:
    """Boolean mask of an axis-aligned ellipsoid."""
    grids = np.indices(shape, dtype=np.float32)
    normalised = ((grids - center[:, None, None, None]) / radii[:, None, None, None]) ** 2
    return normalised.sum(axis=0) <= 1.0


def _smooth_bias(shape: tuple[int, int, int], rng: np.random.Generator, strength: float = 0.15) -> np.ndarray:
    """A gentle multiplicative intensity gradient across the volume (order-1 polynomial)."""
    coords = [np.linspace(-1.0, 1.0, n, dtype=np.float32) for n in shape]
    gx, gy, gz = np.meshgrid(*coords, indexing="ij")
    a, b, c = rng.uniform(-1.0, 1.0, size=3).astype(np.float32)
    field = 1.0 + strength * (a * gx + b * gy + c * gz) / 3.0
    return field.astype(np.float32)


def make_phantom_case(
    case_index: int,
    shape: tuple[int, int, int] = (48, 64, 48),
    spacing_mm: tuple[float, float, float] = (1.0, 1.0, 1.0),
    noise_sd: float = 0.05,
    seed: int = 42,
) -> PhantomCase:
    """Build one phantom subject deterministically from (seed, case_index)."""
    rng = np.random.default_rng([seed, case_index])
    shape_arr = np.asarray(shape, dtype=np.float32)

    # Subject-specific size (about +/-20 %) and a small positional jitter.
    scale = rng.uniform(0.8, 1.2)
    center = shape_arr / 2.0 + rng.uniform(-3.0, 3.0, size=3)

    # "Head" (label 1) is a rounder blob; "body" (label 2) is elongated along y,
    # attached just behind the head. Radii are in voxels.
    head_radii = np.array([7.0, 6.0, 6.0], dtype=np.float32) * scale
    body_radii = np.array([5.0, 12.0, 5.0], dtype=np.float32) * scale
    head_center = center + np.array([0.0, -8.0 * scale, 0.0], dtype=np.float32)
    body_center = center + np.array([0.0, 6.0 * scale, 0.0], dtype=np.float32)

    head = _ellipsoid_mask(shape, head_center, head_radii)
    body = _ellipsoid_mask(shape, body_center, body_radii)
    body &= ~head  # where they overlap, the head wins

    label = np.zeros(shape, dtype=np.uint8)
    label[head] = 1
    label[body] = 2

    image = np.full(shape, BACKGROUND_INTENSITY, dtype=np.float32)
    image[label > 0] = STRUCTURE_INTENSITY
    image *= _smooth_bias(shape, rng)
    image += rng.normal(0.0, noise_sd, size=shape).astype(np.float32)
    image = np.clip(image, 0.0, None)

    affine = np.diag([spacing_mm[0], spacing_mm[1], spacing_mm[2], 1.0]).astype(np.float64)
    image_vol = Volume(data=image, affine=affine, meta={"synthetic": True, "case_index": case_index})
    label_vol = Volume(data=label, affine=affine, meta={"synthetic": True, "case_index": case_index})

    truth = {v: label_volume_mm3(label_vol, v) for v in (1, 2)}
    return PhantomCase(
        case_id=f"phantom_{case_index:03d}", image=image_vol, label=label_vol, true_volume_mm3=truth
    )


def generate_phantom_dataset(
    root: str | Path,
    n_cases: int = 8,
    shape: tuple[int, int, int] = (48, 64, 48),
    spacing_mm: tuple[float, float, float] = (1.0, 1.0, 1.0),
    noise_sd: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """Write `root/images/*.nii.gz`, `root/labels/*.nii.gz` and `root/manifest.csv`.

    The manifest lists every case with its true label volumes: the answer key
    the audit is later checked against.
    """
    root = Path(root)
    rows = []
    for i in range(n_cases):
        case = make_phantom_case(i, shape=shape, spacing_mm=spacing_mm, noise_sd=noise_sd, seed=seed)
        save_volume(case.image, root / "images" / f"{case.case_id}.nii.gz", dtype=np.float32)
        save_volume(case.label, root / "labels" / f"{case.case_id}.nii.gz", dtype=np.uint8)
        rows.append(
            {
                "case_id": case.case_id,
                "true_volume_label1_mm3": case.true_volume_mm3[1],
                "true_volume_label2_mm3": case.true_volume_mm3[2],
                "true_volume_total_mm3": case.true_volume_mm3[1] + case.true_volume_mm3[2],
                "synthetic": True,
                "seed": seed,
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(root / "manifest.csv", index=False)
    return manifest
