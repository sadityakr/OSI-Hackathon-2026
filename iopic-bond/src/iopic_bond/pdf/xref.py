"""Internal cross-reference resolver (ADR-0002, M4) — ``references-*`` edges *within* one document.

Meaning in a paper is non-local: "as shown in Fig. 4" is a ``block -> block`` edge that an agent must
be able to walk from a claim to the figure/table/section/equation it depends on. This module scans
body text for in-text mentions, matches each to the *labelled* node carrying that number, and adds a
``references-{figure,table,section,equation}`` edge on the text leaf, **anchored on the marker's
char-span** (in ``text.txt`` coordinates, consistent with provenance). Docling supplies the typed
blocks + labels; the linking logic is ours.

Design stance — **precision over recall** (abstain over fabricate, applied to edges): a marker only
produces an edge if its number resolves to a real node, so a stray "Eq. 5" with no equation 5 yields
*nothing* rather than a wrong edge. Compound/ambiguous markers ("Figs. 4-6", "the figure above") and
unnumbered sections are named open problems (parsing-layer §5), deliberately not forced here.
"""

from __future__ import annotations

import re

from .schema import BlockNode, Edge

_NUM = r"\d+(?:\.\d+)*"  # "4", "2.5", "3.3.1" — chapter-prefixed numbers included

# in-text marker -> (edge type, index kind). The number is group(1); a trailing subpart letter
# ("4a") is intentionally left out of the captured number so "Fig. 4a" resolves to figure 4.
_SCANNERS = [
    ("references-figure", "figure", re.compile(rf"\bFig(?:ure)?s?\.?\s*({_NUM})", re.IGNORECASE)),
    ("references-table", "table", re.compile(rf"\bTab(?:le)?s?\.?\s*({_NUM})", re.IGNORECASE)),
    (
        "references-section",
        "section",
        re.compile(rf"\b(?:Sec(?:tion)?s?\.?|§)\s*({_NUM})", re.IGNORECASE),
    ),
    (
        "references-equation",
        "equation",
        re.compile(rf"\b(?:Eq(?:uation)?s?\.?|Eqn\.?)\s*\(?({_NUM})\)?", re.IGNORECASE),
    ),
]

_NUM_RE = re.compile(rf"({_NUM})")
_HEADING_NUM_RE = re.compile(rf"^\s*({_NUM})\s+\S")  # "3.3.1 Scanning Electron Microscopy"
_EQ_TAIL_RE = re.compile(rf"\(({_NUM})\)\s*$")  # equation body ending in its number "(2.3)"

# only real prose carries cross-references; captions are *labels* (not refs), so they are not scanned
_SCAN_LEAF_TYPES = ("paragraph", "list-item", "footnote")


def _num_from_label(label: str | None) -> str | None:
    if not label:
        return None
    m = _NUM_RE.search(label)
    return m.group(1) if m else None


def _num_from_heading(text: str | None) -> str | None:
    if not text:
        return None
    m = _HEADING_NUM_RE.match(text)
    return m.group(1) if m else None


def _equation_numbers(node: BlockNode) -> list[str]:
    """Resolved equation numbers carried on the node, newest source first.

    Prefers the geometry-recovered ``attrs['numbers']`` / ``attrs['number']`` (issue 0001 —
    authoritative, from the PDF text layer), and falls back to a trailing ``(N)`` parsed out of the
    VLM latex for trees built before that pass ran.
    """
    nums = node.attrs.get("numbers")
    if nums:
        return [str(x) for x in nums]
    num = node.attrs.get("number")
    if num:
        return [str(num)]
    txt = (node.attrs.get("latex") or node.text or "").strip()
    m = _EQ_TAIL_RE.search(txt)
    return [m.group(1)] if m else []


def _build_index(root: BlockNode) -> dict[str, dict[str, str]]:
    """Map a reference number -> node id, per kind. A number claimed by >1 node is **ambiguous and
    dropped** (abstain), not first-wins: a thesis with per-chapter numbering has a "Figure 1" in every
    chapter, so first-wins would resolve every "Fig. 1" to chapter 1's figure — a *wrong* edge. Better
    no edge than a confidently wrong one (precision over recall, consistent with the resolver)."""
    # collect all node ids claiming each (kind, number); collapse to a single id only when unique
    claims: dict[str, dict[str, set[str]]] = {
        "figure": {},
        "table": {},
        "section": {},
        "equation": {},
    }

    def _claim(kind: str, num: str | None, node_id: str) -> None:
        if num:
            claims[kind].setdefault(num, set()).add(node_id)

    for n in root.walk():
        if n.type == "figure":
            _claim("figure", _num_from_label(n.attrs.get("label")), n.id)
        elif n.type == "table":
            _claim("table", _num_from_label(n.attrs.get("label")), n.id)
        elif n.type in ("chapter", "section", "subsection"):
            _claim("section", _num_from_heading(n.text), n.id)
        elif n.type == "equation":
            for num in _equation_numbers(n):  # a node may carry several merged display numbers
                _claim("equation", num, n.id)
    return {
        kind: {num: next(iter(ids)) for num, ids in by_num.items() if len(ids) == 1}
        for kind, by_num in claims.items()
    }


def resolve_internal_refs(root: BlockNode) -> int:
    """Add ``references-*`` edges across one tree in place. Returns the number of edges added."""
    idx = _build_index(root)
    added = 0
    for n in root.walk():
        if n.type not in _SCAN_LEAF_TYPES or not n.text:
            continue
        base = n.prov[0].char_span[0] if n.prov else 0
        for edge_type, kind, rx in _SCANNERS:
            table = idx[kind]
            if not table:
                continue
            for m in rx.finditer(n.text):
                target = table.get(m.group(1))
                if not target or target == n.id:
                    continue  # unresolved number or self-reference -> no edge (precision)
                marker = (base + m.start(), base + m.end())
                if any(
                    e.type == edge_type and e.target == target and e.marker_span == marker
                    for e in n.edges
                ):
                    continue  # already linked this exact marker
                n.edges.append(Edge(type=edge_type, target=target, marker_span=marker))
                added += 1
    return added
