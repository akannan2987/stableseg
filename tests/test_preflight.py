"""The safety check must catch real problems and ignore look-alikes.

A scanner that never fires is worse than no scanner, because it creates
confidence without evidence. These tests fire it on purpose.

This file deliberately contains fake credentials and fake home paths as test
inputs, so it carries the `preflight: allow-file` marker below and the scanner
skips it. That marker is the escape hatch, used here for the one honest reason
it exists.

    preflight: allow-file

The two functions tested here are pure: they take a string or a path and
return findings, with no git and no filesystem involved. That is deliberate,
so the checks can be verified in milliseconds on every machine.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from preflight import (  # noqa: E402
    is_forbidden_path,
    scan_text_for_private_paths,
    scan_text_for_secrets,
)

# --------------------------------------------------------------------------
# Credential scanning
# --------------------------------------------------------------------------


def test_catches_private_key_block():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEow...\n"
    findings = scan_text_for_secrets(text)
    assert findings and findings[0][1] == "private key block"


def test_catches_assigned_secret():
    text = 'api_key = "sk-9f3a2b7c1d4e5f6a7b8c"\n'
    assert scan_text_for_secrets(text)


def test_catches_aws_key_id():
    assert scan_text_for_secrets("AKIA2QWERTYUIOPASDFG\n")


def test_issuer_format_is_reported_even_when_labelled_an_example():
    """The word 'example' must not be a way to smuggle a real key past the check."""
    assert scan_text_for_secrets("# example only\nAKIA2QWERTYUIOPASDFG\n")


def test_ignores_ordinary_prose():
    text = "This project stores no secrets. The password field stays empty.\n"
    assert scan_text_for_secrets(text) == []


def test_ignores_obvious_placeholders():
    """Shape-based guesses defer to an obviously fake value."""
    assert scan_text_for_secrets('api_key = "your_key_here_replace_me"\n') == []
    assert scan_text_for_secrets('password = "changeme_placeholder"\n') == []


def test_allow_marker_exempts_a_single_line():
    text = 'api_key = "sk-9f3a2b7c1d4e5f6a7b8c"  # preflight: allow (test fixture)\n'
    assert scan_text_for_secrets(text) == []


def test_reports_the_line_number():
    text = "clean line\nanother clean line\ntoken = 'abcdefghijklmnopqrstuvwx'\n"
    findings = scan_text_for_secrets(text)
    assert findings[0][0] == 3


# --------------------------------------------------------------------------
# Private path scanning
# --------------------------------------------------------------------------


def test_catches_real_home_path():
    assert scan_text_for_private_paths("path = '/Users/asmith/projects/x'\n")


def test_allows_documentation_placeholder_home_path():
    assert scan_text_for_private_paths("cd /Users/yourname/projects/stableseg\n") == []


def test_allows_ci_runner_path():
    assert scan_text_for_private_paths("/home/runner/work/stableseg\n") == []


# --------------------------------------------------------------------------
# Path exclusion: the near-misses are the point
# --------------------------------------------------------------------------


def test_blocks_generated_data_and_outputs():
    assert is_forbidden_path("data/phantom/images/phantom_000.nii.gz")
    assert is_forbidden_path("runs/phantom-smoke/run.json")
    assert is_forbidden_path(".venv/lib/python3.13/site-packages/x.py")
    assert is_forbidden_path("src/stableseg/__pycache__/io.cpython-313.pyc")


def test_blocks_real_env_file_but_allows_the_template():
    assert is_forbidden_path(".env")
    assert not is_forbidden_path(".env.example")


def test_allows_directory_placeholders():
    assert not is_forbidden_path("data/.gitkeep")
    assert not is_forbidden_path("runs/.gitkeep")


def test_does_not_confuse_similar_names():
    # 'metadata/' is not 'data/', and a file merely named like a folder is fine.
    assert not is_forbidden_path("metadata/schema.json")
    assert not is_forbidden_path("docs/data-sources.md")
    assert not is_forbidden_path("src/stableseg/io.py")
