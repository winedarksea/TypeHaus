"""Resolve a :class:`~typehaus.model.braces.StrapBrace` into one thin raked member.

The strap hosts itself on a :class:`ResolvedBrace` (``kind="strap"``) exactly as a knee
brace does, so every emitter that draws braces draws it. Its member category is
:data:`STRAP_CATEGORY`, which the lumber take-off and the interference check skip: a strap
is hardware nailed flat to the faces it crosses (``takeoff/strap_braces`` bills it).
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.braces import StrapBrace
from typehaus.resolve.model import FramedMember, ResolvedBrace, ResolvedModel

#: The member category a strap resolves to. Not lumber, and not a clash with what it is
#: nailed to or passes behind.
STRAP_CATEGORY = "strap"
_MIN_RUN_M = 1e-6


def resolve_strap_brace(model: ResolvedModel, el: StrapBrace, storey: str) -> list[Finding]:
    """One member start→end in 3-D, lying in a vertical plane offset by ``face_plane``.

    ``face_plane`` places the strap's CONTACT face; the steel lies on the far side of it from
    the authored line, so a strap pushed onto a member face never overlaps that member.
    Plan width is the sheet thickness; the vertical extent at each end is the strap width
    read vertically, ``width / cos(theta)``.
    """
    (ax, ay), (bx, by) = el.start.xy_m, el.end.xy_m
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run < _MIN_RUN_M:
        return [Finding(
            severity=Severity.WARN, check_id="integrity.strap_brace_unresolved",
            message=f"strap brace {el.tag} has no plan run; a plumb strap is not resolved",
            element_tags=(el.tag,), result=Result.FAIL)]
    thickness = el.thickness.meters
    offset = el.face_plane.meters
    if offset:
        offset += math.copysign(thickness / 2.0, offset)
    nx, ny = -dy / run * offset, dx / run * offset  # left normal, scaled
    z_start, z_end = el.start_elevation.meters, el.end_elevation.meters
    rise = z_end - z_start
    half = el.width.meters / 2.0 / math.cos(math.atan2(abs(rise), run))
    width_in = el.width.meters / 0.0254
    model.braces.append(ResolvedBrace(
        uid=el.uid or f"{el.tag}-strap", tag=el.tag, storey=storey, kind="strap",
        members=(FramedMember(
            parent_uid=el.uid or el.tag, child_key="strap", category=STRAP_CATEGORY,
            # Actual thickness x width, so ``cross_section`` reads it rather than guessing.
            profile=f"{el.thickness.meters / 0.0254:g}x{width_in:g}",
            p0=(ax + nx, ay + ny), p1=(bx + nx, by + ny),
            z0_m=z_start - half, z1_m=z_start + half,
            z0_end_m=z_end - half, z1_end_m=z_end + half,
            length_m=math.hypot(run, rise),
            plan_width_m=thickness,
            connection=f"strap:{el.product}",
        ),),
    ))
    return []
