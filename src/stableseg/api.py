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
from stableseg import datasets as _datasets
from stableseg.config import AuditConfig
from stableseg.dicom import series_to_nifti
from stableseg.io import load_volume, scan_dataset_folder
from stableseg.pathology.phantom import (
    generate_he_phantom_dataset,
    generate_ihc_phantom_dataset,
    generate_mif_phantom_dataset,
)
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


def fetch_dataset(key: str, dest_root: str | Path = "data", force: bool = False) -> dict[str, Any]:
    """Download (if needed), verify by checksum, and unpack a registered dataset."""
    return _datasets.fetch(key, dest_root=dest_root, force=force)


def list_datasets() -> dict[str, Any]:
    """The registry, as plain data: what can be fetched, under what licence, with which data card."""
    return {
        k: {
            "title": v.title,
            "license": v.license,
            "approx_mb": v.approx_mb,
            "track": v.track,
            "data_card": v.data_card,
        }
        for k, v in _datasets.DATASETS.items()
    }


def dataset_summary(root: str | Path, manifest_out: str | Path | None = None) -> dict[str, Any]:
    """Catalogue a folder of scans; optionally write the table as CSV; return a summary.

    The summary is the first thing to read about any new dataset: how many
    cases, how many with outlines, and - above all - the range of voxel
    spacings, because a dataset whose spacing varies is a dataset whose volumes
    must be compared in millimetres, never in voxels.
    """
    table = scan_dataset_folder(root, read_geometry=True)
    if manifest_out is not None:
        Path(manifest_out).parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(manifest_out, index=False)
    out: dict[str, Any] = {
        "root": str(Path(root).resolve()),
        "n_cases": int(len(table)),
        "n_with_labels": int((table["label"] != "").sum()),
        "n_train": int((table["split"] == "train").sum()),
        "n_test": int((table["split"] == "test").sum()),
    }
    if len(table):
        for ax in ("x", "y", "z"):
            out[f"spacing_{ax}_mm_min"] = float(table[f"spacing_{ax}_mm"].min())
            out[f"spacing_{ax}_mm_max"] = float(table[f"spacing_{ax}_mm"].max())
            out[f"shape_{ax}_min"] = int(table[f"shape_{ax}"].min())
            out[f"shape_{ax}_max"] = int(table[f"shape_{ax}"].max())
    if manifest_out is not None:
        out["manifest"] = str(Path(manifest_out).resolve())
    return out


def dicom_to_nifti(series_dir: str | Path, out_path: str | Path) -> dict[str, Any]:
    """Convert one DICOM series folder to a NIfTI file and describe the result."""
    written = series_to_nifti(series_dir, out_path)
    vol = load_volume(written)
    out = vol.describe()
    out["path"] = str(written)
    return out


def generate_ihc_phantoms(config: AuditConfig) -> dict[str, Any]:
    """Generate synthetic IHC tiles with a known positive fraction into `config.data.root`."""
    spec = config.data.ihc_phantom
    manifest = generate_ihc_phantom_dataset(
        root=config.data.root,
        n_tiles=spec.n_tiles,
        positive_fraction=spec.positive_fraction,
        seed=spec.seed,
        shape=spec.shape,
        mpp=spec.mpp,
        n_nuclei=spec.n_nuclei,
        nucleus_radius_um=spec.nucleus_radius_um,
        illumination_strength=spec.illumination_strength,
        noise_sd=spec.noise_sd,
    )
    storage = LocalStorage(config.output.root, config.output.run_name)
    stamp_run(
        storage,
        config.model_dump(mode="json"),
        extra={"step": "generate_ihc_phantoms", "n_tiles": int(len(manifest)), "modality": "pathology"},
    )
    return {
        "data_root": str(Path(config.data.root).resolve()),
        "n_tiles": int(len(manifest)),
        "manifest": str((Path(config.data.root) / "manifest.csv").resolve()),
        "run_dir": str(storage.run_dir),
        "mean_positive_fraction_true": float(manifest["positive_fraction_true"].mean()),
    }


def generate_mif_phantoms(config: AuditConfig) -> dict[str, Any]:
    """Generate synthetic multiplex-IF tiles (OME-TIFF) with known phenotypes into `config.data.root`."""
    spec = config.data.mif_phantom
    manifest = generate_mif_phantom_dataset(
        root=config.data.root,
        n_tiles=spec.n_tiles,
        seed=spec.seed,
        shape=spec.shape,
        mpp=spec.mpp,
        n_cells=spec.n_cells,
        nucleus_radius_um=spec.nucleus_radius_um,
        noise_sd=spec.noise_sd,
    )
    storage = LocalStorage(config.output.root, config.output.run_name)
    stamp_run(
        storage,
        config.model_dump(mode="json"),
        extra={"step": "generate_mif_phantoms", "n_tiles": int(len(manifest)), "modality": "pathology"},
    )
    counts = {
        c[2:-5]: float(manifest[c].mean())
        for c in manifest.columns
        if c.startswith("n_") and c.endswith("_true") and c != "n_cells_true"
    }
    return {
        "data_root": str(Path(config.data.root).resolve()),
        "n_tiles": int(len(manifest)),
        "manifest": str((Path(config.data.root) / "manifest.csv").resolve()),
        "run_dir": str(storage.run_dir),
        "mean_cells_true": float(manifest["n_cells_true"].mean()),
        "mean_phenotype_counts_true": counts,
    }


def describe_slide(path: str | Path) -> dict[str, Any]:
    """Geometry of a whole-slide image: vendor, microns per pixel, pyramid levels, physical field."""
    from stableseg.pathology.io import describe_slide as _describe

    return _describe(path)


def slide_tiles(
    path: str | Path, out_dir: str | Path, size: int = 256, level: int = 0, limit: int = 32
) -> dict[str, Any]:
    """Stream up to `limit` tissue tiles from a slide into PNGs with geometry sidecars."""
    from stableseg.pathology.io import open_slide
    from stableseg.pathology.tile import save_tile

    out_dir = Path(out_dir)
    written = []
    with open_slide(path) as s:
        for i, tile in enumerate(s.iter_tiles(size=size, level=level, tissue_only=True, limit=limit)):
            written.append(str(save_tile(tile, out_dir / f"tile_{i:04d}.png")))
        info = s.describe()
    return {
        "slide": info,
        "n_tiles": len(written),
        "out_dir": str(out_dir.resolve()),
        "level": level,
        "size": size,
    }
