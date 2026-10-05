"""RM-M-BED reading corner on W-M-W4 and the SE desk's chair."""

import pytest
from shapely.geometry import Polygon

from typehaus.model.placeable_symbols import symbol_geometry
from typehaus.model.placeable_symbols._sektion_seat import sektion_open_base
from typehaus.resolve.geometry_millwork import window_stool_prism

INCH = 0.0254
WALL_FACE_X = 6.635 * INCH
COVERS = ("FURN-M-BED-NOOK-COVER-S", "FURN-M-BED-NOOK-COVER-N")
CABINETS = ("FURN-M-BED-NOOK-END-S", "FURN-M-BED-NOOK-END-N")
TOPS = ("CT-M-BED-NOOK-S", "CT-M-BED-NOOK-N")
SEATS = ("FURN-M-BED-NOOK-SEAT-S", "FURN-M-BED-NOOK-SEAT-N")
CHAIR = "FURN-M-BED-ARMCHAIR"
RUN = (COVERS[0], CABINETS[0], *SEATS, CABINETS[1], COVERS[1])


def _objects(model):
    return {obj.tag: obj for obj in model.canvas_objects}


def _bounds(objects, tag):
    return Polygon(objects[tag].footprint).bounds


def test_seat_run_is_contiguous_and_centred_on_w4(
    catlin_model_ro,
):
    objects = _objects(catlin_model_ro)
    assert "FURN-M-BED-BOOKCASE-SW" not in objects
    assert "FURN-M-BED-BOOKCASE-W" in objects
    assert "FURN-M-BED-BOOKCASE-E" in objects
    bounds = [_bounds(objects, tag) for tag in RUN]
    for tag, bound in zip(RUN, bounds, strict=True):
        assert objects[tag].room == "RM-M-BED"
        assert bound[0] == pytest.approx(WALL_FACE_X, abs=1e-4), tag
    for south, north in zip(bounds, bounds[1:], strict=False):
        assert north[1] == pytest.approx(south[3], abs=1e-4)
    room = next(room for room in catlin_model_ro.rooms if room.tag == "RM-M-BED")
    _, room_south, _, room_north = Polygon(room.clear_face).bounds
    run_south, run_north = bounds[0][1], bounds[-1][3]
    assert run_south - room_south == pytest.approx(room_north - run_north, abs=1e-4)


