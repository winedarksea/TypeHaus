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
  the more easily lost one: a pier carrying a member with no plan area anywhere in the model
  has a tributary that is an under-count of unknown size, so the record grades the cage in
  full and omits the axial state. A d/c appearing there is the regression this guards. It is
  SYNTHETIC since 2026-09-20 — the breezeway piers that used to exercise it are retired, and
  `pier_basis.wall_line_loads` took the last two catlin piers out of that branch by pricing
  the wall they carry. A branch nothing walks through is a branch that rots.
* :func:`test_a_wall_on_a_beam_is_a_line_load_and_reaches_the_piers_under_it` is the other
  half of that change and its oracle is `north_entry_piers.md` §2.
"""

from __future__ import annotations

import math

import pytest

from typehaus.engineering.item import Status

# The cage, as `params/sunken_garden.py` authors it (§4c of the note).
#
# Since 2026-09-03 every cast column in the sunken garden carries the SAME cage: PT-SG-FCOL
# came down from 20" round / (8) #6 to 12" round / (4) #5 when PT-SG-BF2 stopped standing on
# its top, and the four balcony corner columns arrived at the same section. Since 2026-09-12
# PT-SG-COL reads `SPEC.corner_column_cage` too, so ALL SIX spell ONE string — the cage is a
# fabricated part and the drawing names one part to order. `_COL_CAGE` survives only as a
# `parse_cage` fixture: it is the bare form the north-entry pours still author.
_COL_CAGE = '(4) #5 vertical, #3 ties @ 10" o.c.'
_FCOL_CAGE = ('(4) #5 vertical, #3 ties @ 10" o.c., 2" cover, '
              'galvanized (ASTM A767 after fabrication, or A1094)')
# The corner columns' two cage lines in the PILLARS loop, at its 28-space indent. Since
# PT-SG-COL retired (2026-09-22) the four corners are the only court columns left, so the
# strip tests break all four at once and take a north-entry pier as the control.
_COL_CAGE_SOURCE = ("                            vertical_reinforcement=SPEC.corner_column_cage,\n"
                    "                            reinforcement=_MOMENT_COLUMN_CAGE,\n")
_UNREADABLE_CAGE_SOURCE = (" " * 28) + "vertical_reinforcement='rebar per engineer',\n"
# The SPEC field the four 12" corner columns share. Mutating it moves all four at once, which is
# what `test_an_under_minimum_cage_is_over_not_ok` wants.
_SPEC_CAGE_SOURCE = "corner_column_cage: str = ('(4) #5 vertical, #3 ties @ 10\" o.c., 2\" cover, '"
_SPEC_SHORT_CAGE_SOURCE = "corner_column_cage: str = ('(3) #4 vertical, #3 ties @ 10\" o.c., 2\" cover, '"

# ** SINCE 2026-09-03 A CAGE IS AUTHORED TWICE AND THE STRUCT GOVERNS. **
# `deck_post.cage_for` reads the structured `ReinforcementSpec` where one exists and does not
# call `parse_cage` at all — so mutating only the free-text string above is now INERT, and
# the three "break it on purpose" tests below would have passed while testing nothing. Each
# mutation therefore has to move both spellings. That is the same fact
# `integrity.reinforcement_spec_agrees` polices in the house: two spellings, one steel.
# The galvanized twin struct went on 2026-09-12: the coating lives on `EXPOSED_MIX` and
# `_pour_coating` reads it, so ONE `ReinforcementSpec` now feeds all six court columns and
# carries no per-bar coating. Mutating its vertical BarSpec therefore moves all six at once.
_STRUCT_BAR_SOURCE = 'BarSpec(role="vertical", bar=5, count=4),'
_STRUCT_SHORT_BAR_SOURCE = 'BarSpec(role="vertical", bar=4, count=3),'

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
# ** 120.83 -> 119.17 ft² ON 2026-09-14, AND IT IS AN ARTEFACT RATHER THAN A LOAD CHANGE. **
# The two centre pillars came down onto these column tops, so each porch beam stops 2 3/4"
# short of the column axis and hangs off the pillar's face (HU212-3) instead of bearing on
# the pour. ``_weighted_shares`` reads ``share = strip_ft * length_ft`` off the beam's own
# node-to-node length, so four beams 2 3/4" shorter is 1.66 ft² less tributary — 10.00' ->
# 9.77' per beam, 72.50 -> 70.84 ft² of porch share.
#
# **The deck did not shrink and the load did not go anywhere.** The 2 3/4" of porch at each
# beam end is carried by the pillar chase's header into the joist lines either side and
# reaches the same beams. So the model UNDER-counts this column by 1.4% and the notes say so;
# it is the direction a demand should not err in, and it is recorded rather than corrected
# because ``length_ft`` is the proxy the whole module is built on. d/c 0.60 -> 0.59 on the
# governing bearing state, so nothing turns on it.
#
# The tributary is BEAM-WEIGHTED as of 2026-09-03: each column takes half of each porch beam
# that lands on it (the bearing WALL at the beam's far end taking the other half) plus half of
# BM-SG-BLC, handed down by its centre pillar (48.33 ft²).
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
        "tributary_ft2": 119.17, "dead_lb": 2528.0, "live_lb": 4767.0,
        "service_lb": 7295.0, "factored_lb": 10_662.0,
        # 4.909 / 1651 while this bell was 30". Both bells are 36" since 2026-09-10 — the
        # 36" was a fossil from a 20" column and the 30" was set by nothing — which takes
        # the tightest pier in the house from d/c 0.83 to 0.60 for ~0.09 cy of concrete.
        # NET of the 778 lb of soil the bell displaced (§3c, 110 pcf at the low end of
        # the band) — a flat 110 psf off the 1,182 the gross convention read until
        # 2026-09-18. See `engineering/soil.displaced_soil_credit_lb`.
        "bell_area_ft2": 7.069, "bearing_psf": 1072.0,
        "gross_in2": 113.1, "h_over_d": 10.68, "min_steel_in2": 1.131,
        # §4c / §4d / §4e of the note.
        "cage": _FCOL_CAGE, "bars": 4, "steel_in2": 1.24,
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
        "tributary_ft2": 119.17, "dead_lb": 2527.0, "live_lb": 4767.0,
        "service_lb": 7294.0, "factored_lb": 10_660.0,
        # NET of the 778 lb of soil the bell displaced (§3c, 110 pcf at the low end of
        # the band) — a flat 110 psf off the 1,182 the gross convention read until
        # 2026-09-18. See `engineering/soil.displaced_soil_credit_lb`.
        "bell_area_ft2": 7.069, "bearing_psf": 1072.0,
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
#
# ** WIND FELL 1,385 -> 1,140 ON 2026-09-22 ** (note §12b): BM-SG-BLC's 11 7/8" band left
# with the centre line and the 2x12 deck edge is 13", so A_s 35.94 -> 29.60 sf, 506 lb of
# storey shear over the same four columns. The guard rows did not move.
_CORNER_ORACLE = {
    "PT-SG-BF1": {"height_in": 108.125, "wind_lb_ft": 1140.4, "guard_lb_ft": 2502.1},
    "PT-SG-BF3": {"height_in": 108.125, "wind_lb_ft": 1140.4, "guard_lb_ft": 2502.1},
    # The rear row runs 2" proud for the deck's drainage crown.
    # ** THE REAR PAIR LOST 1/6" ON 2026-09-14. ** ``SPEC.rear_pillar_rise_in = 2.0`` became
    # ``SPEC.balcony_fall_in_per_ft = 0.25``: the FALL is the authored number now and the rise
    # follows the run between the bearing rows, which over 7'-4" is 1.833" rather than 2.000".
    # Both base moments are ``shear x height``, so they follow it exactly and by the same
    # 0.15%. Nothing else about the rear row moved.
    "PT-SG-BR1": {"height_in": 109.958, "wind_lb_ft": 1159.7, "guard_lb_ft": 2532.6},
    "PT-SG-BR3": {"height_in": 109.958, "wind_lb_ft": 1159.7, "guard_lb_ft": 2532.6},
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
#:
#: ** 24,700 -> 25,470 ON 2026-09-22 (note §12c). ** P_u rose 4,947 -> 7,886 lb when the
#: balcony went wall-to-wall on two beams, and below balance more axial is more moment
#: capacity: c 2.752" -> 2.809", C_c 60,473 -> 62,268 lb. The rear row reads 25,476.
#:
#: ** 25,470 -> 24,678 ON 2026-09-23 (note §13). ** Each edge beam carries its own 9.75'
#: strip, not the 18' joist span: P_u 7,886 -> 4,855 lb, c 2.809" -> 2.750". Rear 24,684.
_CORNER_PHI_MN_LB_FT = 24_678.0
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

    ``PT-SG-COL`` / ``PT-SG-FCOL`` left on 2026-09-22 with the 17'-0" court: both decks span
    wall to wall and there is no centre support line. Their oracle rows live on in
    conftest's ``catlin_retired_columns``.
    """
    assert set(piers) == {*_CORNER_PIERS, *_ENTRY_PIERS}
    assert not {"PT-SG-COL", "PT-SG-FCOL"} & set(piers)
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


