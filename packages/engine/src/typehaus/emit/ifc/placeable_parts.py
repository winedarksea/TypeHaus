"""IFC tessellation of shared box/mesh parts, without re-measuring their geometry."""

from typehaus.model.canvas import MATERIAL_COLOR_ROLES
from typehaus.model.placeable_symbols import PART_COLORS, place_local
from typehaus.triangulation import planar_ring_triangles

BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))


def device_parts(product_type):
    """Generated parts for devices that opt into IFC tessellation."""
    from typehaus.model.canvas import model_symbol_for
    from typehaus.model.placeable_symbols import model_parts
    from typehaus.model.placeable_symbols._leviton_9726_c import LEVITON_9726_C_SYMBOL
    from typehaus.model.placeable_symbols._leviton_9880 import LEVITON_9880_SYMBOL
    from typehaus.model.placeable_symbols._unifi_access_point import UNIFI_ACCESS_POINT_SYMBOLS
    from typehaus.model.placeable_symbols.receptacles import RECEPTACLE_SYMBOLS
    from typehaus.model.placeable_symbols.switches import SWITCH_SYMBOLS

    symbol = model_symbol_for(product_type)
    explicit_symbol = getattr(getattr(product_type, "model_representation", None), "symbol", None)
    if (getattr(product_type, "plan_symbol", None) in {"flood-light", "recessed-can"}
            or symbol in {LEVITON_9726_C_SYMBOL, LEVITON_9880_SYMBOL}
            or explicit_symbol in RECEPTACLE_SYMBOLS or explicit_symbol in SWITCH_SYMBOLS
            or explicit_symbol in UNIFI_ACCESS_POINT_SYMBOLS):
        return model_parts(symbol, *(dimension.meters for dimension in product_type.footprint),
                           product_type.height.meters)
    return ()


def fixture_parts(product_type, tag: str, hosted_countertops) -> list | None:
    """A fixture's or appliance's generated parts as the emitter draws them, else None (a prism).

    One reader for the emitter and ``diff/ifc_bounds.py``, so the self-diff sees the same body.
    """
    from typehaus.emit.ifc.architectural import is_parts_fixture
    from typehaus.model.canvas import model_symbol_for
    from typehaus.model.placeable_symbols import model_parts
    from typehaus.model.placeable_symbols._frame import is_counter_part

    symbol = model_symbol_for(product_type)
    shower = getattr(product_type, "shower_assembly", None)
    if not is_parts_fixture(symbol) and shower is None:
        return None
    representation = product_type.model_representation
    return [part for part in model_parts(
        symbol, product_type.footprint[0].meters, product_type.footprint[1].meters,
        product_type.height.meters, shower_assembly=shower,
        material_refs=representation.material_refs if representation else None)
        # A vanity under a countertop slab: the slab draws its deck (→ millwork).
        if tag not in hosted_countertops or not is_counter_part(part)]


def parts_representation(f, body, parts, center, rotation, z_base, *, materials=None, frame=None):
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
        xy = place_local([(x, y) for x, y, _ in vertices], (0.0, 0.0) if frame else center,
                         rotation)
        placed = tuple((x, y, vertex[2]) for (x, y), vertex in zip(xy, vertices, strict=True))
        points = f.createIfcCartesianPointList3D(
            tuple(frame.point(*point) for point in placed) if frame
            else tuple((x, y, z_base + z) for x, y, z in placed))
        item = f.create_entity("IfcTriangulatedFaceSet", Coordinates=points, Closed=True,
                               CoordIndex=tuple(tuple(i + 1 for i in t) for t in triangles))
        color = PART_COLORS[part["color"]]
        material = (materials or {}).get(part.get("material_ref"))
        if part["color"] in {"faucet", *MATERIAL_COLOR_ROLES} and material and material.color:
            color = tuple(int(material.color[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)
        rgb = f.createIfcColourRgb(None, *color[:3])
        shading = f.create_entity("IfcSurfaceStyleShading", SurfaceColour=rgb,
                                  Transparency=1 - color[3])
        style = f.create_entity("IfcSurfaceStyle", Name=part.get("material_ref", part["color"]),
                                Side="BOTH", Styles=[shading])
        f.create_entity("IfcStyledItem", Item=item, Styles=[style])
        items.append(item)
    return f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                           RepresentationIdentifier="Body", RepresentationType="Tessellation",
                           Items=items)
