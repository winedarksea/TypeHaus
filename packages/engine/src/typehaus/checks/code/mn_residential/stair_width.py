"""R311.7.1 stairway width, measured off the tread boards, the handrails and the guard posts.

Split out of ``stairs.py`` (past the 500-line policy) when the guard posts joined it: a
surface-mounted guard's posts stand ON the treads, so they bound the 36" "above the
permitted handrail height" and narrow the 31.5"/27" past the handrails as well.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.railings.guard_line import guard_line_offset_m
from typehaus.resolve.railings.parts import rail_half_section_m

_MIN_STAIR_WIDTH = inch(36)  # above the handrail / between finished walls and guard posts
# R311.7.1's clear-width-past-handrail limits: 31.5" with a handrail on one side of the
# flight, 27" with handrails both sides. Measured against the authored rail's plan line
# plus the section the resolver frames (``rail_half_section_m``: the type's diameter).
_MIN_WIDTH_PAST_ONE_RAIL = inch(31.5)
_MIN_WIDTH_PAST_TWO_RAILS = inch(27)
# A rail whose plan line sits farther than this outside a flight's tread edge belongs to
# some other run (the same stair's opposite lane), not to this flight's side.
_RAIL_LATERAL_REACH = inch(12)
_RAIL_PARALLEL_DOT = 0.9  # rail runs along the flight, not across it
# A surface guard's posts stand on the treads where they are drawn. A fascia guard's are read
# only when drawn outboard in their brackets (``guard_line_offset_m`` > 0, it states its
# fascia face); one that states none is drawn on its path, which is not where it stands.
_POST_MOUNTS = frozenset({"surface", "fascia"})

Flight = tuple[float, float, float, float, float]  # width, rail 0/1, post 0/1 (m)


def _flight_projections(stair, rails, library, posts) -> dict[str, Flight]:
    """Per straight flight, ``(width, rail low, rail high, post low, post high)`` in m.

    Geometry is measured, never assumed: the flight's edges come off its tread boards'
    endpoints, the handrail's plan line off the authored path, a post off its drawn outline.
    A rail counts against a flight when it runs parallel to it, overlaps its run extent, and
    sits within ``_RAIL_LATERAL_REACH`` of one edge; its projection is however far the near
    face of its drawn section reaches past that edge. A post counts when its outline
    overlaps the run extent within the same reach. Winders are excluded — only ``tread``
    boards define a lane.
    """
    flights: dict[str, list] = {}
    for member in stair.members:
        if member.category == "tread":
            flights.setdefault(member.child_key.rsplit("-", 1)[0], []).append(member)
    out: dict[str, Flight] = {}
    for key, treads in flights.items():
        (x0, y0), (x1, y1) = treads[0].p0, treads[0].p1
        span = math.hypot(x1 - x0, y1 - y0)
        if span < 1e-9:
            continue
        cross = ((x1 - x0) / span, (y1 - y0) / span)  # across the lane
        run = (-cross[1], cross[0])  # along the climb

        def c_of(p, cross=cross):  # noqa: E306 - tiny projection helpers, scoped to this flight
            return p[0] * cross[0] + p[1] * cross[1]

        def r_of(p, run=run):
            return p[0] * run[0] + p[1] * run[1]

        ends = [p for t in treads for p in (t.p0, t.p1)]
        e0, e1 = min(c_of(p) for p in ends), max(c_of(p) for p in ends)
        r0, r1 = min(r_of(p) for p in ends), max(r_of(p) for p in ends)
        reach = _RAIL_LATERAL_REACH.meters
        proj0 = proj1 = post0 = post1 = 0.0
        for rail in rails:
            pts, half = [p.xy_m for p in rail.path], rail_half_section_m(library, rail)
            for a, b in zip(pts[:-1], pts[1:], strict=True):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if seg < 1e-9:
                    continue
                u = ((b[0] - a[0]) / seg, (b[1] - a[1]) / seg)
                if abs(u[0] * run[0] + u[1] * run[1]) < _RAIL_PARALLEL_DOT:
                    continue
                if min(r_of(a), r_of(b)) > r1 or max(r_of(a), r_of(b)) < r0:
                    continue  # alongside a different flight of the same stair
                c = c_of(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
                if not (e0 - reach <= c <= e1 + reach):
                    continue
                if abs(c - e0) <= abs(c - e1):
                    proj0 = max(proj0, min(c + half - e0, e1 - e0))
                else:
                    proj1 = max(proj1, min(e1 - (c - half), e1 - e0))
        for outline in posts:
            cs, rs = [c_of(p) for p in outline], [r_of(p) for p in outline]
            if min(rs) > r1 or max(rs) < r0:
                continue
            c = (min(cs) + max(cs)) / 2.0
            if not (e0 - reach <= c <= e1 + reach):
                continue
            if abs(c - e0) <= abs(c - e1):
                post0 = max(post0, min(max(cs) - e0, e1 - e0))
            else:
                post1 = max(post1, min(e1 - min(cs), e1 - e0))
        out[key] = (e1 - e0, max(proj0, 0.0), max(proj1, 0.0), post0, post1)
    return out


def _guard_posts(ctx: CheckContext, stair_tag: str, railings) -> list:
    """Drawn outlines of the posts of every guard serving ``stair_tag``, including a post
    one of them ends on that another guard draws (``Railing.end_post_ref``)."""
    library = getattr(getattr(ctx, "plan", None), "library", None)
    serving = [r for r in railings
               if r.serves_stair == stair_tag and r.mount in _POST_MOUNTS
               and (r.mount != "fascia" or guard_line_offset_m(library, r) > 0)]
    owners = {r.tag for r in serving}
    owners |= {ref for r in serving for ref in (r.start_post_ref, r.end_post_ref) if ref}
    if not owners:
        return []
    return [s.outline for s in getattr(ctx.model, "solids", ())
            if s.host_ref in owners and "-POST" in s.tag and len(s.outline) >= 3]


@check(Tier.CODE, "code.R311_7_1_stair_width")
def stair_width(ctx: CheckContext) -> list[Finding]:
    """Built flight width from the tread boards (R311.7.1: 36" minimum), the clear width
    past the handrails, and the clear width between guard posts.

    Three numbers per flight, all measured off the output: 36" between the tread board's
    ends; where a ``serves_stair`` guard's posts stand on the treads, 36" between
    their faces ("above the permitted handrail height"); and where a ``serves_stair``
    handrail runs alongside, what remains past its section and any post on either side —
    31.5" with a rail on one side, 27" with rails both sides. The winder turn is excluded:
    its width is the turn square's by construction.
    """
    cid, code = "code.R311_7_1_stair_width", "R311.7.1"
    from typehaus.model.structure import Railing

    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    plan = getattr(ctx, "plan", None)
    railings = [e for e in plan.all_elements() if isinstance(e, Railing)] if plan else []
    handrails = [r for r in railings if r.role in ("handrail", "guard_and_handrail")]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        widths = [member.length_m for member in stair.members
                  if member.category == "tread"]
        if not widths:
            out.append(_unknown(cid, f"{stair.tag} has no tread boards to measure",
                                (stair.tag,), code))
            continue
        width = min(widths)
        head = f"{stair.tag} flight width {width / .0254:.2f}\""
        if width < _MIN_STAIR_WIDTH.meters - 1e-9:
            out.append(_fail(cid, f"{head} < 36\"", (stair.tag,), code))
            continue
        serving = [r for r in handrails if r.serves_stair == stair.tag]
        posts = _guard_posts(ctx, stair.tag, railings)
        if not serving and not posts:
            out.append(_pass(cid, f"{head} >= 36\" (no handrail authored to project into it)",
                             code))
            continue
        failed = False
        worst_rail: tuple[float, float, int] | None = None  # (clear, limit, sides)
        worst_posts: float | None = None
        for key, (flight_w, proj0, proj1, post0, post1) in sorted(_flight_projections(
                stair, serving, getattr(plan, "library", None), posts).items()):
            if post0 > 1e-9 or post1 > 1e-9:
                between = flight_w - post0 - post1
                worst_posts = between if worst_posts is None else min(worst_posts, between)
                if between < _MIN_STAIR_WIDTH.meters - 1e-9:
                    failed = True
                    out.append(_fail(cid, f"{stair.tag} {key} clears {between / .0254:.2f}\" "
                                     "between its guard posts; R311.7.1 requires 36\" above "
                                     "the handrail", (stair.tag,), code))
            sides = (proj0 > 1e-9) + (proj1 > 1e-9)
            if sides == 0:
                continue
            clear = flight_w - max(proj0, post0) - max(proj1, post1)
            limit = (_MIN_WIDTH_PAST_TWO_RAILS if sides == 2
                     else _MIN_WIDTH_PAST_ONE_RAIL).meters
            if worst_rail is None or clear - limit < worst_rail[0] - worst_rail[1]:
                worst_rail = (clear, limit, sides)
            if clear < limit - 1e-9:
                failed = True
                out.append(_fail(cid, f"{stair.tag} {key} clears {clear / .0254:.2f}\" "
                                 f"past its handrail{'s' if sides == 2 else ''}; "
                                 f"R311.7.1 requires {limit / .0254:.1f}\"",
                                 (stair.tag,), code))
        if failed:
            continue
        parts = [f"{head} >= 36\""]
        if worst_posts is not None:
            parts.append(f"{worst_posts / .0254:.2f}\" between its guard posts (>= 36\")")
        if worst_rail is not None:
            clear, limit, sides = worst_rail
            parts.append(f"{clear / .0254:.2f}\" clear past "
                         f"{'handrails both sides' if sides == 2 else 'its handrail'} "
                         f"(>= {limit / .0254:.1f}\")")
        elif serving:
            parts[0] += " (its handrails project into no measured flight)"
        out.append(_pass(cid, " and ".join(parts), code))
    return out
