"""tree.json -> graph (nodes + links) — the pure projection at the heart of the visualizer.

The graph model (what each visual element *means*):

* **Nodes** are the paper's typed blocks — the document, its sections, the text units, and the
  citable entities (figures, tables, equations, references). ``caption`` nodes are *folded into
  their figure* (their text becomes the figure's label/tooltip), exactly as the chunker does, so the
  same unit is never drawn twice.
* **Containment links** (``contains``) are synthesized from the tree backbone — document → section
  → paragraph — and form the skeleton.
* **Cross-links** are the parser's *resolved* edges carried verbatim: ``cites`` (text → reference),
  ``references-figure`` / ``-table`` / ``-equation`` / ``-section`` (text → entity), which turn a
  bare hierarchy into the recognisable hub-and-spoke shape of a real paper.

**The 800-token rule.** A node's text is the unit a downstream embedder would see, so the graph caps
text-bearing leaves at ``max_tokens`` (default 800): a leaf over the cap is split into sequential
sub-chunks (``…#c0``, ``#c1``) linked ``contains`` from the same parent and ``next`` to each other.
The split is rare (most paragraphs are well under 800), so a split leaf's cross-edges are attached to
its first chunk — fidelity there is not load-bearing for a visualization.

Pure and offline: it takes a parsed ``tree.json`` dict and returns a dict. No DB, no model, no
filesystem — the CLI does the I/O.
"""

from __future__ import annotations

from typing import Any

# --- node taxonomy: type -> (display group, base size) ------------------------------------------
# `group` drives colour + the legend; `base` seeds node area (degree is added on top in JS).
_GROUP = {
    "document": "document",
    "chapter": "section",
    "section": "section",
    "subsection": "section",
    "abstract": "text",
    "paragraph": "text",
    "list-item": "text",
    "list": "text",
    "footnote": "text",
    "author": "meta",
    "affiliation": "meta",
    "funding": "meta",
    "acknowledgement": "meta",
    "figure": "figure",
    "table": "table",
    "equation": "equation",
    "reference": "reference",
    "dataset": "reference",
}
_BASE_SIZE = {
    "document": 14.0,
    "section": 5.0,
    "text": 2.0,
    "figure": 4.0,
    "table": 4.0,
    "equation": 3.0,
    "reference": 2.0,
    "meta": 2.0,
}

# Leaves whose text we cap at `max_tokens` (containers + entities are never split).
_TEXT_LEAVES = frozenset({"paragraph", "list-item", "footnote", "abstract"})
# `caption` nodes are folded into their figure and never drawn standalone.
_FOLDED = frozenset({"caption"})

# Headings that mark a bibliography block (normalized: lowercased, alpha-only).
_BIB_HEADINGS = frozenset(
    {"references", "reference", "bibliography", "referencesandnotes", "notesandreferences"}
)


def _norm_heading(text: str | None) -> str:
    return "".join(c for c in (text or "").lower() if c.isalpha())


def _bibliography_dupes(tree: dict[str, Any]) -> set[str]:
    """Ids of *raw* bibliography sections that duplicate the resolved ``reference`` entities.

    A paper's bibliography can land in the tree twice: once as the GROBID-resolved ``reference``
    entities (DOIs, the ``cites`` targets) and once as the raw text Docling rendered under a
    "References" heading (plain ``list-item``/``paragraph`` leaves). The second is a duplicate that
    clutters the graph with a dead star of unlinked nodes. We drop it — but only when resolved
    entities exist to supersede it, and only the *raw* block (a references-headed section with **no**
    ``reference`` descendants), never the resolved container itself.
    """

    def _has_ref_descendant(n: dict[str, Any]) -> bool:
        return any(d["type"] == "reference" for d in _walk(n))

    has_resolved = any(d["type"] == "reference" for d in _walk(tree))
    if not has_resolved:
        return set()  # the raw block is the only bibliography we have — keep it
    dupes: set[str] = set()
    for n in _walk(tree):
        if (
            n["type"] in ("section", "subsection", "chapter")
            and _norm_heading(n.get("text")) in _BIB_HEADINGS
            and not _has_ref_descendant(n)
        ):
            dupes.add(n["id"])
    return dupes


def _walk(n: dict[str, Any]):
    yield n
    for c in n.get("children") or []:
        yield from _walk(c)


def _est_tokens(text: str) -> int:
    """Cheap whitespace-based token estimate (~1.3 tokens/word) — no tokenizer dependency."""
    return max(1, round(len(text.split()) * 1.3))


def _split_text(text: str, max_tokens: int) -> list[str]:
    """Split on word boundaries into windows of <= max_tokens (estimated). Returns >=1 segment."""
    words = text.split()
    if not words:
        return [text]
    per = max(1, int(max_tokens / 1.3))  # words per window
    return [" ".join(words[i : i + per]) for i in range(0, len(words), per)] or [text]


