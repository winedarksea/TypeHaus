"""``engineering/spread_footing.py`` and ``deck_post.py`` against two hand-worked notes.

The oracles are ``houses/catlin/notes/sunken_garden_piers.md`` and
``houses/catlin/notes/breezeway_piers.md``, each worked by hand in a separate pass — the
discipline every calc module in this package is held to.

Two of these assertions are doing unusual work and are worth reading before changing:

* :func:`test_the_bell_is_read_as_a_circle_not_the_resolved_square` pins a place where the
  calculation deliberately **disagrees with the resolved model's geometry**, because the
  resolver's square is a drawing convenience and the pier is round. Getting this wrong
  credits 27% of bearing area that does not exist.
* :func:`test_a_plain_cast_column_is_incomplete_and_says_why` pins an INCOMPLETE that must
  never become OK by the section getting bigger. The section is already twenty times what it
  needs; what is missing is reinforcement the model has nowhere to state.
* :func:`test_a_pier_whose_demand_is_short_publishes_no_ratio` pins the OTHER INCOMPLETE, and
  the more easily lost one: the breezeway piers carry a roof with no plan area anywhere in
  the model, so their tributary is an under-count. The record grades the cage in full and
  omits the axial state. A d/c appearing there is the regression this guards.
"""

from __future__ import annotations

import math

import pytest

from typehaus.engineering.item import Status

# The cages, as `params/sunken_garden.py` authors them (§4c of the note).
#
# Since 2026-09-03 every cast column in the sunken garden carries the SAME cage: PT-SG-FCOL
# came down from 20" round / (8) #6 to 12" round / (4) #5 when PT-SG-BF2 stopped standing on
# its top, and the four balcony corner columns arrived at the same section. PT-SG-COL's cage
# is authored as a literal; the other five read `SPEC.corner_column_cage`, which adds the
# cover and the galvanizing the durability case asks for. Two strings, one section.
_COL_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'
_FCOL_CAGE = ('(4) #5 vertical, #3 ties @ 10" o.c., 2" cover, '
              'hot-dip galvanized (ASTM A767 cl. 1 or A1094)')
_COL_CAGE_SOURCE = "vertical_reinforcement='" + _COL_CAGE + "',"
_UNREADABLE_CAGE_SOURCE = "vertical_reinforcement='rebar per engineer',"
# The SPEC field the five 12" columns share. Mutating it moves all five at once, which is
# what `test_an_under_minimum_cage_is_over_not_ok` wants.
_SPEC_CAGE_SOURCE = "corner_column_cage: str = ('(4) #5 vertical, #3 ties @ 10\" o.c., 2\" cover, '"
_SPEC_SHORT_CAGE_SOURCE = "corner_column_cage: str = ('(3) #4 vertical, #3 ties @ 10\" o.c., 2\" cover, '"

# §2 and §4 of `notes/breezeway_piers.md`. All four piers are identical — same height,
# section, tributary and cage — so one row covers them.
_BW_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'
_BREEZEWAY_ORACLE = {
    "height_in": 56.75, "gross_in2": 113.097, "h_over_d": 4.73,
    "tributary_ft2": 3.1727, "carried_dead_lb": 50.70, "self_weight_lb": 557.14,
    "dead_lb": 639.57, "live_lb": 126.91, "service_lb": 766.48, "factored_lb": 970.54,
    "min_steel_in2": 1.1310, "steel_in2": 1.24, "capacity_lb": 187_011.0,
    "tie_spacing_in": 10.0,
    "slenderness": 18.92, "delta_ns": 1.0006, "e_magnified_in": 0.9606, "e_capped_in": 1.20,
}
_BREEZEWAY_PIERS = ("PR-BW-1", "PR-BW-2", "PR-BW-3", "PR-BW-4")

