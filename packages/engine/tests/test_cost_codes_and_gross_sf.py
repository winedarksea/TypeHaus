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
