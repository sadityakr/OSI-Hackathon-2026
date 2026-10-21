"""Batch corpus parse: every PDF under a corpus dir -> output/parsed/<hash>/ vaults, with QA.

Loads Docling once (the converter is process-cached in ``pipeline._build_converter``), wraps each
paper so one failure never kills the batch, and appends a per-paper JSONL record (timing, pages, QA,
tree stats, the pass ledger) as it completes. The summary aggregates failure modes AND the per-pass
status histogram — a pass that errors on many papers is a systematic regression, not noise, and it
must be visible at the end of the run (review finding F6), not buried in a ledger nobody reads.
"""

from __future__ import annotations

import time
import traceback
from collections import Counter
from pathlib import Path

from . import append_jsonl, fresh_report, log, write_summary


def _tree_stats(root) -> dict:
    nodes = list(root.walk())
    edge_counts: dict[str, int] = {}
    for n in nodes:
        for e in n.edges:
            edge_counts[e.type] = edge_counts.get(e.type, 0) + 1
    return {
        "n_nodes": len(nodes),
        "n_figures": sum(1 for n in nodes if n.type == "figure"),
        "n_equations": sum(1 for n in nodes if n.type == "equation"),
        "n_tables": sum(1 for n in nodes if n.type == "table"),
        "n_sections": sum(1 for n in nodes if n.type in ("chapter", "section", "subsection")),
        "cites_edges": edge_counts.get("cites", 0),
        "xref_edges": sum(v for k, v in edge_counts.items() if k.startswith("references-")),
        "title": (root.attrs.get("title") or "")[:120],
    }


def add_args(ap) -> None:
    ap.add_argument("--corpus", required=True, help="dir of PDFs (searched recursively)")
    ap.add_argument("--out", default="output/parsed")
    ap.add_argument("--report", default="tmp/corpus_report")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--vram-fraction", type=float, default=0.35)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shuffle-seed", type=int, default=0)
    ap.add_argument("--no-formula", action="store_true")


def run(args) -> int:
    from lit_rag.parsing.pipeline import parse_pdf
    from lit_rag.parsing.qa import qa_report

    pdfs = sorted(Path(args.corpus).rglob("*.pdf"))
    if args.shuffle_seed:
        import random

        random.Random(args.shuffle_seed).shuffle(pdfs)
    if args.limit:
        pdfs = pdfs[: args.limit]

    out_dir = Path(args.out)
    records, summary_path = fresh_report(args.report)

    n = len(pdfs)
    log.info(
        "[parse] %d PDFs | out=%s | device=%s | vram=%s",
        n,
        out_dir,
        args.device,
        args.vram_fraction,
    )
    t_start = time.time()
    n_ok = n_fail = n_qa_fail = 0
    pass_status: Counter = Counter()  # "<pass>:<ok|skipped|error>" across the corpus (F6 histogram)

    for i, pdf in enumerate(pdfs, 1):
        rec: dict = {
            "i": i,
            "pdf": str(pdf),
            "name": pdf.name,
            "size_mb": round(pdf.stat().st_size / 1e6, 2),
        }
        t0 = time.time()
        try:
            root = parse_pdf(
                pdf,
                out_dir,
                do_formula=not args.no_formula,
                device=args.device,
                vram_fraction=args.vram_fraction,
            )
            rec["hash"] = root.id
            rec["pages"] = root.attrs.get("n_pages")
            rec["parse_s"] = round(time.time() - t0, 1)
            rec.update(_tree_stats(root))
            passes = root.attrs.get("passes", {})
            rec["passes"] = passes
            for name, status in passes.items():
                kind = status if status in ("ok", "skipped") else "error"
                pass_status[f"{name}:{kind}"] += 1
            try:
                report = qa_report(out_dir / root.id, pdf)
                rec["qa_ok"] = report.ok
                rec["qa_stats"] = report.stats
                rec["qa_issues"] = [
                    {"check": x.check, "severity": x.severity, "detail": x.detail[:200]}
                    for x in report.issues
                ]
                if not report.ok:
                    n_qa_fail += 1
            except Exception as exc:  # QA must never sink the parse result
                rec["qa_error"] = f"{type(exc).__name__}: {exc}"
            rec["status"] = "ok"
            n_ok += 1
        except Exception as exc:
            rec["status"] = "fail"
            rec["parse_s"] = round(time.time() - t0, 1)
            rec["error"] = f"{type(exc).__name__}: {exc}"
            rec["traceback"] = traceback.format_exc()[-1500:]
            n_fail += 1

        append_jsonl(records, rec)
        eta = (time.time() - t_start) / i * (n - i)
        flag = "OK " if rec["status"] == "ok" else "FAIL"
        qa = "" if rec.get("qa_ok", True) else " [QA-FAIL]"
        log.info(
            "[%3d/%d] %s%s %5ss p=%s %s | ETA %.0fm",
            i,
            n,
            flag,
            qa,
            rec.get("parse_s", "?"),
            rec.get("pages", "?"),
            pdf.name[:60],
            eta / 60,
        )

    dur = time.time() - t_start
    bad_passes = {k: v for k, v in sorted(pass_status.items()) if k.endswith(":error")}
    if bad_passes:  # the F6 tripwire: a pass erroring across papers is a SYSTEMATIC regression
        log.warning("[parse] passes with errors across the corpus: %s", bad_passes)
    write_summary(
        summary_path,
        {
            "total": n,
            "ok": n_ok,
            "parse_fail": n_fail,
            "qa_fail": n_qa_fail,
            "pass_status": dict(sorted(pass_status.items())),
            "wall_min": round(dur / 60, 1),
            "mean_parse_s": round(dur / max(n, 1), 1),
        },
    )
    return 1 if n_fail else 0
