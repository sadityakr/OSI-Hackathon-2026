"""Smoke test for the figure pipeline on the PC (needs network and docling).

    cd "OSI Hackathon"
    python scratch/smoke_figures.py 2211.12939        # Pawbake et al., CrSBr spin-phonon
    python scratch/smoke_figures.py 1005.2509 --cuda  # Lee et al. 2010, MoS2 layer counting

First run downloads Docling models (about 1 GB) and takes a few minutes; later runs use the cache.
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ramanlens.literature.arxiv import fetch_pdf
from ramanlens.literature.figures import extract_figures, likely_spectrum_figures

arxiv_id = sys.argv[1] if len(sys.argv) > 1 else "2211.12939"
device = "cuda" if "--cuda" in sys.argv else "cpu"
root = Path(__file__).resolve().parents[1]

t0 = time.time()
pdf = fetch_pdf(arxiv_id, root / "data/raw/pdfs")
print("pdf:", pdf, f"({time.time()-t0:.1f}s)")
assert pdf, "download failed"

t0 = time.time()
figs = extract_figures(pdf, root / "data/raw/parsed", device=device)
print(f"parsed in {time.time()-t0:.1f}s, {len(figs)} figures")
for f in figs:
    print(f"  {f.label or '(no label)':10s} p{f.page}  img={'yes' if f.image_path else 'no '}  mentions={len(f.mentions)}  {f.caption[:90]}")
print("likely spectrum figures:", [f.label for f in likely_spectrum_figures(figs)])
