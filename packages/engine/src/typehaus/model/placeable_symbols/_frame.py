"""Primitives every placeable glyph is composed from — geometry helpers and the colour roles.

Pure functions over floats. The local frame is the one contract each builder honours:

* origin at the footprint centre,
* ``+x`` along the object's width, ``+y`` along its depth *toward the object's back*,
* ``z = 0`` at the object's base.

Rotation and translation stay with the consumer (Canvas2D, the draw writers, Panel3D and the
glTF emitter each already own that math), so a symbol is authored once, at the origin.

Circles are polygonised here rather than downstream, so every consumer only ever handles
polylines — the drawing IR (``emit/draw/scene.py``) needs no new node type for an ovoid
toilet bowl or a round dining table.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

try:  # TypedDict moved out of typing_extensions in 3.8, but total=False support varies.
    from typing import TypedDict
except ImportError:  # pragma: no cover - 3.7 and older are unsupported anyway
    TypedDict = dict  # type: ignore[assignment,misc]

Point = Tuple[float, float]


class Stroke(TypedDict):
    """One drawn polyline of a plan symbol, in the local frame (metres)."""

    points: Tuple[Point, ...]
    closed: bool
    fill: Optional[str]  # a PART_COLORS role, or None for an unfilled line
    weight: float


class Part(TypedDict):
    """One axis-aligned massing box of a 3D symbol, in the local frame (metres)."""

    center: Tuple[float, float, float]
    size: Tuple[float, float, float]
    color: str  # a PART_COLORS role


# Linear RGBA, matching the convention ``emit/gltf/emitter._PALETTE`` already uses: the same
# numbers feed a glTF baseColorFactor and (via ``part_hex``) a three.js material, so viewer
# and export cannot disagree about what a cushion looks like.
PART_COLORS: dict[str, tuple[float, float, float, float]] = {
    "upholstery": (0.55, 0.56, 0.58, 1.0),
    "cushion": (0.68, 0.69, 0.70, 1.0),
    "wood": (0.70, 0.52, 0.33, 1.0),
    "wood-dark": (0.45, 0.32, 0.20, 1.0),
    "metal": (0.62, 0.64, 0.66, 1.0),
    "glass": (0.72, 0.82, 0.86, 0.55),
    "mattress": (0.93, 0.92, 0.89, 1.0),
    "pillow": (0.85, 0.86, 0.88, 1.0),
    "screen": (0.14, 0.15, 0.17, 1.0),
    "appliance-white": (0.94, 0.94, 0.93, 1.0),
    "appliance-steel": (0.76, 0.78, 0.80, 1.0),
    "porcelain": (0.97, 0.97, 0.96, 1.0),
    "counter": (0.52, 0.50, 0.48, 1.0),
    # Painted casework. Fitted kitchen millwork is finished, not stained: a warm off-white
    # against the grey counter and the stainless goods. The ``-dark`` shade is the same paint
    # in shadow — door faces and toe kicks — so a run reads as one colour with relief, the way
    # ``wood``/``wood-dark`` do for the stained casegoods.
    "cabinet-cream": (0.93, 0.90, 0.82, 1.0),
    "cabinet-cream-dark": (0.84, 0.80, 0.71, 1.0),
}

# Drawn-line weights. Plan symbols read as a hierarchy: the object outline is the heaviest
# line, interior divisions medium, and detail (seams, grout, burner rings) lightest.
OUTLINE_WEIGHT = 0.25
DETAIL_WEIGHT = 0.18

CIRCLE_SEGMENTS = 32


def clamp(value: float, low: float, high: float) -> float:
    """Hold a scaled dimension between an absolute floor and a share-of-the-object ceiling.

    The ceiling wins when the two cross: ``low`` is a legibility minimum, ``high`` is usually
    a fraction of the object itself, and a symbol that leaves its own footprint is worse than
    one drawn slightly too fine.
    """
    return min(high, max(low, value))


def rect(cx: float, cy: float, w: float, d: float, *,
         fill: Optional[str] = None, weight: float = OUTLINE_WEIGHT) -> Stroke:
    """A closed axis-aligned rectangle centred on ``(cx, cy)``."""
    hw, hd = w / 2.0, d / 2.0
    return {"points": ((cx - hw, cy - hd), (cx + hw, cy - hd),
                       (cx + hw, cy + hd), (cx - hw, cy + hd)),
            "closed": True, "fill": fill, "weight": weight}


def circle(cx: float, cy: float, r: float, *, segments: int = CIRCLE_SEGMENTS,
           fill: Optional[str] = None, weight: float = OUTLINE_WEIGHT) -> Stroke:
    """A closed polygonised circle — see the module note on why this is not an arc node."""
    return ellipse(cx, cy, r, r, segments=segments, fill=fill, weight=weight)


def ellipse(cx: float, cy: float, rx: float, ry: float, *, segments: int = CIRCLE_SEGMENTS,
            fill: Optional[str] = None, weight: float = OUTLINE_WEIGHT) -> Stroke:
    """A closed polygonised ellipse. Toilet bowls and tub basins are ovoid, not round."""
    points = tuple((cx + rx * math.cos(2 * math.pi * index / segments),
                    cy + ry * math.sin(2 * math.pi * index / segments))
                   for index in range(segments))
    return {"points": points, "closed": True, "fill": fill, "weight": weight}


def arc(cx: float, cy: float, r: float, start_degrees: float, end_degrees: float, *,
        segments: int = 16, weight: float = DETAIL_WEIGHT) -> Stroke:
    """An open polygonised arc — a chair back, a swept door edge."""
    start, end = math.radians(start_degrees), math.radians(end_degrees)
    points = tuple((cx + r * math.cos(start + (end - start) * index / segments),
                    cy + r * math.sin(start + (end - start) * index / segments))
                   for index in range(segments + 1))
    return {"points": points, "closed": False, "fill": None, "weight": weight}


def line(p0: Point, p1: Point, *, weight: float = DETAIL_WEIGHT) -> Stroke:
    """A single open segment."""
    return {"points": (p0, p1), "closed": False, "fill": None, "weight": weight}


def polygon(points: Sequence[Point], *, closed: bool = True,
            fill: Optional[str] = None, weight: float = OUTLINE_WEIGHT) -> Stroke:
    """An explicit point list, for the glyphs convention draws rather than parameterises."""
    return {"points": tuple((float(x), float(y)) for x, y in points),
            "closed": closed, "fill": fill, "weight": weight}


def box(cx: float, cy: float, z0: float, z1: float, w: float, d: float, color: str) -> Part:
    """One massing box, spanning ``z0``..``z1`` and centred on ``(cx, cy)`` in plan."""
    return {"center": (cx, cy, (z0 + z1) / 2.0), "size": (abs(w), abs(d), abs(z1 - z0)),
            "color": color}


def part_hex(role: str) -> str:
    """The ``#rrggbb`` a consumer without the linear palette (the browser) should draw."""
    red, green, blue, _ = PART_COLORS.get(role, PART_COLORS["wood"])
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(channel * 255)))
                                          for channel in (red, green, blue)))
