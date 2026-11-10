"""The cleanouts a proposed drain needs (UPC 707.4), placed where their caps can be reached.

The requirements are ``resolve/cleanout_rules.run_requirements`` — the reading
``mep.drain_cleanouts`` grades — applied to the proposal as if it were pasted. Each one is
then stationed: its access ray, the 707.9 clearance (18" to 2", 24" above) along the plug
axis, which is the run's upstream direction, must miss every hard prism. Every station within
the check's own tolerance is priced and the cheapest wins, nearest on a tie: ``cleanout_in``
for any cleanout; plus ``cleanout_concealed_in`` for one in a wall cavity, bay or soffit (an
access panel, UPC 707.9) or overhead; one below its storey's floor comes up flush in it and
pays ``cleanout_floor_finished_in`` only in a finished room. A buried station also offers a
wall station: the extension rises in a partition cavity the run crosses or runs under.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any

from typehaus.quantities import M_PER_IN

_STEP_M = 3 * M_PER_IN
#: integrity.drain_cleanout: a cap at least 2" off its fitting, a wall cap 1 1/2" wallward.
_EXTENSION_M = 2 * M_PER_IN


def place_cleanouts(model: Any, space: Any, proposal: Any
                    ) -> tuple[tuple[Any, ...], float, list[str]]:
    """``(cleanouts, cost in, notes)`` for one proposed drain.

    A ``sanitary=False`` run (condensate, indirect waste) is outside UPC 707.4: none."""
    sanitary = bool(proposal.echo.get("sanitary", True))
    if not sanitary:
        return (), 0.0, []
    from typehaus.resolve.cleanout_rules import (
        _LOCATION_TOLERANCE_M,
        _TERMINAL_TOLERANCE_M,
        run_requirements,
    )
    from typehaus.routing.proposal import ProposedCleanout

    pts = proposal.points
    run = SimpleNamespace(tag=proposal.tag, path=[p[:2] for p in pts], z_m=[p[2] for p in pts],
                          serves=proposal.serves, sanitary=sanitary, system="drain",
                          diameter_m=proposal.diameter_m)
    building = next((r for r in model.pipe_runs if r.system == "drain"
                     and r.tag.endswith("MAIN-DRAIN")), None)
    # Only whether it ties onto the building drain matters (707.4 exception 3).
    ties = ({run.tag: building.tag} if building is not None and _ends_on(pts[-1], building)
            else {})
    lowest = min(s.elevation.meters for s in model.plan.storeys)
    clear_in = 18.0 if proposal.diameter_m <= 2 * M_PER_IN + 1e-9 else 24.0
    from typehaus.cli.route_eval import _storey_for

    storey = _storey_for(model, proposal)
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    out, cost, notes = [], 0.0, []
    for k, req in enumerate(run_requirements(run, {run.tag: run}, ties, building, lowest)):
        reach = (_TERMINAL_TOLERANCE_M if req.reason == "upper terminal"
                 else _LOCATION_TOLERANCE_M)
        station = _cheapest(space, [
            *(st for st in _clear_stations(space, pts, req, reach, clear_in * M_PER_IN)
              if st[0][2] >= datum - M_PER_IN or _floor_cap_open(model, st[0], storey, datum)),
            *_wall_stations(space, pts, req, reach, clear_in * M_PER_IN, datum)], datum)
        if station is None:
            notes.append(f"cleanout ({req.reason}) near ({req.point[0] / M_PER_IN:.2f}\", "
                         f"{req.point[1] / M_PER_IN:.2f}\"): no station within "
                         f"{reach / M_PER_IN:.0f}\" has {clear_in:g}\" clear along its plug")
            continue
        point, corridor, (ux, uy), wall_cap = station
        wall = corridor is not None and corridor.kind == "wall"
        # Below its storey's floor the plug comes up flush in it; overhead it is a panel.
        access = "wall" if wall else ("floor" if point[2] < datum - M_PER_IN else "ceiling")
        concealed = access != "floor"
        cap = (wall_cap or ((point[0], point[1], datum) if access == "floor"
                            else _cap(space, point, (ux, uy), wall)))
        out.append(ProposedCleanout(
            tag=f"CO-{proposal.tag}-{k + 1}", point=point, reason=req.reason, access=access,
            wall_ref=corridor.tag if wall else None, clear_in=clear_in, concealed=concealed,
            cap=cap))
        cost += _price(space, access, point, datum)
    notes.extend(_collisions(model, out, proposal))
    return tuple(out), cost, notes


def _ends_on(point: tuple, run: Any) -> bool:
    from typehaus.hardware.plan_geometry import distance_point_to_segment

    return any(distance_point_to_segment(point[:2], a, b) < run.diameter_m
               for a, b in zip(run.path, run.path[1:], strict=False))


def _stations(pts: list, req: Any, reach: float):
    """``(point, plug direction, axis, lo, hi)`` every 3" along the run within ``reach`` of
    the requirement, nearest first."""
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        length = math.dist(a[:2], b[:2])
        if length < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        axis = "x" if abs(ux) > abs(uy) else "y"
        lo, hi = sorted((a[0], b[0]) if axis == "x" else (a[1], b[1]))
        for j in range(int(length / _STEP_M) + 1):
            t = min(1.0, j * _STEP_M / length)
            p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2]))
            off = math.dist(p[:2], req.point)
            if off <= reach + 1e-6:
                out.append((off, i, j, (p, (ux, uy), axis, lo, hi)))
    return [entry[3] for entry in sorted(out, key=lambda e: e[:3])]


def _clear_stations(space: Any, pts: list, req: Any, reach: float, clear_m: float) -> list:
    """Stations within ``reach`` of the requirement whose access ray is clear, nearest first,
    each as ``(point, corridor, plug direction, wall cap or None)``."""
    out = []
    for p, (ux, uy), axis, lo, hi in _stations(pts, req, reach):
        # The plug faces upstream: the ray runs back along the flow.
        if any(space.blocked((p[0] - ux * clear_m * f, p[1] - uy * clear_m * f), p[2])
               for f in (0.25, 0.5, 0.75, 1.0)):
            continue
        corridor = space.corridor_at(axis, p[1] if axis == "x" else p[0], lo, hi, p[2])
        out.append((p, corridor, (ux, uy), None))
    return out


def _wall_stations(space: Any, pts: list, req: Any, reach: float, clear_m: float,
                   datum: float) -> list:
    """Wall stations for a BURIED run: the run crosses under, or runs under, a partition
    cavity; the extension rises through the slab into it, cap 12" up. Nearest first."""
    out = []
    z = datum + 12 * M_PER_IN
    for point, (ux, uy), _axis, _lo, _hi in _stations(pts, req, reach):
        if point[2] >= datum - M_PER_IN:
            continue
        for axis, station, along in (("x", point[1], point[0]), ("y", point[0], point[1])):
            corridor = space.corridor_at(axis, station, along, along, z)
            if corridor is None or corridor.kind != "wall":
                continue
            cap = _wall_cap(space, point, z, axis, clear_m)
            if cap is not None:
                out.append((point, corridor, (ux, uy), cap))
                break
    return out


