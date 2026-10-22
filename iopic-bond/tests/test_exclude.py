"""Withheld papers (IOPIC_BOND_EXCLUDE) never reach the agent: matching, search, figures, ingest.

Input: a temporary library with two fake parsed papers; no network, no Docling.
Process: sets IOPIC_BOND_EXCLUDE and calls the server tools directly.
Output: pytest results.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from iopic_bond import exclude, server
from iopic_bond.store import Store


def test_matching_by_id_doi_and_title(monkeypatch):
    monkeypatch.setenv("IOPIC_BOND_EXCLUDE",
                       "arXiv:2503.15298v2; https://doi.org/10.1021/ACS.NANOLETT.7B05184, Magneto-Raman effect")
    assert exclude.is_excluded("2503.15298")
    assert exclude.is_excluded("2503.15298v1")
    assert exclude.is_excluded(doi="10.1021/acs.nanolett.7b05184")
    assert exclude.is_excluded(title="The magneto-Raman effect in CrSBr")
    assert not exclude.is_excluded("2212.01754", "10.1/other", "Probing defects in CrSBr")
    assert exclude.record_excluded({"id": "2503.15298v1", "title": "x"})


def test_inactive_without_env(monkeypatch):
    monkeypatch.delenv("IOPIC_BOND_EXCLUDE", raising=False)
    assert not exclude.is_excluded("2503.15298", "10.1021/acs.nanolett.7b05184", "anything")


@pytest.fixture
def library(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IOPIC_BOND_HOME", str(tmp_path))
    s = Store(tmp_path)
    fig = [{"label": "Figure 1", "image_rel": "figures/fig1.png", "caption": "Raman spectra of CrSBr flakes",
            "mentions": ["Ag1 shifts with layer number"]}]
    s.record_parse("2503.15298", {"title": "Magneto-Raman effect in CrSBr"}, "h1", "v1", fig)
    s.record_parse("2212.01754", {"title": "Probing defects and spin-phonon coupling in CrSBr"}, "h2", "v1", fig)
    monkeypatch.setattr(server, "_store", s)
    return s


def test_tools_hide_and_refuse_withheld(library, monkeypatch):
    monkeypatch.setenv("IOPIC_BOND_EXCLUDE", "2503.15298")
    hits = server.search_library("CrSBr")["hits"]
    assert [h["arxiv_id"] for h in hits] == ["2212.01754"]
    assert server.list_figures("2503.15298")["status"] == "withheld"
    assert server.view_figure("2503.15298", "1")[0]["status"] == "withheld"
    assert all(p["base_id"] != "2503.15298" for p in server.library_status()["papers"])
    assert asyncio.run(server.ingest_paper("2503.15298"))["status"] == "withheld"
    assert asyncio.run(server.expand("2503.15298"))["status"] == "withheld"


def test_tools_unchanged_without_env(library, monkeypatch):
    monkeypatch.delenv("IOPIC_BOND_EXCLUDE", raising=False)
    assert len(server.search_library("CrSBr")["hits"]) == 2
    assert server.list_figures("2503.15298")["status"] != "withheld"  # no parse tree in the fake library


def test_exclude_file(tmp_path: Path, monkeypatch):
    f = tmp_path / "withheld.txt"
    f.write_text("# held-out sources\n2006.05912  # McDonnell 2020\nDark Excitons in Monolayer WS2 Using Resonance Raman\n")
    monkeypatch.delenv("IOPIC_BOND_EXCLUDE", raising=False)
    monkeypatch.setenv("IOPIC_BOND_EXCLUDE_FILE", str(f))
    assert exclude.is_excluded("2006.05912v2")
    assert exclude.is_excluded(title="Probing Excitons, Trions, and Dark Excitons in Monolayer WS2 Using Resonance "
                                     "Raman Spectroscopy.")
    assert not exclude.is_excluded("2212.01754")
