"""RM-M-BED: the SE desk (SEKTION drawer bases under a walnut glue-up) and the reading chair."""

import pytest
from shapely.geometry import Polygon

from typehaus.model.placeable_symbols import symbol_geometry

INCH = 0.0254
EAST_FACE_X = 212.115 * INCH
CABINETS = ("FURN-M-BED-DESK-CAB-S", "FURN-M-BED-DESK-CAB-N")
LEDGER = "FURN-M-BED-DESK"
COVER = "FURN-M-BED-DESK-COVER-N"
TOP = "CT-M-BED-DESK"
CHAIR = "FURN-M-BED-ARMCHAIR"


def _objects(model):
    return {obj.tag: obj for obj in model.canvas_objects}


def _bounds(objects, tag):
    return Polygon(objects[tag].footprint).bounds


def test_nook_is_retired(catlin_model_ro):
    tags = {obj.tag for obj in catlin_model_ro.canvas_objects}
    assert not any("BED-NOOK" in tag for tag in tags)
    assert not any("BED-NOOK" in top.tag for top in catlin_model_ro.countertops)


def test_bases_and_ledger_back_onto_the_east_face_around_a_31_inch_knee(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    for tag in (*CABINETS, LEDGER):
        assert objects[tag].room == "RM-M-BED"
        assert _bounds(objects, tag)[2] == pytest.approx(EAST_FACE_X, abs=1e-4), tag
    south, north = (_bounds(objects, tag) for tag in CABINETS)
    ledger = _bounds(objects, LEDGER)
    assert north[1] - south[3] == pytest.approx(31 * INCH, abs=1e-4)
    assert (ledger[1], ledger[3]) == pytest.approx((south[3], north[1]), abs=1e-4)
    assert (south[1], north[3]) == pytest.approx((7.25 * INCH, 68.25 * INCH), abs=1e-4)
    # The north base's exposed side takes a 1/2" FÖRBÄTTRA cover, tight to the frame and wall.
    cover = _bounds(objects, COVER)
    assert (cover[1], cover[3]) == pytest.approx((north[3], north[3] + 0.5 * INCH), abs=1e-4)
    assert cover[2] == pytest.approx(EAST_FACE_X, abs=1e-4)


def test_one_walnut_top_spans_bases_knee_and_cover_at_31_inches(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    top = next(t for t in catlin_model_ro.countertops if t.tag == TOP)
    assert top.hosts == (CABINETS[0], LEDGER, CABINETS[1], COVER)
    assert top.material_ref == "walnut-counter"
    x0, y0, x1, y1 = Polygon(top.outline).bounds
    assert x1 == pytest.approx(EAST_FACE_X, abs=1e-4)
    assert x1 - x0 == pytest.approx(24.875 * INCH, abs=1e-4)
    assert y1 - y0 == pytest.approx(61.5 * INCH, abs=1e-4)
    assert Polygon(top.outline).area == pytest.approx((x1 - x0) * (y1 - y0))
    floor = objects[CABINETS[0]].body_z0_m
    assert max(objects[tag].body_z1_m for tag in top.hosts) - floor == pytest.approx(31 * INCH)
    # The ledger's top meets the slab's underside.
    assert objects[LEDGER].body_z1_m - floor == pytest.approx(30 * INCH)


def test_drawer_pull_outs_stay_in_the_room(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-BED")
    clear = Polygon(room.clear_face).buffer(1e-4)
    for tag in CABINETS:
        zones = objects[tag].recommended_clearances
        assert zones, tag
        for zone in zones:
            assert clear.contains(Polygon(zone)), tag
            assert Polygon(zone).bounds[2] <= _bounds(objects, tag)[0] + 1e-4, tag


def test_desk_chair_sits_in_the_knee_zone_clear_of_the_bed_and_bases(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    chair = Polygon(objects["FURN-M-BED-DESK-CHAIR"].footprint)
    desk = objects[LEDGER]
    zone = Polygon(desk.recommended_clearances[0])
    assert zone.buffer(1e-4).contains(chair.difference(Polygon(desk.footprint)))
    for tag in CABINETS:
        assert chair.disjoint(Polygon(objects[tag].footprint)), tag
    bed = objects["FURN-M-BED"]
    for footprint in (bed.footprint, *bed.recommended_clearances):
        assert not chair.intersects(Polygon(footprint))


def test_armchair_clears_the_bookcase_and_the_bed(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    chair = Polygon(objects[CHAIR].footprint)
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-BED")
    assert Polygon(room.clear_face).covers(chair)
    for tag in ("FURN-M-BED-BOOKCASE-W", "FURN-M-BED"):
        assert chair.distance(Polygon(objects[tag].footprint)) >= 4 * INCH, tag


def test_axstad_drawer_base_has_three_fronts_and_stops_under_the_slab():
    width, depth, height = 15 * INCH, 24.75 * INCH, 31 * INCH
    _strokes, parts = symbol_geometry("sektion-axstad-drawers", width, depth, height)
    front = -depth / 2
    fronts = [p for p in parts
              if p["center"][1] - p["size"][1] / 2 < front + 0.75 * INCH - 1e-6
              and p["color"] != "counter"]
    assert len(fronts) == 15  # three fronts x (two stiles, two rails, one panel)
    assert min(p["center"][2] - p["size"][2] / 2 for p in parts) == pytest.approx(0)
    counter = [p for p in parts if p["color"] == "counter"]
    assert len(counter) == 1 and counter[0]["size"][2] == pytest.approx(1 * INCH)
    body_tops = [p["center"][2] + p["size"][2] / 2 for p in parts if p["color"] != "counter"]
    assert max(body_tops) == pytest.approx(30 * INCH)


def test_axstad_door_base_keeps_its_recessed_panel():
    width, depth, height = 12 * INCH, 24.75 * INCH, 34.5 * INCH
    _strokes, parts = symbol_geometry("sektion-axstad-base", width, depth, height)
    front = -depth / 2
    door = [part for part in parts
            if part["center"][1] - part["size"][1] / 2 < front + 0.75 * INCH - 1e-6
            and part["center"][2] - part["size"][2] / 2 > 3.5 * INCH
            and part["color"] != "counter"]
    assert len(door) == 5
    assert max(p["center"][2] + p["size"][2] / 2 for p in door) - min(
        p["center"][2] - p["size"][2] / 2 for p in door) == pytest.approx(29.875 * INCH)
    body_tops = [p["center"][2] + p["size"][2] / 2 for p in parts if p["color"] != "counter"]
    assert max(body_tops) == pytest.approx(33.5 * INCH)