# §2 and §3c of the note. Both piers are 12" round and carry the same cage since
# 2026-09-03, so the two rows agree on everything but the bell and a pound of pillar.
_ORACLE = {
    "PT-SG-COL": {
        "tributary_ft2": 116.17, "dead_lb": 2487.0, "live_lb": 4647.0,
        "service_lb": 7134.0, "factored_lb": 10_419.0,
        "bell_area_ft2": 4.909, "bearing_psf": 1603.0,
        "gross_in2": 113.1, "h_over_d": 10.7, "min_steel_in2": 1.131,
        # §4c / §4d / §4e of the note.
        "cage": _COL_CAGE, "bars": 4, "steel_in2": 1.24,
        "capacity_lb": 187_011.0, "tie_spacing_in": 10.0,
        "slenderness": 42.7, "delta_ns": 1.024, "e_magnified_in": 0.983, "e_capped_in": 1.20,
    },
    "PT-SG-FCOL": {
        "tributary_ft2": 116.17, "dead_lb": 2486.0, "live_lb": 4647.0,
        "service_lb": 7132.0, "factored_lb": 10_418.0,
        "bell_area_ft2": 7.069, "bearing_psf": 1159.0,
        "gross_in2": 113.1, "h_over_d": 10.7, "min_steel_in2": 1.131,
        "cage": _FCOL_CAGE, "bars": 4, "steel_in2": 1.24,
        "capacity_lb": 187_011.0, "tie_spacing_in": 10.0,
        "slenderness": 42.7, "delta_ns": 1.024, "e_magnified_in": 0.983, "e_capped_in": 1.20,
    },
}

