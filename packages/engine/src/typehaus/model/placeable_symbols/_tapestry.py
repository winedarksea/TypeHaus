"""A wall-hung woven tapestry: a thin body plus a face sheet the viewer paints."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, rect

SHEET_M = 0.002


def wall_tapestry(width: float, depth: float, height: float) -> Geometry:
    """Back on the wall (+y); the room-facing sheet is the ``tapestry`` part at -y."""
    strokes = (rect(0, 0, width, depth, weight=DETAIL_WEIGHT),)
    parts = (
        box(0, SHEET_M / 2, 0.0, height, width, depth - SHEET_M, "wood-dark"),
        box(0, -depth / 2 + SHEET_M / 2, 0.0, height, width, SHEET_M, "tapestry"),
    )
    return strokes, parts
