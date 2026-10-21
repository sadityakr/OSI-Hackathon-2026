"""Unit tests for the optional literature figure tools (find_papers, view_figure) in the agent toolset.

Skipped as a whole when iopic_bond is not installed. No test touches the network: Bond is replaced by a stub, and
view_figure is checked against the local iopic-Bond library only when Lee et al. 2010 (arXiv 1005.2509) is parsed
there (data/raw/iopic-bond on the development PC).
"""

import base64
import json
from pathlib import Path

import pytest

pytest.importorskip("iopic_bond")

from ramanlens.agent import toolset  # noqa: E402
from ramanlens.literature import figure_tools  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "data" / "raw" / "iopic-bond"


def test_figure_tools_registered():
    names = [t["name"] for t in toolset.TOOLS]
    assert {"find_papers", "view_figure"} <= set(names)
    assert len(names) == len(set(names))


@pytest.fixture
def stub_store(monkeypatch, tmp_path):
    from iopic_bond.store import Store

    monkeypatch.setattr(figure_tools, "_store", Store(root=tmp_path))


def test_find_papers_withholds_excluded_and_merges(monkeypatch, stub_store):
    papers = [
        {"id": "2503.15298v1", "base_id": "2503.15298", "source": "arxiv", "title": "excluded CrSBr paper"},
        {"id": "x1", "source": "pubmed", "title": "excluded by DOI", "doi": "10.1021/acs.nanolett.7b05184"},
        {"id": "1005.2509v1", "base_id": "1005.2509", "source": "arxiv", "title": "Lee 2010", "doi": "10.1/a"},
        {"id": "p2", "source": "pubmed", "title": "Lee 2010 journal record", "doi": "10.1/A"},
    ]

    async def fake_call(tool, args, **kw):
        assert tool == "semantic_search_papers" and args["query"] == "MoS2 layer number"
        return {"papers": papers, "confidence": "high"}

    monkeypatch.setattr(figure_tools.bond, "call", fake_call)
    out = json.loads(toolset.call("find_papers", {"query": "MoS2 layer number"}, workdir=None))
    assert out["status"] == "ok" and out["provenance"] == "literature"
    assert [p["id"] for p in out["papers"]] == ["1005.2509"]
    assert out["papers"][0]["parseable"] is True
    assert "withheld" in out["note"]


def test_find_papers_reports_bond_error(monkeypatch, stub_store):
    async def failing(tool, args, **kw):
        raise figure_tools.bond.BondError("VALENCY_BOND_TOKEN is not set")

    monkeypatch.setattr(figure_tools.bond, "call", failing)
    out = json.loads(toolset.call("find_papers", {"query": "graphene defects"}, workdir=None))
    assert out["status"] == "bond_error"


def test_view_figure_refuses_excluded_and_bad_ids(stub_store):
    out = json.loads(toolset.call("view_figure", {"arxiv_id": "2503.15298", "figure": "3"}, workdir=None))
    assert out["status"] == "withheld"
    out = json.loads(toolset.call("view_figure", {"arxiv_id": "not an id"}, workdir=None))
    assert out["status"] == "bad_request"


@pytest.mark.skipif(not (LIB / "papers" / "1005.2509").is_dir(), reason="Lee 2010 not parsed in the local library")
def test_view_figure_from_local_library(monkeypatch):
    from iopic_bond.store import Store

    monkeypatch.setattr(figure_tools, "_store", Store(root=LIB))
    listing = json.loads(toolset.call("view_figure", {"arxiv_id": "1005.2509"}, workdir=None))
    assert listing["status"] == "ok" and len(listing["figures"]) >= 4

    blocks = toolset.call("view_figure", {"arxiv_id": "1005.2509", "figure": "Fig. 2", "max_px": 400}, workdir=None)
    assert isinstance(blocks, list) and [b["type"] for b in blocks] == ["text", "image"]
    info = json.loads(blocks[0]["text"])
    assert info["status"] == "ok" and info["cite_as"].endswith("of arXiv:1005.2509")
    assert "png" not in info
    png = base64.b64decode(blocks[1]["source"]["data"])
    assert png[:8] == b"\x89PNG\r\n\x1a\n"

    missing = json.loads(toolset.call("view_figure", {"arxiv_id": "1005.2509", "figure": "99"}, workdir=None))
    assert missing["status"] == "not_found" and missing["available"]
