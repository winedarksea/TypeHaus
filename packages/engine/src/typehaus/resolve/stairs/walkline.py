"""The sloped walking line of a resolved stair, per flight.

Extracted from ``checks/code/mn_residential/stairs.py`` so the resolver can rake a
``Railing`` with ``serves_stair`` along the same nosing line the R311.7 checks measure
against — one derivation, two consumers, no drift. The checks keep importing
:func:`flight_stations` (their ``_flight_stations``) from here unchanged.

Everything reads the *resolved* stair members (measure-the-output doctrine): tread riser
lines, winder fan lines and landing edges, never the authored inputs.
"""

from __future__ import annotations

import math

from typehaus.resolve.framing.profiles import cross_section

#: How far a plan point may sit from every flight centreline before it is judged *off* the
#: stair. 2 m clears a rail path at the far edge of a code-width flight plus a landing's
#: depth without ever reaching the next lane's flight one storey away in plan. Lives here,
#: beside the derivation it qualifies, because both the resolver that rakes a rail and the
#: check that measures one have to mean the same thing by "beside this flight".
RAIL_LATERAL_REACH_M = 2.0


def flight_stations(stair) -> dict[str, list[tuple[tuple[float, float],
                                                   tuple[float, float], float]]]:
    """Per flight, the nosing stations of the sloped walking line, in climb order.

    A station is ``(a, b, z)``: the riser-face segment (a winder's fan line) at its
    tread's finished walking elevation. R311.7.2 measures plumb from the sloped line
    adjoining the nosings, so the line to sample is the interpolation between
    consecutive stations of one flight — never across flights, whose runs occupy
    different lanes.
    """
    flights: dict[str, list] = {}
    for member in stair.members:
        if member.category == "winder":
            flights.setdefault("winder", []).append((member.p0, member.p1, member.z1_m))
        elif member.category == "tread" and member.riser_line is not None:
            a, b = member.riser_line
            key = member.child_key.rsplit("-", 1)[0]
            flights.setdefault(key, []).append((a, b, member.z1_m))
        elif member.category == "landing":
            # A landing's walking surface: its two end edges at the deck face, swept from
            # the member axis by the profile's true half-width.
            (x0, y0), (x1, y1) = member.p0, member.p1
            run = math.hypot(x1 - x0, y1 - y0)
            if run < 1e-9:
                continue
            ux, uy = (x1 - x0) / run, (y1 - y0) / run
            half = cross_section(member.profile).width_m / 2.0
            px, py = -uy * half, ux * half
            flights[member.child_key] = [
                ((x0 - px, y0 - py), (x0 + px, y0 + py), member.z1_m),
                ((x1 - px, y1 - py), (x1 + px, y1 + py), member.z1_m),
            ]
    for key, stations in flights.items():
        stations.sort(key=lambda station: station[2])
        # Extend a straight flight one station past its top riser: the sloped line runs
        # to the edge it arrives at (the landing zone or the arrival deck), one going
        # beyond and one riser above the last nosing. Only tread flights extend — a
        # landing's stations already are its edges, and a winder fan's continuation is
        # the straight flight itself (its first riser line lies on the turn's departing
        # edge).
        if key.startswith("tread") and len(stations) >= 2:
            (a0, b0, z0), (a1, b1, z1) = stations[-2], stations[-1]
            stations.append(((2 * a1[0] - a0[0], 2 * a1[1] - a0[1]),
                             (2 * b1[0] - b0[0], 2 * b1[1] - b0[1]), 2 * z1 - z0))
    return flights


def flight_walklines(stair, include_arrival: bool = True, flights_only: bool = False
                     ) -> list[list[tuple[float, float, float]]]:
    """Each flight's walking line as a 3D centreline: station midpoints, climb order.

    The reduction a railing rake needs: a rail authored *alongside* a flight projects onto
    the flight's centreline, and the projection parameter carries the elevation because the
    rail runs parallel to the flight axis. Degenerate flights (fewer than two stations)
    contribute nothing.

    ``include_arrival=False`` drops the synthetic station :func:`flight_stations` extends a
    tread flight by — the arrival edge, one going past the top nosing. That extension is
    right for *raking* a rail, which runs out onto the deck it arrives at, and wrong for
    asking how long the flight is: R311.7.8.2 wants a handrail continuous from a point above
    the lowest riser to a point above the top riser, and the deck beyond the top riser is
    not part of that measurement.

    ``flights_only=True`` drops the *landings* as well. They are stations of the walking
    line — a rail rakes across one — but they are not flights, and R311.7.8.2 asks its
    question about a flight: a handrail is expressly permitted to be interrupted at a turn
    or a landing, which is where the newel goes.
    """
    lines: list[list[tuple[float, float, float]]] = []
    for key, stations in flight_stations(stair).items():
        if flights_only and not (key.startswith("tread") or key == "winder"):
            continue
        used = stations
        if not include_arrival and key.startswith("tread") and len(stations) >= 3:
            used = stations[:-1]
        line = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, z) for a, b, z in used]
        if len(line) >= 2:
            lines.append(line)
    return lines


def walkline_z_at(lines: list[list[tuple[float, float, float]]],
                  point: tuple[float, float],
                  max_lateral_m: float) -> float | None:
    """Walking-surface elevation under plan ``point``, off the nearest flight centreline.

    The point is projected onto every centreline segment; the closest one in plan wins and
    its interpolated ``z`` is returned. ``None`` when every flight is farther than
    ``max_lateral_m`` away — the caller's cue that the point is off the stair (a rail run
    continuing past the flight onto a floor edge).

    **A segment the point projects *inside* always beats one it projects past the end of**,
    however much nearer that end happens to be. Ranking on clamped distance alone let a
    *neighbouring* flight's endpoint win over the flight the point actually runs beside:
    on ST-S2A, the first band of RL-A-HANDRAIL sits 0.40 m from the straight flight it
    rakes along and 0.28 m from the last nosing of the winder fan below it, so it took the
    winder's elevation and drew a rail band 0.416 m out of step with its own neighbours —
    twice their 0.176 m rise. Clamping is what a *lateral* reach test is for; it is not a
    way to decide which flight a point belongs to.
    """
    interior: tuple[float, float] | None = None  # (plan distance, z), projection in [0,1]
    beyond: tuple[float, float] | None = None    # (plan distance, z), projection clamped
    px, py = point
    for line in lines:
        for (x0, y0, z0), (x1, y1, z1) in zip(line, line[1:]):
            dx, dy = x1 - x0, y1 - y0
            run2 = dx * dx + dy * dy
            raw = 0.0 if run2 < 1e-18 else ((px - x0) * dx + (py - y0) * dy) / run2
            t = max(0.0, min(1.0, raw))
            dist = math.hypot(px - (x0 + dx * t), py - (y0 + dy * t))
            candidate = (dist, z0 + (z1 - z0) * t)
            if -1e-9 <= raw <= 1.0 + 1e-9:
                if interior is None or dist < interior[0]:
                    interior = candidate
            elif beyond is None or dist < beyond[0]:
                beyond = candidate
    best = interior if interior is not None else beyond
    if best is None or best[0] > max_lateral_m:
        return None
    return best[1]
