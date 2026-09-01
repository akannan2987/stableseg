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
