"""Door fillings reuse resolved IR parts and style each swept solid."""
import math

from typehaus.emit.door_surfaces import door_part_color, door_part_surface
from typehaus.emit.gltf.palette import authored_colors
from typehaus.emit.ifc import lowlevel as ll
from typehaus.resolve.geometry_ir import GSweep


def cased_door_representation(f, body, model, opening):
    geometry = model.geometry.by_uid(opening.uid)
    colors = authored_colors(model)
    solids = []
    for part in geometry.parts:
        representations = []
        for solid in part.solids:
            if isinstance(solid, GSweep):
                ex, ey, _ = solid.extrude
                depth = math.hypot(ex, ey)
                axis = (ex / depth, ey / depth, 0.0)
                ref = (-axis[1], axis[0], 0.0)
                origin = solid.profile[0]
                points = [((x - origin[0]) * ref[0] + (y - origin[1]) * ref[1],
                           z - origin[2]) for x, y, z in solid.profile]
                signed_area = sum(a[0] * b[1] - b[0] * a[1]
                                  for a, b in zip(points, points[1:] + points[:1], strict=True))
                if signed_area < 0:
                    points.reverse()
                representations.append(ll.add_swept_profile(
                    f, body, profile_points=points, origin_m=origin, axis=axis,
                    ref_direction=ref, depth_m=depth))
            else:
                representations.append(ll.add_prisms_at_elevations(
                    f, body, [(list(solid.ring), solid.z0_m, solid.z1_m)]))
        representation = f.createIfcShapeRepresentation(
            body, "Body", "SweptSolid", [item for r in representations for item in r.Items])
        for temporary in representations:
            f.remove(temporary)
        color = door_part_color(part, colors,
                                linear_paint_defaults=opening.cased_product is not None)
        # IFC surface colors are display RGB; undo glTF's linear-light encoding.
        def srgb(channel):
            return 12.92 * channel if channel <= 0.0031308 else 1.055 * channel ** (1 / 2.4) - 0.055
        rgb = f.createIfcColourRgb(None, *(srgb(c) for c in color[:3]))
        roughness, _metalness = door_part_surface(part)
        highlight = f.create_entity("IfcSpecularRoughness", roughness)
        render = f.create_entity("IfcSurfaceStyleRendering", SurfaceColour=rgb,
                                 Transparency=1 - color[3], ReflectanceMethod="NOTDEFINED",
                                 SpecularHighlight=highlight)
        style = f.create_entity("IfcSurfaceStyle", Name=part.catalog.material_ref
                                if part.catalog else part.material_key,
                                Side="BOTH", Styles=[render])
        for solid in representation.Items:
            f.create_entity("IfcStyledItem", Item=solid, Styles=[style], Name=part.key)
            solids.append(solid)
        f.remove(representation)
    return f.createIfcShapeRepresentation(body, "Body", "SweptSolid", solids)
