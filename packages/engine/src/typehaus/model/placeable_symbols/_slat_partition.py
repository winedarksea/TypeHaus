"""A floor-to-ceiling slat screen: vertical slats on a fixed pitch between two cleats.

Width runs along the screen, depth is the slat's depth through it. Slats sit on one pitch
with a half gap at each end, so two screens whose widths are whole pitches abut with the
rhythm unbroken across the joint.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, rect

SLAT_FACE_M = 1.5 * 0.0254
SLAT_PITCH_M = 2.75 * 0.0254
CLEAT_HEIGHT_M = 0.75 * 0.0254


def slat_count(width: float) -> int:
    """Whole pitches that fit the width; at least one slat."""
    return max(1, int(width / SLAT_PITCH_M + 1e-6))


def slat_partition(width: float, depth: float, height: float) -> Geometry:
    """Slats centred on the width, with a floor and a ceiling cleat the full run."""
    count = slat_count(width)
    face = min(SLAT_FACE_M, width / count)
    first = -(count - 1) * SLAT_PITCH_M / 2
    cleat = min(CLEAT_HEIGHT_M, height / 4)
    strokes = [rect(0, 0, width, depth)]
    parts = [box(0, 0, 0, cleat, width, depth, "wood"),
             box(0, 0, height - cleat, height, width, depth, "wood")]
    for index in range(count):
        x = first + index * SLAT_PITCH_M
        strokes.append(rect(x, 0, face, depth, fill="wood"))
        parts.append(box(x, 0, cleat, height - cleat, face, depth, "wood"))
    return tuple(strokes), tuple(parts)
