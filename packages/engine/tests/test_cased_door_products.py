"""Small product fixtures pin the void contract, handing, finishes and export shapes."""
from dataclasses import asdict, replace
import json
from types import SimpleNamespace

import pytest

from typehaus.checks.integrity.door_finishes import door_material_ref
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.openings import _add_opening_filling
from typehaus.emit.gltf.palette import _color
from typehaus.model import DoorType, Material
from typehaus.quantities import m
from typehaus.resolve.door_product_spec import resolve_cased_door, resolve_door_products
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall
from typehaus.server.model_json_fabric import wall_graph_json


@pytest.fixture(scope="module")
def starter_model(starter_dir):
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    return resolve(load_plan(starter_dir).plan)[0]


@pytest.fixture
def product_fixture():
    wall = ResolvedWall(
        uid="wall", tag="W", storey="main", assembly="partition",
        axis=((0., 0.), (4., 0.)), z0_m=0., z1_m=3.,
        layers=(ResolvedLayer(name="stud", material_ref="spf", function="structure",
                              thickness_m=0.14,
                              polygon=((0., 0.), (4., 0.), (4., 0.14), (0., 0.14))),
                ResolvedLayer(name="finish", material_ref="paint", function="finish",
                              thickness_m=0.013,
                              polygon=((0., 0.14), (4., 0.14), (4., 0.153), (0., 0.153)))),)
    opening = ResolvedOpening(uid="door", tag="D", host_wall="W", type_ref="DT",
                              width_m=0.8128, height_m=2.032, sill_m=0., center_along_m=2.,
                              kind="door", is_door=True)
    door_type = DoorType(tag="DT", width=m(0.8128), height=m(2.032))
    return wall, opening, door_type


def _parts(wall, opening, door_type, **kwargs):
    spec = resolve_cased_door(wall, opening, door_type, **kwargs)
    assert spec is not None
    opening = replace(opening, cased_product=spec)
    return opening, {part.key: part for part in opening_parts(wall, opening, door_type.operation)}


def test_swing_has_real_jamb_and_stop_with_finished_floor_clearance(product_fixture):
    wall, opening, product = product_fixture
    standard = SimpleNamespace(jamb_allowance=m(0.028), reveal=m(0.005))
    resolved, parts = _parts(wall, opening, product, standard=standard,
                             finished_floors=(0.020, 0.035))
    spec = resolved.cased_product
    assert spec.jamb_allowance_m == 0.028
    assert spec.casing_reveal_m == 0.005
    assert len(parts["jamb_liner"].solids) == len(parts["stop"].solids) == 3
    leaf = parts["leaf"].solids[0]
    assert leaf.z0_m == pytest.approx(0.045)
    assert leaf.z1_m == pytest.approx(2.032 - 0.028 - 0.003)
    assert max(x for x, _ in leaf.ring) - min(x for x, _ in leaf.ring) == pytest.approx(
        opening.width_m - 2 * (0.028 + spec.leaf_gap_m))
    for solid in parts["jamb_liner"].solids:
        assert min(y for _, y in solid.ring) == pytest.approx(0.)
        assert max(y for _, y in solid.ring) == pytest.approx(0.153)
        assert not (solid.z0_m < 0.04 and min(x for x, _ in solid.ring) < 2
                    and max(x for x, _ in solid.ring) > 2)
    assert parts["jamb_liner"].material_key == parts["stop"].material_key == "door_frame"
    assert _color("door_frame") == _color("door_leaf")
    assert resolved.width_m == opening.width_m and resolved.height_m == opening.height_m


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("sign", [-1, 1])
def test_pocket_mouth_and_head_leave_a_slot_at_structural_center(product_fixture, reverse, sign):
    wall, opening, product = product_fixture
    if reverse:
        wall = replace(wall, axis=tuple(reversed(wall.axis)))
    opening = replace(opening, pocket_run_m=0.9, pocket_sign=sign)
    product = DoorType.model_validate({**product.model_dump(), "operation": "pocket"})
    resolved, parts = _parts(wall, opening, product)
    spec = resolved.cased_product
    assert len(parts["jamb_liner"].solids) == 5
    leaf = parts["leaf"].solids[0]
    assert sum(y for _, y in leaf.ring) / 4 == pytest.approx(0.07)
    assert parts["pocket_track"].material_key == "door_hardware"
    # No head/mouth board crosses the leaf's slot. Receiving jamb remains full-depth.
    assert sum(min(y for _, y in solid.ring) < 0.07 < max(y for _, y in solid.ring)
               for solid in parts["jamb_liner"].solids) == 1
    assert spec.finish_faces_m[1] - spec.finish_faces_m[0] == pytest.approx(0.153)
    head_solids = parts["jamb_liner"].solids[-2:]
    track = parts["pocket_track"].solids[0]
    assert all(board.z0_m <= track.z0_m + 1e-9 and board.z1_m >= track.z1_m - 1e-9
               for board in head_solids)
    assert leaf.z1_m < min(board.z0_m for board in head_solids)


