"""``engineering/retaining_wall.py`` against an independently hand-worked screening.

This is the most important test in the engineering suite, and the reason is in the suite's
own claim: a record here asserts that it *mirrors what an engineer would compute*. A
calculation that only agrees with itself has not established that. So every calc module is
oracled against a note written in a separate pass, by hand, from the code — the discipline
``tests/test_wind_loads.py`` keeps for ``typehaus/wind.py``.

The oracle here is ``houses/catlin/notes/sunken_garden_retaining_screening.md`` §4: three
load cases × four limit states, twelve published numbers, all reproduced below.

Note what the oracle *says*: the walls reach 0.48-0.64 against sliding where IRC R404.4
requires 1.5. **These assertions pin a failure, and that is correct.** If a future edit makes
them pass, the wall changed or the arithmetic broke — and either way this test should be the
thing that notices.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.retaining_wall import KIND, _Geometry, analyse
from typehaus.engineering.soil import presumptive

# §2 of the note, ON THE NOTE'S OWN CONVENTION: 12" stem 9'-4 7/16" tall on a 7'-0" x 1'-0"
# footing centred on the wall axis, retaining 9.62' with the toe top AT the court floor.
#
# **This is deliberately no longer "as modelled", and it must not be re-synced.** The
# screening note read -9'-10 7/16" as the footing's underside when it is the footing's top
# (`resolve/envelope.py::_resolve_footing` — see `retaining_wall`'s module docstring), so its
# stem is a foot short and its H a foot short. That slip is *inside the frozen oracle*: these
# twelve numbers are what an independent hand pass produced from these inputs, and the job of
# the parametrised test below is to prove `analyse()` reproduces them from the same inputs.
# Correcting the geometry here would test the correction against itself and verify nothing.
#
# What the correction moves is `_geometry()` — the model-to-`_Geometry` conversion, which the
# oracle does not exercise — and that shows up in
# `test_catlin_reports_the_three_free_walls_as_over` below, where it belongs.
# `notes/sunken_garden_court_free_body.md` §1 works the convention question both ways.
#
# ** AND IT IS FROZEN AGAINST THE HOUSE AS WELL AS AGAINST THAT SLIP. ** These numbers are
# the court of 2026-08-30. The wall has come down three times since — 9.62' when the
# footings rose to the court plane, 9.2865' at the owner's 36" cap, 9.1198' when all five
# court walls came flush with the porch datum on 2026-09-10 — and the footing has gone
# 7'-0" to 8'-0" with a 6" offset. **None of that belongs here.** This module verifies that
# `analyse()` reproduces a hand pass from the hand pass's own inputs; it will keep passing
# while the house moves under it, by design. The landed house is graded in
# `test_retaining_court.py` and `test_retaining_footing_calc.py`, both of which read the
# plan and both of which were re-pinned at each of those three moves.
CATLIN_SG = _Geometry(
    tag="W-SG-E2",
    stem_thickness_ft=1.0,
    stem_height_ft=9.3698,
    footing_width_ft=7.0,
    footing_depth_ft=1.0,
    toe_ft=3.0,
    heel_ft=3.0,
    retained_height_ft=10.3698,
    toe_embedment_ft=7.0 / 12.0,
)

# §4's table, verbatim: (at_rest, soil pcf) -> (FS sliding, FS overturning, q_max, e).
#
# The note takes base friction from the SITE's class (GM, mu 0.25). The engine takes it from
# what the footing actually bears on, which for these three is 42" of replacement stone
# (`test_the_bearing_interface_is_the_stone_not_the_backfill` below) — so `analyse` is driven
# here with `base` defaulting to `soil`, reproducing the note on the note's own assumption.
# That separation is the point: the oracle checks the *mechanics*, and the interface choice
# is checked separately, so a change to either cannot hide inside the other.
ORACLE = {
    (False, 110.0): (0.58, 3.06, 1060.0, 0.39),
    (False, 130.0): (0.64, 3.43, 1002.0, 0.17),
    (True, 130.0): (0.48, 2.57, 1344.0, 0.63),
}


@pytest.mark.parametrize(("at_rest", "soil_pcf"), sorted(ORACLE))
def test_the_screening_reproduces_the_hand_calc(at_rest, soil_pcf) -> None:
    want_sliding, want_overturning, want_bearing, want_eccentricity = ORACLE[
        (at_rest, soil_pcf)]
    case = analyse(CATLIN_SG, presumptive("GM"), at_rest=at_rest, soil_pcf=soil_pcf)

    assert case.fs_sliding == pytest.approx(want_sliding, abs=0.005)
    assert case.fs_overturning == pytest.approx(want_overturning, abs=0.005)
    # The note rounds q_max to whole psf; 1 psf of rounding on a 1,000 psf number is not a
    # disagreement about the mechanics.
    assert case.bearing_psf == pytest.approx(want_bearing, abs=1.5)
    assert case.eccentricity_ft == pytest.approx(want_eccentricity, abs=0.005)


def test_the_thrust_matches_the_notes_own_figure() -> None:
    """§4's prose quotes the active thrust directly — a term-level check, not just a ratio.

    Two different errors can cancel inside a safety factor. This pins the numerator.
    """
    case = analyse(CATLIN_SG, presumptive("GM"), soil_pcf=110.0)
    assert case.thrust_plf == pytest.approx(2420.0, abs=5.0)


def test_passive_on_the_toe_is_under_one_percent_of_resistance() -> None:
    """The note's reason for the module neglecting passive by default, asserted rather than
    trusted: a 6 1/2" embedment contributes about 26 plf against a 2,420 plf thrust."""
    soil = presumptive("GM")
    with_passive = analyse(CATLIN_SG, soil, soil_pcf=110.0)
    without = analyse(
        _Geometry(**{**CATLIN_SG.__dict__, "toe_embedment_ft": 0.0}), soil, soil_pcf=110.0)
    contribution = with_passive.resistance_plf - without.resistance_plf
    assert contribution == pytest.approx(26.0, abs=5.0)
    assert contribution / with_passive.resistance_plf < 0.02


