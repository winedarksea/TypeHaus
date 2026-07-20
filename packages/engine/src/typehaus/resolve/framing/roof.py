"""Deterministic gable/shed rafter layout from resolved roof planes (M3).

Also resolves an authored ridge :class:`Beam` (WP4): trims the rafter ridge ends
back by half the beam's width so they land on top of it rather than crossing to
the exact ridge centerline, and annotates rafters with their connection details
for the 2D detail pipeline to bind later (geometry stays a plain box — no seat
cuts here).
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConditionKind, LayerFunction
from typehaus.model.structure import Beam
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import BoundaryCondition, FramedMember, ResolvedModel, ResolvedRoof

_RAFTER_CONNECTION = "ridge:adjustable-slope-hanger;eave:birdsmouth-1.17in"


def frame_roofs(model: ResolvedModel) -> list[Finding]:
    """Attach roof-plane rafter members at the assembly's framing spacing."""
    findings: list[Finding] = []
    framed: list[ResolvedRoof] = []
    for roof in model.roofs:
        rafters = _roof_rafters(model, roof)
        beam_member, beam_findings = _resolve_ridge_beam(model, roof)
        findings.extend(beam_findings)
        if beam_member is not None:
            beam_width_m = cross_section(beam_member.profile).width_m
            rafters = tuple(_trim_rafter_to_beam(r, roof, beam_width_m) for r in rafters)
            model.conditions.append(_ridge_condition(roof, beam_member))
        rafters = tuple(replace(r, connection=_RAFTER_CONNECTION) for r in rafters)
        members = rafters + ((beam_member,) if beam_member is not None else ())
        framed.append(ResolvedRoof(
            uid=roof.uid, tag=roof.tag, storey=roof.storey, form=roof.form,
            footprint=roof.footprint, eave_z_m=roof.eave_z_m, ridge_z_m=roof.ridge_z_m,
            ridge_direction=roof.ridge_direction, assembly=roof.assembly,
            surface_area_m2=roof.surface_area_m2, members=members,
        ))
    model.roofs = framed
    return findings


def _roof_rafters(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return ()
    structure = next((layer for layer in assembly.layers
                      if layer.function is LayerFunction.STRUCTURE and layer.framing is not None), None)
    if structure is None or structure.framing is None:
        return ()
    spacing = (structure.framing.spacing or DEFAULT_SPACING).meters
    depth = structure.thickness.meters
    profile = structure.framing.member
    xs, ys = [point[0] for point in roof.footprint], [point[1] for point in roof.footprint]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    along_low, along_high = ((minx, maxx) if roof.ridge_direction == "x" else (miny, maxy))
    # Rafters repeat along the ridge and span perpendicular to it.
    count = int(round((along_high - along_low) / spacing))
    positions = [min(along_high, along_low + index * spacing) for index in range(count + 1)]
    if positions[-1] < along_high - 1e-9:
        positions.append(along_high)
    if roof.ridge_direction == "x":
        ridge = (miny + maxy) / 2
        halves = [half for value in positions for half in (
            ((value, miny), (value, ridge)), ((value, maxy), (value, ridge)),
        )]
    else:
        ridge = (minx + maxx) / 2
        halves = [half for value in positions for half in (
            ((minx, value), (ridge, value)), ((maxx, value), (ridge, value)),
        )]
    if roof.form == "shed":
        halves = halves[:len(positions)]
    members: list[FramedMember] = []
    rise = roof.ridge_z_m - roof.eave_z_m
    for index, (eave, ridge_point) in enumerate(halves):
        length = math.hypot(ridge_point[0] - eave[0], ridge_point[1] - eave[1], rise)
        members.append(FramedMember(
            roof.uid, f"rafter-{index:03d}", "rafter", profile, eave, ridge_point,
            roof.eave_z_m - depth, roof.eave_z_m, length,
            z0_end_m=roof.ridge_z_m - depth, z1_end_m=roof.ridge_z_m,
        ))
    return tuple(members)


def _find_ridge_beam(model: ResolvedModel, roof: ResolvedRoof) -> Beam | None:
    """An authored Beam whose node axis is coincident+parallel with the ridge line.

    Matches on the infinite line (constant x for a "y"-running ridge, constant y for
    an "x"-running ridge), not on endpoints — the beam need not span the full ridge.
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    axis = 1 if roof.ridge_direction == "x" else 0
    ridge_const = ((min(ys) + max(ys)) / 2 if axis == 1 else (min(xs) + max(xs)) / 2)
    nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(roof.storey)
             if e.element_kind == "Node"}
    for element in model.plan.storey_elements(roof.storey):
        if not isinstance(element, Beam):
            continue
        start, end = nodes.get(element.start_node), nodes.get(element.end_node)
        if start is None or end is None:
            continue
        if (abs(start[axis] - ridge_const) < 1e-6 and abs(end[axis] - ridge_const) < 1e-6):
            return element, start, end
    return None


def _resolve_ridge_beam(
    model: ResolvedModel, roof: ResolvedRoof
) -> tuple[FramedMember | None, list[Finding]]:
    found = _find_ridge_beam(model, roof)
    if found is None:
        if roof.form != "gable":
            return None, []
        return None, [Finding(
            severity=Severity.WARN, check_id="structural.ridge_support",
            message=f"roof {roof.tag} has no authored ridge Beam — the ridge line has "
                    "no modeled support member (advisory, not engineering)",
            element_tags=(roof.tag,), result=Result.UNKNOWN,
        )]
    beam, start, end = found
    depth = cross_section(beam.size).depth_m
    z1 = roof.ridge_z_m
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    member = FramedMember(
        beam.uid, "ridge-beam", "ridge_beam", beam.size, start, end, z1 - depth, z1, length,
    )
    return member, []


def _trim_rafter_to_beam(rafter: FramedMember, roof: ResolvedRoof, beam_width_m: float) -> FramedMember:
    """Pull the rafter's ridge end back by half the beam width, staying on the roof plane."""
    ex, ey = rafter.p0
    rx, ry = rafter.p1
    dx, dy = rx - ex, ry - ey
    horiz_run = math.hypot(dx, dy)
    trim = min(beam_width_m / 2.0, horiz_run * 0.5)
    if horiz_run < 1e-9 or trim <= 0.0:
        return rafter
    fraction = (horiz_run - trim) / horiz_run
    new_p1 = (ex + dx * fraction, ey + dy * fraction)
    new_top = roof.eave_z_m + (roof.ridge_z_m - roof.eave_z_m) * fraction
    depth = rafter.z1_m - rafter.z0_m
    new_bottom = new_top - depth
    new_length = math.hypot(new_p1[0] - ex, new_p1[1] - ey, new_top - roof.eave_z_m)
    return replace(rafter, p1=new_p1, length_m=new_length, z0_end_m=new_bottom, z1_end_m=new_top)


def _ridge_condition(roof: ResolvedRoof, beam_member: FramedMember) -> BoundaryCondition:
    assemblies = (roof.assembly,)
    return BoundaryCondition(
        kind=ConditionKind.ROOF_RIDGE, assemblies=assemblies, detail="lvl-ridge-hanger",
        element_tags=(roof.tag, beam_member.parent_uid), key=f"roof_ridge:{roof.tag}",
    )
