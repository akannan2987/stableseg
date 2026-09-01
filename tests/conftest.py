"""Shared test fixtures. `tmp_path` is pytest's throwaway folder, unique per test."""

from __future__ import annotations

import pytest

from stableseg.config import AuditConfig, DataSpec, OutputSpec, PhantomSpec


@pytest.fixture
def small_config(tmp_path) -> AuditConfig:
    """A tiny run that finishes in well under a second."""
    return AuditConfig(
        name="test-run",
        data=DataSpec(
            source="phantom",
            root=tmp_path / "data",
            phantom=PhantomSpec(n_cases=2, shape=(24, 32, 24)),
        ),
        output=OutputSpec(root=tmp_path / "runs", run_name="t"),
    )
