"""Track P's synthetic H&E phantom: known truth, determinism, geometry that travels.

These mirror tests/test_phantom.py deliberately. Where that file checks that
a volume's voxel spacing survives a round trip, this one checks that a tile's
microns-per-pixel does; where that one checks a known volume, this checks a
known nucleus count.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from stableseg.pathology.phantom import (
    STAIN_VECTORS,
    generate_he_phantom,
    generate_he_phantom_dataset,
    render_he,
)
from stableseg.pathology.tile import Tile, load_label_tile, load_tile, save_tile

# --------------------------------------------------------------------------
# Tile: geometry never separated from numbers
# --------------------------------------------------------------------------


def test_tile_pixel_area_follows_from_mpp():
    t = Tile(data=np.zeros((10, 10, 3), dtype=np.uint8), mpp=0.5)
    assert t.pixel_area_um2 == pytest.approx(0.25)
    assert t.field_um == pytest.approx((5.0, 5.0))


def test_tile_refuses_mismatched_channel_names():
    with pytest.raises(ValueError):
        Tile(data=np.zeros((4, 4, 3), dtype=np.uint8), mpp=0.5, channels=("R", "G"))


def test_tile_refuses_nonpositive_mpp():
    with pytest.raises(ValueError):
        Tile(data=np.zeros((4, 4, 3), dtype=np.uint8), mpp=0.0)


def test_single_channel_tile_becomes_three_axes():
    t = Tile(data=np.zeros((4, 4), dtype=np.uint8), mpp=1.0, channels=("gray",))
    assert t.shape == (4, 4, 1)


def test_tile_round_trip_keeps_geometry_and_pixels(tmp_path):
    tile, _, _ = generate_he_phantom(seed=1, tile_index=0, shape=(64, 64))
    path = save_tile(tile, tmp_path / "t.png")
    back = load_tile(path)
    assert back.mpp == tile.mpp
    assert back.channels == tile.channels
    assert back.synthetic is True
    assert back.meta["stain"] == "H&E"
    np.testing.assert_array_equal(back.data, tile.data)  # PNG is lossless


def test_loading_a_tile_without_geometry_refuses(tmp_path):
    from PIL import Image

    Image.new("RGB", (8, 8)).save(tmp_path / "orphan.png")
    with pytest.raises(FileNotFoundError):
        load_tile(tmp_path / "orphan.png")


# --------------------------------------------------------------------------
# The optical-density model
# --------------------------------------------------------------------------


def test_stain_vectors_are_unit_length():
    """Ruifrok-style vectors are unit OD directions; anything else is a typo."""
    norms = np.linalg.norm(STAIN_VECTORS, axis=1)
    assert np.allclose(norms, 1.0, atol=0.02)


def test_more_hematoxylin_means_darker_and_bluer():
    """Absorbing more light must lower brightness, and hematoxylin absorbs red most."""
    low = render_he(np.full((2, 2), 0.1, np.float32), np.full((2, 2), 0.3, np.float32))
    high = render_he(np.full((2, 2), 1.2, np.float32), np.full((2, 2), 0.3, np.float32))
    assert high.mean() < low.mean()
    # hematoxylin absorbs red (0.65) more than blue (0.29): red drops more than blue
    red_drop = int(low[0, 0, 0]) - int(high[0, 0, 0])
    blue_drop = int(low[0, 0, 2]) - int(high[0, 0, 2])
    assert red_drop > blue_drop


# --------------------------------------------------------------------------
# The phantom: known truth and determinism
# --------------------------------------------------------------------------


def test_same_seed_same_tile():
    a, la, ta = generate_he_phantom(seed=7, tile_index=2, shape=(96, 96))
    b, lb, tb = generate_he_phantom(seed=7, tile_index=2, shape=(96, 96))
    np.testing.assert_array_equal(a.data, b.data)
    np.testing.assert_array_equal(la, lb)
    assert ta == tb


def test_different_tile_index_different_tile():
    a, _, _ = generate_he_phantom(seed=7, tile_index=0, shape=(96, 96))
    b, _, _ = generate_he_phantom(seed=7, tile_index=1, shape=(96, 96))
    assert not np.array_equal(a.data, b.data)


def test_label_map_agrees_with_truth_table():
    """Every drawn nucleus is in the label map with exactly its recorded area, and nothing else is."""
    _, labels, truths = generate_he_phantom(seed=3, tile_index=0, shape=(128, 128), n_nuclei=30)
    ids = np.unique(labels[labels > 0])
    assert len(ids) == len(truths) == 30
    for t in truths:
        assert int((labels == t.instance_id).sum()) == t.area_px


def test_nuclei_do_not_overlap():
    _, labels, truths = generate_he_phantom(seed=3, tile_index=1, shape=(128, 128), n_nuclei=40)
    # If two ellipses overlapped, the later one would have overwritten pixels of
    # the earlier one and its recorded area would exceed what remains in the map.
    assert sum(t.area_px for t in truths) == int((labels > 0).sum())


def test_nucleus_sizes_respect_the_micron_range():
    _, _, truths = generate_he_phantom(seed=5, tile_index=0, mpp=0.5, nucleus_radius_um=(3.0, 6.0))
    for t in truths:
        assert 3.0 / 0.5 <= t.semi_axis_a_px <= 6.0 / 0.5
        assert t.semi_axis_b_px <= t.semi_axis_a_px


def test_dataset_roundtrip_and_reference_value(tmp_path):
    """The written files reproduce the truth table, and the default set gives the documented number."""
    manifest = generate_he_phantom_dataset(
        root=tmp_path,
        n_tiles=8,
        shape=(256, 256),
        mpp=0.5,
        n_nuclei=60,
        nucleus_radius_um=(3.0, 6.0),
        illumination_strength=0.08,
        noise_sd=0.02,
        seed=42,
    )
    assert len(manifest) == 8
    assert (manifest["n_nuclei_true"] == 60).all()
    assert manifest["synthetic"].all()
    # the reference number printed by `stableseg he-phantom`
    assert manifest["nuclear_area_um2"].mean() == pytest.approx(2950.875)
    # the label file on disk matches the manifest's area
    labels = load_label_tile(tmp_path / "labels" / "he_phantom_000.png")
    assert (labels > 0).sum() * 0.25 == pytest.approx(manifest.loc[0, "nuclear_area_um2"])
    # the geometry sidecar says synthetic, so nobody downstream has to remember
    side = json.loads((tmp_path / "images" / "he_phantom_000.json").read_text())
    assert side["synthetic"] is True and side["mpp"] == 0.5
    assert (tmp_path / "nuclei.csv").exists()
