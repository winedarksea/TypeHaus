"""Concentrated loads standing on a cantilevered deck (→ 12 §checks/structural).

Every span table this model owns — the interior floor tables in
:mod:`typehaus.checks.structural.checks`, AWC DCA6 Table 3A in
:mod:`typehaus.checks.structural.deck_tables` — is a *uniform load* table. It answers "how
far may this joist reach carrying 40 psf over its whole length", and it is silent about a
6x6 pillar set down on the free end of one 1 1/2" ply — nothing else in this model looks
at whether a point load is standing on an overhang.

This check looks. Scope is a ``FloorSystem`` whose ``JoistSpec`` declares any cantilever,
paired with what it resolved into; the load is a ``Post`` naming that deck in
``supported_by``. A post over the back span is the ordinary case and reports nothing — the
uniform tables already grade it. A post inside the overhang band is a finding, always:

* nothing recognisably carrying it       -> FAIL, tagged ``[advisory, not engineering]``;
* the reinforcement contract satisfied   -> UNKNOWN, same tag.

The mitigated case is deliberately **not** a PASS. Sistering the line and blocking it is
the right answer and the take-off bills it, but "the load is answered" is a judgement the
tables cannot make: they assume no point load at all, so there is no row to pass. Calling
it UNKNOWN keeps the reinforcement visible in the not-evaluable column, which is where an
engineer's stamp belongs, rather than retiring the question.

What counts as mitigation is a contract shared with :mod:`typehaus.resolve.floors` — see the
CHECK-RECOGNITION CONTRACT comment above ``_reinforcement_members`` there, which is the
producer of arms (a) and (b). The three arms are alternatives, not requirements:

(a) sistered plies on the post's own joist line — an authored
    ``FloorSystem.reinforcements`` entry with ``plies >= 3`` near the post, or, read off
    the geometry, resolved ``"sister_joist"`` members within half a joist spacing of it;
(b) solid ``"blocking"`` within 0.3 m, which is what stops a loaded joist rolling and
    shares the load with the lines either side;
(c) an uplift ``Connector`` (HURRICANE_TIE / HOLD_DOWN) on the same joist line, tying the
    deck or its *back-span* bearing down against the prying the overhang does there.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConnectorKind
from typehaus.model.floors import FloorSystem
from typehaus.model.structure import Connector, Post
from typehaus.quantities import M_PER_IN

# The bearing lines a deck's joists land on are the resolver's own derivation — a resolved
# wall axis, or a standalone Beam looked up through its per-storey nodes. Re-deriving them
# here would be a second answer to the same question (and the two would drift);
# ``code/mn_residential/fall_protection.py`` reaches into the same module for the same
# reason.
from typehaus.resolve.floors import _bearing_axis
from typehaus.resolve.model import ResolvedFloor

# The tables are published at 12/16/24" o.c.; a FloorSystem that leaves JoistSpec.spacing
# unset gets the solver's own default, which is the middle one. (Same constant as deck.py —
# duplicated rather than shared because it is a restatement of the solver's default, not a
# deck rule.)
_DEFAULT_SPACING_IN = 16.0
# Arm (b): the blocks are placed at the load's own axis coordinate by the resolver, so this
# is a "did the blocking follow the post" tolerance, not a search radius. Roughly a foot —
# wide enough for a block sitting one joist bay over, far too tight for blocking left at a
# bearing line.
_BLOCKING_NEAR_M = 0.3
# A post centred exactly on the joist tip — which is what catlin's PT-SG-BR2 is — has to
# read as *inside* the overhang, not one float ulp outside it.
_EPS = 1e-6
# How near a bearing line's axis coordinate has to be to a deck end to be that end's
# bearing. Bearing lines sit feet apart, so this only has to absorb the difference between
# a wall's resolved axis and the joist tip that landed on it.
_BEARING_LINE_TOL_M = 0.05


def _advisory(msg: str, tags: tuple[str, ...], result: Result,
              fix_hint: str | None = None) -> Finding:
    """Same contract as the sibling structural checks: the finding says out loud that a
    prescriptive table lookup is not an engineered design."""
    return Finding(severity=Severity.WARN, check_id="structural.cantilever_point_load",
                   message=f"[advisory, not engineering] {msg}", element_tags=tags,
                   result=result, fix_hint=fix_hint)


def _unknown(msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id="structural.cantilever_point_load",
                   message=f"UNKNOWN — {msg}", element_tags=tags, result=Result.UNKNOWN)


def _axis_perp(point: tuple[float, float], along_x: bool) -> tuple[float, float]:
    """A plan point as (along the joists, across them) — the resolver's own frame."""
    x, y = point
    return (x, y) if along_x else (y, x)


