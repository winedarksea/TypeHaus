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
# stairway's clear width, which includes its narrow end against the newel.
MIN_WINDER_NARROW_TREAD_IN = 6.0

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
    winder_stairs = [stair for stair in ctx.model.stairs
                     if any(member.category == "winder" for member in stair.members)]
    if not winder_stairs:
        return [Finding(severity=Severity.WARN,
                        check_id="structural.winder_narrow_tread_depth",
                        message="UNKNOWN — no winder treads to measure",
                        result=Result.UNKNOWN)]
    minimum_m = inch(MIN_WINDER_NARROW_TREAD_IN).meters
    out: list[Finding] = []
    for stair in winder_stairs:
        # Ascending order: consecutive risers are what the code measures between.
        winders = sorted((member for member in stair.members if member.category == "winder"),
                         key=lambda member: member.z0_m)
        gaps = [math.hypot(upper.p0[0] - lower.p0[0], upper.p0[1] - lower.p0[1])
                for lower, upper in zip(winders, winders[1:])]
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
