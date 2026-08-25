"""In-wall backing courses: fire/nailer blocking between studs, and T-junction backing.

Split out of ``solver.py``: neither course belongs to the stud/plate/corner layout the
solver decides — they are what a *finish* trade nails into (drywall at an intersecting
partition, blocking at a fixed height), and both are driven entirely by ``FramingSpec``.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.tables import DEFAULT_TEE_BLOCKING_SPACING, member_actual
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember, ResolvedWall

_EPSILON = 1e-9
_VERTICAL_OPENING_MEMBERS_THAT_ACCEPT_BLOCKING = frozenset({
    "stud", "king", "jack", "cripple",
})


def _convex_footprints_have_positive_area_overlap(
        first_ring: list[tuple[float, float]],
        second_ring: list[tuple[float, float]]) -> bool:
    """Return whether two convex member footprints overlap in area, not just at a face."""
    for ring in (first_ring, second_ring):
        for index, start in enumerate(ring):
            end = ring[(index + 1) % len(ring)]
            edge_x, edge_y = end[0] - start[0], end[1] - start[1]
            edge_length = math.hypot(edge_x, edge_y)
            if edge_length <= _EPSILON:
                continue
            axis = (-edge_y / edge_length, edge_x / edge_length)
            first_projection = [x * axis[0] + y * axis[1] for x, y in first_ring]
            second_projection = [x * axis[0] + y * axis[1] for x, y in second_ring]
            overlap = (min(max(first_projection), max(second_projection))
                       - max(min(first_projection), min(second_projection)))
            if overlap <= _EPSILON:
                return False
    return True


def _framing_members_have_positive_volume_overlap(
        first_member: FramedMember, second_member: FramedMember) -> bool:
    """Use emitted member footprints and elevations so face contact remains legal."""
    first_ring, first_z0, first_z1 = member_footprint(first_member)
    second_ring, second_z0, second_z1 = member_footprint(second_member)
    vertical_overlap = min(first_z1, second_z1) - max(first_z0, second_z0)
    return (vertical_overlap > _EPSILON
            and _convex_footprints_have_positive_area_overlap(first_ring, second_ring))


def append_blocking_rows(members: list[FramedMember], rw: ResolvedWall, spec, member: str,
                         direction, wall_start, stud_bottom: float, spacing: float,
                         stud_stations: list[float]) -> None:
    """Emit a horizontal blocking course fitted between studs at each configured height.

    One block per stud bay, butting the flanking studs (the same-wall blocking/stud
    contact the interference check treats as intended nailing). Bays wider than ~1.5
    modules — an opening — are skipped so a block never spans an opening.
    """
    heights = getattr(spec, "blocking_heights", ()) or ()
    if not heights or len(stud_stations) < 2:
        return
    thickness = member_actual(member)[0] * M_PER_IN
    block_height = thickness  # a flat 2x course
    max_bay = spacing * 1.5
    stations = sorted(stud_stations)
    for hi, height in enumerate(heights):
        base = stud_bottom + height.meters
        for bi in range(len(stations) - 1):
            s0, s1 = stations[bi], stations[bi + 1]
            if s1 - s0 > max_bay or s1 - s0 <= thickness:
                continue  # opening bay, or studs too close to fit a block
            a = add(wall_start, scale(direction, s0 + thickness / 2))
            b = add(wall_start, scale(direction, s1 - thickness / 2))
            members.append(FramedMember(
                rw.uid, f"blocking-{hi}-{bi:03d}", "blocking", member, a, b,
                base, base + block_height, s1 - s0 - thickness,
            ))


def append_tee_backing(members: list[FramedMember], rw: ResolvedWall, spec,
                       member: str, direction, wall_start, axis_len: float,
                       station: float, junction_key: str, stud_bottom: float,
                       top_at,
                       opening_framing_members: tuple[FramedMember, ...] = ()) -> None:
    """Emit through-wall backing, yielding ladder elevations occupied by opening framing."""
    station = min(max(station, 0.0), axis_len)
    if spec.tee_backing_style == "none":
        return
    center = add(wall_start, scale(direction, station))
    if spec.tee_backing_style == "stud-pack":
        thickness_m = member_actual(member)[0] * M_PER_IN
        for index, offset in enumerate((-thickness_m, thickness_m)):
            stud_station = min(max(station + offset, 0.0), axis_len)
            point = add(wall_start, scale(direction, stud_station))
            stud_top = top_at(stud_station)
            members.append(FramedMember(
                rw.uid, f"tee-{junction_key}-stud-{index}", "corner", member,
                point, point, stud_bottom, stud_top, stud_top - stud_bottom,
                orient=direction,
            ))
        return

    depth_m = member_actual(member)[1] * M_PER_IN
    perpendicular = (-direction[1], direction[0])
    half_depth = depth_m / 2.0
    block_start = add(center, scale(perpendicular, -half_depth))
    block_end = add(center, scale(perpendicular, half_depth))
    block_height = member_actual(member)[0] * M_PER_IN
    spacing = (spec.tee_blocking_spacing or DEFAULT_TEE_BLOCKING_SPACING).meters
    top = top_at(station)
    elevation = stud_bottom + spacing
    index = 0
    while elevation + block_height < top - _EPSILON:
        candidate = FramedMember(
            rw.uid, f"tee-{junction_key}-block-{index:02d}", "blocking", member,
            block_start, block_end, elevation, elevation + block_height, depth_m,
        )
        # Horizontal opening framing owns its volume; a ladder rung is only finish backing.
        # Vertical jamb/cripple members are different: blocking is face-nailed into them by
        # design, just as ordinary in-line blocking is nailed into a stud. Keeping those
        # contacts is what preserves every useful rung around the one occupied elevation.
        if not any(
            opening_member.category not in _VERTICAL_OPENING_MEMBERS_THAT_ACCEPT_BLOCKING
            and _framing_members_have_positive_volume_overlap(candidate, opening_member)
            for opening_member in opening_framing_members
        ):
            members.append(candidate)
        elevation += spacing
        index += 1
