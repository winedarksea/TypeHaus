"""Floor deck framing: FloorSystem JoistSpec -> joist FramedMembers (→ 30 WP3.4/3.7).

One joist line per spacing position across the deck's perpendicular extent (both ends
included), split into spans at each bearing line.
Opening headers and trimmers: ``resolve/floor_openings.py``.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import FloorOpeningPurpose
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import Beam
from typehaus.quantities import inch
from typehaus.resolve.floor_ends import floor_ends
from typehaus.resolve.floor_lines import extra_lines, move_lines
from typehaus.resolve.floor_openings import (
    _shift,
    opening_frames,
    opening_members,
    within_one_bay,
)
from typehaus.resolve.floor_tilt import joist_lift, twisted
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel, Ring
from typehaus.resolve.through_deck import through_deck_cuts, through_deck_walls

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
    z1 = (system.top_elevation.meters if system.top_elevation is not None
          else storey.elevation.meters)
    z0 = z1 - depth
    # A field on TILTED bearings (``Beam.top_rise_end``): each joist end sits on its own
    # bearing's top at the joist's station, so ``lift`` is read off the bearings and the datum
    # above is the joist top where the first bearing starts (``resolve/floor_tilt.py``).
    tilt = joist_lift(model.plan, [(tag, _axis_coord(axis)) for tag, axis
                                   in zip(spec.bearing_refs, bearing_axes, strict=True)
                                   if axis is not None], boundaries, along_x)

    def lift(axis: float, perp: float) -> float:
        """How far the field has risen at ``axis`` along a joist on line ``perp``."""
        return 0.0 if tilt is None else tilt.at(axis, perp)

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
    opening_boxes, opening_findings = opening_frames(
        model, system, along_x, boundaries, ends, depth)
    if opening_boxes is None:
        return None, opening_findings

    members: list[FramedMember] = []
    positions: list[float] = []
    position = perp0
    while position <= perp1 + 1e-9:
        positions.append(position)
        position += spacing
    if positions and positions[-1] < perp1 - 1e-6:
        positions.append(perp1)
    findings = move_lines(system, positions, perp0, perp1)
    extra, extra_findings = extra_lines(system, positions, perp0, perp1)
    findings += extra_findings
    opening_boxes = within_one_bay(opening_boxes, positions + extra)

    # Anything shorter than the joist's own depth is bearing seat, not span. An opening
    # drawn to a bearing wall's *near face* stops short of the bearing line the span is cut
    # at, and the remainder — 3 3/8" of deck over the top plate, where the trimmer actually
    # sits — is not a joist. Emitting it put stub members in the frame and the take-off.
    min_segment_m = _member_depth_m(spec.member)
    lines = [(f"{index:03d}", perp) for index, perp in enumerate(positions)]
    lines += [(f"x{index:02d}", perp) for index, perp in enumerate(extra)]
    for index, perp in lines:
        for span_index in range(len(boundaries) - 1):
            a, b = boundaries[span_index], boundaries[span_index + 1]
            # Cantilever only the two outer joist tips past the outermost bearing lines;
            # interior spans and opening-clipping are unchanged.
            if span_index == 0:
                a = ends.tip_lo
            if span_index == len(boundaries) - 2:
                b = ends.tip_hi
            segments = [(a, b)]
            for frame in opening_boxes:
                segments = frame.clip(segments, perp)
            for segment_index, (segment_a, segment_b) in enumerate(segments):
                if segment_b - segment_a <= min_segment_m:
                    continue
                if along_x:
                    p0, p1 = (segment_a, perp), (segment_b, perp)
                else:
                    p0, p1 = (perp, segment_a), (perp, segment_b)
                lift_a, lift_b = lift(segment_a, perp), lift(segment_b, perp)
                rakes = abs(lift_b - lift_a) > 1e-9
                members.append(FramedMember(
                    system.uid, f"joist-{span_index}-{index}-{segment_index}", "joist",
                    spec.member, p0, p1, z0 + lift_a, z1 + lift_a, segment_b - segment_a,
                    z0_end_m=(z0 + lift_b) if rakes else None,
                    z1_end_m=(z1 + lift_b) if rakes else None,
                ))

    # Sistered plies + solid blocking under an authored concentrated load. This runs on the
    # joist field above (it needs its line positions and its cantilevered axis extent), and
    # before the opening/rim framing so a reinforced line is already in ``members`` when the
    # rim is drawn to the same tips.
    # Every laid line, extra ones included: a block cut against the regular lines alone
    # would run straight through an authored extra joist.
    members.extend(_reinforcement_members(
        system, spec, sorted(positions + extra), along_x, ends.tip_lo, ends.tip_hi, z0, z1,
        lift if tilt is not None else None))

    # Opening framing after clipping: headers on edges with no declared bearing, trimmer
    # packs bearing to bearing (resolve/floor_openings.py).
    members.extend(opening_members(system, opening_boxes, along_x, z0, z1, depth))

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
        # A rim runs from ``perp0`` to ``perp1`` — ALONG the fall — so on a tilted field it
        # is a raked member, and it says so through the end elevations rather than being
        # drawn level and left to interpenetrate the joists it closes.
        rim_a, rim_b = lift(boundary, perp0), lift(boundary, perp1)
        rim_rakes = abs(rim_b - rim_a) > 1e-9
        members.append(FramedMember(
            system.uid, f"rim-{rim_index}", "rim", rim_profile, r0, r1, z0 + rim_a, z1 + rim_a,
            perp1 - perp0, material=spec.rim_material,
            z0_end_m=(z0 + rim_b) if rim_rakes else None,
            z1_end_m=(z1 + rim_b) if rim_rakes else None,
        ))

    # The subfloor sheet over the joist field. Its extent is the framed field itself —
    # bearing line to bearing line including both cantilevers, by the joists' perpendicular
    # extent — because that is exactly what the decking is nailed to. Openings are cut out
    # rather than drawn over: the joists were already clipped to them.
    deck_outline: Ring = []
    deck_voids: tuple[Ring, ...] = ()
    through_walls: tuple = ()
    deck_z0_m = deck_z1_m = z1
    deck_plane = None
    if tilt is not None:
        deck_plane, miss = tilt.plane(perp0, perp1)
        if twisted(miss):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.floor_plane",
                message=f"floor {system.tag}: its tilted bearings miss one deck plane by "
                        f"{miss / inch(1).meters:.2f}\"; the joists follow them, the deck "
                        "sheet is drawn on the plane through the outer two",
                element_tags=(system.tag,), result=Result.FAIL))
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
        deck_z1_m = z1 + system.subfloor.thickness.meters
        # A wall that passes through this deck cuts the sheet and nothing else — no header,
        # no trimmer, no hanger, and no authored FloorOpening (decision #78,
        # ``resolve/through_deck.py``). It deliberately does NOT enter ``opening_boxes``
        # above: ``frame.clip`` would then cut the joists at it, and a 4 5/8" pier mid-span
        # would turn one 18'-0" joist into 14'-7" + 3'-0", both over the 11 7/8" floor, both
        # emitted, both billed, the short one bearing on nothing — and
        # ``integrity.floor_end_bearing`` grades a deck's two ends, not a segment's. Nor is
        # it a chase: ``routing/corridors.chase_corridors`` would offer a riser lane through
        # solid brick.
        # The band a through-wall must clear is the tilted deck's whole range.
        lift_lo, lift_hi = _plane_range(deck_plane, deck_outline)
        through_walls = through_deck_walls(model, system, z0 + lift_lo, deck_z1_m + lift_hi,
                                           deck_outline)
        deck_voids = tuple(
            [(f.minx, f.miny), (f.maxx, f.miny), (f.maxx, f.maxy), (f.minx, f.maxy)]
            for f in opening_boxes
        ) + through_deck_cuts(through_walls, members, deck_outline)

    chases = tuple(
        (f.opening.tag, [(f.minx, f.miny), (f.maxx, f.miny),
                         (f.maxx, f.maxy), (f.minx, f.maxy)])
        for f in opening_boxes
        if getattr(f.opening, "purpose", None) is FloorOpeningPurpose.CHASE)
    penetrations = tuple(
        (f.opening.tag, [(f.minx, f.miny), (f.maxx, f.miny),
                         (f.maxx, f.maxy), (f.minx, f.maxy)],
         tuple(getattr(f.opening, "penetration_for", ()) or ()))
        for f in opening_boxes
        if getattr(f.opening, "penetration_for", ()))

    panels = None
    if (spec.web_panel_pitch is not None and spec.web_opening_width is not None
            and spec.web_panel_offset is not None):
        panels = (spec.web_panel_pitch.meters, spec.web_opening_width.meters,
                  spec.web_panel_offset.meters)

    return ResolvedFloor(
        uid=system.uid, tag=system.tag, storey=storey.tag, web_panels=panels,
        direction=spec.direction, members=tuple(members), chases=chases,
        penetrations=penetrations,
        deck_outline=deck_outline, deck_voids=deck_voids,
        deck_z0_m=deck_z0_m, deck_z1_m=deck_z1_m, deck_plane=deck_plane, ends=ends,
        through_walls=tuple(w.tag for w in through_walls),
        deck_material_ref=(system.subfloor.material_ref if system.subfloor else None),
    ), findings


def _plane_range(plane, ring) -> tuple[float, float]:
    lifts = [plane.lift(*p) for p in ring] if plane is not None and ring else [0.0]
    return min(lifts), max(lifts)


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
                           z0: float, z1: float, lift=None) -> list[FramedMember]:
    """Sister plies + blocking for each of ``system.reinforcements``.

    The plies run the *whole* joist — bearing line to bearing line including both
    cantilevers — because a sister that stops at the support carries nothing where the load
    actually is (out on the overhang, for the catlin porch). The blocks run to the adjacent
    joist line on each side, cut to the clear gap between member faces so the frame does not
    read as a clash in ``structural.member_interference``.

    **Two reinforcements on ONE joist line share their plies.** catlin's porch is the case:
    both centre balcony pillars stand at x = 18'-0", one on each beam line, and a sister runs
    the whole joist, so the pack authored under the first is already under the second. Laying
    each entry's plies independently put two members in one place — billed twice, drawn
    twice — and computed the second entry's blocks against a bare joist, so they ran straight
    through the sisters the first entry had laid (``structural.member_interference``, two
    FAILs). ``laid`` is what makes the second entry see the first: it tops the cluster up to
    the deepest ``plies`` any entry on that line asks for, and every entry's blocks are cut
    against the finished cluster.
    """
    out: list[FramedMember] = []
    if not positions:
        return out
    #: joist line index -> (cluster lo, cluster hi, sisters laid, the side they went)
    laid: dict[int, tuple[float, float, int, float]] = {}
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
        existing_lo, existing_hi, existing, existing_sign = laid.get(
            line, (perp - ply_width / 2.0, perp + ply_width / 2.0, 0, 0.0))
        # The first entry on a line picks the side (toward the load); later ones extend the
        # pack that is already there rather than starting a second one on the other face.
        sign = existing_sign or (1.0 if perp_at >= perp else -1.0)
        normal = (0.0, sign) if along_x else (sign, 0.0)
        if along_x:
            p0, p1 = (axis_lo, perp), (axis_hi, perp)
        else:
            p0, p1 = (perp, axis_lo), (perp, axis_hi)
        # A sister runs BESIDE its joist, so on a tilted field it takes that joist's own
        # end heights (``lift``) — the same line, one ply over.
        raise_a = lift(axis_lo, perp) if lift is not None else 0.0
        raise_b = lift(axis_hi, perp) if lift is not None else 0.0
        sister_rakes = abs(raise_b - raise_a) > 1e-9
        for ply in range(existing, plies - 1):
            s0, s1 = _shift(p0, p1, normal, (ply + 1) * ply_width)
            out.append(FramedMember(
                system.uid, f"sister-{index}-{ply}", "sister_joist", member,
                s0, s1, z0 + raise_a, z1 + raise_a, axis_hi - axis_lo,
                z0_end_m=(z0 + raise_b) if sister_rakes else None,
                z1_end_m=(z1 + raise_b) if sister_rakes else None,
            ))
        # Outer faces of the finished cluster (authored joist + every ply on this line,
        # this entry's and any earlier entry's).
        sisters = max(existing, plies - 1)
        spread = sign * sisters * ply_width
        cluster_lo = min(existing_lo, perp - ply_width / 2.0 + min(0.0, spread))
        cluster_hi = max(existing_hi, perp + ply_width / 2.0 + max(0.0, spread))
        laid[line] = (cluster_lo, cluster_hi, sisters, sign)
        if not reinforcement.blocking:
            continue
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
            # A block spans BETWEEN two joist lines, so on a tilted field it rakes across
            # the step between them, exactly as the rim does along the whole fall.
            start = lift(block_axis, a) if lift is not None else 0.0
            block_z0, block_z1 = z0 + start, z1 + start
            block_end = lift(block_axis, b) - start if lift is not None else 0.0
            out.append(FramedMember(
                system.uid, f"sister-{index}-block-{key}", "blocking", member,
                q0, q1, block_z0, block_z1, b - a,
                z0_end_m=(block_z0 + block_end) if block_end else None,
                z1_end_m=(block_z1 + block_end) if block_end else None,
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
