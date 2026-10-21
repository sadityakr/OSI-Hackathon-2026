"""Contract for material identification: the reference library and matcher, plus curated literature tables."""

import pytest

from cases import dev_cases
from score import same_material


@pytest.mark.slow
def test_ws2_ranks_top3_from_textbook_peaks():
    """Stage-1 criterion: 2H-WS2 E2g and A1g at 532 nm (Berkdemir et al. 2013, Sci. Rep. 3, 1755)."""
    from ramanlens.perception.library import match
    cands = match([356.0, 418.0], intensities=[1.0, 0.6], top_k=5)
    # each candidate has .material (formula string), .score (float), .matched (list of (measured, reference, label))
    assert any(same_material(c.material, "WS2") for c in cands[:3]), [c.material for c in cands]
    assert all(cands[i].score >= cands[i + 1].score for i in range(len(cands) - 1))


@pytest.mark.slow
def test_identify_top3_on_dev_single_cases():
    from ramanlens.perception.io import read_spectrum
    from ramanlens.perception.library import match
    from ramanlens.perception.pipeline import analyze_spectrum
    hits, cases = 0, dev_cases(kind="single", task="identify")
    for c in cases:
        res = analyze_spectrum(read_spectrum(c["dir"] / "spectrum.csv"))
        sample = [p for p in res.peaks if not p.is_substrate]  # substrate lines flagged by the pipeline
        cands = match([p.position for p in sample], intensities=[p.height for p in sample], top_k=5)
        hits += any(same_material(m.material, c["truth"]["formula"]) for m in cands[:3])
    assert cases and hits / len(cases) >= 0.8, f"{hits}/{len(cases)}"


def test_reference_tables_for_demo_materials():
    """Curated literature mode tables for materials the CRD lacks; every mode carries its source."""
    from ramanlens.literature.reference_tables import get_table
    for name in ("graphene", "2H-MoS2", "CrSBr", "2H-WS2"):
        t = get_table(name)
        assert t.modes, name
        for m in t.modes:
            assert m.position_cm1 > 0 and m.label
            assert m.source.doi or m.source.arxiv, (name, m.label)
            assert m.source.locator, "figure or table where the number was read"
        assert t.conditions.get("laser_nm"), name


def test_si_substrate_line_is_flagged():
    import numpy as np
    from ramanlens.perception.pipeline import analyze_spectrum
    from ramanlens.perception.io import Spectrum
    x = np.arange(100, 800, 1.0)
    g = 2.0
    y = 100 + 1000 * g * g / ((x - 520.7) ** 2 + g * g) + 800 * g * g / ((x - 383) ** 2 + g * g)
    res = analyze_spectrum(Spectrum(x=x, y=y, meta={"substrate": "SiO2/Si"}))
    si = [p for p in res.peaks if p.is_substrate]
    assert len(si) == 1 and abs(si[0].position - 520.7) < 1
