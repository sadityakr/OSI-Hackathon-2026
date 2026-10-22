import sys, pickle
sys.path.insert(0, sys.argv[1])
from crd_loader import load_crd, modes, summary
db = load_crd(sys.argv[2])
rows = []
for k, e in db.items():
    s = summary(e)
    if s["dimensionality"] != "2D" or s["negative_freq_Gamma"]:
        continue
    ms = [m for m in modes(e) if m["raman_active"] == 1]
    rows.append((k, s["formula"], s["spacegroup"], s["pointgroup"], s["natom"], len(ms)))
pickle.dump({k: db[k] for k, *_ in rows}, open(sys.argv[3], "wb"))
for r in sorted(rows, key=lambda r: r[4]):
    print(*r, sep=" | ")
