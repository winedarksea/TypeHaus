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


def test_unknown_and_missing_symbols_yield_no_geometry() -> None:
    for symbol in (None, "", "not-a-symbol"):
        assert plan_symbol_strokes(symbol, 1.0, 1.0) == ()
        assert model_parts(symbol, 1.0, 1.0, 1.0) == ()
    # A degenerate size is not a crash, it is simply nothing to draw.
    assert plan_symbol_strokes("sofa", 0.0, 1.0) == ()
    assert model_parts("sofa", 1.0, 1.0, 0.0) == ()


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
def test_parts_stay_inside_the_declared_box_and_name_a_real_colour(symbol: str, size: tuple) -> None:
    width, depth, height = size
    parts = model_parts(symbol, width, depth, height)
    assert parts, f"{symbol} massed nothing at {size}"
    for part in parts:
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        assert part["color"] in PART_COLORS
        assert min(sx, sy, sz) > 0, f"{symbol} has a degenerate part"
        assert abs(cx) + sx / 2 <= width / 2 + TOLERANCE, f"{symbol} part escapes width"
        assert abs(cy) + sy / 2 <= depth / 2 + TOLERANCE, f"{symbol} part escapes depth"
        assert cz - sz / 2 >= -TOLERANCE, f"{symbol} part sinks below its base"
        assert cz + sz / 2 <= height + TOLERANCE, f"{symbol} part escapes its height"


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
def test_generation_is_pure_and_deterministic(symbol: str) -> None:
    first = plan_symbol_strokes(symbol, 1.2, 0.8), model_parts(symbol, 1.2, 0.8, 0.9)
    second = plan_symbol_strokes(symbol, 1.2, 0.8), model_parts(symbol, 1.2, 0.8, 0.9)
    assert first == second


@pytest.mark.parametrize("symbol", sorted(_REGISTRY))
def test_the_plan_glyph_does_not_depend_on_the_objects_height(symbol: str) -> None:
    """``plan_symbol_strokes`` passes a nominal height; that has to be a no-op for strokes."""
    from typehaus.model.placeable_symbols import symbol_geometry

    assert symbol_geometry(symbol, 1.2, 0.8, 0.4)[0] == symbol_geometry(symbol, 1.2, 0.8, 2.1)[0]


def test_every_colour_role_resolves_to_a_hex_string() -> None:
    for role in PART_COLORS:
        assert part_hex(role).startswith("#") and len(part_hex(role)) == 7


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
