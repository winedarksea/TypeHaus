"""One found route turned into a :class:`RouteProposal`: leads, gravity, concealment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.route_fall import _fall
from typehaus.cli.route_ports import attach_leads
from typehaus.cli.route_support import Endpoints

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal


def one_proposal(model: ResolvedModel, ends: Endpoints, found: Any, target: str,
                 suffix: str, slope: float | None, explain: bool,
                 problems: list[str], *, space: Any = None) -> RouteProposal | None:
    """One found route, given its elevations and its concealment, or None with a reason."""
    from typehaus.routing.gravity import HeadBudget, minimum_slope
    from typehaus.routing.proposal import RouteProposal, bay_note, concealment
    from typehaus.routing.trades import conduit as conduit_trade

    points, lead_notes, lead_bends = attach_leads(found.polyline(), ends)
    if ends.tie_is_the_goal:
        # The search ran riser -> trunk because the fixture end is the fixed one; the run is
        # authored trunk -> riser, and every reader downstream (the dialect, `serves`, the
        # tie-in derivation itself) reads path[0] as the tee. No gravity profile is
        # involved, so this really is the one line it looks like.
        points = list(reversed(points))
    # **A route of one point is not a run.** It means the origin was already standing on the
    # goal — which is a true and useful FINDING, and on catlin it is exactly the one the
    # vent merge is about: PR-S-BATH1-VENT's origin sits 0.9" from PR-S-SUITEBATH-VENT's
    # north leg. But "paste this" is the wrong thing to say about it, and printing a 1-tuple
    # of points emits dialect that will not even parse. So it is reported, never proposed.
    if len({(round(x, 6), round(y, 6)) for x, y, _z in points}) < 2:
        problems.append(
            f"{target + suffix}: its origin already stands on what it is being routed to, "
            "so the shortest route is no route at all. That is not a lane to paste — it is "
            "a finding: the two are already in one place, and what to do about it (land "
            "this run's fixtures on the other, or move one of them) is a judgement, not a "
            "search")
        return None
    notes: list[str] = lead_notes
    if ends.falls:
        grade = slope if slope is not None else minimum_slope(ends.diameter_m)

        def fall(plan: list) -> tuple[list, str] | None:
            developed_ft = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                               for a, b in zip(plan, plan[1:], strict=False)) / 0.3048
            budget = HeadBudget(ceiling_m=ends.origin[2], required_m=ends.root[2],
                                developed_ft=developed_ft, diameter_m=ends.diameter_m)
            return _fall(plan, ends.origin, budget, grade, target + suffix, problems,
                         start_m=getattr(found, "start_m", None))

        fallen, compacted = None, _compacted(model, space, points)
        if compacted is not None:
            before = len(problems)
            fallen = fall(compacted[0])
            if fallen is not None and not _diagonals_clear(model, space, fallen[0]):
                fallen = None
            if fallen is not None:
                notes.append(compacted[1])
            else:
                del problems[before:]  # a refused pair is not the route's refusal
        if fallen is None:
            fallen = fall(points)
        if fallen is None:
            return None
        points, note = fallen
        notes.append(note)

    routing, floor_ref, soffit_ref = (None, None, None)
    if ends.kind == "duct":
        routing, floor_ref, soffit_ref = concealment(model, found.corridor_tags)
        note = bay_note(model, found.corridor_tags, ends.radius_m)
        if note:
            notes.append(note)
    if ends.kind == "conduit":
        disclosed = conduit_trade.disclosure(conduit_trade.legalize(list(points)))
        if disclosed:
            notes.append(disclosed)

    proposal = RouteProposal(
        tag=f"{target}-PROPOSED{suffix}", kind=ends.kind, points=[*ends.held, *points],
        diameter_m=ends.diameter_m, width_m=ends.width_m, depth_m=ends.depth_m,
        serves=ends.serves, system=ends.system, cost=found.cost, bends=found.bends + lead_bends,
        terms=dict(found.terms) if explain else {}, notes=notes, routing=routing,
        floor_ref=floor_ref, soffit_ref=soffit_ref, echo=dict(ends.echo),
        after=ends.after_paste).snapped()
    # After snapping: the indices must be the pasted run's own.
    return proposal.with_pull_points(ends.pull_boxes) if ends.kind == "conduit" else proposal


def _compacted(model: Any, space: Any, points: list) -> tuple[list, str] | None:
    """The plan route with its short jogs as 45-degree pairs (oracle §10), or None."""
    if space is None:
        return None
    from typehaus.quantities import M_PER_IN
    from typehaus.routing.compaction import compact_offsets, segment_clear

    out, made = compact_offsets(
        points, space.cost.offset_jog_max_in * M_PER_IN,
        lambda candidate, i: segment_clear(space, model, candidate[i], candidate[i + 1]))
    if not made:
        return None
    return out, (f"offset: {made} short jog(s) drawn as a pair of 1/8 bends rather than "
                 "two 90s, each re-checked against obstacles and member windows")


def _diagonals_clear(model: Any, space: Any, points: list) -> bool:
    """Every oblique plan leg, at its graded invert, still clear (``segment_clear``)."""
    from typehaus.routing.compaction import segment_clear

    return all(segment_clear(space, model, a, b)
               for a, b in zip(points, points[1:], strict=False)
               if abs(b[0] - a[0]) > 1e-6 and abs(b[1] - a[1]) > 1e-6)
