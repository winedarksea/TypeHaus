"""Raceway. The one trade whose element cannot say what the search finds.

A ``ConduitRun`` travels its plan polyline **flat** and rises vertically **only at its last
vertex** (``model/mep.py``). So a route with two changes of elevation is not expressible as
one ``ConduitRun`` — and the tempting move, emitting it anyway and letting the resolver
flatten it, produces geometry nobody authored and no check catches, because every
individual run resolves fine.

:func:`legalize` instead splits the route into one element per flat plane and **discloses
the chain**. Legalise and tell: a proposal that quietly became three runs is a proposal
whose reader will be surprised by the model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Leg:
    """One flat plan run and the rise at its end — exactly one ``ConduitRun``."""

    points: list[tuple[float, float]]
    z_m: float
    rise_to_m: float | None = None


def radius_m(trade_size_m: float) -> float:
    """Half the trade size.

    A raceway's trade size is a nominal BORE rather than an outside diameter, so this
    under-states by up to about an eighth of an inch on 3/4" EMT — the same reading
    ``checks/mep/routing_geometry.run_radii`` documents, and in the conservative direction
    for a hole and the wrong one for a clearance. It is stated rather than corrected
    because a correction would need a per-type outside diameter this catalog has not got.
    """
    return (trade_size_m or 0.0) / 2.0


def legalize(points: list[tuple[float, float, float]]) -> list[Leg]:
    """Split a 3-D route into flat legs, each ending in at most one rise.

    A route that never changes elevation comes back as one leg with no rise, which is the
    common case and is byte-identical to what a hand-authored run would be.
    """
    if not points:
        return []
    legs: list[Leg] = []
    current: list[tuple[float, float]] = [(points[0][0], points[0][1])]
    z = points[0][2]
    for previous, point in zip(points, points[1:], strict=False):
        flat = abs(point[2] - previous[2]) <= 1e-9
        if flat:
            current.append((point[0], point[1]))
            continue
        legs.append(Leg(points=list(current), z_m=z, rise_to_m=point[2]))
        current = [(point[0], point[1])]
        z = point[2]
    legs.append(Leg(points=list(current), z_m=z))
    return legs


def disclosure(legs: list[Leg]) -> str | None:
    """What to print when a route became more than one element, or None when it did not."""
    if len(legs) <= 1:
        return None
    return (f"this route changes elevation {len(legs) - 1} time(s) and a ConduitRun rises "
            f"only at its LAST vertex, so it is emitted as {len(legs)} runs. Each is a "
            "real element with its own tag and its own sleeve obligations; they are one "
            "raceway on the job and are not one run in the model")
