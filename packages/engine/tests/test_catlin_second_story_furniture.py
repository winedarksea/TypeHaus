"""Preserve the second-storey layout, including the study's compact corner bookshelf."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.quantities import ft, inch
from typehaus.takeoff.placeables import placeables_takeoff

# UI coordinates are metres; BED1 was nudged 1/64" east for the added PAX frame.
# The study table/chairs subsequently moved together 30" west for the corner shelf.
# tag, catalog type, room, centre, rotation in degrees
SECOND_STORY_UI_PLACEMENTS = (
    ("FURN-S-BED1", "FURN-BED-TWIN", "RM-S-BED1", (9.801366875, 3.36872), -90),
    ("FURN-S-DESK1", "FURN-DESK-48", "RM-S-BED1", (10.4995, 4.58763), 90),
    ("FURN-S-DESK-CHAIR1", "FURN-DESK-CHAIR", "RM-S-BED1", (10.0492, 4.62797), 90),
    ("FURN-S-STUDY-TABLE", "FURN-CHESS-TABLE-315", "RM-S-STUDY2", (8.79495, 0.568579), 90),
    ("FURN-S-STUDY-CHAIR1", "FURN-CANTILEVER-CHAIR", "RM-S-STUDY2", (9.4696, 0.589194), -90),
    ("FURN-S-STUDY-CHAIR2", "FURN-CANTILEVER-CHAIR", "RM-S-STUDY2", (8.1304, 0.588713), 90),
    ("FURN-S-PLANT-POT1", "FURN-PLANT-18", "RM-S-PLANT", (1.28957, 0.606871), 0),
    ("FURN-S-PLANT-POT2", "FURN-PLANT-18", "RM-S-PLANT", (2.6348, 0.584116), 0),
    ("FURN-S-PLANT-POT2-COPY", "FURN-PLANT-18", "RM-S-PLANT", (3.87087, 0.600137), 0),
    ("FURN-S-PLANT-ROCKER", "FURN-ROCKING-CHAIR-30", "RM-S-PLANT", (4.51571, 1.96147), -45),
    ("ED-S-PLANT-TUBE1", "ED-T-LT-TUBE6", "RM-S-PLANT", (1.62004, 0.594343), 0),
    ("ED-S-PLANT-TUBE2", "ED-T-LT-TUBE6", "RM-S-PLANT", (3.7205, 0.609677), 0),
)


@pytest.mark.parametrize(
    "tag,type_ref,room,position,rotation_degrees",
    SECOND_STORY_UI_PLACEMENTS,
    ids=[placement[0] for placement in SECOND_STORY_UI_PLACEMENTS],
)
def test_second_story_ui_placements_survive_resolution(
    catlin_model_ro, tag, type_ref, room, position, rotation_degrees,
):
    placed = next(item for item in catlin_model_ro.canvas_objects if item.tag == tag)
    assert placed.storey == "second"
    assert placed.type_ref == type_ref
    assert placed.room == room
    assert placed.position == pytest.approx(position, abs=1e-9)
    assert placed.rotation_degrees == pytest.approx(rotation_degrees, abs=1e-9)


def test_bed1_resolves_as_a_twin_running_east_west(catlin_model_ro):
    bed = next(item for item in catlin_model_ro.canvas_objects if item.tag == "FURN-S-BED1")
    west, south, east, north = Polygon(bed.footprint).bounds
    assert east - west == pytest.approx(ft(6, 7).meters)
    assert north - south == pytest.approx(ft(3, 6).meters)


def test_moved_study_chairs_still_drag_with_the_table(catlin_model_ro):
    study_group = {
        item.tag for item in catlin_model_ro.canvas_objects
        if item.placement_group == "FURN-S-STUDY-TABLE"
    }
    assert study_group == {
        "FURN-S-STUDY-TABLE", "FURN-S-STUDY-CHAIR1", "FURN-S-STUDY-CHAIR2",
    }


def test_study_chess_table_dimensions_and_takeoff(catlin_model_ro):
    table = next(item for item in catlin_model_ro.canvas_objects
                 if item.tag == "FURN-S-STUDY-TABLE")
    west, south, east, north = Polygon(table.footprint).bounds
    assert (east - west, north - south) == pytest.approx(
        (inch(27.75).meters, inch(31.5).meters))
    south_wall = next(wall for wall in catlin_model_ro.walls if wall.tag == "W-S-S2")
    finished_drywall_face = max(y for layer in south_wall.layers
                               if layer.name == "paint" for _, y in layer.polygon)
    assert south == pytest.approx(finished_drywall_face, abs=1e-9)
    assert table.body_z1_m - table.body_z0_m == pytest.approx(inch(27.5).meters)
    row = next(row for row in placeables_takeoff(catlin_model_ro)
               if row["type"] == "FURN-CHESS-TABLE-315")
    assert row["count"] == 1
    assert row["tags"] == [table.tag]


def test_study_corner_bookcase_fits_between_windows_and_preserves_chess_access(catlin_model_ro):
    from typehaus.model.placeable_symbols import model_parts, place_local
    from typehaus.resolve.geometry_millwork import window_stool_prism

    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    bookcase = objects["FURN-S-STUDY-CORNER-BOOKCASE"]
    footprint = Polygon(bookcase.footprint)
    west, south, east, north = footprint.bounds
    room = next(room for room in catlin_model_ro.rooms if room.tag == bookcase.room)
    assert Polygon(room.clear_face).covers(footprint)
    assert east - west == pytest.approx(inch(23.62).meters)
    assert north - south == pytest.approx(inch(23.62).meters)
    assert bookcase.body_z1_m - bookcase.body_z0_m == pytest.approx(inch(78.74).meters)
    assert bookcase.rotation_degrees == -90
    # Even the room's minimum (under its remote soffit) exceeds this bookcase's height.
    assert room.clear_height_m > bookcase.body_z1_m - bookcase.body_z0_m
    room_bounds = Polygon(room.clear_face).bounds
    assert room_bounds[2] - east == pytest.approx(inch(0.5).meters)
    assert south - room_bounds[1] == pytest.approx(inch(0.5).meters)

    for opening in catlin_model_ro.openings:
        if opening.host_wall in ("W-S-S2", "W-S-E1"):
            assert footprint.intersection(Polygon(opening.framing_bumper)).area < 1e-12
        if opening.swing_clearance:
            assert footprint.intersection(Polygon(opening.swing_clearance)).area < 1e-12
    for stool in catlin_model_ro.window_stools:
        if stool.window_ref in {"WIN-S-STUDY1", "WIN-S-STUDY2", "WIN-S-STUDY3"}:
            opening = next(item for item in catlin_model_ro.openings
                           if item.tag == stool.window_ref)
            prism = window_stool_prism(catlin_model_ro.wall(opening.host_wall), opening, stool)
            assert prism is not None
            assert footprint.intersection(Polygon(prism.ring)).area < 1e-12
    parts = model_parts("corner-bookcase", east - west, north - south,
                        bookcase.body_z1_m - bookcase.body_z0_m)
    for run in catlin_model_ro.base_runs:
        if run.room != bookcase.room:
            continue
        for part in parts:
            x, y, z = part["center"]
            w, d, h = part["size"]
            if bookcase.body_z0_m + z - h / 2 >= run.piece.z1_m:
                continue
            ring = [(x - w / 2, y - d / 2), (x + w / 2, y - d / 2),
                    (x + w / 2, y + d / 2), (x - w / 2, y + d / 2)]
            placed = place_local(ring, bookcase.position, bookcase.rotation_degrees)
            assert Polygon(placed).intersection(Polygon(run.piece.outline)).area < 1e-12
    for other in objects.values():
        if other.room == bookcase.room and other.kind == "Furniture" and other != bookcase:
            assert footprint.intersection(Polygon(other.footprint)).area < 1e-12, other.tag
    for clearance in objects["FURN-S-STUDY-TABLE"].recommended_clearances:
        assert footprint.intersection(Polygon(clearance)).area < 1e-12
    chair_east = Polygon(objects["FURN-S-STUDY-CHAIR1"].footprint).bounds[2]
    assert west - chair_east > inch(17).meters


def test_study_bookcase_product_takeoff_and_relocated_outlet(catlin_plan, catlin_model_ro):
    row = next(row for row in placeables_takeoff(catlin_model_ro)
               if row["type"] == "FT-STUDY-CORNER-BOOKCASE")
    assert row["count"] == 1
    assert row["tags"] == ["FURN-S-STUDY-CORNER-BOOKCASE"]
    catalog_type = next(item for item in catlin_plan.library.furniture_types
                        if item.tag == row["type"])
    product = next(item for item in catlin_plan.library.products
                   if item.tag == catalog_type.product_ref)
    assert product.brand == "Tribesigns"
    assert product.model == "HOGA-JW0510"

    source_outlet = catlin_plan.by_tag("ED-S-STUDY2-RC5")
    assert source_outlet.uid == "NEC062AAAA"
    assert source_outlet.circuit == "CKT-RC-SECOND"
    assert source_outlet.mount.elevation.meters == pytest.approx(inch(16).meters)
    assert source_outlet.location.attachment.wall_ref == "W-S-E1"
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    outlet = objects[source_outlet.tag]
    assert outlet.position[1] == pytest.approx(inch(40).meters)
    outlet_bounds = Polygon(outlet.footprint).bounds
    shelf_north = Polygon(objects["FURN-S-STUDY-CORNER-BOOKCASE"].footprint).bounds[3]
    window = next(item for item in catlin_model_ro.openings if item.tag == "WIN-S-STUDY3")
    assert outlet_bounds[1] - shelf_north > inch(7).meters
    assert Polygon(window.framing_bumper).bounds[1] > outlet_bounds[3]


def test_deleted_study_rocker_and_duplicate_pot_reach_the_takeoff(catlin_model_ro):
    second_story_furniture = [
        item for item in catlin_model_ro.canvas_objects
        if item.storey == "second" and item.kind == "Furniture"
    ]
    assert "FURN-S-STUDY-ROCKING-CHAIR" not in {
        item.tag for item in second_story_furniture
    }
    plant_pots = [item for item in second_story_furniture if item.type_ref == "FURN-PLANT-18"]
    expected_pot_tags = {"FURN-S-PLANT-POT1", "FURN-S-PLANT-POT2", "FURN-S-PLANT-POT2-COPY"}
    assert {item.tag for item in plant_pots} == expected_pot_tags
    assert len({item.uid for item in plant_pots}) == 3
    rows = {
        row["type"]: row for row in placeables_takeoff(catlin_model_ro)
        if row["storey"] == "second" and row["domain"] == "furniture"
    }
    assert rows["FURN-PLANT-18"]["count"] == 3
    assert set(rows["FURN-PLANT-18"]["tags"]) == expected_pot_tags
    assert rows["FURN-ROCKING-CHAIR-30"]["count"] == 1
    assert rows["FURN-ROCKING-CHAIR-30"]["tags"] == ["FURN-S-PLANT-ROCKER"]
    assert rows["FURN-BED-TWIN"]["tags"] == ["FURN-S-BED1"]
    assert "FURN-S-BED1" not in rows["FURN-QUEEN-BED"]["tags"]


@pytest.mark.parametrize("tag", ("ED-S-PLANT-TUBE1", "ED-S-PLANT-TUBE2"))
def test_moved_grow_lights_keep_their_timer_and_ceiling_drop(catlin_plan, tag):
    light = catlin_plan.by_tag(tag)
    assert light.circuit == "CKT-LT-UPPER"
    assert light.controlled_by == ("ED-S-PLANT-SW-TIMER",)
    assert light.mount.kind.value == "ceiling"
    assert light.mount.drop.meters == pytest.approx(ft(2, 3).meters)


@pytest.mark.parametrize("bedroom", ("BED1", "BED2"))
def test_east_pax_frame_meets_corner_and_leaves_outlet_and_erv_access(catlin_model_ro, bedroom):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    corner = objects[f"FURN-S-{bedroom}-WARD"]
    shelf = objects[f"FURN-S-{bedroom}-PAX-SHELF-EAST"]
    shelf_polygon = Polygon(shelf.footprint)
    west, south, east, north = shelf_polygon.bounds
    corner_bounds = Polygon(corner.footprint).bounds
    assert shelf.type_ref == objects[f"FURN-S-{bedroom}-PAX-SHELF"].type_ref
    assert west == pytest.approx(corner_bounds[2])
    assert south == pytest.approx(corner_bounds[1])
    assert east - west == pytest.approx(inch(19.625).meters)
    assert north - south == pytest.approx(inch(22.875).meters)
    assert east == pytest.approx(ft(27, 4.375).meters)

    outlet = objects[f"ED-S-{bedroom}-RC4"]
    grille = objects[f"REG-S-RET-{bedroom}"]
    assert Polygon(outlet.footprint).bounds[0] - east == pytest.approx(inch(5.625).meters)
    assert Polygon(grille.footprint).bounds[0] - east == pytest.approx(inch(5.125).meters)
    duct = next(item for item in catlin_model_ro.ducts if item.tag == f"DU-M-ERV-R-{bedroom}")
    assert duct.path[-1] == pytest.approx(grille.position)
    assert grille.position[1] == pytest.approx(
        ft(9, 9).meters if bedroom == "BED1" else ft(18, 4).meters)
    if bedroom == "BED1":
        bed_west = Polygon(objects["FURN-S-BED1"].footprint).bounds[0]
        assert bed_west - east >= inch(18).meters

    for other in objects.values():
        if other.room == shelf.room and other.tag != shelf.tag and other.kind == "Furniture":
            assert shelf_polygon.intersection(Polygon(other.footprint)).area < 1e-9, other.tag


def test_east_pax_frames_are_counted_and_have_rail_backing(catlin_plan, catlin_model_ro):
    row = next(row for row in placeables_takeoff(catlin_model_ro)
               if row["type"] == "FURN-S-PAX-SHELF-20")
    assert row["count"] == 5
    assert {"FURN-S-BED1-PAX-SHELF-EAST", "FURN-S-BED2-PAX-SHELF-EAST"} <= set(row["tags"])
    for bedroom, wall in (("BED1", "SS2"), ("BED2", "BD1")):
        backing = catlin_plan.by_tag(f"BK-S-{wall}-PAX-EAST")
        shelf = catlin_plan.by_tag(f"FURN-S-{bedroom}-PAX-SHELF-EAST")
        attachment = shelf.location.attachment
        assert backing.wall_ref == attachment.wall_ref
        assert backing.face == attachment.face
        half_width = inch(19.625).meters / 2
        assert backing.start.meters <= attachment.distance_from_start.meters - half_width
        assert (backing.start.meters + backing.length.meters
                >= attachment.distance_from_start.meters + half_width)


@pytest.mark.parametrize("bedroom", ("BED1", "BED2"))
def test_expanded_pax_run_preserves_receptacle_spacing(catlin_ctx, bedroom):
    from typehaus.checks.mep.electrical import receptacle_spacing
    from typehaus.findings import Result

    findings = [finding for finding in receptacle_spacing(catlin_ctx)
                if f"RM-S-{bedroom}" in finding.element_tags]
    assert findings
    assert all(finding.result is Result.PASS for finding in findings), findings
