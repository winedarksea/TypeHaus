"""``engineering/spread_footing.py`` and ``deck_post.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/sunken_garden_piers.md``, worked by hand in a separate
pass before either module was written — the discipline every calc module in this package is
held to.

Two of these assertions are doing unusual work and are worth reading before changing:

* :func:`test_the_bell_is_read_as_a_circle_not_the_resolved_square` pins a place where the
  calculation deliberately **disagrees with the resolved model's geometry**, because the
  resolver's square is a drawing convenience and the pier is round. Getting this wrong
  credits 27% of bearing area that does not exist.
* :func:`test_a_plain_cast_column_is_incomplete_and_says_why` pins an INCOMPLETE that must
  never become OK by the section getting bigger. The section is already twenty times what it
  needs; what is missing is reinforcement the model has nowhere to state.
"""

from __future__ import annotations

import math

import pytest

from typehaus.engineering.item import Status

# §2 and §3c of the note.
_ORACLE = {
    "PT-SG-COL": {
        "tributary_ft2": 82.33, "dead_lb": 2082.0, "live_lb": 3293.0,
        "service_lb": 5375.0, "factored_lb": 7768.0,
        "bell_area_ft2": 4.909, "bearing_psf": 1245.0,
        "gross_in2": 113.1, "plain_capacity_lb": 81_400.0, "h_over_d": 10.7,
        "min_steel_in2": 1.13,
    },
    "PT-SG-FCOL": {
        "tributary_ft2": 116.17, "dead_lb": 4735.0, "live_lb": 4647.0,
        "service_lb": 9382.0, "factored_lb": 13_117.0,
        "bell_area_ft2": 7.069, "bearing_psf": 1477.0,
        "gross_in2": 314.2, "plain_capacity_lb": 244_300.0, "h_over_d": 6.4,
        "min_steel_in2": 3.14,
    },
}

_PRESUMPTIVE_ALLOWABLE_PSF = 2000.0


