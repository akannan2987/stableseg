"""Fetching real datasets: download, verify, unpack, catalogue - with no trust.

Why a dataset needs a registry entry rather than a URL in a script
------------------------------------------------------------------
A URL alone tells you where a file was. It does not tell you whether the file
you got is the file the authors published, or whether it is still the same
file next year. So every dataset this project uses is described once, here,
with four things: where it is, what its bytes must hash to, how it is
licensed, and what its data card says. The download refuses to keep anything
whose hash does not match - a corrupted or tampered archive is deleted, not
used.

The everyday version: a parcel has a tracking number (the URL) and a seal (the
checksum). You do not open a parcel whose seal is broken; you send it back.

What a checksum is
------------------
A checksum - here MD5 - is a fixed-length fingerprint computed from every byte
of a file. Change one byte and the fingerprint changes completely. It is not a
security guarantee against a determined attacker, but it is a reliable
guarantee against the failures that actually happen: a truncated download, a
flipped bit, a silently updated file on the server.

The AppleDouble quirk
---------------------
Archives created on a Mac often carry hidden `._name` companion files
(resource forks) beside every real file. The Medical Segmentation Decathlon
archives do. They look like NIfTI files by name and are not; a loader that
picks them up crashes or, worse, counts them. `extract_archive` drops them.
"""

from __future__ import annotations

import hashlib
import shutil
import tarfile
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DatasetInfo:
    """Everything needed to fetch one dataset and say honestly what it is."""

    key: str
    title: str
    url: str
    md5: str
    archive_name: str
    unpacked_dir: str  # folder name the archive creates
    license: str
    data_card: str  # path in the repository
    approx_mb: int
    track: str  # "V" or "P"


DATASETS: dict[str, DatasetInfo] = {
    "msd_task04_hippocampus": DatasetInfo(
        key="msd_task04_hippocampus",
        title="Medical Segmentation Decathlon - Task04 Hippocampus",
        # The public mirror maintained for the MONAI project. The MD5 is the
        # one MONAI's DecathlonDataset verifies against; a mismatch here means
        # the file changed and the data card must be revisited, not the check.
        url="https://msd-for-monai.s3-us-west-2.amazonaws.com/Task04_Hippocampus.tar",
        md5="9d24dba78a72977dbd1d2e110310f31b",
        archive_name="Task04_Hippocampus.tar",
        unpacked_dir="Task04_Hippocampus",
        license="CC BY-SA 4.0",
        data_card="docs/data-cards/msd-hippocampus.md",
        approx_mb=27,
        track="V",
    ),
}


# --------------------------------------------------------------------------
# Verify
# --------------------------------------------------------------------------


def md5_of(path: str | Path, chunk_bytes: int = 1 << 20) -> str:
    """MD5 fingerprint of a file, read in 1 MB chunks so large files never fill memory."""
    h = hashlib.md5()  # noqa: S324 - integrity check, not security
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_bytes), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_md5(path: str | Path, expected: str) -> bool:
    """True if the file's fingerprint matches; comparison is case-insensitive."""
    return md5_of(path).lower() == expected.lower()


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------


def download(
    url: str,
    dest: str | Path,
    progress: Callable[[int, int], None] | None = None,
    chunk_bytes: int = 1 << 20,
) -> Path:
    """Stream a URL to disk in chunks, writing to a temporary name until complete.

    Writing to `dest.part` and renaming at the end means a half-finished
    download can never be mistaken for a finished one - a crash mid-way leaves
    a `.part` file, not a plausible-looking archive.

    `urllib` is used rather than a third-party downloader because it is in the
    standard library, so the fetch path has no dependency that could differ
    between machines. It also understands `file://` URLs, which is how the
    tests exercise this function without a network.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "stableseg"})
    with urllib.request.urlopen(req) as resp, part.open("wb") as out:  # noqa: S310 - URL comes from the registry
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        for chunk in iter(lambda: resp.read(chunk_bytes), b""):
            out.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total)
    part.replace(dest)
    return dest


# --------------------------------------------------------------------------
# Extract
# --------------------------------------------------------------------------


def _is_apple_double(name: str) -> bool:
    return Path(name).name.startswith("._") or "/__MACOSX/" in f"/{name}"


def _is_safe_member(member: tarfile.TarInfo, dest: Path) -> bool:
    """Refuse archive entries that would write outside `dest` (a classic tar attack)."""
    target = (dest / member.name).resolve()
    return str(target).startswith(str(dest.resolve()))


def extract_archive(archive: str | Path, dest: str | Path) -> Path:
    """Unpack a .tar (or .tar.gz) into dest, dropping AppleDouble companions and unsafe paths."""
    archive, dest = Path(archive), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tf:
        members = [m for m in tf.getmembers() if not _is_apple_double(m.name) and _is_safe_member(m, dest)]
        tf.extractall(dest, members=members, filter="data")
    return dest


# --------------------------------------------------------------------------
# Fetch = download + verify + extract, idempotent
# --------------------------------------------------------------------------


def fetch(
    key: str,
    dest_root: str | Path = "data",
    force: bool = False,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, object]:
    """Get a registered dataset onto disk, verified, unpacked, ready to catalogue.

    Idempotent: running it twice downloads nothing the second time. Pass
    `force=True` to re-download regardless.

    Returns a small dictionary saying what happened - because a fetch that
    silently did nothing is as confusing as one that silently failed.
    """
    if key not in DATASETS:
        raise KeyError(f"unknown dataset {key!r}; known: {sorted(DATASETS)}")
    info = DATASETS[key]
    dest_root = Path(dest_root)
    archive = dest_root / info.archive_name
    unpacked = dest_root / info.unpacked_dir

    steps: list[str] = []
    if archive.exists() and not force and verify_md5(archive, info.md5):
        steps.append("archive already present and verified")
    else:
        if archive.exists():
            archive.unlink()
        download(info.url, archive, progress=progress)
        steps.append(f"downloaded {archive.name}")
        if not verify_md5(archive, info.md5):
            archive.unlink()  # never keep a file whose seal is broken
            raise RuntimeError(
                f"{archive.name}: MD5 does not match the registry value {info.md5}. "
                "The download is corrupt or the published file changed. Deleted. "
                f"See {info.data_card} before changing the expected value."
            )
        steps.append("MD5 verified")

    if unpacked.exists() and any(unpacked.iterdir()) and not force:
        steps.append("already unpacked")
    else:
        if unpacked.exists():
            shutil.rmtree(unpacked)
        extract_archive(archive, dest_root)
        steps.append(f"unpacked to {unpacked.name}")

    return {
        "dataset": key,
        "title": info.title,
        "license": info.license,
        "data_card": info.data_card,
        "archive": str(archive),
        "root": str(unpacked),
        "steps": steps,
    }