def _wall_cap(space: Any, point: tuple, z: float, axis: str, clear_m: float) -> tuple | None:
    """The cap 2" to a clear face of a wall running along ``axis``, if 707.9's room is clear."""
    ax, ay = (1.0, 0.0) if axis == "x" else (0.0, 1.0)
    for sign in (1.0, -1.0):
        nx, ny = -sign * ay, sign * ax
        cap = (point[0] + nx * _EXTENSION_M, point[1] + ny * _EXTENSION_M, z)
        if space.blocked(cap[:2], z) is None and not any(
                space.blocked((point[0] + nx * clear_m * f, point[1] + ny * clear_m * f), z)
                for f in (0.25, 0.5, 0.75, 1.0)):
            return cap
    return None


def _finished_floor(space: Any, point: tuple, datum: float) -> bool:
    """A floor in a room the cost table prices (not utility, mechanical, garage, storage)."""
    return any(prism.kind == "room" and space.cost.room_penalty(prism.occupancy) > 0
               for prism in space.soft_at(point[:2], datum + M_PER_IN))


def _price(space: Any, access: str, point: tuple, datum: float) -> float:
    cost = space.cost
    if access == "floor":
        return cost.cleanout_in + (cost.cleanout_floor_finished_in
                                   if _finished_floor(space, point, datum) else 0.0)
    return cost.cleanout_in + cost.cleanout_concealed_in


def _cheapest(space: Any, stations: list, datum: float) -> tuple | None:
    """The cheapest station; ``min`` keeps the earlier (nearer) one on a tie."""
    def access(st: tuple) -> str:
        if st[1] is not None and st[1].kind == "wall":
            return "wall"
        return "floor" if st[0][2] < datum - M_PER_IN else "ceiling"

    return min(stations, key=lambda st: _price(space, access(st), st[0], datum),
               default=None)


def _floor_cap_open(model: Any, p: tuple, storey: str, datum: float) -> bool:
    """A floor cap no fixture, appliance or furniture stands over (``mep.drain_cleanouts``)."""
    from shapely.geometry import Point, Polygon

    return not any(item.storey == storey and item.body_z1_m >= datum
                   and item.domain in {"plumbing", "appliance", "furniture"} and item.footprint
                   and Polygon(item.footprint).covers(Point(p[:2]))
                   for item in getattr(model, "canvas_objects", ()))


def _cap(space: Any, p: tuple, u: tuple[float, float], wall: bool) -> tuple:
    """The cap on its extension: 2" up the plug axis, or for a wall 2" to its clear face."""
    reach = _EXTENSION_M
    if not wall:
        return (p[0] - u[0] * reach, p[1] - u[1] * reach, p[2])
    for sign in (1.0, -1.0):
        cap = (p[0] - sign * u[1] * reach, p[1] + sign * u[0] * reach, p[2])
        if space.blocked(cap[:2], cap[2]) is None:
            return cap
    return (p[0] - u[1] * reach, p[1] + u[0] * reach, p[2])


def _collisions(model: Any, placed: list, proposal: Any) -> list[str]:
    """An authored cleanout within a pipe diameter of a proposed fitting or cleanout."""
    notes = []
    spots = [*proposal.points[1:-1], *(c.point for c in placed)]
    for co in model.drain_cleanouts:
        here = (co.position[0], co.position[1], co.fitting_z_m)
        if any(math.dist(here, p) < 2 * proposal.diameter_m for p in spots):
            notes.append(f"a proposed fitting stands on {co.tag}'s fitting (within "
                         f"{2 * proposal.diameter_m / M_PER_IN:.1f}\"): a combo detail, or "
                         "nudge one of them")
    return notes
