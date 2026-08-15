"""Exterior-deck checks — IRC R507 / AWC DCA6 (→ 12 §checks/structural).

An exterior deck is not an interior floor with the weather on it: it carries a different
load case, its beams and posts are sized off their own tables, its footings are sized off
the soil, and it needs a guard once it is high enough. None of that was encoded — a deck
resolved into joists, beams, posts and pads and no rule ever looked at the result.

Scope comes from :attr:`~typehaus.model.floors.FloorSystem.service` being ``"deck"``.
Nothing here is inferred from geometry: a freestanding deck and an interior floor resolve
identically, so the distinction is authored (and the interior-floor span check skips decks
on the same flag rather than grading them against the 40 psf residential floor table).

Everything reads :mod:`typehaus.checks.structural.deck_tables`, whose docstring states what
those numbers are and are not. Results are tri-state: a missing table row, a missing soil
bearing value, or an unresolvable bearing chain reports UNKNOWN, never a silent pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.deck_tables import (
    DECK_TOTAL_LOAD_PSF,
    GUARD_MIN_HEIGHT_IN,
    GUARD_REQUIRED_ABOVE_IN,
    MIN_DECK_FOOTING_SIDE_IN,
    MIN_DECK_FOOTING_THICKNESS_IN,
    MIN_DECK_POST_NOMINAL,
    deck_beam_span_limit,
    deck_joist_span_limit,
    deck_post_height_limit,
    required_footing_area_ft2,
)
from typehaus.findings import Finding, Result
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import Beam, Pad, Post, Railing
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedFloor

_M_PER_FT = 0.3048
# The tables are published at 12/16/24" o.c.; a FloorSystem that leaves JoistSpec.spacing
# unset gets the solver's own default, which is the middle one.
_DEFAULT_SPACING_IN = 16.0




@dataclass(frozen=True)
class _Deck:
    """One authored ``service="deck"`` FloorSystem paired with what it resolved into."""

    authored: FloorSystem
    resolved: ResolvedFloor

    @property
    def tag(self) -> str:
        return self.authored.tag

    @property
    def spacing_in(self) -> float:
        spacing = self.authored.joists.spacing
        return spacing.inches if spacing is not None else _DEFAULT_SPACING_IN

    @property
    def joists(self) -> list:
        return [m for m in self.resolved.members if m.category == "joist"]

    @property
    def joist_span_ft(self) -> float | None:
        joists = self.joists
        return max(m.length_m for m in joists) / _M_PER_FT if joists else None

    @property
    def area_ft2(self) -> float | None:
        """Plan area of the deck, from its authored outline. Tributary areas divide this."""
        ring = [p.xy_m for p in self.authored.outline]
        if len(ring) < 3:
            return None
        return abs(_shoelace(ring)) / (_M_PER_FT ** 2)


def _shoelace(ring: list[tuple[float, float]]) -> float:
    total = 0.0
    for i, (x0, y0) in enumerate(ring):
        x1, y1 = ring[(i + 1) % len(ring)]
        total += x0 * y1 - x1 * y0
    return total / 2.0


def _decks(ctx: CheckContext) -> list[_Deck]:
    """Every authored deck that actually resolved, paired with its resolved floor."""
    by_tag = {f.tag: f for f in ctx.model.floors}
    out: list[_Deck] = []
    for element in ctx.plan.all_elements():
        if not isinstance(element, FloorSystem) or element.service != "deck":
            continue
        resolved = by_tag.get(element.tag)
        if resolved is not None:
            out.append(_Deck(element, resolved))
    return out


@check(Tier.STRUCTURAL, "structural.deck_joist_span")
def deck_joist_span(ctx: CheckContext) -> list[Finding]:
    """Deck joist span vs. AWC DCA6 Table 3A, at the deck's own o.c. spacing."""
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply; not an unknown
    out: list[Finding] = []
    for deck in decks:
        member = deck.authored.joists.member
        span_ft = deck.joist_span_ft
        if span_ft is None:
            out.append(_unknown("structural.deck_joist_span",
                                f"deck {deck.tag} resolved no joists to measure",
                                (deck.tag,)))
            continue
        limit = deck_joist_span_limit(member, deck.spacing_in)
        if limit is None:
            out.append(_unknown("structural.deck_joist_span",
                                f"no DCA6 Table 3A row for {member} at "
                                f"{deck.spacing_in:.0f}\" o.c.", (deck.tag,)))
            continue
        allowable, tabulated = limit
        at = (f"{tabulated:.0f}\" o.c." if abs(tabulated - deck.spacing_in) < 1e-9
              else f"the {tabulated:.0f}\" o.c. row (framed at {deck.spacing_in:.0f}\")")
        if span_ft > allowable + 1e-6:
            out.append(_advisory(
                "structural.deck_joist_span",
                f"deck {deck.tag} {member} joists span {span_ft:.2f}', past the "
                f"{allowable:.2f}' DCA6 Table 3A limit at {at}", (deck.tag,), Result.FAIL,
                fix_hint=("deepen the joist, tighten the spacing, or add a beam line to "
                          "shorten the span"),
            ))
        else:
            out.append(_advisory(
                "structural.deck_joist_span",
                f"deck {deck.tag} {member} joists span {span_ft:.2f}', within the "
                f"{allowable:.2f}' DCA6 Table 3A limit at {at}", (deck.tag,), Result.PASS,
            ))
    return out


