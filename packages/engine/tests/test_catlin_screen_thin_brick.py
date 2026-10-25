"""Screen veneer regressions: east/west datums, actual areas/mass and stopped door."""
import math

import pytest
from shapely.geometry import Point, Polygon

from typehaus.resolve.assembly_weight import dead_load_plf, wall_line_plf
from typehaus.takeoff.envelope import envelope_layer_takeoff

INCH = 0.0254


def test_east_brick_does_not_move_studs_or_west_skin(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    layers = {layer.name: layer for layer in wall.layers}
    for name, expected in {"stud": (70.25, 73.75), "cdx-out": (69.625, 70.25),
                           "cladding-out": (68.75, 69.625),
                           "siding-in": (74.875, 75.5),
                           "thin-brick-in": (76.405, 76.905)}.items():
        xs = [x / INCH for x, _y in layers[name].polygon]
        assert (min(xs), max(xs)) == pytest.approx(expected)
    assert wall.axis[0][0] / INCH == pytest.approx(72)
    assert tuple(v / INCH for v in layers["thin-brick-in"].band(wall)) == pytest.approx((2, 47.5))
    assert layers["thin-brick-in"].thickness_m / INCH == pytest.approx(0.5)
    assert min(x for x, _ in layers["siding-in"].polygon) / INCH - 74.75 == pytest.approx(0.125)
    assert catlin_model_ro.plan.by_tag(wall.tag).shear_panel.sheathing_layer == "cdx-out"


def test_veneer_uses_its_own_net_area_and_purchased_slip_appearance(catlin_model_ro):
    rows = [row for row in envelope_layer_takeoff(catlin_model_ro)
            if "W-BW-SCREEN" in row.get("tags", ())]
    brick = next(row for row in rows if row["material"] == "thin-brick-brown")
    assert brick["area_ft2"] == pytest.approx(78.875 * 45.5 / 144, abs=0.1)
    material = next(m for m in catlin_model_ro.plan.library.materials if m.tag == "thin-brick-brown")
    assert (material.finish, material.color) == ("brown-brick", "#a07c5c")
    assert material.product_ref == "PROD-BW-THIN-BRICK"


def test_screen_load_is_known_and_skirt_is_not_its_bearing(catlin_ctx):
    from typehaus.checks.structural.masonry_load import support_at

    wall = catlin_ctx.model.wall("W-BW-SCREEN")
    own = dead_load_plf(catlin_ctx, wall, wall.z1_m - wall.z0_m)
    assert own is not None and 70 < own < 80
    total, basis = wall_line_plf(catlin_ctx, wall)
    assert total is not None and total > own
    assert "SB-BW-BAND" in basis
    assert support_at(catlin_ctx, wall, wall.axis[0])[1] != "W-BW-SCREEN-SKIRT"


def test_real_positive_stop_reaches_exports_and_clearance_sector(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    hinge = door.swing_clearance[0]
    tip = door.swing_clearance[-1]
    assert (tip[0] - hinge[0]) / INCH == pytest.approx(36 * math.cos(math.radians(85)))
    assert (tip[1] - hinge[1]) / INCH == pytest.approx(-36 * math.sin(math.radians(85)))
    exported = next(o for o in model_to_dict(catlin_model_ro)["openings"] if o["tag"] == door.tag)
    assert exported["maximum_opening_degrees"] == 85
    # The veneer is outside the idealized leaf's entire sweep, not merely its parked line.
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    brick = next(layer for layer in wall.layers if layer.name == "thin-brick-in")
    assert not Polygon(door.swing_clearance).intersects(Polygon(brick.polygon))
    assert not Polygon(brick.polygon).covers(Point(hinge))
