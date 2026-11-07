"""The 1/16" grid a drain's profile is snapped to: ONE rule for the search and the proposal.

``route_fall`` snaps a found route from its arrival up, each leg's fall rounded UP, so
snapping never costs grade (drain basis §13). The search used to estimate that excess as
an allowance on the tie's floor (``gravity.grid_allowance``). For a route that starts
higher than its tie needs — "over" a banded prism, its band's floor above the tie's — the
proposal's profile hangs from that higher start, and the estimate missed by up to a step:
on catlin's ``tree:main+lift`` FX-M-KITCH-SINK was accepted at -0.047" and refused 0.062"
over its weir. Both sides now call :func:`grid_start` on the profile the proposal draws.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from typehaus.quantities import M_PER_IN

Point3 = tuple[float, float, float]


def on_grid(points: Sequence[Point3], grade: float) -> list[Point3]:
    """Snap to 1/16", building z from the arrival up with each leg's fall rounded UP."""
    from typehaus.routing.proposal import SNAP_IN, snap

    step = SNAP_IN * M_PER_IN
    plan = [(snap(x), snap(y)) for x, y, _z in points]
    z = [snap(p[2]) for p in points]
    for i in range(len(points) - 2, -1, -1):
        run_ft = math.dist(plan[i], plan[i + 1]) / 0.3048
        fall = math.ceil(grade * run_ft * M_PER_IN / step - 1e-6) * step if run_ft else 0.0
        z[i] = max(z[i], z[i + 1] + fall)
    return [(x, y, zz) for (x, y), zz in zip(plan, z, strict=True)]


def grid_start(points: Sequence[tuple[float, ...]], start_m: float, grade: float) -> float:
    """Where a profile from ``start_m`` at ``grade`` starts once :func:`on_grid` has it.

    The profile is the one ``route_fall`` draws for the route: each vertex ``start - slope
    x developed`` (an arrival-anchored profile is the same line with ``start`` at the
    tie's floor), a plumb drop into the tie adding nothing above its top."""
    from typehaus.routing.gravity import developed_lengths

    lengths = developed_lengths(points)
    profile = [(p[0], p[1], start_m - grade * length * M_PER_IN)
               for p, length in zip(points, lengths, strict=True)]
    return on_grid(profile, grade)[0][2]
