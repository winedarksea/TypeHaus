"""Closed horizontal sheet meshes with polygon openings, shared by equipment details."""

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import triangulate

from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.geometry_ir import GMesh


def panel(outer, holes, bottom, top):
    """Closed sheet extrusion with real openings, in metres."""
    polygon = Polygon(outer)
    for hole in holes:
        polygon = polygon.difference(Polygon(hole))
    if not polygon.is_valid or top <= bottom:
        raise ValueError("panel must have valid rings and positive thickness")
    if polygon.is_empty:
        return GMesh(positions=(), triangles=())
    if polygon.geom_type == "MultiPolygon":
        return combine_meshes(*(panel(tuple(p.exterior.coords)[:-1],
                                     tuple(tuple(r.coords)[:-1] for r in p.interiors),
                                     bottom, top) for p in polygon.geoms))
    polygon = orient(polygon, sign=1.0)
    positions, triangles = [], []
    for triangle in triangulate(polygon):
        if not polygon.covers(triangle):
            continue
        corners = tuple(orient(triangle, sign=1.0).exterior.coords)[:3]
        start = len(positions)
        positions.extend((x, y, z) for z in (bottom, top) for x, y in corners)
        triangles.extend(((start, start + 2, start + 1),
                          (start + 3, start + 4, start + 5)))
    for boundary in (polygon.exterior, *polygon.interiors):
        ring = tuple(boundary.coords)[:-1]
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            start = len(positions)
            positions.extend((x, y, z) for (x, y), z in
                             ((a, bottom), (b, bottom), (b, top), (a, top)))
            triangles.extend(((start, start + 1, start + 2),
                              (start, start + 2, start + 3)))
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))

