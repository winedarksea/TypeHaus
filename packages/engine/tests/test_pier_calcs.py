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

# ** SINCE 2026-09-03 A CAGE IS AUTHORED TWICE AND THE STRUCT GOVERNS. **
# `deck_post.cage_for` reads the structured `ReinforcementSpec` where one exists and does not
# call `parse_cage` at all — so mutating only the free-text string above is now INERT, and
# the three "break it on purpose" tests below would have passed while testing nothing. Each
# mutation therefore has to move both spellings. That is the same fact
# `integrity.reinforcement_spec_agrees` polices in the house: two spellings, one steel.
_STRUCT_CAGE_SOURCE = "reinforcement=_CAST_COLUMN_CAGE,"
_STRUCT_CAGE_HDG_SOURCE = "reinforcement=_CAST_COLUMN_CAGE_HDG,"
_STRUCT_BAR_SOURCE = 'BarSpec(role="vertical", bar=5, count=4, coating="hdg-a767"),'
_STRUCT_SHORT_BAR_SOURCE = 'BarSpec(role="vertical", bar=4, count=3, coating="hdg-a767"),'

# §2 and §4 of `notes/breezeway_piers.md`. All four piers are identical — same height,
# section, tributary and cage — so one row covers them.
_BW_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'
# REVISED 2026-09-03: the tributary DOUBLED when the split went beam-weighted.
# FS-BW-FLOOR is a single-bay deck on two beams, and each of them is an EDGE beam given the
# FULL joist span as its strip — so the two strips cover the deck twice. That is the
# conservative direction and it is the same over-count `glulam_beam.py` prints on its own
# record; on a pier bearing 1.78 ft² against a required 1.00 it changes nothing that
# matters, which is why the simpler rule is kept rather than opening a fourth opinion about
# deck loads. §2 of the note carries both numbers.
#
# RE-WORKED 2026-09-09 for the 4'-6" deck: `params/breezeway.py::_EW_FT` went 4.0 -> 4.5 so
# that D-G-SERVICE gets its R311.3 landing, which moved every plan dimension §2 is built on.
# **These values are transcribed from `notes/breezeway_piers.md` §2, which was re-worked BY
# HAND first** — post-to-post span 4.5 - 2(5.5/24) = 4.041667', deck 4.041667 x 3.583333 =
# 14.4826 ft², half of it per beam; roof covering 4.5 x 4.0 = 18.000 ft², a quarter per
# pier. The note's independent bound (deck factored + a hand estimate of the roof) reaches
# ~1,665 lb against the 1,693.75 below, agreeing to 1.7%. Do NOT re-pin these from engine
# output: the note is the oracle and the engine is what is being checked.
_BREEZEWAY_ORACLE = {
    "height_in": 56.75, "gross_in2": 113.097, "h_over_d": 4.73,
    "tributary_ft2": 7.2413, "carried_dead_lb": 50.70, "self_weight_lb": 557.14,
    # §2 as re-worked 2026-09-04, when the roof field closed the axial gap. The roof share
    # is SNOW-loaded (50 psf) and kept apart from the 40 psf deck tributary on purpose.
    "roof_tributary_ft2": 4.5, "roof_snow_psf": 50.0,
    "dead_lb": 725.26, "live_lb": 514.65, "service_lb": 1239.91, "factored_lb": 1693.75,
    # §4. 285,893 lb is the EXPOSED_MIX 5,000 psi figure; this read 187,011 (the presumptive
    # 3,000 psi the engine used to substitute) until 2026-09-09, unused and stale.
    "min_steel_in2": 1.1310, "steel_in2": 1.24, "capacity_lb": 285_893.0,
    "tie_spacing_in": 10.0,
    "slenderness": 18.92, "delta_ns": 1.0005, "e_magnified_in": 0.9604, "e_capped_in": 1.20,
}
_BREEZEWAY_PIERS = ("PR-BW-1", "PR-BW-2", "PR-BW-3", "PR-BW-4")

