"""A hung luminaire's cable: resolved to what is overhead, drawn, and graded for reach."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from shapely.geometry import Polygon

from typehaus.checks.mep.lighting_suspension import suspension_reach
from typehaus.findings import Result
from typehaus.model.canvas import resolved_canvas_objects
from typehaus.resolve.stair_headroom import headroom_prisms

INCH = 0.0254


def _chandelier(model):
    return next(o for o in model.canvas_objects if o.tag == "ED-S-STAIR-CHAND")


def _grade(plan, *objects):
    ctx = SimpleNamespace(plan=plan, model=SimpleNamespace(canvas_objects=list(objects)))
    return suspension_reach(ctx)


def test_the_stair_chandelier_hangs_from_the_rafters_within_its_wire(catlin_model_ro):
    item = _chandelier(catlin_model_ro)
    assert item.suspended_from == "RF-HOUSE"
    # 27'-3" (project) under the 6:12 rafters, less a 5'-6" hang over a 10'-1" floor and
    # the 6' cascade band: ~68" of cable, 140" overall of the 156" the product ships.
    assert 60 * INCH < item.suspension_m < 76 * INCH
    assert item.suspension_m + 72 * INCH <= 156 * INCH


def test_the_lowest_globe_clears_the_stair_headroom_it_overhangs(catlin_model_ro):
    item = _chandelier(catlin_model_ro)
    body = Polygon(item.footprint)
    under = [p for p in headroom_prisms(catlin_model_ro)
             if p.stair_tag == "ST-M2S" and p.footprint.intersects(body)]
    assert under, "the 23-inch cascade should overhang the flight in plan"
    assert all(p.z1_m < item.z_m for p in under)


def test_model_json_carries_the_cable_and_canopy(catlin_model_ro):
    record = next(r for r in resolved_canvas_objects(catlin_model_ro)
                  if r["tag"] == "ED-S-STAIR-CHAND")
    hang = record["suspension"]
    assert hang["from"] == "RF-HOUSE"
    assert abs(hang["canopy_m"] - 23 * INCH) < 1e-9
    assert hang["z1_m"] > hang["z0_m"]


def test_a_seated_pendant_carries_no_drawn_cable(catlin_model_ro):
    record = next(r for r in resolved_canvas_objects(catlin_model_ro)
                  if r["tag"] == "ED-M-DINING-PEND")
    assert record["suspension"] is None


def test_reach_grades_every_case(catlin_plan, catlin_model_ro):
    item = _chandelier(catlin_model_ro)
    ok, = _grade(catlin_plan, item)
    assert ok.result is Result.PASS
    too_far, = _grade(catlin_plan, replace(item, suspension_m=100 * INCH))
    assert too_far.result is Result.FAIL and "ships 156.0\"" in too_far.message
    through, = _grade(catlin_plan, replace(item, suspension_m=-6 * INCH))
    assert through.result is Result.FAIL and "up through RF-HOUSE" in through.message
    floating, = _grade(catlin_plan, replace(item, suspension_m=None, suspended_from=None))
    assert floating.result is Result.UNKNOWN
    unrated = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-M-DINING-PEND")
    hung, = _grade(catlin_plan, replace(unrated, suspension_m=12 * INCH))
    assert hung.result is Result.UNKNOWN and "max_overall_height" in hung.message


def test_no_hung_luminaire_is_not_applicable(catlin_plan):
    finding, = _grade(catlin_plan)
    assert finding.result is Result.NOT_APPLICABLE
