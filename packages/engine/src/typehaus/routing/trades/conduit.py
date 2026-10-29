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

import math
from dataclasses import dataclass

from typehaus.resolve.conduit_pulls import MAX_BEND_DEG_BETWEEN_PULLS
from typehaus.resolve.sweep import path_turns

Vec3 = tuple[float, float, float]

#: How far a re-route may pass from an authored box and still count as passing it (6").
PULL_TOLERANCE_M = 0.1524


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


@dataclass(frozen=True)
class PullPointAssignment:
    """The path with its pull boxes: ``points`` may hold vertices inserted for kept boxes."""

    points: tuple[Vec3, ...]
    indices: tuple[int, ...]  # interior only; the two ends are pull points already
    kept: int  # authored boxes the path still passes (an end counts)
    added: int  # pulls the 360 degree rule needed beyond the kept ones
    dropped: tuple[Vec3, ...]  # authored boxes no longer on the path

    def disclosure(self) -> str:
        parts = [f"kept {self.kept} authored", f"added {self.added}"]
        if self.dropped:
            parts.append(f"{len(self.dropped)} no longer on the path")
        return "pull points: " + ", ".join(parts)

    def as_dict(self) -> dict:
        return {"kept": self.kept, "added": self.added, "dropped": len(self.dropped),
                "dropped_at_m": [list(p) for p in self.dropped],
                "indices": list(self.indices)}


def _project(path: list[Vec3], box: Vec3) -> tuple[float, int, Vec3]:
    """``(distance, segment, foot)`` of the nearest point of the polyline to ``box``."""
    best: tuple[float, int, Vec3] = (math.inf, 0, path[0])
    for i, (a, b) in enumerate(zip(path, path[1:], strict=False)):
        ab = [b[k] - a[k] for k in range(3)]
        length2 = sum(c * c for c in ab)
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, sum(
            (box[k] - a[k]) * ab[k] for k in range(3)) / length2))
        foot = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
        best = min(best, (math.dist(foot, box), i, foot), key=lambda row: row[0])
    return best


def assign_pull_points(path: list[Vec3], boxes: tuple[Vec3, ...] = (), *,
                       tolerance_m: float = PULL_TOLERANCE_M) -> PullPointAssignment:
    """Keep the authored boxes the path still passes, then add what 360 degrees needs.

    A box within ``tolerance_m`` of an interior vertex lands on that vertex; one beside a
    straight stretch gets a vertex inserted at its foot (hence ``points``); one near an end
    is kept with no index. Anything farther is dropped and reported, never moved. Then
    bends are summed from the last pull point (the 3D turn measure of ``conduit_pulls``,
    where a bend AT a pull point is not counted) and the vertex that would carry a section
    past 360 degrees becomes a pull point, so every section ends at or under the limit.
    """
    from typehaus.routing.proposal import snap

    pts = list(path)
    marked: set[int] = set()
    kept = 0
    dropped: list[Vec3] = []
    for box in boxes:
        if len(pts) < 2:
            dropped.append(box)
            continue
        interior = [(math.dist(pts[i], box), i) for i in range(1, len(pts) - 1)]
        near = min(interior, default=(math.inf, 0))
        if near[0] <= tolerance_m:
            marked.add(near[1])
            kept += 1
        elif min(math.dist(pts[0], box), math.dist(pts[-1], box)) <= tolerance_m:
            kept += 1
        else:
            distance, segment, foot = _project(pts, box)
            if distance > tolerance_m:
                dropped.append(box)
                continue
            pts.insert(segment + 1, (snap(foot[0]), snap(foot[1]), snap(foot[2])))
            marked = {m + 1 if m > segment else m for m in marked} | {segment + 1}
            kept += 1
    angles = {turn.index: turn.angle_deg for turn in path_turns(pts)}
    total, added = 0.0, 0
    for i in range(1, len(pts) - 1):
        if i in marked:
            total = 0.0
        elif total + angles.get(i, 0.0) > MAX_BEND_DEG_BETWEEN_PULLS + 1e-6:
            marked.add(i)  # its own bend is then the box's, not the conduit's
            added += 1
            total = 0.0
        else:
            total += angles.get(i, 0.0)
    return PullPointAssignment(points=tuple(pts), indices=tuple(sorted(marked)), kept=kept,
                               added=added, dropped=tuple(dropped))
