"""CLI for the paper-graph visualizer — a standalone side tool.

    python -m lit_rag.viz <parsed-dir-or-tree.json> [--out FILE] [--max-tokens 800] [--publish NAME]

``--publish NAME`` also copies the HTML into the artifact-review serve root
(``/data/aditya/artifacts/NAME.html``) so it is reachable over the existing localhost:8765 tunnel
without standing up a second server. With no ``--out`` it writes next to the parsed tree.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .figures import embed_figures
from .graph import build_graph
from .render import render_html

_ARTIFACT_ROOT = Path("/data/aditya/artifacts")


def _resolve_tree(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        cand = p / "tree.json"
        if not cand.exists():
            sys.exit(f"no tree.json in {p}")
        return cand
    if p.is_file():
        return p
    sys.exit(f"not found: {arg}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m lit_rag.viz", description=__doc__)
    ap.add_argument("source", help="a parsed output dir (containing tree.json) or a tree.json file")
    ap.add_argument("--out", help="output HTML path (default: <dir>/graph.html)")
    ap.add_argument("--max-tokens", type=int, default=800, help="text cap per node (default 800)")
    ap.add_argument(
        "--fig-px",
        type=int,
        default=720,
        help="longest side of inlined figure thumbnails (default 720; 0 disables figures)",
    )
    ap.add_argument(
        "--publish",
        metavar="NAME",
        help="also copy to /data/aditya/artifacts/NAME.html (served on localhost:8765)",
    )
    args = ap.parse_args(argv)

    tree_path = _resolve_tree(args.source)
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    graph = build_graph(tree, max_tokens=args.max_tokens)
    n_figs = 0
    if args.fig_px > 0:
        n_figs = embed_figures(graph, tree_path.parent, max_px=args.fig_px)
    else:
        for node in graph["nodes"]:
            node.pop("image", None)
    html = render_html(graph)

    out = Path(args.out) if args.out else tree_path.parent / "graph.html"
    out.write_text(html, encoding="utf-8")
    m = graph["meta"]
    size_mb = out.stat().st_size / 1e6
    print(
        f"graph: {m['n_nodes']} nodes · {m['n_links']} links · {n_figs} figures  ->  {out} ({size_mb:.1f} MB)"
    )

    if args.publish:
        _ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        dest = _ARTIFACT_ROOT / f"{args.publish}.html"
        shutil.copyfile(out, dest)
        print(f"published -> {dest}")
        print(f"  open:   http://127.0.0.1:8765/{args.publish}.html")
        print("  tunnel: ssh -L 8765:localhost:8765 Laufey")


if __name__ == "__main__":
    main()
