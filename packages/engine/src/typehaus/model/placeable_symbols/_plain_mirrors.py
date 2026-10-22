"""Plain framed mirror faces extruded toward the wall, without lighting or shelves."""

from __future__ import annotations

import math
from typing import Literal

from typehaus.model.placeable_symbols._families import Builder
from typehaus.model.placeable_symbols._frame import Part, depth_cylinder, rect
from typehaus.model.placeable_symbols._mesh import mesh_part

MirrorShape = Literal["round", "arch", "soft-rectangle", "capsule"]
FRAME_BORDER_M = 0.00635
GLASS_THICKNESS_M = 0.004
CORNER_RADIUS_SHARE = 0.12
QUARTER_ARC_SEGMENTS = 16


def mirror_face_outline(shape: MirrorShape, width: float, height: float):
    """Counterclockwise convex face in local x/z, with its bottom at zero."""
    if shape == "arch":
        radius = min(width / 2, height)
        return ((-width / 2, 0.0), (width / 2, 0.0), *(
            (radius * math.cos(math.pi * step / (2 * QUARTER_ARC_SEGMENTS)),
             height - radius + radius * math.sin(math.pi * step / (2 * QUARTER_ARC_SEGMENTS)))
            for step in range(2 * QUARTER_ARC_SEGMENTS + 1)))
    radius = min(width, height) * (0.5 if shape == "capsule" else CORNER_RADIUS_SHARE)
    points = []
    for cx, cz, start in ((width / 2 - radius, radius, -90),
                          (width / 2 - radius, height - radius, 0),
                          (-width / 2 + radius, height - radius, 90),
                          (-width / 2 + radius, radius, 180)):
        for step in range(QUARTER_ARC_SEGMENTS + 1):
            angle = math.radians(start + 90 * step / QUARTER_ARC_SEGMENTS)
            point = (cx + radius * math.cos(angle), cz + radius * math.sin(angle))
            # Capsule semicircles join at the same point; zero edges have no normal.
            if not points or math.dist(points[-1], point) > 1e-10:
                points.append(point)
    if math.dist(points[0], points[-1]) < 1e-10:
        points.pop()
    return tuple(points)


def _face_solid(outline, front_y: float, rear_y: float, color: str) -> Part:
    count = len(outline)
    centre = tuple(sum(p[axis] for p in outline) / count for axis in range(2))
    positions = [(x, y, z) for y in (front_y, rear_y) for x, z in outline]
    positions.extend((centre[0], y, centre[1]) for y in (front_y, rear_y))
    triangles = []
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((2 * count, index, following),
                          (2 * count + 1, count + following, count + index),
                          (index, count + index, count + following),
                          (index, count + following, following)))
    return mesh_part(positions, triangles, color)


def plain_mirror(shape: MirrorShape, finish: str) -> Builder:
    """A narrow frame with the polished glass exposed toward the room (-y)."""
    def build(width: float, depth: float, height: float):
        border = min(FRAME_BORDER_M, min(width, height) / 8)
        glass_depth = min(GLASS_THICKNESS_M, depth / 4)
        strokes = (rect(0, 0, width, depth, fill=finish),)
        if shape == "round":
            parts = (depth_cylinder(0, glass_depth / 2, height / 2, min(width, height) / 2,
                                    depth - glass_depth, finish),
                     depth_cylinder(0, -depth / 2 + glass_depth / 2, height / 2,
                                    min(width, height) / 2 - border, glass_depth, "mirror"))
        else:
            outer = mirror_face_outline(shape, width, height)
            inner = tuple((x, z + border) for x, z in mirror_face_outline(
                shape, width - 2 * border, height - 2 * border))
            parts = (_face_solid(outer, -depth / 2 + glass_depth, depth / 2, finish),
                     _face_solid(inner, -depth / 2, -depth / 2 + glass_depth, "mirror"))
        return strokes, parts
    return build
