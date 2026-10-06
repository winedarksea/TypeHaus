"""Buildable cabinet joins, working faces and clearances in the revised kitchen."""

import math
from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon, box

from typehaus.cli.prices import load_prices
from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.model.placeable_symbols._sektion_corner_wall import sektion_corner_wall
from typehaus.server.model_json import model_to_dict
from typehaus.takeoff import placeables_takeoff

INCH = 0.0254
FINISH_TOLERANCE = 0.03125 * INCH
DOOR_FRONT_ALLOWANCE_IN = 1.0
PANTRY_DOOR_WIDTH_IN = 24.0
PANTRY_RACK_EXTENSION_IN = 18.5


@pytest.fixture(scope="module")
def kitchen_objects(catlin_model_ro):
    return {item.tag: item for item in catlin_model_ro.canvas_objects}


def _bounds(item):
    return tuple(value / INCH for value in Polygon(item.footprint).bounds)


def test_stock_north_modules_close_without_a_filler(catlin_plan, kitchen_objects):
    modules = (
        ("FURN-M-KIT-E1", "SEKT-B12", 297.375, 309.375),
        ("FURN-M-KIT-SINKBASE", "SEKT-SINK-B36", 333.375, 369.375),
        ("FURN-M-KIT-E2", "SEKT-B18", 369.375, 387.375),
    )
    for tag, type_ref, west, east in modules:
        obj = kitchen_objects[tag]
        assert obj.type_ref == type_ref
        assert (_bounds(obj)[0], _bounds(obj)[2]) == pytest.approx((west, east))
    dishwasher = catlin_plan.by_tag("APPL-M-DW")
    assert dishwasher.position.x.inches == pytest.approx((309.375 + 333.375) / 2)
    assert "FURN-M-KIT-E2-FILLER" not in kitchen_objects
    assert "FURN-M-KIT-WE2" not in kitchen_objects
    assert "FURN-M-KIT-WE2-ST" not in kitchen_objects
    upper = kitchen_objects["FURN-M-KIT-WE1"]
    assert (_bounds(upper)[0], _bounds(upper)[2]) == pytest.approx((297.375, 333.375))


def test_stock_cold_uppers_preserve_hinge_clearance_and_appliance_joint(
    catlin_plan, kitchen_objects
):
    freezer = kitchen_objects["FURN-M-KIT-OVER-FREEZER"]
    refrigerator = kitchen_objects["FURN-M-KIT-OVER-FRIDGE"]
    types = {item.tag: item for item in catlin_plan.library.furniture_types}
    frame = types["SEKT-TS30-20"]
    assert tuple(value.inches for value in frame.footprint) == pytest.approx((30, 24))
    assert frame.height.inches == pytest.approx(20)
    assert "402.655.12" in frame.source
    assert "FT-KIT-DEEP30-30" not in types
    cabinet_mount = catlin_plan.by_tag("FURN-M-KIT-OVER-FREEZER").mount.elevation.meters
    finished_floor_z = freezer.body_z0_m - cabinet_mount
    for cabinet, appliance_tag in (
        (freezer, "APPL-M-FREEZER"), (refrigerator, "APPL-M-FRIDGE")
    ):
        appliance = kitchen_objects[appliance_tag]
        assert cabinet.type_ref == "SEKT-TS30-20"
        assert (cabinet.body_z0_m - finished_floor_z) / INCH == pytest.approx(73.5)
        assert (cabinet.body_z1_m - finished_floor_z) / INCH == pytest.approx(93.5)
        assert (cabinet.body_z0_m - appliance.body_z1_m) / INCH == pytest.approx(1)
        assert _bounds(cabinet)[2] == pytest.approx(243.375, abs=0.03125)
        assert f"{cabinet.tag}-ST" not in kitchen_objects
    assert (_bounds(freezer)[1], _bounds(freezer)[3]) == pytest.approx((331.75, 361.75))
    assert (_bounds(refrigerator)[1], _bounds(refrigerator)[3]) == pytest.approx(
        (361.75, 391.75)
    )
    south = _bounds(kitchen_objects["APPL-M-FREEZER"])[1]
    north = _bounds(kitchen_objects["APPL-M-FRIDGE"])[3]
    assert _bounds(freezer)[1] - south == pytest.approx(2.875)
    assert north - _bounds(refrigerator)[3] == pytest.approx(2.875)
    # The rail near the frame top needs its own band, independent of lower restraint.
    backing = catlin_plan.by_tag("BK-M-C5-COLD-TOP")
    assert backing.wall_ref == "W-M-C5"
    rail_screw_elevation = refrigerator.body_z1_m - INCH
    assert backing.elevation.meters < rail_screw_elevation
    assert rail_screw_elevation < backing.elevation.meters + backing.height.meters


