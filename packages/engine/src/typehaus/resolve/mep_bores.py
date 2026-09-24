"""What a trade may cut out of a framing member, and what it may not.

IRC R502.8 (joists) and R602.6 / R602.6.1 (studs and plates) are the two sections this
engine's jurisdiction profile has carried on its **not-covered** list since the profile was
written. That was honest — nothing graded them — and it is also the largest hole a routing
proposal can fall into: a search that finds a lane through a wall has proposed boring every
stud on the way, and until now nothing at all said whether the holes were legal.

The rules are stated here as **data plus predicates**, in ``resolve`` rather than in
``checks``, for the same reason ``mep_envelopes`` is: a router must aim at the same rule the
check grades it by, and the leaf rule forbids the router reaching into ``checks``.

**Three things this module refuses to do.**

* **It never invents a rule for an engineered member.** An LVL, an I-joist, an open-web
  truss and an LSL rim are cut to the *fabricator's* chart and no code table describes them.
  A verdict for one of those is ``None`` — UNKNOWN — and a consumer prints that rather than
  applying R502.8 to a product R502.8 has never governed. A generic "open webs are borable"
  is not evidence that THIS hole is.
* **It never proposes a repair.** R602.6.1's 16 ga tie is stated as the *condition under
  which a cut plate is acceptable*, not as something an engine adds to a model. Introducing
  a strap to make a route legal is a structural redesign, and those belong to a person.
* **It grades what is authored as well as what is proposed.** A notch somebody drew is the
  same question as a notch somebody is about to propose, and a module that only answered the
  second would be a router's private opinion rather than a rule about the house.

Scalar rules only; which members a run's leg crosses is ``mep_bore_geometry``.
``houses/catlin/notes/framing_bore_limits.md`` is the hand-worked oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN

# The member geometry lives in `mep_bore_geometry`; re-exported for existing callers.
from typehaus.resolve.mep_bore_geometry import _CUTTABLE_CATEGORIES as _CUTTABLE_CATEGORIES
from typehaus.resolve.mep_bore_geometry import MemberCut as MemberCut
from typehaus.resolve.mep_bore_geometry import leg_crossings as leg_crossings

#: R502.8.1: a bored hole in a solid-sawn joist keeps 2" clear of top and bottom, and is no
#: nearer than 2" to any other hole or notch.
JOIST_EDGE_CLEAR_IN = 2.0
JOIST_HOLE_SPACING_IN = 2.0
#: R502.8.1: hole <= D/3; notch <= D/6 and not in the middle third of the span; an END notch
#: (within D of the bearing) <= D/4; a notch no longer than D/3.
JOIST_HOLE_FRACTION = 1.0 / 3.0
JOIST_NOTCH_FRACTION = 1.0 / 6.0
JOIST_END_NOTCH_FRACTION = 1.0 / 4.0
JOIST_NOTCH_LENGTH_FRACTION = 1.0 / 3.0

#: R602.6: fractions of the stud's DEPTH (its 5 1/2" dimension on a 2x6 wall).
STUD_NOTCH_BEARING = 0.25
STUD_BORE_BEARING = 0.40
STUD_NOTCH_NONBEARING = 0.40
STUD_BORE_NONBEARING = 0.60
#: R602.6: a doubled stud may be bored to 60%, **and no more than two successive** doubled
#: studs may be so bored. The count is the caller's to track; this module states the limit.
STUD_BORE_DOUBLED = 0.60
STUD_BORE_DOUBLED_MAX_SUCCESSIVE = 2
#: R602.6: the edge of a bore or notch stays 5/8" from the edge of the stud.
STUD_EDGE_CLEAR_IN = 0.625
#: Not code: R602.6 is written about a stud running floor to plate. A member shorter than
#: twice its depth (a cripple over a header) is a block, and a bore in it is UNKNOWN.
STUD_MIN_LENGTH_DEPTHS = 2.0

#: R602.6.1: a top plate cut or notched more than 50% of its width needs a galvanized metal
#: tie **16 ga (0.054") x 1 1/2"** across and 6" past the opening each way, fastened with
#: eight 10d nails each side.
PLATE_CUT_FRACTION = 0.50
PLATE_TIE_GAUGE_IN = 0.054
PLATE_TIE_WIDTH_IN = 1.5
PLATE_TIE_LAP_IN = 6.0
PLATE_TIE_NAILS_EACH_SIDE = 8

#: Section shapes no code table governs. A verdict about one of these is UNKNOWN, always.
ENGINEERED_SHAPES = frozenset({"i_joist", "floor_truss", "roof_truss"})

#: Products whose section resolves as a plain rectangle and which R502.8 still does not
#: govern. ``cross_section`` reads ``1.75x11.875 LVL`` as a ``rect``, because for framing
#: geometry it IS one — but a laminated veneer member is cut to Weyerhaeuser's chart and
#: applying a solid-sawn table to it is exactly the mistake this module refuses to make.
#: Matched on the profile string, which is where the product name lives.
ENGINEERED_MARKERS = ("lvl", "lsl", "psl", "glulam", "i-joist", "truss", "rim")


@dataclass(frozen=True)
class BoreVerdict:
    """One cut, graded. ``ok is None`` means **no published rule reaches this member**.

    ``limit_in`` is the number the rule allows and ``actual_in`` what was asked for, so a
    consumer can print the margin rather than the verdict alone — "0.44" over" is actionable
    and "FAIL" is not.
    """

    ok: bool | None
    kind: str  # "bore" | "notch" | "plate_cut"
    actual_in: float
    limit_in: float | None
    basis: str
    #: What a person has to do for an otherwise-illegal cut to become legal. Stated, never
    #: applied: introducing a strap to make a route legal is a structural redesign.
    remedy: str | None = None

    @property
    def unknown(self) -> bool:
        return self.ok is None


def _engineered(section: Any, profile: str, what: str) -> BoreVerdict | None:
    if section is None:
        return BoreVerdict(None, what, 0.0, None,
                           f"{profile!r} resolves no cross-section, so nothing can be "
                           "measured against it")
    text = profile.lower()
    if (section.shape in ENGINEERED_SHAPES
            or any(marker in text for marker in ENGINEERED_MARKERS)):
        return BoreVerdict(
            None, what, 0.0, None,
            f"{profile} is an engineered member: it is cut to the fabricator's chart and "
            "no IRC table describes it. This engine does not hold that chart, and a "
            "generic 'open webs are borable' is not evidence that THIS hole is",
            remedy="get the hole's diameter and its allowable zone along the span from the "
                   "manufacturer's literature and author it")
    return None


def joist_bore(profile: str, diameter_in: float, *, edge_clear_in: float | None = None,
               nearest_cut_in: float | None = None) -> BoreVerdict:
    """IRC R502.8.1 on a bored hole in a solid-sawn joist.

    Three separate limits and the report names which one bit. A check that collapsed them
    into one boolean would say "illegal" about a 1" hole that is merely too close to its
    neighbour, which is a different thing to fix.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "bore")
    if engineered is not None:
        return engineered
    depth_in = section.depth_m / M_PER_IN
    limit = depth_in * JOIST_HOLE_FRACTION
    if diameter_in > limit + 1e-9:
        return BoreVerdict(False, "bore", diameter_in, limit,
                           f"IRC R502.8.1: a bored hole in a {profile} may not exceed D/3 = "
                           f'{limit:.2f}" and this is {diameter_in:.2f}"')
    if edge_clear_in is not None and edge_clear_in < JOIST_EDGE_CLEAR_IN - 1e-9:
        return BoreVerdict(False, "bore", edge_clear_in, JOIST_EDGE_CLEAR_IN,
                           f'IRC R502.8.1: a hole stays 2" clear of the top and bottom of a '
                           f'{profile} and this leaves {edge_clear_in:.2f}"')
    if nearest_cut_in is not None and nearest_cut_in < JOIST_HOLE_SPACING_IN - 1e-9:
        return BoreVerdict(False, "bore", nearest_cut_in, JOIST_HOLE_SPACING_IN,
                           f'IRC R502.8.1: a hole stays 2" from any other hole or notch and '
                           f'this is {nearest_cut_in:.2f}" from one')
    return BoreVerdict(True, "bore", diameter_in, limit,
                       f'IRC R502.8.1: {diameter_in:.2f}" in a {profile} against the D/3 = '
                       f'{limit:.2f}" limit, 2" clear of both edges')


