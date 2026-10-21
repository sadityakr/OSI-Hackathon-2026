"""Dispatcher: ``python -m lit_rag.corpusops {parse|enrich|consolidate|ingest}``.

Each step declares its own flags via ``add_args`` and executes via ``run`` — heavy imports stay
inside the step modules' ``run`` so ``--help`` is instant.
"""

from __future__ import annotations

import argparse
import sys

from . import consolidate, enrich, fetch_zotero, ingest, parse, setup_logging

_STEPS = {
    "fetch-zotero": (fetch_zotero, "new weekly journal-club Zotero folders -> a PDF corpus dir"),
    "parse": (parse, "PDFs -> output/parsed vaults (Docling; GPU-capped)"),
    "enrich": (enrich, "Phase 1 (ADR-0005): GROBID structure onto parsed trees"),
    "consolidate": (consolidate, "Phase 2 (ADR-0005): CrossRef DOI resolution, resumable"),
    "ingest": (ingest, "enriched trees -> the live Postgres store"),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lit_rag.corpusops", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, (mod, help_text) in _STEPS.items():
        p = sub.add_parser(name, help=help_text)
        mod.add_args(p)
        p.set_defaults(func=mod.run)
    args = ap.parse_args(argv)
    setup_logging()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
