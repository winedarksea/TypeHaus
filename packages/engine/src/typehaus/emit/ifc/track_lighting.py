"""IFC tessellation from the same rail/head meshes used by the canvas and GLB."""

from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._track_lighting import track_geometry

BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))


def track_representation(f, body, spec, center, rotation, z_base):
    _, parts = track_geometry(spec)
    items = []
    for part in parts:
        if "mesh" in part:
            vertices, triangles = part["mesh"]["positions"], part["mesh"]["triangles"]
        else:
            cx, cy, cz = part["center"]
            sx, sy, sz = part["size"]
            vertices = tuple((cx + x * sx / 2, cy + y * sy / 2, cz + z * sz / 2)
                             for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1),
                                            (-1, 1, -1), (-1, -1, 1), (1, -1, 1),
                                            (1, 1, 1), (-1, 1, 1)))
            triangles = BOX_TRIANGLES
        xy = place_local([(x, y) for x, y, _ in vertices], center, rotation)
        points = f.createIfcCartesianPointList3D(tuple(
            (x, y, z_base + vertex[2]) for (x, y), vertex in zip(xy, vertices, strict=True)))
        items.append(f.create_entity("IfcTriangulatedFaceSet", Coordinates=points, Closed=True,
                                     CoordIndex=tuple(tuple(i + 1 for i in t) for t in triangles)))
    return f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                           RepresentationIdentifier="Body", RepresentationType="Tessellation",
                           Items=items)
