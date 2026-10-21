"""Parsing layer — PDF -> canonical ``BlockNode`` tree -> projections (design: parsing-layer.md).

One fixed contract (``schema.BlockNode``) fed by replaceable adapters. Both halves are implemented:
the *structural* half (ADR-0002: Docling adapter + normalization passes + Markdown render) and the
*bibliographic* half (ADR-0003/0005: ``grobid_adapter`` — GROBID enrichment + CrossRef
ref-consolidation). The store projection (ADR-0004) lives in :mod:`lit_rag.store`.

Public surface:

* ``parse_pdf(pdf_path, out_dir)`` — parse one PDF into ``<out_dir>/<hash>/{tree.json, text.txt,
  paper.md, figures/}`` and return the document-root ``BlockNode``.
* ``schema`` — the IR (``BlockNode``, ``Provenance``, ``Edge``, ``to_json``/``from_json``).
"""

from __future__ import annotations

from .schema import BlockNode, Edge, Provenance, from_json, to_json

__all__ = ["BlockNode", "Edge", "Provenance", "to_json", "from_json", "parse_pdf"]


def parse_pdf(pdf_path, out_dir, **kwargs):
    """Parse ``pdf_path`` into the canonical tree + projections under ``out_dir``.

    Thin orchestrator; the real work lives in ``pipeline.parse_pdf``. Imported lazily so that
    ``import lit_rag.parsing`` (and the schema) stays cheap and Docling-free for callers that only
    need the IR.
    """
    from .pipeline import parse_pdf as _parse_pdf

    return _parse_pdf(pdf_path, out_dir, **kwargs)
