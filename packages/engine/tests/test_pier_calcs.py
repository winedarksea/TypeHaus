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

# The two cages, as `params/sunken_garden.py` authors them (§4c of the note).
_COL_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'
_FCOL_CAGE = '(8) #6 vertical, #3 ties @ 12" o.c.'
_COL_CAGE_SOURCE = "vertical_reinforcement='" + _COL_CAGE + "',"
_FCOL_CAGE_SOURCE = "vertical_reinforcement='" + _FCOL_CAGE + "',"
_UNREADABLE_CAGE_SOURCE = "vertical_reinforcement='rebar per engineer',"
_FCOL_SHORT_CAGE_SOURCE = (
    "vertical_reinforcement='" + _FCOL_CAGE.replace("(8)", "(6)") + "',")

# §2 and §3c of the note.
_ORACLE = {
    "PT-SG-COL": {
        "tributary_ft2": 82.33, "dead_lb": 2082.0, "live_lb": 3293.0,
        "service_lb": 5375.0, "factored_lb": 7768.0,
        "bell_area_ft2": 4.909, "bearing_psf": 1245.0,
        "gross_in2": 113.1, "h_over_d": 10.7, "min_steel_in2": 1.131,
        # §4c / §4d / §4e of the note.
        "cage": _COL_CAGE, "bars": 4, "steel_in2": 1.24,
        "capacity_lb": 187_011.0, "tie_spacing_in": 10.0,
        "slenderness": 42.7, "delta_ns": 1.018, "e_magnified_in": 0.978, "e_capped_in": 1.20,
    },
    "PT-SG-FCOL": {
        "tributary_ft2": 116.17, "dead_lb": 4735.0, "live_lb": 4647.0,
        "service_lb": 9382.0, "factored_lb": 13_117.0,
        "bell_area_ft2": 7.069, "bearing_psf": 1477.0,
        "gross_in2": 314.2, "h_over_d": 6.4, "min_steel_in2": 3.142,
        "cage": _FCOL_CAGE, "bars": 8, "steel_in2": 3.52,
        "capacity_lb": 521_732.0, "tie_spacing_in": 12.0,
        "slenderness": 25.6, "delta_ns": 1.004, "e_magnified_in": 1.205, "e_capped_in": 2.00,
    },
}

_PRESUMPTIVE_ALLOWABLE_PSF = 2000.0


def _mutated(tmp_path, replacements):
    """A copy of catlin with `params/sunken_garden.py` edited — the same free-pass harness
    `test_retaining_court.py` uses, and for the same reason: a limit state nobody can break
    on purpose is not being tested."""
    from pathlib import Path

    from _helpers import copy_house

    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    house = copy_house(catlin, tmp_path / "house")
    source = house / "params" / "sunken_garden.py"
    text = source.read_text()
    for old, replacement in replacements:
        assert old in text, old
        text = text.replace(old, replacement)
    source.write_text(text)
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    return result.plan


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
def test_the_cage_reproduces_the_hand_worked_design(tag, results, piers) -> None:
    """§4c and §4d — the cage the house authors, and the capacity it buys."""
    want = _ORACLE[tag]
    assert piers[tag].vertical_reinforcement == want["cage"]

    record = results[f"deck_post/{tag}"]
    assert record.status is Status.OK, record.summary
    assert not record.missing

    state = next(s for s in record.limit_states if s.name == "axial, tied column")
    assert state.demand == pytest.approx(want["factored_lb"], abs=5.0)
    assert state.capacity == pytest.approx(want["capacity_lb"], rel=0.002)
    # The section is enormous for the load; the cage is NOT there for strength.
    assert state.demand / state.capacity < 0.05


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_cage_sits_at_the_code_minimum_and_not_below_it(tag, results) -> None:
    """§4b/§4c — the 1% floor is what sizes these cages, and both clear it by ~10%.

    **This is the assertion that stops a well-meant "save concrete" edit.** The columns run
    at d/c 0.04; nothing about the load justifies less steel, because ACI 318-19 §10.6.1.1's
    floor covers creep, shrinkage and the accidental moment and is indifferent to loading.
    """
    want = _ORACLE[tag]
    record = results[f"deck_post/{tag}"]

    steel = next(s for s in record.limit_states if s.name == "longitudinal steel")
    assert steel.demand == pytest.approx(want["min_steel_in2"], abs=0.002)  # 0.01 Ag
    assert steel.capacity == pytest.approx(want["steel_in2"], abs=0.005)
    assert steel.ok, "the authored cage is BELOW the ACI minimum"
    # Clears the floor, but by a builder's margin rather than a designer's.
    assert 1.0 < want["steel_in2"] / want["min_steel_in2"] < 1.15

    ceiling = next(s for s in record.limit_states if s.name == "steel ratio ceiling")
    assert ceiling.ok and ceiling.ratio < 0.2  # nowhere near 0.08 Ag

    count = next(s for s in record.limit_states if s.name == "bar count")
    assert count.demand == 4.0, "§10.7.3.1(b) is FOUR within circular ties, not six"
    assert count.capacity == float(want["bars"])
    assert count.ok


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_ties_are_at_the_25_7_2_2_maximum(tag, results) -> None:
    """§4b — least of 16db, 48dt and the column's own least dimension."""
    want = _ORACLE[tag]
    record = results[f"deck_post/{tag}"]
    spacing = next(s for s in record.limit_states if s.name == "tie spacing")
    assert spacing.demand == pytest.approx(want["tie_spacing_in"])
    assert spacing.capacity == pytest.approx(want["tie_spacing_in"]), (
        "the authored spacing IS the code maximum for this cage — if this drifts, the "
        "house got cheaper than the code allows")
    assert spacing.ok
    assert next(s for s in record.limit_states if s.name == "tie size").ok


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_slenderness_is_carried_and_the_minimum_eccentricity_is_covered(tag, results) -> None:
    """§4e — the argument that lets one axial comparison be the whole check.

    The 12" column is past §6.2.5's non-sway floor of 34 and the 20" is not, but both end in
    the same place: the magnified minimum eccentricity is INSIDE the 0.10h that R22.4.2 says
    the 0.80 axial cap already carries, so no interaction diagram is needed.
    """
    want = _ORACLE[tag]
    record = results[f"deck_post/{tag}"]
    state = next(s for s in record.limit_states if s.name == "minimum eccentricity")
    assert state.demand == pytest.approx(want["e_magnified_in"], abs=0.005)
    assert state.capacity == pytest.approx(want["e_capped_in"], abs=0.005)
    assert state.ok
    assert f"{want['delta_ns']:.3f}" in state.citation
    slender = next(n for n in record.notes if n.startswith("SLENDERNESS"))
    assert f"{want['slenderness']:.1f}" in slender
    expected = "NOT neglectable" if want["slenderness"] > 34.0 else "neglectable outright"
    assert expected in slender


