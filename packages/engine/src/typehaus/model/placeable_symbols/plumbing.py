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


def tub_shower() -> Builder:
    """A tub-shower combination: the tub glyph under a full-height three-sided surround.

    Drafting convention draws this as the alcove tub it is — the shower is not a second
    outline but the head, so the glyph adds a small filled dot on the plumbing end's wall
    where the riser lands, which is what distinguishes it from a plain ``tub`` on a plan.

    The type's height is the surround (about 7'), not the tub rim, so the massing splits
    the two: a tub basin at the bottom of the box and three tiled walls carried the rest of
    the way up. The open side is ``-y``, the side facing the room, exactly like ``shower``.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        rim = clamp(min(width, depth) * 0.08, 0.04, 0.09)
        basin_w = width - 2 * rim
        basin_d = depth - 2 * rim
        # Standard alcove tub rim, clamped so a short type still reads as tub-under-walls.
        tub_h = min(0.51, height * 0.4)
        drain_cx = -width / 2 + rim + basin_w * 0.12
        head_r = min(width, depth) * 0.03
        strokes = [rect(0, 0, width, depth, fill="porcelain"),
                   ellipse(0, 0, basin_w / 2, basin_d / 2, weight=DETAIL_WEIGHT),
                   circle(drain_cx, 0, min(width, depth) * 0.035, weight=DETAIL_WEIGHT),
                   # The shower head, over the plumbing end, drawn against the back wall.
                   circle(-width / 2 + rim, depth / 2 - rim, head_r, fill="metal")]
        wall_t = min(0.05, rim, depth * 0.1)
        parts = list(_basin(0, 0, width, depth, 0.0, tub_h, rim, "porcelain"))
        parts.append(box(0, depth / 2 - wall_t / 2, tub_h, height, width, wall_t, "porcelain"))
        for sign in (-1, 1):
            parts.append(box(sign * (width / 2 - wall_t / 2), 0, tub_h, height, wall_t,
                             depth - wall_t, "porcelain"))
        # Riser and head at the plumbing end, on the back wall above the drain.
        riser_t = min(0.035, width * 0.05)
        head_z = min(height * 0.85, height - riser_t)
        parts.append(box(-width / 2 + rim, depth / 2 - wall_t - riser_t / 2, tub_h, head_z,
                         riser_t, riser_t, "metal"))
        parts.append(box(-width / 2 + rim, depth / 2 - wall_t - riser_t * 1.5, head_z,
                         min(head_z + riser_t, height), riser_t * 2, riser_t * 2, "metal"))
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
    """A drop-in kitchen sink: a stainless rim deck, one or two bowls, a gooseneck faucet.

    Unlike a lavatory, a kitchen sink's overall height is not "a basin plus a spout tucked
    under the rim" — it is a ~9" bowl below the counter and a gooseneck of about the same
    reach above it. So this family splits the type's height in half rather than using
    ``_deck_height``, and ``height / 2`` is the *countertop plane*: the bowls hang below it
    into the sink base, and the rim flange rests on top of it the way a drop-in sink does.
    A type mounted at ``counter - height / 2`` therefore lands correctly with no fudge.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        rim = clamp(min(width, depth) * 0.05, 0.02, 0.05)
        deck_d = depth * 0.2
        bowl_d = depth - deck_d - 2 * rim
        bowl_cy = -depth / 2 + rim + bowl_d / 2
        count = max(1, bowls)
        bowl_w = (width - rim * (count + 1)) / count
        counter_z = height / 2.0            # the plane the flange sits on
        flange = min(0.02, counter_z * 0.2)
        deck_z = counter_z + flange         # top of the rim
        bowl_z0 = counter_z - min(0.23, counter_z * 0.95)
        faucet = height - deck_z
        faucet_cy = depth / 2 - deck_d * 0.5

        strokes = [rect(0, 0, width, depth, fill="counter"),
                   circle(0, faucet_cy, min(width, depth) * 0.05, weight=DETAIL_WEIGHT)]
        # The rim: a back deck carrying the faucet, the strip in front of it, a front lip,
        # ends, and a divider between bowls. Bands rather than one slab — a solid top would
        # bury the bowls it is supposed to frame — and between them they close the footprint,
        # so nothing of the cabinet below shows through the counter's cut.
        parts: list[Part] = [
            box(0, depth / 2 - deck_d / 2, counter_z, deck_z, width, deck_d,
                "appliance-steel"),
            box(0, depth / 2 - deck_d - rim / 2, counter_z, deck_z, width, rim,
                "appliance-steel"),
            box(0, -depth / 2 + rim / 2, counter_z, deck_z, width, rim, "appliance-steel"),
        ]
        for sign in (-1, 1):
            parts.append(box(sign * (width / 2 - rim / 2), 0, counter_z, deck_z, rim, depth,
                             "appliance-steel"))
        for index in range(count):
            cx = -width / 2 + rim + bowl_w * (index + 0.5) + rim * index
            strokes.append(rect(cx, bowl_cy, bowl_w, bowl_d, weight=DETAIL_WEIGHT))
            strokes.append(circle(cx, bowl_cy, min(bowl_w, bowl_d) * 0.06,
                                  weight=DETAIL_WEIGHT))
            parts.extend(_basin(cx, bowl_cy, bowl_w, bowl_d, bowl_z0, counter_z, 0.015,
                                "appliance-steel"))
            if index:  # the rim band the two bowls share
                parts.append(box(cx - bowl_w / 2 - rim / 2, bowl_cy, counter_z, deck_z, rim,
                                 bowl_d, "appliance-steel"))
        # Gooseneck: a column at the deck's back, an arm reaching forward over the bowls and a
        # short downturn at its end — the three moves that make a faucet read as a faucet from
        # any viewing angle instead of as a peg.
        shaft = min(0.032, width * 0.05, faucet * 0.3)
        spout_cy = bowl_cy + bowl_d * 0.18
        arm_z = height - shaft
        parts.extend([
            box(0, faucet_cy, deck_z, arm_z, shaft, shaft, "metal"),
            box(0, (faucet_cy + spout_cy) / 2, arm_z, height, shaft * 0.8,
                abs(faucet_cy - spout_cy) + shaft, "metal"),
            box(0, spout_cy, arm_z - faucet * 0.22, arm_z, shaft * 0.7, shaft * 0.7, "metal"),
        ])
        for sign in (-1, 1):  # the two lever handles, either side of the column
            handle_cx = sign * shaft * 2.2
            parts.append(box(handle_cx, faucet_cy, deck_z, deck_z + faucet * 0.28,
                             shaft * 0.6, shaft * 0.6, "metal"))
            strokes.append(circle(handle_cx, faucet_cy, shaft * 0.5, weight=DETAIL_WEIGHT))
        return tuple(strokes), tuple(parts)

    return build


