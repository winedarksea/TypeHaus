"""IFC tessellation of shared box/mesh parts, without re-measuring their geometry."""

from typehaus.model.placeable_symbols import PART_COLORS, place_local
from typehaus.triangulation import planar_ring_triangles

BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))


def parts_representation(f, body, parts, center, rotation, z_base):
    items = []
    for part in parts:
        if "mesh" in part:
            vertices, triangles = part["mesh"]["positions"], part["mesh"]["triangles"]
        elif part.get("points"):
            z0 = part["center"][2] - part["size"][2] / 2
            z1 = z0 + part["size"][2]
            ring = part["points"]
            count = len(ring)
            vertices = tuple((x, y, z) for z in (z0, z1) for x, y in ring)
            cap = planar_ring_triangles(vertices[:count])
            triangles = [*(tuple(reversed(t)) for t in cap),
                         *(tuple(i + count for i in t) for t in cap)]
            for i in range(count):
                following = (i + 1) % count
                triangles.extend(((i, following, following + count),
                                  (i, following + count, i + count)))
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
        item = f.create_entity("IfcTriangulatedFaceSet", Coordinates=points, Closed=True,
                               CoordIndex=tuple(tuple(i + 1 for i in t) for t in triangles))
        color = PART_COLORS[part["color"]]
        rgb = f.createIfcColourRgb(None, *color[:3])
        shading = f.create_entity("IfcSurfaceStyleShading", SurfaceColour=rgb,
                                  Transparency=1 - color[3])
        style = f.create_entity("IfcSurfaceStyle", Name=part["color"], Side="BOTH",
                                Styles=[shading])
        f.create_entity("IfcStyledItem", Item=item, Styles=[style])
        items.append(item)
    return f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                           RepresentationIdentifier="Body", RepresentationType="Tessellation",
                           Items=items)
