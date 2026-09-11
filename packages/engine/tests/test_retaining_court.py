"""``engineering/retaining_system.py`` against an independently hand-worked free body.

Two jobs, and the second is the more important one.

**The oracle.** ``houses/catlin/notes/sunken_garden_court_free_body.md`` §4 works the closed
court by hand, term by term, in a pass written before this calculation was encoded — the
discipline ``tests/test_wind_loads.py`` keeps for ``typehaus/wind.py`` and
``tests/test_retaining_wall_calc.py`` keeps for the isolated wall. A calculation that only
agrees with itself is not verified.

**The free-pass battery.** ``lateral_support="base"`` is the one field in this model that can
turn a FAIL into a PASS by being *authored*, so every condition ``_verify`` tests is broken
here in turn — the loop opened, the ref pointed at a non-member, the ref pointed at nothing,
the cross-member's concrete taken away — and each is asserted INCOMPLETE and **never OK**. A
verification that has never been shown to fail is not a verification; it is a comment.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.retaining_system import KIND

_M_PER_FT = 0.3048

# §4 of the note, at the graded case (at-rest 60 psf/ft, 110 pcf, mu 0.35 on the stone bed).
# Re-oracled by hand FOUR times. The first three took the top of the wall down: the footings
# rose 9" to become the court's walking surface (stem 10.37' -> 9.62', H 11.37' -> 10.62'),
# the tops came down 4" to the owner's 36"-above-grade cap (stem -> 9.2865', H -> 10.2865'),
# and on 2026-09-10 all five court walls came flush with the porch datum at 0'-0"
# (stem -> 9.1198', H -> 10.1198'). Thrust goes as H^2 while the resisting weights fall
# linearly, so all three of those pushed every one of these the same way, and were free.
#
# ** THE FOURTH IS DIFFERENT IN KIND AND IT SPENDS MARGIN. ** H does not move at all. Two
# PLAN dimensions do: the court's clear length 28'-0" -> 26'-0", which takes 2'-0" off each
# side wall, and the footing strip 8'-0" offset 6" -> 7'-0" centred, toe 4'-0" -> 3'-0".
#
# The DEMAND is untouched. The E-W thrusts cancel identically (see the cancellation test
# below), so the resultant is the south wall's thrust alone and the south wall is the
# court's WIDTH, which did not change. `_NOTE_RESULTANT_LB` is therefore the ONE number in
# this block that does not move, and that is a structural fact rather than a coincidence.
# Every capacity-side figure falls: 4'-0" of base friction gone from the run, and 150 plf
# off W as the strip narrows.
_NOTE_RESULTANT_LB = 61_446.0
_NOTE_CAPACITY_LB = 100_047.0
_NOTE_CANCELLED_LB = 100_362.0
_NOTE_SYSTEM_FS = 1.63
# §8: half the largest member's whole thrust, factored, against phi-Pn on a 12" x 17.5"
# section over a 20'-0" clear span. phi-Pn does not move with the wall height; Pu does.
#
# ** DO NOT READ A FALLING Pu AS PERMISSION TO SHRINK THE BEAM. ** The two shallower
# sections §8 once rejected (10 1/4" and 8 1/2") both PASS at this Pu, at d/c 0.81 and
# 0.98. What holds 17.5" is the sequencing argument and the absence of redundancy, not the
# ratio; §8's three-reason block is where that now lives.
_NOTE_STRUT_PU_LB = 49_157.0
_NOTE_STRUT_PHI_PN_LB = 103_655.0
# The exposure of the run above the authored yard, which is a RESULT of the flush tops and
# not the driver it used to be. `params/sunken_garden.RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN`.
_NOTE_EXPOSURE_IN = 40.0
_NOTE_EXPOSURE_BAND_IN = (36.0, 48.0)


def _results(plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(plan)
    return EngineeringResults(EngineeringContext(
        plan=plan, model=model, soil_class="GM"))


def test_the_court_reproduces_the_hand_worked_free_body(catlin_plan) -> None:
    """The whole of §4's system block, from the landed house."""
    record = _results(catlin_plan)[f"{KIND}/W-SG-ARCH"]
    assert record.status is Status.OK, record.summary

    states = {state.name: state for state in record.limit_states}
    # 1.80 against the 1.50 IRC R404.4 requires. Carried as required/achieved, so < 1 is fine.
    assert states["sliding"].capacity == pytest.approx(_NOTE_SYSTEM_FS, abs=0.01)
    assert states["sliding"].demand == pytest.approx(1.5)
    assert states["sliding"].ok

    assert states["strut compression"].demand == pytest.approx(_NOTE_STRUT_PU_LB, rel=0.001)
    assert states["strut compression"].capacity == pytest.approx(
        _NOTE_STRUT_PHI_PN_LB, rel=0.001)
    assert states["strut compression"].ok

    # The resultant and the capacity themselves, not just their ratio: two errors can cancel
    # inside a safety factor, and the note publishes both terms.
    assert f"{_NOTE_RESULTANT_LB:,.0f}" in record.summary
    assert f"{_NOTE_CAPACITY_LB:,.0f}" in record.summary
    assert any(f"{_NOTE_CANCELLED_LB:,.0f}" in note for note in record.notes)


