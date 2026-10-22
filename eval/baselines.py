"""Non-LLM baselines for the comparison: classical library search and the RamanLens pipeline without an agent.

The project claim is an improvement over the existing state of the art, which for Raman identification without
an LLM is (a) full-spectrum library search by correlation or cosine similarity after preprocessing, the method of
commercial software and of the RRUFF tools and the classical baseline benchmarked by Li, Schmidt and Alstrom
(Analyst 2022, doi:10.1039/D2AN00403H), and (b) peak-list matching against a reference database. No public
deep-learning model covers 2D materials, and closed-set classifiers cannot name materials outside their training
classes, so none is included (see docs/sota-research.md). Both baselines write reports in the agents' schemas, so
eval/score.py and eval/judge.py grade them exactly like the agent arms.

Input:
    Test-set cases (data/test_set/<split>/<case>/input.json and spectrum*.csv); truth and rubrics are never read.
    Reference data: the Computational Raman Database (385 layered crystals) and the curated literature tables,
    through ramanlens.perception.library.
Process:
    Arm `libsearch`: despike and ALS baseline (ramanlens pipeline), Si line masked when flagged, spectrum compared by
    cosine similarity with a library of simulated spectra (Lorentzians, FWHM 6 cm-1, reference relative intensities)
    over the measured window; for computed (DFT) entries the best global frequency scale in 0.98 to 1.05 is used.
    Peaks are assigned the irrep of the nearest mode of the best hit within 8 cm-1.
    Arm `pipeline`: fitted peaks -> ramanlens.perception.library.match (peak-list matcher with scale fit and missing-
    mode penalty) -> irreps from the matched modes -> relations from the registry applied where their inputs can be
    computed (MoS2 and WS2 layer number from the two strongest bands, graphene L_D from I_D/I_G).
    Verify tasks: consistent if the stated material is among the top 3 candidates. Interpretation cases (pipeline arm
    only): per-spectrum fits, band tracking and the same relations, written as observations.
Output:
    eval/runs/<run>/<arm>/<case>/report.json and transcript.json (method notes, timing), like the agent runners.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from score import material_counts  # noqa: E402  (same material-name parsing as the scorer)

from ramanlens.agent import toolset  # noqa: E402
from ramanlens.perception.io import read_series, read_spectrum, Spectrum  # noqa: E402
from ramanlens.perception.library import crd_library, literature_library, match  # noqa: E402
from ramanlens.perception.pipeline import analyze_spectrum  # noqa: E402

GRID = np.arange(40.0, 3300.0, 1.0)
LIB_FWHM = 6.0
SCALES = np.arange(0.98, 1.0501, 0.005)


def lorentz_sum(x, positions, heights, fwhm=LIB_FWHM):
    g = (fwhm / 2) ** 2
    return sum(h * g / ((x - p) ** 2 + g) for p, h in zip(positions, heights))


def load_case_spectrum(path, substrate):
    """Single spectrum, or the sum of all frames of an angle series (a library search sees one spectrum)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        header = fh.readline().lower()
    if "angle" in header:
        s = read_series(path)
        y = np.sum([np.asarray(v) for v in s.spectra.values()], axis=0)
        return Spectrum(x=np.asarray(s.x), y=y, meta={"substrate": substrate, "path": Path(path)})
    s = read_spectrum(path)
    s.meta = {**(s.meta or {}), "substrate": substrate}
    return s


class LibrarySearch:
    """Full-spectrum cosine search against simulated reference spectra (the classical method)."""

    def __init__(self):
        self.entries = list(literature_library()) + list(crd_library())

    def search(self, x, y, top_k=5):
        lo, hi = float(x[0]), float(x[-1])
        m = (GRID >= lo) & (GRID <= hi)
        q = np.interp(GRID[m], x, y)
        q = np.clip(q, 0, None)
        qn = np.linalg.norm(q) or 1.0
        out = []
        for e in self.entries:
            pos = np.array([md.position_cm1 for md in e.modes])
            hts = np.array([md.rel_intensity for md in e.modes])
            best = (-1.0, 1.0)
            for s in (SCALES if e.kind == "crd" else [1.0]):
                ref = lorentz_sum(GRID[m], pos * s, hts)
                rn = np.linalg.norm(ref)
                if rn > 0:
                    c = float(q @ ref / (qn * rn))
                    if c > best[0]:
                        best = (c, s)
            out.append((best[0], best[1], e))
        out.sort(key=lambda t: -t[0])
        return out[:top_k]


