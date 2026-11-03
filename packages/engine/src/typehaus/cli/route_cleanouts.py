"""The cleanouts a proposed drain needs (UPC 707.4), placed where their caps can be reached.

The requirements are ``resolve/cleanout_rules.run_requirements`` — the reading
``mep.drain_cleanouts`` grades — applied to the proposal as if it were pasted. Each one is
then stationed: its access ray, the 707.9 clearance (18" to 2", 24" above) along the plug
axis, which is the run's upstream direction, must miss every hard prism. The first clear
station within the check's own tolerance wins. A station inside a wall cavity, bay or soffit
is concealed and needs an access panel, priced at ``cleanout_concealed_in``; so is one
overhead. One below its storey's floor comes up flush in it, which needs no panel.
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
    """``(cleanouts, cost in, notes)`` for one proposed drain."""
    from typehaus.resolve.cleanout_rules import (
        _LOCATION_TOLERANCE_M,
        _TERMINAL_TOLERANCE_M,
        run_requirements,
    )
    from typehaus.routing.proposal import ProposedCleanout

    pts = proposal.points
    run = SimpleNamespace(tag=proposal.tag, path=[p[:2] for p in pts], z_m=[p[2] for p in pts],
                          serves=proposal.serves, sanitary=True, system="drain",
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
        station = next((st for st in _clear_stations(space, pts, req, reach,
                                                     clear_in * M_PER_IN)
                        if st[0][2] >= datum - M_PER_IN
                        or _floor_cap_open(model, st[0], storey, datum)),
                       None)
        if station is None:
            notes.append(f"cleanout ({req.reason}) near ({req.point[0] / M_PER_IN:.2f}\", "
                         f"{req.point[1] / M_PER_IN:.2f}\"): no station within "
                         f"{reach / M_PER_IN:.0f}\" has {clear_in:g}\" clear along its plug")
            continue
        point, corridor, (ux, uy) = station
        wall = corridor is not None and corridor.kind == "wall"
        # Below its storey's floor the plug comes up flush in it; overhead it is a panel.
        access = "wall" if wall else ("floor" if point[2] < datum - M_PER_IN else "ceiling")
        concealed = access != "floor"
        cap = ((point[0], point[1], datum) if access == "floor"
               else _cap(space, point, (ux, uy), wall))
        out.append(ProposedCleanout(
            tag=f"CO-{proposal.tag}-{k + 1}", point=point, reason=req.reason, access=access,
            wall_ref=corridor.tag if wall else None, clear_in=clear_in, concealed=concealed,
            cap=cap))
        if concealed:
            cost += space.cost.cleanout_concealed_in
    notes.extend(_collisions(model, out, proposal))
    return tuple(out), cost, notes


def _ends_on(point: tuple, run: Any) -> bool:
    from typehaus.hardware.plan_geometry import distance_point_to_segment

    return any(distance_point_to_segment(point[:2], a, b) < run.diameter_m
               for a, b in zip(run.path, run.path[1:], strict=False))


def _clear_stations(space: Any, pts: list, req: Any, reach: float, clear_m: float) -> list:
    """Stations within ``reach`` of the requirement whose access ray is clear, nearest first,
    each as ``(point, corridor, plug direction)``."""
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        length = math.dist(a[:2], b[:2])
        if length < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        for j in range(int(length / _STEP_M) + 1):
            t = min(1.0, j * _STEP_M / length)
            p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2]))
            off = math.dist(p[:2], req.point)
            if off > reach + 1e-6:
                continue
            # The plug faces upstream: the ray runs back along the flow.
            if any(space.blocked((p[0] - ux * clear_m * f, p[1] - uy * clear_m * f), p[2])
                   for f in (0.25, 0.5, 0.75, 1.0)):
                continue
            axis = "x" if abs(ux) > abs(uy) else "y"
            lo, hi = sorted((a[0], b[0]) if axis == "x" else (a[1], b[1]))
            corridor = space.corridor_at(axis, p[1] if axis == "x" else p[0], lo, hi, p[2])
            out.append((off, i, j, (p, corridor, (ux, uy))))
    return [entry[3] for entry in sorted(out, key=lambda e: e[:3])]


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