# §2 and §3c of the note. Both piers are 12" round and carry the same cage since
# 2026-09-03, so the two rows agree on everything but the bell and a pound of pillar.
#
# The tributary is 120.83 ft², and it is BEAM-WEIGHTED as of 2026-09-03: each column takes
# half of each porch beam that lands on it (72.50 ft², the bearing WALL at the beam's far end
# taking the other half) plus half of BM-SG-BLC, handed down by its centre pillar (48.33 ft²).
# It was 116.97 under the old `deck area / post count`, and the two errors that rule made
# nearly cancelled: the porch share was 10 ft² too high and the balcony share 14 too low.
# PT-SG-COL's bearing d/c is what feels it — 0.81 -> 0.83 on a 30" bell, the least margin in
# this structure.
#
# ** THE SHAFTS GREW 7 1/4" ON 2026-09-03 AND GAVE IT BACK ON 2026-09-05. ** The court
# dropped that far (the flood step at D-B-PATIO) and `_pier_bell_bottom_ft` is 42" below the
# COURT, so both bells followed the ground down and the shafts made up the difference; then
# the court came back flush and they came back with it. No beam soffit moved in either
# direction. In between, `_pier_bell_bottom_ft` was PINNED at the dropped elevation for a
# day, which left the bells carrying 49 1/4" of cover instead of the 42" the rule asks for;
# the owner's instruction reverses that and the constant is derived again.
#
# So these rows are back where they were before the step: 1,258 lb of shaft, h/d 10.7,
# k*lu/r 42.7. What is NOT symmetric is the tributary — that changed for its own reasons on
# 2026-09-03 and stayed changed — so a reader diffing this block against its pre-step
# version will find D and P_u agreeing and the loads above them not. notes §1, §2, §4e.
_ORACLE = {
    "PT-SG-COL": {
        "tributary_ft2": 120.83, "dead_lb": 2534.0, "live_lb": 4833.0,
        "service_lb": 7367.0, "factored_lb": 10_774.0,
        # 4.909 / 1651 while this bell was 30". Both bells are 36" since 2026-09-10 — the
        # 36" was a fossil from a 20" column and the 30" was set by nothing — which takes
        # the tightest pier in the house from d/c 0.83 to 0.60 for ~0.09 cy of concrete.
        "bell_area_ft2": 7.069, "bearing_psf": 1192.0,
        "gross_in2": 113.1, "h_over_d": 10.68, "min_steel_in2": 1.131,
        # §4c / §4d / §4e of the note.
        "cage": _COL_CAGE, "bars": 4, "steel_in2": 1.24,
        # §4d: 5,000 psi, and both piers have read it since 2026-09-10. This column got
        # there first (PIER_CONCRETE_12 named EXPOSED_MIX on 2026-09-03) and its sibling
        # caught up when SUNKEN_GARDEN_COLUMN_12 was given the same spec — completing the
        # migration this comment used to flag as unfinished. 187,011 -> 285,893 lb, and
        # E_c goes as sqrt(f'c) so the magnifier eases with it. PT-SG-COL itself moved onto
        # SUNKEN_GARDEN_COLUMN_12 in the same pass; the two are one type now.
        "capacity_lb": 285_893.0, "tie_spacing_in": 10.0,
        "slenderness": 42.7, "delta_ns": 1.019, "e_magnified_in": 0.978, "e_capped_in": 1.20,
    },
    "PT-SG-FCOL": {
        "tributary_ft2": 120.83, "dead_lb": 2532.0, "live_lb": 4833.0,
        "service_lb": 7366.0, "factored_lb": 10_772.0,
        "bell_area_ft2": 7.069, "bearing_psf": 1192.0,
        "gross_in2": 113.1, "h_over_d": 10.68, "min_steel_in2": 1.131,
        "cage": _FCOL_CAGE, "bars": 4, "steel_in2": 1.24,
        # ** 187,011 -> 285,893 ON 2026-09-10, AND THE SPLIT ABOVE IS CLOSED. **
        # `SUNKEN_GARDEN_COLUMN_12` stated its 5,000 psi mix in prose only, so this column
        # was graded on the presumptive 3,000 while PT-SG-COL — the same 12" round at the
        # same height four feet away, holding the other end of the same frame — read the
        # real mix off PIER_CONCRETE_12. The register printed the FRONT column as the
        # weaker of the two, which is backwards. The assembly names EXPOSED_MIX now and
        # all six of the court's rounds are on it, so the two rows agree.
        "capacity_lb": 285_893.0, "tie_spacing_in": 10.0,
        "slenderness": 42.7, "delta_ns": 1.019, "e_magnified_in": 0.978, "e_capped_in": 1.20,
    },
}

