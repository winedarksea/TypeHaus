"""Opening headers narrower than the stud band sit flush with its sheathing face.

The sheathing then nails to the header and the girt-block screw bites full wood; the
room-side void takes cavity insulation (``sill_alignment.header_shift_m``).
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.model import FramedMember, ResolvedWall
from typehaus.resolve.sill_alignment import header_shift_m


def flush_headers(members: list[FramedMember], rw: ResolvedWall, band_polygon) -> None:
    """Shift each ``header`` member across the wall, in place, onto the sheathing face."""
    (x0, y0), (x1, y1) = rw.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if not band_polygon or run <= 0.0:
        return
    ux, uy = -(y1 - y0) / run, (x1 - x0) / run  # the axis' left normal, as header_shift_m
    for i, m in enumerate(members):
        if m.category != "header":
            continue
        width = m.plan_width_m or plan_cross_section_m(cross_section(m.profile),
                                                       m.z1_m - m.z0_m)
        shift = header_shift_m(rw, band_polygon, width)
        if not shift:
            continue
        nx, ny = ux * shift, uy * shift
        members[i] = replace(m, p0=(m.p0[0] + nx, m.p0[1] + ny),
                             p1=(m.p1[0] + nx, m.p1[1] + ny))
