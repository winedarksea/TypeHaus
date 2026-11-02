"""Floor finishes: a library material behind every finish string, and a colour off it.

``Room.floor_finish`` has resolved and exported since M1, but nothing consumed it — the .glb
painted every room one flat grey and the viewer drew no room floor at all, so a house of
carpet, oak, LVP and tile looked like bare subfloor everywhere. The fix is not "a colour per
room": it is that the finish string names a real ``Material`` in ``library/materials/``, so
the viewer, the export and the takeoff all resolve one definition. These tests pin that
contract — the string↔material join, and what happens when it fails.

The visual acceptance test is the headless UI pass, not anything here.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.palette import _authored_material_color, _color, _room_floor_color
from typehaus.resolve.solid_categories import in_slab_family

# Every finish string that reaches a floor anywhere in houses/catlin — the field finishes
# authored on Rooms plus the zone finishes (none is derived from a Slab since the main deck
# went to wood trusses, decision #112). Kept explicit rather
# than derived so that adding a finish to a storey without adding its material trips here.
_CATLIN_FINISHES = {"oak-floor-custom", "lvp", "catlin-theater-carpet", "sealed-concrete",
                    "catlin-rubber-stall-mat", "vinyl-sheet", "catlin-plant-vinyl-raised",
                    "catlin-carpet-raised",
                    "catlin-tile-opera-blue", "catlin-tile-kaleo-brick",
                    "catlin-tile-agua-linda", "catlin-tile-carrara"}


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
    """Carpet bills its pad; Cotton Oak is one plank with its backing."""
    for material in _library(catlin_model).materials:
        for companion in material.floor_companion_refs:
            assert _material(catlin_model, companion) is not None


# --- 2. the colour the export resolves ----------------------------------------------------

def test_the_glb_paints_a_room_in_its_own_finish(catlin_model):
    """The colour comes off the material, through the same authored-colour path
    ui/src/nordic/palette.ts::materialColor takes."""
    seen = {}
    for tag in sorted(_CATLIN_FINISHES):
        material = _material(catlin_model, tag)
        color = _room_floor_color(catlin_model, tag)
        assert color == _authored_material_color(material)
        seen[tag] = color
    assert len(set(seen.values())) == len(seen), "finishes must not export the same colour"
    assert _color("floor") not in seen.values()


def test_an_unfinished_or_unknown_finish_falls_back_rather_than_raising(catlin_model):
    """A room with no finish is bare deck; a typo'd finish must not crash the export — it
    shows up as bare deck here and as an explicit UNKNOWN row in the takeoff."""
    assert _room_floor_color(catlin_model, None) == _color("floor")
    assert _room_floor_color(catlin_model, "no-such-finish") == _color("floor")


# --- 3. the second storey the user asked for ----------------------------------------------

def test_second_storey_finishes_match_the_doorway_assemblies(catlin_model):
    finishes = {room.tag: room.floor_finish for room in catlin_model.rooms
                if room.storey == "second"}
    assert {tag for tag, finish in finishes.items() if finish == "oak-floor-custom"} == {
        "RM-S-HALL", "RM-S-NCLOSET", "RM-S-SUITE", "RM-S-CLOSET", "RM-S-STUDY2"}
    assert {tag for tag, finish in finishes.items()
            if finish == "catlin-carpet-raised"} == {
        "RM-S-BED1", "RM-S-BED2", "RM-S-BED3"}
    assert finishes["RM-S-SUITEBATH"] == "catlin-tile-kaleo-brick"
    assert finishes["RM-S-VANITY"] == "catlin-tile-agua-linda"
    assert finishes["RM-S-BATH1"] == "catlin-tile-carrara"
    assert finishes["RM-S-PLANT"] == "catlin-plant-vinyl-raised"
    assert "RM-S-LANDING" not in finishes
    assert "RM-S-STAIR" not in finishes


# --- 4. FinishZone reaches the IR ---------------------------------------------------------

def test_finish_zones_survive_resolve(catlin_model, project):
    """``Room.finish_zones`` was authored-only: ``ResolvedRoom`` had no field for it, so a
    FinishZone written in plan source loaded fine and was then silently dropped. Resolve it,
    clipped to the room, so a hearth pad drawn proud of the wall cannot bill more tile than
    the room has floor."""
    from typehaus.model import (
        Assembly,
        FinishZone,
        Layer,
        LayerFunction,
        Library,
        Material,
        Node,
        Occupancy,
        PlanModel,
        Room,
        Storey,
        Wall,
        ft,
        inch,
        pt,
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
    # Clipped to the room's finish face, 1 3/4" (half the stud) inside the wall axis:
    # 22 1/4" x 4' of the authored 4' x 4' pad.
    clipped = (ft(2).meters - inch(1.75).meters) * ft(4).meters
    assert carried.area_m2 == pytest.approx(clipped, rel=1e-6)
    # ** AND THE CLIPPED RING IS WHAT IS DRAWN. ** Until 2026-09-05 the authored outline was
    # carried through instead, so this pad billed 2'x4' and drew 4'x4' — two feet of tile on
    # the wrong side of the wall, in the .glb, the viewer and every plan drawing. It surfaced
    # as a living-room floor sticking a foot out of the catlin house, past walls that were
    # never near the zone's real edges, and no check saw it because the AREA was right.
    assert Polygon(carried.outline).area == pytest.approx(clipped, rel=1e-6)
    assert Polygon(resolved.clear_face).buffer(1e-6).contains(Polygon(carried.outline))


# --- 5. the advisory ----------------------------------------------------------------------

def test_radiant_under_a_limited_finish_is_advised(catlin_model):
    """Nothing in this house puts radiant under a limited finish any more — and the cases
    that did are why the check exists.

    FH-S-BATH1 ran under RM-S-BATH1's LVP until 2026-09-05 and FH-M-DINING under the main
    floor's LVP until 2026-11-01 (it was retired with SL-M-DECK, decision #112, so no mat is
    left to throttle). The two remaining zones are under tile and the advisory is silent,
    which is the outcome an advisory is for. The synthetic loop in the next test keeps the
    mechanism pinned, including the polygon match for a zone that carries no ``room_ref``.
    """
    from typehaus.checks.advisory.checks import floor_finish_over_radiant
    from typehaus.checks.code.mn_residential.profile import MN_2020
    from typehaus.checks.registry import CheckContext, Preferences

    findings = floor_finish_over_radiant(CheckContext(
        plan=catlin_model.plan, model=catlin_model, preferences=Preferences(),
        profile=MN_2020))
    assert findings == []


# A loop from x 23' to 30', y 11' to 16', wholly inside RM-M-LIVING; a synthetic hearth-style
# zone covers its east third (x > 8 m).
_STRADDLING_LOOP = [(7.0104, 3.3528), (9.144, 3.3528), (9.144, 4.8768), (7.0104, 4.8768)]
_EAST_ZONE = [(8.0, 0.0), (20.0, 0.0), (20.0, 20.0), (8.0, 20.0)]


def test_a_radiant_loop_that_crosses_a_finish_boundary_reports_the_limited_half(catlin_model):
    """The half-and-half case the polygon test exists to catch: a loop spanning a finish
    zone's edge is read per polygon, not by the room's field string alone. Synthetic
    (the house has no such boundary); the unlimited zone must not mask the plank half."""
    from dataclasses import replace

    from typehaus.checks.advisory.checks import floor_finish_over_radiant
    from typehaus.checks.code.mn_residential.profile import MN_2020
    from typehaus.checks.registry import CheckContext, Preferences
    from typehaus.resolve.model import ResolvedFinishZone

    straddle = replace(catlin_model.floor_heat[0], zone=_STRADDLING_LOOP)
    zone = ResolvedFinishZone(outline=_EAST_ZONE, material_ref="sealed-concrete", area_m2=1.0)
    rooms = [replace(room, finish_zones=(zone,)) if room.tag == "RM-M-LIVING" else room
             for room in catlin_model.rooms]
    model = replace(catlin_model, floor_heat=[straddle], rooms=rooms)
    findings = floor_finish_over_radiant(CheckContext(
        plan=model.plan, model=model, preferences=Preferences(), profile=MN_2020))
    messages = [f.message for f in findings if "RM-M-LIVING" in f.element_tags]
    assert len(messages) == 1, messages
    assert "lvp floor" in messages[0]


# --- 4. the finish follows the deck ------------------------------------------------------
#
# Since decision #112 no slab carries a floor_finish: the whole main floor is plywood under
# one LVP field. The slab-derived zone (``Slab.floor_finish``) is pinned synthetically.


def test_the_living_room_is_one_lvp_field_with_no_derived_zone(catlin_model):
    living = next(room for room in catlin_model.rooms if room.tag == "RM-M-LIVING")
    assert living.floor_finish == "lvp"
    assert living.finish_zones == ()


def test_a_slab_with_a_floor_finish_claims_its_footprint_back_from_the_room():
    """Engine feature, synthetic: a slab whose top IS the finish becomes a clipped, derived
    zone named for the slab; a slab already matching the room's field adds none."""
    from types import SimpleNamespace as NS

    from shapely.geometry import Polygon

    from typehaus.resolve.rooms import _derived_finish_zones

    def slab(tag, finish, x0):
        pts = [(x0, 0), (x0 + 10, 0), (x0 + 10, 10), (x0, 10)]
        return NS(element_kind="Slab", tag=tag, floor_finish=finish,
                  outline=[NS(xy_m=p) for p in pts])

    plan = NS(storey_elements=lambda _tag: [slab("S1", "coated-concrete", 5),
                                             slab("S2", "lvp", 0)])
    clear = Polygon([(0, 0), (8, 0), (8, 10), (0, 10)])
    zones = _derived_finish_zones(plan, "main", NS(floor_finish="lvp"), clear, [])
    assert [(z.material_ref, z.source_ref) for z in zones] == [("coated-concrete", "S1")]
    assert zones[0].area_m2 == pytest.approx(30.0)  # clipped to the room: x 5..8


