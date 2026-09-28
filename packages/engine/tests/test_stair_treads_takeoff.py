"""Finish walking surfaces bill by the piece, and a winder by the blank it is cut from."""

from __future__ import annotations

import pytest

from typehaus.takeoff.sheet_goods import sheet_goods_takeoff
from typehaus.takeoff.stairs import stair_tread_takeoff, winder_blank_in


def test_no_stair_surface_is_a_sheet_good(catlin_model_ro) -> None:
    """The oak flights once ordered "4 sheets 4x8" of tread stock through the framing RFQ."""
    assert not [row for row in sheet_goods_takeoff(catlin_model_ro)
                if str(row["material"]).startswith("oak")]


def test_the_oak_flights_bill_owner_furnished_pieces(catlin_model_ro) -> None:
    rows = stair_tread_takeoff(catlin_model_ro)
    count = {use: sum(r["pieces"] for r in rows if r["use"] == use)
             for use in ("tread", "winder", "landing")}
    assert count == {"tread": 26, "winder": 3, "landing": 2}
    assert {r["stair"] for r in rows} == {"ST-M2S", "ST-S2A"}
    assert all(r["supply"] == "owner-milled" for r in rows)
    # The landing field is the floor oak, 3/4" — its nosing is a millwork detail.
    [landing] = [r for r in rows if r["use"] == "landing"]
    assert (landing["material"], landing["thickness_in"]) == ("oak-floor-custom", 0.75)


def test_a_winder_blank_is_its_outline_with_the_grain_on_the_nosing(catlin_model_ro) -> None:
    """ST-S2A's 36" turn: a 24x30 triangle off the entering edge, a five-sided middle
    winder, and a triangle whose nosing is its 38 3/8" hypotenuse. Each blank is the
    outline's reach back from its nosing plus the 1" that tucks under the next riser."""
    [stair] = [s for s in catlin_model_ro.stairs if s.tag == "ST-S2A"]
    winders = sorted((m for m in stair.members if m.category == "winder"),
                     key=lambda m: m.child_key)
    blanks = [winder_blank_in(m, stair.nosing_depth_m) for m in winders]
    assert blanks == [pytest.approx(b, abs=0.01)
                      for b in [(25.0, 36.0), (17.87, 46.85), (19.74, 38.42)]]
