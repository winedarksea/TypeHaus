"""Floor deck framing: FloorSystem JoistSpec -> joist FramedMembers (→ 30 WP3.4/3.7).

One joist line per spacing position across the deck's perpendicular extent (both ends
included), split into spans at each bearing line.
Rim boards, opening headers/trimmers are future refinements — quantities and the S-101
sheets consume these members as-is.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.structure import Beam
from typehaus.quantities import inch, m
from typehaus.resolve.floor_ends import floor_ends
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.tables import ENGINEERED_LVL, header_size
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel, Ring

_DEFAULT_SPACING_M = inch(16).meters
# One LVL ply. A floor-opening header hangs *inside* the joist band (the cut joists come
# back to it in hangers), so the deck fixes its depth and the ply count is the only free
# variable — which is exactly what the prescriptive header table names.
_HEADER_PLY_WIDTH_IN = 1.75
# Ply count carried past the prescriptive table's 8 ft ceiling. The table's widest entry
# is two plies; a longer opening is a designed beam, and ``structural.floor_opening_header``
# says so rather than letting the drawn member imply a prescriptive answer.
_ENGINEERED_HEADER_PLIES = 3
# The two trimmer plies of an opening edge. Doubled trimmer joists are the standard
# prescriptive answer (IRC R502.10) for the edge that carries a header end.
_TRIMMER_PLIES = 2


def _member_depth_m(member: str) -> float:
    return cross_section(member).depth_m


def opening_header_profile(span_m: float, band_depth_m: float) -> str:
    """Multi-ply LVL header profile for a floor opening of ``span_m``.

    Emitting the deck's own ``JoistSpec.member`` here left every opening header a single
    *unsized* joist ply — a 3'-4" attic header and an 11'-0" stair header drawn identically,
    and neither of them a header. The prescriptive table sizes the ply count; the deck's
    joist depth sizes the member, so the header sits flush in the band.
    """
    prescriptive = header_size(m(span_m))
    plies = (_ENGINEERED_HEADER_PLIES if prescriptive == ENGINEERED_LVL
             else int(prescriptive.split("-", 1)[0]))
    return f"{plies}-{_HEADER_PLY_WIDTH_IN:g}x{band_depth_m / inch(1).meters:g} LVL"


def _shift(p0: tuple[float, float], p1: tuple[float, float],
           normal: tuple[float, float], distance: float):
    """``p0``/``p1`` translated ``distance`` along the unit ``normal``."""
    return ((p0[0] + normal[0] * distance, p0[1] + normal[1] * distance),
            (p1[0] + normal[0] * distance, p1[1] + normal[1] * distance))


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
    # strict=True: `bearing_axes` is a comprehension over `spec.bearing_refs`.
    missing = [tag for tag, axis in zip(spec.bearing_refs, bearing_axes, strict=True)
               if axis is None]
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

    # Deduplicated: several refs routinely name one line (catlin's x=18' carries three
    # basement walls, and its two west walls share x=0). Left in, each duplicate opened a
    # zero-length span that was silently dropped later — and, worse, pushed the real span
    # off ``span_index == 0``, so the two outermost spans stopped being recognised as
    # outermost and neither a cantilever nor an end bearing reached them.
    boundaries: list[float] = []
    for coord in sorted(_axis_coord(a) for a in resolved_axes):
        if not boundaries or coord - boundaries[-1] > 1e-9:
            boundaries.append(coord)

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

    cant_m = spec.cantilever.meters if spec.cantilever else 0.0
    # Per-end overrides (a deck with a flush bearing at one end and an overhang at the
    # other); each falls back to the symmetric scalar.
    cant_start_m = spec.cantilever_start.meters if spec.cantilever_start is not None else cant_m
    cant_end_m = spec.cantilever_end.meters if spec.cantilever_end is not None else cant_m
    # Where the joists physically stop, which is not the line they are cut at: behind the
    # rim board at a free end, at their authored share of the plate where two decks meet.
    # ``resolve/floor_ends.py`` is the whole derivation, and the only place the three
    # coordinates at a deck end (span line, joist tip, deck edge) are told apart.
    depth_in = depth / inch(1).meters
    rim_profile = spec.rim_member or f"1.25x{depth_in:g} rim"
    ends = floor_ends(model, system, storey.tag, boundaries, 0 if along_x else 1,
                      perp0, perp1, cross_section(rim_profile).width_m,
                      cant_start_m, cant_end_m)
    # Width of a regular joist AND of one trimmer ply — both are ``spec.member``, so a
    # doubled trimmer pair's outboard face reaches ``_TRIMMER_PLIES * trimmer_ply_width``
    # past the opening edge (see the trim_specs loop below). A narrow-flange I-joist never
    # reaches the next regular joist line; a wide-chord floor truss can (see the position
    # loop's opening-band check).
    trimmer_ply_width = cross_section(spec.member).width_m

    opening_boxes: list[tuple[FloorOpening, float, float, float, float]] = []
    for opening_tag in system.openings:
        opening = model.plan.by_tag(opening_tag)
        if not isinstance(opening, FloorOpening):
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            return None, [Finding(
                severity=Severity.ERROR, check_id="integrity.floor_opening_shape",
                message=f"floor {system.tag} only frames axis-aligned rectangular "
                        f"opening {opening.tag}",
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

    # Anything shorter than the joist's own depth is bearing seat, not span. An opening
    # drawn to a bearing wall's *near face* stops short of the bearing line the span is cut
    # at, and the remainder — 3 3/8" of deck over the top plate, where the trimmer actually
    # sits — is not a joist. Emitting it put stub members in the frame and the take-off.
    min_segment_m = _member_depth_m(spec.member)
    for index, perp in enumerate(positions):
        for span_index in range(len(boundaries) - 1):
            a, b = boundaries[span_index], boundaries[span_index + 1]
            # Cantilever only the two outer joist tips past the outermost bearing lines;
            # interior spans and opening-clipping are unchanged.
            if span_index == 0:
                a = ends.tip_lo
            if span_index == len(boundaries) - 2:
                b = ends.tip_hi
            segments = [(a, b)]
            for _opening, minx, maxx, miny, maxy in opening_boxes:
                opening_perp0, opening_perp1 = (miny, maxy) if along_x else (minx, maxx)
                opening_axis0, opening_axis1 = (minx, maxx) if along_x else (miny, maxy)
                # A doubled-trimmer band, one on each parallel edge, reaches
                # ``_TRIMMER_PLIES * trimmer_ply_width`` past the opening edge (trim_specs
                # below) — a wide-chord member (e.g. a floor truss) can put that band's
                # outboard face past the *next* regular joist line's centre, which is a real
                # plan clash (structural.member_interference) rather than a drafting one.
                # The nearest regular line the band would reach is absorbed into the
                # trimmer pair instead of being drawn twice.
                trim_band = _TRIMMER_PLIES * trimmer_ply_width
                in_opening = opening_perp0 - 1e-9 <= perp <= opening_perp1 + 1e-9
                in_trim_band = (opening_perp0 - trim_band - 1e-9 <= perp < opening_perp0 - 1e-9
                               or opening_perp1 + 1e-9 < perp <= opening_perp1 + trim_band + 1e-9)
                if in_opening or in_trim_band:
                    segments = _subtract_interval(segments, opening_axis0, opening_axis1)
            for segment_index, (segment_a, segment_b) in enumerate(segments):
                if segment_b - segment_a <= min_segment_m:
                    continue
                if along_x:
                    p0, p1 = (segment_a, perp), (segment_b, perp)
                else:
                    p0, p1 = (perp, segment_a), (perp, segment_b)
                members.append(FramedMember(
                    system.uid, f"joist-{span_index}-{index:03d}-{segment_index}", "joist",
                    spec.member, p0, p1, z0, z1, segment_b - segment_a,
                ))

    # Sistered plies + solid blocking under an authored concentrated load. This runs on the
    # joist field above (it needs its line positions and its cantilevered axis extent), and
    # before the opening/rim framing so a reinforced line is already in ``members`` when the
    # rim is drawn to the same tips.
    members.extend(_reinforcement_members(
        system, spec, positions, along_x, ends.tip_lo, ends.tip_hi, z0, z1))

    # Opening edge framing is generated once per opening, after clipping.  A declared
    # bearing wall directly under a long edge is the explicit support path; otherwise a
    # header closes that edge and receives the cut joists.
    # Headers stay *on* the authored opening line: the cut joists are clipped to that line
    # and land on the header, and the trimmer pair's first ply retains its ends there.
    # Only the second trimmer ply moves, and it moves outboard — away from the hole.
    for opening, minx, maxx, miny, maxy in opening_boxes:
        edge_specs = (((minx, miny), (minx, maxy)), ((maxx, miny), (maxx, maxy))) if along_x else (
            ((minx, miny), (maxx, miny)), ((minx, maxy), (maxx, maxy)))
        for edge_index, (p0, p1) in enumerate(edge_specs):
            if _opening_edge_has_declared_bearing(model, opening, p0, p1):
                continue
            span = abs((p1[1] - p0[1]) if along_x else (p1[0] - p0[0]))
            members.append(FramedMember(
                system.uid, f"header-{opening.tag}-{edge_index}", "header",
                opening_header_profile(span, depth), p0, p1, z0, z1, span,
            ))
        # Parallel opening edges retain the header ends and prevent the adjacent joist
        # line from rolling.  They are doubled to model the usual trimmer pair — plies laid
        # face to face, not stacked on one another (which drew two byte-identical members,
        # so the pair rendered and measured as a single joist in every section and take-off).
        trim_specs = ((((minx, miny), (maxx, miny)), (0.0, -1.0)),
                      (((minx, maxy), (maxx, maxy)), (0.0, 1.0))) if along_x else (
            (((minx, miny), (minx, maxy)), (-1.0, 0.0)),
            (((maxx, miny), (maxx, maxy)), (1.0, 0.0)))
        for edge_index, ((p0, p1), outboard) in enumerate(trim_specs):
            span = abs((p1[0] - p0[0]) if along_x else (p1[1] - p0[1]))
            for ply in range(_TRIMMER_PLIES):
                t0, t1 = _shift(p0, p1, outboard, ply * trimmer_ply_width)
                members.append(FramedMember(
                    system.uid, f"trimmer-{opening.tag}-{edge_index}-{ply}", "trimmer",
                    spec.member, t0, t1, z0, z1, span,
                ))

    # Rim (band) boards cap the joist ends — perpendicular to the joists, not a duplicate
    # of the parallel edge joists above. When the outer spans cantilever, the band rides
    # out to the joist tips (the fascia line), not the beam axis it oversails.
    # The rim rides the deck edge, not the span line: at a free end its outboard face is
    # flush with the framing face the sheathing runs down over, so it sits wholly outside
    # the joist tips instead of overlapping the last 5/8" of every one of them. A *shared*
    # line keeps the old centred placement, because the band there is not a rim at all —
    # it is the squash-block course under a bearing line (``JoistSpec.rim_member``), and
    # the joists landing on the plate from both sides leave it nowhere else to go.
    for rim_index, boundary in enumerate((ends.rim_lo, ends.rim_hi)):
        if boundary is None:
            continue  # shared plate: blocking, not a band — see floor_ends
        if along_x:
            r0, r1 = (boundary, perp0), (boundary, perp1)
        else:
            r0, r1 = (perp0, boundary), (perp1, boundary)
        members.append(FramedMember(
            system.uid, f"rim-{rim_index}", "rim", rim_profile, r0, r1, z0, z1,
            perp1 - perp0, material=spec.rim_material,
        ))

    # The subfloor sheet over the joist field. Its extent is the framed field itself —
    # bearing line to bearing line including both cantilevers, by the joists' perpendicular
    # extent — because that is exactly what the decking is nailed to. Openings are cut out
    # rather than drawn over: the joists were already clipped to them.
    deck_outline: Ring = []
    deck_voids: tuple[Ring, ...] = ()
    deck_z0_m = deck_z1_m = z1
    if system.subfloor is not None:
        if system.subfloor_outline:
            # An authored sheet wins outright — a plank that oversails its rim. It replaces
            # the derived corners and nothing else; see FloorSystem.subfloor_outline.
            deck_outline = [p.xy_m for p in system.subfloor_outline]
        else:
            axis0, axis1 = ends.deck_lo, ends.deck_hi
            if along_x:
                corners = ((axis0, perp0), (axis1, perp0), (axis1, perp1), (axis0, perp1))
            else:
                corners = ((perp0, axis0), (perp0, axis1), (perp1, axis1), (perp1, axis0))
            deck_outline = list(corners)
        deck_voids = tuple(
            [(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]
            for _opening, minx, maxx, miny, maxy in opening_boxes
        )
        deck_z1_m = z1 + system.subfloor.thickness.meters

    return ResolvedFloor(
        uid=system.uid, tag=system.tag, storey=storey.tag,
        direction=spec.direction, members=tuple(members),
        deck_outline=deck_outline, deck_voids=deck_voids,
        deck_z0_m=deck_z0_m, deck_z1_m=deck_z1_m, ends=ends,
        deck_material_ref=(system.subfloor.material_ref if system.subfloor else None),
    ), []


# --- concentrated-load reinforcement --------------------------------------------------
# CHECK-RECOGNITION CONTRACT (``structural.cantilever_point_load``, checks/structural/
# cantilever.py). That advisory fires when a Post bears on a FloorSystem inside its
# cantilever band, and downgrades its FAIL to UNKNOWN when it can see the load answered.
# It reads three things, all of which this function is what produces:
#   (a) a ``FloorSystem.reinforcements`` entry whose ``at`` is near the post with
#       ``plies >= 3`` — or, geometrically, resolved members of category
#       ``"sister_joist"`` within *half a joist spacing* of the post. Hence the nearest-
#       line rule below (never more than half a spacing away by construction) and the
#       plies laid face to face *toward* the load, so the cluster brackets it.
#   (b) members of category ``"blocking"`` within 0.3 m of the post. The blocks are
#       therefore placed at the load's own axis coordinate, not at a bearing line.
#   (c) a ``Connector`` (HURRICANE_TIE / HOLD_DOWN) on the same joist line — authored on
#       the house, not emitted here (catlin: CN-SG-TIE-BR2 at the back-span bearing).
# Changing either category string, or moving the blocking off the load, silently turns a
# mitigated deck back into an unmitigated one. Both categories are also take-off
# vocabulary — ``takeoff/framing.py`` groups by ``(profile, category)`` — so the plies and
# the blocks bill themselves with no further wiring.
def _reinforcement_members(system: FloorSystem, spec, positions: list[float], along_x: bool,
                           axis_lo: float, axis_hi: float,
                           z0: float, z1: float) -> list[FramedMember]:
    """Sister plies + blocking for each of ``system.reinforcements``.

    The plies run the *whole* joist — bearing line to bearing line including both
    cantilevers — because a sister that stops at the support carries nothing where the load
    actually is (out on the overhang, for the catlin porch). The blocks run to the adjacent
    joist line on each side, cut to the clear gap between member faces so the frame does not
    read as a clash in ``structural.member_interference``.
    """
    out: list[FramedMember] = []
    if not positions:
        return out
    for index, reinforcement in enumerate(system.reinforcements):
        at_x, at_y = reinforcement.at.xy_m
        perp_at, axis_at = (at_y, at_x) if along_x else (at_x, at_y)
        line = min(range(len(positions)), key=lambda i: abs(positions[i] - perp_at))
        perp = positions[line]
        member = reinforcement.member or spec.member
        ply_width = cross_section(member).width_m
        plies = max(int(reinforcement.plies), 1)
        # The extra plies go on the side the load is on, so the cluster straddles it rather
        # than leaving the post overhanging its own reinforcement. A load exactly on the
        # line is arbitrary; +1 keeps it deterministic.
        sign = 1.0 if perp_at >= perp else -1.0
        normal = (0.0, sign) if along_x else (sign, 0.0)
        if along_x:
            p0, p1 = (axis_lo, perp), (axis_hi, perp)
        else:
            p0, p1 = (perp, axis_lo), (perp, axis_hi)
        for ply in range(plies - 1):
            s0, s1 = _shift(p0, p1, normal, (ply + 1) * ply_width)
            out.append(FramedMember(
                system.uid, f"sister-{index}-{ply}", "sister_joist", member,
                s0, s1, z0, z1, axis_hi - axis_lo,
            ))
        if not reinforcement.blocking:
            continue
        # Outer faces of the finished cluster (authored joist + the plies just added).
        spread = sign * (plies - 1) * ply_width
        cluster_lo = perp - ply_width / 2.0 + min(0.0, spread)
        cluster_hi = perp + ply_width / 2.0 + max(0.0, spread)
        # Blocks sit at the load, held a full member width inside the joist tips so they
        # clear the rim board riding on those tips.
        block_axis = min(max(axis_at, axis_lo + ply_width), axis_hi - ply_width)
        for key, neighbour in (("lo", line - 1), ("hi", line + 1)):
            if not 0 <= neighbour < len(positions):
                continue  # the cluster is on the field edge — nothing to block against
            if key == "lo":
                a, b = positions[neighbour] + ply_width / 2.0, cluster_lo
            else:
                a, b = cluster_hi, positions[neighbour] - ply_width / 2.0
            if b - a <= 1e-6:
                continue
            if along_x:
                q0, q1 = (block_axis, a), (block_axis, b)
            else:
                q0, q1 = (a, block_axis), (b, block_axis)
            out.append(FramedMember(
                system.uid, f"sister-{index}-block-{key}", "blocking", member,
                q0, q1, z0, z1, b - a,
            ))
    return out


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


def _subtract_interval(intervals: list[tuple[float, float]], cut0: float,
                       cut1: float) -> list[tuple[float, float]]:
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


def _wall_footprint_span(wall, across: int) -> tuple[float, float] | None:
    """The wall's plan extent along axis ``across`` (0=x, 1=y), from its layer polygons.

    Read off the resolved polygons rather than ``axis`` +/- half ``thickness_m`` because an
    ``alignment=face(...)`` wall's axis is not its centreline.
    """
    values = [point[across] for layer in wall.layers for point in layer.polygon]
    return (min(values), max(values)) if values else None


def _bearing_footprint_span(model: ResolvedModel, tag: str,
                            across: int) -> tuple[float, float] | None:
    """The plan extent across the member's axis, for a wall *or* a standalone ``Beam``.

    A wall reads its resolved layer polygons (``alignment=face(...)`` means the axis is not
    the centreline). A ``Beam`` has no layers — it is not a resolved wall at all — so its
    width comes off ``Beam.size`` and straddles the axis, which is how the resolver places
    it. Without this, a beam named in ``FloorOpening.bearing_refs`` was skipped outright and
    the edge read as unsupported, putting a header under a beam that plainly carries it.
    """
    wall = model.wall(tag)
    if wall is not None:
        return _wall_footprint_span(wall, across)
    beam = model.plan.by_tag(tag)
    if not isinstance(beam, Beam):
        return None
    axis = _bearing_axis(model, tag)
    if axis is None:
        return None
    half = cross_section(beam.size).width_m / 2.0
    centre = axis[0][across]
    return (centre - half, centre + half)


def _opening_edge_has_declared_bearing(model: ResolvedModel, opening: FloorOpening,
                                       p0: tuple[float, float], p1: tuple[float, float]) -> bool:
    """Does a declared bearing wall carry this whole opening edge?

    The edge is tested against each wall's plan *footprint*, not against its centreline.
    An opening drawn to the finished well — which is what a stair climbs, and what keeps
    its stringers out of the stud cavities — never coincides with a wall axis, so a
    centreline-equality test claimed "no bearing" for every edge a wall plainly carries
    and put a 10' header under it (plans/TODO.md D3).
    """
    covered: list[tuple[float, float]] = []
    vertical = abs(p0[0] - p1[0]) < 1e-9
    across, along = (0, 1) if vertical else (1, 0)
    for tag in opening.bearing_refs:
        axis = _bearing_axis(model, tag)
        if axis is None:
            continue
        a0, a1 = axis
        if abs(a0[across] - a1[across]) > 1e-9:
            continue  # runs across the edge, not along it — it cannot carry its length
        footprint = _bearing_footprint_span(model, tag, across)
        if footprint is None or not (footprint[0] - 1e-9 <= p0[across] <= footprint[1] + 1e-9):
            continue
        covered.append((min(a0[along], a1[along]), max(a0[along], a1[along])))
    if not covered:
        return False
    target0, target1 = min(p0[along], p1[along]), max(p0[along], p1[along])
    cursor = target0
    for start, end in sorted(covered):
        if start > cursor + 1e-9:
            return False
        cursor = max(cursor, end)
    return cursor >= target1 - 1e-9
