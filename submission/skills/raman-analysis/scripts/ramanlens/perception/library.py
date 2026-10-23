"""Reference library of Raman modes and a matcher that ranks candidate materials for a measured peak list.

Identification is the first question the agent asks of an unknown spectrum. The general-purpose reference is the
Computational Raman Database (CRD; Bagheri and Komsa 2023, Sci. Data 10, 80, CC BY 4.0): DFT frequencies, irreps
and Raman tensors for 5,099 bulk crystals, of which the 385 layered ("2D") ones are loaded here. Curated literature
mode tables (ramanlens.literature.reference_tables) are scored alongside the CRD and win ties for any material they
cover, because measured positions beat DFT ones and some key materials (graphene, 2H-MoS2, CrSBr) are absent from
the CRD.

Input: the precomputed observable-mode library `resources/crd_layered_modes.json` shipped with the skill (built
by scripts/build_crd_resource.py with exactly the processing below). Without it, the raw CRD as `crd_2d.pkl`
(pickle of the layered rows) or `crd.json` (full ASE JSON dump) in the directory named by the environment
variable RAMANLENS_CRD_DIR. For `match`, measured peak positions in cm-1 and optionally their heights.
Process: per CRD entry, every Raman-active mode gets its irrep (CRD labels are per band, mapped to modes through
IRbands) and its tensor rotated into the layer frame (z = layer normal, found as the lattice-plane family with the
widest empty gap, the van der Waals gap). In backscattering along the layer normal both polarizations lie in
the plane, so a mode's visible intensity is the in-plane block of its tensor; modes below 2 % of the strongest
are treated as invisible (E1g in 2H-TMDs, for example). `match` fits one global frequency scale per candidate
(DFT runs 0 to 3 % low), scores the fraction of measured intensity it explains, subtracts a penalty for strong
predicted modes that are missing from the measurement, and ranks.
Output: a list of Candidate records (material, score, matched peaks with labels, unmatched and missing modes, the
fitted scale and the source of the reference).
"""

from __future__ import annotations

import ast
import json
import os
import pickle
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

from ramanlens import RESOURCES

CRD_RESOURCE = RESOURCES / "crd_layered_modes.json"
CRD_CITATION = "Bagheri and Komsa 2023, Sci. Data 10, 80 (Computational Raman Database, CC BY 4.0)"

# Modes weaker than this fraction of the strongest visible mode are treated as not observable. Same 2 % threshold
# as the "silent" class of the test-set conventions.
MIN_RELATIVE_INTENSITY = 0.02
# Range of the global frequency scale fitted per CRD candidate. The CRD's PBE-type frequencies run 0 to 3 % below
# experiment for layered sulfides and selenides (2H-WS2: E2g 353.9 vs 356, A1g 415.7 vs 420 cm-1; CRD v1.0.1
# row 90 against Berkdemir et al. 2013, Sci. Rep. 3, 1755); the range leaves margin on both sides.
CRD_SCALE_RANGE = (0.98, 1.05)
# Literature tables hold measured positions, so only a small calibration offset is allowed.
LIT_SCALE_RANGE = (0.995, 1.005)
SCALE_STEP = 0.001
# Matching width after scaling: a fixed part for peak-position and calibration errors plus a relative part for
# the mode-to-mode scatter of DFT errors. Design choice, tuned on synthetic data, not a literature value.
MATCH_SIGMA_FIXED_CM1 = 3.0
MATCH_SIGMA_REL = 0.01
# When the measurement window is not given (x_range), predicted modes are fully expected within this margin around
# the measured peaks; strong modes farther out count with OUTSIDE_WEIGHT, a prior that a spectrum usually covers
# the main fingerprint region. This also breaks ties between materials that explain a single peak equally well,
# in favour of the one that predicts nothing else (Occam). Modes below 50 cm-1 are never expected, because edge
# filters usually block them. Design choices, not literature values.
WINDOW_MARGIN_CM1 = 50.0
OUTSIDE_WEIGHT = 0.25
LOW_CUTOFF_CM1 = 50.0
# Only predicted modes at least this strong (relative to the strongest) are penalized when absent: weaker ones can
# sit below the noise of a real measurement.
MISSING_MIN_RELATIVE = 0.1
# Weight of the missing-mode penalty against the explained-intensity term.
MISSING_PENALTY = 0.6


