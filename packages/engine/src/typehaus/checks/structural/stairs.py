"""Stair load-path and winder-geometry checks — advisory, not engineering (→ 12).

Kept out of ``resolve/stairs.py`` on purpose. ``resolve_envelope_geometry``'s finding
contract is *bad references* — a stair naming a storey or an opening that does not exist —
and it fails the build when one shows up. Neither rule here is a bad reference: a landing
post can land on a perfectly resolvable deck that simply is not carrying anything, and a
winder turn can be geometrically consistent and still short of code. Both are judgements
about a resolved model, so both belong in the STRUCTURAL tier, at WARN, beside every other
"advisory, not engineering" rule.
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedStair

# IRC R311.7.5.2.1: a winder tread must be at least 6" deep at every point within the
# stairway's clear width, which includes its narrow end against the newel — and at least
# 10" deep on the walk line, measured 12" in from the narrow side.
MIN_WINDER_NARROW_TREAD_IN = 6.0
MIN_WINDER_WALK_LINE_TREAD_IN = 10.0
WALK_LINE_OFFSET_IN = 12.0

# IRC R311.7.5.1: the greatest riser height in a flight may exceed the smallest by 3/8".
MAX_RISER_VARIATION_IN = 0.375
# Categories whose top face is a surface a foot lands on, in the order a climber meets
# them. A winder box's deck is its ``winder`` tread; a U-stair's platforms are ``landing``
# decks (``landing-joist``/``-rim``/``-post`` members are framing under them, not surfaces).
_WALKING_SURFACE_CATEGORIES = frozenset({"tread", "winder"})
_LANDING_FRAMING_PREFIXES = ("landing-joist-", "landing-rim-", "landing-post-")

# How close a supporting element's top has to be to a post's base to be carrying it.
_BEARING_TOLERANCE_M = inch(1.0).meters
# Solids that carry a point load landing on them: concrete (a slab, footing or pad spans to
# its own supports, so anywhere inside one has a load path) and the beams/columns a post
# stacks straight down onto. A *framed* deck is deliberately absent — see
# ``_bearing_element_under``.
_BEARING_SOLID_CATEGORIES = frozenset({"slab", "footing", "pad", "beam", "column"})

_LANDING_POST_PREFIX = "landing-post-"


def _advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result,
              fix_hint: str | None = None) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid,
                   message=f"[advisory, not engineering] {msg}", element_tags=tags,
                   result=result, fix_hint=fix_hint)


def _landing_posts(stair: ResolvedStair) -> list[FramedMember]:
    return [member for member in stair.members
            if member.child_key.startswith(_LANDING_POST_PREFIX)]


def _point_in_ring(point: tuple[float, float], ring) -> bool:
    """Ray-cast point-in-polygon, so this module stays free of the geometry kernel."""
    x, y = point
    inside = False
    count = len(ring)
    for index in range(count):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % count]
        if (y0 > y) != (y1 > y):
            crossing_x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < crossing_x:
                inside = not inside
    return inside


def _bearing_element_under(ctx: CheckContext, point: tuple[float, float],
                           base_z: float) -> str | None:
    """The tag of whatever carries a point load at ``point``/``base_z``, or ``None``.

    Three load paths count, in the order a framer would look for them: concrete under the
    post (a slab distributes a point load to its own supports), a beam or column topping
    out right beneath it, and a wall whose top plate — or whose concrete top — is at the
    post's base. A framed deck's joists are deliberately *not* a load path: a 4x4 landing
    post set down mid-bay needs blocking or a beam under it, and that is the whole point of
    the check.
    """
    for solid in ctx.model.solids:
        if (solid.category in _BEARING_SOLID_CATEGORIES
                and abs(solid.z1_m - base_z) <= _BEARING_TOLERANCE_M
                and _point_in_ring(point, solid.outline)):
            return solid.tag
    for wall in ctx.model.walls:
        if abs(wall.z1_m - base_z) > _BEARING_TOLERANCE_M:
            continue
        (x0, y0), (x1, y1) = wall.axis
        dx, dy = x1 - x0, y1 - y0
        run2 = dx * dx + dy * dy
        if run2 < 1e-18:
            continue
        t = max(0.0, min(1.0, ((point[0] - x0) * dx + (point[1] - y0) * dy) / run2))
        if math.hypot(point[0] - (x0 + t * dx), point[1] - (y0 + t * dy)) <= wall.thickness_m / 2:
            return wall.tag
    return None


@check(Tier.STRUCTURAL, "structural.landing_post_bearing")
def landing_post_bearing(ctx: CheckContext) -> list[Finding]:
    """Every stair landing post must land on something that can carry it.

    ``resolve/stairs.py`` drops a 4x4 under each landing-platform corner no host wall
    reaches and stops the post at the subfloor of the storey the flight springs from — it
    never asks what is under that subfloor. A post bearing mid-bay on an I-joist deck is a
    point load on a member sized for a uniform one.
    """
    posts = [(stair, post) for stair in ctx.model.stairs for post in _landing_posts(stair)]
    if not posts:
        return [Finding(severity=Severity.WARN, check_id="structural.landing_post_bearing",
                        message="UNKNOWN — no stair landing posts to trace",
                        result=Result.UNKNOWN)]
    out: list[Finding] = []
    for stair, post in posts:
        label = f"{stair.tag}:{post.child_key}"
        support = _bearing_element_under(ctx, post.p0, post.z0_m)
        if support is None:
            out.append(_advisory(
                "structural.landing_post_bearing",
                f"landing post {label} bears on the deck at "
                f"{post.z0_m / 0.3048:.2f}' with no slab, beam or bearing wall under it",
                (stair.tag,), Result.FAIL,
                fix_hint=("carry the post down to a beam, a bearing wall or a footing, or "
                          "block the joist bay under it — a deck joist alone is sized for a "
                          "uniform load, not a landing corner reaction"),
            ))
        else:
            out.append(_advisory(
                "structural.landing_post_bearing",
                f"landing post {label} bears on {support}", (stair.tag, support), Result.PASS))
    return out


def _walking_surfaces(stair: ResolvedStair) -> list[float]:
    """Every finished face a climber lands on between the two floors, ascending.

    Treads, winder box decks and landing platforms — but not the framing under them: a
    landing joist/rim/post tops out at the deck's *underside*, so counting one would read
    as a step where there is none.
    """
    tops = [member.z1_m for member in stair.members
            if member.category in _WALKING_SURFACE_CATEGORIES
            or (member.category == "landing"
                and not member.child_key.startswith(_LANDING_FRAMING_PREFIXES))]
    return sorted(tops)


@check(Tier.STRUCTURAL, "structural.stair_riser_uniformity")
def stair_riser_uniformity(ctx: CheckContext) -> list[Finding]:
    """Measure every riser in each flight against IRC R311.7.5.1's 3/8" spread.

    The rise from the springing floor to the first tread, tread to tread, tread to
    landing, and the last tread to the arrival deck are all risers a foot has to take, and
    the code allows 3/8" between the largest and the smallest. Nothing measured them here
    before, which is how the tread boards came to sit *on* each step's theoretical
    elevation rather than being dropped to it (``resolve/stairs/common.py::_notch_z``) —
    a 9" first riser and a 6" last one against a 7.5" design riser, invisible because
    ``riser_height_m`` is the design number and only the generated members carry the
    built one.
    """
    if not ctx.model.stairs:
        return [Finding(severity=Severity.WARN, check_id="structural.stair_riser_uniformity",
                        message="UNKNOWN — no stairs to measure", result=Result.UNKNOWN)]
    allowed_m = inch(MAX_RISER_VARIATION_IN).meters
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        surfaces = _walking_surfaces(stair)
        if not surfaces:
            continue
        # The flight springs from the lowest framing it was clipped to (its own subfloor)
        # and lands on the arrival deck a full design rise above it.
        springing = min(member.z0_m for member in stair.members)
        arrival = springing + stair.riser_height_m * stair.riser_count
        ladder = [springing, *surfaces, arrival]
        risers = [upper - lower for lower, upper in zip(ladder, ladder[1:])]
        spread = max(risers) - min(risers)
        label = (f"{min(risers) / 0.0254:.2f}\"–{max(risers) / 0.0254:.2f}\" over "
                 f"{len(risers)} risers")
        if spread > allowed_m + 1e-9:
            out.append(_advisory(
                "structural.stair_riser_uniformity",
                f"stair {stair.tag} risers vary by {spread / 0.0254:.2f}\" ({label}), over "
                f"the {MAX_RISER_VARIATION_IN:.3f}\" IRC R311.7.5.1 maximum",
                (stair.tag,), Result.FAIL,
                fix_hint=("drop every tread/landing board to its step elevation instead of "
                          "stacking it on top — the first and last risers are the ones a "
                          "board thickness lands on"),
            ))
        else:
            out.append(_advisory(
                "structural.stair_riser_uniformity",
                f"stair {stair.tag} risers vary by {spread / 0.0254:.2f}\" ({label})",
                (stair.tag,), Result.PASS))
    return out


def _winder_stairs(ctx: CheckContext) -> list[ResolvedStair]:
    return [stair for stair in ctx.model.stairs
            if any(member.category == "winder" for member in stair.members)]


def _winder_gaps(stair: ResolvedStair, offset_m: float) -> list[float]:
    """Going between consecutive winder nosings, ``offset_m`` out from the narrow end.

    A winder member runs narrow end (``p0``, on the newel's face) to nosing (``p1``), so
    walking ``offset_m`` along it lands on the line the code measures: 0 is the narrow end
    itself, 12" the walk line. Consecutive risers are what the code measures between, so
    the winders are taken in ascending order.
    """
    winders = sorted((member for member in stair.members if member.category == "winder"),
                     key=lambda member: member.z0_m)

    def point_at(member: FramedMember) -> tuple[float, float]:
        dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
        run = math.hypot(dx, dy)
        if run < 1e-9:
            return member.p0
        reach = min(offset_m, run) / run
        return (member.p0[0] + dx * reach, member.p0[1] + dy * reach)

    points = [point_at(member) for member in winders]
    return [math.hypot(upper[0] - lower[0], upper[1] - lower[1])
            for lower, upper in zip(points, points[1:])]


@check(Tier.STRUCTURAL, "structural.winder_walk_line_depth")
def winder_walk_line_depth(ctx: CheckContext) -> list[Finding]:
    """Measure winder going on the walk line against IRC R311.7.5.2.1's 10".

    The walk line is 12" in from the narrow side of the treads, and that is where a winder
    has to deliver the same 10" going a straight tread does. It is the *other* half of the
    winder rule — ``winder_narrow_tread_depth`` measures the 6" floor at the newel — and
    the one that decides whether a turn is walkable rather than merely legal at its pinch
    point. A 90° turn taken in three winders sweeps 22.5° per tread, so the walk line has
    to sit ~2'-2" out from the pivot before consecutive nosings are 10" apart: it is a
    function of the *well*, which is why neither a bigger newel nor better framing moves
    it.
    """
    winder_stairs = _winder_stairs(ctx)
    if not winder_stairs:
        return [Finding(severity=Severity.WARN,
                        check_id="structural.winder_walk_line_depth",
                        message="UNKNOWN — no winder treads to measure",
                        result=Result.UNKNOWN)]
    minimum_m = inch(MIN_WINDER_WALK_LINE_TREAD_IN).meters
    out: list[Finding] = []
    for stair in winder_stairs:
        gaps = _winder_gaps(stair, inch(WALK_LINE_OFFSET_IN).meters)
        if not gaps:
            continue
        narrowest = min(gaps)
        detail = (f"stair {stair.tag} winder going on the walk line "
                  f"({WALK_LINE_OFFSET_IN:.0f}\" from the narrow end) is "
                  f"{narrowest / 0.0254:.1f}\"")
        if narrowest + 1e-9 < minimum_m:
            out.append(_advisory(
                "structural.winder_walk_line_depth",
                f"{detail}, under the {MIN_WINDER_WALK_LINE_TREAD_IN:.0f}\" IRC "
                "R311.7.5.2.1 minimum", (stair.tag,), Result.FAIL,
                fix_hint=("widen the well so the turn sweeps a longer arc, or spread the "
                          "turn over more risers — the walk line is set by the well, not "
                          "by the newel or the turn framing"),
            ))
        else:
            out.append(_advisory(
                "structural.winder_walk_line_depth",
                f"{detail} (>= {MIN_WINDER_WALK_LINE_TREAD_IN:.0f}\")",
                (stair.tag,), Result.PASS))
    return out


@check(Tier.STRUCTURAL, "structural.winder_narrow_tread_depth")
def winder_narrow_tread_depth(ctx: CheckContext) -> list[Finding]:
    """Measure winder tread depth at the narrow end against IRC R311.7.5.2.1's 6".

    The narrow-end depth is the plan gap between the narrow ends of two consecutive winder
    nosings. It was structurally 0 while every winder converged on the newel *centreline*;
    starting them at the newel's face gives it a real value, and this reports whether that
    value clears the code minimum. A quarter turn taken in three winders around a 4x4 will
    not — the honest fix is a layout decision (more risers in the turn, or a larger newel
    the winders wrap), not a number this generator can invent.
    """
    winder_stairs = _winder_stairs(ctx)
    if not winder_stairs:
        return [Finding(severity=Severity.WARN,
                        check_id="structural.winder_narrow_tread_depth",
                        message="UNKNOWN — no winder treads to measure",
                        result=Result.UNKNOWN)]
    minimum_m = inch(MIN_WINDER_NARROW_TREAD_IN).meters
    out: list[Finding] = []
    for stair in winder_stairs:
        gaps = _winder_gaps(stair, 0.0)
        if not gaps:
            continue
        narrowest = min(gaps)
        if narrowest + 1e-9 < minimum_m:
            out.append(_advisory(
                "structural.winder_narrow_tread_depth",
                f"stair {stair.tag} winder tread depth at the narrow end is "
                f"{narrowest / 0.0254:.1f}\", under the "
                f"{MIN_WINDER_NARROW_TREAD_IN:.0f}\" IRC R311.7.5.2.1 minimum",
                (stair.tag,), Result.FAIL,
                fix_hint=(f"spread the turn over more risers, or wrap the winders around a "
                          f"newel/well wide enough that consecutive narrow ends are "
                          f"{MIN_WINDER_NARROW_TREAD_IN:.0f}\" apart"),
            ))
        else:
            out.append(_advisory(
                "structural.winder_narrow_tread_depth",
                f"stair {stair.tag} winder tread depth at the narrow end is "
                f"{narrowest / 0.0254:.1f}\" (>= {MIN_WINDER_NARROW_TREAD_IN:.0f}\")",
                (stair.tag,), Result.PASS))
    return out
