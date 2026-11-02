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
from typehaus.resolve.model import ResolvedModel

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
    along = [_project(p, origin, unit)[0] for m in floor.members if m.category == "joist"
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
                            if m.category == "joist"
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
