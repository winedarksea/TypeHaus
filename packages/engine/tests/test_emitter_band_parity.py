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

**CATLIN NO LONGER SUPPLIES A LIVE SUBJECT, and that is why the fixture below exists.**
``W-B-BRICK`` was the house's only multi-region ``slot`` wall, and on 2026-09-04 its Ishtar
banding collapsed to one flat unglazed field (``BASEMENT_BRICK_VENEER``). The ``Layer.slot``
machinery is untouched and any house may use it tomorrow, so the regression test is
retargeted rather than retired: ``_banded_model`` builds the smallest wall that can regress
this way — one wythe in three stacked regions sharing a slot, in three colours — and the
two house-wide sweeps still run over catlin, where they guard the *other* direction (an
emitter inventing parts for a wall that has no bands).
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.model import (
    Assembly,
    Building,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Slice,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.model.enums import SliceKind
from typehaus.resolve import resolve

_SLOT_WALL = "W-BANDED"
#: Three regions of one 3 5/8" wythe, bottom to top, each its own colour — the shape of the
#: Ishtar wall that regressed, cut to the smallest thing that still has a middle band to drop.
_VENEER_REGIONS = ("brick-plinth", "brick-band", "brick-field")
_WYTHE = inch(3.625)


def _banded_plan() -> PlanModel:
    project = Project(
        name="Banded", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000d1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Banded"))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))

    def region(name: str, material: str, bottom: float, top: float | None) -> Layer:
        extent = LayerExtent(
            bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(bottom)),
            top=None if top is None
            else LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(top)))
        return Layer(name=name, material_ref=material, thickness=_WYTHE,
                     function=LayerFunction.STRUCTURE, slot="wythe", extent=extent)

    banded = Assembly(tag="BANDED", layers=(
        Layer(name="air-gap", material_ref="air", thickness=inch(1.5),
              function=LayerFunction.AIRGAP),
        # Each region is a DIFFERENT material, because the glTF assertion counts distinct
        # colours: three regions of one colour would collapse to one primitive and the test
        # would pass with two of them dropped.
        region("brick-plinth", "brick-a", 0.0, 32.0),
        region("brick-band", "brick-b", 32.0, 37.333),
        # `top=None` is the wall's own top — the open-topped region the real wall carried.
        region("brick-field", "brick-c", 37.333, None),
    ))
    plain = Assembly(tag="PLAIN", layers=(
        Layer(name="concrete", material_ref="brick-a", thickness=inch(8),
              function=LayerFunction.STRUCTURE),))

    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = (
        Wall(uid="W000000001", tag=_SLOT_WALL, start_node="N-1", end_node="N-2",
             assembly="BANDED", top=ft(8, 5)),
        # An unbanded neighbour, so the sweeps have something to be right about in both
        # directions within the fixture itself.
        Wall(uid="W000000002", tag="W-PLAIN", start_node="N-2", end_node="N-3",
             assembly="PLAIN", top=ft(8, 5)),
    )
    # A transverse cut through W-BANDED at x=10', so the section draws the wythe in
    # elevation-order and a dropped region is visible as a missing course. The crop is in
    # the CUT PLANE — (along-cut, elevation), not plan x/y — so it is ±4' either side of the
    # wall at y=0 and -4'..12' vertically, the way SL-D-WALLTYP crops catlin's wall section.
    cut = Slice(uid="SL00000001", tag="SL-BANDED", kind=SliceKind.DETAIL,
                title="Banded wythe", cut_origin=pt(ft(10), ft(0)), cut_direction="y",
                crop=(pt(ft(-4), ft(-4)), pt(ft(4), ft(12))))
    plan = PlanModel(project=project, library=Library(
        materials=(
            Material(tag="air", name="Air", r_per_inch=0.0),
            Material(tag="brick-a", name="Brick A", r_per_inch=0.2, color="#a07c5c"),
            Material(tag="brick-b", name="Brick B", r_per_inch=0.2, color="#c08a12"),
            Material(tag="brick-c", name="Brick C", r_per_inch=0.2, color="#10386a"),
        ),
        assemblies=(banded, plain)), storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, cut))


@pytest.fixture(scope="module")
def banded_model():
    model, _findings = resolve(_banded_plan())
    return model


