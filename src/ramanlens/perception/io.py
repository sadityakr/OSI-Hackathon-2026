"""Readers that turn Raman data files into Spectrum and AngleSeries objects.

Every later perception step (spike removal, baseline, fitting, polarization analysis) works on these two containers,
so the readers normalize what instruments and datasets disagree on: delimiters, header lines, comment lines and the
direction of the Raman-shift axis.

Input: a path to a text file. Single spectra are two-column csv/txt (Raman shift in cm-1, intensity), with or
without a header, separated by commas, semicolons, tabs or spaces; lines starting with '#' or '%' are comments.
Angle series are long-format csv with columns shift_cm1, intensity, angle_deg, config (config is parallel or crossed).
Process: parse the numeric rows, sort by Raman shift, average duplicate shift values, and for angle series group
the rows by (config, angle) and put every curve on one common shift axis (linear interpolation if the axes differ).
Output: Spectrum(x, y, meta) with x strictly ascending, or AngleSeries(x, spectra, meta) where spectra maps
(config, angle_deg) to an intensity array on the common axis x.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_COMMENT_PREFIXES = ("#", "%", "//")
_SPLIT = re.compile(r"[,;\t ]+")


# @dataclass writes __init__ and __repr__ from the annotated fields, so the container stays a plain record.
@dataclass
class Spectrum:
    """One Raman spectrum: shift x (cm-1, strictly ascending), intensity y, and free-form metadata."""

    x: np.ndarray
    y: np.ndarray
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.x = np.asarray(self.x, dtype=float)
        self.y = np.asarray(self.y, dtype=float)
        if self.x.ndim != 1 or self.x.shape != self.y.shape:
            raise ValueError(f"x and y must be 1D arrays of equal length, got {self.x.shape} and {self.y.shape}")


# @dataclass as above: a record of the shared axis plus one intensity curve per (config, angle).
@dataclass
class AngleSeries:
    """Polarization angle series: common shift axis x and spectra[(config, angle_deg)] -> intensity array."""

    x: np.ndarray
    spectra: dict
    meta: dict = field(default_factory=dict)

    @property
    def angles(self) -> list[float]:
        """Sorted distinct polarization angles in degrees."""
        return sorted({a for _, a in self.spectra})

    @property
    def configs(self) -> list[str]:
        """Sorted distinct configurations, for example ['crossed', 'parallel']."""
        return sorted({c for c, _ in self.spectra})


def _sorted_unique(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sort by x and average y over repeated x values, so x is strictly ascending."""
    order = np.argsort(x, kind="stable")
    x, y = x[order], y[order]
    ux, inv = np.unique(x, return_inverse=True)
    if ux.size == x.size:
        return x, y
    uy = np.bincount(inv, weights=y) / np.bincount(inv)
    return ux, uy


def _numeric_rows(path: Path) -> tuple[list[list[float]], list[str] | None]:
    """Parse a delimited text file into numeric rows; return (rows, header) where header may be None."""
    rows, header = [], None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(_COMMENT_PREFIXES):
            continue
        parts = [p for p in _SPLIT.split(s) if p]
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            if not rows and header is None:
                header = parts  # first non-numeric line before any data is the header
            # any other non-numeric line (footer, instrument text) is skipped
    return rows, header


def read_spectrum(path) -> Spectrum:
    """Read a two-column (shift, intensity) text or csv file into a Spectrum with ascending shift axis.

    Files with more than two numeric columns use the first two. A header line, if present, is kept in meta.
    """
    path = Path(path)
    rows, header = _numeric_rows(path)
    rows = [r for r in rows if len(r) >= 2]
    if len(rows) < 2:
        raise ValueError(f"{path}: fewer than two numeric rows with at least two columns")
    arr = np.array([r[:2] for r in rows], dtype=float)
    ok = np.all(np.isfinite(arr), axis=1)
    x, y = _sorted_unique(arr[ok, 0], arr[ok, 1])
    meta = {"source_path": str(path), "header": header, "n_points": int(x.size),
            "x_range_cm1": [float(x[0]), float(x[-1])]}
    return Spectrum(x, y, meta)


def read_series(path) -> AngleSeries:
    """Read a long-format angle-series csv (shift_cm1, intensity, angle_deg, config) into an AngleSeries.

    Each (config, angle) curve is sorted; if the curves do not share one shift axis, they are interpolated onto the
    axis of the first curve, restricted to the shift range covered by every curve.
    """
    path = Path(path)
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"shift_cm1", "intensity", "angle_deg", "config"}
    if not need <= set(df.columns):
        raise ValueError(f"{path}: angle series needs columns {sorted(need)}, found {list(df.columns)}")
    df["config"] = df["config"].astype(str).str.strip().str.lower()
    df = df.dropna(subset=["shift_cm1", "intensity", "angle_deg"])

    curves = {}
    for (cfg, ang), g in df.groupby(["config", "angle_deg"], sort=True):
        curves[(cfg, float(ang))] = _sorted_unique(g["shift_cm1"].to_numpy(float), g["intensity"].to_numpy(float))
    if not curves:
        raise ValueError(f"{path}: no data rows")

    axes = [cx for cx, _ in curves.values()]
    x = axes[0]
    same_axis = all(a.shape == x.shape and np.allclose(a, x) for a in axes)
    if not same_axis:
        lo, hi = max(a[0] for a in axes), min(a[-1] for a in axes)
        x = x[(x >= lo) & (x <= hi)]
    spectra = {k: (cy if same_axis else np.interp(x, cx, cy)) for k, (cx, cy) in curves.items()}

    meta = {"source_path": str(path), "n_points": int(x.size), "x_range_cm1": [float(x[0]), float(x[-1])],
            "interpolated": not same_axis}
    return AngleSeries(x, spectra, meta)
