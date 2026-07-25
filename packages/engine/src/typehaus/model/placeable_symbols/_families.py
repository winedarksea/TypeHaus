"""Parametric glyph families — the builders furniture.py and appliances.py compose from.

Families, not bespoke functions per catalog entry: a loveseat is a sofa with two seats, a
nightstand is a dresser with one drawer row, and a dryer is a washer with a different door.
Each family returns *both* the drawn strokes and the 3D massing parts from one body, so the
arms you see in plan are the arms you see in the viewer.

Every dimension is expressed as a fraction of the type's own W/D/H, clamped by an absolute
limit where the real object has one (an arm is ~5" whatever the sofa's length). Symbols
therefore stay legible from a 22" end table to a 110" sectional without per-size tuning.

Nothing here leaves the W×D×H box: the footprint is the clearance and collision contract, so
a drawn handle stops at the front face rather than protruding through it.
"""

from __future__ import annotations

import math
from typing import Callable, Tuple

from typehaus.model.placeable_symbols._frame import (DETAIL_WEIGHT, Part, Point, Stroke, arc,
                                                     box, circle, clamp, line, polygon, rect)

Geometry = Tuple[Tuple[Stroke, ...], Tuple[Part, ...]]
Builder = Callable[[float, float, float], Geometry]

# Seat height is the one anthropometric constant every seat family shares (17"-19" for lounge
# and dining alike); everything else scales with the object.
SEAT_HEIGHT_M = 0.45
CUSHION_THICKNESS_M = 0.12
ARM_WIDTH_M = 0.14
BACK_DEPTH_M = 0.20
TOP_THICKNESS_M = 0.04
DRAWER_FACE_DEPTH_M = 0.03
# Depth a pull/handle occupies at the front plane, and how far the door face sits behind it.
HANDLE_DEPTH_M = 0.02


def seating(*, arms: bool = True, seats: int = 3, back_depth_m: float = BACK_DEPTH_M) -> Builder:
    """Sofas, loveseats, armchairs and dining chairs: back band, optional arms, seat cushions."""

    def build(width: float, depth: float, height: float) -> Geometry:
        back_d = clamp(back_depth_m, 0.06, depth * 0.35)
        arm_w = clamp(ARM_WIDTH_M, 0.05, width * 0.22) if arms else 0.0
        seat_top = min(SEAT_HEIGHT_M, height * 0.55)
        cushion_t = min(CUSHION_THICKNESS_M, seat_top * 0.35)
        inner_w = width - 2 * arm_w
        inner_d = depth - back_d
        back_cy = depth / 2 - back_d / 2
        seat_cy = -depth / 2 + inner_d / 2

        strokes = [rect(0, 0, width, depth, fill="upholstery"),
                   rect(0, back_cy, width, back_d, fill="cushion")]
        parts = [box(0, back_cy, 0.0, height, width, back_d, "upholstery"),
                 box(0, seat_cy, 0.0, seat_top - cushion_t, inner_w, inner_d, "upholstery")]
        for sign in (-1, 1):
            if not arms:
                break
            arm_cx = sign * (width / 2 - arm_w / 2)
            strokes.append(rect(arm_cx, 0, arm_w, depth, fill="cushion"))
            parts.append(box(arm_cx, 0, 0.0, min(height * 0.72, seat_top + 0.22),
                             arm_w, depth, "upholstery"))
        seat_w = inner_w / max(1, seats)
        for index in range(max(1, seats)):
            seat_cx = -inner_w / 2 + seat_w * (index + 0.5)
            strokes.append(rect(seat_cx, seat_cy, seat_w * 0.94, inner_d * 0.94,
                                fill="cushion", weight=DETAIL_WEIGHT))
            parts.append(box(seat_cx, seat_cy, seat_top - cushion_t, seat_top,
                             seat_w * 0.96, inner_d * 0.96, "cushion"))
        return tuple(strokes), tuple(parts)

    return build


# The L a sectional makes: a back run across the full width, plus a chaise returning forward
# on the +x end. Fractions of the overall 110"x85" reference (35" deep run, 35" wide chaise).
SECTIONAL_RUN_DEPTH_FRACTION = 0.41
SECTIONAL_CHAISE_WIDTH_FRACTION = 0.32


