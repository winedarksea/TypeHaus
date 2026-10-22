"""K-1130-W1 drop-in shell: rectangular basin, end drain, one sloped lumbar end.

Local +x runs from the drain end to the lumbar (heater) end. Basin sizes are Kohler's;
the end-wall split of the 13 1/8" top-to-bottom taper is a visualization estimate.
"""

from math import cos, pi, sin

from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, rect
from typehaus.model.placeable_symbols._kohler_underscore import (
    BASIN_BOTTOM_Z_IN,
    DRAIN_RADIUS_IN,
    DRAIN_SEGMENTS,
    OVERFLOW_BELOW_RIM_IN,
    OVERFLOW_WIDTH_IN,
    RIM_THICKNESS_IN,
    SEGMENTS,
    SHELL_THICKNESS_IN,
    _band,
)
from typehaus.model.placeable_symbols._mesh import mesh_part

OVERALL_WIDTH_IN = 60.0
OVERALL_DEPTH_IN = 32.0
OVERALL_HEIGHT_IN = 21.0
BASIN_TOP_WIDTH_IN = 55.125
BASIN_TOP_DEPTH_IN = 27.125
BASIN_BOTTOM_WIDTH_IN = 42.0
BASIN_BOTTOM_DEPTH_IN = 23.5
DRAIN_END_TAPER_IN = 2.0  # the rest of the taper is the lumbar slope (~34 deg)
DRAIN_FROM_END_IN = 12.5625


def _extents(z_fraction):
    """(x0, x1, half_y) of the inner basin, inches, at a fraction of rim height."""
    f = max(0.0, min(1.0, z_fraction))
    top_x0 = -BASIN_TOP_WIDTH_IN / 2
    bottom_x0 = top_x0 + DRAIN_END_TAPER_IN
    x0 = bottom_x0 + f * (top_x0 - bottom_x0)
    x1 = bottom_x0 + BASIN_BOTTOM_WIDTH_IN + f * (
        BASIN_TOP_WIDTH_IN / 2 - bottom_x0 - BASIN_BOTTOM_WIDTH_IN)
    half_y = (BASIN_BOTTOM_DEPTH_IN + f * (BASIN_TOP_DEPTH_IN - BASIN_BOTTOM_DEPTH_IN)) / 2
    return x0, x1, half_y


def shell_section(z_fraction: float, width: float, depth: float):
    """Conservative outer shell rectangle (local x0, x1, y0, y1) for clearance clipping."""
    shoulder = 1 - RIM_THICKNESS_IN / OVERALL_HEIGHT_IN
    x0, x1, half_y = _extents(z_fraction / shoulder)
    sx, sy = width / OVERALL_WIDTH_IN, depth / OVERALL_DEPTH_IN
    t = SHELL_THICKNESS_IN
    return ((x0 - t) * sx, (x1 + t) * sx, -(half_y + t) * sy, (half_y + t) * sy)


def support_center_x(width: float):
    """The basin bottom's centre, offset toward the drain end."""
    x0, x1, _ = _extents(0.0)
    return (x0 + x1) / 2 * width / OVERALL_WIDTH_IN


def drain_x(width: float):
    return (DRAIN_FROM_END_IN - OVERALL_WIDTH_IN / 2) * width / OVERALL_WIDTH_IN


def _ring(x0, x1, ry, z):
    cx, rx = (x0 + x1) / 2, (x1 - x0) / 2
    result = []
    for index in range(SEGMENTS):
        angle = 2 * pi * index / SEGMENTS
        x, y = cos(angle), sin(angle)
        divisor = max(abs(x), abs(y))
        result.append((cx + rx * x / divisor, ry * y / divisor, z))
    return result


