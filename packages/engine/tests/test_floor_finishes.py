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

# Every finish string authored anywhere in houses/catlin. Kept explicit rather than derived
# so that adding a finish to a storey without adding its material trips this file.
_CATLIN_FINISHES = {"oak", "lvp", "carpet", "tile", "sealed-concrete", "rubber"}


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
    """Every room used to export as _color("floor"). Now the colour comes off the material,
    through the same authored-colour path ui/src/nordic/palette.ts::materialColor takes."""
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
    assert {tag for tag, finish in finishes.items() if finish == "lvp"} == {
        "RM-S-LANDING", "RM-S-HALL", "RM-S-SUITEBATH", "RM-S-VANITY", "RM-S-ENSUITE"}
    # Both walk-ins are carpet, continuing out of the bedrooms they open off.
    assert finishes["RM-S-CLOSET"] == "carpet"
    assert finishes["RM-S-NCLOSET"] == "carpet"
    # Everything else on the storey is untouched.
    assert finishes["RM-S-STAIR"] == "oak"
    assert finishes["RM-S-PLANT"] == "tile"
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
    """LVP over FH-S-ENSUITE is legal but surface-temperature limited, and the loop under
    the dining table is under oak. Both are commissioning decisions, so both are advised.

    FH-M-DINING is the case the polygon match exists for: it carries no ``room_ref`` at all,
    so a ref lookup would have missed it entirely.
    """
    from typehaus.checks.advisory.checks import floor_finish_over_radiant
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    findings = floor_finish_over_radiant(CheckContext(
        plan=catlin_model.plan, model=catlin_model, preferences=Preferences(),
        profile=MN_2024))
    assert {tuple(sorted(f.element_tags)) for f in findings} == {
        ("FH-M-DINING", "RM-M-LIVING"),
        ("FH-S-ENSUITE", "RM-S-ENSUITE"),
    }
    assert all(f.severity.value == "warn" for f in findings)
    # FH-M-BATH2 is under tile, which is what radiant wants — no advisory for it.
    assert not any("FH-M-BATH2" in f.element_tags for f in findings)
