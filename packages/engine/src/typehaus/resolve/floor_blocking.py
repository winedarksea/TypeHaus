"""Full-depth blocking at a floor's two joints with a wall — the bearing line, and the
partition top under it.

A joist field carries a wall's gravity load across its bearing only through the joists
themselves, whose webs are not a column. The wall above bears on a course of full-depth
blocks between the joists, one per bay, over the plate below. Only interior and shared lines
get this pass: an outer line has its rim, and a flush beam carries its joists in hangers
with no plate under them to block over.

**Where a pipe, duct or raceway crosses the line** the bay gets a box instead of a solid
block: a flat 2x6 rail under the subfloor, a flat 2x6 rail on the plate, and 2x6 cheeks
either side of the pass-through, so the wall load still reaches the plate around the hole.
A run too big for the box is recorded on ``ResolvedFloor.blocking_conflicts`` and
``mep.run_through_blocking`` fails it.

**And the mirror joint: blocking ABOVE a partition that runs BETWEEN two joists.** The
bearing pass above blocks a line a wall stands ON. A non-bearing partition standing in a
joist bay has the opposite problem — its top plate stops 3/4" clear of the deck on Simpson
SDPW DEFLECTOR screws (``resolve/partition_top.py``) and those screws have to land in
something, so every framing module along such a wall gets a block between the two joists
either side of it. That blocking was called for by ``takeoff/partition_fasteners.py``'s
count and framed by nothing until 2026-09-19, so the take-off billed 4 1/2 dozen screws
into lumber the bill of materials did not carry. It is laid at the SAME module the screw
count uses — ``resolve/partition_fasteners.py`` is the one reading both take — and it
takes the same 2x6 box where a run crosses it.

A wall over a wall along the joists gets a ladder of blocks (``stacked_ladder.py``).

Over a ROOF the same condition exists and is still unframed: this pass is a floor's, and
blocking between rafters belongs to roof framing.

Runs after ``resolve_mep`` (the boxes need the runs), and replaces each blocked
``ResolvedFloor`` whole.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import cast

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
from typehaus.hardware.plan_geometry import point_in_ring
from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.quantities import inch
from typehaus.resolve.blocking_parts import (
    BASE_TOL_M,
    BAY_EDGES,
    LINE_TOL_M,
    MIN_BEARING_OVERLAP_M,
    RAIL_W_M,
    BlockingConflict,
    RunBand,
    Span,
    bay_edges_at,
    block_member,
    carrier_spans,
    clip,
    crossing_runs,
    pass_through_box,
    run_bands,
)
from typehaus.resolve.floor_ends import FloorEnds, structure_span
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import (
    FramedMember,
    ResolvedFloor,
    ResolvedModel,
    ResolvedWall,
    Vec2,
)
from typehaus.resolve.partition import framing_top_z_m
from typehaus.resolve.partition_fasteners import (
    BETWEEN_MEMBERS,
    PARTITION_BLOCK_PREFIX,
    PartitionTopJoint,
    partition_top_joints,
)

#: A partition top under a deck sits one deflection gap clear of it. This is how far the
#: framing top may miss the joists' underside and still be that joint — the gap, the 2x6
#: box's own slack, and nothing more.
_PARTITION_TOP_WINDOW_M = inch(2).meters
#: A bay narrower than this needs no partition-top block: the wall is hard against a joist
#: ply or a trimmer and the screw has that member to land in. ``MIN_BAY_M``'s 2" is the
#: bearing course's rule, where a short block still carries load; a 2 1/2" filler between
#: two plies is not a nailer.
_MIN_PARTITION_BAY_M = inch(6).meters





def resolve_bearing_blocking(model: ResolvedModel) -> None:
    runs = run_bands(model)
    for index, floor in enumerate(model.floors):
        system = model.plan.by_tag(floor.tag)
        if system is None or floor.ends is None:
            continue
        system = cast(FloorSystem, system)
        members, conflicts = _floor_blocking(model, floor, system, runs)
        if members or conflicts:
            model.floors[index] = dataclasses.replace(
                floor, members=(*floor.members, *members),
                blocking_conflicts=tuple(conflicts))
    # A wall over a wall along the joists: its ladder is a bearing course too.
    from typehaus.resolve.stacked_ladder import resolve_stacked_ladders

    resolve_stacked_ladders(model, runs)
    # ** STRICTLY AFTER the bearing course, and that ordering is load-bearing. ** A bearing
    # block is real structure over whatever crosses under it, so a partition under one is a
    # PERPENDICULAR crossing and not a wall in a bay — and ``takeoff/partition_fasteners.py``
    # asks the same question of the finished model. Reading it before the bearing course was
    # laid classified six walls the other way from the take-off that bills their screws.
    joints = [joint for joint
              in partition_top_joints(
                  model, DEFAULT_HARDWARE_TAKEOFF_CONFIG.partition_deflection)[0]
              if joint.scope == BETWEEN_MEMBERS]
    for index, floor in enumerate(model.floors):
        system = model.plan.by_tag(floor.tag)
        if system is None or floor.ends is None:
            continue
        system = cast(FloorSystem, system)
        members, _unframed = _partition_top_blocking(model, floor, system, runs, joints)
        if members:
            model.floors[index] = dataclasses.replace(
                model.floors[index],
                members=(*model.floors[index].members, *members))


def _floor_blocking(
    model: ResolvedModel,
    floor: ResolvedFloor,
    system: FloorSystem,
    runs: list[RunBand],
) -> tuple[list[FramedMember], list[BlockingConflict]]:
    spec = system.joists
    along_x = floor.direction == "x"
    axis_i, perp_i = (0, 1) if along_x else (1, 0)
    joists = [m for m in floor.members if m.category == "joist"]
    if not joists:
        return [], []
    width = cross_section(spec.member).width_m
    spacing = spec.spacing.meters if spec.spacing is not None else inch(16).meters
    z0, z1 = min(m.z0_m for m in joists), max(m.z1_m for m in joists)
    walls_above = [w for w in model.walls
                   if w.storey == floor.storey and not w.is_foundation
                   and abs(w.z0_m - z1) <= BASE_TOL_M]
    edges = [m for m in floor.members if m.category in BAY_EDGES
             and abs(m.p0[perp_i] - m.p1[perp_i]) <= 1e-6]
    ends = cast(FloorEnds, floor.ends)  # guarded by the resolver entry point

    members: list[FramedMember] = []
    conflicts: list[BlockingConflict] = []
    lines_below = _walls_below(model, floor.storey, _line_coords(model, spec, axis_i),
                               z0, axis_i, perp_i)
    for line_index, (coord, spans) in enumerate(_merge_lines(lines_below)):
        # A shared end's joists stop inside the plate, just short of the line; its blocks
        # stay on its own side, flush with those tips. An interior line is blocked on centre.
        if ends.shared_lo and abs(coord - ends.tip_lo) < LINE_TOL_M:
            tip, inward = ends.tip_lo, 1.0
        elif ends.shared_hi and abs(coord - ends.tip_hi) < LINE_TOL_M:
            tip, inward = ends.tip_hi, -1.0
        elif ends.tip_lo < coord < ends.tip_hi:
            tip, inward = coord, 0.0
        else:
            continue
        above = [span for lo, hi in spans
                 for span in _overlap_above(walls_above, coord, lo, hi, axis_i, perp_i)]
        if not above:
            continue
        blocked = carrier_spans(model, coord, z0, z1, axis_i, perp_i)
        lines = bay_edges_at(edges, coord, axis_i, perp_i)
        for bay, ((p_a, w_a), (p_b, w_b)) in enumerate(zip(lines, lines[1:], strict=False)):
            if p_b - p_a > spacing + inch(1).meters:
                continue  # an opening between them, not one bay
            # Any real overlap, not the bay's midpoint: a wall ending mid-bay still has an
            # end stud to carry down.
            clear = (p_a + w_a / 2.0, p_b - w_b / 2.0)
            if not any(min(a_hi, clear[1]) - max(a_lo, clear[0]) >= MIN_BEARING_OVERLAP_M
                       for a_lo, a_hi in above):
                continue
            gap = clip((p_a + w_a / 2.0, p_b - w_b / 2.0), blocked)
            if gap is None:
                continue
            key = f"bearing-block-{line_index}-{bay:03d}"
            block_centre = tip + inward * width / 2.0
            crossing = crossing_runs(runs, along_x, block_centre, width, gap, z0, z1)
            if not crossing:
                members.append(block_member(floor, key, spec.member, along_x, block_centre, gap,
                                       z0, z1))
                continue
            box, box_conflicts = pass_through_box(
                floor, key, along_x, tip + inward * RAIL_W_M / 2.0, gap, z0, z1, crossing)
            members.extend(box)
            conflicts.extend(box_conflicts)
    return members, conflicts


def _partition_top_blocking(
    model: ResolvedModel,
    floor: ResolvedFloor,
    system: FloorSystem,
    runs: list[RunBand],
    joints: list[PartitionTopJoint],
) -> tuple[list[FramedMember], list[str]]:
    """Blocks between joists over every partition standing IN a bay of this deck.

    The mirror of the bearing pass: there the wall is under the line and the block carries
    it down; here the wall stops short of the deck and the block is what the deflection
    screw lands in. One per framing module along the wall, fencepost at both ends — the
    same count ``takeoff/partition_fasteners.py`` bills the screws at, from the same
    reading, so the screws and the lumber can never disagree.

    **A bay a run occupies gets the same 2x6 box, and a bay the box cannot clear gets
    NOTHING.** That is the one place this pass differs from the bearing course, and it is
    deliberate: a bearing block carries load and a bay it cannot reach is a defect
    ``mep.run_through_blocking`` must fail. This block carries none — it is a nailer — so a
    bay already full of pipe is a station the screw moves off, not a broken load path, and
    asserting an unbuildable box there would fire a bearing-line check at a joint that is
    not one. What is NOT laid is named on the check's own finding.
    """
    spec = system.joists
    along_x = floor.direction == "x"
    axis_i, perp_i = (0, 1) if along_x else (1, 0)
    joists = [m for m in floor.members if m.category == "joist"]
    if not joists:
        return [], []
    z0, z1 = min(m.z0_m for m in joists), max(m.z1_m for m in joists)
    spacing = spec.spacing.meters if spec.spacing is not None else inch(16).meters
    width = cross_section(spec.member).width_m
    tip_lo = min(min(m.p0[axis_i], m.p1[axis_i]) for m in joists)
    tip_hi = max(max(m.p0[axis_i], m.p1[axis_i]) for m in joists)
    # Every member that closes a bay, not the joists alone: an opening's trimmers and a
    # flush beam bound one too, and a block cut to a joist line through either of them is
    # an interpenetration ``structural.member_interference`` reports (and did).
    edges = [m for m in floor.members if m.category in BAY_EDGES
             and abs(m.p0[perp_i] - m.p1[perp_i]) <= 1e-6]

    members: list[FramedMember] = []
    unframed: list[str] = []
    for joint in joints:
        wall = model.wall(joint.wall_tag)
        if wall is None:
            continue
        (a, b) = wall.axis
        # Parallel to the joists, and stopping just under THIS deck. A partition in the
        # storey below another deck reads the same in plan; only the elevation tells them
        # apart, and a wall whose plate is not within a gap of these joists is not this
        # deck's joint.
        if abs(a[perp_i] - b[perp_i]) > 1e-6:
            continue
        if not 0.0 <= z0 - framing_top_z_m(wall) <= _PARTITION_TOP_WINDOW_M:
            continue
        # ** AND it has to be under THIS deck in plan. ** Two decks meeting on a bearing
        # line share an elevation, so without the plan gate a wall in one field is blocked
        # in both — on catlin that doubled every second-storey partition into FS-S-EAST.
        midpoint = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        if not floor.deck_outline or not point_in_ring(midpoint, floor.deck_outline):
            continue
        lo, hi = sorted((a[axis_i], b[axis_i]))
        # A block stays inside this deck's own joists: centred on a bearing line two decks
        # share, half of it stood in the neighbour's joist ends.
        lo, hi = max(lo, tip_lo + width / 2.0), min(hi, tip_hi - width / 2.0)
        if hi < lo:
            continue
        # Only bay edges that actually run beside this wall bound its bay: a member whose
        # own extent misses the wall names no face to cut a block to.
        bay = _straddling_bay(_bay_lines(edges, axis_i, perp_i, lo, hi), a[perp_i], spacing)
        if bay is None:
            unframed.append(joint.wall_tag)
            continue
        for step in range(int((hi - lo) / spacing + 1e-9) + 1):  # fencepost, both ends
            centre = lo + step * spacing
            # A block has to reach BOTH faces of the bay to be the nailer this screw needs.
            # A beam standing in the bay leaves a stub, and a 2 1/2" stub is not a block —
            # ``clip``'s longest-surviving-piece rule is right for a bearing course, where
            # a short block still carries, and wrong here.
            gap = bay
            if any(b_lo < gap[1] and b_hi > gap[0] for b_lo, b_hi
                   in carrier_spans(model, centre, z0, z1, axis_i, perp_i, block_width=width)):
                unframed.append(joint.wall_tag)
                continue
            key = f"{PARTITION_BLOCK_PREFIX}{joint.wall_tag}-{step:03d}"
            crossing = crossing_runs(runs, along_x, centre, width, gap, z0, z1)
            if not crossing:
                members.append(block_member(floor, key, spec.member, along_x, centre, gap, z0, z1))
                continue
            box, box_conflicts = pass_through_box(floor, key, along_x, centre, gap, z0, z1,
                                                  crossing)
            if box_conflicts:
                unframed.append(joint.wall_tag)
                continue
            members.extend(box)
    return members, unframed


def _bay_lines(
    edges: Sequence[FramedMember], axis_i: int, perp_i: int, lo: float, hi: float,
) -> list[Span]:
    """Sorted ``(perp, width)`` of the bay edges that run beside ``lo``..``hi``."""
    lines: dict[float, float] = {}
    for member in edges:
        m_lo, m_hi = sorted((member.p0[axis_i], member.p1[axis_i]))
        if m_hi < lo - LINE_TOL_M or m_lo > hi + LINE_TOL_M:
            continue
        perp = round(member.p0[perp_i], 6)
        lines[perp] = max(lines.get(perp, 0.0), cross_section(member.profile).width_m)
    return sorted(lines.items())


def _straddling_bay(lines: Sequence[Span], perp: float, spacing: float) -> Span | None:
    """The clear bay between the two bay edges either side of ``perp``, or ``None``."""
    below = [entry for entry in lines if entry[0] <= perp]
    above = [entry for entry in lines if entry[0] > perp]
    if not below or not above:
        return None
    (p_a, w_a), (p_b, w_b) = below[-1], above[0]
    if p_b - p_a > spacing + inch(1).meters:
        return None  # an opening or a beam between them, not one bay
    gap = (p_a + w_a / 2.0, p_b - w_b / 2.0)
    return gap if gap[1] - gap[0] >= _MIN_PARTITION_BAY_M else None


def _line_coords(model: ResolvedModel, spec: JoistSpec, axis_i: int) -> list[float]:
    """Axis coordinates of the floor's bearing lines, walls and beams alike."""
    coords = []
    for tag in spec.bearing_refs:
        wall = model.wall(tag)
        axis = wall.axis if wall is not None else _beam_axis(model, tag)
        if axis is not None and abs(axis[0][axis_i] - axis[1][axis_i]) <= 1e-6:
            coords.append(axis[0][axis_i])
    return coords


