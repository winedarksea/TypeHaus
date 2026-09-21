"""``engineering/thermal_break.py`` against ``sunken_garden_court_free_body.md`` §11.

The note was worked by hand before the module existed; this file reproduces it. Values are
read off the resolved catlin model rather than pinned where another pass could move them.
Since basis 2 catlin names its products (Aslan 100 #5, Styrofoam Highload 40, §11f), so the
catlin rows are graded on published values and two of them are OVER.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.thermal_break import KIND, SETTLEMENT_MISSING, SETTLEMENT_OWED

# §11a/§11b — hand-worked.
_NOTE_PRESSURE_PSI = {"DW-SG-W1": 10.194, "DW-SG-E1": 10.194,
                      "DW-SG-W1-STEM": 9.500, "DW-SG-E1-STEM": 9.500}
_NOTE_BUOYANCY_LB = 116.67
_NOTE_FLOTATION_RESTRAINT_LB = 500.0
# §11c/§11d.
_NOTE_RUN_IN = 322.815
_NOTE_MOVEMENT_IN = 0.07102      # 5.5e-6 x (90 - 50) x 322.815; was 0.1864 at basis 1
_NOTE_MOVEMENT_CAP_IN = 0.019048   # 2 x (40/3) / 1,400
_NOTE_BAR_LB = 1_385.31            # 0.55 x 32,240 x 0.625 / (4 x 2)
_NOTE_SHORTFALL_LB = 24_464.0   # §4d (AB Classic apron); §4c 24,834; §4 23,454
_NOTE_RESERVE_LB = {"DW-SG-W1": 16_309.0, "DW-SG-E1": 16_309.0,
                    "DW-SG-W1-STEM": 3_262.0, "DW-SG-E1-STEM": 3_262.0}


@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    from typehaus.engineering import EngineeringContext

    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


@pytest.fixture(scope="module")
def records(ctx):
    from typehaus.engineering import EngineeringResults

    results = EngineeringResults(ctx)
    return {tag: results[f"{KIND}/{tag}"] for tag in _NOTE_PRESSURE_PSI}


def _state(record, name):
    return next((s for s in record.limit_states if s.name == name), None)


def _input(record, name):
    return next(q.value for q in record.inputs if q.name == name)


def test_the_kind_is_computed_not_deferred(ctx) -> None:
    from typehaus.engineering import DEFERRALS, keys_of

    assert KIND not in DEFERRALS
    assert keys_of(KIND, ctx) == sorted(_NOTE_PRESSURE_PSI)


@pytest.mark.parametrize("tag", sorted(_NOTE_PRESSURE_PSI))
def test_the_pressure_row_reproduces_section_11a(records, tag) -> None:
    state = _state(records[tag], "fresh-concrete pressure")
    assert state.demand == pytest.approx(_NOTE_PRESSURE_PSI[tag], abs=0.001)
    assert state.capacity == 40.0


def test_flotation_is_graded_on_the_footing_boards_and_omitted_on_the_stems(records) -> None:
    for tag in ("DW-SG-W1", "DW-SG-E1"):
        state = _state(records[tag], "board flotation")
        assert state.demand == pytest.approx(_NOTE_BUOYANCY_LB, abs=0.01)
        assert state.capacity == pytest.approx(_NOTE_FLOTATION_RESTRAINT_LB)
    for tag in ("DW-SG-W1-STEM", "DW-SG-E1-STEM"):
        assert _state(records[tag], "board flotation") is None
        assert any("NO FLOTATION ROW" in note for note in records[tag].notes)


@pytest.mark.parametrize("tag", sorted(_NOTE_PRESSURE_PSI))
def test_movement_and_reserve_demands_reproduce_section_11c_d(records, tag) -> None:
    from typehaus.engineering.thermal_break import ALPHA_C_PER_F

    record = records[tag]
    run = _input(record, "court_run")
    assert run == pytest.approx(_NOTE_RUN_IN, abs=0.01)
    assert ALPHA_C_PER_F * _input(record, "delta_T") * run == pytest.approx(
        _NOTE_MOVEMENT_IN, abs=1e-4)
    shortfall = _input(record, "loop_shortfall")
    assert shortfall == pytest.approx(_NOTE_SHORTFALL_LB, abs=1.0)
    assert 1.6 * shortfall * _input(record, "bar_share") == pytest.approx(
        _NOTE_RESERVE_LB[tag], abs=1.0)


@pytest.mark.parametrize("tag", sorted(_NOTE_PRESSURE_PSI))
def test_catlin_grades_every_row_on_the_named_products(records, tag) -> None:
    record = records[tag]
    movement = _state(record, "thermal movement")
    assert movement.demand == pytest.approx(_NOTE_MOVEMENT_IN, abs=1e-5)
    assert movement.capacity == pytest.approx(_NOTE_MOVEMENT_CAP_IN, abs=1e-6)
    assert movement.ratio == pytest.approx(3.73, abs=0.005)
    reserve = _state(record, "dowel shear reserve")
    bars = 10 if "STEM" not in tag else 2
    assert reserve.capacity == pytest.approx(bars * _NOTE_BAR_LB, abs=0.1)
    assert reserve.ratio == pytest.approx(1.177, abs=0.001)
    assert reserve.combination == "1.6H"


@pytest.mark.parametrize("tag", sorted(_NOTE_PRESSURE_PSI))
def test_catlin_stays_incomplete_naming_what_is_owed(records, tag) -> None:
    record = records[tag]
    assert record.status is Status.INCOMPLETE
    assert SETTLEMENT_MISSING in record.missing
    assert "Dowel." not in " ".join(record.missing)
    over = next(m for m in record.missing if m.startswith("a design answer"))
    assert "thermal movement 3.73" in over and "dowel shear reserve 1.18" in over


def _authored(ctx, tag, **values):
    """``_one`` on a copy of the dowel with some fields replaced."""
    from typehaus.engineering import thermal_break as tb

    loops = tb.footing_shortfalls(ctx)
    breaks = tb._dowels(ctx)
    bars = {}
    for d in breaks:
        side = tb._court_side(ctx, d, loops)
        bars[side[0]] = bars.get(side[0], 0) + d.count
    dowel = ctx.plan.by_tag(tag).model_copy(update=values)
    return tb._one(ctx, dowel, loops, tb._court_side(ctx, dowel, loops), bars)


def test_unnamed_products_hold_the_rows_open(ctx) -> None:
    record = _authored(ctx, "DW-SG-W1", foam_source=None, bar_source=None)
    missing = " ".join(record.missing)
    assert "Dowel.foam_source" in missing and "Dowel.bar_source" in missing
    assert _state(record, "thermal movement") is None
    assert _state(record, "dowel shear reserve") is None


def test_the_shear_branch_governs_when_the_bar_is_weak_in_shear(ctx) -> None:
    record = _authored(ctx, "DW-SG-W1-STEM", bar_shear_lb=1_000.0)
    assert _state(record, "dowel shear reserve").capacity == pytest.approx(2 * 0.75 * 1_000.0)


def test_a_measured_k_v_is_read_and_still_owes_the_demand() -> None:
    from types import SimpleNamespace

    from typehaus.engineering.thermal_break import _settlement

    def run(k_v):
        site = SimpleNamespace(lateral_subgrade_modulus=SimpleNamespace(k_v_pci=k_v))
        ctx = SimpleNamespace(plan=SimpleNamespace(project=SimpleNamespace(site=site)))
        missing, inputs = [], []
        _settlement(ctx, missing, inputs)
        return missing, inputs

    assert run(None) == ([SETTLEMENT_MISSING], [])
    missing, inputs = run(120.0)
    assert missing == [SETTLEMENT_OWED]
    assert [(q.name, q.value) for q in inputs] == [("k_v", 120.0)]


def test_dowel_product_fields_round_trip() -> None:
    from typehaus.model.structure import Dowel
    from typehaus.quantities import ft, inch, pt

    dowel = Dowel(uid="AAAAAAAAAA", tag="DW-RT", position=pt(ft(0), ft(0)),
                  length=inch(24), diameter=inch(0.625), elevation=inch(-100),
                  foam_thickness=inch(2), foam_modulus_psi=400.0, bar_shear_lb=6_000.0,
                  bar_tensile_lb=27_000.0, bar_modulus_psi=6.5e6, bar_source="datasheet")
    back = Dowel.model_validate(dowel.model_dump())
    assert back == dowel
    assert back.bar_source == "datasheet" and back.foam_modulus_psi == 400.0
    bare = Dowel(uid="AAAAAAAAAB", tag="DW-RT2", position=pt(ft(0), ft(0)),
                 length=inch(24), diameter=inch(0.625), elevation=inch(-100))
    assert bare.bar_shear_lb is None and bare.foam_modulus_psi is None