def test_a_pad_borne_pier_gets_no_engineered_bearing_record(results, piers) -> None:
    """§6 — a ``Pad`` IS an IRC Table R507.3.1 row, graded by
    ``structural.deck_footing_size``. Two authorities on one number is worse than one.

    ** AND AS OF 2026-09-14 THAT IS EVERY PIER IN THE HOUSE. ** This used to close with
    ``"spread_footing/PT-SG-COL" in results`` as its control — proof that the exclusion was
    selective rather than a module that had stopped running. The two centre-garden bells came
    off and onto pads that day, and with them the last ``spread_footing`` item catlin had.

    So the control is inverted rather than dropped: the register must hold **no** such item,
    and the reason is the one above rather than a calc that silently stopped computing.
    ``_piers_on_their_own_footing`` is asked directly for the same answer, because an empty
    ``results`` slice and a calc that never ran look identical from here.
    """
    for tag in _BREEZEWAY_PIERS:
        assert f"spread_footing/{tag}" not in results
    assert not [item for item in results if item.startswith("spread_footing/")], (
        "catlin has a belled pier again — restore a positive control here, and check whether "
        "conftest's `catlin_retired_bells` should now read it off the house")
    assert piers, "every pier stopped being a pier — the fixture has drifted"


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_load_path_reproduces_the_note(tag, catlin_retired_columns) -> None:
    """§2's table, term by term. Two errors can cancel inside a d/c ratio.

    On conftest's rebuilt columns since 2026-09-22: the tributary is the note's input, so
    what is checked is ``_Pier``'s D / L / P_u arithmetic against the note's own table.
    """
    want = _ORACLE[tag]
    pier = catlin_retired_columns[tag]
    assert pier.tributary_ft2 == pytest.approx(want["tributary_ft2"], abs=0.02)
    assert pier.dead_lb == pytest.approx(want["dead_lb"], abs=3.0)
    assert pier.live_lb == pytest.approx(want["live_lb"], abs=2.0)
    assert pier.service_lb == pytest.approx(want["service_lb"], abs=4.0)
    assert pier.factored_lb == pytest.approx(want["factored_lb"], abs=5.0)
    assert pier.gross_area_in2 == pytest.approx(want["gross_in2"], rel=0.001)


def test_no_deck_borne_pillar_is_left_handing_a_share_to_nobody(catlin_plan, piers) -> None:
    """`structural.deck_footing_size` reported N/A on a pillar standing on a deck and said
    its share was picked up by the pier below. **That sentence was a promise** (§2).

    ** THE PILLARS ARE GONE SINCE 2026-09-22. ** PT-SG-BR2/BF2 retired with the centre
    support line, so no catlin post stands on a ``FloorSystem`` any more and no pier carries
    a pillar's dead load. What is kept is the promise's other half: nothing in the court
    names a floor as its bearing, so there is no share to lose. The retired columns' own
    48.33 ft2 pillar share is in ``catlin_retired_columns`` (note §2).
    """
    from typehaus.model import FloorSystem, Post

    for post in catlin_plan.all_elements():
        if isinstance(post, Post) and post.tag.startswith("PT-SG-"):
            assert not isinstance(catlin_plan.by_tag(post.supported_by or ""), FloorSystem), (
                f"{post.tag} stands on a deck again — restore the hand-down assertion")
    assert not {"PT-SG-BR2", "PT-SG-BF2"} & {e.tag for e in catlin_plan.all_elements()}
    for tag in _CORNER_PIERS:
        assert piers[tag].carried_dead_lb == 0.0, tag


def test_the_bell_is_read_as_a_circle_not_the_resolved_square(catlin_retired_bells) -> None:
    """§3a — the calculation disagrees with the resolved solid ON PURPOSE.

    `resolve/envelope.py` draws a post-hosted footing as a SQUARE of side `width`, and
    `params/sunken_garden.py` calls that same number a bell DIAMETER. Taking the square
    credits 27% more bearing area than exists, in the unconservative direction.

    ** RUNS ON conftest's RECONSTRUCTED BELLS SINCE 2026-09-14 ** — catlin draws no
    post-hosted footing solid any more, so the "and the resolved solid really is the bigger
    square" half cannot be re-read off ``catlin_model``; the square is computed from the same
    ``width`` the resolver would have taken. The disagreement itself is still live code in
    ``pier_basis``, which is what is asserted.
    """
    _ctx, piers = catlin_retired_bells
    # One diameter on both since 2026-09-10, so this now reads as two identical rows. Keep
    # both: the point is that the CIRCLE is taken, and a single row could be satisfied by a
    # square of some other bell.
    for tag, dia_in in (("PT-SG-COL", 36.0), ("PT-SG-FCOL", 36.0)):
        pier = piers[tag]
        circle = math.pi * (dia_in / 2.0) ** 2 / 144.0
        square = (dia_in / 12.0) ** 2
        assert pier.bearing_area_ft2 == pytest.approx(circle, rel=1e-6)
        assert pier.bearing_area_ft2 == pytest.approx(_ORACLE[tag]["bell_area_ft2"], abs=0.002)
        assert pier.bearing_area_ft2 < square * 0.80


