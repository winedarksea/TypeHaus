"""The living-room hammock chair hangs clear of the sitting group, the table and the door."""

import pytest
from shapely.geometry import Polygon

from typehaus.quantities import inch
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.placeables import placeables_takeoff

CHAIR = "FURN-M-HAMMOCK"


def test_hammock_body_and_swing_clear_every_neighbour(catlin_model_ro):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    chair = objects[CHAIR]
    body, [swing] = Polygon(chair.footprint), chair.recommended_clearances
    swing = Polygon(swing)
    assert chair.room == "RM-M-LIVING"
    assert swing.distance(Polygon(objects["FURN-M-PUZZLE-COFFEE-TABLE"].footprint)) > 0
    for other in objects.values():
        if other.storey != chair.storey or other.tag == CHAIR:
            continue
        if other.body_z0_m < chair.body_z1_m and other.body_z1_m > chair.body_z0_m:
            assert swing.intersection(Polygon(other.footprint)).area < 1e-8, other.tag
        for zone in (*other.required_clearances, *other.recommended_clearances):
            assert body.intersection(Polygon(zone)).area < 1e-8, other.tag
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-M-BALC")
    assert Polygon(door.swing_clearance).distance(swing) > inch(12).meters


def test_hammock_bills_its_chair_and_hardware(catlin_model_ro):
    rows = [row for row in placeables_takeoff(catlin_model_ro) if CHAIR in row["tags"]]
    assert [row["count"] for row in rows] == [1]
    parts = {row["part_number"]: row["count"] for row in hardware_takeoff(catlin_model_ro)
             if row["scope"] == "suspension anchor"}
    assert parts == {"3-S-5": 1, "SADDLE-3.5-2x58": 1}


def test_hammock_hangs_on_its_suspension(catlin_model_ro):
    chair = next(o for o in catlin_model_ro.canvas_objects if o.tag == CHAIR)
    assert chair.body_z1_m - chair.body_z0_m == pytest.approx(inch(63).meters)
    assert inch(6).meters < chair.suspension_m < inch(48).meters
