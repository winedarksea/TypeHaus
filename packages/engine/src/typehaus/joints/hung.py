"""Where members **hang** — the joints developed inside a carrier's depth.

The hanging condition is geometric, never nominal: a member is *hung* when one of its ends
lands inside the depth of a carrying beam instead of on top of it. That is what
distinguishes the rafters framing into the ridge beam (hung — the rafter tails sit in the
beam's depth) from the floor joists crossing the interior bearing wall (bearing — they sit
on the plate, and :mod:`typehaus.joints.bearing` has them). No member is located because of
what it is called.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.config import HangerDetectionRules
from typehaus.hardware.plan_geometry import centerline_endpoints, distance_point_to_segment
from typehaus.joints.model import axis_of
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sweep import interpolate_along, straight_sweep_band


@dataclass(frozen=True)
class CarryingElement:
    """A beam (framed member or standalone solid) other members can hang off."""

    tag: str
    p0: tuple
    p1: tuple
    z0_m: float
    z1_m: float
    category: str = "beam"
    #: Soffit and top at ``p1``, for a carrier that is not level — a TILTED beam
    #: (``Beam.top_rise_end``). ``None`` is a level carrier and the flat pair above answers
    #: for the whole run. Without this the run's bounding box stands in for its section, and
    #: a 2" drainage tilt makes an 11 7/8" beam look 14 1/2" deep — deep enough for every
    #: joist BEARING on it to read as hung inside it.
    z0_end_m: float | None = None
    z1_end_m: float | None = None

    def band_at(self, point) -> tuple[float, float]:
        """``(soffit, top)`` at plan ``point`` along this carrier."""
        if self.z0_end_m is None:
            return self.z0_m, self.z1_m
        seg = (self.p0, self.p1)
        return (interpolate_along(seg, point, self.z0_m, self.z0_end_m),
                interpolate_along(seg, point, self.z1_m, self.z1_end_m))


@dataclass(frozen=True)
class HungConnection:
    """One detected hung end: which member, onto which carrier, sloped or level."""

    member_key: str
    member_profile: str
    carrier_tag: str
    sloped: bool
    # What the carrier IS, not what it is called. A ridge beam takes a strap across it that
    # a girder does not, and reading that off the tag string would be reading a uid.
    carrier_category: str = "beam"
    # Where along the carrier the hung end lands. Two rafters meeting over a ridge share this
    # station, which is what lets a per-PAIR part be counted without dividing by two and
    # hoping.
    station_m: float = 0.0
    #: Plan point of the hung end, in project-frame metres.
    point_m: tuple = (0.0, 0.0)
    #: The carrier's SOFFIT under this end — a hanger seats off the carrier's underside and
    #: carries the member's depth up from there, so the soffit is the face to anchor to.
    carrier_soffit_m: float = 0.0
    #: The hung member's own depth at this end, for a marker sized like the hanger.
    member_depth_m: float = 0.0
    #: The carrier line, snapped to ``"x"``/``"y"``. A hanger straddles the carrier, so the
    #: carrier's direction is what orients it.
    axis: str = "x"


def _member_carriers(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    carriers = [
        CarryingElement(tag=f"{member.parent_uid}:{member.child_key}", p0=member.p0,
                        p1=member.p1, z0_m=member.z0_m, z1_m=member.z1_m,
                        category=member.category)
        for member in model.all_members()
        if member.category in rules.carrier_member_categories
    ]
    for solid in model.solids:
        if solid.category not in rules.carrier_solid_categories:
            continue
        band = straight_sweep_band(solid)
        if band is not None:
            (start, end), depth, soffit0, soffit1 = band
            carriers.append(CarryingElement(
                tag=solid.tag, p0=start, p1=end, z0_m=soffit0, z1_m=soffit0 + depth,
                z0_end_m=soffit1, z1_end_m=soffit1 + depth))
            continue
        start, end = centerline_endpoints(list(solid.outline))
        carriers.append(CarryingElement(tag=solid.tag, p0=start, p1=end,
                                        z0_m=solid.z0_m, z1_m=solid.z1_m))
    return carriers


def _member_ends(member) -> list:
    """Both ends as ``(point, bottom_z, top_z)``; a raked member carries its own end
    elevations, which is exactly what tells a ridge connection from an eave one."""
    return [
        (member.p0, member.z0_m, member.z1_m),
        (member.p1,
         member.z0_m if member.z0_end_m is None else member.z0_end_m,
         member.z1_m if member.z1_end_m is None else member.z1_end_m),
    ]


def hung_connections(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    """Every framed member end that hangs in a carrier's depth."""
    carriers = _member_carriers(model, rules)
    if not carriers:
        return []
    gap_tolerance_m = rules.end_gap_tolerance_in * M_PER_IN
    seat_tolerance_m = rules.bearing_seat_tolerance_in * M_PER_IN

    found: list = []
    for member in model.all_members():
        if member.category not in rules.hangable_member_categories:
            continue
        sloped = member.z0_end_m is not None or member.z1_end_m is not None
        for point, bottom_z, top_z in _member_ends(member):
            for carrier in carriers:
                if distance_point_to_segment(point, carrier.p0, carrier.p1) > gap_tolerance_m:
                    continue
                # Bearing on top of the carrier is not a hanger; hanging means the member's
                # depth is developed inside the carrier's depth. Measured AT THE HUNG END's
                # plan point, because a tilted carrier's depth is somewhere different at
                # every station along it.
                carrier_z0, carrier_z1 = carrier.band_at(point)
                if bottom_z >= carrier_z1 - seat_tolerance_m:
                    continue
                if top_z <= carrier_z0 or bottom_z >= carrier_z1:
                    continue
                found.append(HungConnection(
                    member_key=f"{member.parent_uid}:{member.child_key}",
                    member_profile=member.profile, carrier_tag=carrier.tag, sloped=sloped,
                    carrier_category=carrier.category,
                    station_m=_station_along(point, carrier),
                    point_m=(point[0], point[1]), carrier_soffit_m=carrier_z0,
                    member_depth_m=max(top_z - bottom_z, 0.0),
                    axis=axis_of(carrier.p0, carrier.p1)))
                break  # one hanger per end, even where carriers overlap in plan
    return found