@pytest.fixture(scope="module")
def records(catlin_retired_bells):
    """``spread_footing`` on the two bells conftest puts back. See ``catlin_retired_bells``."""
    from typehaus.engineering.spread_footing import _one

    ctx, piers = catlin_retired_bells
    return {tag: _one(ctx, pier) for tag, pier in piers.items()}


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_bearing_checks_out_on_the_sites_own_soil(tag, records) -> None:
    """§3c. And the allowable is the SITE's class 4, not the washed stone's class 3.

    The retaining footings earn 3,000 psf from a 42" replacement section. These bells were
    augered to frost depth to bear on undisturbed soil and carry a 7" LEVELLING course;
    reading the stone's number off that would be a sixth of a section's worth of credit.

    ** ON conftest's RECONSTRUCTED BELLS SINCE 2026-09-14 ** — both piers stand on pads now
    and mint no ``spread_footing`` record at all, which is what the test above asserts. The
    bearing derivation is unchanged and still the only one the engine has for a bell.
    """
    record = records[tag]
    assert record.status is Status.OK, record.summary
    state = next(s for s in record.limit_states if s.name == "bearing")
    assert state.demand == pytest.approx(_ORACLE[tag]["bearing_psf"], abs=3.0)
    assert state.capacity == pytest.approx(_PRESUMPTIVE_ALLOWABLE_PSF)
    assert "class 4" in state.citation
    assert state.ok


@pytest.fixture(scope="module")
def retired_posts(catlin_retired_columns):
    """``deck_post`` on the two columns conftest rebuilds from the note (retired 2026-09-22)."""
    from typehaus.engineering.deck_post import _one

    return {f"deck_post/{tag}": _one(pier) for tag, pier in catlin_retired_columns.items()}


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_cage_reproduces_the_hand_worked_design(tag, retired_posts,
                                                    catlin_retired_columns) -> None:
    """§4c and §4d — the cage the house authored, and the capacity it buys."""
    want = _ORACLE[tag]
    assert catlin_retired_columns[tag].vertical_reinforcement == want["cage"]

    record = retired_posts[f"deck_post/{tag}"]
    assert record.status is Status.OK, record.summary
    assert not record.missing

    state = next(s for s in record.limit_states if s.name == "axial, tied column")
    assert state.demand == pytest.approx(want["factored_lb"], abs=5.0)
    assert state.capacity == pytest.approx(want["capacity_lb"], rel=0.002)
    # The section is enormous for the load; the cage is NOT there for strength.
    assert state.demand / state.capacity < 0.10


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_cage_sits_at_the_code_minimum_and_not_below_it(tag, retired_posts) -> None:
    """§4b/§4c — the 1% floor is what sizes these cages, and both clear it by ~10%.

    **This is the assertion that stops a well-meant "save concrete" edit.** The columns run
    at d/c 0.06; nothing about the load justifies less steel, because ACI 318-19 §10.6.1.1's
    floor covers creep, shrinkage and the accidental moment and is indifferent to loading.
    """
    want = _ORACLE[tag]
    record = retired_posts[f"deck_post/{tag}"]

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
def test_the_ties_are_at_the_25_7_2_2_maximum(tag, retired_posts) -> None:
    """§4b — least of 16db, 48dt and the column's own least dimension."""
    want = _ORACLE[tag]
    record = retired_posts[f"deck_post/{tag}"]
    spacing = next(s for s in record.limit_states if s.name == "tie spacing")
    assert spacing.demand == pytest.approx(want["tie_spacing_in"])
    assert spacing.capacity == pytest.approx(want["tie_spacing_in"]), (
        "the authored spacing IS the code maximum for this cage — if this drifts, the "
        "house got cheaper than the code allows")
    assert spacing.ok
    assert next(s for s in record.limit_states if s.name == "tie size").ok


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_slenderness_is_carried_and_the_minimum_eccentricity_is_covered(tag,
                                                                       retired_posts) -> None:
    """§4e — the argument that lets one axial comparison be the whole check.

    Both are past §6.2.5's non-sway floor of 34 (PT-SG-FCOL was at 25.6 and neglectable
    outright while it was a 20" round — shrinking a column is the one edit that makes
    slenderness appear), and both end in the same place: the magnified minimum eccentricity
    is INSIDE the 0.10h that R22.4.2 says the 0.80 axial cap already carries, so no
    interaction diagram is needed.
    """
    want = _ORACLE[tag]
    record = retired_posts[f"deck_post/{tag}"]
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

    for tag in _CORNER_PIERS:
        record = results[f"deck_post/{tag}"]
        assert record.status is Status.INCOMPLETE, record.summary
        assert any("vertical_reinforcement" in m for m in record.missing), record.missing
        assert any("14.1.5" in m for m in record.missing), record.missing
    # A north-entry pier still has its cage, so this is the field and not a global break.
    assert results["deck_post/PT-BW-W"].status is Status.OK


def test_a_cage_that_does_not_parse_reads_as_no_steel(tmp_path) -> None:
    """Same contract as `retaining_basis.parse_reinforcement`: unreadable is NOT a pass."""
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    plan = _mutated(tmp_path, [(_COL_CAGE_SOURCE, _UNREADABLE_CAGE_SOURCE)])
    model, _ = resolve(plan)
    results = EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))
    for tag in _CORNER_PIERS:
        assert results[f"deck_post/{tag}"].status is Status.INCOMPLETE, tag


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

    record = results["deck_post/PT-SG-BF1"]
    assert record.status is Status.OVER, record.summary
    steel = next(s for s in record.limit_states if s.name == "longitudinal steel")
    assert not steel.ok
    assert steel.capacity == pytest.approx(0.60, abs=0.005)
    count = next(s for s in record.limit_states if s.name == "bar count")
    assert not count.ok
    # And it takes all four corner columns with it — one SPEC field feeds them.
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


