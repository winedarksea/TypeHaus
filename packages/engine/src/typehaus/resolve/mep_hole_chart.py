"""The published ALLOWABLE HOLES chart, read — the grading half of ``header_bore``.

No IRC section publishes a bore limit for a header (``mep_bores.header_bore`` says so at
length), so the only thing that turns that UNKNOWN into a verdict is the maker's own chart,
authored as a ``PublishedHole`` on the opening. This module is where such a row is compared
against a real hole: the drift guards that say whether the row describes THIS member, and
the zone arithmetic that says whether the hole is where the chart allows one.

It lives in ``resolve`` and not in ``checks`` for the module's own reason: a check that
graded a different limit from the one the router plans against makes the loop impossible to
close. ``houses/catlin/notes/framing_bore_limits.md`` §8 is the hand-worked oracle.
"""

from __future__ import annotations

from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_bores import BoreVerdict


def hole_chart_drift(chart: Any, profile: str, *, span_in: float | None = None,
                     plies: int | None = None) -> str | None:
    """Why ``chart`` does not describe THIS member, or ``None`` when it does.

    The ``published._drift`` discipline, lifted into ``resolve`` so the router and the check
    read one rule and neither imports ``checks``. A quoted allowable is only true for the row
    it was read at: retype the header and the chart stops being about this building, and the
    verdict must go UNKNOWN naming the mismatch rather than keep printing a PASS.

    An authored guard the caller cannot answer is a MISMATCH, not agreement — the same trap
    ``PublishedSpan`` names: a row stating a span nobody passed used to be indistinguishable
    from a row that matched.
    """
    if _normalise_member(chart.member) != _normalise_member(profile):
        return (f"the chart was read for {chart.member!r} and this header resolves as "
                f"{profile!r}")
    if chart.plies is not None:
        if plies is None:
            return f"the chart is for a {chart.plies}-ply member and nothing states the plies"
        if plies != chart.plies:
            return (f"the chart is for a {chart.plies}-ply member and this header is "
                    f"{plies}-ply")
    if chart.span is not None:
        row_in = chart.span.meters / M_PER_IN
        if span_in is None:
            return (f'the chart was read at a {row_in:.2f}" span and this crossing passed '
                    "no span")
        if span_in > row_in + 1e-6:
            return (f'the chart was read at a {row_in:.2f}" span and this header spans '
                    f'{span_in:.2f}"')
    return None


def _normalise_member(member: str) -> str:
    return "".join(ch for ch in member.lower() if ch.isalnum())


