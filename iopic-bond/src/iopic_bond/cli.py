"""Command line for iopic-Bond: run the MCP server and maintain the local library.

Input: a subcommand (see ``iopic-bond --help``) and the settings in ``config``.
Process: loads ``.env`` first (tracing is decided when tool modules are imported), then dispatches.
Output: ``serve`` runs the MCP server until the client closes it; the other subcommands print a short
report and exit.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from . import config


def main(argv: list[str] | None = None) -> None:
    config.load_env()

    ap = argparse.ArgumentParser(prog="iopic-bond", description="Local MCP server over Valency Bond.")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="run the MCP server (default)")
    s.add_argument("--http", action="store_true", help="Streamable HTTP instead of stdio")
    s.add_argument("--port", type=int, default=8765, help="port for --http (default 8765)")
    sub.add_parser("doctor", help="check the library folder, the Bond token and the parser")
    sub.add_parser("warmup", help="download the Docling models once, so the first parse is not slow")
    sub.add_parser("reindex", help="rebuild index.sqlite from the paper folders")
    i = sub.add_parser("ingest", help="ingest one arXiv paper from the command line")
    i.add_argument("arxiv_id")
    i.add_argument("--force", action="store_true", help="re-download and re-parse")
    args = ap.parse_args(argv)

    if args.cmd in (None, "serve"):
        from .server import mcp

        if getattr(args, "http", False):
            mcp.run("streamable-http", port=args.port)
        else:
            mcp.run()
    elif args.cmd == "doctor":
        _doctor()
    elif args.cmd == "warmup":
        _warmup()
    elif args.cmd == "reindex":
        from .library import figure_dicts
        from .store import Store

        n = Store().reindex(figure_dicts)
        print(f"reindexed {n} parsed papers")
    elif args.cmd == "ingest":
        from .library import ingest
        from .store import Store

        res = ingest(Store(), args.arxiv_id, force=args.force)
        print(json.dumps({k: v for k, v in res.items() if k != "paper"}, indent=2, default=str))


def _doctor() -> None:
    from .store import Store

    s = Store()
    print(f"library   {s.root}  ({len(s.list_papers())} papers)")
    print(f"token     {'set' if config.bond_token() else 'MISSING: set VALENCY_BOND_TOKEN'}")
    if config.bond_token():
        from . import bond

        try:
            res = asyncio.run(bond.call("list_sources", {}, use_cache=False))
            names = [x["source"] for x in res.get("sources", [])]
            print(f"bond      ok  ({', '.join(names)})")
        except bond.BondError as exc:
            print(f"bond      FAILED  {exc}")
    try:
        import docling  # noqa: F401

        print(f"parser    docling installed, device={config.parse_device()}")
    except ImportError:
        print("parser    docling MISSING: pip install iopic-bond[parse]")
    from .tracing import tracing_enabled

    print(f"tracing   {'on' if tracing_enabled() else 'off'}")


def _warmup() -> None:
    try:
        from .pdf.pipeline import load_converter
    except ImportError:
        sys.exit("docling is not installed: pip install iopic-bond[parse]")
    device = config.parse_device()
    print(f"loading Docling models on {device} (first run downloads them) ...")
    conv = load_converter(device)
    # models load lazily on first conversion; initialise the PDF pipeline explicitly
    try:
        from docling.datamodel.base_models import InputFormat

        conv.initialize_pipeline(InputFormat.PDF)
    except Exception as exc:  # older Docling has no initialize_pipeline; the first parse loads them
        print(f"note: models will load on the first parse ({type(exc).__name__})")
    print("ready")


if __name__ == "__main__":
    main()
