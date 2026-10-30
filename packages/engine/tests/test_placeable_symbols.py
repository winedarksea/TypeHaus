"""Invariants every generated placeable symbol has to hold, whatever it draws.

The symbol registry is the seam between one author (the glyph) and four renderers (canvas,
sheets, viewer, glTF). Nothing downstream re-measures geometry, so the guarantees a renderer
relies on — everything inside the declared W×D×H, every colour resolvable, pure and
deterministic — have to be proved here rather than eyeballed per glyph.

The size sweep is parameterised over the whole registry on purpose: a new builder inherits
these cases the moment it is registered.
"""

from __future__ import annotations

import math

import pytest

from typehaus.model.placeable_symbols import (PART_COLORS, PENDING_SYMBOLS, SYMBOL_NAMES,
                                              _REGISTRY, model_parts, part_hex, place_local,
                                              plan_symbol_strokes)

TOLERANCE = 1e-9

# Deliberately spans the catalog's extremes — a 4"x12" register through a 110" sectional —
# because the families scale by fraction and clamp by absolute limit, and only the ends of
# that range can break the clamps.
SIZES = [(0.30, 0.10, 0.04), (0.56, 0.41, 0.66), (1.02, 0.71, 0.91), (2.79, 2.16, 0.86)]


def test_every_vocabulary_name_is_implemented_or_explicitly_pending() -> None:
    assert set(_REGISTRY) | PENDING_SYMBOLS == set(SYMBOL_NAMES)
    assert not (set(_REGISTRY) & PENDING_SYMBOLS)


def test_espresso_machine_has_front_dispensing_space_and_top_hopper() -> None:
    width, depth, height = 0.24765, 0.4318, 0.37465
    parts = model_parts("espresso-machine", width, depth, height)
    hopper = [part for part in parts if part["color"] == "glass"
              and part["center"][2] > height * 0.8]
    assert len(hopper) == 1
    assert hopper[0]["center"][1] > 0
    assert any(part["color"] == "screen" and part["center"][2] > height * 0.75
               for part in parts)
    # The tray is below the twin spouts, leaving a real cup-sized space in front.
    spouts = [part for part in parts if part["color"] == "metal-black"
              and part["size"][0] == pytest.approx(width * 0.045)]
    assert len(spouts) == 2
    assert all(part["center"][1] < -depth * 0.26 for part in spouts)
    assert min(part["center"][2] - part["size"][2] / 2 for part in spouts) > height * 0.30
    assert any(part["color"] == "glass" and part["center"][0] < 0
               and part["center"][1] < 0 for part in parts)  # attached milk carafe
    assert any(part["color"] == "glass" and part["center"][0] > 0
               and part["center"][1] > 0 for part in parts)  # side water tank


def test_unknown_and_missing_symbols_yield_no_geometry() -> None:
    for symbol in (None, "", "not-a-symbol"):
        assert plan_symbol_strokes(symbol, 1.0, 1.0) == ()
        assert model_parts(symbol, 1.0, 1.0, 1.0) == ()
    # A degenerate size is not a crash, it is simply nothing to draw.
    assert plan_symbol_strokes("sofa", 0.0, 1.0) == ()
    assert model_parts("sofa", 1.0, 1.0, 0.0) == ()


