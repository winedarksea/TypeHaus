"""Where a floor restrains the top of a foundation wall it runs PARALLEL to.

Minn. R. 1309.0404, Table R404.1(1) footnote f: "full depth 2-inch blocking or approved
equivalent" in the first three joist spaces next to the wall, at the table's spacing, each
station "within 8 inches of an anchor bolt". A perpendicular floor restrains the wall
through its seated ends (``joints/bearing``); a parallel one only through these stations.

Stations are read off the blocking the resolver derived from an authored
``JoistReinforcement(blocking=True)`` (child keys ``sister-*-block-*``), never off a
proximity search for loose lumber: a bearing-line block that happens to sit near a wall is
not a restraint station anyone designed. ``code.MN_1309_0404_wall_top`` grades them and
``joints/sills.mudsill_anchor_stations`` adds an anchor where none is within 8".
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.joints.model import axis_of
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, on_joist_line

#: A floor whose subfloor sits this far over the wall top is seated on it (a 1 1/2" sill
#: plus joists of any depth this house frames); a deck at the wall top hangs off it.
_SEAT_RISE_M = (6.0 * M_PER_IN, 16.0 * M_PER_IN)
#: Blocks this close along the wall are one station.
_STATION_CLUSTER_M = 6.0 * M_PER_IN
#: Footnote f's "first three joist spaces adjacent to the wall".
_BAYS = 3
#: The overlap below which a floor merely touches a wall's end.
_MIN_OVERLAP_M = 0.3


@dataclass(frozen=True)
class BlockStation:
    along_m: float  # from the wall axis's p0
    point_m: tuple  # plan point on the wall axis
    bays: frozenset  # joist spaces blocked, 1 = the space next to the wall


@dataclass(frozen=True)
class ParallelRun:
    """One floor over one foundation wall it runs parallel to."""

    wall_tag: str
    floor_tag: str
    storey: str
    span_m: tuple  # (start, end) of the floor's overlap, along the wall from p0
    stations: tuple  # BlockStation, sorted along the wall
    #: ``(start, end)`` stretches along the wall where a deck void (a stair well) cuts the
    #: first three joist spaces: no blocking can stand there.
    voids: tuple = ()


def _frame(wall):
    (ax, ay), (bx, by) = wall.axis[0][:2], wall.axis[1][:2]
    length = math.hypot(bx - ax, by - ay) or 1.0
    return (ax, ay), ((bx - ax) / length, (by - ay) / length), length


def _project(point, origin, unit) -> tuple:
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    return dx * unit[0] + dy * unit[1], abs(dx * unit[1] - dy * unit[0])


def along_wall(wall, point) -> tuple:
    """``(distance along the wall axis from p0, offset off it)`` of a plan point."""
    origin, unit, _length = _frame(wall)
    return _project(point, origin, unit)


def _overlap(floor, origin, unit, length, reach_m) -> tuple | None:
    """The stretch of the wall the floor's deck covers, from its parallel joists' ends."""
    along = [_project(p, origin, unit)[0] for m in floor.members if on_joist_line(m)
             for p in (m.p0, m.p1) if _project(p, origin, unit)[1] <= reach_m]
    if not along:
        return None
    start, end = max(0.0, min(along)), min(length, max(along))
    return (start, end) if end - start >= _MIN_OVERLAP_M else None


def parallel_runs(model: ResolvedModel) -> list:
    """Every (foundation wall, parallel floor seated on it) pair, with its block stations."""
    elements = {e.tag: e for e in model.plan.all_elements()} if model.plan else {}
    runs: list = []
    for wall in model.walls:
        if not wall.is_foundation:
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        origin, unit, length = _frame(wall)
        wall_axis = axis_of(wall.axis[0], wall.axis[1])
        for floor in model.floors:
            if floor.direction != wall_axis:
                continue
            if not _SEAT_RISE_M[0] <= floor.deck_z0_m - top <= _SEAT_RISE_M[1]:
                continue
            joists = getattr(elements.get(floor.tag), "joists", None)
            spacing = getattr(getattr(joists, "spacing", None), "meters", None)
            if not spacing:
                continue
            span = _overlap(floor, origin, unit, length, wall.thickness_m / 2.0 + spacing)
            if span is None:
                continue
            lines = sorted({round(_project(m.p0, origin, unit)[1], 4) for m in floor.members
                            if on_joist_line(m)
                            and _project(m.p0, origin, unit)[1] <= wall.thickness_m})
            edge = lines[0] if lines else 0.0
            runs.append(ParallelRun(wall.tag, floor.tag, floor.storey, span,
                                    _stations(floor, origin, unit, span, edge, spacing),
                                    _voids(floor, origin, unit, span, edge, spacing)))
    return runs


def _voids(floor, origin, unit, span, edge_m, spacing_m) -> tuple:
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import intersection, union_all

    normal = (-unit[1], unit[0])
    out = []
    for side in (1.0, -1.0):
        near, far = edge_m * side, (edge_m + _BAYS * spacing_m) * side
        strip = Polygon([(origin[0] + unit[0] * a + normal[0] * d,
                          origin[1] + unit[1] * a + normal[1] * d)
                         for a, d in ((span[0], near), (span[1], near),
                                      (span[1], far), (span[0], far))])
        holes = [Polygon([p[:2] for p in ring]) for ring in floor.deck_voids if len(ring) >= 3]
        if not holes:
            return ()
        cut = intersection(strip, union_all(holes))
        if cut.is_empty or cut.area < 1e-6:
            continue
        for part in getattr(cut, "geoms", (cut,)):
            if not hasattr(part, "exterior"):
                continue
            along, off = zip(*(_project(p, origin, unit) for p in part.exterior.coords),
                             strict=True)
            # A riser hole in one bay leaves room for a station beside it; a well across
            # the spaces does not.
            if (max(along) - min(along) > _STATION_CLUSTER_M
                    and max(off) - min(off) >= (_BAYS - 0.5) * spacing_m):
                out.append((min(along), max(along)))
    return tuple(sorted(out))


def _stations(floor, origin, unit, span, edge_m, spacing_m) -> tuple:
    blocks = []
    for member in floor.members:
        key = member.child_key or ""
        if member.category != "blocking" or not key.startswith("sister-"):
            continue
        a0, d0 = _project(member.p0, origin, unit)
        a1, d1 = _project(member.p1, origin, unit)
        if abs(a1 - a0) > _STATION_CLUSTER_M:
            continue  # runs along the wall: not a strut across the joist spaces
        along, mid = (a0 + a1) / 2.0, (d0 + d1) / 2.0
        if not span[0] - _STATION_CLUSTER_M <= along <= span[1] + _STATION_CLUSTER_M:
            continue
        bay = int(math.floor((mid - edge_m) / spacing_m)) + 1
        if 1 <= bay <= _BAYS:
            blocks.append((along, bay))
    stations: list = []
    for along, bay in sorted(blocks):
        if stations and along - stations[-1][0] <= _STATION_CLUSTER_M:
            stations[-1][1].add(bay)
        else:
            stations.append([along, {bay}])
    return tuple(BlockStation(along, (origin[0] + unit[0] * along, origin[1] + unit[1] * along),
                              frozenset(bays)) for along, bays in stations)


# --- the ties at each station ---------------------------------------------------------

#: How far from a station point a tie still serves it (``code.MN_1309_0404_wall_top``).
STATION_REACH_M = 18.0 * M_PER_IN
#: Laid ties stay this far inside the reach, so the check never grades a float hair.
_REACH_MARGIN_M = 1.0 / 16.0 * M_PER_IN
#: Clear of the block end that butts the edge member, and the pitch's floor when closing.
_BLOCK_GAP_M = 0.125 * M_PER_IN
_MIN_PITCH_M = 3.0 * M_PER_IN
_PITCH_STEP_M = 0.125 * M_PER_IN


@dataclass(frozen=True)
class StationTie:
    """One tie at a block station: on the edge member's inboard face, on the sill top."""

    wall_tag: str
    floor_tag: str
    storey: str
    part: str
    station_m: tuple  # the station's plan point on the wall axis
    point_m: tuple  # the leaf's centre on the inboard face
    z_m: float | None  # the sill top under it
    under: str | None = None  # the framing member over its flat leaf, if any: not nailable


