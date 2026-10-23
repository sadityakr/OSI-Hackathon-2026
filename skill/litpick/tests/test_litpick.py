from __future__ import annotations

import json
import os
import sys

import pymupdf
import pytest

from litpick import service
from litpick.arxiv import parse_id
from litpick.parse import _expand, normalise_label, parse_pdf


# ------------------------------------------------------------------ pure functions

@pytest.mark.parametrize("text, full", [
    ("2407.13230", "2407.13230"),
    ("arXiv:2407.13230v2", "2407.13230v2"),
    ("https://arxiv.org/abs/2407.13230v1", "2407.13230v1"),
    ("https://arxiv.org/pdf/2407.13230.pdf", "2407.13230"),
    ("arxiv.org/html/2608.11389v1", "2608.11389v1"),
    ("cond-mat/0601001v1", "cond-mat/0601001v1"),
])
def test_parse_id(text, full):
    assert parse_id(text).full == full


def test_parse_id_rejects_noise():
    assert parse_id("not a paper") is None


@pytest.mark.parametrize("listing, labels", [
    ("2 and 3", ["2", "3"]),
    ("2-4", ["2", "3", "4"]),
    ("3(b)", ["3"]),
    ("S1, S2", ["S1", "S2"]),
    ("1–3", ["1", "2", "3"]),
])
def test_expand(listing, labels):
    assert _expand(listing) == labels


@pytest.mark.parametrize("text, label", [
    ("2", "2"), ("Fig. 2", "2"), ("figure 2", "2"), ("FIG. 2", "2"), ("S1", "S1"),
    ("Supplementary Fig. 1", "S1"), ("Extended Data Fig. 3", "ED3"), ("FIG.| 1. Phonons", "1"),
])
def test_normalise_label(text, label):
    assert normalise_label(text) == label


# ------------------------------------------------------------------ the figure finder

def _body_overlap(pdf, fig) -> float:
    """Largest share of a body paragraph's area that falls inside a figure region."""
    doc = pymupdf.open(pdf)
    page = doc[fig.page - 1]
    r = pymupdf.Rect(fig.bbox)
    worst = 0.0
    for b in page.get_text("blocks"):
        br = pymupdf.Rect(b[:4])
        if len(b[4]) > 150:  # a paragraph, not an axis label
            worst = max(worst, (br & r).get_area() / max(br.get_area(), 1))
    doc.close()
    return worst


def test_aps_layout(aps_pdf):
    parsed = parse_pdf(aps_pdf)
    figs = {f.label: f for f in parsed.figures}
    assert list(figs) == ["1", "2", "3"], "the 'Fig. 2 shows' sentence must not become a caption"
    for f in figs.values():
        assert f.method == "graphics"
        assert _body_overlap(aps_pdf, f) < 0.05, f"figure {f.label} swallowed body text"
    assert figs["2"].bbox[2] - figs["2"].bbox[0] > 400, "full-width figure should span both columns"
    assert any("Fig. 1(a)" in m for m in figs["1"].mentions)
    assert any("Figs. 2 and 3" in m for m in figs["3"].mentions)


def test_nature_layout(nature_pdf):
    figs = {f.label: f for f in parse_pdf(nature_pdf).figures}
    assert set(figs) == {"1", "S1"}
    assert all(f.method == "graphics" for f in figs.values())


# ------------------------------------------------------------------ library round trip

def test_ingest_view_search_forget(aps_pdf):
    first = service.ingest(str(aps_pdf))
    assert first["status"] == "parsed" and len(first["figures"]) == 3
    key = first["paper"]
    assert service.ingest(str(aps_pdf))["status"] == "cached"

    info, png = service.view_figure(key, "Fig. 2")
    assert png.startswith(b"\x89PNG") and info["figure"] == "2" and "cite_as" in info

    hits = service.search_library("bilayer trilayer")["results"]
    assert hits and hits[0]["figure"] == "2"

    assert key in [p["paper"] for p in service.status()["papers"]]
    service.forget(key)
    assert service.status()["papers"] == []


def test_missing_figure_names_the_ones_that_exist(aps_pdf):
    key = service.ingest(str(aps_pdf))["paper"]
    with pytest.raises(service.LitpickError, match="It has: 1, 2, 3"):
        service.view_figure(key, "9")


# ------------------------------------------------------------------ the MCP server, as a client sees it

def test_mcp_server_over_stdio(aps_pdf):
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "litpick.server"],
                                       env={**os.environ})
        async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            names = {t.name for t in (await s.list_tools()).tools}
            assert names == {"ingest_paper", "list_figures", "view_figure", "search_library", "library_status"}
            res = await s.call_tool("ingest_paper", {"paper": str(aps_pdf)})
            key = json.loads(res.content[0].text)["paper"]
            res = await s.call_tool("view_figure", {"paper": key, "figure": "1"})
            assert res.content[1].type == "image" and (getattr(res.content[1], "mime_type", None) or getattr(res.content[1], "mimeType", None)) == "image/png"

    anyio.run(run)


# ------------------------------------------------------------------ live arXiv (opt in)

@pytest.mark.skipif(os.environ.get("LITPICK_NETWORK") != "1", reason="set LITPICK_NETWORK=1 to hit arXiv")
def test_live_arxiv():
    out = service.ingest("2407.13230v2")
    assert out["status"] == "parsed" and out["figures"]
    assert service.ingest("2407.13230")["status"] == "cached"
