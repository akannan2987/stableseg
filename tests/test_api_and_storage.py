"""The API layer must work without the CLI, and storage must keep provenance."""

from __future__ import annotations

from pathlib import Path

from stableseg import __version__, api
from stableseg.storage import LocalStorage


def test_version_shape():
    assert api.version() == {"stableseg": __version__}


def test_generate_phantoms_writes_data_and_provenance(small_config):
    result = api.generate_phantoms(small_config)
    assert result["n_cases"] == 2
    assert Path(result["manifest"]).exists()
    run = LocalStorage(small_config.output.root, small_config.output.run_name)
    stamp = run.read_json("run.json")
    assert stamp["stableseg_version"] == __version__
    assert stamp["step"] == "generate_phantoms"
    assert stamp["config"]["data"]["phantom"]["n_cases"] == 2


def test_describe_volume(small_config):
    api.generate_phantoms(small_config)
    info = api.describe_volume(Path(small_config.data.root) / "images" / "phantom_000.nii.gz")
    assert info["shape"] == [24, 32, 24]
    assert info["spacing_mm"] == [1.0, 1.0, 1.0]
    assert info["max"] > info["min"]


def test_local_storage_is_scoped(tmp_path):
    s = LocalStorage(tmp_path, "r1")
    p = s.write_json("x.json", {"a": 1})
    assert p.parent == tmp_path / "r1"
    assert s.read_json("x.json") == {"a": 1}
    assert s.list() == ["x.json"]
    assert not s.exists("missing.json")