def _deck_beams(ctx: CheckContext, deck: _Deck) -> list[Beam]:
    """The authored Beams a deck's joists bear on (walls/ledgers in bearing_refs are not
    beams and are governed by R507.9, not the beam-span table)."""
    beams: list[Beam] = []
    for ref in deck.authored.joists.bearing_refs:
        element = ctx.plan.by_tag(ref)
        if isinstance(element, Beam):
            beams.append(element)
    return beams


def _beam_span_ft(ctx: CheckContext, beam: Beam) -> float | None:
    """Clear-ish beam span: the distance between the posts it bears on, or — when the posts
    cannot be resolved — its own node-to-node length, which is the same thing for a beam
    that runs post to post."""
    posts = [ctx.plan.by_tag(ref) for ref in beam.bearing_refs]
    points = [p.position.xy_m for p in posts if isinstance(p, Post)]
    if len(points) >= 2:
        widest = max((x1 - x0) ** 2 + (y1 - y0) ** 2
                     for x0, y0 in points for x1, y1 in points) ** 0.5
        if widest > 1e-9:
            return widest / _M_PER_FT
    solid = next((s for s in ctx.model.solids if s.tag == beam.tag), None)
    if solid is None:
        return None
    ring = list(solid.outline)
    if len(ring) < 4:
        return None
    # The beam solid is a rectangle around its axis; its long side is the span.
    sides = [((ring[i][0] - ring[i - 1][0]) ** 2 + (ring[i][1] - ring[i - 1][1]) ** 2) ** 0.5
             for i in range(len(ring))]
    return max(sides) / _M_PER_FT