def _beam_axis(model: ResolvedModel, tag: str) -> tuple[Vec2, Vec2] | None:
    from typehaus.hardware.plan_geometry import centerline_endpoints

    solid = next((s for s in model.solids if s.tag == tag), None)
    if solid is None or not solid.outline:
        return None
    return centerline_endpoints(list(solid.outline))


def _walls_below(
    model: ResolvedModel,
    storey: str,
    coords: list[float],
    z0: float,
    axis_i: int,
    perp_i: int,
) -> list[tuple[float, float, float]]:
    """``(structure centre, perp lo, perp hi)`` of every wall under a bearing line.

    By geometry, not ``bearing_refs``: a line names one of its collinear walls and bears on
    all of them (catlin's W-M-C3 carries FS-S-* and neither deck names it).
    """
    out: list[tuple[float, float, float]] = []
    for wall in model.walls:
        if wall.storey == storey:
            continue
        (a, b) = wall.axis
        if abs(a[axis_i] - b[axis_i]) > 1e-6:
            continue
        if not any(abs(a[axis_i] - c) <= LINE_TOL_M for c in coords):
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        if abs(top - z0) > BASE_TOL_M:
            continue
        span = structure_span(model, wall.tag, axis_i)
        coord = (span[0] + span[1]) / 2.0 if span else a[axis_i]
        out.append((coord, min(a[perp_i], b[perp_i]), max(a[perp_i], b[perp_i])))
    return sorted(out)


