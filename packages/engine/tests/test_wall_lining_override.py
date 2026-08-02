"""``Room.wall_lining`` / ``wall_lining_exceptions`` are real: they replace the assembly's
``default_lining`` in resolved wall geometry (per-wall paint colour, W-F).

The schema fields existed and set the room's clear-face inset, but the wall resolver always
stacked ``assembly.default_lining`` — an authored override reached no viewer, emitter or
takeoff. These tests lock the whole chain: plan override → resolved layers →
authored-colour glTF parity → per-lining IfcWallType variants, plus the two WARNING kinds
(shared-wall conflict, lining-less assembly) that keep a silent no-op from coming back.
"""

from __future__ import annotations

import pytest

from typehaus.model import (
    Assembly,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Room,
    Storey,
    Wall,
    WallLiningException,
    ft,
    inch,
    pt,
)
from typehaus.model.enums import Occupancy
from typehaus.resolve import resolve
from typehaus.resolve.rooms import _lining_inset, wall_lining_overrides

_PAINT = Layer(name="paint", material_ref="paint", thickness=inch(0.01),
               function=LayerFunction.FINISH)
_GWB = Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
             function=LayerFunction.FINISH)

# The override stack: the same gypsum under a different paint *material* — colour is a
# material property, so a differently coloured wall is a different material tag.
ACCENT_LINING = (
    Layer(name="paint", material_ref="paint-accent", thickness=inch(0.01),
          function=LayerFunction.FINISH),
    _GWB,
)


def _library() -> Library:
    materials = (
        Material(tag="paint", name="Off-white latex", color="#f0ede6", coating=True),
        Material(tag="paint-accent", name="Spruce accent latex", color="#2e4a44",
                 coating=True),
        Material(tag="gwb", name="gwb"),
        Material(tag="spf", name="spf"),
        Material(tag="osb", name="osb"),
        Material(tag="metal", name="metal"),
    )
    exterior = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="sheathing", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="cladding", material_ref="metal", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ), default_lining=(_PAINT, _GWB))
    # A partition that carries a lining of its own (the shared-wall conflict case) …
    lined_partition = Assembly(tag="PART", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
    ), default_lining=(_PAINT, _GWB))
    # … and one that does not (the ``wall_lining_unlined`` case).
    bare_partition = Assembly(tag="BARE", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
    ))
    return Library(materials=materials,
                   assemblies=(exterior, lined_partition, bare_partition))