@pytest.mark.parametrize("flip", [False, True])
def test_swing_leaf_and_stop_follow_handing(product_fixture, flip):
    wall, opening, product = product_fixture
    opening = replace(opening, flip_swing=flip, flip_hinge=flip)
    resolved, parts = _parts(wall, opening, product)
    leaf = parts["leaf"].solids[0]
    near = min(y for _, y in leaf.ring) if flip else max(y for _, y in leaf.ring)
    assert near == pytest.approx(0 if flip else 0.153)
    stop = parts["stop"].solids[0]
    assert (min(y for _, y in stop.ring) >= max(y for _, y in leaf.ring) - 1e-9 if flip
            else max(y for _, y in stop.ring) <= min(y for _, y in leaf.ring) + 1e-9)
    hardware = parts["hardware"].solids
    assert (sum(x for x, _ in hardware[0].ring) / 4 > 2) == flip


@pytest.mark.parametrize("update", [{"exterior": True}, {"trimless": True}, {"glazed": True},
                                    {"operation": "overhead"}])
def test_specialized_products_keep_their_geometry(product_fixture, update):
    wall, opening, product = product_fixture
    product = DoorType.model_validate({**product.model_dump(), **update})
    assert resolve_cased_door(wall, opening, product) is None


def test_raised_hatch_omits_unspecified_product_sill(product_fixture):
    wall, opening, product = product_fixture
    opening = replace(opening, sill_m=0.6)
    assert resolve_cased_door(wall, opening, product) is None
    parts = opening_parts(wall, opening, product.operation)
    assert len(parts[0].solids) == 3


