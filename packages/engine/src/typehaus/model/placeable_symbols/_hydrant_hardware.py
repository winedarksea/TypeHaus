"""Flat casting cheeks shared by the yard and wall hydrant product models."""

import math

from typehaus.model.placeable_symbols._frame import Part
from typehaus.quantities import M_PER_IN
from typehaus.triangulation import planar_ring_triangles


def side_profile(profile, width, color, z_shift=0.0) -> Part:
    if sum(a[0] * b[1] - b[0] * a[1]
           for a, b in zip(profile, (*profile[1:], profile[0]), strict=True)) < 0:
        profile = tuple(reversed(profile))
    points = tuple((x * M_PER_IN, y * M_PER_IN, (z + z_shift) * M_PER_IN)
                   for x in (-width / 2, width / 2) for y, z in profile)
    count = len(profile)
    cap = planar_ring_triangles(points[:count])
    triangles = [*(tuple(reversed(t)) for t in cap),
                 *(tuple(i + count for i in t) for t in cap)]
    for i in range(count):
        following = (i + 1) % count
        triangles.extend(((i, following, following + count), (i, following + count, i + count)))
    minimum = tuple(min(p[i] for p in points) for i in range(3))
    maximum = tuple(max(p[i] for p in points) for i in range(3))
    # Split sharp edges so the head's flat casting cheeks do not inherit rounded normals.
    vertices, normals = [], []
    for triangle in triangles:
        a, b, c = (points[i] for i in triangle)
        u = tuple(v - w for v, w in zip(b, a, strict=True))
        v = tuple(v - w for v, w in zip(c, a, strict=True))
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                 u[0] * v[1] - u[1] * v[0])
        magnitude = math.sqrt(sum(x * x for x in cross))
        normal = tuple(x / magnitude for x in cross)
        vertices.extend((a, b, c))
        normals.extend((normal,) * 3)
    return {"center": tuple((a + b) / 2 for a, b in zip(minimum, maximum, strict=True)),
            "size": tuple(b - a for a, b in zip(minimum, maximum, strict=True)),
            "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(vertices),
                     "triangles": tuple((i, i + 1, i + 2) for i in range(0, len(vertices), 3)),
                     "normals": tuple(normals)}}

