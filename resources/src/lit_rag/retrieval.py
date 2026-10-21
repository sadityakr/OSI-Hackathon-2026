"""Baseline retriever: rank documents by keyword overlap with the query.

Intentionally the simplest thing that produces a real recall@k number, so the evaluation loop is
meaningful immediately. It will be replaced by hybrid SciNCL (semantic) + BM25 (lexical) retrieval
with a paper-importance prior that *orders but never hides* dissent; keep the `search` interface
stable as that happens so the eval harness keeps working unchanged.
"""

from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class KeywordRetriever:
    """Rank corpus documents by the number of tokens they share with the query."""

    def __init__(self, corpus: dict[str, str]) -> None:
        self._tokens = {doc_id: _tokenize(text) for doc_id, text in corpus.items()}

    def search(self, query: str, k: int = 5) -> list[str]:
        """Return the ids of the top-`k` documents, most relevant first (score > 0 only)."""
        q = _tokenize(query)
        scored = ((doc_id, len(q & toks)) for doc_id, toks in self._tokens.items())
        ranked = sorted(scored, key=lambda kv: kv[1], reverse=True)
        return [doc_id for doc_id, score in ranked[:k] if score > 0]
