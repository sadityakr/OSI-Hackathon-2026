"""Keyword extraction for the lexical channel (ADR-0015, resolving Issue 0014).

The lexical channel exists to match the *exact discriminating tokens* embeddings blur (CrSBr vs CrCl3;
ADR-0008). But `websearch_to_tsquery` **AND-s** every term, so a long natural-language question
(~20 terms) becomes a conjunction no chunk satisfies — the channel goes silent and hybrid degrades to
semantic (Issue 0014). The fix is query-side: feed the lexical channel a short list of *salient* terms
(OR-combined downstream), while the semantic channel keeps the full question.

Deliberately a **deterministic heuristic, not an LLM**: retrieval is the hot path, so this stays fast,
pure, and offline-testable — no per-query model call on the untestable side of the seam. It preserves
the tokens the lexical channel is *for* (chemical formulae, compounds, acronyms — anything alphanumeric
survives whole) and drops interrogative/scaffolding words + bare numbers that carry no retrieval signal.
Postgres's own `english` config strips its standard stopwords too; this list only adds the
question-scaffolding words that config keeps.
"""

from __future__ import annotations

import re

# Interrogative + generic research/measurement scaffolding that the Postgres `english` config does NOT
# treat as stopwords but that carry little discriminating signal in a scientific query. Kept lean —
# over-dropping loses recall; the OR-combine + ts_rank_cd downstream tolerate a few generic survivors.
_STOPWORDS = frozenset(
    {
        "what",
        "how",
        "why",
        "which",
        "who",
        "when",
        "where",
        "whose",
        "whom",
        "does",
        "do",
        "did",
        "done",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "for",
        "to",
        "and",
        "or",
        "with",
        "by",
        "at",
        "from",
        "as",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "their",
        "them",
        "there",
        "using",
        "use",
        "used",
        "uses",
        "study",
        "studies",
        "studied",
        "paper",
        "passage",
        "work",
        "measured",
        "measure",
        "measurement",
        "observed",
        "observe",
        "report",
        "reported",
        "reports",
        "show",
        "shown",
        "shows",
        "reveal",
        "revealed",
        "reveals",
        "demonstrate",
        "demonstrated",
        "between",
        "versus",
        "vs",
        "compared",
        "compare",
        "comparison",
        "under",
        "into",
        "within",
        "via",
        "across",
        "both",
        "one",
        "two",
        "first",
        "second",
        "different",
        "distinct",
        "dependence",
        "depend",
        "depends",
        "effect",
        "effects",
        "role",
        "given",
        "make",
        "makes",
        "why",
        "such",
        "than",
        "over",
        "about",
        "can",
        "would",
        "should",
        "were",
        "here",
        "each",
    }
)

_TOKEN = re.compile(r"[a-z0-9]+")
_ALLDIGITS = re.compile(r"\d+$")


def extract_keywords(query: str) -> list[str]:
    """Salient lexical-search terms from a query, order-preserving and de-duplicated.

    Keeps alphanumeric tokens whole (so ``Fe3GeTe2`` / ``CoFeB`` survive), drops single characters,
    bare numbers (years, counts, indices — not discriminating), and scaffolding stopwords. A short
    keyword query reduces to (nearly) itself; a long NL question collapses to its content terms.
    """
    seen: set[str] = set()
    out: list[str] = []
    for tok in _TOKEN.findall(query.lower()):
        if len(tok) < 2 or _ALLDIGITS.match(tok) or tok in _STOPWORDS or tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return out