# @dataclass generates the constructor and repr: these are plain records that the agent tools serialize to JSON.
@dataclass
class RefMode:
    """One observable reference mode: position (cm-1), relative intensity (0 to 1), irrep and label."""

    position_cm1: float
    rel_intensity: float
    irrep: str
    label: str


@dataclass
class RefEntry:
    """One reference material: formula, its observable modes, and where the numbers come from."""

    material: str
    modes: list[RefMode]
    source: str
    kind: str  # "crd" or "literature"
    spacegroup: str | None = None
    entry_id: str | None = None


@dataclass
class Candidate:
    """A ranked identification candidate.

    matched: (measured cm-1, reference cm-1 after scaling, label) for every measured peak assigned to a mode.
    unmatched: measured positions no reference mode explains. missing: (reference cm-1, label, rel. intensity) of
    strong predicted modes inside the window that were not found.
    """

    material: str
    score: float
    matched: list[tuple[float, float, str]]
    source: str
    scale: float = 1.0
    unmatched: list[float] = field(default_factory=list)
    missing: list[tuple[float, str, float]] = field(default_factory=list)
    spacegroup: str | None = None
    kind: str = "crd"
    entry_id: str | None = None


# --------------------------------------------------------------------------------------------- CRD loading


def crd_dir() -> Path:
    """Directory of the raw CRD files, needed only to rebuild the precomputed library."""
    d = os.environ.get("RAMANLENS_CRD_DIR")
    if not d:
        raise FileNotFoundError("Raw CRD not configured: set RAMANLENS_CRD_DIR to the folder with crd.json")
    return Path(d)


def _decode(x):
    """Decode ASE's {"__ndarray__": [shape, dtype, flat_data]} array encoding."""
    if isinstance(x, dict) and "__ndarray__" in x:
        shape, dtype, data = x["__ndarray__"]
        return np.array(data, dtype=dtype).reshape(shape)
    if isinstance(x, dict) and "array" in x:  # the cell is wrapped once more as an ASE Cell object
        return _decode(x["array"])
    return np.asarray(x)


def load_crd_rows(directory: Path | None = None) -> dict:
    """Layered ("2D") CRD rows keyed by row id. Writes crd_2d.pkl next to crd.json on first use (parse takes ~30 s)."""
    d = Path(directory) if directory else crd_dir()
    pkl = d / "crd_2d.pkl"
    if pkl.exists():
        with open(pkl, "rb") as f:
            return pickle.load(f)
    js = d / "crd.json"
    if not js.exists():
        raise FileNotFoundError(f"No CRD found in {d}: need crd_2d.pkl or crd.json (see data/README.md)")
    with open(js) as f:
        raw = json.load(f)
    rows = {k: v for k, v in raw.items()
            if isinstance(v, dict) and v["key_value_pairs"].get("dimensionality") == "2D"}
    with open(pkl, "wb") as f:
        pickle.dump(rows, f)
    return rows


def _tensor(tensors, i):
    """Raman tensor of mode i; the CRD stores them as a list by mode or as a dict keyed by the mode index string."""
    t = tensors.get(str(i)) if isinstance(tensors, dict) else (tensors[i] if i < len(tensors) else None)
    return None if t is None else np.array(t, dtype=float)


