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


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    fig_voxel_volume()
    fig_repeatability_wobble()
    fig_perturbation_preview()
    fig_he_phantom()
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
