"""Handrail ends (R311.7.8.2): a ``wall_return`` draws the return and the plate it lands on.

The return is a level run in the rail's own profile from the rail end to the wall finish
face; the end plate (wall flange) closes it against the face. Both are discrete parts, so
both are solids the take-off counts and the R311.7.8.2 check reads back. Tags are
``{tag}-RETURN{n}`` / ``{tag}-ENDPLATE{n}`` — neither starts with ``{tag}-RAIL``, so the
top-rail readers never mistake a return for the bar.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import Railing
from typehaus.resolve.geometry import Vec
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, SolidSweep
from typehaus.resolve.railings.parts import RAILING_CATEGORY, RAILING_FACETS, RailingParts
from typehaus.resolve.railings.spans import RailingSurface
from typehaus.resolve.railings.wall_contact import REACH_M, mounting_wall_face
from typehaus.resolve.sweep import (
    rect_profile,
    round_profile,
    sweep_plan_silhouette,
    sweep_z_extent,
)

#: A stock round wall flange for 42.4 mm tube: Ø70 × 6 mm. A drawing size only.
_PLATE_RADIUS_M = 0.035
_PLATE_THICK_M = 0.006


def emit_terminations(model: ResolvedModel, el: Railing, storey: str, path: list[Vec],
                      surface: RailingSurface, parts: RailingParts,
                      rail_h: float) -> list[Finding]:
    """Draw a return + end plate at each ``wall_return`` end; WARN where no wall is near."""
    findings: list[Finding] = []
    ends = ((1, path[0], path[1], el.start_termination, el.start_return_target),
            (2, path[-1], path[-2], el.end_termination, el.end_return_target))
    radius = parts.rail_round_radius_m
    profile = (round_profile(radius, RAILING_FACETS) if radius is not None
               else rect_profile(parts.rail_section_m, parts.rail_section_m))
    for index, end, inward, termination, target in ends:
        if termination != "wall_return":
            continue
        z = surface.height_at(end) + rail_h
        contact, obstructing_tags = mounting_wall_face(
            model, end if target is None else target.xy_m, z,
            along=((end[0] - inward[0], end[1] - inward[1]),),
            half_width_m=_PLATE_RADIUS_M, z0_m=z - _PLATE_RADIUS_M,
            z1_m=z + _PLATE_RADIUS_M)
        distance = math.dist(end, contact.face_point) if contact is not None else 0.0
        if contact is None or not 1e-4 <= distance <= REACH_M:
            findings.append(Finding(
                severity=Severity.WARN, check_id="geometry.railing_return_unanchored",
                message=(f"railing {el.tag} end {index} is a wall_return but no solid wall "
                         "face supports its full plate within reach; no return drawn"),
                element_tags=(el.tag, *obstructing_tags), result=Result.FAIL))
            continue
        fx, fy = contact.face_point
        _append(model, el, storey, f"t{index:02d}", f"RETURN{index}",
                SolidSweep(path=((end[0], end[1], z), (fx, fy, z)), profile=profile),
                parts.rail_material)
        wall = next(w for w in model.walls if w.tag == contact.wall_tag)
        (ax, ay), (bx, by) = wall.axis
        wall_length = math.hypot(bx - ax, by - ay)
        ux, uy = -(by - ay) / wall_length, (bx - ax) / wall_length
        if ux * (end[0] - fx) + uy * (end[1] - fy) < 0:
            ux, uy = -ux, -uy
        plate = SolidSweep(
            path=((fx, fy, z), (fx + ux * _PLATE_THICK_M, fy + uy * _PLATE_THICK_M, z)),
            profile=round_profile(_PLATE_RADIUS_M, RAILING_FACETS))
        _append(model, el, storey, f"f{index:02d}", f"ENDPLATE{index}", plate,
                parts.post_material)
    return findings


def _append(model: ResolvedModel, el: Railing, storey: str, uid_suffix: str,
            tag_suffix: str, sweep: SolidSweep, material: str | None) -> None:
    z0, z1 = sweep_z_extent(sweep)
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-{uid_suffix}", tag=f"{el.tag}-{tag_suffix}", storey=storey,
        category=RAILING_CATEGORY, outline=sweep_plan_silhouette(sweep), z0_m=z0, z1_m=z1,
        assembly=el.assembly, material=material, sweep=sweep,
    ))
