"""IKEA NYMÅNE wall/reading lamp, white plug-in (203.569.90), head tilted down and out.

Form: a tall rectangular wall housing (dimmer knob low on its room face), a short round
arm, and an open cylindrical shade on a horizontal pivot, GU10 LED lamp inside.
Published (cm): height 11, diameter 7; the 4 3/4 x 3 1/4 x 6 1/2 in. IKEA lists is the
carton, not the lamp. Estimated from the assembly-sheet drawings and photos: housing
5 x 4.5 x 11 (the published height read as the housing's), arm 1.6 dia x 2.5 long, shade
7 dia x 8.5 long pivoting 3.7 below its top, knob 1.8 dia, 30 degree tilt from straight down.
The envelope is that pose: +y is the mounting wall, z=0 the housing bottom.
Refs: https://www.ikea.com/us/en/p/nymane-wall-reading-lamp-white-20356990/ and
https://www.ikea.com/us/en/assembly_instructions/nymane-wall-reading-lamp-white__AA-2040655-6-100.pdf
"""

from __future__ import annotations

import math
from functools import cache

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, box, line, polygon
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

HOUSING_W, HOUSING_D, HOUSING_H = 5.0, 4.5, 11.0
ARM_RADIUS, ARM_LENGTH, ARM_Z = 0.8, 2.5, 9.3
SHADE_RADIUS, SHADE_LENGTH, PIVOT_BELOW_TOP = 3.5, 8.5, 3.7
TILT = math.radians(30)
KNOB_RADIUS, KNOB_PROJECTION, KNOB_Z = 0.9, 0.9, 3.2
LAMP_FILL, LAMP_THICKNESS, LAMP_PROUD = 0.82, 0.1, 0.02
SEGMENTS = 32
FINISH = "appliance-white"

Point2 = tuple[float, float]
Point3 = tuple[float, float, float]
Mesh = tuple[list[Point3], list[tuple[int, int, int]], str]


def _tube(start: Point2, end: Point2, radius: float, color: str) -> Mesh:
    """A closed round cylinder between two (projection, z) points; its axis lies in that plane."""
    length = math.dist(start, end)
    normal = (-(end[1] - start[1]) / length, (end[0] - start[0]) / length)
    positions: list[Point3] = [
        (radius * math.cos(a), c[0] + radius * math.sin(a) * normal[0],
         c[1] + radius * math.sin(a) * normal[1])
        for c in (start, end) for a in (math.tau * i / SEGMENTS for i in range(SEGMENTS))]
    triangles: list[tuple[int, int, int]] = []
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        triangles.extend(((i, i + SEGMENTS, j), (j, i + SEGMENTS, j + SEGMENTS)))
    for offset in (0, SEGMENTS):
        triangles.extend((offset, offset + i, offset + i + 1) for i in range(1, SEGMENTS - 1))
    return positions, outward(positions, triangles), color


def _along(point: Point2, axis: Point2, distance: float) -> Point2:
    return point[0] + distance * axis[0], point[1] + distance * axis[1]


@cache
def _design() -> tuple[tuple[Mesh, ...], tuple[float, float, float]]:
    """Round parts as meshes in product cm (x along the wall, p out from it, z up), and the
    (x, p, z) maxima of the whole lamp, housing included."""
    pivot = (HOUSING_D + ARM_LENGTH, ARM_Z)
    centre = _along(pivot, (math.cos(TILT), math.sin(TILT)), SHADE_RADIUS)
    down = (math.sin(TILT), -math.cos(TILT))  # shade axis, closed top to open mouth
    top = _along(centre, down, -PIVOT_BELOW_TOP)
    mouth = _along(centre, down, SHADE_LENGTH - PIVOT_BELOW_TOP)
    meshes = (_tube((HOUSING_D - 0.2, ARM_Z), pivot, ARM_RADIUS, FINISH),
              _tube((HOUSING_D - 0.2, KNOB_Z), (HOUSING_D + KNOB_PROJECTION, KNOB_Z),
                    KNOB_RADIUS, FINISH),
              _tube(top, mouth, SHADE_RADIUS, FINISH),
              _tube(_along(mouth, down, -LAMP_THICKNESS), _along(mouth, down, LAMP_PROUD),
                    SHADE_RADIUS * LAMP_FILL, "lamp"))
    points = [p for positions, _, _ in meshes for p in positions]
    points.append((HOUSING_W / 2, HOUSING_D, HOUSING_H))
    return meshes, tuple(max(p[axis] for p in points) for axis in range(3))


def _hull(points: list[Point2]) -> list[Point2]:
    """Convex hull, counter-clockwise (monotone chain)."""
    pts = sorted(set(points))

    def chain(seq: list[Point2]) -> list[Point2]:
        out: list[Point2] = []
        for q in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (q[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(q)
        return out[:-1]

    return chain(pts) + chain(pts[::-1])


def ikea_nymane_wall_lamp(width: float, depth: float, height: float) -> Geometry:
    """Scale the posed lamp into width x depth x height; +y is the wall, z=0 the housing bottom."""
    meshes, (x_max, p_max, z_max) = _design()
    sx, sy, sz = width / 2 / x_max, depth / p_max, height / z_max

    def place(x: float, p: float, z: float) -> Point3:
        return x * sx, depth / 2 - p * sy, z * sz

    # Housing, then the round parts, each scaled with the one anisotropic frame.
    (hx0, hy0, hz0), (hx1, hy1, hz1) = (place(-HOUSING_W / 2, 0, 0),
                                        place(HOUSING_W / 2, HOUSING_D, HOUSING_H))
    parts: list[Part] = [box(0, (hy0 + hy1) / 2, hz0, hz1, hx1 - hx0, hy0 - hy1, FINISH)]
    placed = [[place(*p) for p in positions] for positions, _, _ in meshes]
    parts.extend(mesh_part(pts, tri, color)
                 for pts, (_, tri, color) in zip(placed, meshes, strict=True))
    shade, lit = placed[2:]
    strokes = (polygon([(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)], fill=FINISH),
               line((0, hy1), place(0, HOUSING_D + ARM_LENGTH, 0)[:2]),
               polygon(_hull([p[:2] for p in shade]), fill=FINISH),
               polygon(_hull([p[:2] for p in lit]), fill="lamp"))
    return strokes, tuple(parts)