def _merge_lines(
    lines: Sequence[tuple[float, float, float]],
) -> list[tuple[float, list[Span]]]:
    """Collinear walls under one line, their perp extents merged: one course per line.

    Two walls overlapping in plan on one line (catlin's x=18' basement run) would otherwise
    lay two blocks in each shared bay.
    """
    merged: list[tuple[float, list[tuple[float, float]]]] = []
    for coord, lo, hi in sorted(lines):
        if merged and abs(coord - merged[-1][0]) <= LINE_TOL_M:
            spans = merged[-1][1]
        else:
            spans = []
            merged.append((coord, spans))
        if spans and lo <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], hi))
        else:
            spans.append((lo, hi))
        spans.sort()
    return merged


def _overlap_above(
    walls_above: Sequence[ResolvedWall],
    coord: float,
    lo: float,
    hi: float,
    axis_i: int,
    perp_i: int,
) -> list[Span]:
    out: list[Span] = []
    for wall in walls_above:
        (a, b) = wall.axis
        if abs(a[axis_i] - b[axis_i]) > 1e-6 or abs(a[axis_i] - coord) > LINE_TOL_M:
            continue
        w_lo, w_hi = max(lo, min(a[perp_i], b[perp_i])), min(hi, max(a[perp_i], b[perp_i]))
        if w_hi > w_lo:
            out.append((w_lo, w_hi))
    return out
