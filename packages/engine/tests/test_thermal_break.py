"""``engineering/thermal_break.py`` against ``sunken_garden_court_free_body.md`` §11 (basis 5).

The note was worked by hand before the module was rewritten; this file reproduces it. Basis 5
is a pure isolation joint — the 24 dowels deleted, the boards Styrofoam Highload 40 (2.5"
closure, 2" beam) — and every item is OVER on the thrust its board passes into the house,
which the stop rule reports rather than designs away (§11h weighs the board).
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.thermal_break import KIND

_FOOT, _STEM, _BEAM = ("TB-SG-W1", "TB-SG-E1"), ("TB-SG-W1-STEM", "TB-SG-E1-STEM"), "W-SG-BRKBM"
_ALL = (*_FOOT, *_STEM, _BEAM)

# (demand, capacity, ratio) per row, hand-worked in §11a-§11d.
_NOTE = {
    "foot": {
        "fresh-concrete pressure": (0.6944, 40.0, 0.0174),
        "thermal movement": (0.053223, 0.071429, 0.7451),
        "house footing sliding": (1.5, 0.07045, 21.29),
        "house footing bearing": (20.746, 8.253, 2.514),
        "court sliding under break thrust": (1.5, 0.4701, 3.191),
    },
    "stem": {
        "fresh-concrete pressure": (9.4998, 40.0, 0.2375),
        "thermal movement": (0.053223, 0.071429, 0.7451),
        "house insulation bearing": (29.805, 15.0, 1.987),
        "house wall flexure": (412_024.0, 276_299.0, 1.491),
        "house wall shear": (17_168.0, 72_377.0, 0.2372),
        "house floor-line reaction": (21_974.0, 3_285.0, 6.689),
        "court sliding under break thrust": (1.5, 0.4701, 3.191),
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
_NOTE_THRUST_LB = {"TB-SG-W1": 20_029.0, "TB-SG-W1-STEM": 39_141.4, _BEAM: 156_957.6}
_NOTE_RUN_IN = 322.565


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
def test_basis_5_is_over_with_nothing_open(records, tag) -> None:
    record = records[tag]
    assert record.status is Status.OVER
    assert record.missing == ()
    assert record.basis_version == "5"
    assert any("RETIRED WITH THE BARS" in n for n in record.notes)


def test_the_thrust_and_the_run(records) -> None:
    for tag, thrust in _NOTE_THRUST_LB.items():
        assert _input(records[tag], "board_thrust") == pytest.approx(thrust, rel=1e-4)
    assert _input(records["TB-SG-W1"], "board_stress") == pytest.approx(_NOTE_SIGMA_PSI, abs=1e-3)
    assert _input(records["TB-SG-W1"], "court_run") == pytest.approx(_NOTE_RUN_IN, abs=1e-3)
    assert _input(records["TB-SG-W1"], "delta_T") == 30.0


def _compute_with(ctx, monkeypatch, **values):
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering import thermal_break_geometry as geo

    real = geo.isolation_boards(ctx)
    monkeypatch.setattr(geo, "isolation_boards",
                        lambda _ctx: [b.model_copy(update=values) for b in real])
    return {r.key: r for r in tb.compute(ctx)}


def test_an_unnamed_product_holds_every_row_open(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, source=None)
    assert out["TB-SG-W1"].limit_states == ()
    assert "IsolationBoard.psi" in " ".join(out["TB-SG-W1"].missing)
    assert out[_BEAM].limit_states == (), "the beam's board names the closure boards' product"


def test_without_a_placement_sequence_the_pour_is_monolithic(ctx, monkeypatch) -> None:
    out = _compute_with(ctx, monkeypatch, placement_sequence_ref=None)
    state = _state(out["TB-SG-W1"], "fresh-concrete pressure")
    assert state.demand == pytest.approx(150 * 117.4375 / 1728.0, abs=1e-4)


def _with_site(ctx, **site_values):
    project = ctx.plan.project
    site = project.site.model_copy(update=site_values)
    plan = ctx.plan.model_copy(update={"project": project.model_copy(update={"site": site})})
    return dataclasses.replace(ctx, plan=plan)


def test_no_service_temperature_holds_the_thermal_rows_open(ctx) -> None:
    from typehaus.engineering import thermal_break as tb
    from typehaus.engineering.thermal_break_board import TEMPERATURE_MISSING

    out = {r.key: r for r in tb.compute(_with_site(ctx, concrete_service_temperature=None))}
    record = out["TB-SG-W1"]
    assert TEMPERATURE_MISSING in record.missing
    assert [s.name for s in record.limit_states] == ["fresh-concrete pressure"]
    assert record.status is Status.INCOMPLETE


def test_a_k_v_only_report_leaves_base_rotation_on_its_band(ctx) -> None:
    from typehaus.engineering.base_supports import measured

    report = ctx.plan.project.site.lateral_subgrade_modulus.model_copy(update={"n_h_pci": None})
    assert measured(_with_site(ctx, lateral_subgrade_modulus=report)) is None
    assert measured(ctx) is not None, "catlin authors a presumed n_h since 2026-09-21"


def test_isolation_board_round_trips() -> None:
    from typehaus.model.structure import IsolationBoard
    from typehaus.quantities import ft, inch, pt

    board = IsolationBoard(uid="AAAAAAAAAA", tag="TB-RT", position=pt(ft(0), ft(0)),
                           thickness=inch(2.5), height=inch(8), length=inch(84),
                           elevation=inch(-100), modulus_psi=1_400.0, source="sheet",
                           placement_sequence_ref="AN-X")
    assert IsolationBoard.model_validate(board.model_dump()) == board
    assert board.psi == 40.0 and board.material == "xps"


def test_site_inputs_carry_their_provenance() -> None:
    from typehaus.model import ConcreteServiceTemperature, SubgradeModulus

    presumed = SubgradeModulus(k_v_pci=88.4, provenance="presumed", source="Bowles T9-1",
                               basis="table row")
    assert SubgradeModulus.model_validate(presumed.model_dump()) == presumed
    temps = ConcreteServiceTemperature(max_f=80.0, min_f=0.0, source="AASHTO T3.12.2.1.1-1",
                                       basis="published row", placement_min_f=50.0)
    assert ConcreteServiceTemperature.model_validate(temps.model_dump()) == temps
    assert temps.provenance == "published"
