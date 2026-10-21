"""Score a parsed ``BlockNode`` tree against the LaTeX-derived gold — a per-failure-mode scorecard.

Intrinsic eval: each row scores one structured field in isolation and maps to a known parser issue
(see docs/research/parsing-eval-harness.md), so a change shows *which* mode moved. The headline row
is **equation number-binding** (docs/issues/0001).

Alignment is offline and label-blind: gold ``\\ref``/``\\cite`` targets are source *labels* while the
tree carries node *ids*, so cross-references are scored by per-kind **count recall**, not exact
target match (a label->id resolver would lift this — future work). Equations are matched greedily by
LaTeX similarity (robust to a dropped/extra equation); title/sections/captions by normalised text.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lit_rag.parseval.gold import GoldDoc
from lit_rag.parseval.mathmetric import latex_similarity, normalize_text, text_similarity
from lit_rag.parsing.chemistry import (
    extract_materials,
    find_dropped_formulas,
    nontechnical_section_ids,
    normalize_subscripts,
    tree_text,
)
from lit_rag.parsing.schema import BlockNode

# parsed container types -> the same level scale gold uses (chapter outermost)
_PARSED_LEVEL = {"chapter": 0, "section": 1, "subsection": 2}
_NUM_RE = re.compile(r"\d+(?:\.\d+)*")
_REF_EDGE_KIND = {
    "references-equation": "equation",
    "references-figure": "figure",
    "references-table": "table",
    "references-section": "section",
}


@dataclass
class Metric:
    """One scorecard row: a score in [0, 1] plus the raw counts behind it for transparency."""

    score: float
    gold_n: int
    parsed_n: int
    note: str = ""


@dataclass
class Scorecard:
    rows: dict[str, Metric] = field(default_factory=dict)

    @property
    def overall(self) -> float:
        """Mean of the headline rows — a single trend number; the rows are the real signal."""
        vals = [m.score for m in self.rows.values()]
        return sum(vals) / len(vals) if vals else 0.0

    def render(self) -> str:
        w = max((len(k) for k in self.rows), default=10)
        lines = [
            f"{'metric'.ljust(w)}  score   gold  parsed  note",
            f"{'-' * w}  -----   ----  ------  ----",
        ]
        for k, m in self.rows.items():
            lines.append(f"{k.ljust(w)}  {m.score:5.3f}  {m.gold_n:4d}  {m.parsed_n:6d}  {m.note}")
        lines.append(f"{'OVERALL'.ljust(w)}  {self.overall:5.3f}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Plain-dict snapshot (JSON-ready) — the persisted baseline a later run diffs against."""
        return {
            "overall": round(self.overall, 4),
            "rows": {
                k: {"score": round(m.score, 4), "gold_n": m.gold_n, "parsed_n": m.parsed_n}
                for k, m in self.rows.items()
            },
        }


def diff_scorecards(baseline: dict, current: dict, *, tol: float = 0.005) -> list[dict]:
    """Compare two ``Scorecard.to_dict`` snapshots; return the rows that moved beyond ``tol``.

    Each entry is ``{row, kind, old, new, delta}`` where ``kind`` is ``regressed`` / ``improved`` /
    ``added`` / ``removed`` — a **removed** row (a metric that stopped being scored) or a regression is
    the signal an autonomous loop must not silently pass. ``tol`` absorbs float noise, not real moves.
    """
    b_rows, c_rows = baseline.get("rows", {}), current.get("rows", {})
    out: list[dict] = []
    for k in dict.fromkeys([*b_rows, *c_rows]):
        if k not in c_rows:
            out.append({"row": k, "kind": "removed", "old": b_rows[k]["score"], "new": None})
        elif k not in b_rows:
            out.append({"row": k, "kind": "added", "old": None, "new": c_rows[k]["score"]})
        else:
            old, new = b_rows[k]["score"], c_rows[k]["score"]
            if abs(new - old) > tol:
                kind = "regressed" if new < old else "improved"
                out.append(
                    {"row": k, "kind": kind, "old": old, "new": new, "delta": round(new - old, 4)}
                )
    return out


