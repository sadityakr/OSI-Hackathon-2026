"""Offline tests for iopic-Bond: store, duplicate merging, and the MCP tools over a real client.

Input: a temporary library for the store tests; for the tool tests, an existing library at
``IOPIC_BOND_HOME`` containing arXiv 1005.2509 (run ``iopic-bond ingest 1005.2509`` once), else skipped.
Process: exercises the code paths that need neither Bond nor Docling.
Output: pytest results.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from iopic_bond.bond import merge_papers
from iopic_bond.store import Store


def test_merge_prefers_arxiv_and_keys_on_doi_or_id():
    papers = [
        {"id": "PMC1", "base_id": "PMC1", "doi": "10.1/X", "source": "pubmed"},
        {"id": "1005.2509v1", "base_id": "1005.2509", "doi": "10.1/x", "source": "arxiv"},
        {"id": "1706.01677v1", "base_id": "1706.01677", "doi": "", "source": "arxiv"},
        {"id": "1706.01677v2", "base_id": "1706.01677", "doi": "", "source": "arxiv"},
    ]
    out = merge_papers(papers)
    assert [p["base_id"] for p in out] == ["1005.2509", "1706.01677"]
    assert out[0]["also_in"] == "pubmed"


def test_store_lookup_and_search(tmp_path: Path):
    s = Store(tmp_path)
    figs = [{"label": "Figure 2", "image_rel": "figures/fig2.png",
             "caption": "Raman spectra of thin MoS2 films", "mentions": ["E2g and A1g modes shift"]}]
    s.record_parse("1005.2509", {"doi": "10.1021/nn1003937", "title": "Anomalous lattice vibrations"},
                   "abcd", "v1", figs)
    assert s.lookup(doi="10.1021/NN1003937")["base_id"] == "1005.2509"
    assert s.search("raman MoS2")[0]["label"] == "Figure 2"
    assert s.search("A1g")  # matches the mentioning paragraph
    assert s.search("graphene") == []
    assert s.known_ids([{"base_id": "1005.2509", "doi": ""}]) == {"1005.2509"}


_HOME = os.environ.get("IOPIC_BOND_HOME")
_HAVE_LEE = bool(_HOME) and (Path(_HOME) / "papers" / "1005.2509" / "meta.json").exists()


def _json(res) -> dict:
    """A tool's JSON result, whether the server sent it as structured content or as text."""
    import json

    return res.structured_content or json.loads(res.content[0].text)


@pytest.mark.skipif(not _HAVE_LEE, reason="needs a library with 1005.2509 ingested")
def test_tools_through_mcp_client():
    import anyio
    from mcp import Client

    from iopic_bond.server import mcp

    async def run():
        async with Client(mcp) as c:
            names = {t.name for t in (await c.list_tools()).tools}
            assert {"find_papers", "ingest_paper", "list_figures", "view_figure", "search_library"} <= names

            res = await c.call_tool("ingest_paper", {"arxiv_id": "1005.2509"})
            assert _json(res)["status"] == "cached"

            res = await c.call_tool("list_figures", {"arxiv_id": "1005.2509"})
            figs = _json(res)["figures"]
            assert sum(bool(f["caption"]) for f in figs) >= 4  # Lee 2010: Figs. 1-4 + uncaptioned TOC image

            res = await c.call_tool("view_figure", {"arxiv_id": "1005.2509", "figure": "2"})
            kinds = [b.type for b in res.content]
            assert kinds == ["text", "image"], kinds

            res = await c.call_tool("search_library", {"query": "Raman"})
            assert _json(res)["hits"]
            return figs

    figs = anyio.run(run)
    for f in figs:
        print(f["label"], "|", f["caption"][:90])
