"""DICOM: the format hospitals actually use, read into the same Volume as everything else.

NIfTI, which the research datasets use, stores a whole 3-D scan in one file
with its geometry in one header. DICOM - the hospital standard - stores one
file PER SLICE, each carrying a large header of tags: patient, scanner,
position in space, pixel size, and hundreds more. A scan is therefore a folder
of files that must be sorted into the right order and stacked, and the
geometry must be reassembled from tags spread across them.

Two libraries divide the work:

- **SimpleITK** reads a whole series: it finds the files that belong together,
  sorts them by position, stacks them, and returns the geometry. It is the
  robust path for reading.
- **pydicom** reads and WRITES individual files tag by tag. It is how the test
  suite builds a small, valid DICOM series from scratch - so hospital-format
  reading is tested without any patient data existing anywhere.

On orientation: DICOM describes space in "LPS" (x toward the patient's Left,
y Posterior, z Superior); NIfTI convention is "RAS" (Right, Anterior,
Superior). The two differ by flipping the first two axes. This module hands
back a `Volume` whose affine is expressed in RAS, so a DICOM-read scan and a
NIfTI-read scan of the same patient land in the same coordinate frame - the
kind of detail that, if ignored, silently mirrors a brain left-to-right.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import SimpleITK as sitk

from stableseg.io import Volume

# LPS -> RAS: negate x and y. A 4x4 so it composes with the affine directly.
_LPS_TO_RAS = np.diag([-1.0, -1.0, 1.0, 1.0])


def read_series(series_dir: str | Path) -> Volume:
    """Read a folder of DICOM slices as one Volume with an RAS affine.

    SimpleITK sorts the slices by their position along the scan axis, checks
    that they form a regular stack, and reports spacing, origin and direction.
    We assemble those into the 4x4 affine every other loader in the project
    uses, so downstream code never knows or cares that this came from DICOM.
    """
    series_dir = Path(series_dir)
    if not series_dir.is_dir():
        raise FileNotFoundError(series_dir)
    reader = sitk.ImageSeriesReader()
    ids = reader.GetGDCMSeriesIDs(str(series_dir))
    if not ids:
        raise ValueError(f"no DICOM series found in {series_dir}")
    if len(ids) > 1:
        raise ValueError(
            f"{len(ids)} DICOM series in {series_dir}; put one series per folder "
            "(this is the usual export layout, and it removes any guessing)"
        )
    files = reader.GetGDCMSeriesFileNames(str(series_dir), ids[0])
    reader.SetFileNames(files)
    img = reader.Execute()

    # SimpleITK arrays come back (z, y, x); the project stores (x, y, z), matching nibabel.
    data = sitk.GetArrayFromImage(img).transpose(2, 1, 0)
    spacing = np.asarray(img.GetSpacing(), dtype=np.float64)  # (x, y, z)
    origin = np.asarray(img.GetOrigin(), dtype=np.float64)
    direction = np.asarray(img.GetDirection(), dtype=np.float64).reshape(3, 3)

    affine_lps = np.eye(4)
    affine_lps[:3, :3] = direction * spacing[None, :]
    affine_lps[:3, 3] = origin
    affine_ras = _LPS_TO_RAS @ affine_lps

    meta: dict[str, Any] = {
        "source": str(series_dir),
        "format": "DICOM",
        "n_slices": len(files),
        "series_uid": ids[0],
    }
    # A few human-meaningful tags, read from the first slice if present.
    first = sitk.ReadImage(files[0])
    for key, name in (
        ("0008|0060", "modality"),
        ("0008|0070", "manufacturer"),
        ("0018|0050", "slice_thickness"),
    ):
        if first.HasMetaDataKey(key):
            meta[name] = first.GetMetaData(key).strip()
    return Volume(data=data, affine=affine_ras, meta=meta)


def write_synthetic_series(
    dest: str | Path,
    data: np.ndarray,
    spacing_mm: tuple[float, float, float] = (1.0, 1.0, 1.0),
    origin_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Path:
    """Write a (x, y, z) array as a valid DICOM series - one file per slice - with no patient in it.

    Exists so the reader above can be tested against a series whose geometry
    is known exactly, using no real data. Every identifying tag is a fixed
    placeholder ("ANONYMOUS", a generated UID), and the modality is set to
    MR. The pixel type is unsigned 16-bit, the common case for MRI exports.

    This is the reader's answer key, the same role the phantoms play for the
    pipeline: a series whose spacing, orientation and origin we chose, so the
    reader can be checked against arithmetic before it meets a hospital
    export.
    """
    import datetime

    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage, generate_uid

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if data.ndim != 3:
        raise ValueError("data must be (x, y, z)")
    if data.dtype != np.uint16:
        lo, hi = float(data.min()), float(data.max())
        scaled = (data - lo) / (hi - lo) if hi > lo else np.zeros_like(data, dtype=np.float32)
        data = (scaled * 4000).astype(np.uint16)

    study_uid, series_uid, frame_uid = generate_uid(), generate_uid(), generate_uid()
    now = datetime.datetime.now(datetime.UTC)
    nx, ny, nz = data.shape
    sx, sy, sz = spacing_mm
    ox, oy, oz = origin_mm

    for k in range(nz):
        meta = FileMetaDataset()
        meta.MediaStorageSOPClassUID = MRImageStorage
        meta.MediaStorageSOPInstanceUID = generate_uid()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        # The transfer syntax in file_meta (explicit VR, little endian) is the
        # single source of truth for encoding; the older is_little_endian /
        # is_implicit_VR attributes are deprecated in pydicom 3 and removed in 4.
        ds = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)

        ds.PatientName, ds.PatientID = "ANONYMOUS", "SYNTHETIC-0000"
        ds.PatientBirthDate, ds.PatientSex = "", ""
        ds.StudyInstanceUID, ds.SeriesInstanceUID = study_uid, series_uid
        ds.FrameOfReferenceUID = frame_uid
        ds.SOPClassUID, ds.SOPInstanceUID = MRImageStorage, meta.MediaStorageSOPInstanceUID
        ds.StudyDate = ds.SeriesDate = now.strftime("%Y%m%d")
        ds.StudyTime = ds.SeriesTime = now.strftime("%H%M%S")
        ds.Modality, ds.Manufacturer = "MR", "StableSeg synthetic"
        ds.SeriesDescription = "synthetic test series - not a patient"
        ds.StudyID, ds.SeriesNumber, ds.InstanceNumber = "1", 1, k + 1

        # Geometry: identity orientation, slices stacked along +z.
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.ImagePositionPatient = [ox, oy, oz + k * sz]
        ds.PixelSpacing = [sy, sx]  # DICOM lists row spacing then column spacing
        ds.SliceThickness = sz
        ds.SpacingBetweenSlices = sz

        # Pixels: a DICOM slice is (rows, columns) = (y, x).
        slice_yx = np.ascontiguousarray(data[:, :, k].T)
        ds.Rows, ds.Columns = slice_yx.shape
        ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, "MONOCHROME2"
        ds.BitsAllocated = ds.BitsStored = 16
        ds.HighBit, ds.PixelRepresentation = 15, 0
        ds.PixelData = slice_yx.tobytes()

        pydicom.dcmwrite(dest / f"slice_{k:04d}.dcm", ds, enforce_file_format=True)
    return dest


def series_to_nifti(series_dir: str | Path, out_path: str | Path) -> Path:
    """Read a DICOM series and write it as one NIfTI file, geometry preserved."""
    from stableseg.io import save_volume

    vol = read_series(series_dir)
    return save_volume(vol, out_path)
