"""K-5713-W1 drop-in shell, scaled from Kohler's published basin dimensions.

Shell thickness and rim thickness are visualization approximations. The rim is not a
skirt and never extends down to the subfloor. The center drain is not the downstream tee.
"""

from math import cos, pi, sin, sqrt

from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, ellipse, rect
from typehaus.model.placeable_symbols._mesh import mesh_part

OVERALL_WIDTH_IN = 59.6875
OVERALL_DEPTH_IN = 35.75
OVERALL_HEIGHT_IN = 21.0
BASIN_TOP_WIDTH_IN = 55.5625
BASIN_TOP_DEPTH_IN = 28.375
BASIN_BOTTOM_WIDTH_IN = 43.0
BASIN_BOTTOM_DEPTH_IN = 25.625
SHELL_THICKNESS_IN = 0.25
RIM_THICKNESS_IN = 0.375
BASIN_BOTTOM_Z_IN = 1.5
OVERFLOW_BELOW_RIM_IN = 3.0
OVERFLOW_WIDTH_IN = 4.0
SEGMENTS = 96
DRAIN_RADIUS_IN = 0.75
DRAIN_SEGMENTS = 32


def shell_half_axes_at(z_fraction: float, width: float, depth: float):
    """Conservative outer shell section; shared by lower-return clearance clipping."""
    shoulder_fraction = 1 - RIM_THICKNESS_IN / OVERALL_HEIGHT_IN
    fraction = max(0.0, min(1.0, z_fraction / shoulder_fraction))
    thickness = width * SHELL_THICKNESS_IN / OVERALL_WIDTH_IN
    return (width * (BASIN_BOTTOM_WIDTH_IN + fraction *
                     (BASIN_TOP_WIDTH_IN - BASIN_BOTTOM_WIDTH_IN)) / OVERALL_WIDTH_IN / 2
            + thickness,
            depth * (BASIN_BOTTOM_DEPTH_IN + fraction *
                     (BASIN_TOP_DEPTH_IN - BASIN_BOTTOM_DEPTH_IN)) / OVERALL_DEPTH_IN / 2
            + thickness)


def _ring(rx, ry, z, rectangle=False):
    result = []
    for index in range(SEGMENTS):
        angle = 2 * pi * index / SEGMENTS
        x, y = cos(angle), sin(angle)
        divisor = max(abs(x), abs(y)) if rectangle else 1.0
        result.append((rx * x / divisor, ry * y / divisor, z))
    return result


def _band(first, second, smooth=False):
    vertices = first + second
    triangles = []
    for index in range(SEGMENTS):
        following = (index + 1) % SEGMENTS
        triangles.extend(((index, following, following + SEGMENTS),
                          (index, following + SEGMENTS, index + SEGMENTS)))
    triangles = [(a, c, b) for a, b, c in triangles]
    part = mesh_part(vertices, triangles, "porcelain")
    if smooth:
        # Average across each curved surface, splitting vertices between the rim and shell
        # so the acrylic keeps a crisp lip without visible triangulation in the basin.
        normals = [[0.0, 0.0, 0.0] for _ in vertices]
        for a, b, c in triangles:
            u = tuple(vertices[b][i] - vertices[a][i] for i in range(3))
            v = tuple(vertices[c][i] - vertices[a][i] for i in range(3))
            normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            for index in (a, b, c):
                for axis in range(3):
                    normals[index][axis] += normal[axis]
        unit_normals = tuple(tuple(value / sqrt(sum(n*n for n in normal)) for value in normal)
                             for normal in normals)
        part["mesh"] = {"positions": tuple(vertices), "triangles": tuple(triangles),
                        "normals": unit_normals}
    return part