# --- parsed-side extractors ---------------------------------------------------------------------


def _parsed_numbers(node: BlockNode) -> set[str]:
    """Equation numbers the parser recorded, as a set — a node may carry several merged display
    numbers (``attrs['numbers']``) or one (``attrs['number']``), or a number parsed out of
    ``attrs['label']`` (e.g. '(3.4)'). Robust to whichever convention the 0001 fix lands on."""
    out: set[str] = set()
    for x in node.attrs.get("numbers", []) or []:
        out.add(str(x).strip())
    num = node.attrs.get("number")
    if num:
        out.add(str(num).strip())
    label = node.attrs.get("label")
    if label:
        m = _NUM_RE.search(str(label))
        if m:
            out.add(m.group(0))
    return out


def _collect(root: BlockNode):
    eqs, secs, caps, authors = [], [], [], []
    title = root.attrs.get("title")
    ref_kinds: Counter[str] = Counter()
    n_refs = 0
    for node in root.walk():
        if node.type == "equation":
            eqs.append(node)
        elif node.type in _PARSED_LEVEL:
            secs.append(node)
        elif node.type == "caption":
            caps.append(node)
        elif node.type == "author":
            if node.text:
                authors.append(node.text)
        elif node.type == "reference":
            n_refs += 1
        for e in node.edges:
            if e.type in _REF_EDGE_KIND:
                ref_kinds[_REF_EDGE_KIND[e.type]] += 1
    if not authors:
        authors = list(root.attrs.get("authors", []) or [])
    return title, eqs, secs, caps, authors, ref_kinds, n_refs


# --- per-field scorers --------------------------------------------------------------------------


def _score_equations(gold: GoldDoc, parsed_eqs: list[BlockNode]) -> dict[str, Metric]:
    gold_eqs = gold.equations
    if not gold_eqs:  # nothing to score — omit (don't inflate the mean with a vacuous 1.0)
        return {}
    # greedy best-similarity matching, label-blind
    unused = list(range(len(parsed_eqs)))
    pairs: list[tuple] = []
    for g in gold_eqs:
        best_j, best_s = None, 0.5  # require >0.5 to count as a match
        for j in unused:
            s = latex_similarity(g.latex, parsed_eqs[j].attrs.get("latex", ""))
            if s > best_s:
                best_j, best_s = j, s
        if best_j is not None:
            unused.remove(best_j)
            pairs.append((g, parsed_eqs[best_j], best_s))

    n_gold = len(gold_eqs)
    recall = len(pairs) / n_gold
    sim = sum(s for _, _, s in pairs) / len(pairs) if pairs else 0.0
    out = {
        "equation_recall": Metric(recall, n_gold, len(parsed_eqs), "matched by latex-sim>0.5"),
        "equation_latex_sim": Metric(sim, n_gold, len(parsed_eqs), "mean norm-latex sim of pairs"),
    }

    numbered = [g for g in gold_eqs if g.number]
    if numbered:  # only score number-binding where the source actually numbers equations
        matched_by_g = {id(g): p for g, p, _ in pairs}
        hits = sum(
            1
            for g in numbered
            if id(g) in matched_by_g and g.number in _parsed_numbers(matched_by_g[id(g)])
        )
        out["equation_number_binding"] = Metric(
            hits / len(numbered), len(numbered), len(parsed_eqs), "issue 0001 — resolved # match"
        )
    return out


def _score_sections(gold: GoldDoc, parsed_secs: list[BlockNode]) -> dict[str, Metric]:
    gold_titles = {normalize_text(s.title): s for s in gold.sections if normalize_text(s.title)}
    if not gold_titles:
        return {}
    parsed_titles = {
        normalize_text(s.text): s for s in parsed_secs if s.text and normalize_text(s.text)
    }
    matched = set(gold_titles) & set(parsed_titles)
    recall = len(matched) / len(gold_titles) if gold_titles else 1.0
    precision = len(matched) / len(parsed_titles) if parsed_titles else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    rows = {
        "section_hierarchy_f1": Metric(
            f1, len(gold_titles), len(parsed_titles), "title-match F1 (gold vs parsed headings)"
        ),
    }
    # depth accuracy is defined only over matched titles — when nothing matched there is no depth to
    # score, so OMIT the row rather than report a vacuous 1.0 that rises as heading-matching gets
    # worse (the same vacuous-1.0 trap already avoided on number-binding; review trust-gap #2).
    if matched:
        depth_hits = sum(
            1
            for t in matched
            if gold_titles[t].level == _PARSED_LEVEL.get(parsed_titles[t].type, -1)
        )
        rows["section_depth_acc"] = Metric(
            depth_hits / len(matched), len(matched), len(matched), "issue 0004 — nesting level"
        )
    return rows