@check(Tier.STRUCTURAL, "structural.deck_beam_span")
def deck_beam_span(ctx: CheckContext) -> list[Finding]:
    """Deck beam span vs. IRC Table R507.5(1), indexed by the joist span the beam carries."""
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    out: list[Finding] = []
    for deck in decks:
        joist_span_ft = deck.joist_span_ft
        beams = _deck_beams(ctx, deck)
        if not beams:
            out.append(_unknown("structural.deck_beam_span",
                                f"deck {deck.tag} names no Beam in its joist bearing_refs",
                                (deck.tag,)))
            continue
        if joist_span_ft is None:
            out.append(_unknown("structural.deck_beam_span",
                                f"deck {deck.tag} resolved no joists, so no carried span",
                                (deck.tag,)))
            continue
        for beam in beams:
            span_ft = _beam_span_ft(ctx, beam)
            if span_ft is None:
                out.append(_unknown("structural.deck_beam_span",
                                    f"beam {beam.tag} has no resolvable span",
                                    (deck.tag, beam.tag)))
                continue
            limit = deck_beam_span_limit(beam.size, joist_span_ft)
            if limit is None:
                out.append(_unknown("structural.deck_beam_span",
                                    f"no IRC Table R507.5(1) row for a {beam.size} carrying "
                                    f"a {joist_span_ft:.2f}' joist span",
                                    (deck.tag, beam.tag)))
                continue
            allowable, tabulated = limit
            carried = (f"a {tabulated:.0f}' joist span"
                       if abs(tabulated - joist_span_ft) < 1e-9
                       else f"the {tabulated:.0f}' joist-span row "
                            f"(carrying {joist_span_ft:.2f}')")
            if span_ft > allowable + 1e-6:
                out.append(_advisory(
                    "structural.deck_beam_span",
                    f"deck {deck.tag} beam {beam.tag} ({beam.size}) spans {span_ft:.2f}', "
                    f"past the {allowable:.2f}' IRC Table R507.5(1) limit for {carried}",
                    (deck.tag, beam.tag), Result.FAIL,
                    fix_hint="add a post, add a ply, or deepen the beam",
                ))
            else:
                out.append(_advisory(
                    "structural.deck_beam_span",
                    f"deck {deck.tag} beam {beam.tag} ({beam.size}) spans {span_ft:.2f}', "
                    f"within the {allowable:.2f}' IRC Table R507.5(1) limit for {carried}",
                    (deck.tag, beam.tag), Result.PASS,
                ))
    return out


def _deck_posts(ctx: CheckContext, deck: _Deck) -> list[Post]:
    """Posts under a deck: whatever its beams name as bearing. De-duplicated by tag, since
    two beams may land on the same post."""
    seen: dict[str, Post] = {}
    for beam in _deck_beams(ctx, deck):
        for ref in beam.bearing_refs:
            element = ctx.plan.by_tag(ref)
            if isinstance(element, Post) and element.tag not in seen:
                seen[element.tag] = element
    return list(seen.values())


def _tributary_ft2(deck: _Deck, post_count: int) -> float | None:
    """Deck area divided evenly among its posts. The deck is a regular post grid, so this is
    the tributary area exactly; it would be an approximation on an irregular one, which is
    why the finding prints it."""
    area = deck.area_ft2
    if area is None or post_count <= 0:
        return None
    return area / post_count


@check(Tier.STRUCTURAL, "structural.deck_post_size")
def deck_post_size(ctx: CheckContext) -> list[Finding]:
    """Deck posts vs. IRC R507.4: minimum nominal size, and height capped by tributary area."""
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    out: list[Finding] = []
    for deck in decks:
        posts = _deck_posts(ctx, deck)
        if not posts:
            out.append(_unknown("structural.deck_post_size",
                                f"deck {deck.tag} resolves to no supporting posts",
                                (deck.tag,)))
            continue
        tributary = _tributary_ft2(deck, len(posts))
        if tributary is None:
            out.append(_unknown("structural.deck_post_size",
                                f"deck {deck.tag} has no outline to derive tributary area from",
                                (deck.tag,)))
            continue
        for post in posts:
            solid = next((s for s in ctx.model.solids if s.tag == post.tag), None)
            if solid is None:
                out.append(_unknown("structural.deck_post_size",
                                    f"post {post.tag} did not resolve", (deck.tag, post.tag)))
                continue
            height_ft = (solid.z1_m - solid.z0_m) / _M_PER_FT
            limit = deck_post_height_limit(post.size, tributary)
            if limit is None:
                out.append(_unknown("structural.deck_post_size",
                                    f"no IRC Table R507.4 row for a {post.size} post at "
                                    f"{tributary:.1f} ft2 tributary",
                                    (deck.tag, post.tag)))
                continue
            if post.size != MIN_DECK_POST_NOMINAL and height_ft > limit + 1e-6:
                undersize = f" (R507.4 wants {MIN_DECK_POST_NOMINAL} nominal minimum)"
            else:
                undersize = ""
            if height_ft > limit + 1e-6:
                out.append(_advisory(
                    "structural.deck_post_size",
                    f"deck {deck.tag} post {post.tag} ({post.size}) stands {height_ft:.2f}', "
                    f"past the {limit:.2f}' IRC Table R507.4 limit at {tributary:.1f} ft2 "
                    f"tributary{undersize}", (deck.tag, post.tag), Result.FAIL,
                    fix_hint="use a larger post section, or brace it",
                ))
            else:
                out.append(_advisory(
                    "structural.deck_post_size",
                    f"deck {deck.tag} post {post.tag} ({post.size}) stands {height_ft:.2f}', "
                    f"within the {limit:.2f}' IRC Table R507.4 limit at {tributary:.1f} ft2 "
                    f"tributary", (deck.tag, post.tag), Result.PASS,
                ))
    return out


