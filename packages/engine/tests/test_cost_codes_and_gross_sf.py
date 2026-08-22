"""Cost codes, and the $/sf denominator.

Two small things an export cannot do without. Neither existed: ``grep`` for nahb /
masterformat / uniformat / cost_code returned nothing anywhere in the repo, and no gross
area metric existed either — so a $/sf figure had no honest denominator at all.
"""

from __future__ import annotations

import pytest

from typehaus.cli.prices import ESTIMATE_PLANS
from typehaus.emit.trades import TRADES
from typehaus.server.space_summary import build_space_summary, gross_area_sf
from typehaus.takeoff.cost_codes import KEY_PATTERNS, SECTION_CODES, cost_code

# Spaces that must never be billed as conditioned floor area
# (memory: catlin-house-conditioned-sqft).
_NEVER_CONDITIONED = ("garage", "sunken garden", "porch", "balcony", "breezeway")


def test_every_estimate_section_has_a_default_code() -> None:
    assert {name for name, *_ in ESTIMATE_PLANS} == set(SECTION_CODES)


def test_every_code_names_a_trade_the_viewer_actually_has() -> None:
    """The trade column reuses ``emit/trades.TRADES`` rather than inventing a parallel
    vocabulary — that set is already shared with ui/src/state/vocabulary.ts and pinned by
    test_solid_trade_parity.py, and a second one would drift from it within a release."""
    named = {code.trade for code in SECTION_CODES.values()}
    named |= {code.trade for _, _, code in KEY_PATTERNS}
    assert named <= TRADES


def test_a_key_pattern_beats_the_section_default() -> None:
    assert cost_code("concrete", "slab_on_grade").nahb == "1300"
    assert cost_code("concrete", "footing_wall").nahb == "1200"
    assert cost_code("concrete", "anything_else").nahb == SECTION_CODES["concrete"].nahb


def test_a_house_override_beats_both_but_only_for_nahb() -> None:
    """Decision #28: the house owns its own numbers, and custom cost codes are the
    residential norm. MasterFormat is not the builder's to rename, so csi and trade stay."""
    code = cost_code("framing", "2x6", {"framing": "06-100"})
    assert code.nahb == "06-100"
    assert code.csi == SECTION_CODES["framing"].csi
    assert code.trade == "framing"


def test_a_per_key_override_beats_a_section_override() -> None:
    overrides = {"framing": "06-100", "framing:2x6": "06-110"}
    assert cost_code("framing", "2x6", overrides).nahb == "06-110"
    assert cost_code("framing", "2x4", overrides).nahb == "06-100"


def test_an_unknown_section_raises_rather_than_inventing_a_code() -> None:
    with pytest.raises(KeyError, match="no cost code"):
        cost_code("not_a_section", "x")


# --- the $/sf denominator -----------------------------------------------------------------

def test_gross_area_is_reported_per_storey_and_overall(catlin_model) -> None:
    gross = gross_area_sf(catlin_model)
    assert gross["overall"] == pytest.approx(sum(gross["storeys"].values()), abs=0.2)
    assert gross["overall"] > 0


def test_gross_exceeds_conditioned_because_it_includes_the_walls(catlin_model) -> None:
    """Rooms stop at the finish face, so a room-sum understates the building by its whole
    envelope thickness — about 6% on a 36x36 house with 12" foundation walls. That is the
    difference between the two figures and the reason both are reported."""
    summary = build_space_summary(catlin_model)["overall"]
    assert summary["gross_sf"] > summary["conditioned_sf"]
    assert summary["gross_sf"] < summary["conditioned_sf"] * 1.6


def test_the_conditioned_denominator_excludes_every_unconditioned_space(catlin_model) -> None:
    """The pin memory `catlin-house-conditioned-sqft` asks for: the garage is the plan's
    only ``conditioned=False`` Room, and the sunken garden, porch, balcony and breezeway
    contribute nothing *because they are not Rooms at all*. That is a property of the plan,
    not of a filter, so it can move without anyone noticing — hence this test."""
    conditioned = [room for room in catlin_model.rooms if room.conditioned]
    for room in conditioned:
        label = f"{room.tag} {room.occupancy}".lower()
        assert not any(word.split()[0] in label for word in _NEVER_CONDITIONED), room.tag
    summary = build_space_summary(catlin_model)["overall"]
    expected = sum(room.area_m2 for room in conditioned) * 10.7639
    assert summary["conditioned_sf"] == pytest.approx(expected, abs=0.5)


def test_the_garage_is_counted_in_gross_but_not_in_conditioned(catlin_model) -> None:
    """A builder does price garage square footage — separately, and at a different rate —
    so it belongs in gross and never in conditioned."""
    summary = build_space_summary(catlin_model)
    garage = next(row for row in summary["storeys"] if row["storey"] == "garage")
    assert garage["conditioned_sf"] == 0.0
    assert garage["unconditioned_sf"] > 0.0
    assert garage["gross_sf"] > garage["unconditioned_sf"]


