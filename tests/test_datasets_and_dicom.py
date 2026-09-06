"""Phase V2: fetching real data safely, cataloguing it, and reading DICOM.

None of these tests touch the network. The fetch path is exercised against a
tar file built on the spot and served through a `file://` URL - which the
standard library's downloader accepts - so every step that would run against
the real archive runs here against a known one: download, checksum, refusal
on mismatch, extraction, AppleDouble filtering, idempotence.

The DICOM tests write a series with pydicom and read it back with SimpleITK -
two independent implementations of the standard agreeing on geometry - so
hospital-format support is verified with no patient data anywhere.
"""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import numpy as np
import pytest

from stableseg import datasets
from stableseg.datasets import DatasetInfo, extract_archive, fetch, md5_of, verify_md5
from stableseg.dicom import read_series, series_to_nifti, write_synthetic_series
from stableseg.io import load_volume, scan_dataset_folder
from stableseg.phantom import generate_phantom_dataset

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _make_dataset_tar(tmp_path: Path, with_apple_double: bool = True) -> Path:
    """A tiny Decathlon-shaped archive: imagesTr/labelsTr with two phantoms, plus junk."""
    src = tmp_path / "src"
    generate_phantom_dataset(
        src, n_cases=2, shape=(16, 16, 16), spacing_mm=(1.0, 1.0, 1.0), noise_sd=0.0, seed=1
    )
    tar_path = tmp_path / "Mini.tar"
    with tarfile.open(tar_path, "w") as tf:
        for sub, dest_name in (("images", "imagesTr"), ("labels", "labelsTr")):
            for f in sorted((src / sub).iterdir()):
                tf.add(f, arcname=f"Mini/{dest_name}/{f.name}")
                if with_apple_double:
                    junk = tarfile.TarInfo(f"Mini/{dest_name}/._{f.name}")
                    junk.size = 4
                    tf.addfile(junk, io.BytesIO(b"junk"))
    return tar_path


def _register_local(tmp_path: Path, tar_path: Path, md5: str) -> str:
    key = "test_local_mini"
    datasets.DATASETS[key] = DatasetInfo(
        key=key,
        title="local test archive",
        url=tar_path.resolve().as_uri(),  # file:///... - no network
        md5=md5,
        archive_name="Mini.tar",
        unpacked_dir="Mini",
        license="test",
        data_card="none",
        approx_mb=0,
        track="V",
    )
    return key


@pytest.fixture
def local_dataset(tmp_path):
    tar_path = _make_dataset_tar(tmp_path)
    key = _register_local(tmp_path, tar_path, md5_of(tar_path))
    yield key, tar_path, tmp_path / "dl"
    datasets.DATASETS.pop(key, None)


# --------------------------------------------------------------------------
# checksums
# --------------------------------------------------------------------------


def test_md5_matches_hashlib_and_is_case_insensitive(tmp_path):
    import hashlib

    f = tmp_path / "x.bin"
    f.write_bytes(b"stableseg" * 1000)
    expected = hashlib.md5(f.read_bytes()).hexdigest()  # noqa: S324
    assert md5_of(f) == expected
    assert verify_md5(f, expected.upper())


def test_one_changed_byte_changes_the_fingerprint(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"a" * 100)
    before = md5_of(f)
    f.write_bytes(b"a" * 99 + b"b")
    assert md5_of(f) != before


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------


def test_extract_drops_apple_double_companions(tmp_path):
    tar_path = _make_dataset_tar(tmp_path)
    out = extract_archive(tar_path, tmp_path / "out")
    names = sorted(p.name for p in (out / "Mini" / "imagesTr").iterdir())
    assert names == ["phantom_000.nii.gz", "phantom_001.nii.gz"]
    assert not any(n.startswith("._") for n in names)


def test_extract_refuses_paths_escaping_the_destination(tmp_path):
    evil = tmp_path / "evil.tar"
    with tarfile.open(evil, "w") as tf:
        info = tarfile.TarInfo("../escaped.txt")
        info.size = 3
        tf.addfile(info, io.BytesIO(b"bad"))
    extract_archive(evil, tmp_path / "out")
    assert not (tmp_path / "escaped.txt").exists()


# --------------------------------------------------------------------------
# fetch: download + verify + unpack, with no network
# --------------------------------------------------------------------------


def test_fetch_downloads_verifies_and_unpacks(local_dataset):
    key, _, dest = local_dataset
    result = fetch(key, dest_root=dest)
    assert "MD5 verified" in result["steps"]
    assert (dest / "Mini" / "imagesTr" / "phantom_000.nii.gz").exists()
    assert not (dest / "Mini.tar.part").exists()  # temporary name was renamed away


def test_fetch_is_idempotent(local_dataset):
    key, _, dest = local_dataset
    fetch(key, dest_root=dest)
    second = fetch(key, dest_root=dest)
    assert "archive already present and verified" in second["steps"]
    assert "already unpacked" in second["steps"]


def test_fetch_refuses_and_deletes_on_checksum_mismatch(tmp_path):
    tar_path = _make_dataset_tar(tmp_path)
    key = _register_local(tmp_path, tar_path, "0" * 32)  # deliberately wrong seal
    try:
        with pytest.raises(RuntimeError, match="MD5 does not match"):
            fetch(key, dest_root=tmp_path / "dl")
        assert not (tmp_path / "dl" / "Mini.tar").exists()  # never kept
    finally:
        datasets.DATASETS.pop(key, None)


