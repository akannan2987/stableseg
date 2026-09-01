"""The phantom generator must be deterministic, physically sensible, and honest about its truth."""

from __future__ import annotations

import numpy as np

from stableseg.io import label_volume_mm3, load_volume
from stableseg.phantom import generate_phantom_dataset, make_phantom_case


def test_same_seed_same_phantom():
    a = make_phantom_case(3, shape=(24, 32, 24), seed=7)
    b = make_phantom_case(3, shape=(24, 32, 24), seed=7)
    assert np.array_equal(a.image.data, b.image.data)
    assert np.array_equal(a.label.data, b.label.data)


def test_different_seed_different_phantom():
    a = make_phantom_case(0, shape=(24, 32, 24), seed=1)
    b = make_phantom_case(0, shape=(24, 32, 24), seed=2)
    assert not np.array_equal(a.image.data, b.image.data)


def test_labels_are_1_and_2_and_non_empty():
    case = make_phantom_case(0, shape=(48, 64, 48))
    values = set(np.unique(case.label.data).tolist())
    assert values == {0, 1, 2}
    assert case.true_volume_mm3[1] > 0
    assert case.true_volume_mm3[2] > 0


def test_truth_matches_voxel_count_times_voxel_size():
    case = make_phantom_case(0, shape=(24, 32, 24), spacing_mm=(2.0, 1.0, 1.5))
    n1 = int((case.label.data == 1).sum())
    assert np.isclose(case.true_volume_mm3[1], n1 * 3.0)
    assert np.isclose(label_volume_mm3(case.label, 1), case.true_volume_mm3[1])


def test_dataset_roundtrip(tmp_path):
    manifest = generate_phantom_dataset(tmp_path, n_cases=2, shape=(24, 32, 24))
    assert len(manifest) == 2
    assert (tmp_path / "manifest.csv").exists()
    lbl = load_volume(tmp_path / "labels" / "phantom_000.nii.gz")
    img = load_volume(tmp_path / "images" / "phantom_000.nii.gz")
    assert lbl.shape == img.shape == (24, 32, 24)
    # The volume recomputed from the saved file must equal the manifest's truth.
    assert np.isclose(label_volume_mm3(lbl, 1), manifest.loc[0, "true_volume_label1_mm3"])
