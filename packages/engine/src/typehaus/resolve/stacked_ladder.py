"""A ladder of blocks where a wall stands over another wall along a floor's joists.

Joists running ALONG a stacked line give the wall above nothing but subfloor to stand on:
its line load goes into the nearest joist, not the wall below. Full-depth blocks across the
bay the lower plate sits in, no further apart than the deck's own joist spacing, carry it
down — the bearing course of ``floor_blocking.py`` turned 90 degrees. Catlin's case is
``W-S-SN3`` over ``W-M-HS3`` in ``FS-S-WEST`` (plans/TODO.md, D-M-LAUN item 4).

Each line is read off the RESOLVED deck (its outline less its voids) and left on
``ResolvedModel.stacked_ladders`` station by station: ``carried`` where a joist, trimmer,
rim, header, beam, bearing block or post already stands on the plate; ``block`` where a
block (or a 2x6 box with a cheek on the plate) was laid; ``missing`` where nothing fits.
A partition stopped a deflection gap under the deck takes no ladder; an outdoor wall has
its rim. An open-web truss deck gets the line and no lumber: a block between trusses is no
published detail, so ``structural.stacked_line_ladder`` sends it to the truss designer.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

from typehaus.quantities import inch
from typehaus.resolve.blocking_parts import (
    BASE_TOL_M,
    BAY_EDGES,
    BOX_T_M,
    MIN_BEARING_OVERLAP_M,
    bay_edges_at,
    block_member,
    carrier_spans,
    clip,
    crossing_runs,
    pass_through_box,
)
from typehaus.resolve.layout_lines import collinear_overlap
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedModel

LADDER_BLOCK_PREFIX = "ladder-block-"
_AXIS_TOL_M = 0.5 * 0.0254  # stacking's raw-axis tolerance, as header_loads
_OVERLAP_M = 0.0254  # a run shorter than this touches, it does not carry
_STEP_M = inch(1).meters  # a block slides along its line in these steps
_IN = 0.0254
_POSTS = ("column", "post")
#: Perpendicular members that stand on the plate themselves (a box's rails do not).
_ACROSS = ("blocking", "header", "rim")
_RAILS = ("-rail-top", "-rail-bottom")


@dataclass(frozen=True)
class LadderStation:
    at_m: float  # plan coordinate along the joists
    status: str  # "block" | "carried" | "missing"
    by: str = ""  # what carries it, or why nothing fits


@dataclass(frozen=True)
class LadderLine:
    floor: str
    lowers: tuple[str, ...]
    uppers: tuple[str, ...]
    member: str
    spacing_m: float
    #: Merged laddered runs, plan coordinates along the joists.
    runs: tuple[tuple[float, float], ...]
    open_web: bool = False
    stations: tuple[LadderStation, ...] = ()

    def near(self, lo: float, hi: float) -> list[LadderStation]:
        """The stations bearing on ``lo``..``hi``: within a module of it."""
        return [s for s in self.stations if lo - self.spacing_m < s.at_m < hi + self.spacing_m]


def walls_over(plan, walls, wall) -> list[tuple[object, tuple[float, float]]]:
    """(upper wall, run on ``wall``) on the next storey up of its building on this line."""
    here = plan.storey(wall.storey).elevation.meters
    above = sorted((s for s in plan.storeys_of(plan.building_of(wall.storey))
                    if s.elevation.meters > here), key=lambda s: s.elevation.meters)
    for storey in above:
        runs = [(upper, run) for upper in walls if upper.storey == storey.tag
                and (run := collinear_overlap(wall.axis, upper.axis, _AXIS_TOL_M))
                and run[1] - run[0] > _OVERLAP_M]
        if runs:
            return runs
    return []


def ladder_note(model, wall, upper, lo_pt, hi_pt) -> str | None:
    """How ``upper``'s load crosses the floor onto ``wall`` over ``lo_pt``..``hi_pt``."""
    for line in getattr(model, "stacked_ladders", ()):
        if wall.tag in line.lowers and upper.tag in line.uppers:
            floor = next((f for f in model.floors if f.tag == line.floor), None)
            axis = 0 if floor is None or floor.direction == "x" else 1
            near = [] if line.open_web else line.near(*sorted((lo_pt[axis], hi_pt[axis])))
            if not near or any(s.status == "missing" for s in near):
                return f"assumes a ladder in {line.floor} under {upper.tag}"
            if any(s.status == "block" for s in near):
                return f"on the ladder in {line.floor} under {upper.tag}"
            by = ", ".join(dict.fromkeys(s.by for s in near))
            return f"on {by} in {line.floor} under {upper.tag}"
    return None