def test_receptacles_show_distinct_faces_and_remain_orange() -> None:
    combo = model_parts("receptacle-combined", .1, .05, .1)
    quad = model_parts("receptacle-quad", .1, .05, .1)
    assert combo[0]["color"] == quad[0]["color"] == "electrical-orange"
    combo_marks = [part for part in combo if part["color"] == "electrical-recess"]
    quad_marks = [part for part in quad if part["color"] == "electrical-recess"]
    assert len(combo_marks) == 8
    assert len(quad_marks) == 16
    assert len({round(part["center"][2], 4) for part in quad_marks}) >= 4
    assert len({round(part["center"][0], 4) for part in quad_marks}) >= 4


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
@pytest.mark.parametrize("size", SIZES)
def test_strokes_stay_inside_the_declared_footprint(symbol: str, size: tuple) -> None:
    width, depth, _ = size
    strokes = plan_symbol_strokes(symbol, width, depth)
    assert strokes, f"{symbol} drew nothing at {size}"
    for stroke in strokes:
        assert len(stroke["points"]) >= 2
        assert stroke["weight"] > 0
        assert stroke["fill"] is None or stroke["fill"] in PART_COLORS
        for x, y in stroke["points"]:
            assert abs(x) <= width / 2 + TOLERANCE, f"{symbol} stroke escapes width"
            assert abs(y) <= depth / 2 + TOLERANCE, f"{symbol} stroke escapes depth"


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
@pytest.mark.parametrize("size", SIZES)
def test_parts_stay_inside_the_declared_box_and_name_a_real_colour(
    symbol: str, size: tuple,
) -> None:
    width, depth, height = size
    parts = model_parts(symbol, width, depth, height)
    assert parts, f"{symbol} massed nothing at {size}"
    # Configured kitchen types retain the legacy FRAME envelope. Door/hardware projection
    # is explicit; all other symbols continue to promise a finished-product envelope.
    projection = 2 * 0.0254 if symbol.startswith("sektion-axstad-kitchen-") else 0.0
    side_projection = projection if symbol.endswith("corner-wall") else 0.0
    if symbol == "swanstone-flex-3636":
        # The separately supported return/post sits on the adjacent tub deck.
        side_projection = width * 1.5 / 36
    for part in parts:
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        assert part["color"] in PART_COLORS
        assert min(sx, sy, sz) > 0, f"{symbol} has a degenerate part"
        assert abs(cx) + sx / 2 <= width / 2 + side_projection + TOLERANCE, (
            f"{symbol} part escapes width")
        assert abs(cy) + sy / 2 <= depth / 2 + projection + TOLERANCE, (
            f"{symbol} part escapes depth")
        assert cz - sz / 2 >= -TOLERANCE, f"{symbol} part sinks below its base"
        assert cz + sz / 2 <= height + TOLERANCE, f"{symbol} part escapes its height"


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
def test_generation_is_pure_and_deterministic(symbol: str) -> None:
    first = plan_symbol_strokes(symbol, 1.2, 0.8), model_parts(symbol, 1.2, 0.8, 0.9)
    second = plan_symbol_strokes(symbol, 1.2, 0.8), model_parts(symbol, 1.2, 0.8, 0.9)
    assert first == second


def test_cellular_blind_has_a_pleated_raised_shade_at_the_window_head() -> None:
    from typehaus.library.placeables.allowances import CELLULAR_BLIND_2748
    from typehaus.model.canvas import model_symbol_for
    from typehaus.quantities import inch

    product = CELLULAR_BLIND_2748
    symbol = model_symbol_for(product)
    width, depth = (dimension.meters for dimension in product.footprint)
    height = product.height.meters
    strokes = plan_symbol_strokes(symbol, width, depth)
    parts = model_parts(symbol, width, depth, height)

    assert len(strokes) == 2
    assert strokes[0]["closed"]
    headrail, shade, bottom_rail, *pleats = parts
    assert len(pleats) >= 20
    assert headrail["center"][2] + headrail["size"][2] / 2 == pytest.approx(height)
    stack_bottom = bottom_rail["center"][2] - bottom_rail["size"][2] / 2
    assert stack_bottom == pytest.approx(height - inch(4).meters)
    assert all(part["center"][2] - part["size"][2] / 2 >= stack_bottom - TOLERANCE
               for part in parts)
    assert bottom_rail["center"][2] + bottom_rail["size"][2] / 2 == pytest.approx(
        shade["center"][2] - shade["size"][2] / 2)
    assert shade["center"][2] + shade["size"][2] / 2 == pytest.approx(
        headrail["center"][2] - headrail["size"][2] / 2)
    assert all(pleat["color"] == "casework-shadow" for pleat in pleats)


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
def test_the_plan_glyph_does_not_depend_on_the_objects_height(symbol: str) -> None:
    """``plan_symbol_strokes`` passes a nominal height; that has to be a no-op for strokes."""
    from typehaus.model.placeable_symbols import symbol_geometry

    assert symbol_geometry(symbol, 1.2, 0.8, 0.4)[0] == symbol_geometry(symbol, 1.2, 0.8, 2.1)[0]


