"""Citation normalization (ADR-0003, M-parse) — standardize every citation to ``[N]`` in the parse.

Citation styles differ per journal — superscript ``³⁴``, bracket ``[34]``, author–year ``(Smith
2019)``. Downstream (retrieval, the cites resolver, display) should never have to care: this stage
rewrites the dominant **superscript** style into the canonical ``[N]`` form *in the canonical tree*,
so a paper that used superscripts and one that used brackets are byte-identical after parsing. The
citation problem is solved once, here, rather than re-solved by every consumer.

Why this is non-trivial: Docling keeps the citation digits as **ambiguous bare inline tokens**
(``…topology 1-4 . They…``) — indistinguishable at the text layer from ``Figure 1`` or ``100 nm``.
What disambiguates them is PDF **glyph geometry** (a raised baseline — see :mod:`superscript_cites`).
So we detect citation runs geometrically, then rewrite the matching bare token to ``[1-4]`` in the
host leaf's text, anchored by *preceding-word + number* so we never touch a non-citation number.

The keystone is :func:`rebuild_text_stream`: ``text.txt`` is a pure projection of the tree (each node
emits ``text + "\\n"`` in reading order, and its ``char_span`` is ``(cursor, cursor+len)``), so after
mutating leaf text we **re-derive every char-span by replaying that emission** — the coordinate
substrate stays exactly consistent with the (now normalized) text.

Pure tree surgery, except glyph extraction (pypdfium2, via :mod:`superscript_cites`).
"""

from __future__ import annotations

import re
from dataclasses import replace

from .schema import BlockNode
from .superscript_cites import extract_glyphs, markers_from_page

_CITE_HOST_TYPES = ("paragraph", "list-item", "footnote")

# Superscript numbers in the AUTHOR/AFFILIATION block are affiliation markers ("Beneke¹" = affiliation
# 1), NOT citations — so leaves under a front-matter heading are excluded from normalization. (Without
# this guard, the author list gets rewritten to "Beneke [1]", a false citation.)
_FRONT_MATTER_RE = re.compile(
    r"(?i)^\s*(authors?|affiliations?|author information|addresses?|present address"
    r"|corresponding author|author contributions)\b"
)


def _front_matter_leaf_ids(root: BlockNode) -> set[str]:
    """Ids of cite-host leaves whose nearest enclosing section heading is front matter (skip these)."""
    skip: set[str] = set()

    def _walk(node: BlockNode, in_front: bool) -> None:
        here = in_front
        if node.type in ("section", "chapter", "subsection") and node.text:
            here = bool(_FRONT_MATTER_RE.match(node.text))
        if here and node.type in _CITE_HOST_TYPES:
            skip.add(node.id)
        for child in node.children:
            _walk(child, here)

    _walk(root, False)
    return skip


def replay_text_stream(root: BlockNode) -> tuple[str, dict[str, tuple[int, int]]]:
    """Replay the adapter's emission WITHOUT mutating the tree: ``(text.txt, {node_id: char_span})``.

    The projection law, in one place: pre-order DFS (skipping the document root), each node with text
    contributes ``text + "\\n"`` and owns ``char_span = (start, start+len(text))``; a text-less node
    (a figure) gets a zero-length span at the cursor. :func:`rebuild_text_stream` applies this to the
    tree; QA replays it read-only to verify a vault's ``text.txt``/spans never silently desynced.
    """
    parts: list[str] = []
    spans: dict[str, tuple[int, int]] = {}
    cursor = 0
    for node in root.walk():
        if node is root:
            continue
        txt = node.text
        if txt:
            start = cursor
            parts.append(txt + "\n")
            cursor += len(txt) + 1
            spans[node.id] = (start, cursor - 1)
        else:
            spans[node.id] = (cursor, cursor)
    return "".join(parts), spans


def rebuild_text_stream(root: BlockNode) -> str:
    """Re-derive ``text.txt`` and every node's ``char_span`` from the tree's current leaf text.

    Applies :func:`replay_text_stream` to the tree: mutate a leaf's ``text`` then call this and all
    offsets stay consistent — the basis for in-place citation normalization, and the invariant every
    text-mutating pass must restore before the tree is written to disk.
    """
    text, spans = replay_text_stream(root)
    for node in root.walk():
        if node is not root and node.prov:
            node.prov = [replace(p, char_span=spans[node.id]) for p in node.prov]
    return text


def _number_pattern(run: str) -> str:
    """A tolerant regex for a citation run as it may appear in the text (loose spaces / dash variants)."""
    out = []
    for ch in run:
        if ch.isdigit():
            out.append(ch)
        elif ch == ",":
            out.append(r"\s*,\s*")
        else:  # any dash
            out.append(r"\s*[-–—]\s*")
    return "".join(out)


def _canonical(run: str) -> str:
    """Canonical bracketed marker: dashes normalized to '-', spaces stripped → ``[9-13,21,34-36]``."""
    return "[" + re.sub(r"\s*[-–—]\s*", "-", run).replace(" ", "") + "]"


def normalize_superscript_citations(root: BlockNode, pdf_path) -> tuple[str, int]:
    """Rewrite superscript citation runs to canonical ``[N]`` in-place; return (new text.txt, count).

    Detection is geometric (:mod:`superscript_cites`); the rewrite is anchored by *preceding word +
    number run* so only the citation token is replaced, never a same-valued non-citation number. After
    all rewrites, :func:`rebuild_text_stream` re-derives ``text.txt`` + char-spans.
    """
    glyphs_by_page, heights = extract_glyphs(pdf_path)
    front_matter = _front_matter_leaf_ids(root)
    rewrites = 0
    for page_no, glyphs in glyphs_by_page.items():
        markers = markers_from_page(glyphs, page_no, heights[page_no], with_word=True)
        for m in markers:
            leaf = _host_leaf(root, m.page_no, m.bbox)
            if leaf is None or not leaf.text or not m.word or leaf.id in front_matter:
                continue  # skip author/affiliation superscripts (not citations)
            pattern = re.escape(m.word) + r"(\s*)" + _number_pattern(m.run)
            replacement = m.word + r"\1" + _canonical(m.run)
            new_text, n = re.subn(pattern, replacement, leaf.text, count=1)
            if n:
                leaf.text = new_text
                rewrites += 1
    text_txt = rebuild_text_stream(root)
    return text_txt, rewrites


def _host_leaf(root: BlockNode, page_no: int, bbox, pad: float = 2.0):
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    for n in root.walk():
        if n.type not in _CITE_HOST_TYPES:
            continue
        for p in n.prov:
            if p.page_no != page_no:
                continue
            left, top, right, bottom = p.bbox
            if left - pad <= cx <= right + pad and top - pad <= cy <= bottom + pad:
                return n
    return None
