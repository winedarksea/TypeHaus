"""Fabricated plenums: six sheet faces cut by the type's declared air openings.

Stations are design coordinates, not evidence of manufacturer or fabricator approval.
The same port list drives the shell and coordination metadata in every renderer.
"""

import math

import shapely
from shapely.geometry import Polygon
from shapely.geometry import box as rectangle
from shapely.geometry.polygon import orient

from typehaus.model.placeable_symbols._frame import rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.quantities import M_PER_IN
from typehaus.resolve.overlay import union_all

SHEET_THICKNESS_M = 0.019 * M_PER_IN  # nominal 26 ga galvanized, visual sheet thickness
ROUND_OPENING_SEGMENTS = 32
FACE_TOLERANCE_M = 1e-7


def sheet_metal_plenum(width, depth, height):
    return (rect(0, 0, width, depth),), plenum_parts(width, depth, height, ())


def _triangles(polygon):
    if hasattr(shapely, "constrained_delaunay_triangles"):
        return shapely.constrained_delaunay_triangles(polygon).geoms
    # Pyodide's Shapely 2.0: unconstrained Delaunay, kept where it lies in the sheet
    from shapely.ops import triangulate
    return [t for t in triangulate(polygon) if polygon.contains(t.representative_point())]


def _sheet_part(polygon, axis, station, thickness):
    """Extrude a polygon with holes into a closed sheet, in any principal plane."""
    polygon = orient(polygon)
    vertices, triangles = [], []

    def vertex(u, v, offset):
        point = [u, v]
        point.insert(axis, station + offset)
        vertices.append(tuple(point))
        return len(vertices) - 1

    for triangle in _triangles(polygon):
        coords = list(orient(triangle).exterior.coords)[:3]
        for offset, reverse in ((0, True), (thickness, False)):
            indices = [vertex(u, v, offset) for u, v in coords]
            triangles.append(tuple(reversed(indices)) if reverse else tuple(indices))
    for ring in (polygon.exterior, *polygon.interiors):
        for (u0, v0), (u1, v1) in zip(ring.coords[:-1], ring.coords[1:], strict=True):
            a, b = vertex(u0, v0, 0), vertex(u1, v1, 0)
            c, d = vertex(u1, v1, thickness), vertex(u0, v0, thickness)
            triangles.extend(((a, b, c), (a, c, d)))
    part = mesh_part(vertices, outward(vertices, triangles), "metal")
    part["role"] = "plenum:sheet"
    return part


def plenum_parts(width, depth, height, ports):
    if min(width, depth, height) <= 0:
        return ()
    bounds = ((-width / 2, width / 2), (-depth / 2, depth / 2), (0, height))
    openings = {}
    for port in ports:
        if port.service.value not in ("supply_air", "return_air", "exhaust_air", "outdoor_air"):
            continue
        if port.direction is None:
            raise ValueError(f"Plenum opening {port.tag} needs a face direction")
        axis = max(range(3), key=lambda index: abs(port.direction[index]))
        if (abs(abs(port.direction[axis]) - 1) > FACE_TOLERANCE_M
                or any(abs(value) > FACE_TOLERANCE_M for index, value in enumerate(
                    port.direction) if index != axis)):
            raise ValueError(f"Plenum opening {port.tag} must be normal to a sheet face")
        side = int(port.direction[axis] > 0)
        position = tuple(value.meters for value in port.position)
        if abs(position[axis] - bounds[axis][side]) > FACE_TOLERANCE_M:
            raise ValueError(f"Plenum opening {port.tag} is not on its declared face")
        u, v = (position[index] for index in range(3) if index != axis)
        if port.connection_size is not None:
            radius = port.connection_size.meters / 2
            opening = Polygon([(u + radius * math.cos(2 * math.pi * i / ROUND_OPENING_SEGMENTS),
                                v + radius * math.sin(2 * math.pi * i / ROUND_OPENING_SEGMENTS))
                               for i in range(ROUND_OPENING_SEGMENTS)])
        elif port.width is not None and port.depth is not None:
            half_width, half_depth = port.width.meters / 2, port.depth.meters / 2
            opening = rectangle(u - half_width, v - half_depth, u + half_width, v + half_depth)
        else:
            raise ValueError(f"Plenum opening {port.tag} needs a section")
        openings.setdefault((axis, side), []).append(opening)
    parts = []
    for axis in range(3):
        (u0, u1), (v0, v1) = [bound for index, bound in enumerate(bounds) if index != axis]
        face = rectangle(u0, v0, u1, v1)
        for side in range(2):
            holes = union_all(openings.get((axis, side), []))
            if not holes.is_empty and not face.buffer(FACE_TOLERANCE_M).covers(holes):
                raise ValueError("Plenum opening extends beyond its sheet face")
            sheet = face.difference(holes)
            station = bounds[axis][side] - (SHEET_THICKNESS_M if side else 0)
            polygons = sheet.geoms if sheet.geom_type == "MultiPolygon" else (sheet,)
            parts.extend(_sheet_part(polygon, axis, station, SHEET_THICKNESS_M)
                         for polygon in polygons if not polygon.is_empty)
    return tuple(parts)
