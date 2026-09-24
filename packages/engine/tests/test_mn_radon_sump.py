"""The radon sump's two questions: is it the connected collection point MN 1303.2402 subp. 4.E
accepts, and does the hole it sits in undermine a footing?

SM-B-RADON left the NW corner on 2026-09-23: centred on the chase it sat 19 1/2" below
FT-B-W1/FT-B-N4's bearing and cut 9" into both, and nothing graded a pit against a footing.
"""

from __future__ import annotations

import copy
import dataclasses

from _helpers import check_context

from typehaus.checks.code.mn_residential.radon import (
    interior_tile_feeders,
    radon_control_system,
)
from typehaus.checks.mep.sump_discharge import pit_footing_clearance
from typehaus.findings import Result

_FT = 0.3048


def _with_pit(model, outline, z0_m=None):
    """The model with SM-B-RADON's pit solid moved (and optionally made shallower)."""
    moved = copy.copy(model)
    moved.solids = [
        dataclasses.replace(s, outline=outline,
                            z0_m=s.z0_m if z0_m is None else z0_m)
        if s.tag == "SM-B-RADON" else s for s in model.solids]
    return moved


def _square(cx_ft, cy_ft, half_ft=0.75):
    return [((cx_ft + dx) * _FT, (cy_ft + dy) * _FT)
            for dx, dy in ((-half_ft, -half_ft), (half_ft, -half_ft),
                           (half_ft, half_ft), (-half_ft, half_ft))]


def test_the_pit_clears_every_footing(catlin_model):
    found = pit_footing_clearance(check_context(model=catlin_model))
    assert [f.result for f in found] == [Result.PASS]


def test_the_old_corner_station_undermines_both_footings(catlin_model):
    """At (1'-0", 35'-1.3") the pit overlapped FT-B-W1 and FT-B-N4 in plan."""
    found = pit_footing_clearance(check_context(
        model=_with_pit(catlin_model, _square(1.0, 35.11))))
    assert [f.result for f in found] == [Result.FAIL]
    assert "FT-B-N4" in found[0].message and "FT-B-W1" in found[0].message
    assert "overlaps it" in found[0].message


def test_the_influence_line_is_depth_for_distance(catlin_model):
    """1'-0" off FT-B-W1's inner face fails a pit 19 1/2" below its bearing, and passes one
    whose floor is only 11" below it."""
    pit = next(s for s in catlin_model.solids if s.tag == "SM-B-RADON")
    footing = next(s for s in catlin_model.solids if s.tag == "FT-B-W1")
    inner_x_ft = max(x for x, _ in footing.outline) / _FT
    outline = _square(inner_x_ft + 1.0 + 0.75, 28.0)
    deep = pit_footing_clearance(check_context(model=_with_pit(catlin_model, outline)))
    assert deep[0].result is Result.FAIL and "is 12.0\" off it" in deep[0].message
    shallow = pit_footing_clearance(check_context(model=_with_pit(
        catlin_model, outline, z0_m=footing.z0_m - 11 * 0.0254)))
    assert shallow[0].result is Result.PASS
    assert pit.z0_m < footing.z0_m


def test_subpart_4e_reads_the_tile_into_the_pit(catlin_model, catlin_plan):
    ctx = check_context(model=catlin_model)
    sump = catlin_plan.by_tag("SM-B-RADON")
    feeders = interior_tile_feeders(ctx, sump)
    assert len(feeders) == 19 and all(tag.startswith("FB-B-") for tag in feeders)
    finding = next(f for f in radon_control_system(ctx) if "SM-B-RADON" in f.message)
    assert finding.result is Result.PASS and "subpart 4.E" in finding.message


def test_a_sump_named_by_nothing_it_can_reach_is_unknown(catlin_model):
    """Strip the lead and the house stone no longer reaches the pit: the connection 4.E asks
    for is not shown, and a sealed lid alone does not show it."""
    model = copy.copy(catlin_model)
    plan = catlin_model.plan
    elements = [e for e in plan.storey_elements("basement") if e.tag != "FD-B-SUMP-LEAD"]
    model.plan = plan.with_elements("basement", elements)
    ctx = check_context(model=model)
    assert interior_tile_feeders(ctx, model.plan.by_tag("SM-B-RADON")) == []
    finding = next(f for f in radon_control_system(ctx) if "SM-B-RADON" in f.message)
    assert finding.result is Result.UNKNOWN and "4.E" in finding.message