def chart_verdict(chart: Any, profile: str, depth_in: float, cut_in: float,
                  diameter_in: float, notch: bool, *,
                  from_bearing_in: float | None, span_in: float | None,
                  edge_clear_in: float | None, nearest_cut_in: float | None,
                  nearest_diameter_in: float | None = None) -> BoreVerdict:
    """Grade one hole against an authored ``PublishedHole`` row. Four outcomes, no fifth.

    A chart is a SHAPE as much as a number: a legal-diameter hole three inches off a bearing
    is the one hole no chart on the market allows, so the zone is graded beside the size.
    """
    row = f"{chart.source} — {chart.table}"
    tail = f" [{row}]" + (f" Conditions: {chart.condition}" if chart.condition else "")
    remedy = ("route the run clear of the header, or have the header's designer state an "
              "allowable this chart does not publish")

    if notch and chart.round_holes_only:
        return BoreVerdict(
            False, "notch", cut_in, None,
            f'the run clips this header for {cut_in:.2f}" of its {diameter_in:.2f}" outside '
            "— that is a NOTCH off a face, and the chart permits ROUND HOLES ONLY, so no row "
            f"of it reaches this cut{tail}", remedy=remedy)

    limit_in = chart.max_diameter.meters / M_PER_IN
    if cut_in > limit_in + 1e-6:
        return BoreVerdict(
            False, "bore", cut_in, limit_in,
            f'{cut_in:.2f}" through a {profile} header is over the {limit_in:.2f}" the chart '
            f'publishes for a {depth_in:.2f}" member, by {cut_in - limit_in:.2f}"{tail}',
            remedy=remedy)

    zone: list[str] = []
    if chart.zone_from_bearing is not None:
        need = chart.zone_from_bearing.meters / M_PER_IN
        if from_bearing_in is None:
            return _chart_unanswered("a hole zone measured from the bearings", row)
        if from_bearing_in < need - 1e-6:
            return BoreVerdict(
                False, "bore", cut_in, limit_in,
                f'the hole is {from_bearing_in:.2f}" from the nearest bearing and the chart '
                f'allows none within {need:.2f}"{tail}', remedy=remedy)
        zone.append(f'{from_bearing_in:.2f}" off the nearest bearing against {need:.2f}"')
    if chart.zone_fraction is not None:
        if span_in is None or from_bearing_in is None:
            return _chart_unanswered("an allowed hole zone stated as a span fraction", row)
        edge = span_in * (1.0 - chart.zone_fraction) / 2.0
        if from_bearing_in < edge - 1e-6:
            return BoreVerdict(
                False, "bore", cut_in, limit_in,
                f'the hole is {from_bearing_in:.2f}" from the nearest bearing, outside the '
                f'middle {chart.zone_fraction:.3g} of the {span_in:.2f}" span, which starts '
                f'{edge:.2f}" in{tail}', remedy=remedy)
        zone.append(f"inside the middle {chart.zone_fraction:.3g} of the span")
    if chart.depth_fraction is not None or chart.min_edge_clear is not None:
        if edge_clear_in is None:
            return _chart_unanswered("a hole zone stated across the member's depth", row)
        need = 0.0
        if chart.depth_fraction is not None:
            need = max(need, depth_in * (1.0 - chart.depth_fraction) / 2.0)
        if chart.min_edge_clear is not None:
            need = max(need, chart.min_edge_clear.meters / M_PER_IN)
        if edge_clear_in < need - 1e-6:
            return BoreVerdict(
                False, "bore", cut_in, limit_in,
                f'the hole leaves {edge_clear_in:.2f}" of clear wood to the nearer face and '
                f'the chart\'s hole zone wants {need:.2f}"{tail}', remedy=remedy)
        zone.append(f'{edge_clear_in:.2f}" clear of the nearer face against {need:.2f}"')
    if chart.min_spacing is not None or chart.min_spacing_diameters is not None:
        need = 0.0
        if chart.min_spacing is not None:
            need = max(need, chart.min_spacing.meters / M_PER_IN)
        if chart.min_spacing_diameters is not None:
            # "2 x diameter of the LARGEST hole": the rule is about the PAIR, so the
            # neighbour's diameter is half of it and grading on this hole's alone would
            # publish the smaller of two numbers on the smaller of two holes.
            largest = max(cut_in, nearest_diameter_in or 0.0)
            need = max(need, chart.min_spacing_diameters * largest)
        if nearest_cut_in is not None and nearest_cut_in < need - 1e-6:
            return BoreVerdict(
                False, "bore", cut_in, limit_in,
                f'the nearest other hole in this header is {nearest_cut_in:.2f}" away and '
                f'the chart wants {need:.2f}"{tail}', remedy=remedy)
        if nearest_cut_in is not None:
            zone.append(f'{nearest_cut_in:.2f}" from the next hole against {need:.2f}"')

    where = "; ".join(zone) or "no zone stated by the chart"
    return BoreVerdict(
        True, "bore", cut_in, limit_in,
        f'{cut_in:.2f}" through a {profile} header ({depth_in:.2f}" deep) is inside the '
        f'{limit_in:.2f}" this chart publishes, and inside its hole zone — {where}{tail}')


def _chart_unanswered(what: str, row: str) -> BoreVerdict:
    """A row states a guard the caller passed nothing for. That is a MISMATCH, not a PASS."""
    return BoreVerdict(
        None, "bore", 0.0, None,
        f"the chart states {what} and this crossing passed nothing to compare it against, "
        f"so the row cannot be said to cover it [{row}]",
        remedy="give the check the header's span and bearings, or quote a row that does not "
               "state that guard")
