"""A sole plate that is a sill: the wider ``FramingSpec.sill_member`` board, and the treated
stock of a wall framed on a pour, whose plate IS the sill return (billed once, as framing)."""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall
from typehaus.resolve.sill_alignment import sill_shift_m
from typehaus.resolve.sill_solids import framed_on_the_pour

_IN = 0.0254
_Z_TOL_M = 0.001


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


def treat_pour_sole_plates(model: ResolvedModel) -> None:
    """A sole plate at a pour sill's z takes the sill's material, unless one is authored."""
    sills: dict[str, list[tuple[float, str]]] = {}
    for ret in model.construction_returns:
        if framed_on_the_pour(model, ret):
            for tag in ret.element_tags[1:]:
                sills.setdefault(tag, []).append((ret.z0_m, ret.material_ref))

    def restocked(m: FramedMember, at: list[tuple[float, str]]) -> FramedMember:
        if (m.category != "plate" or not m.child_key.startswith("plate-bottom")
                or m.material is not None):
            return m
        ref = next((ref for z, ref in at if abs(m.z0_m - z) < _Z_TOL_M), None)
        return replace(m, material=ref) if ref else m

    for i, wall in enumerate(model.walls):
        if wall.tag in sills:
            model.walls[i] = replace(wall, members=tuple(
                restocked(m, sills[wall.tag]) for m in wall.members))
