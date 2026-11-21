"""A device box's mount, drawn (decision #149): convex prisms beside, over or under the box.

Pieces are built straight in world coordinates from unit vectors, so a sloped ceiling's
frame needs nothing special: ``along`` is the run of a bar, ``across`` its width and ``up``
its thickness direction (away from the room).
"""

from __future__ import annotations

import math

from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.duct_mesh import prism
from typehaus.resolve.geometry_ir import GMesh

Vec3 = tuple[float, float, float]
_TUBE_FACETS = 8
FOOT_RISE_M = 0.0254  # a bar's end tab, up its member's face (representative)


def _at(origin: Vec3, *terms: tuple[Vec3, float]) -> Vec3:
    return tuple(origin[i] + sum(v[i] * k for v, k in terms) for i in range(3))


def block(centre: Vec3, axes: tuple[Vec3, Vec3, Vec3], half: tuple[float, float, float]) -> GMesh:
    """A rectangular block about ``centre``, ``half`` its half-sizes along ``axes``."""
    a, b, c = axes
    ring = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    def face(sign: float) -> list[Vec3]:
        return [_at(centre, (a, -half[0] * sign), (b, i * half[1]), (c, j * half[2]))
                for i, j in ring]
    return prism(face(1.0), face(-1.0))


def bar(start: Vec3, end: Vec3, across: Vec3, up: Vec3, width: float, thick: float,
        profile: str = "flat") -> GMesh:
    """A flat bar ``width`` x ``thick`` (or a tube of diameter ``width``) from start to end."""
    if profile == "tube":
        r = width / 2
        ring = [(r * math.cos(2 * math.pi * (i + 0.5) / _TUBE_FACETS),
                 r * math.sin(2 * math.pi * (i + 0.5) / _TUBE_FACETS))
                for i in range(_TUBE_FACETS)]
    else:
        ring = [(-width / 2, -thick / 2), (width / 2, -thick / 2), (width / 2, thick / 2),
                (-width / 2, thick / 2)]
    return prism([_at(start, (across, s), (up, t)) for s, t in ring],
                 [_at(end, (across, s), (up, t)) for s, t in ring])


def spanning_bar(centre: Vec3, along: Vec3, across: Vec3, up: Vec3, s0: float, s1: float,
                 width: float, thick: float, profile: str) -> GMesh:
    """A bar from ``s0`` to ``s1`` along ``along`` through ``centre``, plus an end tab up
    each member face (a brace's flanged end plate, a hanger's foot)."""
    start, end = _at(centre, (along, s0)), _at(centre, (along, s1))
    tabs = [block(_at(centre, (along, s + sense * thick / 2), (up, FOOT_RISE_M / 2)),
                  (along, across, up), (thick / 2, width / 2, FOOT_RISE_M / 2))
            for s, sense in ((s0, 1.0), (s1, -1.0))]
    return combine_meshes(bar(start, end, across, up, width, thick, profile), *tabs)


def side_plate(face_point: Vec3, tangent: Vec3, normal: Vec3, up: Vec3, side: float,
               half_width: float, depth: float, setback: float, plate: float, thick: float,
               length: float) -> GMesh:
    """A nail-on ear or side bracket on the stud side (``side`` = -1 left, +1 right) of a
    wall box: ``thick`` against the stud face, ``plate`` deep behind the set-back."""
    plate = min(plate, max(depth - setback, thick))
    centre = _at(face_point, (tangent, side * (half_width + thick / 2)),
                 (normal, -setback - plate / 2))
    return block(centre, (tangent, normal, up), (thick / 2, plate / 2, length / 2))
