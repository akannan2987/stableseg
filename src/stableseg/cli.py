"""Command-line front door. Every command is one line of argument handling plus one API call.

Try `stableseg --help` after installing.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from stableseg import api
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
    config: Path = typer.Option(
        Path("configs/phantom.yaml"), "--config", "-c", exists=True, help="Run config (YAML)."
    ),
) -> None:
    """Generate the synthetic phantom dataset described in a config file."""
    cfg = AuditConfig.from_yaml(config)
    _emit(api.generate_phantoms(cfg))


@app.command("validate-config")
def validate_config(config: Path = typer.Argument(..., exists=True, help="Run config (YAML).")) -> None:
    """Check that a config file is valid without running anything."""
    cfg = AuditConfig.from_yaml(config)
    _emit({"valid": True, "name": cfg.name, "config": cfg.model_dump(mode="json")})


if __name__ == "__main__":  # allows `python -m stableseg.cli`
    app()