def test_both_piers_are_columns_and_not_pedestals(catlin_retired_columns) -> None:
    """The ratio that decides which ACI chapter applies. A pedestal may be plain; a column
    may not, and that single fact is the whole reason the records above are INCOMPLETE."""
    from typehaus.engineering.deck_post import PEDESTAL_HEIGHT_RATIO

    assert PEDESTAL_HEIGHT_RATIO == 3.0
    for tag in _ORACLE:
        pier = catlin_retired_columns[tag]
        ratio = pier.height_in / pier.diameter_in
        assert ratio == pytest.approx(_ORACLE[tag]["h_over_d"], abs=0.05)
        assert ratio > PEDESTAL_HEIGHT_RATIO


def test_the_deck_tributary_rule_is_single_sourced(catlin_plan) -> None:
    """Every reader of the deck rule gets ``engineering/deck_tributary``'s half-bay strip.

    Since 2026-09-23 ``pier_basis``, ``post_bearing``, ``analytical/loads`` and the check
    all call it, where four of them used to hand every beam the whole joist span. What is
    left to assert is that they agree, and the number itself.
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
    # Each balcony glulam carries 18'/2 + 9" = 9.75' (glulam_beam's own strip) over its
    # 9.667' length, halved between its two corner columns: the 188.5 ft2 deck, once.
    assert mine["PT-SG-BR1"] == pytest.approx(9.75 * 9.667 / 2.0, abs=0.02)
    assert sum(mine[t] for t in ("PT-SG-BR1", "PT-SG-BF1", "PT-SG-BR3", "PT-SG-BF3")) \
        == pytest.approx(19.5 * 9.667, abs=0.1)
    for tag, value in theirs.items():
        assert mine[tag] == pytest.approx(value, rel=1e-9), tag

    # post_bearing's beam load is the same strip at 50 psf; BR1 sits 7.333' behind BF1,
    # which is 0.667' in from the front of the 9.667' beam (analytical_model_basis §3c).
    from typehaus.engineering.glulam_beam import DECK_TOTAL_LOAD_PSF
    from typehaus.engineering.post_bearing import _reaction_lb

    ectx = EngineeringContext(plan=catlin_plan, model=model)
    reaction, beams = _reaction_lb(ectx, catlin_plan.by_tag("PT-SG-BR1"))
    assert beams == ("BM-SG-BLW",)
    assert reaction is not None
    total = DECK_TOTAL_LOAD_PSF * 9.75 * 9.667
    assert reaction == pytest.approx(total * (9.667 / 2 - 0.667) / 7.333, rel=0.01)


def _deck_posts_everywhere(plan):
    """Every post any deck delivers load to, across all decks."""
    from _helpers import check_context

    from typehaus.checks.structural.deck import _deck_posts, _decks

    ctx = check_context(plan=plan)
    return [post for deck in _decks(ctx) for post in _deck_posts(ctx, deck)]


def test_the_roof_tributary_rule_is_single_sourced_and_reaches_both_halves(catlin_ctx) -> None:
    """``_roof_borne_posts`` IS ``pier_basis.landed_roof_tributaries``, scaled.

    ** WHAT THIS REPLACES, AND THE TWO DEFECTS THE REPLACEMENT CLOSED. **
    ``test_the_two_ROOF_tributary_rules_agree_too`` pinned a hand copy of
    ``pier_basis._roof_fields`` living in ``checks/structural/deck.py``, on the claim that
    the package layering forbade the import. It does not — ``checks`` imports
    ``engineering`` in some twenty places — so the copy was unnecessary, not forced, and it
    had drifted in two directions at once. It restated only ``_roof_fields`` and not
    ``_rafter_fields``, which the old test asserted as a documented UNDER-count rather than
    fixing; and it scaled the share at ``Site.ground_snow_load_psf`` while the beams
    overhead were designed at ``preferences.toml [structural] roof_beam_snow_psf``. Both are
    gone with the copy.

    ** AND ``_rafter_fields`` ITSELF WAS DOUBLE-COUNTING, WHICH THE OLD TEST RECORDED AND
    LEFT. ** It keyed purely on "a beam naming two beams", which in catlin is the garage
    landing's floor carriers — whose area ``_deck_tributaries`` already divides among the
    same four piers. Each collected 9.34 ft2 a second time, at the roof's snow rather than
    the deck's 40 psf. Single-sourcing made that duplicate reach
    ``structural.deck_footing_size`` too, where it flipped ``PD-BW-W`` to FAIL — so the
    field rule now skips a parent pair some ``FloorSystem`` or ``Roof`` has already
    accounted for, and catlin has no rafter field left at all.
    """
    from typehaus.checks.structural._engineering import engineering_context
    from typehaus.checks.structural.deck import _roof_borne_posts
    from typehaus.checks.structural.deck_tables import (
        DECK_DEAD_LOAD_PSF,
        DECK_TOTAL_LOAD_PSF,
    )
    from typehaus.engineering.pier_basis import (
        _rafter_fields,
        design_roof_snow_psf,
        landed_roof_tributaries,
    )

    # The house's OWN context, not ``check_context``'s empty ``Preferences``: the authored
    # design snow is the input under test, and a default-preferences context cannot see it.
    ctx = catlin_ctx
    ectx = engineering_context(ctx)

    snow, basis = design_roof_snow_psf(ectx)
    assert snow == pytest.approx(73.7), "the AUTHORED design snow, not the 50 psf ground snow"
    assert "roof_beam_snow_psf" in basis
    scale = (DECK_DEAD_LOAD_PSF + snow) / DECK_TOTAL_LOAD_PSF
    assert scale == pytest.approx(1.674, abs=0.001)

    landed, subjects = landed_roof_tributaries(ectx)
    theirs, their_subjects, their_snow = _roof_borne_posts(ctx)
    assert their_snow == pytest.approx(snow)
    assert their_subjects == subjects
    for tag, area in landed.items():
        assert theirs[tag] == pytest.approx(area * scale, rel=1e-9), tag

    # The canopy is the whole of it, and it reaches four piers, not two. Its EAST header
    # lands straight on PT-BW-RE/-RNE; its WEST one lands on PT-BW-CW/-CNW, two wood columns
    # standing on PT-BW-W/-GW — so the west half arrives at the ground two posts down, which
    # is what ``landed_roof_tributaries`` is for. The subjects set keeps naming the columns
    # in between, because a post that hands its load on still has to be reported.
    assert set(landed) == {"PT-BW-RE", "PT-BW-RNE", "PT-BW-W", "PT-BW-GW"}, sorted(landed)
    assert {"PT-BW-CW", "PT-BW-CNW"} <= subjects, sorted(subjects)
    assert all(theirs[tag] == pytest.approx(67.0, abs=0.5)
               for tag in ("PT-BW-RE", "PT-BW-RNE"))

    # And no rafter field survives the "already accounted for" gate.
    rafter, _ = _rafter_fields(ectx)
    assert rafter == {}, sorted(rafter)


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
    # The control: a pad-borne entry pier is NOT on a shared footing (the two centre-court
    # columns that used to be the control retired 2026-09-22).
    for tag in ("PT-BW-W", "PT-BW-E"):
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
    # The control: a pier under a deck TIED to a concrete wall leans — no column moment.
    # (The two porch columns that used to be it retired 2026-09-22.)
    for other in ("PT-BW-W", "PT-BW-E"):
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


# --- the balcony glulams: a PUBLISHED TABLE READ, with an NDS advisory beside it --------
#
# Until 2026-09-11 these three beams were `deck_beam/*` engineering items, delegated because
# IRC Table R507.5(1) publishes sawn plies and has no row for a glulam. That reasoning missed
# the supplier: Anthony/Canfor's Power Preserved Glulam Deck Guide tabulates exactly this
# section against exactly this joist span, and reading a published row is a prescriptive act.
#
# The NDS arithmetic did not go away and must not — the deck guide's values are DRY-use and
# every one of these stands in weather. It runs beside the table read as an advisory, and
# `engineering/glulam_beam.py` is now a pure module exposing `nds_states`.

#: ** BM-SG-BLC IS 7.25' AND ITS TWO NEIGHBOURS ARE NOT, SINCE 2026-09-14. ** PT-SG-BR2 came
#: 3" north onto PT-SG-COL's axis when it came down onto that column — its old 3" southward
#: offset only ever dodged ``cantilever.py::_band``'s epsilon, which cannot reach a post that
#: does not bear on a deck, while on concrete it would have put two of the post's corners 3/8"
#: outside a 12" round. The centre beam's back span follows its own rear bearing and grows
#: with it; BR1/BR3 did not move, so BLW/BLE are unchanged at 7.333'. The three beams are
#: three separate members with their own pairs of bearings, which is why one can move alone.
#:
#: The R507.5.1 cantilever limit moves the right way with it: the north overhang falls
#: 20" -> 17" against a limit that rises 22" -> 22.75".
#:
#: ** SINCE 2026-09-22 TWO BEAMS, EACH CARRYING 9.75' ** (note §5a): BM-SG-BLC retired and the
#: 2x12 deck spans 18'-0" wall to wall. Graded between their own posts (note §5b, basis 4):
#: 0.667' south overhang, 7.333' back span, 1.667' north. Bearing governs at 0.65.
_BALCONY_SPANS = {"BM-SG-BLW": (0.667, 7.333, 1.667), "BM-SG-BLE": (0.667, 7.333, 1.667)}
_BALCONY_JOIST_SPAN_FT = 9.75


@pytest.mark.parametrize("tag,bearings", sorted(_BALCONY_SPANS.items()))
def test_the_nds_pass_on_a_balcony_glulam(tag, bearings) -> None:
    """§5b of the note, against the pure module rather than a record."""
    from typehaus.engineering.glulam_beam import nds_states

    a, span, b = bearings
    states = {state.name: state
              for state in nds_states(3.5, 11.875, span, _BALCONY_JOIST_SPAN_FT,
                                      overhangs_ft=(a, b))}
    assert set(states) == {"bending", "shear parallel to grain",
                           "bearing, compression perpendicular", "live-load deflection"}
    assert all(state.ok for state in states.values())
    assert states["bending"].capacity == pytest.approx(1920.0, abs=1.0)   # 2,400 x C_M 0.80
    assert states["shear parallel to grain"].capacity == pytest.approx(262.5, abs=0.5)
    assert states["bearing, compression perpendicular"].capacity == pytest.approx(392.2,
                                                                                  abs=0.5)
    assert states["bending"].demand == pytest.approx(466.6, abs=0.5)
    assert states["shear parallel to grain"].demand == pytest.approx(50.3, abs=0.1)
    assert states["bearing, compression perpendicular"].demand == pytest.approx(256.1, abs=0.3)
    assert states["live-load deflection"].demand == pytest.approx(0.0347, abs=0.0003)
    worst = max(states.values(), key=lambda s: s.demand / s.capacity)
    assert worst.name == "bearing, compression perpendicular"
    assert worst.demand / worst.capacity == pytest.approx(0.653, abs=0.005)


def test_the_overhang_envelope_against_the_hand_pass() -> None:
    """§5b: reactions by statics, and the north tip under live on both overhangs."""
    from typehaus.engineering.overhang_beam import envelope

    ei = 1.8e6 * 0.833 * 3.5 * 11.875 ** 3 / 12.0
    env = envelope(0.6667, 7.3333, 1.6667, 97.5, 390.0, ei, 11.875 / 12.0)
    assert env.reactions_lb[1] == pytest.approx(2689.0, abs=2.0)
    assert env.moment_lb_ft == pytest.approx(3199.0, abs=2.0)
    assert env.shear_at_d_lb == pytest.approx(1394.0, abs=2.0)
    assert env.tip_deflection_in[1] == pytest.approx(0.0065, abs=0.0001)
    # no overhang: the simple-span closed forms
    simple = envelope(0.0, 9.667, 0.0, 97.5, 390.0, ei, 11.875 / 12.0)
    assert simple.reactions_lb[0] == pytest.approx(487.5 * 9.667 / 2.0, rel=1e-9)
    assert simple.moment_lb_ft == pytest.approx(487.5 * 9.667 ** 2 / 8.0, rel=1e-6)
    assert simple.span_deflection_in == pytest.approx(
        5.0 * 32.5 * (9.667 * 12.0) ** 4 / (384.0 * ei), rel=1e-5)


@pytest.mark.parametrize(("posts", "fragment"), [
    ((("P1", 3.0),), "a single bearing is a cantilever"),
    ((("P1", 1.0), ("P2", 5.0), ("P3", 9.0)), "3 bearings make a continuous beam"),
    ((), "no bearing_refs"),
])
def test_a_glulam_not_on_two_bearings_names_why(posts, fragment) -> None:
    from types import SimpleNamespace

    from typehaus.engineering.glulam_beam import _bearings

    m = 0.3048
    at = {"N0": 0.0, "N1": 10.0, **dict(posts)}
    elements = {k: SimpleNamespace(position=SimpleNamespace(xy_m=(x * m, 0.0)))
                for k, x in at.items()}
    beam = SimpleNamespace(tag="B", start_node="N0", end_node="N1",
                           bearing_refs=tuple(tag for tag, _ in posts))
    ctx = SimpleNamespace(plan=SimpleNamespace(by_tag=elements.get))
    why = _bearings(ctx, beam)
    assert isinstance(why, str) and fragment in why
    elements["P1"] = SimpleNamespace(position=SimpleNamespace(xy_m=(2 * m, 0.0)))
    elements["P2"] = SimpleNamespace(position=SimpleNamespace(xy_m=(8 * m, 0.0)))
    beam2 = SimpleNamespace(tag="B", start_node="N0", end_node="N1",
                            bearing_refs=("P1", "P2"))
    assert _bearings(ctx, beam2) == pytest.approx((2.0, 6.0, 2.0))


def test_wet_service_is_applied_to_the_glulam() -> None:
    """The single most common way to overstate one of these by a quarter.

    AWC NDS Table 5.3.1: C_M is 0.80 on F_b and 0.833 on E for a glulam in weather. A
    supplier's span table is quoted DRY — which is exactly why this arithmetic still runs
    beside the published row rather than being retired with the engineering item.
    """
    from typehaus.engineering.glulam_beam import GLULAM_FB_PSI, WET_FB, nds_states

    dry = GLULAM_FB_PSI
    wet = nds_states(3.5, 11.875, 7.0, _BALCONY_JOIST_SPAN_FT)[0].capacity
    assert wet == pytest.approx(dry * WET_FB, abs=1.0)
    assert wet < dry


def test_an_edge_glulam_carries_its_own_strip_not_the_whole_span() -> None:
    """§5a of the note: half a bay plus the overhang, 5.75' on a 10' bay with 9" over."""
    from typehaus.engineering.glulam_beam import nds_states

    states = {s.name: s for s in nds_states(3.5, 11.875, 9.667, 5.75)}
    assert states["bending"].demand == pytest.approx(490.0, abs=1.0)
    assert states["shear parallel to grain"].demand == pytest.approx(39.9, abs=0.2)
    bearing = states["bearing, compression perpendicular"]
    assert bearing.demand == pytest.approx(132.3, abs=0.2)
    assert bearing.demand / bearing.capacity == pytest.approx(0.34, abs=0.005)
    assert states["live-load deflection"].demand == pytest.approx(0.062, abs=0.001)


