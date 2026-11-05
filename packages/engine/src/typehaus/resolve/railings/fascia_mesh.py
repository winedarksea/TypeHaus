"""Ultralox mount shells and unthreaded hardware, in a local inch-based part frame."""

import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import triangulate

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import (
    box_mesh,
    combine_meshes,
    plate_mesh,
    transform_mesh,
)
from typehaus.resolve.geometry_ir import GMesh

HARDWARE_FACETS = 12


def pierced_plate(width, bottom, top, thickness, holes=()):
    """A mounting leaf in x/z, extruded outboard (+y), with actual open bolt holes."""
    outer = ((-width / 2, bottom), (width / 2, bottom),
             (width / 2, top), (-width / 2, top))
    rings = [tuple(Point(x, z).buffer(radius, quad_segs=3).exterior.coords)[:-1]
             for x, z, radius in holes]
    polygon = Polygon(outer, rings)
    if not polygon.is_valid:
        raise ValueError("fascia mounting holes must fit within their flange")
    positions, triangles = [], []
    for triangle in triangulate(polygon):
        if not polygon.covers(triangle):
            continue
        corners = tuple(triangle.exterior.coords)[:3]
        start = len(positions)
        for y in (0, thickness):
            positions.extend((x * M_PER_IN, y * M_PER_IN, z * M_PER_IN)
                             for x, z in corners)
        triangles.extend(((start, start + 1, start + 2),
                          (start + 3, start + 5, start + 4)))
    for ring in (outer, *rings):
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            start = len(positions)
            positions.extend((x * M_PER_IN, y * M_PER_IN, z * M_PER_IN)
                             for x, z, y in ((*a, 0), (*b, 0),
                                             (*b, thickness), (*a, thickness)))
            triangles.extend(((start, start + 3, start + 2),
                              (start, start + 2, start + 1)))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def cylinder(radius, y0, y1, facets=HARDWARE_FACETS):
    ring = tuple((radius * math.cos(index * 2 * math.pi / facets), y0,
                  radius * math.sin(index * 2 * math.pi / facets)) for index in range(facets))
    return plate_mesh(ring, (0, y1 - y0, 0))


def washer(outer_radius, inner_radius, y, thickness):
    """Closed annulus, so neither washer fills the bolt clearance."""
    positions, triangles = [], []
    for depth in (y, y + thickness):
        for radius in (outer_radius, inner_radius):
            positions.extend((radius * math.cos(i * 2 * math.pi / HARDWARE_FACETS) * M_PER_IN,
                              depth * M_PER_IN,
                              radius * math.sin(i * 2 * math.pi / HARDWARE_FACETS) * M_PER_IN)
                             for i in range(HARDWARE_FACETS))
    n = HARDWARE_FACETS
    for i in range(n):
        j = (i + 1) % n
        for a, b, c, d in ((i, j, n + j, n + i),
                           (2*n + i, 3*n + i, 3*n + j, 2*n + j),
                           (i, 2*n + i, 2*n + j, j),
                           (n + i, n + j, 3*n + j, 3*n + i)):
            triangles.extend(((a, b, c), (a, c, d)))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def bolt_mesh(spec, grip_in=None):
    """A through-bolt with its rear washer and nut at ``grip_in``; None = a screw, no tail."""
    diameter = spec.bolt_diameter.inches
    thickness = spec.display_washer_thickness.inches
    head_height = spec.display_head_height.inches
    parts = [
        cylinder(diameter / 2, -spec.bolt_length.inches, 0),
        washer(spec.washer_diameter.inches / 2, diameter / 2, 0, thickness),
        cylinder(spec.display_head_width.inches / math.sqrt(3), thickness,
                 thickness + head_height, 6),
    ]
    if grip_in is not None:
        parts += [
            washer(spec.rear_washer_diameter.inches / 2, diameter / 2,
                   -grip_in - thickness, thickness),
            cylinder(spec.display_head_width.inches / math.sqrt(3),
                     -grip_in - thickness - head_height, -grip_in - thickness, 6),
        ]
    return combine_meshes(*parts)


def post_screw_mesh(spec, *, length_in=None):
    length = spec.post_screw_length.inches if length_in is None else length_in
    return combine_meshes(
        cylinder(spec.post_screw_diameter.inches / 2, -length, 0),
        cylinder(spec.display_head_width.inches / 2, 0,
                 spec.display_head_height.inches / 2),
    )


def pocket_mesh(spec, corner=False):
    """Open hat section; corners use a square sleeve joined to two mounting leaves."""
    half = spec.pocket_width.inches / 2
    wall = spec.wall_thickness.inches
    bottom = -spec.overall_height.inches
    plates = [box_mesh((-half-wall, -half, bottom), (-half, half+wall, 0)),
              box_mesh((half, -half, bottom), (half+wall, half+wall, 0)),
              box_mesh((-half, half, bottom), (half, half+wall, 0))]
    if corner:
        plates.append(box_mesh((-half-wall, -half-wall, bottom), (half+wall, -half, 0)))
    return combine_meshes(*plates)


def outside_corner_mesh(spec, mount_a, mount_b, side):
    """FM244390 in the first face's frame (x tangent, y outward, post at the origin): the
    post's two outboard walls run full, its two inboard walls jog out at 45 deg to the
    flanges' inner ends. ``mount_*`` are the mounting faces' offsets from the post along
    their own outward; ``side`` is the second face's outward along x (+/-1)."""
    half = spec.pocket_width.inches / 2
    mid = spec.wall_thickness.inches / 2
    jog = spec.display_corner_jog.inches
    out = half + mid
    # (along the first face's outward, along the second face's outward)
    path = ((mount_a + mid, mount_b - jog), (mount_a + jog, -out), (out, -out), (out, out),
            (-out, out), (-out, mount_b + jog), (mount_a - jog, mount_b + mid))
    wall = LineString([(side * v, u) for u, v in path]).buffer(
        mid, cap_style="flat", join_style="mitre")
    ring = tuple((x, y, -spec.overall_height.inches)
                 for x, y in tuple(wall.exterior.coords)[:-1])
    return plate_mesh(ring, (0, 0, spec.overall_height.inches))


def place(mesh, origin, tangent, outward):
    return transform_mesh(mesh, origin_m=origin,
                          x_axis=(*tangent, 0), y_axis=(*outward, 0))
