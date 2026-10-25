"""Screen veneer regressions: east/west datums, actual areas/mass and stopped door."""

import math

import pytest
from shapely.affinity import rotate, translate
from shapely.geometry import MultiPoint, box
from shapely.ops import unary_union

from typehaus.resolve.assembly_weight import dead_load_plf, wall_line_plf
from typehaus.takeoff.envelope import (
    envelope_layer_takeoff,
    wall_layer_net_area_m2,
    wall_net_areas_m2,
)

INCH = 0.0254


def test_east_brick_does_not_move_studs_or_west_skin(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    layers = {layer.name: layer for layer in wall.layers}
    for name, expected in {
        "stud": (70.25, 73.75),
        "cdx-out": (69.625, 70.25),
        "cladding-out": (68.75, 69.625),
        "siding-in": (74.875, 75.5),
        "thin-brick-in": (76.405, 76.905),
    }.items():
        xs = [x / INCH for x, _y in layers[name].polygon]
        assert (min(xs), max(xs)) == pytest.approx(expected)
    assert wall.axis[0][0] / INCH == pytest.approx(72)
    assert tuple(v / INCH for v in layers["thin-brick-in"].band(wall)) == pytest.approx((2, 47.5))
    assert layers["thin-brick-in"].thickness_m / INCH == pytest.approx(0.5)
    assert min(x for x, _ in layers["siding-in"].polygon) / INCH - 74.75 == pytest.approx(0.125)
    assert catlin_model_ro.plan.by_tag(wall.tag).shear_panel.sheathing_layer == "cdx-out"


def test_veneer_uses_its_own_net_area_and_purchased_slip_appearance(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    veneer = next(layer for layer in wall.layers if layer.name == "thin-brick-in")
    net = wall_net_areas_m2(catlin_model_ro)[wall.tag]
    screen_ft2 = wall_layer_net_area_m2(catlin_model_ro, wall, veneer, net) * 10.7639104
    assert screen_ft2 == pytest.approx(78.875 * 45.5 / 144, abs=0.1)
    # Rows carry no wall tags; the takeoff's one thin-brick row is the screen's area alone.
    rows = [
        row
        for row in envelope_layer_takeoff(catlin_model_ro)
        if row["material"] == "thin-brick-brown"
    ]
    assert len(rows) == 1
    assert rows[0]["net_area_sqft"] == pytest.approx(screen_ft2, abs=0.05)  # row rounds to 0.1
    material = next(
        m for m in catlin_model_ro.plan.library.materials if m.tag == "thin-brick-brown"
    )
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


def test_normal_swing_reaches_exports_and_preserves_east_jamb(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    hinge = door.swing_clearance[0]
    tip = door.swing_clearance[-1]
    assert door.type_ref == "DT-EXT-SWING32-G"
    assert door.width_m / INCH == pytest.approx(32)
    assert hinge[0] / INCH == pytest.approx(83)
    assert (hinge[0] + door.width_m) / INCH == pytest.approx(115)
    assert (tip[0] - hinge[0]) / INCH == pytest.approx(0)
    assert (tip[1] - hinge[1]) / INCH == pytest.approx(-32)
    exported = next(o for o in model_to_dict(catlin_model_ro)["openings"] if o["tag"] == door.tag)
    assert exported["maximum_opening_degrees"] == 90
    assert catlin_model_ro.plan.by_tag(
        "SL-D-NORTH-BRIDGE"
    ).cut_origin.x.meters / INCH == pytest.approx(99)


def test_entire_thick_leaf_and_lever_sweep_clears_nearby_geometry(catlin_model_ro):
    import runpy

    from _helpers import CATLIN

    from typehaus.emit.draw.elevation_project import solid_faces

    budget = runpy.run_path(str(CATLIN / "plan/entry_screen_finish_spec.py"))
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    half_leaf = budget["DOOR_LEAF_THICKNESS_IN"] / 2 * INCH
    lever_depth = half_leaf + budget["LEVER_PROJECTION_BUDGET_IN"] * INCH
    latch_station = door.width_m - budget["DOOR_BACKSET_IN"] * INCH
    # Both faces are budgeted; the lever reaches hingeward from the latch spindle.
    closed = unary_union(
        [
            box(0, -half_leaf, door.width_m, half_leaf),
            box(
                latch_station - budget["LEVER_HINGEWARD_EXTENT_IN"] * INCH,
                -lever_depth,
                latch_station,
                lever_depth,
            ),
        ]
    )
    limit = budget["DOOR_STOP_DEGREES"] + budget["DOOR_STOP_TOLERANCE_DEGREES"]
    assert limit == 91
    poses = [rotate(closed, -angle, origin=(0, 0)) for angle in range(int(limit) + 1)]
    radius = math.hypot(door.width_m, lever_depth)
    # Chords alone undercount rotation. Buffer each interval's hull by the maximum
    # vertex-arc sagitta, enclosing every intermediate angle, not just sampled poses.
    sagitta = radius * (1 - math.cos(math.radians(0.5)))
    swept = unary_union(
        [a.union(b).convex_hull.buffer(sagitta) for a, b in zip(poses, poses[1:], strict=False)]
    )
    swept = translate(swept, *door.swing_clearance[0])
    leaf_bottom = budget["DOOR_LEAF_BOTTOM_ABOVE_ROUGH_SILL_IN"] * INCH
    allowance = budget["INSTALLATION_TOLERANCE_IN"] * INCH
    required = budget["MINIMUM_HARDWARE_CLEARANCE_IN"] * INCH
    tags = {element.uid: element.tag for element in catlin_model_ro.plan.all_elements()}
    tags.update({solid.uid: solid.tag for solid in catlin_model_ro.solids})
    checked = set()
    minimum = (float("inf"), "")
    for element in catlin_model_ro.geometry.elements:
        tag = tags.get(
            element.uid,
            tags.get(element.uid.split("::")[0], tags.get(element.uid[:10], element.uid)),
        )
        # The host and this opening's frame/flashing belong to the fitted prehung
        # assembly, checked separately by the door-installation regressions.
        if tag == door.host_wall or tag.startswith(door.tag):
            continue
        for part in element.parts:
            for solid in part.solids:
                faces = list(solid_faces(solid))
                vertices = [point for face in faces for point in face]
                if (
                    not vertices
                    or max(p[2] for p in vertices) <= 0
                    or min(p[2] for p in vertices) >= door.height_m
                ):
                    continue
                points = []
                # Clip sloped faces to leaf height before projection: straps below the
                # deck and sloping stair rails otherwise cast false plan obstructions.
                for face in faces:
                    clipped = list(face)
                    lower_clip = leaf_bottom if max(p[2] for p in vertices) >= leaf_bottom else 0.0
                    for height, sign in ((lower_clip, 1), (door.height_m, -1)):
                        output = []
                        for start, end in zip(clipped, clipped[1:] + clipped[:1], strict=True):
                            inside_start = sign * (start[2] - height) >= 0
                            inside_end = sign * (end[2] - height) >= 0
                            if inside_start:
                                output.append(start)
                            if inside_start != inside_end:
                                fraction = (height - start[2]) / (end[2] - start[2])
                                output.append(
                                    tuple(
                                        start[k] + fraction * (end[k] - start[k]) for k in range(3)
                                    )
                                )
                        clipped = output
                    points.extend(clipped)
                if not points:
                    continue
                footprint = MultiPoint([(p[0], p[1]) for p in points]).convex_hull
                if not footprint.intersects(swept.buffer(INCH * 12)):
                    continue
                vertical_gap = max(0, leaf_bottom - max(p[2] for p in vertices))
                clearance = math.hypot(swept.distance(footprint), vertical_gap) - allowance
                checked.add(tag)
                minimum = min(minimum, (clearance / INCH, tag))
                assert clearance >= required, (tag, part.key, clearance / INCH)
    assert {"W-BW-SCREEN", "PT-BW-CNW", "CN-BW-TIE-GEB"} <= checked
    assert any(tag.startswith("TR-BW-BRICK-HEAD") for tag in checked)
    print(f"Continuous 0..91deg swing minimum after installation allowance: {minimum}")


def test_service_door_takeoff_uses_masonite_32in_price(catlin_model_ro):
    from _helpers import CATLIN

    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.openings import opening_takeoff

    rows = [r for r in opening_takeoff(catlin_model_ro) if "D-G-SERVICE" in r["tags"]]
    assert len(rows) == 1
    assert (rows[0]["type"], rows[0]["width_in"], rows[0]["count"]) == ("DT-EXT-SWING32-G", 32, 1)
    door_type = next(t for t in catlin_model_ro.plan.library.door_types if t.tag == rows[0]["type"])
    assert door_type.product_ref == "PROD-MASONITE-STEEL-FLUSH"
    prices = load_prices(CATLIN)
    assert "finish-door-closer-hold-open" not in prices.allowances
    from dataclasses import replace

    estimate = estimate_costs({"openings": rows}, replace(prices, allowances={}))
    assert estimate["sections"]["openings"]["subtotal"]["low"] >= 620
    assert estimate["sections"]["openings"]["subtotal"]["high"] >= 1320
    assert not estimate["unpriced"]
