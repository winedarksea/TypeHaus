"""Mechanical equipment standing on an exterior deck — is it held down, and where (→ 12).

An outdoor unit on a deck is three problems the rest of the model does not see:

1. **It has to be bolted down.** Not a preference — Gree's service manual (and every other
   manufacturer's) says to fix the unit's foot holes to a support rated well past the unit's
   own weight, and IRC M1401.4 makes a manufacturer's installation instruction mandatory.
   Section M1401.4 says it directly as well: *"supports and foundations shall prevent
   excessive vibration, settlement or movement of the equipment."* A cabinet standing loose
   on a deck at storey height satisfies none of that.

2. **The fastener has to land in the right member.** A deck that is also a roof over occupied
   space has a waterproof plane, and an equipment anchor is a hole through it. Where the hole
   goes is a hundred-year decision: into blocking it is replaceable from below, and into a
   beam or a joist it is not. This check is the only thing in the model that states that rule,
   because nothing about the geometry distinguishes the two — both are lumber under a plank.

3. **It makes water all winter.** A cold-climate heat pump sheds defrost meltwater every time
   it reverses, over whatever is under the deck, in a climate that freezes it.

** THIS CHECK GRADES COVERAGE, NOT CAPACITY. ** It reports whether a joint has hardware and
where that hardware lands, never whether the hardware is big enough: this check derives no
demand from Site's wind fields (``design_wind_speed_mph`` / ``wind_exposure`` /
``risk_category``). Sizing an outdoor unit's restraint wants the cabinet's own
projected area and an ASCE 7 §29.4 rooftop-equipment force coefficient, neither of which is
in the model, and a restraint schedule without a load is still a drawing, not a calculation.
``wind.py::capacity_caveat`` owns the wording so this file and
``checks/structural/uplift_path.py`` cannot drift into two accounts of the same model. So a
fully covered unit is reported UNKNOWN, exactly as that check reports a covered link, and for
the same reason: "there is an anchor here" is a different claim from "this anchor holds", and
folding the first into a PASS would retire a question an engineer still has to answer.

An **uncovered** unit is a FAIL. No anchor at all is not a judgement call.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import engineered as _engineered
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.floors import FloorSystem
from typehaus.model.mep import Equipment, PipeRun
from typehaus.model.structure import Beam, Connector
from typehaus.wind import capacity_caveat

#: Named for what this rule grades: whether the anchorage is COVERED — every anchor in
#: blocking rather than a joist or beam, condensate piped and traced — not the connection's
#: capacity, which lives at one `equipment_anchorage/<unit>` item per unit in the
#: engineering register.
_CID = "mep.deck_equipment_support_coverage"
_ANCHORAGE_KIND = "equipment_anchorage"

#: Plan distance within which an authored ``Connector`` counts as anchoring a unit. Generous
#: on purpose: a stand's legs are deliberately NOT under the cabinet's own feet (they dodge
#: beams), so a tight radius would report a correctly-built stand as unanchored. Half the
#: cabinet's own diagonal plus a foot is the honest reading of "this hardware is this unit's".
_ANCHOR_REACH_M = 0.30
#: How close an anchor may come to a joist or beam centreline before it stops being "in the
#: bay". A 2x is 1 1/2" wide and a 3-ply beam 4 1/2"; 4" clears the widest of them with room
#: for a base plate, and is tight enough that an anchor authored *on* a line is caught.
_MEMBER_CLEAR_M = 4.0 * 0.0254


def _fail(msg: str, tags: tuple[str, ...], fix: str | None = None) -> Finding:
    """WARN severity with a FAIL result — shows as a failure without gating the permit.

    Deliberate, and the same call ``checks/mep/data.py`` makes: the permit integrity gate
    keys off ERROR severity alone, and how a condenser is bolted down is not a question the
    permit set answers.
    """
    return advisory(_CID, msg, tags, Result.FAIL, fix=fix)


def _inside(point: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    """Ray cast. The deck outlines here are rectangles, but nothing guarantees that."""
    x, y = point
    hit = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1], strict=True):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


def _decks_by_storey(ctx: CheckContext) -> dict[str, list[FloorSystem]]:
    """Authored exterior decks that resolved, KEYED BY STOREY.

    Storey-scoped, and that is not tidiness. This house stacks two exterior decks on one plan
    footprint — the porch at 0'-0" and the balcony 10' above it — so a point inside one is
    inside both, and a whole-plan search matched every balcony condenser to the porch it is
    standing over rather than to the deck it is standing on. It then read the porch pillars'
    own post bases as the condensers' anchors and graded those. Two wrong answers from one
    missing filter, and both of them looked plausible.
    """
    resolved = {f.tag for f in ctx.model.floors}
    out: dict[str, list[FloorSystem]] = {}
    for storey in ctx.plan.storeys:
        decks = [e for e in ctx.plan.storey_elements(storey.tag)
                 if isinstance(e, FloorSystem) and e.service == "deck" and e.tag in resolved]
        if decks:
            out[storey.tag] = decks
    return out


@check(Tier.ADVISORY, _CID)
def deck_equipment_support(ctx: CheckContext) -> list[Finding]:
    """Equipment on an exterior deck is anchored, anchored into blocking, and drained."""
    by_storey = _decks_by_storey(ctx)
    if not by_storey:
        return []  # no exterior deck — nothing to stand on; not an unknown

    connectors = [e for e in ctx.plan.all_elements() if isinstance(e, Connector)]
    runs = {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, PipeRun)}
    nodes = {e.tag: e.position.xy_m for e in ctx.plan.all_elements()
             if e.element_kind == "Node"}

    out: list[Finding] = []
    for storey_tag, decks in by_storey.items():
        outlines = {d.tag: [p.xy_m for p in d.outline] for d in decks if d.outline}
        if not outlines:
            continue
        # Beams from THIS STOREY only, for the same reason the decks are storey-scoped: the
        # porch's back beams run east-west directly under the balcony's anchors, ten feet
        # below them, and a whole-plan search reported four anchors as landing on a beam that
        # a lag through this deck cannot reach. The wrong-deck bug this collector was written
        # to fix had a twin one function away.
        beams = [e for e in ctx.plan.storey_elements(storey_tag) if isinstance(e, Beam)]
        blocking = _members_by_deck(ctx, decks, frozenset({"blocking"}))
        # "rim" as well as "joist": the rim IS a joist line as far as an anchor is concerned
        # — full depth, at the field edge, and just as unreplaceable.
        joists = _members_by_deck(ctx, decks, frozenset({"joist", "rim"}))
        units = [e for e in ctx.plan.storey_elements(storey_tag) if isinstance(e, Equipment)]
        for unit in sorted(units, key=lambda e: e.tag):
            here = next((tag for tag, ring in outlines.items()
                         if _inside(unit.position.xy_m, ring)), None)
            if here is None:
                continue  # not on a deck — this rule is not about it
            out.extend(_grade_unit(unit, here, connectors, runs, beams, nodes,
                                   blocking.get(here, []), joists.get(here, []),
                                   ctx.plan.project.site))
    return out


def _members_by_deck(ctx: CheckContext, decks: list[FloorSystem],
                     categories: frozenset) -> dict:
    """Resolved member spans per deck, as (x0, y0, x1, y1) in metres."""
    by_uid = {d.uid: d.tag for d in decks}
    out: dict[str, list[tuple[float, float, float, float]]] = {}
    for floor in ctx.model.floors:
        for member in getattr(floor, "members", ()):
            if member.category not in categories:
                continue
            tag = by_uid.get(member.parent_uid)
            if tag is not None:
                out.setdefault(tag, []).append(
                    (member.p0[0], member.p0[1], member.p1[0], member.p1[1]))
    return out


def _on_a_block(point: tuple[float, float], blocks: list) -> bool:
    """Is this anchor inside one of the deck's blocking spans (plus a base-plate margin)?"""
    x, y = point
    for x0, y0, x1, y1 in blocks:
        if (min(x0, x1) - _MEMBER_CLEAR_M <= x <= max(x0, x1) + _MEMBER_CLEAR_M
                and min(y0, y1) - _MEMBER_CLEAR_M <= y <= max(y0, y1) + _MEMBER_CLEAR_M):
            return True
    return False


