"""Floor finishes: a library material behind every finish string, and a colour off it.

``Room.floor_finish`` has resolved and exported since M1, but nothing consumed it — the .glb
painted every room one flat grey and the viewer drew no room floor at all, so a house of
carpet, oak, LVP and tile looked like bare subfloor everywhere. The fix is not "a colour per
room": it is that the finish string names a real ``Material`` in ``library/materials.py``, so
the viewer, the export and the takeoff all resolve one definition. These tests pin that
contract — the string↔material join, and what happens when it fails.

The visual acceptance test is the headless UI pass, not anything here.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.palette import _color, _room_floor_color, _hex_rgba
from typehaus.emit.draw.palette import material_color

# Every finish string that reaches a floor anywhere in houses/catlin — the field finishes
# authored on Rooms plus the zone finishes, which include one taken from a Slab
# (SL-M-DECK's polished cap) rather than authored on a room at all. Kept explicit rather
# than derived so that adding a finish to a storey without adding its material trips here.
_CATLIN_FINISHES = {"oak", "lvp", "carpet", "tile", "sealed-concrete", "rubber",
                    "vinyl-sheet", "polished-concrete"}


def _library(catlin_model):
    return catlin_model.plan.library


def _material(catlin_model, tag: str):
    return next((m for m in _library(catlin_model).materials if m.tag == tag), None)


# --- 1. the string↔material join ----------------------------------------------------------

def test_every_authored_floor_finish_names_a_library_material(catlin_model):
    """The join the whole feature rests on. A finish with no material behind it renders as
    bare deck, exports as flat grey, and bills as an UNKNOWN row — all silently, which is
    why this is asserted over the *authored* set rather than over the material list."""
    authored = {room.floor_finish for room in catlin_model.rooms if room.floor_finish}
    authored |= {zone.material_ref for room in catlin_model.rooms
                 for zone in room.finish_zones}
    assert authored == _CATLIN_FINISHES
    missing = sorted(tag for tag in authored if _material(catlin_model, tag) is None)
    assert missing == []


def test_each_finish_material_declares_what_it_looks_like(catlin_model):
    """A finish material exists to carry appearance — an entry with no colour would resolve
    to the family fallback and put carpet, oak and LVP back on the same grey."""
    colors = {}
    for tag in sorted(_CATLIN_FINISHES):
        material = _material(catlin_model, tag)
        assert material.color, f"{tag} declares no colour"
        assert material.hatch, f"{tag} declares no hatch family"
        colors[tag] = material.color
    # ...and they have to be *different* colours, or the viewer separates nothing.
    assert len(set(colors.values())) == len(colors), colors


def test_the_companion_layers_a_finish_implies_are_in_the_library(catlin_model):
    """Carpet needs pad under it and LVP needs underlayment; a takeoff that bills the
    covering alone hands over an unorderable schedule."""
    for tag in ("carpet-pad", "lvp-underlayment"):
        assert _material(catlin_model, tag) is not None


# --- 2. the colour the export resolves ----------------------------------------------------

def test_the_glb_paints_a_room_in_its_own_finish(catlin_model):
    """The colour comes off the material, through the same authored-colour path
    ui/src/nordic/palette.ts::materialColor takes."""
    seen = {}
    for tag in sorted(_CATLIN_FINISHES):
        material = _material(catlin_model, tag)
        color = _room_floor_color(catlin_model, tag)
        assert color == _hex_rgba(material_color(material.hatch, material.color))
        seen[tag] = color
    assert len(set(seen.values())) == len(seen), "finishes must not export the same colour"
    assert _color("floor") not in seen.values()


def test_an_unfinished_or_unknown_finish_falls_back_rather_than_raising(catlin_model):
    """A room with no finish is bare deck; a typo'd finish must not crash the export — it
    shows up as bare deck here and as an explicit UNKNOWN row in the takeoff."""
    assert _room_floor_color(catlin_model, None) == _color("floor")
    assert _room_floor_color(catlin_model, "no-such-finish") == _color("floor")


# --- 3. the second storey the user asked for ----------------------------------------------

def test_the_second_storey_circulation_and_baths_run_one_lvp_floor(catlin_model):
    """LVP through both hallways, the stair landing and all three baths — one continuous
    plank floor with no thresholds on the traffic route."""
    finishes = {room.tag: room.floor_finish
                for room in catlin_model.rooms if room.storey == "second"}
    # RM-S-LANDING and RM-S-STAIR are gone as separate claims: with the centre line open
    # under BM-S-HALL between y 22'-4" and 30'-10", the hall, the landing and the stair
    # well polygonize as one face, and RM-S-HALL is the seed that claims it.
    assert {tag for tag, finish in finishes.items() if finish == "lvp"} == {
        "RM-S-HALL", "RM-S-SUITEBATH", "RM-S-VANITY", "RM-S-BATH1"}
    assert "RM-S-LANDING" not in finishes
    assert "RM-S-STAIR" not in finishes
    # Both walk-ins are carpet, continuing out of the bedrooms they open off.
    assert finishes["RM-S-CLOSET"] == "carpet"
    assert finishes["RM-S-NCLOSET"] == "carpet"
    # Everything else on the storey is untouched. RM-S-PLANT left tile for heat-welded
    # sheet vinyl — the plant room's floor and walls are one coved tray (notes/plant_room.md),
    # which tile cannot be.
    assert finishes["RM-S-PLANT"] == "vinyl-sheet"
    assert finishes["RM-S-STUDY2"] == "oak"


# --- 4. FinishZone reaches the IR ---------------------------------------------------------

def test_finish_zones_survive_resolve(catlin_model, project):
    """``Room.finish_zones`` was authored-only: ``ResolvedRoom`` had no field for it, so a
    FinishZone written in plan source loaded fine and was then silently dropped. Resolve it,
    clipped to the room, so a hearth pad drawn proud of the wall cannot bill more tile than
    the room has floor."""
    from typehaus.model import (
        Assembly, FinishZone, Layer, LayerFunction, Library, Material, Node, Occupancy,
        PlanModel, Room, Storey, Wall, ft, inch, pt,
    )
    from typehaus.resolve import resolve

    assembly = Assembly(tag="P", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),))
    storey = Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(8))
    corners = ((0, 0), (10, 0), (10, 10), (0, 10))
    nodes = [Node(uid=f"N00000000{i + 1}", tag=f"N{i}", position=pt(ft(x), ft(y)))
             for i, (x, y) in enumerate(corners)]
    walls = [Wall(uid=f"W00000000{i + 1}", tag=f"W{i}", start_node=f"N{i}",
                  end_node=f"N{(i + 1) % 4}", assembly="P", top=ft(8))
             for i in range(4)]
    # A 4'x4' hearth pad at the room's SW corner, drawn 2' *outside* the wall so the clip has
    # something to do: 4x4 authored, 2x4 of it actually inside the room.
    zone = FinishZone(outline=(pt(ft(-2), ft(1)), pt(ft(2), ft(1)),
                               pt(ft(2), ft(5)), pt(ft(-2), ft(5))),
                      material_ref="tile")
    room = Room(uid="R000000001", tag="RM", seed=pt(ft(5), ft(5)),
                occupancy=Occupancy.LIVING, floor_finish="oak", finish_zones=(zone,))
    plan = PlanModel(
        project=project,
        library=Library(materials=(Material(tag="wood", name="Wood", r_per_inch=1.2),),
                        assemblies=(assembly,)),
        storeys=(storey,),
    ).with_elements("main", [*nodes, *walls, room])

    model, _findings = resolve(plan)
    resolved = next(r for r in model.rooms if r.tag == "RM")
    assert len(resolved.finish_zones) == 1
    carried = resolved.finish_zones[0]
    assert carried.material_ref == "tile"
    # Clipped to the room: 2' x 4' of the authored 4' x 4' pad.
    assert carried.area_m2 == pytest.approx(ft(2).meters * ft(4).meters, rel=1e-6)
    # ...but the authored outline is preserved, so the drawing still shows what was drawn.
    assert Polygon(carried.outline).area == pytest.approx(
        ft(4).meters * ft(4).meters, rel=1e-6)


# --- 5. the advisory ----------------------------------------------------------------------

def test_radiant_under_a_limited_finish_is_advised(catlin_model):
    """LVP over FH-S-BATH1 is legal but surface-temperature limited, which is a
    commissioning decision and so is advised.

    FH-M-DINING is the case the polygon match exists for — it carries no ``room_ref`` at
    all, so a ref lookup would miss it entirely — and it is also why the check reads
    ``finish_zones`` rather than ``Room.floor_finish``. The loop sits wholly inside
    SL-M-DECK's band, where the finish is the polished cap, not RM-M-LIVING's field LVP.
    Polished concrete is exactly what radiant wants, so there is nothing to advise.
    """
    from typehaus.checks.advisory.checks import floor_finish_over_radiant
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    findings = floor_finish_over_radiant(CheckContext(
        plan=catlin_model.plan, model=catlin_model, preferences=Preferences(),
        profile=MN_2024))
    assert {tuple(sorted(f.element_tags)) for f in findings} == {
        ("FH-S-BATH1", "RM-S-BATH1"),
    }
    assert all(f.severity.value == "warn" for f in findings)
    # FH-M-BATH2 is under tile, which is what radiant wants — no advisory for it.
    assert not any("FH-M-BATH2" in f.element_tags for f in findings)


# A loop from x 23' to 30', y 11' to 16', wholly inside RM-M-LIVING and straddling
# _BAND_Y (13'): 40% of it is over FS-M-EAST's plywood, 60% over SL-M-DECK's cap.
_STRADDLING_LOOP = [(7.0104, 3.3528), (9.144, 3.3528), (9.144, 4.8768), (7.0104, 4.8768)]


def test_a_radiant_loop_that_crosses_a_finish_boundary_reports_the_limited_half(catlin_model):
    """The half-and-half case the polygon test exists to catch.

    A loop spanning the concrete/wood boundary in RM-M-LIVING runs under polished concrete
    for part of its length and under a covering for the rest. The covered half is still
    surface-temperature limited, and reading either the field finish alone or the zone alone
    would report exactly one of the two wrongly.

    South of `_BAND_Y` is the authored OAK zone since 2026-09-05, so the half this reports
    is oak rather than the plank it was — a **stronger** advisory, not a different mechanism:
    solid wood is moisture-limited as well as temperature-limited. The catlin house does not
    actually put radiant under that bay (FH-M-DINING is wholly over the cap, and
    ``haus check`` reports nothing here); this loop is synthetic, and the assertion is about
    which SIDE the check reads, not about a real condition.
    """
    from dataclasses import replace

    from typehaus.checks.advisory.checks import floor_finish_over_radiant
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    dining = next(zone for zone in catlin_model.floor_heat if zone.tag == "FH-M-DINING")
    straddle = replace(dining, zone=_STRADDLING_LOOP)  # 40% plank, 60% cap
    model = replace(catlin_model, floor_heat=[straddle])
    findings = floor_finish_over_radiant(CheckContext(
        plan=model.plan, model=model, preferences=Preferences(), profile=MN_2024))
    messages = [f.message for f in findings if "RM-M-LIVING" in f.element_tags]
    assert len(messages) == 1, messages
    assert "oak floor" in messages[0]


# --- 4. the finish follows the deck ------------------------------------------------------
#
# RM-M-LIVING is one 766 SF claim over two structures: SL-M-DECK's EPS-formed cap north of
# y=13' east of x=18', and FS-M-EAST / FS-M-WEST's I-joists and plywood everywhere else.
# ``Room.floor_finish`` is one string, so before ``Slab.floor_finish`` existed the room
# billed 766 SF of LVP — 411 of it over a polished concrete cap nobody was going to cover.

_M2_TO_FT2 = 10.7639104


def test_the_living_room_splits_its_floor_where_its_structure_splits(catlin_model):
    """One derived zone taken from the slab, one authored oak zone, and the field is what
    is left of the room after both."""
    living = next(room for room in catlin_model.rooms if room.tag == "RM-M-LIVING")
    assert living.floor_finish == "lvp", "the room's own string stays the FIELD finish"
    # TWO zones: the derived concrete band below, and an AUTHORED oak
    # rectangle over the south bay. They do not overlap — the oak stops at y=13' and
    # SL-M-DECK starts there — so neither zone is cut against the other.
    #
    # It was the derived band plus an authored `vinyl-sheet` HALL band until 2026-09-05.
    # That zone is deleted rather than replaced: the hall's finish is now the room's own
    # field `lvp`, which is also what the rooms off it carry, so there is nothing left for a
    # zone to override.
    assert len(living.finish_zones) == 2
    zone = next(z for z in living.finish_zones if z.source_ref is not None)
    assert zone.material_ref == "polished-concrete"
    # Derived, not authored — and it names the slab, which is the answer to "why is this
    # band different" in the Inspector and in the takeoff.
    assert zone.source_ref == "SL-M-DECK"
    # 411.3 when RM-M-PANTRY was framed out of the living room's NW corner. The band is
    # clipped to the room, so the room losing its clear face plus the new partition
    # footprint takes exactly that off the zone. That area did not leave the slab —
    # it moved to RM-M-PANTRY's own derived zone, which is the whole of that room's floor
    # (see test_the_billed_finishes_move_with_the_split).
    #
    # 390.6 -> 392.7 when W-M-PAN-S moved 4" north to pull the cold-storage run out of the
    # passage: the pantry gave 2.1 sf of clear face back to the
    # living room. ** THE INVARIANT IS THE SUM, NOT EITHER HALF. ** Both rooms sit wholly on
    # SL-M-DECK, so moving the wall between them only moves area from one derived zone to the
    # other — the billed polished-concrete total in
    # test_the_billed_finishes_move_with_the_split is 410.2 before and after, and does not
    # move when this number does.
    #
    # UNMOVED by the 2026-09-05 finishes change, and that is the point: the oak is south of
    # _BAND_Y and the concrete is north of it, so nothing was taken off the band.
    assert zone.area_m2 * _M2_TO_FT2 == pytest.approx(392.7, abs=0.5)
    oak = next(z for z in living.finish_zones if z.source_ref is None)
    assert oak.material_ref == "oak"
    # The whole south bay: x 18'..36' (the centre bearing line to the east wall) by
    # y 0'..13' (the south wall to _BAND_Y), less the wall linings the clear face takes off.
    # Only the north edge is authored as a real number — the other three are over-extended
    # past the room and clipped (test_catlin_contract_m3 pins that north edge to _BAND_Y).
    assert oak.area_m2 * _M2_TO_FT2 == pytest.approx(231.7, abs=0.5)
    # 355.1 until the hall zone; 307.0 with it. 123.9 now: the hall's 48.5 sf came BACK to
    # the field when the vinyl zone was deleted, and the oak took 231.7 off it. What is left
    # of the plank in this room is the stair lane and the hall band it runs into.
    field = (living.area_m2 - zone.area_m2 - oak.area_m2) * _M2_TO_FT2
    assert field == pytest.approx(123.9, abs=0.5)


def test_a_derived_zone_is_clipped_to_the_room_not_drawn_as_the_slab(catlin_model):
    """An authored zone draws as authored and bills clipped; a derived one has no reason to
    be drawn proud of the room, so its outline IS the clipped ring. Here that is an L —
    the slab runs to x=36' and y=36', the room's clear face stops short of both."""
    from shapely.geometry import Polygon

    living = next(room for room in catlin_model.rooms if room.tag == "RM-M-LIVING")
    # Selected by ``source_ref``, not by index: the room carries an authored OAK zone, and
    # an authored ring is exactly the thing this test does NOT hold to the clear face — it
    # draws as drawn and bills clipped. The oak's ring is deliberately drawn well outside
    # the room on three sides, so it would fail the containment below.
    derived = next(z for z in living.finish_zones if z.source_ref is not None)
    ring = Polygon(derived.outline)
    face = Polygon(living.clear_face)
    assert face.buffer(1e-6).contains(ring), "the drawn ring never leaves the room"
    assert ring.area == pytest.approx(derived.area_m2, rel=1e-9)


