"""Where ``haus route --group`` may tie a bathroom group into its main (``cmd_route_group``).

A main can cross a floor-system seam on its way past the room, and a seam is a joist break a
branch cannot cross cheaply, so the offer spans the systems rather than the main's highest
points alone. Bound: ``MAX_TIES`` stations, at most ``MAX_AUTHORED`` of them the plan's own;
every other slot is dealt round-robin to the floor systems the main passes through, nearest the
room first, best (highest) station of each system before any system's second. Each station is a
full gravity search when the ones before it refuse (``cmd_route_group._lay``, ``_dry``)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from shapely.geometry import Point, Polygon

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

MAX_TIES = 4
MAX_AUTHORED = 2
PER_SYSTEM = 3
_SPREAD_M = 8 * M_PER_IN


def tie_stations(model: ResolvedModel, authored: list, pts: list, band: tuple[float, float],
                 lifted: frozenset[str], site: tuple[str, tuple[float, float]]) -> list[tuple]:
    """Where the group may tie in, best first: its authored ties, highest first (where the
    plan already ties it, band or no band; at most ``MAX_AUTHORED``), then the tie run's
    stations inside ``band`` (sampled every 1/4", spread 8" apart, highest first), each a 3"
    wye's pitch clear of every inlet left on it (``route_roots._spaced_goals``' test), dealt
    per floor system of ``site``'s storey — the system nearest ``site``'s plan point first,
    ``PER_SYSTEM`` each, the whole offer capped at ``MAX_TIES``."""
    from typehaus.resolve.mep_inlet_spacing import level_inlets, main_inlet_pitch_m

    pitch = main_inlet_pitch_m(3 * M_PER_IN) or 0.0
    inlets = level_inlets(model.pipe_runs, lifted)

    def clear(p: tuple, banded: bool = True) -> bool:
        return (not banded or band[0] <= p[2] <= band[1]) and all(
            abs(z - p[2]) >= pitch or abs(x - p[0]) + abs(y - p[1]) >= pitch
            for x, y, z, _t in inlets)

    sampled = [tuple(a[i] + k / n * (b[i] - a[i]) for i in range(3))
               for a, b in zip(pts, pts[1:], strict=False)
               for n in [max(1, int(math.dist(a, b) / (0.25 * M_PER_IN)))]
               for k in range(n + 1)]
    storey, near = site
    decks = [Polygon(f.deck_outline) for f in model.floors
             if f.storey == storey and len(f.deck_outline) >= 3] or [Polygon()]
    # Spread at least a joist bay's half apart: a station hard by a member takes no drop.
    spread: list[list[tuple]] = [[] for _ in decks]
    for p in sorted(sampled, key=lambda p: -p[2]):
        if not clear(p):
            continue
        at = min(range(len(decks)), key=lambda i: decks[i].distance(Point(p[:2])))
        if len(spread[at]) < PER_SYSTEM and all(math.dist(p[:2], q[:2]) >= _SPREAD_M
                                                for s in spread for q in s):
            spread[at].append(p)
    ranked = sorted(zip(decks, spread, strict=True), key=lambda ds: ds[0].distance(Point(near)))
    dealt = [s[k] for k in range(PER_SYSTEM) for _d, s in ranked if k < len(s)]
    keep = [p for p in authored if clear(p, False)][:MAX_AUTHORED]
    return (keep + dealt)[:MAX_TIES]
