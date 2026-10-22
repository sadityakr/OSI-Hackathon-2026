"""litpick commands: open arXiv papers and look at their figures, without an MCP client.

Finds the repo (RAMANLENS_REPO, .claude-plugin/repo_root.txt in an installed plugin, or the folders
above this file), points the library at data/raw/iopic-bond, and runs the parse and figure
operations of the iopic-Bond server with search off. Prints one JSON object. view also writes a PNG
in the current folder for the model to read.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


def _plugin_root() -> Path | None:
    here = Path(__file__).resolve()
    # scripts / litpick / skills / <plugin root>
    if len(here.parents) > 3:
        root = here.parents[3]
        if (root / ".claude-plugin" / "plugin.json").is_file():
            return root
    return None


def _repo() -> Path:
    env = os.environ.get("RAMANLENS_REPO")
    if env:
        return Path(env).expanduser().resolve()
    plugin = _plugin_root()
    if plugin is not None:
        marker = plugin / ".claude-plugin" / "repo_root.txt"
        if marker.is_file():
            recorded = Path(marker.read_text(encoding="utf-8").strip()).expanduser()
            if (recorded / "iopic-bond" / "src").is_dir():
                return recorded.resolve()
        start: list[Path] = [plugin, *plugin.parents]
    else:
        start = list(Path(__file__).resolve().parents)
    for candidate in start:
        if (candidate / "iopic-bond" / "src").is_dir() and (candidate / ".venv").is_dir():
            return candidate.resolve()
    sys.stderr.write("litpick: repo not found. Set RAMANLENS_REPO.\n")
    sys.exit(1)


def _prepare() -> Path:
    repo = _repo()
    os.environ.setdefault("IOPIC_BOND_HOME", str(repo / "data" / "raw" / "iopic-bond"))
    os.environ["IOPIC_BOND_SEARCH"] = "off"
    venv_py = repo / ".venv" / "bin" / "python"
    if not venv_py.is_file():
        venv_py = repo / ".venv" / "Scripts" / "python.exe"
    if os.environ.get("LITPICK_READY") != "1" and venv_py.is_file():
        os.environ["LITPICK_READY"] = "1"
        if Path(sys.executable).resolve() != venv_py.resolve():
            os.execv(str(venv_py), [str(venv_py), str(Path(__file__).resolve()), *sys.argv[1:]])
    src = repo / "iopic-bond" / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
    return repo


def _emit(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, default=str))
    sys.stdout.write("\n")


def _view(server, arxiv_id: str, figure: str) -> dict:
    parts = server.view_figure(arxiv_id, figure)
    info = dict(parts[0]) if parts else {"status": "empty"}
    blob = getattr(parts[1], "data", None) if len(parts) > 1 else None
    if not blob:
        return info
    safe_id = arxiv_id.replace("/", "-")
    safe_fig = "".join(ch if ch.isalnum() else "-" for ch in figure).strip("-")[:40] or "figure"
    dest = Path.cwd() / f"litpick-{safe_id}-{safe_fig}.png"
    dest.write_bytes(blob)
    info["saved_png"] = str(dest)
    return info


def main() -> None:
    _prepare()
    from iopic_bond import server

    ap = argparse.ArgumentParser(description="litpick: open arXiv papers and look at their figures.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="list parsed papers in the local library")
    p.set_defaults(run=lambda a: server.library_status())

    p = sub.add_parser("library", help="search captions of papers already parsed (no network)")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(run=lambda a: server.search_library(a.query, a.limit))

    p = sub.add_parser("ingest", help="open an arXiv paper; returns at once if already parsed")
    p.add_argument("arxiv_id")
    p.add_argument("--force", action="store_true")
    p.set_defaults(run=lambda a: asyncio.run(server.ingest_paper(a.arxiv_id, a.force)))

    p = sub.add_parser("figures", help="captions and discussing paragraphs for one parsed paper")
    p.add_argument("arxiv_id")
    p.set_defaults(run=lambda a: server.list_figures(a.arxiv_id))

    p = sub.add_parser("view", help="save one figure as a PNG in the current folder")
    p.add_argument("arxiv_id")
    p.add_argument("figure", help='printed number, for example "2" or "Fig. 2"')
    p.set_defaults(run=lambda a: _view(server, a.arxiv_id, a.figure))

    args = ap.parse_args()
    _emit(args.run(args))


if __name__ == "__main__":
    main()
