"""Wall base, door, screen-end and small-opening trim: the inventory the note works by hand."""

from collections import Counter

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.takeoff.cladding_trim import cladding_trim_takeoff


def _pieces(model):
    return [s for s in model.solids if s.category == "cladding_trim"]


def test_trim_inventory_by_profile(catlin_model_ro):
    counts = Counter(s.product for s in _pieces(catlin_model_ro))
    assert counts == {
        "WINDOW_JAMB_CUSTOM": 86, "WINDOW_SILL_CUSTOM": 43, "OPENING_HEAD": 43,
        "PBR_BASE": 11, "BBD_BASE": 10, "CORRUGATED_BASE": 12, "BBD_TRANSITION": 10,
        "BBD_PANEL_STARTER": 6, "CORRUGATED_JAMB": 8, "DOOR_HEAD_CUSTOM": 5,
        "WIDE_OUTSIDE_CORNER": 8, "CORRUGATED_OUTSIDE_CORNER": 4,
    }


def test_base_run_splits_at_stock_with_a_lap():
    # W-M-W4: a 164.8 in run takes one 122 in stick and a second to cover the 2 in lap.
    assert len(split_stock_run(164.8, (122.0,), 2.0)) == 2


def test_screen_ends_close_both_edges_of_the_screen_and_its_skirt(catlin_model_ro):
    ends = {s.tag: s for s in _pieces(catlin_model_ro) if "-END-" in s.tag}
    assert sorted(ends) == [
        "TRIM-W-BW-SCREEN-END-HI-1", "TRIM-W-BW-SCREEN-END-LO-1",
        "TRIM-W-BW-SCREEN-SKIRT-END-HI-1", "TRIM-W-BW-SCREEN-SKIRT-END-LO-1"]
    assert ends["TRIM-W-BW-SCREEN-END-HI-1"].trim_length_m / M_PER_IN == pytest.approx(48.9, 0.01)


def test_catalog_door_takes_jambs_but_its_head_is_the_band(catlin_model_ro):
    pieces = _pieces(catlin_model_ro)
    deck = [s for s in pieces if s.host_ref == "D-S-DECK-E"]
    assert sorted(s.product for s in deck) == ["BBD_PANEL_STARTER", "BBD_PANEL_STARTER"]
    assert all("-TRIM-HEAD-" not in s.tag for s in deck)
    bands = [s for s in pieces if s.product == "BBD_TRANSITION"]
    assert any(s.z0_m / M_PER_IN < 208 < s.z1_m / M_PER_IN for s in bands)


def test_penetrations_under_six_inches_take_no_trim(catlin_model_ro):
    hosts = {s.host_ref for s in _pieces(catlin_model_ro)}
    assert {"AO-M-FIRE-NICHE", "AO-M-ERV-OA", "AO-S-ERV-EA"} <= hosts
    assert not hosts & {"AO-M-PORCH-HYD", "AO-S-BALC-HYD"}


def test_roof_edges_bill_as_image_ii_pieces(catlin_model_ro):
    rows = {r["part"]: r for r in cladding_trim_takeoff(catlin_model_ro) if r["kind"] == "roof"}
    assert rows["52124XX"]["count"] == 16        # extended eave, three roofs' eaves
    assert rows["52131XX"]["count"] == 5         # closed ridge cover: house and canopy
    assert rows["IMAGE_II_RAKE_4IN_CUSTOM"]["unit"] == "LF"   # house rakes: 4 in face
    assert "52126XX" in rows                     # garage and canopy rakes fit the stock leg
