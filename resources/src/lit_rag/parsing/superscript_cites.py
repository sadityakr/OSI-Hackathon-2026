"""Superscript citation **detector** (ADR-0003) — find the raised numeric markers in a PDF's glyphs.

Most physics journals cite by a **raised superscript number** (``...skyrmion dynamics³⁴``), not a
bracketed ``[34]``. In the text layer these are *ambiguous bare numbers* (Docling renders them as
``dynamics 34``, indistinguishable from ``Figure 34``). What disambiguates a citation is the **PDF
glyph geometry**. This module is the detector; :mod:`citation_normalize` consumes it to rewrite each
detected run into the canonical ``[34]`` form in the tree (so every citation style ends up uniform).

A superscript citation marker is a run of digits that is, against the page's body text, all four of:

1. **smaller** — font size below ``min_ratio`` × the page's median body size (a crisp 7pt-vs-11pt
   cluster on real papers);
2. **digits + separators** (``,`` ``–`` ``-``) — so ranges/lists (``9–13,21,34–36``) parse out;
3. **after a word** — the run follows ≥2 alphabetic glyphs. This is the user's key rule ("markers
   appear after text, rarely after numbers"), strengthened to a *word* so it also rejects inline
   variable exponents (``E²``): it kills math exponents (``10⁷``, ``10⁻²`` — after a digit/operator);
4. **raised** — the run's vertical centre sits above the preceding glyph's midline, which rejects
   *sub*scripts of the same small font (chemical formulae like ``Co₂₀Fe₆₀B₂₀``).

All four validated on real papers: 50 body citations, zero false positives, each mapping back to the
right paragraph. (The 9 author-block ``Beneke¹`` *affiliation* superscripts are excluded downstream in
:mod:`citation_normalize`, by front-matter section.) Detection is **pure** (operates on a glyph list,
unit-tested offline with synthetic glyphs); only :func:`extract_glyphs` touches the PDF (pypdfium2,
already a Docling dependency).
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

_SEP = ",-–—"  # separators allowed inside a citation run (comma, hyphen, en/em dash)


@dataclass(frozen=True)
class Glyph:
    """One character with its pdfium box (BOTTOM-LEFT origin, PDF points) and font size."""

    char: str
    left: float
    bottom: float
    right: float
    top: float
    size: float


@dataclass(frozen=True)
class CitationMarker:
    """A detected superscript marker: where it is + which references it cites."""

    page_no: int
    bbox: tuple[float, float, float, float]  # TOP-LEFT origin (l, t, r, b), like Provenance
    numbers: tuple[int, ...]  # parsed reference numbers (ranges/lists expanded), sorted
    run: str  # the raw run text, e.g. "9–13,21"
    word: str = ""  # the word the marker follows (anchor for ``[N]`` normalization); "" if unused


# ── pure: number parsing ──────────────────────────────────────────────────────────────────────────


def expand_numbers(run: str, *, max_range: int = 200) -> list[int]:
    """ "9–13,21,34–36" → [9,10,11,12,13,21,34,35,36]. Ranges expand; junk parts are skipped."""
    nums: set[int] = set()
    for part in run.split(","):
        part = re.sub(r"[—–-]", "–", part.strip())  # normalise all dashes to en dash
        if "–" in part:
            a, _, b = part.partition("–")
            a, b = a.strip(), b.strip()  # tolerate "1 - 4" (spaced ranges in source brackets)
            if a.isdigit() and b.isdigit():
                lo, hi = int(a), int(b)
                if 0 < lo <= hi and hi - lo < max_range:
                    nums.update(range(lo, hi + 1))
        elif part.isdigit():
            nums.add(int(part))
    return sorted(nums)


# ── pure: superscript detection over a page's glyphs ──────────────────────────────────────────────


def _body_size(glyphs: list[Glyph]) -> float:
    sizes = [g.size for g in glyphs if g.char.strip()]
    return statistics.median(sizes) if sizes else 0.0


def _is_raised(run_chars: list[Glyph], prev: Glyph, raise_frac: float) -> bool:
    run_mid = statistics.median([(g.bottom + g.top) / 2 for g in run_chars])
    prev_mid = (prev.bottom + prev.top) / 2
    return run_mid > prev_mid + raise_frac * (prev.top - prev.bottom)


def _preceding_word(glyphs: list[Glyph], i: int) -> str:
    """The contiguous run of alpha glyphs ending just before index ``i`` — the citation's anchor word."""
    chars = []
    k = i - 1
    while k >= 0 and glyphs[k].char.isalpha():
        chars.append(glyphs[k].char)
        k -= 1
    return "".join(reversed(chars))