def test_sink_centres_on_fixed_window_and_drain_components_move_together(catlin_model_ro):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    sink = objects["FX-M-KITCH-SINK"]
    base = objects["FURN-M-KIT-SINKBASE"]
    assert sink.type_ref == "FX-KITCHEN-SINK-32-SINGLE"
    assert (sink.position[0] - base.position[0]) / INCH == pytest.approx(0.625)
    window = next(item for item in catlin_model_ro.openings if item.tag == "WIN-M-KITCH")
    wall = catlin_model_ro.wall(window.host_wall)
    window_x = wall.axis[0][0] - window.center_along_m
    assert sink.position[0] == pytest.approx(window_x)
    plan = catlin_model_ro.plan
    expected = (352 * INCH, 416.875 * INCH)
    assert objects["APPL-M-DISP"].position == pytest.approx(expected, abs=FINISH_TOLERANCE)
    assert plan.by_tag("FX-M-KITCH-SINK").drain_position.xy_m == pytest.approx(expected)
    assert plan.by_tag("SP-M-KITCH").position.xy_m == pytest.approx(expected)
    assert plan.by_tag("CO-B-KITCH-HEAD").position.xy_m == pytest.approx(expected)
    assert plan.by_tag("CO-B-KITCH-HEAD").cap_position.xy_m == pytest.approx(expected)
    assert plan.by_tag("PR-B-KITCH-DRAIN").path[0].xy_m == pytest.approx(expected)
    assert plan.by_tag("PR-B-KITCH-DRAIN").path[1].xy_m == pytest.approx(expected)
    assert plan.by_tag("PR-B-KITCH-DRAIN").path[2].xy_m == pytest.approx((216 * INCH, 420 * INCH))


def test_single_bowl_opening_fits_offset_base_and_meets_quartz_underside(catlin_model_ro):
    from typehaus.resolve.geometry_countertops import countertop_prisms

    model = catlin_model_ro
    objects = {item.tag: item for item in model.canvas_objects}
    sink = objects["FX-M-KITCH-SINK"]
    base = objects["FURN-M-KIT-SINKBASE"]
    top = next(item for item in model.countertops if item.tag == "CT-M-KIT-N")
    hole = Polygon(top.cutouts[0])
    expected_bounds = tuple(value * INCH for value in (337, 403.375, 367, 420.375))
    assert hole.bounds == pytest.approx(expected_bounds, abs=FINISH_TOLERANCE)
    assert hole.area == pytest.approx(30 * 17 * INCH * INCH)
    assert Polygon(base.footprint).buffer(-0.75 * INCH).contains(hole)
    # The 32-inch flange extends an inch past each bowl side; east panel has 5/8 inch left.
    assert (_bounds(base)[2] - 0.75) - (sink.position[0] / INCH + 16) == pytest.approx(0.625)
    prism = countertop_prisms(model, top)[0]
    assert sink.z_m + 10 * INCH == pytest.approx(prism.z0_m)
    assert prism.z1_m - 36 * INCH == pytest.approx(base.z_m)
    assert objects["APPL-M-DISP"].body_z1_m == pytest.approx(sink.z_m)
    from typehaus.takeoff.plumbing_calc import fixture_units

    units = next(row for row in fixture_units(model.plan) if row.tag == sink.tag)
    assert (units.dfu, units.wsfu_total, units.wsfu_hot, units.wsfu_cold) == (2.0, 1.5, 1.0, 1.0)