def test_instance_finishes_inherit_independently_and_do_not_touch_casing(starter_model):
    from copy import deepcopy
    model = deepcopy(starter_model)
    plan = model.plan
    authored = plan.by_tag("D-201")
    product = next(p for p in plan.library.door_types if p.tag == authored.type_ref)
    updated_type = product.model_copy(update={"frame_material_ref": "type-frame",
                                              "leaf_material_ref": "type-leaf"})
    model.plan = plan.model_copy(update={"library": plan.library.model_copy(update={
        "door_types": tuple(updated_type if p.tag == product.tag else p
                            for p in plan.library.door_types)})})
    storey = next(key for key, items in plan.elements.items() if authored in items)
    model.plan = model.plan.with_elements(storey, [
        el.model_copy(update={"frame_material_ref": "instance-frame"}) if el.tag == authored.tag
        else el for el in model.plan.storey_elements(storey)])
    casings = tuple(model.door_casings)
    resolve_door_products(model)
    resolved = next(o for o in model.openings if o.tag == authored.tag)
    assert resolved.effective_frame_material_ref == "instance-frame"
    assert resolved.effective_leaf_material_ref == "type-leaf"
    second_authored = authored.model_copy(update={"tag": "D-PAIR", "uid": "DPAIRAAAAA"})
    model.plan = model.plan.with_elements(storey, [*model.plan.storey_elements(storey), second_authored])
    model.openings.append(replace(resolved, tag=second_authored.tag, uid=second_authored.uid))
    resolve_door_products(model)
    second = next(o for o in model.openings if o.tag == "D-PAIR")
    assert second.effective_frame_material_ref == "type-frame"
    assert second.effective_leaf_material_ref == "type-leaf"
    output = wall_graph_json(model, None)
    data = next(o for o in output["openings"] if o["tag"] == authored.tag)
    assert data["frame_material_ref"] == "instance-frame"
    assert data["leaf_material_ref"] is None
    assert data["effective_leaf_material_ref"] == "type-leaf"
    assert json.loads(json.dumps(data))["cased_product"] == json.loads(json.dumps(asdict(resolved.cased_product)))
    assert tuple(model.door_casings) == casings
    findings = door_material_ref(SimpleNamespace(plan=model.plan))
    assert {f.element_tags for f in findings} == {(authored.tag,), (product.tag,)}
    model.plan = model.plan.with_elements(storey, [
        el.model_copy(update={"frame_material_ref": None}) if el.tag == authored.tag
        else el for el in model.plan.storey_elements(storey)])
    resolve_door_products(model)
    reset = next(o for o in model.openings if o.tag == authored.tag)
    assert reset.frame_material_ref is None and reset.effective_frame_material_ref == "type-frame"
    assert next(o for o in model.openings if o.tag == "D-PAIR") == second


def test_explicit_catalog_colors_reach_glb_in_linear_light(product_fixture):
    wall, opening, product = product_fixture
    resolved, _ = _parts(wall, opening, product)
    resolved = replace(resolved, effective_frame_material_ref="paint-frame",
                       effective_leaf_material_ref="paint-leaf")
    materials = {ref: Material(tag=ref, name=ref, color=color) for ref, color in
                 (("paint-frame", "#808080"), ("paint-leaf", "#ff0000"))}
    parts = opening_parts(wall, resolved, product.operation)
    assert {p.key: p.catalog.material_ref for p in parts if p.catalog} == {
        "jamb_liner": "paint-frame", "stop": "paint-frame", "leaf": "paint-leaf"}
    surfaces = _add_opening_filling(_MeshBuilder(), wall, resolved, product.operation,
                                    authored=materials)
    gray = next(color for color in surfaces if color[0] == color[1] == color[2])
    assert gray[0] == pytest.approx(0.2158605)
    assert surfaces[gray] == (0.45, 0.)


def test_cased_ifc_uses_ir_parts_and_preserves_door_identity(starter_model, tmp_path):
    import ifcopenshell
    from typehaus.emit.ifc import emit_ifc
    path = tmp_path / "door.ifc"
    emit_ifc(starter_model, path, lod="core")
    document = ifcopenshell.open(str(path))
    opening = next(o for o in starter_model.openings if o.tag == "D-201")
    door = next(d for d in document.by_type("IfcDoor") if d.Name == opening.tag)
    parts = starter_model.geometry.by_uid(opening.uid).parts
    items = door.Representation.Representations[0].Items
    assert len(items) == sum(len(p.solids) for p in parts)
    assert all(item.StyledByItem for item in items)
    assert door.OverallWidth == opening.width_m and door.OverallHeight == opening.height_m
    assert door.FillsVoids and door.IsTypedBy
    assert {s.Name for s in document.by_type("IfcSurfaceStyle")} >= {
        "door_frame", "door_leaf", "door_hardware"}


