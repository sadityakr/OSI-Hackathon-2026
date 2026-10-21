"""Paper-graph visualizer — a standalone *side tool*, not part of the parse/embed/serve pipeline.

It reads a persisted ``tree.json`` (the parser's single source of truth) and projects it into an
Obsidian-style force-directed graph rendered in the browser: structural containment as the
backbone, plus the parser's already-resolved cross-references (``cites``, ``references-figure``…)
as the cross-links that give the paper its real shape.

This package only *reads* the parse artifact — it never imports the parsing/store pipeline — so it
can ship and be called independently (``python -m lit_rag.viz``).
"""

from .graph import build_graph

__all__ = ["build_graph"]
