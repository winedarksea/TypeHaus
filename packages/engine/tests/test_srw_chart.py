"""``structural.srw_gravity_chart`` and the scope rule behind it, against
``houses/catlin/notes/raised_garden_srw.md`` §10 (the applicability sheet, by hand per leg).

AB Table 1.3 (12° AB Stones, level, clay 27°): 3'-6" exposed, cap included. Each leg's exposure
is its authored top less the nearest grade station: 40" south/west (-3'-4"), 36" west return
(-3'-0"), 37" east return (-3'-1"); every one is under 42".
"""

from __future__ import annotations

import pytest

from typehaus import SrwDrain, inch
from typehaus.checks.structural.srw_chart import graded_wall
from typehaus.engineering import EngineeringContext
from typehaus.engineering.segmental_wall import segmental_walls
from typehaus.engineering.srw_chart import applicability
from typehaus.engineering.srw_scope import on_chart_path
from typehaus.engineering.srw_tiers import lower_tiers
from typehaus.findings import Result

_CHART = {"W-RG-BLOCK": 40, "W-RG-WEST": 40, "W-RG-WEST-BALCONY": 36, "W-RG-EAST-BALCONY": 37}


@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


def _sheet(ctx, wall):
    return {c.name: c for c in applicability(ctx, wall, lower_tiers(ctx, wall))}


def test_the_scope_rule_is_per_leg(ctx) -> None:
    on = {w.tag for w in segmental_walls(ctx) if on_chart_path(w)}
    assert on == set(_CHART)
    # W-RG-EAST authors no chart row: its toe takes TR-SG-RUNNEL's spout (gate G9).
    assert not on_chart_path(ctx.plan.by_tag("W-RG-EAST"))
    over = ctx.plan.by_tag("W-RG-BLOCK").model_copy(update={"unbalanced_fill": inch(49)})
    assert not on_chart_path(over)      # R404.4 limb 1: "in excess of 48 inches"


@pytest.mark.parametrize(("tag", "exposed_in"), sorted(_CHART.items()))
def test_every_chart_leg_passes_its_sheet(ctx, tag, exposed_in) -> None:
    wall = ctx.plan.by_tag(tag)
    sheet = _sheet(ctx, wall)
    assert all(c.ok for c in sheet.values()), {n: c.drawn for n, c in sheet.items() if not c.ok}
    assert f"{exposed_in:.1f}\"" in sheet["exposed height, cap included"].drawn
    # Six 8" courses and a 4" cap: the top stays on the court datum, the base is 4" down.
    assert "AB Capstone 4\" on 6.00 courses" in sheet["cap on the top course"].drawn
    assert (wall.top_elevation.meters - wall.bottom_elevation.meters) / 0.0254 == (
        pytest.approx(52.0))
    finding = graded_wall(ctx, wall)
    assert finding.result is Result.PASS and "12 deg AB Stones" in finding.message


def test_the_east_return_carries_the_runnel_on_its_cap_and_still_fits(ctx) -> None:
    sheet = _sheet(ctx, ctx.plan.by_tag("W-RG-EAST-BALCONY"))
    assert "TR-SG-RUNNEL seated on the cap" in sheet["cap on the top course"].drawn
    assert sheet["water kept off the toe"].ok          # its toe faces the north yard


def test_the_east_leg_misses_on_its_toe(ctx) -> None:
    """G9: the runnel's spout and the basin stand at W-RG-EAST's yard face."""
    east = ctx.plan.by_tag("W-RG-EAST")
    donor = ctx.plan.by_tag("W-RG-BLOCK")
    wall = east.model_copy(update={
        "srw": east.srw.model_copy(update={"chart": donor.srw.chart, "cap": "AB Capstone",
                                           "published": donor.srw.published}),
        "bottom_elevation": donor.bottom_elevation})
    sheet = _sheet(ctx, wall)
    assert [n for n, c in sheet.items() if c.ok is False] == ["water kept off the toe"]
    assert "TR-SG-RUNNEL" in sheet["water kept off the toe"].drawn
    assert graded_wall(ctx, wall).result is Result.FAIL


def test_a_drifted_condition_fails(ctx) -> None:
    wall = ctx.plan.by_tag("W-RG-BLOCK")
    srw = wall.srw
    drifts = {
        "exposed height, cap included": {"unbalanced_fill": inch(40),
                                         "top_elevation": wall.top_elevation + inch(6)},
        "cap on the top course": {"srw": srw.model_copy(update={"cap": None})},
        "wall rock": {"srw": srw.model_copy(update={"drainage_zone": None})},
        "drain pipe and outlet": {"srw": srw.model_copy(update={
            "chart": srw.chart.model_copy(update={"drain": None})})},
        "unit and setback": {"srw": srw.model_copy(update={"batter_deg": 6.0})},
        "buried base course": {"bottom_elevation": wall.bottom_elevation + inch(8)},
        "founding fill": {"srw": srw.model_copy(update={"chart": srw.chart.model_copy(
            update={"founding_compaction_pct": 90.0})})},
    }
    for name, update in drifts.items():
        moved = wall.model_copy(update=update)
        sheet = _sheet(ctx, moved)
        assert sheet[name].ok is False, (name, sheet[name].drawn)
        assert graded_wall(ctx, moved).result is Result.FAIL, name
    wrong = srw.chart.model_copy(update={"drain": SrwDrain(pipe="p", outlet_ref="FB-SG-W1")})
    assert _sheet(ctx, wall.model_copy(update={"srw": srw.model_copy(update={"chart": wrong})})
                  )["drain pipe and outlet"].ok is False    # W1 retains nothing: no column


def test_soil_below_the_rows_floor_fails(ctx) -> None:
    wall = ctx.plan.by_tag("W-RG-BLOCK")
    hard = wall.srw.chart.model_copy(update={"soil_phi_deg": 33.0})
    sheet = _sheet(ctx, wall.model_copy(update={"srw": wall.srw.model_copy(
        update={"chart": hard})}))
    assert sheet["soil friction"].ok is False


def test_the_register_holds_only_the_leg_off_the_chart(ctx) -> None:
    from typehaus.engineering.registry import keys_of

    assert keys_of("tiered_retaining", ctx) == ["W-RG-EAST"]