def nearest_irrep(entry, scale, position, tol=8.0):
    best = None
    for md in entry.modes:
        d = abs(md.position_cm1 * scale - position)
        if d <= tol and (best is None or d < best[0]):
            best = (d, md.irrep or md.label)
    return best[1] if best else None


def same_material(a, b):
    ca, cb = material_counts(a), material_counts(b)
    return ca is not None and ca == cb


def auto_relations(material, peaks, laser_nm):
    """Apply registry relations whose inputs follow from the fitted peaks; returns report properties."""
    props = []
    sample = sorted([p for p in peaks if not p.is_substrate], key=lambda p: -p.height)
    mc = material_counts(material) or {}
    rel = None
    if mc in ({"Mo": 1, "S": 2}, {"W": 1, "S": 2}) and len(sample) >= 2:
        a, b = sorted(sample[:2], key=lambda p: p.position)
        name = "mos2_layer_number_from_separation" if "Mo" in mc else "ws2_layer_number_from_separation"
        rel = (name, {"delta_E2g_A1g_cm1": round(b.position - a.position, 2)})
    elif mc == {"C": 1}:
        d = [p for p in sample if 1300 < p.position < 1400]
        g = [p for p in sample if 1560 < p.position < 1610]
        if d and g and laser_nm:
            rel = ("graphene_defect_distance_from_ID_IG",
                   {"I_D_over_I_G": round(d[0].height / g[0].height, 3), "laser_nm": laser_nm})
    if rel:
        res = json.loads(toolset.call("apply_relation", {"name": rel[0], "inputs": rel[1]}, ROOT))
        if res.get("applicable"):
            vals = res.get("values", {})
            if "layer_number" in vals:
                props.append({"name": "layers", "value": str(vals.get("layer_label", vals["layer_number"])),
                              "provenance": "inferred", "source": f"{rel[0]} ({res.get('source', '')})"[:300]})
            if "L_D_nm" in vals:
                props.append({"name": "L_D_nm", "value": str(vals["L_D_nm"]), "provenance": "inferred",
                              "source": f"{rel[0]}"})
    return props


def report_identify(arm, inp, spec, lib):
    res = analyze_spectrum(spec)
    peaks = res.peaks
    x = np.asarray(res.x)
    sig = np.asarray(res.y_clean) - np.nan_to_num(np.asarray(res.baseline))
    for p in peaks:  # mask the substrate line, as a user of library-search software would
        if p.is_substrate:
            sig[np.abs(x - p.position) < 3 * p.fwhm] = 0.0
    sample = [p for p in peaks if not p.is_substrate]
    if arm == "libsearch":
        hits = lib.search(x, sig)
        cands = [{"material": e.material, "confidence": round(c, 3),
                  "evidence": f"cosine {c:.3f} against {e.kind} reference ({e.source[:80]}), scale {s:.3f}"}
                 for c, s, e in hits]
        top = hits[0] if hits else None
        irrep_of = (lambda pos: nearest_irrep(top[2], top[1], pos)) if top else (lambda pos: None)
        props = []
    else:
        cs = match([p.position for p in sample], [p.height for p in sample], top_k=5,
                   x_range=(float(x[0]), float(x[-1])))
        cands = [{"material": c.material, "confidence": round(float(c.score), 3),
                  "evidence": f"peak-list match ({c.kind}), scale {c.scale:.3f}, matched {len(c.matched)}, "
                              f"missing {len(c.missing)}"} for c in cs]
        labels = {round(mp, 2): lab for mp, _, lab in (cs[0].matched if cs else [])}
        irrep_of = lambda pos: labels.get(round(pos, 2))  # noqa: E731
        props = auto_relations(cs[0].material, peaks, inp.get("laser_nm")) if cs else []
    patterns = {}
    if arm == "pipeline" and inp.get("kind") == "angle_series" and spec.meta.get("path"):
        pol = json.loads(toolset.call("classify_polarization", {"path": spec.meta["path"].name},
                                      spec.meta["path"].parent))
        for b in pol.get("peaks", pol.get("bands", [])):
            pos = b.get("position_cm1")
            if pos is not None:
                patterns[round(float(pos), 1)] = b.get("pattern")

    def pattern_of(pos):
        near = [(abs(k - pos), v) for k, v in patterns.items() if abs(k - pos) < 4]
        return min(near)[1] if near else None

    out_peaks = [{"position_cm1": round(p.position, 2), "fwhm_cm1": round(p.fwhm, 2),
                  "assignment": "Si substrate" if p.is_substrate else (irrep_of(p.position) or "unassigned"),
                  "irrep": None if p.is_substrate else irrep_of(p.position), "pattern": pattern_of(p.position),
                  "provenance": "measured", "source": None} for p in peaks]
    hint = inp.get("material_hint")
    if inp["task"] == "verify" and hint:
        ok = any(same_material(c["material"], hint) for c in cands[:3])
        verdict, why = ("consistent" if ok else "inconsistent"), "stated material among top 3" if ok else \
            "stated material not among top 3"
    else:
        verdict, why = "not_applicable", "identify task"
    return {"candidates": cands, "hint_verdict": verdict, "hint_reasoning": why, "peaks": out_peaks,
            "properties": props, "artifacts": [{"type": "cosmic_ray", "position_cm1": float(s)} for s in res.spikes],
            "citations": [], "limits": []}


