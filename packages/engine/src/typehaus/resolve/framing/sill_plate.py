"""The sole plate of a wall with ``FramingSpec.sill_member``: the wider sill board."""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.model import FramedMember, ResolvedWall
from typehaus.resolve.sill_alignment import sill_shift_m

_IN = 0.0254


def sill_width_m(spec) -> float | None:
    member = getattr(spec, "sill_member", None)
    return member_actual(member)[1] * _IN if member else None


def widen_sole_plate(members: list[FramedMember], rw: ResolvedWall, spec,
                     band_polygon) -> None:
    """Re-stock ``plate-bottom*`` as the sill member, flush with the band's outside face."""
    width = sill_width_m(spec)
    if width is None or not band_polygon:
        return
    shift = sill_shift_m(rw, band_polygon, width)
    (x0, y0), (x1, y1) = rw.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    nx, ny = -(y1 - y0) / run * shift, (x1 - x0) / run * shift
    for i, m in enumerate(members):
        if m.category == "plate" and m.child_key.startswith("plate-bottom"):
            members[i] = replace(
                m, profile=spec.sill_member,
                p0=(m.p0[0] + nx, m.p0[1] + ny), p1=(m.p1[0] + nx, m.p1[1] + ny))
