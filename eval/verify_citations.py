"""Check that the papers an agent cites exist and are what the report says they are.

A strong model answers textbook cases from memory; the skill's claim is that its answers can be traced. This scorer
tests the claim directly: every entry in a report's `citations` list is resolved against arXiv and Crossref, so
invented or garbled references are counted per arm. It checks the reference, not the number quoted from it.

Input:
    eval/runs/<run>/<arm>/<case>/report.json for each arm (the `citations` list, free text), network access.
Process:
    Per citation: take the first author surname and the year from the text, then resolve
      - an arXiv id (arXiv API) or a DOI (Crossref) if the text gives one: verified when the first author and year
        (within one year, preprint vs journal) match; mismatch when the id exists but the author or year does not;
        not_found when the id does not exist;
      - otherwise the best Crossref bibliographic match: verified on the same author and year test, else unresolved
        (books, theses and old papers can land here; unresolved is not counted as wrong). Entries that point at a skill
        note file are internal_note and left out of the rate.
    Citations the report itself marks "from recall" or "not checked" are counted separately.
Output:
    eval/runs/<run>/citation_check.json (per citation) and a table per arm printed to the terminal: citations per
    report, verified, mismatch plus not_found (the hallucination rate), unresolved, self-flagged as unchecked.
"""

import argparse
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARXIV_RE = re.compile(r"(?:arxiv[:\s]*)?\b(\d{4}\.\d{4,5})(?:v\d+)?\b", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s,;)]+)", re.I)
UNCHECKED_RE = re.compile(r"from recall|not checked|not verified|unverified|could not verify", re.I)
UA = {"User-Agent": "RamanLens-citation-check (mailto:none@example.org)"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def clean(text):
    text = re.sub(r"^\s*\[[^\]]*\]\([^)]*\):?\s*", "", text)  # markdown link prefix, e.g. [arXiv:1](url): Lee 2012
    return re.sub(r"^\s*arxiv[:\s]*\d{4}\.\d{4,5}(v\d+)?[:,]?\s*", "", text, flags=re.I)


def surname(text):
    m = re.match(r"\s*([A-Z][\w'\-\u2019]+)", text)
    return fold(m.group(1)) if m else None


def year(text):
    m = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", text)
    return int(m.group(1)) if m else None


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                return r.read()
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def arxiv_meta(aid):
    raw = get(f"https://export.arxiv.org/api/query?id_list={aid}")
    if not raw:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(raw).find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None or entry.find("a:title", ns).text.strip() == "Error":
        return {"exists": False}
    names = [fold(n.text.split()[-1]) for n in entry.findall("a:author/a:name", ns)]
    return {"exists": True, "authors": names, "year": int(entry.find("a:published", ns).text[:4]),
            "title": " ".join(entry.find("a:title", ns).text.split())}


def crossref_item(item):
    fam = [fold(a.get("family", "")) for a in item.get("author", [])]
    parts = (item.get("issued") or item.get("published") or {}).get("date-parts", [[None]])[0]
    return {"exists": True, "authors": fam, "year": parts[0], "title": (item.get("title") or [""])[0]}


def doi_meta(doi):
    raw = get("https://api.crossref.org/works/" + urllib.parse.quote(doi.rstrip(".")))
    return crossref_item(json.loads(raw)["message"]) if raw else {"exists": False}


def search_meta(text):
    q = urllib.parse.urlencode({"query.bibliographic": text[:300], "rows": 3})
    raw = get("https://api.crossref.org/works?" + q)
    items = json.loads(raw)["message"]["items"] if raw else []
    return [crossref_item(i) for i in items]


def matches(meta, sn, yr):
    if not meta or not meta.get("exists") or not meta.get("authors"):
        return False
    ok_author = sn is not None and sn in meta["authors"][:2]  # first author, or first two for name-order quirks
    ok_year = yr is None or meta.get("year") is None or abs(meta["year"] - yr) <= 1
    return ok_author and ok_year


def check(text, cache):
    if text in cache:
        return cache[text]
    if re.match(r"\s*(reference/|skill/|\S+\.md\b)", text):  # points at a skill note, not a paper
        cache[text] = {"text": text, "status": "internal_note", "self_flagged_unchecked": False,
                       "resolved_title": None}
        return cache[text]
    body = clean(text)
    sn, yr = surname(body), year(body)
    aid = ARXIV_RE.search(text)
    doi = DOI_RE.search(text)
    meta, status = None, "unresolved"
    if aid:
        meta = arxiv_meta(aid.group(1))
        status = ("not_found" if meta and not meta["exists"] else "verified" if matches(meta, sn, yr) else "mismatch")
        if meta is None:
            status = "unresolved"
    elif doi:
        meta = doi_meta(doi.group(1))
        status = "not_found" if not meta["exists"] else "verified" if matches(meta, sn, yr) else "mismatch"
    else:
        for cand in search_meta(body):
            if matches(cand, sn, yr):
                meta, status = cand, "verified"
                break
    res = {"text": text, "status": status, "self_flagged_unchecked": bool(UNCHECKED_RE.search(text)),
           "resolved_title": (meta or {}).get("title")}
    cache[text] = res
    time.sleep(0.3)
    return res


def main():
    ap = argparse.ArgumentParser(description="Verify that cited papers exist and match the cited author and year.")
    ap.add_argument("run", help="run name under eval/runs, e.g. final-int")
    ap.add_argument("--arms", nargs="*", default=["bare", "skill"])
    args = ap.parse_args()
    run = ROOT / "eval" / "runs" / args.run
    cache, out = {}, {}
    for arm in args.arms:
        out[arm] = {}
        for rp in sorted((run / arm).glob("*/report.json")):
            rep = json.loads(rp.read_text(encoding="utf-8"))
            cites = [c if isinstance(c, str) else json.dumps(c) for c in rep.get("citations", [])]
            out[arm][rp.parent.name] = [check(c, cache) for c in cites]
    (run / "citation_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    cols = ["verified", "mismatch", "not_found", "unresolved", "internal_note"]
    print("arm".ljust(8), "reports", "cites/report", *[c.ljust(10) for c in cols], "hallucination rate", "self-flagged")
    for arm, cases in out.items():
        rows = [r for rs in cases.values() for r in rs]
        n = len(rows)
        cnt = {c: sum(r["status"] == c for r in rows) for c in cols}
        bad = cnt["mismatch"] + cnt["not_found"]
        n -= cnt["internal_note"]  # notes are not papers
        flagged = sum(r["self_flagged_unchecked"] for r in rows)
        print(arm.ljust(8), str(len(cases)).ljust(7), f"{n / max(len(cases), 1):<12.1f}",
              *[str(cnt[c]).ljust(10) for c in cols], f"{bad}/{n} = {bad / n:.2f}" if n else "n/a", "      ", flagged)
    print("\nmismatch and not_found entries:")
    for arm, cases in out.items():
        for case, rs in cases.items():
            for r in rs:
                if r["status"] in ("mismatch", "not_found"):
                    print(f"  [{arm}] {case}: {r['status']}: {r['text'][:140]}")


if __name__ == "__main__":
    main()