def resolve_stacked_ladders(model: ResolvedModel, runs) -> None:
    """Record every ladder line and lay its blocks; from ``floor_blocking`` after the bearing
    course, before the partition tops."""
    from typehaus.resolve.framing.profiles import cross_section

    model.stacked_ladders = []
    for index, floor in enumerate(model.floors):
        system = model.plan.by_tag(floor.tag)
        joists = [m for m in floor.members if m.category == "joist"]
        if getattr(system, "joists", None) is None or not joists:
            continue
        spec = system.joists
        spacing = spec.spacing.meters if spec.spacing is not None else inch(16).meters
        open_web = cross_section(spec.member).shape == "floor_truss"
        laid: list[FramedMember] = []
        for lowers, uppers, spans in _lines(model, floor, joists):
            stations: tuple[LadderStation, ...] = ()
            if not open_web:
                found, laid_here, spans = _ladder(model, floor, spec.member, spacing, joists,
                                                  lowers, spans, runs, laid)
                stations, laid = tuple(found), laid + laid_here
            model.stacked_ladders.append(LadderLine(
                floor.tag, tuple(w.tag for w in lowers), uppers, spec.member, spacing,
                tuple(spans), open_web, stations))
        if laid:
            model.floors[index] = dataclasses.replace(floor, members=(*floor.members, *laid))


def _lines(model, floor: ResolvedFloor, joists):
    """``(lower walls, upper tags, merged runs)`` per stacked line along this deck's joists."""
    from shapely.geometry import LineString, Polygon

    from typehaus.resolve.mep_bore_scope import outdoor_wall_tags
    from typehaus.resolve.partition import (
        bearing_ref_tags,
        framing_top_z_m,
        takes_a_deflection_gap,
    )

    if len(floor.deck_outline) < 3:
        return []
    axis_i, perp_i = (0, 1) if floor.direction == "x" else (1, 0)
    deck = Polygon(floor.deck_outline)
    for void in floor.deck_voids:
        if len(void) >= 3:
            deck = deck.difference(Polygon(void))
    z0 = min(m.z0_m for m in joists)
    outdoor, refs = outdoor_wall_tags(model), bearing_ref_tags(model.plan)
    groups: dict[int, tuple[dict, dict, list]] = {}
    for wall in model.walls:
        (a, b) = wall.axis
        if (wall.tag in outdoor or abs(a[perp_i] - b[perp_i]) > _AXIS_TOL_M
                or abs(a[axis_i] - b[axis_i]) <= _AXIS_TOL_M
                or abs(framing_top_z_m(wall) - z0) > BASE_TOL_M):
            continue
        uppers = [(u, run) for u, run in walls_over(model.plan, model.walls, wall)
                  if u.storey == floor.storey]
        if not uppers or takes_a_deflection_gap(model, wall, refs):
            continue
        length = math.dist(a, b)
        for upper, (s0, s1) in uppers:
            ends = [tuple(p + (q - p) * s / length for p, q in zip(a, b, strict=True))
                    for s in (s0, s1)]
            piece = LineString(ends).intersection(deck)
            for seg in getattr(piece, "geoms", [piece]):
                if seg.is_empty or seg.length <= _OVERLAP_M:
                    continue
                coords = [c[axis_i] for c in seg.coords]
                lowers, ups, spans = groups.setdefault(round(a[perp_i] / _IN), ({}, {}, []))
                lowers[wall.tag] = wall
                ups[upper.tag] = None
                spans.append((min(coords), max(coords)))
    return [(tuple(lowers.values()), tuple(ups), _merged(sorted(spans)))
            for lowers, ups, spans in groups.values()]