def _point_to_segment_m(point: tuple[float, float], p0: tuple[float, float],
                        p1: tuple[float, float]) -> float:
    """Plan distance from a point to a segment. A block is measured to its whole length,
    not to an end: a post standing over the middle of a block is nearer it than either end.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length2 = dx * dx + dy * dy
    if length2 <= 0.0:
        return ((point[0] - p0[0]) ** 2 + (point[1] - p0[1]) ** 2) ** 0.5
    t = ((point[0] - p0[0]) * dx + (point[1] - p0[1]) * dy) / length2
    t = min(1.0, max(0.0, t))
    near = (p0[0] + t * dx, p0[1] + t * dy)
    return ((point[0] - near[0]) ** 2 + (point[1] - near[1]) ** 2) ** 0.5


@dataclass(frozen=True)
class _Cantilever:
    """One authored FloorSystem that overhangs a bearing line, paired with what it framed."""

    authored: FloorSystem
    resolved: ResolvedFloor

    @property
    def tag(self) -> str:
        return self.authored.tag

    @property
    def along_x(self) -> bool:
        return self.authored.joists.direction == "x"

    @property
    def spacing_m(self) -> float:
        spacing = self.authored.joists.spacing
        return (spacing.inches if spacing is not None else _DEFAULT_SPACING_IN) * M_PER_IN

    @property
    def overhangs(self) -> tuple[float, float]:
        """(start, end) overhang in metres — the per-end override falling back to the
        symmetric scalar, exactly as ``resolve/floors.py`` reads it when it lays the field
        out. "start"/"end" are the low/high ends along the joist span direction."""
        spec = self.authored.joists
        both = spec.cantilever.meters if spec.cantilever is not None else 0.0
        start = spec.cantilever_start.meters if spec.cantilever_start is not None else both
        end = spec.cantilever_end.meters if spec.cantilever_end is not None else both
        return start, end

    def members(self, category: str) -> list:
        return [m for m in self.resolved.members if m.category == category]

    def field_extent(self) -> tuple[float, float, float, float] | None:
        """(axis_lo, axis_hi, perp_lo, perp_hi) of the resolved joist field.

        The joist tips *are* the overhang: the resolver extends the outer spans by the
        cantilever before it emits them, so the field's axis extent already includes both
        overhangs and the bands can be measured back off it. Reading the resolved members
        rather than re-deriving the bearing lines means a deck whose joists were clipped or
        whose bearings moved cannot be graded against a band it no longer has.
        """
        joists = self.members("joist")
        if not joists:
            return None
        pairs = [_axis_perp(p, self.along_x) for m in joists for p in (m.p0, m.p1)]
        axis_values = [a for a, _ in pairs]
        perp_values = [p for _, p in pairs]
        return min(axis_values), max(axis_values), min(perp_values), max(perp_values)


def _cantilevered_decks(ctx: CheckContext) -> list[_Cantilever]:
    """Every authored deck that declares an overhang and actually resolved."""
    by_tag = {f.tag: f for f in ctx.model.floors}
    out: list[_Cantilever] = []
    for element in ctx.plan.all_elements():
        if not isinstance(element, FloorSystem):
            continue
        resolved = by_tag.get(element.tag)
        if resolved is None:
            continue
        deck = _Cantilever(element, resolved)
        if max(deck.overhangs) > _EPS:
            out.append(deck)
    return out


def _band(deck: _Cantilever, extent: tuple[float, float, float, float],
          post_xy: tuple[float, float]) -> tuple[str, float, float] | None:
    """The overhang the post stands on, as (which end, its depth in metres, how far past
    the bearing line the post is) — or ``None`` for a post over the back span.

    Perpendicular containment is part of the test: a post whose plan position is off the
    side of the joist field is not standing on a joist tip at all, whatever it names as its
    support. The band is deliberately *open* outward, though — a post past the joist tips
    is a worse version of this condition, not an exemption from it.
    """
    axis_lo, axis_hi, perp_lo, perp_hi = extent
    post_axis, post_perp = _axis_perp(post_xy, deck.along_x)
    if not perp_lo - _EPS <= post_perp <= perp_hi + _EPS:
        return None
    start, end = deck.overhangs
    if start > _EPS and post_axis <= axis_lo + start + _EPS:
        return "start", start, axis_lo + start - post_axis
    if end > _EPS and post_axis >= axis_hi - end - _EPS:
        return "end", end, post_axis - (axis_hi - end)
    return None


def _back_span_bearings(ctx: CheckContext, deck: _Cantilever,
                        extent: tuple[float, float, float, float]) -> set[str]:
    """The deck's bearing refs at an end that does *not* overhang.

    Arm (c) is an uplift tie at the back span: the overhang levers that bearing upward and
    a tie there is what holds it down. A tie on the *cantilevered* bearing line answers a
    different load — catlin authors one (CN-SG-TIE-COL, tying the back beams to their
    sonotube column) and it must not be mistaken for this one — so the end each bearing sits
    at decides whether naming it counts.
    """
    axis_lo, axis_hi, _perp_lo, _perp_hi = extent
    start, end = deck.overhangs
    ends = ([axis_lo] if start <= _EPS else []) + ([axis_hi] if end <= _EPS else [])
    if not ends:
        return set()
    axis_index = 0 if deck.along_x else 1
    out: set[str] = set()
    for ref in deck.authored.joists.bearing_refs:
        bearing = _bearing_axis(ctx.model, ref)
        if bearing is None:
            continue
        p0, p1 = bearing
        coord = (p0[axis_index] + p1[axis_index]) / 2.0
        if any(abs(coord - line) <= _BEARING_LINE_TOL_M for line in ends):
            out.add(ref)
    return out


def _mitigations(ctx: CheckContext, deck: _Cantilever,
                 extent: tuple[float, float, float, float],
                 post: Post) -> tuple[list[str], tuple[str, ...]]:
    """The mitigation arms this post's load satisfies, as prose, plus any element tags they
    name. Empty means nothing in the model carries the point load."""
    post_xy = post.position.xy_m
    post_perp = _axis_perp(post_xy, deck.along_x)[1]
    half_spacing = deck.spacing_m / 2.0
    reasons: list[str] = []
    tags: list[str] = []

    # (a) — the authored intent. Measured to the post as a plan distance because ``at`` is
    # the *load*, not a joist index: an entry two bays away reinforces a different line.
    authored = [r for r in deck.authored.reinforcements
                if r.plies >= 3
                and ((r.at.xy_m[0] - post_xy[0]) ** 2
                     + (r.at.xy_m[1] - post_xy[1]) ** 2) ** 0.5 <= half_spacing + _EPS]
    if authored:
        reasons.append(f"an authored {max(r.plies for r in authored)}-ply JoistReinforcement "
                       "on the line under it")
    # (a) again, geometrically. Perpendicular offset only: a sister runs the joist's whole
    # length (including the overhang, by contract), so where it starts along the span says
    # nothing about whether it reaches the load — which line it is on says everything.
    sisters = [m for m in deck.members("sister_joist")
               if abs(_axis_perp(m.p0, deck.along_x)[1] - post_perp) <= half_spacing + _EPS]
    if sisters:
        reasons.append(f"{len(sisters)} sistered {sisters[0].profile} plies within "
                       f"{half_spacing / M_PER_IN:.0f}\" of it")
    # (b) — blocking at the load.
    blocks = [m for m in deck.members("blocking")
              if _point_to_segment_m(post_xy, m.p0, m.p1) <= _BLOCKING_NEAR_M]
    if blocks:
        reasons.append(f"{len(blocks)} solid blocks within "
                       f"{_BLOCKING_NEAR_M / M_PER_IN:.0f}\" of it")
    # (c) — an uplift tie on the same joist line, on the deck itself or on its back-span
    # bearing.
    anchors = {deck.tag} | _back_span_bearings(ctx, deck, extent)
    ties = [e for e in ctx.plan.all_elements()
            if isinstance(e, Connector)
            and e.kind in (ConnectorKind.HURRICANE_TIE, ConnectorKind.HOLD_DOWN)
            and anchors.intersection(e.connects)
            and abs(_axis_perp(e.position.xy_m, deck.along_x)[1] - post_perp)
            <= half_spacing + _EPS]
    if ties:
        reasons.append("uplift hardware " + ", ".join(
            f"{t.tag} ({t.size or t.kind.value})" for t in sorted(ties, key=lambda t: t.tag)))
        tags.extend(sorted(t.tag for t in ties))
    return reasons, tuple(tags)


@check(Tier.STRUCTURAL, "structural.cantilever_point_load")
def cantilever_point_load(ctx: CheckContext) -> list[Finding]:
    """A Post bearing on a cantilevered FloorSystem's overhang — never a silent pass."""
    decks = _cantilevered_decks(ctx)
    if not decks:
        return []  # nothing overhangs — there is no band for a post to stand on
    posts = [e for e in ctx.plan.all_elements() if isinstance(e, Post)]
    out: list[Finding] = []
    for deck in decks:
        carried = [p for p in posts if p.supported_by == deck.tag]
        if not carried:
            continue  # an overhang with nothing set down on it is just an overhang
        extent = deck.field_extent()
        if extent is None:
            out.append(_unknown(
                f"deck {deck.tag} declares a cantilever and carries "
                f"{', '.join(p.tag for p in carried)}, but resolved no joists, so the "
                "overhang band cannot be located",
                (deck.tag, *(p.tag for p in carried))))
            continue
        spacing_in = deck.spacing_m / M_PER_IN
        for post in carried:
            band = _band(deck, extent, post.position.xy_m)
            if band is None:
                continue  # over the back span — the uniform span tables already grade it
            end, depth_m, past_m = band
            # ``JoistSpec`` names the ends "start"/"end"; a reader of the finding needs to
            # know *which* edge of the deck that is, so print it as the span direction.
            edge = f"{'low' if end == 'start' else 'high'}-{deck.authored.joists.direction}"
            where = (f"{depth_m / M_PER_IN:.0f}\" cantilever at its {edge} edge "
                     f"({deck.authored.joists.member} joists at {spacing_in:.0f}\" o.c.)")
            reasons, tags = _mitigations(ctx, deck, extent, post)
            element_tags = (deck.tag, post.tag, *tags)
            if not reasons:
                out.append(_advisory(
                    f"post {post.tag} ({post.size}) bears on deck {deck.tag}'s {where}, "
                    f"{past_m / M_PER_IN:.1f}\" past the bearing line, with nothing in the "
                    "model carrying the point load; the span tables are uniform-load tables "
                    "and have no row for this", element_tags, Result.FAIL,
                    fix_hint=("sister the joist line under the post (a JoistReinforcement "
                              "with plies >= 3 and blocking) and tie the back-span bearing "
                              "down, or move the post onto a bearing line"),
                ))
                continue
            out.append(_advisory(
                f"post {post.tag} ({post.size}) bears on deck {deck.tag}'s {where}, "
                f"{past_m / M_PER_IN:.1f}\" past the bearing line; the load is answered by "
                f"{'; '.join(reasons)} — but the prescriptive span tables assume no "
                "cantilever point load, so this is reinforced, not verified",
                element_tags, Result.UNKNOWN,
                fix_hint="an engineered check of the reinforced cluster would close this",
            ))
    return out