def layer_normal_frame(cell: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Rotation matrix whose rows are the layer-frame axes (x, y in plane, z along the layer normal).

    The normal is the reciprocal vector of the lattice-plane family (h k l), |h|,|k|,|l| <= 2, whose atoms leave
    the widest empty slab between planes, i.e. the van der Waals gap of the layered crystal.
    """
    frac = np.linalg.solve(cell.T, positions.T).T
    recip = np.linalg.inv(cell).T  # rows b_i with a_i . b_j = delta_ij
    best, best_gap = np.array([0.0, 0.0, 1.0]), -1.0
    for h in range(-2, 3):
        for k in range(-2, 3):
            for l in range(0, 3):
                hkl = np.array([h, k, l])
                if not hkl.any() or np.gcd.reduce(np.abs(hkl)) != 1:
                    continue
                g = hkl @ recip
                s = np.sort((frac @ hkl) % 1.0)
                gap = np.max(np.diff(np.append(s, s[0] + 1.0))) / np.linalg.norm(g)  # in Angstrom
                if gap > best_gap + 1e-6:
                    best, best_gap = g, gap
    z = best / np.linalg.norm(best)
    # x along the in-plane projection of the lattice vector closest to the plane, y completes a right-handed frame
    a = cell[int(np.argmin([abs(v @ z) / np.linalg.norm(v) for v in cell]))]
    x = a - (a @ z) * z
    x /= np.linalg.norm(x)
    return np.vstack([x, np.cross(z, x), z])


def crd_entry(row_id: str, row: dict) -> RefEntry | None:
    """Observable modes of one CRD row in backscattering along the layer normal; None if the row is unusable."""
    kv, dt = row["key_value_pairs"], row["data"]
    try:
        labels = ast.literal_eval(kv["IRlabels"])
        bands = ast.literal_eval(kv["IRbands"])
    except (KeyError, ValueError, SyntaxError):
        return None
    if not labels or not bands:  # a few rows have no symmetry analysis
        return None
    freqs = np.array(re.findall(r"[-+]?\d+\.\d+(?:e[-+]?\d+)?", kv["frequencies_cm"]), dtype=float)
    active = _decode(dt["Ramanactive"])
    Q = layer_normal_frame(_decode(row["cell"]), _decode(row["positions"]))
    modes = []
    for lab, idxs in zip(labels, bands):
        # A degenerate band (E modes) is observed as one line: sum the in-plane intensity of its partners.
        inten, fs = 0.0, []
        for i in idxs:
            T = _tensor(dt["raman_tensors"], i)
            if i >= len(active) or active[i] != 1 or T is None:
                continue
            R = Q @ T @ Q.T
            # Average over in-plane incident polarizations, summed over both analyser directions: 1/2 sum R_ij^2.
            inten += 0.5 * float(np.sum(R[:2, :2] ** 2))
            fs.append(freqs[i])
        if fs:
            modes.append(RefMode(float(np.mean(fs)), inten, str(lab), str(lab)))
    if not modes:
        return None
    top = max(m.rel_intensity for m in modes)
    if top <= 0:
        return None
    for m in modes:
        m.rel_intensity /= top
    modes = [m for m in modes if m.rel_intensity >= MIN_RELATIVE_INTENSITY and m.position_cm1 > 0]
    src = f"{CRD_CITATION}, row {row_id}, {kv.get('mpid', '')}, {kv.get('spacegroup', '')}".rstrip(", ")
    return RefEntry(material=dt["chemical_formula"], modes=modes, source=src, kind="crd",
                    spacegroup=kv.get("spacegroup"), entry_id=f"crd:{row_id}")


def crd_entries_from_rows(rows: dict) -> list[RefEntry]:
    """Observable-mode entries of every usable CRD row, in row order."""
    out = []
    for rid, row in rows.items():
        e = crd_entry(rid, row)
        if e is not None:
            out.append(e)
    return out


def entry_to_dict(e: RefEntry) -> dict:
    return {"material": e.material, "source": e.source, "kind": e.kind, "spacegroup": e.spacegroup,
            "entry_id": e.entry_id,
            "modes": [[m.position_cm1, m.rel_intensity, m.irrep, m.label] for m in e.modes]}


def entry_from_dict(d: dict) -> RefEntry:
    return RefEntry(material=d["material"], modes=[RefMode(*m) for m in d["modes"]], source=d["source"],
                    kind=d["kind"], spacegroup=d["spacegroup"], entry_id=d["entry_id"])


# lru_cache keeps the parsed library in memory, so only the first match() call pays the loading cost.
@lru_cache(maxsize=1)
def crd_library() -> tuple[RefEntry, ...]:
    """The CRD reference entries: from the shipped resource file, else computed from the raw CRD."""
    if CRD_RESOURCE.exists():
        with open(CRD_RESOURCE, encoding="utf-8") as f:
            return tuple(entry_from_dict(d) for d in json.load(f)["entries"])
    return tuple(crd_entries_from_rows(load_crd_rows()))


def literature_library() -> list[RefEntry]:
    """Curated literature tables as reference entries; empty until ramanlens.literature.reference_tables exists.

    Expects `all_tables()` returning tables with `.formula` (or `.name`) and `.modes`, each mode with
    position_cm1, label, irrep and an optional relative intensity; every mode is weighted equally otherwise.
    """
    try:
        from ramanlens.literature.reference_tables import all_tables
    except ImportError:
        return []
    out = []
    for t in all_tables():
        modes = [RefMode(float(m.position_cm1), float(getattr(m, "rel_intensity", None) or 1.0),
                         str(getattr(m, "irrep", "") or ""), str(m.label)) for m in t.modes]
        if modes:
            src = "; ".join(sorted({str(m.source.doi or m.source.arxiv) for m in t.modes}))
            name = getattr(t, "formula", None) or t.name
            out.append(RefEntry(material=name, modes=modes, source=f"literature table: {src}", kind="literature",
                                entry_id=f"lit:{t.name}"))
    return out


# --------------------------------------------------------------------------------------------- matching


def _formula_key(name: str) -> tuple:
    """Reduced element counts as a hashable key, so 'W2S4', 'WS2' and '2H-WS2' collapse to one material."""
    s = re.sub(r"^\d[HRT]\d?[-_ ]", "", str(name).strip())
    aliases = {"graphene": "C", "graphite": "C", "hbn": "BN", "h-bn": "BN"}
    s = aliases.get(s.lower(), s)
    parts = re.findall(r"([A-Z][a-z]?)(\d*)", s)
    if not parts or "".join(e + n for e, n in parts) != s:
        return (s.lower(),)
    counts: dict[str, int] = {}
    for el, n in parts:
        counts[el] = counts.get(el, 0) + (int(n) if n else 1)
    g = np.gcd.reduce(list(counts.values()))
    return tuple(sorted((el, c // g) for el, c in counts.items()))


def _reduced_formula(name: str) -> str:
    key = _formula_key(name)
    if len(key) == 1 and isinstance(key[0], str):
        return name
    return "".join(f"{el}{c if c > 1 else ''}" for el, c in key)


def score_entry(entry: RefEntry, pos: np.ndarray, w: np.ndarray, window: tuple[float, float],
                outside_weight: float = OUTSIDE_WEIGHT) -> Candidate | None:
    """Best-scale score of one reference entry against measured positions pos with normalized weights w.

    score = (weighted fraction of measured intensity explained) - MISSING_PENALTY * (weighted fraction of strong
    predicted modes not found); modes inside `window` carry their relative intensity as weight, modes outside
    it (above LOW_CUTOFF_CM1) that times outside_weight.
    """
    lo_s, hi_s = LIT_SCALE_RANGE if entry.kind == "literature" else CRD_SCALE_RANGE
    ref = np.array([m.position_cm1 for m in entry.modes])
    rel = np.array([m.rel_intensity for m in entry.modes])
    best = None
    for s in np.arange(lo_s, hi_s + SCALE_STEP / 2, SCALE_STEP):
        r = ref * s
        inwin = (r >= window[0]) & (r <= window[1])
        if not inwin.any():
            continue
        sigma = MATCH_SIGMA_FIXED_CM1 + MATCH_SIGMA_REL * r
        # similarity of every measured peak (rows) to every reference mode (columns)
        sim = np.exp(-0.5 * ((pos[:, None] - r[None, :]) / sigma[None, :]) ** 2)
        explained = float(np.sum(w * sim.max(axis=1)))
        found = sim.max(axis=0)
        expect = np.where(inwin, 1.0, outside_weight * (r >= LOW_CUTOFF_CM1))
        wr = rel * expect * (rel >= MISSING_MIN_RELATIVE)
        missing = float(np.sum(wr * (1 - found)) / np.sum(wr)) if wr.sum() > 0 else 0.0
        sc = explained - MISSING_PENALTY * missing
        if best is None or sc > best[0] + 1e-12:
            best = (sc, s, sim, r, inwin, found)
    if best is None:
        return None
    sc, s, sim, r, inwin, found = best
    matched, unmatched = [], []
    for i, p in enumerate(pos):
        j = int(np.argmax(sim[i]))
        if sim[i, j] >= 0.5:
            matched.append((float(p), round(float(r[j]), 1), entry.modes[j].label))
        else:
            unmatched.append(float(p))
    missing = [(round(float(r[j]), 1), entry.modes[j].label, round(entry.modes[j].rel_intensity, 3))
               for j in range(len(r))
               if inwin[j] and found[j] < 0.5 and entry.modes[j].rel_intensity >= MISSING_MIN_RELATIVE]
    return Candidate(material=_reduced_formula(entry.material), score=round(sc, 4), matched=matched,
                     source=entry.source, scale=round(float(s), 4), unmatched=unmatched, missing=missing,
                     spacegroup=entry.spacegroup, kind=entry.kind, entry_id=entry.entry_id)


def match(positions, intensities=None, top_k: int = 5, x_range: tuple[float, float] | None = None,
          library: list[RefEntry] | None = None) -> list[Candidate]:
    """Rank reference materials for a measured peak list.

    positions: peak positions in cm-1 (substrate lines removed). intensities: peak heights or areas, same order;
    equal weights if None. x_range: the measured shift window (lo, hi), if known: every strong predicted mode
    inside it is expected, none outside. Otherwise predicted modes are fully expected within WINDOW_MARGIN_CM1 of
    the outermost peaks and weakly (OUTSIDE_WEIGHT) elsewhere. Returns at most top_k candidates, best first, one
    per material (the best-scoring polytype or reference; a literature table wins a tie with a CRD entry).
    """
    pos = np.asarray(positions, dtype=float)
    if pos.size == 0:
        return []
    w = np.ones_like(pos) if intensities is None else np.clip(np.abs(np.asarray(intensities, dtype=float)), 0, None)
    w = w / w.sum() if w.sum() > 0 else np.full_like(pos, 1.0 / pos.size)
    if x_range is not None:
        window, outside = (max(float(x_range[0]), LOW_CUTOFF_CM1), float(x_range[1])), 0.0
    else:
        window, outside = (pos.min() - WINDOW_MARGIN_CM1, pos.max() + WINDOW_MARGIN_CM1), OUTSIDE_WEIGHT
    if library is None:
        # Both references stay in the race for a material the literature covers: the measured table can sit a few
        # cm-1 away from a strained or doped sample, or from a spectrum simulated from DFT, where the CRD entry with
        # its fitted scale still matches. The better score per material wins; literature wins ties.
        library = literature_library() + list(crd_library())
    best: dict[tuple, Candidate] = {}
    for e in library:
        c = score_entry(e, pos, w, window, outside)
        if c is None:
            continue
        k = _formula_key(e.material)
        if k not in best or c.score > best[k].score + 1e-9 or (
                c.kind == "literature" and best[k].kind != "literature" and c.score >= best[k].score - 1e-9):
            best[k] = c
    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]
