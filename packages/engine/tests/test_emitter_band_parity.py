"""The exports and the IR must agree about how many solids a wall has.

``ResolvedWall`` publishes two layer lists and the distinction is easy to get wrong.
``depth_layers()`` counts a ``Layer.slot``'s regions **once**, because a brown plinth and a
lapis field are one 3 5/8" wythe and charging the wall for both stands 18 1/8" of brick
where 3 5/8" is built. ``body_layers()`` counts them **all**, because each is a real course
at its own elevation.

``geometry_build`` was fixed to read the second; both emitters were still reading the first,
so ``W-B-BRICK`` exported as its brick plinth and nothing above it — four of five regions
absent from IFC *and* glTF. ``test_geometry_ir_parity`` could not see it: it compares the IR
against itself, never against emitter output. This module is the missing side of that
comparison.
"""

from __future__ import annotations

import pytest

_SLOT_WALL = "W-B-BRICK"
_VENEER_REGIONS = ("brick-plinth", "brick-band-lo", "brick-field-lo",
                   "brick-band-hi", "brick-field-hi")


def _banded_part_names(wall) -> set[str]:
    """The ``IfcBuildingElementPart`` names ``_emit_banded_layer_parts`` owes this wall."""
    names = set()
    for layer in wall.body_layers():
        if not layer.is_banded or len(layer.polygon) < 3:
            continue
        z0, z1 = layer.band(wall)
        if z1 - z0 <= 1e-9:
            continue
        names.add(f"{wall.tag}:{layer.name}")
    return names


@pytest.fixture(scope="module")
def catlin_ifc(catlin_model, tmp_path_factory):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    path = emit_ifc(catlin_model, tmp_path_factory.mktemp("parity") / "catlin.ifc")
    return ifcopenshell.open(str(path))


def test_every_wall_exports_one_ifc_part_per_banded_body_layer(catlin_model, catlin_ifc):
    """Wall by wall, over the whole house — not just the one that regressed."""
    parts_by_parent: dict[str, set[str]] = {}
    for rel in catlin_ifc.by_type("IfcRelAggregates"):
        parent = rel.RelatingObject
        if not parent.is_a("IfcWall"):
            continue
        for child in rel.RelatedObjects or ():
            if child.is_a("IfcBuildingElementPart"):
                parts_by_parent.setdefault(parent.Name, set()).add(child.Name)

    mismatches = []
    for wall in catlin_model.walls:
        expected = _banded_part_names(wall)
        actual = parts_by_parent.get(wall.tag, set())
        if expected != actual:
            mismatches.append((wall.tag, sorted(expected - actual), sorted(actual - expected)))
    assert not mismatches, mismatches


def test_the_split_wythe_exports_all_five_regions_not_just_the_plinth(catlin_model,
                                                                     catlin_ifc):
    """The regression itself, named. ``depth_layers()`` here shipped the plinth alone."""
    wall = catlin_model.wall(_SLOT_WALL)
    assert [ly.name for ly in wall.depth_layers()] == ["air-gap", "brick-plinth"]
    assert [ly.name for ly in wall.body_layers()] == ["air-gap", *_VENEER_REGIONS]

    parts = {p.Name: p for p in catlin_ifc.by_type("IfcBuildingElementPart")}
    assert {n for n in parts if n.startswith(f"{_SLOT_WALL}:")} == {
        f"{_SLOT_WALL}:{name}" for name in _VENEER_REGIONS}


def test_the_glb_draws_every_body_layer_of_every_wall(catlin_model):
    """glTF buckets its primitives by colour, so the count a wall's node carries is the
    number of *distinct* colours among the layers drawn — which is exactly what a dropped
    layer changes when it is a colour of its own. The Ishtar wythe is four colours over one
    strip (brown plinth, two gold registers, two lapis fields), so reading ``depth_layers()``
    here cost the node two of its four buckets.
    """
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.emit.gltf.palette import _layer_color, authored_colors

    gltf, _blob = emit_gltf_dict(catlin_model)
    authored = authored_colors(catlin_model)
    # A wall emits two nodes with one uid — its body and, at the framed LOD, its members —
    # so the trade is what picks the body out.
    nodes = {n["extras"]["uid"]: n for n in gltf["nodes"]
             if n.get("extras", {}).get("kind") == "wall"
             and n["extras"].get("trade") == "walls"}

    mismatches = []
    for wall in catlin_model.walls:
        node = nodes.get(wall.uid)
        if node is None or "mesh" not in node:
            continue
        expected = {_layer_color(ly, authored) for ly in wall.body_layers() if ly.polygon}
        actual = len(gltf["meshes"][node["mesh"]]["primitives"])
        if actual != len(expected):
            mismatches.append((wall.tag, len(expected), actual))
    assert not mismatches, mismatches