def _short(text: str | None, n: int = 6) -> str:
    if not text:
        return ""
    words = text.split()
    out = " ".join(words[:n])
    return out + ("…" if len(words) > n else "")


def _ref_index(node_id: str) -> str:
    """`…/ref12` -> `[12]` for a compact, paper-native reference label."""
    tail = node_id.rsplit("/", 1)[-1]
    digits = "".join(c for c in tail if c.isdigit())
    return f"[{digits}]" if digits else tail


def _surname(author: str) -> str:
    """`"V Baltz"` -> `"Baltz"` — last whitespace token, stripped of punctuation."""
    toks = (author or "").replace(".", " ").split()
    return toks[-1].strip(",;") if toks else ""


def _year(date: str | None) -> str:
    """Pull a 4-digit year out of an ISO `published_date` (`"2018-02-15"` -> `"2018"`)."""
    if date and len(date) >= 4 and date[:4].isdigit():
        return date[:4]
    return ""


def _ref_identity(node: dict[str, Any]) -> dict[str, Any]:
    """The *resolved* identity of a reference entity (GROBID + CrossRef), for label + inspector.

    The whole point: a reference node is not a bare ``[12]`` — it is a located, DOI-resolved Work.
    This surfaces that so a citation marker reads as the paper it points to.
    """
    a = node.get("attrs") or {}
    authors = a.get("authors") or []
    year = _year(a.get("published_date"))
    return {
        "n": _ref_index(node["id"]).strip("[]"),
        "title": (a.get("title") or "").strip(),
        "authors": authors,
        "surname": _surname(authors[0]) if authors else "",
        "journal": (a.get("journal") or "").strip(),
        "year": year,
        "doi": (a.get("doi") or "").strip(),
        "is_preprint": bool(a.get("is_preprint")),
        "raw": (a.get("raw") or node.get("text") or "").strip(),
    }


def _label(node: dict[str, Any]) -> str:
    """The short text drawn next to a node — chosen per type to read like the paper."""
    t = node["type"]
    attrs = node.get("attrs") or {}
    text = node.get("text") or ""
    if t == "document":
        return _short(attrs.get("title") or text, 9) or "(paper)"
    if t in ("section", "subsection", "chapter"):
        return _short(text, 7) or t
    if t == "figure":
        return (attrs.get("label") or "Figure").strip()
    if t == "table":
        return (attrs.get("label") or "Table").strip()
    if t == "equation":
        lbl = (attrs.get("label") or "").strip()
        return f"Eq {lbl}" if lbl else "Eq"
    if t == "reference":
        ident = _ref_identity(node)
        # author-year reads as the cited work; fall back to the bracket index when unresolved
        if ident["surname"] and ident["year"]:
            return f"{ident['surname']} {ident['year']}"
        if ident["surname"]:
            return ident["surname"]
        return _ref_index(node["id"])
    if t == "abstract":
        return "Abstract"
    return _short(text, 6) or t


def _caption_text(fig_id: str, captions: dict[str, str]) -> str:
    return captions.get(fig_id, "")