def test_a_column_with_no_cage_is_incomplete_and_names_the_field(tmp_path) -> None:
    """**The free pass this whole field exists to refuse.**

    Strip the reinforcement and the record must go back to INCOMPLETE naming
    `Post.vertical_reinforcement` — never to an OK earned by the section alone, which is at
    d/c 0.04 and would sail through anything that graded only strength.
    """
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    plan = _mutated(tmp_path, [(_COL_CAGE_SOURCE, "")])
    model, _ = resolve(plan)
    results = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))

    record = results["deck_post/PT-SG-COL"]
    assert record.status is Status.INCOMPLETE, record.summary
    assert any("vertical_reinforcement" in m for m in record.missing), record.missing
    assert any("14.1.5" in m for m in record.missing), record.missing
    # The other pier still has its cage, so this is the field and not a global break.
    assert results["deck_post/PT-SG-FCOL"].status is Status.OK


def test_a_cage_that_does_not_parse_reads_as_no_steel(tmp_path) -> None:
    """Same contract as `retaining_basis.parse_reinforcement`: unreadable is NOT a pass."""
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    plan = _mutated(tmp_path, [(_COL_CAGE_SOURCE, _UNREADABLE_CAGE_SOURCE)])
    model, _ = resolve(plan)
    results = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))
    assert results["deck_post/PT-SG-COL"].status is Status.INCOMPLETE


def test_an_under_minimum_cage_is_over_not_ok(tmp_path) -> None:
    """6-#6 in the 20" column: 2.64 in2 against a 3.142 in2 floor — the §4c trap, which
    looks like a sensible cage and is 16% short of legal."""
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    plan = _mutated(tmp_path, [(_FCOL_CAGE_SOURCE, _FCOL_SHORT_CAGE_SOURCE)])
    model, _ = resolve(plan)
    results = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))

    record = results["deck_post/PT-SG-FCOL"]
    assert record.status is Status.OVER, record.summary
    steel = next(s for s in record.limit_states if s.name == "longitudinal steel")
    assert not steel.ok
    assert steel.capacity == pytest.approx(2.64, abs=0.005)


@pytest.mark.parametrize("spec,expected", [
    (_COL_CAGE, (4, 5, 3, 10.0)),
    (_FCOL_CAGE, (8, 6, 3, 12.0)),
    ("8-#6 vertical with #3 ties @ 12 in. o.c.", (8, 6, 3, 12.0)),
    ("4 #5 verticals, #4 TIES @ 9.5 in o.c.", (4, 5, 4, 9.5)),
    ("rebar per engineer", None),
    ("#3 ties @ 10 in o.c.", None),        # ties alone are not a cage
    ("(4) #5 vertical", None),             # verticals alone are not a cage
    ("", None),
    (None, None),
])
def test_parse_cage(spec, expected) -> None:
    """A count and a spacing are different specs, and only one of them is a column's."""
    from typehaus.engineering.deck_post import parse_cage

    cage = parse_cage(spec)
    if expected is None:
        assert cage is None
        return
    assert (cage.count, cage.bar, cage.tie_bar, cage.tie_spacing_in) == expected


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