def sectional_points(width: float, depth: float,
                     run_depth_fraction: float = SECTIONAL_RUN_DEPTH_FRACTION,
                     chaise_width_fraction: float = SECTIONAL_CHAISE_WIDTH_FRACTION,
                     ) -> Tuple[Point, ...]:
    """The L outline shared by the sectional glyph and its catalog ``footprint_shape``.

    Exported so the drawn symbol and the resolver's collision footprint cannot drift.
    """
    run_d = depth * run_depth_fraction
    chaise_w = width * chaise_width_fraction
    return ((width / 2 - chaise_w, -depth / 2), (width / 2, -depth / 2),
            (width / 2, depth / 2), (-width / 2, depth / 2),
            (-width / 2, depth / 2 - run_d), (width / 2 - chaise_w, depth / 2 - run_d))


def sectional(*, run_depth_fraction: float = SECTIONAL_RUN_DEPTH_FRACTION,
              chaise_width_fraction: float = SECTIONAL_CHAISE_WIDTH_FRACTION) -> Builder:
    """An L-shaped sectional: a back run plus a chaise returning along one end."""

    def build(width: float, depth: float, height: float) -> Geometry:
        run_d = depth * run_depth_fraction
        chaise_w = width * chaise_width_fraction
        back_t = clamp(BACK_DEPTH_M, 0.06, min(run_d, chaise_w) * 0.35)
        seat_top = min(SEAT_HEIGHT_M, height * 0.55)
        cushion_t = min(CUSHION_THICKNESS_M, seat_top * 0.35)

        strokes = [polygon(sectional_points(width, depth, run_depth_fraction,
                                            chaise_width_fraction), fill="upholstery"),
                   rect(0, depth / 2 - back_t / 2, width, back_t, fill="cushion"),
                   rect(width / 2 - back_t / 2, 0, back_t, depth, fill="cushion")]
        parts = [box(0, depth / 2 - back_t / 2, 0.0, height, width, back_t, "upholstery"),
                 box(width / 2 - back_t / 2, 0, 0.0, height, back_t, depth, "upholstery")]
        # Two seat runs: the back run (west of the chaise) and the chaise itself.
        for cx, cy, run_w, seat_d, seats in (
            (-chaise_w / 2, depth / 2 - back_t - (run_d - back_t) / 2,
             width - chaise_w, run_d - back_t, 2),
            (width / 2 - back_t - (chaise_w - back_t) / 2, -back_t / 2,
             chaise_w - back_t, depth - back_t, 1),
        ):
            parts.append(box(cx, cy, 0.0, seat_top - cushion_t, run_w, seat_d, "upholstery"))
            for index in range(seats):
                cell = run_w / seats
                seat_cx = cx - run_w / 2 + cell * (index + 0.5)
                strokes.append(rect(seat_cx, cy, cell * 0.92, seat_d * 0.92,
                                    fill="cushion", weight=DETAIL_WEIGHT))
                parts.append(box(seat_cx, cy, seat_top - cushion_t, seat_top,
                                 cell * 0.94, seat_d * 0.94, "cushion"))
        return tuple(strokes), tuple(parts)

    return build


def pedestal_seat() -> Builder:
    """An office chair: a seat disc over a five-star caster base, with a back arc."""

    def build(width: float, depth: float, height: float) -> Geometry:
        base_r = min(width, depth) / 2
        seat_r = base_r * 0.62
        seat_cy = -depth * 0.05
        seat_top = min(SEAT_HEIGHT_M, height * 0.5)
        strokes = [circle(0, 0, base_r, weight=DETAIL_WEIGHT),
                   circle(0, seat_cy, seat_r, fill="upholstery")]
        for index in range(5):  # the five-star base, drawn as spokes out to the caster ring
            radians = math.radians(90 + index * 72)
            strokes.append(line((0, 0), (base_r * math.cos(radians),
                                         base_r * math.sin(radians))))
        strokes.append(arc(0, seat_cy, seat_r * 1.05, 200, 340))
        back_d = depth * 0.12
        base_h = min(0.04, height * 0.1)
        seat_t = min(0.07, seat_top * 0.3)
        parts = [box(0, 0, 0.0, base_h, base_r * 1.9, base_r * 1.9, "metal"),
                 box(0, 0, base_h, seat_top - seat_t, base_r * 0.22, base_r * 0.22, "metal"),
                 box(0, seat_cy, seat_top - seat_t, seat_top, seat_r * 1.9, seat_r * 1.9,
                     "cushion"),
                 box(0, depth / 2 - back_d / 2, seat_top, height, seat_r * 1.7, back_d,
                     "upholstery")]
        return tuple(strokes), tuple(parts)

    return build


