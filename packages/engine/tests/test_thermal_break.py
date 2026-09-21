"""``engineering/thermal_break.py`` against ``sunken_garden_court_free_body.md`` §11 (basis 4).

The note was worked by hand before the module was rewritten; this file reproduces it. Basis 4
is XPS (Styrofoam Highload 40) at 2.5" on the closure boards, #6 Aslan 100 @ 8", every row
graded — and five items OVER, which the stop rule reports rather than designs away.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.thermal_break import KIND, SETTLEMENT_MISSING

_FOOT, _STEM, _BEAM = ("DW-SG-W1", "DW-SG-E1"), ("DW-SG-W1-STEM", "DW-SG-E1-STEM"), "W-SG-BRKBM"
_ALL = (*_FOOT, *_STEM, _BEAM)

# (demand, capacity, ratio) per row, hand-worked in §11a-§11h.
_NOTE = {
    "foot": {
        "fresh-concrete pressure": (0.6944, 40.0, 0.0174),
        "board flotation": (145.833, 750.0, 0.1944),
        "thermal movement": (0.053223, 0.071429, 0.7451),
        "house footing sliding": (1.5, 0.07045, 21.29),
        "house footing bearing": (20.746, 8.253, 2.514),
        "court sliding under break thrust": (1.5, 0.4701, 3.191),
        "dowel shear reserve": (16_308.9, 14_429.8, 1.130),
        "differential settlement": (0.015352, 0.022368, 0.6863),
        "racking drift": (0.054987, 0.022368, 2.458),
        "joint opening": (0.141929, 0.013698, 10.36),
        "bar development": (15.0, 10.565, 1.420),
    },
    "stem": {
        "fresh-concrete pressure": (9.4998, 40.0, 0.2375),
        "thermal movement": (0.053223, 0.071429, 0.7451),
        "house insulation bearing": (29.805, 15.0, 1.987),
        "house wall flexure": (412_024.0, 276_299.0, 1.491),
        "house wall shear": (17_168.0, 72_377.0, 0.2372),
        "house floor-line reaction": (21_974.0, 3_285.0, 6.689),
        "court sliding under break thrust": (1.5, 0.4701, 3.191),
        "dowel shear reserve": (3_261.8, 1_159.1, 2.814),
        "differential settlement": (0.015352, 0.138655, 0.1107),
        "racking drift": (0.054987, 0.138655, 0.3966),
        "joint opening": (0.141929, 0.030933, 4.588),
        "bar development": (15.0, 6.565, 2.285),
    },
    "beam": {
        "fresh-concrete pressure": (10.4329, 40.0, 0.2608),
        "thermal movement": (0.052635, 0.057143, 0.9211),
        "house footing sliding": (1.5, 0.03339, 44.92),
        "house footing bearing": (45.858, 8.253, 5.557),
        "court sliding under break thrust": (1.5, 0.4701, 3.191),
    },
}
_NOTE_SIGMA_PSI = 29.805
_NOTE_THRUST_LB = {"DW-SG-W1": 20_029.0, "DW-SG-W1-STEM": 39_141.4, _BEAM: 156_957.6}
_NOTE_RUN_IN = 322.565
_NOTE_SHORTFALL_LB = 24_463.3   # §4d (AB apron), unmoved by the SRW merge


def _group(tag):
    return "beam" if tag == _BEAM else ("stem" if tag in _STEM else "foot")


@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    from typehaus.engineering import EngineeringContext

    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


@pytest.fixture(scope="module")
def records(ctx):
    from typehaus.engineering import EngineeringResults

    results = EngineeringResults(ctx)
    return {tag: results[f"{KIND}/{tag}"] for tag in _ALL}


def _state(record, name):
    return next((s for s in record.limit_states if s.name == name), None)


def _input(record, name):
    return next(q.value for q in record.inputs if q.name == name)


def test_the_kind_is_computed_and_the_beam_board_is_an_item(ctx) -> None:
    from typehaus.engineering import DEFERRALS, keys_of

    assert KIND not in DEFERRALS
    assert keys_of(KIND, ctx) == sorted(_ALL)


@pytest.mark.parametrize("tag", _ALL)
def test_every_row_reproduces_section_11(records, tag) -> None:
    record = records[tag]
    expected = _NOTE[_group(tag)]
    assert [s.name for s in record.limit_states] == list(expected), tag
    for name, (demand, capacity, ratio) in expected.items():
        state = _state(record, name)
        assert state.demand == pytest.approx(demand, rel=2e-4), (tag, name)
        assert state.capacity == pytest.approx(capacity, rel=2e-4), (tag, name)
        assert state.ratio == pytest.approx(ratio, rel=1e-3, abs=6e-4), (tag, name)


@pytest.mark.parametrize("tag", _ALL)
def test_basis_4_is_over_with_nothing_open(records, tag) -> None:
    record = records[tag]
    assert record.status is Status.OVER
    assert record.missing == ()
    assert record.basis_version == "4"


def test_the_thrust_and_the_run(records) -> None:
    for tag, thrust in _NOTE_THRUST_LB.items():
        assert _input(records[tag], "board_thrust") == pytest.approx(thrust, rel=1e-4)
    assert _input(records["DW-SG-W1"], "board_stress") == pytest.approx(_NOTE_SIGMA_PSI, abs=1e-3)
    assert _input(records["DW-SG-W1"], "court_run") == pytest.approx(_NOTE_RUN_IN, abs=1e-3)
    assert _input(records["DW-SG-W1"], "delta_T") == 30.0
    assert _input(records["DW-SG-W1"], "clear_gap") == pytest.approx(2.685, abs=1e-6)
    assert _input(records["DW-SG-W1-STEM"], "clear_gap") == pytest.approx(6.685, abs=1e-6)
    assert _input(records["DW-SG-W1"], "loop_shortfall") == pytest.approx(
        _NOTE_SHORTFALL_LB, abs=1.0)


def test_flotation_is_graded_only_where_a_face_is_under_the_pour(records) -> None:
    for tag in (*_STEM, _BEAM):
        assert _state(records[tag], "board flotation") is None
        assert any("NO FLOTATION ROW" in note for note in records[tag].notes)


def test_the_environmental_factor_is_the_codes_single_value() -> None:
    from typehaus.engineering import thermal_break_bars as bars

    assert bars.ENVIRONMENTAL_FACTOR == 0.85      # ACI 440.11-22 §20.2.2.3, not 440.1R's 0.7
    assert bars.SUSTAINED_FRACTION == 0.30        # §24.6.2


def _compute_with(ctx, monkeypatch, **dowel_values):
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering import thermal_break_geometry as geo

    real = geo.dowels(ctx)
    monkeypatch.setattr(geo, "dowels",
                        lambda _ctx: [d.model_copy(update=dowel_values) for d in real])
    return {r.key: r for r in tb.compute(ctx)}


def test_unnamed_products_hold_every_row_open(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, foam_source=None, bar_source=None)
    record = out["DW-SG-W1"]
    assert record.limit_states == ()
    assert "foam_source" in " ".join(record.missing)
    assert out[_BEAM].limit_states == (), "the beam's board names the closure boards' product"


def test_without_a_placement_sequence_the_pour_is_monolithic(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, placement_sequence_ref=None)
    state = _state(out["DW-SG-W1"], "fresh-concrete pressure")
    assert state.demand == pytest.approx(150 * 117.4375 / 1728.0, abs=1e-4)


def test_the_shear_branch_governs_when_the_bar_is_weak_in_shear(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, bar_shear_lb=100.0)
    assert _state(out["DW-SG-W1-STEM"], "dowel shear reserve").capacity == pytest.approx(
        2 * 0.75 * 100.0)


def _with_site(ctx, **site_values):
    project = ctx.plan.project
    site = project.site.model_copy(update=site_values)
    plan = ctx.plan.model_copy(update={"project": project.model_copy(update={"site": site})})
    return dataclasses.replace(ctx, plan=plan)


def test_no_service_temperature_holds_the_thermal_rows_open(ctx) -> None:
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering.thermal_break_board import TEMPERATURE_MISSING

    out = {r.key: r for r in tb.compute(_with_site(ctx, concrete_service_temperature=None))}
    record = out["DW-SG-W1"]
    assert TEMPERATURE_MISSING in record.missing
    assert _state(record, "thermal movement") is None
    assert _state(record, "joint opening") is None
    assert record.status is Status.OVER, "the reserve is still over; OVER outranks INCOMPLETE"


def test_no_k_v_holds_the_settlement_row_open(ctx) -> None:
    from typehaus.engineering import thermal_break as tb
    from typehaus.model import Site

    out = {r.key: r for r in tb.compute(_with_site(ctx, lateral_subgrade_modulus=None))}
    record = out["DW-SG-W1"]
    assert SETTLEMENT_MISSING in record.missing
    assert _state(record, "differential settlement") is None
    assert Site.model_fields["lateral_subgrade_modulus"].default is None


def test_a_k_v_only_report_leaves_base_rotation_on_its_band(ctx) -> None:
    from typehaus.engineering.base_supports import measured

    report = ctx.plan.project.site.lateral_subgrade_modulus.model_copy(update={"n_h_pci": None})
    assert measured(_with_site(ctx, lateral_subgrade_modulus=report)) is None
    assert measured(ctx) is not None, "catlin authors a presumed n_h since 2026-09-21"


def test_dowel_product_fields_round_trip() -> None:
    from typehaus.model.structure import Dowel
    from typehaus.quantities import ft, inch, pt

    dowel = Dowel(uid="AAAAAAAAAA", tag="DW-RT", position=pt(ft(0), ft(0)),
                  length=inch(24), diameter=inch(0.625), elevation=inch(-100),
                  foam_thickness=inch(2), foam_modulus_psi=400.0, bar_shear_lb=6_000.0,
                  bar_tensile_lb=27_000.0, bar_modulus_psi=6.5e6, bar_source="datasheet",
                  placement_sequence_ref="AN-X")
    back = Dowel.model_validate(dowel.model_dump())
    assert back == dowel and back.placement_sequence_ref == "AN-X"
    bare = Dowel(uid="AAAAAAAAAB", tag="DW-RT2", position=pt(ft(0), ft(0)),
                 length=inch(24), diameter=inch(0.625), elevation=inch(-100))
    assert bare.bar_shear_lb is None and bare.placement_sequence_ref is None


def test_site_inputs_carry_their_provenance() -> None:
    from typehaus.model import ConcreteServiceTemperature, SubgradeModulus

    presumed = SubgradeModulus(k_v_pci=88.4, provenance="presumed", source="Bowles T9-1",
                               basis="table row")
    assert SubgradeModulus.model_validate(presumed.model_dump()) == presumed
    temps = ConcreteServiceTemperature(max_f=80.0, min_f=0.0, source="AASHTO T3.12.2.1.1-1",
                                       basis="published row", placement_min_f=50.0)
    assert ConcreteServiceTemperature.model_validate(temps.model_dump()) == temps
    assert temps.provenance == "published"