@pytest.fixture(scope="module")
def banded_ifc(banded_model, tmp_path_factory):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    out = tmp_path_factory.mktemp("banded-ifc") / "banded.ifc"
    return ifcopenshell.open(str(emit_ifc(banded_model, out)))


def _banded_part_names(wall, openings=()) -> set[str]:
    """The ``IfcBuildingElementPart`` names ``_emit_banded_layer_parts`` owes this wall.

    A banded layer is cut around the openings in its own wall, so a layer crossing a door
    or window owes one part per surviving region rather than one part. ``layer_solids`` is
    the same call the emitter makes — the point of this test is that the IFC agrees with
    the geometry, so restating the split here instead of asking for it would only pin the
    restatement. That is why ``layer_name`` is passed: a BLIND opening cuts only the layers
    its depth reaches, and asking without the name would expect a hydrant bore to split the
    gypsum it deliberately stops short of.
    """
    from typehaus.resolve.geometry_walls import layer_solids
    from typehaus.resolve.layer_bands import wall_body_band

    body = wall_body_band(wall)
    names = set()
    for layer in wall.body_layers():
        if not layer.is_banded or len(layer.polygon) < 3:
            continue
        z0, z1 = layer.band(wall)
        # A layer standing at the wall's own body band is IN the body prism, not a part —
        # the same predicate ``_emit_wall`` uses. Every layer of a platform-trimmed
        # partition is one of those, which is why trimming adds no parts.
        if abs(z0 - body[0]) <= 1e-9 and abs(z1 - body[1]) <= 1e-9:
            continue
        if z1 - z0 <= 1e-9:
            continue
        pieces = [p for p in layer_solids(wall, layer.polygon, openings, band=(z0, z1),
                                          layer_name=layer.name)
                  if getattr(p, "ring", None) is not None and len(p.ring) >= 3]
        if len(pieces) == 1:
            names.add(f"{wall.tag}:{layer.name}")
            continue
        for index in range(len(pieces)):
            names.add(f"{wall.tag}:{layer.name} ({index + 1}/{len(pieces)})")
    return names


