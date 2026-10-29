"""Resolved cased door appearance within the existing modeled void.

Type dimensions still size the void, not a guaranteed nominal leaf/clear passage. These
schematic defaults do not specify purchased jamb stock or change framing quantities.
"""
from __future__ import annotations

from dataclasses import replace

from typehaus.model.enums import DoorOperation
from typehaus.model.millwork import TrimStandard
from typehaus.resolve.door_sizing import CASED_DOOR_DEFAULTS
from typehaus.resolve.geometry import opening_center, pocket_centerline_offset, wall_frame
from typehaus.resolve.geometry_door_products import finish_faces, handing
from typehaus.resolve.geometry_walls import is_raked, wall_top_at
from typehaus.resolve.model_door_products import CasedDoorSpec
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.resolve.room_lookup import room_owning


def resolve_cased_door(wall, opening, door_type, *, standard=None,
                       finished_floors=None) -> CasedDoorSpec | None:
    """Only floor-level, solid, cased interior swing/pocket products use this recipe."""
    defaults = CASED_DOOR_DEFAULTS
    if (opening.kind != "door" or door_type is None or door_type.exterior
            or door_type.glazed or door_type.trimless or door_type.bookcase_door is not None
            or door_type.operation not in (DoorOperation.SWING, DoorOperation.POCKET)
            or opening.sill_m > defaults.raised_sill_m):
        return None
    layers = wall.depth_layers()
    if layers and layers[-1].function.strip().lower() == "cladding":
        return None  # preserve the existing clad-wall exterior product path
    faces = finish_faces(wall)
    if faces is None:
        return None
    base = wall.base_ref_z_m + opening.sill_m
    floors = finished_floors or (base, base)
    if base - min(floors) > defaults.raised_sill_m:
        return None  # intentionally raised access hatch retains its sill
    center = opening_center(wall, opening)
    _, tangent, _, _ = wall_frame(wall)
    height = opening.height_m
    if is_raked(wall):
        height = min(height, *(wall_top_at(wall, center[0] + tangent[0] * along,
                                          center[1] + tangent[1] * along) - base
                               for along in (-opening.width_m / 2, opening.width_m / 2)))
    allowance = standard.jamb_allowance.meters if standard else defaults.jamb_allowance_m
    reveal = standard.reveal.meters if standard else defaults.casing_reveal_m
    jamb = min(defaults.jamb_thickness_m, allowance)
    pocket = door_type.operation == DoorOperation.POCKET
    offset = pocket_centerline_offset(wall) if pocket else 0.0
    faces = (faces[0] - offset, faces[1] - offset)
    _, swing = handing(opening)
    # Swing leaf closes near the pull face; pocket leaf stays on the structural cavity.
    leaf_normal = 0.0 if pocket else (
        faces[1] - defaults.leaf_thickness_m / 2 if swing > 0
        else faces[0] + defaults.leaf_thickness_m / 2)
    head = base + height
    bottom = max(base, *floors) + defaults.undercut_m
    top = head - allowance - defaults.leaf_gap_m - (defaults.track_height_m if pocket else 0)
    sizing = opening.sizing
    if sizing is not None and not sizing.held:
        # A kit's head allowance can exceed jamb + track; the leaf is still its own height.
        top = min(top, bottom + sizing.leaf_h_m)
    if top <= bottom or opening.width_m <= 2 * (allowance + defaults.leaf_gap_m):
        return None
    return CasedDoorSpec(
        operation=door_type.operation.value, width_m=opening.width_m,
        base_z_m=max(base, min(floors)),
        head_z_m=head, finished_floor_z_m=floors, finish_faces_m=faces,
        jamb_allowance_m=allowance, jamb_thickness_m=jamb, casing_reveal_m=reveal,
        leaf_gap_m=defaults.leaf_gap_m, leaf_thickness_m=defaults.leaf_thickness_m,
        leaf_bottom_z_m=bottom, leaf_top_z_m=top, leaf_normal_m=leaf_normal,
        stop_projection_m=defaults.stop_projection_m, stop_depth_m=defaults.stop_depth_m,
        undercut_m=defaults.undercut_m, pocket_slot_gap_m=defaults.pocket_slot_gap_m,
        track_height_m=defaults.track_height_m, track_depth_m=defaults.track_depth_m,
        pocket_sign=opening.pocket_sign or 1,
        leaf_width_m=opening.sizing.leaf_w_m if opening.sizing is not None else None,
        frame_material_ref=opening.effective_frame_material_ref,
        leaf_material_ref=opening.effective_leaf_material_ref)


def resolve_door_products(model) -> None:
    """Resolve after rooms/floor finishes, once for IR, model JSON and both exports."""
    types = {item.tag: item for item in model.plan.library.door_types}
    standards = [item for item in model.plan.all_elements() if isinstance(item, TrimStandard)]
    standard = standards[0] if len(standards) == 1 else None
    walls = {wall.tag: wall for wall in model.walls}
    resolved = []
    floor_cache = {}
    for opening in model.openings:
        product_type = types.get(opening.type_ref)
        if opening.kind != "door" or product_type is None:
            resolved.append(opening)
            continue
        authored = model.plan.by_tag(opening.tag)
        refs = {field: getattr(authored, field, None)
                for field in ("frame_material_ref", "leaf_material_ref")}
        refs.update({f"effective_{field}": value or getattr(product_type, field)
                     for field, value in tuple(refs.items())})
        wall = walls[opening.host_wall]
        origin, tangent, normal, _ = wall_frame(wall)
        faces = finish_faces(wall)
        floor_z = wall.base_ref_z_m + opening.sill_m
        floors = []
        for side, face in zip((-1, 1), faces or (0, 0), strict=True):
            point = (origin[0] + tangent[0] * opening.center_along_m
                     + normal[0] * (face + side * CASED_DOOR_DEFAULTS.room_probe_m),
                     origin[1] + tangent[1] * opening.center_along_m
                     + normal[1] * (face + side * CASED_DOOR_DEFAULTS.room_probe_m))
            room = room_owning(model, wall.storey, point)
            if room is not None:
                if room.tag not in floor_cache:
                    floor_cache[room.tag] = room_finished_floor_elevation(model, room)
                floors.append(floor_cache[room.tag])
            else:
                floors.append(floor_z)
        opening = replace(opening, **refs)
        spec = resolve_cased_door(wall, opening, product_type, standard=standard,
                                 finished_floors=tuple(floors))
        resolved.append(replace(opening, cased_product=spec))
    model.openings = resolved
