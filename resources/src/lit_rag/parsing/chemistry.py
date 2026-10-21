"""Chemistry primitives shared by the parsing-eval gold (the ruler) and the chemistry enrichment
pass (the parser, forthcoming): a periodic-table element alphabet, subscript normalisation, and
pymatgen-backed canonicalisation.

Design notes carried over from the TracEx ``compound_extractor.py`` baseline (the survey prototype):

* The element alphabet lists two-letter symbols **first** so the regex prefers the longest match
  (``Sb`` over ``S`` + ``b``).
* ``pymatgen.Composition`` accepts *dummy species* (non-element symbols), so a validity check must
  confirm every parsed species is a real :class:`~pymatgen.core.periodic_table.Element` — a bare
  ``Composition(...)`` call is **not** a sufficient filter (``Composition("SPIN")`` succeeds:
  ``S, P, In`` are all real elements). The acronym false-positive gate lives in the parser pass.
* Alloys are canonicalised to **fractional composition** (at.% preserved), never ``reduced_formula``
  — GCD reduction turns ``Co20Fe60B20`` into ``CoFe3B`` and discards the at.%.

``pymatgen`` is an **optional** dependency (the ``chem`` extra). Everything degrades gracefully when
it is absent: :func:`canonical_formula` returns ``None`` and :func:`is_valid_composition` returns
``False`` rather than raising, so the offline gate never hard-requires the heavy stack.
"""

from __future__ import annotations

import re
from functools import lru_cache

# --- element alphabet (two-letter first, for longest-match) -------------------------------------

_TWO_LETTER = (
    "Ac|Ag|Al|Am|Ar|As|At|Au|Ba|Be|Bh|Bi|Bk|Br|Ca|Cd|Ce|Cf|Cl|Cm|"
    "Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|Fe|Fl|Fm|Fr|Ga|Gd|Ge|He|Hf|Hg|"
    "Ho|Hs|In|Ir|Kr|La|Li|Lr|Lu|Mc|Md|Mg|Mn|Mo|Mt|Na|Nb|Nd|Ne|Nh|"
    "Ni|No|Np|Og|Os|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|"
    "Ru|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|Xe|Yb|"
    "Zn|Zr"
)
_ONE_LETTER = "B|C|F|H|I|K|N|O|P|S|U|V|W|Y"
ELEMENT = rf"(?:{_TWO_LETTER}|{_ONE_LETTER})"

# A plain-text formula candidate: >=2 (element + optional inline numeric subscript) groups. This is
# the *discovery* regex for prose that has already been normalised (subscripts flattened to digits);
# the parser pass adds the acronym/casing precision gate before trusting a hit.
_INLINE_SUB = r"(?:[0-9]+(?:\.[0-9]+)?)"
FORMULA_RE = re.compile(rf"\b((?:{ELEMENT}{_INLINE_SUB}?){{2,}})\b")

# --- subscript normalisation --------------------------------------------------------------------

_SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def normalize_subscripts(s: str) -> str:
    """Flatten Unicode sub/superscript digits to ASCII (``Co₂₀`` -> ``Co20``)."""
    return s.translate(_SUBSCRIPT_MAP).translate(_SUPERSCRIPT_MAP)


# --- pymatgen-backed canonicalisation (optional, lazy) ------------------------------------------


@lru_cache(maxsize=1)
def pymatgen_available() -> bool:
    """True if pymatgen can be imported. Cached; used to decide whether validity-gating applies."""
    try:
        import pymatgen.core.composition  # noqa: F401

        return True
    except Exception:
        return False


def _composition(surface: str):
    """``Composition`` for ``surface`` if every species is a real element, else ``None``. Returns
    ``None`` (never raises) when pymatgen is absent or the string does not parse."""
    try:
        from pymatgen.core.composition import Composition
        from pymatgen.core.periodic_table import Element
    except Exception:
        return None
    try:
        comp = Composition(surface)
    except Exception:
        return None
    if not comp.elements or not all(isinstance(el, Element) for el in comp.elements):
        return None
    return comp


