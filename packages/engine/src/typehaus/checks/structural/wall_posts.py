"""A post standing *inside* a wall (``Post.within_wall``): clear of its openings, over a stud.

``structural.member_interference`` pardons every clash between such a post and its own wall,
because the framer cuts the plates and studs around it (``resolve/framing/posts.py``). That
pardon is blind to *what* got cut, so the two things it hides are graded here:

* ``structural.wall_post_opening_clearance`` — the post's band on the wall axis must not
  overlap any opening's framed extent: the rough opening plus its jack and king pack. A post
  in a window is a post with no header over it and a pack with no plate to bear on.
* ``structural.wall_post_bearing`` — where the wall stacks on a lower framed wall, a
  vertical member of that wall (stud, king, jack, corner, or a post within it) must have its
  centreline under the post's footprint. An ungraded heavy timber is a point load the rim
  and subfloor alone should not carry, so it needs a stud to land on. With no wall below,
  a post on a floor system is UNKNOWN (the joist under it is not graded here) and one on a
  slab or foundation is N/A — the ground takes it.
"""

from __future__ import annotations

import math
import re

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.floors import FloorSystem
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.posts import post_bands, posts_by_wall
from typehaus.resolve.layout_lines import collinear_overlap

_CLEAR_CID = "structural.wall_post_opening_clearance"
_BEAR_CID = "structural.wall_post_bearing"
_CLEAR_CODE = "IRC R602.7"
_BEAR_CODE = "IRC R301.1"
_IN = 0.0254
_PACK_KEY = re.compile(r"^(jack|king)-(\d+)-")
_BEARING_MEMBERS = frozenset({"stud", "king", "jack", "corner"})
# ``resolve/stacking``'s raw-axis tolerance: the same "is this that wall line" question.
_AXIS_TOL_M = 0.5 * _IN


def _axis(wall) -> tuple[tuple[float, float], tuple[float, float]]:
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0) or 1.0
    return (x0, y0), ((x1 - x0) / run, (y1 - y0) / run)


def _station(point, start, direction) -> float:
    return (point[0] - start[0]) * direction[0] + (point[1] - start[1]) * direction[1]


def _post_band(post, wall) -> tuple[float, float]:
    """``(low, high)`` of ``post``'s footprint on ``wall``'s axis, metres from its start."""
    start, direction = _axis(wall)
    centre, half = post_bands((post,), start, direction)[0]
    return centre - half, centre + half


def _opening_extents(wall, openings) -> list[tuple[str, float, float]]:
    """``(tag, low, high)`` framed extent of each opening: RO plus its jack/king pack."""
    start, direction = _axis(wall)
    packs: dict[str, list[float]] = {}
    for member in wall.members:
        match = _PACK_KEY.match(member.child_key)
        if match:
            ring, _z0, _z1 = member_footprint(member)
            packs.setdefault(match.group(2), []).extend(
                _station(p, start, direction) for p in ring)
    out: list[tuple[str, float, float]] = []
    for opening in openings:
        low = opening.center_along_m - opening.width_m / 2.0
        high = opening.center_along_m + opening.width_m / 2.0
        if opening.pocket_sign > 0:
            high += opening.pocket_run_m
        elif opening.pocket_sign < 0:
            low -= opening.pocket_run_m
        # The pack whose stations sit nearest this RO is its own: keys index the host's
        # openings, and matching by geometry keeps this check off that ordering.
        near = [s for s in min(packs.values(), key=lambda ss: min(
            abs(x - opening.center_along_m) for x in ss), default=[])
            if low - 0.2 <= s <= high + 0.2]
        out.append((opening.tag, min([low, *near]), max([high, *near])))
    return out


def _post_walls(ctx: CheckContext):
    """``[(post, wall or None), ...]`` for every post that names a wall."""
    walls = {w.tag: w for w in ctx.model.walls}
    return [(post, walls.get(tag))
            for tag, posts in sorted(posts_by_wall(ctx.plan).items()) for post in posts]


@check(Tier.STRUCTURAL, _CLEAR_CID)
def wall_post_opening_clearance(ctx: CheckContext) -> list[Finding]:
    """A within-wall post stands clear of every opening's RO and jamb pack."""
    if ctx.plan is None:
        return []
    pairs = _post_walls(ctx)
    if not pairs:
        return [not_applicable(_CLEAR_CID, "no post names a wall it stands inside",
                               code=_CLEAR_CODE)]
    out: list[Finding] = []
    for post, wall in pairs:
        if wall is None:
            out.append(unknown(_CLEAR_CID, f"{post.tag} names within_wall="
                               f"{post.within_wall!r}, which does not resolve",
                               (post.tag,), code=_CLEAR_CODE))
            continue
        low, high = _post_band(post, wall)
        hosted = [o for o in ctx.model.openings if o.host_wall == wall.tag]
        hits = [(tag, min(high, b) - max(low, a))
                for tag, a, b in _opening_extents(wall, hosted) if min(high, b) > max(low, a)]
        tags = (post.tag, wall.tag)
        if hits:
            out.append(failed(
                _CLEAR_CID,
                f"{post.tag} stands in {wall.tag}'s "
                + "; ".join(f"{tag} framing by {overlap / _IN:.2f}\"" for tag, overlap in hits),
                (*tags, *(tag for tag, _ in hits)), code=_CLEAR_CODE,
                fix="move the post clear of the opening's jack and king studs"))
        else:
            out.append(passed(_CLEAR_CID, f"{post.tag} clears the {len(hosted)} openings "
                              f"in {wall.tag}", tags, code=_CLEAR_CODE))
    return out


