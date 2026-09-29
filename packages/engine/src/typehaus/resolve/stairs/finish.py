"""Separate stair covering geometry over stock treads, landings and closed risers."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, StairFinishPart

_LOWERED_CATEGORIES = frozenset({
    "tread", "winder", "landing", "stringer", "landing_framing",
})
_WALKING_CATEGORIES = frozenset({"tread", "winder", "landing"})


def lower_stair_substrates(members: tuple[FramedMember, ...],
                           finish_thickness_m: float) -> tuple[FramedMember, ...]:
    """Leave the design walking and riser faces in place while adding a real finish depth."""
    if finish_thickness_m <= 0:
        return members
    lowered: list[FramedMember] = []
    for member in members:
        if member.category in _LOWERED_CATEGORIES:
            lowered.append(replace(
                member, z0_m=member.z0_m - finish_thickness_m,
                z1_m=member.z1_m - finish_thickness_m,
                z0_end_m=(member.z0_end_m - finish_thickness_m
                          if member.z0_end_m is not None else None),
                z1_end_m=(member.z1_end_m - finish_thickness_m
                          if member.z1_end_m is not None else None),
            ))
        elif member.category == "riser":
            # The plywood's exposed face moves inward; the carpet ends at its former
            # face. Its bottom still meets the lower finished surface, while its top
            # follows the underside of the lowered tread or landing.
            ux, uy = member.orient or (0.0, 0.0)
            lowered.append(replace(
                member,
                p0=(member.p0[0] + ux * finish_thickness_m,
                    member.p0[1] + uy * finish_thickness_m),
                p1=(member.p1[0] + ux * finish_thickness_m,
                    member.p1[1] + uy * finish_thickness_m),
                z1_m=member.z1_m - finish_thickness_m,
            ))
        else:
            lowered.append(member)
    return tuple(lowered)


def stair_finish_parts(members: tuple[FramedMember, ...], material_ref: str,
                       finish_thickness_m: float,
                       substrate_thickness_m: float) -> tuple[StairFinishPart, ...]:
    """Make top sheets, exposed nosing returns and riser facings from final substrates."""
    parts: list[StairFinishPart] = []
    for member in members:
        if member.category in _WALKING_CATEGORIES:
            outline, _, _ = member_footprint(member)
            parts.append(StairFinishPart(
                f"{member.child_key}:top", "walking", material_ref, tuple(outline),
                member.z1_m, member.z1_m + finish_thickness_m))
            if member.category == "tread" and member.riser_line is not None:
                nose = _nosing_return(member, outline, finish_thickness_m)
                if nose is not None:
                    parts.append(StairFinishPart(
                        f"{member.child_key}:nosing", "nosing", material_ref, nose,
                        member.z0_m, member.z1_m + finish_thickness_m))
        elif member.category == "riser" and member.orient is not None:
            ux, uy = member.orient
            thick = cross_section(member.profile).width_m
            ax, ay = member.p0[0] - ux * thick / 2, member.p0[1] - uy * thick / 2
            bx, by = member.p1[0] - ux * thick / 2, member.p1[1] - uy * thick / 2
            outline = ((ax, ay), (bx, by),
                       (bx - ux * finish_thickness_m, by - uy * finish_thickness_m),
                       (ax - ux * finish_thickness_m, ay - uy * finish_thickness_m))
            parts.append(StairFinishPart(
                f"{member.child_key}:face", "riser", material_ref, outline,
                member.z0_m, member.z1_m + substrate_thickness_m
                + finish_thickness_m))
    return tuple(parts)


def _nosing_return(member: FramedMember, outline, depth: float):
    """The board's leading plan edge, carried down its front as the carpet rolls over it."""
    (ax, ay), (bx, by) = member.riser_line
    ux = (member.p0[0] + member.p1[0] - ax - bx) / 2
    uy = (member.p0[1] + member.p1[1] - ay - by) / 2
    norm = math.hypot(ux, uy)
    if norm < 1e-9:
        return None
    ux, uy = ux / norm, uy / norm
    positions = sorted(outline, key=lambda point: point[0] * ux + point[1] * uy)
    first, second = positions[:2]
    return (first, second,
            (second[0] - ux * depth, second[1] - uy * depth),
            (first[0] - ux * depth, first[1] - uy * depth))