def test_every_colour_role_resolves_to_a_hex_string() -> None:
    for role in PART_COLORS:
        assert part_hex(role).startswith("#") and len(part_hex(role)) == 7


def test_single_bowl_undermount_has_actual_flange_bowl_and_separate_faucet():
    inch_m = 0.0254
    width, depth, height = (value * inch_m for value in (32, 22, 20))
    strokes = plan_symbol_strokes("kitchen-sink-undermount-single", width, depth)
    flange, bowl, drain, faucet = strokes
    for stroke, expected_width, expected_depth in ((flange, 32, 19), (bowl, 30, 17)):
        xs, ys = zip(*stroke["points"], strict=True)
        assert (max(xs) - min(xs)) / inch_m == pytest.approx(expected_width)
        assert (max(ys) - min(ys)) / inch_m == pytest.approx(expected_depth)
    flange_center_y = (min(y for _, y in flange["points"])
                       + max(y for _, y in flange["points"])) / 2
    assert flange_center_y / inch_m == pytest.approx(-1.5)
    # Drain and faucet circles both stay on the window centreline; rear drain is 4.5" forward.
    for stroke in (drain, faucet):
        center_x = (min(x for x, _ in stroke["points"])
                    + max(x for x, _ in stroke["points"])) / 2
        assert center_x == pytest.approx(0)
    parts = model_parts("kitchen-sink-undermount-single", width, depth, height)
    steel = [part for part in parts if part["color"] == "appliance-steel"]
    metal = [part for part in parts if part["color"] == "metal"]
    rim_z = max(part["center"][2] + part["size"][2] / 2 for part in steel)
    faucet_base_z = min(part["center"][2] - part["size"][2] / 2 for part in metal)
    assert rim_z == pytest.approx(10 * inch_m)
    assert faucet_base_z == pytest.approx(11.181 * inch_m)


def test_drawer_desk_has_two_drawers_on_each_side_and_open_knee_space() -> None:
    from typehaus.library.placeables import HEMNES_DESK_61

    width, depth = (length.meters for length in HEMNES_DESK_61.footprint)
    parts = model_parts("drawer-desk", width, depth, HEMNES_DESK_61.height.meters)
    desktop, *supports = parts
    pulls = [part for part in supports if part["color"] == "metal"]
    left_pulls = [part for part in pulls if part["center"][0] < 0]
    right_pulls = [part for part in pulls if part["center"][0] > 0]
    assert len(left_pulls) == len(right_pulls) == 2
    assert all(part["center"][1] < 0 for part in pulls)
    for left, right in zip(left_pulls, right_pulls, strict=True):
        assert left["center"] == pytest.approx(
            (-right["center"][0], right["center"][1], right["center"][2]),
        )
        assert left["size"] == right["size"]
    # Nothing below the desktop crosses the centre where the seated person's knees go.
    assert all(abs(part["center"][0]) > part["size"][0] / 2 for part in supports)
    desktop_bottom = desktop["center"][2] - desktop["size"][2] / 2
    support_top = max(part["center"][2] + part["size"][2] / 2 for part in supports)
    assert support_top == pytest.approx(desktop_bottom)


