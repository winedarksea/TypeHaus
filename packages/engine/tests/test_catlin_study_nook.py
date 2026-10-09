"""Study 2 window seat under ST-S2A: on the wall, clear of the door, under the flight."""

import pytest
from shapely.geometry import Polygon

INCH = 0.0254
WALL_FACE_Y = 105.625 * INCH
SEATS = ("FURN-S-STUDY-NOOK-SEAT-W", "FURN-S-STUDY-NOOK-SEAT-C", "FURN-S-STUDY-NOOK-SEAT-E")
SHELF = "FURN-S-STUDY-NOOK-SHELF"
COVERS = ("FURN-S-STUDY-NOOK-COVER", "FURN-S-STUDY-NOOK-END")
NOOK = (COVERS[0], SHELF, *SEATS, COVERS[1])


def _objects(model):
    return {obj.tag: obj for obj in model.canvas_objects}


def _stringer_underside(model, x):
    """Lowest stringer soffit of ST-S2A at plan x, as an absolute elevation."""
    stair = next(s for s in model.stairs if s.tag == "ST-S2A")
    heights = []
    for member in stair.members:
        if member.category != "stringer":
            continue
        (x0, _), (x1, _) = member.p0, member.p1
        t = (x - x0) / (x1 - x0)
        if 0 <= t <= 1:
            heights.append(member.z0_m + t * (member.z0_end_m - member.z0_m))
    assert heights, x
    return min(heights)


def test_run_is_six_pieces_on_the_south_face_of_w_s_ss2(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    bounds = [Polygon(objects[tag].footprint).bounds for tag in NOOK]
    for tag, bound in zip(NOOK, bounds, strict=True):
        assert objects[tag].room == "RM-S-STUDY2"
        gap = 0.25 * INCH if tag in COVERS else 0
        assert bound[3] == pytest.approx(WALL_FACE_Y - gap, abs=1e-4), tag
    # West to east, each piece butts the next.
    for left, right in zip(bounds, bounds[1:], strict=False):
        assert right[0] == pytest.approx(left[2], abs=1e-4)
    assert bounds[0][0] / INCH == pytest.approx(264.0, abs=1e-3)
    assert bounds[-1][2] / INCH == pytest.approx(343.0, abs=1e-3)


def test_partition_clears_the_doorway_and_its_casing(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-S-STUDY2")
    door_east = Polygon(door.framing_bumper).bounds[2]
    for tag in NOOK:
        footprint = Polygon(objects[tag].footprint)
        # A 2 1/2" casing and a hair: nothing of the run overlaps the trim.
        assert footprint.bounds[0] - door_east >= 3 * INCH, tag
        assert all(not footprint.intersects(Polygon(zone)) for zone in door.swing_clearance)


def test_everything_stays_under_the_flight(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    stair = next(s for s in catlin_model_ro.stairs if s.tag == "ST-S2A")
    flight = Polygon(stair.outline).buffer(1e-4)
    for tag in SEATS:
        assert flight.contains(Polygon(objects[tag].footprint)), tag
    shelf = objects[SHELF]
    shelf_east = Polygon(shelf.footprint).bounds[2]
    assert _stringer_underside(catlin_model_ro, shelf_east) - shelf.body_z1_m >= 6 * INCH
    for tag in SEATS:
        seat = objects[tag]
        east = Polygon(seat.footprint).bounds[2]
        assert seat.body_z1_m - seat.body_z0_m == pytest.approx(19.5 * INCH)
        # Even the foot cubby keeps a usable 20" over the seat top.
        assert _stringer_underside(catlin_model_ro, east) - seat.body_z1_m >= 20 * INCH, tag


def test_each_front_swing_stays_inside_the_room(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-S-STUDY2")
    clear = Polygon(room.clear_face).buffer(1e-4)
    for tag in SEATS:
        zones = objects[tag].recommended_clearances
        assert zones, tag
        assert all(clear.contains(Polygon(zone)) for zone in zones), tag


def test_receptacle_behind_the_seat_rose_above_it(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    seat = objects["FURN-S-STUDY-NOOK-SEAT-C"]
    receptacle = objects["ED-S-STUDY2-RC3"]
    assert Polygon(receptacle.footprint).bounds[0] >= Polygon(seat.footprint).bounds[0]
    assert receptacle.body_z0_m >= seat.body_z1_m + 4 * INCH


def test_reading_sconce_and_its_dimmer_are_in_reach_of_the_seat(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    seat = objects["FURN-S-STUDY-NOOK-SEAT-W"]
    sconce = objects["ED-S-STUDY2-NOOK-SC"]
    switch = objects["ED-S-STUDY2-NOOK-SW"]
    x0, _, x1, _ = Polygon(seat.footprint).bounds
    for device in (sconce, switch):
        dx0, _, dx1, _ = Polygon(device.footprint).bounds
        assert x0 <= dx0 and dx1 <= x1, device.tag
        assert device.body_z0_m >= seat.body_z1_m + 12 * INCH, device.tag
    assert sconce.body_z1_m < _stringer_underside(catlin_model_ro, x1)
    authored = next(e for e in catlin_model_ro.plan.all_elements() if e.tag == sconce.tag)
    assert authored.controlled_by == (switch.tag,)


def test_cushion_rests_on_the_seat_and_clears_the_lift_up_fronts(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    cushion = objects["FURN-S-STUDY-NOOK-CUSHION"]
    x0, front, x1, back = Polygon(cushion.footprint).bounds
    seats = [Polygon(objects[tag].footprint).bounds for tag in SEATS]
    assert (x0, x1) == pytest.approx((seats[0][0], seats[-1][2]), abs=1e-4)
    assert back == pytest.approx(WALL_FACE_Y, abs=1e-4)
    # Set back from the fronts, or the lift-up doors bind on it.
    assert front - seats[0][1] == pytest.approx(0.5 * INCH, abs=1e-4)
    assert cushion.body_z0_m == pytest.approx(objects[SEATS[0]].body_z1_m)
    assert _stringer_underside(catlin_model_ro, x1) - cushion.body_z1_m >= 18 * INCH