def test_the_billed_finishes_move_with_the_split(catlin_model):
    """The whole point, in the takeoff: LVP drops by the band and the band bills as its own
    material, at its own rate, with no waste on a process measured by coverage."""
    from typehaus.takeoff.finishes import floor_finish_rows

    rows = {row["finish"]: row for row in floor_finish_rows(catlin_model)}
    # RM-M-PANTRY stands ENTIRELY on SL-M-DECK, so its derived zone is
    # its whole floor and its authored "lvp" contributes no field area at all — which is why
    # it is in the lvp room LIST below and adds nothing to the lvp number. The zone total
    # barely moves (411.3 -> 410.2): the room did not leave the slab, it only grew two
    # partitions that stand on it.
    assert rows["polished-concrete"]["rooms"] == ["RM-M-LIVING", "RM-M-PANTRY"]
    assert rows["polished-concrete"]["coating"] is True
    assert rows["polished-concrete"]["waste_pct"] == 0.0
    assert float(rows["polished-concrete"]["net_area_sqft"]) == pytest.approx(410.2, abs=0.5)
    # ** 2026-09-05, the main-floor finishes. ** 694.3 -> 590.1 of LVP. Two moves in
    # opposite directions and the oak is the bigger one:
    #   * -231.7  the living room's south bay went to the authored oak zone
    #   * +48.5   the hall band's vinyl-sheet zone was DELETED, so the corridor falls back
    #             to the room's own field finish
    #   * +79.0   RM-M-BATH1, RM-M-LAUNDRY, RM-M-MECH and RM-M-MUD-CLOSET retyped off
    #             vinyl-sheet onto the plank the hall now carries
    # RM-M-MUDROOM went the other way, to tile, and is the one room on this floor that
    # deliberately breaks the plank.
    assert float(rows["lvp"]["net_area_sqft"]) == pytest.approx(590.1, abs=0.5)
    assert "RM-M-PANTRY" in rows["lvp"]["rooms"]
    assert rows["lvp-underlayment"]["net_area_sqft"] == rows["lvp"]["net_area_sqft"]
    # The oak was RM-A-STUDY + RM-S-STUDY2 (the two studies) and is now those plus the
    # living room's south bay: 324.3 -> 555.9. That crosses a real threshold in the
    # ESTIMATE, not just in the model — houses/catlin/prices.toml's oak row carried a
    # standing warning that its quantity was under a sand-and-finish mobilisation minimum.
    assert set(rows["oak"]["rooms"]) == {"RM-A-STUDY", "RM-M-LIVING", "RM-S-STUDY2"}
    assert float(rows["oak"]["net_area_sqft"]) == pytest.approx(555.9, abs=0.5)
    # ** vinyl-sheet has left the main storey entirely. ** What is left is the three rooms
    # that are genuinely wet or genuinely cheap-and-washable, on three different storeys:
    # RM-S-PLANT (the spec that started it), RM-A-STUBATH and RM-B-BATH.
    assert set(rows["vinyl-sheet"]["rooms"]) == {"RM-A-STUBATH", "RM-B-BATH", "RM-S-PLANT"}
    assert float(rows["vinyl-sheet"]["net_area_sqft"]) == pytest.approx(228.8, abs=0.5)
    # Tile is RM-M-BATH2 (its radiant zone's mass) plus RM-M-MUDROOM (dirt containment at
    # the entry). RM-B-BATH is NOT in it — 30.2 sf under the basement stair with no radiant
    # zone went to vinyl-sheet on 2026-09-02, and that decision is untouched here.
    assert set(rows["tile"]["rooms"]) == {"RM-M-BATH2", "RM-M-MUDROOM"}
    # And the membrane follows the tile, one for one. Both tile floors in this house are
    # over a wood deck, and neither billed an uncoupling layer before 2026-09-05 —
    # ``takeoff/finishes._COMPANIONS``.
    assert rows["tile-uncoupling-membrane"]["net_area_sqft"] == rows["tile"]["net_area_sqft"]
    assert rows["tile-uncoupling-membrane"]["rooms"] == rows["tile"]["rooms"]


