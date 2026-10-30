"""All six bathing installations omit coverings, while vanity and WC floors remain."""

from dataclasses import replace

import pytest
from shapely.geometry import Point, Polygon

from typehaus.resolve.fixture_floor_finish import resolve_fixture_floor_finishes
from typehaus.resolve.overlay import union_all
from typehaus.resolve.walking_surface import room_finish_at
from typehaus.takeoff.finishes import floor_finish_rows

_BATHING_FIXTURES = {
    "FX-B-SAUNA-SH": ("RM-B-SAUNA", -109.4375),
    "FX-M-BATH2-SH": ("RM-M-BATH2", 0.75),
    "FX-M-BATH2-TUB": ("RM-M-BATH2", 1.75),
    "FX-S-BATH1-SH": ("RM-S-BATH1", 120.75),
    "FX-S-SUITEBATH-TUBSH": ("RM-S-SUITEBATH", 120.75),
    "FX-A-STUBATH-SH": ("RM-A-STUBATH", 240.75),
}


def _geometry(parts):
    return union_all([Polygon(outline, holes=list(holes)) for outline, holes in parts])


@pytest.mark.parametrize("tag", _BATHING_FIXTURES)
def test_installed_base_has_no_covering_and_correct_bearing_plane(catlin_model_ro, tag):
    model = catlin_model_ro
    room_tag, elevation_in = _BATHING_FIXTURES[tag]
    placed = next(item for item in model.canvas_objects if item.tag == tag)
    room = next(room for room in model.rooms if room.tag == room_tag)
    field = _geometry(room.field_finish)
    exclusion = _geometry(room.floor_finish_exclusions)
    assert exclusion.covers(Polygon(placed.footprint).centroid)
    assert placed.z_m / 0.0254 == pytest.approx(elevation_in)
    coating = room_tag == "RM-B-SAUNA"
    if coating:
        assert room.field_area_m2 == pytest.approx(66.5054 / 10.7639104, abs=1e-6)
    else:
        assert field.intersection(exclusion).area < 1e-10
        assert field.intersection(Polygon(placed.footprint)).area < 1e-10
    assert room_finish_at(model, placed.storey, placed.position)[1] == (
        "sealed-concrete" if coating else None)


def test_tub_deck_cutout_and_aprons_do_not_restore_tile(catlin_model_ro):
    model = catlin_model_ro
    room = next(room for room in model.rooms if room.tag == "RM-M-BATH2")
    field = _geometry(room.field_finish)
    deck = next(solid for solid in model.solids if solid.tag == "SL-M-TUBDK")
    assert field.intersection(Polygon(deck.outline)).area < 1e-10
    for hole in deck.voids:
        assert field.intersection(Polygon(hole)).area < 1e-10
    for apron in model.panelings:
        if apron.tag == "WP-M-BATH2-TUBDK-APRON":
            assert field.intersection(Polygon(apron.outline)).area < 1e-10
    for tag in ("FX-M-BATH2-SINK", "FX-M-BATH2-WC"):
        placed = next(item for item in model.canvas_objects if item.tag == tag)
        assert field.covers(Point(placed.position))
        assert field.intersection(Polygon(placed.footprint)).area == pytest.approx(
            Polygon(placed.footprint).intersection(Polygon(room.clear_face)).area, abs=1e-8)


def test_takeoff_and_membranes_bill_only_retained_floor(catlin_model_ro):
    rows = floor_finish_rows(catlin_model_ro)
    for finish, net, order in (("catlin-tile-opera-blue", 39.5, 48),
                                ("catlin-tile-carrara", 59.9, 69),
                                ("catlin-tile-kaleo-brick", 34.2, 40)):
        row = next(row for row in rows if row["finish"] == finish)
        assert row["net_area_sqft"] == net
        assert row["order_area_sqft"] == order
        companions = [row for row in rows if row.get("under") == finish]
        assert companions
        assert all(row["net_area_sqft"] == net and row["order_area_sqft"] == order
                   for row in companions)
    attic = next(room for room in catlin_model_ro.rooms if room.tag == "RM-A-STUBATH")
    assert attic.field_area_m2 * 10.7639104 == pytest.approx(28.4, abs=0.05)


def test_existing_heat_zones_still_fit_and_uncut_rooms_remain_identical(catlin_model_ro):
    model = catlin_model_ro
    for heat in model.floor_heat:
        room_ref = model.plan.by_tag(heat.tag).room_ref
        if room_ref not in ("RM-M-BATH2", "RM-S-BATH1"):
            continue
        room = next(room for room in model.rooms if room.tag == room_ref)
        assert _geometry(room.field_finish).buffer(1e-6).covers(Polygon(heat.zone))
    # Rerun on a shallow model copy: all records are frozen and the session model is read-only.
    copied = replace(model, rooms=list(model.rooms))
    assert not resolve_fixture_floor_finishes(copied)
    assert copied.rooms == model.rooms
    for room in copied.rooms:
        if room.tag not in {pair[0] for pair in _BATHING_FIXTURES.values()}:
            assert not room.floor_finish_exclusions


def test_json_carries_actual_exclusion_parts(catlin_model_ro):
    from typehaus.server.model_json_spaces import spaces_json

    payload = spaces_json(catlin_model_ro, None)
    for room in catlin_model_ro.rooms:
        row = next(row for row in payload["rooms"] if row["tag"] == room.tag)
        expected = _geometry(room.floor_finish_exclusions)
        actual = union_all([Polygon(part["outline"], holes=part["holes"])
                            for part in row["floor_finish_exclusions"]])
        assert actual.equals(expected)
