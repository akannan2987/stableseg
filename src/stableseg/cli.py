"""Command-line front door. Every command is one line of argument handling plus one API call.

Try `stableseg --help` after installing.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from stableseg import api
from stableseg import datasets as _datasets
from stableseg.config import AuditConfig

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="StableSeg: audit how much an imaging biomarker moves when the patient has not changed.",
)


def _emit(payload: dict) -> None:
    """Print any API result as indented JSON, so output is readable by people and by programs."""
    typer.echo(json.dumps(payload, indent=2, default=str))


@app.command()
def version() -> None:
    """Show the installed version."""
    _emit(api.version())


@app.command()
def describe(path: Path = typer.Argument(..., exists=True, readable=True, help="A NIfTI file.")) -> None:
    """Summarise a NIfTI volume: shape, voxel size, intensity range."""
    _emit(api.describe_volume(path))


@app.command()
def phantom(
    config: Path | None = typer.Option(
        None, "--config", "-c", exists=True, help="Run config (YAML). Defaults are used if omitted."
    ),
) -> None:
    """Generate the synthetic phantom dataset (from a config file, or from defaults).

    Config resolution, in order:

    1. ``--config PATH`` was given: use that file.
    2. No option, but ``configs/phantom.yaml`` exists in the current folder:
       use it. This is the developer case - someone standing in the project
       checkout - and it keeps every documented command and its printed output
       exactly as the tutorials show them.
    3. Neither: fall back to the built-in defaults, which are byte-identical
       to what ``configs/phantom.yaml`` describes. This is the installed case:
       ``pip install`` puts the package on a machine, but a package carries
       code, not the repository's ``configs/`` folder, so a relative path to
       it cannot be the required default. Version 0.1.0 shipped exactly that
       mistake, and ``stableseg phantom`` failed on any machine that was not
       a project checkout. The v0.1.1 fix is this fallback chain, plus a test
       that runs the command from an empty folder the way an installed user
       would.
    """
    if config is not None:
        cfg = AuditConfig.from_yaml(config)
    elif Path("configs/phantom.yaml").exists():
        cfg = AuditConfig.from_yaml(Path("configs/phantom.yaml"))
    else:
        cfg = AuditConfig(name="phantom-smoke")
    _emit(api.generate_phantoms(cfg))


@app.command("validate-config")
def validate_config(config: Path = typer.Argument(..., exists=True, help="Run config (YAML).")) -> None:
    """Check that a config file is valid without running anything."""
    cfg = AuditConfig.from_yaml(config)
    _emit({"valid": True, "name": cfg.name, "config": cfg.model_dump(mode="json")})


if __name__ == "__main__":  # allows `python -m stableseg.cli`
    app()


@app.command("he-phantom")
def he_phantom(
    config: Path | None = typer.Option(
        None, "--config", "-c", exists=True, help="Run config (YAML). Defaults are used if omitted."
    ),
) -> None:
    """Generate the synthetic H&E phantom tiles (Track P), from a config file or from defaults.

    Same three-step config resolution as `phantom`: an explicit --config path;
    else configs/he_phantom.yaml if present in the current folder; else the
    built-in defaults, which are identical to that file.
    """
    if config is not None:
        cfg = AuditConfig.from_yaml(config)
    elif Path("configs/he_phantom.yaml").exists():
        cfg = AuditConfig.from_yaml(Path("configs/he_phantom.yaml"))
    else:
        cfg = AuditConfig(
            name="he-phantom-smoke",
            data={"source": "he_phantom", "root": "data/he_phantom"},
            output={"run_name": "he-phantom-smoke"},
        )
    _emit(api.generate_he_phantoms(cfg))


@app.command("describe-tile")
def describe_tile(
    path: Path = typer.Argument(..., exists=True, help="A PNG tile written by this tool."),
) -> None:
    """Summarise a 2-D tile: shape, microns per pixel, channels, intensity range."""
    _emit(api.describe_tile(path))


@app.command("datasets")
def datasets_cmd() -> None:
    """List the datasets this tool can fetch, with licence and data card."""
    _emit(api.list_datasets())


@app.command("fetch")
def fetch(
    key: str = typer.Argument(
        ..., help="Dataset key, e.g. msd_task04_hippocampus (see `stableseg datasets`)."
    ),
    dest: Path = typer.Option(Path("data"), "--dest", "-d", help="Folder to download and unpack into."),
    force: bool = typer.Option(False, "--force", help="Re-download even if a verified copy exists."),
) -> None:
    """Download a registered dataset, verify its checksum, and unpack it. Idempotent."""

    def bar(done: int, total: int) -> None:
        if total:
            pct = 100 * done / total
            typer.echo(f"\r  {done / 1e6:6.1f} / {total / 1e6:.1f} MB  {pct:5.1f}%", nl=False, err=True)

    result = _datasets.fetch(key, dest_root=dest, force=force, progress=bar)
    typer.echo("", err=True)
    _emit(result)


@app.command("dataset-summary")
def dataset_summary(
    root: Path = typer.Argument(..., exists=True, help="Dataset root (has images/ or imagesTr/)."),
    manifest: Path | None = typer.Option(
        None, "--manifest", "-m", help="Also write the catalogue as CSV here."
    ),
) -> None:
    """Catalogue a folder of scans: counts, label coverage, and the range of voxel spacings."""
    _emit(api.dataset_summary(root, manifest_out=manifest))


@app.command("dicom-to-nifti")
def dicom_to_nifti(
    series_dir: Path = typer.Argument(..., exists=True, help="Folder holding one DICOM series."),
    out: Path = typer.Argument(..., help="Output .nii.gz path."),
) -> None:
    """Read a folder of DICOM slices and write one NIfTI volume, geometry preserved."""
    _emit(api.dicom_to_nifti(series_dir, out))
