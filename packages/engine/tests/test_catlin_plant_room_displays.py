"""Plant displays, complete counts and the framing they are attached to."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.model.placeable_symbols import model_parts
from typehaus.quantities import inch
from typehaus.resolve.framing.backing_panels import backing_bands
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.takeoff.placeables import placeables_takeoff

STAND_TYPE = "FT-PLANT-ROOM-SKUGGRONA"
POT_TYPE = "FT-PLANT-ROOM-POT-3P5"
BASKET_TYPE = "FT-PLANT-ROOM-HANGING-VINE-12"


def test_display_counts_and_grouping_reach_the_model_and_takeoff(catlin_model_ro):
    objects = catlin_model_ro.canvas_objects
    expected_counts = {STAND_TYPE: 4, POT_TYPE: 12, BASKET_TYPE: 2}
    rows = {row["type"]: row for row in placeables_takeoff(catlin_model_ro)}
    for type_ref, expected in expected_counts.items():
        instances = [obj for obj in objects if obj.type_ref == type_ref]
        assert len(instances) == expected
        assert len({obj.uid for obj in instances}) == expected
        assert all(obj.room == "RM-S-PLANT" and obj.storey == "second" for obj in instances)
        assert rows[type_ref]["count"] == expected
    for number in range(1, 5):
        stand = f"FURN-S-PLANT-STAND-{number}"
        grouped = {obj.tag for obj in objects if obj.placement_group == stand}
        assert grouped == {stand, *(f"{stand}-POT-{level}" for level in range(1, 4))}


def test_stands_are_centered_on_the_desk_with_supported_separate_pots(catlin_model_ro):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    room = next(room for room in model.rooms if room.tag == "RM-S-PLANT")
    floor = room_finished_floor_elevation(model, room)
    stands = [objects[f"FURN-S-PLANT-STAND-{number}"] for number in range(1, 5)]
    assert sum(stand.position[0] for stand in stands) / 4 == pytest.approx(
        objects["FURN-S-PLANT-DESK"].position[0])
    assert [b.position[0] - a.position[0] for a, b in zip(stands, stands[1:], strict=False)] \
        == pytest.approx([inch(24).meters] * 3)
    for stand in stands:
        assert stand.z_m - floor == pytest.approx(inch(48).meters)
        assert stand.attachment_face == "right"
        product = next(t for t in model.plan.library.furniture_types if t.tag == stand.type_ref)
        trays = [part for part in model_parts(product.plan_symbol,
                 *(length.meters for length in product.footprint), product.height.meters)
                 if part["shape"] == "prism"]
        for level, tray in enumerate(trays, 1):
            pot = objects[f"{stand.tag}-POT-{level}"]
            assert pot.position == pytest.approx(stand.position)
            assert pot.z_m == pytest.approx(
                stand.z_m + tray["center"][2] + tray["size"][2] / 2)


def test_both_brackets_have_blocks_flush_to_studs_with_two_supported_ends(
    catlin_plan, catlin_model_ro,
):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    authored = [item for item in catlin_plan.all_elements()
                if item.tag.startswith("BK-S-PLANT-STAND-")]
    assert len(authored) == 8
    for number in range(1, 5):
        stand = objects[f"FURN-S-PLANT-STAND-{number}"]
        wall = model.wall(stand.attachment_wall)
        structure = next(layer for layer in wall.layers
                         if layer.function == "structure" and not layer.is_cavity)
        right_face_y = min(point[1] for point in structure.polygon)
        studs = [member for member in wall.members if member.category == "stud"]
        stud_faces_x = [member.p0[0] + inch(offset).meters
                        for member in studs for offset in (-0.75, 0.75)]
        bracket_spacing = 0.720  # IKEA AA-2435064-2, broad-back mounting.
        height = inch(30.75).meters
        bracket_offset = (height - bracket_spacing) / 2
        for course, bracket_height in (("LOW", bracket_offset),
                                       ("HIGH", bracket_offset + bracket_spacing)):
            block = catlin_plan.by_tag(f"BK-S-PLANT-STAND-{number}-{course}")
            assert block.wall_ref == stand.attachment_wall and block.face == "right"
            bands = sorted(backing_bands(catlin_plan)[wall.tag],
                           key=lambda band: (band.elevation_m, band.tag))
            index = next(index for index, band in enumerate(bands) if band.tag == block.tag)
            member = next(member for member in wall.members
                          if member.child_key == f"backing-{index}-000")
            footprint, z0, z1 = member_footprint(member)
            assert min(point[1] for point in footprint) == pytest.approx(right_face_y)
            assert stand.z_m + bracket_height >= z0
            assert stand.z_m + bracket_height <= z1
            assert member.p0[0] <= stand.position[0] <= member.p1[0]
            for end in (member.p0[0], member.p1[0]):
                assert min(abs(end - face) for face in stud_faces_x) < 1e-8
            assert member.length_m == pytest.approx(inch(14.5).meters)


def test_baskets_meet_finished_ceiling_over_existing_joist_and_clear_exhaust(catlin_model_ro):
    model = catlin_model_ro
    room = next(room for room in model.rooms if room.tag == "RM-S-PLANT")
    room_bounds = Polygon(room.clear_face).bounds
    ceiling = next(ceiling for ceiling in model.ceilings if ceiling.room_ref == room.tag)
    floor = room_finished_floor_elevation(model, room)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    baskets = [objects[f"FURN-S-PLANT-HANG-{corner}"] for corner in ("NW", "NE")]
    joists = next(floor for floor in model.floors if floor.tag == "FS-ATTIC").members
    for basket, side in zip(baskets, (room_bounds[0], room_bounds[2]), strict=True):
        assert abs(basket.position[0] - side) == pytest.approx(inch(18).meters)
        assert basket.position[1] == pytest.approx(inch(96).meters)
        assert basket.body_z1_m == pytest.approx(ceiling.z0_m)
        assert any(member.category == "joist" and
                   abs(member.p0[1] - basket.position[1]) < 1e-8 and
                   member.p0[0] <= basket.position[0] <= member.p1[0] for member in joists)
        assert Polygon(room.clear_face).covers(Polygon(basket.footprint))
        assert basket.z_m + inch(24).meters - floor == pytest.approx(
            inch(84).meters, abs=inch(0.5).meters)
    east_edge = Polygon(baskets[1].footprint).bounds[2]
    grille_edge = Polygon(objects["REG-S-ERV-PLANT-EXH"].footprint).bounds[0]
    assert grille_edge - east_edge >= inch(6).meters


def test_displays_clear_existing_bodies_in_three_dimensions(catlin_model_ro):
    objects = catlin_model_ro.canvas_objects
    displays = [obj for obj in objects if obj.type_ref in {STAND_TYPE, POT_TYPE, BASKET_TYPE}]
    existing_tags = {"FURN-S-PLANT-CHAIR", "FURN-S-PLANT-ROCKER", "FURN-S-PLANT-DESK",
                     "ED-S-PLANT-LT", "ED-S-PLANT-SPOT", "REG-S-ERV-PLANT-EXH"}
    for display in displays:
        for existing in (obj for obj in objects if obj.tag in existing_tags):
            overlaps_z = (display.body_z0_m < existing.body_z1_m
                          and existing.body_z0_m < display.body_z1_m)
            overlaps_plan = Polygon(display.footprint).intersection(
                Polygon(existing.footprint)).area > 1e-9
            assert not (overlaps_z and overlaps_plan), (display.tag, existing.tag)


def test_backing_advisory_grades_stands_and_leaves_supported_pots_on_their_trays(catlin_ctx):
    from typehaus.checks.advisory.backing import wall_backing_present
    from typehaus.findings import Result

    findings = [finding for finding in wall_backing_present(catlin_ctx)
                if any(tag.startswith("FURN-S-PLANT-STAND-") for tag in finding.element_tags)]
    assert len(findings) == 4
    assert all(finding.result is Result.PASS for finding in findings)