def kohler_underscore_rect(width, depth, height):
    """A hollow rectangular basin, drain end toward local -x, inside the drop-in lip."""
    sx, sy, sz = width / OVERALL_WIDTH_IN, depth / OVERALL_DEPTH_IN, height / OVERALL_HEIGHT_IN
    thickness = SHELL_THICKNESS_IN * sz
    rim_t = RIM_THICKNESS_IN * sz
    bottom_z = BASIN_BOTTOM_Z_IN * sz
    bx0, bx1, by = _extents(0.0)
    tx0, tx1, ty = _extents(1.0)
    rings = [
        _ring(bx0 * sx, bx1 * sx, by * sy, bottom_z),
        _ring(tx0 * sx, tx1 * sx, ty * sy, height),
        _ring(-width / 2, width / 2, depth / 2, height),
        _ring(-width / 2, width / 2, depth / 2, height - rim_t),
        _ring(tx0 * sx - thickness, tx1 * sx + thickness, ty * sy + thickness, height - rim_t),
        _ring(bx0 * sx - thickness, bx1 * sx + thickness, by * sy + thickness, 0.0),
    ]
    parts = [_band(a, b) for a, b in zip(rings[:-1], rings[1:], strict=True)]
    for ring, upward in ((rings[0], True), (rings[-1], False)):
        cx = sum(p[0] for p in ring) / len(ring)
        vertices = ring + [(cx, 0.0, ring[0][2])]
        triangles = [(SEGMENTS, index, (index + 1) % SEGMENTS) for index in range(SEGMENTS)]
        if not upward:
            triangles = [(a, c, b) for a, b, c in triangles]
        parts.append(mesh_part(vertices, triangles, "porcelain"))
    vertices, triangles, normals = [], [], []
    for part in parts:
        mesh = part["mesh"]
        offset = len(vertices)
        vertices.extend(mesh["positions"])
        normals.extend(mesh["normals"])
        triangles.extend(tuple(offset + i for i in triangle) for triangle in mesh["triangles"])
    bounds = [(min(p[i] for p in vertices), max(p[i] for p in vertices)) for i in range(3)]
    shell = {"center": tuple((lo + hi) / 2 for lo, hi in bounds),
             "size": tuple(hi - lo for lo, hi in bounds), "color": "porcelain",
             "points": (), "shape": "mesh",
             "mesh": {"positions": tuple(vertices), "triangles": tuple(triangles),
                      "normals": tuple(normals)}}
    parts = [shell]
    dx = drain_x(width)
    radius = DRAIN_RADIUS_IN * sx
    angles = [2 * pi * i / DRAIN_SEGMENTS for i in range(DRAIN_SEGMENTS)]
    ring = [(dx + radius * cos(a), radius * sin(a)) for a in angles]
    drain_vertices = [(x, y, z) for z in (bottom_z, bottom_z + thickness / 4) for x, y in ring]
    drain_triangles = []
    for index in range(DRAIN_SEGMENTS):
        following = (index + 1) % DRAIN_SEGMENTS
        drain_triangles.extend(((index, following, following + DRAIN_SEGMENTS),
                                (index, following + DRAIN_SEGMENTS, index + DRAIN_SEGMENTS)))
    for index in range(1, DRAIN_SEGMENTS - 1):
        drain_triangles.extend(((0, index + 1, index),
                                (DRAIN_SEGMENTS, DRAIN_SEGMENTS + index,
                                 DRAIN_SEGMENTS + index + 1)))
    parts.append(mesh_part(drain_vertices, drain_triangles, "metal"))
    # The slotted overflow sits on the drain end wall, just under the rim.
    overflow_z = height - OVERFLOW_BELOW_RIM_IN * sz
    fraction = (overflow_z - bottom_z) / (height - bottom_z)
    overflow_x = (bx0 + fraction * (tx0 - bx0)) * sx
    parts.append(box(overflow_x + thickness / 4, 0, overflow_z, overflow_z + thickness,
                     thickness / 2, OVERFLOW_WIDTH_IN * sy, "metal"))
    strokes = (rect(0, 0, width, depth, fill="porcelain"),
               rect((tx0 + tx1) / 2 * sx, 0, (tx1 - tx0) * sx, 2 * ty * sy, weight=DETAIL_WEIGHT),
               circle(dx, 0, radius, weight=DETAIL_WEIGHT))
    return strokes, tuple(parts)