def in_span(run, station) -> bool:
    """Whether ``station`` lies on ``run``'s own stretch of wall (and so on its sill)."""
    return run.span_m[0] <= station.along_m <= run.span_m[1]


def _width(member) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    return member.plan_width_m or cross_section(member.profile).width_m


def edge_face(floor, wall) -> tuple | None:
    """``(signed offset of the edge member's inboard face off the wall axis, inward unit)``."""
    origin, unit, _length = _frame(wall)
    normal = (-unit[1], unit[0])
    lines = []
    for m in floor.members:
        if not on_joist_line(m):
            continue
        dx, dy = m.p1[0] - m.p0[0], m.p1[1] - m.p0[1]
        if abs(dx * unit[1] - dy * unit[0]) > 0.01 * (math.hypot(dx, dy) or 1.0):
            continue  # not parallel to the wall
        lines.append(((m.p0[0] - origin[0]) * normal[0] + (m.p0[1] - origin[1]) * normal[1],
                      _width(m)))
    near = [line for line in lines if abs(line[0]) <= wall.thickness_m]
    if not near:
        return None
    sign = 1.0 if sum(off for off, _w in lines) >= 0.0 else -1.0
    offset, width = min(near, key=lambda line: abs(line[0]))
    return offset + sign * width / 2.0, (normal[0] * sign, normal[1] * sign)


