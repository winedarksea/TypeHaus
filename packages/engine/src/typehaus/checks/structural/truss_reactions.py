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
   (:func:`drift_trusses`) — which is how RF-GARAGE's two southern trusses are held to it.
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
    structural = getattr(ctx.preferences, "structural", None)
    design = getattr(structural, "roof_beam_snow_psf", None)
    if design is None or row.drift_psf:
        return None
    reach = drift_trusses(ctx, roof)
    if reach is None:
        return None
    inside, why = reach
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


#: Two roof footprints this close (ft) across an edge are one drift surface.
_ADJACENT_FT = 0.5


def drift_trusses(ctx: CheckContext, roof) -> tuple[set[str], str] | None:
    """``(truss keys inside the roof-step drift, why)`` for ``roof``, or ``None``.

    A roof whose beams are graded at the authored design snow is drifted WHOLE. A trussed
    roof abutting one is drifted where the drift outruns it: the width
    (``roof_beam_drift_width_ft``) is laid from the drifted roof's FAR edge — conservative,
    the step face is at or beyond it — so the truss lines inside that width carry it too.
    With no width authored the neighbour is held to it whole. Oracle:
    ``notes/north_entry_piers.md`` §3a.
    """
    from typehaus.engineering.registry import records_of

    trusses = [m for m in roof.members if m.category == "roof_truss"]
    records = [r for r in records_of(ctx).values() if r.kind == "roof_beam"]
    if any(roof.tag in r.element_tags for r in records):
        return ({_key(m.child_key) for m in trusses},
                f"the house grades {roof.tag}'s beams at it")
    drifted = {tag for r in records for tag in r.element_tags}
    width = getattr(getattr(ctx.preferences, "structural", None),
                    "roof_beam_drift_width_ft", None)
    for other in sorted(ctx.model.roofs, key=lambda r: r.tag):
        if other.tag not in drifted or other.tag == roof.tag:
            continue
        axis = _abutting(other.footprint, roof.footprint)
        if axis is None:
            continue
        if width is None:
            return ({_key(m.child_key) for m in trusses},
                    f"it abuts the drifted {other.tag} and no roof_beam_drift_width_ft says "
                    f"how far the drift runs")
        (i, sign), ft = axis, 0.3048
        far = min(sign * p[i] for p in other.footprint) / ft
        near = max(sign * p[i] for p in other.footprint) / ft
        limit = far + width
        inside = {_key(m.child_key) for m in trusses
                  if min(sign * m.p0[i], sign * m.p1[i]) / ft <= limit + 1e-6}
        if inside:
            return inside, (f"the {other.tag} drift, {width:g} ft from its far edge "
                            f"(preferences.toml [structural] roof_beam_drift_width_ft), runs "
                            f"{limit - near:.2f} ft past it into {roof.tag}")
    return None


def _abutting(first, second) -> tuple[int, float] | None:
    """``(axis, sign)`` pointing from ``first`` to ``second`` where their plan boxes share an
    edge (within ``_ADJACENT_FT``) and overlap along it, else ``None``."""
    tol = _ADJACENT_FT * 0.3048
    lo1 = [min(p[i] for p in first) for i in (0, 1)]
    hi1 = [max(p[i] for p in first) for i in (0, 1)]
    lo2 = [min(p[i] for p in second) for i in (0, 1)]
    hi2 = [max(p[i] for p in second) for i in (0, 1)]
    for i in (0, 1):
        j = 1 - i
        if min(hi1[j], hi2[j]) - max(lo1[j], lo2[j]) <= tol:
            continue
        if abs(lo2[i] - hi1[i]) <= tol:
            return i, 1.0
        if abs(lo1[i] - hi2[i]) <= tol:
            return i, -1.0
    return None


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