def test_an_enclosure_with_no_room_in_it_is_not_floor_area(catlin_model) -> None:
    """The sunken garden's retaining walls stand on the basement storey and enclose no
    Room. Counting them would have added ~1,170 sf of "floor area" nobody builds or buys —
    which the first draft of this metric did."""
    gross = gross_area_sf(catlin_model)["storeys"]
    assert gross["basement"] == pytest.approx(gross["main"], rel=0.05)


# --- the section name is not the trade ---------------------------------------------------
#
# ``[concrete]`` in a prices.toml prices the whole ``structural_solids`` scope, not "the
# concrete". Until ``cost_codes._solid_code`` existed, every row in it inherited
# ``SECTION_CODES["concrete"]``, so four solid elm timbers, six painted 6x6 pillars, the
# breezeway's multiwall polycarbonate, 4.35 cy of #57 washed stone and two framed-and-taped
# duct soffits all exported under NAHB 1300 / CSI 03 30 00 CAST-IN-PLACE CONCRETE — and
# ``haus tasks`` scheduled them into the concrete sub's work package.


@pytest.mark.parametrize("key,trade", [
    ("column:ELM_TIMBER", "framing"),
    ("column:POST_WHITE_PAINT", "framing"),
    ("glazing:BREEZEWAY_GLAZED_WALL", "openings"),
    ("glazing:BREEZEWAY_ROOF_GLAZING", "openings"),
    ("bug_screen:CATLIN_EXT_2X6", "openings"),
    ("drywell", "drainage"),
    ("drain_tile", "drainage"),
    ("sump", "drainage"),
    ("soffit", "floors"),
    ("beam", "framing"),
])
def test_a_solid_that_is_not_a_pour_is_not_filed_as_concrete(key, trade) -> None:
    code = cost_code("concrete", key)
    assert code.trade == trade
    assert code.csi != "03 30 00"


@pytest.mark.parametrize("key", ["footing", "slab", "pad", "slab:CATLIN_DECK_EPS_INT",
                                 "thermal_break"])
def test_an_actual_pour_still_files_as_concrete(key) -> None:
    assert cost_code("concrete", key).trade == "concrete"


def test_a_laid_deck_in_a_slab_row_needs_its_material_to_say_so() -> None:
    """The one thing a solid's CATEGORY cannot say. "slab" covers 9" of cast concrete and a
    composite plank on 2x8 joists alike, so this is the only case the trade table cannot
    settle on its own — and silence is not evidence, so a row with no assembly stays a
    pour."""
    assert cost_code("concrete", "slab:PORCH_DECK_COMPOSITE",
                     material="composite-deck").trade == "floors"
    assert cost_code("concrete", "slab:BALCONY_DECK_ALUMINUM",
                     material="aluminum-deck").trade == "floors"
    assert cost_code("concrete", "slab:CATLIN_DECK_EPS_INT",
                     material="concrete").trade == "concrete"
    assert cost_code("concrete", "slab", material=None).trade == "concrete"


def test_the_footing_account_survives_the_derivation() -> None:
    """``KEY_PATTERNS`` runs first and carries refinements the category cannot know: a
    footing is NAHB 1200 against flatwork's 1300, two accounts and often two subs."""
    assert cost_code("concrete", "footing").nahb == "1200"
    assert cost_code("concrete", "slab").nahb == "1300"


def test_every_trade_a_solid_category_can_name_has_an_account() -> None:
    """The derivation is keyed on the trade table, so a solid category added there must not
    fall back to the concrete default just because nobody added an account for its trade."""
    from typehaus.emit.trades import SOLID_CATEGORY_TRADE
    from typehaus.takeoff.cost_codes import _SOLID_TRADE_CODES

    assert set(SOLID_CATEGORY_TRADE.values()) <= set(_SOLID_TRADE_CODES)


def test_no_catlin_solid_reaches_the_concrete_sub_unless_it_is_concrete(catlin_model) -> None:
    """End to end, against the real house: every priced solid filed under the concrete trade
    is either a pour or a row that never said what it was made of."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.bom import bill_of_materials

    prices = load_prices(catlin_model.plan.source_root)
    bom = bill_of_materials(catlin_model)
    material_of = {(row["category"], row.get("assembly")): row.get("structure_material")
                   for row in bom["structural_solids"]}
    concrete_keys = {row["key"] for row in
                     estimate_costs(bom, prices)["sections"]["concrete"]["rows"]
                     if row["trade"] == "concrete"}
    for key in concrete_keys:
        category, _, assembly = key.partition(":")
        material = material_of.get((category, assembly or None))
        assert material in (None, "concrete"), f"{key} bills as concrete but is {material}"
