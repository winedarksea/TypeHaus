"""Grading a header against a published ALLOWABLE LOAD row: plf, not a span for a load case.

A maker's load table is the same read as its span table: a reviewer opens the page, finds the
span and depth, and compares a number. The span is centre to centre of the supports and the
demand is the derived line load (``resolve/header_line_load.py``). The same four outcomes as
``published.graded_against_published``, drift guards included.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory
from typehaus.findings import Finding, Result
from typehaus.model.refs import PublishedSpan

from .published import drift_reason


def graded_against_published_line_load(
    cid: str, subject: str, tags: tuple[str, ...], span_ft: float, published: PublishedSpan,
    member: str | None, demand_plf: float | str, *, bearing_in: float,
    load_basis: str = "",
) -> Finding:
    """``demand_plf`` is the derived load, or the reason there is none."""
    code = published.source
    if isinstance(demand_plf, str):
        return structural_advisory(
            cid, f"{subject}: no line load to read against the published row ({demand_plf})",
            tags, Result.UNKNOWN, code=code,
            fix_hint="make the load derivable, or re-read the header against a load case row")
    drift = drift_reason(published, member, bearing_in=bearing_in)
    if drift is not None:
        return structural_advisory(
            cid, f"{subject}: the authored published row no longer describes this member — "
                 f"{drift}", tags, Result.UNKNOWN, code=code,
            fix_hint="re-read the table at the model's own condition and re-author the "
                     "PublishedSpan")
    capacity = published.capacity_plf
    if span_ft > published.span.feet + 1e-6 or demand_plf > capacity + 1e-6:
        return structural_advisory(
            cid, f"{subject}: {span_ft:.2f}' c-c at {demand_plf:,.0f} plf is past its published "
                 f"row, {capacity:,.0f} plf at {published.span.feet:.2f}' "
                 f"({published.table}; {published.source})",
            tags, Result.FAIL, code=code,
            fix_hint="shorten the span, read a deeper member, or have the header designed")
    return structural_advisory(
        cid, f"{subject} spans {span_ft:.2f}' c-c — a prescriptive read of a published load "
             f"table: {published.table}; {demand_plf:,.0f} plf <= {capacity:,.0f} plf "
             f"(d/c {demand_plf / capacity:.2f}; {load_basis}); bearing {bearing_in:.1f}\" "
             f"on the jacks; conditions the engine does not check: {published.condition} "
             f"({published.source})", tags, Result.PASS, code=code)
