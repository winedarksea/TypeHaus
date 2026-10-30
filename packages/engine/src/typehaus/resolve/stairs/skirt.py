"""Stair skirt boards: the raked board on each wall-backed side of a scoped flight (#85).

The skirt goes up first, so the treads, risers and side stringers butt it: on a skirted side
each moves inboard by the board's thickness (``plan_skirts``). The board is a
``FramedMember`` carrying the swept ``elevation_profile`` a cut stringer does, so every
emitter draws it unchanged. Hand-worked basis: houses/catlin/notes/stair_skirt_basis.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from shapely.geometry import Polygon, box

from typehaus.findings import Finding
from typehaus.findings import element_error as _error
from typehaus.model.spatial import Stair
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.overlay import difference, intersection
from typehaus.resolve.stairs.common import _WELL_PARTITION_THICKNESS_M, _ascent

# A wall finish face this close to a lane edge backs it: catlin's lanes sit 0.02"-0.24" off
# their walls' paint, either side.
_FACE_ON_EDGE_M = 0.5 * 0.0254
# The skirt's bottom edge runs this far below the throat line (tread top meets riser face),
# so the board hides every tread and riser end.
_COVER_BELOW_THROAT_M = 0.5 * 0.0254
# A backing that covers less of the flight's run than this is a stub, not a side to skirt.
_MIN_BACKED_FRACTION = 0.5
_MERGE_GAP_M = 1e-3
_SKIRT_LAYOUTS = frozenset({"straight", "u_split_landing", "u_level_landing"})


@dataclass(frozen=True)
class SkirtedEdge:
    """One flight side a skirt backs onto: ``edge`` is the lane's cross coordinate (the
    board's back face), ``outward`` points from the lane toward the backing, and ``s`` is
    distance up the flight (``along``)."""

    treads: tuple[str, ...]
    cross_axis: int
    lane: tuple[float, float]
    edge: float
    outward: int
    sign: int
    backing: tuple[float, float]
    # Ascent-s intervals where a to-storey wall continues the face above the arrival floor.
    above_arrival: tuple[tuple[float, float], ...]
    # The arrival deck's well edge on this face, which backs the board where it rises
    # above the deck's underside (the stairhead, past the last wall).
    opening: tuple[float, float] | None = None

    def along(self, point: tuple[float, float]) -> float:
        return point[1 - self.cross_axis] * self.sign


@dataclass(frozen=True)
class SkirtPlan:
    material_ref: str
    thickness_m: float
    board_width_m: float
    base_height_m: float
    # Underside of the arrival deck's framing, or None: where its well edge starts to back.
    deck_underside_m: float | None
    edges: tuple[SkirtedEdge, ...]
    # Stringer child key -> how far it moved off the wall for its skirt (``bearing.py``).
    offsets: dict[str, float]


def plan_skirts(model: ResolvedModel, stair: Stair, members: tuple[FramedMember, ...],
                outline, deck_underside_m: float | None
                ) -> tuple[SkirtPlan | None, tuple[FramedMember, ...], list[Finding]]:
    """Find the skirted sides of a scoped flight and move its treads, risers and side
    stringers inboard to butt the boards. Runs before ``set_tread_nosing_lines``."""
    standard = _trim_standard(model, stair)
    if standard is None:
        return None, members, []
    if stair.layout not in _SKIRT_LAYOUTS or stair.carriage != "stringer":
        return None, members, [_error(
            "integrity.stair_skirt", f"stair {stair.tag}: a skirt is derived for a straight "
            "or U flight on raked stringers only", stair.tag)]
    spec = standard.stair_skirt
    edges = tuple(replace(edge, opening=_opening_interval(outline, edge))
                  for edge in skirted_edges(model, stair, members))
    members, offsets = inset_for_skirts(members, edges, spec.thickness.meters)
    return SkirtPlan(spec.material_ref, spec.thickness.meters, spec.board_width.meters,
                     standard.base_height.meters, deck_underside_m, edges,
                     offsets), members, []


def _trim_standard(model: ResolvedModel, stair: Stair):
    from typehaus.model.millwork import TrimStandard

    return next((el for el in model.plan.all_elements() if isinstance(el, TrimStandard)
                 and el.stair_skirt is not None and stair.tag in el.stair_skirt.stair_refs),
                None)


def _flights(members: tuple[FramedMember, ...]) -> dict[tuple, list[FramedMember]]:
    """Straight treads grouped by lane and ascent: one entry per flight."""
    groups: dict[tuple, list[FramedMember]] = {}
    for member in members:
        if member.category != "tread" or member.riser_line is None:
            continue
        ux, uy = _ascent(member)
        cross_axis = 0 if abs(ux) < 0.5 else 1
        sign = round(uy if cross_axis == 0 else ux)
        a, b = member.riser_line
        lo, hi = sorted((a[cross_axis], b[cross_axis]))
        groups.setdefault((cross_axis, sign, round(lo, 6), round(hi, 6)), []).append(member)
    return groups


def skirted_edges(model: ResolvedModel, stair: Stair,
                  members: tuple[FramedMember, ...]) -> list[SkirtedEdge]:
    """Each flight lane edge a from-storey wall face or the well partition backs."""
    out = []
    for (cross_axis, sign, lo, hi), treads in sorted(_flights(members).items()):
        run_axis = 1 - cross_axis
        first = min(t.riser_line[0][run_axis] * sign for t in treads)
        lane_members = [m for m in members if m.category in ("tread", "riser")
                        and _in_lane(m, cross_axis, lo, hi)]
        head = max(p[run_axis] * sign for m in lane_members for p in member_footprint(m)[0])
        for edge, outward in ((lo, -1), (hi, 1)):
            probe = SkirtedEdge((), cross_axis, (lo, hi), edge, outward, sign, (0, 0), ())
            backing = _merge(_wall_intervals(model, stair.from_storey, probe)
                             + _partition_intervals(members, probe))
            best = max(backing, key=lambda iv: min(iv[1], head) - max(iv[0], first),
                       default=None)
            if best is None or (min(best[1], head) - max(best[0], first)
                                < _MIN_BACKED_FRACTION * (head - first)):
                continue
            out.append(replace(probe, treads=tuple(t.child_key for t in treads),
                               backing=best, above_arrival=tuple(_merge(
                                   _wall_intervals(model, stair.to_storey, probe)))))
    return out


def _in_lane(member: FramedMember, cross_axis: int, lo: float, hi: float) -> bool:
    ends = (member.p0[cross_axis], member.p1[cross_axis])
    return (abs(member.p0[1 - cross_axis] - member.p1[1 - cross_axis]) < 1e-6
            and all(lo - 1e-6 <= c <= hi + 1e-6 for c in ends))


def _wall_intervals(model: ResolvedModel, storey: str, edge: SkirtedEdge):
    """Ascent-s extents of the walls on ``storey`` whose finish face lies on ``edge``."""
    cross = edge.cross_axis
    out = []
    for wall in model.walls:
        (a, b) = wall.axis
        if wall.storey != storey or abs(a[cross] - b[cross]) > 1e-6:
            continue
        polygons = [layer.polygon for layer in wall.depth_layers() if len(layer.polygon) >= 3]
        if not polygons:
            continue
        near = [(edge.outward * min(edge.outward * p[cross] for p in poly), poly)
                for poly in polygons]
        face, face_polygon = min(near, key=lambda item: edge.outward * item[0])
        coords = [p[cross] for poly in polygons for p in poly]
        centre = (min(coords) + max(coords)) / 2.0
        if abs(face - edge.edge) > _FACE_ON_EDGE_M or (centre - edge.edge) * edge.outward <= 0:
            continue
        run = [edge.along(p) for p in face_polygon]
        out.append((min(run), max(run)))
    return out


def _partition_intervals(members: tuple[FramedMember, ...], edge: SkirtedEdge):
    """The generated U-stair well partition, when its finished face is ``edge``."""
    parts = [m for m in members if m.child_key.startswith("well-partition-")]
    face = [m for m in parts
            if abs(m.p0[edge.cross_axis] - edge.outward * _WELL_PARTITION_THICKNESS_M / 2.0
                   - edge.edge) <= _FACE_ON_EDGE_M]
    if not face:
        return []
    run = [edge.along(p) for m in face for p in (m.p0, m.p1)]
    return [(min(run), max(run))]


def _opening_interval(outline, edge: SkirtedEdge) -> tuple[float, float] | None:
    """The ascent-s extent of the opening side lying on ``edge``, if one does."""
    cross = edge.cross_axis
    for a, b in zip(outline, [*outline[1:], *outline[:1]], strict=True):
        if (abs(a[cross] - b[cross]) < 1e-6
                and abs(a[cross] - edge.edge) <= _FACE_ON_EDGE_M):
            return tuple(sorted((edge.along(a), edge.along(b))))
    return None


def _merge(intervals):
    out: list[tuple[float, float]] = []
    for lo, hi in sorted(intervals):
        if out and lo <= out[-1][1] + _MERGE_GAP_M:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def inset_for_skirts(members: tuple[FramedMember, ...], edges: tuple[SkirtedEdge, ...],
                     thickness: float
                     ) -> tuple[tuple[FramedMember, ...], dict[str, float]]:
    """Trim tread and riser ends on each skirted edge and move its side stringer inboard.

    Landings keep their full width: the landing takes base, not skirt."""
    offsets: dict[str, float] = {}
    out = list(members)
    for edge in edges:
        cross = edge.cross_axis
        inboard = edge.edge - edge.outward * thickness
        for index, member in enumerate(out):
            if member.category in ("tread", "riser") and _in_lane(member, cross, *edge.lane):
                if all(abs(p[cross] - edge.edge) > 1e-6 for p in (member.p0, member.p1)):
                    continue
                line = member.riser_line
                p0 = _moved(member.p0, cross, edge.edge, inboard)
                p1 = _moved(member.p1, cross, edge.edge, inboard)
                out[index] = replace(
                    member, p0=p0, p1=p1, length_m=math.dist(p0, p1),
                    riser_line=tuple(_moved(p, cross, edge.edge, inboard) for p in line)
                    if line is not None else None)
            elif member.category == "stringer" and abs(
                    member.p0[cross] - member.p1[cross]) < 1e-6:
                face = edge.edge - edge.outward * cross_section(member.profile).width_m / 2.0
                if abs(member.p0[cross] - face) > 1e-6:
                    continue
                shifted = face - edge.outward * thickness
                out[index] = replace(member, p0=_moved(member.p0, cross, face, shifted),
                                     p1=_moved(member.p1, cross, face, shifted))
                offsets[member.child_key] = thickness
    return tuple(out), offsets


def _moved(point: tuple[float, float], cross: int, at: float, to: float):
    """``point`` with its ``cross`` coordinate moved ``at`` -> ``to``; others untouched."""
    if abs(point[cross] - at) > 1e-6:
        return point
    moved = list(point)
    moved[cross] = to
    return (moved[0], moved[1])


def skirt_members(stair: Stair, plan: SkirtPlan | None, members: tuple[FramedMember, ...],
                  riser: float, going: float, nosing: float, finish_m: float,
                  arrival_z: float) -> tuple[FramedMember, ...]:
    """One raked board per skirted flight side, profiled off the treads' nosing line."""
    if plan is None:
        return ()
    by_key = {m.child_key: m for m in members}
    slope = riser / going
    secant = math.sqrt(1.0 + slope * slope)
    out = []
    for edge in plan.edges:
        treads = sorted((by_key[key] for key in edge.treads),
                        key=lambda t: edge.along(t.riser_line[0]))
        first, last = treads[0], treads[-1]
        s_nose = edge.along(first.riser_line[0]) - nosing
        z_nose = first.z1_m + finish_m
        drop = riser * (going + nosing) / going + _COVER_BELOW_THROAT_M
        bottom = _line(s_nose, z_nose - drop, slope)
        rise = plan.board_width_m * secant
        spring_z = z_nose - riser
        toe = s_nose + (spring_z + plan.base_height_m - z_nose + drop - rise) / slope
        lane = [m for m in members if m.category in ("tread", "riser")
                and _in_lane(m, edge.cross_axis, *edge.lane)]
        head = max(edge.along(p) for m in lane for p in member_footprint(m)[0])
        backing = edge.backing
        if edge.opening is not None and plan.deck_underside_m is not None:
            # The well edge backs only where the board stands in the deck's depth.
            above = s_nose + (plan.deck_underside_m - z_nose + drop) / slope
            merged = _merge([backing, (max(edge.opening[0], above), edge.opening[1])])
            backing = next(iv for iv in merged if iv[0] <= backing[0] <= iv[1])
        s0, s1 = max(toe, backing[0]), min(head, backing[1])
        if s1 - s0 <= 1e-6:
            continue
        ceiling = bottom(s1) + rise + 1.0
        board = intersection(
            Polygon(((s0, bottom(s0)), (s1, bottom(s1)), (s1, bottom(s1) + rise),
                     (s0, bottom(s0) + rise))), box(s0, spring_z, s1, ceiling))
        if abs(last.z1_m + finish_m + riser - arrival_z) < 1e-4:
            # No ear above the arrival floor where no wall continues the face up there.
            for lo, hi in _gaps((s0, s1), edge.above_arrival):
                board = difference(board, box(lo, arrival_z, hi, ceiling))
        if not isinstance(board, Polygon) or board.is_empty:
            raise ValueError(f"stair {stair.tag}: a skirt cut leaves no single board")
        out.append(_board(stair, edge, plan, board, slope, secant, _name(first.child_key)))
    return tuple(out)