def _on_a_joist(point: tuple[float, float], joists: list) -> bool:
    """Is this anchor sitting on a joist line rather than in the bay between two?

    ** THIS IS NOT REDUNDANT WITH ``_on_a_block``, AND ASSUMING IT WAS LEFT A HOLE. **
    A ``JoistReinforcement`` lays its blocking in the bays *either side of the joist line
    nearest the load*, spanning the full clear gap — so the block's bounding box reaches from
    one joist line to the next, and the anchor is inside it whether it sits mid-bay or dead
    on a joist. Blocking presence therefore proves a host exists; it cannot prove the anchor
    found it. Only the distance to a joist line can, which is the same test ``_on_a_beam``
    already makes against the beams for the same reason.
    """
    x, y = point
    for x0, y0, x1, y1 in joists:
        dx, dy = x1 - x0, y1 - y0
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-9:
            continue
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / length_sq))
        nx, ny = x0 + t * dx, y0 + t * dy
        if (x - nx) ** 2 + (y - ny) ** 2 <= _MEMBER_CLEAR_M ** 2:
            return True
    return False


def _on_a_beam(point: tuple[float, float], beams: list, nodes: dict) -> str | None:
    """The tag of a beam this anchor lands on, if any — the case the rule exists to catch."""
    x, y = point
    for beam in beams:
        p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
        if p0 is None or p1 is None:
            continue
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-9:
            continue
        t = max(0.0, min(1.0, ((x - p0[0]) * dx + (y - p0[1]) * dy) / length_sq))
        near = (p0[0] + t * dx, p0[1] + t * dy)
        if (x - near[0]) ** 2 + (y - near[1]) ** 2 <= _MEMBER_CLEAR_M ** 2:
            return beam.tag
    return None


