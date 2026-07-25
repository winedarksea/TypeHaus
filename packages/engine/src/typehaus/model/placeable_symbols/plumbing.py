"""Plumbing-fixture glyphs, drawn against drafting convention rather than parameterised.

These are the most conventionalized symbols in architectural drafting — a toilet is a tank
rectangle plus an ovoid bowl and a shower is a square with its diagonals, not a box with a
door — so forcing them into the ``_families`` shapes would lose exactly the thing that makes
them readable. They are hand-drawn here instead, and they share only the basin helper below.

Every fixture faces the room: its wall side is ``+y`` (the object's back), matching the
attachment convention the resolver already uses.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import (DETAIL_WEIGHT, Part, box, circle, clamp,
                                                     ellipse, line, rect)

__all__ = ["PLUMBING_SYMBOLS"]


def _basin(cx: float, cy: float, width: float, depth: float, z0: float, z1: float,
           wall_t: float, color: str) -> list[Part]:
    """A hollow vessel as four rim walls over a floor — an opaque box would read as solid."""
    wall_t = min(wall_t, width * 0.3, depth * 0.3, (z1 - z0) * 0.5)
    return [box(cx, cy, z0, z0 + wall_t, width, depth, color),
            box(cx, cy + depth / 2 - wall_t / 2, z0, z1, width, wall_t, color),
            box(cx, cy - depth / 2 + wall_t / 2, z0, z1, width, wall_t, color),
            box(cx - width / 2 + wall_t / 2, cy, z0, z1, wall_t, depth - 2 * wall_t, color),
            box(cx + width / 2 - wall_t / 2, cy, z0, z1, wall_t, depth - 2 * wall_t, color)]


def toilet() -> Builder:
    """Tank rectangle at the wall, ovoid bowl into the room, seat ring — the standard glyph."""

    def build(width: float, depth: float, height: float) -> Geometry:
        tank_d = clamp(depth * 0.28, 0.15, depth * 0.34)
        tank_cy = depth / 2 - tank_d / 2
        bowl_rx = width * 0.42
        bowl_ry = (depth - tank_d) * 0.5
        bowl_cy = -depth / 2 + bowl_ry
        seat_top = min(0.42, height * 0.5)
        strokes = [rect(0, tank_cy, width, tank_d, fill="porcelain"),
                   ellipse(0, bowl_cy, bowl_rx, bowl_ry, fill="porcelain"),
                   ellipse(0, bowl_cy, bowl_rx * 0.7, bowl_ry * 0.72, weight=DETAIL_WEIGHT)]
        seat_t = min(0.05, seat_top * 0.2)
        parts = [box(0, tank_cy, seat_top, height, width, tank_d, "porcelain"),
                 box(0, tank_cy, 0.0, seat_top, width * 0.55, tank_d * 0.8, "porcelain"),
                 box(0, bowl_cy, 0.0, seat_top - seat_t, bowl_rx * 1.3, bowl_ry * 1.3,
                     "porcelain"),
                 box(0, bowl_cy, seat_top - seat_t, seat_top, bowl_rx * 2, bowl_ry * 2,
                     "porcelain")]
        return tuple(strokes), tuple(parts)

    return build


# A fixture's catalog height is its overall height — spout included — so the deck plane sits
# this far below it. Keeping the faucet inside the type's box is what lets the bbox invariant
# hold for every symbol without special cases.
FAUCET_HEIGHT_M = 0.14


def _deck_height(height: float) -> tuple[float, float]:
    faucet = min(FAUCET_HEIGHT_M, height * 0.16)
    return height - faucet, faucet


def lavatory(*, pedestal: bool = False) -> Builder:
    """A wall-hung or pedestal lavatory: outline, oval basin, drain, faucet at the wall."""

    def build(width: float, depth: float, height: float) -> Geometry:
        basin_ry = depth * 0.34
        basin_cy = -depth * 0.06
        rim = min(0.03, width * 0.06)
        deck_z, faucet = _deck_height(height)
        strokes = [rect(0, 0, width, depth, fill="porcelain"),
                   ellipse(0, basin_cy, width * 0.34, basin_ry, weight=DETAIL_WEIGHT),
                   circle(0, basin_cy, min(width, depth) * 0.035, weight=DETAIL_WEIGHT),
                   line((-width * 0.08, depth / 2 - depth * 0.12),
                        (width * 0.08, depth / 2 - depth * 0.12))]
        bowl_h = min(0.16, deck_z * 0.8)
        parts = [*_basin(0, basin_cy, width * 0.8, basin_ry * 2, deck_z - bowl_h, deck_z,
                         rim, "porcelain"),
                 box(0, depth / 2 - depth * 0.1, deck_z, deck_z + faucet, width * 0.1,
                     depth * 0.12, "metal")]
        if pedestal:
            parts.append(box(0, 0, 0.0, deck_z - bowl_h, width * 0.3, depth * 0.35,
                             "porcelain"))
        return tuple(strokes), tuple(parts)

    return build


def vanity() -> Builder:
    """A sink base: counter slab, cabinet under, oval basin dropped in."""

    def build(width: float, depth: float, height: float) -> Geometry:
        deck_z, faucet = _deck_height(height)
        top_t = min(0.04, deck_z * 0.2)
        kick = min(0.09, deck_z * 0.12)
        basin_ry = depth * 0.3
        basin_cy = -depth * 0.04
        strokes = [rect(0, 0, width, depth, fill="counter"),
                   ellipse(0, basin_cy, width * 0.24, basin_ry, weight=DETAIL_WEIGHT),
                   circle(0, basin_cy, min(width, depth) * 0.03, weight=DETAIL_WEIGHT),
                   line((-width / 2, -depth / 2 + 0.02), (width / 2, -depth / 2 + 0.02)),
                   line((-width * 0.06, depth / 2 - depth * 0.1),
                        (width * 0.06, depth / 2 - depth * 0.1))]
        parts = [box(0, 0, deck_z - top_t, deck_z, width, depth, "counter"),
                 box(0, 0.01, kick, deck_z - top_t, width, depth - 0.02, "wood"),
                 box(0, 0.03, 0.0, kick, width * 0.98, depth - 0.06, "wood-dark"),
                 *_basin(0, basin_cy, width * 0.5, basin_ry * 2,
                         max(kick, deck_z - top_t - 0.16), deck_z - top_t, 0.02, "porcelain"),
                 box(0, depth / 2 - depth * 0.08, deck_z, deck_z + faucet, width * 0.08,
                     depth * 0.1, "metal")]
        return tuple(strokes), tuple(parts)

    return build


def tub() -> Builder:
    """An alcove tub: rim rectangle, rounded basin, drain at the plumbing end."""

    def build(width: float, depth: float, height: float) -> Geometry:
        rim = clamp(min(width, depth) * 0.08, 0.04, 0.09)
        basin_w = width - 2 * rim
        basin_d = depth - 2 * rim
        drain_cx = -width / 2 + rim + basin_w * 0.12
        strokes = [rect(0, 0, width, depth, fill="porcelain"),
                   ellipse(0, 0, basin_w / 2, basin_d / 2, weight=DETAIL_WEIGHT),
                   circle(drain_cx, 0, min(width, depth) * 0.035, weight=DETAIL_WEIGHT)]
        parts = _basin(0, 0, width, depth, 0.0, height, rim, "porcelain")
        return tuple(strokes), tuple(parts)

    return build


def shower() -> Builder:
    """A shower enclosure: the square-with-diagonals convention, plus a pan, curb and glass."""

    def build(width: float, depth: float, height: float) -> Geometry:
        curb = clamp(min(width, depth) * 0.06, 0.03, min(width, depth) * 0.12)
        pan_h = min(curb, height * 0.2)
        wall_z0 = min(curb * 2, height * 0.4)
        strokes = [rect(0, 0, width, depth, fill="porcelain"),
                   line((-width / 2, -depth / 2), (width / 2, depth / 2)),
                   line((-width / 2, depth / 2), (width / 2, -depth / 2)),
                   circle(0, 0, min(width, depth) * 0.04, weight=DETAIL_WEIGHT)]
        glass_t = min(0.012, min(width, depth) * 0.1)
        head = min(0.06, min(width, depth) * 0.2)
        parts = [box(0, 0, 0.0, pan_h, width, depth, "porcelain"),
                 box(0, -depth / 2 + curb / 2, 0.0, wall_z0, width, curb, "porcelain"),
                 # Two enclosing walls of glass; the other two sides are the room's walls.
                 box(0, -depth / 2 + glass_t / 2, wall_z0, height, width, glass_t, "glass"),
                 box(-width / 2 + glass_t / 2, 0, wall_z0, height, glass_t, depth, "glass"),
                 box(0, depth / 2 - head / 2, height * 0.78, height * 0.82, head, head,
                     "metal")]
        return tuple(strokes), tuple(parts)

    return build


def kitchen_sink(*, bowls: int = 2) -> Builder:
    """A drop-in kitchen sink: counter cut-out, one or two bowls, faucet at the wall."""

    def build(width: float, depth: float, height: float) -> Geometry:
        rim = clamp(min(width, depth) * 0.05, 0.02, 0.05)
        deck_d = depth * 0.2
        bowl_d = depth - deck_d - 2 * rim
        bowl_cy = -depth / 2 + rim + bowl_d / 2
        count = max(1, bowls)
        bowl_w = (width - rim * (count + 1)) / count
        # The bowls hang *below* the deck, so the type's mount elevation places the deck at
        # counter height and the sink reads correctly against the cabinets around it.
        deck_z, faucet = _deck_height(height)
        strokes = [rect(0, 0, width, depth, fill="counter"),
                   circle(0, depth / 2 - deck_d / 2, min(width, depth) * 0.05,
                          weight=DETAIL_WEIGHT)]
        deck_t = min(0.02, deck_z * 0.3)
        parts: list[Part] = [box(0, depth / 2 - deck_d / 2, deck_z - deck_t, deck_z, width,
                                 deck_d, "counter"),
                             box(0, depth / 2 - deck_d * 0.4, deck_z, deck_z + faucet,
                                 width * 0.05, deck_d * 0.3, "metal")]
        for index in range(count):
            cx = -width / 2 + rim + bowl_w * (index + 0.5) + rim * index
            strokes.append(rect(cx, bowl_cy, bowl_w, bowl_d, weight=DETAIL_WEIGHT))
            strokes.append(circle(cx, bowl_cy, min(bowl_w, bowl_d) * 0.06,
                                  weight=DETAIL_WEIGHT))
            parts.extend(_basin(cx, bowl_cy, bowl_w, bowl_d, 0.0, deck_z, 0.015,
                                "appliance-steel"))
        return tuple(strokes), tuple(parts)

    return build


PLUMBING_SYMBOLS: dict[str, Builder] = {
    "toilet": toilet(),
    "lavatory": lavatory(pedestal=True),
    "vanity": vanity(),
    "tub": tub(),
    "shower": shower(),
    "kitchen-sink": kitchen_sink(bowls=2),
}
