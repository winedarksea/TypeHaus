"""Generic folded double swing-arm light retained for library compatibility."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import (
    OUTLINE_WEIGHT,
    Part,
    Stroke,
    box,
    circle,
    line,
    prism,
    rect,
)

SIDES = 10


def _disc(cx: float, cy: float, r: float, z0: float, z1: float, color: str) -> Part:
    return prism(circle(cx, cy, r, segments=SIDES)["points"], z0, z1, color)


def _plate(width: float, depth: float, share: float = 0.2) -> tuple[float, float]:
    plate_d = min(depth * share, 0.0254)
    return plate_d, depth / 2 - plate_d / 2


def swing_arm_sconce() -> Builder:
    """A double swing-arm reading light (WAC Stretch), drawn folded back along the wall.

    Plate at the centre, first arm out to +x, second arm back to -x further off the wall,
    and the head at the -x end aiming down.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        plate_d, plate_cy = _plate(width, depth)
        arm_t = depth * 0.08
        arm_h = min(arm_t, height * 0.1)
        head_r = min(width * 0.12, (depth - plate_d) * 0.4)
        # Arm centrelines: the first touches the plate face, the head sits at the front.
        y1 = plate_cy - plate_d / 2 - arm_t / 2
        y2 = -depth / 2 + head_r
        arm_z = height * 0.55
        head_x = -width / 2 + head_r
        strokes: list[Stroke] = [
            rect(0, plate_cy, width * 0.18, plate_d, fill="luminaire-housing"),
            line((0, y1), (width / 2 - arm_t, y1), weight=OUTLINE_WEIGHT),
            line((width / 2 - arm_t, y1), (head_x, y2), weight=OUTLINE_WEIGHT),
            circle(head_x, y2, head_r, segments=SIDES, fill="lamp"),
        ]
        parts = [
            box(0, plate_cy, height * 0.25, height * 0.85, width * 0.18, plate_d,
                "luminaire-housing"),
            box(width / 4, y1, arm_z, arm_z + arm_h, width / 2, arm_t, "luminaire-housing"),
            box(width / 2 - arm_t / 2, (y1 + y2) / 2, arm_z, arm_z + arm_h, arm_t, y1 - y2,
                "luminaire-housing"),
            box((width / 2 + head_x) / 2, y2, arm_z, arm_z + arm_h, width / 2 - head_x, arm_t,
                "luminaire-housing"),
            _disc(head_x, y2, head_r, arm_z - height * 0.25, arm_z + arm_h,
                  "luminaire-housing"),
            _disc(head_x, y2, head_r * 0.75, arm_z - height * 0.27, arm_z - height * 0.25,
                  "lamp"),
        ]
        return tuple(strokes), tuple(parts)

    return build
