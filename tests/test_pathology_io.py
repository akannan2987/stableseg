"""Phase P1: the shared geometry contract, OME-TIFF, pyramidal TIFF, whole-slide reading.

Every slide read here was written moments earlier by this project's own
writer, so the reader is checked against a slide whose geometry and pixels
are known exactly - no download, no vendor file, no patient. OpenSlide reads
generic pyramidal TIFF through the same code path it uses for scanner
exports, which is what makes the test meaningful.

The whole-slide tests need the optional [pathology] extra (OpenSlide) and
are skipped cleanly without it, with a message saying so; everything else
runs on the core install.
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from stableseg.image import ImageBase
from stableseg.io import Volume
from stableseg.pathology.io import (
    open_slide,
    read_ome_tiff,
    write_ome_tiff,
    write_pyramidal_tiff,
)
from stableseg.pathology.phantom import (
    MIF_CHANNELS,
    MIF_PHENOTYPES,
    generate_he_phantom,
    generate_ihc_phantom,
    generate_ihc_phantom_dataset,
    generate_mif_phantom,
    generate_mif_phantom_dataset,
)
from stableseg.pathology.tile import Tile

# tifffile is a core dependency (via scikit-image); OpenSlide is the optional
# [pathology] extra, so only the whole-slide tests are skipped without it.
needs_openslide = pytest.mark.skipif(
    importlib.util.find_spec("openslide") is None,
    reason="pathology extra not installed: pip install -r requirements-pathology.lock",
)

# --------------------------------------------------------------------------
# The shared contract
# --------------------------------------------------------------------------


def test_volume_and_tile_both_speak_the_shared_geometry_contract():
    v = Volume(np.zeros((2, 2, 2)), np.diag([2.0, 2.0, 3.0, 1.0]))
    t = Tile(np.zeros((4, 4, 3), np.uint8), mpp=0.5, synthetic=True)
    assert isinstance(v, ImageBase) and isinstance(t, ImageBase)
    assert (v.unit, v.spacing, v.element_measure) == ("mm", (2.0, 2.0, 3.0), 12.0)
    assert (t.unit, t.spacing, t.element_measure) == ("um", (0.5, 0.5), 0.25)
    assert t.is_synthetic and not v.is_synthetic
    for img in (v, t):
        g = img.describe_geometry()
        assert set(g) >= {"shape", "dtype", "spacing", "unit", "element_measure", "synthetic"}


def test_existing_volume_describe_is_unchanged_by_the_base():
    """Backward compatibility: Volume.describe() keeps its original keys and values."""
    v = Volume(np.ones((3, 3, 3)), np.eye(4))
    d = v.describe()
    assert d["spacing_mm"] == [1.0, 1.0, 1.0] and d["voxel_volume_mm3"] == 1.0 and d["n_nonzero"] == 27


# --------------------------------------------------------------------------
# OME-TIFF
# --------------------------------------------------------------------------


def test_ome_tiff_round_trip_keeps_channels_geometry_and_pixels(tmp_path):
    rng = np.random.default_rng(0)
    t = Tile(
        rng.random((32, 40, 4)).astype(np.float32),
        mpp=0.325,
        channels=("DAPI", "CD3", "CD8", "PanCK"),
        synthetic=True,
        meta={"stain": "mIF"},
    )
    path = write_ome_tiff(t, tmp_path / "t.ome.tiff")
    back = read_ome_tiff(path)
    assert back.channels == t.channels
    assert back.mpp == pytest.approx(0.325)
    assert back.synthetic is True and back.meta["stain"] == "mIF"
    np.testing.assert_array_equal(back.data, t.data)  # zlib is lossless


def test_ome_tiff_reader_refuses_a_plain_tiff(tmp_path):
    import tifffile

    tifffile.imwrite(tmp_path / "plain.tif", np.zeros((8, 8), np.uint8))
    with pytest.raises(ValueError, match="not an OME-TIFF"):
        read_ome_tiff(tmp_path / "plain.tif")


# --------------------------------------------------------------------------
# Pyramidal TIFF -> OpenSlide
# --------------------------------------------------------------------------


@pytest.fixture
def synthetic_slide(tmp_path):
    """A 1024 x 1536 'slide': an oval of tissue-coloured pixels on glass-white, with a pyramid."""
    rng = np.random.default_rng(3)
    h, w = 1024, 1536
    rgb = np.full((h, w, 3), 245, np.uint8)  # glass
    yy, xx = np.mgrid[0:h, 0:w]
    tissue = ((yy - h / 2) / (h * 0.38)) ** 2 + ((xx - w / 2) / (w * 0.40)) ** 2 < 1.0
    colour = np.stack(
        [rng.integers(150, 200, (h, w)), rng.integers(90, 140, (h, w)), rng.integers(170, 220, (h, w))], -1
    )
    rgb[tissue] = colour[tissue].astype(np.uint8)
    path = write_pyramidal_tiff(rgb, mpp=0.5, path=tmp_path / "slide.tif", n_levels=4)
    return path, rgb, tissue


@needs_openslide
def test_openslide_reads_our_pyramid_with_correct_geometry(synthetic_slide):
    path, rgb, _ = synthetic_slide
    with open_slide(path) as s:
        assert s.vendor == "generic-tiff"
        assert s.mpp == pytest.approx(0.5)
        # n_levels=4 is a maximum: 1024 -> 512 -> 256, then a level would be
        # smaller than a 256-px tile, so the writer stops at three.
        assert s.level_count == 3
        assert s.level_dimensions[0] == (1536, 1024)  # (width, height)
        assert s.level_downsamples == pytest.approx((1.0, 2.0, 4.0))
        assert s.mpp_at(2) == pytest.approx(2.0)
        assert s.describe()["field_mm"] == pytest.approx([0.768, 0.512])


@needs_openslide
def test_tile_read_is_pixel_exact_and_carries_geometry(synthetic_slide):
    path, rgb, _ = synthetic_slide
    with open_slide(path) as s:
        t = s.read_tile(256, 512, 128)
        np.testing.assert_array_equal(t.data, rgb[512:640, 256:384])
        assert t.mpp == 0.5 and t.channels == ("R", "G", "B") and t.meta["x0"] == 256
        t1 = s.read_tile(0, 0, 64, level=1)
        assert t1.mpp == pytest.approx(1.0) and t1.level == 1


@needs_openslide
def test_tissue_mask_finds_the_tissue_and_not_the_glass(synthetic_slide):
    path, _, tissue = synthetic_slide
    with open_slide(path) as s:
        mask = s.tissue_mask(max_px=256)
    # compare against the truth at the thumbnail's resolution
    from skimage.transform import resize

    truth = resize(tissue.astype(float), mask.shape, order=0) > 0.5
    agreement = (mask == truth).mean()
    assert agreement > 0.97


@needs_openslide
def test_iter_tiles_counts_and_tissue_filter(synthetic_slide):
    path, _, _ = synthetic_slide
    with open_slide(path) as s:
        all_tiles = list(s.iter_tiles(size=256, tissue_only=False))
        tissue_tiles = list(s.iter_tiles(size=256, tissue_only=True, min_tissue_fraction=0.5))
        capped = list(s.iter_tiles(size=256, tissue_only=True, limit=3))
    assert len(all_tiles) == (1024 // 256) * (1536 // 256)  # 24
    assert 0 < len(tissue_tiles) < len(all_tiles)
    assert len(capped) == 3
    # every tissue tile really is mostly tissue-coloured (not near-white)
    for t in tissue_tiles:
        assert (t.data.mean(axis=2) < 230).mean() > 0.4


@needs_openslide
def test_slide_without_mpp_refuses_to_guess(tmp_path):
    import tifffile

    rgb = np.zeros((512, 512, 3), np.uint8)
    tifffile.imwrite(tmp_path / "nompp.tif", rgb, tile=(256, 256), photometric="rgb")  # no resolution tags
    with open_slide(tmp_path / "nompp.tif") as s:
        with pytest.raises(ValueError, match="no microns-per-pixel"):
            _ = s.mpp


# --------------------------------------------------------------------------
# IHC and mIF phantoms
# --------------------------------------------------------------------------


def test_ihc_phantom_positive_fraction_is_exact():
    _, labels, truths, positive = generate_ihc_phantom(
        seed=1, tile_index=0, n_nuclei=60, positive_fraction=0.35
    )
    assert len(truths) == 60 and positive.sum() == 21
    assert labels.max() == 60


def test_ihc_positive_nuclei_are_browner_than_negative_ones():
    tile, labels, truths, positive = generate_ihc_phantom(seed=1, tile_index=0)
    rgb = tile.data.astype(float)

    # brown = red high relative to blue; blue nuclei the opposite
    def rb(inst):
        m = labels == inst
        return rgb[m, 0].mean() - rgb[m, 2].mean()

    pos_rb = np.mean([rb(t.instance_id) for t, p in zip(truths, positive, strict=True) if p])
    neg_rb = np.mean([rb(t.instance_id) for t, p in zip(truths, positive, strict=True) if not p])
    assert pos_rb > neg_rb + 20


def test_ihc_dataset_writes_manifest_with_truth(tmp_path):
    m = generate_ihc_phantom_dataset(tmp_path, n_tiles=3, positive_fraction=0.5, seed=2)
    assert (m["positive_fraction_true"] == 0.5).all() and m["synthetic"].all()
    assert (tmp_path / "cells.csv").exists()


def test_mif_phantom_phenotype_counts_are_exact():
    tile, labels, truths, phenotypes = generate_mif_phantom(seed=1, tile_index=0, n_cells=80)
    assert len(truths) == 80 and tile.channels == MIF_CHANNELS and tile.data.shape[2] == 5
    counts = {ph: phenotypes.count(ph) for ph in MIF_PHENOTYPES}
    assert counts == {"tumour": 36, "T_helper": 12, "T_cytotoxic": 12, "macrophage": 8, "other": 12}


def test_mif_channels_light_up_only_for_their_phenotypes():
    tile, labels, truths, phenotypes = generate_mif_phantom(seed=1, tile_index=0)
    ck = tile.data[:, :, MIF_CHANNELS.index("PanCK")]
    cd8 = tile.data[:, :, MIF_CHANNELS.index("CD8")]
    for t, ph in zip(truths, phenotypes, strict=True):
        nuc = labels == t.instance_id
        if ph == "tumour":
            assert ck[nuc].mean() > 0.5 and cd8[nuc].mean() < 0.2
        if ph == "T_cytotoxic":
            assert cd8[nuc].mean() > 0.5 and ck[nuc].mean() < 0.2


def test_mif_dataset_round_trips_through_ome_tiff(tmp_path):
    m = generate_mif_phantom_dataset(tmp_path, n_tiles=2, seed=5)
    back = read_ome_tiff(tmp_path / "images" / "mif_phantom_000.ome.tiff")
    assert back.channels == MIF_CHANNELS and back.mpp == 0.5 and back.synthetic
    assert int(m.loc[0, "n_cells_true"]) == 80


def test_he_checkpoint_unchanged_by_the_renderer_refactor():
    tile, labels, truths = generate_he_phantom(seed=42, tile_index=0)
    assert len(truths) == 60 and int((labels > 0).sum()) == 11984  # 2996.0 um2 / 0.25