@pytest.mark.parametrize(("lines_ft", "beam_ft", "expected"), [
    ((0.75, 10.75, 20.75), 0.75, 5.75),    # an edge beam: half a bay plus the overhang
    ((0.75, 10.75, 20.75), 10.75, 10.0),   # the interior beam: half of each bay
    ((0.75, 18.75), 0.75, 9.75),           # 18' wall to wall, 9" over
])
def test_the_tributary_rule(lines_ft, beam_ft, expected) -> None:
    from types import SimpleNamespace

    from typehaus.engineering.deck_tributary import beam_tributary_ft as _beam_tributary_ft
    from typehaus.quantities import inch

    m = 0.3048
    node = {f"N{i}": SimpleNamespace(position=SimpleNamespace(xy_m=(x * m, 0.0)))
            for i, x in enumerate(lines_ft)}
    beams = {f"B{i}": SimpleNamespace(start_node=f"N{i}", end_node=f"N{i}")
             for i in range(len(lines_ft))}
    lo, hi = lines_ft[0] - 0.75, lines_ft[-1] + 0.75
    joist = SimpleNamespace(category="joist", p0=(lo * m, 0.0), p1=(hi * m, 0.0))
    deck = SimpleNamespace(tag="FS", joists=SimpleNamespace(
        direction="x", bearing_refs=tuple(beams), cantilever=inch(9),
        cantilever_start=None, cantilever_end=None))
    ctx = SimpleNamespace(
        model=SimpleNamespace(floors=[SimpleNamespace(tag="FS", members=[joist])]),
        plan=SimpleNamespace(by_tag=lambda t: node.get(t) or beams.get(t)))
    beam = beams[f"B{lines_ft.index(beam_ft)}"]
    assert _beam_tributary_ft(ctx, deck, beam) == pytest.approx(expected, abs=1e-6)