def is_valid_composition(surface: str) -> bool:
    """True if ``surface`` parses as a composition of only real periodic-table elements. False when
    pymatgen is unavailable — so callers gate on it only when :func:`pymatgen_available`."""
    return _composition(surface) is not None


def canonical_formula(surface: str) -> str | None:
    """Canonical **fractional-composition** formula string (at.% preserved), e.g.
    ``"Co20Fe60B20"`` -> ``"Co0.2 Fe0.6 B0.2"``. ``None`` if pymatgen is unavailable or the string is
    not a pure-element composition (e.g. a variable subscript like ``Ti3C2Tx``)."""
    comp = _composition(surface)
    if comp is None:
        return None
    return comp.fractional_composition.formula


# --- the acronym/casing precision gate + extractor ----------------------------------------------

_ELEMENT_TOKEN_RE = re.compile(rf"({ELEMENT})([0-9]*(?:\.[0-9]+)?)")
# Mixed-case acronyms that *are* valid element sequences (so casing alone can't reject them).
# Tiny, evidence-driven stoplist — grows only as real corpus false positives appear.
_ACRONYM_STOPLIST = frozenset({"IUCr"})


def looks_like_formula(surface: str) -> bool:
    """Precision gate distinguishing a real material formula from an all-caps acronym or a code.

    ``pymatgen``-validity is necessary but **not sufficient** — ``Composition("SPIN")`` succeeds
    (``S, P, In`` are all elements), as do ``ISBN``/``NSCF``. The discriminator is orthography, read
    off the empirical false positives:

    * Real formulas carry a **lowercase letter** (a two-letter element: ``GaAs``, ``MoS2``, ``NaCl``)
      **or** give **every element a numeric count** (``V2O5``, ``Co20Fe60B20``, ``K0.5V2O5``).
    * Bare all-caps acronyms (``SPIN``, ``ISBN``, ``NSCF``, ``CSIC``) have neither.
    * Institution/grant codes (``ICN2``, ``FPU21``, ``CN00000013``) have only a *trailing* number, so
      not every element is counted — rejected by the same rule.

    Residual formula-shaped acronyms (``IUCr`` = I·U·Cr) are caught by a small stoplist."""
    if surface in _ACRONYM_STOPLIST:
        return False
    if any(c.islower() for c in surface):
        return True  # two-letter element present => formula-like
    # all-uppercase: accept only if the token tokenises cleanly into elements that *each* carry a
    # count (real stoichiometry), which a trailing-number code like "ICN2" fails.
    toks = _ELEMENT_TOKEN_RE.findall(surface)
    if not toks or "".join(e + n for e, n in toks) != surface:
        return False
    return all(n for _, n in toks)


def extract_materials(text: str) -> list[dict]:
    """Find material-formula occurrences in (already citation-normalised) prose: discover candidates
    with :data:`FORMULA_RE`, keep those that pass :func:`looks_like_formula` (and, when pymatgen is
    present, are valid all-element compositions), and canonicalise each. Returns one record per
    occurrence — ``{surface, canonical, start, end}`` — spans indexing into ``text`` (subscript
    normalisation is 1:1, so spans are preserved). Precision-first: an uncertain candidate is dropped.
    """
    norm = normalize_subscripts(text)
    out: list[dict] = []
    for m in FORMULA_RE.finditer(norm):
        surface = m.group(1)
        if not looks_like_formula(surface):
            continue
        if pymatgen_available() and not is_valid_composition(surface):
            continue
        out.append(
            {
                "surface": surface,
                "canonical": canonical_formula(surface),
                "start": m.start(1),
                "end": m.end(1),
            }
        )
    return out