@pytest.fixture(scope="module")
def results(catlin_plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    return EngineeringResults(EngineeringContext(
        plan=catlin_plan, model=model, soil_class="GM"))


@pytest.fixture(scope="module")
def piers(catlin_plan):
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    return {pier.tag: pier for pier in cast_piers(ctx)}


def test_only_the_two_belled_piers_are_in_scope(piers) -> None:
    """A post on a Pad, a wall, a floor or another post is somebody else's rule."""
    assert set(piers) == {"PT-SG-COL", "PT-SG-FCOL"}


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_load_path_reproduces_the_note(tag, piers) -> None:
    """§2's table, term by term. Two errors can cancel inside a d/c ratio."""
    want = _ORACLE[tag]
    pier = piers[tag]
    assert pier.tributary_ft2 == pytest.approx(want["tributary_ft2"], abs=0.02)
    assert pier.dead_lb == pytest.approx(want["dead_lb"], abs=3.0)
    assert pier.live_lb == pytest.approx(want["live_lb"], abs=2.0)
    assert pier.service_lb == pytest.approx(want["service_lb"], abs=4.0)
    assert pier.factored_lb == pytest.approx(want["factored_lb"], abs=5.0)
    assert pier.gross_area_in2 == pytest.approx(want["gross_in2"], rel=0.001)


def test_the_front_column_carries_the_pillar_standing_on_it(piers) -> None:
    """`structural.deck_footing_size` reports N/A on PT-SG-BF2 and says its share is picked
    up here. **That sentence is a promise, and this is the only thing keeping it.**

    PT-SG-BF2 bears on PT-SG-FCOL's top rather than on the porch framing, which is why that
    column is 20" and not 16". If the hand-down were dropped, the front pier would be graded
    on 82.33 ft2 like the back one and the balcony's share would be carried by nothing.
    """
    back, front = piers["PT-SG-COL"], piers["PT-SG-FCOL"]
    assert back.tributary_ft2 == pytest.approx(82.33, abs=0.02)
    # 203.00 ft2 of balcony over six pillars = 33.83, and exactly one of them lands here.
    assert front.tributary_ft2 - back.tributary_ft2 == pytest.approx(33.83, abs=0.02)
    assert front.carried_dead_lb > 0.0


def test_the_bell_is_read_as_a_circle_not_the_resolved_square(piers, catlin_model) -> None:
    """§3a — the calculation disagrees with the resolved solid ON PURPOSE.

    `resolve/envelope.py` draws a post-hosted footing as a SQUARE of side `width`, and
    `params/sunken_garden.py` calls that same number a bell DIAMETER. Taking the square
    credits 27% more bearing area than exists, in the unconservative direction.
    """
    for tag, dia_in in (("PT-SG-COL", 30.0), ("PT-SG-FCOL", 36.0)):
        pier = piers[tag]
        circle = math.pi * (dia_in / 2.0) ** 2 / 144.0
        square = (dia_in / 12.0) ** 2
        assert pier.bearing_area_ft2 == pytest.approx(circle, rel=1e-6)
        assert pier.bearing_area_ft2 == pytest.approx(_ORACLE[tag]["bell_area_ft2"], abs=0.002)
        # The resolved solid really is the bigger square — this is not a hypothetical.
        solid = next(s for s in catlin_model.solids if s.tag == pier.footing_tag)
        xs = [x for x, _ in solid.outline]
        ys = [y for _, y in solid.outline]
        resolved = ((max(xs) - min(xs)) / 0.3048) * ((max(ys) - min(ys)) / 0.3048)
        assert resolved == pytest.approx(square, rel=1e-6)
        assert pier.bearing_area_ft2 < resolved * 0.80


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_bearing_checks_out_on_the_sites_own_soil(tag, results) -> None:
    """§3c. And the allowable is the SITE's class 4, not the washed stone's class 3.

    The retaining footings earn 3,000 psf from a 42" replacement section. These bells were
    augered to frost depth to bear on undisturbed soil and carry a 7" LEVELLING course;
    reading the stone's number off that would be a sixth of a section's worth of credit.
    """
    record = results[f"spread_footing/{tag}"]
    assert record.status is Status.OK, record.summary
    state = next(s for s in record.limit_states if s.name == "bearing")
    assert state.demand == pytest.approx(_ORACLE[tag]["bearing_psf"], abs=3.0)
    assert state.capacity == pytest.approx(_PRESUMPTIVE_ALLOWABLE_PSF)
    assert "class 4" in state.citation
    assert state.ok


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_a_plain_cast_column_is_incomplete_and_says_why(tag, results) -> None:
    """§4 — and the INCOMPLETE is about REINFORCEMENT, never about the section.

    The section is at d/c 0.095 and 0.054. If a future edit makes this OK by growing the
    column, something has gone wrong: a column may not be plain concrete at any stress, and
    `Post` has no field in which the bars could be recorded.
    """
    want = _ORACLE[tag]
    record = results[f"deck_post/{tag}"]
    assert record.status is Status.INCOMPLETE, record.summary
    assert record.missing, "an INCOMPLETE that names nothing is a shrug"
    assert any("reinforcement" in m for m in record.missing), record.missing
    assert any(f"{want['min_steel_in2']:.2f} in2" in m for m in record.missing), record.missing

    state = next(s for s in record.limit_states if s.name == "axial, gross section")
    assert state.demand == pytest.approx(want["factored_lb"], abs=5.0)
    assert state.capacity == pytest.approx(want["plain_capacity_lb"], rel=0.002)
    # The section is enormous for the load, and the record must not read as if it were tight.
    assert state.demand / state.capacity < 0.12
    assert state.ok


def test_both_piers_are_columns_and_not_pedestals(piers) -> None:
    """The ratio that decides which ACI chapter applies. A pedestal may be plain; a column
    may not, and that single fact is the whole reason the records above are INCOMPLETE."""
    from typehaus.engineering.deck_post import PEDESTAL_HEIGHT_RATIO

    assert PEDESTAL_HEIGHT_RATIO == 3.0
    for tag in _ORACLE:
        pier = piers[tag]
        ratio = pier.height_in / pier.diameter_in
        assert ratio == pytest.approx(_ORACLE[tag]["h_over_d"], abs=0.05)
        assert ratio > PEDESTAL_HEIGHT_RATIO


def test_the_two_tributary_rules_agree(catlin_plan) -> None:
    """`engineering/` may not import `checks/`, so the tributary rule is stated twice.

    That duplication is deliberate and documented in `pier_basis`, and this is the only
    thing that stops the two copies drifting into two different answers about what these
    posts hold up.
    """
    from _helpers import check_context

    from typehaus.checks.structural.deck import _deck_posts, _decks, _tributary_ft2
    from typehaus.engineering.pier_basis import _deck_tributaries
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    mine = _deck_tributaries(EngineeringContext(plan=catlin_plan, model=model))

    ctx = check_context(plan=catlin_plan)
    theirs: dict[str, float] = {}
    for deck in _decks(ctx):
        posts = _deck_posts(ctx, deck)
        share = _tributary_ft2(deck, len(posts))
        for post in posts:
            theirs[post.tag] = theirs.get(post.tag, 0.0) + share

    assert set(mine) == set(theirs)
    for tag, value in theirs.items():
        assert mine[tag] == pytest.approx(value, rel=1e-9), tag
