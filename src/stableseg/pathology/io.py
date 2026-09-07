"""Reading and writing pathology images: OME-TIFF, pyramidal TIFF, and whole slides.

Three kinds of file, one rule: the geometry comes out of the file, never out
of a guess.

- **OME-TIFF** carries channel names and physical pixel size INSIDE the file,
  in a small XML block. It is what multiplex immunofluorescence is stored in,
  and it is the right home for any multichannel image.
- **Pyramidal TIFF** stores the same picture at several resolutions so a
  viewer can zoom without loading everything. Its resolution tags give the
  microns per pixel.
- **Whole-slide images** in vendor formats (SVS, NDPI, MRXS ...) are read
  through OpenSlide, which also reads generic pyramidal TIFF - so a slide
  built by this module can be read back by the same code that reads a
  scanner's export, and the reader is tested without downloading one.

OME-TIFF and pyramidal-TIFF writing use `tifffile`, which the core already
carries (scikit-image depends on it), so those work everywhere. Whole-slide
READING needs OpenSlide, which is the optional `[pathology]` extra. Its
import is deferred into the functions so that the core package installs and
runs without it; calling a slide function without the extra produces one
clear message rather than a stack trace from deep inside a library.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from stableseg.pathology.tile import Tile

_EXTRA_HINT = (
    "This needs the optional pathology extra. Install it with:\n"
    "    python -m pip install -r requirements-pathology.lock\n"
    "(see docs/01-setup-<your-os>.md, section 'The pathology extra')."
)


def _need(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise ImportError(f"{module} is not installed. {_EXTRA_HINT}") from exc


# ---------------------------------------------------------------------------
# OME-TIFF: multichannel images with their geometry inside the file
# ---------------------------------------------------------------------------


def write_ome_tiff(tile: Tile, path: str | Path) -> Path:
    """Write a Tile as OME-TIFF with channel names and physical pixel size embedded.

    The data is stored channels-first (C, Y, X), which is the OME convention.
    Compression is lossless (zlib): what is written is what is read back.
    """
    tifffile = _need("tifffile")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cyx = np.ascontiguousarray(np.moveaxis(tile.data, -1, 0))
    metadata = {
        "axes": "CYX",
        "Channel": {"Name": list(tile.channels)},
        "PhysicalSizeX": tile.mpp,
        "PhysicalSizeXUnit": "µm",
        "PhysicalSizeY": tile.mpp,
        "PhysicalSizeYUnit": "µm",
    }
    tifffile.imwrite(
        path,
        cyx,
        ome=True,
        metadata=metadata,
        compression="zlib",
        description=None,
    )
    # Facts OME has no slot for travel in a sidecar, exactly as for PNG tiles.
    import json

    side = {"synthetic": tile.synthetic, "level": tile.level, **tile.meta}
    path.with_suffix(".json").write_text(json.dumps(side, indent=2), encoding="utf-8")
    return path


def read_ome_tiff(path: str | Path) -> Tile:
    """Read an OME-TIFF written by `write_ome_tiff` (or any OME-TIFF with CYX or YXC axes)."""
    tifffile = _need("tifffile")
    import json

    path = Path(path)
    with tifffile.TiffFile(path) as tf:
        if not tf.is_ome:
            raise ValueError(
                f"{path.name} is not an OME-TIFF; use read_tile for PNG or open_slide for pyramids"
            )
        series = tf.series[0]
        arr = series.asarray()
        axes = series.axes  # e.g. "CYX"
        ome = tifffile.xml2dict(tf.ome_metadata)["OME"]
    image = ome["Image"] if not isinstance(ome["Image"], list) else ome["Image"][0]
    pixels = image["Pixels"]
    mpp_x = float(pixels.get("PhysicalSizeX", 0) or 0)
    if mpp_x <= 0:
        raise ValueError(
            f"{path.name} carries no PhysicalSizeX; "
            "a picture without its microns-per-pixel cannot be measured"
        )
    chans = pixels.get("Channel", [])
    if isinstance(chans, dict):
        chans = [chans]
    names = tuple(str(c.get("Name", f"C{i}")) for i, c in enumerate(chans))

    if axes == "CYX":
        data = np.moveaxis(arr, 0, -1)
    elif axes == "YXC":
        data = arr
    elif axes == "YX":
        data = arr[:, :, None]
    else:
        raise ValueError(f"unsupported OME axes {axes!r} in {path.name}")
    if not names or len(names) != data.shape[2]:
        names = tuple(f"C{i}" for i in range(data.shape[2]))

    side_path = path.with_suffix(".json")
    side = json.loads(side_path.read_text(encoding="utf-8")) if side_path.exists() else {}
    known = {"synthetic", "level"}
    return Tile(
        data=np.ascontiguousarray(data),
        mpp=mpp_x,
        channels=names,
        level=int(side.get("level", 0)),
        synthetic=bool(side.get("synthetic", False)),
        meta={k: v for k, v in side.items() if k not in known},
    )


# ---------------------------------------------------------------------------
# Pyramidal TIFF: a slide-shaped file, written so OpenSlide reads it
# ---------------------------------------------------------------------------


def write_pyramidal_tiff(
    rgb: np.ndarray,
    mpp: float,
    path: str | Path,
    tile_size: int = 256,
    n_levels: int = 4,
    compression: str = "zlib",
) -> Path:
    """Write an RGB picture as a tiled, multi-resolution TIFF that OpenSlide opens as a slide.

    Each level halves the previous one. Levels are written as consecutive
    pages with the 'reduced image' flag, which is how OpenSlide's generic
    TIFF reader recognises a pyramid. Resolution tags encode the microns per
    pixel, so `open_slide` recovers the geometry from the file.

    `n_levels` is a maximum: the pyramid stops before a level would be smaller
    than one tile, because such a level is smaller than the unit anything
    reads. A 1024 x 1536 picture with 256-px tiles gets three levels
    (1024, 512, 256), not four.

    Default compression is lossless so tests can compare pixels exactly; real
    scanners use JPEG, and `compression="jpeg"` produces that too.
    """
    tifffile = _need("tifffile")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("write_pyramidal_tiff expects an (H, W, 3) uint8 RGB array")
    with tifffile.TiffWriter(path, bigtiff=rgb.nbytes > 2**31) as tw:
        level = rgb
        for i in range(n_levels):
            mpp_level = mpp * (2**i)
            per_cm = 1e4 / mpp_level  # pixels per centimetre
            tw.write(
                level,
                tile=(tile_size, tile_size),
                photometric="rgb",
                compression=compression,
                subfiletype=0 if i == 0 else 1,
                resolution=(per_cm, per_cm),
                resolutionunit="CENTIMETER",
                metadata=None,
            )
            if min(level.shape[:2]) // 2 < tile_size and i < n_levels - 1:
                break  # stop before a level smaller than one tile
            level = level[::2, ::2]
    return path


# ---------------------------------------------------------------------------
# Whole slides
# ---------------------------------------------------------------------------


@dataclass
class Slide:
    """An open whole-slide image: geometry per level, tiles on demand, never all in memory.

    Everyday version: a satellite map service. The whole map exists, but you
    only ever download the tiles for the part you are looking at, at the zoom
    level you are looking at.
    """

    path: Path
    _os: Any  # the openslide.OpenSlide handle

    # ---- construction -------------------------------------------------------
    @classmethod
    def open(cls, path: str | Path) -> Slide:
        openslide = _need("openslide")
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        return cls(path=path, _os=openslide.OpenSlide(str(path)))

    def close(self) -> None:
        self._os.close()

    def __enter__(self) -> Slide:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---- geometry -----------------------------------------------------------
    @property
    def mpp(self) -> float:
        """Microns per pixel at level 0, read from the file. Refuses to guess."""
        p = self._os.properties
        x, y = p.get("openslide.mpp-x"), p.get("openslide.mpp-y")
        if x is None:
            raise ValueError(
                f"{self.path.name} carries no microns-per-pixel. A slide whose physical size is "
                "unknown cannot be measured; supply mpp explicitly if you know it from elsewhere."
            )
        x, y = float(x), float(y or x)
        if abs(x - y) > 1e-6 * max(x, y):
            raise ValueError(f"non-square pixels ({x} x {y} um); not supported")
        return x

    @property
    def level_count(self) -> int:
        return int(self._os.level_count)

    @property
    def level_dimensions(self) -> tuple[tuple[int, int], ...]:
        """(width, height) per level - note OpenSlide's width-first order."""
        return tuple((int(w), int(h)) for w, h in self._os.level_dimensions)

    @property
    def level_downsamples(self) -> tuple[float, ...]:
        return tuple(float(d) for d in self._os.level_downsamples)

    @property
    def vendor(self) -> str:
        return str(self._os.properties.get("openslide.vendor", "unknown"))

    def mpp_at(self, level: int) -> float:
        return self.mpp * self.level_downsamples[level]

    def describe(self) -> dict[str, Any]:
        w0, h0 = self.level_dimensions[0]
        return {
            "path": str(self.path),
            "vendor": self.vendor,
            "mpp": self.mpp,
            "level_count": self.level_count,
            "level_dimensions": [list(d) for d in self.level_dimensions],
            "level_downsamples": list(self.level_downsamples),
            "field_mm": [w0 * self.mpp / 1000.0, h0 * self.mpp / 1000.0],
        }

    # ---- reading ------------------------------------------------------------
    def read_tile(self, x: int, y: int, size: int, level: int = 0) -> Tile:
        """Read a size x size RGB tile whose top-left is (x, y) in LEVEL-0 pixel coordinates.

        OpenSlide addresses every region by level-0 coordinates regardless of
        the level read - a convention that is convenient once known and a trap
        before. This wrapper keeps that convention and states it.
        """
        region = self._os.read_region((int(x), int(y)), int(level), (int(size), int(size)))
        rgb = np.asarray(region.convert("RGB"))
        return Tile(
            data=rgb,
            mpp=self.mpp_at(level),
            channels=("R", "G", "B"),
            level=level,
            meta={"slide": self.path.name, "x0": int(x), "y0": int(y), "vendor": self.vendor},
        )

    def thumbnail(self, max_px: int = 512) -> np.ndarray:
        """A small RGB overview, for tissue detection and for looking."""
        return np.asarray(self._os.get_thumbnail((max_px, max_px)).convert("RGB"))

    def tissue_mask(self, max_px: int = 512, saturation_threshold: float | None = None) -> np.ndarray:
        """A boolean overview mask of where tissue is, so tiles are not wasted on glass.

        Glass is white (bright, unsaturated); stained tissue has colour. So the
        thumbnail is converted to HSV and thresholded on saturation - Otsu's
        method chooses the threshold from the image itself unless one is given.
        Deliberately simple: it is a tile-selection heuristic, not a
        segmentation, and phase P3 owns the real thing. Consequence worth
        knowing: a uniformly grey picture has no saturation anywhere and is
        therefore "no tissue" - correct for a blank slide, surprising for a
        synthetic one.
        """
        from skimage.color import rgb2hsv
        from skimage.filters import threshold_otsu

        thumb = self.thumbnail(max_px)
        sat = rgb2hsv(thumb)[:, :, 1]
        thr = float(threshold_otsu(sat)) if saturation_threshold is None else saturation_threshold
        return sat > thr

    def iter_tiles(
        self,
        size: int = 256,
        level: int = 0,
        tissue_only: bool = True,
        min_tissue_fraction: float = 0.5,
        limit: int | None = None,
    ) -> Iterator[Tile]:
        """Walk the slide in a grid, yielding tiles one at a time.

        With `tissue_only`, a tile is yielded only if at least
        `min_tissue_fraction` of its footprint on the thumbnail mask is tissue.
        `limit` caps the count, which is what keeps a demonstration on a
        laptop to seconds rather than an afternoon.
        """
        w0, h0 = self.level_dimensions[0]
        ds = self.level_downsamples[level]
        step0 = int(round(size * ds))  # tile footprint in level-0 pixels
        mask = self.tissue_mask() if tissue_only else None
        if mask is not None:
            mh, mw = mask.shape
            sx, sy = mw / w0, mh / h0
        n = 0
        for y0 in range(0, h0 - step0 + 1, step0):
            for x0 in range(0, w0 - step0 + 1, step0):
                if mask is not None:
                    my0, my1 = int(y0 * sy), max(int((y0 + step0) * sy), int(y0 * sy) + 1)
                    mx0, mx1 = int(x0 * sx), max(int((x0 + step0) * sx), int(x0 * sx) + 1)
                    frac = float(mask[my0:my1, mx0:mx1].mean()) if mask[my0:my1, mx0:mx1].size else 0.0
                    if frac < min_tissue_fraction:
                        continue
                yield self.read_tile(x0, y0, size, level)
                n += 1
                if limit is not None and n >= limit:
                    return


def open_slide(path: str | Path) -> Slide:
    return Slide.open(path)


def describe_slide(path: str | Path) -> dict[str, Any]:
    with open_slide(path) as s:
        return s.describe()