def test_a_wall_with_no_declared_soil_class_is_incomplete_not_guessed() -> None:
    """Guessing the ground is the one assumption a retaining wall cannot survive (#32)."""
    assert presumptive(None) is None
    assert presumptive("XX") is None


def test_catlin_grades_the_three_court_walls_through_their_base_restraint(
        catlin_plan) -> None:
    """End to end, through the registry, on the landed house.

    Graded as three ISOLATED free cantilevers, each resisting by its own base friction,
    these walls reach FS 0.73 against the 1.5 IRC R404.4 requires. ``W-SG-ARCH``, a buried
    12" x 17 1/2" grade beam, closes the court's north end, so ``W-SG-W2`` and ``W-SG-E2``
    face each other across 19'-0" of cast concrete and their thrusts cancel —
    ``engineering/retaining_system`` sums all three as one rigid body instead.

    Two things keep this from being the check being talked out of its finding:

    * the per-wall row is not deleted, it is REPLACED by ``base restraint``, which carries
      the court's own number and cites the item it came from; and
    * the demand went UP, not down. Crediting a permanent restraint concedes that the wall
      cannot move enough to shed to the active wedge, so these are graded at at-rest
      (60 psf/ft) where the free-cantilever branch grades at active (45).

    ``tests/test_retaining_court.py`` holds the oracle and the free-pass battery.
    """
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    results = EngineeringResults(EngineeringContext(
        plan=catlin_plan, model=model, soil_class="GM"))

    for tag in ("W-SG-E2", "W-SG-S", "W-SG-W2"):
        record = results[f"{KIND}/{tag}"]
        assert record.status is Status.OK, record.summary
        assert record.governing is not None
        assert record.governing.name == "base restraint", record.summary
        # 1.63 against 1.50. Carried as required/achieved, so the ratio is under 1.
        # It was 1.77, then 1.80 with the flush tops, and 1.63 since the court shortened
        # 28'-0" -> 26'-0" and the strips narrowed 8'-0" -> 7'-0" (2026-09-10). That is a
        # deliberate purchase, not a regression: notes/sunken_garden_court_free_body.md §4.
        assert record.ratio == pytest.approx(1.5 / 1.63, abs=0.02)
        by_name = {state.name: state for state in record.limit_states}
        # Per-wall sliding is not a meaningful number once the free body is wrong, so it is
        # gone rather than reported alongside a contradicting one.
        assert "sliding" not in by_name
        # Everything else stays on the wall's OWN conservative free body and still clears —
        # including the section check, which a base restraint does nothing for and which
        # the free-cantilever branch never computed.
        for name in ("overturning", "bearing", "eccentricity", "stem flexure"):
            assert by_name[name].ok, (tag, name, by_name[name])
        assert record.basis_version == "3"

    # Every wall the register computes is one a signoff can cover, one at a time.
    assert sorted(results[f"{KIND}/{t}"].item_id for t in ("W-SG-E2",)) == [
        "retaining_wall/W-SG-E2"]


