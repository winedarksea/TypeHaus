"""Every way into catlin's rainscreen cavity is closed: base, opening heads, and the top.

The ccSPF face in the 2" vented cavity has no protection but a physical one, so these pin
the derived closures (``resolve/rainscreen_closures.py``) and the roof deck that caps the top.
"""

from __future__ import annotations

import pytest

from typehaus.model.enums import TrimKind
from typehaus.quantities import inch
from typehaus.resolve.geometry import length, sub, wall_frame
from typehaus.resolve.rainscreen_closures import (
    BUG_SCREEN_HEIGHT_IN,
    head_screen_spans,
    rainscreen_cavity_m,
    screens_rainscreen_base,
)
from typehaus.takeoff.envelope import bug_screen_takeoff

_RAINSCREEN = ("EXT_2X6", "PLANT_EXT_2X6_HUMID")
_M_TO_FT = 3.280839895


def _head_screens(model) -> dict[str, object]:
    return {s.tag.removesuffix("-HEADSCREEN"): s for s in model.solids
            if s.tag.endswith("-HEADSCREEN")}


def test_every_window_and_door_on_a_rainscreen_wall_has_one_head_screen(catlin_model_ro):
    model = catlin_model_ro
    walls = {w.tag: w for w in model.walls}
    screens = _head_screens(model)
    expected = {o.tag for o in model.openings
                if o.kind in ("window", "door") and walls[o.host_wall].assembly in _RAINSCREEN}
    assert len(expected) >= 40, "catlin has 39 windows and 3 doors on its rainscreen walls"
    assert set(screens) == expected
    assert sum(s.tag.endswith("-HEADSCREEN") for s in model.solids) == len(expected)
    face = inch(3.5).meters
    for opening in model.openings:
        if opening.tag not in expected:
            continue
        wall = walls[opening.host_wall]
        screen = screens[opening.tag]
        assert screen.category == TrimKind.BUG_SCREEN.value
        assert screen.assembly == wall.assembly
        # On the head course, not the RO: the course is the 3-1/2" face of a flat 2x4.
        head = wall.base_ref_z_m + opening.sill_m + opening.height_m
        assert screen.z0_m == pytest.approx(head + face)
        assert screen.z1_m - screen.z0_m == pytest.approx(inch(BUG_SCREEN_HEIGHT_IN).meters)
        # RO plus a jamb post each side, measured off the solid itself.
        origin, tangent, _across, _length = wall_frame(wall)
        stations = [(x - origin[0]) * tangent[0] + (y - origin[1]) * tangent[1]
                    for x, y in screen.outline]
        assert max(stations) - min(stations) == pytest.approx(opening.width_m + 2 * face,
                                                              abs=1e-6)


def test_rough_openings_and_cavityless_walls_get_no_head_screen(catlin_model_ro):
    model = catlin_model_ro
    walls = {w.tag: w for w in model.walls}
    screens = _head_screens(model)
    rough = [o for o in model.openings if o.kind == "rough_opening"]
    assert rough, "catlin's ERV hoods are rough openings; the test needs one"
    assert not [o.tag for o in rough if o.tag in screens]
    bare = [o for o in model.openings
            if rainscreen_cavity_m(walls[o.host_wall].layers) is None]
    assert bare, "the garage and interior walls carry openings with no cavity"
    assert not [o.tag for o in bare if o.tag in screens]


def test_the_take_off_bills_base_plus_heads_and_agrees_with_the_solids(catlin_model_ro):
    model = catlin_model_ro
    rows = bug_screen_takeoff(model)
    assert rows
    billed_ft = sum(float(row["length_ft"]) for row in rows)
    base_m = sum(length(sub(w.axis[1], w.axis[0]))
                 for w in model.walls if screens_rainscreen_base(model, w))
    # The heads measured off the drawn solids, not the spans the take-off read: the two
    # can only agree if the geometry and the order are one derivation.
    walls = {w.tag: w for w in model.walls}
    heads_m = 0.0
    for opening in model.openings:
        screen = _head_screens(model).get(opening.tag)
        if screen is None:
            continue
        origin, tangent, _across, _length = wall_frame(walls[opening.host_wall])
        stations = [(x - origin[0]) * tangent[0] + (y - origin[1]) * tangent[1]
                    for x, y in screen.outline]
        heads_m += max(stations) - min(stations)
    assert billed_ft == pytest.approx((base_m + heads_m) * _M_TO_FT, abs=0.2)
    assert sum(int(row["heads"]) for row in rows) == len(_head_screens(model))
    spans = sum(len(head_screen_spans(model, w)) for w in model.walls)
    assert spans == len(_head_screens(model))


def test_the_cavity_top_stays_closed_by_the_roof_deck(catlin_model_ro):
    """Decision: no screen at the eave or rake, because there is no opening there. The deck
    oversails to the girt's OUTER face on every edge of RF-HOUSE, so the cavity's top is the
    underside of the deck. Clipped back at the wall sheathing face instead, it would leave
    the whole 2" cavity open into the roof edge."""
    from typehaus.model.enums import LayerFunction
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers, layer_edge_setbacks

    model = catlin_model_ro
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    layers = above_structure_layers(model.plan.library.resolve_assembly(roof.assembly))
    deck_index = next(i for i, layer in enumerate(layers)
                      if layer.function is LayerFunction.SHEATHING)
    deck = layer_edge_setbacks(model, roof)[deck_index]
    # Outboard of the girt band is the cladding alone, on every rainscreen wall.
    girt_face = max(
        sum(ly.thickness_m for ly in w.depth_layers()[i + 1:])
        for w in model.walls if w.assembly in _RAINSCREEN
        for i in [max(j for j, ly in enumerate(w.depth_layers()) if ly.function == "furring")])
    for edge in ("west", "east", "south", "north"):
        assert 0.0 <= deck[edge] <= girt_face + 1e-6, (edge, deck[edge], girt_face)


def test_every_base_screen_stands_at_least_six_inches_above_grade(catlin_model_ro):
    """A screen at grade is a screen under mulch and snow, which neither vents nor drains."""
    from typehaus.resolve.site_earth import local_grade_elevation_m

    model = catlin_model_ro
    bases = [s for s in model.solids if s.tag.endswith("-BUGSCREEN")]
    assert bases
    for screen in bases:
        grade, _why = local_grade_elevation_m(model, list(screen.outline))
        assert screen.z0_m - grade >= inch(6).meters, (screen.tag, screen.z0_m - grade)
