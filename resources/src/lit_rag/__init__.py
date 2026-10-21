"""Literature RAG — provenance-first retrieval over the AG Kläui scientific corpus.

Pipeline (implemented): parse (typed block tree, `parsing/`) -> chunk (search small, resolve
large) -> embed (SciNCL) -> hybrid index (Postgres FTS + pgvector, RRF-fused, `store/`) -> serve
(MCP tool layer). The defining commitment is provenance: every surfaced claim carries a locatable
citation, and abstention is cheaper than fabrication. See `docs/design/retrieval-for-science.md`
for the design spine.

``__version__`` is also the ``parser_version`` stamped onto every parse artifact and chunk row
(derived-data provenance) — bump it when a pipeline change makes existing artifacts stale.
"""

__version__ = "0.1.0"