def _ladder(model, floor, profile, spacing, joists, lowers, spans, runs, placed):
    """Greedy along each run: the furthest station within a module of the last that bears."""
    from typehaus.resolve.floor_ends import structure_span
    from typehaus.resolve.framing.profiles import cross_section

    along_x = floor.direction == "x"
    axis_i, perp_i = (0, 1) if along_x else (1, 0)
    z0, z1 = min(m.z0_m for m in joists), max(m.z1_m for m in joists)
    width = cross_section(profile).width_m
    tip_lo = min(min(m.p0[axis_i], m.p1[axis_i]) for m in joists) + width / 2
    tip_hi = max(max(m.p0[axis_i], m.p1[axis_i]) for m in joists) - width / 2
    edges = [m for m in floor.members if m.category in (*BAY_EDGES, "rim")
             and abs(m.p0[perp_i] - m.p1[perp_i]) <= 1e-6]
    across = [m for m in floor.members if m.category in _ACROSS
              and abs(m.p0[axis_i] - m.p1[axis_i]) <= 1e-6 and not m.child_key.endswith(_RAILS)]
    posts = [s for s in model.solids if s.category in _POSTS and s.z1_m > z0 and s.z0_m < z1]

    def plate_at(c):
        for wall in lowers:
            lo, hi = sorted((wall.axis[0][axis_i], wall.axis[1][axis_i]))
            if lo - _AXIS_TOL_M <= c <= hi + _AXIS_TOL_M:
                span = structure_span(model, wall.tag, perp_i)
                return wall.tag, span or (wall.axis[0][perp_i] - wall.thickness_m / 2,
                                          wall.axis[0][perp_i] + wall.thickness_m / 2)
        return None, None

    stations: list[LadderStation] = []
    members: list[FramedMember] = []
    half = spacing / 2
    clipped = [(max(lo, tip_lo), min(hi, tip_hi)) for lo, hi in spans]
    for lo, hi in clipped:
        prev = None
        while hi >= lo:
            if prev is not None and prev >= hi - half - 1e-9:
                break
            top = min(lo + half if prev is None else prev + spacing, hi)
            bottom = lo if prev is None else prev + _STEP_M
            found, why = None, "no bay over the plate"
            c = top
            while c >= bottom - 1e-9:
                tag, plate = plate_at(c)
                if plate is not None:
                    carrier = (_carried(edges, across, posts, c, width, plate, axis_i, perp_i)
                               or _beam(model, c, z0, z1, axis_i, perp_i, plate))
                    if carrier:
                        found = LadderStation(c, "carried", carrier)
                        break
                    key = f"{LADDER_BLOCK_PREFIX}{tag}-{c / _IN:.2f}"
                    block, why = _block_at(model, floor, key, profile, c, width, plate, edges,
                                           spacing, runs, (*placed, *members), z0, z1)
                    if block:
                        members.extend(block)
                        found = LadderStation(c, "block")
                        break
                c -= _STEP_M
            stations.append(found or LadderStation(top, "missing", why))
            prev = found.at_m if found else top
    return stations, members, [(lo, hi) for lo, hi in clipped if hi >= lo]


def _block_at(model, floor, key, profile, c, width, plate, edges, spacing, runs, placed, z0,
              z1):
    """The block (or box) at ``c`` if it bears on the plate, else ``None`` and why not."""
    along_x = floor.direction == "x"
    axis_i, perp_i = (0, 1) if along_x else (1, 0)
    lines = bay_edges_at(edges, c, axis_i, perp_i, width / 2.0)
    bays = [(min(clear[1], plate[1]) - max(clear[0], plate[0]), clear)
            for (p_a, w_a), (p_b, w_b) in zip(lines, lines[1:], strict=False)
            if p_b - p_a <= spacing + _IN
            and (clear := (p_a + w_a / 2.0, p_b - w_b / 2.0))]
    if not bays or max(bays)[0] < MIN_BEARING_OVERLAP_M:
        return None, "no bay over the plate"
    gap = clip(max(bays)[1], carrier_spans(model, c, z0, z1, axis_i, perp_i, block_width=width))
    if gap is None or _taken(placed, c, width, gap, axis_i, perp_i):
        return None, "the bay is taken"
    crossing = crossing_runs(runs, along_x, c, width, gap, z0, z1)
    return seated(floor, key, profile, along_x, c, gap, plate, z0, z1, crossing, runs)


