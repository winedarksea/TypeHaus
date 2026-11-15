"""Pipe-aligned, bore-scaled valve symbols shared by the viewer and both exporters.

These are generic quarter-turn valves, not manufacturer installation envelopes. One mesh
keeps each accessory a single selectable, scheduled and exported device.
"""

from dataclasses import dataclass
from math import cos, dist, sin, sqrt, tau

from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.resolve.geometry_ir import GMesh, Vec3
from typehaus.resolve.model import ResolvedPipeRun, ResolvedSolid


@dataclass(frozen=True)
class IsolationValveProportions:
    """Lengths as multiples of host diameter; representative full-port valve proportions."""

    body_length: float = 2.4
    body_radius: float = 0.85
    coupling_offset: float = 1.35
    coupling_length: float = 0.7
    coupling_radius: float = 0.95
    tail_offset: float = 1.85
    tail_length: float = 0.5
    tail_radius: float = 0.65
    bonnet_height: float = 0.95
    bonnet_radius: float = 0.5
    bonnet_length: float = 0.55
    stem_height: float = 1.3
    stem_radius: float = 0.22
    stem_length: float = 0.6
    lever_height: float = 1.65
    lever_start: float = -0.4
    lever_end: float = 3.7
    lever_width: float = 0.6
    lever_thickness: float = 0.16
    fastener_height: float = 1.82
    fastener_radius: float = 0.3
    fastener_length: float = 0.18


VALVE_PROPORTIONS = IsolationValveProportions()
_GEOMETRY_TOLERANCE = 1e-12
_VERTICAL_ALIGNMENT_LIMIT = 0.95


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(vector):
    magnitude = sqrt(_dot(vector, vector))
    return tuple(value / magnitude for value in vector)


def host_pipe_frame(host: ResolvedPipeRun, center: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    """Nearest nonzero 3D leg; repeated XY vertices on risers remain real segments.

    A horizontal valve's stem points up. A vertical valve's stem points toward -Y;
    projecting that reference off the pipe also handles sloping legs without distortion.
    """
    points = [(x, y, host.z_m[i] if host.z_m is not None else center[2])
              for i, (x, y) in enumerate(host.path)]
    candidates = []
    for start, end in zip(points, points[1:], strict=False):
        vector = tuple(b - a for a, b in zip(start, end, strict=True))
        length_squared = _dot(vector, vector)
        if length_squared <= _GEOMETRY_TOLERANCE:
            continue
        fraction = max(0.0, min(1.0, _dot(
            tuple(c - a for c, a in zip(center, start, strict=True)), vector) / length_squared))
        closest = tuple(a + fraction * v for a, v in zip(start, vector, strict=True))
        candidates.append((dist(center, closest), vector))
    if not candidates:
        raise ValueError(f"{host.tag}: isolation valve requires a nonzero host pipe segment")
    axis = _unit(min(candidates, key=lambda item: item[0])[1])
    reference = (0.0, -1.0, 0.0) if abs(axis[2]) > _VERTICAL_ALIGNMENT_LIMIT else (0., 0., 1.)
    stem = _unit(tuple(r - _dot(reference, axis) * a
                       for r, a in zip(reference, axis, strict=True)))
    return axis, _cross(stem, axis), stem


def _polygonal_prism(profile, start, end, axis):
    radial_axes = ((axis + 1) % 3, (axis + 2) % 3)

    def ring(station):
        points = []
        for u, v in profile:
            point = [0.0, 0.0, 0.0]
            point[axis] = station
            point[radial_axes[0]], point[radial_axes[1]] = u, v
            points.append(tuple(point))
        return points

    lower, upper = ring(start), ring(end)
    count = len(profile)
    lower_center = tuple(sum(p[i] for p in lower) / count for i in range(3))
    upper_center = tuple(sum(p[i] for p in upper) / count for i in range(3))
    vertices = (*lower, *upper, lower_center, upper_center)
    triangles = []
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((index, following, count + following),
                          (index, count + following, count + index),
                          (2 * count, following, index),
                          (2 * count + 1, count + index, count + following)))
    # Split flat faces so the coupling flats and stamped lever stay crisp beside cylinders.
    positions, normals = [], []
    for triangle in triangles:
        a, b, c = [vertices[i] for i in triangle]
        normal = _unit(_cross(tuple(y - x for x, y in zip(a, b, strict=True)),
                              tuple(y - x for x, y in zip(a, c, strict=True))))
        positions.extend((a, b, c))
        normals.extend((normal,) * 3)
    return GMesh(tuple(positions), tuple((i, i + 1, i + 2)
                 for i in range(0, len(positions), 3)), tuple(normals))


def isolation_valve_solid(*, uid: str, tag: str, storey: str, category: str,
                          center: Vec3, host: ResolvedPipeRun) -> ResolvedSolid:
    dimensions = VALVE_PROPORTIONS
    diameter = host.diameter_m
    parts = []

    def cylinder(point, radius, length, axis):
        mesh = round_cylinder(point, radius, length, axis=axis)["mesh"]
        parts.append(GMesh(mesh["positions"], mesh["triangles"], mesh["normals"]))

    def hex_nut(station, radius, length, axis):
        profile = [(radius * cos(tau * i / 6), radius * sin(tau * i / 6)) for i in range(6)]
        parts.append(_polygonal_prism(profile, station - length / 2, station + length / 2, axis))

    cylinder((0., 0., 0.), dimensions.body_radius, dimensions.body_length, 0)
    for sign in (-1, 1):
        hex_nut(sign * dimensions.coupling_offset, dimensions.coupling_radius,
                dimensions.coupling_length, 0)
        cylinder((sign * dimensions.tail_offset, 0., 0.), dimensions.tail_radius,
                 dimensions.tail_length, 0)
    cylinder((0., 0., dimensions.bonnet_height), dimensions.bonnet_radius,
             dimensions.bonnet_length, 2)
    cylinder((0., 0., dimensions.stem_height), dimensions.stem_radius, dimensions.stem_length, 2)
    half_width = dimensions.lever_width / 2
    lever_profile = [(dimensions.lever_start, -half_width), (dimensions.lever_end, -half_width),
                     (dimensions.lever_end, half_width), (dimensions.lever_start, half_width)]
    parts.append(_polygonal_prism(lever_profile,
        dimensions.lever_height - dimensions.lever_thickness / 2,
        dimensions.lever_height + dimensions.lever_thickness / 2, 2))
    hex_nut(dimensions.fastener_height, dimensions.fastener_radius, dimensions.fastener_length, 2)
    frame = host_pipe_frame(host, center)

    def rotate(point):
        return tuple(sum(point[j] * frame[j][i] for j in range(3)) for i in range(3))

    positions, normals, triangles, curved = [], [], [], set()
    for part in parts:
        offset = len(positions)
        positions.extend(tuple(c + diameter * v for c, v in zip(center, rotate(p), strict=True))
                         for p in part.positions)
        normals.extend(rotate(n) for n in part.normals)
        triangles.extend(tuple(offset + i for i in triangle) for triangle in part.triangles)
        curved.update(range(offset, len(positions)))
    minimum = tuple(min(p[i] for p in positions) for i in range(3))
    maximum = tuple(max(p[i] for p in positions) for i in range(3))
    x0, y0, z0 = minimum
    x1, y1, z1 = maximum
    return ResolvedSolid(uid=uid, tag=tag, storey=storey, category=category,
        outline=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), z0_m=z0, z1_m=z1,
        body_mesh=GMesh(tuple(positions), tuple(triangles), tuple(normals),
                        curved_vertices=frozenset(curved)))
