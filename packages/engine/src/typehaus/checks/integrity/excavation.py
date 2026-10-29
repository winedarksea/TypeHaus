"""An ``Excavation`` states its soil basis, digs only beds, and caps where its columns stop.

Slope, swell and shrink all rest on a soil nobody has tested yet; a blank basis or source
would let a presumed number read as a measured one. A cap thinner or thicker than the gap a
column leaves under grade leaves the stone open to surface water, or buries it; a column
authored by ``height`` is held to the same line off its resolved top.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.excavation import Excavation
from typehaus.model.structure import FootingBedding
from typehaus.resolve.excavation import top_of_cut

_CHECK_ID = "integrity.excavation"
_TOL_M = 1e-4
_FT = 0.3048


def _inch(length) -> str:
    return f'{length.meters / 0.0254:g}"'


@check(Tier.INTEGRITY, _CHECK_ID)
def excavation_is_well_formed(ctx: CheckContext) -> list[Finding]:
    digs = [el for el in ctx.plan.all_elements() if isinstance(el, Excavation)]
    if not digs:
        return [not_applicable(_CHECK_ID, "no Excavation is authored")]
    columns = {c.bed_tag: c for c in ctx.model.wall_columns}
    out: list[Finding] = []
    for dig in digs:
        tags = (dig.tag,)
        for name, text in (("side_slope.basis", dig.side_slope.basis),
                           ("swell.source", dig.swell.source),
                           ("shrink.source", dig.shrink.source)):
            if not text.strip():
                out.append(failed(_CHECK_ID, f"{dig.tag} {name} is blank", tags=tags,
                                  fix=f"say what {name.split('.')[0]} rests on"))
        for host in dig.hosts:
            bed = ctx.plan.by_tag(host)
            if not isinstance(bed, FootingBedding):
                out.append(failed(_CHECK_ID, f"{dig.tag} hosts {host!r}, which is not a "
                                  "FootingBedding", tags=tags))
                continue
            column = bed.wall_column
            if column is not None and column.cap_below_grade is not None and abs(
                    column.cap_below_grade.meters - dig.cap_thickness.meters) > _TOL_M:
                out.append(failed(
                    _CHECK_ID, f"{dig.tag}'s {_inch(dig.cap_thickness)} cap does not meet "
                    f"{host}'s column, which stops {_inch(column.cap_below_grade)} under grade",
                    tags=(dig.tag, host)))
            resolved = columns.get(host)
            if resolved is not None and (
                    resolved.top_m > resolved.grade_m - dig.cap_thickness.meters + _TOL_M):
                rise = (resolved.top_m - resolved.grade_m + dig.cap_thickness.meters) / 0.0254
                out.append(failed(
                    _CHECK_ID, f"{host}'s drain column rises {rise:.1f}\" into "
                    f"{dig.tag}'s {_inch(dig.cap_thickness)} cap", tags=(dig.tag, host),
                    fix="stop the column at the cap's underside (cap_below_grade)"))
        out.extend(_past_the_lot(ctx, dig))
    if not out:
        return [passed(_CHECK_ID, f"{len(digs)} excavation(s) state their basis and dig "
                       "only beds")]
    return out


def _past_the_lot(ctx: CheckContext, dig: Excavation) -> list[Finding]:
    from shapely.geometry import Point, Polygon

    ring = [p.xy_m for p in ctx.plan.project.site.parcel]
    lip = top_of_cut(ctx.model, dig) if len(ring) >= 3 else None
    if lip is None:
        return []
    parcel = Polygon(ring)
    if lip.difference(parcel).area < 0.01:
        return []
    past = max(parcel.exterior.distance(Point(p)) for g in getattr(lip, "geoms", [lip])
               for p in g.exterior.coords if not parcel.contains(Point(p)))
    return [failed(_CHECK_ID, f"{dig.tag}'s cut reaches {past / _FT:.1f}' past the lot line",
                   tags=(dig.tag,), fix="steepen the presumed cut, stand a vertical toe, "
                   "shore the face, or secure a temporary construction easement")]
