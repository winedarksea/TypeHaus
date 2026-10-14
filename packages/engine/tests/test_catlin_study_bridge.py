"""The stationary oak cover joins the study door casing to the stepped shelf run."""

import struct
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.cli.price_file import load_prices
from typehaus.emit.gltf.canvas_objects import _add_canvas_objects
from typehaus.emit.gltf.palette import _hex_rgba
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.model.canvas import canvas_object_types
from typehaus.model.ids import derive_guid
from typehaus.model.millwork import MillworkStandard
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.millwork import _validate_board_furniture_scope
from typehaus.takeoff.hardwood import _furniture_board_rows, hardwood_takeoff
from typehaus.takeoff.placeables import placeables_takeoff

BRIDGE_PREFIX = "FURN-A-STUDY-BRIDGE-"
BOARD_BOUNDS_IN = {
    "FRONT": (263.875, 99.75, 269.375, 100.5),
    "WEST": (263.875, 100.5, 264.625, 105.625),
    "EAST": (268.625, 100.5, 269.375, 105.625),
    "CAP": (264.625, 100.5, 268.625, 105.625),
}


def _boards(model):
    return {item.tag.removeprefix(BRIDGE_PREFIX): item for item in model.canvas_objects
            if item.tag.startswith(BRIDGE_PREFIX)}


def test_four_boards_form_a_connected_cover_at_the_built_in_elevation(catlin_model_ro):
    boards = _boards(catlin_model_ro)
    assert set(boards) == set(BOARD_BOUNDS_IN)
    builtin = next(item for item in catlin_model_ro.canvas_objects
                   if item.tag == "FURN-A-STUDY-BUILTIN")
    for suffix, board in boards.items():
        assert tuple(v / M_PER_IN for v in Polygon(board.footprint).bounds) == pytest.approx(
            BOARD_BOUNDS_IN[suffix])
        assert board.body_z1_m == pytest.approx(builtin.body_z1_m)
        bottom = 59.25 if suffix == "CAP" else 0
        assert board.body_z0_m == pytest.approx(builtin.body_z0_m + bottom * M_PER_IN)
    for first, second in combinations(boards.values(), 2):
        overlap_height = max(0, min(first.body_z1_m, second.body_z1_m)
                             - max(first.body_z0_m, second.body_z0_m))
        overlap_area = Polygon(first.footprint).intersection(Polygon(second.footprint)).area
        assert overlap_height * overlap_area < 1e-10
    for first, second in (('FRONT', 'WEST'), ('FRONT', 'EAST'), ('FRONT', 'CAP'),
                          ('WEST', 'CAP'), ('EAST', 'CAP')):
        assert Polygon(boards[first].footprint).distance(Polygon(boards[second].footprint)) < 1e-8
    assert Polygon(boards["EAST"].footprint).distance(Polygon(builtin.footprint)) < 1e-8


def test_bridge_fits_the_study_without_overlapping_partitions_or_other_furniture(catlin_model_ro):
    model = catlin_model_ro
    boards = _boards(model)
    room = next(room for room in model.rooms if room.tag == "RM-A-STUDY")
    room_face = Polygon(room.clear_face).buffer(1e-8)
    walls = unary_union([Polygon(layer.polygon) for wall in model.walls
                         if wall.tag.startswith("W-A-SN") for layer in wall.layers])
    peers = [item for item in model.canvas_objects
             if item.storey == "attic" and not item.tag.startswith(BRIDGE_PREFIX)]
    for board in boards.values():
        footprint = Polygon(board.footprint)
        assert room_face.covers(footprint), board.tag
        assert footprint.intersection(walls).area < 1e-10
        for peer in peers:
            assert footprint.intersection(Polygon(peer.footprint)).area < 1e-10, peer.tag


