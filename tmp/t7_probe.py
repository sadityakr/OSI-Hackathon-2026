"""Probe: per dev identify case, the top-3 matcher candidates with and without the literature tables.

Throwaway diagnostic for loop T7. Input: dev single cases via tests/contract/cases.py. Process: pipeline, then
match. Output: printed truth formula, peak positions and top candidates.
"""
import sys
sys.path.insert(0, "tests")
sys.path.insert(0, "eval")
from cases import dev_cases
from score import same_material
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.library import match
from ramanlens.perception.pipeline import analyze_spectrum

for c in dev_cases(kind="single", task="identify"):
    res = analyze_spectrum(read_spectrum(c["dir"] / "spectrum.csv"))
    s = [p for p in res.peaks if not p.is_substrate]
    cands = match([p.position for p in s], intensities=[p.height for p in s], top_k=5)
    hit = any(same_material(m.material, c["truth"]["formula"]) for m in cands[:3])
    print(c["dir"].name, c["truth"]["formula"], "HIT" if hit else "MISS",
          [round(p.position, 1) for p in s])
    for m in cands[:4]:
        print("   ", m.material, m.score, m.kind, m.matched, m.missing)