def detect_runs(glyphs: list[Glyph], *, min_ratio: float = 0.85, raise_frac: float = 0.10):
    """Yield ``(run_chars, run_text, prev_glyph, preceding_word)`` per superscript citation run.

    Pure: takes a glyph list (any source), so it is unit-tested with synthetic glyphs — no PDF.
    """
    body = _body_size(glyphs)
    if body <= 0:
        return
    n = len(glyphs)
    i = 0
    while i < n:
        g = glyphs[i]
        if g.char.isdigit() and g.size < min_ratio * body:
            run_chars = [g]
            j = i + 1
            while (
                j < n
                and (glyphs[j].char.isdigit() or glyphs[j].char in _SEP)
                and glyphs[j].size < min_ratio * body
            ):
                run_chars.append(glyphs[j])
                j += 1
            while run_chars and run_chars[-1].char in _SEP:  # trim trailing separators
                run_chars.pop()
            run = "".join(c.char for c in run_chars)
            # rule: after a WORD (≥2 alpha glyphs) → kills exponents (10⁷) and variable powers (E²)
            after_word = i >= 2 and glyphs[i - 1].char.isalpha() and glyphs[i - 2].char.isalpha()
            if run_chars and after_word and _is_raised(run_chars, glyphs[i - 1], raise_frac):
                yield run_chars, run, glyphs[i - 1], _preceding_word(glyphs, i)
            i = max(j, i + 1)
        else:
            i += 1


def markers_from_page(
    glyphs: list[Glyph], page_no: int, page_height: float, *, with_word: bool = False
) -> list[CitationMarker]:
    """Detect markers on one page and convert their boxes to TOP-LEFT origin (Provenance convention).

    ``with_word=True`` also carries the preceding word, the anchor used by citation normalization.
    """
    out: list[CitationMarker] = []
    for run_chars, run, _prev, word in detect_runs(glyphs):
        nums = expand_numbers(run)
        if not nums:
            continue
        left = min(c.left for c in run_chars)
        right = max(c.right for c in run_chars)
        bottom = min(c.bottom for c in run_chars)
        top = max(c.top for c in run_chars)
        bbox_tl = (left, page_height - top, right, page_height - bottom)
        out.append(CitationMarker(page_no, bbox_tl, tuple(nums), run, word if with_word else ""))
    return out


# ── thin I/O: glyph extraction (not exercised by the offline gate) ─────────────────────────────────


def extract_glyphs(pdf_path) -> tuple[dict[int, list[Glyph]], dict[int, float]]:
    """Extract per-page glyphs (char + box + font size) and page heights via pypdfium2.

    Font size comes from the raw pdfium API (``FPDFText_GetFontSize``); the box from ``get_charbox``.
    Returns ``({page_no: [Glyph]}, {page_no: height})`` — pages are 1-indexed (Provenance convention).
    """
    import pypdfium2 as pdfium
    import pypdfium2.raw as pdfium_c

    pdf = pdfium.PdfDocument(str(pdf_path))
    glyphs_by_page: dict[int, list[Glyph]] = {}
    heights: dict[int, float] = {}
    for pno in range(len(pdf)):
        page = pdf[pno]
        _w, height = page.get_size()
        heights[pno + 1] = height
        tp = page.get_textpage()
        count = tp.count_chars()
        gs: list[Glyph] = []
        for i in range(count):
            char = tp.get_text_range(i, 1)
            left, bottom, right, top = tp.get_charbox(i)
            size = pdfium_c.FPDFText_GetFontSize(tp.raw, i)
            gs.append(Glyph(char, left, bottom, right, top, size))
        glyphs_by_page[pno + 1] = gs
    return glyphs_by_page, heights
