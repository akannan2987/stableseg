"""The version string must be identical in pyproject.toml and the package.

Two places can drift apart; this test makes the release checklist enforceable.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from stableseg import __version__

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_and_package_version_match():
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        declared = tomllib.load(fh)["project"]["version"]
    assert declared == __version__