def test_the_bearing_interface_is_the_stone_not_the_backfill(catlin_plan) -> None:
    """Sliding happens at the base, so mu describes what the footing sits on.

    These footings bear on 42" of ASTM C33 #57 washed crushed stone — a replacement section
    the model already carries as a ``FootingBedding``, authored non-frost-susceptible for the
    frost check. Taking friction from the silty gravel *behind the stem* reads the wrong side
    of the footing, and it is worth 0.25 -> 0.35 here.

    Asserted as a delta rather than an absolute so it cannot silently become a no-op: if the
    bedding stops being found, both numbers collapse together and this fails.
    """
    from typehaus.engineering import EngineeringContext
    from typehaus.engineering.retaining_wall import _base_interface, _retaining_walls
    from typehaus.engineering.soil import presumptive
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    wall = next(w for w in _retaining_walls(ctx) if w.tag == "W-SG-E2")

    base = _base_interface(ctx, wall)
    assert base is not None and base.friction_coefficient == pytest.approx(0.35)
    assert presumptive("GM").friction_coefficient == pytest.approx(0.25)

    on_backfill = analyse(CATLIN_SG, presumptive("GM"), soil_pcf=110.0)
    on_stone = analyse(CATLIN_SG, presumptive("GM"), soil_pcf=110.0, base=base)
    assert on_stone.fs_sliding > on_backfill.fs_sliding * 1.3
    # And it is still nowhere near enough. This assertion is the honest one: the correction
    # is real, and the wall still does not reach the code's factor.
    assert on_stone.fs_sliding < 1.5


def test_the_braced_basement_walls_are_not_in_this_suite(catlin_plan) -> None:
    """Scope: a wall braced top and bottom is a basement wall and the IRC table answers it.

    Pulling those into an engineered design would be the opposite error to the one this
    package exists to fix — it would send ten walls the code already answers to a consultant.
    """
    from typehaus.engineering import EngineeringContext
    from typehaus.engineering.retaining_wall import enumerate_walls
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tags = set(enumerate_walls(EngineeringContext(plan=catlin_plan, model=model)))
    assert tags == {"W-SG-E2", "W-SG-S", "W-SG-W2"}
    assert not any(tag.startswith("W-B-") for tag in tags)


# --- the column surcharge (finding 6) ----------------------------------------------------
#
# ``analyse`` took DEAD LOAD ONLY until 2026-09-11 — stem, footing and the soil column on
# the heel — and there was no surcharge term anywhere in the engineering package. A
# fixed-base cast column standing on a wall top delivers a service axial load AND its own
# base moment, both computed by ``deck_post`` on the column, and neither reached the
# concrete underneath it.
#
# Driven as a free function against hand arithmetic, which is what this module's own
# docstring keeps it a free function for.


def _hand(surcharge=None):
    from typehaus.engineering.soil import presumptive as _presumptive

    return analyse(CATLIN_SG, _presumptive("GM"), soil_pcf=110.0, surcharge=surcharge)


