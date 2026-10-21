"""Identifiers — the two handles every node carries (design §2).

* **content_hash(pdf_bytes)** — the document's content-addressed key, used as the ``citable_key``
  until a DOI is resolved (M6). Stable across re-parses of the same bytes; it names the
  ``output/parsed/<hash>/`` directory and the document-root id.
* **PathBuilder** — assigns human-readable, root-relative *path ids* (``sec2/sub1/p3``, ``fig4``)
  that encode tree position. Path ids are stable only *within one parse*; durable corpus-wide joins
  use the DOI + physical provenance, never the path string (design §2).
"""

from __future__ import annotations

import hashlib

# A short, collision-safe slice of the sha256 hex digest — long enough to be unique across a corpus
# of tens of thousands of papers, short enough to read in a path.
_HASH_LEN = 16


def content_hash(pdf_bytes: bytes) -> str:
    """Content-addressed id for a source document: ``sha256``-derived, hex, truncated."""
    return hashlib.sha256(pdf_bytes).hexdigest()[:_HASH_LEN]


# Short per-type segment prefixes for readable path ids.
TYPE_PREFIX: dict[str, str] = {
    "chapter": "ch",
    "section": "sec",
    "subsection": "sub",
    "paragraph": "p",
    "figure": "fig",
    "caption": "cap",
    "table": "tab",
    "equation": "eq",
    "footnote": "fn",
    "list": "list",
    "list-item": "li",
    "author": "au",
    "affiliation": "aff",
    "funding": "fund",
    "acknowledgement": "ack",
    "supplementary-material": "supp",
    "dataset": "data",
    "data-availability": "davail",
    "reference": "ref",
}


class PathBuilder:
    """Hands out unique, hierarchical path ids during a single tree build.

    Each container opens a new namespace; per-type counters within a namespace give ``sec2``,
    ``p3``, ``fig4`` … A child's full id is ``<parent_id>/<segment>``. The document root holds the
    ``citable_key`` and is *not* prefixed onto its children here — callers pass the root id as the
    base so ids read ``<citable_key>/sec2/p3``.
    """

    def __init__(self, base_id: str) -> None:
        self._base = base_id
        # one counter table per parent path -> {type_prefix: next_index}
        self._counters: dict[str, dict[str, int]] = {}

    def child(self, parent_id: str, node_type: str) -> str:
        prefix = TYPE_PREFIX.get(node_type, node_type)
        table = self._counters.setdefault(parent_id, {})
        idx = table.get(prefix, 0) + 1
        table[prefix] = idx
        return f"{parent_id}/{prefix}{idx}"
