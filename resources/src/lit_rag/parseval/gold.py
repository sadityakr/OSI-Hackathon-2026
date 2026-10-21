"""Gold-from-authoring-source: extract a structured answer key from LaTeX source (+ compiled .aux).

The author already declared the structure we want to recover — ``\\title`` *is* the title,
``\\begin{equation}\\label{eq:x}`` *is* a numbered equation, ``\\cite`` *are* the citation keys — so we
mint gold from the **input** (source) rather than hand-labelling the **output** (PDF). Structure
comes from a tolerant TexSoup parse; *resolved numbers* come from the compiled ``.aux``
(``\\newlabel{eq:x}{{3.4}{...}}``), which is LaTeX's own authoritative cross-reference table.

Scope (v1): structured fields only — no geometry. See docs/research/parsing-eval-harness.md for the
covered/uncovered axis and the multi-numbered-align limitation.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from TexSoup import TexSoup

from lit_rag.parsing.chemistry import (
    ELEMENT,
    canonical_formula,
    is_valid_composition,
    pymatgen_available,
)

# heading command -> nesting level (chapter outermost). starred variants share the level.
_HEADING_LEVEL = {
    "chapter": 0,
    "chapter*": 0,
    "section": 1,
    "section*": 1,
    "subsection": 2,
    "subsection*": 2,
    "subsubsection": 3,
    "subsubsection*": 3,
}
_MATH_ENVS = (
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
    "displaymath",
)
_CITE_CMDS = ("cite", "citep", "citet", "citealp", "citealt", "citeauthor", "citeyear")
_REF_CMDS = ("ref", "eqref", "autoref", "cref", "Cref", "pageref")
_FLOAT_ENVS = ("figure", "figure*", "table", "table*")

_LABEL_RE = re.compile(r"\\label\s*\{[^}]*\}")
_NEWLABEL_RE = re.compile(r"\\newlabel\s*\{(.+?)\}\s*\{\s*\{(.*?)\}")
_WS = re.compile(r"\s+")

# A LaTeX subscript on an element: ``$_2$``, ``_{20}``, ``$_{0.5}$``, ``_x`` — the explicit marker
# that makes author-declared stoichiometry machine-extractable from *source* (no geometry guessing).
_LATEX_SUB = r"(?:\$?_\{?(?:[0-9]+(?:\.[0-9]+)?|[a-z])\}?\$?)"
# An in-source chemical formula: >=2 (element + optional LaTeX subscript) groups.
_SRC_FORMULA_RE = re.compile(rf"((?:{ELEMENT}{_LATEX_SUB}?){{2,}})")
_HAS_SUB_RE = re.compile(r"[_$]")
# Strip the LaTeX markup of a subscript formula to its inline-digit surface form
# (``V$_2$O$_5$`` -> ``V2O5``, ``Ti3C2T{$_x$}`` -> ``Ti3C2Tx``).
_SURFACE_STRIP_RE = re.compile(r"[${}_\\]|\s+")


# --- gold schema --------------------------------------------------------------------------------


@dataclass
class GoldSection:
    level: int  # 0 chapter, 1 section, 2 subsection, 3 subsubsection
    title: str


@dataclass
class GoldEquation:
    label: str | None  # \label name, e.g. "eq:llg" (None for an unnumbered/unlabelled env)
    number: str | None  # resolved printed number from .aux, e.g. "3.4" (None if unresolved)
    latex: str  # equation body LaTeX (\label stripped, whitespace-collapsed)


@dataclass
class GoldCitation:
    key: str  # \cite key
    order: int | None  # 1-based \bibitem order, when a thebibliography is in the source


@dataclass
class GoldXref:
    target: str  # \ref/\eqref target label
    kind: str  # equation|figure|table|section|unknown (from label prefix / \eqref)


@dataclass
class GoldCaption:
    kind: str  # figure|table
    label: str | None
    number: str | None  # resolved float number from .aux
    text: str


@dataclass
class GoldChemical:
    surface: str  # inline-digit form as it should survive in parsed text, e.g. "Co20Fe60B20"
    canonical: (
        str | None
    )  # pymatgen fractional-composition formula (at.% preserved); None if uncanonicalisable
    source: (
        str  # "ce" (mhchem \ce{}) | "subscript" (element + $_N$ run) — provenance of the gold hit
    )


@dataclass
class GoldDoc:
    arxiv_id: str | None = None
    categories: list[str] = field(default_factory=list)
    license: str | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    sections: list[GoldSection] = field(default_factory=list)
    equations: list[GoldEquation] = field(default_factory=list)
    citations: list[GoldCitation] = field(default_factory=list)
    xrefs: list[GoldXref] = field(default_factory=list)
    captions: list[GoldCaption] = field(default_factory=list)
    chemicals: list[GoldChemical] = field(default_factory=list)

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> GoldDoc:
        d = json.loads(s)
        return cls(
            arxiv_id=d.get("arxiv_id"),
            categories=d.get("categories", []),
            license=d.get("license"),
            title=d.get("title"),
            authors=d.get("authors", []),
            sections=[GoldSection(**x) for x in d.get("sections", [])],
            equations=[GoldEquation(**x) for x in d.get("equations", [])],
            citations=[GoldCitation(**x) for x in d.get("citations", [])],
            xrefs=[GoldXref(**x) for x in d.get("xrefs", [])],
            captions=[GoldCaption(**x) for x in d.get("captions", [])],
            chemicals=[GoldChemical(**x) for x in d.get("chemicals", [])],
        )


# --- helpers ------------------------------------------------------------------------------------


def _arg_text(node) -> str | None:
    """Inner text of a command's last brace group — robust to optional args (``\\section[x]{y}``)
    where TexSoup's ``.string`` asserts. Nested braces/math inside are preserved."""
    args = list(node.args)
    braces = [str(a) for a in args if str(a).startswith("{")]
    chosen = braces[-1] if braces else (str(args[-1]) if args else None)
    return chosen[1:-1] if chosen else None