def kohler_underscore(width, depth, height):
    """A hollow, tapered oval basin inside the rectangular drop-in lip."""
    thickness = height * SHELL_THICKNESS_IN / OVERALL_HEIGHT_IN
    rim_t = height * RIM_THICKNESS_IN / OVERALL_HEIGHT_IN
    bottom_z = height * BASIN_BOTTOM_Z_IN / OVERALL_HEIGHT_IN
    top_rx = width * BASIN_TOP_WIDTH_IN / OVERALL_WIDTH_IN / 2
    top_ry = depth * BASIN_TOP_DEPTH_IN / OVERALL_DEPTH_IN / 2
    bottom_rx = width * BASIN_BOTTOM_WIDTH_IN / OVERALL_WIDTH_IN / 2
    bottom_ry = depth * BASIN_BOTTOM_DEPTH_IN / OVERALL_DEPTH_IN / 2
    rings = [
        _ring(bottom_rx, bottom_ry, bottom_z),
        _ring(top_rx, top_ry, height),
        _ring(width / 2, depth / 2, height, True),
        _ring(width / 2, depth / 2, height - rim_t, True),
        _ring(top_rx + thickness, top_ry + thickness, height - rim_t),
        _ring(bottom_rx + thickness, bottom_ry + thickness,
              0.0),
    ]
    parts = [_band(a, b, index in (0, 4))
             for index, (a, b) in enumerate(zip(rings[:-1], rings[1:], strict=True))]
    for ring, upward in ((rings[0], True), (rings[-1], False)):
        vertices = ring + [(0.0, 0.0, ring[0][2])]
        triangles = [(SEGMENTS, index, (index + 1) % SEGMENTS) for index in range(SEGMENTS)]
        if not upward:
            triangles = [(a, c, b) for a, b, c in triangles]
        parts.append(mesh_part(vertices, triangles, "porcelain"))
    # One closed shell part: individual rim surfaces have zero thickness by themselves.
    vertices, triangles, normals = [], [], []
    for part in parts:
        mesh = part["mesh"]
        offset = len(vertices)
        vertices.extend(mesh["positions"])
        normals.extend(mesh["normals"])
        triangles.extend(tuple(offset+i for i in triangle) for triangle in mesh["triangles"])
    bounds = [(min(p[i] for p in vertices), max(p[i] for p in vertices)) for i in range(3)]
    shell = {"center": tuple((lo+hi)/2 for lo, hi in bounds),
             "size": tuple(hi-lo for lo, hi in bounds), "color": "porcelain",
             "points": (), "shape": "mesh",
             "mesh": {"positions": tuple(vertices), "triangles": tuple(triangles),
                      "normals": tuple(normals)}}
    parts = [shell]
    drain_radius = width * DRAIN_RADIUS_IN / OVERALL_WIDTH_IN
    drain_points = [(drain_radius * cos(2*pi*i/DRAIN_SEGMENTS),
                     drain_radius * sin(2*pi*i/DRAIN_SEGMENTS)) for i in range(DRAIN_SEGMENTS)]
    drain_vertices = [(x, y, z) for z in (bottom_z, bottom_z+thickness/4)
                      for x, y in drain_points]
    drain_triangles = []
    for index in range(DRAIN_SEGMENTS):
        following = (index+1) % DRAIN_SEGMENTS
        drain_triangles.extend(((index, following, following+DRAIN_SEGMENTS),
                                (index, following+DRAIN_SEGMENTS, index+DRAIN_SEGMENTS)))
    for index in range(1, DRAIN_SEGMENTS-1):
        drain_triangles.extend(((0, index+1, index),
                                (DRAIN_SEGMENTS, DRAIN_SEGMENTS+index,
                                 DRAIN_SEGMENTS+index+1)))
    parts.append(mesh_part(drain_vertices, drain_triangles, "metal"))
    overflow_z = height * (1 - OVERFLOW_BELOW_RIM_IN / OVERALL_HEIGHT_IN)
    fraction = (overflow_z - bottom_z) / (height - bottom_z)
    overflow_y = bottom_ry + fraction * (top_ry - bottom_ry)
    parts.append(box(0, overflow_y - thickness / 4, overflow_z,
                     overflow_z + thickness, width * OVERFLOW_WIDTH_IN / OVERALL_WIDTH_IN,
                     thickness / 2, "metal"))
    strokes = (rect(0, 0, width, depth, fill="porcelain"),
               ellipse(0, 0, top_rx, top_ry, weight=DETAIL_WEIGHT),
               circle(0, 0, drain_radius, weight=DETAIL_WEIGHT))
    return strokes, tuple(parts)
