"""Joist/rafter hangers derived from the resolved framing geometry.

The hanging condition is geometric, never nominal: a member is *hung* when one of its ends
lands inside the depth of a carrying beam instead of on top of it. That is what
distinguishes the rafters framing into the ridge beam (hung — the rafter tails sit in the
beam's depth) from the floor joists crossing the interior bearing wall (bearing — they sit
on the plate). No member is billed because of what it is called.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_catalog import (
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_SLOPED_JOIST_HANGER,
    hardware_for_role,
    hardware_row,
)
from typehaus.takeoff.hardware_config import HangerDetectionRules
from typehaus.takeoff.plan_geometry import centerline_endpoints, distance_point_to_segment


@dataclass(frozen=True)
class CarryingElement:
    """A beam (framed member or standalone solid) other members can hang off."""

    tag: str
    p0: tuple
    p1: tuple
    z0_m: float
    z1_m: float


@dataclass(frozen=True)
class HungConnection:
    """One detected hung end: which member, onto which carrier, sloped or level."""

    member_key: str
    member_profile: str
    carrier_tag: str
    sloped: bool


def _member_carriers(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    carriers = [
        CarryingElement(tag=f"{member.parent_uid}:{member.child_key}", p0=member.p0,
                        p1=member.p1, z0_m=member.z0_m, z1_m=member.z1_m)
        for member in model.all_members()
        if member.category in rules.carrier_member_categories
    ]
    for solid in model.solids:
        if solid.category not in rules.carrier_solid_categories:
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
                # depth is developed inside the carrier's depth.
                if bottom_z >= carrier.z1_m - seat_tolerance_m:
                    continue
                if top_z <= carrier.z0_m or bottom_z >= carrier.z1_m:
                    continue
                found.append(HungConnection(
                    member_key=f"{member.parent_uid}:{member.child_key}",
                    member_profile=member.profile, carrier_tag=carrier.tag, sloped=sloped))
                break  # one hanger per end, even where carriers overlap in plan
    return found


def _explicit_hanger_rows(model: ResolvedModel) -> list:
    """Hangers the resolver already emitted as their own members (stair members hung on a
    concrete wall). The supporting wall is found by geometry, and a foundation wall takes
    the concrete-rated hanger rather than the wood face-mount one."""
    hosts_by_role: dict = {}
    for hanger in model.all_members():
        if hanger.category != "hanger":
            continue
        host = _supporting_wall(model, hanger)
        role = (ROLE_CONCRETE_FACE_MOUNT_HANGER
                if host is not None and host.is_foundation
                else ROLE_FACE_MOUNT_JOIST_HANGER)
        hosts_by_role.setdefault(role, Counter())[host.tag if host else "unbound"] += 1

    rows = []
    for role in sorted(hosts_by_role):
        hosts = hosts_by_role[role]
        item = hardware_for_role(role)
        rows.append(hardware_row(
            item, scope="hung framing", count=int(sum(hosts.values())),
            basis=("resolver-emitted hanger members on " + ", ".join(
                f"{tag} x{count}" for tag, count in sorted(hosts.items())))))
    return rows


def _supporting_wall(model: ResolvedModel, member):
    """The resolved wall a hanger member is fastened to (nearest wall whose axis the hanger
    runs along and whose elevation range brackets it).

    Measured from the hanger's *midpoint*: an endpoint often lands exactly on a corner node
    shared by two walls, which is a tie the midpoint breaks correctly.
    """
    midpoint = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
    best, best_distance = None, float("inf")
    for wall in model.walls:
        if not (wall.z0_m - 1e-6 <= member.z0_m and member.z1_m <= wall.z1_m + 1e-6):
            continue
        distance = distance_point_to_segment(midpoint, wall.axis[0], wall.axis[1])
        if distance < best_distance:
            best, best_distance = wall, distance
    # A hanger is fastened to the wall's face, i.e. within half a wall thickness of its axis.
    if best is None or best_distance > best.thickness_m:
        return None
    return best


def joist_hanger_rows(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    """BOM lines for every hung framing connection, sloped and level billed separately."""
    groups: Counter = Counter()
    for connection in hung_connections(model, rules):
        role = ROLE_SLOPED_JOIST_HANGER if connection.sloped else ROLE_FACE_MOUNT_JOIST_HANGER
        groups[(role, connection.carrier_tag, connection.member_profile)] += 1

    rows = []
    for (role, carrier_tag, profile), count in sorted(groups.items()):
        item = hardware_for_role(role)
        carrier_name = carrier_tag.split(":")[-1]
        rows.append(hardware_row(
            item, scope="hung framing", count=count, size=profile,
            basis=(f"{count} x {profile} hung in the depth of {carrier_name} "
                   f"({'sloped/skewed' if role == ROLE_SLOPED_JOIST_HANGER else 'level'} "
                   f"connection derived from the resolved framing)")))
    return rows + _explicit_hanger_rows(model)