def test_suspended_linear_light_has_a_shallow_body_and_two_end_cables() -> None:
    """A grow tube's declared height is its drop, not a 27-inch-deep lamp box."""
    width, depth, height = 1.8288, 0.0762, 0.6858  # 6 ft x 3 in., dropped 2 ft 3 in.
    parts = model_parts("suspended-linear-light", width, depth, height)

    housing, lens, *cables = parts
    assert housing["color"] == "luminaire-housing"
    assert housing["size"][2] == pytest.approx(0.0762 - 0.0762 * 0.45)
    assert lens["color"] == "lamp"
    assert len(cables) == 2
    assert all(cable["color"] == "luminaire-housing" for cable in cables)
    assert all(cable["size"][2] == pytest.approx(height - 0.0762) for cable in cables)
    assert cables[0]["center"][0] == pytest.approx(-cables[1]["center"][0])
    assert cables[0]["center"][2] == pytest.approx((height + 0.0762) / 2)


def test_place_local_matches_the_resolvers_own_footprint_transform() -> None:
    """The resolver bakes rotation into ``footprint`` but not into symbol geometry, so the two
    transforms have to be the same one — otherwise a rotated sofa's arms leave its outline."""
    from typehaus.resolve.placeables import _transformed_polygon

    points = [(0.5, -0.25), (-0.5, 0.25), (0.0, 0.0)]
    for rotation in (0.0, 37.5, 90.0, -180.0):
        placed = place_local(points, (3.0, -1.5), rotation)
        expected = _transformed_polygon(points, (3.0, -1.5), rotation)
        assert all(a == pytest.approx(b) for pair in zip(placed, expected) for a, b in zip(*pair))
    # And it is a rigid motion: lengths survive.
    (ax, ay), (bx, by) = place_local([(0.0, 0.0), (1.0, 0.0)], (2.0, 2.0), 45.0)
    assert math.hypot(bx - ax, by - ay) == pytest.approx(1.0)


def test_wall_hung_toilet_has_no_tank_and_uses_the_whole_depth() -> None:
    """The whole point of the glyph: a wall-hung WC's cistern is in the wall, not on the bowl.

    ``toilet`` draws a tank rectangle across the back ~28% of its footprint. Drawing that on
    a wall-hung fixture puts an object on the sheet and in the viewer that does not exist,
    squashed into the china's 13 5/8" of height. What stands at ``+y`` here instead is the
    actuator plate, which is the only thing a finished wall shows.
    """
    width, depth, height = 0.381, 0.49022, 0.346  # FX-TOILET-WH: 15" x 19.3" x 13 5/8"
    strokes = plan_symbol_strokes("toilet-wall-hung", width, depth)
    bowl, seat, plate = strokes

    # The bowl reaches the front edge and stops only at the plate — no tank band behind it.
    assert min(y for _, y in bowl["points"]) == pytest.approx(-depth / 2)
    plate_depth = depth - (max(y for _, y in bowl["points"]) - min(y for _, y in bowl["points"]))
    assert plate_depth < depth * 0.21, "the plate has swollen into a tank"
    assert max(y for _, y in plate["points"]) == pytest.approx(depth / 2)
    assert min(y for _, y in plate["points"]) == pytest.approx(depth / 2 - plate_depth)
    assert bowl["fill"] == "porcelain" and plate["fill"] == "metal"
    assert seat["fill"] is None  # the seat ring is a detail line, not a filled shape

    # ``toilet``'s tank is a full-height box at the wall; this one's plate is a thin band.
    tank = model_parts("toilet", width, depth, height)[0]
    plate_part = model_parts("toilet-wall-hung", width, depth, height)[2]
    assert tank["size"][1] > plate_part["size"][1] * 3


