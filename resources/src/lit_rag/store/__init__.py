"""Storage projection (M5, ADR-0004) — PostgreSQL + pgvector.

Walks the canonical ``tree.json`` into three derived, regenerable projections: the **catalog** (one
row per citable node), the **cites** edge table (the corpus citation graph), and **chunks** (embedding
units with a pgvector HNSW index). Pure logic (:mod:`chunker`, :mod:`projection`) is offline-testable;
:mod:`db`, :mod:`embed`, :mod:`ingest` are thin adapters over the live server + SciNCL model.
"""

from __future__ import annotations

from .chunker import Chunk, iter_chunks
from .projection import catalog_row, cites_edges, reference_rows

__all__ = ["Chunk", "iter_chunks", "catalog_row", "cites_edges", "reference_rows"]
