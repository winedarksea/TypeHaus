"""Preserve the second-storey layout edited in the UI in aa20cbcb."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.quantities import ft
from typehaus.takeoff.placeables import placeables_takeoff

# UI coordinates are metres; retain their precision instead of snapping to inches.
# tag, catalog type, room, centre, rotation in degrees
SECOND_STORY_UI_PLACEMENTS = (
    ("FURN-S-BED1", "FURN-BED-TWIN", "RM-S-BED1", (9.80097, 3.36872), -90),
    ("FURN-S-DESK1", "FURN-DESK-48", "RM-S-BED1", (10.4995, 4.58763), 90),
    ("FURN-S-DESK-CHAIR1", "FURN-DESK-CHAIR", "RM-S-BED1", (10.0492, 4.55177), 90),
    ("FURN-S-STUDY-TABLE", "FURN-DINING-2-36", "RM-S-STUDY2", (9.55695, 0.625729), 0),
    ("FURN-S-STUDY-CHAIR1", "FURN-DINING-CHAIR", "RM-S-STUDY2", (10.1327, 0.588309), -90),
    ("FURN-S-STUDY-CHAIR2", "FURN-DINING-CHAIR", "RM-S-STUDY2", (8.8924, 0.588713), 90),
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