def _bearing_stations(ctx: CheckContext, upper, lower) -> list[tuple[float, str]]:
    """``(station on upper's axis, label)`` of every vertical bearing member below it."""
    start, direction = _axis(upper)
    lower_posts = posts_by_wall(ctx.plan)
    out: list[tuple[float, str]] = []
    for wall in lower:
        for member in wall.members:
            if member.category in _BEARING_MEMBERS and member.p0 == member.p1:
                out.append((_station(member.p0, start, direction),
                            f"{wall.tag}:{member.child_key}"))
        for post in lower_posts.get(wall.tag, ()):
            out.append((_station(post.position.xy_m, start, direction), post.tag))
    return out


def _walls_under(ctx: CheckContext, upper, stacked_on: list[str], station: float) -> list:
    """The walls on ``upper``'s stacked storey(s) whose run on its line covers ``station``.

    A stack edge pairs each lower wall with ONE upper, so an upper wall spanning two lower
    segments (W-S-W3 over W-M-W3 and part of W-M-W4) is read off the line, not the edges.
    """
    walls = {w.tag: w for w in ctx.model.walls}
    storeys = {walls[t].storey for t in stacked_on if t in walls}
    out = []
    for wall in ctx.model.walls:
        if wall.storey not in storeys:
            continue
        run = collinear_overlap(upper.axis, wall.axis, _AXIS_TOL_M)
        if run is not None and run[0] - 1e-9 <= station <= run[1] + 1e-9:
            out.append(wall)
    return out


@check(Tier.STRUCTURAL, _BEAR_CID)
def wall_post_bearing(ctx: CheckContext) -> list[Finding]:
    """A within-wall post over a lower framed wall lands on one of its vertical members."""
    if ctx.plan is None:
        return []
    pairs = [(p, w) for p, w in _post_walls(ctx) if w is not None]
    if not pairs:
        return [not_applicable(_BEAR_CID, "no post names a wall it stands inside",
                               code=_BEAR_CODE)]
    below: dict[str, list[str]] = {}
    for edge in ctx.model.stack_edges:
        below.setdefault(edge.upper_wall, []).append(edge.lower_wall)
    out: list[Finding] = []
    for post, wall in pairs:
        tags = (post.tag, wall.tag)
        low, high = _post_band(post, wall)
        lower = _walls_under(ctx, wall, below.get(wall.tag, []), (low + high) / 2.0)
        if not lower:
            support = ctx.plan.by_tag(post.supported_by) if post.supported_by else None
            if support is None or isinstance(support, FloorSystem):
                out.append(unknown(
                    _BEAR_CID, f"{post.tag} stands in {wall.tag}, which stacks on no wall; "
                    f"what carries it under {post.supported_by or 'its base'} is not graded",
                    tags, code=_BEAR_CODE))
            else:
                out.append(not_applicable(
                    _BEAR_CID, f"{post.tag} bears on {support.tag} "
                    f"({type(support).__name__}), not through a framed floor", tags,
                    code=_BEAR_CODE))
            continue
        lower_tags = tuple(w.tag for w in lower)
        solid = [w.tag for w in lower if not any(m.category in _BEARING_MEMBERS
                                                 for m in w.members)]
        if solid:
            out.append(passed(_BEAR_CID, f"{post.tag} bears on {', '.join(solid)}, a "
                              "continuous wall with no stud grid", (*tags, *lower_tags),
                              code=_BEAR_CODE))
            continue
        stations = _bearing_stations(ctx, wall, lower)
        under = [label for s, label in stations if low - 1e-9 <= s <= high + 1e-9]
        if under:
            out.append(passed(_BEAR_CID, f"{post.tag} lands on {', '.join(under)}",
                              (*tags, *lower_tags), code=_BEAR_CODE))
            continue
        centre = (low + high) / 2.0
        near = min(stations, key=lambda sl: abs(sl[0] - centre), default=None)
        if near is None:
            where = "; the wall below frames no vertical members"
        else:
            past = abs(near[0] - centre) - (high - low) / 2.0
            where = f"; nearest is {near[1]}, {past / _IN:.2f}\" past its face"
        out.append(failed(
            _BEAR_CID, f"{post.tag} in {wall.tag} stands over no stud of "
            f"{', '.join(lower_tags)}{where}", (*tags, *lower_tags), code=_BEAR_CODE,
            fix="move the post over a stud line, or add a stud under it in the wall below"))
    return out
