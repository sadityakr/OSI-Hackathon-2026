"""Parsing-eval harness — intrinsic, gold-from-authoring-source.

Mints a structured answer key from LaTeX source (+ compiled .aux) and scores a parsed BlockNode tree
against it, per failure mode. Offline and gate-safe (no torch / no network). See
docs/research/parsing-eval-harness.md.
"""

from lit_rag.parseval.gold import GoldDoc, extract_gold
from lit_rag.parseval.score import Scorecard, mean_scorecard, score_tree

__all__ = ["GoldDoc", "extract_gold", "Scorecard", "score_tree", "mean_scorecard"]
