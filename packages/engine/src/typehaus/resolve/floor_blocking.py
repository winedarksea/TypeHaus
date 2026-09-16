"""Full-depth blocking where a wall above stands on a floor's bearing line.

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

Runs after ``resolve_mep`` (the boxes need the runs), and replaces each blocked
``ResolvedFloor`` whole.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from typehaus.quantities import inch
from typehaus.resolve.floor_ends import structure_span
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel

#: The pass-through box's lumber: flat for the rails, on edge for the cheeks.
BOX_PROFILE = "2x6"
_BOX_T_M = inch(1.5).meters
_RAIL_W_M = inch(5.5).meters
#: Clearance from a run's outside to a cheek.
BOX_CLEARANCE_M = inch(0.5).meters
#: Members that close a joist bay at a bearing line.
_BAY_EDGES = ("joist", "sister_joist", "trimmer")
#: A gap narrower than this is two plies face to face, not a bay to block.
_MIN_BAY_M = inch(2).meters
#: Fit slack: a run tangent to a rail or a face still fits.
_FIT_TOL_M = inch(0.0625).meters
#: A run standing this little into the joist depth passes under or over the block.
_GRAZE_M = inch(0.25).meters
#: A wall counts as on the line when its axis is this close to it.
_LINE_TOL_M = inch(3).meters
#: How far a wall's base or top may miss the joist field's own face (subfloor, plate).
_BASE_TOL_M = inch(2).meters


@dataclass(frozen=True)
class BlockingConflict:
    """A run crossing a blocked bay that the 2x6 box cannot clear."""

    run_tag: str
    member_key: str
    reason: str


def resolve_bearing_blocking(model: ResolvedModel) -> None:
    runs = _run_bands(model)
    for index, floor in enumerate(model.floors):
        system = model.plan.by_tag(floor.tag)
        if system is None or floor.ends is None:
            continue
        members, conflicts = _floor_blocking(model, floor, system, runs)
        if members or conflicts:
            model.floors[index] = dataclasses.replace(
                floor, members=(*floor.members, *members),
                blocking_conflicts=tuple(conflicts))


def _floor_blocking(model, floor: ResolvedFloor, system, runs):
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
                   and abs(w.z0_m - z1) <= _BASE_TOL_M]
    edges = [m for m in floor.members if m.category in _BAY_EDGES
             and abs(m.p0[perp_i] - m.p1[perp_i]) <= 1e-6]
    ends = floor.ends

    members: list[FramedMember] = []
    conflicts: list[BlockingConflict] = []
    lines_below = _walls_below(model, floor.storey, _line_coords(model, spec, axis_i),
                               z0, axis_i, perp_i)
    for line_index, (coord, spans) in enumerate(_merge_lines(lines_below)):
        # A shared end's joists stop inside the plate, just short of the line; its blocks
        # stay on its own side, flush with those tips. An interior line is blocked on centre.
        if ends.shared_lo and abs(coord - ends.tip_lo) < _LINE_TOL_M:
            tip, inward = ends.tip_lo, 1.0
        elif ends.shared_hi and abs(coord - ends.tip_hi) < _LINE_TOL_M:
            tip, inward = ends.tip_hi, -1.0
        elif ends.tip_lo < coord < ends.tip_hi:
            tip, inward = coord, 0.0
        else:
            continue
        above = [span for lo, hi in spans
                 for span in _overlap_above(walls_above, coord, lo, hi, axis_i, perp_i)]
        if not above:
            continue
        blocked = _carrier_spans(model, coord, z0, z1, axis_i, perp_i)
        lines = _bay_edges_at(edges, coord, axis_i, perp_i)
        for bay, ((p_a, w_a), (p_b, w_b)) in enumerate(zip(lines, lines[1:], strict=False)):
            if p_b - p_a > spacing + inch(1).meters:
                continue  # an opening between them, not one bay
            if not any(a_lo <= (p_a + p_b) / 2.0 <= a_hi for a_lo, a_hi in above):
                continue
            gap = _clip((p_a + w_a / 2.0, p_b - w_b / 2.0), blocked)
            if gap is None:
                continue
            key = f"bearing-block-{line_index}-{bay:03d}"
            block_centre = tip + inward * width / 2.0
            crossing = _crossing_runs(runs, along_x, block_centre, width, gap, z0, z1)
            if not crossing:
                members.append(_member(floor, key, spec.member, along_x, block_centre, gap,
                                       z0, z1))
                continue
            box, box_conflicts = _box(floor, key, along_x, tip + inward * _RAIL_W_M / 2.0,
                                      gap, z0, z1, crossing)
            members.extend(box)
            conflicts.extend(box_conflicts)
    return members, conflicts


def _line_coords(model, spec, axis_i: int) -> list[float]:
    """Axis coordinates of the floor's bearing lines, walls and beams alike."""
    coords = []
    for tag in spec.bearing_refs:
        wall = model.wall(tag)
        axis = wall.axis if wall is not None else _beam_axis(model, tag)
        if axis is not None and abs(axis[0][axis_i] - axis[1][axis_i]) <= 1e-6:
            coords.append(axis[0][axis_i])
    return coords


