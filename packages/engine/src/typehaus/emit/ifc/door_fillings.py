"""Door fillings reuse resolved IR parts and style each swept solid."""
import math

from typehaus.emit.door_surfaces import door_part_color, door_part_surface
from typehaus.emit.gltf.palette import authored_colors
from typehaus.emit.ifc import lowlevel as ll
from typehaus.resolve.geometry_ir import GSweep


def cased_door_representation(f, body, model, opening, *, parts=None):
    geometry = model.geometry.by_uid(opening.uid)
    colors = authored_colors(model)
    solids = []
    for part in (parts if parts is not None else
                 (part for part in geometry.parts if not part.key.startswith("hardware:"))):
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


def emit_door_hardware(f, body, model, opening, door_type, filling, storey, project_uuid):
    """One discrete accessory per authored item; all geometry shares the GLB parts."""
    from typehaus.model.ids import derive_guid

    accessories = []
    geometry = model.geometry.by_uid(opening.uid)
    for index, item in enumerate(door_type.hardware):
        part = next(part for part in geometry.parts if part.key == f"hardware:{index}")
        accessory = ll.create_entity(f, "IfcDiscreteAccessory",
                                     name=f"{opening.tag}: {item.product_ref}")
        accessory.GlobalId = derive_guid(project_uuid, f"{opening.uid}/hardware/{index}")
        representation = cased_door_representation(f, body, model, opening, parts=(part,))
        ll.assign_representation(f, accessory, representation)
        ll.assign_container(f, accessory, storey)
        ll.ensure_pset(f, accessory, "TypeHaus_DoorHardware", {
            "ProductRef": item.product_ref, "Role": item.role, "Quantity": item.quantity,
            "Installation": item.installation,
            **({"HeightAboveLeafBottom": item.height.meters} if item.height else {}),
        })
        accessories.append(accessory)
    if accessories:
        relationship = ll.create_entity(f, "IfcRelNests", name="Door hardware set")
        relationship.GlobalId = derive_guid(project_uuid, f"{opening.uid}/hardware")
        relationship.RelatingObject = filling
        relationship.RelatedObjects = accessories
