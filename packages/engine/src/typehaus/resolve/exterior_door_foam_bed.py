"""A foam-bed tread's water path, measured off its resolved neighbours.

The water sheet runs back under the pan, which laps over it, and stops at the tread's outer
face; the slot between that face and the next solid drops into an isolation joint whose
board is replaced across the reveal by a drainage board down to a stone bed. The box sides'
sealant joint to separately supported masonry is graded against the reserved movement.
"""

from dataclasses import replace

from shapely.geometry import Polygon, box

from typehaus.resolve.exterior_door_sections import DoorSectionBuilder
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_slice import CutPlane, slice_solid
from typehaus.resolve.geometry_walls import layer_solids

_IN = 0.0254
_TOL = _IN / 32
#: A drain board's foot this close to a stone bed, in plan and in elevation, lets go into it.
_BED_REACH = 0.5 * _IN


def foam_bed_water_path(model, wall, opening, placement, layout):
    """``(sections, conflicts, unknown, report)`` for one foam-bed installation."""
    spec = placement.specification.catalog_installation
    installation = placement.specification
    sign = placement.outward_sign
    builder = DoorSectionBuilder(sign, layout.width)
    conflicts, unknown, report = [], [], {}
    sheet = spec.apron_material_ref or spec.pan_material_ref

    # The lap: the sheet's back edge runs under the pan on the seat, and the pan's drop at the
    # seat's outer edge comes down over the sheet's top. Water on the pan never meets an edge.
    lap_back = layout.end - spec.sheet_lap_under_pan.meters
    if lap_back < layout.start - _TOL:
        conflicts.append("the pan seat is shallower than the water sheet's lap under it")
    builder.rectangle("water-sheet-lap-under-pan", max(lap_back, layout.start), layout.end,
                      layout.base, layout.base + layout.membrane, sheet, "membrane")
    sheet_top = layout.apron_back + layout.membrane
    drop_bottom = layout.apron_back
    if drop_bottom > sheet_top + _TOL:
        conflicts.append("the pan's outlet drop stops above the water sheet: not shingled")
    report["sheet_lap_under_pan_in"] = (layout.end - max(lap_back, layout.start)) / _IN

    if spec.joint_drain_wall_ref:
        _joint_drain(model, wall, opening, spec, layout, builder, conflicts, report)
    else:
        unknown.append("foam-bed tread: the drain slot names no outlet")

    if installation.exterior_return_to_reveal_back:
        needed = spec.movement_horizontal.meters / spec.box_side_sealant_class
        report["box_side_joint_in"] = spec.box_side_joint_width.meters / _IN
        report["box_side_joint_required_in"] = needed / _IN
        if spec.box_side_sealant_ref is None:
            unknown.append("box sides meet the masonry with no sealant joint specified")
        elif spec.box_side_joint_width.meters < needed - _TOL:
            conflicts.append(
                f"box-side sealant joint {spec.box_side_joint_width.meters / _IN:.3f}\" cannot "
                f"take the reserved movement: needs {needed / _IN:.3f}\" at its class")
    unknown.append("foam-bed tread: the PVC sheet, drainage board and sealant are specified "
                   "by performance; product compatibility with the pan, Trex and brick is a "
                   "supplier hold")
    return tuple(builder.sections), conflicts, unknown, report