def _beam_axis(model, tag: str):
    from typehaus.hardware.plan_geometry import centerline_endpoints

    solid = next((s for s in model.solids if s.tag == tag), None)
    if solid is None or not solid.outline:
        return None
    return centerline_endpoints(list(solid.outline))


def _walls_below(model, storey: str, coords: list[float], z0: float, axis_i: int,
                 perp_i: int) -> list[tuple[float, float, float]]:
    """``(structure centre, perp lo, perp hi)`` of every wall under a bearing line.

    By geometry, not ``bearing_refs``: a line names one of its collinear walls and bears on
    all of them (catlin's W-M-C3 carries FS-S-* and neither deck names it).
    """
    out = []
    for wall in model.walls:
        if wall.storey == storey:
            continue
        (a, b) = wall.axis
        if abs(a[axis_i] - b[axis_i]) > 1e-6:
            continue
        if not any(abs(a[axis_i] - c) <= _LINE_TOL_M for c in coords):
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        if abs(top - z0) > _BASE_TOL_M:
            continue
        span = structure_span(model, wall.tag, axis_i)
        coord = (span[0] + span[1]) / 2.0 if span else a[axis_i]
        out.append((coord, min(a[perp_i], b[perp_i]), max(a[perp_i], b[perp_i])))
    return sorted(out)


def _merge_lines(lines):
    """Collinear walls under one line, their perp extents merged: one course per line.

    Two walls overlapping in plan on one line (catlin's x=18' basement run) would otherwise
    lay two blocks in each shared bay.
    """
    merged: list[tuple[float, list[tuple[float, float]]]] = []
    for coord, lo, hi in sorted(lines):
        if merged and abs(coord - merged[-1][0]) <= _LINE_TOL_M:
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


def _overlap_above(walls_above, coord: float, lo: float, hi: float,
                   axis_i: int, perp_i: int) -> list[tuple[float, float]]:
    out = []
    for wall in walls_above:
        (a, b) = wall.axis
        if abs(a[axis_i] - b[axis_i]) > 1e-6 or abs(a[axis_i] - coord) > _LINE_TOL_M:
            continue
        w_lo, w_hi = max(lo, min(a[perp_i], b[perp_i])), min(hi, max(a[perp_i], b[perp_i]))
        if w_hi > w_lo:
            out.append((w_lo, w_hi))
    return out


def _bay_edges_at(edges, coord: float, axis_i: int, perp_i: int):
    """Sorted ``(perp, width)`` of the members bounding bays at this line.

    Joists, sister plies and opening trimmers all close a bay; a block is cut to their faces.
    """
    reach = _LINE_TOL_M + inch(4).meters
    lines: dict[float, float] = {}
    for member in edges:
        lo, hi = sorted((member.p0[axis_i], member.p1[axis_i]))
        if lo - reach <= coord <= hi + reach:
            perp = round(member.p0[perp_i], 6)
            lines[perp] = max(lines.get(perp, 0.0), cross_section(member.profile).width_m)
    return sorted(lines.items())


def _carrier_spans(model, coord: float, z0: float, z1: float, axis_i: int,
                   perp_i: int) -> list[tuple[float, float]]:
    """Perp extents of beams on this line in the joist depth: no plate under them."""
    out = []
    for solid in model.solids:
        if solid.category != "beam" or solid.z1_m <= z0 or solid.z0_m >= z1:
            continue
        axis = [p[axis_i] for p in solid.outline]
        if min(axis) - _LINE_TOL_M <= coord <= max(axis) + _LINE_TOL_M:
            perps = [p[perp_i] for p in solid.outline]
            out.append((min(perps), max(perps)))
    return out


def _clip(gap, blocked):
    """The longest part of ``gap`` clear of every blocked span, or ``None``."""
    if gap[1] - gap[0] < _MIN_BAY_M:
        return None  # plies face to face
    pieces = [gap]
    for b_lo, b_hi in blocked:
        pieces = [piece for lo, hi in pieces
                  for piece in ((lo, min(hi, b_lo)), (max(lo, b_hi), hi))
                  if piece[1] > piece[0]]
    pieces = [piece for piece in pieces if piece[1] - piece[0] >= _MIN_BAY_M]
    return max(pieces, key=lambda piece: piece[1] - piece[0]) if pieces else None


def _member(floor, key, profile, along_x, centre, gap, z0, z1):
    if along_x:
        p0, p1 = (centre, gap[0]), (centre, gap[1])
    else:
        p0, p1 = (gap[0], centre), (gap[1], centre)
    return FramedMember(floor.uid, key, "blocking", profile, p0, p1, z0, z1, gap[1] - gap[0])