# Non-technical section headings whose bodies never declare the *studied* material — their "formulas"
# are funder acronyms, grant codes, institute names, and author initials pymatgen mis-parses (ADR-0006).
# Matched at a heading's start; an optional leading section number/roman ("6.", "VI.") is tolerated.
_NONTECHNICAL_HEADING_RE = re.compile(
    r"(?i)^\s*(?:[\dIVXLC]+[.)]?\s+)?"
    r"(?:acknowledge?ments?|fundings?|financial support|grants?"
    r"|data availability|code availability|availability of data"
    r"|author contributions?|author information|contributions"
    r"|competing interests?|conflicts? of interest|declarations?"
    r"|references|bibliography|works cited)\b"
)


def _is_nontechnical_heading(text: str | None) -> bool:
    return bool(text and _NONTECHNICAL_HEADING_RE.match(text))


def nontechnical_section_ids(root) -> set[str]:
    """Ids of every node inside a non-technical region — acknowledgements, funding, data/code
    availability, author contributions, references/bibliography (ADR-0006) — plus GROBID-added
    ``reference`` nodes regardless of heading. This is the shared **input-domain restriction** seam:
    material extraction (and later retrieval down-weighting, [[docs/issues/0011]]) skips these ids so a
    whole false-positive family is never generated, rather than caught by a downstream denylist.

    **Precision-first, like** :func:`citation_normalize._front_matter_leaf_ids`: a region is excluded
    only when a section heading matches, and the exclusion inherits down the whole subtree (a nested
    non-heading paragraph stays excluded). An *unlabeled* acknowledgements block is therefore still
    scanned — a miss costs a few false positives, never a wrongly-dropped body section.
    """
    skip: set[str] = set()

    def _walk(node, excluded: bool) -> None:
        here = excluded
        if node.type in ("chapter", "section", "subsection"):
            here = excluded or _is_nontechnical_heading(node.text)
        if here or node.type == "reference":
            skip.add(node.id)
        for child in node.children:
            _walk(child, here)

    _walk(root, False)
    return skip


def tag_materials(root) -> int:
    """Attach :func:`extract_materials` hits to each text node's ``attrs['materials']`` (the structured
    material-entity signal retrieval filters/boosts on), returning the total count. Runs on the
    already-citation-normalised tree (the ordering caution: post-normalisation, so an element
    subscript is never double-claimed as a citation). **Skips non-technical regions**
    (:func:`nontechnical_section_ids`, ADR-0006) — precision-by-construction over a downstream FP-list.
    Idempotent — overwrites any prior tags (and clears stale tags on now-excluded nodes)."""
    skip = nontechnical_section_ids(root)
    total = 0
    for node in root.walk():
        node.attrs.pop("materials", None)
        if not node.text or node.id in skip:
            continue
        mats = extract_materials(node.text)
        if mats:
            node.attrs["materials"] = mats
            total += len(mats)
    return total


def tree_text(root, exclude_ids: set[str] | None = None) -> str:
    """All textual content of a parsed tree as one blob — title, every node's text, and table-cell
    text (table nodes carry content in ``attrs['cells']``, not ``text``). The text a formula must
    appear in to count as 'parsed'. ``exclude_ids`` drops those nodes (the eval passes
    :func:`nontechnical_section_ids` so its extract rows measure the same input domain the parse pass
    tags over; the text-*survival* row keeps the full blob, being a region-agnostic fidelity check)."""
    exclude_ids = exclude_ids or set()
    parts = [str(root.attrs.get("title") or "")]
    for n in root.walk():
        if n.id in exclude_ids:
            continue
        if n.text:
            parts.append(n.text)
        for row in n.attrs.get("cells", []) or []:
            parts.extend(str(c) for c in row)
    return " ".join(parts)


# --- glyph formula recovery (issue 0009 / 0005): recover live-text formulas Docling dropped --------
#
# Born-digital PDFs store every formula as real text in the glyph layer; Docling's *layout* stage
# (not OCR — OCR is off) sometimes misclassifies a text region as a picture and drops its glyphs. We
# read the glyph stream directly (pypdfium2) and recover the formulas the structural tree is missing.
# Scope: formulas rendered as PDF *text*; formulas that live only in figure *images* are out of scope
# here (the figure VLM's job at embed time). The general "glyph stream as text authority" pivot is the
# architectural direction in docs/issues/0002 + 0005.


