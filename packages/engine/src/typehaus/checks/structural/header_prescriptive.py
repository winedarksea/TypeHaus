"""``structural.header_prescriptive`` — a wall header graded against the beam maker's own table.

Past 8' the IRC's table stops and something else has to answer. Until 2026-09-11 that was
always an engineering item, which was right for a one-off beam and wrong for the ordinary
case: an LVL over a garage door is a row in the supplier's own header table, and reading it
is a prescriptive act. An authored ``Door.published_span`` is that read;
``checks/structural/published.py`` grades against it and refuses the row when the model
drifts away from what it was read at. A house that authors neither the row nor the beam
gets UNKNOWN with the hint.

Within 8' R602.7 answers, so an opening there is graded only when it opts out of the table
by authoring BOTH an LVL ``header_spec`` and the ``published_span`` that sizes it.

Either way the read is graded on the header's whole clear span (a pocket's cavity
included), and refused while ``resolve/header_loads.py`` finds a point load inside it:
header guides are uniform load only.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

from .header_spans import published_read
from .published import graded_against_published

_CID = "structural.header_prescriptive"
_PRESCRIPTIVE_SPAN_M = 8.0 * 0.3048


@check(Tier.STRUCTURAL, _CID)
def header_within_prescriptive(ctx: CheckContext) -> list[Finding]:
    """Grade an authored header-table read, and flag a header past R602.7 with none."""
    from typehaus.resolve.framing.tables import flat_header_member, header_profile_from_spec
    from typehaus.resolve.header_loads import LoadIndex

    out: list[Finding] = []
    index = None
    for op in ctx.model.openings:
        source = ctx.plan.by_tag(op.tag) if ctx.plan is not None else None
        spec = getattr(source, "header_spec", None)
        published = getattr(source, "published_span", None)
        wide = op.width_m > _PRESCRIPTIVE_SPAN_M
        if not wide:
            if (spec is None or published is None or flat_header_member(spec) is not None
                    or header_profile_from_spec(spec) is None):
                continue
        else:
            if spec is None and source is not None:
                type_ref = getattr(source, "type_ref", None)
                door_type = ctx.plan.by_tag(type_ref) if type_ref else None
                spec = getattr(door_type, "header_spec", None)
            if spec is None:
                out.append(_advisory(
                    _CID, f"opening {op.tag} is {op.width_m * 3.281:.1f}' wide, past IRC "
                    f"R602.7's table, and no header is authored for it", (op.tag,),
                    Result.UNKNOWN, code="IRC R602.7",
                    fix_hint="author Door.header_spec (or DoorType.header_spec) with the "
                             "beam, and Door.published_span with the table row that sizes it"))
                continue
        span_ft = op.width_m / 0.3048
        if ctx.plan is not None:
            index = index or LoadIndex.of(ctx.plan, ctx.model)
            span_ft, points = published_read(ctx, op, index)
            if points and published is not None:
                out.append(_advisory(
                    _CID, f"opening {op.tag}, headed with {spec}: the published row is "
                    f"uniform load only and point load(s) {', '.join(points)} bear inside "
                    f"its {span_ft:.2f}' span", (op.tag,), Result.UNKNOWN,
                    code=published.source,
                    fix_hint="move the opening so the point lands on its jamb pack, or "
                             "carry the header as an engineered item"))
                continue
        out.append(graded_against_published(
            _CID, f"opening {op.tag}, headed with {spec}", (op.tag,), span_ft, published,
            spec,
            # ** THE LOAD BASIS THE ROW IS INDEXED AT HAS TO BE ANSWERED, AND THIS CHECK
            # CANNOT TELL ROOF FROM FLOOR. ** So it answers with the LARGER of the two
            # (`loads.WIDE_HEADER_LOAD_PSF`), the safe direction on an allowable, and with
            # NOTHING where the site's ground snow is not the 50 psf those figures are
            # derived at: an unverified guard is UNKNOWN, not a silent PASS (2026-09-18).
            demand_psf=_wide_header_demand_psf(ctx),
            fix=("author Door.published_span with the manufacturer's header-table row "
                 "that sizes this beam, or leave the opening to an engineered design") if wide
            else ("re-read the manufacturer's header-table row at the model's own "
                  "condition, or drop header_spec and let R602.7 size the header")))
    return out


def _wide_header_demand_psf(ctx: CheckContext) -> float | None:
    """The uniform load a header read is compared against, or ``None`` off this site.

    ``loads.ROOF_SNOW_PSF`` is ``0.7 Ce Ct Is Pg`` stated at Pg = 50 and derived nowhere in
    this engine, so a site at any other ground snow gets no demand rather than a wrong one —
    the same refusal ``checks/structural/snow.py`` makes for its own table.
    """
    from typehaus.loads import DERIVED_AT_GROUND_SNOW_PSF, WIDE_HEADER_LOAD_PSF

    site = getattr(ctx.plan.project, "site", None) if ctx.plan is not None else None
    ground = getattr(site, "ground_snow_load_psf", None)
    if ground is None or abs(float(ground) - DERIVED_AT_GROUND_SNOW_PSF) > 1e-6:
        return None
    return WIDE_HEADER_LOAD_PSF