def _grade_unit(unit, deck_tag: str, connectors, runs, beams, nodes, blocks,
                joists, site) -> list[Finding]:
    ux, uy = unit.position.xy_m
    reach = _ANCHOR_REACH_M + max(unit.footprint[0].meters, unit.footprint[1].meters)
    anchors = [c for c in connectors
               if (c.position.xy_m[0] - ux) ** 2 + (c.position.xy_m[1] - uy) ** 2
               <= reach ** 2 and deck_tag in c.connects]
    out: list[Finding] = []

    if not anchors:
        return [_fail(
            f"{unit.tag} stands on deck {deck_tag} with no anchor: no Connector within "
            f"{reach / 0.0254:.0f}\" of it names {deck_tag}. IRC M1401.4 adopts the "
            f"manufacturer's instruction, and every outdoor-unit instruction requires the "
            f"foot holes bolted to a rated support",
            (unit.tag, deck_tag),
            fix="author a Connector per stand leg naming the deck it anchors into")]

    # Where each anchor lands. A beam or a joist is a FAIL even though it is stiffer — the
    # rule is about what can be replaced, not about what carries best.
    for anchor in sorted(anchors, key=lambda c: c.tag):
        beam_tag = _on_a_beam(anchor.position.xy_m, beams, nodes)
        if beam_tag is not None:
            out.append(_fail(
                f"anchor {anchor.tag} for {unit.tag} lands on beam {beam_tag}: a fastener "
                f"through this deck's waterproof plane must land in sacrificial blocking, "
                f"not in a primary member that cannot be cut out and replaced from below",
                (unit.tag, anchor.tag, beam_tag),
                fix="move the stand leg into a joist bay and add a JoistReinforcement "
                    "(plies=1, blocking=True) at that point"))
        elif _on_a_joist(anchor.position.xy_m, joists):
            out.append(_fail(
                f"anchor {anchor.tag} for {unit.tag} lands within "
                f"{_MEMBER_CLEAR_M / 0.0254:.0f}\" of a joist line on {deck_tag}: the "
                f"blocking either side of that line is the intended host, and a lag driven "
                f"on the line goes into the joist instead — a member that cannot be cut out "
                f"and replaced from the porch below",
                (unit.tag, anchor.tag, deck_tag),
                fix="move the stand leg to a bay centre and put the JoistReinforcement at "
                    "the same point"))
        elif not _on_a_block(anchor.position.xy_m, blocks):
            out.append(_fail(
                f"anchor {anchor.tag} for {unit.tag} lands on no modeled blocking: it is "
                f"either on a joist or in an unblocked bay, and either way the penetration "
                f"is hosted by a member the deck cannot spare",
                (unit.tag, anchor.tag, deck_tag),
                fix="add a JoistReinforcement (plies=1, blocking=True) at the anchor point"))

    # Condensate. Only asked of equipment that makes it.
    out.extend(_grade_condensate(unit, deck_tag, runs))

    if not out:
        out.append(_pass(
            _CID,
            f"{unit.tag} on deck {deck_tag} is held by {len(anchors)} authored anchor(s), "
            f"every one of them landing in blocking rather than a joist or a beam, and its "
            f"condensate is piped and freeze-protected — the anchorage is covered; its "
            f"CAPACITY is not graded here and belongs to "
            f"`{_ANCHORAGE_KIND}/{unit.tag}` in the engineering register "
            f"({capacity_caveat(site)})",
            (unit.tag, deck_tag)))
    return out