_LINE_BREAK_FRAC = 0.8  # vertical jump (× font size) that separates two text lines


def _glyph_page_text(glyphs):
    """Reconstruct a page's reading-order text from its glyphs **with a line-break separator**, plus a
    parallel map from each string index to its source glyph (``None`` for inserted spaces).

    A space is inserted only on a **vertical line break** (jump > :data:`_LINE_BREAK_FRAC`·size), so two
    stacked lines don't merge into a spurious formula. The threshold sits above a subscript's vertical
    drop (~0.3·size) so ``Mn₄N₃Cl₂`` stays whole — tuned on the corpus: a tighter 0.6 split deep
    subscripts and a horizontal word-gap separator split formulas at internal kerning (both fragmented
    the dense MXene lists). Real space glyphs already separate words, so no horizontal rule is needed.
    """
    chars: list[str] = []
    gmap: list[object] = []
    prev = None
    for g in glyphs:
        if prev is not None:
            size = max(getattr(prev, "size", 0) or 0, 1.0)
            if abs(g.top - prev.top) > _LINE_BREAK_FRAC * size:
                chars.append(" ")
                gmap.append(None)
        chars.append(g.char)
        gmap.append(g)
        prev = g
    return normalize_subscripts("".join(chars)), gmap


def glyph_formula_candidates(pdf_path) -> list[dict]:
    """Every gated material formula in the PDF's glyph layer, with page + bbox provenance. The same
    ``FORMULA_RE`` + :func:`looks_like_formula` (+ pymatgen) gate as the text extractor — precision
    first — but reading the raw glyph stream instead of Docling's (lossy) tree text."""
    from .superscript_cites import extract_glyphs

    glyphs_by_page, _heights = extract_glyphs(pdf_path)
    out: list[dict] = []
    for page, glyphs in glyphs_by_page.items():
        text, gmap = _glyph_page_text(glyphs)
        for m in FORMULA_RE.finditer(text):
            surface = m.group(1)
            if not looks_like_formula(surface):
                continue
            if pymatgen_available() and not is_valid_composition(surface):
                continue
            run = [gmap[i] for i in range(m.start(1), m.end(1)) if gmap[i] is not None]
            if not run:
                continue
            bbox = (
                min(g.left for g in run),
                min(g.top for g in run),
                max(g.right for g in run),
                max(g.bottom for g in run),
            )
            out.append(
                {
                    "surface": surface,
                    "canonical": canonical_formula(surface),
                    "page": page,
                    "bbox": [round(v, 2) for v in bbox],
                }
            )
    return out


def find_dropped_formulas(root, pdf_path) -> list[dict]:
    """Glyph-layer formulas **absent from the parsed tree text** — i.e. what Docling dropped. One
    record per distinct surface (first occurrence's provenance)."""
    present = normalize_subscripts(tree_text(root))
    dropped: list[dict] = []
    seen: set[str] = set()
    for c in glyph_formula_candidates(pdf_path):
        if c["surface"] in seen:
            continue
        pat = rf"(?<![A-Za-z0-9]){re.escape(c['surface'])}(?![A-Za-z0-9])"
        if re.search(pat, present, re.IGNORECASE):
            continue  # Docling kept this one
        seen.add(c["surface"])
        dropped.append(c)
    return dropped


def recover_dropped_formulas(root, pdf_path) -> int:
    """Recover the formulas Docling dropped from live text and record them on
    ``root.attrs['recovered_materials']`` (``{surface, canonical, page, bbox}`` — exact text with
    page/bbox provenance, deterministic, no VLM). Page/bbox provenance is reliable; tying each to a
    specific surviving node is deferred (the dropped region often has no surviving node). Returns the
    count. Idempotent."""
    root.attrs.pop("recovered_materials", None)
    dropped = find_dropped_formulas(root, pdf_path)
    if dropped:
        root.attrs["recovered_materials"] = dropped
    return len(dropped)
