"""Floor deck framing: FloorSystem JoistSpec -> joist FramedMembers (→ 30 WP3.4/3.7).

Semantics match the old catlin builder: one joist line per spacing position across the
deck's perpendicular extent (both ends included), split into spans at each bearing line.
Rim boards, opening headers/trimmers are future refinements — quantities and the S-101
sheets consume these members as-is.
"""

from __future__ import annotations

import re

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorSystem
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel

_DEFAULT_SPACING_M = inch(16).meters
_DEFAULT_DEPTH_M = inch(11.875).meters


def _member_depth_m(member: str) -> float:
    """Leading number in a member string is its depth in inches ('11.875 I-joist')."""
    match = re.match(r"\s*(\d+(?:\.\d+)?)", member)
    return inch(float(match.group(1))).meters if match else _DEFAULT_DEPTH_M


def resolve_floors(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    plan = model.plan
    for storey in plan.storeys:
        for element in plan.storey_elements(storey.tag):
            if not isinstance(element, FloorSystem):
                continue
            floor, floor_findings = _resolve_floor(model, element, storey)
            findings.extend(floor_findings)
            if floor is not None:
                model.floors.append(floor)
    return findings


def _resolve_floor(model: ResolvedModel, system: FloorSystem, storey):
    spec = system.joists
    along_x = spec.direction == "x"
    if not spec.bearing_refs:
        return None, []  # nothing to frame yet — bearing refs are the M3 opt-in
    bearing_walls = [model.wall(tag) for tag in spec.bearing_refs]
    missing = [tag for tag, wall in zip(spec.bearing_refs, bearing_walls) if wall is None]
    if missing or len(spec.bearing_refs) < 2:
        return None, [Finding(
            severity=Severity.ERROR, check_id="integrity.floor_bearing",
            message=f"floor {system.tag} needs >= 2 resolvable bearing refs "
                    f"(missing: {', '.join(missing) or 'none'})",
            element_tags=(system.tag,), result=Result.FAIL,
        )]

    # Span boundaries: bearing wall axis positions along the joist direction.
    def _axis_coord(wall) -> float:
        (x0, y0), (x1, y1) = wall.axis
        return (x0 + x1) / 2.0 if along_x else (y0 + y1) / 2.0

    boundaries = sorted(_axis_coord(w) for w in bearing_walls)

    # Perpendicular extent: bbox of the deck storey's walls (the deck spans its storey).
    storey_walls = [w for w in model.walls if w.storey == storey.tag]
    if not storey_walls:
        storey_walls = bearing_walls
    perp_coords = [
        (p[1] if along_x else p[0]) for w in storey_walls for p in w.axis
    ]
    perp0, perp1 = min(perp_coords), max(perp_coords)

    spacing = (spec.spacing.meters if spec.spacing is not None else _DEFAULT_SPACING_M)
    depth = _member_depth_m(spec.member)
    z1 = storey.elevation.meters
    z0 = z1 - depth

    members: list[FramedMember] = []
    positions: list[float] = []
    position = perp0
    while position <= perp1 + 1e-9:
        positions.append(position)
        position += spacing
    if positions and positions[-1] < perp1 - 1e-6:
        positions.append(perp1)

    for index, perp in enumerate(positions):
        for span_index in range(len(boundaries) - 1):
            a, b = boundaries[span_index], boundaries[span_index + 1]
            if along_x:
                p0, p1 = (a, perp), (b, perp)
            else:
                p0, p1 = (perp, a), (perp, b)
            members.append(FramedMember(
                system.uid, f"joist-{span_index}-{index:03d}", "joist", spec.member,
                p0, p1, z0, z1, b - a,
            ))

    return ResolvedFloor(
        uid=system.uid, tag=system.tag, storey=storey.tag,
        direction=spec.direction, members=tuple(members),
    ), []
