"""A wood desktop over matching drawer pedestals, with open central knee space."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import TOP_THICKNESS_M, Geometry, case, slab

DRAWER_PEDESTAL_WIDTH_FRACTION = 0.24
SUPPORT_INSET_FRACTION = 0.04

_DESKTOP = slab(apron=False, legs=False)
_DRAWER_PEDESTAL = case(rows=2, color="cabinet-cream", face_color="cabinet-cream-dark")


def drawer_desk(width: float, depth: float, height: float) -> Geometry:
    """Front is -y; two drawers on each side leave the centre open for knees."""
    desktop_strokes, desktop_parts = _DESKTOP(width, depth, height)
    pedestal_width = width * DRAWER_PEDESTAL_WIDTH_FRACTION
    inset = min(width, depth) * SUPPORT_INSET_FRACTION
    pedestal_depth = depth - 2 * inset
    pedestal_center_x = width / 2 - inset - pedestal_width / 2
    support_height = height - min(TOP_THICKNESS_M, height * 0.12)
    pedestal_strokes, pedestal_parts = _DRAWER_PEDESTAL(
        pedestal_width, pedestal_depth, support_height,
    )
    strokes = [*desktop_strokes]
    parts = [*desktop_parts]
    for sign in (-1, 1):
        for stroke in pedestal_strokes:
            strokes.append({**stroke, "points": tuple(
                (x + sign * pedestal_center_x, y) for x, y in stroke["points"]
            )})
        for part in pedestal_parts:
            x, y, z = part["center"]
            parts.append({**part, "center": (x + sign * pedestal_center_x, y, z)})
    return tuple(strokes), tuple(parts)