def _score_captions(gold: GoldDoc, parsed_caps: list[BlockNode]) -> dict[str, Metric]:
    n_gold = len(gold.captions)
    if not n_gold:
        return {}
    recall = min(len(parsed_caps), n_gold) / n_gold
    # best-text-match each gold caption to a parsed caption
    pool = [c.text or "" for c in parsed_caps]
    sims = [max((text_similarity(g.text, p) for p in pool), default=0.0) for g in gold.captions]
    sim = sum(sims) / len(sims)
    return {
        "caption_recall": Metric(recall, n_gold, len(parsed_caps), "count recall"),
        "caption_text_sim": Metric(sim, n_gold, len(parsed_caps), "best-match text sim"),
    }


def _score_xref(gold: GoldDoc, ref_kinds: Counter) -> dict[str, Metric]:
    gold_kinds = Counter(x.kind for x in gold.xrefs if x.kind != "unknown")
    if not gold_kinds:  # nothing to score — omit rather than score a vacuous 1.0
        return {}
    recalls = [min(ref_kinds.get(k, 0), n) / n for k, n in gold_kinds.items()]
    return {
        "xref_kind_recall": Metric(
            sum(recalls) / len(recalls),
            sum(gold_kinds.values()),
            sum(ref_kinds.values()),
            "validates xref.py (count recall/kind)",
        )
    }


def _score_citations(gold: GoldDoc, n_refs: int) -> dict[str, Metric]:
    n_gold = len(gold.citations)
    # gate on the bib pass: the structural parse creates no reference nodes (that's GROBID's job),
    # so without it there is nothing to score — omit rather than report a misleading ~0.
    if not n_gold or n_refs == 0:
        return {}
    recall = min(n_refs, n_gold) / n_gold
    return {
        "citation_recall": Metric(recall, n_gold, n_refs, "issue 0006 — reference-count recall")
    }


def _recall(gold_chems, surfaces: set[str], canons: set[str]) -> int:
    """How many gold formulas are covered by a surface/canonical set (canonical unifies 0.5/0.50)."""
    return sum(
        1 for c in gold_chems if c.surface in surfaces or (c.canonical and c.canonical in canons)
    )


