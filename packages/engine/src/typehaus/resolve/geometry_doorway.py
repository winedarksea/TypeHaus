"""Sweep the exact sourced section along its documented doorway span."""
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_ir import GPart, GSweep, PartCatalogRef


def doorway_parts(wall, opening):
    assembly = opening.doorway
    if assembly is None:
        return ()
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)
    result = []
    for component in assembly.components:
        spec = component.specification
        along = component.along_m - component.span_m / 2
        for part in spec.parts:
            profile = tuple((
                center[0] + tangent[0] * along
                + normal[0] * (component.normal_m + spec.positive_normal_sign * x),
                center[1] + tangent[1] * along
                + normal[1] * (component.normal_m + spec.positive_normal_sign * x),
                component.base_z_m + z) for x, z in part.polygon_m)
            result.append(GPart(
                key=f"doorway:{spec.role}:{part.name}", material_key=part.material_key,
                solids=(GSweep(profile, (tangent[0] * component.span_m,
                                         tangent[1] * component.span_m, 0.0)),),
                catalog=PartCatalogRef(material_ref=part.material_ref, role=spec.role,
                                       name=spec.product_ref)))
    return tuple(result)