def _station_along(point, carrier: CarryingElement) -> float:
    """How far along the carrier's own axis a hung end lands, in meters from its start."""
    (ax, ay), (bx, by) = carrier.p0, carrier.p1
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return 0.0
    return ((point[0] - ax) * dx + (point[1] - ay) * dy) / run


#: Two rafter ends this close along the ridge are the same station — one opposing pair, one
#: strap. They are trimmed to opposite faces of the beam, so they never share a plan point;
#: what they share is the station, and half an inch is far tighter than the 16" that separates
#: one station from the next.
_PAIR_STATION_TOL_M = 0.5 * M_PER_IN


@dataclass(frozen=True)
class RidgeStraps:
    """The straps over one ridge carrier, and the rafter ends that got none."""

    carrier_tag: str
    #: One station per PAIR, in metres along the carrier from its start. Counted by station
    #: rather than as ``hangers // 2``, so a rafter that has lost its opposite number shows
    #: up as an uncounted end rather than half a strap.
    stations_m: tuple[float, ...]
    unpaired: int
    p0: tuple
    p1: tuple
    #: The carrier's TOP: a strap crosses over the peak, not through the beam.
    z_m: float
    axis: str


def ridge_strap_pairs(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    """One entry per ridge carrier: where its straps go, and how many ends are unpaired.

    The sloped hanger holds a rafter up in the beam's depth and does nothing across the
    peak. Weyerhaeuser's H5S ridge detail adds an LSTA24 rafter-to-rafter over the top for
    any slope above 3:12 (catlin's 4:12 is squarely in it) and APA D710 10c calls for the
    same from 1/4:12.
    """
    carriers = {carrier.tag: carrier for carrier in _member_carriers(model, rules)}
    stations: dict[str, list[float]] = {}
    for connection in hung_connections(model, rules):
        if connection.carrier_category != "ridge_beam":
            continue
        stations.setdefault(connection.carrier_tag, []).append(connection.station_m)

    found = []
    for carrier_tag in sorted(stations):
        values = sorted(stations[carrier_tag])
        paired: list[float] = []
        unpaired, index = 0, 0
        while index < len(values):
            if (index + 1 < len(values)
                    and values[index + 1] - values[index] <= _PAIR_STATION_TOL_M):
                # The two ends are trimmed to opposite faces of the beam and never share a
                # plan point; the strap sits between them, which is their mean station.
                paired.append((values[index] + values[index + 1]) / 2.0)
                index += 2
            else:
                unpaired += 1
                index += 1
        if not paired:
            continue
        carrier = carriers.get(carrier_tag)
        if carrier is None:
            continue
        found.append(RidgeStraps(
            carrier_tag=carrier_tag, stations_m=tuple(paired), unpaired=unpaired,
            p0=carrier.p0, p1=carrier.p1, z_m=carrier.z1_m,
            axis=axis_of(carrier.p0, carrier.p1)))
    return found


def point_along(carrier_p0: tuple, carrier_p1: tuple, station_m: float) -> tuple:
    """The plan point ``station_m`` along a carrier — the inverse of :func:`_station_along`."""
    (ax, ay), (bx, by) = carrier_p0, carrier_p1
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return (ax, ay)
    return (ax + dx * station_m / run, ay + dy * station_m / run)
