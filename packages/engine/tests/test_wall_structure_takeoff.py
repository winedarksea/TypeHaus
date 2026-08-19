"""The `wall_structure` section: monolithic wall cores by the square foot and the yard.

A wall whose STRUCTURE layer is a pour or a masonry course frames no members and is not a
``ResolvedSolid``, so before this section existed it reached no BOM row at all. These tests
pin both the numbers and — more importantly — that the two wall-structure sections
*partition* the walls, so the same class of hole cannot open again silently.
"""

from __future__ import annotations

from typehaus.takeoff.wall_structure import wall_structure_takeoff


def test_monolithic_walls_reach_the_bom(catlin_model) -> None:
    rows = wall_structure_takeoff(catlin_model)
    assert rows, "catlin's basement, garage and garden walls are all monolithic"
    # 39 since 2026-08-18: the sunken garden's 16" arched cross-wall and the three
    # W-SG-RAIL-* masonry parapets over it went, and with them the last `cmu` in the house.
    assert sum(int(row["count"]) for row in rows) == 39
    assert {row["material"] for row in rows} == {
        "concrete", "retaining-block", "glazed-green-brick"}
    # Bigger than the entire priced concrete order (footings + slab) the estimate used to
    # know about, which is the measure of what was missing.
    assert sum(float(row["volume_cubic_yards"]) for row in rows) > 100
    assert all(float(row["net_area_sqft"]) > 0 for row in rows)


def test_every_wall_bills_its_structure_exactly_once(catlin_model) -> None:
    """The regression gate. Asserted against *members*, not against the predicate the
    takeoff selects on, so it cannot be satisfied circularly: a wall either frames studs
    (billed in `framing`) or it appears here, never both and never neither."""
    monolithic = {tag for row in wall_structure_takeoff(catlin_model) for tag in row["tags"]}
    framed = {wall.tag for wall in catlin_model.walls
              if any(member.category == "stud" for member in wall.members)}
    all_walls = {wall.tag for wall in catlin_model.walls}

    assert monolithic & framed == set(), (
        f"double-billed: {sorted(monolithic & framed)}")
    assert monolithic | framed == all_walls, (
        f"billed nowhere: {sorted(all_walls - monolithic - framed)}")


def test_the_sunken_garden_brick_wythe_is_billed(catlin_model) -> None:
    """W-B-BRICK — the glazed-brick veneer over the exposed basement wall at the sunken
    garden, added in 76c1871 — is the wall whose absence from the BOM surfaced this hole."""
    rows = [row for row in wall_structure_takeoff(catlin_model)
            if "W-B-BRICK" in row["tags"]]
    assert len(rows) == 1, "the brick wythe is one row of its own"
    row = rows[0]
    assert row["material"] == "glazed-green-brick"
    assert row["assembly"] == "BASEMENT_BRICK_VENEER"
    assert row["tags"] == ["W-B-BRICK"]
    assert 118 < float(row["net_area_sqft"]) < 126
    assert float(row["volume_cuft"]) > 0


def test_the_garden_walls_are_distinguishable_from_house_concrete(catlin_model) -> None:
    """Grouped by assembly, so garden work never merges into the foundation pour — they
    are both `concrete` and they are not the same order or the same price."""
    by_assembly = {row["assembly"]: row for row in wall_structure_takeoff(catlin_model)}
    for assembly in ("SUNKEN_GARDEN_WALL", "RETAINING_BLOCK_12",
                     "BASEMENT_BRICK_VENEER", "CATLIN_BASEMENT_12"):
        assert assembly in by_assembly, f"{assembly} lost its own row"
    house = by_assembly["CATLIN_BASEMENT_12"]
    garden = by_assembly["SUNKEN_GARDEN_WALL"]
    assert set(house["tags"]).isdisjoint(garden["tags"])


def test_openings_are_deducted_from_area_and_volume(catlin_model) -> None:
    """A doored wall does not order concrete for the doorway."""
    from typehaus.resolve.geometry import length, sub

    monolithic = {tag: row for row in wall_structure_takeoff(catlin_model)
                  for tag in row["tags"]}
    walls = {wall.tag: wall for wall in catlin_model.walls}
    holed = [opening.host_wall for opening in catlin_model.openings
             if opening.host_wall in monolithic]
    assert holed, "catlin has openings in monolithic walls"

    tag = holed[0]
    wall = walls[tag]
    row = monolithic[tag]
    gross_m2 = length(sub(wall.axis[1], wall.axis[0])) * (
        ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0 - wall.z0_m)
    holes_m2 = sum(opening.width_m * opening.height_m for opening in catlin_model.openings
                   if opening.host_wall == tag)
    assert holes_m2 > 0
    # The row may aggregate several walls, so compare against its own group, not the wall.
    group_gross = 0.0
    for other in row["tags"]:
        sibling = walls[other]
        group_gross += length(sub(sibling.axis[1], sibling.axis[0])) * (
            ((sibling.top_z0_m or sibling.z1_m) + (sibling.top_z1_m or sibling.z1_m)) / 2.0
            - sibling.z0_m)
    assert float(row["net_area_sqft"]) < group_gross * 10.7639104, (
        "openings must come out of the billed area")
    assert gross_m2 > 0 and float(row["volume_cuft"]) > 0


def test_icf_and_masonry_walls_are_both_caught(catlin_model) -> None:
    """The three-armed predicate, pinned. GARAGE_ICF_6 is concrete *with* a `masonry=`
    spec and CATLIN_BASEMENT_12 is concrete *without* one, so neither "is masonry" nor
    "is not masonry" alone selects the right set — only "no masonry AND has framing"
    frames, and everything else bills here."""
    assemblies = {row["assembly"] for row in wall_structure_takeoff(catlin_model)}
    assert {"GARAGE_ICF_6", "CATLIN_BASEMENT_12"} <= assemblies
