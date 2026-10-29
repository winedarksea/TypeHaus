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

_CHECK_ID = "integrity.excavation"
_TOL_M = 1e-4


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
    if not out:
        return [passed(_CHECK_ID, f"{len(digs)} excavation(s) state their basis and dig "
                       "only beds")]
    return out
