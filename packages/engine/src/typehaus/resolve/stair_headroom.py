"""The volume over a flight that R311.7.2 keeps clear, and the one place it is derived.

``code.R311_7_2_stair_headroom`` grades what stands in it and ``routing/obstacles`` refuses
to lane a run through it, following :func:`~typehaus.resolve.mep_envelopes.opening_prisms`:
two readers of one derivation, so a router cannot propose what the check will then fail.

One prism per going, off :func:`~typehaus.resolve.stairs.walkline.flight_stations` (a
landing's two edges are a going too). The top is the higher nosing plus 6'-8" — conservative
by at most one riser against the sloped line, which is right for a router, which chooses
rather than reads. The bottom is the underside of the flight's own structure under that
going, so a run can no more pass through a stringer than through the headroom above it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import ft

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

STAIR_HEADROOM = ft(6, 8)  # R311.7.2

#: Members that are the flight's own walking structure. A partition, a post or a hanger
#: stands to the floor below and would drag the prism down over the storage under it.
_STRUCTURE = frozenset({"tread", "winder", "landing", "landing_framing", "stringer"})


@dataclass(frozen=True)
class HeadroomPrism:
    """One going's clear volume: plan quad, its walking z, and the band that stays clear."""

    stair_tag: str
    footprint: Any  # shapely Polygon
    walk_z_m: float
    z0_m: float
    z1_m: float
    #: Which flight (or landing) this going belongs to, and its two station edges in climb
    #: order, so a reader can inflate a flight outward without splitting it at every riser.
    flight: str = ""
    near: tuple[Any, Any] = ((0.0, 0.0), (0.0, 0.0))
    far: tuple[Any, Any] = ((0.0, 0.0), (0.0, 0.0))
    first: bool = True
    last: bool = True


def _member_underside(member: Any, quad: Any) -> float | None:
    """The member's lowest z within ``quad``, interpolated along a raked axis."""
    from shapely.geometry import LineString, Point

    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.overlay import intersection

    if member.category not in _STRUCTURE and not (
            member.category == "hanger" and member.profile != "hanger"):  # a ledger
        return None
    if member.p0 == member.p1:
        return None  # a post
    if member.plan_outline:
        from shapely.geometry import Polygon

        footprint = Polygon(member.plan_outline)
    else:
        half = (getattr(cross_section(member.profile), "width_m", None) or 0.0381) / 2.0
        footprint = LineString([member.p0, member.p1]).buffer(half, cap_style="flat")
    meet = intersection(footprint, quad)
    if meet.is_empty or meet.area < 1e-6:
        return None
    if member.z0_end_m is None:
        return member.z0_m
    axis = LineString([member.p0, member.p1])
    ts = [axis.project(Point(c), normalized=True) for c in meet.envelope.exterior.coords]
    return min(member.z0_m + (member.z0_end_m - member.z0_m) * t
               for t in (min(ts), max(ts)))


def headroom_prisms(model: ResolvedModel,
                    headroom_m: float = STAIR_HEADROOM.meters) -> list[HeadroomPrism]:
    """Every going of every stair as the prism R311.7.2 keeps clear."""
    from shapely.geometry import Polygon

    from typehaus.resolve.stairs.walkline import flight_stations

    out: list[HeadroomPrism] = []
    for stair in model.stairs:
        for key, stations in flight_stations(stair).items():
            count = len(stations) - 1
            for index, ((a0, b0, z0), (a1, b1, z1)) in enumerate(
                    zip(stations, stations[1:], strict=False)):
                quad = Polygon([a0, b0, b1, a1])
                if not quad.is_valid or quad.area < 1e-6:
                    continue  # a fan line meeting its neighbour: no going to keep clear
                walk = min(z0, z1)
                undersides = [z for member in stair.members
                              if (z := _member_underside(member, quad)) is not None]
                out.append(HeadroomPrism(stair_tag=stair.tag, footprint=quad, walk_z_m=walk,
                                         z0_m=min([walk, *undersides]),
                                         z1_m=max(z0, z1) + headroom_m, flight=key,
                                         near=(a0, b0), far=(a1, b1), first=index == 0,
                                         last=index == count - 1))
    return out


def runs_over(model: ResolvedModel, stair_tag: str) -> list[Any]:
    """The run prisms (``mep_envelopes.Prism``, uninflated) that reach into a stair's volume.

    A pre-filter so the check's dense nosing-line sampling only tests what can matter.
    """
    from typehaus.resolve.mep_envelopes import envelopes
    from typehaus.resolve.overlay import union_all

    prisms = [p for p in headroom_prisms(model) if p.stair_tag == stair_tag]
    if not prisms:
        return []
    area = union_all([p.footprint for p in prisms])
    low = min(p.z0_m for p in prisms)
    high = max(p.z1_m for p in prisms)
    return [prism for envelope in envelopes(model) for prism in envelope.prisms
            if prism.z1_m > low and prism.z0_m < high and prism.footprint.intersects(area)]


def run_clearances(model: ResolvedModel, stair: Any
                   ) -> dict[str, tuple[float, tuple[float, float]]]:
    """``run tag -> (worst plumb clearance over the nosing line, where)`` for one stair.

    Exact rather than sampled: a 1" raceway crossing a flight is narrower than any sampling
    step worth paying for, so each run prism is intersected with each going and graded at
    the highest nosing z it overlaps. A prism wholly under that going's walking surface is
    under-stair storage and skipped; one through a tread reads negative.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import intersection
    from typehaus.resolve.stairs.walkline import flight_stations

    runs = runs_over(model, stair.tag)
    out: dict[str, tuple[float, tuple[float, float]]] = {}
    if not runs:
        return out
    for stations in flight_stations(stair).values():
        for (a0, b0, z0), (a1, b1, z1) in zip(stations, stations[1:], strict=False):
            quad = Polygon([a0, b0, b1, a1])
            if not quad.is_valid or quad.area < 1e-6:
                continue
            m0 = ((a0[0] + b0[0]) / 2.0, (a0[1] + b0[1]) / 2.0)
            dx, dy = (a1[0] + b1[0]) / 2.0 - m0[0], (a1[1] + b1[1]) / 2.0 - m0[1]
            span = dx * dx + dy * dy
            for prism in runs:
                meet = intersection(prism.footprint, quad)
                if meet.is_empty:
                    continue
                points = [(x, y) for x, y in meet.envelope.exterior.coords] \
                    if meet.area > 0 else list(meet.coords)
                walked = []
                for x, y in points:
                    t = 0.0 if span == 0 else ((x - m0[0]) * dx + (y - m0[1]) * dy) / span
                    walked.append((z0 + (z1 - z0) * min(1.0, max(0.0, t)), (x, y)))
                low, high = min(walked), max(walked)
                if prism.z1_m <= low[0] + 1e-3:
                    continue  # under the walk: storage, not headroom
                clearance = prism.z0_m - high[0]
                if prism.tag not in out or clearance < out[prism.tag][0]:
                    out[prism.tag] = (clearance, high[1])
    return out
