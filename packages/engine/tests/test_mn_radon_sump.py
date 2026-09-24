"""The radon sump's two questions: is it the connected collection point MN 1303.2402 subp. 4.E
accepts, and does the hole it sits in cut a footing?

SM-B-RADON is back in the NW corner (2026-09-24), tangent to FT-B-W1/FT-B-N4 and 19 1/2"
below their bearing. A lined pit is not a trench, so UPC 314.1's 45° line is not applied to
it; only a pit that cuts footing concrete fails.
"""

from __future__ import annotations

import copy
import dataclasses

from _helpers import check_context
from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential.radon import (
    interior_tile_feeders,
    radon_control_system,
)
from typehaus.checks.mep.sump_discharge import pit_footing_clearance
from typehaus.findings import Result

_FT = 0.3048
_IN = 0.0254


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


def test_a_tangent_pit_below_the_bearing_passes(catlin_model):
    """Tangent to both footings, 19 1/2" below their bearing: no concrete cut, so PASS."""
    pit = next(s for s in catlin_model.solids if s.tag == "SM-B-RADON")
    for tag in ("FT-B-W1", "FT-B-N4"):
        footing = next(s for s in catlin_model.solids if s.tag == tag)
        assert Polygon(pit.outline).distance(Polygon(footing.outline)) < 0.25 * _IN
        assert footing.z0_m - pit.z0_m > 19 * _IN
    found = pit_footing_clearance(check_context(model=catlin_model))
    assert found[0].result is Result.PASS and "cuts no footing" in found[0].message


def test_a_pit_cutting_footing_concrete_fails(catlin_model):
    """At (1'-0", 35'-1.3") the pit overlapped FT-B-W1 and FT-B-N4 in plan."""
    found = pit_footing_clearance(check_context(
        model=_with_pit(catlin_model, _square(1.0, 35.11))))
    assert [f.result for f in found] == [Result.FAIL]
    assert "FT-B-N4" in found[0].message and "FT-B-W1" in found[0].message


def test_a_pit_above_the_footing_passes_even_over_it(catlin_model):
    """Plan overlap alone is not a cut: the z ranges must overlap too."""
    footing = next(s for s in catlin_model.solids if s.tag == "FT-B-W1")
    moved = _with_pit(catlin_model, _square(1.0, 30.0))
    moved.solids = [dataclasses.replace(s, z0_m=footing.z1_m + 0.01, z1_m=footing.z1_m + 0.3)
                    if s.tag == "SM-B-RADON" else s for s in moved.solids]
    assert pit_footing_clearance(check_context(model=moved))[0].result is Result.PASS


def test_subpart_4e_reads_the_tile_into_the_pit(catlin_model, catlin_plan):
    ctx = check_context(model=catlin_model)
    sump = catlin_plan.by_tag("SM-B-RADON")
    feeders = interior_tile_feeders(ctx, sump)
    assert len(feeders) == 19 and all(tag.startswith("FB-B-") for tag in feeders)
    finding = next(f for f in radon_control_system(ctx) if "SM-B-RADON" in f.message)
    assert finding.result is Result.PASS and "subpart 4.E" in finding.message


def test_a_pit_off_the_tile_is_unknown(catlin_model):
    """Move the pit off the corner to its 2026-09-23 station: no house stone reaches it, so
    the connection 4.E asks for is not shown, and a sealed lid alone does not show it."""
    ctx = check_context(model=_with_pit(catlin_model, _square(5.75, 28.0)))
    assert interior_tile_feeders(ctx, catlin_model.plan.by_tag("SM-B-RADON")) == []
    finding = next(f for f in radon_control_system(ctx) if "SM-B-RADON" in f.message)
    assert finding.result is Result.UNKNOWN and "4.E" in finding.message
