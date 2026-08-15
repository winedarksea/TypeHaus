"""In-wall backing courses: fire/nailer blocking between studs, and T-junction backing.

Split out of ``solver.py``: neither course belongs to the stud/plate/corner layout the
solver decides — they are what a *finish* trade nails into (drywall at an intersecting
partition, blocking at a fixed height), and both are driven entirely by ``FramingSpec``.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.tables import DEFAULT_TEE_BLOCKING_SPACING, member_actual
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember, ResolvedWall

_EPSILON = 1e-9


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
                       top_at) -> None:
    """Emit the through-wall backing selected by ``FramingSpec`` at one T branch."""
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
        members.append(FramedMember(
            rw.uid, f"tee-{junction_key}-block-{index:02d}", "blocking", member,
            block_start, block_end, elevation, elevation + block_height, depth_m,
        ))
        elevation += spacing
        index += 1
