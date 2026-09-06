"""The public API: plain Python functions with typed inputs and JSON-friendly outputs.

Everything a person can do from the command line is a call into this module,
and so is everything a future web app, service or tool server will do. The
CLI adds nothing but argument parsing on top. Keeping the real behaviour here,
and keeping the return values plain dictionaries and paths, is what makes the
engine callable from anywhere without rewriting it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stableseg import __version__
from stableseg.config import AuditConfig
from stableseg.io import load_volume
from stableseg.pathology.phantom import generate_he_phantom_dataset
from stableseg.pathology.tile import load_tile
from stableseg.phantom import generate_phantom_dataset
from stableseg.storage import LocalStorage, stamp_run


def version() -> dict[str, str]:
    """Package version, as a dictionary so every API call has the same shape."""
    return {"stableseg": __version__}


def describe_volume(path: str | Path) -> dict[str, Any]:
    """Load a NIfTI file and return its geometry and intensity summary."""
    vol = load_volume(path)
    out = vol.describe()
    out["path"] = str(Path(path))
    return out


def generate_phantoms(config: AuditConfig) -> dict[str, Any]:
    """Generate the synthetic dataset described by `config.data.phantom` into `config.data.root`.

    Also stamps a run folder with `run.json` so even data generation has provenance.
    """
    spec = config.data.phantom
    manifest = generate_phantom_dataset(
        root=config.data.root,
        n_cases=spec.n_cases,
        shape=spec.shape,
        spacing_mm=spec.spacing_mm,
        noise_sd=spec.noise_sd,
        seed=spec.seed,
    )
    storage = LocalStorage(config.output.root, config.output.run_name)
    stamp_run(
        storage,
        config.model_dump(mode="json"),
        extra={"step": "generate_phantoms", "n_cases": int(len(manifest))},
    )
    return {
        "data_root": str(Path(config.data.root).resolve()),
        "n_cases": int(len(manifest)),
        "manifest": str((Path(config.data.root) / "manifest.csv").resolve()),
        "run_dir": str(storage.run_dir),
        "mean_true_volume_mm3": float(manifest["true_volume_total_mm3"].mean()),
    }


def describe_tile(path: str | Path) -> dict[str, Any]:
    """Load a PNG tile (with its geometry sidecar) and return its geometry and intensity summary."""
    tile = load_tile(path)
    out = tile.describe()
    out["path"] = str(Path(path))
    return out


def generate_he_phantoms(config: AuditConfig) -> dict[str, Any]:
    """Generate the synthetic H&E tiles described by `config.data.he_phantom` into `config.data.root`.

    Track P's twin of `generate_phantoms`: same provenance stamp, same shape of
    result, a different reference number - the mean true nucleus count.
    """
    spec = config.data.he_phantom
    manifest = generate_he_phantom_dataset(
        root=config.data.root,
        n_tiles=spec.n_tiles,
        shape=spec.shape,
        mpp=spec.mpp,
        n_nuclei=spec.n_nuclei,
        nucleus_radius_um=spec.nucleus_radius_um,
        illumination_strength=spec.illumination_strength,
        noise_sd=spec.noise_sd,
        seed=spec.seed,
    )
    storage = LocalStorage(config.output.root, config.output.run_name)
    stamp_run(
        storage,
        config.model_dump(mode="json"),
        extra={"step": "generate_he_phantoms", "n_tiles": int(len(manifest)), "modality": "pathology"},
    )
    return {
        "data_root": str(Path(config.data.root).resolve()),
        "n_tiles": int(len(manifest)),
        "manifest": str((Path(config.data.root) / "manifest.csv").resolve()),
        "run_dir": str(storage.run_dir),
        "mean_true_nuclei": float(manifest["n_nuclei_true"].mean()),
        "mean_nuclear_area_um2": float(manifest["nuclear_area_um2"].mean()),
    }
