"""Wall luminaires shaped after named products: tube, slim up/down, swing arm, candle.

Coarse on purpose: each is a handful of boxes and 10-sided prisms that reads as the
product's silhouette, not its every curve. Wall side is ``+y``; light throws toward ``-y``.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    OUTLINE_WEIGHT,
    Part,
    Stroke,
    box,
    circle,
    depth_cylinder,
    line,
    prism,
    rect,
)

# Low-poly rounds: enough sides to read as round, few enough to stay cheap.
SIDES = 10


def _disc(cx: float, cy: float, r: float, z0: float, z1: float, color: str) -> Part:
    return prism(circle(cx, cy, r, segments=SIDES)["points"], z0, z1, color)


def _plate(width: float, depth: float, share: float = 0.2) -> tuple[float, float]:
    """(thickness, centre y) of the plate screwed to the wall."""
    plate_d = min(depth * share, 0.0254)
    return plate_d, depth / 2 - plate_d / 2


def tube_sconce() -> Builder:
    """An outdoor cylinder (WAC Tube): a vertical tube held off a small plate, lens below."""

    def build(width: float, depth: float, height: float) -> Geometry:
        plate_d, plate_cy = _plate(width, depth)
        r = min(width / 2, (depth - plate_d) / 2)
        cy = depth / 2 - plate_d - r
        lens = height * 0.08
        strokes: list[Stroke] = [rect(0, plate_cy, width * 0.6, plate_d, fill="luminaire-housing"),
                                 circle(0, cy, r, segments=SIDES, fill="luminaire-housing"),
                                 circle(0, cy, r * 0.7, segments=SIDES, fill="lamp",
                                        weight=DETAIL_WEIGHT)]
        # Wall to room: plate, arm, tube, lens.
        parts = [box(0, plate_cy, height * 0.15, height * 0.85, width * 0.6, plate_d,
                     "luminaire-housing"),
                 depth_cylinder(0, (plate_cy + cy) / 2, height * 0.6, r * 0.3,
                                abs(plate_cy - cy), "luminaire-housing"),
                 _disc(0, cy, r, lens, height, "luminaire-housing"),
                 _disc(0, cy, r * 0.8, 0.0, lens, "lamp")]
        return tuple(strokes), tuple(parts)

    return build


def slim_updown_sconce() -> Builder:
    """A tall narrow up/down body (WAC Roland): lit slots at the top and bottom faces."""

    def build(width: float, depth: float, height: float) -> Geometry:
        lens = min(height * 0.04, 0.0127)
        strokes: list[Stroke] = [rect(0, 0, width, depth, fill="luminaire-housing"),
                                 line((-width * 0.3, depth * 0.2), (0, -depth * 0.3)),
                                 line((width * 0.3, depth * 0.2), (0, -depth * 0.3))]
        parts = [box(0, 0, lens, height - lens, width, depth, "luminaire-housing"),
                 box(0, 0, 0.0, lens, width * 0.85, depth * 0.7, "lamp"),
                 box(0, 0, height - lens, height, width * 0.85, depth * 0.7, "lamp")]
        return tuple(strokes), tuple(parts)

    return build


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
        y1 = plate_cy - plate_d / 2 - arm_t
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


def candle_sconce() -> Builder:
    """A plain one-light candle sconce (Livex 4451): tall plate, arm, cup, sleeve, bulb."""

    def build(width: float, depth: float, height: float) -> Geometry:
        plate_d, plate_cy = _plate(width, depth)
        cup_r = min(width * 0.4, (depth - plate_d) / 2)
        cup_y = -depth / 2 + cup_r
        arm_z = height * 0.2
        arm_r = min(width * 0.05, arm_z)
        cup_top = arm_z + height * 0.12
        sleeve_top = cup_top + height * 0.35
        strokes: list[Stroke] = [
            rect(0, plate_cy, width, plate_d, fill="luminaire-housing"),
            line((0, plate_cy - plate_d / 2), (0, cup_y), weight=OUTLINE_WEIGHT),
            circle(0, cup_y, cup_r, segments=SIDES, fill="luminaire-housing"),
            circle(0, cup_y, cup_r * 0.4, segments=SIDES, fill="lamp", weight=DETAIL_WEIGHT),
        ]
        parts = [
            box(0, plate_cy, 0.0, height * 0.7, width, plate_d, "luminaire-housing"),
            depth_cylinder(0, (plate_cy + cup_y) / 2, arm_z, arm_r, plate_cy - cup_y,
                           "luminaire-housing"),
            _disc(0, cup_y, cup_r, arm_z, cup_top, "luminaire-housing"),
            _disc(0, cup_y, cup_r * 0.45, cup_top, sleeve_top, "cabinet-cream"),
            _disc(0, cup_y, cup_r * 0.35, sleeve_top, min(height, sleeve_top + height * 0.15),
                  "lamp"),
        ]
        return tuple(strokes), tuple(parts)

    return build