def test_no_deck_beam_is_an_engineering_item_any_more(results) -> None:
    """The kind is deregistered. A published table read is not something a seal adds to."""
    assert not [key for key in results if key.startswith("deck_beam/")]
    from typehaus.engineering import registered_kinds

    assert "deck_beam" not in registered_kinds()


def test_the_balcony_beams_are_graded_by_the_engineered_record(
        catlin_ctx) -> None:
    """ONE finding per beam, and it is the ENGINEERED one.

    ** THIS TEST ASSERTED SIX FINDINGS AND THE WRONG ONE AS THE VERDICT. ** It read: the
    published row is the verdict a reviewer can confirm, and the NDS line beside it is an
    advisory saying how much of the row's margin weather spends. But the guide's values are
    DRY-USE — the row's own authored ``condition`` said so — and these beams stand in
    weather, so the verdict was coming from a row that does not describe the member while
    the only arithmetic modelling the real service condition carried no weight.

    Since 2026-09-18 ``PublishedSpan.service_condition`` refuses the row and
    ``engineering/glulam_beam`` is a registered kind again, carrying the verdict with a
    record, a fingerprint and an oracle. The refusal is said out loud INSIDE that finding
    rather than emitted as a second, UNKNOWN one: an UNKNOWN beside a PASS about one member
    would claim nobody knows, which is false the moment the record exists, and it would
    block the permit gate on a question the engine has answered.
    """
    from typehaus.checks.structural.deck import deck_beam_span
    from typehaus.findings import Authority, Result

    findings = [f for f in deck_beam_span(catlin_ctx)
                if any(tag in _BALCONY_SPANS for tag in f.element_tags)]
    assert len(findings) == 2, [f.message for f in findings]
    assert all(f.result is Result.PASS for f in findings), [f.message for f in findings]
    assert all(f.authority is Authority.ENGINEERED for f in findings)
    assert {f.engineering_item for f in findings} == {
        f"glulam_beam/{tag}" for tag in _BALCONY_SPANS}

    for finding in findings:
        # Since 2026-09-22 no supplier row is authored at all (the deck guide's row was read
        # at a 10' joist span and is DRY-use; neither describes these beams now). The finding
        # still says why no table carries the verdict — silence would read as never looking.
        assert "no supplier row is authored for it either" in finding.message
        assert "bearing, compression perpendicular" in finding.message


def test_the_glulam_record_carries_its_wet_service_factors_in_the_fingerprint(
        catlin_ctx) -> None:
    """Every reference value and every adjustment is an input, so a seal covers the design.

    The lesson ``retaining_wall`` learned the hard way on the same day — f'c and the bars
    drove four capacities and were absent from its ``inputs`` — applied at registration
    rather than after the fact. Re-grade this beam dry, at a different layup, or at snow's
    C_D and the record is about a different member; the digest has to move with it.
    """
    from typehaus.engineering.glulam_beam import WET_FB, WET_FV

    record = catlin_ctx.engineering["glulam_beam/BM-SG-BLW"]
    names = {q.name: q.value for q in record.inputs}
    assert names["C_M_bending"] == pytest.approx(WET_FB)
    assert names["C_M_shear"] == pytest.approx(WET_FV)
    assert {"Fb", "Fv", "Fc_perp", "E", "C_D", "C_V", "bearing_length"} <= set(names)
    assert record.oracle and record.oracle[0].note == "balcony_moment_columns.md"