def sill_returns(model: ResolvedModel) -> list:
    """``(z0, top over the gasket, prepared outline)`` per construction return, for
    ``sill_top_z``: built once per caller, not once per tie."""
    from shapely.geometry import Polygon
    from shapely.prepared import prep

    return [(r.z0_m, r.z1_m + (r.gasket_thickness_m or 0.0),
             prep(Polygon(r.outline).buffer(1e-6)))
            for r in model.construction_returns if len(r.outline) >= 3]


def sill_top_z(model: ResolvedModel, point, base_z_m: float, returns=None) -> float | None:
    """The top of the sill standing on ``base_z_m`` under ``point``, over its gasket."""
    from shapely.geometry import Point

    here = Point(point[0], point[1])
    tops = [top for z0, top, outline in (sill_returns(model) if returns is None else returns)
            if abs(z0 - base_z_m) <= 1e-3 and outline.contains(here)]
    return max(tops) if tops else None


def _under(floor, footprint) -> str | None:
    """The first non-rim, non-block member standing on ``footprint`` (the flat leaf)."""
    from shapely.geometry import LineString

    x0, y0, x1, y1 = footprint.bounds
    for m in floor.members:
        if m.category in ("rim", "blocking"):
            continue
        r = _width(m) / 2.0
        if (max(m.p0[0], m.p1[0]) + r <= x0 or min(m.p0[0], m.p1[0]) - r >= x1
                or max(m.p0[1], m.p1[1]) + r <= y0 or min(m.p0[1], m.p1[1]) - r >= y1):
            continue
        if LineString([m.p0[:2], m.p1[:2]]).buffer(r, cap_style=2).intersection(
                footprint).area > 1e-7:
            return m.child_key or m.category
    return None