def _score_chemicals(gold: GoldDoc, root: BlockNode, pdf_path=None) -> dict[str, Metric]:
    """Three views of chemistry fidelity, gold (LaTeX-source) as the ruler:

    1. ``chem_formula_recall`` — did the formula survive *verbatim* in the parsed text? An
       extractor-independent measure of Docling's text fidelity (Issue 0009 headline; ~0.13).
    2. ``chem_extract_recall`` — of those, how many does the precision-gated chemistry pass recover as
       material entities (bounded above by 1)?
    3. ``chem_recover_recall`` — adds **glyph recovery**: formulas Docling dropped but that are live
       text in the PDF, read back from the glyph layer. Only scored when the source ``pdf_path`` is
       available. This is the row the recovery pass moves.
    """
    if not gold.chemicals:
        return {}
    # normalise any Unicode subscripts the parse may carry (Mo₈₉ -> Mo89) so they match the
    # ASCII-digit gold surface; gold is already inline-digit form.
    # Survival is a region-agnostic text-fidelity check → full blob; extraction mirrors the parse
    # pass, which skips non-technical regions (ADR-0006) → technical-only blob, so the eval measures
    # the same input domain `tag_materials` tags over.
    blob = normalize_subscripts(tree_text(root))
    tech_blob = normalize_subscripts(tree_text(root, exclude_ids=nontechnical_section_ids(root)))
    n_gold = len(gold.chemicals)

    preserved = sum(
        1
        for c in gold.chemicals
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(c.surface)}(?![A-Za-z0-9])", blob, re.IGNORECASE)
    )

    found = extract_materials(tech_blob)
    surf = {m["surface"] for m in found}
    canon = {m["canonical"] for m in found if m["canonical"]}
    extracted = _recall(gold.chemicals, surf, canon)

    rows = {
        "chem_formula_recall": Metric(
            preserved / n_gold, n_gold, preserved, "issue 0009 — formula survives parse text"
        ),
        "chem_extract_recall": Metric(
            extracted / n_gold, n_gold, len(found), "gated pass over surviving text"
        ),
    }

    if pdf_path and Path(pdf_path).exists():
        recovered = find_dropped_formulas(root, str(pdf_path))
        surf |= {m["surface"] for m in recovered}
        canon |= {m["canonical"] for m in recovered if m["canonical"]}
        rows["chem_recover_recall"] = Metric(
            _recall(gold.chemicals, surf, canon) / n_gold,
            n_gold,
            len(found) + len(recovered),
            "issue 0009 — + glyph recovery of dropped text",
        )
    return rows


def _score_title(gold: GoldDoc, parsed_title: str | None) -> dict[str, Metric]:
    if not gold.title:
        return {}
    return {"title_sim": Metric(text_similarity(gold.title, parsed_title), 1, 1, "issue 0008")}


def _score_authors(gold: GoldDoc, parsed_authors: list[str]) -> dict[str, Metric]:
    # gate on the bib pass: authors come from GROBID, not the structural parse. No parsed authors
    # => the bib stage didn't run => nothing this stage is responsible for. Omit.
    if not gold.authors or not parsed_authors:
        return {}
    blob = normalize_text(" ; ".join(parsed_authors))
    hits = 0
    for a in gold.authors:
        surname = normalize_text(a).split()[-1] if normalize_text(a) else ""
        if surname and surname in blob:
            hits += 1
    return {
        "author_recall": Metric(
            hits / len(gold.authors), len(gold.authors), len(parsed_authors), "surname match"
        )
    }


def score_tree(gold: GoldDoc, root: BlockNode, pdf_path=None) -> Scorecard:
    """Score one parsed tree against its gold; returns the per-field :class:`Scorecard`. ``pdf_path``
    (the source PDF) lights up the ``chem_recover_recall`` row — glyph recovery of dropped formulas."""
    title, eqs, secs, caps, authors, ref_kinds, n_refs = _collect(root)
    card = Scorecard()
    card.rows.update(_score_title(gold, title))
    card.rows.update(_score_authors(gold, authors))
    card.rows.update(_score_sections(gold, secs))
    card.rows.update(_score_equations(gold, eqs))
    card.rows.update(_score_xref(gold, ref_kinds))
    card.rows.update(_score_citations(gold, n_refs))
    card.rows.update(_score_captions(gold, caps))
    card.rows.update(_score_chemicals(gold, root, pdf_path))
    return card


def mean_scorecard(cards: list[Scorecard]) -> Scorecard:
    """Average several papers' scorecards row-wise (corpus-level scorecard). A row is averaged over
    only the papers that *have* it — some fields don't apply to every paper (a paper with no
    equations omits the equation rows; one with no chemistry omits ``chem_formula_recall``) — so the
    key set is the **union** across cards, in first-seen order, not just the first card's."""
    agg = Scorecard()
    if not cards:
        return agg
    keys = list(dict.fromkeys(k for c in cards for k in c.rows))  # union, order-preserving
    for k in keys:
        ms = [c.rows[k] for c in cards if k in c.rows]
        agg.rows[k] = Metric(
            score=sum(m.score for m in ms) / len(ms),
            gold_n=sum(m.gold_n for m in ms),
            parsed_n=sum(m.parsed_n for m in ms),
            note=ms[0].note,
        )
    return agg
