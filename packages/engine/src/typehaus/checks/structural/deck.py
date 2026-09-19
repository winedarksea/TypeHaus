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

import math
from dataclasses import dataclass

from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import not_applicable
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.guard_lines import guard_lines
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.deck_tables import (
    DECK_DEAD_LOAD_PSF,
    DECK_TOTAL_LOAD_PSF,
    GUARD_MIN_HEIGHT_IN,
    GUARD_REQUIRED_ABOVE_IN,
    MAX_BEAM_CANTILEVER_RATIO,
    MAX_JOIST_CANTILEVER_RATIO,
    MIN_DECK_FOOTING_SIDE_IN,
    MIN_DECK_FOOTING_THICKNESS_IN,
    MIN_DECK_POST_NOMINAL,
    deck_beam_span_limit,
    deck_joist_span_limit,
    deck_post_height_limit,
    required_footing_area_ft2,
)
from typehaus.engineering import item_id
from typehaus.findings import Finding, Result
from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.structure import Beam, GlazingPanel, Pad, Post
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


@check(Tier.STRUCTURAL, "structural.deck_beam_cantilever")
def deck_beam_cantilever(ctx: CheckContext) -> list[Finding]:
    """Deck BEAM overhang vs. IRC R507.5.1 — not more than a quarter of the back span.

    The sibling of :func:`deck_joist_cantilever`, and it did not exist. R507.5.1 bounds a
    beam's overhang past its end bearing exactly as R507.6.1 bounds a joist's, and the
    north entry landing broke it by 67% with nothing looking: two beams running 10'-4 3/8"
    over bearings 6'-2 1/2" apart, the 4'-1 7/8" tail carrying a stair landing 34" up.

    Measured from the OUTERMOST resolved bearings, so a beam continuous over three supports
    is graded on the tail past the last one, not on an interior bay.
    """
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    out: list[Finding] = []
    seen: set[str] = set()
    for deck in decks:
        for beam in _deck_beams(ctx, deck):
            if beam.tag in seen:
                continue  # a beam under two decks is still one beam
            seen.add(beam.tag)
            axis = _beam_axis_m(ctx, beam)
            points = _bearing_points_m(ctx, beam)
            if axis is None or len(points) < 2:
                out.append(_unknown(
                    "structural.deck_beam_cantilever",
                    f"beam {beam.tag} resolved fewer than two bearing points, so no "
                    f"overhang can be measured", (deck.tag, beam.tag)))
                continue
            # Along the beam's own axis: everything here is a 1-D question on that line.
            (x0, y0), (x1, y1) = axis
            length = math.dist((x0, y0), (x1, y1))
            ux, uy = (x1 - x0) / length, (y1 - y0) / length
            offsets = sorted((px - x0) * ux + (py - y0) * uy for px, py in points)
            back_span_ft = (offsets[-1] - offsets[0]) / _M_PER_FT
            overhang_ft = max(offsets[0] - 0.0, length - offsets[-1]) / _M_PER_FT
            if overhang_ft <= 1e-6:
                continue  # ends flush on its bearings — nothing to bound
            if back_span_ft <= 1e-9:
                out.append(_unknown(
                    "structural.deck_beam_cantilever",
                    f"beam {beam.tag} overhangs {overhang_ft:.2f}' past a back span that "
                    f"did not resolve", (deck.tag, beam.tag)))
                continue
            allowable = back_span_ft * MAX_BEAM_CANTILEVER_RATIO
            passing = overhang_ft <= allowable + 1e-6
            out.append(_advisory(
                "structural.deck_beam_cantilever",
                f"deck {deck.tag} beam {beam.tag} overhangs {overhang_ft:.2f}', "
                f"{'within' if passing else 'past'} the {allowable:.2f}' IRC R507.5.1 "
                f"limit (a quarter of the {back_span_ft:.2f}' back span)",
                (deck.tag, beam.tag), Result.PASS if passing else Result.FAIL,
                fix_hint=None if passing else
                "post the tip, or move the end bearing out under the overhang",
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


def _beam_axis_m(ctx: CheckContext, beam: Beam) -> tuple[tuple[float, float],
                                                          tuple[float, float]] | None:
    """The beam's plan centreline, from its two authored nodes."""
    start, end = ctx.plan.by_tag(beam.start_node), ctx.plan.by_tag(beam.end_node)
    if start is None or end is None:
        return None
    p0, p1 = start.position.xy_m, end.position.xy_m
    return None if math.dist(p0, p1) < 1e-9 else (p0, p1)


def _bearing_points_m(ctx: CheckContext, beam: Beam) -> list[tuple[float, float]]:
    """Where, in plan, each of ``beam``'s bearing refs actually holds it up.

    A Post holds it at a point, which is its position. **A Beam holds it where the two
    cross**, and that is the case this used to miss: ``BM-BW-FC`` bears on two seat beams,
    resolved no Posts at all, and fell through to the solid's long side — reporting its
    whole 10'-4 3/8" node-to-node LENGTH as a span against a table row for 6'-10". A length
    is not a span, and the difference here is a cantilever nothing else was grading.

    The same fallback ``resolve/floors.py::_bearing_axis`` already makes for a joist
    bearing, one element up. A wall in ``bearing_refs`` is deliberately not a point: it is
    a ledger, governed by R507.9, and ``_deck_beams`` says so.
    """
    from shapely.geometry import LineString
    from shapely.ops import nearest_points

    axis = _beam_axis_m(ctx, beam)
    out: list[tuple[float, float]] = []
    for ref in beam.bearing_refs:
        element = ctx.plan.by_tag(ref)
        if isinstance(element, Post):
            out.append(element.position.xy_m)
            continue
        if axis is None:
            continue
        if isinstance(element, Beam):
            other = _beam_axis_m(ctx, element)
        else:
            wall = ctx.model.wall(ref)
            other = None if wall is None else (wall.axis[0], wall.axis[1])
        if other is None or _parallel(axis, other):
            # A support running ALONGSIDE the beam holds it everywhere or nowhere — it is a
            # ledger condition (R507.9), not a point bearing, and picking the "nearest"
            # point on a parallel line would be picking an arbitrary one.
            continue
        # The point on THIS beam nearest the carrying member: their crossing where they
        # cross, the seat where one lands on the side of the other.
        near, _ = nearest_points(LineString(axis), LineString(other))
        out.append((near.x, near.y))
    return out


def _parallel(a: tuple[tuple[float, float], tuple[float, float]],
              b: tuple[tuple[float, float], tuple[float, float]]) -> bool:
    """Within about 5 degrees, by the normalised cross product of the two directions."""
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    la, lb = math.dist((ax0, ay0), (ax1, ay1)), math.dist((bx0, by0), (bx1, by1))
    if la < 1e-9 or lb < 1e-9:
        return False
    cross = ((ax1 - ax0) * (by1 - by0) - (ay1 - ay0) * (bx1 - bx0)) / (la * lb)
    return abs(cross) < 0.087


def _beam_span_ft(ctx: CheckContext, beam: Beam) -> float | None:
    """Clear-ish beam span: the distance between the bearings it stands on, or — when they
    cannot be resolved — its own node-to-node length, which is the same thing for a beam
    that runs bearing to bearing and an OVER-count for one that cantilevers past them."""
    axis = _beam_axis_m(ctx, beam)
    points = _bearing_points_m(ctx, beam)
    if axis is not None and len(points) >= 2:
        # The LONGEST BAY, not end to end. A beam continuous over three supports spans each
        # bay separately; measuring corner to corner would report a 9'-7 5/8" span for a
        # beam whose worst bay is 5'-5 3/4", and R507.5(1) would fail it for a span it does
        # not have. Ordered along the beam's own axis, so "adjacent" means adjacent.
        (x0, y0), (x1, y1) = axis
        length = math.dist((x0, y0), (x1, y1))
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        offsets = sorted((px - x0) * ux + (py - y0) * uy for px, py in points)
        widest = max(b - a for a, b in zip(offsets, offsets[1:], strict=False))
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
                # Off the end of R507.5(1) — a glulam, an LVL, or a joist span the table
                # stops short of. The IRC not publishing a row does not mean nobody does:
                # the beam's own supplier tabulates it, and reading that table is a
                # prescriptive act (2026-09-11; it was an engineering item before).
                out.extend(_off_table_beam(ctx, deck, beam, span_ft, joist_span_ft))
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


def _delivered_to_posts(ctx: CheckContext, supports: tuple[str, ...],
                        depth: int = 0) -> dict[str, float]:
    """``post tag -> fraction of one beam's load`` that actually reaches a Post.

    ** A LOAD PATH CAN BE MORE THAN ONE BEAM DEEP. ** The north entry landing's joists bear
    on three floor beams, those bear on two SEAT beams, and only the seats bear on piers.
    Stopping one level down and keeping whatever happened to be a Post handed the whole
    landing to the two posts under the interior cantilever and gave the four piers carrying
    it nothing. A support that is itself a Beam passes its share on to ITS supports.

    A support that is neither (a bearing wall, a pier direct) keeps its share and falls out
    here, so the fractions deliberately need not sum to 1.

    **The twin of ``engineering/pier_basis.py::_delivered_to_posts``**, and deliberately a
    restatement rather than an import: ``engineering`` may not import ``checks``. If one
    moves, MOVE THE OTHER — ``test_pier_calcs.py::test_the_two_tributary_rules_agree`` is
    what notices when they drift, and it has.
    """
    out: dict[str, float] = {}
    if not supports or depth > 4:
        return out
    each = 1.0 / len(supports)
    for tag in supports:
        element = ctx.plan.by_tag(tag)
        if isinstance(element, Post):
            out[tag] = out.get(tag, 0.0) + each
        elif isinstance(element, Beam):
            for post, fraction in _delivered_to_posts(
                    ctx, tuple(element.bearing_refs or ()), depth + 1).items():
                out[post] = out.get(post, 0.0) + each * fraction
    return out


def _deck_posts(ctx: CheckContext, deck: _Deck) -> list[Post]:
    """Posts under a deck: whatever its beams deliver to, down the whole beam chain.
    De-duplicated by tag, since two beams may land on the same post."""
    seen: dict[str, Post] = {}
    for beam in _deck_beams(ctx, deck):
        for tag in _delivered_to_posts(ctx, tuple(beam.bearing_refs or ())):
            element = ctx.plan.by_tag(tag)
            if isinstance(element, Post) and element.tag not in seen:
                seen[element.tag] = element
    return list(seen.values())


def _beam_length_ft(ctx: CheckContext, beam: Beam) -> float | None:
    """A beam's full node-to-node length, cantilever tips included.

    Not ``_beam_span_ft``: what a beam delivers to its posts is everything standing on it,
    and an overhang past the end bearing is part of that load even though it is not span.
    """
    nodes = {e.tag: e.position.xy_m  # type: ignore[attr-defined]
             for e in ctx.plan.all_elements() if e.element_kind == "Node"}
    p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
    if p0 is None or p1 is None:
        return None
    return math.dist(p0, p1) / _M_PER_FT


def _tributaries_ft2(ctx: CheckContext, deck: _Deck) -> dict[str, float] | None:
    """``post tag -> tributary ft2``, weighted by the strip of deck each BEAM carries.

    An equal ``area / len(posts)`` split is right only on a regular grid with one post per
    bay corner, and catlin's balcony is not that: its centre beam runs the full depth of the
    deck onto two posts while the two edge beams share four, so the even split under-reported
    the centre pair by about a half. That mattered — those two are the pillars whose bearing
    ``engineering/post_bearing.py`` now grades, and a tributary that is 2/3 of the truth is a
    demand that is 2/3 of the truth.

    The weighting reuses the strip that already exists rather than opening a fourth opinion
    about deck loads: ``joist_span_ft`` is the width of deck a beam carries — the same figure
    ``engineering/glulam_beam.py`` puts under its 500 plf — so a beam's share of the deck is
    that strip times its own length, divided among the supports it names and kept where
    that support is a post. Each beam takes the
    FULL joist span, which double-counts where two beams' strips overlap; that is the
    conservative direction and it is the same over-count ``glulam_beam``'s record prints and
    invites a reviewer to disagree with.

    The even split survives as the fallback for a deck with no resolvable strip or a beam
    with no resolvable length, so nothing that graded before stops grading.
    """
    posts = _deck_posts(ctx, deck)
    area = deck.area_ft2
    if not posts:
        return None
    fallback = ({p.tag: area / len(posts) for p in posts}
                if area is not None else None)
    strip_ft = deck.joist_span_ft
    if strip_ft is None:
        return fallback
    out: dict[str, float] = {p.tag: 0.0 for p in posts}
    for beam in _deck_beams(ctx, deck):
        length_ft = _beam_length_ft(ctx, beam)
        if length_ft is None:
            return fallback
        # Divided among ALL the beam's supports and then kept only where a support is a
        # POST. A porch beam that runs from a column to a bearing WALL delivers half its
        # load to each, and a split that counted only the posts would hand the column the
        # wall's half as well.
        supports = tuple(beam.bearing_refs or ())
        if not supports:
            return fallback
        share = strip_ft * length_ft
        for tag, fraction in _delivered_to_posts(ctx, supports).items():
            out[tag] = out.get(tag, 0.0) + share * fraction
    return out


@check(Tier.STRUCTURAL, "structural.deck_post_size")
def deck_post_size(ctx: CheckContext) -> list[Finding]:
    """Deck posts vs. IRC R507.4: maximum height by post size (tributary area is reported)."""
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
        tributaries = _tributaries_ft2(ctx, deck)
        if tributaries is None:
            out.append(_unknown("structural.deck_post_size",
                                f"deck {deck.tag} has no outline to derive tributary area from",
                                (deck.tag,)))
            continue
        for post in posts:
            tributary = tributaries.get(post.tag, 0.0)
            solid = next((s for s in ctx.model.solids if s.tag == post.tag), None)
            if solid is None:
                out.append(_unknown("structural.deck_post_size",
                                    f"post {post.tag} did not resolve", (deck.tag, post.tag)))
                continue
            height_ft = (solid.z1_m - solid.z0_m) / _M_PER_FT
            limit = deck_post_height_limit(post.size, tributary)
            if limit is None:
                # Off the end of R507.4 — a round column, or a tributary the table stops
                # short of. The table not publishing a row is not the same as the post
                # being wrong, and it is not something an author can fix by editing the
                # model: it is a column design, so it is delegated as one.
                out.append(_engineered(
                    ctx, "structural.deck_post_size", item_id("deck_post", post.tag),
                    f"no IRC Table R507.4 row for a {post.size} post at "
                    f"{tributary:.1f} ft2 tributary",
                    (deck.tag, post.tag), code="IRC R507.4"))
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


@check(Tier.STRUCTURAL, "structural.deck_post_bearing")
def deck_post_bearing(ctx: CheckContext) -> list[Finding]:
    """A post standing on FRAMING vs. NDS §3.10 — compression perpendicular to grain.

    The gap this closes: ``structural.deck_post_size`` grades a post's SECTION and R507.4's
    height limit, ``structural.deck_footing_size`` grades what is under it *on the ground*,
    and neither has anything to say about a 6x6 landing on the flat of a 2x8. Cross-grain
    bearing is the limit state that actually governs there, and ``landing_post_bearing`` —
    the rule that says so elsewhere — is scoped to resolver-generated stair landing posts
    and never sees an authored ``Post``. Until 2026-09-03 catlin's two centre balcony
    pillars were over on that limit state at 0 FAIL.

    Delegated rather than tabulated: there is no prescriptive table for it. NDS §3.10 is a
    calculation, so it is an engineered item (decision #65) and the record carries the
    numbers a reviewer can disagree with.
    """
    posts = [e for e in ctx.plan.all_elements() if isinstance(e, Post)]
    floors = {e.tag for e in ctx.plan.all_elements() if isinstance(e, FloorSystem)}
    on_framing = [p for p in posts
                  if p.supported_by in floors and not p.within_wall]
    if not on_framing:
        # Earned, not assumed: there ARE posts here and not one of them stands on a floor
        # system — every one is on a pad, a footing, a wall or inside one. A house with no
        # post at all is the same statement one step weaker, and both are the absence this
        # rule governs rather than a rule that quietly found nothing to do.
        return [not_applicable(
            "structural.deck_post_bearing",
            f"no post in this plan stands on a floor system ({len(posts)} post(s) resolve, "
            f"all of them on a pad, a footing, a wall, or inside one) — NDS §3.10's "
            f"cross-grain bearing has no wood-on-wood post joint to grade",
            (), code="AWC NDS 2018 §3.10")]
    return [_engineered(
        ctx, "structural.deck_post_bearing", item_id("post_bearing", post.tag),
        f"post {post.tag} ({post.size}) stands on {post.supported_by}, framing rather than "
        f"a pour — what it bears through is joist stock across the grain, which no "
        f"prescriptive table publishes",
        (post.tag, post.supported_by or ""), code="AWC NDS 2018 §3.10")
        for post in sorted(on_framing, key=lambda p: p.tag)]


#: How far a ``supported_by`` chain is followed before it is treated as a loop. A post on a
#: post on a post is already unusual; anything past this is authored in error.
_BEARING_CHAIN_LIMIT = 6


def _bearing_of(ctx: CheckContext, post: Post) -> tuple[object, tuple[str, ...]]:
    """Walk ``supported_by`` to whatever finally carries this post, and how it got there.

    Following the whole chain — not just one ``Post -> Post`` link ending at a ``Pad`` — lets
    ``PT-SG-BF2 -> PT-SG-FCOL -> FT-SG-FCOL`` (a post on a column on a bell) and
    ``PT-SG-BR1 -> W-SG-W1`` (a pillar on a foundation wall with its own strip footing) both
    report what they actually bear on, rather than "does not bear on a resolvable Pad" — a
    sentence about the CHECK's reach dressed up as a fact about the model.

    Returns the last element in the chain and the tags it passed through, so the finding can
    quote the evidence rather than assert a conclusion.
    """
    seen: list[str] = []
    current: object = post
    for _ in range(_BEARING_CHAIN_LIMIT):
        ref = getattr(current, "supported_by", None)
        if not ref or ref in seen:
            break
        seen.append(ref)
        nxt = ctx.plan.by_tag(ref)
        if nxt is None:
            break
        current = nxt
        if not isinstance(current, Post):
            break
    return (current if current is not post else None), tuple(seen)


def _hands_over(ctx: CheckContext, chain: tuple[str, ...]) -> bool:
    """Does this post stand on ANOTHER POST, and so hand its load over at that joint?

    ** ASKED BEFORE THE PAD TEST, AND THAT ORDER IS THE WHOLE POINT. ** This lived inside
    ``_not_a_pad``, which is only reached when the chain does NOT end at a ``Pad`` — so the
    day ``PT-BW-W`` became a Pad, ``PT-BW-CW`` standing on it stopped being N/A and started
    reporting a PASS on that same pad. The pad was then graded twice: once against the pier's
    own tributary and once against the wood column's, two answers about one pour, and the
    second of them silently ignoring everything the first had already put on it.

    The first hop is the tell — what the post is authored to stand on, before the chain is
    followed any further — and it is a fact about the LOAD PATH, not about what happens to be
    at the bottom of it.
    """
    from typehaus.model.structure import Post as _Post

    return bool(chain) and isinstance(ctx.plan.by_tag(chain[0]), _Post)


def _not_a_pad(ctx: CheckContext, carried_tag: str, post: Post, bearing: object,
               chain: tuple[str, ...]) -> Finding:
    """The verdict for a post that does not land on a ``Pad``. Three different verdicts.

    **N/A is earned here from positive evidence of absence, never from the check running
    out of road.** ``Result.NOT_APPLICABLE`` means "the condition this rule governs does not
    exist in this building", and IRC R507.3.1 governs a deck post bearing on its own spread
    footing over soil. A post that lands on a foundation wall, or on a floor system, or on
    another post, is not that condition — the load leaves through something with its own
    footing, checked by its own rule. Saying so is a verdict.

    A post on a ``Footing`` IS the governed condition and is not N/A: it bears on soil like
    any deck post. R507.3's table just has no row for a 30"/36" belled pier, so it stays an
    engineered item — which is the branch this function was written for and the only one
    that survives from the original.
    """
    from typehaus.model.structure import Footing, FoundationWall

    where = " -> ".join(chain) if chain else "nothing"
    # A post standing on ANOTHER POST hands its load over at that joint, and the item that
    # covers the bearing is the other post's. Minting `spread_footing/PT-SG-BF2` would name a
    # spread footing that does not exist and ask a consultant to design it twice — once under
    # the pillar and again under the column it actually shares. The tell is the FIRST hop:
    # what this post is authored to stand on, before the chain is followed any further.
    first = ctx.plan.by_tag(chain[0]) if chain else None
    if isinstance(first, Post):
        # ** NAME WHAT ACTUALLY CARRIES IT, WHICH IS NOT ALWAYS AN ENGINEERED ITEM. ** This
        # sentence used to read "spread_footing/<the post below>" unconditionally, which was
        # true while every pier in this house stood on a belled `Footing`. Since 2026-09-14
        # some stand on a `Pad` and are graded prescriptively right here, and pointing a
        # reader at a `spread_footing/` item that does not exist is worse than vague.
        if isinstance(bearing, Pad):
            answer = (f"What carries both is {first.tag}'s own bearing on {bearing.tag}, "
                      f"graded in this same rule — and the share this post hands down is "
                      f"already in that tributary")
        else:
            answer = (f"What carries both is spread_footing/{first.tag}, and that item's "
                      f"bearing design has to include this post's share")
        return not_applicable(
            "structural.deck_footing_size",
            f"post {post.tag} bears on {first.tag}, another post ({where}) — its load leaves "
            f"through that column, so IRC R507.3.1 has no separate footing to size here. "
            f"{answer}",
            (carried_tag, post.tag, first.tag), code="IRC R507.3")
    if isinstance(bearing, FoundationWall):
        return not_applicable(
            "structural.deck_footing_size",
            f"post {post.tag} bears on {bearing.tag}, a foundation wall with its own strip "
            f"footing ({where}) — IRC R507.3.1 sizes a deck post's own spread footing over "
            f"soil, and this load path has none. The wall's footing is graded by "
            f"structural.foundation_unbalanced_fill and structural.frost_depth",
            (carried_tag, post.tag, bearing.tag), code="IRC R507.3")
    if isinstance(bearing, FloorSystem):
        return not_applicable(
            "structural.deck_footing_size",
            f"post {post.tag} bears on {bearing.tag}, a floor system ({where}) — it is a "
            f"post on a deck, not a post on the ground, so IRC R507.3.1 has no footing to "
            f"size. What carries it is graded by structural.deck_post_bearing (the "
            f"cross-grain bearing at the joint itself), by structural.cantilever_point_load "
            f"and by the joist span checks",
            (carried_tag, post.tag, bearing.tag), code="IRC R507.3")
    if isinstance(bearing, Footing):
        return _engineered(
            ctx, "structural.deck_footing_size",
            item_id("spread_footing", post.tag),
            f"post {post.tag} bears on {bearing.tag}, a {bearing.width.inches:.0f}\" "
            f"Footing rather than a Pad ({where}) — a belled pier, which IRC Table R507.3.1's "
            f"flat-pad rows do not publish. Its bearing is a design against the site's own "
            f"allowable pressure, not a lookup",
            (carried_tag, post.tag, bearing.tag), code="IRC R507.3")
    if isinstance(bearing, Slab):
        # ** EARNED, NOT ASSUMED. ** R507.3.1 sizes a deck post's own spread footing over
        # SOIL, and the positive evidence of absence here is that the post lands on a slab on
        # grade: there is no footing to size because the slab is what bears. What that leaves
        # ungraded is the slab's own bending and punching shear under the point load, and
        # this says so rather than letting it pass silently. If the answer turns out to be a
        # thickening, a Pad authored beside the slab is NOT how to model it (it reports a
        # concrete_interference lap with the slab it is part of, because the model has no way
        # to say "monolithic") — it stays a drawing note.
        return not_applicable(
            "structural.deck_footing_size",
            f"post {post.tag} bears on {bearing.tag}, a slab on grade ({where}) — IRC "
            f"R507.3.1 sizes a spread footing over soil and there is none here. NOT graded "
            f"by this or any other rule: the slab's own bending and punching shear under the "
            f"point load, and the bearing of whatever is under the slab",
            (carried_tag, post.tag, bearing.tag), code="IRC R507.3")
    if bearing is None:
        return _unknown(
            "structural.deck_footing_size",
            f"post {post.tag} declares no supported_by, so nothing says what carries it — "
            f"author it before IRC R507.3.1 can size anything",
            (carried_tag, post.tag))
    return _engineered(
        ctx, "structural.deck_footing_size",
        item_id("spread_footing", post.tag),
        f"post {post.tag} bears on {getattr(bearing, 'tag', where)}, which is neither a Pad "
        f"nor anything this check knows how to grade ({where})",
        (carried_tag, post.tag), code="IRC R507.3")


def _roof_borne_posts(ctx: CheckContext) -> tuple[dict[str, float], set[str], float]:
    """``(post tag -> EQUIVALENT deck tributary ft2, every post the roof reaches, snow psf)``.

    **Two collections and not one, because a post can be worth a VERDICT without being worth
    an AREA.** The shares are handed down the post chain to whatever stands on the ground, so
    a wood column standing on a pier keeps none of the roof it carries — but it still has to
    be reported, as the N/A that says where its load went. Dropping it from the shares dict
    and stopping there made two posts that used to carry a verdict carry nothing at all,
    which reads exactly like a check that never looked at them.

    ** A POST CAN BE INVISIBLE TO THIS CHECK RATHER THAN MERELY LIGHT, AND TWO OF CATLIN'S
    ARE. ** ``_deck_posts`` walks ``deck.authored.joists.bearing_refs``, so a post that
    carries no deck never enters the loop at all. ``PT-BW-RE`` and ``PT-BW-RNE`` carry
    ``BM-BW-RE``, a ROOF header and nothing else: they do not read tributary 0, they are not
    read.

    ** THE RULE IS ``engineering/pier_basis``'S AND IS NOT RESTATED HERE. ** It used to be —
    a hand copy carrying only ``_roof_fields``, with a comment claiming the package layering
    forbade the import. It does not: ``checks`` may import ``engineering`` and not the
    reverse, which is what ``checks/structural/_engineering.py`` exists to say. The copy had
    drifted twice over. It knew nothing of ``pier_basis._rafter_fields``, so every post under
    a beams-on-beams field was short by that field's whole area (catlin's four breezeway
    piers, 7.71 ft2 each, in the unconservative direction); and it scaled at
    ``Site.ground_snow_load_psf`` while the beams overhead were designed at the authored
    drift. Both are gone with the copy.

    ** THE ROOF SHARE IS CONVERTED TO DECK CURRENCY, BECAUSE R507.3.1 HAS ONLY ONE. ** The
    table sizes a bearing area from ``tributary x 50 psf``. A roof does not carry 50 psf: it
    carries SNOW, and ``pier_basis`` grades a pier's roof area at ``DECK_DEAD_LOAD_PSF +
    design snow``. So the area is scaled by the ratio of those two loads rather than added
    raw, and one currency reaches the table. At catlin's 73.7 psf design snow that is
    ``(10 + 73.7) / 50 = 1.674``, so 40 ft2 of canopy reads as 67 ft2 of deck.

    The third return is the design snow itself, 0.0 where the house authors none — the
    caller needs it to say WHY it cannot convert, rather than reporting a silent zero.
    """
    from typehaus.checks.structural._engineering import engineering_context
    from typehaus.engineering.pier_basis import design_roof_snow_psf, landed_roof_tributaries

    ectx = engineering_context(ctx)
    snow_psf, _basis = design_roof_snow_psf(ectx)
    landed, subjects = landed_roof_tributaries(ectx)
    if not snow_psf:
        return {}, subjects, 0.0
    scale = (DECK_DEAD_LOAD_PSF + snow_psf) / DECK_TOTAL_LOAD_PSF
    return {tag: area * scale for tag, area in landed.items()}, subjects, snow_psf


_WOOD_UNIT_WEIGHT_PCF = 35.0
_CONCRETE_UNIT_WEIGHT_PCF = 150.0


def _self_weight_ft2(ctx: CheckContext, post: Post, pad: Pad, area_ft2: float) -> float:
    """The shaft's and the pad's own weight, as EQUIVALENT R507.3.1 tributary ft2.

    **A footing carries its own concrete and the column standing on it**, and until
    2026-09-18 nothing on the ``Pad`` path counted either: ``engineering/spread_footing.py``
    adds both for a belled ``Footing`` (see its ``_one``), but it scopes itself off
    ``footing_tag`` and ``pier_basis.cast_piers`` sets that to ``None`` for a pad — so
    catlin's three house-side pads got their only bearing verdict from here, with no
    self weight in it at all.

    R507.3.1 has one currency, tributary area at ``DECK_TOTAL_LOAD_PSF``, so the weight is
    divided back into it rather than compared separately. A 12" round x 8' concrete shaft on
    a 30" x 10" pad is about 1,160 lb — 23 ft2 of equivalent tributary, which is not a
    rounding error beside a 40 ft2 deck share.

    **NET of the soil the pad displaced** — see
    ``engineering/soil.displaced_soil_credit_lb`` for why a presumptive allowable is a net
    pressure and charging the ground for both the excavated soil and the concrete that
    replaced it counts the same cubic feet twice.
    """
    from typehaus.engineering.pier_basis import post_section
    from typehaus.engineering.soil import displaced_soil_credit_lb
    from typehaus.resolve.assembly_material import assembly_structure_material

    depth_ft = pad.thickness.inches / 12.0
    weight = area_ft2 * depth_ft * _CONCRETE_UNIT_WEIGHT_PCF
    weight -= displaced_soil_credit_lb(area_ft2, depth_ft)
    section = post_section(post.size)
    if section is not None and post.height is not None:
        side, round_section = section
        face_in2 = math.pi * (side / 2.0) ** 2 if round_section else side ** 2
        concrete = assembly_structure_material(ctx.plan, post.assembly) == "concrete"
        density = _CONCRETE_UNIT_WEIGHT_PCF if concrete else _WOOD_UNIT_WEIGHT_PCF
        weight += (face_in2 / 144.0) * (post.height.inches / 12.0) * density
    return weight / DECK_TOTAL_LOAD_PSF


@check(Tier.STRUCTURAL, "structural.deck_footing_size")
def deck_footing_size(ctx: CheckContext) -> list[Finding]:
    """Deck footing bearing area vs. IRC R507.3.1 — tributary load over soil bearing value.

    **One finding per POST, not per (deck, post).** The outer loop used to be over decks, so
    a post landing two of them was graded twice, each time against ONE deck's share while
    adding the whole roof share again. Neither finding saw the reaction the pad actually
    carries, and the two disagreed with each other in the register. A footing answers for
    everything standing on it at once, so the shares are aggregated first and graded once.
    """
    decks = _decks(ctx)
    if not decks:
        return []  # no exterior deck — R507 does not apply
    soil_psf = ctx.profile.soil_bearing_psf
    if soil_psf is None:
        return [_unknown("structural.deck_footing_size",
                         f"profile {ctx.profile.name} declares no soil bearing value, so a "
                         "footing cannot be sized")]
    out: list[Finding] = []
    # Per post, not per deck: the beam-weighted split gives the centre pair half again the
    # share of the corners, and one pad size for all of them would either under-size those
    # two or over-size the other four.
    deck_share: dict[str, float] = {}
    carried: dict[str, set[str]] = {}
    for deck in decks:
        tributaries = _tributaries_ft2(ctx, deck)
        if tributaries is None:
            out.append(_unknown("structural.deck_footing_size",
                                f"deck {deck.tag} has no tributary area to size footings from",
                                (deck.tag,)))
            continue
        for post in _deck_posts(ctx, deck):
            deck_share[post.tag] = deck_share.get(post.tag, 0.0) + tributaries.get(post.tag, 0.0)
            carried.setdefault(post.tag, set()).add(deck.tag)

    roof_borne, roof_subjects, snow_psf = _roof_borne_posts(ctx)
    if not snow_psf and roof_subjects:
        out.append(_unknown(
            "structural.deck_footing_size",
            "this site authors no design snow (preferences.toml [structural] "
            "roof_beam_snow_psf) and no Site.ground_snow_load_psf, so the roof share on "
            f"{', '.join(sorted(roof_subjects))} cannot be put into R507.3.1's currency",
            tuple(sorted(roof_subjects))))

    minimum = (MIN_DECK_FOOTING_SIDE_IN / 12.0) ** 2
    for tag in sorted(set(deck_share) | set(roof_borne) | roof_subjects):
        post = ctx.plan.by_tag(tag)
        if not isinstance(post, Post):
            continue
        # A post under a deck may ALSO be under a roof — the north entry's west pair is
        # both. Its footing answers for the two together, so the roof's equivalent share
        # is added here rather than reported separately.
        tributary = deck_share.get(tag, 0.0) + roof_borne.get(tag, 0.0)
        named = ", ".join(sorted(carried.get(tag, ()))) or _roof_over(ctx, tag)
        what = "deck" if tag in carried else "roof"
        bearing, chain = _bearing_of(ctx, post)
        if _hands_over(ctx, chain) or not isinstance(bearing, Pad):
            out.append(_not_a_pad(ctx, named, post, bearing, chain))
            continue
        pad = bearing
        area_ft2 = abs(_shoelace([p.xy_m for p in pad.outline])) / (_M_PER_FT ** 2)
        thickness_in = pad.thickness.inches
        self_ft2 = _self_weight_ft2(ctx, post, pad, area_ft2)
        required = max(required_footing_area_ft2(tributary + self_ft2, soil_psf), minimum)
        if area_ft2 + 1e-9 < required:
            out.append(_advisory(
                "structural.deck_footing_size",
                f"{what} {named} pad {pad.tag} bears {area_ft2:.2f} ft2, under the "
                f"{required:.2f} ft2 IRC R507.3.1 needs for {tributary:.1f} ft2 tributary "
                f"+ {self_ft2:.1f} ft2 of its own weight at "
                f"{DECK_TOTAL_LOAD_PSF:.0f} psf on {soil_psf:.0f} psf soil",
                (pad.tag, post.tag), Result.FAIL,
                fix_hint="widen the pad, or add a post to cut the tributary area",
            ))
        elif thickness_in + 1e-9 < MIN_DECK_FOOTING_THICKNESS_IN:
            out.append(_advisory(
                "structural.deck_footing_size",
                f"{what} {named} pad {pad.tag} bears enough area but is only "
                f"{thickness_in:.1f}\" thick, under the "
                f"{MIN_DECK_FOOTING_THICKNESS_IN:.0f}\" minimum",
                (pad.tag, post.tag), Result.FAIL,
                fix_hint="thicken the pad to at least 6\"",
            ))
        else:
            out.append(_advisory(
                "structural.deck_footing_size",
                f"{what} {named} pad {pad.tag} bears {area_ft2:.2f} ft2 on "
                f"{soil_psf:.0f} psf soil, over the {required:.2f} ft2 IRC R507.3.1 "
                f"needs for {tributary:.1f} ft2 tributary + {self_ft2:.1f} ft2 of its "
                f"own weight",
                (pad.tag, post.tag), Result.PASS,
            ))
    return out


def _roof_over(ctx: CheckContext, post_tag: str) -> str:
    """The tag of the roof whose load reaches ``post_tag``, for the finding to name."""
    from typehaus.model.spatial import Roof

    for roof in ctx.model.roofs:
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        for ref in element.bearing_refs:
            beam = ctx.plan.by_tag(ref)
            if isinstance(beam, Beam) and post_tag in (beam.bearing_refs or ()):
                return roof.tag
    return post_tag


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
    railings = guard_lines(ctx.plan)
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
        # A rail raked with a stair (``serves_stair``) stands on no deck, whatever its datum.
        on_deck = [r for r in railings
                   if abs(r.base_elevation.meters - surface_m) < 0.15
                   and not getattr(r.source, "serves_stair", None)]
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


def _off_table_beam(ctx, deck, beam, span_ft: float, joist_span_ft: float) -> list[Finding]:
    """A beam IRC Table R507.5(1) has no row for: the supplier's table, and the NDS record.

    Two findings, deliberately — and **which of them is the verdict changed on 2026-09-18.**
    It was the published row, with the NDS pass beside it as an ADVISORY. But the deck
    guide's values are DRY-USE and every one of these beams stands in weather, which the
    row's own ``condition`` string said all along: the verdict was coming from a row that
    does not describe the member, and the only calculation modelling the real service
    condition was the one carrying no weight.

    So ``PublishedSpan.service_condition`` is passed and the row is refused on it — UNKNOWN
    naming the mismatch, which is what a read of a table that does not cover this member is
    worth — and ``engineering/glulam_beam`` is a registered kind again, carrying the verdict
    through ``engineered()`` with a record, a fingerprint and an oracle.

    A beam whose row DOES match its service condition still passes prescriptively: the
    published read is not weakened, it is answered.
    """
    from typehaus.checks.structural.published import graded_against_published
    from typehaus.engineering.glulam_beam import KIND as GLULAM_KIND
    from typehaus.engineering.glulam_beam import section_of
    from typehaus.resolve.assembly_material import assembly_structure_material

    source = ctx.plan.by_tag(beam.tag) if ctx.plan is not None else None
    published = getattr(source, "published_span", None)
    material = assembly_structure_material(ctx.plan, beam.assembly) or ""

    # ** A GLULAM IS ANSWERED BY THE RECORD, AND THEN THE ROW IS NOT ASKED. ** Emitting both
    # would put an UNKNOWN beside a PASS about one member and one question — and an UNKNOWN
    # is a statement that nobody knows, which is false the moment the record exists. It
    # would also block the permit gate on a question the engine has answered.
    if material.startswith("glulam") and section_of(beam) is not None:
        item = item_id(GLULAM_KIND, beam.tag)
        refusal = _published_refusal(published, beam, joist_span_ft)
        return [_engineered(
            ctx, "structural.deck_beam_span", item,
            f"deck {deck.tag} beam {beam.tag} ({beam.size}) is a glulam in WEATHER, which "
            f"no IRC table publishes a row for — {refusal}",
            (deck.tag, beam.tag),
            code="AWC NDS 2018 Ch. 3 and 5",
            fix=f"deepen the member, shorten the span, or seal `{item}` in engineering.toml")]

    # Weather, because a deck is outdoors by definition — R507 is the exterior-deck chapter
    # and `_decks` scopes on `service="deck"`. A row published dry does not cover it.
    return [graded_against_published(
        "structural.deck_beam_span",
        f"deck {deck.tag} beam {beam.tag} ({beam.size})",
        (deck.tag, beam.tag), span_ft, published, beam.size,
        carried_span_ft=joist_span_ft,
        # ** THIS ARGUMENT WAS MISSING UNTIL 2026-09-18. ** Without it the load-basis
        # comparison — the most important guard a span table has — never ran on any deck
        # beam in the house, and its absence was indistinguishable from agreement.
        demand_psf=DECK_TOTAL_LOAD_PSF,
        service_condition="wet",
        fix="author Beam.published_span with the supplier's deck-guide row for this beam "
            "at this joist span, or leave the beam to an engineered design")]


def _published_refusal(published, beam, joist_span_ft: float) -> str:
    """Why the supplier's row is not the verdict here, in one clause for the record's message.

    Said out loud rather than dropped, because "there is a published row and we are not
    using it" is exactly the sentence a reviewer needs; a silent engineered record beside an
    authored ``PublishedSpan`` looks like the engine never read the table.
    """
    from typehaus.checks.structural.published import drift_reason

    if published is None:
        return "and no supplier row is authored for it either"
    reason = drift_reason(published, beam.size, carried_span_ft=joist_span_ft,
                          demand_psf=DECK_TOTAL_LOAD_PSF, service_condition="wet")
    if reason is None:
        return (f"the supplier's row ({published.table}) does cover it, and the NDS pass "
                f"below is the arithmetic behind that row's own conditions")
    return f"and its supplier's row does not cover it: {reason}"
