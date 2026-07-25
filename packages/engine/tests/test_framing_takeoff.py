"""Framing bill-of-materials takeoff — grouped by size AND type, bucketed by length."""

from __future__ import annotations

from typehaus.takeoff import (
    _board_feet_per_ft,
    _order_length_ft,
    bill_of_materials,
    framing_bom_by_size,
    framing_takeoff,
    structural_solids_takeoff,
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


def test_structural_solids_account_for_every_resolved_solid(catlin_model) -> None:
    """The member cut list cannot see concrete or standalone structure; this row set can."""
    rows = structural_solids_takeoff(catlin_model)
    assert sum(int(row["count"]) for row in rows) == len(catlin_model.solids)
    assert {tag for row in rows for tag in row["tags"]} == {
        solid.tag for solid in catlin_model.solids}
    # Concrete is ordered by the yard, so the volume rollup has to be real.
    footings = next(row for row in rows if row["category"] == "footing")
    assert footings["volume_cubic_yards"] > 0


def test_bill_of_materials_carries_every_section(catlin_model) -> None:
    bom = bill_of_materials(catlin_model)
    assert set(bom) == {"framing", "framing_by_size", "structural_solids",
                        "construction_returns", "sheet_goods", "glazing_panels",
                        "glazing_trim", "hardware", "placeables", "floor_heat",
                        "electrical_devices", "panel_schedule", "service_load",
                        "conduit", "solar", "backup_components"}
    assert all(section for section in bom.values()), "no BOM section may come back empty"
    # The framing section still reconciles 1:1 with the resolved members.
    assert sum(int(row["pieces"]) for row in bom["framing"]) == len(catlin_model.all_members())


def test_placeables_takeoff_reconciles_with_canvas_objects(catlin_model) -> None:
    """The engine twin of the UI BOM's placeablesSection: every free-placed or
    wall-attached product is counted, hosted openings are billed elsewhere, and the
    grouped counts reconcile 1:1 with ``model.canvas_objects``."""
    from typehaus.takeoff.placeables import placeables_takeoff

    rows = placeables_takeoff(catlin_model)
    assert rows, "the catlin house places furniture/appliances/fixtures"
    billable = [item for item in catlin_model.canvas_objects if item.domain != "opening"]
    assert sum(int(row["count"]) for row in rows) == len(billable)
    assert {tag for row in rows for tag in row["tags"]} == {item.tag for item in billable}
    assert all(row["domain"] != "opening" for row in rows)
    # Grouping key is (type, domain, storey) — each appears exactly once.
    keys = [(row["type"], row["domain"], row["storey"]) for row in rows]
    assert len(keys) == len(set(keys))


def test_floor_heat_rides_in_the_bom(catlin_model) -> None:
    """The radiant zones moved out of the CLI patch: bill_of_materials carries them."""
    bom = bill_of_materials(catlin_model)
    rows = {row["tag"]: row for row in bom["floor_heat"]}
    assert set(rows) == {zone.tag for zone in catlin_model.floor_heat}
    sauna = rows["FH-B-SAUNA"]
    zone = next(z for z in catlin_model.floor_heat if z.tag == "FH-B-SAUNA")
    assert sauna["wire_length_ft"] == round(zone.wire_length_m / 0.3048, 1)
    assert sauna["system"] == zone.system and sauna["storey"] == zone.storey
