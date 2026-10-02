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


def test_toilet_position_and_its_required_clear_floor_remain_intact(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    toilet = objects["FX-S-BATH1-WC"]
    assert toilet.uid == "CSQ801AAAA"
    assert toilet.position == pytest.approx((0.560313, 363.5 * INCH))
    for tag in (*CABINET_TAGS, "FURN-S-BATH1-CLOSET-COVER", "FURN-S-BATH1-CLOSET-SCRIBE"):
        cabinet = Polygon(objects[tag].footprint)
        assert not cabinet.intersects(Polygon(toilet.footprint))
        assert all(not cabinet.intersects(Polygon(zone)) for zone in toilet.required_clearances)


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
        if obj.room != "RM-S-BATH1" or obj.kind not in {"Fixture", "Furniture"}:
            continue
        assert polygon.distance(Polygon(obj.footprint)) >= 2 * INCH - 1e-9, obj.tag
    # Schluter also requires seven inches from the drain. The drain stays at its WC centre.
    assert polygon.distance(Point(objects["FX-S-BATH1-WC"].position)) > 7 * INCH