@check(Tier.STRUCTURAL, "structural.deck_footing_size")
def deck_footing_size(ctx: CheckContext) -> list[Finding]:
    """Deck footing bearing area vs. IRC R507.3.1 — tributary load over soil bearing value."""
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    soil_psf = ctx.profile.soil_bearing_psf
    if soil_psf is None:
        return [_unknown("structural.deck_footing_size",
                         f"profile {ctx.profile.name} declares no soil bearing value, so a "
                         "footing cannot be sized")]
    out: list[Finding] = []
    for deck in decks:
        posts = _deck_posts(ctx, deck)
        tributary = _tributary_ft2(deck, len(posts))
        if tributary is None:
            out.append(_unknown("structural.deck_footing_size",
                                f"deck {deck.tag} has no tributary area to size footings from",
                                (deck.tag,)))
            continue
        required = required_footing_area_ft2(tributary, soil_psf)
        minimum = (MIN_DECK_FOOTING_SIDE_IN / 12.0) ** 2
        required = max(required, minimum)
        for post in posts:
            pad = ctx.plan.by_tag(post.supported_by) if post.supported_by else None
            # A post may stand on a concrete pier that in turn stands on the pad; follow one
            # link so the bearing chain post -> pier -> pad resolves like post -> pad.
            if isinstance(pad, Post) and pad.supported_by:
                pad = ctx.plan.by_tag(pad.supported_by)
            if not isinstance(pad, Pad):
                out.append(_unknown("structural.deck_footing_size",
                                    f"post {post.tag} does not bear on a resolvable Pad",
                                    (deck.tag, post.tag)))
                continue
            area_ft2 = abs(_shoelace([p.xy_m for p in pad.outline])) / (_M_PER_FT ** 2)
            thickness_in = pad.thickness.inches
            if area_ft2 + 1e-9 < required:
                out.append(_advisory(
                    "structural.deck_footing_size",
                    f"deck {deck.tag} pad {pad.tag} bears {area_ft2:.2f} ft2, under the "
                    f"{required:.2f} ft2 IRC R507.3.1 needs for {tributary:.1f} ft2 tributary "
                    f"at {DECK_TOTAL_LOAD_PSF:.0f} psf on {soil_psf:.0f} psf soil",
                    (deck.tag, pad.tag), Result.FAIL,
                    fix_hint="widen the pad, or add a post to cut the tributary area",
                ))
            elif thickness_in + 1e-9 < MIN_DECK_FOOTING_THICKNESS_IN:
                out.append(_advisory(
                    "structural.deck_footing_size",
                    f"deck {deck.tag} pad {pad.tag} bears enough area but is only "
                    f"{thickness_in:.1f}\" thick, under the "
                    f"{MIN_DECK_FOOTING_THICKNESS_IN:.0f}\" minimum",
                    (deck.tag, pad.tag), Result.FAIL,
                    fix_hint="thicken the pad to at least 6\"",
                ))
            else:
                out.append(_advisory(
                    "structural.deck_footing_size",
                    f"deck {deck.tag} pad {pad.tag} bears {area_ft2:.2f} ft2 on "
                    f"{soil_psf:.0f} psf soil, over the {required:.2f} ft2 IRC R507.3.1 "
                    f"needs for {tributary:.1f} ft2 tributary",
                    (deck.tag, pad.tag), Result.PASS,
                ))
    return out


