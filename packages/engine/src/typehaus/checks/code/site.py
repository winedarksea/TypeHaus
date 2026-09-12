"""Site setback check (→ Permit-ready plan set Phase 4).

Two rules over one parcel: the setback distances, and whether the ring they are measured
on came from a licensed surveyor at all.

Shapely is already a dependency (checks/advisory, checks/building_science). Distance is
measured from every wall-axis endpoint to the finite parcel-edge segment the setback
applies to — a reasonable approximation near corners without a full offset-polygon solve.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN

# Setbacks are a *local zoning* requirement, not an IRC one — there is no section number to
# cite, and citing one would be a fabrication. "local zoning" is the honest citation, and
# saying so is what lets the coverage test insist every CODE finding carries one.
_SETBACK_REF = "local zoning"


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return passed(cid, msg, tags, code=_SETBACK_REF)


def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return failed(cid, msg, tags, code=_SETBACK_REF)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return unknown(cid, reason, tags, code=_SETBACK_REF)


def _placeholder(cid: str) -> Finding:
    """A declared placeholder ring: FAIL result, WARN severity — red, but not a blocker.

    The verdict stays FAIL because it is true of the set: every lot line, setback and
    coverage figure on C-101 was drawn, not measured, and a reviewer has to see that in
    red rather than have it fold into the UNKNOWN pile.

    The *severity* is WARN, and that is the correction. ERROR is reserved for a hard
    blocker, and the permit checklist already declares this line ``blocking=False``
    (``code/mn_residential/profile.py``, "Certified parcel survey"): the survey is a
    separate submittal by a licensed land surveyor on its own schedule, not a defect in
    the building this engine models. Carrying ERROR anyway made ``--exit-on error`` gate
    on an item the profile had deliberately opened, and misfiled a project state as a
    fault. This is exactly ``_authoring.advisory``'s WARN/FAIL pairing.
    """
    return advisory(cid, "the parcel ring is a PLACEHOLDER, not a survey — lot lines, "
                    "setbacks, lot area and coverage on this set are not measured",
                    (), Result.FAIL, code=_SETBACK_REF)


@check(Tier.CODE, "code.site_setback")
def site_setback(ctx: CheckContext) -> list[Finding]:
    from shapely.geometry import LineString, Point

    site = ctx.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3 or not site.setbacks:
        return [_unknown("code.site_setback", "site setbacks not modeled")]

    out: list[Finding] = []
    n = len(parcel)
    for spec in site.setbacks:
        a, b = parcel[spec.edge % n], parcel[(spec.edge + 1) % n]
        edge = LineString([a, b])
        label = spec.label or f"edge {spec.edge}"
        violations: list[tuple[str, float]] = []
        for wall in ctx.model.walls:
            for point in (wall.axis[0], wall.axis[1]):
                dist = Point(point).distance(edge)
                if dist + 1e-6 < spec.distance.meters:
                    shortfall_in = (spec.distance.meters - dist) / M_PER_IN
                    violations.append((wall.tag, shortfall_in))
        if violations:
            tag, shortfall_in = max(violations, key=lambda item: item[1])
            out.append(_fail(
                "code.site_setback",
                f"wall {tag} is {shortfall_in:.1f}\" short of the {label} setback "
                f"({spec.distance.inches / 12:.0f}')", (tag,),
            ))
        else:
            out.append(_pass(
                "code.site_setback", f"{label} setback ({spec.distance.inches / 12:.0f}') "
                "satisfied by every wall",
            ))
    return out


@check(Tier.CODE, "code.site_parcel_is_surveyed")
def site_parcel_is_surveyed(ctx: CheckContext) -> list[Finding]:
    """Is the parcel ring a certified survey, or a stand-in someone drew?

    Every setback, lot-area and coverage number on the permit set is measured off
    ``Site.parcel``. A reviewer accepts those only from a survey by a licensed land
    surveyor, so the question the drawing has to answer is not "is the ring closed" but
    "who measured it". ``Site.parcel_basis`` is the answer and nothing infers it: a ring
    with no stated basis reads as UNKNOWN, not as a survey, because the failure mode of
    guessing here is a set that silently claims a measurement nobody made.

    Three answers short of a survey, and they are not one answer. ``"placeholder"`` is a
    ring somebody DREW — FAIL, because nothing on it is a measurement. ``"plat"`` is a
    ring somebody STATED off a record but nobody certified — UNKNOWN, because the
    dimensions may well be right and the engine cannot tell. ``None`` is UNKNOWN too, for
    the different reason that nobody has said at all.
    """
    cid = "code.site_parcel_is_surveyed"
    site = ctx.plan.project.site
    basis = site.parcel_basis
    if basis is None:
        return [_unknown(cid, "the parcel states no basis (Site.parcel_basis): the lot "
                         "lines, setbacks and coverage on this set rest on a ring nobody "
                         "has certified")]
    if basis == "placeholder":
        return [_placeholder(cid)]
    if basis == "plat":
        return [_unknown(cid, "the parcel dimensions are STATED but UNCERTIFIED (plat, "
                         "county record or deed): no corner has been located and nobody "
                         "has signed them, so the lot lines, setbacks and coverage on "
                         "this set are only as good as that record — a certified survey "
                         "is still owed")]
    if not site.survey_by:
        return [_unknown(cid, "the parcel is stated as surveyed but names no surveyor "
                         "(Site.survey_by)")]
    dated = f" dated {site.survey_date}" if site.survey_date else ""
    return [_pass(cid, f"parcel per certified survey by {site.survey_by}{dated}")]
