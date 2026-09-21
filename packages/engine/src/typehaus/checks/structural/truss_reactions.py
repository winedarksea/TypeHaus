"""A trussed roof's published reactions, and the chain below the heel graded against them.

The fabricator seals the component and publishes a reaction at every bearing; everything
below the heel is somebody else's. ``Roof.published_reactions`` quotes those rows into the
model, and this check does two things with them:

1. **Refuses a row that does not describe this roof** — the ``published._capacity_drift``
   guards (member, spacing, wind basis) plus a SNOW guard: the row's ground snow must reach
   the site's, and a roof the house designs for a drift must carry a row that states one. A
   quote priced on the bare ground snow buys ordinary trusses under a roof-step drift, and
   this guard is what stops that reading as a PASS.
2. **Grades the first link below** — the heel connector's published allowable against the
   row's uplift, through ``published.graded_against_published_capacity``.

Its own check id, never ``structural.uplift_capacity``'s: a permit line folds by id, and two
subjects sharing one sent a blocking line red on the other's findings (``profile.py``,
2026-09-20). Nothing here is an ``engineering_item``: the component design stays
``rafter/<roof>`` until a real sealed submittal is recorded in ``engineering.toml``.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable, structural_advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.published import (
    _capacity_drift,
    graded_against_published_capacity,
)
from typehaus.findings import Finding, Result

CID = "structural.truss_reactions"


@check(Tier.STRUCTURAL, CID)
def truss_reactions(ctx: CheckContext) -> list[Finding]:
    roofs = [roof for roof in sorted(ctx.model.roofs, key=lambda r: r.tag)
             if not any(m.category == "rafter" for m in roof.members)]
    if not roofs:
        return [not_applicable(CID, "every roof in this plan resolves rafter members, so no "
                                    "fabricator publishes a reaction for any of them", ())]
    out: list[Finding] = []
    for roof in roofs:
        element = ctx.plan.by_tag(roof.tag)
        rows = tuple(getattr(element, "published_reactions", ()) or ())
        if not rows:
            out.append(structural_advisory(
                CID, f"{roof.tag} is trussed and no published reaction is authored for it, "
                     f"so the uplift chain below its heels has no demand to be graded at",
                (roof.tag,), Result.UNKNOWN,
                fix_hint=f"author Roof.published_reactions on {roof.tag} from the truss "
                         f"fabricator's SEALED reaction schedule — one row per bearing, "
                         f"with the ground snow, drift and wind basis it was run at"))
            continue
        out.extend(_row_findings(ctx, roof, row) for row in rows)
    return out


def _row_findings(ctx: CheckContext, roof, row) -> Finding:
    subject = f"{roof.tag} bearing '{row.table}'"
    reason = _reaction_drift(ctx, roof, row)
    if reason is not None:
        return structural_advisory(
            CID, f"{subject}: the published reaction no longer describes this roof — "
                 f"{reason}", (roof.tag,), Result.UNKNOWN,
            fix_hint="have the fabricator re-run the design at the model's own loads and "
                     "re-author Roof.published_reactions")
    return graded_against_published_capacity(
        CID, f"{subject} (the heel connector under a {row.uplift_lb:,.0f} lb published "
             f"reaction, {row.source})",
        (roof.tag,), row.uplift_lb, row.connector,
        row.connector.member if row.connector is not None else None,
        fix=f"author PublishedReaction.connector on {roof.tag}: the heel connector's own "
            f"published uplift allowable")


def _reaction_drift(ctx: CheckContext, roof, row) -> str | None:
    """What stops a reaction row from describing this roof, or ``None``."""
    from typehaus.checks.structural.snow import _spacing_in

    site = ctx.plan.project.site
    trusses = [m for m in roof.members if m.category == "roof_truss"]
    spacing_in = round(_spacing_in(roof, trusses), 1) if len(trusses) > 1 else None
    # `_capacity_drift` is the PublishedCapacity guard set; a reaction carries the same
    # member / spacing / wind fields, and its demand guard is not used (the row IS the demand).
    if site.design_wind_speed_mph is not None and row.wind_speed_mph is None:
        return (f"the site declares {site.design_wind_speed_mph:g} mph and the row states no "
                f"wind basis, so the uplift it publishes is unverified")
    as_capacity = _RowView(row)
    drift = _capacity_drift(as_capacity, None, spacing_in, site.design_wind_speed_mph,
                            site.wind_exposure, 0.0)
    if drift is not None:
        return drift
    ground = site.ground_snow_load_psf
    if ground is not None:
        if row.ground_snow_psf is None:
            return (f"the site declares {ground:g} psf ground snow and the row states no "
                    f"ground snow, so the load it was run at is unverified")
        if row.ground_snow_psf + 0.01 < ground:
            return (f"the row was run at {row.ground_snow_psf:g} psf ground snow and the site "
                    f"declares {ground:g} psf")
    design = getattr(getattr(ctx.preferences, "structural", None), "roof_beam_snow_psf", None)
    if design is not None and _designed_for_drift(ctx, roof) and not row.drift_psf:
        return (f"the house designs {roof.tag} for a drifted {design:g} psf "
                f"(preferences.toml [structural] roof_beam_snow_psf) and the row states no "
                f"drift surcharge — a quote on ground snow alone prices ordinary trusses")
    return None


def _designed_for_drift(ctx: CheckContext, roof) -> bool:
    """A roof whose beams this house grades at its authored (drifted) design snow."""
    from typehaus.engineering.registry import records_of

    return any(record.kind == "roof_beam" and roof.tag in record.element_tags
               for record in records_of(ctx).values())


class _RowView:
    """A reaction row read through the ``PublishedCapacity`` guard's field names."""

    def __init__(self, row) -> None:
        self.member = row.member
        self.spacing = row.spacing
        self.wind_speed_mph = row.wind_speed_mph
        self.exposure = row.exposure
        self.demand_lb = None