@check(Tier.STRUCTURAL, "structural.deck_guard")
def deck_guard(ctx: CheckContext) -> list[Finding]:
    """IRC R312.1 — a walking surface more than 30" above the surface below needs a guard,
    and that guard has to be at least 36" tall."""
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown("structural.deck_guard",
                         "the site declares no grade datum to measure a drop against")]
    grade_m = grade.meters
    railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)]
    # A guard need not be a Railing. A masonry parapet standing at the edge is the same
    # fixture in R312.1 terms, and is authored as a Wall with ``guard=True`` so it keeps its
    # layer stack and its cubic-yard take-off (→ checks/structural/guards.py). Without this
    # the rule failed a deck that is guarded, for having no element of the one class it knew.
    guard_walls = [w for w in ctx.model.walls
                   if getattr(ctx.plan.by_tag(w.tag), "guard", False)]
    out: list[Finding] = []
    for deck in decks:
        joists = deck.joists
        if not joists:
            out.append(_unknown("structural.deck_guard",
                                f"deck {deck.tag} resolved no joists, so no walking surface",
                                (deck.tag,)))
            continue
        surface_m = max(m.z1_m for m in joists)
        drop_in = (surface_m - grade_m) / M_PER_IN
        if drop_in <= GUARD_REQUIRED_ABOVE_IN + 1e-9:
            out.append(_advisory(
                "structural.deck_guard",
                f"deck {deck.tag} walking surface is {drop_in:.1f}\" above grade, at or "
                f"under the {GUARD_REQUIRED_ABOVE_IN:.0f}\" IRC R312.1 guard threshold",
                (deck.tag,), Result.PASS,
            ))
            continue
        # A guard is required. It has to actually sit on this deck, at full height.
        on_deck = [r for r in railings
                   if abs(r.base_elevation.meters - surface_m) < 0.15]
        walls_on_deck = [w for w in guard_walls if abs(w.z0_m - surface_m) < 0.15]
        if not on_deck and not walls_on_deck:
            out.append(_advisory(
                "structural.deck_guard",
                f"deck {deck.tag} walking surface is {drop_in:.1f}\" above grade and has no "
                f"Railing at that elevation; IRC R312.1 requires a guard over "
                f"{GUARD_REQUIRED_ABOVE_IN:.0f}\"", (deck.tag,), Result.FAIL,
                fix_hint="author a Railing along the deck's open edges",
            ))
            continue
        # Heights, in inches, keyed by tag — a Railing states one and a guard wall's is the
        # run of its own resolved prism, so the two are measured the same way from here on.
        heights = {r.tag: r.height.inches for r in on_deck}
        heights.update({w.tag: (w.z1_m - w.z0_m) / M_PER_IN for w in walls_on_deck})
        short = sorted(tag for tag, tall in heights.items()
                       if tall + 1e-9 < GUARD_MIN_HEIGHT_IN)
        if short:
            out.append(_advisory(
                "structural.deck_guard",
                f"deck {deck.tag} guard {short[0]} is {heights[short[0]]:.0f}\" "
                f"tall, under the {GUARD_MIN_HEIGHT_IN:.0f}\" IRC R312.1 minimum",
                (deck.tag, short[0]), Result.FAIL,
                fix_hint=f"raise the guard to at least {GUARD_MIN_HEIGHT_IN:.0f}\"",
            ))
        else:
            out.append(_advisory(
                "structural.deck_guard",
                f"deck {deck.tag} is {drop_in:.1f}\" above grade and guarded by "
                f"{', '.join(sorted(heights))} at {min(heights.values()):.0f}\" or more",
                (deck.tag, *sorted(heights)), Result.PASS,
            ))
    return out