def _kind_from_label(label: str) -> str:
    p = label.split(":", 1)[0].lower() if ":" in label else ""
    return {
        "eq": "equation",
        "eqn": "equation",
        "fig": "figure",
        "tab": "table",
        "table": "table",
        "sec": "section",
        "sect": "section",
    }.get(p, "unknown")


def parse_aux(aux_text: str) -> dict[str, str]:
    """label -> printed number, from LaTeX's ``\\newlabel`` records (plain or hyperref form)."""
    return {m.group(1): m.group(2) for m in _NEWLABEL_RE.finditer(aux_text)}


def _env_body(node) -> str:
    """Stringify an environment's contents, strip ``\\label{...}``, collapse whitespace."""
    body = "".join(str(c) for c in node.contents)
    body = _LABEL_RE.sub("", body)
    return _WS.sub(" ", body).strip()


def _surface(raw: str) -> str:
    """LaTeX formula markup -> inline-digit surface form (``V$_2$O$_5$`` -> ``V2O5``)."""
    return _SURFACE_STRIP_RE.sub("", raw)


def _ce_bodies(latex: str) -> list[str]:
    """Bodies of every ``\\ce{...}`` (mhchem), brace-balanced so nested groups like
    ``\\ce{Ti3C2T{$_x$}}`` are captured whole rather than truncated at the first ``}``."""
    out: list[str] = []
    i = 0
    while True:
        k = latex.find(r"\ce{", i)
        if k < 0:
            return out
        j = start = k + 4
        depth = 1
        while j < len(latex) and depth:
            depth += {"{": 1, "}": -1}.get(latex[j], 0)
            j += 1
        out.append(latex[start : j - 1])
        i = j


def extract_chemicals(latex: str) -> list[GoldChemical]:
    """Mint chemical-formula gold from LaTeX **source** — the author already declared the
    stoichiometry, two machine-readable ways:

    * **mhchem ``\\ce{...}``** — explicit, author-tagged chemistry; trusted as-is.
    * **element + LaTeX-subscript runs** (``V$_2$O$_5$``) — the ``$_N$`` makes the stoichiometry
      explicit in source, no PDF geometry needed. Requires an actual subscript (a bare ``GaAs`` is
      indistinguishable from an acronym in source, so — like the ``\\label``-only equation gold — it
      is left uncredited rather than guessed), and, when pymatgen is present, must be a valid
      all-element composition (drops math-mode noise like a field component ``B_2``).

    Deduplicated by surface form; ``\\ce`` wins the source tag on collision.
    """
    by_surface: dict[str, GoldChemical] = {}

    def _add(surface: str, source: str) -> None:
        if not surface or surface in by_surface:
            return
        by_surface[surface] = GoldChemical(
            surface=surface, canonical=canonical_formula(surface), source=source
        )

    for body in _ce_bodies(latex):
        _add(_surface(body), "ce")
    for m in _SRC_FORMULA_RE.finditer(latex):
        raw = m.group(1)
        if not _HAS_SUB_RE.search(raw):  # require an explicit subscript marker
            continue
        surface = _surface(raw)
        if pymatgen_available() and not is_valid_composition(surface):
            continue  # precision gate, only when we can actually validate
        _add(surface, "subscript")

    return list(by_surface.values())


