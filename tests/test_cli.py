"""The CLI is a thin wrapper: every command must succeed and print JSON."""

from __future__ import annotations

import json

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
