"""Separate stair covering geometry over stock treads, landings and closed risers."""

from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import Point, Polygon

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, StairFinishPart

_LOWERED_CATEGORIES = frozenset({
    "tread", "winder", "landing", "stringer", "landing_framing", "stair_subdeck",
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


def set_landing_stack(members: tuple[FramedMember, ...], stack_m: float,
                      tread_m: float) -> tuple[FramedMember, ...]:
    """Thin each landing deck to its floor stack and lift its own framing to meet it.

    The layouts build a landing deck at tread thickness. A hardwood landing is field over
    subfloor instead; its walking face stays put and the difference goes to the framing,
    up when the stack is thinner than a tread, down when it is thicker (1" treads under a
    3/4" + 3/4" landing).
    """
    lift = tread_m - stack_m
    if abs(lift) <= 1e-9:
        return members
    names = [m.child_key.removeprefix("landing-") for m in members
             if m.category == "landing"]
    own = tuple(f"landing-{part}-{name}-" for name in names for part in ("joist", "rim"))
    out: list[FramedMember] = []
    for member in members:
        if member.category == "landing":
            section = cross_section(member.profile)
            width_in = max(section.width_m, section.depth_m) / 0.0254
            out.append(replace(member, profile=f"deck {width_in:g}x{stack_m / 0.0254:g}",
                               z0_m=member.z1_m - stack_m))
        elif member.category == "landing_framing" and member.child_key.startswith(own):
            out.append(replace(
                member, z0_m=member.z0_m + lift, z1_m=member.z1_m + lift,
                z0_end_m=member.z0_end_m + lift if member.z0_end_m is not None else None,
                z1_end_m=member.z1_end_m + lift if member.z1_end_m is not None else None))
        else:
            out.append(member)
    return tuple(out)


def nosing_lip(riser: FramedMember, key: str, material_ref: str, top_z: float,
               nosing_m: float, finish_m: float = 0.0) -> StairFinishPart:
    """A nosing over ``riser``: from its board's back face (the edge it meets) out past its
    finished face by the flight's nosing, from the board's top up to ``top_z``."""
    ux, uy = riser.orient
    half = cross_section(riser.profile).width_m / 2
    back = [(x + ux * half, y + uy * half) for x, y in (riser.p0, riser.p1)]
    reach = 2 * half + finish_m + nosing_m
    front = [(x - ux * reach, y - uy * reach) for x, y in back]
    return StairFinishPart(key, "landing-nosing", material_ref,
                           (back[0], back[1], front[1], front[0]), riser.z1_m, top_z)


def landing_nosing_parts(members: tuple[FramedMember, ...], material_ref: str,
                         tread_m: float, nosing_m: float,
                         finish_m: float = 0.0) -> tuple[StairFinishPart, ...]:
    """The lip of each landing tread: over the riser that climbs onto the landing edge.

    Only an arrival edge has one. The riser a flight leaves a landing by stands ON it.
    """
    parts: list[StairFinishPart] = []
    risers = [m for m in members if m.category == "riser" and m.orient is not None]
    for landing in (m for m in members if m.category == "landing"):
        edge = Polygon(member_footprint(landing)[0]).exterior
        for riser in risers:
            if abs(riser.z1_m - (landing.z1_m - tread_m)) > 1e-4:
                continue
            ux, uy = riser.orient
            half = cross_section(riser.profile).width_m / 2
            back = [(x + ux * half, y + uy * half) for x, y in (riser.p0, riser.p1)]
            if any(edge.distance(Point(point)) > 1e-3 for point in back):
                continue
            parts.append(nosing_lip(riser, f"{landing.child_key}:nosing", material_ref,
                                    landing.z1_m + finish_m, nosing_m, finish_m))
    return tuple(parts)


def stairhead_nosing_part(members: tuple[FramedMember, ...], material_ref: str,
                          arrival_z: float, nosing_m: float,
                          finish_m: float) -> StairFinishPart | None:
    """The arrival floor's nosing, over the flight's topmost riser."""
    risers = [m for m in members if m.category == "riser" and m.orient is not None]
    if not risers:
        return None
    head = max(risers, key=lambda m: m.z1_m)
    return nosing_lip(head, "stairhead:nosing", material_ref, arrival_z, nosing_m, finish_m)
