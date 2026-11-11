"""The z band of the storeys a run's own terminals stand in (a vent's default band).

A vent's levels came mostly from corridor planes on every storey above it (PR-B-BATH-VENT:
19 planes, 8 of them on main, second and attic, none a terminal's); its terminals say which
storeys it can use. ``--level`` still wins: the caller applies this only where no band was
asked for. See docs/routing.md."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

#: A terminal this close under a datum is on it (the same sixteenth ``graph`` calls one line).
_TOL_M = 0.0015875


def terminal_band(datums: Iterable[float], zs: Sequence[float]
                  ) -> tuple[float, float] | None:
    """``(lowest terminal storey's datum, the datum above the highest)``, or None for no z.

    Storeys at one elevation are one band, as in ``route_support.storey_band``. The lowest
    storey runs down to its lowest terminal (a pit under the slab), the top one to infinity.
    """
    levels = sorted(set(datums))
    if not zs or not levels:
        return None

    def storey(z: float) -> int:
        return max((i for i, d in enumerate(levels) if d <= z + _TOL_M), default=0)

    low, high = storey(min(zs)), storey(max(zs))
    lower = min(levels[low], min(zs))
    upper = levels[high + 1] if high + 1 < len(levels) else float("inf")
    return (lower, upper)
