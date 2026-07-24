"""WP2.4b/#33/#51 — room macros, mutation remap, and glTF emission (→ 20, → 21b).

Covers the server-dependent write flows the read/edit seam was already wired for: wall-draw
add ops, split/heal with the reference-remap contract, the ``/macro`` endpoint riding the
standard journal (undo byte-identical), and the self-contained ``.glb`` artifact.
"""

from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

import pytest

from typehaus.emit.gltf import emit_glb, emit_gltf_dict
from typehaus.model.elements import RoughOpening
from typehaus.model.refs import from_node
from typehaus.quantities import ft
from typehaus.model.remap import ReferenceRemap, registered_ref_fields, remap_ops_for
from typehaus.resolve import resolve
from typehaus.source import load_plan, macros


@pytest.fixture
def plan(starter_dir: Path):
    result = load_plan(starter_dir)
    assert result.plan is not None
    return result.plan


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    dst = tmp_path / "starter"
    shutil.copytree(starter_dir, dst)
    return dst


@pytest.fixture
def client(house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(house)) as c:
        yield c, house


# --- wall-draw ---------------------------------------------------------------

def test_draw_wall_snaps_to_existing_node(plan):
    # Starting on N-1 (at the origin) should reuse it, not mint a duplicate node.
    result = macros.draw_wall(plan, "main", ("0'", "0'"), ("10'", "0'"), "INT_2X4")
    adds_node = [o for o in result.ops if o.op == "add" and o.type == "Node"]
    wall = next(o for o in result.ops if o.type == "Wall")
    assert len(adds_node) == 1  # only the free end got a new node
    assert wall.fields["start_node"] == "N-1"
    assert wall.fields["end_node"] == adds_node[0].tag


def test_draw_wall_degenerate_rejected(plan):
    with pytest.raises(macros.MacroError):
        macros.draw_wall(plan, "main", ("0'", "0'"), ("0'", "0'"), "INT_2X4")


# --- move / stretch ----------------------------------------------------------

def test_move_nodes_translates_each(plan):
    result = macros.move_nodes(plan, "main", ["N-1", "N-2"], "1'", "0'")
    assert {o.tag for o in result.ops} == {"N-1", "N-2"}
    assert all(o.op == "update" for o in result.ops)


def test_move_opening_rewrites_structured_position_on_its_current_host(plan):
    result = macros.move_opening(plan, "main", tag="D-101", along="5'")
    (op,) = result.ops
    assert op.type == "Door" and op.tag == "D-101"
    assert op.fields["position"].expr == 'from_node("N-1", ft(5))'


def test_move_opening_rejects_wrong_storey(plan):
    with pytest.raises(macros.MacroError):
        macros.move_opening(plan, "upper", tag="D-101", along="5'")


def test_move_opening_rejects_a_station_that_does_not_fit_the_host(plan):
    with pytest.raises(macros.MacroError, match="does not fit"):
        macros.move_opening(plan, "main", tag="D-101", along="100'")


def test_place_opening_rejects_an_overlapping_host_station(plan):
    with pytest.raises(macros.MacroError, match="conflicts"):
        macros.place_opening(plan, "main", host="W-101", type_ref="DT-EXT36",
                             along="5'", is_door=True)


def test_duplicate_opening_finds_a_non_overlapping_station(plan):
    (op,) = macros.duplicate_canvas_object(plan, "main", tag="D-101").ops
    assert (op.op, op.type, op.tag) == ("add", "Door", "D-101-COPY")


def test_duplicate_rough_opening_keeps_its_unfilled_opening_semantics(plan):
    original = next(item for item in plan.storey_elements("main") if item.tag == "D-101")
    rough = RoughOpening(uid=original.uid, tag="RO-1", host=original.host,
                         position=from_node("N-1", ft(5)), width=ft(2), height=ft(6), sill_height=ft(0))
    copied_plan = plan.model_copy(update={
        "elements": {**plan.elements, "main": tuple(
            rough if item.tag == original.tag else item for item in plan.storey_elements("main")
        )},
    })
    (op,) = macros.duplicate_canvas_object(copied_plan, "main", tag="RO-1").ops
    assert (op.op, op.type, op.tag, op.hint_list) == ("add", "RoughOpening", "RO-1-COPY", "OPENINGS")


