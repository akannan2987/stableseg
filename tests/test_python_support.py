"""The declared Python range must match reality.

Two failures this file exists to prevent, both of which have bitten this
project already:

1. The range in `pyproject.toml` says one thing and the interpreter actually
   running the tests is outside it. That means someone built an environment
   the project does not support, and every later error would be confusing.
2. The range is written from memory rather than derived from what the pinned
   dependencies actually require. `numpy` and `scipy` raised their floor to
   Python 3.12; a range still claiming 3.11 would let pip get several minutes
   into an install before refusing.

The second check is offline on purpose: it reads the declared range and the
lock file, not the network, so the test suite stays fast and works on a
machine with no internet. The live check against PyPI is documented in
`docs/04-phase-tutorials/phase-01-skeleton.md` and belongs in the release
checklist, not in every test run.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Packages known to set the effective floor, with the minimum they require.
# Update this table whenever requirements.lock is regenerated, after checking
# the real value with the PyPI query shown in the phase 1 tutorial.
DEPENDENCY_FLOORS = {
    "numpy": (3, 12),
    "scipy": (3, 12),
}


def _declared_range() -> str:
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["requires-python"]


def _bounds(spec: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Parse '>=3.12,<3.14' into ((3, 12), (3, 14))."""
    lower = re.search(r">=\s*(\d+)\.(\d+)", spec)
    upper = re.search(r"<\s*(\d+)\.(\d+)", spec)
    assert lower and upper, f"could not parse requires-python: {spec!r}"
    return (int(lower[1]), int(lower[2])), (int(upper[1]), int(upper[2]))


def test_running_interpreter_is_inside_the_declared_range():
    low, high = _bounds(_declared_range())
    current = sys.version_info[:2]
    assert low <= current < high, (
        f"running Python {current[0]}.{current[1]}, but this project declares "
        f"{_declared_range()}. Rebuild the virtual environment on a supported "
        f"interpreter (see your setup guide, section 6)."
    )


def test_declared_floor_is_at_least_what_the_dependencies_demand():
    low, _ = _bounds(_declared_range())
    for package, floor in DEPENDENCY_FLOORS.items():
        assert low >= floor, (
            f"{package} requires Python >= {floor[0]}.{floor[1]}, but this "
            f"project declares {_declared_range()}. A user on a version below "
            f"the dependency floor gets an install failure instead of a clear "
            f"refusal. Raise the floor in pyproject.toml."
        )


def test_lock_file_pins_the_floor_setting_packages():
    """If a floor-setting package leaves the lock file, this table is stale."""
    lock = (REPO_ROOT / "requirements.lock").read_text().lower()
    for package in DEPENDENCY_FLOORS:
        assert f"{package}==" in lock, (
            f"{package} is no longer pinned in requirements.lock; re-check the "
            f"DEPENDENCY_FLOORS table in this file against the new pins."
        )