def test_a_neo_angle_shower_draws_and_masses_its_pentagon_not_its_bounding_box() -> None:
    """The defect this closes: the type carried a five-sided ``footprint_shape`` that only
    the resolver's collision test read, so the sheets drew a 36" square and the viewer massed
    one — the cut corner existed in the model and in no drawing.

    Both halves come off ``neo_angle_points``, so the assertion is that the glyph outline, the
    pan's swept ring and the catalog outline are one polygon.
    """
    from typehaus.model.placeable_symbols.plumbing import (NEO_ANGLE_CUT_FRACTION,
                                                           neo_angle_points)

    size = 0.9144  # 36"
    ring = neo_angle_points(size, size, size * NEO_ANGLE_CUT_FRACTION)
    assert len(ring) == 5
    # The wall corner survives whole; the diagonally opposite one is gone.
    assert (size / 2, size / 2) in ring
    assert (-size / 2, -size / 2) not in ring

    outline = plan_symbol_strokes("shower-neo-angle", size, size)[0]
    assert outline["closed"] and outline["points"] == ring
    pan = model_parts("shower-neo-angle", size, size, 2.0)[0]
    assert pan["points"] == ring
    # The square pan is untouched: no cut, and its outline is still the plain rectangle.
    square = plan_symbol_strokes("shower", size, size)[0]
    assert len(square["points"]) == 4


def test_a_box_part_carries_no_ring_and_a_ringed_part_carries_its_bounding_box() -> None:
    """``points`` is the optional half of the contract: every consumer may fall back to
    ``center``/``size``, so a ringed part has to state a bounding box that is actually its
    own. Asserted over the whole registry — a new ringed builder inherits it."""
    for symbol in sorted(_REGISTRY):
        for width, depth, height in SIZES:
            for part in model_parts(symbol, width, depth, height):
                ring = part["points"]
                if not ring:
                    continue
                xs = [x for x, _ in ring]
                ys = [y for _, y in ring]
                cx, cy, _ = part["center"]
                sx, sy, _ = part["size"]
                assert cx == pytest.approx((min(xs) + max(xs)) / 2, abs=TOLERANCE)
                assert cy == pytest.approx((min(ys) + max(ys)) / 2, abs=TOLERANCE)
                assert sx == pytest.approx(max(xs) - min(xs), abs=TOLERANCE)
                assert sy == pytest.approx(max(ys) - min(ys), abs=TOLERANCE)


def test_wave_chandelier_is_five_strips_waving_in_elevation() -> None:
    """Five parallel strips in plan, each rising and falling along its length, lit underneath."""
    width, depth, height = 1.2192, 0.4064, 1.0668  # 48" x 16", 3'-6" assembly
    canopy, *rest = model_parts("wave-chandelier", width, depth, height)
    assert canopy["color"] == "brass"
    assert canopy["center"][2] + canopy["size"][2] / 2 == pytest.approx(height)
    cables = [p for p in rest if p["size"][0] < 0.01]
    bands = [p for p in rest if p["size"][0] >= 0.01]
    assert len(cables) == 10
    assert [p["color"] for p in bands[:2]] == ["lamp", "brass"]
    assert min(p["center"][2] - p["size"][2] / 2 for p in bands) == pytest.approx(0.0)
    rows = sorted({round(p["center"][1], 6) for p in bands})
    assert len(rows) == 5 and rows[-1] - rows[0] < depth
    first = [p for p in bands if round(p["center"][1], 6) == rows[0] and p["color"] == "lamp"]
    assert len(first) == 1 and "mesh" in first[0]
    bottoms = [z for _, _, z in first[0]["mesh"]["positions"]]
    assert max(bottoms) - min(bottoms) > 0.1  # it undulates, not a flat bar


def test_wall_tv_panel_reaches_its_mount_elevation_without_a_pedestal():
    width, depth, height = 2.16, 0.1016, 1.27
    panel, = model_parts("tv-wall", width, depth, height)
    assert panel["color"] == "screen"
    assert panel["size"] == pytest.approx((width, depth, height))
    assert panel["center"] == pytest.approx((0, 0, height / 2))
    assert all(stroke["fill"] != "wood-dark"
               for stroke in plan_symbol_strokes("tv-wall", width, depth))
    stand_parts = model_parts("tv", width, 0.4191, height)
    assert {part["color"] for part in stand_parts} == {"screen", "wood-dark", "metal"}
    assert stand_parts[0]["center"][2] - stand_parts[0]["size"][2] / 2 > 0


