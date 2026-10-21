"""Command-line entry to the parser — the one tool that turns a PDF into a vault + QA report.

    python -m lit_rag.parsing.cli parse data/samples/foo.pdf --out tmp/parsed
    python -m lit_rag.parsing.cli qa tmp/parsed/<hash> --pdf data/samples/foo.pdf

``parse`` writes ``<out>/<hash>/{tree.json,text.txt,paper.md,figures/}`` and prints the hash;
``qa`` runs the deterministic checks and exits non-zero if any error-level check fails (so it can
gate a script or CI step).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _cmd_parse(args) -> int:
    from .pipeline import parse_pdf

    root = parse_pdf(args.pdf, args.out, do_formula=not args.no_formula, device=args.device)
    doc_dir = Path(args.out) / root.id
    print(f"parsed {Path(args.pdf).name} -> {doc_dir}")
    print(f"  title: {root.attrs.get('title')!r}")
    print(f"  pages: {root.attrs.get('n_pages')}")
    if args.qa:
        from .qa import qa_report

        report = qa_report(doc_dir, args.pdf)
        print(report.summary())
        return 0 if report.ok else 1
    return 0


def _cmd_bib(args) -> int:
    """Bibliographic Phase 1 (ADR-0005): enrich a parsed tree with the GROBID structure only —
    identity, reference nodes (GROBID's own DOIs), ``cites`` edges, abstract. **No CrossRef, no
    network beyond the local GROBID service** — DOI resolution is the separate, resumable Phase 2:
    ``python -m lit_rag.corpusops consolidate``.

    Needs GROBID (``make grobid-up``). Writes the enriched ``tree.json`` (citation count stripped —
    catalog-only) plus a ``catalog_signals.json`` sidecar that ``store ingest`` applies to the catalog.
    """
    import json
    import os

    from .grobid_adapter import (
        GrobidClient,
        collect_catalog_signals,
        enrich_tree,
        parse_tei,
        strip_catalog_only,
    )
    from .render import render_markdown
    from .schema import from_json, to_json

    doc_dir = Path(args.doc_dir)
    root = from_json((doc_dir / "tree.json").read_text(encoding="utf-8"))

    tei = GrobidClient(os.environ.get("GROBID_URL", "http://127.0.0.1:8070")).process_fulltext(
        Path(args.pdf).read_bytes()
    )
    gdoc = parse_tei(tei)
    enrich_tree(root, gdoc)
    # Citations were standardized to [N] at parse time (citation_normalize), so enrich_tree's bracket
    # resolver linked every style uniformly — no separate superscript pass needed here.
    n_cites = sum(1 for n in root.walk() for e in n.edges if e.type == "cites")
    print(f"  cites edges: {n_cites}")

    signals = collect_catalog_signals(root)
    (doc_dir / "catalog_signals.json").write_text(json.dumps(signals, indent=2), encoding="utf-8")

    strip_catalog_only(root)
    # Enrichment appended reference nodes (new text at the tree's tail), so text.txt must be rebuilt
    # or it goes stale as a projection of the tree. Body offsets are unchanged (references walk last);
    # QA's text-stream check enforces this invariant on every vault.
    from .citation_normalize import rebuild_text_stream

    text_txt = rebuild_text_stream(root)
    (doc_dir / "tree.json").write_text(to_json(root), encoding="utf-8")
    (doc_dir / "text.txt").write_text(text_txt, encoding="utf-8")
    (doc_dir / "paper.md").write_text(render_markdown(root), encoding="utf-8")

    n_refs = sum(1 for n in root.walk() if n.type == "reference")
    n_resolved = sum(1 for n in root.walk() if n.type == "reference" and n.attrs.get("doi"))
    print(f"enriched {doc_dir}")
    print(f"  doi: {root.attrs.get('doi')!r}  published: {root.attrs.get('published_date')!r}")
    print(f"  references: {n_refs} ({n_resolved} resolved, {n_refs - n_resolved} abstained)")
    print(f"  catalog signals: {len(signals)} -> catalog_signals.json")
    return 0


def _cmd_qa(args) -> int:
    from .qa import qa_report

    report = qa_report(args.doc_dir, args.pdf)
    print(report.summary())
    return 0 if report.ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lit_rag.parsing.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="parse a PDF into a vault dir")
    p.add_argument("pdf")
    p.add_argument("--out", default="tmp/parsed", help="output root (default: tmp/parsed)")
    p.add_argument(
        "--no-formula",
        action="store_true",
        help="skip the formula VLM — it is ~95%% of parse time (~2-3s/equation on GPU, the dominant "
        "cost). Off: structure, equation numbers, and Eq.(N) cross-refs are still recovered "
        "(from PDF glyphs, VLM-independent); only the equation LaTeX *body* is lost.",
    )
    p.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="run the models on cpu (default) or cuda (GPU, VRAM-capped)",
    )
    p.add_argument("--qa", action="store_true", help="run QA after parsing")
    p.set_defaults(func=_cmd_parse)

    b = sub.add_parser(
        "bib",
        help="Phase 1 bibliographic enrichment: GROBID only (Phase 2 = corpusops consolidate)",
    )
    b.add_argument("doc_dir", help="a parsed output/parsed/<hash> directory")
    b.add_argument("--pdf", required=True, help="the source PDF (GROBID re-reads it)")
    b.set_defaults(func=_cmd_bib)

    q = sub.add_parser("qa", help="run deterministic QA on a parsed dir")
    q.add_argument("doc_dir")
    q.add_argument("--pdf", default=None, help="source PDF for coverage check")
    q.set_defaults(func=_cmd_qa)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
