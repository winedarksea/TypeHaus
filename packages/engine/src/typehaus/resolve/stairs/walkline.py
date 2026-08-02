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


def flight_walklines(stair) -> list[list[tuple[float, float, float]]]:
    """Each flight's walking line as a 3D centreline: station midpoints, climb order.

    The reduction a railing rake needs: a rail authored *alongside* a flight projects onto
    the flight's centreline, and the projection parameter carries the elevation because the
    rail runs parallel to the flight axis. Degenerate flights (fewer than two stations)
    contribute nothing.
    """
    lines: list[list[tuple[float, float, float]]] = []
    for stations in flight_stations(stair).values():
        line = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, z) for a, b, z in stations]
        if len(line) >= 2:
            lines.append(line)
    return lines


def walkline_z_at(lines: list[list[tuple[float, float, float]]],
                  point: tuple[float, float],
                  max_lateral_m: float) -> float | None:
    """Walking-surface elevation under plan ``point``, off the nearest flight centreline.

    The point is projected (clamped) onto every centreline segment; the closest one in
    plan wins and its interpolated ``z`` is returned. ``None`` when every flight is
    farther than ``max_lateral_m`` away — the caller's cue that the point is off the
    stair (a rail run continuing past the flight onto a floor edge).
    """
    best: tuple[float, float] | None = None  # (plan distance, z)
    px, py = point
    for line in lines:
        for (x0, y0, z0), (x1, y1, z1) in zip(line, line[1:]):
            dx, dy = x1 - x0, y1 - y0
            run2 = dx * dx + dy * dy
            t = 0.0 if run2 < 1e-18 else max(
                0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / run2))
            dist = math.hypot(px - (x0 + dx * t), py - (y0 + dy * t))
            if best is None or dist < best[0]:
                best = (dist, z0 + (z1 - z0) * t)
    if best is None or best[0] > max_lateral_m:
        return None
    return best[1]
