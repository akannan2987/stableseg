"""Storage: where run outputs live, behind one small interface.

Today everything is a folder on disk. Later it may be a shared drive, an
object store in the cloud, or a database. If the rest of the code only ever
talks to `Storage`, swapping the backend is one new class, not a rewrite.
That is the whole reason this file exists.

A `Storage` is scoped to ONE run: `Storage(root="runs", run_name="x")`
owns `runs/x/` and nothing outside it.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class Storage(ABC):
    """The contract every backend must honour."""

    @abstractmethod
    def path(self, *parts: str) -> Path:
        """Absolute path of a file inside this run (backend may create parents)."""

    @abstractmethod
    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        """Persist a small JSON document."""

    @abstractmethod
    def read_json(self, name: str) -> dict[str, Any]:
        """Read a JSON document written by `write_json`."""

    @abstractmethod
    def exists(self, *parts: str) -> bool:
        """Does this file exist in the run?"""

    @abstractmethod
    def list(self, subdir: str = "") -> list[str]:
        """Names of files directly inside `subdir` of the run."""


class LocalStorage(Storage):
    """A run folder on the local disk. `pathlib` keeps it OS-independent."""

    def __init__(self, root: str | Path, run_name: str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.run_name = run_name
        self.run_dir = self.root / run_name
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        target = self.run_dir.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        target = self.path(name)
        with target.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True, default=str)
        return target

    def read_json(self, name: str) -> dict[str, Any]:
        with self.path(name).open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def exists(self, *parts: str) -> bool:
        return self.run_dir.joinpath(*parts).exists()

    def list(self, subdir: str = "") -> list[str]:
        folder = self.run_dir / subdir if subdir else self.run_dir
        if not folder.exists():
            return []
        return sorted(p.name for p in folder.iterdir() if p.is_file())

    def __repr__(self) -> str:
        return f"LocalStorage({self.run_dir})"


def stamp_run(storage: Storage, config_dump: dict[str, Any], extra: dict[str, Any] | None = None) -> Path:
    """Write `run.json`: who ran what, when, with which settings and package version.

    Provenance in one file. If a number is questioned later, this is the
    first thing you open.
    """
    from stableseg import __version__

    payload: dict[str, Any] = {
        "stableseg_version": __version__,
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": config_dump,
    }
    if extra:
        payload.update(extra)
    return storage.write_json("run.json", payload)
