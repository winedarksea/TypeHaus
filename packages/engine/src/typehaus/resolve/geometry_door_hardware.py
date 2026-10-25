"""Schematic authored door hardware in the shared geometry IR.

These envelopes locate components; shop drawings still govern drilling and keeps.
"""
from dataclasses import dataclass, replace

from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import lever_solids
from typehaus.resolve.geometry_ir import GPart, GPrism, PartCatalogRef


@dataclass(frozen=True)
class HardwareGeometryDimensions:
    backset_m: float = .060325
    leaf_thickness_m: float = .04445
    deadbolt_width_m: float = .0762
    deadbolt_height_m: float = .1397
    deadbolt_depth_m: float = .032
    viewer_size_m: float = .060325
    viewer_depth_m: float = .0127
    hinge_width_m: float = .0254
    hinge_height_m: float = .1016
    plate_width_m: float = .028575
    plate_depth_m: float = .004
    fastener_size_m: float = .006
    jamb_allowance_m: float = .0254


HARDWARE_DIMENSIONS = HardwareGeometryDimensions()


def authored_door_parts(wall, opening, parts, hardware, field_finish, operation):
    from typehaus.resolve.geometry_openings import _exterior_face

    dimensions = HARDWARE_DIMENSIONS
    origin, tangent, normal, _run = wall_frame(wall)
    placement = opening.doorway.exterior_placement if opening.doorway else None
    center_normal = placement.leaf_normal_m if placement else 0.0
    leaves = [solid for part in parts if part.key == "leaf" for solid in part.solids
              if isinstance(solid, GPrism)]
    face_offsets = [sum((point[i]-origin[i])*normal[i] for i in (0, 1))
                    for solid in leaves for point in solid.ring]
    if face_offsets:
        center_normal = (min(face_offsets) + max(face_offsets))/2
        leaf_thickness = max(face_offsets) - min(face_offsets)
    else:
        leaf_thickness = dimensions.leaf_thickness_m
    bottom = min((solid.z0_m for solid in leaves),
                 default=wall.base_ref_z_m + opening.sill_m)
    top = max((solid.z1_m for solid in leaves), default=bottom + opening.height_m)
    hinge_sign = -1 if opening.flip_hinge else 1

    def box(width, height, depth, along, z, offset=0):
        station = opening.center_along_m + along
        cx = origin[0] + tangent[0] * station + normal[0] * (center_normal + offset)
        cy = origin[1] + tangent[1] * station + normal[1] * (center_normal + offset)
        return GPrism(tuple((cx + tangent[0] * a + normal[0] * n,
                             cy + tangent[1] * a + normal[1] * n)
                            for a, n in ((width/2, depth/2), (-width/2, depth/2),
                                         (-width/2, -depth/2), (width/2, -depth/2))),
                      z - height/2, z + height/2)

    if hardware:
        parts = tuple(part for part in parts if part.key != "hardware")
        leaf_stations = [sum((point[i]-origin[i])*tangent[i] for i in (0, 1))
                         - opening.center_along_m for solid in leaves for point in solid.ring]
        leaf_edge = max((abs(station) for station in leaf_stations),
                        default=opening.width_m / 2 - dimensions.jamb_allowance_m)
        double = str(getattr(operation, "value", operation)) == "double_swing"
        latch = 0.0 if double else -hinge_sign * leaf_edge
        for index, item in enumerate(hardware):
            z = bottom + item.height.meters if item.height else (bottom + top) / 2
            solids = []
            if item.role == "passage":
                solids = lever_solids(box, latch, hinge_sign,
                    (-leaf_thickness/2, leaf_thickness/2),
                    bottom, item.height.meters if item.height else None)
            elif item.role in {"deadbolt", "viewer"}:
                viewer = item.role == "viewer"
                width = dimensions.viewer_size_m if viewer else dimensions.deadbolt_width_m
                height = width if viewer else dimensions.deadbolt_height_m
                depth = dimensions.viewer_depth_m if viewer else dimensions.deadbolt_depth_m
                along = 0 if viewer else latch + hinge_sign * dimensions.backset_m
                solids = [box(width, height, depth, along, z,
                              side * (leaf_thickness + depth)/2)
                          for side in (-1, 1)]
            elif item.role == "hinge":
                signs = (-1, 1) if item.quantity > 1 else (hinge_sign,)
                solids = [box(dimensions.hinge_width_m, dimensions.hinge_height_m,
                              dimensions.hinge_width_m, sign * leaf_edge, z) for sign in signs]
            elif item.role == "astragal":
                solids = [box(dimensions.plate_width_m, top-bottom,
                              leaf_thickness, 0, z)]
            elif item.role in {"strike_reinforcement", "multipoint"}:
                solids = [box(dimensions.plate_width_m,
                              dimensions.hinge_height_m if item.height else top-bottom,
                              dimensions.plate_depth_m, latch, z)]
            elif item.role == "fastener":
                solids = [box(dimensions.fastener_size_m, dimensions.fastener_size_m,
                              dimensions.fastener_size_m, hinge_sign * leaf_edge, top)]
            parts += (GPart(key=f"hardware:{index}", material_key="door_hardware",
                            solids=tuple(solids), catalog=PartCatalogRef(
                                role=item.role, name=item.product_ref)),)
    if field_finish:
        exterior = _exterior_face(wall)
        exterior_sign = exterior[1] if exterior else 1
        painted = []
        for part in parts:
            if (part.key not in {"leaf", "frame", "jamb_liner", "stop"}
                    or part.material_key == "glass"):
                painted.append(part)
                continue
            for face, material in zip((exterior_sign, -exterior_sign), field_finish, strict=True):
                solids = []
                for solid in part.solids:
                    offsets = [sum((point[i]-origin[i])*normal[i] for i in (0, 1))
                               for point in solid.ring]
                    mid = (min(offsets)+max(offsets))/2
                    ring = tuple((point[0] + normal[0]*(max(offset, mid)-offset if face > 0
                                                       else min(offset, mid)-offset),
                                  point[1] + normal[1]*(max(offset, mid)-offset if face > 0
                                                       else min(offset, mid)-offset))
                                 for point, offset in zip(solid.ring, offsets, strict=True))
                    solids.append(replace(solid, ring=ring))
                suffix = ":exterior" if face == exterior_sign else ":interior"
                painted.append(replace(part, key=part.key + suffix, solids=tuple(solids),
                    catalog=PartCatalogRef(material_ref=material, role=part.key)))
        parts = tuple(painted)
    return parts