# The four balcony corner columns — same section, same cage, and a different question.
# `notes/balcony_moment_columns.md` is their oracle: they stand on the 12" tops of
# W-SG-W1/E1 rather than on their own belled piers, and what governs them is BENDING at a
# fixed base, not bearing. §4 and §5 of that note.
_CORNER_PIERS = ("PT-SG-BF1", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3")
# The north entry's 12" cast piers, all thirteen of them, in scope since 2026-09-10. Five
# carry the landing seats and the canopy's roof columns; eight are the box-tier footings
# under ST-BW-ENTRY at the Zone II 42" (AN-BW-TIERS). Every one is a `PIER_CONCRETE_12` on
# its own `Footing`, which is precisely this module's gate — the retired sonotubes they
# replaced were `Pier` elements standing under WOOD posts and were never in it.
_ENTRY_PIERS = ("PT-BW-W", "PT-BW-E", "PT-BW-RE", "PT-BW-GW", "PT-BW-GE", "PT-BW-RNE")
#: Retired 2026-09-10 with the framed terrace they carried. Kept named so that a pier tag
#: coming BACK is a visible change: the eight stood east of a flight that runs west, under
#: open ground, and the tiers they were meant to support are cast pours now (SL-BW-TIER1..4).
_TIER_PIERS = tuple(f"PT-BW-T{_n}{_s}" for _n in (1, 2, 3, 4) for _s in ("W", "E"))
# The wind rows rose 0.5% on 2026-09-03 and no member moved. `balcony_wind.ground_below_ft`
# takes the LOWEST site spot elevation as the ground under this deck, and the two over the
# sunken garden fell 4 11/16" (the court's flood step, plus 1 7/16" of stale annotation).
# A lower floor is a taller structure: z 23.0' -> 23.3', q_h 18.7 -> 18.8 psf. The guard case
# still governs both rows, so no capacity comparison changes.
_CORNER_ORACLE = {
    "PT-SG-BF1": {"height_in": 108.125, "wind_lb_ft": 1384.7, "guard_lb_ft": 2502.1},
    "PT-SG-BF3": {"height_in": 108.125, "wind_lb_ft": 1384.7, "guard_lb_ft": 2502.1},
    # The rear row runs 2" proud for the deck's drainage crown.
    "PT-SG-BR1": {"height_in": 110.125, "wind_lb_ft": 1410.3, "guard_lb_ft": 2535.4},
    "PT-SG-BR3": {"height_in": 110.125, "wind_lb_ft": 1410.3, "guard_lb_ft": 2535.4},
}
#: §4 of the note: phi*Mn at the column's own axial load, hand-worked term by term.
#:
#: ** RE-WORKED AT 5,000 psi ON 2026-09-10. ** `SUNKEN_GARDEN_COLUMN_12` stated its mix in
#: prose only, so every calc on these four fell back to the presumptive 3,000 while the
#: identical column four feet away (PT-SG-COL, on PIER_CONCRETE_12) was graded on the 5,000
#: both are poured from. The assembly names EXPOSED_MIX now. 20,900 -> 24,700 lb-ft, and
#: only about half of that is the concrete: beta1 steps 0.85 -> 0.80, `c` falls to 2.752",
#: the concrete resultant moves out to +4.695", and the extreme tension strain rises past
#: Table 21.2.2's transition band so phi goes 0.872 -> 0.900.
_CORNER_PHI_MN_LB_FT = 24_700.0
#: §7: ld = (60,000 / (25 sqrt(5,000))) x 0.625 = 21.2", x 1.3 for a class B splice.
#: 35.6" at the presumptive 3,000 psi — development length goes as 1/sqrt(f'c), so reading
#: the real mix SHORTENS the required lap. The assembly's own source text still specifies
#: "~30in", which is longer than required and is what gets built; this is the requirement,
#: not the detail.
_CLASS_B_LAP_IN = 27.6

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
    """Two belled piers, four standing on a concrete wall top, and thirteen at the north
    entry.

    A post on a FLOOR or on a WOOD post is somebody else's rule, and so is a wood post on
    anything. The wall case joined this module on 2026-09-03: the four balcony corner
    columns are exactly the member it grades and had no ``Footing`` of their own, so they
    fell out of the enumeration entirely and the check that named them reported "an
    engineer's design governs, and this engine computes none" about a column the engine
    could compute perfectly well.

    The north entry joined it on 2026-09-10 for the same reason from the other direction:
    the passage's four wood-post-on-sonotube stacks became cast piers, each on its own
    ``Footing``, and the pier is now the member rather than the thing a member stands on.
    The four 6x6 KDAT roof columns on top of them stay out, because a wood post on anything
    is somebody else's rule.

    Six, not thirteen. Later the same day the eight tier piers went: they were laid out east
    of a flight that runs WEST, so all eight stood under open ground carrying nothing, and
    the terrace they were meant to hold up is four cast pours on a compacted base now.
    ``PT-BW-RNE`` arrived in the same pass as the canopy's fourth column.
    """
    assert set(piers) == {"PT-SG-COL", "PT-SG-FCOL", *_CORNER_PIERS, *_ENTRY_PIERS}
    assert not set(_BREEZEWAY_PIERS) & set(piers)
    assert not set(_TIER_PIERS) & set(piers)
    assert not {"PT-BW-CW", "PT-BW-CE", "PT-BW-CNW", "PT-BW-CNE",
                "PT-BW-IC", "PT-BW-IE"} & set(piers)


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

    PT-SG-BR2 and PT-SG-BF2 each stand on the porch DECK and each carries the middle of the
    balcony. Until 2026-09-03 ``pier_basis`` handed load down only post-to-post, so a pillar
    on a FloorSystem handed nothing and PT-SG-COL was graded on 82.33 ft2 with a third of a
    balcony landing on it uncounted. Both now hand their share through the deck's beams to
    the column under them.

    And the share itself is the BEAM's, not a fraction of the deck: BM-SG-BLC runs the
    balcony's full depth onto these two pillars alone while the two edge beams share four
    posts, so a sixth of the deck was never what either pillar carried.
    """
    own_porch_share = 72.50          # 2 porch beams x 7.25' strip x 10.00' over 2 supports
    balcony_share = 48.33            # BM-SG-BLC, 10.00' strip x 9.67' over its 2 posts
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
    # One diameter on both since 2026-09-10, so this now reads as two identical rows. Keep
    # both: the point is that the CIRCLE is taken, and a single row could be satisfied by a
    # square of some other bell.
    for tag, dia_in in (("PT-SG-COL", 36.0), ("PT-SG-FCOL", 36.0)):
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

    plan = _mutated(tmp_path, [(_COL_CAGE_SOURCE, ""), (_STRUCT_CAGE_SOURCE, "")])
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

    plan = _mutated(tmp_path, [(_COL_CAGE_SOURCE, _UNREADABLE_CAGE_SOURCE),
                               (_STRUCT_CAGE_SOURCE, "")])
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

    plan = _mutated(tmp_path, [(_SPEC_CAGE_SOURCE, _SPEC_SHORT_CAGE_SOURCE),
                               (_STRUCT_BAR_SOURCE, _STRUCT_SHORT_BAR_SOURCE)])
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

    from typehaus.checks.structural.deck import _decks, _tributaries_ft2
    from typehaus.engineering.pier_basis import _deck_tributaries
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    mine = _deck_tributaries(EngineeringContext(plan=catlin_plan, model=model))

    ctx = check_context(plan=catlin_plan)
    theirs: dict[str, float] = {}
    for deck in _decks(ctx):
        for tag, share in (_tributaries_ft2(ctx, deck) or {}).items():
            theirs[tag] = theirs.get(tag, 0.0) + share

    assert set(mine) == set(theirs)
    # And it is the BEAM-WEIGHTED answer both are giving, not the even split they used to
    # agree on: BM-SG-BLC hands its two pillars half its own strip each, which is half again
    # what a sixth of the balcony would have been.
    assert mine["PT-SG-BR2"] == pytest.approx(48.33, abs=0.02)
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
    # 0.12 until 2026-09-10; the denominator rose 17% when the assembly's 5,000 psi mix
    # became readable. Not one demand moved: wind is a pressure on a guard and a deck, and
    # the guard case is R301.5's 200 lb. Neither has an opinion about the concrete.
    #
    # 0.10 -> 0.16 on 2026-09-11, and this time it is the NUMERATOR. Both base moments were
    # compared at working stress against phi*Mn, a strength capacity, evaluated at a
    # factored Pu — two bases inside one P-M point. The guard's SERVICE 200 lb now takes
    # ASCE 7-16 §2.3.1's 1.6L and wind goes from 0.6W back to 1.0W. Nothing about the
    # structure moved and no column is re-sized: a sixth of phi*Mn is still a section
    # nowhere near spent. See deck_post.STRENGTH_FROM_ASD_WIND.
    assert guard.demand / guard.capacity == pytest.approx(0.16, abs=0.01)
    assert guard.demand == pytest.approx(
        _CORNER_ORACLE[tag]["guard_lb_ft"] * 1.6, abs=2.0), "1.6L, not the service load"
    assert states["bending at base, wind"].demand == pytest.approx(
        _CORNER_ORACLE[tag]["wind_lb_ft"] / 0.6, abs=2.0), "1.0W, not 0.6W"
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
    assert spans["BM-SG-BLC"] == pytest.approx(7.0, abs=0.01)
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


# --- the north entry canopy: a ROOF-carrying moment column ------------------------------
#
# `notes/north_entry_piers.md` §8 is the hand pass these reproduce. Until 2026-09-11 both
# columns published `SCREENING: axial only, no moment and no lateral case.` while
# `notes/north_entry_structure.md` §1a called them the canopy's east lateral system in
# print — a false claim the tests did not catch because nothing asked.
_CANOPY_COLUMNS = ("PT-BW-RE", "PT-BW-RNE")
#: §8's table, term by term. The ASD base moment is the roof-plane shear on the full shaft
#: plus the shaft drag at its own mid-height lever; `deck_post` then divides by 0.6 for
#: §2.3.1's 1.0W.
_CANOPY_ORACLE = {
    "PT-BW-RE": {"height_ft": 15.349, "drag_arm_ft": 9.957, "wind_asd_lb_ft": 9_461.0},
    "PT-BW-RNE": {"height_ft": 12.729, "drag_arm_ft": 7.337, "wind_asd_lb_ft": 7_680.0},
}
#: §8: 0.6 x 18.335 psf x 0.85 x 1.80, the ASD pressure every band below is multiplied by.
_CANOPY_ASD_PRESSURE_PSF = 16.831
#: §8: the N-S case governs — the gable-end triangle (26.667' x 4.444'/2 = 59.26 ft2) with
#: no header band, because both headers run north-south and present their ends to N-S wind.
_CANOPY_TOP_SHEAR_LB = 997.4
#: Two 12" shafts, each 10.78' of exposed length (eave +7.951' down to Site.grade -2.833').
_CANOPY_DRAG_SHEAR_LB = 363.0


@pytest.mark.parametrize("tag", _CANOPY_COLUMNS)
def test_a_roof_carrying_column_is_a_lateral_system_too(tag, piers) -> None:
    """The whole of finding 1. A canopy column carries a roof header, not a deck, and every
    path into the moment machinery was gated on ``FloorSystem.service == "deck"``."""
    pier = piers[tag]
    assert pier.lateral_system is True
    assert pier.wind_base_moment_lb_ft > 0.0
    # No guard on a canopy, and the slot is left at zero rather than filled with an
    # invented 200 lb.
    assert pier.guard_base_moment_lb_ft == 0.0
    assert "RF-BW-CANOPY" in pier.moment_basis


@pytest.mark.parametrize("tag", _CANOPY_COLUMNS)
def test_the_canopy_base_moment_reproduces_the_note(tag, piers) -> None:
    """§8 term by term: two shears at two lever arms, all of it on the two cast columns."""
    want = _CANOPY_ORACLE[tag]
    pier = piers[tag]
    assert pier.height_in / 12.0 == pytest.approx(want["height_ft"], abs=0.01)
    hand = (_CANOPY_TOP_SHEAR_LB / 2.0) * want["height_ft"] \
        + (_CANOPY_DRAG_SHEAR_LB / 2.0) * want["drag_arm_ft"]
    assert hand == pytest.approx(want["wind_asd_lb_ft"], rel=0.005)
    assert pier.wind_base_moment_lb_ft == pytest.approx(want["wind_asd_lb_ft"], rel=0.005)


def test_nothing_is_claimed_for_the_west_shear_panel(piers) -> None:
    """The frame's whole shear goes on the two cast columns.

    W-BW-SCREEN is a sheathed 2x4 panel on the west line and is the canopy's west lateral
    system in fact. Splitting between it and a 12" cast column is a relative-rigidity
    judgement this engine has no standing to make, so it makes none and takes the whole
    frame shear east — the same reasoning ``_base_moments`` applies to the guard load.
    """
    for tag in _CANOPY_COLUMNS:
        assert "NOTHING is claimed for a sheathed panel" in piers[tag].moment_basis
    # And the west line's own columns are wood, so they never reach this module at all.
    assert "PT-BW-CW" not in piers and "PT-BW-CNW" not in piers


@pytest.mark.parametrize("tag", _CANOPY_COLUMNS)
def test_the_canopy_column_is_graded_in_bending_and_it_checks_out(tag, results) -> None:
    """A real d/c in BENDING, not `SCREENING: axial only`. The section is not re-sized."""
    record = results[f"deck_post/{tag}"]
    assert record.status is Status.OK, record.summary
    states = {state.name: state for state in record.limit_states}
    assert set(states) >= {"bending at base, wind", "bending at base, guard",
                           "magnified moment (sway)", "axial, tied column"}
    assert all(state.ok for state in record.limit_states)
    wind = states["bending at base, wind"]
    assert wind.demand == pytest.approx(
        _CANOPY_ORACLE[tag]["wind_asd_lb_ft"] / 0.6, rel=0.005), "1.0W, not 0.6W"
    # Bending governs and wind governs the bending — the reverse of the balcony, which has
    # a guard and almost no wind area.
    assert wind.demand > states["bending at base, guard"].demand
    magnified = states["magnified moment (sway)"]
    assert 0.4 < magnified.demand / magnified.capacity < 0.85, (
        "the demand is a deliberate over-read (see §8's 2.1x against the §27.3.2 hand "
        "pass); if this ever reaches 1.0 the note's wood alternate is back on the table")
    assert "no moment and no lateral case" not in " ".join(record.notes)


def test_the_canopy_demand_bounds_the_free_roof_provision(piers) -> None:
    """§8's whole argument, as a number.

    ASCE 7-16 §27.3.2 is the literal provision and its C_N comes out of Fig. 27.3-4, a
    copyrighted grid this repository does not hold — the same problem Fig. 29.3-1 poses.
    So the roof's vertical projection is taken as a SOLID SIGN at MAX_VERIFIED_CASE_AB
    instead. §8 works the §27.3.2 case by hand at about 470 lb ASD across the frame; the
    surrogate must be comfortably above it, or the bound is not one.
    """
    from typehaus.wind_tables import MAX_VERIFIED_CASE_AB

    frame_shear = _CANOPY_TOP_SHEAR_LB + _CANOPY_DRAG_SHEAR_LB
    assert frame_shear / 470.0 > 2.0
    for tag in _CANOPY_COLUMNS:
        basis = piers[tag].moment_basis
        assert f"C_f {MAX_VERIFIED_CASE_AB:.2f}" in basis
        assert "Fig. 27.3-4" in basis and "a bound, not a reading" in basis


def test_one_knee_brace_does_not_silence_every_other_column(tmp_path) -> None:
    """The latent defect found beside finding 1, and the reason it had to be fixed now.

    ``_base_moments`` bailed GLOBALLY on the first ``KneeBrace`` in the plan. The owner has
    accepted knee braces as a fallback at the canopy, and `notes/north_entry_piers.md` §7
    names a KBS1Z at each column as the cheap answer if the roof joint ever becomes a real
    break — so one brace authored there would have switched moment grading off for the four
    BALCONY columns half a house away, at zero FAIL and with nothing in any report to read.
    """
    from typehaus.engineering.pier_basis import knee_braced

    plan = _catlin()
    # No brace anywhere today, so nothing is braced and every structure keeps its moment.
    assert knee_braced(plan, {"PT-SG-BF1", "PT-SG-BF3"}) is False
    assert knee_braced(plan, {"PT-BW-RE", "PT-BW-RNE"}) is False

    braced = _with_a_canopy_knee_brace(plan)
    assert knee_braced(braced, {"PT-BW-RE", "PT-BW-RNE", "BM-BW-RE"}) is True, \
        "the brace is on the canopy and the canopy must see it"
    assert knee_braced(braced, {"PT-SG-BF1", "PT-SG-BF3", "BM-SG-BLW"}) is False, \
        "a canopy brace must not reach across the house and silence the balcony"


def _catlin():
    from pathlib import Path

    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = load_plan(catlin)
    assert result.plan is not None
    return result.plan


def _with_a_canopy_knee_brace(plan):
    """catlin's elements plus the one KBS1Z §7 names, at PT-BW-RE.

    A stub plan rather than an authored element: ``knee_braced`` reads exactly two things,
    ``all_elements`` and ``by_tag``, and adding a real brace to the house would move the
    model every other test in this file measures. The point under test is the SCOPE of the
    bail, not the brace's geometry.
    """
    from typehaus.model.structure import KneeBrace
    from typehaus.quantities import ft, inch

    column = plan.by_tag("PT-BW-RE")
    brace = KneeBrace(
        uid="TESTKB0001", tag="CN-BW-TESTKB", position=column.position,
        soffit_elevation=inch(76.75), leg=ft(2), axis="y", member="2x6",
        post_size="12 round", connects=("PT-BW-RE", "BM-BW-RE"))
    return _PlanWith(plan, brace)


class _PlanWith:
    """``plan`` with one more element, for ``knee_braced``'s two-method interface."""

    def __init__(self, plan, extra) -> None:
        self._plan = plan
        self._extra = extra

    def all_elements(self):
        return [*self._plan.all_elements(), self._extra]

    def by_tag(self, tag: str):
        return self._extra if tag == self._extra.tag else self._plan.by_tag(tag)
