"""Corpus source step 0: pull new weekly journal-club folders from Zotero into a PDF corpus dir.

The journal-club collection (default key ``648ZC48T``, "Zotero Journal Club") nests year ->
month -> week collections; a **leaf** collection (no subcollections of its own) is one week's
reading list. This step walks the subtree once, skips any leaf already recorded in the state
ledger, and for the rest fetches every item's PDF into ``--out/<leaf-path-slug>/<zotero-key>.pdf``
plus a JSONL manifest row per item (found or not, and which source found it). A leaf is marked done
in the ledger only once every item in it was attempted with zero hard errors, so a partial failure
leaves it open for retry next run instead of silently dropping papers — same "one failure never
kills the batch, but nothing is silently lost" contract as the other corpusops steps.

An item with no PDF attached in Zotero is not a dead end: unless ``--no-oa-fallback``, it falls
through to :mod:`oa_fetch` (arXiv direct download, then Unpaywall by DOI) before being recorded as
``no_pdf`` — no PDF means no parse, no embedding, so the OA fallback is what keeps a paper the group
is reading from silently dropping out of the corpus just because nobody attached a PDF in Zotero.

Downstream is untouched: point ``corpusops parse --corpus`` at ``--out`` (or the specific new
subfolder) and the existing parse -> enrich -> consolidate -> ingest chain runs as-is.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import append_jsonl, fresh_report, log, write_summary

DEFAULT_PARENT = "648ZC48T"  # "Zotero Journal Club", group 11251


def add_args(ap) -> None:
    ap.add_argument("--group", type=int, default=11251, help="Zotero group id")
    ap.add_argument("--parent", default=DEFAULT_PARENT, help="journal-club parent collection key")
    ap.add_argument("--out", default="data/samples/zotero", help="dir new PDFs are copied into")
    ap.add_argument(
        "--state", default="output/zotero_fetch_state.json", help="ledger of already-fetched leaves"
    )
    ap.add_argument("--report", default="tmp/zotero_fetch_report")
    ap.add_argument("--dry-run", action="store_true", help="walk + plan only, write nothing")
    ap.add_argument(
        "--force", nargs="*", default=None, help="re-fetch these leaf collection keys even if in the ledger"
    )
    ap.add_argument(
        "--under",
        default=None,
        help="scope the walk to this collection key instead of --parent (e.g. one year, for testing "
        "or a deliberate backfill)",
    )
    ap.add_argument(
        "--seed",
        action="store_true",
        help="mark every leaf currently in the tree as already-fetched WITHOUT downloading anything. "
        "Run this once on first adoption so the journal club's multi-year history is not treated as "
        "'new' — only leaves created after seeding are fetched by subsequent runs.",
    )
    ap.add_argument(
        "--via-web",
        action="store_true",
        help="use the Zotero web API (ZOTERO_API_KEY) instead of the local desktop-app API — the "
        "only mode that works headless, e.g. on a server with no Zotero desktop running",
    )
    ap.add_argument(
        "--no-oa-fallback",
        action="store_true",
        help="don't try Unpaywall/arXiv when an item has no PDF attached in Zotero (default: try)",
    )


def _slug(name: str) -> str:
    s = re.sub(r"[^\w\-. ]", "", name).strip()
    return re.sub(r"\s+", "-", s)


def _walk_leaves(client, key: str, path: list[str]) -> list[dict]:
    """Recurse to every collection with no children; return [{key, name, path, slug}]."""
    children = client.subcollections(key)
    if not children:
        return [{"key": key, "name": path[-1], "path": path, "slug": "/".join(_slug(p) for p in path)}]
    leaves: list[dict] = []
    for c in children:
        name = c["data"]["name"]
        leaves.extend(_walk_leaves(client, c["key"], path + [name]))
    return leaves


def run(args) -> int:
    import os

    from . import oa_fetch
    from .zotero_client import ZoteroClient

    mailto = os.environ.get("CROSSREF_MAILTO")
    use_oa = not args.no_oa_fallback and not args.dry_run
    if use_oa and not mailto:
        log.warning("[fetch-zotero] CROSSREF_MAILTO not set — OA fallback disabled (Unpaywall needs it)")
        use_oa = False

    client = ZoteroClient(args.group, via_web=args.via_web)
    root_key = args.under or args.parent
    root_name = client.collection(root_key)["name"]
    leaves = _walk_leaves(client, root_key, [root_name])
    log.info("[fetch-zotero] %d leaf (weekly) collections under '%s'", len(leaves), root_name)

    state_path = Path(args.state)
    ledger: dict = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    if args.seed:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        for leaf in leaves:
            ledger.setdefault(
                leaf["key"],
                {"name": leaf["name"], "slug": leaf["slug"], "fetched_at": now, "seeded": True},
            )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        log.info("[fetch-zotero] seeded %d leaves into the ledger, fetched nothing", len(leaves))
        return 0

    force = set(args.force or [])
    todo = [leaf for leaf in leaves if leaf["key"] not in ledger or leaf["key"] in force]
    if not todo:
        log.info("[fetch-zotero] nothing new — every leaf already in the ledger")
        return 0
    log.info("[fetch-zotero] %d new/forced leaves: %s", len(todo), [leaf["slug"] for leaf in todo])

    out_root = Path(args.out)
    records, summary_path = fresh_report(args.report)
    t0 = time.time()
    totals = {"leaves": 0, "items": 0, "pdf_found": 0, "pdf_missing": 0, "errors": 0}

    for leaf in todo:
        items = client.collection_items_top(leaf["key"])
        leaf_dir = out_root / leaf["slug"]
        n_pdf = n_missing = n_err = 0
        log.info("[fetch-zotero] %s: %d items", leaf["slug"], len(items))

        for item in items:
            data = item.get("data", {})
            item_type = data.get("itemType")
            if item_type == "note":
                continue
            rec: dict = {
                "leaf": leaf["slug"],
                "leaf_key": leaf["key"],
                "zotero_key": item["key"],
                "item_type": item_type,
                "title": data.get("title"),
                "doi": data.get("DOI"),
                "extra": data.get("extra"),
            }
            try:
                children = [] if item_type == "attachment" else client.children(item["key"])
                attachment = client.find_pdf_attachment(item, children)
                if attachment and args.dry_run:
                    rec["status"] = "pdf_found"
                    n_pdf += 1
                    append_jsonl(records, rec)
                    continue

                pdf, source = None, "zotero"
                if attachment:
                    pdf = client.pdf_bytes(attachment)
                if not pdf and use_oa:
                    aid = oa_fetch.arxiv_id_from_item(data.get("DOI"), data.get("extra"))
                    if aid:
                        pdf, source = oa_fetch.arxiv_pdf(aid, mailto=mailto), "arxiv"
                    if not pdf and data.get("DOI"):
                        pdf, source = oa_fetch.unpaywall_pdf(data["DOI"], mailto=mailto), "unpaywall"

                if pdf:
                    leaf_dir.mkdir(parents=True, exist_ok=True)
                    dest = leaf_dir / f"{item['key']}.pdf"
                    dest.write_bytes(pdf)
                    rec["pdf_path"] = str(dest)
                    rec["pdf_source"] = source
                    rec["status"] = "pdf_found"
                    n_pdf += 1
                else:
                    rec["status"] = "no_pdf"
                    n_missing += 1
            except Exception as exc:  # one bad item must not abort the leaf
                rec["status"] = "error"
                rec["error"] = f"{type(exc).__name__}: {exc}"
                n_err += 1
            append_jsonl(records, rec)

        totals["leaves"] += 1
        totals["items"] += len(items)
        totals["pdf_found"] += n_pdf
        totals["pdf_missing"] += n_missing
        totals["errors"] += n_err
        log.info(
            "[fetch-zotero] %s: pdf_found=%d no_pdf=%d errors=%d",
            leaf["slug"],
            n_pdf,
            n_missing,
            n_err,
        )

        if not args.dry_run and n_err == 0:
            ledger[leaf["key"]] = {
                "name": leaf["name"],
                "slug": leaf["slug"],
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_items": len(items),
                "n_pdf": n_pdf,
            }
        elif n_err:
            log.warning("[fetch-zotero] %s left OUT of the ledger (%d errors) — will retry next run", leaf["slug"], n_err)

    if not args.dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    write_summary(summary_path, {**totals, "wall_s": round(time.time() - t0), "dry_run": args.dry_run})
    return 1 if totals["errors"] else 0
