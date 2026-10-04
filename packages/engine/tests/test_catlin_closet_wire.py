"""The west replacement joins the corner shelves and rods in resolved viewer geometry."""

from math import hypot

import pytest
from shapely.geometry import Polygon

from typehaus.model.placeable_symbols import model_parts, place_local, plan_symbol_strokes

INCH_M = 0.0254


@pytest.mark.parametrize("tier", ("HI", "LO"))
def test_west_wire_continues_corner_shelf_and_rod(catlin_plan, catlin_model_ro, tier):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    corner = objects[f"FURN-M-CLOSET-CORNER-{tier}"]
    west = objects[f"FURN-M-CLOSET-WEST-{tier}"]
    types = {item.tag: item for item in catlin_plan.library.furniture_types}
    corner_type, west_type = types[corner.type_ref], types[west.type_ref]
    assert "FURN-M-CLOSET-PAX-WEST" not in objects
    assert west.z_m == pytest.approx(corner.z_m)
    assert west.body_z1_m == pytest.approx(corner.body_z1_m)
    corner_shape, west_shape = Polygon(corner.footprint), Polygon(west.footprint)
    assert corner_shape.intersection(west_shape).area < 1e-9
    assert west_shape.bounds[3] == pytest.approx(corner_shape.bounds[1], abs=1e-8)
    assert west_shape.bounds[0] == pytest.approx(corner_shape.bounds[0], abs=1e-8)
    assert west_shape.bounds[2] == pytest.approx(corner_shape.bounds[0] + 12 * INCH_M,
                                               abs=1e-8)

    def rod_endpoint(item, item_type, end):
        width, depth = (length.meters for length in item_type.footprint)
        stroke = plan_symbol_strokes(item_type.plan_symbol, width, depth)[-1]
        return place_local(stroke["points"], item.position, item.rotation_degrees)[end]

    corner_end = rod_endpoint(corner, corner_type, -1)
    west_end = rod_endpoint(west, west_type, -1)
    assert hypot(corner_end[0] - west_end[0], corner_end[1] - west_end[1]) < 1e-8
    corner_parts = model_parts(corner_type.plan_symbol, *(v.meters for v in
                                corner_type.footprint), corner_type.height.meters)
    west_parts = model_parts(west_type.plan_symbol, *(v.meters for v in
                              west_type.footprint), west_type.height.meters)
    # The rod connection must meet vertically as well as in the plan glyph.
    assert west_parts[-1]["center"][2] == pytest.approx(corner_parts[-1]["center"][2])
    assert west_parts[-1]["size"][2] == pytest.approx(corner_parts[-1]["size"][2])


def test_retired_west_pax_lighting_and_backing_are_removed(catlin_plan):
    tags = {item.tag for item in catlin_plan.all_elements()}
    assert not {"LR-M-CLOSET-PAX-WEST", "BK-M-BA2E2-PAX"} & tags
