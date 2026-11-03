"""Rack lanes: a laid run's level legs offer a parallel lane to the next run of its trade.

A plumber hangs the second supply line on the first one's hangers. In a campaign each
accepted level, axis-aligned leg emits a lane either side, its station offset by the laid
run's radius, the rack spacing and the new run's radius, at the laid leg's own height. Only
a compatible trade may ride it: supply with supply, drain with drain — a drain never shares
a supply hanger. The graph prices a rack lane at ``rack_discount_per_ft`` instead of the
corridor discount; one discount per edge, so the corridor heuristic floor stays admissible.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from typehaus.routing.corridors import Corridor

_LEVEL_M = 0.0015875  # 1/16": a leg that falls less than this is level
_MIN_LANE_M = 0.6096 - 1e-6  # 2 ft: a shorter leg is a jog, not a rack


def rack_family(system: str) -> str:
    """The trade a rack is shared within: supply with supply, drain with drain."""
    from typehaus.resolve.mep_fittings import SERVICE_BY_SYSTEM

    system = getattr(system, "value", system)
    return SERVICE_BY_SYSTEM.get(system, system)


def rack_lanes(laid: Iterable[Any], *, system: str, radius_m: float,
               spacing_m: float) -> list[Corridor]:
    """Lanes beside every level leg of the ``laid`` proposals this ``system`` may share."""
    from typehaus.routing.trades.pipe import radius_m as pipe_radius_m

    family = rack_family(system)
    out: list[Corridor] = []
    for proposal in laid:
        if proposal.kind != "pipe" or rack_family(proposal.system) != family:
            continue
        material = (getattr(proposal, "echo", None) or {}).get("material")
        offset = pipe_radius_m(proposal.diameter_m, material) + spacing_m + radius_m
        points = proposal.points
        for i, (a, b) in enumerate(zip(points, points[1:], strict=False)):
            if abs(b[2] - a[2]) > _LEVEL_M:
                continue
            if abs(a[1] - b[1]) < 1e-6 and abs(b[0] - a[0]) >= _MIN_LANE_M:
                axis, station, lo, hi = "x", a[1], *sorted((a[0], b[0]))
            elif abs(a[0] - b[0]) < 1e-6 and abs(b[1] - a[1]) >= _MIN_LANE_M:
                axis, station, lo, hi = "y", a[0], *sorted((a[1], b[1]))
            else:
                continue
            for side, sign in (("L", -1.0), ("R", 1.0)):
                out.append(Corridor(
                    tag=f"RACK-{proposal.tag}-{i}{side}", kind="rack", axis=axis,
                    station=station + sign * offset, z0_m=a[2] - radius_m - _LEVEL_M,
                    z1_m=a[2] + radius_m + _LEVEL_M, clear_width_m=2 * radius_m,
                    lo_m=lo, hi_m=hi))
    return out


def rack_shared(proposals: list[Any], *, spacing_m: float, tolerance_m: float = 0.0127) -> int:
    """Runs with a level leg on a rack lane of another compatible run (the scorecard's)."""
    from typehaus.routing.trades.pipe import radius_m as pipe_radius_m

    shared = set()
    for p in proposals:
        if p.kind != "pipe":
            continue
        lanes = rack_lanes([q for q in proposals if q is not p], system=p.system,
                           radius_m=pipe_radius_m(p.diameter_m,
                                                  (getattr(p, "echo", None) or {}).get(
                                                      "material")),
                           spacing_m=spacing_m)
        for a, b in zip(p.points, p.points[1:], strict=False):
            if any(_rides(lane, a, b, tolerance_m) for lane in lanes):
                shared.add(p.tag)
                break
    return len(shared)


def _rides(lane: Corridor, a: tuple, b: tuple, tolerance_m: float) -> bool:
    k, s = (0, 1) if lane.axis == "x" else (1, 0)
    if abs(a[s] - b[s]) > 1e-6 or abs(a[s] - lane.station) > tolerance_m:
        return False
    lo, hi = sorted((a[k], b[k]))
    return (min(hi, lane.hi_m) - max(lo, lane.lo_m) >= _MIN_LANE_M
            and lane.z0_m <= a[2] <= lane.z1_m)
