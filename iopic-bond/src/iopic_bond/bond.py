"""Client for Valency Bond, the paper discovery layer iopic-Bond builds on.

Bond is itself an MCP server (``https://mcp.valency.io/``, Streamable HTTP). We talk to it as an MCP
*client* with the Direct API bearer token, so iopic-Bond is an MCP server on the outside and an MCP
client on the inside.

Input: ``VALENCY_BOND_TOKEN``; a Bond tool name and its arguments.
Process: opens one connection per call, calls the tool, decodes the JSON payload, caches the response
under ``<home>/bond/`` for ``CACHE_TTL_S``; ``merge_papers`` collapses arXiv/PubMed duplicates.
Output: plain dicts in Bond's own shape (``papers`` list of paper objects with ``id``, ``base_id``,
``doi``, ``source``, ``title``, ``citation_count``, ``url``...).

Query rule (docs/bond-evaluation.md in the RamanLens repo): ask by concept ("Raman mode assignment
in CrSBr"), never by peak frequencies; embeddings do not encode numbers.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from . import config
from .tracing import traced

CACHE_TTL_S = 7 * 24 * 3600


class BondError(RuntimeError):
    """Bond could not be reached or refused the call (missing token, HTTP error, tool error)."""


def _cache_path(tool: str, args: dict) -> Path:
    key = json.dumps([tool, args], sort_keys=True)
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return config.home() / "bond" / f"{tool}-{h}.json"


async def call(tool: str, args: dict[str, Any], *, use_cache: bool = True) -> dict:
    """Call one Bond tool and return its decoded JSON payload."""
    cache = _cache_path(tool, args)
    if use_cache and cache.exists() and time.time() - cache.stat().st_mtime < CACHE_TTL_S:
        return json.loads(cache.read_text(encoding="utf-8"))

    payload = await _call_remote(tool, args)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload), encoding="utf-8")
    return payload


@traced("bond.call")
async def _call_remote(tool: str, args: dict[str, Any]) -> dict:
    token = config.bond_token()
    if not token:
        raise BondError("VALENCY_BOND_TOKEN is not set; copy a token from https://app.valency.io/settings")
    headers = {"Authorization": f"Bearer {token}"}
    # 300 s read timeout: the MCP transport may hold a response stream open
    timeout = httpx2.Timeout(30.0, read=300.0)
    try:
        async with httpx2.AsyncClient(headers=headers, timeout=timeout) as http:
            async with Client(streamable_http_client(config.bond_url(), http_client=http)) as client:
                result = await client.call_tool(tool, args)
    except Exception as exc:  # transport and auth failures arrive as assorted exception types
        raise BondError(f"Bond call {tool} failed: {type(exc).__name__}: {exc}") from exc

    if result.is_error:
        text = " ".join(getattr(c, "text", "") for c in result.content)
        raise BondError(f"Bond tool {tool} returned an error: {text[:500]}")
    if result.structured_content:
        return dict(result.structured_content)
    text = "".join(getattr(c, "text", "") for c in result.content)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BondError(f"Bond tool {tool} returned non-JSON text: {text[:200]}") from exc


def merge_papers(papers: list[dict]) -> list[dict]:
    """Collapse records of the same work, keeping the arXiv one (it has a fetchable PDF).

    Keyed on DOI when present, else on ``base_id``: Bond leaves ``doi`` empty for some arXiv
    records, so DOI alone would let duplicates through. Order of first appearance is kept, so the
    relevance ranking survives the merge.
    """
    kept: dict[str, dict] = {}
    order: list[str] = []
    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        key = f"doi:{doi}" if doi else f"id:{p.get('base_id') or p.get('id')}"
        if key not in kept:
            kept[key] = p
            order.append(key)
        elif p.get("source") == "arxiv" and kept[key].get("source") != "arxiv":
            # keep the arXiv record but remember the journal-side id for citation
            p = {**p, "also_in": kept[key].get("source")}
            kept[key] = p
    return [kept[k] for k in order]
