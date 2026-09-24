"""Joist/rafter hanger ROWS, grouped from the hung joints.

Where a member hangs is :mod:`typehaus.joints.hung`' business — the condition is geometric,
never nominal, and no member is billed because of what it is called. This module is what a
framer buys: sloped and level hangers billed separately because they are different parts,
the ridge straps counted per opposing PAIR, and the hanger members the resolver emits in
their own right.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_SCL_FACE_MOUNT_HANGER,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_STAIR_STRINGER_CONNECTOR,
    hardware_for_role,
)
from typehaus.hardware.config import HangerDetectionRules
from typehaus.hardware.plan_geometry import distance_point_to_segment
from typehaus.joints.authored import hanger_part, hanger_specs
from typehaus.joints.hung import hung_connections, ridge_strap_pairs
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row


def ridge_tie_strap_rows(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    """One strap per opposing rafter pair over a ridge beam.

    The sloped hanger holds a rafter up in the beam's depth and does nothing across the peak.
    Weyerhaeuser's H5S ridge detail adds an LSTA24 rafter-to-rafter over the top for any slope
    above 3:12 (catlin's 4:12 is squarely in it) and APA D710 10c calls for the same from
    1/4:12.

    Counted per PAIR by station rather than as ``hangers // 2``, so a rafter that has lost its
    opposite number shows up as an uncounted end rather than half a strap.
    """
    rows = []
    for straps in ridge_strap_pairs(model, rules):
        item = hardware_for_role(ROLE_RIDGE_TIE_STRAP)
        carrier_name = straps.carrier_tag.split(":")[-1]
        pairs = len(straps.stations_m)
        note = (f" ({straps.unpaired} unpaired rafter end(s) take none)"
                if straps.unpaired else "")
        rows.append(hardware_row(
            item, scope="roof ridge", count=pairs,
            basis=(f"{pairs} opposing rafter pairs over {carrier_name}, one strap each "
                   f"(station-matched across the beam, not hangers/2){note}")))
    return rows


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
        # A resolver-emitted hanger is a stair member on an interior wall: dry.
        item = hardware_for_role(role, exposure=EXPOSURE_DRY)
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
    """BOM lines for every hung framing connection, sloped and level billed separately.

    An authored hanger spec for a (carrier, floor) joint names the part; the count is still
    every hung end the framing derives there."""
    specs = hanger_specs(model)
    groups: Counter = Counter()
    parts: dict = {}
    for connection in hung_connections(model, rules):
        role, item, part = hanger_part(connection, specs)
        key = (role, connection.carrier_tag, connection.member_profile, part)
        groups[key] += 1
        parts[key] = (item, connection.sloped)

    rows = []
    for key, count in sorted(groups.items()):
        role, carrier_tag, profile, part = key
        item, sloped = parts[key]
        carrier_name = carrier_tag.split(":")[-1]
        authored = role not in (ROLE_FACE_MOUNT_JOIST_HANGER, ROLE_SLOPED_JOIST_HANGER,
                                ROLE_SCL_FACE_MOUNT_HANGER, ROLE_STAIR_STRINGER_CONNECTOR)
        rows.append(hardware_row(
            item, scope="hung framing", count=count, size=profile, part_number=part,
            basis=(f"{count} x {profile} hung in the depth of {carrier_name} "
                   f"({'sloped/skewed' if sloped else 'level'} connection derived from the "
                   f"resolved framing"
                   f"{'; part authored for this joint' if authored else ''})")))
    return rows + _explicit_hanger_rows(model)