# --- the north entry canopy: a ROOF-carrying moment column ------------------------------
#
# `notes/north_entry_piers.md` §8 is the hand pass these reproduce. Until 2026-09-11 both
# columns published `SCREENING: axial only, no moment and no lateral case.` while
# `notes/north_entry_structure.md` §1a called them the canopy's east lateral system in
# print — a false claim the tests did not catch because nothing asked.
_CANOPY_COLUMNS = ("PT-BW-RE", "PT-BW-RNE")
#: ** THE SECOND ORACLE FOR THESE TWO IS NOW `entry_column_base_fixity.md` §7, AND IT MOVED
#: EVERY NUMBER ON THIS PAGE. ** `north_entry_piers.md` §8 still derives the wind and the
#: bands; what changed on 2026-09-19 is who carries the result. The canopy's deck is a
#: declared diaphragm and `W-BW-SCREEN` a declared shear panel, so the shear is distributed
#: in proportion to rigidity (IBC 2018 §1604.4) instead of being loaded wholly onto the two
#: cast columns, and each column's own drag is a PROPPED-cantilever load rather than a
#: free-cantilever one now that the deck holds its head.
#:
#: Three consequences, and the first is the one a reader will not expect: **E-W governs
#: both columns now**. The panel runs north-south, so it takes 62% of the N-S case and none
#: of the E-W one, and the case with the smaller total is the case the columns keep.
# ** ONE ROW, TWICE, AND THAT IS §6a's WHOLE RESULT. ** Both canopy bases went onto one plane
# at -10'-2" on 2026-09-20, so the two columns have the same shaft, the same 3EI/h³ and the
# same 50% of the E-W case. Until then they read 15.349'/0.3632/523.4/4,940 and
# 12.729'/0.6368/444.6/6,866 — the SHORT column stiff and taking the larger share of exactly
# the case the panel does not resist, which is why deepening it alone could not close it.
_CANOPY_ORACLE = {
    # §7b/§7e: 0.500 x 821.3 x 16.563' + 552.6 lb-ft of propped drag.
    "PT-BW-RE": {"height_ft": 16.563, "drag_arm_ft": 11.170, "share": 0.500,
                 "drag_moment_lb_ft": 552.6, "wind_asd_lb_ft": 7_354.0},
    "PT-BW-RNE": {"height_ft": 16.563, "drag_arm_ft": 11.170, "share": 0.500,
                  "drag_moment_lb_ft": 552.6, "wind_asd_lb_ft": 7_354.0},
}
#: §7a: 0.6 x 18.335 psf x 0.85 x 1.80, the ASD pressure every band below is multiplied by.
_CANOPY_ASD_PRESSURE_PSF = 16.831
#: §7a: the E-W case, which is the one the columns keep — the slope rise (6.000' x 4.444' =
#: 26.67 ft2) plus both headers' section depths seen end-on (5.36 ft2 each).
_CANOPY_TOP_SHEAR_LB = 629.3
#: §7a: the N-S case, the gable-end triangle 26.667' x 4.444'/2 = 59.26 ft2. Shared.
_CANOPY_TOP_SHEAR_NS_LB = 997.4
#: Two 12" shafts, each 10.78' of exposed length (eave +7.951' down to Site.grade -2.833').
_CANOPY_DRAG_SHEAR_LB = 363.0
#: §7b: the two propped-cantilever head reactions, which join the deck and are distributed
#: with everything else. 821.3 = 629.3 + 192.0 on the E-W case.
_CANOPY_DIAPHRAGM_SHEAR_LB = 821.3


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
    """`entry_column_base_fixity.md` §7e term by term: this column's SHARE of the deck's
    shear on the full shaft, plus the propped-cantilever moment from its own drag."""
    want = _CANOPY_ORACLE[tag]
    pier = piers[tag]
    assert pier.height_in / 12.0 == pytest.approx(want["height_ft"], abs=0.01)
    hand = (want["share"] * _CANOPY_DIAPHRAGM_SHEAR_LB * want["height_ft"]
            + want["drag_moment_lb_ft"])
    assert hand == pytest.approx(want["wind_asd_lb_ft"], rel=0.005)
    assert pier.wind_base_moment_lb_ft == pytest.approx(want["wind_asd_lb_ft"], rel=0.005)


@pytest.mark.parametrize("tag", _CANOPY_COLUMNS)
def test_the_propped_shaft_is_not_a_cantilever(tag, piers) -> None:
    """§7b, and it is the half of the revision a reader is most likely to miss.

    Wind on the shaft reaches the base alone only while the head is free. With the deck
    declared a diaphragm the shaft is a propped cantilever, and the same load makes three to
    four times less moment at the base — the balance goes UP into the deck, where it is
    distributed with everything else rather than vanishing.
    """
    want = _CANOPY_ORACLE[tag]
    free_cantilever = (_CANOPY_DRAG_SHEAR_LB / 2.0) * want["drag_arm_ft"]
    # P a (H^2 - a^2) / (2 H^2) against P a. Both columns land near a third, and the exact
    # value is a pure function of a/H, so a band this tight is a real assertion about the
    # influence coefficient rather than a tolerance.
    assert 0.25 < want["drag_moment_lb_ft"] / free_cantilever < 0.40
    assert "PROPPED cantilever" in piers[tag].moment_basis


def test_the_shear_is_shared_with_the_west_panel_and_the_split_is_stated(piers) -> None:
    """The frame's shear is distributed by rigidity, IBC 2018 §1604.4.

    ** THIS TEST ASSERTED THE OPPOSITE UNTIL 2026-09-19, AND BOTH VERSIONS ARE RIGHT ABOUT
    THEIR OWN MODEL. ** While no `Roof.diaphragm` and no `Wall.shear_panel` were authored,
    the whole shear DID go east: there was no horizontal member to share it through and no
    declared line to share it with, and taking it all on the columns was the honest answer
    rather than a conservatism. Authoring both is what changed the structure.

    What the basis has to keep saying is which case is which — the panel runs north-south,
    so the E-W case is still the columns' alone, and it is now the one that governs them.

    ** AND IT GOVERNS AGAINST THE EQUILIBRIUM-CONSISTENT N-S CASE, NOT THE k/Σk ONE. ** The
    rigidity split gave each column 142.3 lb N-S (2,908 lb-ft), which left M_t = V e
    unbalanced. With torsion (canopy_lateral §8g/§8h) each takes 342.5 lb, 6,225 lb-ft — still
    under E-W's 7,354, so E-W governs by 15%, not by 2.5x.
    """
    from typehaus.engineering.roof_moment import frame_cases_of

    north_south = next(c for c in frame_cases_of("RF-BW-CANOPY") if c.axis == "y")
    for tag in _CANOPY_COLUMNS:
        basis = piers[tag].moment_basis
        assert "shared by relative rigidity (IBC 2018 §1604.4)" in basis
        assert "E-W wind on RF-BW-CANOPY" in basis, "the unshared case governs"
        assert "W-BW-SCREEN" not in basis, "the panel resists N-S and takes no E-W share"
        want = _CANOPY_ORACLE[tag]
        force = north_south.column_forces_lb[tag]
        assert force == pytest.approx(342.5, rel=0.005)
        ns_moment = force * want["height_ft"] + want["drag_moment_lb_ft"]
        assert ns_moment == pytest.approx(6_225.0, rel=0.005)
        assert piers[tag].wind_base_moment_lb_ft > 1.1 * ns_moment
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
    # ** THE FLOOR CAME DOWN 0.40 -> 0.30 ON 2026-09-19 AND THE CEILING DID NOT MOVE. **
    # The shear split (entry_column_base_fixity.md §7) roughly halved PT-BW-RE's base moment
    # and its sway ratio fell to 0.37, while PT-BW-RNE — which takes the larger share of the
    # one case the panel does not resist — stayed high. The demand is still a deliberate
    # over-read (§8's 2.1x against the §27.3.2 hand pass); if this ever reaches 1.0 the
    # note's wood alternate is back on the table.
    assert 0.3 < magnified.demand / magnified.capacity < 0.85
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