def test_north_end_clears_the_open_bath_door(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-M-BATH2")
    assert door.swing_clearance
    swing = Polygon(door.swing_clearance)
    leaf_south = swing.bounds[1]
    for tag in RUN:
        footprint = Polygon(objects[tag].footprint)
        assert not footprint.intersects(swing), tag
        assert leaf_south - footprint.bounds[3] >= 2 * INCH, tag


def test_cabinet_tops_stand_under_both_window_stools(catlin_model_ro):
    model = catlin_model_ro
    objects = _objects(model)
    openings = {opening.tag: opening for opening in model.openings}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    top = max(objects[tag].body_z1_m for tag in CABINETS)
    for tag in ("WIN-M-BED-W1", "WIN-M-BED-W2"):
        stool = stools[tag]
        prism = window_stool_prism(model.wall(stool.wall_tag), openings[tag], stool)
        assert prism is not None, tag
        assert prism.z0_m - top >= 1.5 * INCH, tag
    # Symmetric ends; the south one is the backrest, 15" over the seat top.
    assert _bounds(objects, CABINETS[0])[3] - _bounds(objects, CABINETS[0])[1] == pytest.approx(
        _bounds(objects, CABINETS[1])[3] - _bounds(objects, CABINETS[1])[1])
    assert objects[CABINETS[0]].body_z1_m == pytest.approx(objects[CABINETS[1]].body_z1_m)
    assert objects[CABINETS[0]].body_z1_m - objects[SEATS[0]].body_z1_m == pytest.approx(
        15 * INCH)


def test_seat_front_swings_stay_inside_the_room(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-BED")
    clear = Polygon(room.clear_face).buffer(1e-4)
    for tag in SEATS:
        zones = objects[tag].recommended_clearances
        assert zones, tag
        for zone in zones:
            assert clear.contains(Polygon(zone)), tag
            # East of the run, not into the wall.
            assert Polygon(zone).bounds[0] >= _bounds(objects, tag)[2] - 1e-4, tag


def test_cushion_rests_on_the_seats_behind_the_fronts(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    cushion = objects["FURN-M-BED-NOOK-CUSHION"]
    back, y0, front, y1 = _bounds(objects, "FURN-M-BED-NOOK-CUSHION")
    seats = [_bounds(objects, tag) for tag in SEATS]
    assert (y0, y1) == pytest.approx((seats[0][1], seats[-1][3]), abs=1e-4)
    assert back == pytest.approx(WALL_FACE_X, abs=1e-4)
    assert seats[0][2] - front == pytest.approx(0.5 * INCH, abs=1e-4)
    assert cushion.body_z0_m == pytest.approx(objects[SEATS[0]].body_z1_m)


def test_armchair_clears_the_cover_the_bookcase_and_the_bed(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    chair = Polygon(objects[CHAIR].footprint)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-BED")
    assert Polygon(room.clear_face).covers(chair)
    # The rotated chair sits beside the end cover; its former four-inch gap and
    # centring between cabinets were placement choices, not access requirements.
    assert chair.disjoint(Polygon(objects[COVERS[0]].footprint))
    for tag in ("FURN-M-BED-BOOKCASE-W", "FURN-M-BED"):
        assert chair.distance(Polygon(objects[tag].footprint)) >= 4 * INCH, tag


def test_receptacle_rc7_moved_clear_of_the_end_cabinet(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    receptacle = Polygon(objects["ED-M-BED-RC7"].footprint)
    end = Polygon(objects[COVERS[1]].footprint)
    assert receptacle.bounds[1] > end.bounds[3]


def test_walnut_tops_cap_each_end_flush_with_the_seat_fronts(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    tops = {top.tag: top for top in catlin_model_ro.countertops}
    seat_front = _bounds(objects, SEATS[0])[2]
    for tag, cabinet, cover in zip(TOPS, CABINETS, COVERS, strict=True):
        top = tops[tag]
        assert top.material_ref == "walnut-counter"
        assert top.thickness_m == pytest.approx(1 * INCH)
        x0, y0, x1, y1 = Polygon(top.outline).bounds
        assert x0 == pytest.approx(WALL_FACE_X, abs=1e-4), tag
        assert x1 == pytest.approx(seat_front, abs=1e-4), tag
        # One rectangle over the cabinet and its cover.
        span = Polygon(objects[cabinet].footprint).union(Polygon(objects[cover].footprint))
        assert (y0, y1) == pytest.approx((span.bounds[1], span.bounds[3]), abs=1e-4), tag
        assert Polygon(top.outline).area == pytest.approx((x1 - x0) * (y1 - y0)), tag


def test_desk_chair_sits_in_the_desk_zone_clear_of_the_bed(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    chair = Polygon(objects["FURN-M-BED-DESK-CHAIR"].footprint)
    desk = objects["FURN-M-BED-DESK"]
    zone = Polygon(desk.recommended_clearances[0])
    assert zone.buffer(1e-4).contains(chair.difference(Polygon(desk.footprint)))
    bed = objects["FURN-M-BED"]
    for footprint in (bed.footprint, *bed.recommended_clearances):
        assert not chair.intersects(Polygon(footprint))


def test_open_base_frame_stops_under_the_slab_it_hosts():
    # The 1" top is a `counter` part, dropped when a Countertop is hosted; nothing else
    # may reach into the slab's inch, or the two draw coplanar and flicker.
    _strokes, parts = sektion_open_base(12 * INCH, 24 * INCH, 34.5 * INCH)
    tops = {part["color"]: [] for part in parts}
    for part in parts:
        tops[part["color"]].append(part["center"][2] + part["size"][2] / 2)
    counter = [part for part in parts if part["color"] == "counter"]
    assert len(counter) == 1
    assert counter[0]["size"][2] == pytest.approx(1 * INCH)
    body = [z for color, zs in tops.items() if color != "counter" for z in zs]
    assert max(body) == pytest.approx(33.5 * INCH)


def test_end_cabinet_doors_fit_under_tops_and_open_into_room(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-BED")
    clear = Polygon(room.clear_face).buffer(1e-4)
    for tag in CABINETS:
        cabinet = objects[tag]
        cabinet_type = next(t for t in catlin_model_ro.plan.library.furniture_types
                            if t.tag == "FURN-M-BED-NOOK-END-12")
        assert cabinet_type.plan_symbol == "sektion-axstad-base"
        assert _bounds(objects, tag)[2] - WALL_FACE_X == pytest.approx(24.75 * INCH, abs=1e-4)
        assert cabinet.recommended_clearances
        for zone in cabinet.recommended_clearances:
            assert clear.contains(Polygon(zone))
            assert Polygon(zone).bounds[0] >= _bounds(objects, tag)[2] - 1e-4
        # The 3/4" door sits within the walnut top's 24 7/8" depth.
        top = next(t for t in catlin_model_ro.countertops if tag in t.hosts)
        assert Polygon(top.outline).bounds[2] - _bounds(objects, tag)[2] == pytest.approx(
            0.125 * INCH, abs=1e-4)


def test_axstad_door_has_a_recessed_panel_and_does_not_enter_hosted_slab():
    width, depth, height = 12 * INCH, 24.75 * INCH, 34.5 * INCH
    _strokes, parts = symbol_geometry("sektion-axstad-base", width, depth, height)
    front = -depth / 2
    door = [part for part in parts
            if part["center"][1] - part["size"][1] / 2 < front + 0.75 * INCH - 1e-6
            and part["center"][2] - part["size"][2] / 2 > 3.5 * INCH
            and part["color"] != "counter"]
    assert len(door) == 5  # two stiles, two rails, one recessed panel
    assert max(p["size"][0] / 2 + abs(p["center"][0]) for p in door) * 2 == pytest.approx(
        11.875 * INCH)
    assert max(p["center"][2] + p["size"][2] / 2 for p in door) - min(
        p["center"][2] - p["size"][2] / 2 for p in door) == pytest.approx(29.875 * INCH)
    panel = door[-1]
    assert panel["center"][1] - panel["size"][1] / 2 == pytest.approx(front + 0.25 * INCH)
    body_tops = [p["center"][2] + p["size"][2] / 2 for p in parts if p["color"] != "counter"]
    assert max(body_tops) == pytest.approx(33.5 * INCH)