def _joint_drain(model, wall, opening, spec, layout, builder, conflicts, report):
    joint_wall = model.wall(spec.joint_drain_wall_ref)
    bed = next((b for b in model.footing_beddings if b.tag == spec.joint_drain_bed_ref), None)
    if joint_wall is None or bed is None:
        conflicts.append("joint drain wall or stone bed does not resolve")
        return
    sign = builder.outward_sign
    to_local, to_plan = _frame(wall, opening)
    faces = _layer_bounds(joint_wall, to_local)
    structure = [b for function, b in faces if function == "structure"]
    joints = [b for function, b in faces if function not in ("structure", "airgap", "finish")]
    if not structure or not joints:
        conflicts.append(f"{joint_wall.tag} has no isolation joint at the door")
        return
    # Layout depth is outward-positive: local = sign * layout.
    face = min(sign * x for b in structure for x in (b[0], b[2]))
    slot = face - layout.outlet
    report["drain_slot_in"] = slot / _IN
    if slot < spec.minimum_drainage_clearance.meters - _TOL:
        conflicts.append(f"tread drain slot {slot / _IN:.3f}\" is under the minimum clearance")
    ranges = [tuple(sorted(sign * x for x in (b[0], b[2]))) for b in joints]
    x0, x1 = max(ranges, key=lambda r: min(r[1], face) - max(r[0], layout.outlet))
    if min(x1, face) - max(x0, layout.outlet) < spec.minimum_drainage_clearance.meters - _TOL:
        conflicts.append("the drain slot does not open onto the isolation joint")
    # From the bed course's underside, which the slot drops onto, to the joint's foot, and
    # along the reveal short of any isolation board already filling the joint lower down.
    top = layout.pan_front + spec.bearing_plate_thickness.meters - spec.foam_course_depth.meters
    lo, hi = _clear_span(model, to_local, sign, (x0, x1), (joint_wall.z0_m, top),
                         layout.width / 2)
    builder.rectangle("joint-drain", x0, x1, joint_wall.z0_m, top,
                      spec.joint_drain_material_ref, "rigid", span=hi - lo, along=(lo + hi) / 2)
    report["joint_drain_length_in"] = (hi - lo) / _IN
    foot = Polygon([to_plan(sign * x, a) for x, a in ((x0, lo), (x1, lo), (x1, hi), (x0, hi))])
    reach = foot.distance(Polygon(bed.outline))
    drop = joint_wall.z0_m - bed.z1_m
    report.update(joint_drain_bed=bed.tag, joint_drain_bed_gap_in=reach / _IN,
                  joint_drain_foot_above_bed_in=drop / _IN,
                  joint_drain_depth_in=(top - joint_wall.z0_m) / _IN)
    if reach > _BED_REACH or abs(drop) > _BED_REACH:
        conflicts.append(f"joint drain does not reach {bed.tag}'s stone")


def _clear_span(model, to_local, sign, depths, heights, half):
    """``(lo, hi)`` along the reveal, stopped short of thermal-break boards in the joint."""
    lo, hi = -half, half
    for solid in model.solids:
        if solid.category != "thermal_break" or not solid.outline or \
                solid.z1_m <= heights[0] or solid.z0_m >= heights[1]:
            continue
        local = [to_local(p) for p in solid.outline]
        d0, d1 = sorted(sign * d for d, _ in local)[::len(local) - 1]
        a0, a1 = min(a for _, a in local), max(a for _, a in local)
        if d1 <= depths[0] or d0 >= depths[1] or a1 <= lo or a0 >= hi:
            continue
        if a0 > 0:
            hi = min(hi, a0)
        else:
            lo = max(lo, a1)
    return lo, hi


def _frame(wall, opening):
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)

    def to_local(point):
        delta = (point[0] - center[0], point[1] - center[1])
        return (delta[0] * normal[0] + delta[1] * normal[1],
                delta[0] * tangent[0] + delta[1] * tangent[1])

    def to_plan(depth, along):
        return (center[0] + normal[0] * depth + tangent[0] * along,
                center[1] + normal[1] * depth + tangent[1] * along)

    return to_local, to_plan


def _layer_bounds(target, to_local):
    """``(function, (d0, z0, d1, z1))`` of each layer of ``target`` cut at the door's centre."""
    from typehaus.resolve.geometry_ir import GMesh, GPrism

    out = []
    for layer in target.body_layers():
        if layer.thickness_m <= 0:
            continue
        for solid in layer_solids(target, layer.polygon, [], layer_name=layer.name):
            if not isinstance(solid, (GMesh, GPrism)):
                continue
            moved = (replace(solid, positions=tuple((*to_local(p), p[2]) for p in solid.positions))
                     if isinstance(solid, GMesh) else
                     replace(solid, ring=tuple(to_local(p) for p in solid.ring),
                             voids=tuple(tuple(to_local(p) for p in r) for r in solid.voids)))
            for profile in slice_solid(moved, CutPlane("x", 0.0)):
                bounds = Polygon(profile.outline, profile.voids).bounds
                if not box(*bounds).is_empty:
                    out.append((layer.function, bounds))
    return out