def test_roman_tub_filler_matches_the_align_envelope_and_outlet():
    from typehaus.model.placeable_symbols import _roman_tub_filler as dimensions

    inch_m = 0.0254
    width, depth, height = (value * inch_m for value in
                           (dimensions.TYPE_WIDTH_IN, dimensions.TYPE_DEPTH_IN,
                            dimensions.TYPE_HEIGHT_IN))
    strokes = plan_symbol_strokes("roman-tub-filler", width, depth)
    parts = model_parts("roman-tub-filler", width, depth, height)
    assert len(strokes) == 7 and {part["color"] for part in parts} == {"metal"}
    for part in parts:
        for axis, limit in ((0, width / 2), (1, depth / 2)):
            assert abs(part["center"][axis]) + part["size"][axis] / 2 <= limit + 1e-9
        assert part["center"][2] + part["size"][2] / 2 <= height + 1e-9
    hole_y = strokes[1]["points"][0][1]  # circle's first point lies on its horizontal radius
    outlet = parts[3]
    assert (hole_y - outlet["center"][1]) / inch_m == pytest.approx(7.25)
    assert (outlet["center"][2] - outlet["size"][2] / 2) / inch_m == pytest.approx(3.71875)
    assert [parts[i]["center"][0] / inch_m for i in (4, 7)] == pytest.approx([-5, 5])


@pytest.mark.parametrize("base", ["towel-bar", "towel-hook", "pivoting-paper-holder"])
def test_chrome_accessories_keep_their_geometry_with_a_silver_finish(base):
    size = (0.232918, 0.084582, 0.034036)
    nickel = model_parts(base, *size)
    chrome = model_parts(base + "-chrome", *size)
    assert len(nickel) == len(chrome)
    assert {p["color"] for p in chrome} == {"metal"}
    assert [{**p, "color": "metal"} for p in nickel] == list(chrome)


def test_countertop_microwave_door_window_and_control_column() -> None:
    width, depth, height = 0.5255, 0.4015, 0.3112
    parts = model_parts("countertop-microwave", width, depth, height)
    assert parts
    assert all(abs(part["center"][0]) <= width / 2 + 1e-9 for part in parts)
    assert max(part["center"][2] + part["size"][2] / 2 for part in parts) == pytest.approx(height)
    assert any(part["color"] == "screen" and part["center"][0] > 0 for part in parts)
    window = [part for part in parts if part["color"] == "metal-black"
              and part["size"][0] > width * 0.5]
    assert window and window[0]["center"][0] < 0


def test_curtain_track_draws_open_stacks_inside_the_closed_envelope() -> None:
    from typehaus.model.curtain_track import CurtainStack, CurtainTrackSpec
    from typehaus.model.placeable_symbols._curtain_track import curtain_track_geometry
    from typehaus.quantities import inch

    width, depth, height = 2.4, 0.1524, 2.74
    spec = CurtainTrackSpec(stacks=(CurtainStack(start=inch(0), width=inch(14)),
                                    CurtainStack(start=inch(79), width=inch(14.5))))
    _, parts = curtain_track_geometry(spec, width, depth, height)
    assert [part["color"] for part in parts] == ["appliance-white", "fabric", "fabric"]
    for part in parts:
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        assert abs(cx) + sx / 2 <= width / 2 + TOLERANCE
        assert abs(cy) + sy / 2 <= depth / 2 + TOLERANCE
        assert cz - sz / 2 >= -TOLERANCE and cz + sz / 2 <= height + TOLERANCE
    assert parts[1]["center"][0] - parts[1]["size"][0] / 2 == pytest.approx(-width / 2)
    _, rail_only = curtain_track_geometry(spec.model_copy(update={"show_curtains": False}),
                                          width, depth, height)
    assert rail_only == parts[:1]
