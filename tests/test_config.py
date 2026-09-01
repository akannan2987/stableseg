"""Config validation: good files load, bad values are refused with a clear message."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from stableseg.config import AuditConfig

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_default_config_is_valid():
    cfg = AuditConfig()
    assert cfg.data.source == "phantom"
    assert cfg.data.phantom.seed == 42


def test_yaml_roundtrip(tmp_path):
    cfg = AuditConfig(name="rt")
    p = tmp_path / "cfg.yaml"
    cfg.to_yaml(p)
    again = AuditConfig.from_yaml(p)
    assert again == cfg


def test_repo_config_file_loads():
    cfg = AuditConfig.from_yaml(REPO_ROOT / "configs" / "phantom.yaml")
    assert cfg.output.run_name == "phantom-smoke"


def test_rejects_tiny_shape():
    with pytest.raises(ValidationError):
        AuditConfig.model_validate({"data": {"phantom": {"shape": [8, 8, 8]}}})


def test_rejects_unsafe_run_name():
    with pytest.raises(ValidationError):
        AuditConfig.model_validate({"output": {"run_name": "bad name/with slash"}})
