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
from typehaus.model.refs import PublishedSpan

#: How far a span may exceed the published row before it is a FAIL, in feet. Zero — a table
#: is a maximum and the whole value of reading one is that it does not get rounded.
_TOLERANCE_FT = 1e-6


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