def _block_extent(floor, origin, unit, station) -> tuple:
    """The station's blocks along the wall: the stretch no tie may stand on."""
    spans = []
    for m in floor.members:
        if m.category != "blocking" or not (m.child_key or "").startswith("sister-"):
            continue
        a0, a1 = _project(m.p0, origin, unit)[0], _project(m.p1, origin, unit)[0]
        mid = (a0 + a1) / 2.0
        if abs(a1 - a0) <= _STATION_CLUSTER_M and abs(mid - station.along_m) <= _STATION_CLUSTER_M:
            spans.append((mid - _width(m) / 2.0, mid + _width(m) / 2.0))
    if not spans:
        return station.along_m, station.along_m
    return min(lo for lo, _hi in spans), max(hi for _lo, hi in spans)


def _lay(count, extent, half_m, pitch_m, run, station, blocked) -> list:
    """``count`` positions nearest the station, closing the pitch to 3" before giving up."""
    lo, hi = extent
    reach = STATION_REACH_M - _REACH_MARGIN_M
    while True:
        found = []
        for k in range(count):
            for a in (lo - _BLOCK_GAP_M - half_m - k * pitch_m,
                      hi + _BLOCK_GAP_M + half_m + k * pitch_m):
                if (run.span_m[0] <= a - half_m and a + half_m <= run.span_m[1]
                        and abs(a - station.along_m) <= reach and not blocked(a)):
                    found.append((abs(a - station.along_m), a))
        if len(found) >= count or pitch_m - _PITCH_STEP_M < _MIN_PITCH_M - 1e-9:
            return sorted(a for _d, a in sorted(found)[:count])
        pitch_m -= _PITCH_STEP_M


def station_tie_points(model: ResolvedModel) -> list:
    """Every ``JoistSpec.station_ties`` tie, once per station: a station two collinear runs
    of one floor both see is tied from the run whose span contains it."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.connector_geometry.plate_angle import footprint, plate_angle_dims

    elements = {e.tag: e for e in model.plan.all_elements()} if model.plan else {}
    floors = {f.tag: f for f in model.floors}
    out: list = []
    done: set = set()
    returns = sill_returns(model)
    for run in parallel_runs(model):
        spec = getattr(elements.get(run.floor_tag), "joists", None)
        if spec is None or spec.station_ties <= 0 or not spec.sill_tie:
            continue
        wall, floor = model.wall(run.wall_tag), floors[run.floor_tag]
        face = edge_face(floor, wall)
        if face is None:
            continue
        offset, inward = face
        origin, unit, _length = _frame(wall)
        normal = (-unit[1], unit[0])
        dims = plate_angle_dims(spec.sill_tie)
        half = dims.width_m / 2.0 if dims else 0.75 * M_PER_IN
        holes = [Polygon([p[:2] for p in ring]) for ring in floor.deck_voids if len(ring) >= 3]
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m

        def at(a, off=offset, o=origin, u=unit, n=normal):
            return (o[0] + u[0] * a + n[0] * off, o[1] + u[1] * a + n[1] * off)

        def blocked(a, run=run, holes=holes, at=at, floor=floor, inward=inward, dims=dims):
            # Framing over the flat leaf (a trimmer on the sill, a backer on the rim) too.
            return (any(lo <= a <= hi for lo, hi in run.voids)
                    or any(h.contains(Point(at(a))) for h in holes)
                    or (dims is not None
                        and _under(floor, footprint(at(a), inward, dims)) is not None))

        for station in run.stations:
            key = (run.floor_tag, round(station.point_m[0], 3), round(station.point_m[1], 3))
            if key in done or not in_span(run, station):
                continue
            done.add(key)
            extent = _block_extent(floor, origin, unit, station)
            for a in _lay(spec.station_ties, extent, half, spec.station_tie_pitch.meters,
                          run, station, blocked):
                point = at(a)
                probe = (point[0] + inward[0] * half, point[1] + inward[1] * half)
                under = _under(floor, footprint(point, inward, dims)) if dims else None
                out.append(StationTie(run.wall_tag, run.floor_tag, run.storey, spec.sill_tie,
                                      station.point_m, point,
                                      sill_top_z(model, probe, top, returns), under))
    return out
