"""Cast surface bases, anchors and authored tread backing; shared posts emit once."""

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.railings.fascia_mesh import cylinder, pierced_plate
from typehaus.resolve.railings.mounting_solids import mounting_solid


def emit_surface_mounts(model, railing, storey, stations, parts, spec, shared):
    bearings = railing.surface_post_mounts
    if len(bearings) != len(stations):
        raise ValueError(f"{railing.tag}: surface_post_mounts must match all post stations")
    for index, (station, bearing) in enumerate(zip(stations, bearings, strict=True)):
        if index in shared:
            continue
        a, b = (stations[index:index+2] if index+1 < len(stations)
                else stations[index-1:index+1])
        run = math.dist(a, b)
        if run < 1e-9:
            raise ValueError(f"{railing.tag}: surface stations must be distinct")
        tangent = ((b[0]-a[0])/run, (b[1]-a[1])/run)
        across = (-tangent[1], tangent[0])
        origin = (*station, bearing.elevation.meters)
        half = spec.base_width.inches/2
        thickness = spec.display_base_thickness.inches
        spacing = spec.display_hole_spacing.inches/2
        wood = bearing.substrate == "wood"
        diameter = (spec.wood_screw_diameter if wood else spec.concrete_anchor_diameter).inches
        length = (spec.wood_screw_length if wood else spec.concrete_anchor_length).inches
        holes = [(x, y, diameter/2+0.01) for x in (-spacing, spacing)
                 for y in (-spacing, spacing)]
        # Rotate a pierced x/z plate into x/y; its lower face bears on the substrate.
        base = transform_mesh(pierced_plate(2*half, -half, half, thickness, holes),
                              origin_m=origin, x_axis=(*tangent, 0),
                              y_axis=(0, 0, 1), z_axis=(*across, 0))
        hardware = []
        for x, y, _radius in holes:
            hardware.append(transform_mesh(combine_meshes(
                cylinder(diameter/2, -length, 0),
                cylinder(spec.display_head_width.inches/math.sqrt(3), 0,
                         spec.display_head_height.inches, 6)),
                origin_m=(station[0]+(tangent[0]*x+across[0]*y)*M_PER_IN,
                          station[1]+(tangent[1]*x+across[1]*y)*M_PER_IN,
                          origin[2]+thickness*M_PER_IN),
                x_axis=(*tangent, 0), y_axis=(0, 0, 1), z_axis=(*across, 0)))
        mounting_solid(model, railing, storey, f"BASE{index+1}", base,
                       parts.post_material, spec.product)
        mounting_solid(model, railing, storey, f"ANCHORS{index+1}", combine_meshes(*hardware),
               parts.post_material)
        if bearing.backing_size is not None:
            if bearing.backing_offset is None or bearing.finish_thickness is None:
                raise ValueError(f"{railing.tag}: backing needs offset and finish thickness")
            along, width, depth = (v.inches for v in bearing.backing_size)
            offset = bearing.backing_offset
            backing = transform_mesh(box_mesh((-along/2, -width/2, -depth),
                                               (along/2, width/2, 0)),
                origin_m=(station[0]+offset[0].meters, station[1]+offset[1].meters,
                          origin[2]-bearing.finish_thickness.meters),
                x_axis=(*tangent, 0), y_axis=(*across, 0))
            mounting_solid(model, railing, storey, f"BACKING{index+1}", backing, "kdat")