def _grade_condensate(unit, deck_tag: str, runs) -> list[Finding]:
    """A heat pump over occupied space needs its defrost water piped, and the pipe traced."""
    if unit.kind.value != "heat_pump":
        return []
    if not unit.pan_drain_ref:
        return [_fail(
            f"{unit.tag} stands on deck {deck_tag} with no pan_drain_ref: a heat pump sheds "
            f"defrost meltwater through every winter, and this one sheds it over whatever is "
            f"under the deck",
            (unit.tag, deck_tag),
            fix="author a condensate PipeRun to a receptor and name it in pan_drain_ref")]
    run = runs.get(unit.pan_drain_ref)
    if run is None:
        return [_fail(
            f"{unit.tag} names pan_drain_ref {unit.pan_drain_ref}, which is not a PipeRun in "
            f"the plan",
            (unit.tag, unit.pan_drain_ref))]
    if not run.freeze_protection:
        return [_fail(
            f"condensate run {run.tag} from {unit.tag} carries no freeze_protection: an "
            f"untraced defrost line on an exposed deck is a line full of ice by midwinter, "
            f"which puts the meltwater back on the deck the pipe was added to keep it off",
            (unit.tag, run.tag),
            fix="author freeze_protection on the run (self-regulating heater cable)")]
    return []


@check(Tier.ADVISORY, "mep.deck_equipment_anchorage_capacity")
def deck_equipment_anchorage_capacity(ctx: CheckContext) -> list[Finding]:
    """The question ``deck_equipment_support_coverage`` names and does not answer.

    One item per unit, because that is the thing an anchorage is designed for — a cabinet's
    published foot-hole pattern, its projected area, and the deck's own share of the storey
    shear (#64 works through why the frame's grid and the feet's grid are not the same
    grid). No calculation is registered, by decision: no wind capacity calc is in scope. So
    each item reports UNKNOWN and blocks exactly as the coverage UNKNOWN it replaced did,
    and the difference is that it is now a named thing a seal can cover instead of a
    sentence at the end of a passing row.
    """
    from typehaus.engineering import item_id

    out: list[Finding] = []
    for unit in sorted(_graded_units(ctx), key=lambda e: e.tag):
        out.append(_engineered(
            ctx, "mep.deck_equipment_anchorage_capacity",
            item_id(_ANCHORAGE_KIND, unit.tag),
            f"{unit.tag}'s anchorage to its deck is covered "
            f"(mep.deck_equipment_support_coverage) but its CAPACITY is not evaluated: this "
            f"engine derives no tributary area, force coefficient or load-path share for "
            f"it, and an anchor schedule without a load is a drawing rather than a "
            f"calculation",
            (unit.tag,), code="IRC M1401.4 / ASCE 7-16 §29",
            fix=f"seal `{_ANCHORAGE_KIND}/{unit.tag}` in engineering.toml"))
    return out


def _graded_units(ctx: CheckContext) -> list:
    """The equipment ``deck_equipment_support_coverage`` actually grades — same population.

    Derived by asking that check which units it reported on rather than re-deriving the
    deck-and-storey scoping here. A second opinion about which units stand on a deck would
    drift from the first within a month, which is the drift this module's own docstring
    warns about for its inputs.
    """
    tags = {finding.element_tags[0] for finding in deck_equipment_support(ctx)
            if finding.element_tags}
    return [e for e in ctx.plan.all_elements()
            if isinstance(e, Equipment) and e.tag in tags]
