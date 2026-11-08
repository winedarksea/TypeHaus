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
RunBand = tuple[str, tuple[Vec2, ...], tuple[float, ...], float]
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
    pieces = [gap]
    for b_lo, b_hi in blocked:
        pieces = [piece for lo, hi in pieces
                  for piece in ((lo, min(hi, b_lo)), (max(lo, b_hi), hi))
                  if piece[1] > piece[0]]
    pieces = [piece for piece in pieces if piece[1] - piece[0] >= MIN_BAY_M]
    return max(pieces, key=lambda piece: piece[1] - piece[0]) if pieces else None


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
) -> tuple[list[FramedMember], list[BlockingConflict]]:
    """A 2x6 box around every run crossing this bay, and a conflict for each misfit.

    The bottom rail is drawn only when every run clears it: a run resting on the plate takes
    the plate as the box's bottom, and the cheeks bear straight on it. A run may touch the
    joist or beam closing the bay; the clearance only places the cheeks.
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
    box_members = [
        block_member(floor, f"{key}-rail-top", BOX_PROFILE, along_x, centre, gap, rail_top, z1)
    ]
    if bottom_rail:
        box_members.append(block_member(floor, f"{key}-rail-bottom", BOX_PROFILE, along_x, centre,
                                   gap, z0, base))
    orient = (0.0, 1.0) if along_x else (1.0, 0.0)
    for side, perp in (("lo", open_lo - BOX_T_M / 2.0), ("hi", open_hi + BOX_T_M / 2.0)):
        if not gap[0] + BOX_T_M / 2.0 <= perp <= gap[1] - BOX_T_M / 2.0:
            continue  # the joist or beam face is that side of the box
        point = (centre, perp) if along_x else (perp, centre)
        box_members.append(
            FramedMember(floor.uid, f"{key}-cheek-{side}", "blocking", BOX_PROFILE,
                         point, point, base, rail_top, rail_top - base, orient=orient)
        )
    return box_members, list(conflicts.values())


def run_bands(model: ResolvedModel) -> list[RunBand]:
    """``(tag, plan path, per-vertex centreline z, outside radius)`` for every routed run."""
    from typehaus.resolve.pipe_sections import (
        pipe_outside_diameter_m,
        raceway_outside_diameter_m,
    )

    out: list[RunBand] = []
    for run in model.pipe_runs:
        if run.z_m and len(run.z_m) == len(run.path):
            out.append((run.tag, tuple(run.path), tuple(run.z_m),
                        pipe_outside_diameter_m(run.diameter_m or 0.0, run.material) / 2.0))
    for duct in model.ducts:
        if len(duct.z_m) == len(duct.path):
            out.append((duct.tag, tuple(duct.path), tuple(duct.z_m),
                        (duct.diameter_m or 0.0) / 2.0))
    for raceway in model.conduits:
        if raceway.z_m and len(raceway.z_m) == len(raceway.path):
            z = tuple(raceway.z_m)  # placed in z: never the schematic end-pair profile
        else:
            start = raceway.z_start_m or 0.0
            end = raceway.z_end_m if raceway.z_end_m is not None else start
            z = (*([start] * (len(raceway.path) - 1)), end)
        out.append((raceway.tag, tuple(raceway.path), z,
                    raceway_outside_diameter_m(raceway.trade_size_m or 0.0,
                                               raceway.material) / 2.0))
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
    blocks_by_radius = {}
    for tag, path, z, radius in runs:
        a0_run, a1_run = base_a0 - radius, base_a1 + radius
        if along_x:
            run_bounds = a0_run, a1_run, gap[0], gap[1]
            block = blocks_by_radius.get(radius)
            if block is None:
                block = box(a0_run, gap[0], a1_run, gap[1])
                blocks_by_radius[radius] = block
        else:
            run_bounds = gap[0], gap[1], a0_run, a1_run
            block = blocks_by_radius.get(radius)
            if block is None:
                block = box(gap[0], a0_run, gap[1], a1_run)
                blocks_by_radius[radius] = block
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
            if max(zs) + radius < z0 + GRAZE_M or min(zs) - radius > z1 - GRAZE_M:
                continue  # under or over the joists, grazing at most
            perps = [xy[1] if along_x else xy[0] for xy in piece.coords]
            out.append((tag, min(perps) - radius, max(perps) + radius,
                        min(zs) - radius, max(zs) + radius))
    return out