def test_the_run_tops_out_on_the_porch_datum_and_its_exposure_is_a_result(
        catlin_plan) -> None:
    """One form height across all five court walls, and the 36" is derived from it.

    The owner's figure was always a BAND — around 36" out of the yard, up to about 48",
    because a freestanding wall this tall may be read as a guard. It was recorded in
    ``SPEC.retaining_top_ft`` as a MAXIMUM (``(site_grade_in + 36) / 12``), which is the
    opposite constraint: under it a lower yard would have pulled five wall tops down rather
    than letting the exposure grow into the band.

    Both halves are asserted here because each catches a different mistake. The flush tops
    catch a jog reappearing in the form line; the exposure catches the constraint being
    inverted again.

    **The exposure is measured against the AUTHORED YARD, not against ``Site.grade``.** The
    -2'-10" global plane is the near-house bench; the yard these walls stand in is -3'-4",
    and grading the exposure against the wrong one reports 34" for a wall that is 40" out
    of the ground beside it. That is also why this is an equality and not an inequality
    against the plane — see ``params/sunken_garden.RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN``.
    """
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tops = {wall.tag: round(wall.z1_m, 9) for wall in model.walls
            if wall.tag in {"W-SG-W1", "W-SG-E1", "W-SG-W2", "W-SG-E2", "W-SG-S"}}
    assert len(tops) == 5, tops
    assert set(tops.values()) == {0.0}, tops

    yard_m = min(spot.elevation.meters
                 for spot in catlin_plan.project.site.spot_elevations
                 if spot.kind == "grade")
    exposure_in = (0.0 - yard_m) / 0.0254
    assert exposure_in == pytest.approx(_NOTE_EXPOSURE_IN, abs=0.01)
    low, high = _NOTE_EXPOSURE_BAND_IN
    assert low <= exposure_in <= high