def joist_notch(profile: str, depth_of_notch_in: float, *, length_in: float | None = None,
                at_end: bool = False, in_middle_third: bool = False) -> BoreVerdict:
    """IRC R502.8.1 on a notch. The middle third is the one a table cannot express."""
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "notch")
    if engineered is not None:
        return engineered
    depth_in = section.depth_m / M_PER_IN
    if in_middle_third:
        return BoreVerdict(False, "notch", depth_of_notch_in, 0.0,
                           f"IRC R502.8.1: no notch at all in the middle third of a "
                           f"{profile}'s span — that is where the bending moment is")
    limit = depth_in * (JOIST_END_NOTCH_FRACTION if at_end else JOIST_NOTCH_FRACTION)
    where = "at the bearing" if at_end else "in the outer thirds"
    if depth_of_notch_in > limit + 1e-9:
        return BoreVerdict(False, "notch", depth_of_notch_in, limit,
                           f"IRC R502.8.1: a notch {where} in a {profile} may not exceed "
                           f'{"D/4" if at_end else "D/6"} = {limit:.2f}" and this is '
                           f'{depth_of_notch_in:.2f}"')
    length_limit = depth_in * JOIST_NOTCH_LENGTH_FRACTION
    if length_in is not None and length_in > length_limit + 1e-9:
        return BoreVerdict(False, "notch", length_in, length_limit,
                           f"IRC R502.8.1: a notch in a {profile} may be no longer than "
                           f'D/3 = {length_limit:.2f}" and this is {length_in:.2f}"')
    return BoreVerdict(True, "notch", depth_of_notch_in, limit,
                       f'IRC R502.8.1: {depth_of_notch_in:.2f}" {where} in a {profile}, '
                       f'against the {limit:.2f}" limit')


