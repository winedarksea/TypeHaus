"""Floor deck framing: FloorSystem JoistSpec -> joist FramedMembers (→ 30 WP3.4/3.7).

Semantics match the old catlin builder: one joist line per spacing position across the
deck's perpendicular extent (both ends included), split into spans at each bearing line.
Rim boards, opening headers/trimmers are future refinements — quantities and the S-101
sheets consume these members as-is.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.structure import Beam
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel

_DEFAULT_SPACING_M = inch(16).meters


def _member_depth_m(member: str) -> float:
    return cross_section(member).depth_m


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
    bearing_axes = [_bearing_axis(model, tag) for tag in spec.bearing_refs]
    missing = [tag for tag, axis in zip(spec.bearing_refs, bearing_axes) if axis is None]
    if missing or len(spec.bearing_refs) < 2:
        return None, [Finding(
            severity=Severity.ERROR, check_id="integrity.floor_bearing",
            message=f"floor {system.tag} needs >= 2 resolvable bearing refs "
                    f"(missing: {', '.join(missing) or 'none'})",
            element_tags=(system.tag,), result=Result.FAIL,
        )]
    resolved_axes = [axis for axis in bearing_axes if axis is not None]

    # Span boundaries: bearing (wall/beam) axis positions along the joist direction.
    def _axis_coord(axis) -> float:
        (x0, y0), (x1, y1) = axis
        return (x0 + x1) / 2.0 if along_x else (y0 + y1) / 2.0

    boundaries = sorted(_axis_coord(a) for a in resolved_axes)

    # Perpendicular extent: an explicit deck outline (a freestanding sub-structure sharing
    # the storey) scopes the field; otherwise it spans the deck storey's whole wall bbox.
    if system.outline:
        perp_coords = [(p.xy_m[1] if along_x else p.xy_m[0]) for p in system.outline]
    else:
        storey_walls = [w for w in model.walls if w.storey == storey.tag]
        perp_coords = [
            (p[1] if along_x else p[0])
            for w in (storey_walls or [])
            for p in w.axis
        ] or [(p[1] if along_x else p[0]) for a in resolved_axes for p in a]
    perp0, perp1 = min(perp_coords), max(perp_coords)

    spacing = (spec.spacing.meters if spec.spacing is not None else _DEFAULT_SPACING_M)
    depth = _member_depth_m(spec.member)
    z1 = storey.elevation.meters
    z0 = z1 - depth

    opening_boxes: list[tuple[FloorOpening, float, float, float, float]] = []
    for opening_tag in system.openings:
        opening = model.plan.by_tag(opening_tag)
        if not isinstance(opening, FloorOpening):
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            return None, [Finding(
                severity=Severity.ERROR, check_id="integrity.floor_opening_shape",
                message=f"floor {system.tag} only frames axis-aligned rectangular opening {opening.tag}",
                element_tags=(system.tag, opening.tag), result=Result.FAIL,
            )]
        opening_boxes.append((opening, *box))

    members: list[FramedMember] = []
    positions: list[float] = []
    position = perp0
    while position <= perp1 + 1e-9:
        positions.append(position)
        position += spacing
    if positions and positions[-1] < perp1 - 1e-6:
        positions.append(perp1)

    cant_m = spec.cantilever.meters if spec.cantilever else 0.0
    for index, perp in enumerate(positions):
        for span_index in range(len(boundaries) - 1):
            a, b = boundaries[span_index], boundaries[span_index + 1]
            # Cantilever only the two outer joist tips past the outermost bearing lines;
            # interior spans and opening-clipping are unchanged.
            if span_index == 0:
                a -= cant_m
            if span_index == len(boundaries) - 2:
                b += cant_m
            segments = [(a, b)]
            for _opening, minx, maxx, miny, maxy in opening_boxes:
                opening_perp0, opening_perp1 = (miny, maxy) if along_x else (minx, maxx)
                opening_axis0, opening_axis1 = (minx, maxx) if along_x else (miny, maxy)
                if opening_perp0 - 1e-9 <= perp <= opening_perp1 + 1e-9:
                    segments = _subtract_interval(segments, opening_axis0, opening_axis1)
            for segment_index, (segment_a, segment_b) in enumerate(segments):
                if segment_b - segment_a <= 1e-9:
                    continue
                if along_x:
                    p0, p1 = (segment_a, perp), (segment_b, perp)
                else:
                    p0, p1 = (perp, segment_a), (perp, segment_b)
                members.append(FramedMember(
                    system.uid, f"joist-{span_index}-{index:03d}-{segment_index}", "joist", spec.member,
                    p0, p1, z0, z1, segment_b - segment_a,
                ))

    # Opening edge framing is generated once per opening, after clipping.  A declared
    # bearing wall directly under a long edge is the explicit support path; otherwise a
    # header closes that edge and receives the cut joists.
    for opening, minx, maxx, miny, maxy in opening_boxes:
        edge_specs = (((minx, miny), (minx, maxy)), ((maxx, miny), (maxx, maxy))) if along_x else (
            ((minx, miny), (maxx, miny)), ((minx, maxy), (maxx, maxy)))
        for edge_index, (p0, p1) in enumerate(edge_specs):
            if _opening_edge_has_declared_bearing(model, opening, p0, p1):
                continue
            members.append(FramedMember(
                system.uid, f"header-{opening.tag}-{edge_index}", "header", spec.member,
                p0, p1, z0, z1, abs((p1[1] - p0[1]) if along_x else (p1[0] - p0[0])),
            ))
        # Parallel opening edges retain the header ends and prevent the adjacent joist
        # line from rolling.  They are doubled to model the usual trimmer pair.
        trim_specs = (((minx, miny), (maxx, miny)), ((minx, maxy), (maxx, maxy))) if along_x else (
            ((minx, miny), (minx, maxy)), ((maxx, miny), (maxx, maxy)))
        for edge_index, (p0, p1) in enumerate(trim_specs):
            for ply in range(2):
                members.append(FramedMember(
                    system.uid, f"trimmer-{opening.tag}-{edge_index}-{ply}", "trimmer", spec.member,
                    p0, p1, z0, z1, abs((p1[0] - p0[0]) if along_x else (p1[1] - p0[1])),
                ))

    # Rim (band) boards cap the joist ends — perpendicular to the joists, not a duplicate
    # of the parallel edge joists above. When the outer spans cantilever, the band rides
    # out to the joist tips (the fascia line), not the beam axis it oversails.
    depth_in = depth / inch(1).meters
    rim_profile = f"1.25x{depth_in:g} rim"
    for rim_index, boundary in enumerate((boundaries[0] - cant_m, boundaries[-1] + cant_m)):
        if along_x:
            r0, r1 = (boundary, perp0), (boundary, perp1)
        else:
            r0, r1 = (perp0, boundary), (perp1, boundary)
        members.append(FramedMember(
            system.uid, f"rim-{rim_index}", "rim", rim_profile, r0, r1, z0, z1,
            perp1 - perp0,
        ))

    return ResolvedFloor(
        uid=system.uid, tag=system.tag, storey=storey.tag,
        direction=spec.direction, members=tuple(members),
    ), []


def _bearing_axis(model: ResolvedModel, tag: str):
    """The plan axis (p0, p1) of a joist bearing ref — a resolved wall, or an authored
    standalone Beam (looked up through its per-storey nodes)."""
    wall = model.wall(tag)
    if wall is not None:
        return wall.axis
    beam = model.plan.by_tag(tag)
    if isinstance(beam, Beam):
        for storey in model.plan.storeys:
            nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(storey.tag)
                     if e.element_kind == "Node"}
            p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
            if p0 is not None and p1 is not None:
                return (p0, p1)
    return None


def _rectangular_opening_box(opening: FloorOpening) -> tuple[float, float, float, float] | None:
    points = [point.xy_m for point in opening.outline]
    if len(points) != 4:
        return None
    xs, ys = {point[0] for point in points}, {point[1] for point in points}
    if len(xs) != 2 or len(ys) != 2:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def _subtract_interval(intervals: list[tuple[float, float]], cut0: float, cut1: float) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for start, end in intervals:
        if cut1 <= start or cut0 >= end:
            out.append((start, end))
            continue
        if start < cut0:
            out.append((start, min(end, cut0)))
        if cut1 < end:
            out.append((max(start, cut1), end))
    return out


def _opening_edge_has_declared_bearing(model: ResolvedModel, opening: FloorOpening,
                                       p0: tuple[float, float], p1: tuple[float, float]) -> bool:
    covered: list[tuple[float, float]] = []
    vertical = abs(p0[0] - p1[0]) < 1e-9
    for tag in opening.bearing_refs:
        wall = model.wall(tag)
        if wall is None:
            continue
        a0, a1 = wall.axis
        if vertical and abs(a0[0] - p0[0]) < 1e-9 and abs(a1[0] - p0[0]) < 1e-9:
            covered.append((min(a0[1], a1[1]), max(a0[1], a1[1])))
        if not vertical and abs(a0[1] - p0[1]) < 1e-9 and abs(a1[1] - p0[1]) < 1e-9:
            covered.append((min(a0[0], a1[0]), max(a0[0], a1[0])))
    if not covered:
        return False
    target0, target1 = (min(p0[1], p1[1]), max(p0[1], p1[1])) if vertical else (min(p0[0], p1[0]), max(p0[0], p1[0]))
    cursor = target0
    for start, end in sorted(covered):
        if start > cursor + 1e-9:
            return False
        cursor = max(cursor, end)
    return cursor >= target1 - 1e-9
