"""Cased swing and pocket shapes. Mirrors ui/three/builders/casedDoors.ts."""
from __future__ import annotations

from typehaus.resolve.geometry_door_products import hardware_part, lever_solids
from typehaus.resolve.geometry_ir import GPart
from typehaus.resolve.model_door_products import CasedDoorSpec


def cased_door_parts(box, spec: CasedDoorSpec, hinge: float, swing: float):
    s = spec
    lo, hi = s.finish_faces_m
    inner = s.width_m / 2 - s.jamb_allowance_m
    jamb, head = s.jamb_thickness_m, s.head_z_m - s.jamb_allowance_m
    height, base = head - s.base_z_m, s.base_z_m
    pocket = s.operation == "pocket"
    slot = s.leaf_thickness_m + 2 * s.pocket_slot_gap_m
    liners = []

    def liner(side, normal_lo, normal_hi):
        if normal_hi <= normal_lo:
            return
        liners.append(box(jamb, height, normal_hi - normal_lo,
                          side * (inner + jamb / 2), base + height / 2,
                          (normal_hi + normal_lo) / 2))

    for side in (-1, 1):
        if pocket and side == s.pocket_sign:
            liner(side, lo, -slot / 2)
            liner(side, slot / 2, hi)
        else:
            liner(side, lo, hi)
    head_ranges = ((lo, -slot / 2), (slot / 2, hi)) if pocket else ((lo, hi),)
    for n0, n1 in head_ranges:
        if n1 > n0:
            head_cover = s.track_height_m if pocket else 0.0
            liners.append(box(2 * inner, jamb + head_cover, n1 - n0, 0,
                              head + (jamb - head_cover) / 2, (n0 + n1) / 2))
    parts = [GPart(key="jamb_liner", material_key="door_frame", solids=tuple(liners))]
    leaf_width = s.leaf_width_m or 2 * (inner - s.leaf_gap_m)
    # A pocket leaf closes on the latch jamb and runs on into its slot; a swing is centred.
    leaf_along = (s.pocket_sign * (leaf_width / 2 - (inner - s.leaf_gap_m)) if pocket else 0)
    parts.append(GPart(key="leaf", material_key="door_leaf", solids=(
        box(leaf_width, s.leaf_top_z_m - s.leaf_bottom_z_m, s.leaf_thickness_m,
            leaf_along, (s.leaf_top_z_m + s.leaf_bottom_z_m) / 2, s.leaf_normal_m),)))
    if pocket:
        parts.append(GPart(key="pocket_track", material_key="door_hardware", solids=(
            box(2 * inner, s.track_height_m, s.track_depth_m, 0,
                head - s.track_height_m / 2, 0),)))
    else:
        # Applied stops sit behind the closed leaf, touching its push face.
        stop_normal = s.leaf_normal_m - swing * (s.leaf_thickness_m + s.stop_depth_m) / 2
        projection = s.stop_projection_m
        stops = [box(projection, height, s.stop_depth_m, side * (inner - projection / 2),
                     base + height / 2, stop_normal) for side in (-1, 1)]
        stops.append(box(2 * (inner - projection), projection, s.stop_depth_m, 0,
                         head - projection / 2, stop_normal))
        parts.append(GPart(key="stop", material_key="door_frame", solids=tuple(stops)))
        hardware = hardware_part(lever_solids(
            box, -hinge * leaf_width / 2, hinge,
            (s.leaf_normal_m - s.leaf_thickness_m / 2,
             s.leaf_normal_m + s.leaf_thickness_m / 2), max(s.finished_floor_z_m)))
        if hardware:
            parts.append(hardware)
    return tuple(parts)
