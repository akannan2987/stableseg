"""The CLI is a thin wrapper: every command must succeed and print JSON."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from stableseg import __version__
from stableseg.cli import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"stableseg": __version__}


def test_phantom_then_describe(tmp_path, small_config):
    cfg_path = tmp_path / "cfg.yaml"
    small_config.to_yaml(cfg_path)
    result = runner.invoke(app, ["phantom", "--config", str(cfg_path)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["n_cases"] == 2

    image = tmp_path / "data" / "images" / "phantom_001.nii.gz"
    result = runner.invoke(app, ["describe", str(image)])
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["shape"] == [24, 32, 24]


def test_validate_config(tmp_path, small_config):
    cfg_path = tmp_path / "cfg.yaml"
    small_config.to_yaml(cfg_path)
    result = runner.invoke(app, ["validate-config", str(cfg_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["valid"] is True


def test_phantom_runs_from_an_empty_folder_like_an_installed_package(tmp_path, monkeypatch):
    """v0.1.0 shipped a bug this test exists to keep fixed.

    The command's default config was a relative path into the repository
    (configs/phantom.yaml). Inside a project checkout that file exists, so
    every test and every documented example passed - while `pip install`
    followed by `stableseg phantom` on any other machine failed immediately,
    because an installed package carries code, not the repository's folders.

    The trap generalises: a test suite that always runs inside the checkout
    silently assumes the checkout. This test removes the assumption by moving
    to an empty folder first, which is exactly what an installed user's
    current directory looks like.
    """
    monkeypatch.chdir(tmp_path)  # empty folder: no configs/, no data/, no runs/
    result = runner.invoke(app, ["phantom"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    # Defaults must reproduce the reference dataset exactly - same number the
    # tutorials print, so the fallback is provably the same experiment.
    assert payload["n_cases"] == 8
    assert abs(payload["mean_true_volume_mm3"] - 2269.75) < 1e-6
    # And the outputs landed under the folder we ran in, not under the repo.
    assert (tmp_path / "data" / "phantom" / "manifest.csv").exists()
    assert (tmp_path / "runs" / "phantom-smoke" / "run.json").exists()


def test_phantom_prefers_a_local_config_when_one_exists(tmp_path, monkeypatch):
    """The developer case: standing in a checkout, configs/phantom.yaml wins.

    Guarantees the fallback chain cannot reorder itself: an explicit file in
    the working folder must beat built-in defaults, or a developer editing the
    config would silently not be running their edits.
    """
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "phantom.yaml").write_text(
        "name: from-local-file\ndata:\n  phantom:\n    n_cases: 2\noutput:\n  run_name: local-config-run\n"
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["phantom"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["n_cases"] == 2  # the file's value, not the default 8


def test_he_phantom_runs_from_an_empty_folder(tmp_path, monkeypatch):
    """Track P's command must work on an installed copy, like `phantom` does since 0.1.1."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["he-phantom"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["n_tiles"] == 8
    assert abs(payload["mean_true_nuclei"] - 60.0) < 1e-9
    assert (tmp_path / "data" / "he_phantom" / "manifest.csv").exists()
    assert (tmp_path / "runs" / "he-phantom-smoke" / "run.json").exists()


def test_describe_tile_reports_geometry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["he-phantom"])
    result = runner.invoke(app, ["describe-tile", "data/he_phantom/images/he_phantom_000.png"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mpp"] == 0.5
    assert payload["channels"] == ["R", "G", "B"]
    assert payload["synthetic"] is True


def test_datasets_command_lists_the_registry():
    result = runner.invoke(app, ["datasets"])
    assert result.exit_code == 0, result.output
    assert "msd_task04_hippocampus" in json.loads(result.output)


def test_dataset_summary_on_the_phantom_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["phantom"])
    result = runner.invoke(app, ["dataset-summary", "data/phantom", "--manifest", "runs/manifest.csv"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["n_cases"] == 8 and payload["n_with_labels"] == 8
    assert (tmp_path / "runs" / "manifest.csv").exists()


def test_dicom_to_nifti_command(tmp_path, monkeypatch):
    import numpy as np

    from stableseg.dicom import write_synthetic_series

    monkeypatch.chdir(tmp_path)
    write_synthetic_series(
        tmp_path / "series", np.zeros((8, 8, 4), dtype=np.uint16), spacing_mm=(1.0, 1.0, 2.5)
    )
    result = runner.invoke(app, ["dicom-to-nifti", "series", "out/vol.nii.gz"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["spacing_mm"] == [1.0, 1.0, 2.5]


def test_ihc_and_mif_phantom_commands_from_an_empty_folder(tmp_path, monkeypatch):
    pytest.importorskip("tifffile")
    monkeypatch.chdir(tmp_path)
    r1 = runner.invoke(app, ["ihc-phantom"])
    assert r1.exit_code == 0, r1.output
    assert abs(json.loads(r1.output)["mean_positive_fraction_true"] - 0.35) < 1e-9
    r2 = runner.invoke(app, ["mif-phantom"])
    assert r2.exit_code == 0, r2.output
    assert json.loads(r2.output)["mean_phenotype_counts_true"]["tumour"] == 36.0


def test_describe_slide_and_slide_tiles_commands(tmp_path, monkeypatch):
    pytest.importorskip("openslide")
    import numpy as np

    from stableseg.pathology.io import write_pyramidal_tiff

    monkeypatch.chdir(tmp_path)
    # Coloured "tissue" on white glass: a flat grey picture has no colour
    # saturation and the tissue detector would (correctly) find nothing.
    rgb = np.full((512, 768, 3), 245, np.uint8)
    rgb[64:448, 64:704] = (180, 110, 190)
    write_pyramidal_tiff(rgb, 0.25, tmp_path / "s.tif", n_levels=2)
    r = runner.invoke(app, ["describe-slide", "s.tif"])
    assert r.exit_code == 0, r.output
    assert json.loads(r.output)["mpp"] == 0.25
    r = runner.invoke(app, ["slide-tiles", "s.tif", "--out", "tiles", "--limit", "4"])
    assert r.exit_code == 0, r.output
    assert json.loads(r.output)["n_tiles"] == 4
    assert (tmp_path / "tiles" / "tile_0003.json").exists()