def test_place_rough_opening_uses_the_shared_host_validation(plan):
    (op,) = macros.place_rough_opening(plan, "main", host="W-101", width="2'", height="6'",
                                       along="12'", tag="RO-NEW").ops
    assert (op.op, op.type, op.tag, op.hint_list) == ("add", "RoughOpening", "RO-NEW", "OPENINGS")


# --- split + remap -----------------------------------------------------------

def test_split_keeps_survivor_and_adds_segment(plan):
    result = macros.split_wall(plan, "main", "W-101", ("5'", "0'"))
    kinds = [(o.op, o.type, o.tag) for o in result.ops]
    assert ("add", "Node", result.ops[0].tag) in kinds
    assert ("update", "Wall", "W-101") in kinds  # original survives (a-side, #33)
    assert any(o.op == "add" and o.type == "Wall" for o in result.ops)


def test_split_missing_wall_rejected(plan):
    with pytest.raises(macros.MacroError):
        macros.split_wall(plan, "main", "NOPE", ("5'", "0'"))


# --- remap registry ----------------------------------------------------------

def test_remap_registry_covers_reference_fields():
    fields = registered_ref_fields()
    assert "start_node" in fields["Wall"] and "end_node" in fields["Wall"]
    assert fields["Door"] == ("host",)


def test_remap_rewrites_wall_node_ref(plan):
    wall = next(e for e in plan.storey_elements("main") if type(e).__name__ == "Wall")
    remap = ReferenceRemap(renamed={wall.start_node: "N-99"})
    ops = remap_ops_for(wall, remap)
    assert ops and ops[0].fields["start_node"] == "N-99"


# --- /macro endpoint end-to-end ---------------------------------------------

def test_macro_endpoint_draw_and_undo_byte_identical(client):
    c, house = client
    storey_file = next((house / "plan" / "storeys").glob("*.py"))
    before = storey_file.read_text()
    rev = c.get("/model").json()["revision"]
    resp = c.post("/macro", json={
        "macro": "draw_wall", "storey": "main", "revision": rev,
        "start": ["20'", "0'"], "end": ["20'", "12'"], "assembly": "INT_2X4",
    })
    assert resp.status_code == 200, resp.json()
    assert resp.json()["minted"]
    assert c.post("/undo").status_code == 200
    assert storey_file.read_text() == before


def test_macro_endpoint_unknown_is_400(client):
    c, _ = client
    resp = c.post("/macro", json={"macro": "teleport", "storey": "main"})
    assert resp.status_code == 400


def test_macro_endpoint_stale_revision_409(client):
    c, _ = client
    resp = c.post("/macro", json={
        "macro": "draw_wall", "storey": "main", "revision": "STALE",
        "start": ["20'", "0'"], "end": ["20'", "12'"], "assembly": "INT_2X4",
    })
    assert resp.status_code == 409


# --- glTF --------------------------------------------------------------------

def test_emit_glb_is_valid_container(plan, tmp_path):
    model, _ = resolve(plan)
    out = emit_glb(model, tmp_path / "model.glb")
    data = out.read_bytes()
    magic, version, length = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67 and version == 2 and length == len(data)
    json_len, json_type = struct.unpack("<II", data[12:20])
    assert json_type == 0x4E4F534A  # "JSON"
    doc = json.loads(data[20:20 + json_len])
    assert doc["asset"]["version"] == "2.0"
    assert doc["meshes"] and doc["accessors"]


def test_emit_gltf_dict_buffer_matches_blob(plan):
    model, _ = resolve(plan)
    gltf, blob = emit_gltf_dict(model)
    assert gltf["buffers"][0]["byteLength"] == len(blob)


def test_glb_endpoint_serves_binary(client):
    c, _ = client
    resp = c.get("/model.glb")
    assert resp.status_code == 200
    assert resp.content[:4] == b"glTF"


# The 12 visibility trades the UI honours (ui/src/state/store.ts ALL_TRADES). A whole-house glb
# is only promoted to the primary scene when every node classifies to one of these.
_ALL_TRADES = {
    "walls", "openings", "framing", "floors", "concrete", "roof",
    "stairs", "furniture", "plumbing", "electrical", "mechanical", "earth",
}