def slab(*, leg_inset_m: float = 0.06, apron: bool = True,
         modesty_panel: bool = False) -> Builder:
    """Rectangular tables and desks: a top, an optional apron, four corner legs."""

    def build(width: float, depth: float, height: float) -> Geometry:
        inset = clamp(leg_inset_m, 0.02, min(width, depth) * 0.18)
        leg = clamp(min(width, depth) * 0.09, 0.04, 0.09)
        top_t = min(TOP_THICKNESS_M, height * 0.12)
        strokes = [rect(0, 0, width, depth, fill="wood")]
        parts = [box(0, 0, height - top_t, height, width, depth, "wood")]
        if apron:
            strokes.append(rect(0, 0, width - 2 * inset, depth - 2 * inset,
                                weight=DETAIL_WEIGHT))
            parts.append(box(0, 0, height - top_t - min(0.10, height * 0.14), height - top_t,
                             width - 2 * inset, depth - 2 * inset, "wood-dark"))
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx = sx * (width / 2 - inset - leg / 2)
                cy = sy * (depth / 2 - inset - leg / 2)
                strokes.append(rect(cx, cy, leg, leg, fill="wood-dark", weight=DETAIL_WEIGHT))
                parts.append(box(cx, cy, 0.0, height - top_t, leg, leg, "wood-dark"))
        if modesty_panel:  # a desk reads as a desk because its back is closed
            parts.append(box(0, depth / 2 - inset, height * 0.35, height - top_t,
                             width - 2 * inset, 0.02, "wood-dark"))
        return tuple(strokes), tuple(parts)

    return build


def round_slab(*, pedestal: bool = True) -> Builder:
    """A round table: a circular top over a central pedestal (or four legs)."""

    def build(width: float, depth: float, height: float) -> Geometry:
        radius = min(width, depth) / 2
        top_t = min(TOP_THICKNESS_M, height * 0.12)
        strokes = [circle(0, 0, radius, fill="wood"),
                   circle(0, 0, radius * 0.28, weight=DETAIL_WEIGHT)]
        parts = [box(0, 0, height - top_t, height, radius * 2, radius * 2, "wood")]
        if pedestal:
            base_h = min(0.04, height * 0.1)
            parts.append(box(0, 0, base_h, height - top_t, radius * 0.34, radius * 0.34,
                             "wood-dark"))
            parts.append(box(0, 0, 0.0, base_h, radius * 1.1, radius * 1.1, "wood-dark"))
        else:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    parts.append(box(sx * radius * 0.62, sy * radius * 0.62, 0.0,
                                     height - top_t, 0.07, 0.07, "wood-dark"))
        return tuple(strokes), tuple(parts)

    return build


