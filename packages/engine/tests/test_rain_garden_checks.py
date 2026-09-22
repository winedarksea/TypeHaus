"""Rain garden volume, setbacks, extensions and utility clearance — each graded both ways."""

from __future__ import annotations

import dataclasses

import pytest
from _helpers import check_context

from typehaus.checks.code.site_utilities import utility_clearance
from typehaus.checks.mep.drainage_network import outfall_connection
from typehaus.checks.mep.landscape_drainage import (
    infiltration_setback,
    leader_extension_fall,
    rain_garden_capacity,
)
from typehaus.findings import Result
from typehaus.model import RainGarden, Trellis
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.drainage_network import DAYLIGHT, EdgeKind, build_network
from typehaus.resolve.rain_garden import floor_ring, ponding_volume_m3

_CF = 35.3146667


def _swap(plan, tag: str, **update):
    for storey in plan.storeys:
        elements = list(plan.storey_elements(storey.tag))
        for index, element in enumerate(elements):
            if getattr(element, "tag", None) == tag:
                elements[index] = element.model_copy(update=update)
                return plan.with_elements(storey.tag, elements)
    raise KeyError(tag)


def _ctx(model, plan):
    return check_context(plan, dataclasses.replace(model, plan=plan))


def _results(findings):
    return {f.result for f in findings}


def test_prismoidal_volume_by_hand() -> None:
    # 10' x 40' rim, 6" ponding, 3:1: floor 7 x 37 = 259, mid 8.5 x 38.5 = 327.25, top 400.
    # V = 0.5/6 x (400 + 1309 + 259) = 164.0 cf.
    garden = RainGarden(uid="TSTRG00001", tag="RG-T",
                        outline=(pt(ft(0), ft(0)), pt(ft(10), ft(0)), pt(ft(10), ft(40)),
                                 pt(ft(0), ft(40))),
                        rim_elevation=ft(0), ponding_depth=inch(6), side_slope=3.0,
                        media_depth=inch(12))
    assert ponding_volume_m3(garden) * _CF == pytest.approx(164.0, abs=0.05)
    assert len(floor_ring(garden)) == 4
    lower = garden.model_copy(update={"overflow_invert": ft(0, -3)})
    assert ponding_volume_m3(lower) < ponding_volume_m3(garden)


def test_a_leader_that_names_a_receiver_joins_the_network(catlin_model_ro) -> None:
    network = build_network(catlin_model_ro.plan)
    assert network.nodes["TR-G-LEADER-W"].kind == "leader"
    assert "TR-RF-LEADER-E" not in network.nodes     # a splash block is not a connection
    edges = {(e.source, e.target, e.kind) for e in network.edges}
    assert ("TR-RF-LEADER-W", "RG-W-BASIN", EdgeKind.PRIMARY) in edges
    assert ("RG-W-BASIN", DAYLIGHT, EdgeKind.OVERFLOW) in edges


def test_capacity_fails_when_the_basin_shrinks(catlin_model_ro) -> None:
    plan = _swap(catlin_model_ro.plan, "RG-W-BASIN",
                 outline=(pt(ft(-6), ft(47)), pt(ft(-1), ft(47)), pt(ft(-1), ft(60)),
                          pt(ft(-6), ft(60))))
    assert Result.FAIL in _results(rain_garden_capacity(_ctx(catlin_model_ro, plan)))


def test_a_basin_against_the_basement_fails_its_setback(catlin_model_ro) -> None:
    plan = _swap(catlin_model_ro.plan, "RG-W-BASIN",
                 outline=(pt(ft(-6), ft(10)), pt(ft(-2), ft(10)), pt(ft(-2), ft(30)),
                          pt(ft(-6), ft(30))))
    findings = infiltration_setback(_ctx(catlin_model_ro, plan))
    assert any(f.result is Result.FAIL and "basement" in f.message for f in findings)


def test_an_extension_that_runs_uphill_fails(catlin_model_ro) -> None:
    leader = catlin_model_ro.plan.by_tag("TR-G-LEADER-W")
    uphill = leader.extension.model_copy(update={"outlet_invert": ft(-3, -4)})
    plan = _swap(catlin_model_ro.plan, "TR-G-LEADER-W", extension=uphill)
    findings = leader_extension_fall(_ctx(catlin_model_ro, plan))
    assert any(f.result is Result.FAIL and "TR-G-LEADER-W" in f.element_tags
               for f in findings)


def test_an_extension_that_stops_short_of_the_basin_fails(catlin_model_ro) -> None:
    leader = catlin_model_ro.plan.by_tag("TR-G-LEADER-W")
    short = leader.extension.model_copy(update={
        "path": (leader.position, pt(ft(1), leader.position.y))})
    plan = _swap(catlin_model_ro.plan, "TR-G-LEADER-W", extension=short)
    findings = outfall_connection(_ctx(catlin_model_ro, plan))
    assert any(f.result is Result.FAIL and "stops short" in f.message for f in findings)


def test_a_trellis_over_the_power_line_fails(catlin_model_ro) -> None:
    over = Trellis(uid="TSTTR00002", tag="TRL-T-POWER",
                   path=(pt(ft(-5), ft(17)), pt(ft(-5), ft(21))), post_spacing=ft(8),
                   post_height=ft(7), post_embed=ft(3))
    plan = catlin_model_ro.plan.with_elements(
        "yard-grade", (*catlin_model_ro.plan.storey_elements("yard-grade"), over))
    findings = utility_clearance(_ctx(catlin_model_ro, plan))
    assert any(f.result is Result.FAIL and "power" in f.message for f in findings)