def test_python_viewer_shared_fixture_pins_every_part(product_fixture):
    from pathlib import Path
    fixtures = json.loads((Path(__file__).resolve().parents[3]
                           / "ui/src/three/builders/casedDoorFixtures.json").read_text())
    wall, opening, product = product_fixture
    for fixture in fixtures:
        w = replace(wall, axis=tuple(tuple(p) for p in fixture["wall"]["axis"]))
        source = fixture["opening"]
        o = replace(opening, flip_swing=source["flip_swing"], flip_hinge=source["flip_hinge"],
                    pocket_run_m=source["pocket_run_m"], pocket_sign=source["pocket_sign"])
        dt = DoorType.model_validate({**product.model_dump(), "operation": fixture["operation"]})
        spec = resolve_cased_door(w, o, dt, finished_floors=(0.02, 0.035))
        assert json.loads(json.dumps(asdict(spec))) == source["cased_product"]
        parts = opening_parts(w, replace(o, cased_product=spec), dt.operation)
        boxes = [(part.key, part.material_key, solid) for part in parts for solid in part.solids]
        assert len(boxes) == len(fixture["boxes"])
        for (key, finish, solid), expected in zip(boxes, fixture["boxes"], strict=True):
            assert key == expected["part"] and finish == expected["finish"]
            points = [(x, z, -y) for x, y in solid.ring for z in (solid.z0_m, solid.z1_m)]
            bounds = [min(p[i] for p in points) for i in range(3)] + [
                max(p[i] for p in points) for i in range(3)]
            assert bounds == pytest.approx(expected["bounds"])


def test_resolver_reads_both_room_finished_floors(starter_model):
    from typehaus.resolve.room_floor import room_finished_floor_elevation
    opening = next(o for o in starter_model.openings if o.tag == "D-201")
    rooms = [r for r in starter_model.rooms if r.tag in {"RM-Upper", "RM-Upper-Hall"}]
    floors = [room_finished_floor_elevation(starter_model, r) for r in rooms]
    assert len(floors) == 2
    assert sorted(opening.cased_product.finished_floor_z_m) == pytest.approx(sorted(floors))
    assert opening.cased_product.leaf_bottom_z_m == pytest.approx(
        max(floors) + opening.cased_product.undercut_m)


def test_authored_finishes_reach_complete_glb_and_ifc_exports(starter_model, tmp_path):
    import ifcopenshell
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.emit.ifc import emit_ifc
    from typehaus.resolve import resolve
    plan = starter_model.plan
    storey = next(key for key, items in plan.elements.items() if any(el.tag == "D-201" for el in items))
    plan = plan.with_elements(storey, [
        el.model_copy(update={"frame_material_ref": "paint-gray", "leaf_material_ref": "paint-red"})
        if el.tag == "D-201" else el for el in plan.storey_elements(storey)])
    materials = (Material(tag="paint-gray", name="Gray satin", color="#808080"),
                 Material(tag="paint-red", name="Red satin", color="#ff0000"))
    plan = plan.model_copy(update={"library": plan.library.model_copy(update={
        "materials": (*plan.library.materials, *materials)})})
    model, _ = resolve(plan)
    assert model.walls == starter_model.walls
    assert model.door_casings == starter_model.door_casings
    assert not door_material_ref(SimpleNamespace(plan=plan))
    gltf, _ = emit_gltf_dict(model)
    opening = next(o for o in model.openings if o.tag == "D-201")
    node = next(n for n in gltf["nodes"] if n.get("extras", {}).get("uid") == opening.uid)
    finishes = [gltf["materials"][p["material"]]["pbrMetallicRoughness"]
                for p in gltf["meshes"][node["mesh"]]["primitives"]]
    assert any(p["baseColorFactor"] == pytest.approx([0.2158605] * 3 + [1.]) for p in finishes)
    assert any(p["baseColorFactor"] == [1., 0., 0., 1.] for p in finishes)
    path = tmp_path / "finished-door.ifc"
    emit_ifc(model, path, lod="core")
    document = ifcopenshell.open(str(path))
    styles = {s.Name: s for s in document.by_type("IfcSurfaceStyle")}
    gray = styles["paint-gray"].Styles[0].SurfaceColour
    assert (gray.Red, gray.Green, gray.Blue) == pytest.approx([128 / 255] * 3)
    assert "paint-red" in styles
