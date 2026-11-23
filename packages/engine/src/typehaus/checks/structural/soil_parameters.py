"""Specified soil parameters against the site report that must confirm them.

A retaining court can be designed on ``Site.specified_soil`` — values a site report must
confirm — the way a roof is closed on trusses its fabricator has yet to seal. Two statuses:
the design is closed on the specified values (the engineering record grades them), and the
parameters are CONFIRMED only once ``Site.confirmed_soil`` holds the report's values. Until
then this is UNKNOWN, never FAIL; a confirmed value below the specified one FAILs here and
the records, which grade on the confirmed values, go OVER with it.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable, structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

CID = "structural.soil_parameters_confirmed"


@check(Tier.STRUCTURAL, CID)
def soil_parameters_confirmed(ctx: CheckContext) -> list[Finding]:
    site = ctx.plan.project.site
    spec = getattr(site, "specified_soil", None)
    if spec is None:
        return [not_applicable(CID, "no design here is closed on specified soil parameters",
                               ())]
    got = getattr(site, "confirmed_soil", None)
    asked = (f"bed friction >= {spec.bed_friction:.2f} and native phi' >= "
             f"{spec.native_phi_deg:g} deg ({spec.source or 'the drawing note'})")
    if got is None:
        return [structural_advisory(
            CID, f"design closed on specified soil parameters — {asked}; NOT YET CONFIRMED: "
                 f"no site report is entered", (), Result.UNKNOWN,
            fix_hint=f"commission the report ({spec.report_scope or 'see the note'}) and "
                     f"author Site.confirmed_soil from it")]
    short = [f"{name} {have:g} < {want:g}" for name, have, want in (
        ("bed friction", got.bed_friction, spec.bed_friction),
        ("native phi'", got.native_phi_deg, spec.native_phi_deg)) if have < want]
    if short:
        return [structural_advisory(
            CID, f"the site report ({got.source}) is short of the specified soil parameters: "
                 + "; ".join(short), (), Result.FAIL,
            fix_hint="build the printed fallback and return the short rows to the owner")]
    return [structural_advisory(
        CID, f"soil parameters confirmed by {got.source}: {asked}", (), Result.PASS)]
