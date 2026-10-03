"""Hall-bath SEKTION must preserve the WC and avoid its drawer sweeps in three dimensions."""

import pytest
from shapely.geometry import Point, Polygon, box

from typehaus.model.placeable_symbols import model_parts

INCH = 0.0254
SQFT = 0.3048 ** 2
CABINET_TAGS = ("FURN-S-BATH1-CLOSET", "FURN-S-BATH1-CLOSET-C", "FURN-S-BATH1-CLOSET-E")


def _objects(model):
    return {obj.tag: obj for obj in model.canvas_objects}


def test_three_real_sektion_frames_replace_the_placeholder(catlin_plan, catlin_model_ro):
    types = {typ.tag: typ for typ in catlin_plan.library.furniture_types}
    objects = _objects(catlin_model_ro)
    for tag in CABINET_TAGS:
        typ = types[objects[tag].type_ref]
        assert typ.product_ref == "PROD-IKEA-SEKTION-HIGH-24-24-90"
        assert typ.footprint[0].meters == pytest.approx(24 * INCH)
        assert typ.carcass_depth.meters == pytest.approx(24 * INCH)
        assert typ.footprint[1].meters == pytest.approx(24.875 * INCH)
        assert typ.height.meters == pytest.approx(94.5 * INCH)
        assert objects[tag].room == "RM-S-BATH1"
    assert objects[CABINET_TAGS[0]].uid == "CSB707AAAA"
    assert [types[objects[tag].type_ref].plan_symbol for tag in CABINET_TAGS] == [
        "sektion-tall-open-lower", "sektion-tall-open-lower", "sektion-tall-drawers"]
    assert not any(obj.type_ref == "CASE-PANTRY-CLOSET-72"
                   for obj in catlin_model_ro.canvas_objects)