@pytest.fixture(scope="module")
def catlin_ifc(catlin_ifc_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    return ifcopenshell.open(str(catlin_ifc_path))


def test_every_wall_exports_one_ifc_part_per_banded_body_layer_region(catlin_model_ro,
                                                                      catlin_ifc):
    """Wall by wall, over the whole house — not just the one that regressed.

    Per REGION, not per layer: a banded layer crossing an opening is several parts, because
    the opening goes through the part the same way it goes through the wall.
    """
    parts_by_parent: dict[str, set[str]] = {}
    for rel in catlin_ifc.by_type("IfcRelAggregates"):
        parent = rel.RelatingObject
        if not parent.is_a("IfcWall"):
            continue
        for child in rel.RelatedObjects or ():
            if child.is_a("IfcBuildingElementPart"):
                parts_by_parent.setdefault(parent.Name, set()).add(child.Name)

    by_wall: dict[str, list] = {}
    for opening in catlin_model_ro.openings:
        by_wall.setdefault(opening.host_wall, []).append(opening)

    mismatches = []
    for wall in catlin_model_ro.walls:
        expected = _banded_part_names(wall, by_wall.get(wall.tag, ()))
        actual = parts_by_parent.get(wall.tag, set())
        if expected != actual:
            mismatches.append((wall.tag, sorted(expected - actual), sorted(actual - expected)))
    assert not mismatches, mismatches


def test_the_sauna_liner_no_longer_runs_across_its_own_door_and_window(catlin_model_ro,
                                                                      catlin_ifc):
    """The defect, named and counted.

    Six of catlin's 47 banded layers overlap an opening, and all six are the sauna liner:
    ``shiplap-liner``, ``liner-furring`` and ``foil-polyiso`` on ``W-B-S2-FR`` (a window,
    4 regions) and ``W-B-CS`` (a door, 3 regions — no sill strip, because a door has no
    sill). Every one of them used to extrude straight across the hole.
    """
    names = {p.Name for p in catlin_ifc.by_type("IfcBuildingElementPart")}
    for layer in ("shiplap-liner", "liner-furring", "foil-polyiso"):
        assert f"W-B-S2-FR:{layer}" not in names, "the unsplit part must be gone"
        assert {n for n in names if n.startswith(f"W-B-S2-FR:{layer} (")} == {
            f"W-B-S2-FR:{layer} ({i}/4)" for i in range(1, 5)}
        assert {n for n in names if n.startswith(f"W-B-CS:{layer} (")} == {
            f"W-B-CS:{layer} ({i}/3)" for i in range(1, 4)}


def test_an_unsplit_banded_layer_keeps_its_globalid(catlin_model_ro, catlin_ifc):
    """53 of the 59 do not split, and their GUIDs must not move because the call changed.

    47 since 2026-09-16: W-SG-W1/E1's dimpleboard stops at grade. 61 since the platform
    trim (``layer_bands.clamp_to_plates``): a lifted or dropped ENVELOPE wall's interior
    finish stops at the plate while its skin runs the rim band, so the finish is now a part
    too. None of the 41 original keys moved — this count grew, it did not shift. 59 since
    2026-09-23: the ICF grade beam under D-G-OVERHEAD is retired, and W-GF-N-DR's two coil
    layers went with the wall.

    A GlobalId is an identity a federated model and its issue log hold onto. Re-keying a
    part that still means exactly what it meant before would break those references for
    nothing — so only a layer that genuinely becomes several parts takes indexed keys.
    """
    from typehaus.model.ids import derive_child_guid

    project_uuid = catlin_model_ro.plan.project.project_uuid
    parts = {p.Name: p.GlobalId for p in catlin_ifc.by_type("IfcBuildingElementPart")}
    unsplit = [(w, ly) for w in catlin_model_ro.walls for ly in w.body_layers()
               if f"{w.tag}:{ly.name}" in parts]
    assert len(unsplit) == 53, \
        f"expected the 59 banded layers less the 6 that split, got {len(unsplit)}"
    for wall, layer in unsplit:
        assert parts[f"{wall.tag}:{layer.name}"] == derive_child_guid(
            project_uuid, "wall-parts", f"{wall.uid}/{layer.name}")


def test_the_split_wythe_exports_every_region_not_just_the_bottom_one(banded_model,
                                                                      banded_ifc):
    """The regression itself, named. ``depth_layers()`` here shipped the bottom region alone.

    The two lists are asserted side by side on purpose: ``depth_layers()`` returning one
    brick layer is CORRECT — it is what keeps the wall 3 5/8" thick instead of 10 7/8" — and
    the bug was never in that method. It was in reading it from the emitters.
    """
    wall = banded_model.wall(_SLOT_WALL)
    assert [ly.name for ly in wall.depth_layers()] == ["air-gap", "brick-plinth"]
    assert [ly.name for ly in wall.body_layers()] == ["air-gap", *_VENEER_REGIONS]
    assert wall.thickness_m == pytest.approx(inch(1.5).meters + _WYTHE.meters)

    parts = {p.Name: p for p in banded_ifc.by_type("IfcBuildingElementPart")}
    assert {n for n in parts if n.startswith(f"{_SLOT_WALL}:")} == {
        f"{_SLOT_WALL}:{name}" for name in _VENEER_REGIONS}


def test_the_banded_walls_glb_node_carries_one_bucket_per_region(banded_model):
    """The glTF half of the same regression, on the fixture that still has bands.

    The house-wide sweep below cannot see this any more: with no multi-region wall left in
    catlin, every wall's body layers and depth layers agree and a dropped region has nothing
    to drop. Three colours over one strip is what makes the count meaningful.
    """
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.emit.gltf.palette import _layer_color, authored_colors

    gltf, _blob = emit_gltf_dict(banded_model)
    authored = authored_colors(banded_model)
    wall = banded_model.wall(_SLOT_WALL)
    node = next(n for n in gltf["nodes"]
                if n.get("extras", {}).get("uid") == wall.uid
                and n["extras"].get("trades") != ["framing"])
    expected = {_layer_color(ly, authored) for ly in wall.body_layers() if ly.polygon}
    assert len(expected) >= 3, "the fixture must keep its regions in distinct colours"
    assert len(gltf["meshes"][node["mesh"]]["primitives"]) == len(expected)


def test_the_glb_draws_every_body_layer_of_every_wall(catlin_model_ro):
    """glTF buckets its primitives by colour, so the count a wall's node carries is the
    number of *distinct* colours among the layers drawn — which is exactly what a dropped
    layer changes when it is a colour of its own. The Ishtar wythe was four colours over one
    strip (brown plinth, two gold registers, two lapis fields), so reading ``depth_layers()``
    here cost the node two of its four buckets; the banded fixture above keeps that case
    alive. Over catlin this now guards the other direction — that every wall's body layers
    reach the glTF, banded or not.
    """
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.emit.gltf.members import member_color
    from typehaus.emit.gltf.palette import _layer_color, authored_colors

    gltf, _blob = emit_gltf_dict(catlin_model_ro)
    authored = authored_colors(catlin_model_ro)
    # A wall emits two nodes with one uid — its body and, at the framed LOD, its members —
    # so the trade set is what picks the body out: the members are exactly ("framing",).
    nodes = {n["extras"]["uid"]: n for n in gltf["nodes"]
             if n.get("extras", {}).get("kind") == "wall"
             and n["extras"].get("trades") != ["framing"]
             and "facet" not in n["extras"]}  # a wall's rebar is its own facet node
    # The body node also carries the wall's closure bands: the roof resolves them (only the
    # roof planes say how high each layer climbs) but they are this wall's own skin carried
    # past the top plate, and they draw with the wall so the walls toggle keeps them. Their
    # colours join the expected set — a standing-seam band is white metal, not a layer colour.
    closures: dict[str, list] = {}
    for roof in catlin_model_ro.roofs:
        for member in roof.members:
            if member.parent_uid != roof.uid:
                closures.setdefault(member.parent_uid, []).append(member)

    mismatches = []
    for wall in catlin_model_ro.walls:
        node = nodes.get(wall.uid)
        if node is None or "mesh" not in node:
            continue
        expected = {_layer_color(ly, authored) for ly in wall.body_layers() if ly.polygon}
        expected |= {member_color(m) for m in closures.get(wall.uid, ())}
        actual = len(gltf["meshes"][node["mesh"]]["primitives"])
        if actual != len(expected):
            mismatches.append((wall.tag, len(expected), actual))
    assert not mismatches, mismatches


def test_every_slot_region_of_a_banded_wythe_draws_in_section(banded_model):
    """The third emitter. A plinth, a band and a field are one 3 5/8" wythe — and three
    courses of brick.

    They share a ``Layer.slot``, so ``depth_layers()`` counts them once; building section
    bodies from that list left the plinth standing with nothing above it. This lived on
    catlin's ``W-B-BRICK`` (test_section_from_ir.py) until 2026-09-04 took the banding off
    that wall, and follows the same fixture as the two emitter assertions above rather than
    being retired with its subject.
    """
    from typehaus.emit.draw.scene import Polyline
    from typehaus.emit.draw.section import build_section

    cut = next(s for s in banded_model.plan.elements_of_kind("Slice")
               if s.tag == "SL-BANDED")
    scene = build_section(banded_model, cut)
    drawn = {node.tag.split("/")[-1] for node in scene.nodes
             if isinstance(node, Polyline) and node.layer == "A-WALL" and node.tag
             and node.tag.startswith(f"{_SLOT_WALL}/")}
    assert set(_VENEER_REGIONS) <= drawn, drawn


# --- the platform trim, through the emitter ----------------------------------------------
#
# ``layer_bands.clamp_to_plates`` stops a lifted wall's interior finish at the top plate and
# a lifted PARTITION's whole body there. Both are instance facts about one wall, not recipes
# the ``Assembly`` stated — which is the whole reason ``_full_height_layers`` keys off
# ``band_spec`` rather than ``is_banded``. Get that wrong and a lifted partition exports an
# ``IfcShapeRepresentation`` with no ``Items`` (invalid IFC4: ``Items`` is ``SET [1:?]``),
# while every lifted ``EXT_2X6`` exports as a lining variant that is not a lining.

_LIFTED_PARTITION = "W-B-CS3"   # INT_2X6_BRG, lifted, no authored band anywhere on it
_LIFTED_ENVELOPE = "W-M-E1"     # EXT_2X6, lifted AND dropped, no lining override


def _wall(ifc, tag):
    return next(w for w in ifc.by_type("IfcWall") if w.Name == tag)


def _parts_of(ifc, tag) -> set[str]:
    return {child.Name for rel in ifc.by_type("IfcRelAggregates")
            if rel.RelatingObject.Name == tag
            for child in (rel.RelatedObjects or ())
            if child.is_a("IfcBuildingElementPart")}


def test_a_lifted_partition_exports_one_shortened_body_and_no_parts(catlin_model_ro,
                                                                    catlin_ifc):
    wall = catlin_model_ro.wall(_LIFTED_PARTITION)
    assert wall.plate_top_z_m is not None, f"{_LIFTED_PARTITION} is no longer lifted"
    assert all(ly.band(wall)[1] == pytest.approx(wall.plate_top_z_m)
               for ly in wall.body_layers()), "the whole body should stop at the plate"

    assert _parts_of(catlin_ifc, _LIFTED_PARTITION) == set()
    body = next(rep for rep in _wall(catlin_ifc, _LIFTED_PARTITION)
                .Representation.Representations
                if rep.RepresentationIdentifier == "Body")
    assert len(body.Items) == len(wall.depth_layers())
    # The body really is shorter than the wall — the joist bay above it is open.
    depth = body.Items[0].Depth
    assert depth == pytest.approx(wall.plate_top_z_m - wall.z0_m, abs=1e-9)
    assert depth < wall.z1_m - wall.z0_m - 1e-3

    # And the layer set is still complete: an instance trim is not a ``Layer.extent``, so
    # the wall type keeps every layer and still sums to the wall's depth.
    layer_set = next(rel.RelatingMaterial.ForLayerSet
                     for rel in catlin_ifc.by_type("IfcRelAssociatesMaterial")
                     if _wall(catlin_ifc, _LIFTED_PARTITION) in rel.RelatedObjects
                     and rel.RelatingMaterial.is_a("IfcMaterialLayerSetUsage"))
    assert [ly.Name for ly in layer_set.MaterialLayers] == \
        [ly.name for ly in wall.depth_layers()]
    assert sum(ly.LayerThickness for ly in layer_set.MaterialLayers) == \
        pytest.approx(wall.thickness_m, abs=1e-6)


def test_a_lifted_envelope_wall_exports_its_interior_finishes_as_parts(catlin_model_ro,
                                                                       catlin_ifc):
    """The counterpart: the skin still laps the rim, so the body is full height and it is
    the two interior finishes that drop out of it — as parts, cut around the openings the
    way every part is. The TYPE is untouched, which is the assertion that matters: 28 lifted
    EXT_2X6 walls on one ``IfcWallType``, not 28 ``~lining0`` variants."""
    wall = catlin_model_ro.wall(_LIFTED_ENVELOPE)
    trimmed = [ly.name for ly in wall.depth_layers()
               if ly.band(wall) != (wall.z0_m, wall.z1_m)]
    assert trimmed == ["paint", "gwb-int"]

    parts = _parts_of(catlin_ifc, _LIFTED_ENVELOPE)
    assert parts, "the trimmed finishes must still reach the IFC somewhere"
    assert {name.split(":")[1].split(" (")[0] for name in parts} == set(trimmed)

    wall_type = next(iter(_wall(catlin_ifc, _LIFTED_ENVELOPE).IsTypedBy)).RelatingType
    assert wall_type.Name == "EXT_2X6"
    # House-wide: a ``~lining`` suffix on a lifted EXT_2X6 wall means a real
    # ``Room.wall_lining`` override, never the trim. 14 of the 28 have no override at all
    # and every one of them is on the bare type.
    lifted = [w for w in catlin_model_ro.walls
              if w.assembly == "EXT_2X6" and w.plate_top_z_m is not None]
    assert len(lifted) == 28
    bare = [w for w in lifted
            if next(iter(_wall(catlin_ifc, w.tag).IsTypedBy)).RelatingType.Name
            == "EXT_2X6"]
    assert len(bare) == 14