# The four balcony corner columns — same section, same cage, and a different question.
# `notes/balcony_moment_columns.md` is their oracle: they stand on the 12" tops of
# W-SG-W1/E1 rather than on their own belled piers, and what governs them is BENDING at a
# fixed base, not bearing. §4 and §5 of that note.
_CORNER_PIERS = ("PT-SG-BF1", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3")
_CORNER_ORACLE = {
    "PT-SG-BF1": {"height_in": 108.125, "wind_lb_ft": 1388.4, "guard_lb_ft": 2502.1},
    "PT-SG-BF3": {"height_in": 108.125, "wind_lb_ft": 1388.4, "guard_lb_ft": 2502.1},
    # The rear row runs 2" proud for the deck's drainage crown.
    "PT-SG-BR1": {"height_in": 110.125, "wind_lb_ft": 1414.1, "guard_lb_ft": 2535.4},
    "PT-SG-BR3": {"height_in": 110.125, "wind_lb_ft": 1414.1, "guard_lb_ft": 2535.4},
}
#: §4 of the note: phi*Mn at the column's own axial load, hand-worked term by term.
_CORNER_PHI_MN_LB_FT = 20_900.0
#: §7: ld = (60,000 / (25 sqrt(3,000))) x 0.625 = 27.4", x 1.3 for a class B splice.
_CLASS_B_LAP_IN = 35.6

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


def test_every_cast_concrete_pier_on_its_own_base_is_in_scope(piers) -> None:
    """Two belled piers, four pad-borne ones, and four standing on a concrete wall top.

    A post on a FLOOR or on a WOOD post is somebody else's rule, and so is a wood post on
    anything. The wall case joined this module on 2026-09-03: the four balcony corner
    columns are exactly the member it grades and had no ``Footing`` of their own, so they
    fell out of the enumeration entirely and the check that named them reported "an
    engineer's design governs, and this engine computes none" about a column the engine
    could compute perfectly well.
    """
    assert set(piers) == {"PT-SG-COL", "PT-SG-FCOL", *_CORNER_PIERS, *_BREEZEWAY_PIERS}


def test_the_gate_is_concrete_not_a_round_section(catlin_plan, piers) -> None:
    """``size="12 round"`` is a SHAPE. A 12" round wood column is an ordinary thing, and
    ACI 318 has nothing to say about it — the material is what puts a post in this module."""
    from typehaus.model.structure import Post
    from typehaus.resolve.assembly_material import assembly_structure_material

    for element in catlin_plan.all_elements():
        if isinstance(element, Post) and element.tag in piers:
            assert assembly_structure_material(catlin_plan, element.assembly) == "concrete"
    # The wood posts standing on the breezeway piers are not themselves piers.
    assert not {"PT-BW-1", "PT-BW-2", "PT-BW-3", "PT-BW-4"} & set(piers)


@pytest.mark.parametrize("tag", _BREEZEWAY_PIERS)
def test_the_breezeway_load_path_reproduces_its_note(tag, piers) -> None:
    """§2 of ``notes/breezeway_piers.md``, term by term."""
    want = _BREEZEWAY_ORACLE
    pier = piers[tag]
    assert pier.height_in == pytest.approx(want["height_in"], abs=0.01)
    assert pier.gross_area_in2 == pytest.approx(want["gross_in2"], rel=0.001)
    assert pier.height_in / pier.diameter_in == pytest.approx(want["h_over_d"], abs=0.01)
    assert pier.tributary_ft2 == pytest.approx(want["tributary_ft2"], abs=0.001)
    assert pier.carried_dead_lb == pytest.approx(want["carried_dead_lb"], abs=0.5)
    assert pier.self_weight_lb == pytest.approx(want["self_weight_lb"], abs=0.5)
    assert pier.dead_lb == pytest.approx(want["dead_lb"], abs=1.0)
    assert pier.live_lb == pytest.approx(want["live_lb"], abs=0.5)
    assert pier.service_lb == pytest.approx(want["service_lb"], abs=1.0)
    assert pier.factored_lb == pytest.approx(want["factored_lb"], abs=1.5)


@pytest.mark.parametrize("tag", _BREEZEWAY_PIERS)
def test_a_pier_whose_demand_is_short_publishes_no_ratio(tag, results) -> None:
    """§3 of the note: the roof has no plan area, so the tributary is an under-count.

    The six load-independent detailing states are graded in full; the §22.4.2 axial state is
    **omitted, not estimated**. Publishing an understated d/c is worse than publishing none,
    because a reader takes a printed ratio at face value and cannot see what is missing.
    """
    record = results[f"deck_post/{tag}"]
    assert record.status is Status.INCOMPLETE
    names = [state.name for state in record.limit_states]
    assert "axial, tied column" not in names
    assert len(names) == 6
    assert all(state.ok for state in record.limit_states)
    assert record.missing and "BM-BW-R" in record.missing[0]


@pytest.mark.parametrize("tag", _BREEZEWAY_PIERS)
def test_the_breezeway_cage_is_acis_minimum(tag, results) -> None:
    """§4 of the note. The 1% floor is a creep/shrinkage rule, indifferent to §3's gap."""
    want = _BREEZEWAY_ORACLE
    record = results[f"deck_post/{tag}"]
    states = {state.name: state for state in record.limit_states}
    assert states["longitudinal steel"].demand == pytest.approx(want["min_steel_in2"], abs=0.001)
    assert states["longitudinal steel"].capacity == pytest.approx(want["steel_in2"], abs=0.001)
    assert states["bar count"].capacity == 4.0
    assert states["tie size"].capacity == 3.0
    assert states["tie spacing"].capacity == pytest.approx(want["tie_spacing_in"], abs=0.01)
    assert states["minimum eccentricity"].demand == pytest.approx(
        want["e_magnified_in"], abs=0.001)
    assert states["minimum eccentricity"].capacity == pytest.approx(
        want["e_capped_in"], abs=0.001)


def test_a_pad_borne_pier_gets_no_engineered_bearing_record(results) -> None:
    """§6 — a ``Pad`` IS an IRC Table R507.3.1 row, graded by
    ``structural.deck_footing_size``. Two authorities on one number is worse than one."""
    for tag in _BREEZEWAY_PIERS:
        assert f"spread_footing/{tag}" not in results
    assert "spread_footing/PT-SG-COL" in results


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


def test_both_columns_carry_the_centre_pillar_that_lands_beside_them(piers) -> None:
    """`structural.deck_footing_size` reports N/A on both centre pillars and says their share
    is picked up here. **That sentence is a promise, and this is the only thing keeping it.**

    PT-SG-BR2 and PT-SG-BF2 each stand on the porch DECK, 3" from a beam line, and each
    carries a third of the balcony. Until 2026-09-03 ``pier_basis`` handed load down only
    post-to-post, so a pillar on a FloorSystem handed nothing and PT-SG-COL was graded on
    82.33 ft2 with a third of a balcony landing on it uncounted. Both now hand their share
    through the deck's beams to the column under them.
    """
    own_porch_share = 82.33          # FS-SG-PORCH 164.67 ft2 over its two columns
    balcony_share = 33.83            # FS-SG-DECK 203.00 ft2 over its six pillars
    for tag in ("PT-SG-COL", "PT-SG-FCOL"):
        pier = piers[tag]
        assert pier.tributary_ft2 == pytest.approx(own_porch_share + balcony_share, abs=0.02)
        assert pier.carried_dead_lb > 0.0, "the pillar's own 6x6 rides down with its share"


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
    assert state.demand / state.capacity < 0.10


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_cage_sits_at_the_code_minimum_and_not_below_it(tag, results) -> None:
    """§4b/§4c — the 1% floor is what sizes these cages, and both clear it by ~10%.

    **This is the assertion that stops a well-meant "save concrete" edit.** The columns run
    at d/c 0.06; nothing about the load justifies less steel, because ACI 318-19 §10.6.1.1's
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

    Both are past §6.2.5's non-sway floor of 34 (PT-SG-FCOL was at 25.6 and neglectable
    outright while it was a 20" round — shrinking a column is the one edit that makes
    slenderness appear), and both end in the same place: the magnified minimum eccentricity
    is INSIDE the 0.10h that R22.4.2 says the 0.80 axial cap already carries, so no
    interaction diagram is needed.
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
    """(3) #4 in a 12" column: 0.60 in2 against a 1.131 in2 floor — under on BOTH counts.

    It is short of §10.6.1.1's 1% floor and short of §10.7.3.1(b)'s four bars within
    circular ties, which is the pair of limits a "save some steel" edit trips together. The
    §4c trap it replaces was 6-#6 in the retired 20" round: 2.64 in2 against 3.142, a cage
    that looks perfectly sensible and is 16% short of legal.
    """
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    plan = _mutated(tmp_path, [(_SPEC_CAGE_SOURCE, _SPEC_SHORT_CAGE_SOURCE)])
    model, _ = resolve(plan)
    results = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))

    record = results["deck_post/PT-SG-FCOL"]
    assert record.status is Status.OVER, record.summary
    steel = next(s for s in record.limit_states if s.name == "longitudinal steel")
    assert not steel.ok
    assert steel.capacity == pytest.approx(0.60, abs=0.005)
    count = next(s for s in record.limit_states if s.name == "bar count")
    assert not count.ok
    # And it takes the four corner columns with it — one SPEC field feeds all five.
    for tag in _CORNER_PIERS:
        assert results[f"deck_post/{tag}"].status is Status.OVER


@pytest.mark.parametrize("spec,expected", [
    (_COL_CAGE, (4, 5, 3, 10.0)),
    (_FCOL_CAGE, (4, 5, 3, 10.0)),
    ('(8) #6 vertical, #3 ties @ 12" o.c.', (8, 6, 3, 12.0)),
    # The trap the SPEC field's own comment warns about: an adjective wedged between the
    # tie bar and the word "ties" makes the whole string unreadable, which reads as NO
    # STEEL and reports INCOMPLETE rather than failing loudly.
    ('(4) #5 galvanized vertical, #3 galvanized ties @ 10" o.c.', None),
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


# ---------------------------------------------------------------------------------------
# The four balcony corner columns, and the three glulam beams over them.
# Oracle: houses/catlin/notes/balcony_moment_columns.md, hand-worked in a separate pass.
# ---------------------------------------------------------------------------------------


def test_a_column_on_a_wall_top_takes_that_walls_strip_footing(piers) -> None:
    """The load path is real; the footing is not this pier's to grade.

    A cast column standing on a concrete FoundationWall is carried by that wall's continuous
    strip footing, and ``cast_piers`` records it — but ``shared_wall_footing`` is what keeps
    ``engineering/spread_footing.py`` off it. A strip footing under a wall already has an
    authority (``structural.foundation_unbalanced_fill``, as ``retaining_wall/<tag>``), and a
    second engineered record computing a point pressure on the same concrete would be the
    weaker of two answers to one question.
    """
    for tag in _CORNER_PIERS:
        pier = piers[tag]
        assert pier.footing_tag in {"FT-SG-W1", "FT-SG-E1"}
        assert pier.shared_wall_footing is True
    for tag in ("PT-SG-COL", "PT-SG-FCOL"):
        assert piers[tag].shared_wall_footing is False


def test_no_engineered_bearing_record_on_a_shared_wall_footing(results) -> None:
    """The other half of the rule above — and the half a regression would show up in."""
    for tag in _CORNER_PIERS:
        assert f"spread_footing/{tag}" not in results


@pytest.mark.parametrize("tag", _CORNER_PIERS)
def test_the_corner_columns_are_the_decks_lateral_system(tag, piers) -> None:
    """§0 and §2 of the note. No knee brace anywhere in the plan and no beam in a wall, so
    the base moment is real and ``deck_post`` must grade bending."""
    pier = piers[tag]
    assert pier.lateral_system is True
    assert pier.height_in == pytest.approx(_CORNER_ORACLE[tag]["height_in"], abs=0.01)
    # The two porch columns land their beams in W-SG-W1/E1 — braced by shear walls, no
    # column moment, and the finding that claimed otherwise is the regression this pins.
    for other in ("PT-SG-COL", "PT-SG-FCOL"):
        assert piers[other].lateral_system is False


@pytest.mark.parametrize("tag", _CORNER_PIERS)
def test_the_base_moments_reproduce_the_note(tag, piers) -> None:
    """§2b and §2c, term by term.

    Wind is the E-W case at the Fig. 29.3-1 Case A/B ceiling (C_f 1.80), because the figure
    itself is copyrighted and this repository holds three cells of it — spending the
    coefficient conservatively rather than leaving it open. The guard is R301.5's 200 lb at
    the guard top, taken WHOLLY on one column: halving it across the two that bound an end
    bay is a diaphragm claim this module has no standing to make.
    """
    want = _CORNER_ORACLE[tag]
    pier = piers[tag]
    assert pier.wind_base_moment_lb_ft == pytest.approx(want["wind_lb_ft"], abs=1.0)
    assert pier.guard_base_moment_lb_ft == pytest.approx(want["guard_lb_ft"], abs=1.0)
    # 200 lb x (the column + the 3'-6" guard). If this ever stops being an exact multiple
    # of 200, the lever arm has silently changed.
    lever_ft = want["guard_lb_ft"] / 200.0
    assert lever_ft == pytest.approx(want["height_in"] / 12.0 + 3.5, abs=0.01)
    # The guard governs, which is the whole reason it is computed at all.
    assert pier.guard_base_moment_lb_ft > pier.wind_base_moment_lb_ft


@pytest.mark.parametrize("tag", _CORNER_PIERS)
def test_the_corner_column_is_graded_in_bending_and_it_checks_out(tag, results) -> None:
    """§4's table. Bending governs, the section is at an eighth of it, and the AXIAL state
    — the only thing every other record in this module grades — is not what sizes it."""
    record = results[f"deck_post/{tag}"]
    assert record.status is Status.OK, record.summary
    assert not record.missing
    states = {state.name: state for state in record.limit_states}
    assert set(states) >= {"bending at base, wind", "bending at base, guard",
                           "magnified moment (sway)", "dowel lap, class B",
                           "axial, tied column"}
    assert all(state.ok for state in record.limit_states)

    for name in ("bending at base, wind", "bending at base, guard"):
        assert states[name].capacity == pytest.approx(_CORNER_PHI_MN_LB_FT, rel=0.01)
    guard = states["bending at base, guard"]
    assert guard.demand / guard.capacity == pytest.approx(0.12, abs=0.01)
    axial = states["axial, tied column"]
    assert axial.demand / axial.capacity < 0.03, "axial is not what governs, and never was"

    # Magnification is real (k*lu/r 76, past §6.2.5's SWAY limit of 22) and nearly nothing,
    # because P-delta needs P to bite and P is ~2% of capacity.
    magnified = states["magnified moment (sway)"]
    assert 1.02 < magnified.demand / guard.demand < 1.05


@pytest.mark.parametrize("tag", _CORNER_PIERS)
def test_the_cantilever_uses_k_2_1_and_the_sway_threshold(tag, results) -> None:
    """The single most consequential line in the record, and the easiest to lose.

    Every other pier here is a LEANING column: ``_slenderness`` takes k = 1.0 and measures
    against §6.2.5's non-sway floor of 34, because ``structural.lateral_racking`` hands its
    storey shear to a braced bay. These four have no braced bay to hand it to. k is 2.1
    (Table R6.2.5, fixed base / free top, not the ideal 2.0) and the threshold is the SWAY
    limit of 22.
    """
    from typehaus.engineering.deck_post import CANTILEVER_EFFECTIVE_LENGTH_FACTOR

    assert CANTILEVER_EFFECTIVE_LENGTH_FACTOR == 2.1
    citation = next(s for s in results[f"deck_post/{tag}"].limit_states
                    if s.name == "magnified moment (sway)").citation
    assert "k 2.1" in citation
    assert "SWAY limit of 22" in citation


@pytest.mark.parametrize("tag", _CORNER_PIERS)
def test_the_dowel_lap_reads_the_galvanized_row_not_the_epoxy_one(tag, results) -> None:
    """§7. ACI 318-19 §25.4.2.5 gives zinc-coated bar psi_e = 1.0; it is EPOXY that takes
    1.2-1.5. Reading the epoxy row for a galvanized bar lengthens every lap by half."""
    record = results[f"deck_post/{tag}"]
    lap = next(s for s in record.limit_states if s.name == "dowel lap, class B")
    assert lap.demand == pytest.approx(_CLASS_B_LAP_IN, abs=0.2)
    assert lap.ok, "the lap does not fit inside the column it is lapped into"
    note = next(n for n in record.notes if n.startswith("DOWELS"))
    assert "GALVANIZED" in note and "1.0" in note


def test_the_cover_is_read_off_the_authored_cage_not_the_code_minimum(results) -> None:
    """2" of cover shortens the lever arm, and grading on ACI's 1-1/2" would quietly credit
    a capacity the drawing does not build. The house says 2"; the record must use 2"."""
    quantities = {q.name: q.value for q in results["deck_post/PT-SG-BF1"].inputs}
    assert quantities["cover"] == pytest.approx(2.0)


@pytest.mark.parametrize("tag", ["BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"])
def test_the_glulam_beams_are_engineered_and_check_out(tag, results) -> None:
    """§5 of the note. IRC Table R507.5(1) publishes sawn plies, so a glulam is delegated.

    Bearing governs — 3" on concrete against a wet-service F_c-perp of 392 psi — and it
    governs at under half. Nothing here is span-driven: 11-7/8" over the slimmer 9-1/2"
    option is the owner's planter margin, which is a decision and not a calculation.
    """
    record = results[f"deck_beam/{tag}"]
    assert record.status is Status.OK, record.summary
    states = {state.name: state for state in record.limit_states}
    assert set(states) == {"bending", "shear parallel to grain",
                           "bearing, compression perpendicular", "live-load deflection"}
    assert all(state.ok for state in record.limit_states)
    assert states["bending"].capacity == pytest.approx(1920.0, abs=1.0)   # 2,400 x C_M 0.80
    assert states["shear parallel to grain"].capacity == pytest.approx(262.5, abs=0.5)
    assert states["bearing, compression perpendicular"].capacity == pytest.approx(392.2,
                                                                                  abs=0.5)
    worst = max(record.limit_states, key=lambda s: s.demand / s.capacity)
    assert worst.name == "bearing, compression perpendicular"
    assert worst.demand / worst.capacity < 0.5


def test_the_centre_glulam_spans_less_than_its_neighbours(results) -> None:
    """§5 — every balcony back span is shorter than the bay it sits in, and each for a reason.

    BM-SG-BLC fell to 6'-9" when PT-SG-BF2 came north onto the deck; BLW and BLE fell to
    7'-4" when PT-SG-BF1/BF3 came 5-1/4" north so the beams would cantilever 2" clear of the
    12" rounds' tops. Neither is a dimension a reader would predict, and both are spent
    straight out of R507.5.1's quarter-span overhang limit against a 20" rear overhang that
    has not moved: 20.25" on BLC, 22.0" on BLW/BLE. **Nothing in the engine checks a beam
    overhang** — `checks/structural/deck.py` grades beam SPAN only — so those margins live in
    notes/balcony_moment_columns.md §5 and this pins the spans they are computed from.
    """
    spans = {tag: {q.name: q.value for q in results[f"deck_beam/{tag}"].inputs}["clear_span"]
             for tag in ("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")}
    assert spans["BM-SG-BLW"] == pytest.approx(7.333, abs=0.01)
    assert spans["BM-SG-BLE"] == pytest.approx(7.333, abs=0.01)
    assert spans["BM-SG-BLC"] == pytest.approx(6.75, abs=0.01)
    # The rear overhang is 20.0" on all three, so every back span has to carry it.
    for tag, span_ft in spans.items():
        assert 20.0 <= span_ft * 12.0 / 4.0, tag


def test_wet_service_is_applied_to_the_glulam(results) -> None:
    """The single most common way to overstate one of these by a quarter.

    AWC NDS Table 5.3.1: C_M is 0.80 on F_b and 0.833 on E for a glulam in weather. A
    supplier's span table is quoted DRY, and a check that used the dry values would clear
    this beam by a margin that does not exist outdoors.
    """
    from typehaus.engineering.glulam_beam import GLULAM_E_PSI, GLULAM_FB_PSI, WET_E, WET_FB

    quantities = {q.name: q.value for q in results["deck_beam/BM-SG-BLC"].inputs}
    assert quantities["Fb_adjusted"] == pytest.approx(GLULAM_FB_PSI * WET_FB, abs=1.0)
    assert quantities["E_adjusted"] == pytest.approx(GLULAM_E_PSI * WET_E, abs=100.0)
    assert quantities["Fb_adjusted"] < GLULAM_FB_PSI


def test_only_off_table_deck_beams_reach_the_glulam_calc(results) -> None:
    """A beam IRC Table R507.5(1) publishes is graded there, prescriptively. Minting a
    second engineered record for it would be two authorities on one span."""
    beams = {key.split("/", 1)[1] for key in results if key.startswith("deck_beam/")}
    assert beams == {"BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"}
