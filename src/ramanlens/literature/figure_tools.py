"""Paper search and figure viewing for the agent, as thin wrappers over the iopic-Bond package.

The agent should compare a measured spectrum with the published one, not only with numbers in a table. iopic-Bond
(the separate `iopic-bond/` package) finds papers through Valency Bond, downloads arXiv PDFs, parses them once into
a local library and crops their figures; this module calls that package directly (no MCP round trip) and shapes
the results for the RamanLens toolset. It is optional: `AVAILABLE` is False when iopic_bond is not installed, and
the toolset then leaves these two tools out.

Input: `find_papers(query, limit, start_date)`: a concept query (material plus property, never peak positions);
`view_figure(arxiv_id, figure, max_px)`: an arXiv id and a printed figure number, or no figure to list them.
Process: find_papers calls Bond `semantic_search_papers`, merges arXiv and journal duplicates, and drops the papers
excluded from tool building (below); view_figure parses the paper on first use (download plus Docling, minutes on
a cold parse, cached afterwards), finds the figure by its printed number and downscales the crop to a PNG.
Output: find_papers returns a dict (`status`, `papers` with id, title, year, DOI, `parseable`, `in_library`);
view_figure returns a dict with `status`, `cite_as`, caption, page and the PNG bytes under `png`, which the toolset
turns into an image block the model can see. Every result has `provenance: "literature"`. Missing papers, a
missing Bond token or a failed parse come back as a `status` value, never as an exception.
"""

from __future__ import annotations

import asyncio
import io

from ramanlens.tracing import add_metadata, traced

try:
    from iopic_bond import bond, config, library
    from iopic_bond.arxiv import bare_id, looks_like_arxiv_id
    from iopic_bond.store import Store

    AVAILABLE = True
except ImportError:  # iopic-bond (or one of its dependencies) not installed: the toolset skips these tools
    AVAILABLE = False

# Papers whose numbers are the answers of evaluation cases (listed in the evaluation set's README under "Papers
# excluded from building tools"). The tools arm must not read them, or it would be scored against its own source.
# McDonnell et al. 2018 (Nano Lett.) is matched by DOI because its arXiv id is not recorded.
EXCLUDED_ARXIV = {"2503.15298", "2103.09004", "2006.05912"}
EXCLUDED_DOI = {"10.1021/acs.nanolett.7b05184"}

_store = None


def _get_store():
    """One library handle per process; reads IOPIC_BOND_HOME and the Bond token from the environment or .env."""
    global _store
    if _store is None:
        config.load_env()
        _store = Store()
    return _store


def _excluded(paper_id: str | None, doi: str | None) -> bool:
    pid = bare_id(paper_id) if paper_id and looks_like_arxiv_id(paper_id) else (paper_id or "")
    return pid in EXCLUDED_ARXIV or (doi or "").strip().lower() in EXCLUDED_DOI


def _brief(p: dict, in_library: set) -> dict:
    """A Bond paper record cut to what a model needs to choose and cite."""
    authors = p.get("authors") or []
    first = (p.get("dates") or {}).get("first_available") or {}
    abstract = " ".join((p.get("abstract") or "").split())
    pid = p.get("base_id") or p.get("id")
    return {"id": pid, "source": p.get("source"), "title": p.get("title"),
            "authors": authors[:3] + (["et al."] if len(authors) > 3 else []),
            "year": (first.get("value") or p.get("first_submitted") or "")[:4] or None,
            "doi": p.get("doi") or None, "citation_count": p.get("citation_count"), "url": p.get("url"),
            "parseable": p.get("source") == "arxiv", "in_library": pid in in_library,
            "abstract": abstract[:400] + ("..." if len(abstract) > 400 else "")}


@traced("literature.find_papers")
def find_papers(query: str, limit: int = 10, start_date: str | None = None) -> dict:
    args = {"query": query, "limit": min(max(int(limit), 1), 50)}
    if start_date:
        args["start_date"] = start_date
    store = _get_store()
    try:
        # bond.call is a coroutine (Bond is reached as an MCP client); asyncio.run drives it to completion here
        res = asyncio.run(bond.call("semantic_search_papers", args))
    except bond.BondError as exc:
        return {"status": "bond_error", "detail": str(exc), "provenance": "literature"}
    papers = bond.merge_papers(res.get("papers") or [])
    kept = [p for p in papers if not _excluded(p.get("base_id") or p.get("id"), p.get("doi"))]
    known = store.known_ids(kept)
    out = {"status": "ok", "confidence": res.get("confidence"), "papers": [_brief(p, known) for p in kept],
           "provenance": "literature", "method": "Valency Bond semantic_search_papers through iopic-Bond; arXiv and "
                                                 "journal records of one paper merged on DOI"}
    if len(kept) < len(papers):
        out["note"] = f"{len(papers) - len(kept)} paper(s) withheld: they are the source of evaluation answers"
    return out


def _png_bytes(path: str, max_px: int) -> bytes:
    """Downscale so the longer side is at most `max_px` pixels; models see large images downscaled anyway."""
    from PIL import Image

    # `with` closes the image file when the block ends, even if the conversion fails
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


@traced("figure.view")
def view_figure(arxiv_id: str, figure: str | None = None, max_px: int = 1200) -> dict:
    if not looks_like_arxiv_id(arxiv_id):
        return {"status": "bad_request", "detail": f"{arxiv_id!r} is not an arXiv id (e.g. 1005.2509); only "
                                                   "arXiv papers can be parsed", "provenance": "literature"}
    base_id = bare_id(arxiv_id)
    store = _get_store()
    row = store.lookup(base_id=base_id)
    if _excluded(base_id, (row or {}).get("doi")):
        return {"status": "withheld", "detail": "this paper is the source of evaluation answers and is not "
                                                "available to the tools", "provenance": "literature"}
    result = library.ingest(store, base_id)  # returns the stored parse at once when the paper is in the library
    if result["status"] not in ("ok", "cached"):
        return {**result, "provenance": "literature"}
    row = result["paper"]
    if _excluded(base_id, row.get("doi")):  # the DOI is only known after the first ingest
        return {"status": "withheld", "detail": "this paper is the source of evaluation answers and is not "
                                                "available to the tools", "provenance": "literature"}
    paper = {k: row.get(k) for k in ("base_id", "title", "doi", "year", "license", "url")}
    figs = library.figure_dicts(store.tree_path(row))

    def name(f: dict) -> str:
        return f["label"] or f"{f['image_ref']} (no caption)"

    if not figure:
        return {"status": "ok", "paper": paper, "provenance": "literature",
                "figures": [{"figure": name(f), "page": f["page"], "caption": f["caption"]} for f in figs]}
    f = library.find_figure(figs, str(figure))
    if f is None:
        return {"status": "not_found", "paper": paper, "available": [name(x) for x in figs],
                "provenance": "literature"}
    add_metadata(arxiv_id=base_id, figure=name(f))
    out = {"status": "ok", "cite_as": f"{name(f)} of arXiv:{base_id}", "paper": paper, "figure": name(f),
           "page": f["page"], "caption": f["caption"], "mentions": [" ".join(m.split())[:300] for m in
                                                                    f["mentions"][:3]],
           "provenance": "literature"}
    if not f["image_path"]:
        out["status"] = "image_missing"
        return out
    out["png"] = _png_bytes(f["image_path"], int(max_px))
    return out