def stud_bore(profile: str, diameter_in: float, *, bearing: bool = True,
              doubled: bool = False, length_in: float | None = None) -> BoreVerdict:
    """IRC R602.6 on a bored hole through a stud.

    ``bearing`` is the wall's own property and the caller must know it: the difference
    between 40% and 60% of a 2x6 is nearly an inch of pipe, which is the whole question for
    a 2" branch.

    ``length_in`` is the member's own length. Under ``STUD_MIN_LENGTH_DEPTHS`` depths it is
    UNKNOWN, never graded: the depth rules would PASS a 4" hole in a 6.56" cripple that
    leaves two 1.28" slivers, and nothing published governs a block that short.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "bore")
    if engineered is not None:
        return engineered
    # A stud's DEPTH is the wall's thickness dimension — the 5 1/2" of a 2x6 — and that is
    # what R602.6's percentages are of. `cross_section` puts the larger face in depth_m.
    depth_in = max(section.depth_m, section.width_m) / M_PER_IN
    if diameter_in >= depth_in - 1e-9:
        # **Wider than the stud: this is not a bore at all.** A 6" duct does not go
        # THROUGH a 2x6, it goes through a framed opening with a header over it, and
        # R602.6 has nothing to say about that — the section is about holes drilled in
        # members that stay whole. Reporting "a 6" bore exceeds 60% of 5 1/2"" is
        # arithmetic about a hole nobody would drill. Nothing in this engine grades a
        # header over a duct penetration, so the honest answer is UNKNOWN and the reason.
        return BoreVerdict(
            None, "bore", diameter_in, None,
            f'a {diameter_in:.2f}" penetration is wider than the {depth_in:.2f}" depth of '
            f"a {profile}, so it is a framed opening with a header over it and not a bore. "
            "IRC R602.6 governs holes drilled in members that stay whole and does not "
            "reach this; where a header resolves, `mep.run_through_header` names what the "
            "run passes and why no table grades it",
            remedy="draw the opening and its header, or take the run through a floor bay "
                   "instead of across the wall")
    if length_in is not None and length_in < STUD_MIN_LENGTH_DEPTHS * depth_in - 1e-9:
        return BoreVerdict(
            None, "bore", diameter_in, None,
            f'a {diameter_in:.2f}" bore through a {length_in:.2f}" {profile} leaves '
            f'{max(0.0, length_in - diameter_in):.2f}" of wood along it: the member is '
            f'shorter than {STUD_MIN_LENGTH_DEPTHS:g} x its {depth_in:.2f}" depth = '
            f'{STUD_MIN_LENGTH_DEPTHS * depth_in:.2f}", a block rather than a stud. IRC '
            "R602.6 is written about a stud running floor to plate and publishes nothing "
            "for this",
            remedy="take the run through a full-height stud, or have the hole in this "
                   "block designed and author it")
    fraction = (STUD_BORE_DOUBLED if doubled
                else STUD_BORE_BEARING if bearing else STUD_BORE_NONBEARING)
    limit = depth_in * fraction
    edge = (depth_in - diameter_in) / 2.0
    label = ("a doubled stud" if doubled
             else "a bearing-wall stud" if bearing else "a non-bearing stud")
    extra = (f"; no more than {STUD_BORE_DOUBLED_MAX_SUCCESSIVE} successive doubled studs "
             "may be bored to this" if doubled else "")
    if diameter_in > limit + 1e-9:
        return BoreVerdict(False, "bore", diameter_in, limit,
                           f"IRC R602.6: a bore in {label} ({profile}) may not exceed "
                           f'{fraction:.0%} of {depth_in:.2f}" = {limit:.2f}" and this is '
                           f'{diameter_in:.2f}"{extra}',
                           remedy=None if bearing else "none needed on a non-bearing wall "
                                                       "beyond moving the run to a clear bay")
    if edge < STUD_EDGE_CLEAR_IN - 1e-9:
        return BoreVerdict(False, "bore", edge, STUD_EDGE_CLEAR_IN,
                           f'IRC R602.6: 5/8" of stud must remain either side of a bore in '
                           f'a {profile} and this leaves {edge:.3f}"')
    return BoreVerdict(True, "bore", diameter_in, limit,
                       f'IRC R602.6: {diameter_in:.2f}" through {label} ({profile}), '
                       f'against the {fraction:.0%} = {limit:.2f}" limit, {edge:.3f}" of '
                       f"stud either side{extra}")


def stud_notch(profile: str, depth_of_notch_in: float, *,
               bearing: bool = True) -> BoreVerdict:
    """IRC R602.6 on a notch cut into the face of a stud."""
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "notch")
    if engineered is not None:
        return engineered
    depth_in = max(section.depth_m, section.width_m) / M_PER_IN
    fraction = STUD_NOTCH_BEARING if bearing else STUD_NOTCH_NONBEARING
    limit = depth_in * fraction
    label = "a bearing-wall stud" if bearing else "a non-bearing stud"
    ok = depth_of_notch_in <= limit + 1e-9
    return BoreVerdict(
        ok, "notch", depth_of_notch_in, limit,
        f"IRC R602.6: a notch in {label} ({profile}) may not exceed {fraction:.0%} of "
        f'{depth_in:.2f}" = {limit:.2f}" and this is {depth_of_notch_in:.2f}"'
        if not ok else
        f'IRC R602.6: {depth_of_notch_in:.2f}" notched from {label} ({profile}), against '
        f'the {fraction:.0%} = {limit:.2f}" limit',
        remedy=None if ok else "bore rather than notch, or take the run to a clear bay")


def top_plate_cut(profile: str, cut_in: float, *, tie: bool | None = None,
                  through_in: float | None = None,
                  spans_width: bool = False, governed: bool = True) -> BoreVerdict:
    """IRC R602.6.1 on a cut or notched top plate.

    **Over 50% is not illegal, it is conditional**, and that distinction is the whole value
    of this function: a cut plate with the tie on it is built every day. ``tie`` is the
    caller's reading of whether the model says the strap is there — ``True`` a
    ``PlateTie`` covers this cut, ``False`` none does, ``None`` the caller did not look
    (and the verdict stays the pre-2026-09-19 UNKNOWN-shaped "conditional"). Nothing here
    adds a strap to a model: the condition is reported as a ``remedy`` a person applies.

    **A penetration as wide as the plate is not a plate cut**, exactly as it is not a stud
    bore: an 18" duct does not notch a 2x4 top plate, it goes through a framed opening with
    a header over it, and R602.6.1 — which is about a plate that stays continuous either
    side of a notch — has nothing to say about it. Nine of catlin's thirteen were that
    case, reported as "18.00\" out of a 3.50\" plate", which is arithmetic about a notch
    nobody would cut. ``header_bore`` is the question those actually ask.

    **Nor is a run that takes the plate's whole thickness across its whole width**
    (``through_in``, ``spans_width`` → ``MemberCut``): a 2.38" vent laid through a 1.50"
    plate leaves nothing of it at that station, whatever fraction of the width it measures.

    **R602.6.1 reaches "an exterior wall or interior load-bearing wall" and no other.**
    ``governed=False`` is the caller saying the plate is an interior non-bearing
    partition's: a cut there is not the section's business and passes on that ground.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    engineered = _engineered(section, profile, "plate_cut")
    if engineered is not None:
        return engineered
    width_in = max(section.depth_m, section.width_m) / M_PER_IN
    limit = width_in * PLATE_CUT_FRACTION
    if cut_in >= width_in - 1e-9:
        return BoreVerdict(
            None, "plate_cut", cut_in, None,
            f'a {cut_in:.2f}" penetration is as wide as the {width_in:.2f}" width of a '
            f"{profile} top plate, so the plate is interrupted rather than notched: this is "
            "a framed opening with a header over it, and IRC R602.6.1 governs a plate that "
            "stays continuous either side of a cut",
            remedy="draw the opening and its header — `mep.run_through_header` grades what "
                   "the run then passes")
    thickness_in = min(section.depth_m, section.width_m) / M_PER_IN
    if spans_width and through_in is not None and through_in >= thickness_in - 1e-6:
        return BoreVerdict(
            None, "plate_cut", cut_in, None,
            f'a {cut_in:.2f}" run crosses the full {width_in:.2f}" width of a {profile} top '
            f'plate and takes all {thickness_in:.2f}" of its thickness, so the plate is '
            "severed rather than notched: this is a framed opening with a header over it, "
            "and IRC R602.6.1 governs a plate that stays continuous either side of a cut",
            remedy="draw the opening and its header — `mep.run_through_header` grades what "
                   "the run then passes")
    if not governed:
        return BoreVerdict(True, "plate_cut", cut_in, None,
                           f'IRC R602.6.1 governs the top plates of exterior and interior '
                           f'load-bearing walls; this is an interior non-bearing partition, '
                           f'so {cut_in:.2f}" out of its {profile} plate needs no tie')
    if cut_in <= limit + 1e-9:
        return BoreVerdict(True, "plate_cut", cut_in, limit,
                           f'IRC R602.6.1: {cut_in:.2f}" out of a {profile} top plate, '
                           f'under the {limit:.2f}" (50%) line that triggers a tie')
    detail = (f"a galvanized metal tie {PLATE_TIE_GAUGE_IN:.3f}\" (16 ga) x "
              f"{PLATE_TIE_WIDTH_IN:g}\" across the cut, lapping {PLATE_TIE_LAP_IN:g}\" "
              f"past the opening each way, with {PLATE_TIE_NAILS_EACH_SIDE} 10d nails "
              "each side")
    over = (f'IRC R602.6.1: {cut_in:.2f}" out of a {profile} top plate is more than 50% of '
            f'its {width_in:.2f}" width, which is permitted WITH a tie and not without one')
    if tie is True:
        return BoreVerdict(True, "plate_cut", cut_in, limit,
                           f"{over} — and this model authors the tie")
    if tie is False:
        return BoreVerdict(False, "plate_cut", cut_in, limit,
                           f"{over}, and no PlateTie in this model covers it",
                           remedy=f"fasten {detail}, and author it")
    return BoreVerdict(True, "plate_cut", cut_in, limit, over,
                       remedy=f"fasten {detail}")


