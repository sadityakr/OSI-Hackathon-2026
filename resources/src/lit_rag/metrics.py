"""Retrieval metrics for the evaluation harness.

The metric is the contract: it turns "is retrieval good?" into a number an agent can optimize
against without supervision. recall@k is the day-one baseline; a provenance-aware metric (does the
retrieved unit support the claim, and is abstention preferred to a thin fabrication?) is the real
target — see `docs/research/provenance-aware-evaluation.md`. Keep these pure and well-tested.
"""

from __future__ import annotations

from collections.abc import Iterable


def recall_at_k(retrieved: Iterable[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of `relevant` documents present in the top-`k` of `retrieved`.

    Returns 1.0 when there are no relevant documents (nothing to miss).
    """
    relevant = set(relevant)
    if not relevant:
        return 1.0
    top_k = list(retrieved)[:k]
    found = sum(1 for doc_id in relevant if doc_id in top_k)
    return found / len(relevant)