# --- 5. a sealer needs a slab to seal ----------------------------------------------------
#
# The drift this catches is not a typo. RM-M-MUDROOM, RM-M-MECH and RM-M-MUD-CLOSET read
# "sealed-concrete" though the basement-ceiling overhaul put FS-M-WEST's I-joists and 3/4"
# plywood under all three. The string still resolved, still rendered and still billed a
# sealer over a wood deck.

def _concrete_finish_findings(model):
    from _helpers import check_context

    from typehaus.checks.integrity.checks import concrete_finish_needs_concrete_deck

    return concrete_finish_needs_concrete_deck(check_context(model=model))


def test_no_room_claims_a_concrete_finish_over_a_deck_that_is_not_concrete(catlin_model):
    """House-wide, after the retype. ``haus check`` exits 1 on any FAIL, so this is the
    assertion that says §5's edits and the check that guards them landed together."""
    assert _concrete_finish_findings(catlin_model) == []


def test_the_three_retyped_mudroom_rooms_carry_a_hard_finish_over_their_wood_deck(catlin_model):
    """The retype that this section guards is *off* sealed-concrete, and what it lands on
    has moved once since: all three were sheet vinyl from 2026-08-21, and on 2026-09-05 the
    mudroom took porcelain (dirt containment at the entry, on FS-M-MECH's 10'-0" span) while
    the two closets joined the LVP spine. What must not change is that none of them claims a
    concrete finish — there is no slab under any of them."""
    retyped = {"RM-M-MUDROOM", "RM-M-MECH", "RM-M-MUD-CLOSET"}
    finishes = {room.tag: room.floor_finish for room in catlin_model.rooms
                if room.tag in retyped}
    assert finishes == {"RM-M-MUDROOM": "tile",
                        "RM-M-MECH": "lvp",
                        "RM-M-MUD-CLOSET": "lvp"}


