"""The `wall_structure` section: monolithic wall cores by the square foot and the yard.

A wall whose STRUCTURE layer is a pour or a masonry course frames no members and is not a
``ResolvedSolid``, so before this section existed it reached no BOM row at all. These tests
pin both the numbers and — more importantly — that the two wall-structure sections
*partition* the walls, so the same class of hole cannot open again silently.
"""

from __future__ import annotations

from typehaus.takeoff.wall_structure import wall_structure_takeoff

from _helpers import frames_structure


def test_monolithic_walls_reach_the_bom(catlin_model) -> None:
    rows = wall_structure_takeoff(catlin_model)
    assert rows, "catlin's basement, garage and garden walls are all monolithic"
    # 34 since 2026-08-21: the basement-ceiling overhaul framed W-B-CW, W-B-CW2, W-B-CW3,
    # W-B-CE and W-B-STR2, which were 12" cast concrete only because the old suspended deck
    # spanned between them. They bill studs in `framing` now and no longer appear here — the
    # partition the two sections make is exactly ``frames_as_members``, so a wall leaving one
    # arrives in the other.
    #
    # It was 39 from 2026-08-18, when the sunken garden's 16" arched cross-wall and the three
    # W-SG-RAIL-* masonry parapets over it went, and with them the last `cmu` in the house.
    #
    # Counted as DISTINCT WALLS, not as the sum of the rows' counts. One wall CAN reach
    # several rows — a `Layer.slot` wythe bills a row per material — which is why the count
    # is over the tag set rather than the rows. W-B-BRICK was that wall from the Ishtar
    # scheme (2026-08-20) until 2026-09-04, when its three brick colours became one; the
    # rule stays because the machinery does.
    # 36 from 2026-08-23, when the ESS closet's relocation to the NE corner split W-B-N3
    # at x=6'-0" and W-B-STR at y=31'-0" so its two partitions had nodes to tee into —
    # two more tags, the same pour, the same cubic yards.
    # **34 since 2026-08-24**, and this time the pour really did shrink: those same two
    # segments, W-B-STR and W-B-STR3, are 2x6 bearing stud walls now. They hold back no
    # earth, and what they carry is joists and a wall stack — a stud-wall job on a footing.
    # ~9.8 cy out of this table and into [framing] (plan/storeys/basement.py).
    # **40 from 2026-08-26**, the garage east/south/north brick wainscot: W-G-BRICK-S/N (the
    # two east piers) plus W-G-BRICK-SRET/NRET (their SE/NE corner returns) are four new
    # `GARAGE_BRICK_WAINSCOT` wall tags, and W-GF-S3/W-GF-N2 (the corner returns' own
    # widened `GARAGE_ICF_6_BRICKLEDGE` stem segments, split off W-GF-S2/W-GF-N) are two
    # more — six tags, not eight, because W-GF-E1/E2 already existed (only their assembly
    # changed, from `GARAGE_ICF_6` to the brick-ledge form) and add no new tag.
    # **Still 40 on 2026-08-28, and one wall in it changed identity.** W-B-CS was framed —
    # the last 12" pour on the x=18' line that carried wood on both faces — and left this
    # table for [framing]; W-B-S3 split at the excavation edge into W-B-S3 + W-B-S4 so each
    # half could author its own backfill, which put one back. W-B-S2 and W-B-S3 are 7 1/4"
    # curbs under a framed walkout rather than full-height walls, but a curb is still a
    # pour and still counted here — the yardage moved, the tag count did not.
    # **41 since 2026-08-30**: W-SG-ARCH is back on the sunken garden's retired node pair as
    # a 12" x 17 1/2" BURIED GRADE BEAM — not the 16" arched cross-wall and not its masonry
    # parapet, neither of which returns. It is one more `SUNKEN_GARDEN_WALL` tag and ~1.08 cy
    # of the same pour, and it is what closes the court's structural loop so its two side
    # walls cancel each other's soil thrust (`engineering/retaining_system.py`).
    # **37 since 2026-09-03, and the four that left are the whole garage wainscot.**
    # W-G-WAIN-S/N (the two east piers) and W-G-WAIN-SRET/NRET (their SE/NE corner returns)
    # were deleted outright. THE SIX STEM TAGS STAY: W-GF-E1/E2 existed before the wainscot
    # did, because the stem drops to a grade beam under the overhead door, and W-GF-S3/N2
    # are a kept fossil of the corner returns (see test_catlin_contract_m3's
    # freestanding-garage test for why un-splitting them is not worth the uid churn).
    # **38 since 2026-09-05**, and the extra tag is not concrete at all. The morning's
    # replan split W-B-S1 for the rotated sauna's liner; the afternoon's shrink undid that
    # split and added W-B-WELL, the stair well's partition, which lands here for a reason
    # worth knowing: its STRUCTURE layer carries no `FramingSpec` — `resolve/stairs/u_split`
    # already generates the studs between the two flights and a second set interpenetrates
    # them — and `frames_as_members` is the same predicate this table partitions on, so a
    # structure layer that does not frame reads as monolithic and bills its gross volume.
    # `prices.toml` therefore prices `CATLIN_STAIRWELL_PARTITION_4H` at zero and says why:
    # those sticks are already in `[framing]`. That is the one row in this table which is
    # not a pour, and it is the reason the material set below gained "spf".
    # **39 later the same day**: W-SG-BRKBM, the veneer's grade beam, on its own
    # `SG_VENEER_BEAM_14` — the court's 12" pour plus the 2" XPS isolation board that keeps
    # W-B-BRICK's cold out of FT-B-S2/S3. The board is NOT in this table (it is an
    # INSULATION layer and this one partitions on STRUCTURE); it bills as `xps:2.0` through
    # `takeoff/envelope.py`, which is the whole reason the break was authored as a Layer.
    assert len({tag for row in rows for tag in row["tags"]}) == 39
    # **`aluminum-flat-pvdf` LEFT THIS TABLE ON 2026-09-03, and it did not leave the house.**
    # The garage's base skin is now the 24" `coil-ext` band on the ICF stem, which is a
    # banded LAYER inside GARAGE_ICF_6 and bills through `[envelope_layers]` — 156.2 SF,
    # unchanged, because that band always ran behind the wainscot. What this table lost is
    # the wainscot's own free-standing panel wall, whose sheet WAS the assembly's STRUCTURE
    # layer and so priced here on the assembly tag. A material dropping out of this set is
    # therefore not evidence it dropped out of the model; check `[envelope_layers]` first.
    # (`off-white-brick` went the same way on 2026-09-02, brick to metal, then deleted.)
    # `glazed-lapis-brick` and `glazed-gold-brick` LEFT ON 2026-09-04 with the Ishtar scheme:
    # the veneer is one flat `brown-brick` field now. Both Materials are still in the
    # catalog, unreferenced and deliberately so (plan/assemblies.py), so a material dropping
    # out of this set is again not evidence it dropped out of the catalog.
    assert {row["material"] for row in rows} == {
        "concrete", "retaining-block", "brown-brick", "spf"}
    # Bigger than the entire priced concrete order (footings + slab) the estimate used to
    # know about, which is the measure of what was missing. It was >100 cy until 2026-08-23:
    # the flat bearing seat took every basement wall from 9'-4" to exactly 8'-0", which is
    # ~14% of the tallest pour in the house. Then ~9.8 cy more on 2026-08-24, when W-B-STR
    # and W-B-STR3 were framed — 89.0 cy now.
    # ~83.9 cy since 2026-08-28: ~4.1 cy of W-B-CS and ~2.9 cy of the sunken-garden
    # walkout out, ~0.2 cy of curb back. Still bigger than the entire priced concrete order
    # the estimate used to know about, which is what this floor is for.
    assert sum(float(row["volume_cubic_yards"]) for row in rows) > 80
    assert all(float(row["net_area_sqft"]) > 0 for row in rows)