def test_emit_gltf_dict_emits_per_object_nodes_with_trade_extras(plan):
    """Per-object identity (U1): one node per source object, each tagged so the 3D UI can
    promote the whole-house glb to the primary scene (see Panel3D.wholeHouseGlbAssignment)."""
    model, _ = resolve(plan)
    gltf, _blob = emit_gltf_dict(model)

    nodes = gltf["nodes"]
    assert len(nodes) > 1, "the emitter must emit per-object nodes, not one 'building' node"

    for node in nodes:
        extras = node.get("extras")
        assert extras is not None, f"every node needs extras: {node.get('name')}"
        assert extras["trade"] in _ALL_TRADES, f"trade must be an allowlisted token: {extras}"
        assert extras.get("kind") in (None, "wall", "canvas_object")
        # The node name mirrors extras as a "<trade>|<kind|>|<uid|>" fallback.
        assert node["name"].split("|")[0] == extras["trade"]

    # A wall carries its selection kind + uid, so the glb stays pickable and highlightable.
    wall_nodes = [n for n in nodes if n["extras"].get("kind") == "wall"]
    assert wall_nodes, "expected at least one selectable wall node"
    wall = wall_nodes[0]
    assert wall["extras"]["trade"] == "walls"
    assert wall["extras"]["uid"]
    assert wall["name"].split("|") == ["walls", "wall", wall["extras"]["uid"]]


def test_emit_gltf_dict_emits_canvas_object_nodes(plan):
    """A resolved canvas object becomes a selectable node routed to its domain's trade."""
    from typehaus.resolve.model import ResolvedCanvasObject

    model, _ = resolve(plan)
    model.canvas_objects.append(ResolvedCanvasObject(
        uid="CO-TEST-1", tag="CO-TEST-1", storey=model.walls[0].storey, domain="furniture",
        kind="Furniture", type_ref=None, room=None, position=(1.0, 1.0), z_m=0.0,
        rotation_degrees=0.0,
        footprint=((0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)),
    ))
    gltf, _blob = emit_gltf_dict(model)

    canvas = [n for n in gltf["nodes"] if n["extras"].get("uid") == "CO-TEST-1"]
    assert len(canvas) == 1, "the resolved canvas object must emit exactly one node"
    extras = canvas[0]["extras"]
    assert extras["trade"] == "furniture" and extras["kind"] == "canvas_object"
    assert canvas[0]["name"] == "furniture|canvas_object|CO-TEST-1"


# --- glTF ↔ viewer parity: normals, winding, material family, raked tops, roof thickness ---

def _accessor_vec3(gltf, blob, accessor_index):
    a = gltf["accessors"][accessor_index]
    view = gltf["bufferViews"][a["bufferView"]]
    off = view["byteOffset"]
    return [struct.unpack_from("<fff", blob, off + 12 * i) for i in range(a["count"])]


def test_every_primitive_has_flat_unit_normals(plan):
    """Every primitive ships per-face NORMALs (de-indexed triangle soup) so Revit/SketchUp and
    the viewer shade the export correctly instead of inferring from winding."""
    import math

    model, _ = resolve(plan)
    gltf, blob = emit_gltf_dict(model)
    for mesh in gltf["meshes"]:
        for prim in mesh["primitives"]:
            attrs = prim["attributes"]
            assert "POSITION" in attrs and "NORMAL" in attrs
            assert "indices" not in prim, "primitives are non-indexed triangle soup"
            normal = gltf["accessors"][attrs["NORMAL"]]
            position = gltf["accessors"][attrs["POSITION"]]
            assert normal["type"] == "VEC3" and normal["count"] == position["count"]
            for (x, y, z) in _accessor_vec3(gltf, blob, attrs["NORMAL"]):
                assert abs(math.sqrt(x * x + y * y + z * z) - 1.0) < 1e-4


def test_opaque_materials_single_sided_translucent_double(plan):
    """Opaque solids are single-sided (verified outward winding — no SketchUp back-faces);
    translucent glass stays double-sided."""
    model, _ = resolve(plan)
    gltf, _ = emit_gltf_dict(model)
    for material in gltf["materials"]:
        translucent = material["alphaMode"] == "BLEND"
        assert material["doubleSided"] is translucent