def _plan(project, mid_assembly: str = "PART", west_room=None, east_room=None) -> PlanModel:
    """Two 6m x 6m rooms sharing one partition (W-MID); everything else is EXT."""
    storey = Storey(uid="STLINING01", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = [
        Node(uid=f"LN{i:08d}", tag=tag, position=pt(ft(x), ft(y)))
        for i, (tag, x, y) in enumerate((
            ("A", 0, 0), ("B", 20, 0), ("C", 40, 0),
            ("D", 40, 20), ("E", 20, 20), ("F", 0, 20),
        ))
    ]
    edges = [
        ("W-S1", "A", "B", "EXT"), ("W-S2", "B", "C", "EXT"),
        ("W-E", "C", "D", "EXT"), ("W-N1", "D", "E", "EXT"),
        ("W-N2", "E", "F", "EXT"), ("W-W", "F", "A", "EXT"),
        ("W-MID", "B", "E", mid_assembly),
    ]
    walls = [
        Wall(uid=f"LW{i:08d}", tag=tag, start_node=start, end_node=end,
             assembly=assembly, top=ft(9))
        for i, (tag, start, end, assembly) in enumerate(edges)
    ]
    rooms = []
    if west_room is not None:
        rooms.append(west_room)
    if east_room is not None:
        rooms.append(east_room)
    return PlanModel(project=project, library=_library(), storeys=(storey,)).with_elements(
        "main", [*nodes, *walls, *rooms]
    )


def _west(**kwargs) -> Room:
    return Room(uid="LR00000001", tag="RM-WEST", seed=pt(ft(10), ft(10)),
                occupancy=Occupancy.LIVING, **kwargs)


def _east(**kwargs) -> Room:
    return Room(uid="LR00000002", tag="RM-EAST", seed=pt(ft(30), ft(10)),
                occupancy=Occupancy.LIVING, **kwargs)


def _innermost(model, wall_tag: str) -> str:
    wall = model.wall(wall_tag)
    assert wall is not None, wall_tag
    return wall.depth_layers()[0].material_ref


def _exception(wall_ref: str, lining=ACCENT_LINING) -> WallLiningException:
    return WallLiningException(uid=f"LX-{wall_ref}", tag=f"LX-{wall_ref}",
                               wall_ref=wall_ref, lining=lining)


# --- resolve-side behaviour ---------------------------------------------------------


def test_exception_reaches_the_resolved_walls_innermost_layer(project) -> None:
    plan = _plan(project, west_room=_west(
        wall_lining_exceptions=(_exception("W-W"),)))
    model, findings = resolve(plan)
    assert not [f for f in findings if "wall_lining" in f.check_id]
    assert _innermost(model, "W-W") == "paint-accent"
    # The rest of the room keeps the assembly default — the exception names ONE wall.
    for tag in ("W-S1", "W-N2", "W-MID"):
        assert _innermost(model, tag) == "paint", tag


def test_room_wide_lining_reaches_every_bounding_wall(project) -> None:
    plan = _plan(project, west_room=_west(wall_lining=ACCENT_LINING))
    model, findings = resolve(plan)
    assert not [f for f in findings if "wall_lining" in f.check_id]
    for tag in ("W-S1", "W-N2", "W-W", "W-MID"):
        assert _innermost(model, tag) == "paint-accent", tag
    # The east room did not opt in: its own walls are untouched.
    for tag in ("W-S2", "W-E", "W-N1"):
        assert _innermost(model, tag) == "paint", tag


def test_per_wall_exception_beats_the_room_wide_lining(project) -> None:
    bare_face = (_GWB,)  # exception: gypsum with no paint film at all
    plan = _plan(project, west_room=_west(
        wall_lining=ACCENT_LINING,
        wall_lining_exceptions=(_exception("W-W", bare_face),)))
    model, findings = resolve(plan)
    assert not [f for f in findings if "wall_lining" in f.check_id]
    assert _innermost(model, "W-W") == "gwb"
    assert _innermost(model, "W-S1") == "paint-accent"


def test_two_rooms_overriding_a_shared_wall_apply_neither_and_warn(project) -> None:
    plan = _plan(project,
                 west_room=_west(wall_lining=ACCENT_LINING),
                 east_room=_east(wall_lining=ACCENT_LINING))
    model, findings = resolve(plan)
    conflicts = [f for f in findings if f.check_id == "integrity.wall_lining_conflict"]
    assert len(conflicts) == 1
    assert conflicts[0].severity.value == "warn"
    assert set(conflicts[0].element_tags) == {"W-MID", "RM-WEST", "RM-EAST"}
    # The shared wall keeps its assembly default; each room's own walls still override.
    assert _innermost(model, "W-MID") == "paint"
    assert _innermost(model, "W-W") == "paint-accent"
    assert _innermost(model, "W-E") == "paint-accent"


def test_override_on_a_lining_less_assembly_warns_and_is_not_applied(project) -> None:
    plan = _plan(project, mid_assembly="BARE",
                 west_room=_west(wall_lining_exceptions=(_exception("W-MID"),)))
    model, findings = resolve(plan)
    unlined = [f for f in findings if f.check_id == "integrity.wall_lining_unlined"]
    assert len(unlined) == 1
    assert unlined[0].severity.value == "warn"
    assert "W-MID" in unlined[0].element_tags
    # Not applied: the bare partition still resolves stud-first.
    assert _innermost(model, "W-MID") == "spf"


def test_lining_inset_matches_the_overridden_stack(project) -> None:
    """``_lining_inset`` (the clear-face inset) and the resolved stack read the same
    override, so an accent room's floor area does not drift from its walls."""
    room = _west(wall_lining=ACCENT_LINING)
    plan = _plan(project, west_room=room)
    authored = next(e for e in plan.storey_elements("main") if e.element_kind == "Room")
    expected = sum(layer.thickness.meters for layer in ACCENT_LINING)
    assert _lining_inset(plan, authored) == pytest.approx(expected)
    # Same thickness as the default lining — swapping the colour moves no face.
    default = plan.library.resolve_assembly("EXT").default_lining
    assert expected == pytest.approx(sum(ly.thickness.meters for ly in default))


def test_override_map_is_plan_only_and_names_the_walls(project) -> None:
    plan = _plan(project, west_room=_west(wall_lining=ACCENT_LINING))
    overrides, findings = wall_lining_overrides(plan, "main")
    assert not findings
    assert sorted(overrides) == ["W-MID", "W-N2", "W-S1", "W-W"]
    assert all(lining == ACCENT_LINING for lining in overrides.values())


# --- glTF: authored colour reaches the .glb ----------------------------------------


def _hex_to_rgba(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)


def test_authored_paint_colours_round_trip_to_base_color_factor(project) -> None:
    from typehaus.emit.gltf import emit_gltf_dict

    plan = _plan(project, west_room=_west(
        wall_lining_exceptions=(_exception("W-W"),)))
    model, _findings = resolve(plan)
    gltf, _blob = emit_gltf_dict(model)
    factors = {tuple(round(v, 6) for v in material["pbrMetallicRoughness"]
               ["baseColorFactor"]) for material in gltf["materials"]}

    def rounded(color: str) -> tuple:
        return tuple(round(v, 6) for v in _hex_to_rgba(color))

    # The accent wall AND the ordinary walls both read their authored paint colour —
    # before authored-colour precedence the .glb guessed a family for every layer while
    # the viewer honoured the catalog, so the two disagreed (glb-emitter-parity).
    assert rounded("#2e4a44") in factors
    assert rounded("#f0ede6") in factors


def test_catlin_accent_and_latex_paint_reach_the_glb(catlin_model) -> None:
    """The real house: RM-S-BED1's feature wall (W-S-E2, storeys/second.py) ships the
    spruce accent, and every other painted wall ships latex-paint's authored off-white."""
    from typehaus.emit.gltf import emit_gltf_dict

    accent = next(m for m in catlin_model.plan.library.materials
                  if m.tag == "latex-paint-accent")
    base = next(m for m in catlin_model.plan.library.materials
                if m.tag == "latex-paint")
    assert base.color == "#f0ede6"  # the pinned library value this test reads back
    gltf, _blob = emit_gltf_dict(catlin_model)
    factors = {tuple(round(v, 6) for v in material["pbrMetallicRoughness"]
               ["baseColorFactor"]) for material in gltf["materials"]}
    for color in (accent.color, base.color):
        assert tuple(round(v, 6) for v in _hex_to_rgba(color)) in factors, color


# --- IFC: one IfcWallType per (assembly, resolved lining) ---------------------------


def test_overridden_wall_gets_its_own_ifc_wall_type(project, tmp_path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    plan = _plan(project, west_room=_west(
        wall_lining_exceptions=(_exception("W-W"),)))
    model, _findings = resolve(plan)
    out = tmp_path / "lining.ifc"
    emit_ifc(model, out, lod="core")
    f = ifcopenshell.open(str(out))

    wall_types = {wt.Name: wt for wt in f.by_type("IfcWallType")}
    # Two EXT variants: the unoverridden stack keeps the bare assembly name (GUID
    # stability for pre-override exports); the accent lining is a named variant.
    assert "EXT" in wall_types and "EXT~lining1" in wall_types

    def paint_material(name: str) -> set:
        layer_sets = [ls for ls in f.by_type("IfcMaterialLayerSet")
                      if ls.LayerSetName == name]
        assert len(layer_sets) == 1, name
        return {layer.Material.Name for layer in layer_sets[0].MaterialLayers
                if layer.Name == "paint"}

    assert paint_material("EXT") == {"paint"}
    assert paint_material("EXT~lining1") == {"paint-accent"}

    # Each wall occurrence is typed by the variant its resolved layers actually carry.
    typed = {occurrence.Name: relation.RelatingType.Name
             for relation in f.by_type("IfcRelDefinesByType")
             for occurrence in relation.RelatedObjects
             if relation.RelatingType.is_a("IfcWallType")}
    assert typed["W-W"] == "EXT~lining1"
    assert typed["W-S1"] == "EXT"