# --- the wall line load, and the branch it emptied -----------------------------------------


def test_a_wall_on_a_beam_is_a_line_load_and_reaches_the_piers_under_it(catlin_plan) -> None:
    """``BM-BW-SCSILL``, which carried a wall and no plan area — `north_entry_piers.md` §2.

    ** THE NUMBER IS PINNED IN THREE PIECES, NOT ONE. ** The plf, the run and the split each
    fail differently: a plf that lost `SC-BW-WEST` understates by 30% and still looks
    plausible; a run measured off the WALL rather than off the beam's own footprint would be
    6.57' instead of 4.52'; and a split that stopped at the 6x6 KDAT columns would leave the
    piers that actually carry the load with nothing, which is the failure this whole
    mechanism exists to correct.
    """
    from typehaus.engineering.pier_basis import cast_piers, wall_line_loads
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve
    from typehaus.resolve.assembly_weight import wall_line_plf

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")

    screen = next(w for w in model.walls if w.tag == "W-BW-SCREEN")
    plf, basis = wall_line_plf(ctx, screen)
    assert plf == pytest.approx(43.48, abs=0.05), basis
    assert "SC-BW-WEST" in basis, "the slat clerestory is a third of this line"

    # The DIRECT delivery is to the two 6x6 KDAT canopy columns the sill hangs off, and the
    # only beam this accounts for is the sill. A second beam appearing here means some other
    # wall started being read as a line load, which is a real change and not a tolerance.
    raw, accounted = wall_line_loads(ctx)
    assert accounted == {"BM-BW-SCSILL"}
    assert set(raw) == {"PT-BW-CW", "PT-BW-CNW"}
    assert all(v == pytest.approx(98.3, abs=0.1) for v in raw.values())

    # And it lands on the CAST piers, through `supported_by`. Those two are the pair that
    # reported UNKNOWN until 2026-09-20; no other pier in the house moves.
    piers = {p.tag: p for p in cast_piers(ctx)}
    carrying = {tag: p.wall_dead_lb for tag, p in piers.items() if p.wall_dead_lb}
    assert set(carrying) == {"PT-BW-W", "PT-BW-GW"}
    assert all(v == pytest.approx(98.3, abs=0.1) for v in carrying.values())
    assert not piers["PT-BW-W"].unmodelled_load, "the gap this closes"
    assert not piers["PT-BW-GW"].unmodelled_load
    # The basis travels with the pounds, through the wood column that keeps none of them.
    assert "delivered through PT-BW-CW" in piers["PT-BW-W"].wall_load_basis


def test_a_wall_that_states_no_weight_accounts_nothing(catlin_plan, monkeypatch) -> None:
    """Publishing an understated demand is worse than publishing none — ``_unmodelled_beams``'
    whole doctrine, and the line load is held to it.

    A layer whose material names neither a density nor an areal density makes the plf
    ``None``, and the beam must then stay UNACCOUNTED: the pier goes back to INCOMPLETE
    naming it, rather than quietly carrying a wall short one layer.
    """
    from typehaus.engineering import pier_basis
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    monkeypatch.setattr(pier_basis, "wall_line_loads", lambda _c: ({}, set()))
    piers = {p.tag: p for p in pier_basis.cast_piers(ctx)}
    assert piers["PT-BW-W"].wall_dead_lb == 0.0
    assert piers["PT-BW-W"].unmodelled_load == ("BM-BW-SCSILL",)


def test_a_pier_whose_demand_is_short_publishes_no_ratio() -> None:
    """``deck_post._detailing_only``, which NO catlin pier reaches any more.

    It is the branch that grades a cage in full against a demand known to be short: six
    load-independent detailing states published, the §22.4.2 axial comparison **omitted
    rather than estimated**, and the beam it could not price named in `missing`. A d/c
    appearing there is the regression this guards, and it is worth as much now as it was
    when the breezeway piers exercised it — more, because nothing in the reference house
    walks through it any longer and an untested branch is one that rots.

    Synthetic for exactly that reason. It also pins the note that USED to be a hard-coded
    sentence about a retired 4'-0" x 4'-0" multiwall shelter, printed on every record this
    branch produced whatever beams it was actually handed.
    """
    from typehaus.engineering.deck_post import _one
    from typehaus.engineering.item import Status
    from typehaus.engineering.pier_basis import _Pier

    pier = _Pier(
        tag="PT-X", diameter_in=12.0, round_section=True, height_in=60.0,
        tributary_ft2=8.0, carried_dead_lb=0.0, footing_tag=None,
        shared_wall_footing=False, lateral_system=False,
        wind_base_moment_lb_ft=0.0, guard_base_moment_lb_ft=0.0, moment_basis="",
        footing_width_in=24.0, footing_depth_in=12.0,
        base_thickness_in=12.0, base_kind="pad",
        vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
        unmodelled_load=("BM-X", "BM-Y"),
    )
    record = _one(pier)
    assert record.status is Status.INCOMPLETE
    assert len(record.limit_states) == 6
    assert not [s for s in record.limit_states if s.name.startswith("axial")]
    assert record.missing and "BM-X, BM-Y" in record.missing[0]
    assert "no tributary AREA for that load" in record.missing[0]
    # The generalised note names the members it was handed, and says nothing about a shelter.
    unmodelled = next(n for n in record.notes if n.startswith("UNMODELLED:"))
    assert "BM-X, BM-Y" in unmodelled
    assert "multiwall" not in unmodelled and "shelter" not in unmodelled
