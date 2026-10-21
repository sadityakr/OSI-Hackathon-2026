"""Deterministic parse-QA — the machine-checkable half of "did parsing go well?".

Two layers, both run against a parsed ``<out_dir>/<hash>/`` directory:

* **Tree invariants** (parsing-implementation-plan §5) — every located leaf has provenance, ids are
  unique, ``page_no`` in range, ``tree.json`` round-trips, every intra-document edge target exists.
* **Markdown-render checks** — every figure embed resolves to a file on disk, ``$$`` blocks are
  balanced, headings exist and don't skip levels, and the text shows no classic PDF-extraction
  artifacts (``cid:`` glyphs, replacement chars). Optionally a coverage ratio vs ``pdftotext`` to
  catch wholesale dropped body text.

This is the objective signal a Haiku reviewer's semantic spot-check sits *on top of*: cheap
deterministic checks first, the LLM only for what can't be checked mechanically.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .schema import BlockNode, from_json, to_json

_EMBED_RE = re.compile(r"!\[\[([^\]]+)\]\]")  # ![[figures/figN.png]]
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")  # ![alt](path)
_HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)


@dataclass
class Issue:
    check: str
    severity: str  # "error" | "warn"
    detail: str


@dataclass
class QAReport:
    doc_dir: str
    issues: list[Issue]
    stats: dict

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        n_err = len(self.errors)
        n_warn = len(self.issues) - n_err
        head = f"{'PASS' if self.ok else 'FAIL'}  {self.doc_dir}  ({n_err} errors, {n_warn} warns)"
        lines = [head, "  stats: " + ", ".join(f"{k}={v}" for k, v in self.stats.items())]
        for i in self.issues:
            mark = "✗" if i.severity == "error" else "•"
            lines.append(f"  {mark} [{i.check}] {i.detail}")
        return "\n".join(lines)


# --- tree invariants ----------------------------------------------------------------------------


def _check_tree(root: BlockNode, n_pages: int | None, issues: list[Issue], stats: dict) -> None:
    nodes = list(root.walk())
    stats["nodes"] = len(nodes)

    ids = [n.id for n in nodes]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        issues.append(Issue("ids-unique", "error", f"duplicate ids: {sorted(dupes)[:5]}"))

    # "reference" nodes are GROBID-derived back-matter entities with no Docling coordinates by
    # design (two-stream alignment is issue 0002) — exempt, so QA can run on an enriched tree.
    missing_prov = [
        n.id
        for n in nodes
        if n.type not in ("document", "reference") and not n.is_container() and not n.prov
    ]
    if missing_prov:
        issues.append(
            Issue(
                "leaf-provenance",
                "error",
                f"{len(missing_prov)} located leaves without provenance, e.g. {missing_prov[:3]}",
            )
        )

    if n_pages:
        bad_pages = [
            (n.id, p.page_no) for n in nodes for p in n.prov if not (1 <= p.page_no <= n_pages)
        ]
        if bad_pages:
            issues.append(
                Issue(
                    "page-in-range",
                    "error",
                    f"{len(bad_pages)} prov page_no outside [1,{n_pages}], e.g. {bad_pages[:3]}",
                )
            )

    id_set = set(ids)
    dangling = [
        (n.id, e.type, e.target)
        for n in nodes
        for e in n.edges
        if e.type
        in (
            "caption-of",
            "references-figure",
            "references-table",
            "references-section",
            "references-equation",
        )
        and e.target not in id_set
    ]
    if dangling:
        issues.append(
            Issue(
                "edge-targets",
                "error",
                f"{len(dangling)} intra-doc edges point at missing nodes, e.g. {dangling[:3]}",
            )
        )

    empty_paras = [n.id for n in nodes if n.type == "paragraph" and not (n.text or "").strip()]
    if empty_paras:
        issues.append(
            Issue("nonempty-paragraphs", "warn", f"{len(empty_paras)} empty paragraph nodes")
        )

    # round-trip
    if from_json(to_json(root)) != root:
        issues.append(Issue("round-trip", "error", "from_json(to_json(tree)) != tree"))

    # the pass ledger must be CLEAN, not merely present (review F6): _run_pass records an erroring
    # enrichment pass and continues — right for one bad PDF, but without this check a pass failing
    # corpus-wide produced N "successful" trees whose only symptom was a field nobody read.
    passes = root.attrs.get("passes") or {}
    bad = {k: v for k, v in passes.items() if not (v == "ok" or str(v).startswith("skipped"))}
    if bad:
        issues.append(Issue("passes-clean", "error", f"enrichment passes failed: {bad}"))

    stats["figures"] = sum(1 for n in nodes if n.type == "figure")
    stats["equations"] = sum(1 for n in nodes if n.type == "equation")
    stats["sections"] = sum(1 for n in nodes if n.type in ("chapter", "section", "subsection"))


# --- text-stream / char-span integrity ------------------------------------------------------------


def _check_text_stream(root: BlockNode, doc_dir: Path, issues: list[Issue], stats: dict) -> None:
    """The provenance keystone: ``text.txt`` must be the tree's replayed projection, spans must agree.

    Every text-mutating pass is obliged to restore this invariant (``rebuild_text_stream``); it holds
    by convention, so QA is where a pass that forgot becomes a loud failure instead of silently
    corrupt char-span provenance downstream. Three checks against the replayed stream: (1) the
    on-disk ``text.txt`` matches it byte-for-byte, (2) every node's ``char_span`` equals its replayed
    span, (3) every ``cites`` edge's ``marker_span`` still slices to a bracket marker.
    """
    from .citation_normalize import replay_text_stream
    from .schema import REGION_ONLY_SPAN

    expected, spans = replay_text_stream(root)
    stats["text_chars"] = len(expected)

    txt_path = doc_dir / "text.txt"
    if not txt_path.exists():
        issues.append(Issue("text-stream", "error", "text.txt missing"))
    else:
        on_disk = txt_path.read_text(encoding="utf-8")
        if on_disk != expected:
            issues.append(
                Issue(
                    "text-stream",
                    "error",
                    f"text.txt is stale — differs from the tree's replayed projection "
                    f"({len(on_disk)} vs {len(expected)} chars)",
                )
            )

    bad_spans = [
        n.id
        for n in root.walk()
        if n is not root
        and n.prov
        and any(tuple(p.char_span) not in (spans[n.id], REGION_ONLY_SPAN) for p in n.prov)
    ]
    if bad_spans:
        issues.append(
            Issue(
                "char-spans",
                "error",
                f"{len(bad_spans)} nodes' char_span disagrees with the replayed stream, "
                f"e.g. {bad_spans[:3]}",
            )
        )

    bad_markers = [
        (n.id, e.target)
        for n in root.walk()
        for e in n.edges
        if e.type == "cites"
        and e.marker_span is not None
        and not (
            0 <= e.marker_span[0] < e.marker_span[1] <= len(expected)
            and expected[e.marker_span[0]] == "["
            and expected[e.marker_span[1] - 1] == "]"
        )
    ]
    if bad_markers:
        issues.append(
            Issue(
                "cite-markers",
                "error",
                f"{len(bad_markers)} cites marker_spans no longer slice to a [..] marker, "
                f"e.g. {bad_markers[:3]}",
            )
        )


# --- markdown render checks ---------------------------------------------------------------------


def _check_markdown(doc_dir: Path, issues: list[Issue], stats: dict) -> str:
    md_path = doc_dir / "paper.md"
    if not md_path.exists():
        issues.append(Issue("md-exists", "error", "paper.md missing"))
        return ""
    md = md_path.read_text(encoding="utf-8")
    stats["md_words"] = len(md.split())
    if len(md.strip()) < 50:
        issues.append(Issue("md-nonempty", "error", "paper.md is essentially empty"))

    embeds = _EMBED_RE.findall(md) + _MD_IMG_RE.findall(md)
    stats["md_embeds"] = len(embeds)
    missing = [e for e in embeds if not (doc_dir / e).exists()]
    if missing:
        issues.append(
            Issue(
                "embed-targets",
                "error",
                f"{len(missing)} figure embeds point at missing files, e.g. {missing[:3]}",
            )
        )

    if md.count("$$") % 2 != 0:
        issues.append(Issue("equation-balance", "error", "odd number of $$ delimiters"))

    headings = _HEADING_RE.findall(md)
    if not headings:
        issues.append(Issue("headings-present", "warn", "no Markdown headings found"))
    else:
        levels = [len(h) for h in headings]
        jumps = sum(1 for a, b in zip(levels, levels[1:]) if b - a >= 2)
        if jumps:
            issues.append(
                Issue("heading-jumps", "warn", f"{jumps} heading-level skips (e.g. ## -> ####)")
            )

    cids = md.count("(cid:")
    repl = md.count("�")
    if cids:
        issues.append(
            Issue("artifact-cid", "warn", f"{cids} '(cid:' glyph artifacts (font-decode loss)")
        )
    if repl:
        issues.append(Issue("artifact-replacement", "warn", f"{repl} U+FFFD replacement chars"))
    return md


def _coverage_vs_pdftotext(pdf_path: Path, md_words: int, issues: list[Issue], stats: dict) -> None:
    if not pdf_path or not pdf_path.exists() or not shutil.which("pdftotext"):
        return
    try:
        out = subprocess.run(
            ["pdftotext", "-q", str(pdf_path), "-"], capture_output=True, text=True, timeout=120
        )
    except Exception:
        return
    pdf_words = len(out.stdout.split())
    stats["pdf_words"] = pdf_words
    if pdf_words > 0:
        ratio = md_words / pdf_words
        stats["coverage"] = round(ratio, 2)
        if ratio < 0.6:
            issues.append(
                Issue(
                    "coverage",
                    "warn",
                    f"paper.md has {ratio:.0%} of pdftotext words — possible dropped body text",
                )
            )


def page_slices(root: BlockNode) -> dict[int, list[BlockNode]]:
    """Group located leaf nodes by the page their first provenance sits on (reading order).

    Used to build a *page-scoped* review bundle for a Haiku spot-check of a large document: rather
    than read all 282 pages, sample a handful of pages and compare each PDF page against the nodes
    the parser placed on it.
    """
    slices: dict[int, list[BlockNode]] = {}
    for n in root.walk():
        if n.prov and not n.is_container():
            slices.setdefault(n.prov[0].page_no, []).append(n)
    return slices


def qa_report(doc_dir, pdf_path=None) -> QAReport:
    """Run all deterministic checks on a parsed ``<hash>/`` directory."""
    doc_dir = Path(doc_dir)
    issues: list[Issue] = []
    stats: dict = {}

    tree_path = doc_dir / "tree.json"
    if not tree_path.exists():
        issues.append(Issue("tree-exists", "error", "tree.json missing"))
        return QAReport(str(doc_dir), issues, stats)

    root = from_json(tree_path.read_text(encoding="utf-8"))
    n_pages = root.attrs.get("n_pages")
    _check_tree(root, n_pages, issues, stats)
    _check_text_stream(root, doc_dir, issues, stats)
    md_words = _check_markdown(doc_dir, issues, stats).split()
    # captions live in the per-figure notes, not paper.md — count them so coverage stays truthful
    fig_dir = doc_dir / "figures"
    note_words = (
        sum(len(p.read_text(encoding="utf-8").split()) for p in fig_dir.glob("*.md"))
        if fig_dir.exists()
        else 0
    )
    if note_words:
        stats["note_words"] = note_words
    _coverage_vs_pdftotext(
        Path(pdf_path) if pdf_path else None, len(md_words) + note_words, issues, stats
    )
    return QAReport(str(doc_dir), issues, stats)
