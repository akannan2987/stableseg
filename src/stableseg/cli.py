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
