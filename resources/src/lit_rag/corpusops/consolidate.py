"""Batch Phase-2 ref-consolidation (ADR-0005): CrossRef DOI resolution over enriched trees.

Runs :func:`ref_consolidate` on every enriched tree. Default scope is **header-only**: one CrossRef
query per paper to resolve the paper's *own* DOI and promote its ``citable_key`` hash→DOI — the
spine that unlocks dedup + citation→corpus linking. ``--scope refs|all`` also resolves reference
DOIs (the bigger pass). Idempotent (nodes with a DOI are skipped), so re-running IS resuming;
``--hashes`` narrows a re-run to specific papers (the targeted-retry case). Three-way per
ADR-0005: confident → committed DOI; ambiguous → candidate set parked; abstain → nothing.

CrossRef etiquette: requires ``CROSSREF_MAILTO`` (the polite pool); references fan out per paper
(``--ref-workers``) while papers run serially, keeping total concurrency ≈ ref-workers.
"""

from __future__ import annotations

import json
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import append_jsonl, fresh_report, log, retry, write_summary


def add_args(ap) -> None:
    ap.add_argument("--parsed", default="output/parsed")
    ap.add_argument("--report", default="tmp/consolidate_report")
    ap.add_argument("--scope", choices=("header", "refs", "all"), default="header")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--hashes", nargs="*", default=None, help="only these output/parsed/<hash> dirs"
    )
    # --workers = papers in flight; --ref-workers = refs/paper fanned out concurrently. Total
    # concurrent CrossRef connections ≈ workers * ref-workers — keep the product polite (~50).
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--ref-workers", type=int, default=50)


def run(args) -> int:
    mailto = os.environ.get("CROSSREF_MAILTO")
    if not mailto:
        log.error("CROSSREF_MAILTO is not set — refusing to hit CrossRef outside the polite pool")
        return 2

    from lit_rag.parsing.grobid_adapter import (
        arxiv_query,
        collect_catalog_signals,
        crossref_by_doi,
        crossref_candidates,
        ref_consolidate,
        strip_catalog_only,
    )
    from lit_rag.parsing.render import render_markdown
    from lit_rag.parsing.schema import from_json, to_json

    do_header = args.scope in ("header", "all")
    do_refs = args.scope in ("refs", "all")

    def _query(text: str) -> list:
        return retry(crossref_candidates, text, mailto=mailto, default=[])

    def _arxiv(aid: str) -> dict:
        return retry(arxiv_query, aid, default={}) or {}

    def _by_doi(doi: str) -> dict:
        return retry(crossref_by_doi, doi, mailto=mailto, default={}) or {}

    trees = sorted(p for p in Path(args.parsed).glob("*/tree.json"))
    if args.hashes:
        wanted = set(args.hashes)
        trees = [t for t in trees if t.parent.name in wanted]
    if args.limit:
        trees = trees[: args.limit]

    records, summary_path = fresh_report(args.report)

    def _process(tree_path: Path) -> dict:
        doc_dir = tree_path.parent
        rec: dict = {"hash": doc_dir.name}
        t0 = time.time()
        try:
            root = from_json(tree_path.read_text(encoding="utf-8"))
            stats = ref_consolidate(
                root,
                query_fn=_query,
                arxiv_fn=_arxiv,
                doi_fn=_by_doi,
                do_header=do_header,
                do_references=do_refs,
                max_workers=args.ref_workers,
            )
            signals = collect_catalog_signals(root)
            (doc_dir / "catalog_signals.json").write_text(
                json.dumps(signals, indent=2), encoding="utf-8"
            )
            strip_catalog_only(root)
            tree_path.write_text(to_json(root), encoding="utf-8")
            (doc_dir / "paper.md").write_text(render_markdown(root), encoding="utf-8")
            rec.update(
                status="ok",
                s=round(time.time() - t0, 1),
                header_doi=root.attrs.get("doi"),
                header_ambiguous=bool(root.attrs.get("doi_ambiguous")),
                stats=stats,
            )
        except Exception as exc:
            rec.update(status="fail", error=f"{type(exc).__name__}: {exc}")
            rec["traceback"] = traceback.format_exc()[-800:]
        return rec

    n = len(trees)
    log.info(
        "[consolidate] %d trees | scope=%s | papers=%d x ref-workers=%d",
        n,
        args.scope,
        args.workers,
        args.ref_workers,
    )
    t_start = time.time()
    done = 0
    agg = {"confident": 0, "ambiguous": 0, "abstain": 0, "queried": 0, "arxiv": 0}
    n_ok = n_fail = hdr_doi = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_process, tp): tp for tp in trees}
        for fut in as_completed(futs):
            rec = fut.result()
            done += 1
            append_jsonl(records, rec)
            if rec["status"] == "ok":
                n_ok += 1
                for k in agg:
                    agg[k] += rec["stats"].get(k, 0)
                if rec.get("header_doi"):
                    hdr_doi += 1
            else:
                n_fail += 1
            if done % 20 == 0 or done == n:
                log.info(
                    "[%3d/%d] ok=%d fail=%d header_doi=%d conf=%d amb=%d abst=%d | %.1fm",
                    done,
                    n,
                    n_ok,
                    n_fail,
                    hdr_doi,
                    agg["confident"],
                    agg["ambiguous"],
                    agg["abstain"],
                    (time.time() - t_start) / 60,
                )

    write_summary(
        summary_path,
        {
            "trees": n,
            "ok": n_ok,
            "failed": n_fail,
            "scope": args.scope,
            "header_doi_resolved": hdr_doi,
            "outcomes": agg,
            "wall_min": round((time.time() - t_start) / 60, 1),
        },
    )
    return 1 if n_fail else 0
