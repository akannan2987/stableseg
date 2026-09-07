#!/usr/bin/env python3
"""Regenerate every illustration in docs/img/ from code.

Why figures come from a script rather than a drawing tool: this project's
whole argument is that results should be reproducible, and its documentation
should hold itself to the same standard. Every image a reader sees can be
rebuilt, byte-for-byte-similar, by running this file - so a figure can never
quietly drift out of step with the code that it illustrates.

This script is a documentation tool, not part of the package. It needs
matplotlib, which is deliberately NOT a project dependency (the audit engine
has no business dragging a plotting stack around). Install it ad hoc:

    python -m pip install matplotlib
    python scripts/make_figures.py

Figures written (all under docs/img/, all well below the 1 MB preflight cap):

    voxel_volume.png          how voxel spacing turns a count into a volume
    repeatability_wobble.png  the whole project's question, in one picture
    perturbation_preview.png  what phase 3 will do to a scan (illustration)
    he_phantom_tile000.png    Track P: the synthetic H&E phantom, its truth,
                              and what colour deconvolution recovers
    pathology_phantoms.png    Track P: the IHC phantom with its known positive
                              fraction, and the mIF phantom's five channels with
                              known phenotypes
    synthetic_slide.png       Track P: a synthetic whole slide, the tissue
                              detector's mask, and the tiles it selects
    msd_hippocampus_case.png  Track V: a real hippocampus MRI with its expert
                              outline, three orthogonal views (needs the
                              dataset: `stableseg fetch msd_task04_hippocampus`;
                              skipped with a message if absent)

`phantom_case000.png` (the image/labels/overlay panel) is produced separately
during phase 1 and is not rewritten here.

Everything is seeded; run it twice and the story in each figure is identical.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display needed; we only write files
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

REPO_ROOT = Path(__file__).resolve().parents[1]
IMG = REPO_ROOT / "docs" / "img"

# One consistent, colourblind-friendly palette across all figures.
BLUE, ORANGE, GREEN, GREY = "#4477AA", "#EE7733", "#228833", "#BBBBBB"


# ---------------------------------------------------------------------------
# Figure 1: voxel spacing -> volume. The single most important idea in io.py.
# ---------------------------------------------------------------------------
def fig_voxel_volume() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))

    # Panel A: a slice is a grid of voxels; some belong to the structure.
    ax = axes[0]
    n = 8
    inside = np.zeros((n, n), dtype=bool)
    yy, xx = np.mgrid[0:n, 0:n]
    inside[((yy - 3.5) ** 2 / 6 + (xx - 3.5) ** 2 / 4) < 1.6] = True
    for y in range(n):
        for x in range(n):
            color = ORANGE if inside[y, x] else "white"
            ax.add_patch(plt.Rectangle((x, n - 1 - y), 1, 1, facecolor=color, edgecolor=GREY, linewidth=0.8))
    ax.text(
        n / 2,
        -0.9,
        f"{int(inside.sum())} voxels belong\nto the structure",
        ha="center",
        va="top",
        fontsize=10,
    )
    ax.set_xlim(-0.5, n + 0.5)
    ax.set_ylim(-2.6, n + 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("1 · Count the voxels", fontsize=11)

    # Panel B: each voxel has a physical size, stored in the file.
    ax = axes[1]
    ax.add_patch(plt.Rectangle((0.3, 0.3), 1.4, 1.4, facecolor=ORANGE, edgecolor="black", linewidth=1.2))
    ax.annotate("", xy=(1.7, 0.12), xytext=(0.3, 0.12), arrowprops=dict(arrowstyle="<->", color="black"))
    ax.text(1.0, 0.06, "1.0 mm", ha="center", va="top", fontsize=10)
    ax.annotate("", xy=(0.12, 1.7), xytext=(0.12, 0.3), arrowprops=dict(arrowstyle="<->", color="black"))
    ax.text(0.03, 1.0, "1.0 mm", ha="right", va="center", fontsize=10, rotation=90)
    ax.text(1.0, 2.15, "one voxel = 1.0 × 1.0 × 1.0 mm\n= 1.0 mm³ of tissue", ha="center", fontsize=10)
    ax.text(
        1.0,
        -0.55,
        'the size lives in the file ("spacing_mm")',
        ha="center",
        fontsize=9,
        style="italic",
        color="0.35",
    )
    ax.set_xlim(-0.4, 2.4)
    ax.set_ylim(-0.9, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("2 · Read the voxel size", fontsize=11)

    # Panel C: same count, two spacings, eightfold difference.
    ax = axes[2]
    counts = 1446
    vols = {"1.0 mm spacing": counts * 1.0, "2.0 mm spacing": counts * 8.0}
    bars = ax.bar(list(vols), list(vols.values()), color=[GREEN, "#CC3311"], width=0.55)
    for b, v in zip(bars, vols.values(), strict=True):
        ax.text(b.get_x() + b.get_width() / 2, v + 240, f"{v:,.0f} mm³", ha="center", fontsize=10)
    ax.set_ylabel("computed volume (mm³)")
    ax.set_ylim(0, 13500)
    ax.set_title("3 · Same count, wrong spacing:\nan eightfold error", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("How a volume is measured — and why voxel spacing must never be lost", fontsize=12.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(IMG / "voxel_volume.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: repeatability. The bathroom-scale story as one picture.
# ---------------------------------------------------------------------------
def fig_repeatability_wobble() -> None:
    rng = np.random.default_rng(7)
    n = 12
    true_now, true_after = 2270.0, 2210.0  # a real 60 mm3 change

    stable = true_now + rng.normal(0, 12, n)
    wobbly = true_now + rng.normal(0, 95, n)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
    for ax, vals, color, wobble in (
        (axes[0], stable, GREEN, 12),
        (axes[1], wobbly, "#CC3311", 95),
    ):
        x = rng.uniform(-0.13, 0.13, n)
        ax.scatter(x, vals, s=48, color=color, alpha=0.85, zorder=3)
        ax.axhline(true_now, color="black", linewidth=1.2, zorder=1)
        ax.axhline(true_after, color=BLUE, linewidth=1.4, linestyle="--", zorder=1)
        ax.set_xlim(-0.55, 0.55)
        ax.set_xticks([])
        ax.set_title(f"instrument wobble: about ±{wobble} mm³", fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylim(1930, 2610)
    axes[0].set_ylabel("measured volume (mm³)")
    axes[0].text(0.52, true_now + 12, "true value today", fontsize=9, ha="right", va="bottom")
    axes[0].text(
        0.52, true_after - 12, "true value after a real change", fontsize=9, ha="right", va="top", color=BLUE
    )
    axes[0].set_xlabel("the change stands clear of the noise", fontsize=10, color=GREEN)
    axes[1].set_xlabel("the same change drowns in it", fontsize=10, color="#CC3311")

    fig.suptitle(
        "Twelve measurements of a patient who has not changed.\n"
        "The wobble decides which real changes can ever be seen.",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(IMG / "repeatability_wobble.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: perturbation preview - the same real phantom slice, disturbed.
# Uses only numpy/scipy operations, applied to the actual generated data.
# ---------------------------------------------------------------------------
def fig_perturbation_preview() -> None:
    import nibabel as nib

    img_path = REPO_ROOT / "data" / "phantom" / "images" / "phantom_000.nii.gz"
    if not img_path.exists():
        raise SystemExit("Phantom data missing. Generate it first:  stableseg phantom")
    vol = np.asarray(nib.load(str(img_path)).dataobj, dtype=np.float32)
    z = vol.shape[2] // 2
    base = vol[:, :, z].T  # transpose so the head points up, matching case000 figure

    rng = np.random.default_rng(42)

    noisy = base + rng.normal(0, 0.10, base.shape).astype(np.float32)
    blurred = ndimage.gaussian_filter(base, sigma=1.6)
    yy, xx = np.mgrid[0 : base.shape[0], 0 : base.shape[1]]
    bias = 1.0 + 0.35 * (xx / xx.max() - 0.5)  # smooth left-right drift
    drifted = base * bias
    rotated = ndimage.rotate(base, angle=8, reshape=False, order=1, mode="nearest")

    panels = [
        (base, "original slice"),
        (noisy, "noise added\n(a noisier scanner day)"),
        (blurred, "blurred\n(patient moved slightly)"),
        (drifted, "brightness drift\n(field inhomogeneity)"),
        (rotated, "rotated 8°\n(different head position)"),
    ]
    fig, axes = plt.subplots(1, 5, figsize=(13, 3.4))
    for ax, (img, title) in zip(axes, panels, strict=True):
        ax.imshow(img, cmap="gray", origin="lower", vmin=0, vmax=1)
        ax.set_title(title, fontsize=9.5)
        ax.axis("off")
    fig.suptitle(
        "One phantom, disturbed the way real scanning disturbs a picture — the patient has not changed. "
        "(Illustration; phase 3 builds these properly, with physics and parameters.)",
        fontsize=10.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(IMG / "perturbation_preview.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 (Track P): the H&E phantom - picture, known truth, and the
# hematoxylin channel that colour deconvolution recovers from the picture.
# ---------------------------------------------------------------------------
def fig_he_phantom() -> None:
    from skimage.color import rgb2hed

    from stableseg.pathology.phantom import generate_he_phantom

    tile, labels, truths = generate_he_phantom(seed=42, tile_index=0)  # the default tile 000
    rgb = tile.data

    # Colour deconvolution: undo the stain mixing in optical density and read
    # off "how much hematoxylin is here". This is phase P3's classical nucleus
    # detector in one line; shown here as a preview and as a check that the
    # phantom was built in the same OD model the deconvolution assumes.
    hed = rgb2hed(rgb)
    h_channel = hed[:, :, 0]

    # Three panels, tiles at native 256 px, nearest-neighbour. The tile is
    # deliberately noisy (every pixel unique), so it compresses poorly; showing
    # it once, with the truth outlined on it, keeps the file small.
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.4))
    axes[0].imshow(rgb, interpolation="nearest")
    axes[0].contour(labels > 0, levels=[0.5], colors=[GREEN], linewidths=0.8)
    axes[0].set_title("synthetic H&E tile, truth outlined\n(256 px · 0.5 µm/px · 128 µm field)", fontsize=9.5)

    axes[1].imshow(labels > 0, cmap="gray", interpolation="nearest")
    axes[1].set_title(f"known truth: {len(truths)} nuclei\n(instance label map)", fontsize=9.5)

    # Quantise the continuous hematoxylin map to 16 levels: visually identical
    # in a documentation figure, and it compresses several times smaller.
    h_q = np.round(h_channel / h_channel.max() * 15) / 15
    axes[2].imshow(h_q, cmap="magma", interpolation="nearest")
    axes[2].set_title("hematoxylin recovered by\ncolour deconvolution (preview of P3)", fontsize=9.5)
    for ax in axes:
        ax.axis("off")
    fig.suptitle(
        "Track P phantom, case 000 — synthetic, generated by code, not a scan of anyone.\n"
        "Every nucleus has a known position and area, so a detector can be checked against arithmetic.",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    # 100 dpi: the source tiles are 256 px, so higher resolution only inflates
    # the file with noise that compresses badly (an early version was 900 KB).
    fig.savefig(IMG / "he_phantom_tile000.png", dpi=100, pil_kwargs={"optimize": True})
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 (Track V): a real scan. The first figure in the project that is
# not synthetic. Needs the fetched dataset; skips politely otherwise, because
# a figure script that fails on a fresh clone would be a figure script nobody
# runs.
# ---------------------------------------------------------------------------
def fig_msd_case() -> None:
    from stableseg.io import label_volume_mm3, load_volume

    root = REPO_ROOT / "data" / "Task04_Hippocampus"
    case = "hippocampus_001"
    img_path = root / "imagesTr" / f"{case}.nii.gz"
    lbl_path = root / "labelsTr" / f"{case}.nii.gz"
    if not img_path.exists():
        print(
            "  msd_hippocampus_case.png  SKIPPED - real data not present. "
            "Run `stableseg fetch msd_task04_hippocampus` first."
        )
        return

    img, lbl = load_volume(img_path), load_volume(lbl_path)
    data, labels = img.data.astype(np.float32), lbl.data.astype(np.int32)
    # Window the intensities for display; MRI has no fixed scale.
    lo, hi = np.percentile(data, [1, 99])
    shown = np.clip((data - lo) / (hi - lo), 0, 1)
    # Cut through the centre of the outlined structure so every view shows it.
    cz, cy, cx = (np.round(np.mean(np.argwhere(labels > 0), axis=0)).astype(int))[::-1]
    sx, sy, sz = img.spacing_mm
    v1, v2 = label_volume_mm3(lbl, 1), label_volume_mm3(lbl, 2)

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.9))
    views = [
        (shown[cx, :, :].T, labels[cx, :, :].T, sy / sz, "sagittal (x fixed)"),
        (shown[:, cy, :].T, labels[:, cy, :].T, sx / sz, "coronal (y fixed)"),
        (shown[:, :, cz].T, labels[:, :, cz].T, sx / sy, "axial (z fixed)"),
    ]
    for ax, (sl, lb, aspect, title) in zip(axes, views, strict=True):
        ax.imshow(sl, cmap="gray", origin="lower", aspect=1 / aspect, interpolation="nearest")
        ax.contour(lb == 1, levels=[0.5], colors=[BLUE], linewidths=1.0)
        ax.contour(lb == 2, levels=[0.5], colors=[ORANGE], linewidths=1.0)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    fig.suptitle(
        f"Real T1 MRI, Medical Segmentation Decathlon {case} — expert outline: "
        f"label 1 (blue) {v1:.0f} mm³, label 2 (orange) {v2:.0f} mm³; "
        f"voxels {sx:.2g}×{sy:.2g}×{sz:.2g} mm.\n"
        "Tiny volume, real anatomy, CC BY-SA 4.0. "
        "One scan per subject — every repeat in Track V is simulated.",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(IMG / "msd_hippocampus_case.png", dpi=110, pil_kwargs={"optimize": True})
    plt.close(fig)


def _q8(img: np.ndarray, step: int = 12) -> np.ndarray:
    """Quantise a uint8 picture for display: invisible at figure size, compresses 2-3x smaller."""
    return ((img.astype(np.int32) // step) * step).astype(np.uint8)


# ---------------------------------------------------------------------------
# Figure 6 (Track P): the IHC and mIF phantoms and their known truths.
# ---------------------------------------------------------------------------
def fig_pathology_phantoms() -> None:
    from stableseg.pathology.phantom import MIF_CHANNELS, generate_ihc_phantom, generate_mif_phantom

    ihc, ihc_lab, ihc_tr, positive = generate_ihc_phantom(seed=42, tile_index=0)
    mif, mif_lab, mif_tr, phen = generate_mif_phantom(seed=42, tile_index=0)

    fig, axes = plt.subplots(2, 4, figsize=(10.4, 5.8))
    # row 1: IHC picture, positive/negative truth, DAB channel by deconvolution
    from skimage.color import rgb2hed

    axes[0, 0].imshow(_q8(ihc.data), interpolation="nearest")
    axes[0, 0].set_title(
        f"IHC phantom: {positive.sum()} of {len(positive)}\nnuclei positive (brown)", fontsize=9.5
    )
    truth = np.zeros(ihc_lab.shape, dtype=np.uint8)
    for t, p in zip(ihc_tr, positive, strict=True):
        truth[ihc_lab == t.instance_id] = 2 if p else 1
    axes[0, 1].imshow(truth, cmap="viridis", interpolation="nearest", vmin=0, vmax=2)
    axes[0, 1].set_title("known truth: 0 background,\n1 negative, 2 positive", fontsize=9.5)
    dab = rgb2hed(ihc.data)[:, :, 2]
    dab_q = np.round(dab / dab.max() * 15) / 15
    axes[0, 2].imshow(dab_q, cmap="copper", interpolation="nearest")
    axes[0, 2].set_title("DAB channel recovered by\ncolour deconvolution (preview of P3)", fontsize=9.5)
    axes[0, 3].axis("off")
    axes[0, 3].text(
        0.0,
        0.9,
        "The IHC biomarker is\nthe positive fraction.\n\n"
        f"Truth here: {positive.mean():.2f}\n\n"
        "Phase P3 scores it from\nthe picture; the audit\n"
        "asks how far that score\nmoves under stain and\nscanner change.",
        fontsize=9.5,
        va="top",
    )
    # row 2: mIF composite and three single channels
    colours = {
        "DAPI": (0.25, 0.25, 1.0),
        "PanCK": (1.0, 0.9, 0.0),
        "CD3": (0.0, 0.9, 0.0),
        "CD8": (1.0, 0.1, 0.1),
        "CD68": (1.0, 0.0, 1.0),
    }
    comp = np.zeros((*mif.data.shape[:2], 3), dtype=np.float32)
    for i, c in enumerate(MIF_CHANNELS):
        comp += mif.data[:, :, i : i + 1] * np.array(colours[c], dtype=np.float32)
    axes[1, 0].imshow(_q8((np.clip(comp, 0, 1) * 255).astype(np.uint8)), interpolation="nearest")
    counts = {ph: phen.count(ph) for ph in ("tumour", "T_helper", "T_cytotoxic", "macrophage", "other")}
    axes[1, 0].set_title(
        f"mIF phantom, 5 channels composited\n{counts['tumour']} tumour, {counts['T_cytotoxic']} CD8 T, "
        f"{counts['macrophage']} macrophage",
        fontsize=9,
    )
    for ax, name in zip(axes[1, 1:], ("PanCK", "CD3", "CD8"), strict=True):
        ch = mif.data[:, :, MIF_CHANNELS.index(name)]
        ax.imshow(np.round(ch * 7) / 7, cmap="gray", interpolation="nearest", vmin=0, vmax=1)
        ax.set_title(f"{name} channel alone\n(what the scanner records)", fontsize=9.5)
    for ax in axes.ravel():
        if ax is not axes[0, 3]:
            ax.axis("off")
    fig.suptitle(
        "Track P phantoms with known truths — synthetic, generated by code, not tissue from anyone.\n"
        "Top: immunohistochemistry (positive fraction known). "
        "Bottom: multiplex immunofluorescence (phenotype of every cell known).",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92), h_pad=2.2)
    fig.savefig(IMG / "pathology_phantoms.png", dpi=90, pil_kwargs={"optimize": True})
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 7 (Track P): a synthetic whole slide, read back through OpenSlide.
# Skipped without the pathology extra.
# ---------------------------------------------------------------------------
def fig_synthetic_slide() -> None:
    try:
        import openslide  # noqa: F401
    except ImportError:
        print("  synthetic_slide.png  SKIPPED - pathology extra not installed.")
        return
    import tempfile

    from stableseg.pathology.io import open_slide, write_pyramidal_tiff
    from stableseg.pathology.phantom import generate_he_phantom

    # A "slide": an oval of tiled H&E phantoms on glass, 2048 x 3072 px at 0.5 um.
    rng = np.random.default_rng(11)
    h, w, ts = 2048, 3072, 256
    slide = np.full((h, w, 3), 246, np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    tissue = ((yy - h / 2) / (h * 0.40)) ** 2 + ((xx - w / 2) / (w * 0.42)) ** 2 < 1.0
    k = 0
    for y in range(0, h, ts):
        for x in range(0, w, ts):
            tile, _, _ = generate_he_phantom(
                seed=11, tile_index=k, shape=(ts, ts), n_nuclei=int(rng.integers(30, 70))
            )
            slide[y : y + ts, x : x + ts] = tile.data
            k += 1
    slide[~tissue] = 246
    tmp = Path(tempfile.mkdtemp()) / "synthetic_slide.tif"
    write_pyramidal_tiff(slide, mpp=0.5, path=tmp, n_levels=4, compression="jpeg")

    with open_slide(tmp) as s:
        info = s.describe()
        thumb = _q8(s.thumbnail(320), 16)
        mask = s.tissue_mask(320)
        tiles = list(s.iter_tiles(size=ts, level=0, tissue_only=True, min_tissue_fraction=0.6))
        one = tiles[len(tiles) // 2]

    fig, axes = plt.subplots(1, 4, figsize=(11.0, 3.3))
    axes[0].imshow(thumb, interpolation="nearest")
    axes[0].set_title(
        f"synthetic slide via OpenSlide\n{info['level_count']} levels · "
        f"{info['field_mm'][0]:.2f} × {info['field_mm'][1]:.2f} mm",
        fontsize=9.5,
    )
    axes[1].imshow(mask, cmap="gray", interpolation="nearest")
    axes[1].set_title("tissue mask (saturation, Otsu):\nwhere tiles are worth reading", fontsize=9.5)
    axes[2].imshow(thumb, interpolation="nearest")
    sx, sy = thumb.shape[1] / w, thumb.shape[0] / h
    for t in tiles:
        x0, y0 = t.meta["x0"] * sx, t.meta["y0"] * sy
        axes[2].add_patch(
            plt.Rectangle((x0, y0), ts * sx, ts * sy, fill=False, edgecolor=GREEN, linewidth=0.6)
        )
    axes[2].set_title(f"{len(tiles)} tissue tiles selected\n(glass skipped)", fontsize=9.5)
    axes[3].imshow(_q8(one.data), interpolation="nearest")
    axes[3].set_title(f"one streamed tile\n{one.mpp} µm/px · level {one.level}", fontsize=9.5)
    for ax in axes:
        ax.axis("off")
    fig.suptitle(
        "Whole-slide handling on a slide built from the H&E phantom: written as a pyramid, "
        "read back through the same reader used for scanner exports.\n"
        "Synthetic; a real slide is streamed the same way in phase P1b.",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(IMG / "synthetic_slide.png", dpi=90, pil_kwargs={"optimize": True})
    plt.close(fig)


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    fig_voxel_volume()
    fig_repeatability_wobble()
    fig_perturbation_preview()
    fig_he_phantom()
    fig_pathology_phantoms()
    fig_synthetic_slide()
    fig_msd_case()
    # Every figure is committed, and git history is permanent, so size is
    # checked here rather than discovered later. 200 KB is generous for a
    # documentation figure; the pre-push check refuses anything over 1 MB.
    oversized = []
    for f in sorted(IMG.glob("*.png")):
        kb = f.stat().st_size / 1024
        flag = "  <-- OVER 200 KB, reduce dpi or size" if kb > 200 else ""
        print(f"  {f.relative_to(REPO_ROOT)}  {kb:.0f} KB{flag}")
        if kb > 200:
            oversized.append(f.name)
    if oversized:
        raise SystemExit(f"Oversized figure(s): {', '.join(oversized)}")
    print("Figures regenerated.")