def test_no_surcharge_is_the_wall_as_it_was() -> None:
    """The default path must be byte-identical to the frozen oracle above, or the term is
    not a term — it is a rewrite. (It very nearly was: the first draft folded the column
    into ``resisting`` with a conditional that bound over the whole sum, zeroing the
    restoring moment on every wall in the house.)"""
    plain = _hand()
    assert plain.surcharge is None
    assert plain.fs_sliding == pytest.approx(ORACLE[(False, 110.0)][0], abs=0.01)
    assert plain.fs_overturning == pytest.approx(ORACLE[(False, 110.0)][1], abs=0.01)


def test_the_axial_helps_and_the_base_moment_hurts() -> None:
    """Term by term, and the two pull opposite ways — which is the whole reason a column
    cannot be folded in as one number.

    A 12" round cast column at ~3,500 lb service over a 20' wall is 175 plf; its governing
    base moment of ~2,500 lb-ft over the same run is 125 lb-ft/ft. The axial presses the
    footing down, so weight, friction and the restoring moment all rise. The moment is
    added to OVERTURNING whichever way it points, because wind reverses.
    """
    from typehaus.engineering.retaining_basis import Surcharge

    plain = _hand()
    loaded = _hand(Surcharge(axial_plf=175.0, moment_plf=125.0, arm_ft=3.5,
                             source="deck_post/PT-TEST"))

    assert loaded.weight_plf == pytest.approx(plain.weight_plf + 175.0, abs=0.5)
    # mu = 0.25 for GM: every pound of axial buys a quarter pound of sliding resistance.
    assert loaded.resistance_plf == pytest.approx(plain.resistance_plf + 0.25 * 175.0,
                                                  abs=0.5)
    assert loaded.resisting_moment == pytest.approx(
        plain.resisting_moment + 175.0 * 3.5, abs=1.0)
    assert loaded.overturning_moment == pytest.approx(
        plain.overturning_moment + 125.0, abs=0.5)
    # Sliding improves; overturning is pushed both ways and the net here is a wash to
    # within a percent, which is exactly why the term has to be carried rather than
    # assumed to be conservative in one direction.
    assert loaded.fs_sliding > plain.fs_sliding
    assert loaded.thrust_plf == pytest.approx(plain.thrust_plf), \
        "a base moment is not a thrust and must not enter the sliding DEMAND"


def test_the_moment_is_taken_as_overturning_whichever_way_it_points() -> None:
    """Wind reverses, so a sign that helps in one direction hurts in the other and the
    screening takes the one that hurts."""
    from typehaus.engineering.retaining_basis import Surcharge

    plus = _hand(Surcharge(axial_plf=0.0, moment_plf=400.0, arm_ft=3.5))
    minus = _hand(Surcharge(axial_plf=0.0, moment_plf=-400.0, arm_ft=3.5))
    assert plus.overturning_moment == pytest.approx(minus.overturning_moment)
    assert plus.overturning_moment > _hand().overturning_moment


def test_catlins_own_columns_stand_on_walls_this_module_does_not_enumerate(
        catlin_plan) -> None:
    """The machinery above fires on nothing in catlin, and that is a REAL GAP rather than
    a quiet pass — which is why it is asserted rather than left to be discovered.

    The four balcony corner columns stand on ``W-SG-W1`` and ``W-SG-E1``, both
    ``lateral_support="top_and_bottom"``. They are basement walls: ``retaining_wall`` does
    not enumerate them, IRC Table R404.1.2(8) answers them and publishes no surcharge
    column, and ``spread_footing`` skips their strip footings. So the reactions are named
    rather than graded — ``column_support/<tag>`` in ``deferred.py``, reported by
    ``structural.column_on_wall_support``. If this assertion ever flips, the surcharge
    becomes live on a real wall and ``_column_surcharges`` is what runs.
    """
    from typehaus.engineering import EngineeringContext
    from typehaus.engineering.retaining_wall import _column_surcharges
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    assert _column_surcharges(ctx) == {}

    from typehaus.engineering.deferred import _column_support_keys
    assert _column_support_keys(ctx) == ["W-SG-E1", "W-SG-W1"]