def header_bore(profile: str, diameter_in: float, *,
                through_in: float | None = None, chart: Any = None,
                from_bearing_in: float | None = None, span_in: float | None = None,
                edge_clear_in: float | None = None, nearest_cut_in: float | None = None,
                nearest_diameter_in: float | None = None,
                plies: int | None = None) -> BoreVerdict:
    """A hole a run would take through a header over an opening.

    ``chart`` is an authored :class:`~typehaus.model.refs_holes.PublishedHole` — the maker's
    own ALLOWABLE HOLES row — and it is the ONLY thing that turns this verdict into a
    PASS or a FAIL. Absent, the answer is what it has always been: UNKNOWN with the numbers.

    **The engineered early return moves BELOW the chart lookup, and that is the whole
    feature.** A Trus Joist header trips ``ENGINEERED_MARKERS`` on ``lvl``/``lsl``, and
    "cut to the fabricator's chart" was the refusal — so handing the engine that very chart
    has to be reachable. With no chart the refusal stands, word for word.

    ``through_in`` is how much of the diameter the member actually loses (→ ``MemberCut``);
    below the diameter the run only clips the member and the cut is a **notch**. ``None``
    keeps the whole diameter, which is what an unqualified caller means.

    **There is no prescriptive table for this and none is invented here.** R502.8.1 governs
    floor JOISTS, R602.6 governs STUDS, and neither reaches a header: a header is a bending
    member collecting the whole tributary load over an opening into two jack studs, and what
    a hole does to it depends on where along the span it is and what it carries — which is
    an engineering question, not a table lookup. Grading a header against the joist row
    because the section is also a rectangle is exactly the mistake ``_engineered`` exists to
    refuse, one product family further along.

    So the verdict is **UNKNOWN with the numbers printed**, which is the actionable half: a
    person reading "4.00" through a 7.25" 2-2x8 header" can act, and "not covered" alone
    cannot. The one determinate case is a penetration **as deep as the member**: that is not
    a hole, it is the header's removal, and no table is needed to say a severed header does
    not carry the opening. That is a FAIL.

    R502.8.1's D/3 is quoted for SCALE only and is stated as non-binding in the basis text.
    """
    from typehaus.resolve.framing.profiles import cross_section

    cut_in = diameter_in if through_in is None else through_in
    notch = cut_in < diameter_in - 1e-6
    what = "notch" if notch else "bore"
    aside = (f' (the run\'s {diameter_in:.2f}" outside only clips the member: a notch off a '
             "face, not a full-diameter bore)" if notch else "")
    section = cross_section(profile)
    if section is None:
        return BoreVerdict(None, what, cut_in, None,
                           f"{profile!r} resolves no cross-section, so nothing can be "
                           "measured against it")
    depth_in = section.depth_m / M_PER_IN
    if chart is not None:
        from typehaus.resolve.mep_hole_chart import chart_verdict, hole_chart_drift

        drift = hole_chart_drift(chart, profile, span_in=span_in, plies=plies)
        if drift is not None:
            return BoreVerdict(
                None, what, cut_in, None,
                f"a published hole chart is authored on this opening but it does not "
                f"describe this header: {drift} — so it grades nothing here",
                remedy="re-read the chart for the member that is actually in the model, or "
                       "put the member the chart was read for back")
        return chart_verdict(chart, profile, depth_in, cut_in, diameter_in, notch,
                             from_bearing_in=from_bearing_in, span_in=span_in,
                             edge_clear_in=edge_clear_in,
                             nearest_cut_in=nearest_cut_in,
                             nearest_diameter_in=nearest_diameter_in)
    engineered = _engineered(section, profile, what)
    if engineered is not None:
        return engineered
    if cut_in >= depth_in - 1e-9:
        return BoreVerdict(
            False, "bore", cut_in, depth_in,
            f'a {cut_in:.2f}" penetration through a {profile} header is as deep as the '
            f'{depth_in:.2f}" member itself: that is not a hole drilled in a member that '
            "stays whole, it is the header's removal, and a severed header does not carry "
            "the opening under it",
            remedy="take the run under the header through the rough opening, over the wall, "
                   "or through a floor bay — or frame a second opening and header it")
    joist_scale = depth_in * JOIST_HOLE_FRACTION
    return BoreVerdict(
        None, what, cut_in, None,
        f'{cut_in:.2f}" through a {profile} header ({depth_in:.2f}" deep){aside}: NO IRC '
        "table publishes a bore or notch limit for a header. R502.8.1 governs floor joists "
        "and R602.6 studs; a header collects an opening's whole tributary load over a span "
        "and what a hole costs it depends on where along that span it sits. For scale only, "
        f'and binding on nothing here, the joist rule\'s D/3 would be {joist_scale:.2f}"',
        remedy="have the header's designer state the allowable hole and its zone along the "
               "span and author it, or route the run clear of the header")


