"""Reciprocal Rank Fusion — combine several ranked retrieval channels into one (hybrid retrieval).

Hybrid retrieval (design §5.2) runs a query through a **semantic** channel (SciNCL/ANN) and a
**lexical** channel (Postgres full-text search) and must merge their two orderings. The channels
score on *incomparable scales* — cosine distance vs ``ts_rank`` — so a weighted score sum needs a
normalization + a tunable weight the design doc explicitly lists as open ("how to weight the semantic
and lexical channels"). **RRF sidesteps that entirely:** it fuses on *rank position*, not score, so no
normalization and no weight to tune. An item's fused score is the sum over channels of
``1/(rrf_k + rank)``; an item that ranks well in *both* channels beats one that ranks highly in only
one — which is exactly the behaviour we want (a chunk that is both semantically near *and* contains the
exact query token should win).

Pure and offline by design — no DB, no model. Keeping the fusion math here (not in a SQL query) means
the interesting logic is covered by ``make check``; only the per-channel SELECTs are live-SQL, the
surface the offline gate can't reach (the lesson of Issue 0013). ``ingest.py`` supplies the channels.
"""

from __future__ import annotations

from typing import Callable, Hashable, Sequence

# Canonical RRF constant (Cormack, Clarke & Buettcher, SIGIR 2009): big enough that the very top rank
# doesn't dominate absolutely, small enough that rank still matters. Rarely worth tuning.
DEFAULT_RRF_K = 60


def rrf_fuse(
    channels: Sequence[Sequence[dict]],
    *,
    k: int,
    id_of: Callable[[dict], Hashable],
    rrf_k: int = DEFAULT_RRF_K,
) -> list[dict]:
    """Fuse ranked hit-lists by Reciprocal Rank Fusion and return the top ``k`` merged hits.

    Args:
        channels: one hit-list per channel, **each already sorted best-first**. A hit is a dict.
        k: how many fused hits to return.
        id_of: maps a hit to its stable identity. Hits with equal ids across channels are the *same*
            item and are merged (their reciprocal-rank contributions add). The merged dict is taken
            from the first channel the item appears in.
        rrf_k: the RRF constant (see :data:`DEFAULT_RRF_K`).

    Returns:
        The top ``k`` merged hits, each a shallow copy of its source dict annotated with
        ``rrf_score`` (float, higher is better) and ``channel_ranks`` (``{channel_index: 1-based
        rank}``) for transparency. Deterministic: ties break toward the item seen first (stable sort).
    """
    scores: dict[Hashable, float] = {}
    ranks: dict[Hashable, dict[int, int]] = {}
    merged: dict[Hashable, dict] = {}
    order: list[Hashable] = []  # first-seen order, for stable tie-breaking

    for ci, channel in enumerate(channels):
        for rank, hit in enumerate(channel, start=1):
            hid = id_of(hit)
            if hid not in scores:
                scores[hid] = 0.0
                ranks[hid] = {}
                merged[hid] = hit
                order.append(hid)
            scores[hid] += 1.0 / (rrf_k + rank)
            ranks[hid][ci] = rank

    ranked = sorted(
        order, key=lambda h: scores[h], reverse=True
    )  # stable: ties keep first-seen order
    out: list[dict] = []
    for hid in ranked[:k]:
        hit = dict(merged[hid])
        hit["rrf_score"] = scores[hid]
        hit["channel_ranks"] = ranks[hid]
        out.append(hit)
    return out
