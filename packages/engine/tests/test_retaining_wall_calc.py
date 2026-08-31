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
# footing centred on the wall axis, retaining 10.37' with the toe buried 6 1/2".
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


def test_catlin_reports_the_three_free_walls_as_over(catlin_plan) -> None:
    """End to end, through the registry, on the landed house.

    The three sunken-garden walls are the case the whole engineering register was built
    around: two checks delegate to one item id, and the item computes a real answer. The
    answer is that they do not check, which is what the note found by hand.
    """
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    results = EngineeringResults(EngineeringContext(
        plan=catlin_plan, model=model, soil_class="GM"))

    for tag in ("W-SG-E2", "W-SG-S", "W-SG-W2"):
        record = results[f"{KIND}/{tag}"]
        assert record.status is Status.OVER, record.summary
        assert record.governing is not None and record.governing.name == "sliding"
        # 0.725, and it moved twice from the note's 0.58 for two unrelated reasons.
        #
        # UP, to 0.80: the engine reads the base interface off the model's own FootingBedding
        # (42" of washed stone, mu 0.35) where the note used the site's silty gravel (0.25).
        # A 40% gain and a correctness fix.
        #
        # DOWN, to 0.725 (2026-08-30, BASIS_VERSION 2): the stem/footing elevation convention.
        # The wall stands ON its footing, so H runs to the footing's UNDERSIDE — 11.37', not
        # the 10.37' of authored unbalanced fill — and the thrust is 20% larger than the old
        # arithmetic thought. The stem grew a foot too, which is why the two do not cancel.
        #
        # Either way it is short of the 1.5 IRC R404.4 requires by a factor of two, which is
        # the finding that matters and the one this assertion exists to pin.
        assert record.ratio == pytest.approx(1.5 / 0.725, abs=0.05)
        # Overturning and bearing are comfortable; a reviewer's attention belongs at the
        # base, and the record has to say which limit state governs for that to be visible.
        by_name = {state.name: state for state in record.limit_states}
        assert by_name["overturning"].ok and by_name["bearing"].ok

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
