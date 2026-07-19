"""Deterministic gable/shed rafter layout from resolved roof planes (M3)."""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof


def frame_roofs(model: ResolvedModel) -> None:
    """Attach roof-plane rafter members at the assembly's framing spacing."""
    framed: list[ResolvedRoof] = []
    for roof in model.roofs:
        framed.append(ResolvedRoof(
            uid=roof.uid, tag=roof.tag, storey=roof.storey, form=roof.form,
            footprint=roof.footprint, eave_z_m=roof.eave_z_m, ridge_z_m=roof.ridge_z_m,
            ridge_direction=roof.ridge_direction, assembly=roof.assembly,
            surface_area_m2=roof.surface_area_m2, members=_roof_rafters(model, roof),
        ))
    model.roofs = framed


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
