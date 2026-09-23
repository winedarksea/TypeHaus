"""What a run's envelope occupies of a framing solid: the geometry three checks share.

Readers: ``floor_members`` (``mep.run_through_floor_member``), ``joist_flange``
(``mep.run_in_joist_flange``) and ``wall_cavity`` (the per-wall half of
``mep.run_through_stud``). The envelope is :mod:`typehaus.resolve.mep_envelopes` — real
outside diameter plus lagging, one prism per segment — so these grade the solid the router
plans against. Nothing here grades anything.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember, ResolvedModel

#: Overlap below this is a drawing tangency, not a cut (the ``mep.run_through_beam`` value).
TOLERANCE_M = 0.125 * M_PER_IN


@dataclass(frozen=True)
class Leg:
    """One segment of one run, with its envelope prism's plan footprint."""

    kind: str
    tag: str
    index: int
    a: tuple[float, float]
    b: tuple[float, float]
    za: float
    zb: float
    radius_m: float  # plan half-width of the envelope: outside + lagging
    footprint: Any
    half_z_m: float = 0.0  # vertical half-depth: a 10x8 duct is 4" tall either side

    @property
    def plan_m(self) -> float:
        return math.dist(self.a, self.b)

    @property
    def is_riser(self) -> bool:
        """A leg whose rise beats its plan travel crosses a floor the long way."""
        return abs(self.zb - self.za) > self.plan_m

    def axis(self) -> Any:
        from shapely.geometry import LineString, Point

        return Point(self.a) if self.plan_m < 1e-9 else LineString([self.a, self.b])


def legs(model: ResolvedModel) -> list[Leg]:
    """Every placed segment of every run, read off ``mep_envelopes.envelopes``."""
    from typehaus.resolve.mep_envelopes import (
        envelopes,
        insulation_thickness_m,
        run_polylines,
        run_sections,
    )

    sections = run_sections(model)
    out: list[Leg] = []
    for (kind, tag, path, z), envelope in zip(run_polylines(model), envelopes(model),
                                              strict=True):
        half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        # The prism's own growth: the same sums ``run_envelope`` buffers by.
        lagging = insulation_thickness_m(insulation) or 0.0
        for prism in envelope.prisms:
            i = prism.segment
            a, b = tuple(path[i]), tuple(path[i + 1])
            out.append(Leg(kind, tag, i, a, b, z[i], z[i + 1], half_w + lagging,
                           _flat_capped(prism.footprint, a, b, half_w + lagging),
                           half_d + lagging))
    return out


def _flat_capped(footprint: Any, a: Any, b: Any, radius: float) -> Any:
    """The prism's footprint without its round end caps.

    A run ends at its vertex: a round cap put 9" of an 18" duct's end into the wall past it,
    and at a bend the next leg covers the corner anyway. A riser keeps its circle.
    """
    from shapely.geometry import LineString

    if a == b or radius <= 0:
        return footprint
    return LineString([a, b]).buffer(radius, cap_style="flat")


def band_over(leg: Leg, shape: Any) -> tuple[float, float] | None:
    """The centreline's z range over the stretch whose SURFACE is over ``shape`` in plan.

    Interpolated, never the whole segment's band: a drain falling six feet at one end is not
    in every member it passes over (``checks/mep/routing_geometry.crossing_band``).
    """
    from shapely.geometry import Point

    if not leg.footprint.intersects(shape):
        return None
    if leg.plan_m < 1e-9:
        return min(leg.za, leg.zb), max(leg.za, leg.zb)
    line = leg.axis()
    clipped = line.intersection(shape.buffer(leg.radius_m))
    if clipped.is_empty:
        return None
    zs = [leg.za + (leg.zb - leg.za) * line.project(Point(xy)) / line.length
          for piece in getattr(clipped, "geoms", [clipped]) for xy in piece.coords]
    return min(zs), max(zs)


def z_overlap(leg: Leg, band: tuple[float, float], z0: float, z1: float) -> float:
    """How far the surface over ``band`` stands inside ``[z0, z1]``; <= 0 is clear."""
    return min(band[1] + leg.half_z_m, z1) - max(band[0] - leg.half_z_m, z0)


def extent_along(shape: Any, direction: tuple[float, float]) -> tuple[float, float]:
    """``shape``'s coordinates projected onto a unit ``direction``: (min, max)."""
    coords = [xy for part in getattr(shape, "geoms", [shape])
              for xy in (part.exterior.coords if hasattr(part, "exterior") else part.coords)]
    values = [x * direction[0] + y * direction[1] for x, y in coords]
    return (min(values), max(values)) if values else (0.0, 0.0)


def bite(leg: Leg, shape: Any, normal: tuple[float, float]) -> float:
    """How deep the envelope reaches into a member's ``shape``: the lesser of the overlap's
    extent across the member (``normal``) and along it, so a clipped END reads as the clip
    and not as the member's whole width."""
    overlap = leg.footprint.intersection(shape)
    if overlap.is_empty or overlap.area <= 0:
        return 0.0
    low, high = extent_along(overlap, normal)
    start, end = extent_along(overlap, (normal[1], -normal[0]))
    return min(high - low, end - start)


def member_axis(member: FramedMember) -> tuple[tuple[float, float], tuple[float, float]]:
    """(unit direction, unit plan normal) of a horizontal member."""
    (ax, ay), (bx, by) = member.p0, member.p1
    length = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / length, (by - ay) / length
    return (ux, uy), (-uy, ux)


def relation(leg: Leg, member: FramedMember) -> str:
    """``"riser"``, ``"across"`` (the centreline crosses the member's axis) or ``"along"``.

    Crossing the AXIS, not an angle: a shallow diagonal through a joist is still a hole
    through its web, and a leg parallel beside it that clips a face is a notch the length
    of the overlap.
    """
    from shapely.geometry import LineString

    if leg.is_riser:
        return "riser"
    axis = LineString([member.p0, member.p1])
    return "across" if leg.axis().crosses(axis) else "along"


def member_footprint(member: FramedMember) -> tuple[Any, float, float] | None:
    """A member's plan polygon and its z band, from ``geometry_members.member_box``."""
    from shapely.geometry import MultiPoint

    from typehaus.resolve.geometry_members import member_box

    box = member_box(member)
    if box is None:
        return None
    corners = [*box.corners_bottom, *box.corners_top]
    footprint = MultiPoint([(x, y) for x, y, _ in corners]).convex_hull
    if footprint.area <= 0:
        return None
    return footprint, min(c[2] for c in corners), max(c[2] for c in corners)


def at(point: tuple[float, float]) -> str:
    """A plan point in inches, the way the TODO and the notes spell stations."""
    return f'({point[0] / M_PER_IN:.2f}", {point[1] / M_PER_IN:.2f}")'