def report_interpret(inp, case_dir):
    obs, props, per = [], [], []
    for s in inp["spectra"]:
        cond = s.get("conditions", {})
        spec = read_spectrum(case_dir / s["file"])
        spec.meta = {**(spec.meta or {}), "substrate": inp.get("context", "")}
        res = analyze_spectrum(spec)
        sample = sorted([p for p in res.peaks if not p.is_substrate], key=lambda p: -p.height)
        per.append((s["label"], sample))
        obs.append({"finding": f"{s['label']}: bands at " + ", ".join(f"{p.position:.1f}" for p in
                                                                       sorted(sample[:6], key=lambda p: p.position)),
                    "evidence": "; ".join(f"{p.position:.2f}+-{(p.position_err or 0):.2f} cm-1, FWHM {p.fwhm:.1f}"
                                          for p in sample[:6]),
                    "provenance": "measured", "source": None})
        for pr in auto_relations(inp["material"], res.peaks, cond.get("laser_nm")):
            pr["value"] = f"{s['label']}: {pr['value']}"
            props.append(pr)
    if len(per) > 1 and per[0][1]:
        ref = per[0][1][0]
        for lab, sample in per[1:]:
            near = [p for p in sample if abs(p.position - ref.position) < 6]
            if near:
                obs.append({"finding": f"strongest band of {per[0][0]} shifts by {near[0].position - ref.position:+.2f}"
                                       f" cm-1 in {lab}", "evidence": "pipeline fit positions", "provenance": "measured",
                            "source": None})
    return {"summary": "Automatic pipeline output: fitted bands per spectrum, band shifts, and relations applied "
                       "where inputs were available.", "observations": obs, "properties": props, "caveats": [],
            "questions_for_user": [], "citations": [], "limits": []}


def main():
    ap = argparse.ArgumentParser(description="Run the non-LLM baselines (libsearch, pipeline) over test-set cases.")
    ap.add_argument("--arm", choices=["libsearch", "pipeline"], required=True, help="baseline to run")
    ap.add_argument("--split", default="dev", help="dev, dev_hard, dev_interpret or heldout")
    ap.add_argument("--run-name", required=True, help="output folder under eval/runs/")
    ap.add_argument("--kind", choices=["all", "identify", "interpret"], default="all", help="case kind filter")
    args = ap.parse_args()

    lib = LibrarySearch() if args.arm == "libsearch" else None
    for d in sorted(p for p in (ROOT / "data" / "test_set" / args.split).iterdir() if (p / "input.json").exists()):
        inp = json.loads((d / "input.json").read_text())
        interpret = inp.get("kind") == "interpret"
        if (args.kind == "identify" and interpret) or (args.kind == "interpret" and not interpret):
            continue
        if interpret and args.arm == "libsearch":
            continue  # a library search answers "which material"; it has nothing to say on a known material
        out = ROOT / "eval" / "runs" / args.run_name / args.arm / d.name
        out.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        try:
            rep = report_interpret(inp, d) if interpret else \
                report_identify(args.arm, inp, load_case_spectrum(d / "spectrum.csv", inp.get("substrate")), lib)
        except Exception as e:  # a failed baseline case is scored as failed, not hidden
            print(f"{args.arm} {d.name}: ERROR {type(e).__name__}: {e}", flush=True)
            continue
        (out / "report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
        (out / "transcript.json").write_text(json.dumps({"arm": args.arm, "case": inp, "usage": {
            "seconds": round(time.time() - t0, 2)}, "method": __doc__.split("Process:")[1].split("Output:")[0]}))
        print(f"{args.arm} {d.name}: ok ({time.time() - t0:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