def test_a_sealer_over_a_wood_deck_fails(catlin_model):
    """The regression itself: put "sealed-concrete" back on the mudroom and the build stops."""
    from dataclasses import replace

    rooms = [replace(room, floor_finish="sealed-concrete")
             if room.tag == "RM-M-MUDROOM" else room
             for room in catlin_model.rooms]
    findings = _concrete_finish_findings(replace(catlin_model, rooms=rooms))
    assert [f.element_tags for f in findings] == [("RM-M-MUDROOM",)]
    assert findings[0].result.value == "fail"
    assert findings[0].severity.value == "error"
    # The message carries the measured fraction, so the reader can tell "no slab at all"
    # from "the slab moved a little".
    assert "0% of that area sits over a slab" in findings[0].message


def test_the_garage_slab_is_not_reported_though_it_is_not_fully_covered(catlin_model):
    """The threshold is calibrated, not arbitrary. RM-GARAGE is a legitimate sealed slab
    that measures ~86%: its clear face is taken at the wood-wall lining while SL-G-FLOOR is
    poured inside the ICF stem. Exact containment would call that a defect."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    garage = next(room for room in catlin_model.rooms if room.tag == "RM-GARAGE")
    assert garage.floor_finish == "sealed-concrete"
    face = Polygon(garage.clear_face)
    slabs = unary_union([Polygon(solid.outline) for solid in catlin_model.solids
                         if solid.category == "slab" and solid.storey == garage.storey])
    fraction = face.intersection(slabs).area / face.area
    assert 0.8 < fraction < 0.95, fraction
    assert not any("RM-GARAGE" in f.element_tags
                   for f in _concrete_finish_findings(catlin_model))
