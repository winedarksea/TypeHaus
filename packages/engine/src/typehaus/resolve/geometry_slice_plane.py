"""The cut plane itself, and the one measurement every solid owes it.

Split out of :mod:`typehaus.resolve.geometry_slice` for the reason AGENTS.md gives (that
module ran past 500 lines), and it is the seam that makes the split possible at all: the
plane, the profile it produces and the perpendicular-span reject are what *every* other
cutter needs, so they are the layer underneath rather than a peer.

``geometry_slice`` re-exports everything here, which is the name every call site imports.
Same import discipline as its parent — ``math``, ``dataclasses`` and ``resolve.*``, nothing
else, so the section kernel stays safe to run under Pyodide.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.geometry_ir import GBox, GPrism, GSolid, GSweep

# A (u, z) point in the section frame, metres.
Vec2UZ = tuple[float, float]

# How far to move a station off a coincident vertex, metres. 1e-7 m = 100 nm.
NUDGE_M = 1e-7
# Below this, two section-frame coordinates are the same point (mesh chain welding).
WELD_M = 1e-6


@dataclass(frozen=True)
class CutPlane:
    """A vertical cut plane. ``axis`` matches ``Slice.cut_direction`` exactly."""

    axis: str  # "x" | "y"
    station_m: float

    # Which plan coordinate the station measures (y for an "x" cut, x for a "y" cut) and
    # which one is u. Frozen-dataclass fields rather than properties because the reject test
    # reads them once per *vertex* of every solid in the model, per cut.
    perp_index: int = 0
    u_index: int = 0

    def __post_init__(self) -> None:
        if self.axis not in ("x", "y"):
            raise ValueError(f"CutPlane.axis must be 'x' or 'y', not {self.axis!r}")
        object.__setattr__(self, "perp_index", 1 if self.axis == "x" else 0)
        object.__setattr__(self, "u_index", 0 if self.axis == "x" else 1)

    def u_of(self, point) -> float:
        return point[self.u_index]

    def perp_of(self, point) -> float:
        return point[self.perp_index]

    def nudged(self, solid: GSolid) -> CutPlane:
        """This plane, moved off any of ``solid``'s vertices it sits exactly on.

        Called per solid rather than once per drawing: a station nudged clear of one wall's
        face may sit exactly on another's, and the whole point is that no ring is ever cut
        at one of its own vertices.

        The step goes **inward**, toward the middle of the solid's own perpendicular span.
        A cut landing exactly on an end face is common and deliberate — an authored
        foundation detail cut at the end of the wall it is about — and nudging outward there
        would silently drop the very element the drawing exists for. Inward, the plane
        grazes the end face and draws its cross-section, which is what the reader expects.
        """
        values = perp_values(solid, self.perp_index)
        if not values:
            return self
        return _nudge_off(self, values, min(values), max(values))


@dataclass(frozen=True)
class SectionProfile:
    """One closed face of a solid in the cut plane, in section coordinates.

    ``outline`` is the face; ``voids`` are holes through it. Both are closed implicitly (no
    repeated first point), matching the IR's ring convention.
    """

    outline: tuple[Vec2UZ, ...]
    voids: tuple[tuple[Vec2UZ, ...], ...] = ()


def perp_values(solid: GSolid, index: int) -> list[float]:
    """Every vertex's coordinate along one plan axis — the reject test's whole input.

    Yields the *coordinate* rather than the point because this is the hot loop: it runs once
    per vertex of every solid in the model for every cut, and a projection through a method
    call per vertex was half the drawing stage's time.
    """
    if isinstance(solid, GPrism):
        values = [point[index] for point in solid.ring]
        for void in solid.voids:
            values.extend(point[index] for point in void)
        return values
    if isinstance(solid, GBox):
        return ([point[index] for point in solid.corners_bottom]
                + [point[index] for point in solid.corners_top])
    if isinstance(solid, GSweep):
        shift = solid.extrude[index]
        values = [point[index] for point in solid.profile]
        return values + [value + shift for value in values]
    return [point[index] for point in solid.positions]


def solid_perp_span(solid: GSolid, plane: CutPlane) -> tuple[float, float]:
    """The solid's extent perpendicular to ``plane`` — the O(1) reject before slicing."""
    values = perp_values(solid, plane.perp_index)
    if not values:
        return (math.inf, -math.inf)
    return (min(values), max(values))


def _crosses(solid: GSolid, plane: CutPlane) -> bool:
    lo, hi = solid_perp_span(solid, plane)
    return lo <= plane.station_m <= hi


def _nudge_off(plane: CutPlane, values: list[float], lo: float, hi: float) -> CutPlane:
    """``plane.nudged`` with the vertex coordinates already in hand (see ``slice_solid``)."""
    step = NUDGE_M if plane.station_m <= (lo + hi) / 2.0 else -NUDGE_M
    station = plane.station_m
    for _ in range(4):
        if min(abs(value - station) for value in values) > NUDGE_M / 2.0:
            break
        station += step
    if station == plane.station_m:
        return plane
    return CutPlane(axis=plane.axis, station_m=station)


