import sys, json
from collections import Counter
db = {k: v for k, v in json.load(open(sys.argv[1])).items() if isinstance(v, dict)}
c = Counter(); ex = {}
for k, e in db.items():
    rt = e["data"].get("raman_tensors")
    t = type(rt).__name__
    if isinstance(rt, dict):
        t += ":" + ",".join(sorted(rt.keys())[:4])
    c[t] += 1; ex.setdefault(t, k)
print(c.most_common(10)); print(ex)
k = next(v for t, v in ex.items() if t.startswith("dict"))
rt = db[k]["data"]["raman_tensors"]
print(k, str(rt)[:600])
print(str(db["90"]["data"]["raman_tensors"])[:300])
