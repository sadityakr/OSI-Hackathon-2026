"""Domain tools of RamanLens as Anthropic tool definitions plus one dispatcher, for the tooled agent arm.

The evaluation runner (eval/run_agent.py) and the demo give the model these tools next to a plain Python sandbox;
the score difference to the Python-only arm is the value of the tools. Each tool is a thin wrapper over the
perception, literature and relation layers, so the physics lives in those modules and is tested there; this
module only translates between JSON tool calls and Python objects and attaches provenance to every value.

Input: `call(name, input, workdir)` with a tool name from TOOLS, the model's JSON input (a dict) and the case
work folder. File paths in the input are resolved inside `workdir`; paths that leave it are refused, so the
agent can only read the data it was given.
Process: the matching handler runs the library function (reader, perception pipeline, matcher, polarization
classifier, literature tables, relation registry); every handler is wrapped in a LangSmith span with
`ramanlens.tracing.traced` (span names below) and tags the span with the material when it is known.
Output: a JSON string. Measured values carry `provenance: "measured"` and the `method` that produced them;
literature values carry `provenance: "literature"` and a `source` (citation, DOI or arXiv id, locator); relation
results carry the relation's source paper. Bad input that the model can fix (unknown material, unknown relation,
missing file) gives a JSON object with an `error` key and the valid options, not an exception. The one exception
to the JSON string: view_figure with a figure returns a list of two content blocks (the JSON text and the PNG
image), which the Anthropic API accepts as tool_result content, so the model sees the figure.

Span names: io.read (load_spectrum), fit_peaks, match_library, polarization.classify, literature.lookup,
relation.list, relation.<relation name> (apply_relation), literature.find_papers and figure.view (the optional
literature figure tools, present only when the iopic_bond package is installed).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np

from ramanlens.literature import figure_tools, reference_tables
from ramanlens.perception.io import AngleSeries, Spectrum, read_series, read_spectrum
from ramanlens.perception.library import match
from ramanlens.perception.pipeline import analyze_spectrum
from ramanlens.perception.polarization import analyze_series
from ramanlens.relations import registry
from ramanlens.tracing import add_metadata, traced

FIT_METHOD = ("cosmic-ray spikes removed (narrow outliers vs running median), asymmetric least squares baseline "
              "(Eilers and Boelens 2005), prominence-based detection, grouped multi-Lorentzian least-squares fit; "
              "errors are 1-sigma from the fit covariance")

_PATH_PROP = {"path": {"type": "string", "description": "Data file inside the work folder, e.g. 'spectrum.csv'."}}

TOOLS = [
    {
        "name": "load_spectrum",
        "description": "Read a Raman data file from the work folder and describe it without fitting: kind "
                       "(single spectrum or polarization angle series), number of points, shift range and "
                       "spacing in cm-1, intensity range, and for angle series the configurations and angles. "
                       "Use it first to see what the file contains.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["path"],
                         "properties": dict(_PATH_PROP)},
    },
    {
        "name": "fit_peaks",
        "description": "Find and fit the Raman bands of a spectrum: removes cosmic-ray spikes, subtracts an "
                       "asymmetric least squares baseline, fits Lorentzians, excludes the laser-line region when "
                       "the axis reaches it, and flags a narrow line at 520.7 +- 2 cm-1 as the Si substrate. "
                       "Returns each band's position, FWHM, height, area with 1-sigma errors, the removed spikes "
                       "and notes on every automatic decision. For an angle series the bands are fitted on the "
                       "sum of all spectra.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["path"],
                         "properties": {
                             **_PATH_PROP,
                             "substrate": {"type": "string",
                                           "description": "Substrate if known, e.g. 'SiO2/Si' or 'sapphire'; a "
                                                          "non-silicon substrate disables the Si flag."},
                             "min_shift_cm1": {"type": "number",
                                               "description": "Lowest shift to analyse; default 50 cm-1 when the "
                                                              "axis reaches the laser line, else no limit."},
                             "min_snr": {"type": "number",
                                         "description": "Detection threshold in noise sigmas (default 5)."}}},
    },
    {
        "name": "match_library",
        "description": "Rank candidate materials for a list of measured peak positions against the Computational "
                       "Raman Database (DFT modes visible in backscattering along the layer normal, with a fitted "
                       "global frequency scale per candidate) and the curated literature mode tables. Returns per "
                       "candidate the score, the matched (measured, reference, label) triples, unmatched measured "
                       "peaks, strong reference modes that are missing, and the source. Leave substrate lines out "
                       "of the positions.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["positions_cm1"],
                         "properties": {
                             "positions_cm1": {"type": "array", "items": {"type": "number"},
                                               "description": "Measured sample peak positions in cm-1."},
                             "intensities": {"type": "array", "items": {"type": "number"},
                                             "description": "Peak heights or areas in the same order (optional)."},
                             "x_range_cm1": {"type": "array", "items": {"type": "number"}, "minItems": 2,
                                             "maxItems": 2,
                                             "description": "Measured shift window [lo, hi]; strongly "
                                                            "recommended, so modes outside it are not expected."},
                             "top_k": {"type": "integer", "description": "Number of candidates (default 5)."}}},
    },
    {
        "name": "classify_polarization",
        "description": "Analyse a polarization angle series (long-format file with shift_cm1, intensity, "
                       "angle_deg, config = parallel or crossed): fits the bands on the summed spectrum, extracts "
                       "each band's intensity per angle and configuration, and classifies its angle dependence as "
                       "isotropic_par_only, isotropic_both, twofold, fourfold, other or undetermined, with the "
                       "angle of maximum parallel intensity for twofold bands.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["path"],
                         "properties": dict(_PATH_PROP)},
    },
    {
        "name": "lookup_reference_modes",
        "description": "Return the curated literature Raman modes of a material (graphene, 2H-MoS2, 2H-WS2, "
                       "2H-MoSe2, 2H-WSe2, CrSBr, hBN, black phosphorus): position, label, irrep and measurement "
                       "conditions of each mode, every one with its source paper (DOI or arXiv id) and locator, "
                       "plus layer-dependent and conditional modes, notes and modes left out as unverified.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["material"],
                         "properties": {
                             "material": {"type": "string",
                                          "description": "Name, formula or alias, e.g. '2H-MoS2', 'MoS2', 'hBN'."}}},
    },
    {
        "name": "list_relations",
        "description": "List the physics relations that turn Raman quantities into material properties (layer "
                       "number, defect distance, strain and doping, mode assignment): for each the equation with "
                       "all variables defined, the required and optional inputs with units, outputs, validity "
                       "range, source paper with locator and caveats. Filter by material and/or input quantity.",
        "input_schema": {"type": "object", "additionalProperties": False,
                         "properties": {
                             "material": {"type": "string", "description": "e.g. 'MoS2', 'graphene', 'CrSBr'."},
                             "input_quantity": {"type": "string",
                                                "description": "An input name, e.g. 'delta_E2g_A1g_cm1'."}}},
    },
    {
        "name": "apply_relation",
        "description": "Apply one physics relation by name (see list_relations) to measured inputs. Fails closed: "
                       "outside the validity range stated in the source paper it returns applicable=false with "
                       "the reason instead of an extrapolated number. The result carries the relation's source "
                       "paper and caveats.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["name", "inputs"],
                         "properties": {
                             "name": {"type": "string", "description": "Relation name from list_relations."},
                             "inputs": {"type": "object",
                                        "description": "Input name -> value, names and units as listed."}}},
    },
]

# Optional literature figure tools, offered only when the iopic_bond package is installed.
FIGURE_TOOLS = [
    {
        "name": "find_papers",
        "description": "Find papers on a concept through Valency Bond (embedding search over arXiv, PubMed and "
                       "more). Query by material and property, e.g. 'Raman mode assignment and polarization in "
                       "CrSBr', never by peak positions or numbers (the search does not encode numbers). Returns id, "
                       "title, year, DOI, whether figures can be extracted (`parseable`, arXiv only) and whether the "
                       "paper is already parsed (`in_library`). Form a hypothesis from the spectrum first.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["query"],
                         "properties": {
                             "query": {"type": "string", "description": "Concept query: material plus property."},
                             "limit": {"type": "integer", "description": "Number of papers (default 10, max 50)."},
                             "start_date": {"type": "string",
                                            "description": "Optional lower date bound, YYYY or YYYY-MM-DD."}}},
    },
    {
        "name": "view_figure",
        "description": "Look at a figure of an arXiv paper, e.g. its published Raman spectrum, to compare it with "
                       "the measurement. Without `figure` it lists the paper's figures with captions; with a printed "
                       "figure number ('2', 'Fig. 2') it returns the image plus caption, page and a citation string "
                       "('Fig 2 of arXiv:<id>'). The first call on a paper downloads and parses it, which can take "
                       "minutes; later calls are instant.",
        "input_schema": {"type": "object", "additionalProperties": False, "required": ["arxiv_id"],
                         "properties": {
                             "arxiv_id": {"type": "string", "description": "arXiv id, e.g. '1005.2509'."},
                             "figure": {"type": "string", "description": "Printed figure number; omit to list."},
                             "max_px": {"type": "integer",
                                        "description": "Longer image side in pixels (default 1200)."}}},
    },
]
if figure_tools.AVAILABLE:
    TOOLS += FIGURE_TOOLS


# --------------------------------------------------------------------------------------------- helpers


def _resolve(path: str, workdir) -> Path:
    """Path inside the work folder; refuses paths that point outside it."""
    root = Path(workdir).resolve()
    p = (root / path).resolve()
    if p != root and root not in p.parents:
        raise PermissionError(f"path {path!r} is outside the work folder")
    if not p.is_file():
        raise FileNotFoundError(f"no file {path!r} in the work folder")
    return p


def _is_angle_series(p: Path) -> bool:
    """True when the first non-comment line is a header naming an angle_deg column."""
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith(("#", "%", "//")):
                return "angle_deg" in s.lower()
    return False


def _load(p: Path) -> Spectrum | AngleSeries:
    return read_series(p) if _is_angle_series(p) else read_spectrum(p)


def _num(v, nd: int = 3):
    """Round a float for JSON; None and non-finite values become None."""
    if v is None:
        return None
    v = float(v)
    return round(v, nd) if np.isfinite(v) else None


def _source_dict(src) -> dict:
    return {"citation": src.citation, "doi": src.doi, "arxiv": src.arxiv, "locator": src.locator}


# --------------------------------------------------------------------------------------------- tools
# Each tool function is wrapped by @traced, which records the call as a LangSmith span when tracing is configured
# and returns the function unchanged otherwise.


@traced("io.read")
def load_spectrum(path: str, workdir) -> dict:
    p = _resolve(path, workdir)
    data = _load(p)
    x = np.asarray(data.x, dtype=float)
    out = {"path": path, "n_points": int(x.size), "x_range_cm1": [_num(x[0], 2), _num(x[-1], 2)],
           "median_spacing_cm1": _num(np.median(np.diff(x)), 4) if x.size > 1 else None}
    if isinstance(data, AngleSeries):
        ys = np.array(list(data.spectra.values()), dtype=float)
        out.update(kind="angle_series", configs=data.configs, angles_deg=data.angles,
                   n_spectra=len(data.spectra), interpolated=bool(data.meta.get("interpolated")),
                   intensity_range=[_num(ys.min()), _num(ys.max())])
    else:
        out.update(kind="single", header=data.meta.get("header"),
                   intensity_range=[_num(data.y.min()), _num(data.y.max())])
    out["provenance"] = "measured"
    out["method"] = "file read; shift axis sorted ascending, duplicate shifts averaged"
    return out


@traced("fit_peaks")
def fit_peaks(path: str, workdir, substrate: str | None = None, min_shift_cm1: float | None = None,
              min_snr: float = 5.0) -> dict:
    p = _resolve(path, workdir)
    data = _load(p)
    meta = dict(data.meta or {})
    notes = []
    if isinstance(data, AngleSeries):
        y = np.sum([np.asarray(v, dtype=float) for v in data.spectra.values()], axis=0)
        notes.append(f"angle series: bands fitted on the sum of {len(data.spectra)} spectra; heights are sums "
                     "(use classify_polarization for per-angle intensities)")
        spec = Spectrum(data.x, y, meta)
    else:
        spec = data
    if substrate:
        spec.meta["substrate"] = substrate
    res = analyze_spectrum(spec, min_shift_cm1=min_shift_cm1, min_snr=min_snr)
    peaks = [{"position_cm1": _num(pk.position, 2), "position_err_cm1": _num(pk.position_err),
              "fwhm_cm1": _num(pk.fwhm, 2), "fwhm_err_cm1": _num(pk.fwhm_err),
              "height": _num(pk.height, 4), "height_err": _num(pk.height_err, 4), "area": _num(pk.area, 4),
              "shape": pk.shape, "is_substrate": bool(pk.is_substrate), "provenance": "measured"}
             for pk in sorted(res.peaks, key=lambda q: q.position)]
    x = np.asarray(spec.x, dtype=float)
    lo = max(float(x[0]), res.min_shift_cm1) if res.min_shift_cm1 is not None else float(x[0])
    return {"path": path, "peaks": peaks, "spikes_cm1": [_num(s, 2) for s in res.spikes],
            "analysed_range_cm1": [_num(lo, 2), _num(x[-1], 2)], "notes": notes + list(res.notes),
            "provenance": "measured", "method": FIT_METHOD}


def _literature_table_for(material: str) -> str | None:
    try:
        return reference_tables.get_table(material).name
    except KeyError:
        return None


@traced("match_library")
def match_library(positions_cm1, workdir=None, intensities=None, x_range_cm1=None, top_k: int = 5) -> dict:
    x_range = tuple(float(v) for v in x_range_cm1[:2]) if x_range_cm1 else None
    cands = match(positions_cm1, intensities, top_k=int(top_k), x_range=x_range)
    out = []
    for c in cands:
        out.append({
            "material": c.material, "score": c.score, "kind": c.kind, "source": c.source,
            "entry_id": c.entry_id, "spacegroup": c.spacegroup, "frequency_scale": c.scale,
            "matched": [{"measured_cm1": _num(m, 2), "reference_cm1": _num(r, 2), "label": lab}
                        for m, r, lab in c.matched],
            "unmatched_measured_cm1": [_num(u, 2) for u in c.unmatched],
            "missing_strong_modes": [{"reference_cm1": _num(r, 2), "label": lab, "rel_intensity": _num(i)}
                                     for r, lab, i in c.missing],
            # A curated measured table exists for this material even when the CRD entry scored higher; the agent
            # should check the assignment against it with lookup_reference_modes.
            "literature_table": _literature_table_for(c.material),
        })
    if out:
        add_metadata(material=out[0]["material"])
    notes = []
    if x_range is None:
        notes.append("no x_range_cm1 given: strong reference modes far from the measured peaks count only weakly "
                     "as missing; pass the analysed range for a stricter match")
    return {"candidates": out, "notes": notes, "provenance": "inferred",
            "method": "score = explained fraction of measured intensity minus a penalty for strong reference modes "
                      "inside the window that were not found; DFT frequencies of the Computational Raman Database "
                      "(Bagheri and Komsa 2023) scaled by a per-candidate factor 0.98 to 1.05; literature tables "
                      "unscaled"}


@traced("polarization.classify")
def classify_polarization(path: str, workdir) -> dict:
    p = _resolve(path, workdir)
    if not _is_angle_series(p):
        return {"error": f"{path!r} is a single spectrum; classify_polarization needs an angle series with "
                         "columns shift_cm1, intensity, angle_deg, config"}
    bands = analyze_series(read_series(p))
    for b in bands:
        b["provenance"] = "measured"
    return {"path": path, "bands": bands, "provenance": "measured",
            "pattern_classes": {"isotropic_par_only": "parallel constant, crossed near zero (e.g. A1g)",
                                "isotropic_both": "parallel and crossed constant and about equal (E pair)",
                                "twofold": "180 degree period in parallel (e.g. Ag of an orthorhombic crystal)",
                                "fourfold": "cos^2(2 theta) in parallel, sin^2(2 theta) in crossed (B modes)",
                                "other": "none of the above", "undetermined": "too few angles or no crossed data"}}


@traced("literature.lookup")
def lookup_reference_modes(material: str, workdir=None) -> dict:
    try:
        t = reference_tables.get_table(material)
    except KeyError:
        return {"error": f"no literature table for {material!r}", "available": reference_tables.table_names(),
                "hint": "match_library also searches the Computational Raman Database for other materials"}
    add_metadata(material=t.name)

    def mode(m) -> dict:
        return {"position_cm1": m.position_cm1, "label": m.label, "irrep": m.irrep, "conditions": m.conditions,
                "note": m.note, "rel_intensity": m.rel_intensity, "source": _source_dict(m.source),
                "provenance": "literature"}

    return {"material": t.name, "formula": t.formula, "aliases": t.aliases, "conditions": t.conditions,
            "modes": [mode(m) for m in t.modes],
            "layer_dependence": [mode(m) for m in t.layer_dependence],
            "conditional_modes": [mode(m) for m in t.conditional_modes],
            "notes": t.notes, "omitted": t.omitted, "provenance": "literature"}


@traced("relation.list")
def list_relations(workdir=None, material: str | None = None, input_quantity: str | None = None) -> dict:
    rels = registry.find(material=material, input_quantity=input_quantity)
    out = {"relations": [r.describe() for r in rels]}
    if not rels:
        out["note"] = "no relation matches the filter"
        out["known"] = [{"name": r.name, "material": r.material} for r in registry.all_relations()]
    return out


def apply_relation(name: str, inputs: dict | None = None, workdir=None) -> dict:
    try:
        rel = registry.get(name)
    except KeyError:
        return {"error": f"no relation named {name!r}", "known": [r.name for r in registry.all_relations()]}

    # The span is named after the relation (relation.<name>), so it is created per call rather than at import.
    @traced(f"relation.{name}")
    def _apply(**kw) -> dict:
        add_metadata(material=rel.material)
        return rel.apply(**kw).to_dict()

    out = _apply(**(inputs or {}))
    out["provenance"] = "inferred"
    return out


def find_papers(query: str, workdir=None, limit: int = 10, start_date: str | None = None) -> dict:
    return figure_tools.find_papers(query, limit=limit, start_date=start_date)


def view_figure(arxiv_id: str, workdir=None, figure: str | None = None, max_px: int = 1200) -> dict:
    return figure_tools.view_figure(arxiv_id, figure=figure, max_px=max_px)


_HANDLERS = {
    "load_spectrum": load_spectrum,
    "fit_peaks": fit_peaks,
    "match_library": match_library,
    "classify_polarization": classify_polarization,
    "lookup_reference_modes": lookup_reference_modes,
    "list_relations": list_relations,
    "apply_relation": apply_relation,
}
if figure_tools.AVAILABLE:
    _HANDLERS.update(find_papers=find_papers, view_figure=view_figure)


def call(name: str, input: dict, workdir) -> str | list:
    """Run tool `name` with the model's input dict in `workdir` and return its JSON output as a string.

    Unknown tools raise KeyError; library errors propagate, and the runner reports them to the model as tool
    errors. Inputs the model can correct (unknown material or relation) come back as JSON with an `error` key.
    A view_figure result that contains an image is returned as [text block, image block] instead of a string.
    """
    if name not in _HANDLERS:
        raise KeyError(f"unknown tool {name!r}; available: {', '.join(_HANDLERS)}")
    result = _HANDLERS[name](workdir=workdir, **(input or {}))
    png = result.pop("png", None) if isinstance(result, dict) else None
    text = json.dumps(result, default=str)
    if png is None:
        return text
    return [{"type": "text", "text": text},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(png).decode("ascii")}}]
