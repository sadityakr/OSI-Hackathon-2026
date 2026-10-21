"""Unit tests for the relation registry: fail-closed behaviour, candidates, sign conventions, JSON output."""

import json

import pytest

from ramanlens.relations import registry


def test_bad_inputs_fail_closed_instead_of_raising():
    r = registry.get("mos2_layer_number_from_separation")
    assert not r.apply().applicable  # missing input
    out = r.apply(delta_E2g_A1g_cm1=19.1, foo=1)
    assert not out.applicable and "unknown" in out.reason
    assert not r.apply(delta_E2g_A1g_cm1=float("nan")).applicable
    assert not r.apply(delta_E2g_A1g_cm1=21.4, laser_nm=1064).applicable


def test_mos2_candidates_widen_with_uncertainty():
    r = registry.get("mos2_layer_number_from_separation")
    sharp = r.apply(delta_E2g_A1g_cm1=24.0, delta_err_cm1=0.4)
    assert sharp.values["layer_label"] == "4L" and sharp.values["candidates"] == ["4L"]
    broad = r.apply(delta_E2g_A1g_cm1=24.0, delta_err_cm1=1.5)
    assert set(broad.values["candidates"]) == {"3L", "4L", "bulk"} and broad.values["confidence"] == "low"


def test_ws2_three_layer_and_bulk_are_not_separable():
    out = registry.get("ws2_layer_number_from_separation").apply(delta_E2g_A1g_cm1=64.7)
    assert set(out.values["candidates"]) == {"3L", "bulk"}


def test_graphene_LD_closes_below_10_nm_but_reports_value():
    r = registry.get("graphene_defect_distance_from_ID_IG")
    out = r.apply(I_D_over_I_G=4.0, laser_nm=514.5)
    assert not out.applicable and "10 nm" in out.reason and out.values["L_D_nm"] == pytest.approx(5.6, abs=0.1)
    ok = r.apply(I_D_over_I_G=0.5, laser_nm=532.0)
    assert ok.applicable and ok.values["L_D_nm"] > 15


def test_graphene_strain_sign_and_electron_side():
    r = registry.get("graphene_strain_doping_from_G_2D")
    # move from the origin along the strain line toward lower frequencies: tensile strain
    tensile = r.apply(omega_G_cm1=1581.6 - 10, omega_2D_cm1=2676.9 - 22, laser_nm=514.5)
    assert tensile.applicable and tensile.values["strain_percent"] > 0
    assert tensile.values["delta_omega_G_doping_cm1"] == pytest.approx(0, abs=1e-6)
    biax = r.apply(omega_G_cm1=1581.6 - 10, omega_2D_cm1=2676.9 - 22, strain_type="biaxial")
    assert biax.values["strain_percent"] == pytest.approx(10 / 69.1, rel=1e-6)
    # a G downshift with the 2D unchanged needs a negative component along the hole-doping vector
    electron = r.apply(omega_G_cm1=1581.6 - 10, omega_2D_cm1=2676.9)
    assert not electron.applicable and "hole" in electron.reason


def test_graphene_2D_shape_low_confidence_when_2D_weak():
    out = registry.get("graphene_layers_from_2D_shape").apply(n_2D_components=1, I_2D_over_I_G=0.8)
    assert out.values["layer_class"] == "monolayer" and out.values["confidence"] == "low"
    assert not registry.get("graphene_layers_from_2D_shape").apply(n_2D_components=3).applicable


def test_crsbr_axis_angle_and_b2g_reason():
    r = registry.get("crsbr_ag_mode_assignment_with_polarization_axis")
    ag3 = r.apply(position_cm1=345.0, laser_nm=532.0, max_parallel_angle_deg=30.0)
    assert ag3.values["b_axis_angle_deg"] == pytest.approx(30.0)
    ag2 = r.apply(position_cm1=246.0, laser_nm=532.0, max_parallel_angle_deg=30.0, measured_max_axis="a")
    assert ag2.values["expected_max_axis"] == "a" and ag2.values["b_axis_angle_deg"] == pytest.approx(120.0)
    assert ag2.values["consistent"] is True
    unknown = r.apply(position_cm1=246.0)
    assert unknown.applicable and unknown.values["expected_max_axis"] is None and unknown.notes
    b2g = r.apply(position_cm1=194.0)
    assert not b2g.applicable and "B2g" in b2g.reason


def test_find_by_alias_and_describe_is_json():
    assert registry.find(material="2H-MoS2")
    assert len(registry.find(material="graphene")) == 3
    assert {r.material for r in registry.find(input_quantity="delta_E2g_A1g_cm1")} == {"MoS2", "WS2"}
    for r in registry.all_relations():
        json.dumps(r.describe())
        json.dumps(r.apply(**r.out_of_range_example).to_dict())