def test_diagonal_corner_closes_to_both_upper_runs(catlin_plan, kitchen_objects):
    corner = kitchen_objects["FURN-M-KIT-WN1"]
    assert corner.type_ref == "SEKT-CORNER-W26-30"
    assert corner.rotation_degrees == 0
    assert len(corner.footprint) == 5
    assert Polygon(corner.footprint).area < Polygon(corner.footprint).envelope.area
    assert _bounds(corner) == pytest.approx((399.375, 399.375, 425.375, 425.375), abs=0.03125)
    for neighbor in ("FURN-M-KIT-WE5-ST", "FURN-M-KIT-WN2"):
        assert (
            Polygon(corner.footprint).distance(Polygon(kitchen_objects[neighbor].footprint))
            < FINISH_TOLERANCE
        )
        # Attached paint faces differ from the nominal wall face by 0.01 inch.
        overlap = Polygon(corner.footprint).intersection(
            Polygon(kitchen_objects[neighbor].footprint)
        )
        assert overlap.area < FINISH_TOLERANCE * 15 * INCH
    typ = next(t for t in catlin_plan.library.furniture_types if t.tag == corner.type_ref)
    strokes, parts = sektion_corner_wall(*(v.meters for v in typ.footprint), typ.height.meters)
    assert strokes[0]["points"] == tuple(point.xy_m for point in typ.footprint_shape.points)
    door = parts[-1]["points"]
    assert math.dist(door[0], door[1]) / INCH == pytest.approx(14.875)


def test_garage_fronts_face_west_and_pullout_lands_on_counter(
    catlin_plan, catlin_model_ro, kitchen_objects
):
    for tag in ("FURN-M-KIT-MIXER-GARAGE", "FURN-M-KIT-MIXER-GARAGE-UP"):
        obj = kitchen_objects[tag]
        radians = math.radians(obj.rotation_degrees)
        assert (math.sin(radians), -math.cos(radians)) == pytest.approx((-1, 0), abs=1e-9)
    garage = kitchen_objects["FURN-M-KIT-MIXER-GARAGE"]
    x0, y0, _, y1 = _bounds(garage)
    deployed = box((x0 - PANTRY_RACK_EXTENSION_IN) * INCH, y0 * INCH, x0 * INCH, y1 * INCH)
    counters = [
        Polygon(top.outline)
        for top in catlin_model_ro.countertops
        if top.tag in ("CT-M-KIT-E", "CT-M-KIT-PENINSULA")
    ]
    assert counters[0].union(counters[1]).buffer(FINISH_TOLERANCE).covers(deployed)
    typ = next(
        t
        for t in catlin_plan.library.furniture_types
        if t.tag == kitchen_objects["FURN-M-KIT-MIXER-GARAGE-UP"].type_ref
    )
    assert typ.height.inches == 30
    assert typ.product_ref == "PROD-IKEA-SEKTION-BASE24-30"
    assert typ.plan_symbol == "wall-cabinet"


