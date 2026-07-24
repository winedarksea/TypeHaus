"""Framing bill-of-materials takeoff — grouped by size AND type, bucketed by length."""

from __future__ import annotations

from typehaus.takeoff import (
    _board_feet_per_ft,
    _order_length_ft,
    framing_bom_by_size,
    framing_takeoff,
)


def test_order_length_rounds_up_to_stock() -> None:
    assert _order_length_ft(7.5) == 8
    assert _order_length_ft(8.0) == 8
    assert _order_length_ft(8.1) == 10
    assert _order_length_ft(15.9) == 16
    assert _order_length_ft(19.5) == 20
    # Past the longest stock length, round up to the next even foot.
    assert _order_length_ft(21.0) == 22
    assert _order_length_ft(36.0) == 36


def test_board_feet_parses_dimensional_and_builtup_profiles() -> None:
    assert _board_feet_per_ft("2x6") == 1.0            # 2*6/12
    assert _board_feet_per_ft("2-2x8") == 8.0 / 3.0    # 2 plies * 2*8/12
    assert _board_feet_per_ft("11.875 I-joist") is None  # engineered, not dimensional


def test_framing_takeoff_reconciles_and_groups(catlin_model) -> None:
    members = catlin_model.all_members()
    assert members  # the catlin model frames thousands of members

    rows = framing_takeoff(catlin_model)
    # Every (profile, category) pair is present exactly once and total pieces reconcile 1:1.
    keys = [(row["profile"], row["category"]) for row in rows]
    assert len(keys) == len(set(keys))
    assert sum(int(row["pieces"]) for row in rows) == len(members)

    for row in rows:
        # The per-stock buckets account for every piece in the group.
        assert sum(bucket["count"] for bucket in row["stock"]) == row["pieces"]
        assert row["order_length_ft"] >= row["cut_length_ft"]  # ordered >= cut

    # A known dimensional profile carries a board-foot rollup; every stud is a real size.
    studs = [row for row in rows if row["category"] == "stud"]
    assert studs and all(row["board_feet"] for row in studs)


def test_framing_by_size_rolls_up_types(catlin_model) -> None:
    rows = framing_takeoff(catlin_model)
    by_size = framing_bom_by_size(catlin_model)

    # One row per distinct profile, and the piece totals match the detailed takeoff.
    assert {row["profile"] for row in by_size} == {row["profile"] for row in rows}
    assert sum(int(row["pieces"]) for row in by_size) == sum(
        int(row["pieces"]) for row in rows
    )
    # 2x4 is used by several member types in the catlin frame.
    two_by_four = next(row for row in by_size if row["profile"] == "2x4")
    assert len(set(two_by_four["types"])) > 1