def test_the_billed_finishes_are_one_lvp_field(catlin_model):
    """No coating row: the whole main floor bills as plank."""
    from typehaus.takeoff.finishes import floor_finish_rows

    rows = {row["finish"]: row for row in floor_finish_rows(catlin_model)}
    assert "coated-concrete" not in rows
    assert {"RM-M-LIVING", "RM-M-PANTRY"} <= set(rows["lvp"]["rooms"])
    assert "RM-M-MUDROOM" in rows["lvp"]["rooms"]
    assert {"RM-M-MECH", "RM-M-MUD-CLOSET"} <= set(rows["lvp"]["rooms"])
    assert "lvp-underlayment" not in rows
    assert {"RM-S-HALL", "RM-S-NCLOSET"} <= set(rows["oak-floor-custom"]["rooms"])
    assert set(rows["vinyl-sheet"]["rooms"]) == {
        "RM-A-STUBATH", "RM-A-STUDIO", "RM-B-BATH"}
    assert rows["catlin-plant-vinyl-raised"]["rooms"] == ["RM-S-PLANT"]
    assert rows["catlin-plant-sureply"]["rooms"] == ["RM-S-PLANT"]
    assert rows["catlin-plant-sureply"]["under"] == "catlin-plant-vinyl-raised"
    assert rows["catlin-plant-sureply"]["net_area_sqft"] == rows[
        "catlin-plant-vinyl-raised"]["net_area_sqft"]
    assert rows["catlin-plant-sureply"]["order_area_sqft"] == rows[
        "catlin-plant-vinyl-raised"]["order_area_sqft"]
    # 529.6 SF after the 1/2" walls, less the attic's 8.1 SF neo-angle receptor, less
    # ~0.6 SF the D-A-HALVES / D-B-BATH reducers cover in their reveals (2026-11-01).
    assert (float(rows["vinyl-sheet"]["net_area_sqft"])
            + float(rows["catlin-plant-vinyl-raised"]["net_area_sqft"])) == pytest.approx(
                520.6, abs=0.5)
    assignments = {
        "catlin-tile-opera-blue": ("RM-M-BATH2", "catlin-ditra-heat"),
        "catlin-tile-carrara": ("RM-S-BATH1", "catlin-ditra-heat"),
        "catlin-tile-kaleo-brick": ("RM-S-SUITEBATH", "catlin-ditra-xl"),
        "catlin-tile-agua-linda": ("RM-S-VANITY", "tile-uncoupling-membrane"),
    }
    # Two heated finishes share a membrane tag: key companion rows by parent as well.
    companion_rows = {(row["under"], row["finish"]): row
                      for row in floor_finish_rows(catlin_model) if "under" in row}
    for finish, (room, companion) in assignments.items():
        assert rows[finish]["rooms"] == [room]
        companion_row = companion_rows[finish, companion]
        assert companion_row["net_area_sqft"] == rows[finish]["net_area_sqft"]
        assert companion_row["rooms"] == [room]
        assert rows[finish]["known"] and companion_row["known"]
    assert "catlin-tile-heated" not in rows
    assert "catlin-tile-oak-height" not in rows


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
    has moved once since: all three were sheet vinyl from 2026-08-21, and on 2026-09-05 all
    three took porcelain — dirt containment at the entry, on FS-M-MECH's 10'-0" span, which
    is the same deck under all of them. What must not change is that none of them claims a
    concrete finish: there is no slab under any of them."""
    retyped = {"RM-M-MUDROOM", "RM-M-MECH", "RM-M-MUD-CLOSET"}
    finishes = {room.tag: room.floor_finish for room in catlin_model.rooms
                if room.tag in retyped}
    assert finishes == {tag: "lvp" for tag in retyped}


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
                         if in_slab_family(solid.category) and solid.storey == garage.storey])
    fraction = face.intersection(slabs).area / face.area
    assert 0.8 < fraction < 0.95, fraction
    assert not any("RM-GARAGE" in f.element_tags
                   for f in _concrete_finish_findings(catlin_model))


def test_bathroom_tile_product_contracts(catlin_plan):
    materials = {material.tag: material for material in catlin_plan.library.materials}
    products = {product.tag: product for product in catlin_plan.library.products}
    for tag, product, recipe, companion in (
        ("catlin-tile-opera-blue", "PROD-IVY-SELENE-OPERA-BLUE", "tile-onyx-opera-blue-grid",
         "catlin-ditra-heat"),
        ("catlin-tile-kaleo-brick", "PROD-IVY-KALEO-BRICK", "tile-kaleo-running-bond",
         "catlin-ditra-xl"),
        ("catlin-tile-agua-linda", "PROD-MSI-AGUA-LINDA", "tile-onyx-agua-linda-grid",
         "tile-uncoupling-membrane"),
        ("catlin-tile-carrara", "PROD-FLORIDA-CARRARA-MATTE", "tile-carrara-grid",
         "catlin-ditra-heat"),
    ):
        material = materials[tag]
        assert material.product_ref == product
        assert material.finish == recipe
        assert material.finish_thickness_in == 0.75
        assert material.floor_companion_refs == (companion,)
        assert "epoxy grout" in material.source
        assert products[product].url
        assert products[product].model