def seated(floor, key, profile, along_x, c, gap, plate, z0, z1, crossing, runs=()):
    """A solid block, or a 2x6 box only where a cheek stands on the plate: a box whose
    cheeks are off the plate carries the wall above into the joists, not down."""
    if not crossing:
        if min(gap[1], plate[1]) - max(gap[0], plate[0]) >= MIN_BEARING_OVERLAP_M - 1e-9:
            return [block_member(floor, key, profile, along_x, c, gap, z0, z1)], ""
        return None, "the clear bay misses the plate"
    box, clashes = pass_through_box(floor, key, along_x, c, gap, z0, z1, crossing, (), runs)
    if clashes:
        return None, f"{clashes[0].run_tag} cannot clear a 2x6 box"
    perp_i = 1 if along_x else 0
    if any(m.child_key.endswith(("-cheek-lo", "-cheek-hi"))
           and min(m.p0[perp_i] + BOX_T_M / 2, plate[1])
           - max(m.p0[perp_i] - BOX_T_M / 2, plate[0]) >= MIN_BEARING_OVERLAP_M - 1e-9
           for m in box):
        return box, ""
    runs = sorted({tag for tag, *_rest in crossing})
    return None, f"{', '.join(runs)} along the plate leave(s) no cheek on it"


def _carried(edges, across, posts, c, width, plate, axis_i, perp_i) -> str:
    """What already stands on the plate at ``c``: a joist, trimmer or rim along it, a block,
    header or rim across it, or a post."""
    from typehaus.resolve.framing.profiles import cross_section

    def bears(lo, hi):
        return min(hi, plate[1]) - max(lo, plate[0]) >= MIN_BEARING_OVERLAP_M - 1e-9

    for m in edges:
        lo, hi = sorted((m.p0[axis_i], m.p1[axis_i]))
        half = cross_section(m.profile).width_m / 2
        if lo <= c <= hi and bears(m.p0[perp_i] - half, m.p0[perp_i] + half):
            return m.child_key
    for m in across:
        lo, hi = sorted((m.p0[perp_i], m.p1[perp_i]))
        if lo == hi:
            lo, hi = lo - BOX_T_M / 2, hi + BOX_T_M / 2  # a box cheek
        if abs(m.p0[axis_i] - c) <= width / 2 + _IN / 2 and bears(lo, hi):
            return m.child_key
    for solid in posts:
        along = [p[axis_i] for p in solid.outline]
        if min(along) <= c <= max(along) and bears(min(p[perp_i] for p in solid.outline),
                                                    max(p[perp_i] for p in solid.outline)):
            return solid.tag
    return ""


def _beam(model, c, z0, z1, axis_i, perp_i, plate) -> str:
    spans = carrier_spans(model, c, z0, z1, axis_i, perp_i)
    if any(min(hi, plate[1]) - max(lo, plate[0]) >= MIN_BEARING_OVERLAP_M for lo, hi in spans):
        return "a beam or opening header"
    return ""


def _merged(spans):
    out: list[tuple[float, float]] = []
    for lo, hi in spans:
        if out and lo <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def _taken(members, centre, width, gap, axis_i, perp_i) -> bool:
    """Another block already in this bay at this station."""
    reach = width + _IN / 2
    return any(m.category == "blocking" and abs(m.p0[axis_i] - centre) < reach
               and min(m.p0[perp_i], m.p1[perp_i]) < gap[1]
               and max(m.p0[perp_i], m.p1[perp_i]) > gap[0] for m in members)