def _outward_fraction(mb):
    """Fraction of a single-solid mesh's triangles whose winding normal faces away from the
    solid centroid — 1.0 means every face is outward (single-sided-safe). The bucket stores
    indexed geometry, so triangles are formed via the index list, not consecutive vertices."""
    outward = total = 0
    for _c, pos, idx in mb.buckets():
        cx = sum(p[0] for p in pos) / len(pos)
        cy = sum(p[1] for p in pos) / len(pos)
        cz = sum(p[2] for p in pos) / len(pos)
        for k in range(0, len(idx), 3):
            a, b, c = pos[idx[k]], pos[idx[k + 1]], pos[idx[k + 2]]
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            fx = (a[0] + b[0] + c[0]) / 3 - cx
            fy = (a[1] + b[1] + c[1]) / 3 - cy
            fz = (a[2] + b[2] + c[2]) / 3 - cz
            total += 1
            if nx * fx + ny * fy + nz * fz > 0:
                outward += 1
    return outward / total


def test_prism_faces_point_outward_regardless_of_ring_winding():
    """add_prism normalizes ring winding so a single solid's faces all point outward (the
    invariant that makes single-sided export safe) whether the input ring is CW or CCW."""
    from typehaus.emit.gltf.emitter import _MeshBuilder

    ccw = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    cw = list(reversed(ccw))
    for ring in (ccw, cw):
        mb = _MeshBuilder()
        mb.add_prism(ring, 0.0, 1.5, (0.5, 0.5, 0.5, 1.0))
        assert _outward_fraction(mb) == 1.0


def test_member_box_faces_point_outward():
    """add_member_box builds a closed box whose faces all point outward by construction."""
    from typehaus.emit.gltf.emitter import _MeshBuilder

    mb = _MeshBuilder()
    # p0/p1 z are the box's bottom/top elevations, so give it a real vertical extent.
    mb.add_member_box((0.0, 0.0, 0.0), (3.0, 0.0, 0.4), 0.05, (0.6, 0.4, 0.2, 1.0))
    assert _outward_fraction(mb) == 1.0


def test_material_finish_colour_mirrors_viewer_families():
    """Layers colour by material family (viewer parity), with the flat standing-seam / CMU
    finish approximations, and fall back to the function palette when unrecognised."""
    from typehaus.emit.draw.palette import material_family_color
    from typehaus.emit.gltf.emitter import (
        _CMU_BASE,
        _SEAM_BASE,
        _color,
        _hex_rgba,
        _material_finish_color,
    )

    assert _material_finish_color("2x6-spf", "structure") == _hex_rgba(material_family_color("2x6-spf"))
    assert _material_finish_color("standing-seam", "cladding") == _hex_rgba(_SEAM_BASE)
    assert _material_finish_color("cmu-8", "cladding") == _hex_rgba(_CMU_BASE)
    assert _material_finish_color(None, "structure") == _color("structure")


def test_raked_wall_body_follows_the_rake():
    """A gable/ToRoof wall extrudes to its per-vertex raked top, not the flat z1_m bounding box
    that engulfs (and z-fights) the roof — the 'buzzing wall' fix."""
    from typehaus.emit.gltf.emitter import _MeshBuilder, _add_wall_body
    from typehaus.resolve.model import ResolvedLayer, ResolvedWall

    layer = ResolvedLayer(name="stud", material_ref="2x6-spf", function="structure",
                          thickness_m=0.14, polygon=[(0, 0), (4, 0), (4, 0.14), (0, 0.14)])
    wall = ResolvedWall(uid="w1", tag="W1", storey="L1", assembly="EXT", axis=((0, 0), (4, 0)),
                        layers=(layer,), z0_m=0.0, z1_m=4.0, top_z0_m=2.5, top_z1_m=4.0)
    mb = _MeshBuilder()
    _add_wall_body(mb, wall, "core", ())
    pts = [p for _c, pos, _i in mb.buckets() for p in pos]  # gltf (x, elevation, -y)
    top_start = max(p[1] for p in pts if abs(p[0] - 0.0) < 1e-6)
    top_end = max(p[1] for p in pts if abs(p[0] - 4.0) < 1e-6)
    assert abs(top_start - 2.5) < 1e-6  # raked down at the low end, not the z1=4.0 box
    assert abs(top_end - 4.0) < 1e-6