def test_toilet_centres_under_the_window_and_preserves_its_required_clear_floor(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    toilet = objects["FX-S-BATH1-WC"]
    window = next(opening for opening in catlin_model_ro.openings if opening.tag == "WIN-S-BATH-W")
    window_center_y = Polygon(window.framing_bumper).centroid.y
    assert toilet.uid == "CSQ801AAAA"
    assert toilet.position == pytest.approx((0.560313, window_center_y))
    tub_south_face = Polygon(objects["FX-S-BATH1-SH"].footprint).bounds[1]
    vanity_west_face = Polygon(objects["FX-S-BATH1-LAV"].footprint).bounds[0]
    toilet_front_face = Polygon(toilet.footprint).bounds[2]
    assert tub_south_face - toilet.position[1] >= 15 * INCH
    assert vanity_west_face - toilet_front_face >= 24 * INCH
    assert all(not Polygon(objects["FX-S-BATH1-SH"].footprint).intersects(Polygon(zone))
               for zone in toilet.required_clearances)
    for tag in (*CABINET_TAGS, "FURN-S-BATH1-CLOSET-COVER", "FURN-S-BATH1-CLOSET-SCRIBE"):
        cabinet = Polygon(objects[tag].footprint)
        assert not cabinet.intersects(Polygon(toilet.footprint))
        assert all(not cabinet.intersects(Polygon(zone)) for zone in toilet.required_clearances)


def test_toilet_drain_follows_the_flange_into_the_next_clear_truss_bay(catlin_model_ro):
    toilet = _objects(catlin_model_ro)["FX-S-BATH1-WC"]
    drain = next(run for run in catlin_model_ro.pipe_runs if run.tag == "PR-M-S-BATH1-WC-DRAIN")
    assert drain.path[0] == pytest.approx(toilet.position)
    floor = next(floor for floor in catlin_model_ro.floors if floor.tag == "FS-S-WEST")
    adjoining_truss_lines = sorted({member.p0[1] for member in floor.members
                                   if member.category == "joist"})
    south_line = max(y for y in adjoining_truss_lines if y < toilet.position[1])
    north_line = min(y for y in adjoining_truss_lines if y > toilet.position[1])
    # The drain's 3.5" envelope must fit between the 3.5" chords, with no chord cutting.
    required_centerline_separation = 3.5 * INCH
    assert toilet.position[1] - south_line >= required_centerline_separation
    assert north_line - toilet.position[1] >= required_centerline_separation
    # Moving only the flange would lengthen this leg below UPC 708.0's required grade.
    south_run_in_inches = (drain.path[1][1] - drain.path[2][1]) / INCH
    fall_in_inches = (drain.z_m[1] - drain.z_m[2]) / INCH
    assert fall_in_inches / (south_run_in_inches / 12) >= 0.25


def test_every_visible_drawer_can_fully_extend_past_the_toilet(catlin_plan, catlin_model_ro):
    types = {typ.tag: typ for typ in catlin_plan.library.furniture_types}
    objects = _objects(catlin_model_ro)
    toilet = objects["FX-S-BATH1-WC"]
    toilet_polygon = Polygon(toilet.footprint)
    drawer_count = 0
    for tag in CABINET_TAGS:
        cabinet = objects[tag]
        typ = types[cabinet.type_ref]
        assert abs(cabinet.rotation_degrees) == pytest.approx(180)
        x0, _, x1, front_y = Polygon(cabinet.footprint).bounds
        parts = model_parts(typ.plan_symbol, *(d.meters for d in typ.footprint), typ.height.meters)
        fronts = [part for part in parts if part["color"] == "porcelain"]
        for front in fronts:
            bottom = front["center"][2] - front["size"][2] / 2
            top = front["center"][2] + front["size"][2] / 2
            if bottom >= 44.5 * INCH:
                # Both hinged shelf doors start above the WC's entire body.
                assert cabinet.body_z0_m + bottom > toilet.body_z1_m
                continue
            drawer_count += 1
            overlaps_height = (cabinet.body_z0_m + bottom < toilet.body_z1_m
                               and cabinet.body_z0_m + top > toilet.body_z0_m)
            sweep = box(x0, front_y, x1, front_y + 21.375 * INCH)
            assert not overlaps_height or not sweep.intersects(toilet_polygon), tag
    assert drawer_count == 5


def test_run_is_flush_and_has_a_stock_matte_white_end_panel(catlin_plan, catlin_model_ro):
    objects = _objects(catlin_model_ro)
    bounds = [Polygon(objects[tag].footprint).bounds for tag in CABINET_TAGS]
    assert [bound[0] / INCH for bound in bounds] == pytest.approx((7.125, 31.125, 55.125))
    assert [bound[1] / INCH for bound in bounds] == pytest.approx((321.385,) * 3)
    assert [bound[3] / INCH for bound in bounds] == pytest.approx((346.260,) * 3)
    cover = objects["FURN-S-BATH1-CLOSET-COVER"]
    typ = next(t for t in catlin_plan.library.furniture_types if t.tag == cover.type_ref)
    assert typ.product_ref == "PROD-IKEA-FORBATTRA-MATTE-25-90"
    assert Polygon(cover.footprint).bounds[2:] == pytest.approx((79.625 * INCH, 346.260 * INCH))
    assert cover.body_z1_m == pytest.approx(objects[CABINET_TAGS[0]].body_z1_m)


def test_heating_keeps_its_cable_and_clearance_from_all_fixed_storage(catlin_plan, catlin_model_ro):
    objects = _objects(catlin_model_ro)
    zone = next(zone for zone in catlin_model_ro.floor_heat if zone.tag == "FH-S-BATH1")
    polygon = Polygon(zone.zone)
    assert polygon.is_valid
    assert polygon.area / SQFT == pytest.approx(26.82096354)
    assert polygon.area / SQFT >= 26.7
    authored_zone = next(e for e in catlin_plan.all_elements() if e.tag == zone.tag)
    assert authored_zone.watts == 338
    assert round(polygon.area / SQFT * 22.8) == 612
    for obj in objects.values():
        if obj.room != "RM-S-BATH1":
            continue
        if obj.kind != "Fixture" and not obj.tag.startswith("FURN-S-BATH1-CLOSET"):
            continue
        assert polygon.distance(Polygon(obj.footprint)) >= 2 * INCH - 1e-9, obj.tag
    # Schluter also requires seven inches from the drain. The drain stays at its WC centre.
    assert polygon.distance(Point(objects["FX-S-BATH1-WC"].position)) > 7 * INCH


def test_tall_rail_is_backed_on_both_wall_segments_and_stays_below_the_ceiling(
        catlin_plan, catlin_model_ro):
    objects = _objects(catlin_model_ro)
    room = next(room for room in catlin_model_ro.rooms if room.tag == "RM-S-BATH1")
    for tag in CABINET_TAGS:
        cabinet = objects[tag]
        cabinet_height = cabinet.body_z1_m - cabinet.body_z0_m
        assert room.clear_height_m - cabinet_height == pytest.approx(11.5 * INCH)
    for tag, wall_tag in (("BK-S-BD-N-SEKTION", "W-S-BD-N"),
                          ("BK-S-BD-N1B-SEKTION", "W-S-BD-N1B")):
        band = catlin_plan.by_tag(tag)
        assert band.wall_ref == wall_tag
        assert band.face == "left"
        # Installed rail band translated from the finished floor to the storey datum.
        rail_screw_height = (94.25 + 1.5) * INCH
        band_top = band.elevation.meters + band.height.meters
        assert band.elevation.meters < rail_screw_height < band_top