def test_pantry_joins_and_supported_full_depth_tops(catlin_plan, catlin_model_ro, kitchen_objects):
    s1, s2 = (kitchen_objects[f"FURN-M-KIT-PANTRY-S{n}"] for n in (1, 2))
    assert (_bounds(s2)[1], _bounds(s1)[3]) == pytest.approx((271.375, 319.375))
    assert _bounds(s2)[3] == pytest.approx(_bounds(s1)[1])
    assert _bounds(s1)[3] == pytest.approx(_bounds(kitchen_objects["FURN-M-KIT-MIXER-GARAGE"])[1])
    for n in (1, 2):
        top = kitchen_objects[f"FURN-M-KIT-PANTRY-S{n}-ST"]
        base = kitchen_objects[f"FURN-M-KIT-PANTRY-S{n}"]
        assert top.type_ref == "SEKT-TS24-15"
        assert _bounds(top) == pytest.approx(_bounds(base), abs=0.03125)
        assert _bounds(top)[2] - _bounds(top)[0] == pytest.approx(24)
        assert _bounds(top)[0] == pytest.approx(
            _bounds(kitchen_objects["FURN-M-KIT-MIXER-GARAGE-UP"])[0]
        )
        assert top.body_z0_m == pytest.approx(base.body_z1_m)
        assert (top.body_z1_m - top.body_z0_m) / INCH == pytest.approx(15)
        assert (top.body_z1_m - base.body_z0_m) / INCH == pytest.approx(98.5)
        assert f"FURN-M-KIT-PANTRY-S{n}-REAR-DECK" not in kitchen_objects
    assert "FURN-M-KIT-PANTRY-TOP-END" not in kitchen_objects
    shelf_type = next(
        t for t in catlin_plan.library.furniture_types if t.tag == "FT-KIT-PANTRY-SHELVES-70"
    )
    assert shelf_type.footprint[0].inches == 73.25
    assert catlin_plan.by_tag("FURN-M-PANTRY-SHELVES").position.x.inches == 256
    living_modules = [
        kitchen_objects[f"FURN-M-LIV-E-B36-{suffix}"]
        for suffix in ("E2", "E3", "MID", "PANTRY")
    ]
    assert [_bounds(item)[1] for item in living_modules] == pytest.approx(
        (127.25, 163.25, 199.25, 235.25)
    )
    assert [_bounds(item)[3] for item in living_modules] == pytest.approx(
        (163.25, 199.25, 235.25, 271.25)
    )
    assert all(item.type_ref == "SEKT-B36-D15" for item in living_modules)
    living_end = living_modules[-1]
    assert _bounds(living_end)[3] + 0.125 == pytest.approx(_bounds(s2)[1])
    living_top = next(top for top in catlin_model_ro.countertops if top.tag == "CT-M-LIV-E-N")
    assert Polygon(living_top.outline).bounds[3] / INCH == pytest.approx(271.375)
    bank = catlin_plan.by_tag("SB-M-PANTRY")
    assert [bay.width.inches for bay in bank.bays] == [36.25, 36.25]


def test_pantry_doors_and_racks_clear_the_seating_bar(catlin_model_ro, kitchen_objects):
    # The peninsula slab's seating knee: everything south of the cabinet backs.
    peninsula = Polygon(
        next(top for top in catlin_model_ro.countertops if top.tag == "CT-M-KIT-PENINSULA").outline
    )
    bar = peninsula.intersection(box(0, 0, 1000 * INCH, 319.375 * INCH))
    back = Polygon(kitchen_objects["FURN-M-KIT-PEN-BACK"].footprint)
    worktops = [
        Polygon(top.outline)
        for top in catlin_model_ro.countertops
        if top.tag in ("CT-M-KIT-PENINSULA", "CT-M-KIT-E", "CT-M-LIV-E-N")
    ]
    assert (bar.bounds[2] - bar.bounds[0]) / INCH == pytest.approx(73.5)
    assert bar.bounds[2] == pytest.approx(376.375 * INCH)
    assert back.bounds[2] == pytest.approx(bar.bounds[2])
    for n in (1, 2):
        front, south, _, north = _bounds(kitchen_objects[f"FURN-M-KIT-PANTRY-S{n}"])
        # Conservative filled quarter-sector for the entire 90-degree door sweep,
        # allowing a full inch for the front beyond the nominal frame envelope.
        hinge = Point((front - DOOR_FRONT_ALLOWANCE_IN) * INCH, south * INCH)
        sweep = hinge.buffer(PANTRY_DOOR_WIDTH_IN * INCH, quad_segs=64).intersection(
            box((front - 25) * INCH, south * INCH, front * INCH, north * INCH)
        )
        rack = box(
            (front - DOOR_FRONT_ALLOWANCE_IN - PANTRY_RACK_EXTENSION_IN) * INCH,
            south * INCH,
            front * INCH,
            north * INCH,
        )
        assert sweep.intersection(bar).area == 0
        assert sweep.intersection(back).area == 0
        assert rack.intersection(bar).area == 0
        assert all(
            sweep.intersection(top).area < 1e-12 and rack.intersection(top).area < 1e-12
            for top in worktops
        )
        for i in (1, 2, 3):
            stool = Polygon(kitchen_objects[f"FURN-M-KIT-STOOL{i}"].footprint)
            assert sweep.intersection(stool).area == 0
            assert rack.intersection(stool).area == 0
    stools = [kitchen_objects[f"FURN-M-KIT-STOOL{i}"] for i in (1, 2, 3)]
    assert [
        (b.position[0] - a.position[0]) / INCH for a, b in zip(stools, stools[1:], strict=False)
    ] == pytest.approx([24.5, 24.5])
    assert all(
        bar.bounds[0] < Polygon(stool.footprint).bounds[0]
        and Polygon(stool.footprint).bounds[2] < bar.bounds[2]
        for stool in stools
    )


