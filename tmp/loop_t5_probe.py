"""Throwaway probe: run the matcher on dev identify cases and print the top 5 with truth (dev only)."""
import sys
import time

sys.path.insert(0, "tests")
sys.path.insert(0, "eval")
from cases import dev_cases
from score import same_material

from ramanlens.perception.io import read_spectrum
from ramanlens.perception.library import match
from ramanlens.perception.pipeline import analyze_spectrum

t = time.time()
c0 = match([356.0, 418.0], intensities=[1.0, 0.6])
print("WS2 textbook", [(c.material, c.score, c.scale) for c in c0], f"{time.time()-t:.1f}s")
hits = 0
cases = dev_cases(kind="single", task="identify")
for c in cases:
    res = analyze_spectrum(read_spectrum(c["dir"] / "spectrum.csv"))
    s = [p for p in res.peaks if not p.is_substrate]
    cands = match([p.position for p in s], intensities=[p.height for p in s], top_k=5)
    rank = next((i for i, m in enumerate(cands) if same_material(m.material, c["truth"]["formula"])), None)
    hits += rank is not None and rank < 3
    print(c["id"], c["truth"]["formula"], "rank", rank, [round(p.position, 1) for p in s])
    for m in cands:
        print("   ", m.material, m.score, m.scale, m.spacegroup, m.matched, "miss", m.missing)
print(f"{hits}/{len(cases)}")
