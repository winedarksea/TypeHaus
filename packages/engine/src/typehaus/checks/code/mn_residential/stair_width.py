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
# A guard serving another level (a well guard on the deck above) obstructs a flight only
# where its post reaches the envelope R311.7.1 keeps clear: from the lowest permitted
# handrail height (R311.7.8.1) to the required headroom (R311.7.2) over the tread below it.
_CLEAR_FROM = inch(34)
_CLEAR_TO = inch(80)

Flight = tuple[float, float, float, float, float]  # width, rail 0/1, post 0/1 (m)
# A post's drawn outline and, for a guard not serving the flight, its (z0, z1) to test
# against the clear envelope; ``None`` for a serving guard's, which stand on the treads.
Post = tuple[list, tuple[float, float] | None]


def _in_clear_envelope(z_range, treads, r_of, rs, half_going: float) -> bool:
    """Does a post spanning ``z_range`` reach the clear envelope over a tread under it?"""
    z0, z1 = z_range
    for tread in treads:
        r = r_of(tread.p0)
        if max(rs) < r - half_going or min(rs) > r + half_going:
            continue
        if z0 < tread.z1_m + _CLEAR_TO.meters and z1 > tread.z1_m + _CLEAR_FROM.meters:
            return True
    return False


def _flight_projections(stair, rails, library, posts: list[Post]) -> dict[str, Flight]:
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
        for outline, z_range in posts:
            cs, rs = [c_of(p) for p in outline], [r_of(p) for p in outline]
            if min(rs) > r1 or max(rs) < r0:
                continue
            if z_range is not None and not _in_clear_envelope(
                    z_range, treads, r_of, rs, stair.tread_depth_m / 2.0):
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


def _guard_posts(ctx: CheckContext, stair_tag: str, railings) -> tuple[list[Post], list[str]]:
    """Posts that may stand in ``stair_tag``'s width, and the fascia guards whose posts are
    not drawn where they stand.

    A serving guard's posts count wherever they are, including a post one of them ends on
    that another guard draws (``Railing.end_post_ref``). Any other guard's count only where
    they reach the clear envelope over a tread (a well guard hung on the deck edge above).
    A fascia guard that states no fascia face is drawn on its path, which is not where it
    stands: it is returned by tag, for an UNKNOWN wherever its drawn posts would count.
    """
    library = getattr(getattr(ctx, "plan", None), "library", None)
    placed = [r for r in railings if r.mount in _POST_MOUNTS
              and (r.mount != "fascia" or guard_line_offset_m(library, r) > 0)]
    unplaced = {r.tag for r in railings
                if r.mount == "fascia" and guard_line_offset_m(library, r) <= 0}
    serving = {r.tag for r in placed if r.serves_stair == stair_tag}
    serving |= {ref for r in placed if r.serves_stair == stair_tag
                for ref in (r.start_post_ref, r.end_post_ref) if ref}
    others = {r.tag for r in placed} - serving
    posts: list[Post] = []
    unplaced_posts: list[tuple[str, Post]] = []
    for s in getattr(ctx.model, "solids", ()):
        if "-POST" not in s.tag or len(s.outline) < 3:
            continue
        if s.host_ref in serving:
            posts.append((s.outline, None))
        elif s.host_ref in others:
            posts.append((s.outline, (s.z0_m, s.z1_m)))
        elif s.host_ref in unplaced:
            unplaced_posts.append((s.host_ref, (s.outline, (s.z0_m, s.z1_m))))
    return posts, unplaced_posts


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
        posts, unplaced_posts = _guard_posts(ctx, stair.tag, railings)
        library = getattr(plan, "library", None)
        # A fascia guard whose drawn posts would reach a flight stands 1 1/2"+ outboard of
        # them, on a side its path does not say: the width there is not measured.
        unplaced = sorted({tag for tag, post in unplaced_posts
                           if any(p0 > 1e-9 or p1 > 1e-9 for *_, p0, p1 in
                                  _flight_projections(stair, [], library, [post]).values())})
        if not serving and not posts and not unplaced:
            out.append(_pass(cid, f"{head} >= 36\" (no handrail authored to project into it)",
                             code))
            continue
        failed = False
        worst_rail: tuple[float, float, int] | None = None  # (clear, limit, sides)
        worst_posts: float | None = None
        for key, (flight_w, proj0, proj1, post0, post1) in sorted(_flight_projections(
                stair, serving, library, posts).items()):
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
        if unplaced:
            out.append(_unknown(
                cid, f"{stair.tag}: fascia guard(s) {', '.join(unplaced)} state no "
                "fascia_face_offset, so their posts are drawn on the path, not in the "
                "brackets where they stand; the clear width past them is not measured",
                (stair.tag, *unplaced), code))
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
