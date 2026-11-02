"""Physical frame/leaf geometry and the Python/canvas parity contract."""

import json
import math
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.emit.draw.door_symbols import (
    DOOR_SWING,
    DOOR_SWING_DOUBLE,
    door_symbol_geometry,
    door_symbol_params,
)
from typehaus.emit.draw.dxf_writer import write_dxf
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.scene import Scene, Symbol
from typehaus.resolve.door_plan_dimensions import door_plan_dimensions
from typehaus.server.model_json_opening_parts import door_plan_dimensions_json

INCH_M = 0.0254
FIXTURES = (Path(__file__).resolve().parents[3]
            / "ui/src/model/swingDoorFixtures.json")


def _symbol_from_fixture(case):
    inputs = case["input"]
    dimensions = inputs["dimensions"]
    rotation = -inputs["angleRadians"]
    scale = inputs["pixelsPerMeter"]
    center = (inputs["center"][0] / scale, -inputs["center"][1] / scale)
    along = (0 if inputs["doubleSwing"] else
             inputs["hingeSign"] * dimensions["hinge_half_m"])
    normal = dimensions["leaf_normal_m"]
    insert = ((center[0] + math.cos(rotation) * along - math.sin(rotation) * normal) / INCH_M,
              (center[1] + math.sin(rotation) * along + math.cos(rotation) * normal) / INCH_M)
    name = DOOR_SWING_DOUBLE if inputs["doubleSwing"] else DOOR_SWING
    params = door_symbol_params(
        name, dimensions["leaf_width_m"] / INCH_M, 80, inputs["operatingSign"],
        hinge_jamb_sign=inputs["hingeSign"], host_wall_thickness_in=6.5,
        maximum_opening_degrees=inputs["maximumOpeningDegrees"])
    params.update({key.removesuffix("_m") + "_in": value / INCH_M
                   for key, value in dimensions.items() if key != "leaf_width_m"})
    return Symbol(name=name, insert=insert, rotation=math.degrees(rotation),
                  scale=1, layer="A-DOOR", params=params)


@pytest.mark.parametrize("case", json.loads(FIXTURES.read_text()))
def test_swing_outlines_share_the_canvas_contract(case):
    geometry = door_symbol_geometry(_symbol_from_fixture(case))
    inputs = case["input"]
    scale = inputs["pixelsPerMeter"]
    count = 2 if inputs["doubleSwing"] else 1
    for kind, strokes in (("leaves", geometry.strokes[:count]),
                          ("jambs", geometry.strokes[count:])):
        assert len(strokes) == len(case["expected"][kind])
        for stroke, expected in zip(strokes, case["expected"][kind], strict=True):
            for point, expected_point in zip(stroke.points, expected, strict=True):
                assert (point[0] * INCH_M * scale, -point[1] * INCH_M * scale) \
                    == pytest.approx(expected_point)
    d = inputs["dimensions"]
    for leaf, arc in zip(geometry.strokes[:count], geometry.arcs, strict=True):
        assert leaf.points[0] == leaf.points[-1] == arc.center
        assert math.dist(leaf.points[0], leaf.points[1]) * INCH_M \
            == pytest.approx(d["leaf_width_m"] / count)
        assert math.dist(leaf.points[1], leaf.points[2]) * INCH_M \
            == pytest.approx(d["leaf_thickness_m"])
        assert arc.radius * INCH_M == pytest.approx(d["leaf_width_m"] / count)
        assert (arc.end_angle_deg - arc.start_angle_deg) % 360 \
            == pytest.approx(inputs["maximumOpeningDegrees"])
        # At halfway, the arc must lie on the authored operating side, even at 180°.
        angle = math.radians(arc.start_angle_deg + inputs["maximumOpeningDegrees"] / 2)
        normal = math.sin(angle - math.radians(_symbol_from_fixture(case).rotation))
        assert normal * inputs["operatingSign"] > 0


def test_held_rough_opening_keeps_shims_outside_the_visible_jamb():
    opening = SimpleNamespace(
        width_m=0.95, cased_product=None, doorway=None,
        sizing=SimpleNamespace(rough_w_m=0.95, jamb_allowance_m=0.0254,
                               leaf_w_m=0.8932, held=True))
    wall = SimpleNamespace(axis=((0, 0), (1, 0)), depth_layers=lambda: [], thickness_m=0.15)
    dimensions = door_plan_dimensions(opening, wall)
    assert dimensions.hinge_half_m == pytest.approx(0.95 / 2 - 0.0254)
    assert dimensions.leaf_width_m == opening.sizing.leaf_w_m
    assert dimensions.jamb_thickness_m < opening.sizing.jamb_allowance_m
    assert dimensions.hinge_half_m + dimensions.jamb_thickness_m < opening.width_m / 2


def test_dxf_exports_closed_frame_and_leaf_outlines(tmp_path):
    import ezdxf

    symbol = _symbol_from_fixture(json.loads(FIXTURES.read_text())[0])
    path = write_dxf(Scene(name="door", nodes=(symbol,)), tmp_path / "door.dxf")
    entities = ezdxf.readfile(path).modelspace()
    outlines = list(entities.query("LWPOLYLINE"))
    assert len(outlines) == 3
    for outline in outlines:
        points = list(outline.get_points("xy"))
        assert len(points) == 5
        assert points[0] == pytest.approx(points[-1])
    arc, = entities.query("ARC")
    assert arc.dxf.radius == pytest.approx(symbol.params["width_in"])


def test_product_stock_and_exterior_frame_depth_override_schematic_dimensions():
    product = SimpleNamespace(finish_faces_m=(-0.06, 0.09), leaf_thickness_m=0.04,
                              jamb_thickness_m=0.016)
    placement = SimpleNamespace(frame_inner_m=0.12, frame_outer_m=-0.03, leaf_normal_m=0.08)
    opening = SimpleNamespace(width_m=0.95, sizing=None, cased_product=product,
                              doorway=SimpleNamespace(exterior_placement=placement))
    dimensions = door_plan_dimensions(opening, None)
    assert dimensions.leaf_thickness_m == 0.04
    assert dimensions.jamb_thickness_m == 0.016
    assert dimensions.frame_normal_low_m == -0.03
    assert dimensions.frame_normal_high_m == 0.12
    assert dimensions.leaf_normal_m == 0.08


def test_catlin_drawing_and_json_use_the_same_resolved_dimensions(catlin_model_ro):
    model = catlin_model_ro
    symbols = {node.uid: node for storey in model.plan.storeys
               for node in build_floorplan(model, storey.tag).nodes
               if isinstance(node, Symbol) and node.name in (DOOR_SWING, DOOR_SWING_DOUBLE)}
    assert len(symbols) >= 25
    for opening in model.openings:
        if opening.uid not in symbols:
            continue
        dimensions = door_plan_dimensions(opening, model.wall(opening.host_wall))
        assert door_plan_dimensions_json(model, opening) == asdict(dimensions)
        node = symbols[opening.uid]
        assert node.params["width_in"] * INCH_M == pytest.approx(dimensions.leaf_width_m)
        for key, value in asdict(dimensions).items():
            if key != "leaf_width_m":
                assert node.params[key.removesuffix("_m") + "_in"] * INCH_M \
                    == pytest.approx(value)
        expected_strokes = 4 if node.name == DOOR_SWING_DOUBLE else 3
        assert len(door_symbol_geometry(node).strokes) == expected_strokes