def test_every_wall_bills_its_structure_exactly_once(catlin_model) -> None:
    """The regression gate. Asserted against *members*, not against the predicate the
    takeoff selects on, so it cannot be satisfied circularly: a wall either frames lumber
    (billed in `framing`) or it appears here, never both and never neither.

    The witness is every structure category, not ``"stud"`` alone — see
    ``_helpers.FRAMED_STRUCTURE_CATEGORIES`` for the wall that made the difference."""
    monolithic = {tag for row in wall_structure_takeoff(catlin_model) for tag in row["tags"]}
    framed = {wall.tag for wall in catlin_model.walls if frames_structure(wall)}
    all_walls = {wall.tag for wall in catlin_model.walls}

    assert monolithic & framed == set(), (
        f"double-billed: {sorted(monolithic & framed)}")
    assert monolithic | framed == all_walls, (
        f"billed nowhere: {sorted(all_walls - monolithic - framed)}")


def test_the_sunken_garden_brick_wythe_is_billed(catlin_model) -> None:
    """W-B-BRICK — the brick veneer over the exposed basement wall at the sunken garden,
    added in 76c1871 — is the wall whose absence from the BOM surfaced this hole.

    THREE ROWS BECAME ONE on 2026-09-04. From the Ishtar scheme (2026-08-20) the wythe was a
    split row (`Layer.slot`) of five banded regions in three colours, and this test pinned a
    row per colour — because billing it by "the" structure layer, the first one, would have
    put the whole net face on the brown plinth and never mentioned the glaze. The glaze is
    gone and the plinth's brick is now the whole field, so there is one honest row. What is
    still pinned is that the row exists, names its assembly, and carries the wall's WHOLE net
    face: a single-region wythe that under-billed would look exactly like this test's PASS if
    the area bound were dropped with the colours.
    """
    rows = [row for row in wall_structure_takeoff(catlin_model)
            if "W-B-BRICK" in row["tags"]]
    assert len(rows) == 1, "one flat unglazed field, one row"
    (row,) = rows
    assert row["material"] == "brown-brick"
    assert row["assembly"] == "BASEMENT_BRICK_VENEER"
    assert row["tags"] == ["W-B-BRICK"]
    assert float(row["volume_cuft"]) > 0
    # The row is the wall's whole net face, no more and no less: 18'-8" x 8'-6 7/16" gross,
    # less the two reveals (5'-0" x 78" and 14" x 20"). 133.2 until 2026-08-23, when the
    # wythe's base rose 2 9/16" with the footing toe it bears on — its head is still 0'-0",
    # so the wall simply got that much shorter. The window was 132 before 2026-08-21, when
    # both reveals were taken down 6" at the head — a reminder that this bound moves whenever
    # the reveals or the wall's extent do. The face itself did NOT move on 2026-09-04: only
    # the number of rows it is split across did.
    #
    # ** 6" SHORTER SINCE 2026-09-05, AND THE 6" WAS NEVER BUILDABLE. ** N-B-BRICK-E was on
    # W-SG-E1's AXIS at 28'-0", which was harmless while the wythe stood north of that wall's
    # north end. Moving the veneer south for its 6" cavity walked its east 6" INSIDE the
    # retaining wall — 4.25 SF of brick billed into solid concrete, at 0 FAIL. The node is on
    # the court's clear face at 27'-6" now, so this bound drops with it.
    assert 122 < float(row["net_area_sqft"]) < 128


