"""A falling run through an open-web truss: per crossing, the heights no opening leaves it.

``members.cuts`` grades a level run's crossing exactly, but a falling run's height is not
known at graph build, so its only constraint there is chord to chord: it laid a 2" drain down
a pocket another run already held, and through a web at the top of R1. A pocket is a triangle,
so the legal height depends on the station, and Warren pockets can stack into two disjoint
bands split by one diagonal. A ``Window`` intersects one interval; an ``Obstacle`` can split.
So each crossing emits the complement of its free bands inside the chord window, and a
station with no free opening an all-z block, which ``gravity.tie_reach`` reads as a dead edge
and names. ``houses/catlin/notes/framing_bore_limits.md`` §13 is the hand-worked oracle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.open_web import RunSize, run_of, station_bands
from typehaus.routing.holes import (
    ijoist_bores_ok,
    member_lines_crossed,
    sibling_holes,
    taken_pockets,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.graph import Graph
    from typehaus.routing.gravity_band import Obstacle, Obstacles
    from typehaus.routing.space import RoutingSpace

#: The proposal snaps to 1/16": a band's edge keeps that much in hand each side.
_SNAP_INSET_M = 0.0625 * M_PER_IN
_ALL_Z = (float("-inf"), float("inf"))


def web_obstacles(space: RoutingSpace, graph: Graph, laid: Any = ()) -> Obstacles:
    """Per-edge web obstacles, cached per undirected edge and reversed on the way back.

    ``laid`` (``holes.laid_lines``) adds this campaign's runs to the authored occupants.
    """
    band = space.plan_band or _ALL_Z
    # As ``gravity_band.member_constraints``: a floor outside the run's band cannot touch it.
    floors = [floor for floor in (space.members.floors if space.members is not None else ())
              if floor.pockets and floor.window[0] <= band[1] and floor.window[1] >= band[0]]
    if not floors:
        return lambda _a, _b: []
    radius = space.members.radius_m
    size = RunSize(2 * radius, 2 * radius, True)
    held = [_occupants(floor, laid) for floor in floors]
    cache: dict[tuple[int, int], list[Obstacle]] = {}
    stations: dict[tuple[int, int], list] = {}

    def bands(shape: Any, run_m: float) -> list:
        key = (id(shape), round(run_m / 1e-6))
        if key not in stations:
            stations[key] = station_bands(shape, run_m, size)
        return stations[key]

    def crossing_edge(a: int, b: int) -> list[Obstacle]:
        first, second = graph.nodes[a], graph.nodes[b]
        axis = "x" if abs(first.x - second.x) > abs(first.y - second.y) else "y"
        begin, end, along = ((first.x, second.x, first.y) if axis == "x"
                             else (first.y, second.y, first.x))
        if abs(end - begin) < 1e-9:
            return []  # a riser: ``members.cuts`` keeps it off the member lines
        out: list[Obstacle] = []
        for floor, occupants in zip(floors, held, strict=True):
            if floor.across != axis:
                continue
            for i in member_lines_crossed(floor, along, min(begin, end), max(begin, end), band):
                t = min(max((floor.stations[i] - begin) / (end - begin), 0.0), 1.0)
                out.extend((t, t, z0, z1, tag)
                           for z0, z1, tag in _forbidden(floor, i, along, occupants[i], bands))
        return out

    def obstacles(a: int, b: int) -> list[Obstacle]:
        key = (a, b) if a < b else (b, a)
        found = cache.get(key)
        if found is None:
            found = cache[key] = crossing_edge(*key)
        if a < b or not found:
            return found
        return [(1.0 - t1, 1.0 - t0, z0, z1, tag) for t0, t1, z0, z1, tag in found]

    return obstacles


def spacing_obstacles(space: RoutingSpace, graph: Graph, laid: Any = ()) -> Obstacles:
    """Per-edge I-joist hole-spacing blocks against ``laid``'s holes (``holes.sibling_holes``).

    The space reads only the holes it was built with, so a sibling laid since is read here, per
    search: an edge whose crossing would stand inside "2 x the larger hole" of one is blocked
    over that joist's z range (a hole is a hole at any height). ``framing_bore_limits.md`` §14.
    """
    band = space.plan_band or _ALL_Z
    members = space.members
    floors = [(floor, extra) for floor in (members.floors if members is not None else ())
              if floor.window[0] <= band[1] and floor.window[1] >= band[0] and laid
              and (extra := sibling_holes(laid, floor))]
    if not floors:
        return lambda _a, _b: []
    size = 2 * members.radius_m
    cache: dict[tuple[int, int], list[Obstacle]] = {}

    def crossing_edge(a: int, b: int) -> list[Obstacle]:
        first, second = graph.nodes[a], graph.nodes[b]
        axis = "x" if abs(first.x - second.x) > abs(first.y - second.y) else "y"
        begin, end, along = ((first.x, second.x, first.y) if axis == "x"
                             else (first.y, second.y, first.x))
        if abs(end - begin) < 1e-9:
            return []
        out: list[Obstacle] = []
        for floor, extra in floors:
            if floor.across != axis:
                continue
            for i in member_lines_crossed(floor, along, min(begin, end), max(begin, end), band):
                if not extra[i] or ijoist_bores_ok(floor, [i], along, size, extra):
                    continue
                t = min(max((floor.stations[i] - begin) / (end - begin), 0.0), 1.0)
                near = min(extra[i], key=lambda h: abs(h[0] - along))[2]
                out.append((t, t, floor.joists[i][3], floor.joists[i][4],
                            f'{floor.tag} {floor.parts[i].child_key} {axis}='
                            f'{along / M_PER_IN:.2f}": hole too near {near}'))
        return out

    def obstacles(a: int, b: int) -> list[Obstacle]:
        key = (a, b) if a < b else (b, a)
        found = cache.get(key)
        if found is None:
            found = cache[key] = crossing_edge(*key)
        if a < b or not found:
            return found
        return [(1.0 - t1, 1.0 - t0, z0, z1, tag) for t0, t1, z0, z1, tag in found]

    return obstacles


def _occupants(floor: Any, laid: Any) -> list[dict[str, str]]:
    """Per joist line, each taken pocket's holder: authored, then laid this campaign."""
    if not laid:
        return floor.pockets
    extra = taken_pockets(list(laid), floor.source, floor.parts)
    return [{**held, **more} for held, more in zip(floor.pockets, extra, strict=True)]


