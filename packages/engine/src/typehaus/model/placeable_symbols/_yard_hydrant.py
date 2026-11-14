"""Product geometry and the shared hose-outlet frame; no project placement here."""

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, circle, line, rect
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.placeable_symbols._yard_hydrant_config import BREAKER_34HD, Y34SS
from typehaus.quantities import M_PER_IN
from typehaus.triangulation import planar_ring_triangles


def hose_outlet(height_m: float) -> tuple[tuple[float, float, float],
                                         tuple[float, float, float]]:
    """Connection at the nozzle thread tip, directed down toward the hose."""
    return ((0.0, -Y34SS.nozzle_forward * M_PER_IN,
             height_m - (Y34SS.height - Y34SS.nozzle_height) * M_PER_IN), (0.0, 0.0, -1.0))


def _side_profile(profile, width, color, z_shift=0.0) -> Part:
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


def _cylinder(center, diameter, length, *, axis=2, color="hydrant-orange") -> Part:
    return round_cylinder(tuple(v * M_PER_IN for v in center), diameter / 2 * M_PER_IN,
                          length * M_PER_IN, axis=axis, color=color)


def _handle_bar(start, end, diameter) -> Part:
    """Rotate a cylinder in the depth/height plane, retaining smooth analytic normals."""
    dy, dz = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dy, dz)
    part = _cylinder((0, 0, 0), diameter, length)

    def rotate(p):
        return (p[0], p[1] * dz / length + p[2] * dy / length,
                -p[1] * dy / length + p[2] * dz / length)

    center = (0.0, (start[0] + end[0]) / 2 * M_PER_IN,
              (start[1] + end[1]) / 2 * M_PER_IN)
    mesh = part["mesh"]
    points = tuple(tuple(v + c for v, c in zip(rotate(p), center, strict=True))
                   for p in mesh["positions"])
    part["mesh"] = {"positions": points, "triangles": mesh["triangles"],
                    "normals": tuple(rotate(n) for n in mesh["normals"])}
    part["center"] = center
    part["size"] = tuple(max(p[i] for p in points) - min(p[i] for p in points)
                         for i in range(3))
    return part


def yard_hydrant(width: float, depth: float, height: float) -> Geometry:
    """Fixed product dimensions: height changes extend only the straight casing."""
    d = Y34SS
    shift = height / M_PER_IN - d.height
    parts = [
        _cylinder((0, 0, (d.casing_top + shift) / 2), d.casing_outside_diameter,
                  d.casing_top + shift, color="metal"),
        _side_profile(d.casting_profile, d.casting_width, "hydrant-orange", shift),
        _side_profile(d.lever_profile, d.lever_width, "hydrant-orange", shift),
        _cylinder((0, d.linkage_depth, d.linkage_bottom + shift), d.packing_nut_diameter,
                  d.packing_nut_height, color="brass"),
        _cylinder((0, d.linkage_depth, (d.linkage_top + d.linkage_bottom) / 2 + shift),
                  d.linkage_diameter, d.linkage_top - d.linkage_bottom, color="brass"),
        _cylinder((0, d.linkage_depth, d.linkage_top + shift), d.pivot_diameter,
                  d.width, axis=0, color="metal"),
    ]
    for a, b in zip(d.handle_loop, d.handle_loop[1:], strict=False):
        parts.append(_handle_bar((a[0], a[1] + shift), (b[0], b[1] + shift),
                                 d.handle_bar_diameter))
    outlet, _ = hose_outlet(height)
    parts.append(round_cylinder((outlet[0], outlet[1],
                                 outlet[2] + d.nozzle_thread_length * M_PER_IN / 2),
                                d.hose_thread_diameter * M_PER_IN / 2,
                                d.nozzle_thread_length * M_PER_IN, axis=2, color="brass"))
    strokes = (circle(0, 0, d.casing_outside_diameter * M_PER_IN / 2, fill="metal"),
               rect(0, -d.nozzle_forward * M_PER_IN / 2, d.casting_width * M_PER_IN,
                    d.nozzle_forward * M_PER_IN, fill="hydrant-orange"),
               line((0, 0), (0, d.handle_loop[4][0] * M_PER_IN)),
               circle(0, outlet[1], d.hose_thread_diameter * M_PER_IN / 2))
    return strokes, tuple(parts)


def vacuum_breaker_parts() -> tuple[Part, ...]:
    """Origin is the engaged nozzle tip, not the breaker's centre; outlet points -Z."""
    d = BREAKER_34HD
    top, bottom = d.engagement, d.engagement - d.length
    vent_top = top - d.collar_length
    vent_bottom = vent_top - d.vent_band_length
    body_bottom = bottom + d.thread_length
    parts = [
        _cylinder((0, 0, top - d.collar_length / 2), d.diameter, d.collar_length, color="brass"),
        _cylinder((0, 0, (vent_bottom + body_bottom) / 2), d.body_radius * 2,
                  vent_bottom - body_bottom, color="brass"),
        _cylinder((0, 0, bottom + d.thread_length / 2), d.thread_diameter,
                  d.thread_length, color="brass"),
        _cylinder((0, 0, (vent_top + vent_bottom) / 2), d.vent_radius * 2,
                  d.vent_band_length, color="metal-black"),
        _cylinder((d.diameter / 2, 0, top - d.collar_length / 2), d.stop_screw_radius * 2,
                  d.stop_screw_length, axis=0, color="metal"),
    ]
    for i in range(d.vent_count):
        angle = math.tau * i / d.vent_count
        parts.append(_cylinder((d.body_radius * math.cos(angle), d.body_radius * math.sin(angle),
                                (vent_top + vent_bottom) / 2),
                               d.vent_bridge_width, d.vent_band_length, color="brass"))
    return tuple(parts)
