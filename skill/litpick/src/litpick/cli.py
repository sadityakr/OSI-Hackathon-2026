"""litpick on the command line. Each command prints one JSON object (ASCII-only, so a Windows
console with a legacy code page never fails on Greek letters or umlauts in a caption).

    litpick ingest 2407.13230            open a paper (or: litpick ingest C:\\papers\\x.pdf)
    litpick figures 2407.13230           captions + discussing paragraphs
    litpick view 2407.13230 "Fig. 2"     save the figure as a PNG here and print where
    litpick search "CrSBr magnetoresistance"
    litpick status
    litpick forget 2407.13230v1
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import service
from .paths import safe_name


def _print(obj) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True, default=str) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="litpick", description="Open arXiv papers and look at their figures.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest", help="open an arXiv paper or a local PDF")
    p.add_argument("paper")
    p.add_argument("--force", action="store_true", help="download and parse again")

    sub.add_parser("figures", help="list the figures of an opened paper").add_argument("paper")

    p = sub.add_parser("view", help="save one figure as a PNG")
    p.add_argument("paper")
    p.add_argument("figure", help='printed number, e.g. "2", "Fig. 2", "S1"')
    p.add_argument("--out", default=".", help="folder to save the PNG in (default: here)")

    p = sub.add_parser("search", help="search captions of papers already opened")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)

    sub.add_parser("status", help="where the library is and what it holds")
    sub.add_parser("forget", help="remove a paper from the library").add_argument("paper")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "ingest":
            _print(service.ingest(a.paper, a.force))
        elif a.cmd == "figures":
            _print(service.list_figures(a.paper))
        elif a.cmd == "view":
            info, _ = service.view_figure(a.paper, a.figure)
            out = Path(a.out).expanduser()
            out.mkdir(parents=True, exist_ok=True)
            dest = out / f"litpick-{safe_name(info['paper'])}-fig{safe_name(info['figure'])}.png"
            shutil.copyfile(info["png"], dest)
            info["saved_png"] = str(dest.resolve())
            _print(info)
        elif a.cmd == "search":
            _print(service.search_library(a.query, a.limit))
        elif a.cmd == "status":
            _print(service.status())
        elif a.cmd == "forget":
            _print(service.forget(a.paper))
    except service.LitpickError as e:
        _print({"status": "error", "error": str(e)})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
