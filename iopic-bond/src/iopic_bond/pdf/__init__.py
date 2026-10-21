"""PDF parsing and figure extraction (ported and trimmed from an internal literature pipeline).

Public surface:

* ``parse_pdf(pdf_path, out_dir)`` -> document-root ``BlockNode``; writes tree.json, text.txt,
  paper.md and figures/ under ``<out_dir>/<content_hash>/``. Requires ``docling``.
* ``schema`` (``BlockNode``, ``Provenance``, ``Edge``, ``to_json``/``from_json``): Docling-free.
"""
from __future__ import annotations

from .schema import BlockNode, Edge, Provenance, from_json, to_json

__all__ = ["BlockNode", "Edge", "Provenance", "to_json", "from_json", "parse_pdf"]


def parse_pdf(pdf_path, out_dir, **kwargs):
    from .pipeline import parse_pdf as _parse_pdf

    return _parse_pdf(pdf_path, out_dir, **kwargs)