def _forbidden(floor: Any, index: int, along: float, occupants: dict[str, str],
               bands: Any) -> list[tuple[float, float, str]]:
    """``(z0, z1, tag)`` a centreline may not be inside where it crosses this member."""
    member = floor.parts[index]
    shape = member.web
    if shape is None:
        return []
    free: list[tuple[float, float]] = []
    holders: list[str] = []
    for low, high, opening in bands(shape, run_of(member, along, floor.across == "y")):
        holder = occupants.get(opening.key)
        if holder is not None:
            holders.append(f"{opening.key} held by {holder}")
        elif high - low > 2 * _SNAP_INSET_M:
            free.append((member.z0_m + low + _SNAP_INSET_M, member.z0_m + high - _SNAP_INSET_M))
    axis = "x" if floor.across == "y" else "y"
    why = "; ".join(holders) or ("on a web" if free else "no opening fits")
    tag = f'{floor.tag} {member.child_key} {axis}={along / M_PER_IN:.2f}": {why}'
    if not free:
        return [(*_ALL_Z, tag)]
    out = []
    at, top = (member.z0_m + z for z in shape.window_z_m)
    for low, high in free:
        if low > at:
            out.append((at, low, tag))
        at = high
    if at < top:
        out.append((at, top, tag))
    return out
