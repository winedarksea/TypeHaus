"""What the walking surface does under a railing — the one difference between flat and raking.

The flat and the raking railing resolvers used to be two whole function bodies that differed
in exactly one thing: what elevation the walking surface is at under a point, and whether it
varies along a run. Everything else — post stations, rails, and now three styles of infill —
was written twice. This module captures that one difference so the rest is written once.

A :class:`RailingSurface` answers two questions:

* ``height_at(p)`` — the walking-surface elevation under one plan point (where a post's foot
  and a picket's foot land).
* ``spans(a, b)`` — how to break the run ``a → b`` into flat bands, each with the surface
  elevation under it. A flat railing returns the whole run as one band; a raking one returns
  a ladder of short bands stepping along the slope.

Both are called at two granularities and mean the same thing at each: ``spans`` over a *path
segment* draws that segment's rails, and ``spans`` over a *bay* (post face to post face)
draws that bay's infill.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from typehaus.resolve.geometry import Vec, length, sub
from typehaus.resolve.stairs.walkline import flight_walklines, walkline_z_at

#: ``(pa, pb, surface_z)`` — one flat band of a run, and the walking surface under it.
Span = tuple[Vec, Vec, float]
SpanFn = Callable[[Vec, Vec], list[Span]]

# Sloped-rail banding: plan length of each flat band approximating a raking rail, and how
# far a path point may sit from every flight centreline before it is judged *off* the stair
# (and rides at the authored ``base_elevation`` instead). 2 m clears a rail path at the far
# edge of a code-width flight plus a landing's depth without ever reaching the next lane's
# flight one storey away in plan.
RAIL_BAND_STEP_M = 0.25
RAIL_STAIR_REACH_M = 2.0


@dataclass(frozen=True)
class RailingSurface:
    """The walking surface under one railing, as the two questions every part asks of it."""

    height_at: Callable[[Vec], float]
    spans: SpanFn


def flat_surface(base_m: float) -> RailingSurface:
    """A railing riding one authored elevation — a balcony edge, a floor-edge guard.

    One span per run: a flat rail is a single band, and breaking it into steps would put
    joints in a rail that has none and multiply the solid count for nothing.
    """
    def height_at(_point: Vec) -> float:
        return base_m

    def spans(a: Vec, b: Vec) -> list[Span]:
        return [(a, b, base_m)]

    return RailingSurface(height_at=height_at, spans=spans)


def raking_surface(stair, base_m: float) -> RailingSurface:
    """A ``serves_stair`` railing raking along its stair's sloped nosing line.

    A flat resolver extrudes every rail at one elevation, which turns an authored stair
    handrail into a horizontal bar floating over the flight. Here each post stands on the
    walking surface under it — the interpolated nosing line of the nearest flight
    (:mod:`typehaus.resolve.stairs.walkline`, the same derivation the R311.7 checks
    measure). Rails become short flat bands stepping along the slope: the boxes-only solid
    IR extrudes plan outlines vertically, so a raking run is approximated exactly the way
    the round pipe sweeps are (→ :mod:`typehaus.resolve.round_solids`). Take-off is
    unaffected — railings bill per element (takeoff/railings.py), never off these solids.
    Path points beyond every flight (a rail continuing onto a floor edge) fall back to the
    authored ``base_elevation``, so a guard-and-handrail wrapping a well corner stays level
    where the floor is.
    """
    lines = flight_walklines(stair)

    def height_at(point: Vec) -> float:
        z = walkline_z_at(lines, point, RAIL_STAIR_REACH_M)
        return base_m if z is None else z

    def spans(a: Vec, b: Vec) -> list[Span]:
        run = length(sub(b, a))
        steps = max(int(math.ceil(run / RAIL_BAND_STEP_M)), 1)
        out: list[Span] = []
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            out.append((pa, pb, height_at(((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0))))
        return out

    return RailingSurface(height_at=height_at, spans=spans)
