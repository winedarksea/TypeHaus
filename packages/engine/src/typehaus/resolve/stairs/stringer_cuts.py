"""Cut stringer side silhouettes against final walking surfaces and riser boards."""

from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import Polygon, box

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.overlay import difference, intersection, union_all

_CUTTING_CATEGORIES = frozenset({"tread", "riser", "landing", "winder", "stair_subdeck"})
_MIN_OVERLAP_AREA_M2 = 1e-12
_ELEVATION_EPSILON_M = 1e-9


def cut_stringer_profiles(
    members: tuple[FramedMember, ...],
    unclipped_members: tuple[FramedMember, ...],
    subfloor_m: float,
) -> tuple[FramedMember, ...]:
    """Keep the stock rake below each resolved board, including its nose and finish drop.

    Cuts are two-dimensional side silhouettes, then swept across the stock thickness.
    Keeping the pre-clip rake lets the foot meet the floor horizontally: interpolating
    from a clamped endpoint would tilt the entire soffit upward and sever low tread seats.
    """
    original_stringers = {m.child_key: m for m in unclipped_members if m.category == "stringer"}
    if not original_stringers:
        return members
    cutters = [(Polygon(member_footprint(m)[0]), m)
               for m in members if m.category in _CUTTING_CATEGORIES]
    out = []
    for member in members:
        if member.category != "stringer":
            out.append(member)
            continue
        original = original_stringers[member.child_key]
        run = math.dist(member.p0, member.p1)
        if run <= 0:
            raise ValueError(f"{member.child_key}: stringer has no plan run")
        ux = (member.p1[0] - member.p0[0]) / run
        uy = (member.p1[1] - member.p0[1]) / run
        width = cross_section(member.profile).width_m
        member = replace(member, plan_width_m=width)
        footprint = Polygon(member_footprint(member)[0])
        bottom_end = original.z0_end_m if original.z0_end_m is not None else original.z0_m
        top_end = member.z1_end_m if member.z1_end_m is not None else member.z1_m
        blank = Polygon(((0, original.z0_m), (run, bottom_end),
                         (run, top_end), (0, member.z1_m)))
        ceiling = max(member.z1_m, top_end)
        blank = intersection(blank, box(0, subfloor_m, run, ceiling))
        projected_boards = []
        for board_footprint, board in cutters:
            overlap = intersection(footprint, board_footprint)
            if overlap.area <= _MIN_OVERLAP_AREA_M2 or board.z0_m >= ceiling:
                continue
            # Walking boards and risers are planar prisms; their overlap projected onto
            # the run gives the exact cut interval for straight flights in either axis.
            distances = [(x - member.p0[0]) * ux + (y - member.p0[1]) * uy
                         for x, y in overlap.exterior.coords]
            projected_boards.append((min(distances), max(distances), board))
        cuts = []
        foot_cut_end = 0.0
        for start, end, board in projected_boards:
            if board.category == "tread":
                # Carry the flat seat through to the back of the next riser board.
                # Otherwise a nose/finish setback leaves an exposed triangular tooth
                # between the lower tread's back edge and the higher riser's back face.
                following_risers = [(riser.z1_m, back) for _, back, riser in projected_boards
                                    if riser.category == "riser"
                                    and riser.z1_m > board.z0_m + _ELEVATION_EPSILON_M
                                    and back >= end]
                end = min(following_risers)[1] if following_risers else end
            cuts.append(box(start, board.z0_m, end, ceiling))
            if board.z0_m <= subfloor_m:
                # A closed first riser can be set back by its finish thickness. The
                # offcut in front of that board is waste, not a second stringer solid.
                foot_cut_end = max(foot_cut_end, end)
        if foot_cut_end > 0:
            blank = intersection(blank, box(foot_cut_end, subfloor_m, run, ceiling))
        cut = difference(blank, union_all(cuts))
        if not isinstance(cut, Polygon) or cut.is_empty or cut.interiors:
            raise ValueError(f"{member.child_key}: tread cuts leave a disconnected stringer")
        out.append(replace(member, elevation_profile=tuple(cut.exterior.coords)[:-1]))
    return tuple(out)