def test_roof_emits_real_thickness():
    """The roof is a thickened, mitered shell (rises above the ridge by its assembly thickness),
    not a zero-thickness plane that imports as a non-manifold surface."""
    import types

    from typehaus.emit.gltf.emitter import _MeshBuilder, _add_roof
    from typehaus.resolve.model import ResolvedRoof

    roof = ResolvedRoof(uid="r1", tag="R1", storey="L1", form="gable",
                        footprint=[(0, 0), (8, 0), (8, 6), (0, 6)], eave_z_m=3.0, ridge_z_m=5.0,
                        ridge_direction="x", assembly="ROOF", surface_area_m2=50.0)
    model = types.SimpleNamespace(plan=types.SimpleNamespace(
        library=types.SimpleNamespace(resolve_assembly=lambda _t: None)))
    mb = _MeshBuilder()
    _add_roof(mb, roof, model)
    ys = [p[1] for _c, pos, _i in mb.buckets() for p in pos]
    assert max(ys) > 5.0 + 1e-3, "thickened shell rises above the bare ridge"
    assert min(ys) <= 3.0 + 1e-9


# --- assembly editor write flows (WP2.4d/e) ----------------------------------

def test_duplicate_assembly_resolves_and_undoes_byte_identical(client):
    c, house = client
    asm_file = house / "plan" / "assemblies.py"
    before = asm_file.read_text()
    rev = c.get("/model").json()["revision"]
    dup = c.post("/macro", json={
        "macro": "duplicate_assembly", "revision": rev,
        "source": "HOUSE_WALL_2X6_WITH_ZIPR", "tag": "MY_WALL",
    })
    assert dup.status_code == 200, dup.json()
    text = asm_file.read_text()
    assert 'Assembly(tag="MY_WALL"' in text or 'tag="MY_WALL"' in text
    # A `haus check` pass: the model must still resolve after the edit (WP2.4d test).
    assert c.get("/model").json()["ok"] is True
    # Edit it, then undo both ops back to byte-identical source.
    rev = c.get("/model").json()["revision"]
    assert c.patch("/plan", json={
        "revision": rev,
        "ops": [{"op": "update", "type": "Assembly", "tag": "MY_WALL", "fields": {"stc": 50}}],
    }).status_code == 200
    assert c.post("/undo").status_code == 200
    assert c.post("/undo").status_code == 200
    assert asm_file.read_text() == before


def test_duplicate_missing_source_is_400(client):
    c, _ = client
    resp = c.post("/macro", json={
        "macro": "duplicate_assembly", "source": "NOPE", "tag": "X",
    })
    assert resp.status_code == 400


def test_add_material_lands_in_source(plan):
    from typehaus.model.materials import Material
    from typehaus.source.assembly_ops import add_material

    result = add_material(plan, Material(tag="cork", name="Cork", r_per_inch=3.6))
    op = result.ops[0]
    assert op.op == "add" and op.type == "Material" and op.tag == "cork"


# --- serializer / import sync ------------------------------------------------

def test_model_source_omits_defaults_and_emits_nested():
    from typehaus.model import Assembly, ControlLayer, Layer, LayerFunction, inch
    from typehaus.source.serialize import model_source

    asm = Assembly(tag="A", layers=(
        Layer(name="s", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, control=frozenset({ControlLayer.THERMAL})),
    ))
    src = model_source(asm)
    assert src.startswith("Assembly(")
    assert "Layer(" in src and "ControlLayer.THERMAL" in src
    assert "junction_policy" not in src  # default omitted


def test_sync_model_imports_is_idempotent_and_reversible():
    from typehaus.source.imports import sync_model_imports

    base = "MATERIALS = STARTER\nASSEMBLIES = [PRESET]\n"
    with_decl = "MATERIALS = STARTER\nASSEMBLIES = [PRESET, Assembly(tag=\"X\")]\n"
    synced = sync_model_imports(with_decl)
    assert "from typehaus.model import Assembly" in synced
    assert sync_model_imports(synced) == synced  # idempotent
    # Removing the declaration and re-syncing drops the now-unused import.
    assert sync_model_imports(base) == base