def flat_header_cut(profile: str, cut_in: float) -> BoreVerdict:
    """A cut in an IRC R602.7.4 flat nonbearing header — a nailer, not a beam.

    "Load-bearing headers are not required in interior or exterior nonbearing walls": the
    flat 2x carries no tributary load, so ``header_bore``'s question (what a hole costs a
    bending member) is not asked of it and no table limits the cut. What it still does is
    give the jamb head and the finish a nailing surface, so the one thing graded is whether
    wood is left at the station: a cut through its whole 1 1/2" thickness is UNKNOWN.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    if section is None:
        return BoreVerdict(None, "notch", cut_in, None,
                           f"{profile!r} resolves no cross-section, so nothing can be "
                           "measured against it")
    thickness_in = min(section.width_m, section.depth_m) / M_PER_IN
    if cut_in >= thickness_in - 1e-6:
        return BoreVerdict(
            None, "notch", cut_in, thickness_in,
            f'a {cut_in:.2f}" run takes the whole {thickness_in:.2f}" of a flat {profile} '
            "nonbearing header (IRC R602.7.4): nothing is carried, but the door's head "
            "nailing is severed at this station",
            remedy="take the run above the nailer, or add a second flat member clear of it")
    return BoreVerdict(
        True, "notch", cut_in, thickness_in,
        f'IRC R602.7.4: a flat {profile} nonbearing header carries no load, so no rule '
        f'limits a cut in it; {cut_in:.2f}" off it leaves '
        f'{thickness_in - cut_in:.2f}" of the {thickness_in:.2f}" nailer at the head')


#: Every I-joist maker (TJI, LPI, BCI, AJS) forbids cutting, notching or boring a FLANGE, at
#: any station and any size: the one I-joist rule that needs no chart.
I_JOIST_FLANGE_CUT_IN = 0.0


def i_joist_flange_cut(profile: str, cut_in: float) -> BoreVerdict:
    """A run's surface ``cut_in`` into an I-joist flange: FAIL for anything above zero."""
    if cut_in <= I_JOIST_FLANGE_CUT_IN + 1e-9:
        return BoreVerdict(True, "notch", cut_in, I_JOIST_FLANGE_CUT_IN,
                           f"clear of both flanges of the {profile}")
    return BoreVerdict(
        False, "notch", cut_in, I_JOIST_FLANGE_CUT_IN,
        f'{cut_in:.3f}" into a flange of a {profile}: I-joist makers forbid cutting, '
        "notching or boring a flange at any size or station, so no chart permits it",
        remedy="move the run clear of the flange, or through the web inside the maker's "
               "hole zone")
