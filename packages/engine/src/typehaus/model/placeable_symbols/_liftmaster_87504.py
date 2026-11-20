"""LiftMaster 87504-267 Secure View opener with the 7-foot belt rail."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry, _rounded_rectangle_points
from typehaus.model.placeable_symbols._frame import Part, box, circle, polygon, prism
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._sektion_fronts import round_bar
from typehaus.quantities import inch

# LiftMaster product guide dimensions. The rail projects from the +y side of the head.
HEAD_DEPTH = inch(10.5).meters
INSTALLED_LENGTH = inch(124).meters
# Catlin's suspended installation, measured from the bottom of the camera.
CEILING_DROP = inch(33.375).meters
_RAIL_FLANGE_WIDTH = inch(1.75).meters
_RAIL_HEIGHT = inch(1.5).meters
_STEEL_THICKNESS = inch(0.125).meters


def _rounded_shell(sections: tuple[tuple[float, float, float, float], ...],
                   color: str) -> Part:
    """Loft the molded shell or diffuser between rounded rectangular sections."""
    rings = [_rounded_rectangle_points(width, depth, radius)
             for _, width, depth, radius in sections]
    count = len(rings[0])
    vertices = [(x, y, z) for (z, _, _, _), ring in zip(sections, rings, strict=True)
                for x, y in ring]
    triangles = []
    for base in range(0, len(vertices) - count, count):
        for index in range(count):
            first, second = base + index, base + (index + 1) % count
            triangles.extend(((first, second, second + count),
                              (first, second + count, first + count)))
    top = len(vertices) - count
    for index in range(1, count - 1):
        triangles.extend(((0, index + 1, index), (top, top + index, top + index + 1)))
    return mesh_part(vertices, outward(vertices, triangles), color)


def _head(width: float, depth: float, height: float) -> tuple[Part, ...]:
    radius = depth * 0.16
    camera_y = depth * 0.11
    camera_bezel_radius = min(depth * 0.063, height * 0.095)
    return (
        _rounded_shell((
            (height * 0.38, width * 0.91, depth * 0.90, radius),
            (height * 0.48, width * 0.97, depth * 0.96, radius),
            (height * 0.91, width * 0.94, depth * 0.94, radius),
            (height * 0.97, width * 0.85, depth * 0.84, radius),
        ), "eg4-charcoal"),
        _rounded_shell((
            (height * 0.24, width * 0.88, depth * 0.84, radius),
            (height * 0.30, width, depth, radius),
            (height * 0.40, width, depth, radius),
            (height * 0.44, width * 0.97, depth * 0.97, radius),
        ), "plastic-white"),
        # The darker underside stands proud of the diffuser, exposing the white perimeter.
        prism(_rounded_rectangle_points(width * 0.72, depth * 0.61, radius * 0.8),
              height * 0.20, height * 0.26, "driver-black"),
        prism(circle(0, camera_y, depth * 0.115)["points"], 0, height * 0.23, "metal-black"),
        round_bar((0, camera_y + depth * 0.088, height * 0.10),
                  (0, camera_y + depth * 0.128, height * 0.10),
                  camera_bezel_radius, "driver-black"),
        round_bar((0, camera_y + depth * 0.123, height * 0.10),
                  (0, camera_y + depth * 0.135, height * 0.10),
                  camera_bezel_radius * 0.62, "screen"),
        box(0, 0, height * 0.94, height, width * 0.58, depth * 0.73, "metal-black"),
    )


def _installation(width: float, depth: float, height: float) -> tuple[Part, ...]:
    header_y = INSTALLED_LENGTH - HEAD_DEPTH / 2
    bracket_depth = inch(1.25).meters
    rail_start = -depth * 0.09
    rail_end = header_y - bracket_depth / 2
    rail_y = (rail_start + rail_end) / 2
    rail_length = rail_end - rail_start
    rail_top = height + _RAIL_HEIGHT
    trolley_y = rail_end - inch(10).meters
    trolley_bottom = height - inch(0.65).meters
    handle_top = trolley_bottom - inch(12).meters
    strap_width = inch(1.25).meters
    strap_y = -depth * 0.19
    return (
        box(0, rail_y, height, height + _STEEL_THICKNESS,
            _RAIL_FLANGE_WIDTH, rail_length, "metal-black"),
        box(0, rail_y, height + _STEEL_THICKNESS, rail_top,
            _STEEL_THICKNESS, rail_length, "metal-black"),
        box(0, header_y - bracket_depth / 2, height - inch(1).meters, rail_top + inch(1).meters,
            inch(3.5).meters, bracket_depth, "metal"),
        box(0, trolley_y, trolley_bottom, height + inch(0.35).meters,
            inch(2.1).meters, inch(4.5).meters, "appliance-steel"),
        prism(circle(0, trolley_y, inch(0.09).meters, segments=12)["points"],
              handle_top, trolley_bottom, "disposal-reset"),
        box(0, trolley_y, handle_top - inch(0.7).meters, handle_top,
            inch(2.5).meters, inch(0.7).meters, "disposal-reset"),
        box(0, strap_y, CEILING_DROP - _STEEL_THICKNESS, CEILING_DROP,
            width * 0.80, strap_width, "metal"),
        *(box(side * width * 0.27, strap_y, height * 0.895, CEILING_DROP - _STEEL_THICKNESS,
              _STEEL_THICKNESS, strap_width, "metal") for side in (-1, 1)),
    )


def liftmaster_87504(width: float, depth: float, height: float) -> Geometry:
    outline = polygon(_rounded_rectangle_points(width, depth, depth * 0.16))
    installation = tuple({**part, "role": "garage-opener:installation"}
                         for part in _installation(width, depth, height))
    return (outline,), _head(width, depth, height) + installation
