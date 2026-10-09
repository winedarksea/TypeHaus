"""Stair load-path and riser-uniformity checks — advisory, not engineering (→ 12).

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

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedStair
from typehaus.resolve.solid_categories import in_slab_family
from typehaus.resolve.stairs.walkline import intermediate_step_elevations, level_landing_is_complete

# IRC R311.7.5.1: the greatest riser height in a flight may exceed the smallest by 3/8".
MAX_RISER_VARIATION_IN = 0.375
# Categories whose top face is a surface a foot lands on, in the order a climber meets
# them. A winder box's deck is its ``winder`` tread; a U-stair's platform is its ``landing``
# deck. The joists, rims and posts under a platform are ``landing_framing`` and are excluded
# by category — a single frozenset test, not a child-key prefix list, since walking surface
# and framing are separate categories.

# How close a supporting element's top has to be to a post's base to be carrying it.
_BEARING_TOLERANCE_M = inch(1.0).meters
# Solids that carry a point load landing on them: concrete (a slab, footing or pad spans to
# its own supports, so anywhere inside one has a load path) and the beams/columns a post
# stacks straight down onto. A *framed* deck is deliberately absent — see
# ``_bearing_element_under``.
_BEARING_SOLID_CATEGORIES = frozenset({"footing", "pad", "beam", "column"})

_LANDING_POST_PREFIX = "landing-post-"




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
        if ((solid.category in _BEARING_SOLID_CATEGORIES or in_slab_family(solid.category))
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
    return intermediate_step_elevations(stair)


@check(Tier.STRUCTURAL, "structural.stair_riser_uniformity")
def stair_riser_uniformity(ctx: CheckContext) -> list[Finding]:
    """Measure the risers WITHIN each flight against IRC R311.7.5.1's 3/8" spread.

    Tread to tread, tread to landing, landing to tread: every step between two generated
    members, which is what catches a tread board sitting *on* its theoretical elevation
    rather than dropped to it (``resolve/stairs/common.py::_notch_z``) — a 9" first riser
    and a 6" last one against a 7.5" design riser, invisible because ``riser_height_m`` is
    the design number and only the generated members carry the built one.

    ** THE TWO END RISERS ARE NOT THIS CHECK'S ANSWER. ** The springing and arrival used
    here are the flight's own — an authored ``base_elevation`` or the lowest framing, plus
    ``riser_count`` design rises — so the ladder closes on itself and the ends can only
    report what the flight already claims. Measuring them against the floors they really
    meet needs the deck under the probe and the depth of the finish on it, which is
    ``code.R311_7_5_1_stair_end_risers`` and ``resolve/walking_surface.py``. Both rules
    cite R311.7.5.1 and neither subsumes the other: this one grades the flight's interior,
    where nothing but the generator can be wrong, and that one grades its two ends, where
    the building is.
    """
    if not ctx.model.stairs:
        return [Finding(severity=Severity.WARN, check_id="structural.stair_riser_uniformity",
                        message="UNKNOWN — no stairs to measure", result=Result.UNKNOWN)]
    allowed_m = inch(MAX_RISER_VARIATION_IN).meters
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        if not level_landing_is_complete(stair):
            out.append(_advisory(
                "structural.stair_riser_uniformity",
                f"stair {stair.tag} has a missing or uneven level landing half",
                (stair.tag,), Result.FAIL))
            continue
        surfaces = _walking_surfaces(stair)
        if not surfaces:
            continue
        # The flight springs from the lowest framing it was clipped to (its own subfloor)
        # and lands on the arrival deck a full design rise above it — EXCEPT where the flight
        # states its own base, which then wins outright. Reading the members is a proxy for
        # the springing and a good one for a framed flight; it is simply wrong for a cast
        # one, whose only members are its treads, so the proxy returns the FIRST TREAD and
        # reports a 1 1/2" bottom riser and a 12" top one on a terrace whose five risers are
        # equal by construction.
        springing = (stair.base_elevation_m if stair.base_elevation_m is not None
                     else min(member.z0_m for member in stair.members))
        arrival = springing + stair.riser_height_m * stair.riser_count
        ladder = [springing, *surfaces, arrival]
        # strict=False: the tail is one shorter than ``ladder`` by construction — the
        # sliding window is the point.
        risers = [upper - lower for lower, upper in zip(ladder, ladder[1:], strict=False)]
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

