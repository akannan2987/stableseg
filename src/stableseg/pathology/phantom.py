"""Synthetic H&E phantoms: a fully controlled stand-in for a stained tissue tile.

This is Track P's twin of `stableseg.phantom`. The reasons are the same three:

1. Every test must run on any machine in seconds, with nothing downloaded.
2. A phantom has a KNOWN answer. A real tile has a pathologist's opinion about
   how many nuclei it contains; a phantom has arithmetic. That answer key is
   what a nucleus detector is checked against before it is trusted on tissue.
3. Anyone who clones the repository regenerates the identical tiles from the
   same seed, so results compare across machines and months.

What a phantom looks like
-------------------------
A pale pink "cytoplasm" background carrying a slow illumination gradient, and
a known number of nuclei drawn as ellipses - each with its own size, aspect
ratio and orientation - coloured through the hematoxylin-and-eosin
optical-density model so that they come out the purple a pathologist expects.
A few percent of pixels get light noise so the tile is not unrealistically
clean.

Why colours are mixed in optical density, not brightness
--------------------------------------------------------
A stain ABSORBS light. Where two stains overlap, the fractions of light they
each let through MULTIPLY - and multiplication becomes addition once you take
a logarithm. That logarithm of the transmitted fraction is the optical density
(OD). So the recipe is:

    OD = concentration_H * stain_vector_H + concentration_E * stain_vector_E
    RGB = 255 * exp(-OD)

where each stain vector is the OD colour of that pure stain (Ruifrok & Johnston
2001, the same vectors scikit-image uses for colour deconvolution). Building
the tile this way means phase P3's colour deconvolution has a known truth to
recover, and phase P2's stain-vector perturbations are perturbations of
exactly the quantity that real staining varies.

Everything here is NumPy only. The generator is disclosed as synthetic in
every file it writes and in every document that mentions it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from stableseg.pathology.tile import Tile, save_label_tile, save_tile

# Optical-density colour of each pure stain (Ruifrok & Johnston 2001), the
# same vectors scikit-image's rgb2hed uses. Rows: hematoxylin, eosin, DAB.
STAIN_VECTORS = np.array(
    [
        [0.65, 0.70, 0.29],  # hematoxylin: absorbs red and green, lets blue through -> looks blue-purple
        [0.07, 0.99, 0.11],  # eosin: absorbs green -> looks pink
        [0.27, 0.57, 0.78],  # DAB: the brown chromogen of immunohistochemistry
    ],
    dtype=np.float32,
)
HEMATOXYLIN, EOSIN, DAB = 0, 1, 2

DEFAULT_MPP = 0.5  # 20x scan: one pixel is half a micron


@dataclass(frozen=True)
class NucleusTruth:
    """One drawn nucleus and its known geometry."""

    instance_id: int
    cy: float
    cx: float
    semi_axis_a_px: float
    semi_axis_b_px: float
    orientation_rad: float
    area_px: int


def _nucleus_mask(
    shape: tuple[int, int], cy: float, cx: float, a: float, b: float, theta: float
) -> np.ndarray:
    """Boolean mask of a rotated ellipse with semi-axes a, b centred at (cy, cx)."""
    yy, xx = np.indices(shape, dtype=np.float32)
    dy, dx = yy - cy, xx - cx
    c, s = np.cos(theta), np.sin(theta)
    u = dx * c + dy * s  # rotate into the ellipse's own axes
    v = -dx * s + dy * c
    return (u / a) ** 2 + (v / b) ** 2 <= 1.0


def _illumination(shape: tuple[int, int], rng: np.random.Generator, strength: float) -> np.ndarray:
    """A slow multiplicative gradient across the tile - uneven lamp, uneven section thickness."""
    ys = np.linspace(-1.0, 1.0, shape[0], dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, shape[1], dtype=np.float32)[None, :]
    a, b = rng.uniform(-1.0, 1.0, size=2).astype(np.float32)
    return (1.0 + strength * (a * ys + b * xs) / 2.0).astype(np.float32)


def render_stains(
    concentrations: dict[int, np.ndarray], illumination: np.ndarray | None = None
) -> np.ndarray:
    """Turn per-pixel concentrations of any stains into an RGB uint8 picture via the OD model.

    `concentrations` maps a row of STAIN_VECTORS to a (H, W) array. Optical
    densities add; the picture is 255 * exp(-OD). This is the one place the
    project turns "how much stain" into "what colour", which is why phase P2's
    stain perturbations and phase P7's synthetic tiles all call it.
    """
    od = None
    for idx, conc in concentrations.items():
        term = conc[:, :, None] * STAIN_VECTORS[idx]
        od = term if od is None else od + term
    transmitted = np.exp(-od)  # fraction of light that gets through each pixel
    if illumination is not None:
        transmitted = transmitted * illumination[:, :, None]
    return np.clip(transmitted * 255.0, 0, 255).astype(np.uint8)


def render_he(h_conc: np.ndarray, e_conc: np.ndarray, illumination: np.ndarray | None = None) -> np.ndarray:
    """H&E picture from hematoxylin and eosin concentrations (a named case of render_stains)."""
    return render_stains({HEMATOXYLIN: h_conc, EOSIN: e_conc}, illumination)


def _place_nuclei(
    rng: np.random.Generator,
    shape: tuple[int, int],
    n_nuclei: int,
    r_lo: float,
    r_hi: float,
) -> tuple[np.ndarray, list[NucleusTruth]]:
    """Rejection-sample non-overlapping ellipses; shared by the H&E, IHC and mIF phantoms."""
    h, w = shape
    labels = np.zeros(shape, dtype=np.int32)
    truths: list[NucleusTruth] = []
    attempts = 0
    while len(truths) < n_nuclei and attempts < n_nuclei * 50:
        attempts += 1
        a = rng.uniform(r_lo, r_hi)
        b = a * rng.uniform(0.6, 1.0)
        theta = rng.uniform(0, np.pi)
        cy = rng.uniform(a, h - a)
        cx = rng.uniform(a, w - a)
        mask = _nucleus_mask(shape, cy, cx, a, b, theta)
        if labels[mask].any():
            continue
        inst = len(truths) + 1
        labels[mask] = inst
        truths.append(NucleusTruth(inst, cy, cx, a, b, theta, int(mask.sum())))
    return labels, truths


def generate_he_phantom(
    seed: int,
    tile_index: int,
    shape: tuple[int, int] = (256, 256),
    mpp: float = DEFAULT_MPP,
    n_nuclei: int = 60,
    nucleus_radius_um: tuple[float, float] = (3.0, 6.0),
    illumination_strength: float = 0.08,
    noise_sd: float = 0.02,
) -> tuple[Tile, np.ndarray, list[NucleusTruth]]:
    """Generate one tile: the picture, its instance label map, and the truth table.

    Seeded per (seed, tile_index) so tile 3 is byte-identical everywhere and
    independent of whether tiles 0-2 were generated first.
    """
    rng = np.random.default_rng([seed, tile_index])
    h, w = shape

    # --- place nuclei: rejection-sample centres so ellipses do not overlap ----
    r_lo, r_hi = (r / mpp for r in nucleus_radius_um)  # microns -> pixels
    labels = np.zeros(shape, dtype=np.int32)
    truths: list[NucleusTruth] = []
    attempts = 0
    while len(truths) < n_nuclei and attempts < n_nuclei * 50:
        attempts += 1
        a = rng.uniform(r_lo, r_hi)
        b = a * rng.uniform(0.6, 1.0)  # aspect ratio: mildly elongated
        theta = rng.uniform(0, np.pi)
        cy = rng.uniform(a, h - a)
        cx = rng.uniform(a, w - a)
        mask = _nucleus_mask(shape, cy, cx, a, b, theta)
        if labels[mask].any():
            continue  # overlaps an existing nucleus; try again
        inst = len(truths) + 1
        labels[mask] = inst
        truths.append(NucleusTruth(inst, cy, cx, a, b, theta, int(mask.sum())))

    # --- stain concentrations: hematoxylin in nuclei, eosin everywhere ------
    nuclear = labels > 0
    h_conc = np.where(nuclear, rng.uniform(0.9, 1.3), 0.05).astype(np.float32)
    e_conc = np.where(nuclear, 0.25, rng.uniform(0.35, 0.55)).astype(np.float32)
    # per-nucleus intensity variation, so not every nucleus is the same purple
    for t in truths:
        h_conc[labels == t.instance_id] *= rng.uniform(0.85, 1.15)
    h_conc += rng.normal(0.0, noise_sd, size=shape).astype(np.float32)
    e_conc += rng.normal(0.0, noise_sd, size=shape).astype(np.float32)
    h_conc = np.clip(h_conc, 0.0, None)
    e_conc = np.clip(e_conc, 0.0, None)

    rgb = render_he(h_conc, e_conc, _illumination(shape, rng, illumination_strength))
    tile = Tile(
        data=rgb,
        mpp=mpp,
        channels=("R", "G", "B"),
        level=0,
        synthetic=True,
        meta={"stain": "H&E", "seed": seed, "tile_index": tile_index},
    )
    return tile, labels, truths


def generate_he_phantom_dataset(
    root: str | Path,
    n_tiles: int,
    shape: tuple[int, int],
    mpp: float,
    n_nuclei: int,
    nucleus_radius_um: tuple[float, float],
    illumination_strength: float,
    noise_sd: float,
    seed: int,
) -> pd.DataFrame:
    """Write `n_tiles` phantoms into root/images, root/labels, and a manifest.

    Layout mirrors Track V's phantom folder (images/ and labels/ paired by
    filename) and the layout the real pathology datasets use, so the loader
    written for phantoms reads real tiles unchanged.
    """
    root = Path(root)
    images, labels_dir = root / "images", root / "labels"
    rows = []
    nucleus_rows = []
    for i in range(n_tiles):
        tile, labels, truths = generate_he_phantom(
            seed, i, shape, mpp, n_nuclei, nucleus_radius_um, illumination_strength, noise_sd
        )
        tile_id = f"he_phantom_{i:03d}"
        save_tile(tile, images / f"{tile_id}.png")
        save_label_tile(labels, mpp, labels_dir / f"{tile_id}.png", synthetic=True)
        nuclear_area_um2 = float((labels > 0).sum()) * tile.pixel_area_um2
        rows.append(
            {
                "tile_id": tile_id,
                "n_nuclei_true": len(truths),
                "nuclear_area_um2": nuclear_area_um2,
                "nuclear_fraction": float((labels > 0).mean()),
                "mpp": mpp,
                "stain": "H&E",
                "synthetic": True,
                "seed": seed,
            }
        )
        for t in truths:
            nucleus_rows.append(
                {
                    "tile_id": tile_id,
                    "instance_id": t.instance_id,
                    "centroid_y_px": t.cy,
                    "centroid_x_px": t.cx,
                    "semi_axis_a_um": t.semi_axis_a_px * mpp,
                    "semi_axis_b_um": t.semi_axis_b_px * mpp,
                    "orientation_rad": t.orientation_rad,
                    "area_um2": t.area_px * mpp * mpp,
                }
            )
    manifest = pd.DataFrame(rows)
    root.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(root / "manifest.csv", index=False)
    pd.DataFrame(nucleus_rows).to_csv(root / "nuclei.csv", index=False)
    return manifest


# ---------------------------------------------------------------------------
# IHC phantom: a known fraction of nuclei are "positive" (brown, DAB)
# ---------------------------------------------------------------------------


def generate_ihc_phantom(
    seed: int,
    tile_index: int,
    shape: tuple[int, int] = (256, 256),
    mpp: float = DEFAULT_MPP,
    n_nuclei: int = 60,
    positive_fraction: float = 0.35,
    nucleus_radius_um: tuple[float, float] = (3.0, 6.0),
    illumination_strength: float = 0.08,
    noise_sd: float = 0.02,
) -> tuple[Tile, np.ndarray, list[NucleusTruth], np.ndarray]:
    """One IHC tile: a known fraction of nuclei stained brown (DAB), the rest blue (hematoxylin).

    Immunohistochemistry marks cells that carry one specific protein. In the
    common nuclear stains (Ki-67, ER, PR) a positive nucleus turns brown and a
    negative one stays blue from the counterstain. The biomarker is the
    positive fraction, and this phantom knows it exactly: `positive` is a
    boolean per nucleus, and `positive.mean()` is the truth.

    Positive nuclei get strong DAB and weak hematoxylin (DAB masks the blue);
    negatives get hematoxylin only. Intensities vary per nucleus, because real
    positivity is graded - which is what the H-score measures.
    """
    rng = np.random.default_rng([seed, tile_index, 1])
    r_lo, r_hi = (r / mpp for r in nucleus_radius_um)
    labels, truths = _place_nuclei(rng, shape, n_nuclei, r_lo, r_hi)
    n = len(truths)
    positive = np.zeros(n, dtype=bool)
    positive[: int(round(positive_fraction * n))] = True
    rng.shuffle(positive)

    nuclear = labels > 0
    h_conc = np.where(nuclear, 0.9, 0.05).astype(np.float32)
    d_conc = np.zeros(shape, dtype=np.float32)
    e_conc = np.where(nuclear, 0.0, rng.uniform(0.15, 0.25)).astype(np.float32)  # faint background
    for t, pos in zip(truths, positive, strict=True):
        m = labels == t.instance_id
        if pos:
            d_conc[m] = rng.uniform(0.8, 1.4)  # graded: weak to strong DAB
            h_conc[m] = 0.25
        else:
            h_conc[m] *= rng.uniform(0.85, 1.15)
    for arr in (h_conc, d_conc, e_conc):
        arr += rng.normal(0.0, noise_sd, size=shape).astype(np.float32)
        np.clip(arr, 0.0, None, out=arr)

    rgb = render_stains(
        {HEMATOXYLIN: h_conc, DAB: d_conc, EOSIN: e_conc},
        _illumination(shape, rng, illumination_strength),
    )
    tile = Tile(
        data=rgb,
        mpp=mpp,
        channels=("R", "G", "B"),
        synthetic=True,
        meta={"stain": "IHC (DAB, nuclear)", "seed": seed, "tile_index": tile_index},
    )
    return tile, labels, truths, positive


# ---------------------------------------------------------------------------
# mIF phantom: several fluorescent channels, cells with known phenotypes
# ---------------------------------------------------------------------------

# A small, plausible panel. DAPI marks every nucleus; the markers define
# phenotypes. Each phenotype is a set of markers that are "on".
MIF_CHANNELS: tuple[str, ...] = ("DAPI", "PanCK", "CD3", "CD8", "CD68")
MIF_PHENOTYPES: dict[str, tuple[str, ...]] = {
    "tumour": ("PanCK",),
    "T_helper": ("CD3",),
    "T_cytotoxic": ("CD3", "CD8"),
    "macrophage": ("CD68",),
    "other": (),
}


def generate_mif_phantom(
    seed: int,
    tile_index: int,
    shape: tuple[int, int] = (256, 256),
    mpp: float = DEFAULT_MPP,
    n_cells: int = 80,
    phenotype_fractions: dict[str, float] | None = None,
    nucleus_radius_um: tuple[float, float] = (3.0, 5.0),
    noise_sd: float = 0.03,
) -> tuple[Tile, np.ndarray, list[NucleusTruth], list[str]]:
    """One multichannel mIF tile with a known phenotype for every cell.

    Multiplex immunofluorescence gives one picture per marker, black where the
    marker is absent and bright where present. Here every cell gets a
    phenotype drawn from known proportions, and each marker channel is lit in
    the cells whose phenotype includes it (nucleus plus a small halo of
    cytoplasm for membrane/cytoplasmic markers). DAPI lights every nucleus.

    The truth is the list of phenotypes, one per cell; the biomarkers phase
    P3 computes from this tile (density per phenotype, neighbourhood
    enrichment) therefore have an answer key.
    """
    fractions = phenotype_fractions or {
        "tumour": 0.45,
        "T_helper": 0.15,
        "T_cytotoxic": 0.15,
        "macrophage": 0.10,
        "other": 0.15,
    }
    if abs(sum(fractions.values()) - 1.0) > 1e-6:
        raise ValueError("phenotype_fractions must sum to 1")
    rng = np.random.default_rng([seed, tile_index, 2])
    r_lo, r_hi = (r / mpp for r in nucleus_radius_um)
    labels, truths = _place_nuclei(rng, shape, n_cells, r_lo, r_hi)
    n = len(truths)

    names = list(fractions)
    counts = np.floor(np.array([fractions[k] for k in names]) * n).astype(int)
    counts[0] += n - counts.sum()  # remainder to the first phenotype so counts sum to n
    phenotypes = [name for name, c in zip(names, counts, strict=True) for _ in range(c)]
    rng.shuffle(phenotypes)

    from scipy import ndimage

    stack = np.zeros((*shape, len(MIF_CHANNELS)), dtype=np.float32)
    dapi = MIF_CHANNELS.index("DAPI")
    for t, ph in zip(truths, phenotypes, strict=True):
        nuc = labels == t.instance_id
        cell = ndimage.binary_dilation(nuc, iterations=2)  # nucleus + thin cytoplasm
        stack[nuc, dapi] = rng.uniform(0.7, 1.0)
        for marker in MIF_PHENOTYPES[ph]:
            stack[cell, MIF_CHANNELS.index(marker)] = rng.uniform(0.6, 1.0)
    stack += rng.normal(0.0, noise_sd, size=stack.shape).astype(np.float32)
    stack = np.clip(stack, 0.0, 1.0)

    tile = Tile(
        data=stack,
        mpp=mpp,
        channels=MIF_CHANNELS,
        synthetic=True,
        meta={"stain": "mIF", "seed": seed, "tile_index": tile_index, "phenotypes": list(MIF_PHENOTYPES)},
    )
    return tile, labels, truths, phenotypes


# ---------------------------------------------------------------------------
# Dataset writers for the two new phantoms (mirror generate_he_phantom_dataset)
# ---------------------------------------------------------------------------


def generate_ihc_phantom_dataset(
    root: str | Path, n_tiles: int, positive_fraction: float, seed: int, **kw: Any
) -> pd.DataFrame:
    root = Path(root)
    rows, cells = [], []
    for i in range(n_tiles):
        tile, labels, truths, positive = generate_ihc_phantom(
            seed, i, positive_fraction=positive_fraction, **kw
        )
        tid = f"ihc_phantom_{i:03d}"
        save_tile(tile, root / "images" / f"{tid}.png")
        save_label_tile(labels, tile.mpp, root / "labels" / f"{tid}.png", synthetic=True)
        rows.append(
            {
                "tile_id": tid,
                "n_nuclei_true": len(truths),
                "n_positive_true": int(positive.sum()),
                "positive_fraction_true": float(positive.mean()),
                "mpp": tile.mpp,
                "stain": "IHC",
                "synthetic": True,
                "seed": seed,
            }
        )
        for t, pos in zip(truths, positive, strict=True):
            cells.append({"tile_id": tid, "instance_id": t.instance_id, "positive": bool(pos)})
    root.mkdir(parents=True, exist_ok=True)
    manifest = pd.DataFrame(rows)
    manifest.to_csv(root / "manifest.csv", index=False)
    pd.DataFrame(cells).to_csv(root / "cells.csv", index=False)
    return manifest


def generate_mif_phantom_dataset(root: str | Path, n_tiles: int, seed: int, **kw: Any) -> pd.DataFrame:
    from stableseg.pathology.io import write_ome_tiff

    root = Path(root)
    rows, cells = [], []
    for i in range(n_tiles):
        tile, labels, truths, phenotypes = generate_mif_phantom(seed, i, **kw)
        tid = f"mif_phantom_{i:03d}"
        write_ome_tiff(tile, root / "images" / f"{tid}.ome.tiff")
        save_label_tile(labels, tile.mpp, root / "labels" / f"{tid}.png", synthetic=True)
        row: dict[str, Any] = {
            "tile_id": tid,
            "n_cells_true": len(truths),
            "mpp": tile.mpp,
            "stain": "mIF",
            "synthetic": True,
            "seed": seed,
        }
        for ph in MIF_PHENOTYPES:
            row[f"n_{ph}_true"] = int(sum(p == ph for p in phenotypes))
        rows.append(row)
        for t, ph in zip(truths, phenotypes, strict=True):
            cells.append({"tile_id": tid, "instance_id": t.instance_id, "phenotype": ph})
    root.mkdir(parents=True, exist_ok=True)
    manifest = pd.DataFrame(rows)
    manifest.to_csv(root / "manifest.csv", index=False)
    pd.DataFrame(cells).to_csv(root / "cells.csv", index=False)
    return manifest
