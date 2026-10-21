"""Batch Phase-1 enrichment (ADR-0005): GROBID structure onto every parsed tree, in place.

For every parsed ``output/parsed/<hash>`` tree, re-reads the source PDF through the live GROBID
service and enriches the tree: root identity, back-matter ``reference`` nodes (GROBID's own DOIs
only), ``cites`` edges, and the located abstract. **No CrossRef** — DOI resolution is Phase 2
(``corpusops consolidate``). Robust per-paper; idempotent (a tree that already has reference nodes
is skipped); survives GROBID's own mid-run crashes by waiting for its auto-restart.

The work-list comes from the parse report (``--records``), pairing each hash with its source PDF.
"""

from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path

from . import append_jsonl, fresh_report, log, write_summary


def _wait_alive(base_url: str, timeout: float = 150.0) -> bool:
    """Poll GROBID /api/isalive until it's back (it auto-restarts after a crash, ~60s model reload)."""
    import httpx

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{base_url}/api/isalive", timeout=5).text.strip() == "true":
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def _grobid_with_retry(client, pdf_bytes: bytes, *, attempts: int = 3) -> str:
    """Call GROBID, surviving a mid-run crash: on a dropped connection, wait for the service to come
    back and retry — this is what stops one crash from cascading into N failures."""
    import httpx

    transient = (
        httpx.RemoteProtocolError,
        httpx.ConnectError,
        httpx.ReadError,
        httpx.ReadTimeout,
        httpx.PoolTimeout,
    )
    for k in range(attempts):
        try:
            return client.process_fulltext(pdf_bytes)
        except transient:
            if k == attempts - 1:
                raise
            _wait_alive(client.base_url)
            time.sleep(3)
    raise RuntimeError("unreachable")


def add_args(ap) -> None:
    ap.add_argument("--parsed", default="output/parsed")
    ap.add_argument(
        "--records", default="tmp/corpus_report/records.jsonl", help="parse-report work-list"
    )
    ap.add_argument("--report", default="tmp/enrich_report")
    ap.add_argument("--limit", type=int, default=0)


def run(args) -> int:
    from lit_rag.parsing.grobid_adapter import (
        GrobidClient,
        collect_catalog_signals,
        enrich_tree,
        parse_tei,
        strip_catalog_only,
    )
    from lit_rag.parsing.render import render_markdown
    from lit_rag.parsing.schema import from_json, to_json

    work = []
    for line in Path(args.records).read_text().splitlines():
        r = json.loads(line)
        if r.get("status") == "ok" and r.get("hash"):
            work.append((r["hash"], r["pdf"]))
    if args.limit:
        work = work[: args.limit]

    parsed = Path(args.parsed)
    records, summary_path = fresh_report(args.report)

    client = GrobidClient(os.environ.get("GROBID_URL", "http://127.0.0.1:8070"))
    n = len(work)
    log.info("[enrich] %d papers | Phase 1, GROBID-only | service=%s", n, client.base_url)
    t_start = time.time()
    n_ok = n_skip = n_fail = 0
    abs_counts = {"located": 0, "grobid-unlocated": 0, "none": 0}

    for i, (chash, pdf) in enumerate(work, 1):
        doc_dir = parsed / chash
        tree_path = doc_dir / "tree.json"
        rec: dict = {"i": i, "hash": chash, "name": Path(pdf).name}
        if not tree_path.exists():
            rec["status"] = "missing-tree"
            n_fail += 1
            append_jsonl(records, rec)
            continue
        t0 = time.time()
        try:
            root = from_json(tree_path.read_text(encoding="utf-8"))
            if any(node.type == "reference" for node in root.walk()):
                rec["status"] = "skip-already-enriched"
                n_skip += 1
                append_jsonl(records, rec)
                continue

            tei = _grobid_with_retry(client, Path(pdf).read_bytes())
            gdoc = parse_tei(tei)
            enrich_tree(root, gdoc)

            signals = collect_catalog_signals(root)
            (doc_dir / "catalog_signals.json").write_text(
                json.dumps(signals, indent=2), encoding="utf-8"
            )
            strip_catalog_only(root)
            tree_path.write_text(to_json(root), encoding="utf-8")
            (doc_dir / "paper.md").write_text(render_markdown(root), encoding="utf-8")

            n_refs = sum(1 for x in root.walk() if x.type == "reference")
            n_resolved = sum(1 for x in root.walk() if x.type == "reference" and x.attrs.get("doi"))
            n_cites = sum(1 for x in root.walk() for e in x.edges if e.type == "cites")
            abs_src = root.attrs.get("abstract_source") or "none"
            abs_counts[abs_src] = abs_counts.get(abs_src, 0) + 1
            rec.update(
                status="ok",
                enrich_s=round(time.time() - t0, 1),
                n_refs=n_refs,
                n_resolved=n_resolved,
                n_cites=n_cites,
                abstract_source=abs_src,
                doi=root.attrs.get("doi"),
                published_date=root.attrs.get("published_date"),
            )
            n_ok += 1
        except Exception as exc:
            rec["status"] = "fail"
            rec["enrich_s"] = round(time.time() - t0, 1)
            rec["error"] = f"{type(exc).__name__}: {exc}"
            rec["traceback"] = traceback.format_exc()[-1200:]
            n_fail += 1

        append_jsonl(records, rec)
        eta = (time.time() - t_start) / i * (n - i)
        log.info(
            "[%3d/%d] %-22s %5ss refs=%s cites=%s abs=%s %s | ETA %.0fm",
            i,
            n,
            rec["status"],
            rec.get("enrich_s", "?"),
            rec.get("n_refs", "-"),
            rec.get("n_cites", "-"),
            rec.get("abstract_source", "-"),
            rec["name"][:42],
            eta / 60,
        )

    write_summary(
        summary_path,
        {
            "total": n,
            "ok": n_ok,
            "skipped": n_skip,
            "failed": n_fail,
            "abstract": abs_counts,
            "wall_min": round((time.time() - t_start) / 60, 1),
        },
    )
    return 1 if n_fail else 0
