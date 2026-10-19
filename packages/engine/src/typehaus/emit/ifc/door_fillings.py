"""Door fillings reuse resolved IR parts and style each swept solid."""
from typehaus.emit.door_surfaces import door_part_color, door_part_surface
from typehaus.emit.gltf.palette import authored_colors
from typehaus.emit.ifc import lowlevel as ll


def cased_door_representation(f, body, model, opening):
    geometry = model.geometry.by_uid(opening.uid)
    colors = authored_colors(model)
    solids = []
    for part in geometry.parts:
        representation = ll.add_prisms_at_elevations(f, body, [
            (list(solid.ring), solid.z0_m, solid.z1_m) for solid in part.solids])
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
