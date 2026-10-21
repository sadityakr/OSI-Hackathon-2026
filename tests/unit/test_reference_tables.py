"""Unit tests for the curated literature mode tables and their use by the matcher."""

import pytest

from ramanlens.literature.reference_tables import all_tables, get_table

# Papers behind held-out evaluation cases; no table may cite them.
EXCLUDED = ("McDonnell", "Viner", "Wdowik")


def test_every_mode_has_provenance():
    for t in all_tables():
        assert t.modes, t.name
        for m in t.modes + t.layer_dependence + t.conditional_modes:
            assert m.position_cm1 > 0 and m.label
            assert m.source.doi or m.source.arxiv, (t.name, m.label)
            assert m.source.locator and m.source.citation
            assert not any(x in m.source.citation for x in EXCLUDED), m.source.citation


def test_name_resolution_is_forgiving():
    assert get_table("MoS2").name == "2H-MoS2"
    assert get_table("2h-mos2").name == "2H-MoS2"
    assert get_table("h-BN").name == "hBN"
    assert get_table("Graphene").formula == "C"
    with pytest.raises(KeyError):
        get_table("unobtainium")


def test_mode_conditions_inherit_and_override():
    t = get_table("2H-WS2")
    assert t.modes[0].conditions["laser_nm"] == 514.5
    l488 = [m for m in t.layer_dependence if m.conditions.get("laser_nm") == 488]
    assert l488 and all(m.conditions["layers"] == "1L" for m in l488)


@pytest.mark.slow
def test_matcher_uses_literature_tables_and_keeps_crd_fallback():
    from ramanlens.perception.library import _formula_key, match
    # with 2LA(M) resolved, the measured table explains every peak and outscores the CRD entry
    ws2 = match([351.1, 355.2, 417.2], top_k=3)
    assert _formula_key(ws2[0].material) == _formula_key("WS2") and ws2[0].kind == "literature"
    # graphene is absent from the CRD: only the literature table can identify it
    c = match([1581.6, 2676.9], top_k=3)
    assert c[0].material == "C" and c[0].kind == "literature"
    # DFT-like positions (about 3 % high for hBN) are matched by the CRD entry, not lost to the measured table
    bn = match([1396.5], top_k=5)
    assert any(_formula_key(c.material) == _formula_key("BN") for c in bn[:3])
