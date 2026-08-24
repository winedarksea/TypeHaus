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
    MAX_JOIST_CANTILEVER_RATIO,
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
from typehaus.model.structure import Beam, GlazingPanel, Pad, Post, Railing
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedFloor

_M_PER_FT = 0.3048
# The tables are published at 12/16/24" o.c.; a FloorSystem that leaves JoistSpec.spacing
# unset gets the solver's own default, which is the middle one.
_DEFAULT_SPACING_IN = 16.0
# Slop for "is this member tip on the joist field's outer edge", in metres. The tips are
# built by adding the authored cantilever to a bearing coordinate, so they agree to
# floating-point noise; a micron is far tighter than any real framing dimension.
_TOL_M = 1e-6




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
    def _axis(self) -> int:
        """Index into a member point of the joists' own span direction."""
        return 0 if (self.authored.joists.direction or "x") == "x" else 1

    @property
    def cantilevers_ft(self) -> tuple[float, float]:
        """The authored overhang past the low / high outermost bearing lines, in feet.

        Mirrors ``resolve/floors.py``: each per-end value falls back to the symmetric
        ``JoistSpec.cantilever`` scalar, and a deck that authors none has no overhang.
        """
        spec = self.authored.joists
        base = spec.cantilever.meters if spec.cantilever is not None else 0.0
        start = spec.cantilever_start.meters if spec.cantilever_start is not None else base
        end = spec.cantilever_end.meters if spec.cantilever_end is not None else base
        return start / _M_PER_FT, end / _M_PER_FT

    @property
    def joist_span_ft(self) -> float | None:
        """The joists' longest SPAN — bearing line to bearing line, cantilever excluded.

        A cantilever is not span, and both tables this module reads are span tables:
        DCA6 Table 3A is entered with the backspan (R507.6.1 limits the overhang
        separately, at a quarter of it — see ``deck_joist_cantilever`` below), and IRC
        Table R507.5(1) is indexed by the joist span a beam carries.

        ``resolve/floors.py`` adds the overhang to the two outer bays only, one end each,
        so a member is carrying a cantilever exactly when one of its tips sits on the
        joist field's outer extent. Reading it back off the geometry that way — rather
        than off the member key — keeps this correct for a deck of any bay count,
        including the single-bay case that cantilevers at both ends.
        """
        joists = self.joists
        if not joists:
            return None
        axis = self._axis
        ends = [sorted((m.p0[axis], m.p1[axis])) for m in joists]
        low = min(a for a, _ in ends)
        high = max(b for _, b in ends)
        start_ft, end_ft = self.cantilevers_ft
        spans = []
        for (a, b), member in zip(ends, joists, strict=True):
            span_ft = member.length_m / _M_PER_FT
            if abs(a - low) < _TOL_M:
                span_ft -= start_ft
            if abs(b - high) < _TOL_M:
                span_ft -= end_ft
            spans.append(span_ft)
        return max(spans)

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


