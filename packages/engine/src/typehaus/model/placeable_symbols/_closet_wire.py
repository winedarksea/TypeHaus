"""Matching straight and corner wire shelves with separate rods beneath."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    Point,
    box,
    line,
    polygon,
    prism,
    rect,
)
from typehaus.model.placeable_symbols._wardrobe import wardrobe_corner_points

WIRE_SHELF_LEG_M = 0.3048  # 12" deep wire shelf
WIRE_PITCH_M = 0.0508  # 2", representative
WIRE_SHELF_THICKNESS_M = 0.009525  # 3/8"
WIRE_ROD_RADIUS_M = 0.0079375  # 5/8" round
CORNER_BAR_M = 0.26035  # ClosetMaid 56333, 10 1/4" x 10 1/4"
CORNER_BAR_SEGMENTS = 8



def closet_wire(width: float, depth: float, height: float) -> Geometry:
    """Match the corner's shelf top and rod centreline at a supported straight joint."""
    radius = min(WIRE_ROD_RADIUS_M, depth * 0.1)
    shelf_thickness = min(WIRE_SHELF_THICKNESS_M, height * 0.25)
    rod_height = min(2 * radius, height * 0.5)
    rod_y = -depth / 2 + radius
    wire_count = max(1, round(width / WIRE_PITCH_M))
    strokes = [rect(0, 0, width, depth, fill="metal")]
    strokes += [line((-width / 2 + width * i / wire_count, -depth / 2),
                     (-width / 2 + width * i / wire_count, depth / 2))
                for i in range(1, wire_count)]
    strokes.append(line((-width / 2, rod_y), (width / 2, rod_y), weight=DETAIL_WEIGHT))
    return tuple(strokes), (
        box(0, 0, height - shelf_thickness, height, width, depth, "metal"),
        box(0, rod_y, 0, rod_height, width, 2 * radius, "metal"),
    )


def closet_corner_wire(width: float, depth: float, height: float) -> Geometry:
    """Wire-shelf L in a closet corner: a leg along the back (+y), one returning down -x,
    each with its hang rod under the front edge. A corner bar rounds the rod past the
    inner corner, into the notch, so hangers slide from one leg to the other.

    Shelf on top of the body, rod at its bottom; the mount elevation is the rod line.
    """
    hw, hd = width / 2, depth / 2
    leg = min(WIRE_SHELF_LEG_M, width / 2, depth / 2)
    r = min(WIRE_ROD_RADIUS_M, leg * 0.1)
    # Rod centreline: a rod radius inside the L's inner edge.
    cx, cy = -hw + leg - r, hd - leg + r
    bend = min(CORNER_BAR_M, 0.9 * (hw - cx), 0.9 * (cy + hd))
    centre = (cx + bend, cy - bend)

    def on_arc(radius: float, index: int) -> Point:
        angle = math.pi / 2 + (math.pi / 2) * index / CORNER_BAR_SEGMENTS
        return (centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle))

    rod_path = ((hw, cy), *(on_arc(bend, i) for i in range(CORNER_BAR_SEGMENTS + 1)),
                (cx, -hd))
    strokes = [polygon(wardrobe_corner_points(width, depth, leg), fill="metal")]
    for count, span, draw in (
            (round(width / WIRE_PITCH_M), width,
             lambda t: line((-hw + t, hd - leg), (-hw + t, hd))),
            (round((depth - leg) / WIRE_PITCH_M), depth - leg,
             lambda t: line((-hw, -hd + t), (-hw + leg, -hd + t)))):
        strokes += [draw(span * i / count) for i in range(1, count)]
    strokes.append(polygon(rod_path, closed=False, weight=DETAIL_WEIGHT))

    shelf = min(WIRE_SHELF_THICKNESS_M, height * 0.25)
    rod_z = min(2 * r, height * 0.5)
    parts = [box(0, hd - leg / 2, height - shelf, height, width, leg, "metal"),
             box(-hw + leg / 2, -leg / 2, height - shelf, height, leg, depth - leg, "metal"),
             box((cx + bend + hw) / 2, cy, 0, rod_z, hw - cx - bend, 2 * r, "metal"),
             box(cx, (cy - bend - hd) / 2, 0, rod_z, 2 * r, cy - bend + hd, "metal")]
    parts += [prism((on_arc(bend - r, i), on_arc(bend + r, i),
                     on_arc(bend + r, i + 1), on_arc(bend - r, i + 1)), 0, rod_z, "metal")
              for i in range(CORNER_BAR_SEGMENTS)]
    return tuple(strokes), tuple(parts)