# --- extraction ---------------------------------------------------------------------------------


def extract_gold(
    latex_source: str,
    aux: str | None = None,
    *,
    arxiv_id: str | None = None,
    categories: list[str] | None = None,
    license: str | None = None,
) -> GoldDoc:
    """Parse LaTeX source into a :class:`GoldDoc`. ``aux`` (compiled ``.aux`` text) resolves
    equation/float numbers; without it, numbers stay ``None`` (recall/structure still score)."""
    soup = TexSoup(latex_source, tolerance=1)  # tolerance=1: skip malformed nodes, don't crash
    numbers = parse_aux(aux) if aux else {}

    gold = GoldDoc(
        arxiv_id=arxiv_id,
        categories=categories or [],
        license=license,
    )

    # title / authors
    t = soup.find("title")
    if t is not None:
        gold.title = (_arg_text(t) or "").strip() or None
    a = soup.find("author")
    if a is not None:
        raw = _arg_text(a) or ""
        gold.authors = [p.strip() for p in re.split(r"\\and", raw) if p.strip()]

    # section hierarchy (reading order across heading types)
    for node in soup.find_all(list(_HEADING_LEVEL)):
        title = (_arg_text(node) or "").strip()
        if title:
            gold.sections.append(GoldSection(level=_HEADING_LEVEL[node.name], title=title))

    # equations — one gold entry per \label (number-binding gold); one unlabelled entry otherwise
    for env in _MATH_ENVS:
        for node in soup.find_all(env):
            body = _env_body(node)
            labels = [_arg_text(ln) for ln in node.find_all("label") if _arg_text(ln)]
            if labels:
                for lbl in labels:
                    gold.equations.append(
                        GoldEquation(label=lbl, number=numbers.get(lbl), latex=body)
                    )
            else:
                gold.equations.append(GoldEquation(label=None, number=None, latex=body))

    # citations — unique keys in first-appearance order; bib order from \bibitem when present
    bib_order = {}
    for i, b in enumerate(soup.find_all("bibitem"), start=1):
        key = _arg_text(b)
        if key and key not in bib_order:
            bib_order[key] = i
    seen: set[str] = set()
    for cmd in _CITE_CMDS:
        for node in soup.find_all(cmd):
            raw = _arg_text(node) or ""
            for key in (k.strip() for k in raw.split(",")):
                if key and key not in seen:
                    seen.add(key)
                    gold.citations.append(GoldCitation(key=key, order=bib_order.get(key)))

    # cross-references
    for cmd in _REF_CMDS:
        for node in soup.find_all(cmd):
            tgt = _arg_text(node)
            if tgt:
                kind = "equation" if cmd == "eqref" else _kind_from_label(tgt)
                gold.xrefs.append(GoldXref(target=tgt, kind=kind))

    # captions on floats
    for env in _FLOAT_ENVS:
        for node in soup.find_all(env):
            cap = node.find("caption")
            if cap is None:
                continue
            lbl_node = node.find("label")
            label = _arg_text(lbl_node) if lbl_node is not None else None
            kind = "table" if env.startswith("table") else "figure"
            gold.captions.append(
                GoldCaption(
                    kind=kind,
                    label=label,
                    number=numbers.get(label) if label else None,
                    text=(_arg_text(cap) or "").strip(),
                )
            )

    # chemical formulas — extracted from raw source (mhchem + subscript runs), not the TexSoup tree
    gold.chemicals = extract_chemicals(latex_source)

    return gold


def build_gold_file(
    tex_path: str | Path, aux_path: str | Path | None, out_path: str | Path, **meta
) -> GoldDoc:
    """Read a .tex (+ optional .aux), extract gold, write JSON to ``out_path``. Returns the gold."""
    src = Path(tex_path).read_text(encoding="utf-8", errors="replace")
    aux = Path(aux_path).read_text(encoding="utf-8", errors="replace") if aux_path else None
    gold = extract_gold(src, aux, **meta)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)  # fresh clones have no tmp/ (CI run #1)
    out_path.write_text(gold.to_json(), encoding="utf-8")
    return gold
