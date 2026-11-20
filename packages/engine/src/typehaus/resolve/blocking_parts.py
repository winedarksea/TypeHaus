"""Shared parts of a block between joists: the clipped bay, the solid block, the 2x6
pass-through box around a run, and the runs that cross a block's footprint.

``floor_blocking.py`` (bearing lines, partition tops) and ``stacked_ladder.py`` (a wall over
a wall along the joists) lay their blocks with these.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from typehaus.quantities import inch
from typehaus.resolve.floor_opening_support import header_blocking_spans
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel, Vec2

#: The pass-through box's lumber: flat for the rails, on edge for the cheeks.
BOX_PROFILE = "2x6"
BOX_T_M = inch(1.5).meters
RAIL_W_M = inch(5.5).meters
#: Clearance from a run's outside to a cheek.
BOX_CLEARANCE_M = inch(0.5).meters
#: How far a cheek may slide along its rail piece to clear a run; the rail then overhangs it.
CHEEK_SLIDE_MAX_M = inch(3).meters
CHEEK_SLIDE_STEP_M = inch(0.125).meters
#: Members that close a joist bay at a bearing line.
BAY_EDGES = ("joist", "sister_joist", "trimmer")
#: A gap narrower than this is two plies face to face, not a bay to block.
MIN_BAY_M = inch(2).meters
#: Fit slack: a run tangent to a rail or a face still fits.
FIT_TOL_M = inch(0.0625).meters
#: A run standing this little into the joist depth passes under or over the block.
GRAZE_M = inch(0.25).meters
#: A wall counts as on the line when its axis is this close to it.
LINE_TOL_M = inch(3).meters
#: A wall above takes a bearing block once it covers one stud's thickness of the bay.
MIN_BEARING_OVERLAP_M = inch(1.5).meters
#: How far a wall's base or top may miss the joist field's own face (subfloor, plate).
BASE_TOL_M = inch(2).meters


@dataclass(frozen=True)
class BlockingConflict:
    """A run crossing a blocked bay that the 2x6 box cannot clear."""

    run_tag: str
    member_key: str
    reason: str



Span = tuple[float, float]
#: ``(tag, plan path, per-vertex centreline z, half-width in plan, half-height in z)``
RunBand = tuple[str, tuple[Vec2, ...], tuple[float, ...], float, float]
Crossing = tuple[str, float, float, float, float]


def bay_edges_at(
    edges: Sequence[FramedMember], coord: float, axis_i: int, perp_i: int,
) -> list[Span]:
    """Sorted ``(perp, width)`` of the members bounding bays at this line.

    Joists, sister plies and opening trimmers all close a bay; a block is cut to their faces.
    """
    reach = LINE_TOL_M + inch(4).meters
    lines: dict[float, float] = {}
    for member in edges:
        lo, hi = sorted((member.p0[axis_i], member.p1[axis_i]))
        if lo - reach <= coord <= hi + reach:
            perp = round(member.p0[perp_i], 6)
            lines[perp] = max(lines.get(perp, 0.0), cross_section(member.profile).width_m)
    return sorted(lines.items())


def carrier_spans(
    model: ResolvedModel, coord: float, z0: float, z1: float, axis_i: int, perp_i: int,
    *, block_width: float = 0.0,
) -> list[Span]:
    """Beams and opening headers occupying this station: no duplicate block over them."""
    out = header_blocking_spans(model, coord, z0, z1, axis_i, perp_i, block_width)
    for solid in model.solids:
        if solid.category != "beam" or solid.z1_m <= z0 or solid.z0_m >= z1:
            continue
        axis = [p[axis_i] for p in solid.outline]
        if min(axis) - LINE_TOL_M <= coord <= max(axis) + LINE_TOL_M:
            perps = [p[perp_i] for p in solid.outline]
            out.append((min(perps), max(perps)))
    return out


def clip(gap: Span, blocked: Sequence[Span]) -> Span | None:
    """The longest part of ``gap`` clear of every blocked span, or ``None``."""
    if gap[1] - gap[0] < MIN_BAY_M:
        return None  # plies face to face
    pieces = _pieces(gap, blocked)
    return max(pieces, key=lambda piece: piece[1] - piece[0]) if pieces else None


def _pieces(gap: Span, cuts: Sequence[Span]) -> list[Span]:
    """What is left of ``gap`` outside ``cuts``, each piece at least ``MIN_BAY_M`` long."""
    pieces = [gap]
    for c_lo, c_hi in cuts:
        pieces = [piece for lo, hi in pieces
                  for piece in ((lo, min(hi, c_lo)), (max(lo, c_hi), hi))
                  if piece[1] > piece[0]]
    return [piece for piece in pieces if piece[1] - piece[0] >= MIN_BAY_M]


def solid_block_profile(member: str) -> str:
    """A solid block's profile in a field of ``member``. Between open-web trusses it is sawn
    SPF ripped to their depth, not a truss: its holes are R502.8.1's, not a fabricator's."""
    section = cross_section(member)
    if section is not None and section.shape == "floor_truss":
        return f"1.5x{section.depth_m / inch(1).meters:g}:spf"
    return member


def block_member(
    floor: ResolvedFloor,
    key: str,
    profile: str,
    along_x: bool,
    centre: float,
    gap: Span,
    z0: float,
    z1: float,
) -> FramedMember:
    if along_x:
        p0, p1 = (centre, gap[0]), (centre, gap[1])
    else:
        p0, p1 = (gap[0], centre), (gap[1], centre)
    return FramedMember(floor.uid, key, "blocking", profile, p0, p1, z0, z1, gap[1] - gap[0])


def pass_through_box(
    floor: ResolvedFloor,
    key: str,
    along_x: bool,
    centre: float,
    gap: Span,
    z0: float,
    z1: float,
    crossing: Sequence[Crossing],
    risers: Sequence[Span] = (),
    runs: Sequence[RunBand] = (),
) -> tuple[list[FramedMember], list[BlockingConflict]]:
    """A 2x6 box around every run crossing this bay, and a conflict for each misfit.

    ``risers``: perp spans a plumb run opens in the rails (``riser_cuts``). Rail pieces too short
    to bear are dropped, and a cheek stands where a piece ends at the hole.

    The bottom rail is drawn only when every run clears it: a run resting on the plate takes
    the plate as the box's bottom, and the cheeks bear straight on it. A run may touch the
    joist or beam closing the bay; the clearance only places the cheeks.

    ``runs``: every run's band. A cheek (the cheeks are ``RAIL_W_M`` wide) that lands on a run
    slides along its rail piece to clear it, or is left out, as is one a seated cheek already
    covers; ``structural.bearing_block_seat`` grades a beam's bearing stud left with none.
    """
    inch_m = inch(1).meters
    open_lo = min(c[1] for c in crossing) - BOX_CLEARANCE_M
    open_hi = max(c[2] for c in crossing) + BOX_CLEARANCE_M
    rail_top = z1 - BOX_T_M
    bottom_rail = min(c[3] for c in crossing) >= z0 + BOX_T_M - FIT_TOL_M
    base = z0 + BOX_T_M if bottom_rail else z0
    conflicts: dict[str, BlockingConflict] = {}
    for tag, p_lo, p_hi, _r_lo, r_hi in crossing:
        if r_hi > rail_top + FIT_TOL_M:
            conflicts[tag] = BlockingConflict(
                tag, key, f"its crown at {r_hi / inch_m:.2f}\" is above the box's 2x6 top "
                          f"rail at {rail_top / inch_m:.2f}\"")
        elif p_lo < gap[0] - FIT_TOL_M or p_hi > gap[1] + FIT_TOL_M:
            conflicts[tag] = BlockingConflict(
                tag, key, "runs into the joist or beam face that closes the bay")
    pieces = _pieces(gap, sorted(risers))
    box_members = []
    for n, (lo, hi) in enumerate(pieces):
        tag = "" if n == 0 else f"-p{n}"
        box_members.append(block_member(floor, f"{key}{tag}-rail-top", BOX_PROFILE, along_x,
                                        centre, (lo, hi), rail_top, z1))
        if bottom_rail:
            box_members.append(block_member(floor, f"{key}{tag}-rail-bottom", BOX_PROFILE,
                                            along_x, centre, (lo, hi), z0, base))
    orient = (0.0, 1.0) if along_x else (1.0, 0.0)
    posts = [(f"-cheek-{side}", perp) for side, perp in
             (("lo", open_lo - BOX_T_M / 2.0), ("hi", open_hi + BOX_T_M / 2.0))]
    # A piece ending at a riser's hole rests on a cheek there, so the rail never cantilevers.
    posts += [(f"-cheek-r{n}{end}", edge) for n, (lo, hi) in enumerate(pieces)
              for end, edge, cut in (("l", lo + BOX_T_M / 2.0, lo > gap[0] + FIT_TOL_M),
                                     ("h", hi - BOX_T_M / 2.0, hi < gap[1] - FIT_TOL_M)) if cut]
    hazards = _leg_hazards(runs, along_x, centre, gap, base, rail_top) if runs else []
    seated: list[float] = []
    for name, perp in posts:
        if not gap[0] + BOX_T_M / 2.0 <= perp <= gap[1] - BOX_T_M / 2.0:
            continue  # the joist or beam face is that side of the box
        piece = next(((lo, hi) for lo, hi in pieces if lo - FIT_TOL_M <= perp <= hi + FIT_TOL_M),
                     gap)
        perp = _clear_cheek(perp, piece, hazards, along_x, centre, seated)
        if perp is None:
            continue  # a run stands there, or a cheek already carries this spot
        seated.append(perp)
        point = (centre, perp) if along_x else (perp, centre)
        box_members.append(
            FramedMember(floor.uid, f"{key}{name}", "blocking", BOX_PROFILE,
                         point, point, base, rail_top, rail_top - base, orient=orient)
        )
    return box_members, list(conflicts.values())


def _leg_hazards(runs: Sequence[RunBand], along_x: bool, centre: float, gap: Span,
                 z0: float, z1: float) -> list:
    """Plan shapes of the run legs (and risers) in the box footprint, within z ``z0``..``z1``."""
    from shapely.geometry import LineString, Point, box

    reach = RAIL_W_M / 2.0
    out = []
    for _tag, path, z, half_w, half_h in runs:
        bounds = ((centre - reach - half_w, gap[0] - half_w, centre + reach + half_w,
                   gap[1] + half_w) if along_x else
                  (gap[0] - half_w, centre - reach - half_w, gap[1] + half_w,
                   centre + reach + half_w))
        footprint = None
        for i in range(len(path) - 1):
            pa, pb = path[i], path[i + 1]
            low, high = min(z[i], z[i + 1]) - half_h, max(z[i], z[i + 1]) + half_h
            # Raw z and bounds tests first: shapely objects for every leg of every run cost
            # half a second of resolve.
            if not (high > z0 and low < z1
                    and min(pa[0], pb[0]) <= bounds[2] and max(pa[0], pb[0]) >= bounds[0]
                    and min(pa[1], pb[1]) <= bounds[3] and max(pa[1], pb[1]) >= bounds[1]):
                continue
            footprint = footprint or box(*bounds)
            leg = Point(pa) if pa == pb else LineString([pa, pb])
            if footprint.intersects(leg):
                out.append(leg.buffer(half_w))
    return out


def _clear_cheek(perp: float, piece: Span, hazards: Sequence, along_x: bool, centre: float,
                 seated: Sequence[float]) -> float | None:
    """The perp station nearest ``perp`` inside ``piece`` (within ``CHEEK_SLIDE_MAX_M``) where a
    cheek clears every hazard and overlaps no seated cheek; ``None`` if there is none."""
    from shapely.geometry import box

    half = BOX_T_M / 2.0
    steps = round(CHEEK_SLIDE_MAX_M / CHEEK_SLIDE_STEP_M)
    for n in range(steps + 1):
        for sign in ((1.0, -1.0) if n else (1.0,)):
            at = perp + sign * n * CHEEK_SLIDE_STEP_M
            if not piece[0] + half - FIT_TOL_M <= at <= piece[1] - half + FIT_TOL_M:
                continue
            if any(abs(at - other) < BOX_T_M - FIT_TOL_M for other in seated):
                return None  # a cheek already stands within a cheek's width of here
            lo, hi = at - half + FIT_TOL_M, at + half - FIT_TOL_M
            along = (centre - RAIL_W_M / 2.0, centre + RAIL_W_M / 2.0)
            shape = box(along[0], lo, along[1], hi) if along_x else box(lo, along[0], hi, along[1])
            if not any(shape.intersects(h) for h in hazards):
                return at
    return None


def riser_cuts(runs: Sequence[RunBand], along_x: bool, centre: float, gap: Span,
               z0: float, z1: float) -> list[Span]:
    """Perp spans a plumb leg (a riser) opens in a box's rails: each one standing in the
    rails' ``RAIL_W_M`` footprint about ``centre`` over the joist depth, its section plus the
    box's clearance. ``crossing_runs`` skips risers (they pass the plate), so without this a
    riser beside the block stands on a rail the box was never framed round."""
    out: list[Span] = []
    for _tag, path, z, half_w, half_h in runs:
        for i in range(len(path) - 1):
            pa, pb = path[i], path[i + 1]
            if abs(pa[0] - pb[0]) > 1e-9 or abs(pa[1] - pb[1]) > 1e-9:
                continue
            along, perp = (pa[0], pa[1]) if along_x else (pa[1], pa[0])
            low, high = sorted((z[i], z[i + 1]))
            if (abs(along - centre) > RAIL_W_M / 2.0 + half_w
                    or high + half_h < z0 + GRAZE_M or low - half_h > z1 - GRAZE_M):
                continue
            lo, hi = perp - half_w - BOX_CLEARANCE_M, perp + half_w + BOX_CLEARANCE_M
            if hi > gap[0] and lo < gap[1]:
                out.append((lo, hi))
    return sorted(out)


def run_bands(model: ResolvedModel) -> list[RunBand]:
    """A ``RunBand`` per routed run: round is its outside radius both ways, a rectangular
    duct its width/2 across the leg in plan and its depth/2 in z (a horizontal leg)."""
    from typehaus.resolve.pipe_sections import (
        pipe_outside_diameter_m,
        raceway_outside_diameter_m,
    )

    out: list[RunBand] = []
    for run in model.pipe_runs:
        if run.z_m and len(run.z_m) == len(run.path):
            radius = pipe_outside_diameter_m(run.diameter_m or 0.0, run.material) / 2.0
            out.append((run.tag, tuple(run.path), tuple(run.z_m), radius, radius))
    for duct in model.ducts:
        if len(duct.z_m) == len(duct.path):
            if duct.diameter_m is None and duct.width_m and duct.depth_m:
                half_w, half_h = duct.width_m / 2.0, duct.depth_m / 2.0
            else:
                half_w = half_h = (duct.diameter_m or 0.0) / 2.0
            out.append((duct.tag, tuple(duct.path), tuple(duct.z_m), half_w, half_h))
    for raceway in model.conduits:
        if raceway.z_m and len(raceway.z_m) == len(raceway.path):
            z = tuple(raceway.z_m)  # placed in z: never the schematic end-pair profile
        else:
            start = raceway.z_start_m or 0.0
            end = raceway.z_end_m if raceway.z_end_m is not None else start
            z = (*([start] * (len(raceway.path) - 1)), end)
        radius = raceway_outside_diameter_m(raceway.trade_size_m or 0.0,
                                            raceway.material) / 2.0
        out.append((raceway.tag, tuple(raceway.path), z, radius, radius))
    return out


def crossing_runs(
    runs: Sequence[RunBand],
    along_x: bool,
    centre: float,
    width: float,
    gap: Span,
    z0: float,
    z1: float,
) -> list[Crossing]:
    """``(tag, perp lo, perp hi, z lo, z hi)`` of the run surfaces inside this block."""
    from shapely.geometry import LineString, Point, box

    out: list[Crossing] = []
    base_a0, base_a1 = centre - width / 2.0, centre + width / 2.0
    blocks_by_half_w = {}
    for tag, path, z, half_w, half_h in runs:
        a0_run, a1_run = base_a0 - half_w, base_a1 + half_w
        if along_x:
            run_bounds = a0_run, a1_run, gap[0], gap[1]
            block = blocks_by_half_w.get(half_w)
            if block is None:
                block = box(a0_run, gap[0], a1_run, gap[1])
                blocks_by_half_w[half_w] = block
        else:
            run_bounds = gap[0], gap[1], a0_run, a1_run
            block = blocks_by_half_w.get(half_w)
            if block is None:
                block = box(gap[0], a0_run, gap[1], a1_run)
                blocks_by_half_w[half_w] = block
        for i in range(len(path) - 1):
            pa, pb = path[i], path[i + 1]
            if abs(pa[0] - pb[0]) < 1e-9 and abs(pa[1] - pb[1]) < 1e-9:
                continue  # a riser passes through the plate, not between joists
            segment_bounds = (min(pa[0], pb[0]), max(pa[0], pb[0]),
                              min(pa[1], pb[1]), max(pa[1], pb[1]))
            if (segment_bounds[1] < run_bounds[0] or segment_bounds[0] > run_bounds[1]
                    or segment_bounds[3] < run_bounds[2] or segment_bounds[2] > run_bounds[3]):
                continue
            leg = LineString([pa, pb])
            piece = leg.intersection(block)
            if piece.is_empty or piece.length <= 0:
                continue
            ts = [leg.project(Point(xy)) / leg.length for xy in piece.coords]
            zs = [z[i] + (z[i + 1] - z[i]) * t for t in ts]
            if max(zs) + half_h < z0 + GRAZE_M or min(zs) - half_h > z1 - GRAZE_M:
                continue  # under or over the joists, grazing at most
            perps = [xy[1] if along_x else xy[0] for xy in piece.coords]
            out.append((tag, min(perps) - half_w, max(perps) + half_w,
                        min(zs) - half_h, max(zs) + half_h))
    return out
