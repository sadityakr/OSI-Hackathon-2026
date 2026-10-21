"""Equation-number recovery (issue 0001) — bind the right-aligned ``(3.4)`` to its equation node.

Docling's formula VLM consumes the equation region into LaTeX and routinely **drops or renumbers**
the right-aligned number: on the eval corpus it emits sequential ``(1)(2)(3)`` even where the real
numbers are ``(3)(6)(9)``, and on multi-column papers it loses them entirely. So the VLM LaTeX can
*not* be trusted for the number — binding from it would fabricate wrong ``Eq. (N)`` edges, the exact
thing issue 0001 forbids.

But the number itself is plain typeset text in the PDF's text layer, which pypdfium reads with
perfect fidelity, independent of the VLM. So we recover it deterministically from **page geometry** —
the same glyph-geometry move as :mod:`superscript_cites` — and bind each ``(N)`` to the equation node
whose bbox shares its line band *and* right margin. Precision-first: a ``(N)`` that aligns to no
equation is dropped (we never fabricate a number), matching the project's abstain-over-guess stance.

The number lands on ``equation.attrs``: ``number`` (a single scalar, the common one-line case) and/or
``numbers`` (a list — Docling merges several numbered display lines into one node). ``xref`` resolves
``references-equation`` edges off these; the parsing eval scores ``equation_number_binding`` against
them. Detection over a glyph list is pure (unit-tested offline); only :func:`recover_equation_numbers`
touches the PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schema import BlockNode
from .superscript_cites import Glyph, extract_glyphs

# Inner content of a "( ... )" that counts as an equation number: 1–3 digits, an optional decimal
# (chapter-prefixed "3.4"), and an optional sub-equation letter ("2a"). Capping the digits rejects
# years/PACS ids and keeps a long inline "(12345)" from being read as a number.
_EQNUM = re.compile(r"\d{1,3}(?:\.\d+)?[a-z]?")
_MAX_INNER = 8  # max glyphs between "(" and ")" — a real number is short; longer is prose/an array


@dataclass(frozen=True)
class NumberRun:
    """A parenthesised number found in the text layer, y-centred in TOP-LEFT origin (Provenance)."""

    number: str
    y_center: float  # TOP-LEFT origin, PDF points — comparable to Provenance bbox y
    left: float
    right: float


def _num_key(s: str) -> tuple[float, str]:
    """Sort key so "2a" follows "2" and "10" follows "9" (numeric prefix, then suffix)."""
    m = re.match(r"(\d+(?:\.\d+)?)([a-z]?)$", s)
    return (float(m.group(1)), m.group(2)) if m else (float("inf"), s)


def number_runs(glyphs: list[Glyph], page_height: float) -> list[NumberRun]:
    """Find ``( N )`` runs in a page's glyphs (pure; unit-tested with synthetic glyphs).

    Pairs each ``(`` with the next nearby ``)`` and keeps the run only when the enclosed text is a
    plausible equation number. Geometry (band + right-margin) is applied later, per equation.
    """
    out: list[NumberRun] = []
    n = len(glyphs)
    i = 0
    while i < n:
        if glyphs[i].char == "(":
            j = i + 1
            inner: list[Glyph] = []
            while j < n and (j - i) <= _MAX_INNER and glyphs[j].char != ")":
                inner.append(glyphs[j])
                j += 1
            if j < n and glyphs[j].char == ")":
                s = "".join(c.char for c in inner).strip()
                if _EQNUM.fullmatch(s):
                    yc = page_height - (glyphs[i].bottom + glyphs[i].top) / 2
                    out.append(NumberRun(s, yc, glyphs[i].left, glyphs[j].right))
                i = j + 1
                continue
        i += 1
    return out


def bind_equation_numbers(
    root: BlockNode,
    glyphs_by_page: dict[int, list[Glyph]],
    heights: dict[int, float],
    *,
    y_tol: float = 7.0,
    right_tol: float = 30.0,
) -> int:
    """Assign glyph-recovered numbers onto ``equation`` nodes in place; return the count bound.

    A ``(N)`` binds to an equation when its y-centre sits in the node's vertical band (± ``y_tol``)
    *and* it ends at the node's right margin (``run.right >= node.right - right_tol``). The right-edge
    test is **column-aware**: it keys off the equation's own bbox, so a number right-aligned to a
    text *column* (two-column papers) is caught where a page-width test would miss it, and an inline
    ``(5)`` in the equation body — which ends mid-line, far from the right margin — is rejected.
    """
    runs_by_page = {
        pno: number_runs(gs, heights.get(pno, 0.0)) for pno, gs in glyphs_by_page.items()
    }
    bound = 0
    for node in root.walk():
        if node.type != "equation" or not node.prov:
            continue
        p = node.prov[0]
        _l, top, right, bottom = p.bbox
        nums = sorted(
            {
                run.number
                for run in runs_by_page.get(p.page_no, [])
                if (top - y_tol) <= run.y_center <= (bottom + y_tol)
                and run.right >= (right - right_tol)
            },
            key=_num_key,
        )
        if not nums:
            continue
        node.attrs["numbers"] = nums
        if len(nums) == 1:  # the common single-line case keeps a clean scalar for xref/eval
            node.attrs["number"] = nums[0]
        bound += len(nums)
    return bound


def recover_equation_numbers(root: BlockNode, pdf_path) -> int:
    """Thin I/O wrapper: read the PDF glyph layer and bind equation numbers. Returns count bound."""
    glyphs_by_page, heights = extract_glyphs(pdf_path)
    return bind_equation_numbers(root, glyphs_by_page, heights)