def test_unknown_dataset_key_is_a_clear_error():
    with pytest.raises(KeyError, match="unknown dataset"):
        fetch("does_not_exist")


def test_registry_entries_are_complete():
    """Every registered dataset points at a data card that exists and a licence that is stated."""
    repo = Path(__file__).resolve().parents[1]
    for info in datasets.DATASETS.values():
        if info.key.startswith("test_"):
            continue
        assert (repo / info.data_card).exists(), info.data_card
        assert info.license and info.md5 and len(info.md5) == 32


# --------------------------------------------------------------------------
# cataloguing
# --------------------------------------------------------------------------


def test_scan_folder_understands_both_layouts(tmp_path):
    tar_path = _make_dataset_tar(tmp_path)
    extract_archive(tar_path, tmp_path / "out")
    decathlon = scan_dataset_folder(tmp_path / "out" / "Mini")
    ours = scan_dataset_folder(tmp_path / "src")
    assert list(decathlon["case_id"]) == list(ours["case_id"]) == ["phantom_000", "phantom_001"]
    assert (decathlon["label"] != "").all()
    assert (decathlon["spacing_x_mm"] == 1.0).all()
    assert set(decathlon["split"]) == {"train"}


def test_scan_folder_keeps_unlabelled_test_images(tmp_path):
    root = tmp_path / "d"
    generate_phantom_dataset(root, n_cases=1, shape=(16, 16, 16), spacing_mm=(1, 1, 1), noise_sd=0.0, seed=2)
    (root / "images").rename(root / "imagesTr")
    (root / "labels").rename(root / "labelsTr")
    (root / "imagesTs").mkdir()
    (root / "imagesTs" / "phantom_999.nii.gz").write_bytes(
        (root / "imagesTr" / "phantom_000.nii.gz").read_bytes()
    )
    table = scan_dataset_folder(root)
    assert len(table) == 2
    test_row = table[table["case_id"] == "phantom_999"].iloc[0]
    assert test_row["split"] == "test" and test_row["label"] == ""


def test_scan_folder_refuses_a_folder_that_is_not_a_dataset(tmp_path):
    with pytest.raises(ValueError, match="neither images/ nor imagesTr/"):
        scan_dataset_folder(tmp_path)


# --------------------------------------------------------------------------
# DICOM
# --------------------------------------------------------------------------


def test_dicom_round_trip_recovers_pixels_and_spacing(tmp_path):
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 4000, size=(20, 24, 12), dtype=np.uint16)
    write_synthetic_series(tmp_path / "s", arr, spacing_mm=(0.8, 0.9, 2.0), origin_mm=(10.0, -5.0, 3.0))
    vol = read_series(tmp_path / "s")
    assert vol.shape == (20, 24, 12)
    assert vol.spacing_mm == pytest.approx((0.8, 0.9, 2.0))
    np.testing.assert_array_equal(vol.data.astype(np.uint16), arr)
    assert vol.meta["n_slices"] == 12 and vol.meta["modality"] == "MR"


def test_dicom_origin_is_converted_from_lps_to_ras(tmp_path):
    arr = np.zeros((4, 4, 3), dtype=np.uint16)
    write_synthetic_series(tmp_path / "s", arr, origin_mm=(10.0, -5.0, 3.0))
    vol = read_series(tmp_path / "s")
    # LPS (10, -5, 3) -> RAS (-10, 5, 3): x and y flip sign, z does not
    np.testing.assert_allclose(vol.affine[:3, 3], [-10.0, 5.0, 3.0])


def test_dicom_to_nifti_preserves_geometry(tmp_path):
    arr = np.arange(6 * 5 * 4, dtype=np.uint16).reshape(6, 5, 4)
    write_synthetic_series(tmp_path / "s", arr, spacing_mm=(1.5, 1.5, 3.0))
    out = series_to_nifti(tmp_path / "s", tmp_path / "vol.nii.gz")
    back = load_volume(out)
    assert back.shape == (6, 5, 4)
    assert back.spacing_mm == pytest.approx((1.5, 1.5, 3.0))
    np.testing.assert_array_equal(back.data.astype(np.uint16), arr)


def test_dicom_reader_refuses_empty_or_mixed_folders(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="no DICOM series"):
        read_series(tmp_path / "empty")
    # two different series in one folder must be refused, not silently merged
    arr = np.zeros((4, 4, 2), dtype=np.uint16)
    write_synthetic_series(tmp_path / "mixed", arr)
    write_synthetic_series(tmp_path / "mixed2", arr)
    for f in (tmp_path / "mixed2").iterdir():
        f.rename(tmp_path / "mixed" / f"b_{f.name}")
    with pytest.raises(ValueError, match="2 DICOM series"):
        read_series(tmp_path / "mixed")


def test_synthetic_series_carries_no_patient_identity(tmp_path):
    import pydicom

    write_synthetic_series(tmp_path / "s", np.zeros((4, 4, 1), dtype=np.uint16))
    ds = pydicom.dcmread(next((tmp_path / "s").iterdir()))
    assert str(ds.PatientName) == "ANONYMOUS"
    assert "synthetic" in ds.SeriesDescription.lower()