def test_the_east_west_thrusts_cancel_identically(catlin_plan) -> None:
    """The cancellation is exact, and this asserts it from the members' own numbers.

    ``W-SG-W2`` and ``W-SG-E2`` are derived in ``params/sunken_garden.py`` from the same
    symbols — not from matching literals — so there is no arithmetic by which one can differ
    from the other. The resultant is therefore the south wall's thrust alone, to the last
    decimal, and any drift here means the two walls have stopped being mirror images.
    """
    record = _results(catlin_plan)[f"{KIND}/W-SG-ARCH"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["thrust_W-SG-W2"] == pytest.approx(inputs["thrust_W-SG-E2"])
    assert inputs["length_W-SG-W2"] == pytest.approx(inputs["length_W-SG-E2"])

    south = inputs["thrust_W-SG-S"] * inputs["length_W-SG-S"]
    assert south == pytest.approx(_NOTE_RESULTANT_LB, rel=0.001)
    total = sum(inputs[f"thrust_{tag}"] * inputs[f"length_{tag}"]
                for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"))
    assert total - south == pytest.approx(_NOTE_CANCELLED_LB, rel=0.001)


def test_the_no_stone_sensitivity_is_the_designs_real_dependency(catlin_plan) -> None:
    """§5: at the site's own silty gravel (mu 0.25) the court reaches 1.16 and does NOT check.

    **This assertion pins a failure and that is the point.** The whole margin between 1.16
    and 1.63 is the washed-stone bed, and the bed is an authored claim
    (``FootingBedding.non_frost_susceptible``) about how something gets built. The note says
    so out loud; this says so in the suite, so that nobody later reads 1.63 as robust.

    Four passes have moved this row — 1.13 to 1.22 when the footings rose, to 1.26 at the
    36" cap, to 1.29 with the flush tops, to 1.16 when the court shortened and the strip
    narrowed — and none changed anything about the argument: it is still short of 1.50, and
    0.35 versus 0.25 is still the difference between a court that stands and one that does
    not. mu multiplies the same W on both sides, so no amount of geometry can close this
    gap. Only the bed can. The fourth pass moved it the WRONG way, knowingly: 1.29 -> 1.16
    is the accepted price of the 2'-0" and the 12", stated in §4 and carried in §5.
    """
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.retaining_system import _free_body, _loops, _members
    from typehaus.engineering.soil import presumptive
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    members = _loops(ctx)["W-SG-ARCH"]
    built, missing = _members(ctx, members, soil=presumptive("GM"), soil_pcf=110.0)
    assert not missing

    on_stone_demand, on_stone_capacity, _ = _free_body(built)
    assert on_stone_capacity / on_stone_demand == pytest.approx(_NOTE_SYSTEM_FS, abs=0.01)

    # Same walls, same thrust, the site's own class under the footings instead of the bed.
    site = presumptive("GM").friction_coefficient
    assert site == pytest.approx(0.25)
    on_site = sum(site * m.weight_plf * m.length_ft for m in built)
    assert on_site / on_stone_demand == pytest.approx(1.16, abs=0.01)
    assert on_site / on_stone_demand < 1.5


def test_every_member_quotes_the_courts_answer_and_carries_it_in_its_fingerprint(
        catlin_plan) -> None:
    """A wall's own record must depend on the court, visibly and in the hash.

    ``W-SG-E2``'s number depends on ``W-SG-W2`` standing across from it. If that dependency
    is not in the fingerprint, moving the far wall leaves a stale seal reading as fresh.
    """
    results = _results(catlin_plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        record = results[f"retaining_wall/{tag}"]
        assert record.status is Status.OK, record.summary
        by_name = {state.name: state for state in record.limit_states}
        # Per-wall sliding is gone: it is not a meaningful number for a wall in a loop.
        assert "sliding" not in by_name
        assert by_name["base restraint"].capacity == pytest.approx(_NOTE_SYSTEM_FS, abs=0.01)
        assert f"{KIND}/W-SG-ARCH" in by_name["base restraint"].citation

        inputs = {q.name: q.value for q in record.inputs}
        assert inputs["system_demand"] == pytest.approx(_NOTE_RESULTANT_LB, rel=0.001)
        assert inputs["system_capacity"] == pytest.approx(_NOTE_CAPACITY_LB, rel=0.001)
        # The conservative rows stay per-wall and stay comfortable.
        assert by_name["overturning"].ok and by_name["bearing"].ok
        assert by_name["eccentricity"].ok and by_name["stem flexure"].ok


def test_the_stem_is_reinforced_and_a_plain_one_would_not_be_covered_at_all(
        catlin_plan) -> None:
    """§6. The bar schedule is what makes the section work, and it is 4.5x, not marginal.

    ** ⚠ THE GEOMETRY BELOW IS A DELIBERATELY FROZEN MECHANICS ORACLE. DO NOT "CORRECT" IT
    TO THE HOUSE. ** It is the court as it stood when §6 was first worked — stem 10.3698',
    H 11.3698' — and the wall has come down three times since (to 9.62'/10.62' when the
    footings rose, to 9.2865'/10.2865' at the 36" cap, to 9.1198'/10.1198' when the five
    court walls came flush with the porch datum). Nothing here reads the plan, so it passes
    unchanged while the house moves under it, and that is the point: these twelve numbers
    are what an independent hand pass produced from these inputs, and the job of this test
    is to prove `stem_flexure` still reproduces them. Re-deriving the inputs from today's
    model would test the arithmetic against itself and verify nothing.

    The live house's stem ratio is pinned where it belongs, against the landed model:
    `test_the_court_reproduces_the_hand_worked_free_body` above, and
    `test_concrete_cover.test_the_third_inch_on_the_garden_stems_is_pinned`.
    """
    from typehaus.engineering.retaining_basis import _Geometry, analyse, stem_flexure
    from typehaus.engineering.soil import presumptive

    geometry = _Geometry(
        tag="W-SG-E2", stem_thickness_ft=1.0, stem_height_ft=10.3698,
        footing_width_ft=8.0, footing_depth_ft=1.0, toe_ft=4.0, heel_ft=3.0,
        retained_height_ft=11.3698)
    case = analyse(geometry, presumptive("GM"), at_rest=True, soil_pcf=110.0)

    plain_demand, plain_capacity, _how = stem_flexure(geometry, case)
    assert plain_demand == pytest.approx(17_841.0, rel=0.001)
    assert plain_capacity == pytest.approx(3_944.0, rel=0.001)
    assert plain_demand / plain_capacity == pytest.approx(4.52, abs=0.02)

    reinforced = _Geometry(**{**geometry.__dict__,
                              "vertical_reinforcement": '#6 @ 10" o.c.'})
    _demand, capacity, how = stem_flexure(reinforced, case)
    assert capacity == pytest.approx(21_639.0, rel=0.001)
    assert plain_demand / capacity == pytest.approx(0.82, abs=0.01)
    assert "0.528" in how
    # `#6 @ 12"` is the arithmetic minimum and is deliberately NOT what the house authors.
    thin = _Geometry(**{**geometry.__dict__, "vertical_reinforcement": '#6 @ 12" o.c.'})
    assert plain_demand / stem_flexure(thin, case)[1] > 0.97


def test_the_footings_narrowed_inboard_only_and_the_apron_did_not_move(catlin_model) -> None:
    """§3. The east and west edges are the invariant; the toe is what moves under them.

    The raised garden's apron measures its 3'-0" clear off these footings' OUTBOARD edges —
    the owner's figure, from the brief — so those edges may not move. **The premise of this
    test inverted on 2026-09-10 and its assertions did not, which is exactly what it is
    for.** The strip went 7'-0" -> 8'-0" offset 6" into the court, and has now come back to
    7'-0" CENTRED; the two spellings put the outboard reach in the same place
    (``96/24 - 6/12 == 84/24 == 3.5'``), so the x figures below survived a widening AND a
    narrowing unchanged. The toe edges moved both times, by the full 12", into the court
    where nothing is.

    ``FT-SG-S``'s y edges are the exception and move for a different reason: the court's
    clear length went 28'-0" -> 26'-0", so that whole wall walked 2'-0" north with its
    footing. Its own toe reach narrowed by the same 12" every other strip did.
    """
    edges = {}
    for solid in catlin_model.solids:
        if solid.tag in ("FT-SG-W2", "FT-SG-E2", "FT-SG-S"):
            xs = [x / _M_PER_FT for x, _ in solid.outline]
            ys = [y / _M_PER_FT for _, y in solid.outline]
            edges[solid.tag] = (min(xs), max(xs), min(ys), max(ys))

    # Outboard edges. The two x figures are the point of the test and have not moved through
    # either the widening or the narrowing.
    assert edges["FT-SG-W2"][0] == pytest.approx(4.5, abs=1e-6)
    assert edges["FT-SG-E2"][1] == pytest.approx(31.5, abs=1e-6)
    # -32.8333 until the court shortened: wall axis -27.3333 less half the 7'-0" strip.
    assert edges["FT-SG-S"][2] == pytest.approx(-30.8333, abs=1e-3)
    # Inboard edges, 12" back OUT of the court from where the 8'-0" strip put them.
    assert edges["FT-SG-W2"][1] == pytest.approx(11.5, abs=1e-6)
    assert edges["FT-SG-E2"][0] == pytest.approx(24.5, abs=1e-6)
    assert edges["FT-SG-S"][3] == pytest.approx(-23.8333, abs=1e-3)
    # 7'-0" overall on all three, and the heel still 3'-0".
    for tag, (x0, x1, y0, y1) in edges.items():
        span = (x1 - x0) if tag != "FT-SG-S" else (y1 - y0)
        assert span == pytest.approx(7.0, abs=1e-6), tag


def test_the_net_rim_laps_no_footing(catlin_model) -> None:
    """The court's one unasserted invariant, asserted (2026-09-10).

    ``SL-SG-FLOOR``'s ``outline`` spans the whole court and its five ``FO-SG-TOE-*`` voids
    cut it back over the five wall footings, so the rim bills NET concrete while every
    derivation that gates on ``category == "slab"`` still sees one floor. That only holds if
    the voids exactly cover the footings: a lap bills the same cubic foot twice, in two
    sections, and **nothing grades it.** ``structural.concrete_interference`` reports on
    ISOLATED pours and every ``FT-SG-*`` carries ``under=``, so a lap here reads as 0 FAIL.

    It lived as a comment in ``params/sunken_garden.py`` and as a hand measurement in the
    free-body note for five days. The 2026-09-10 pass moved BOTH of its inputs at once — the
    court's clear length and the strips' toe reach — which is the moment to stop measuring it
    by hand.
    """
    from shapely.geometry import Polygon

    solids = {s.tag: s for s in catlin_model.solids}
    rim = solids["SL-SG-FLOOR"]
    net = Polygon(list(rim.outline))
    assert rim.voids, "SL-SG-FLOOR resolves no voids; the FO-SG-* openings are not landing"
    for void in rim.voids:
        net = net.difference(Polygon(list(void)))
    assert net.area > 0, "the rim voided away entirely"

    # The five WALL strips, not all seven FT-SG-*. FT-SG-COL and FT-SG-FCOL are the belled
    # piers' bases: they top out at -11.62', two and a half feet under the rim's -9.41'
    # underside, and their shafts pass up through it. A plan lap there is not a lap.
    footings = ("FT-SG-W1", "FT-SG-W2", "FT-SG-E1", "FT-SG-E2", "FT-SG-S")
    assert set(footings) <= set(solids), sorted(set(footings) - set(solids))
    for tag in footings:
        # These five ARE the court's walking surface: their tops are the rim's top, not its
        # underside. That coplanarity is why a plan lap would be a real double bill.
        assert solids[tag].z1_m == pytest.approx(rim.z1_m, abs=1e-9), (
            f"{tag} no longer tops out on the court floor; this test's premise is that the "
            f"five wall strips and the rim share one plane")
        lap_sf = net.intersection(
            Polygon(list(solids[tag].outline))).area / _M_PER_FT ** 2
        assert lap_sf == pytest.approx(0.0, abs=1e-6), (
            f"the net rim laps {tag} by {lap_sf:.3f} sf — that concrete bills twice, once "
            f"in the slab section and once in the footing one, and no check grades it")


def test_the_grade_beam_holds_its_section_and_carries_the_court_floor(
        catlin_model) -> None:
    """W-SG-ARCH is 17 1/2" deep and NEITHER face moves — which now costs it its flushness.

    The court has been at three configurations and the beam has sat through all of them. It
    dropped 7 1/4" on 2026-09-03 for a flood step, leaving this beam standing 3 3/4" proud as
    a mow strip with FO-SG-ARCH cutting the rim around it; it came back flush on 2026-09-05
    (`court_step_down_in` -> 0), and the beam was buried again with the rim bearing directly
    on it and FO-SG-ARCH retired; and later the same day the three retaining footings rose 9"
    to become the court's walking surface.

    **BOTH faces are fixed by the strut, and that is the assertion here.** Dropping the TOP
    to a lowered floor leaves a 10 1/4" section: phi-Pn 60,712 lb against Pu 62,051, **d/c
    1.02, it fails**. Raising the BOTTOM with the retaining footings leaves 8 1/2", Ag
    102 in^2, phi-Pn ~50,300 lb against Pu 54,134 — **d/c ~1.08, it fails too**. So
    `_grade_beam_bottom` is now DECOUPLED from `_wall_bottom` and held, and the beam
    deliberately stands 9" proud below the footings it used to be flush with. The
    "one excavation, one stone plane" that flushness used to buy is gone; §8 of
    notes/sunken_garden_court_free_body.md says what replaces it.

    The 17 1/2" is the assertion that matters: it is the section §8 of the note grades.
    """
    beam = next(w for w in catlin_model.walls if w.tag == "W-SG-ARCH")
    court = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR")
    footing = next(s for s in catlin_model.solids if s.tag == "FT-SG-W2")

    # NOT flush any more, and by exactly the 9" the footings rose.
    assert (footing.z0_m - beam.z0_m) / _M_PER_FT * 12 == pytest.approx(9.0, abs=1e-6)
    # The footings' TOPS are the court's walking surface: the rim voids over them.
    assert footing.z1_m == pytest.approx(court.z1_m, abs=1e-9)
    assert (beam.z1_m - beam.z0_m) / _M_PER_FT * 12 == pytest.approx(17.5, abs=1e-6)
    # Buried: its top IS the rim slab's underside, so the court floor bears on it. Both
    # sides of this are the same expression in params/sunken_garden (`_grade_beam_top` and
    # `_rim_underside_in`), and that is exactly why FO-SG-ARCH could be retired.
    assert (court.z1_m - beam.z1_m) / _M_PER_FT * 12 == pytest.approx(3.5, abs=1e-6)
    # The court is flush with the basement floor plane again.
    assert court.z1_m / _M_PER_FT * 12 == pytest.approx(-109.4375, abs=1e-6)
    # The curb over that floor is the flood step, and it is 7 1/4" whatever happens here.
    curb = next(w for w in catlin_model.plan.all_elements()
                if getattr(w, "tag", None) == "W-B-S2")
    assert curb.top_elevation.inches - curb.bottom_elevation.inches == pytest.approx(7.25)


def test_the_front_columns_bell_does_not_reach_the_beam(catlin_model) -> None:
    """§7. Their plan outlines touch and their sections are 9" apart — so no shared bearing.

    An earlier scheme merged the two into one pour and gave the beam an intermediate bearing
    at midspan, halving its span. It is worth pinning that this is NOT what is built, because
    the strut's slenderness in §7 is computed on the full 20'-0" because of it.
    """
    bell = next(s for s in catlin_model.solids if s.tag == "FT-SG-FCOL")
    beam = next(w for w in catlin_model.walls if w.tag == "W-SG-ARCH")
    # 9", and back to 9" the long way round. It was 9" while the bell bore 42" under a flush
    # court; 16.25" while the bell followed the court's 7 1/4" flood step down and the beam
    # did not; and 9" again now that the court is flush and the bell is derived from the
    # 42" rule instead of pinned to where it happened to be. The span §7 grades is the full
    # 20'-0" in every one of those states, which is the point of pinning the gap at all.
    gap_in = (beam.z0_m - bell.z1_m) / _M_PER_FT * 12
    assert gap_in == pytest.approx(9.0, abs=0.01), "the bell and the beam must not touch"


# --------------------------------------------------------------------------------------
# The free-pass battery. Each of these breaks one condition in ``_verify`` and asserts the
# record goes INCOMPLETE, naming what is missing — never OK, and never silently OK-by-absence.
# --------------------------------------------------------------------------------------

def _mutated(tmp_path, replacements):
    from pathlib import Path

    from _helpers import copy_house

    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    house = copy_house(catlin, tmp_path / "house")
    source = house / "params" / "sunken_garden.py"
    text = source.read_text()
    for old, new in replacements:
        assert old in text, old
        text = text.replace(old, new)
    source.write_text(text)
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    return result.plan


def _court(plan):
    return _results(plan)[f"{KIND}/W-SG-ARCH"]


def test_opening_the_loop_is_incomplete_not_ok(tmp_path) -> None:
    """Delete the cross-member and the U is open again. **The headline free-pass case.**

    The walls still say ``lateral_support="base"`` and still name ``W-SG-ARCH``. Nothing in
    the authored claim changed — only the thing it claims stopped existing. If this returned
    OK, the field would be a switch that turns the calculation off.
    """
    plan = _mutated(tmp_path, [(
        '    FoundationWall(uid="SGW102AAAA", tag="W-SG-ARCH", start_node="N-SG-MW",',
        '    FoundationWall(uid="SGW102AAAA", tag="W-SG-ARCH-GONE", start_node="N-SG-MW",')])
    record = _court(plan)
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("W-SG-ARCH" in m for m in record.missing)
    assert record.status is not Status.OK

    # And every wall that leaned on it goes INCOMPLETE with it, rather than quietly
    # reverting to a free-cantilever PASS.
    results = _results(plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        wall = results[f"retaining_wall/{tag}"]
        assert wall.status is Status.INCOMPLETE, wall.summary


def test_a_ref_that_names_nothing_is_incomplete(tmp_path) -> None:
    """``base_restraint_ref`` pointed at a tag the model does not contain."""
    plan = _mutated(tmp_path, [
        ('base_restraint_ref="W-SG-ARCH"', 'base_restraint_ref="W-SG-IMAGINARY"')])
    record = _results(plan)[f"{KIND}/W-SG-IMAGINARY"]
    assert record.status is Status.INCOMPLETE
    assert any("W-SG-IMAGINARY" in m for m in record.missing)


def test_a_ref_that_names_a_wall_off_the_loop_is_incomplete(tmp_path) -> None:
    """Point the restraint at a real concrete wall that is on no common cycle.

    ``W-SG-W1`` is a real ``FoundationWall``, real cast concrete, in the same structure and
    even touching the same node — and it is a **bridge**, an open arm of the chain, restrained
    by nothing at its far end. Naming it must not work, and "it is a wall and it is concrete"
    must not be enough.
    """
    plan = _mutated(tmp_path, [
        ('base_restraint_ref="W-SG-ARCH"', 'base_restraint_ref="W-SG-W1"')])
    record = _results(plan)[f"{KIND}/W-SG-W1"]
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("closed structural loop" in m for m in record.missing)


def test_a_cross_member_with_no_concrete_is_incomplete(tmp_path) -> None:
    """The loop has to be CAST. A framed cross-member cannot deliver the strut force."""
    plan = _mutated(tmp_path, [(
        '''                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_grade_beam_top, bottom_elevation=_grade_beam_bottom,''',
        '''                   end_node="N-SG-ME", assembly="EXT_2X6",
                   top_elevation=_grade_beam_top, bottom_elevation=_grade_beam_bottom,''')])
    record = _court(plan)
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("concrete" in m for m in record.missing)


def test_half_authoring_the_claim_reaches_no_restraint(catlin_plan, tmp_path) -> None:
    """``lateral_support="base"`` without a ref, and a ref without ``"base"``.

    A half-authored claim is the shape a free pass arrives in, so neither half alone may
    reach a restrained grading. Dropping the ref leaves the walls in the retaining_wall
    suite with no system to quote — which must be INCOMPLETE, not a silent fall-back to the
    free-cantilever numbers that used to FAIL.
    """
    plan = _mutated(tmp_path, [
        ('lateral_support="base", base_restraint_ref="W-SG-ARCH"',
         'lateral_support="base"')])
    results = _results(plan)
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        record = results[f"retaining_wall/{tag}"]
        assert record.status is Status.INCOMPLETE, record.summary
        assert any("base restraint" in m for m in record.missing), record.missing


def test_a_base_restrained_wall_never_reaches_the_prescriptive_table(catlin_plan) -> None:
    """The most dangerous mis-step in the whole change, asserted directly.

    Table R404.1.2(8) footnote g presumes bracing top AND bottom. A ``"base"`` wall falling
    through to it would collect a prescriptive PASS with no engineering behind it — worse
    than the FAIL it replaced, because a FAIL is visible. ``_grade_one`` must send it to the
    R404.4 handoff beside ``"unsupported"``.
    """
    from _helpers import check_context

    from typehaus.checks.structural.foundation import foundation_unbalanced_fill
    from typehaus.findings import Authority, Result

    findings = foundation_unbalanced_fill(check_context(plan=catlin_plan))
    for tag in ("W-SG-W2", "W-SG-E2", "W-SG-S"):
        mine = [f for f in findings if tag in f.element_tags]
        assert mine, tag
        for finding in mine:
            assert finding.authority is Authority.ENGINEERED, finding.message
            assert finding.engineering_item == f"retaining_wall/{tag}"
            assert "R404.4" in finding.message
            assert "Table R404.1.2(8)" in finding.message
            assert finding.result is not Result.FAIL

    # And the two braced porch walls are still answered by the table, prescriptively.
    porch = [f for f in findings
             if "W-SG-W1" in f.element_tags or "W-SG-E1" in f.element_tags]
    assert porch
    assert all(f.authority is Authority.PRESCRIPTIVE and f.result is Result.PASS
               for f in porch), [f.message for f in porch]


def test_the_restrained_walls_stay_in_the_engineering_suite(catlin_plan) -> None:
    """A wall that stops being computed reads exactly like a wall with no problem."""
    from typehaus.engineering import EngineeringContext
    from typehaus.engineering.retaining_wall import enumerate_walls
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tags = set(enumerate_walls(EngineeringContext(plan=catlin_plan, model=model)))
    assert tags == {"W-SG-E2", "W-SG-S", "W-SG-W2"}