def test_corner_payload_and_glb_share_the_diagonal_geometry(catlin_model_ro, kitchen_objects):
    corner = kitchen_objects["FURN-M-KIT-WN1"]
    typ = next(t for t in catlin_model_ro.plan.library.furniture_types if t.tag == corner.type_ref)
    payload = model_to_dict(catlin_model_ro)
    row = next(t for t in payload["catalog"]["canvas_object_types"] if t["tag"] == typ.tag)
    assert row["model_parts"]
    mesh = _MeshBuilder()
    assert _add_canvas_parts(mesh, corner, typ, {})
    positions = [point for points, _indices in mesh._buckets.values() for point in points]
    # glTF (x,z,-y) vertices retain the clipped corner instead of its bounding box.
    projected = Polygon([(x, -z) for x, _y, z in positions]).convex_hull
    assert projected.symmetric_difference(Polygon(corner.footprint)).area < 1e-8


def test_top_backing_is_emitted_below_the_stud_tops(catlin_plan, catlin_model_ro):
    # Authored backing above the studs is skipped by framing; a schedule entry alone
    # would therefore claim support while emitting no boards or lumber quantities.
    for wall_ref in ("W-M-N1", "W-M-E1"):
        wall = catlin_model_ro.wall(wall_ref)
        blocks = [
            member
            for member in wall.members
            if member.category == "blocking"
            and member.profile == "2x6"
            and member.z0_m == pytest.approx(99.5 * INCH)
            and member.z1_m == pytest.approx(105 * INCH)
        ]
        assert blocks
        band = catlin_plan.by_tag(wall_ref.replace("W-", "BK-", 1) + "-KIT-TOP")
        expected_length = band.length.meters if band.length else math.dist(*wall.axis)
        assert sum(block.length_m for block in blocks) == pytest.approx(expected_length)
    pantry_band = catlin_plan.by_tag("BK-M-E1-PANTRY-TOP")
    pantry_blocks = [
        member for member in catlin_model_ro.wall(pantry_band.wall_ref).members
        if member.category == "blocking" and member.profile == "2x4"
        and member.z0_m == pytest.approx(pantry_band.elevation.meters)
        and member.z1_m == pytest.approx(
            pantry_band.elevation.meters + pantry_band.height.meters
        )
    ]
    assert sum(block.length_m for block in pantry_blocks) == pytest.approx(
        pantry_band.length.meters
    )


def test_stock_replacements_and_supports_are_counted_and_priced(catlin_plan, catlin_model_ro):
    quantities = {
        row["type"]: row["count"]
        for row in placeables_takeoff(catlin_model_ro)
        if row["storey"] == "main"
    }
    prices = load_prices(Path(catlin_plan.source_root))
    expected = {
        "SEKT-B12": 1,
        "SEKT-B18": 1,
        "SEKT-W12-30": 1,
        "SEKT-CORNER-W26-30": 1,
        "SEKT-TS24-15": 2,
        "SEKT-TS30-20": 2,
        "FT-KIT-STOCK24-30-HUNG": 1,
        "SEKT-B36-D15": 6,
    }
    for type_ref, count in expected.items():
        assert quantities[type_ref] == count
        assert prices.placeables[type_ref].low > 0
    for removed in (
        "FT-KIT-FILLER-2375",
        "FT-LIV-E-FILLER-050",
        "SEKT-W24-20",
        "FT-KIT-DEEP24-20",
        "FT-KIT-DEEP30-30",
        "FT-KIT-TOP-REAR-DECK",
        "FT-KIT-TOP-REAR-END",
        "FT-KIT-DEEP24-30",
        "FT-LIV-E-STOCK12-PLINTH",
        "SEKT-B15-D15",
        "SEKT-B30-D15",
    ):
        assert removed not in quantities
        assert removed not in prices.placeables
