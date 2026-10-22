"""The iopic-Bond MCP server: the tools an MCP client (Claude Desktop, Claude Code) sees.

Thin layer over ``bond``, ``library`` and ``store``: each tool validates its input, calls the core,
and shapes a compact result for a model to read. Results carry an explicit ``status`` so a missing
paper is data, not an error.

Input: tool calls from the MCP client over stdio (or Streamable HTTP).
Process: Bond calls are async network calls; ingest (download + Docling parse) is blocking and runs
in a worker thread so the server keeps answering while a paper parses.
Output: JSON results; ``view_figure`` also returns the figure as image content for the model to see.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Literal, Optional

import anyio.to_thread
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.utilities.types import Image

from . import __version__, bond, library
from .arxiv import bare_id, looks_like_arxiv_id
from .store import Store
from .tracing import traced

INSTRUCTIONS = """\
iopic-Bond finds papers through Valency Bond, downloads their arXiv PDFs, parses them into a graph
of sections, paragraphs and figures, and keeps every parse in a local library.

Typical flow: find_papers (concept query) -> ingest_paper (arXiv id) -> list_figures -> view_figure
to look at a figure yourself. search_library searches captions of everything already parsed,
without any network call; try it before find_papers when the topic may already be in the library.

Query by concept (material + property, e.g. "Raman mode assignment and polarization in CrSBr"),
never by peak positions or numbers: the search is embedding based and does not encode numbers.
Only arXiv papers can be parsed; for others, cite the paper without figures and say so.
When you describe a figure to the user, cite it as "Fig. N of arXiv:<id>"."""

mcp = MCPServer("iopic-bond", version=__version__, instructions=INSTRUCTIONS)

_store: Optional[Store] = None


def store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def _brief(p: dict, in_library: set[str]) -> dict:
    """A Bond paper record cut to what a model needs to choose and cite."""
    authors = p.get("authors") or []
    first = (p.get("dates") or {}).get("first_available") or {}
    abstract = p.get("abstract") or ""
    return {
        "id": p.get("base_id") or p.get("id"),
        "source": p.get("source"),
        "title": p.get("title"),
        "authors": authors[:3] + (["et al."] if len(authors) > 3 else []),
        "year": (first.get("value") or p.get("first_submitted") or "")[:4] or None,
        "doi": p.get("doi") or None,
        "citation_count": p.get("citation_count"),
        "url": p.get("url"),
        "parseable": p.get("source") == "arxiv",
        "in_library": (p.get("base_id") or p.get("id")) in in_library,
        "abstract": abstract[:400] + ("..." if len(abstract) > 400 else ""),
    }


@mcp.tool()
@traced("iopic.find_papers")
async def find_papers(query: str, limit: int = 10, start_date: Optional[str] = None) -> dict:
    """Find papers on a concept through Valency Bond (embedding search over arXiv, PubMed and more).

    Ask by material and property ("graphene defect density from the D to G intensity ratio"), never
    by numbers. Duplicates (arXiv and journal record of one paper) are merged, keeping the arXiv
    record. `parseable` says whether figures can be extracted; `in_library` says it is already parsed.
    start_date: optional YYYY or YYYY-MM-DD lower bound.
    """
    args = {"query": query, "limit": min(max(limit, 1), 50)}
    if start_date:
        args["start_date"] = start_date
    try:
        res = await bond.call("semantic_search_papers", args)
    except bond.BondError as exc:
        return {"status": "bond_error", "detail": str(exc)}
    papers = bond.merge_papers(res.get("papers") or [])
    known = store().known_ids(papers)
    return {
        "status": "ok",
        "confidence": res.get("confidence"),
        "papers": [_brief(p, known) for p in papers],
    }


@mcp.tool()
@traced("iopic.expand")
async def expand(paper_id: str, mode: Literal["citing", "similar"] = "citing", limit: int = 10) -> dict:
    """Grow a reading list from one anchor paper: papers that cite it, or papers similar to it.

    paper_id: an arXiv id from find_papers. Bond has forward citations only; for a paper's own
    reference list, ingest it and read the parse.
    """
    tool = "get_citing_papers" if mode == "citing" else "find_similar_papers"
    try:
        res = await bond.call(tool, {"paper_id": paper_id, "limit": min(max(limit, 1), 50)})
    except bond.BondError as exc:
        return {"status": "bond_error", "detail": str(exc)}
    # the two Bond tools name their result list differently; take the first list of records
    items = next((v for v in res.values() if isinstance(v, list) and v and isinstance(v[0], dict)), [])
    if mode == "similar":
        items = bond.merge_papers(items)
        known = store().known_ids(items)
        items = [_brief(p, known) for p in items]
    return {"status": "ok", "mode": mode, "anchor": paper_id, "papers": items}


@mcp.tool()
@traced("iopic.ingest_paper")
async def ingest_paper(arxiv_id: str, force: bool = False) -> dict:
    """Download an arXiv paper and parse it into a graph of sections, paragraphs and figures.

    Returns at once if the paper is already in the library. A first parse runs the layout model on
    the pages that contain figures, not on the whole PDF, and skips table-structure recognition.
    Returns the section outline and the figure list (label, caption).
    """
    if not looks_like_arxiv_id(arxiv_id):
        return {"status": "bad_request", "detail": f"{arxiv_id!r} is not an arXiv id (e.g. 1005.2509)"}
    base_id = bare_id(arxiv_id)
    meta: dict = {}
    if store().lookup(base_id=base_id) is None:
        try:  # the Bond record gives title, DOI and licence for meta.json; parsing works without it
            res = await bond.call("get_paper_by_id", {"paper_id": base_id, "include_abstract": False})
            if res.get("found"):
                meta = library.meta_from_bond(res["paper"])
        except bond.BondError:
            pass
    result = await anyio.to_thread.run_sync(lambda: library.ingest(store(), base_id, meta=meta, force=force))
    if result["status"] not in ("ok", "cached"):
        return result
    figs = library.figure_dicts(Path(result["tree_path"]))
    return {
        "status": result["status"],
        "paper": _paper_brief(result["paper"]),
        "outline": library.outline(Path(result["tree_path"])),
        "figures": [{"label": _name(f), "caption": _clip(f["caption"], 200)} for f in figs],
    }


@mcp.tool()
@traced("iopic.list_figures")
def list_figures(arxiv_id: str) -> dict:
    """List a parsed paper's figures: label, caption, page, and the paragraphs that discuss each.

    The paper must have been ingested (ingest_paper). Use view_figure to look at one.
    """
    row, tree = _parsed(arxiv_id)
    if tree is None:
        return {"status": "not_ingested", "detail": f"call ingest_paper('{arxiv_id}') first"}
    figs = library.figure_dicts(tree)
    return {
        "status": "ok",
        "paper": _paper_brief(row),
        "figures": [{
            "label": _name(f),
            "page": f["page"],
            "caption": f["caption"],
            "mentions": [_clip(m, 300) for m in f["mentions"][:3]],
            "image_path": f["image_path"],
        } for f in figs],
    }


# structured_output=False: the result mixes a JSON block and an image, which has no single schema
@mcp.tool(structured_output=False)
@traced("iopic.view_figure")
def view_figure(arxiv_id: str, figure: str, max_px: int = 1200) -> list:
    """Look at one figure of a parsed paper: returns the image itself plus its caption.

    figure: the printed number ("2", "Fig. 2", "Figure 2"). Use this when you need to read a plot
    (peak positions, axes, labels) or compare it with other data. max_px caps the longer side.
    """
    row, tree = _parsed(arxiv_id)
    if tree is None:
        return [{"status": "not_ingested", "detail": f"call ingest_paper('{arxiv_id}') first"}]
    figs = library.figure_dicts(tree)
    f = library.find_figure(figs, figure)
    if f is None:
        return [{"status": "not_found", "available": [_name(x) for x in figs]}]
    if not f["image_path"]:
        return [{"status": "image_missing", "label": _name(f), "caption": f["caption"]}]
    info = {
        "status": "ok",
        "cite_as": f"{f['label'] or 'uncaptioned ' + f['image_ref'] + ', p. ' + str(f['page'])} of arXiv:{row['base_id']}",
        "paper": _paper_brief(row),
        "label": _name(f),
        "page": f["page"],
        "caption": f["caption"],
        "image_path": f["image_path"],
    }
    return [info, Image(data=_png_bytes(f["image_path"], max_px), format="png")]


@mcp.tool()
@traced("iopic.search_library")
def search_library(query: str, limit: int = 10) -> dict:
    """Search figure captions, the paragraphs that discuss them, and titles of every parsed paper.

    Local and instant (no network). Words must all match; if none match together, any word may.
    """
    hits = store().search(query, limit=min(max(limit, 1), 50))
    return {"status": "ok" if hits else "no_match", "hits": [{
        "arxiv_id": h["base_id"],
        "label": h["label"],
        "title": h["title"],
        "caption": _clip(h["caption"], 300),
        "mention": h["mention_snippet"],
    } for h in hits]}


@mcp.tool()
def library_status() -> dict:
    """What is in the local library: parsed papers with figure counts, and where it is stored."""
    s = store()
    return {"status": "ok", "root": str(s.root), "papers": s.list_papers()}


# -- helpers -----------------------------------------------------------------------------------


def _parsed(arxiv_id: str):
    row = store().lookup(base_id=bare_id(arxiv_id))
    if not row or row["status"] != "parsed":
        return row, None
    return row, store().tree_path(row)


def _paper_brief(row: dict) -> dict:
    return {k: row.get(k) for k in ("base_id", "title", "doi", "year", "license", "url", "n_figures")}


def _clip(s: Optional[str], n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def _png_bytes(path: str, max_px: int) -> bytes:
    """Downscale so the longer side is at most ``max_px``; models see large images downscaled anyway."""
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


def _name(f: dict) -> str:
    """The printed label ("Fig 2"), or "image N (no caption)" for an uncaptioned image."""
    return f["label"] or f"{f['image_ref']} (no caption)"