def _box(floor, key, along_x, centre, gap, z0, z1, crossing):
    """A 2x6 box around every run crossing this bay, and a conflict for each misfit.

    The bottom rail is drawn only when every run clears it: a run resting on the plate takes
    the plate as the box's bottom, and the cheeks bear straight on it. A run may touch the
    joist or beam closing the bay; the clearance only places the cheeks.
    """
    inch_m = inch(1).meters
    open_lo = min(c[1] for c in crossing) - BOX_CLEARANCE_M
    open_hi = max(c[2] for c in crossing) + BOX_CLEARANCE_M
    rail_top = z1 - _BOX_T_M
    bottom_rail = min(c[3] for c in crossing) >= z0 + _BOX_T_M - _FIT_TOL_M
    base = z0 + _BOX_T_M if bottom_rail else z0
    conflicts = {}
    for tag, p_lo, p_hi, _r_lo, r_hi in crossing:
        if r_hi > rail_top + _FIT_TOL_M:
            conflicts[tag] = BlockingConflict(
                tag, key, f"its crown at {r_hi / inch_m:.2f}\" is above the box's 2x6 top "
                          f"rail at {rail_top / inch_m:.2f}\"")
        elif p_lo < gap[0] - _FIT_TOL_M or p_hi > gap[1] + _FIT_TOL_M:
            conflicts[tag] = BlockingConflict(
                tag, key, "runs into the joist or beam face that closes the bay")
    box = [_member(floor, f"{key}-rail-top", BOX_PROFILE, along_x, centre, gap, rail_top, z1)]
    if bottom_rail:
        box.append(_member(floor, f"{key}-rail-bottom", BOX_PROFILE, along_x, centre, gap,
                           z0, base))
    orient = (0.0, 1.0) if along_x else (1.0, 0.0)
    for side, perp in (("lo", open_lo - _BOX_T_M / 2.0), ("hi", open_hi + _BOX_T_M / 2.0)):
        if not gap[0] + _BOX_T_M / 2.0 <= perp <= gap[1] - _BOX_T_M / 2.0:
            continue  # the joist or beam face is that side of the box
        point = (centre, perp) if along_x else (perp, centre)
        box.append(FramedMember(floor.uid, f"{key}-cheek-{side}", "blocking", BOX_PROFILE,
                                point, point, base, rail_top, rail_top - base, orient=orient))
    return box, list(conflicts.values())


def _run_bands(model) -> list[tuple[str, tuple, tuple, float]]:
    """``(tag, plan path, per-vertex centreline z, outside radius)`` for every routed run."""
    from typehaus.resolve.pipe_sections import (
        pipe_outside_diameter_m,
        raceway_outside_diameter_m,
    )

    out = []
    for run in model.pipe_runs:
        if run.z_m and len(run.z_m) == len(run.path):
            out.append((run.tag, tuple(run.path), tuple(run.z_m),
                        pipe_outside_diameter_m(run.diameter_m or 0.0, run.material) / 2.0))
    for duct in model.ducts:
        if len(duct.z_m) == len(duct.path):
            out.append((duct.tag, tuple(duct.path), tuple(duct.z_m),
                        (duct.diameter_m or 0.0) / 2.0))
    for raceway in model.conduits:
        start = raceway.z_start_m or 0.0
        end = raceway.z_end_m if raceway.z_end_m is not None else start
        z = (*([start] * (len(raceway.path) - 1)), end)
        out.append((raceway.tag, tuple(raceway.path), z,
                    raceway_outside_diameter_m(raceway.trade_size_m or 0.0) / 2.0))
    return out


def _crossing_runs(runs, along_x: bool, centre: float, width: float, gap, z0, z1):
    """``(tag, perp lo, perp hi, z lo, z hi)`` of the run surfaces inside this block."""
    from shapely.geometry import LineString, Point, box

    out = []
    for tag, path, z, radius in runs:
        a0, a1 = centre - width / 2.0 - radius, centre + width / 2.0 + radius
        block = box(a0, gap[0], a1, gap[1]) if along_x else box(gap[0], a0, gap[1], a1)
        for i in range(len(path) - 1):
            pa, pb = path[i], path[i + 1]
            if abs(pa[0] - pb[0]) < 1e-9 and abs(pa[1] - pb[1]) < 1e-9:
                continue  # a riser passes through the plate, not between joists
            leg = LineString([pa, pb])
            piece = leg.intersection(block)
            if piece.is_empty or piece.length <= 0:
                continue
            ts = [leg.project(Point(xy)) / leg.length for xy in piece.coords]
            zs = [z[i] + (z[i + 1] - z[i]) * t for t in ts]
            if max(zs) + radius < z0 + _GRAZE_M or min(zs) - radius > z1 - _GRAZE_M:
                continue  # under or over the joists, grazing at most
            perps = [xy[1] if along_x else xy[0] for xy in piece.coords]
            out.append((tag, min(perps) - radius, max(perps) + radius,
                        min(zs) - radius, max(zs) + radius))
    return out