def _line(s_ref: float, z_ref: float, slope: float):
    return lambda s: z_ref + (s - s_ref) * slope


def _gaps(span: tuple[float, float], covered) -> list[tuple[float, float]]:
    out, cursor = [], span[0]
    for lo, hi in covered:
        if lo > cursor:
            out.append((cursor, min(lo, span[1])))
        cursor = max(cursor, hi)
    if cursor < span[1]:
        out.append((cursor, span[1]))
    return [(lo, hi) for lo, hi in out if hi - lo > 1e-9]


def _name(tread_key: str) -> str:
    flight = tread_key.removeprefix("tread").rsplit("-", 1)[0].strip("-")
    return flight or "flight"


def _board(stair: Stair, edge: SkirtedEdge, plan: SkirtPlan, board: Polygon, slope: float,
           secant: float, flight: str) -> FramedMember:
    # The overlay snaps vertices, so the board's ends are read off the cut polygon itself.
    s0, _z0, s1, _z1 = board.bounds
    centre = edge.edge - edge.outward * plan.thickness_m / 2.0
    run_axis = 1 - edge.cross_axis

    def at(s: float) -> tuple[float, float]:
        point = [0.0, 0.0]
        point[edge.cross_axis], point[run_axis] = centre, s * edge.sign
        return (point[0], point[1])

    ring = tuple((s - s0, z) for s, z in tuple(board.exterior.coords)[:-1])
    # The blank spans the cut's long points along the board's rake.
    along_rake = [(s + z * slope) / secant for s, z in ring]
    blank = max(along_rake) - min(along_rake)
    # Which hand of the walker climbing the flight the board is on.
    ascent = [0.0, 0.0]
    ascent[run_axis] = edge.sign
    outward = [0.0, 0.0]
    outward[edge.cross_axis] = edge.outward
    side = "left" if -ascent[1] * outward[0] + ascent[0] * outward[1] > 0 else "right"
    zs = [z for _, z in ring]
    return FramedMember(
        stair.uid, f"skirt-{flight}-{side}", "stair_skirt",
        f"{plan.thickness_m / 0.0254:.3f}x{plan.board_width_m / 0.0254:.3f}",
        at(s0), at(s1), min(zs), max(zs), blank, material=plan.material_ref,
        plan_width_m=plan.thickness_m, elevation_profile=ring, cut_length_m=blank)
