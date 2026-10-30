"""Screws for skirted stair stringers held off the wall on a 2x spacer.

``resolve/stairs/bearing._spacer_carriage`` stands such a stringer a flat 2x4 off the studs;
it is screwed through stringer and spacer into every stud the spacer crosses. Hand check:
houses/catlin/notes/stair_skirt_basis.md §6.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import ROLE_STAIR_SPACER_SCREW, hardware_for_role
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

_SPACER = "framed-wall-spacer:"
_STUD_KINDS = frozenset({"stud", "king", "jack", "corner"})
_M_PER_IN = 0.0254


def stair_spacer_screw_rows(model: ResolvedModel) -> list:
    """One screw per stud a stringer's spacer crosses, sized so its thread is all in the stud."""
    walls = {wall.tag: wall for wall in model.walls}
    members = list(model.all_members())
    by_host: Counter = Counter()
    stack_in = None
    for spacer in members:
        if spacer.category != "blocking" or not (spacer.connection or "").startswith(_SPACER):
            continue
        host = walls[spacer.connection.removeprefix(_SPACER)]
        stringer = next(m for m in members if m.category == "stringer"
                        and m.parent_uid == spacer.parent_uid
                        and m.connection == spacer.connection)
        stack_in = (cross_section(stringer.profile).width_m
                    + cross_section(spacer.profile).width_m) / _M_PER_IN
        by_host[host.tag] += _studs_crossed(members, host.uid, spacer)
    if not by_host:
        return []
    item = hardware_for_role(ROLE_STAIR_SPACER_SCREW)
    length = min(length for length, thread in item.thread_length_in_by_length_in.items()
                 if length - thread >= stack_in - 1e-6)
    thread = item.thread_length_in_by_length_in[length]
    return [hardware_row(
        item, scope="stair stringer spacers", count=sum(by_host.values()),
        part_number=item.part_number_by_length_in[length], size=f"{length:g} in",
        basis=(f"1 per stud each skirted stringer's flat 2x4 spacer crosses, through stringer "
               f"+ spacer ({stack_in:.2f} in stack spanned by plain shank), all {thread:g} in "
               "of thread in the stud; " + ", ".join(
                   f"{tag} x{count}" for tag, count in sorted(by_host.items()))))]


def _studs_crossed(members, wall_uid: str, spacer) -> int:
    """Studs of ``wall_uid`` standing at a station the spacer covers, tall enough to meet it."""
    axis = 1 if abs(spacer.p1[0] - spacer.p0[0]) < 1e-6 else 0
    s0, s1 = spacer.p0[axis], spacer.p1[axis]
    z_lo0, z_lo1 = spacer.z0_m, spacer.z0_end_m if spacer.z0_end_m is not None else spacer.z0_m
    count = 0
    for stud in members:
        if stud.parent_uid != wall_uid or stud.category not in _STUD_KINDS or stud.p0 != stud.p1:
            continue
        at = stud.p0[axis]
        if not min(s0, s1) <= at <= max(s0, s1):
            continue
        z = z_lo0 + (z_lo1 - z_lo0) * (at - s0) / (s1 - s0)
        if stud.z0_m <= z <= stud.z1_m:
            count += 1
    return count
