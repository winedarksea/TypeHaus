"""Grading a span against a published manufacturer table — the prescriptive read.

**Why this is a check and not an engineering item.** A published table is a document a
reviewer opens: they find the row, confirm the conditions, and the question is closed. That
is the same act as reading IRC Table R602.7(1), and it is not something a professional seal
adds anything to. The cladding set the precedent — PBR stays out of the engineering register
because three manufacturers publish a wall span table for it — and this module generalises
it: a ``PublishedSpan`` authored on the element turns what used to be an UNKNOWN waiting for
a seal into a PASS a reviewer can check.

``checks/_authoring.engineered()`` stays for what no table publishes.

**The refusals are the substance.** A quoted row is true for the row, not for the building
forever, so four things are compared before the span is:

* the **member** the row is for, against the member the model now has;
* the **spacing** the row is indexed by, where it has one;
* the **carried span** the row is indexed by, where it has one;
* the row's own **load basis**, against the demand this check computed.

Any mismatch is UNKNOWN naming it — never a PASS off a stale quotation, and never a FAIL,
because a row that does not describe this building is silent about it rather than damning.
And a house that authors nothing gets UNKNOWN with the authoring hint, which is what
``engineered()``'s NO_CALC used to provide.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory
from typehaus.findings import Finding, Result
from typehaus.model.refs import PublishedCapacity, PublishedSpan

#: How far a span may exceed the published row before it is a FAIL, in feet. Zero — a table
#: is a maximum and the whole value of reading one is that it does not get rounded.
_TOLERANCE_FT = 1e-6
#: The same zero, in pounds. A published allowable is a maximum and the whole value of
#: reading one is that it does not get rounded; this exists only to keep float noise out of
#: an equality.
_CAPACITY_TOLERANCE_LB = 1e-6


def graded_against_published(
    cid: str,
    subject: str,
    tags: tuple[str, ...],
    span_ft: float,
    published: PublishedSpan | None,
    member: str | None,
    *,
    spacing_in: float | None = None,
    carried_span_ft: float | None = None,
    demand_psf: float | None = None,
    fix: str | None = None,
) -> Finding:
    """One member, graded against the row authored on it. Always returns exactly one finding."""
    if published is None:
        return structural_advisory(
            cid, f"{subject} spans {span_ft:.1f}' and no published table row is authored "
                 f"for it", tags, Result.UNKNOWN,
            fix_hint=fix or "author a PublishedSpan naming the document, the row read, the "
                            "member it is for and the conditions it assumes")

    drift = _drift(published, member, spacing_in, carried_span_ft, demand_psf)
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored published row no longer describes this "
                 f"member — {drift}", tags, Result.UNKNOWN,
            fix_hint="re-read the table at the model's own condition and re-author the "
                     "PublishedSpan, or delegate the member to an engineered design")

    allowable_ft = published.span.feet
    if span_ft > allowable_ft + _TOLERANCE_FT:
        return structural_advisory(
            cid, f"{subject} spans {span_ft:.2f}', past the {allowable_ft:.2f}' its own "
                 f"published row allows ({published.table}; {published.source})",
            tags, Result.FAIL, code=published.source,
            fix_hint="shorten the span, read a heavier row, or have the member designed")

    return structural_advisory(
        cid, f"{subject} spans {span_ft:.2f}' — a prescriptive read of a published table: "
             f"{published.table}; {span_ft:.2f}' <= {allowable_ft:.2f}'; conditions the "
             f"engine does not check: {published.condition} ({published.source})",
        tags, Result.PASS, code=published.source)


def graded_against_published_capacity(
    cid: str,
    subject: str,
    tags: tuple[str, ...],
    demand_lb: float,
    published: PublishedCapacity | None,
    member: str | None,
    *,
    spacing_in: float | None = None,
    wind_speed_mph: float | None = None,
    exposure: str | None = None,
    fix: str | None = None,
) -> Finding:
    """One uplift joint, graded against the row authored on it. Always exactly one finding.

    The same four outcomes as :func:`graded_against_published`, in the same order and for the
    same reasons — nothing authored is UNKNOWN with the hint, a row that has drifted is
    UNKNOWN naming the drift, an exceeded row is a FAIL, and a covered one is a PASS quoting
    the conditions the engine does not check.

    **What is deliberately absent is an ``engineering_item``, and that absence is the whole
    mechanism.** This function is what takes a roof's uplift capacity out of the seal register:
    a demand this engine computes, against an allowable a reviewer can look up, is a
    prescriptive read and not something a stamp adds to. ``_authoring.engineered()`` remains
    for what no table publishes.

    ** THE COMPARISON IS DEMAND vs CAPACITY, NOT SPAN vs SPAN, AND THE FAIL IS REAL. ** A
    roof whose computed uplift exceeds the part somebody quoted gets a FAIL naming both
    numbers. That is the check working: an under-sized tie is a finding, not a reason to stop
    reading the table.
    """
    if published is None:
        return structural_advisory(
            cid, f"{subject} takes {demand_lb:,.0f} lb of uplift and no published capacity "
                 f"is authored for it", tags, Result.UNKNOWN,
            fix_hint=fix or "author a PublishedCapacity naming the document, the row read, "
                            "the part it is for and the conditions it assumes")

    drift = _capacity_drift(published, member, spacing_in, wind_speed_mph, exposure, demand_lb)
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored published row no longer describes this joint — "
                 f"{drift}", tags, Result.UNKNOWN,
            fix_hint="re-read the table at the model's own condition and re-author the "
                     "PublishedCapacity, or delegate the joint to an engineered design")

    if demand_lb > published.capacity_lb + _CAPACITY_TOLERANCE_LB:
        return structural_advisory(
            cid, f"{subject} takes {demand_lb:,.0f} lb of uplift, past the "
                 f"{published.capacity_lb:,.0f} lb its own published row allows "
                 f"({published.table}; {published.source})",
            tags, Result.FAIL, code=published.source,
            fix_hint="upsize the connector, read a heavier row, or have the joint designed")

    return structural_advisory(
        cid, f"{subject} takes {demand_lb:,.0f} lb of uplift — a prescriptive read of a "
             f"published table: {published.table}; {demand_lb:,.0f} lb <= "
             f"{published.capacity_lb:,.0f} lb; conditions the engine does not check: "
             f"{published.condition} ({published.source})",
        tags, Result.PASS, code=published.source)


def _capacity_drift(published: PublishedCapacity, member: str | None,
                    spacing_in: float | None, wind_speed_mph: float | None,
                    exposure: str | None, demand_lb: float) -> str | None:
    """What stops this row from describing the joint, or ``None`` when nothing does."""
    if member is not None and _normalise(member) != _normalise(published.member):
        return f"the row is for {published.member!r} and the model now has {member!r}"
    if (spacing_in is not None and published.spacing is not None
            and abs(spacing_in - published.spacing.inches) > 0.01):
        return (f"the row is indexed at {published.spacing.inches:g}\" o.c. and the model is "
                f"framed at {spacing_in:g}\"")
    # ** INCREASE-ONLY, on the same reasoning as a carried span. ** A required force read at
    # 115 mph covers a building the site later derates to 105; the reverse is the error. The
    # exposure is not ordered that way and cannot be — B, C and D are categories, not a
    # ladder this check may walk — so ANY change to it drifts.
    if (wind_speed_mph is not None and published.wind_speed_mph is not None
            and wind_speed_mph > published.wind_speed_mph + 0.01):
        return (f"the row was read at {published.wind_speed_mph:g} mph and the site now "
                f"declares {wind_speed_mph:g} mph")
    if (exposure is not None and published.exposure is not None
            and str(exposure).strip().upper() != str(published.exposure).strip().upper()):
        return (f"the row was read at Exposure {published.exposure} and the site now "
                f"declares Exposure {exposure}")
    if published.demand_lb is not None and demand_lb > published.demand_lb + 0.01:
        return (f"the row was judged against {published.demand_lb:,.0f} lb and this check "
                f"computes {demand_lb:,.0f} lb")
    return None


def _drift(published: PublishedSpan, member: str | None, spacing_in: float | None,
           carried_span_ft: float | None, demand_psf: float | None) -> str | None:
    """What stops this row from describing the model, or ``None`` when nothing does."""
    if member is not None and _normalise(member) != _normalise(published.member):
        return (f"the row is for {published.member!r} and the model now has "
                f"{member!r}")
    if (spacing_in is not None and published.spacing is not None
            and abs(spacing_in - published.spacing.inches) > 0.01):
        return (f"the row is indexed at {published.spacing.inches:g}\" o.c. and the "
                f"model is framed at {spacing_in:g}\"")
    # Only an INCREASE drifts. A row read at a 10' joist span covers a beam picking up 7'
    # of joist; reading it the other way round would be the error.
    if (carried_span_ft is not None and published.carried_span is not None
            and carried_span_ft > published.carried_span.feet + 0.01):
        return (f"the row is indexed at a {published.carried_span.feet:g}' carried "
                f"span and this member picks up {carried_span_ft:.2f}'")
    if (demand_psf is not None and published.load_psf is not None
            and demand_psf > published.load_psf + 0.01):
        return (f"the row is published at {published.load_psf:g} psf and this check "
                f"computes {demand_psf:.1f} psf")
    return None


def _normalise(member: str) -> str:
    """Member spellings differ in punctuation and case, never in substance.

    ``'2-ply 14" LVL'`` and ``'2-PLY 14" LVL'`` are the same member; ``'2-ply 14" LVL'`` and
    ``'11.875 TJI 230'`` are not, and no normalisation should make them look alike.
    """
    return "".join(ch for ch in member.lower() if ch.isalnum())
