"""A trussed roof's published reactions, and the chain below the heel graded against them.

The fabricator seals the component and publishes a reaction at every bearing; everything
below the heel is somebody else's. ``Roof.published_reactions`` quotes those rows into the
model, and this check does two things with them:

1. **Refuses a row that does not describe this roof** — the ``published._capacity_drift``
   guards (member, spacing, wind basis) plus a SNOW guard: the row's ground snow must reach
   the site's, and a DRIFT TRUSS must carry a row that states one. A quote priced on the
   bare ground snow buys ordinary trusses under a roof-step drift, and this guard is what
   stops that reading as a PASS. Every truss of a roof whose beams are graded at the drift
   is one; so is every truss of an abutting roof that the drift width reaches
   (``engineering/snow_drift.drift_reach``) — which is how RF-GARAGE's two southern
   trusses are held to it.
2. **Grades the first link below** — the heel connector's published allowable against the
   row's uplift, through ``published.graded_against_published_capacity``.

**Two statuses per roof (decision 20).** ``Roof.specified_reactions`` are the criteria the
truss ORDER states. *Supporting structure closed*: the heel connector named on each is graded
against its specified uplift now, from the catalog. *Component confirmed*: the supplier's
published rows must stay within the specified ones; until a row is authored it is an UNKNOWN
that says so, the one thing left open once the supporting structure closes.

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
from typehaus.engineering.registry import records_of
from typehaus.engineering.snow_drift import drift_reach
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
        specified = tuple(getattr(element, "specified_reactions", ()) or ())
        out.extend(_specified_finding(roof, row) for row in specified)
        if not rows:
            out.append(_awaiting(roof, specified))
            continue
        out.extend(_row_findings(ctx, roof, row) for row in rows)
        out.extend(_within_specified(roof, row, specified) for row in rows if specified)
    return out


def _awaiting(roof, specified: tuple) -> Finding:
    if specified:
        return structural_advisory(
            CID, f"{roof.tag} component NOT YET CONFIRMED: the supplier's reaction schedule is "
                 f"not supplied. The supporting structure is graded on the specified reactions "
                 f"({_summary(specified)}); the supplier's design must stay within them and "
                 f"state its snow, drift and wind basis",
            (roof.tag,), Result.UNKNOWN,
            fix_hint=f"author Roof.published_reactions on {roof.tag} from the truss "
                     f"fabricator's SEALED reaction schedule, one row per bearing")
    return structural_advisory(
        CID, f"{roof.tag} is trussed and no published reaction is authored for it, "
             f"so the uplift chain below its heels has no demand to be graded at",
        (roof.tag,), Result.UNKNOWN,
        fix_hint=f"author Roof.published_reactions on {roof.tag} from the truss "
                 f"fabricator's SEALED reaction schedule — one row per bearing, "
                 f"with the ground snow, drift and wind basis it was run at")


def _summary(specified: tuple) -> str:
    return "; ".join(f"{row.member} on {row.bearing}: {row.uplift_lb:,.0f} lb uplift"
                     for row in specified)


def _specified_finding(roof, row) -> Finding:
    """The heel connector against the specified uplift — supporting structure closed."""
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.model.refs import PublishedCapacity

    allowable = allowable_for_model(row.connector or "")
    capacity = getattr(allowable, "uplift_lb", None)
    subject = (f"{roof.tag} supporting structure, {row.member} on {row.bearing}: the "
               f"{row.connector} heel tie under the specified {row.uplift_lb:,.0f} lb "
               f"({row.basis})")
    if allowable is None or not capacity:
        return structural_advisory(
            CID, f"{subject} has no published uplift in the hardware catalog", (roof.tag,),
            Result.UNKNOWN, fix_hint="name a heel connector the catalog holds an allowable for")
    published = PublishedCapacity(
        source=allowable.citation.split(":")[0], table=f"{row.connector} uplift (160)",
        member=row.connector, capacity_lb=float(capacity),
        condition=f"{allowable.species}; fasteners {allowable.fasteners}")
    return graded_against_published_capacity(
        CID, subject, (roof.tag,), row.uplift_lb, published, row.connector,
        fix=f"respec the heel connector on {roof.tag} or lower the specified reaction")


def _within_specified(roof, row, specified: tuple) -> Finding:
    """A supplier's row against the order's: component confirmed, or over what was specified."""
    mine = [s for s in specified if s.member in ("*", row.member) or s.member.lower()
            == (row.member or "").lower()]
    limit = max((s.uplift_lb for s in mine), default=None)
    subject = f"{roof.tag} bearing '{row.table}' (the supplier's {row.uplift_lb:,.0f} lb uplift)"
    if limit is None:
        return structural_advisory(CID, f"{subject} names no truss the order specifies",
                                   (roof.tag,), Result.UNKNOWN)
    if row.uplift_lb > limit + 0.5:
        return structural_advisory(
            CID, f"{subject} is over the {limit:,.0f} lb the order specifies — the supporting "
                 f"structure was closed on the specified number", (roof.tag,), Result.FAIL,
            fix_hint="have the supplier re-run to the specified reactions, or re-grade the "
                     "chain below the heel at the supplier's")
    return structural_advisory(
        CID, f"{subject}: component confirmed, within the {limit:,.0f} lb specified",
        (roof.tag,), Result.PASS)


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
    structural = getattr(ctx.preferences, "structural", None)
    design = getattr(structural, "roof_beam_snow_psf", None)
    if design is None or row.drift_psf:
        return None
    reach = drift_reach(ctx.model, ctx.preferences, records_of(ctx), roof)
    if reach is None:
        return None
    inside, why = reach.trusses, reach.why
    trusses = {_key(m.child_key) for m in roof.members if m.category == "roof_truss"}
    member = _key(row.member)
    if inside == trusses:
        return (f"every truss of {roof.tag} carries the {design:g} psf drift case "
                f"(preferences.toml [structural] roof_beam_snow_psf) — {why} — and the row "
                f"states no drift surcharge: a quote on ground snow alone prices ordinary "
                f"trusses")
    if member in trusses and member not in inside:
        return None
    named = ("it is for " + row.member if member in inside
             else f"it names no model truss ('{row.member}')")
    return (f"{', '.join(sorted(inside))} of {roof.tag} are drift trusses — {why} — and the "
            f"row states no drift surcharge while {named}; name the truss it covers, or have "
            f"the fabricator quote the drift")


def _key(name: str | None) -> str:
    return (name or "").strip().lower()


class _RowView:
    """A reaction row read through the ``PublishedCapacity`` guard's field names."""

    def __init__(self, row) -> None:
        self.member = row.member
        self.spacing = row.spacing
        self.wind_speed_mph = row.wind_speed_mph
        self.exposure = row.exposure
        self.demand_lb = None