def test_bridge_leaves_a_casing_reveal_and_clears_the_modeled_door(catlin_model_ro):
    model = catlin_model_ro
    door = next(door for door in model.openings if door.tag == "D-A-STUDY")
    door_type = next(t for t in model.plan.library.door_types if t.tag == door.type_ref)
    parts = opening_parts(model.wall(door.host_wall), door, door_type.operation,
                          bookcase_door=door_type.bookcase_door)
    casing = unary_union([Polygon(solid.ring) for part in parts
                          if part.key == "bookcase_casing" for solid in part.solids])
    front = Polygon(_boards(model)["FRONT"].footprint)
    assert front.bounds[0] - casing.bounds[2] == pytest.approx(0.125 * M_PER_IN)
    assert front.bounds[1] == pytest.approx(casing.bounds[1])
    for board in _boards(model).values():
        footprint = Polygon(board.footprint)
        assert footprint.intersection(Polygon(door.swing_clearance)).area < 1e-10
        assert all(footprint.intersection(Polygon(solid.ring)).area < 1e-10
                   for part in parts for solid in part.solids)


def test_viewer_and_gltf_keep_four_oak_boards_with_their_actual_bounds(catlin_model_ro):
    model = catlin_model_ro
    boards = _boards(model)
    types = {record["tag"]: record for record in canvas_object_types(model.plan)}
    oak = next(material for material in model.plan.library.materials if material.tag == "oak-trim")
    for board in boards.values():
        record = types[board.type_ref]
        assert len(record["model_parts"]) == 1
        assert record["model_parts"][0]["material_ref"] == oak.tag
        assert record["model_parts"][0]["color"] == oak.color
        assert record["plan_strokes"]
    # Exercise the production placeable exporter without emitting the rest of the house.
    scene = _SceneBuilder()
    _add_canvas_objects(scene, replace(model, canvas_objects=list(boards.values()), countertops=[]))
    gltf, blob = scene.build()
    nodes = {node["extras"]["uid"]: node for node in gltf["nodes"]}
    assert set(nodes) == {board.uid for board in boards.values()}
    for board in boards.values():
        primitives = gltf["meshes"][nodes[board.uid]["mesh"]]["primitives"]
        assert len(primitives) == 1
        primitive = primitives[0]
        color = gltf["materials"][primitive["material"]]["pbrMetallicRoughness"]["baseColorFactor"]
        assert color == pytest.approx(_hex_rgba(oak.color))
        accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
        view = gltf["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        coordinates = struct.unpack_from(f"<{accessor['count'] * 3}f", blob, offset)
        x0, y0, x1, y1 = Polygon(board.footprint).bounds
        for axis, expected in enumerate(((x0, x1), (board.body_z0_m, board.body_z1_m), (-y1, -y0))):
            values = coordinates[axis::3]
            assert (min(values), max(values)) == pytest.approx(expected, abs=1e-6)


def test_ifc_keeps_each_bridge_board_and_its_cap_mount(catlin_model_ro, catlin_ifc_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    exported = ifcopenshell.open(str(catlin_ifc_path))
    furniture = {item.Name: item for item in exported.by_type("IfcFurniture")
                 if item.Name.startswith(BRIDGE_PREFIX)}
    boards = _boards(catlin_model_ro)
    assert set(furniture) == {board.tag for board in boards.values()}
    for board in boards.values():
        item = furniture[board.tag]
        assert item.GlobalId == derive_guid(catlin_model_ro.plan.project.project_uuid, board.uid)
        solids = item.Representation.Representations[0].Items
        assert len(solids) == 1
        solid = solids[0]
        assert solid.is_a("IfcExtrudedAreaSolid")
        assert solid.Depth == pytest.approx(board.body_z1_m - board.body_z0_m)
        assert solid.Position.Location.Coordinates[2] == pytest.approx(board.body_z0_m)
        footprint = Polygon([point.Coordinates for point in solid.SweptArea.OuterCurve.Points])
        assert footprint.bounds == pytest.approx(Polygon(board.footprint).bounds)


def test_four_boards_are_counted_and_the_separate_owner_stock_allowance_is_priced(catlin_model_ro):
    rows = {row["type"]: row for row in placeables_takeoff(catlin_model_ro)
            if row["type"].startswith("FT-A-STUDY-BRIDGE-")}
    assert {tag: row["count"] for tag, row in rows.items()} == {
        "FT-A-STUDY-BRIDGE-FRONT": 1, "FT-A-STUDY-BRIDGE-RETURN": 2,
        "FT-A-STUDY-BRIDGE-CAP": 1,
    }
    prices = load_prices(Path(catlin_model_ro.plan.source_root))
    assert prices is not None
    rates = [(row["count"], prices.placeables[tag]) for tag, row in rows.items()]
    assert all(rate.is_split for _, rate in rates)
    assert sum(count * rate.material.low for count, rate in rates) == 0
    assert sum(count * rate.material.high for count, rate in rates) == 50
    assert sum(count * rate.labour.low for count, rate in rates) == 120
    assert sum(count * rate.labour.high for count, rate in rates) == 300
    shelves = next(bank for bank in catlin_model_ro.shelf_banks if bank.tag == "SB-A-STUDY")
    assert sum(shelf.count for shelf in shelves.shelves) == 12


def test_catlin_millwork_cuts_all_four_bridge_boards_from_four_quarter_oak(catlin_model_ro):
    rows = [row for row in hardwood_takeoff(catlin_model_ro) if row["use"] == "casework board"]
    assert {(row["finished_thickness_in"], row["finished_width_in"],
             row["finished_length_in"]): row["pieces"] for row in rows} == {
        (0.75, 5.5, 60): 1, (0.75, 5.125, 60): 2, (0.75, 4, 5.125): 1,
    }
    assert {tag for row in rows for tag in row["tags"]} == {
        board.tag for board in _boards(catlin_model_ro).values()}
    for row in rows:
        assert (row["material"], row["nominal_stock"], row["milling_profile"], row["layup"]) == (
            "oak-trim", "4/4", "S4S", "one board")
        assert row["also_in_placeables"] is True
    assert sum(row["rough_board_feet"] for row in rows) == pytest.approx(8.6)


def test_millwork_board_scope_is_explicit_and_cut_sizes_follow_the_catalog(catlin_model_ro):
    model = catlin_model_ro
    standard = next(el for el in model.plan.all_elements() if isinstance(el, MillworkStandard))
    materials = {material.tag: material for material in model.plan.library.materials}
    assert _furniture_board_rows(model, materials, None, 18) == []
    assert _furniture_board_rows(
        model, materials, standard.model_copy(update={"board_furniture_refs": ()}), 18) == []
    front_type = _boards(model)["FRONT"].type_ref
    changed_types = tuple(product.model_copy(update={"footprint": (inch(6), inch(0.75))})
                          if product.tag == front_type else product
                          for product in model.plan.library.furniture_types)
    library = model.plan.library.model_copy(update={"furniture_types": changed_types})
    changed = replace(model, plan=model.plan.model_copy(update={"library": library}))
    rows = _furniture_board_rows(changed, materials, standard, 18)
    front = next(row for row in rows if BRIDGE_PREFIX + "FRONT" in row["tags"])
    assert front["finished_width_in"] == 6


@pytest.mark.parametrize("refs", [
    ("NO-SUCH-BOARD",), ("FURN-A-STUDY-BUILTIN",),
    (BRIDGE_PREFIX + "FRONT", BRIDGE_PREFIX + "FRONT"),
])
def test_invalid_millwork_board_references_fail_validation(catlin_model_ro, refs):
    model = catlin_model_ro
    standard = next(el for el in model.plan.all_elements() if isinstance(el, MillworkStandard))
    standard = standard.model_copy(update={"board_furniture_refs": refs})
    findings = _validate_board_furniture_scope(model.plan, model, standard)
    assert len(findings) == 1
    assert findings[0].check_id == "integrity.millwork_board_ref"
    assert findings[0].result.value == "fail"


@pytest.mark.parametrize("stock_change", [
    {"requires_custom_milling": False}, {"nominal_quarters": None}, {"species": None},
])
def test_millwork_board_requires_declared_custom_milling_stock(catlin_model_ro, stock_change):
    model = catlin_model_ro
    standard = next(el for el in model.plan.all_elements() if isinstance(el, MillworkStandard))
    standard = standard.model_copy(update={"board_furniture_refs": (BRIDGE_PREFIX + "FRONT",)})
    materials = tuple(material.model_copy(update=stock_change) if material.tag == "oak-trim"
                      else material for material in model.plan.library.materials)
    library = model.plan.library.model_copy(update={"materials": materials})
    plan = model.plan.model_copy(update={"library": library})
    findings = _validate_board_furniture_scope(plan, model, standard)
    assert len(findings) == 1
    assert findings[0].check_id == "integrity.millwork_board_stock"
    assert findings[0].result.value == "fail"