@check(Tier.STRUCTURAL, "structural.deck_joist_cantilever")
def deck_joist_cantilever(ctx: CheckContext) -> list[Finding]:
    """Deck joist overhang vs. IRC R507.6.1 — not more than a quarter of the back span.

    The companion to :func:`deck_joist_span`. That check reads DCA6 Table 3A against the
    backspan, which is what a span table means; this is where the overhang it excludes is
    actually bounded. Splitting them the way the code does is what keeps a long cantilever
    from disappearing out of both.
    """
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    out: list[Finding] = []
    for deck in decks:
        start_ft, end_ft = deck.cantilevers_ft
        overhang_ft = max(start_ft, end_ft)
        if overhang_ft <= 1e-9:
            continue  # flush both ends — nothing to bound
        span_ft = deck.joist_span_ft
        if span_ft is None or span_ft <= 1e-9:
            out.append(_unknown("structural.deck_joist_cantilever",
                                f"deck {deck.tag} cantilevers {overhang_ft:.2f}' past a "
                                f"back span that did not resolve", (deck.tag,)))
            continue
        allowable = span_ft * MAX_JOIST_CANTILEVER_RATIO
        if overhang_ft > allowable + 1e-6:
            out.append(_advisory(
                "structural.deck_joist_cantilever",
                f"deck {deck.tag} joists cantilever {overhang_ft:.2f}', past the "
                f"{allowable:.2f}' IRC R507.6.1 limit (a quarter of the {span_ft:.2f}' "
                f"back span)", (deck.tag,), Result.FAIL,
                fix_hint="shorten the overhang or move the outer bearing line out under it",
            ))
        else:
            out.append(_advisory(
                "structural.deck_joist_cantilever",
                f"deck {deck.tag} joists cantilever {overhang_ft:.2f}', within the "
                f"{allowable:.2f}' IRC R507.6.1 limit (a quarter of the {span_ft:.2f}' "
                f"back span)", (deck.tag,), Result.PASS,
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


# --- Enclosure ---------------------------------------------------------------------
#
# R312.1 asks for a guard at an *open* side. A side that is closed floor-to-head by the
# building's own construction is not an open side, and a rail inside a glazed wall is not
# a code requirement — it is a rail inside a wall. Until this existed the rule measured
# nothing but height, so catlin's breezeway vestibule — 30" up, four sides closed by two
# buildings and two 8' glazed walls — sat one inch of grade away from a FAIL that no
# amount of correct design could clear.
#
# What counts as closing an edge is deliberately narrow: a ``Wall`` (its own layers, its
# own height) or a vertical ``GlazingPanel`` (the free-standing sheet idiom, which is what
# a post-and-beam enclosure is actually built from). Both have to stand *on the edge line*
# and *through the walking surface*, which is what the two tolerances below mean.
_ENCLOSURE_LATERAL_TOL_FT = 1.0
# How far off the edge's line a closing element may stand and still be that edge's
# enclosure. A wall closes the edge from behind its cladding, and a glazed wall stands
# just outside the deck it sits on, so the two planes are never exactly coincident:
# catlin's are 2 3/4" (the glazing) and 7 3/4" (the house wall, measured to its axis)
# away. A foot is generous enough for a thick wall read to its centreline and tight
# enough that a wall in the next room cannot close anything.
_ENCLOSURE_END_TOL_FT = 0.25
# Slack at each end of an edge before the remainder reads as an open gap. Three inches:
# smaller than any opening a person falls through, larger than the corner rounding a
# post-to-cladding joint leaves behind.


def _seg_encloses_edge(seg: tuple[tuple[float, float], tuple[float, float]],
                       edge: tuple[tuple[float, float], tuple[float, float]],
                       ) -> tuple[float, float] | None:
    """The stretch of ``edge`` that ``seg`` stands along, as a 0..1 parameter interval.

    ``None`` when ``seg`` is not on this edge at all — either it runs across the edge
    rather than along it, or it stands further off than ``_ENCLOSURE_LATERAL_TOL_FT``.
    """
    (ex0, ey0), (ex1, ey1) = edge
    dx, dy = ex1 - ex0, ey1 - ey0
    edge_len = (dx * dx + dy * dy) ** 0.5
    if edge_len <= 1e-9:
        return None
    ux, uy = dx / edge_len, dy / edge_len
    lateral_tol = _ENCLOSURE_LATERAL_TOL_FT * _M_PER_FT
    span: list[float] = []
    for px, py in seg:
        rx, ry = px - ex0, py - ey0
        if abs(-uy * rx + ux * ry) > lateral_tol:
            return None  # off the edge's line, or crossing it
        span.append((rx * ux + ry * uy) / edge_len)
    lo, hi = min(span), max(span)
    lo, hi = max(0.0, lo), min(1.0, hi)
    return (lo, hi) if hi > lo else None


def _open_edges(ctx: CheckContext, deck: _Deck, surface_m: float) -> list[int] | None:
    """Indices of the deck outline's edges that nothing closes.

    ``None`` when the deck authors no outline — its footprint is then the storey's wall
    bbox, which is not a set of edges anyone can reason about, so enclosure is simply not
    knowable and the caller falls back to the height rule alone.
    """
    outline = [point.xy_m for point in deck.authored.outline]
    if len(outline) < 3:
        return None
    # A closer has to stand through the walking surface and reach guard height above it:
    # a skirt below the deck closes nothing you can fall over, and neither does a parapet
    # whose top is at your ankle. Segments are plan runs, paired with (base, top).
    closers: list[tuple[tuple[tuple[float, float], tuple[float, float]], float, float]] = []
    for wall in ctx.model.walls:
        top = max(wall.top_z0_m or wall.z1_m, wall.top_z1_m or wall.z1_m)
        closers.append(((wall.axis[0], wall.axis[1]), wall.z0_m, top))
    for element in ctx.plan.all_elements():
        if not isinstance(element, GlazingPanel) or element.plane != "vertical":
            continue
        if element.base_elevation is None or len(element.outline) < 2:
            continue
        run = [point.xy_m for point in element.outline]
        closers.append(((run[0], run[-1]), element.base_elevation.meters,
                        element.top_elevation.meters))
    guard_top_m = surface_m + GUARD_MIN_HEIGHT_IN * M_PER_IN
    standing = [seg for seg, base, top in closers
                if base <= surface_m + 1e-6 and top + 1e-6 >= guard_top_m]

    open_edges: list[int] = []
    for index in range(len(outline)):
        edge = (outline[index], outline[(index + 1) % len(outline)])
        edge_len = (((edge[1][0] - edge[0][0]) ** 2
                     + (edge[1][1] - edge[0][1]) ** 2) ** 0.5)
        if edge_len <= 1e-9:
            continue
        # Union the covered stretches before measuring the gap: catlin's south edge is
        # closed by two house walls that meet mid-edge, and neither one covers it alone.
        spans = sorted(span for seg in standing
                       if (span := _seg_encloses_edge(seg, edge)) is not None)
        end_tol = _ENCLOSURE_END_TOL_FT * _M_PER_FT / edge_len
        cursor = 0.0
        for lo, hi in spans:
            if lo > cursor + end_tol:
                break
            cursor = max(cursor, hi)
        if cursor < 1.0 - end_tol:
            open_edges.append(index)
    return open_edges


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
            # Before failing it for having no guard, ask whether it has an open edge at
            # all. R312.1 guards *open* sides; a fully enclosed walking surface has none.
            open_edges = _open_edges(ctx, deck, surface_m)
            if open_edges is not None and not open_edges:
                out.append(_advisory(
                    "structural.deck_guard",
                    f"deck {deck.tag} walking surface is {drop_in:.1f}\" above grade but "
                    f"every edge of its outline is closed to at least "
                    f"{GUARD_MIN_HEIGHT_IN:.0f}\" by a wall or a vertical glazing panel, "
                    f"so IRC R312.1 has no open side to guard",
                    (deck.tag,), Result.PASS,
                ))
                continue
            where = ("" if not open_edges
                     else f" ({len(open_edges)} of its outline edges stand open)")
            out.append(_advisory(
                "structural.deck_guard",
                f"deck {deck.tag} walking surface is {drop_in:.1f}\" above grade and has no "
                f"Railing at that elevation{where}; IRC R312.1 requires a guard over "
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