def case(*, rows: int = 3, cols: int = 1, pulls: bool = True, color: str = "wood") -> Builder:
    """Casegoods — dressers, chests, nightstands, media consoles.

    Plan view of a case piece is its top; the drawer grid is drawn as the front-face band so
    the reader can tell which way the piece opens, which is the whole point of the symbol.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        face_d = clamp(DRAWER_FACE_DEPTH_M, 0.015, depth * 0.2)
        front = -depth / 2
        face_cy = front + HANDLE_DEPTH_M + face_d / 2
        strokes = [rect(0, 0, width, depth, fill=color),
                   rect(0, front + (HANDLE_DEPTH_M + face_d) / 2, width,
                        HANDLE_DEPTH_M + face_d, fill="wood-dark", weight=DETAIL_WEIGHT)]
        carcass_d = depth - HANDLE_DEPTH_M - face_d
        top_t = min(0.02, height * 0.06)
        parts = [box(0, front + HANDLE_DEPTH_M + face_d + carcass_d / 2, 0.0, height - top_t,
                     width, carcass_d, color),
                 box(0, 0, height - top_t, height, width, depth, color)]
        cell_w = width / max(1, cols)
        cell_h = height * 0.94 / max(1, rows)
        for col in range(max(1, cols)):
            cx = -width / 2 + cell_w * (col + 0.5)
            if col:
                strokes.append(line((cx - cell_w / 2, front), (cx - cell_w / 2, depth / 2)))
            for row in range(max(1, rows)):
                cz = height * 0.03 + cell_h * (row + 0.5)
                parts.append(box(cx, face_cy, cz - cell_h * 0.46, cz + cell_h * 0.46,
                                 cell_w * 0.96, face_d, "wood-dark"))
                if not pulls:
                    continue
                pull_h = min(0.012, cell_h * 0.2)
                parts.append(box(cx, front + HANDLE_DEPTH_M / 2, cz - pull_h, cz + pull_h,
                                 cell_w * 0.36, HANDLE_DEPTH_M, "metal"))
                if row == 0:  # one drawn pull is enough to declare the front in plan
                    strokes.append(line((cx - cell_w * 0.18, front + HANDLE_DEPTH_M / 2),
                                        (cx + cell_w * 0.18, front + HANDLE_DEPTH_M / 2)))
        return tuple(strokes), tuple(parts)

    return build


def shelving(*, shelves: int = 5) -> Builder:
    """A bookcase: two side panels, a back, and evenly spaced shelves."""

    def build(width: float, depth: float, height: float) -> Geometry:
        panel = min(clamp(depth * 0.12, 0.015, 0.03), depth * 0.3, width * 0.3,
                    height * 0.3)
        strokes = [rect(0, 0, width, depth, fill="wood"),
                   rect(0, 0, width - 2 * panel, depth - 2 * panel, weight=DETAIL_WEIGHT)]
        parts = [box(0, depth / 2 - panel / 2, 0.0, height, width, panel, "wood-dark")]
        for sign in (-1, 1):
            parts.append(box(sign * (width / 2 - panel / 2), 0, 0.0, height, panel, depth,
                             "wood"))
        count = max(2, shelves)
        for index in range(count):
            cz = clamp(height * index / (count - 1), panel / 2, height - panel / 2)
            parts.append(box(0, 0, cz - panel / 2, cz + panel / 2, width - 2 * panel, depth,
                             "wood"))
        strokes.append(line((-width / 2 + panel, 0), (width / 2 - panel, 0)))
        return tuple(strokes), tuple(parts)

    return build


def bed(*, pillows: int = 2, headboard: bool = True) -> Builder:
    """A bed drawn the way plans draw one: mattress, turned-down sheet, pillows at the head.

    The head is at ``+y`` (the object's back), so a bed rotated to face into the room reads
    correctly without any per-instance flag.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        board_d = clamp(0.08, 0.03, depth * 0.08) if headboard else 0.0
        mattress_w = width * 0.94
        mattress_d = depth - board_d
        mattress_cy = -depth / 2 + mattress_d / 2
        mattress_top = min(0.62, height * 0.62)
        pillow_d = mattress_d * 0.16
        pillow_cy = mattress_cy + mattress_d / 2 - pillow_d / 2 - mattress_d * 0.03

        strokes = [rect(0, 0, width, depth, fill="wood"),
                   rect(0, mattress_cy, mattress_w, mattress_d, fill="mattress")]
        slab_t = min(0.22, mattress_top * 0.4)
        parts = [box(0, mattress_cy, 0.0, mattress_top - slab_t, mattress_w, mattress_d,
                     "wood"),
                 box(0, mattress_cy, mattress_top - slab_t, mattress_top, mattress_w,
                     mattress_d, "mattress")]
        if headboard:
            strokes.append(rect(0, depth / 2 - board_d / 2, width, board_d, fill="wood-dark"))
            parts.append(box(0, depth / 2 - board_d / 2, 0.0, height, width, board_d,
                             "wood-dark"))
        slot = mattress_w / max(1, pillows)
        for index in range(max(0, pillows)):
            cx = -mattress_w / 2 + slot * (index + 0.5)
            strokes.append(rect(cx, pillow_cy, slot * 0.86, pillow_d, fill="pillow",
                                weight=DETAIL_WEIGHT))
            parts.append(box(cx, pillow_cy, mattress_top,
                             min(height, mattress_top + max(0.01, height * 0.1)),
                             slot * 0.86, pillow_d, "pillow"))
        # The turned-down sheet: the line that makes a rectangle read as a bed.
        fold_y = mattress_cy + mattress_d * 0.16
        strokes.append(line((-mattress_w / 2, fold_y), (mattress_w / 2, fold_y)))
        return tuple(strokes), tuple(parts)

    return build


def screen(*, stand: bool = True) -> Builder:
    """A television: a thin panel on a stand, drawn as its footprint plus the screen line."""

    def build(width: float, depth: float, height: float) -> Geometry:
        panel_t = clamp(depth * 0.16, 0.02, 0.06)
        panel_cy = depth / 2 - panel_t / 2
        base_h = min(0.05, height * 0.08)
        strokes = [rect(0, 0, width, depth, weight=DETAIL_WEIGHT),
                   rect(0, panel_cy, width, panel_t, fill="screen")]
        parts = [box(0, panel_cy, height * 0.32, height, width, panel_t, "screen")]
        if stand:
            strokes.append(rect(0, 0, width * 0.3, depth * 0.8, fill="wood-dark",
                                weight=DETAIL_WEIGHT))
            parts.append(box(0, 0, 0.0, base_h, width * 0.34, depth * 0.9, "wood-dark"))
            parts.append(box(0, panel_cy, base_h, height * 0.32, width * 0.1, panel_t,
                             "metal"))
        return tuple(strokes), tuple(parts)

    return build


def appliance_case(*, doors: int = 1, split: str = "vertical", handle: bool = True,
                   body: str = "appliance-white", porthole: bool = False,
                   controls: bool = False) -> Builder:
    """The boxy white/steel goods: fridges, dishwashers, washers, dryers, microwaves.

    ``split`` picks how multiple doors divide the front face — ``"vertical"`` for a
    side-by-side refrigerator, ``"horizontal"`` for a freezer drawer under a fresh-food door.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        face_d = clamp(0.04, 0.015, depth * 0.14)
        front = -depth / 2
        face_cy = front + HANDLE_DEPTH_M + face_d / 2
        body_d = depth - HANDLE_DEPTH_M - face_d
        strokes = [rect(0, 0, width, depth, fill=body),
                   rect(0, front + (HANDLE_DEPTH_M + face_d) / 2, width,
                        HANDLE_DEPTH_M + face_d, weight=DETAIL_WEIGHT)]
        parts = [box(0, front + HANDLE_DEPTH_M + face_d + body_d / 2, 0.0, height, width,
                     body_d, body)]
        count = max(1, doors)
        control_h = min(0.09, height * 0.12) if controls else 0.0
        if controls:  # the console band a washer/dryer wears across its back top
            parts.append(box(0, depth / 2 - face_d, height - control_h, height, width,
                             face_d * 2, "appliance-steel"))
        for index in range(count):
            if split == "vertical":
                cell_w = width / count
                cx = -width / 2 + cell_w * (index + 0.5)
                z0, z1 = 0.0, height - control_h
            else:
                cell_w, cx = width, 0.0
                span = (height - control_h) / count
                z0, z1 = span * index, span * (index + 1)
            parts.append(box(cx, face_cy, z0 + 0.005, z1 - 0.005, cell_w * 0.98, face_d, body))
            if split == "vertical" and index:
                strokes.append(line((cx - cell_w / 2, front), (cx - cell_w / 2, depth / 2)))
            elif split == "horizontal" and index:
                strokes.append(line((-width / 2, front + HANDLE_DEPTH_M + face_d),
                                    (width / 2, front + HANDLE_DEPTH_M + face_d)))
            if not handle or porthole:
                continue
            handle_x = cx + (cell_w * 0.4 if count > 1 and index == 0 else -cell_w * 0.4)
            strokes.append(line((handle_x, front), (handle_x, front + HANDLE_DEPTH_M)))
            parts.append(box(handle_x, front + HANDLE_DEPTH_M / 2,
                             (z0 + z1) / 2 - (z1 - z0) * 0.3, (z0 + z1) / 2 + (z1 - z0) * 0.3,
                             0.03, HANDLE_DEPTH_M, "appliance-steel"))
        if porthole:  # front-loaders read by their door glass, not by a handle
            glass_r = min(width * 0.3, height * 0.4)
            drawn_r = min(width * 0.3, (depth - HANDLE_DEPTH_M) * 0.4)
            strokes.append(circle(0, front + HANDLE_DEPTH_M + drawn_r, drawn_r,
                                  weight=DETAIL_WEIGHT))
            parts.append(box(0, front + HANDLE_DEPTH_M / 2, height * 0.5 - glass_r,
                             height * 0.5 + glass_r, glass_r * 2, HANDLE_DEPTH_M, "glass"))
        return tuple(strokes), tuple(parts)

    return build


def counter_case(*, top_color: str = "counter", body: str = "wood",
                 toe_kick: bool = True) -> Builder:
    """A cabinet under a counter slab — the carcass a vanity or a sink base is built on."""

    def build(width: float, depth: float, height: float) -> Geometry:
        top_t = min(TOP_THICKNESS_M, height * 0.08)
        kick = min(0.09, height * 0.12) if toe_kick else 0.0
        strokes = [rect(0, 0, width, depth, fill=top_color)]
        parts = [box(0, 0, height - top_t, height, width, depth, top_color),
                 box(0, 0.01, kick, height - top_t, width, depth - 0.02, body)]
        if toe_kick:
            parts.append(box(0, 0.03, 0.0, kick, width * 0.98, depth - 0.06, "wood-dark"))
        return tuple(strokes), tuple(parts)

    return build