def test_the_garden_walls_are_distinguishable_from_house_concrete(catlin_model) -> None:
    """Grouped by assembly, so garden work never merges into the foundation pour — they
    are both `concrete` and they are not the same order or the same price."""
    by_assembly = {row["assembly"]: row for row in wall_structure_takeoff(catlin_model)}
    for assembly in ("SUNKEN_GARDEN_WALL", "RETAINING_BLOCK_12",
                     "BASEMENT_BRICK_VENEER", "CATLIN_BASEMENT_12",
                     "CATLIN_BASEMENT_8"):
        assert assembly in by_assembly, f"{assembly} lost its own row"
    house = by_assembly["CATLIN_BASEMENT_12"]
    garden = by_assembly["SUNKEN_GARDEN_WALL"]
    assert set(house["tags"]).isdisjoint(garden["tags"])
    # And the 2026-08-21 pour split bills separately too, which is the whole point of it:
    # the 12" row is the deck-bearing east wall alone, and the eight thinned segments order
    # their own 8" concrete at their own rate (houses/catlin/prices.toml).
    assert set(house["tags"]) == {"W-B-E1", "W-B-E2"}
    # One row since 2026-09-02: CATLIN_BASEMENT_8_GARDEN lost its last two walls with the
    # stucco retirement and is unreferenced (kept in plan/assemblies.py for the revert).
    assert "CATLIN_BASEMENT_8_GARDEN" not in by_assembly
    thinned = set(by_assembly["CATLIN_BASEMENT_8"]["tags"])
    # W-B-N4 is the west 6'-0" of the old W-B-N3, split off on 2026-08-23 for the ESS
    # closet's west partition. Same assembly, same thickness, its own strip footing.
    # W-B-S4 is the east 8'-0" of the old W-B-S3, split off on 2026-08-28 at the excavation
    # edge — and it, not W-B-S3, is the segment that is still a full-height 8" pour: the
    # west half stands inside the sunken garden and is a 7 1/4" curb under a framed wall.
    assert thinned == {"W-B-N1", "W-B-N2", "W-B-N3", "W-B-N4", "W-B-W1", "W-B-W2",
                       "W-B-S1", "W-B-S4"}


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