def hydrant() -> Builder:
    """A wall hydrant: standpipe in plan, with its handle and the hose outlet off one side.

    Not a basin and not a faucet on a deck — the whole fixture is a vertical pipe whose only
    plan presence is its own diameter, so the glyph is a filled circle for the riser with the
    operating handle drawn as a bar across it and the outlet nipple projecting into the room
    (``-y``, the side away from the wall). That reads as a hydrant on a plan rather than as
    the anonymous rectangle a symbol-less type falls back to.

    In 3D it is the standpipe itself: the catalog height is the head height above the floor,
    and the massing stands the full height rather than sitting on a deck plane, because there
    is no deck.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        riser_r = clamp(min(width, depth) * 0.22, 0.02, min(width, depth) * 0.3)
        handle_len = clamp(width * 0.9, riser_r * 2, width)
        # Strokes are height-independent by contract, so nothing the plan glyph uses may
        # depend on `height` — only the 3D parts below clamp against it.
        handle_t = clamp(riser_r * 0.5, 0.008, riser_r)
        outlet_t = clamp(riser_r * 0.8, 0.012, riser_r * 1.2)
        # The outlet reaches from the riser into the room and the vacuum breaker screws onto
        # its tip, so the *breaker* is what has to land on the footprint edge — everything is
        # measured back from there. A non-square type (the escutcheon is square, but the
        # symbol has to hold for any size) would otherwise push the nipple out of the box.
        breaker_r = clamp(outlet_t * 0.8, 0.006, min(outlet_t, depth * 0.12))
        outlet_far = depth / 2.0 - breaker_r
        outlet_near = riser_r * 0.4
        outlet_len = max(outlet_far - outlet_near, 0.0)
        outlet_cy = -(outlet_near + outlet_len / 2.0)
        strokes = [circle(0, 0, riser_r, fill="metal"),
                   rect(0, 0, handle_len, handle_t, fill="metal")]
        if outlet_len > 0:
            strokes.append(rect(0, outlet_cy, outlet_t, outlet_len, fill="metal"))
            strokes.append(circle(0, -outlet_far, breaker_r, weight=DETAIL_WEIGHT))
        # 3D massing, Woodford-W34-style pieces in the box-only vocabulary: an escutcheon
        # flange at the floor, a slim standpipe, a wider head casting at the top, the
        # lever handle above the head, and the outlet nipple capped by its hose-bib
        # vacuum breaker. Round sections are honest squares — the parts vocabulary has
        # no cylinder — but the proportions are the fixture's, which is what makes it
        # read as a hydrant instead of as three anonymous blocks.
        head_h = clamp(height * 0.14, riser_r * 2, height * 0.2)
        head_w = riser_r * 3.2
        head_z0 = height - head_h
        handle_h = min(handle_t, height * 0.06)
        pipe_w = riser_r * 1.6  # the galvanized standpipe, slimmer than the head casting
        flange_w = min(riser_r * 4.0, min(width, depth) * 0.96)
        flange_h = min(0.012, height * 0.02)
        outlet_z1 = head_z0  # the nipple leaves the casting's underside
        outlet_z0 = max(outlet_z1 - outlet_t, 0.0)
        parts = [
            box(0, 0, 0.0, flange_h, flange_w, flange_w, "metal"),  # escutcheon
            box(0, 0, flange_h, head_z0, pipe_w, pipe_w, "metal"),  # standpipe
            box(0, 0, head_z0, height, head_w, head_w, "metal"),  # head casting
            # Lever handle: the bar across the head top.
            box(0, 0, height - handle_h, height, handle_len, handle_t, "metal"),
        ]
        if outlet_len > 0:
            parts.append(box(0, outlet_cy, outlet_z0, outlet_z1,
                             outlet_t, outlet_len, "metal"))
            # Hose-bib vacuum breaker: the fatter cap screwed onto the nipple's tip.
            parts.append(box(0, -outlet_far, outlet_z0 - breaker_r * 0.5,
                             min(outlet_z1 + breaker_r * 0.5, height),
                             breaker_r * 2.0, breaker_r * 2.0, "metal"))
        return tuple(strokes), tuple(parts)

    return build


PLUMBING_SYMBOLS: dict[str, Builder] = {
    "hydrant": hydrant(),
    "toilet": toilet(),
    "lavatory": lavatory(pedestal=True),
    "vanity": vanity(),
    "tub": tub(),
    "tub-shower": tub_shower(),
    "shower": shower(),
    "kitchen-sink": kitchen_sink(bowls=2),
}