def build_graph(tree: dict[str, Any], max_tokens: int = 800) -> dict[str, Any]:
    """Project a parsed ``tree.json`` dict into ``{"nodes": [...], "links": [...], "meta": {...}}``.

    Nodes carry ``id, type, group, label, text, page, heading, val``; links carry
    ``source, target, rel``. Degree-based sizing and final styling happen in the renderer/JS.
    """
    # Pass 0 — find raw bibliography sections that duplicate the resolved reference entities.
    pruned = _bibliography_dupes(tree)

    # Pass 1 — collect caption text keyed by the figure/table it captions (to fold captions in).
    captions: dict[str, str] = {}

    def _scan_captions(n: dict[str, Any]) -> None:
        if n["type"] == "caption":
            for e in n.get("edges") or []:
                if e["type"] == "caption-of":
                    captions[e["target"]] = n.get("text") or ""
        for c in n.get("children") or []:
            _scan_captions(c)

    _scan_captions(tree)

    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    present: set[str] = set()  # node ids actually emitted (for precision-first link filtering)
    # Edges whose source leaf got split: remap source id -> the first chunk's id.
    remap: dict[str, str] = {}

    def _heading_trail(trail: list[str]) -> str:
        return " › ".join([s for s in trail if s])

    def _add_node(
        nid: str,
        ntype: str,
        label: str,
        text: str,
        page: Any,
        heading: str,
        ref: dict[str, Any] | None = None,
        image: str | None = None,
    ) -> None:
        group = _GROUP.get(ntype, "text")
        node = {
            "id": nid,
            "type": ntype,
            "group": group,
            "label": label,
            "text": text,
            "page": page,
            "heading": heading,
            "val": _BASE_SIZE.get(group, 2.0),
        }
        if ref is not None:
            node["ref"] = ref  # resolved bibliographic identity (reference entities only)
        if image is not None:
            node["image"] = image  # relative image path; CLI inlines it as a data URI
        nodes.append(node)
        present.add(nid)

    def _page(n: dict[str, Any]) -> Any:
        prov = n.get("prov") or []
        return prov[0]["page_no"] if prov else None

    def walk(n: dict[str, Any], parent_id: str | None, trail: list[str]) -> None:
        t = n["type"]
        if n["id"] in pruned:
            return  # raw bibliography block — superseded by the resolved reference entities
        if t in _FOLDED:
            return  # captions fold into their figure; not standalone nodes
        nid = n["id"]
        heading = _heading_trail(trail)
        page = _page(n)

        # Figures/tables absorb their caption text for tooltip + searchability.
        text = n.get("text") or ""
        image_rel: str | None = None
        if t in ("figure", "table"):
            cap = _caption_text(nid, captions)
            attrs = n.get("attrs") or {}
            text = " — ".join(p for p in [(attrs.get("label") or "").strip(), cap] if p) or text
            # carry the *relative* image path (the CLI resolves + inlines it — this stays pure).
            image_rel = (attrs.get("image_path") or "").strip() or None

        # 800-token cap: split text leaves, keep everything else whole.
        chunk_ids: list[str] = [nid]
        if t in _TEXT_LEAVES and _est_tokens(text) > max_tokens:
            segs = _split_text(text, max_tokens)
            chunk_ids = [f"{nid}#c{i}" for i in range(len(segs))]
            remap[nid] = chunk_ids[0]
            for i, (cid, seg) in enumerate(zip(chunk_ids, segs)):
                _add_node(cid, t, f"{_label(n)} ·{i}", seg, page, heading)
                if parent_id:
                    links.append({"source": parent_id, "target": cid, "rel": "contains"})
                if i > 0:
                    links.append({"source": chunk_ids[i - 1], "target": cid, "rel": "next"})
        else:
            ref = _ref_identity(n) if t == "reference" else None
            # a resolved reference inspects on its full bibliographic record, not the truncated text
            body = ref["raw"] if ref else text
            _add_node(nid, t, _label(n), body, page, heading, ref=ref, image=image_rel)
            if parent_id:
                links.append({"source": parent_id, "target": nid, "rel": "contains"})

        # Recurse — children's parent is this node (or its first chunk if it was split).
        own_id = chunk_ids[0]
        child_trail = trail + [_label(n)] if t in ("section", "subsection", "chapter") else trail
        for c in n.get("children") or []:
            walk(c, own_id, child_trail)

    walk(tree, None, [])

    # Pass 2 — carry the parser's resolved cross-edges (skip the structural/folded ones).
    _CROSS = {
        "cites": "cites",
        "references-figure": "ref-figure",
        "references-table": "ref-table",
        "references-equation": "ref-equation",
        "references-section": "ref-section",
    }
    seen_link: set[tuple[str, str, str]] = set()

    def _scan_edges(n: dict[str, Any]) -> None:
        src = remap.get(n["id"], n["id"])
        for e in n.get("edges") or []:
            rel = _CROSS.get(e["type"])
            if rel is None:
                continue
            tgt = remap.get(e["target"], e["target"])
            if src not in present or tgt not in present:
                continue  # precision-first: drop links to nodes we didn't draw
            key = (src, tgt, rel)
            if key in seen_link:
                continue  # collapse duplicate markers (e.g. two "Fig. 1" mentions in one para)
            seen_link.add(key)
            links.append({"source": src, "target": tgt, "rel": rel})
        for c in n.get("children") or []:
            _scan_edges(c)

    _scan_edges(tree)

    # Degree -> node size (Obsidian: hubs grow). Area scales with sqrt(degree).
    deg: dict[str, int] = {}
    for ln in links:
        deg[ln["source"]] = deg.get(ln["source"], 0) + 1
        deg[ln["target"]] = deg.get(ln["target"], 0) + 1
    for nd in nodes:
        nd["val"] = round(nd["val"] + (deg.get(nd["id"], 0) ** 0.5), 2)
        nd["deg"] = deg.get(nd["id"], 0)

    attrs = tree.get("attrs") or {}
    meta = {
        "title": attrs.get("title") or "(untitled)",
        "authors": attrs.get("authors") or [],
        "doi": attrs.get("doi"),
        "citable_key": attrs.get("citable_key"),
        "n_nodes": len(nodes),
        "n_links": len(links),
        "max_tokens": max_tokens,
    }
    return {"nodes": nodes, "links": links, "meta": meta}
