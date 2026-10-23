"""D-A-STUDY is a flush-mount Murphy door cased in house oak; one oak infill meets the shelves."""

import struct
from dataclasses import replace
from pathlib import Path

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.cli.price_file import load_prices
from typehaus.emit.gltf.canvas_objects import _add_canvas_objects
from typehaus.emit.gltf.palette import _authored_material_color
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
BOARD_BOUNDS_IN = {"FRONT": (262.875, 104.875, 269.375, 105.625)}
# W-A-SN's two finish faces: the study (shelf) face and the loft (swing) face.
STUDY_FACE_Y_IN, LOFT_FACE_Y_IN = 105.625, 110.375


def _boards(model):
    return {item.tag.removeprefix(BRIDGE_PREFIX): item for item in model.canvas_objects
            if item.tag.startswith(BRIDGE_PREFIX)}


def _door(model):
    door = next(door for door in model.openings if door.tag == "D-A-STUDY")
    door_type = next(t for t in model.plan.library.door_types if t.tag == door.type_ref)
    parts = opening_parts(model.wall(door.host_wall), door, door_type.operation,
                          bookcase_door=door_type.bookcase_door)
    return door, door_type, parts


def _bounds_in(geometry):
    return tuple(v / M_PER_IN for v in geometry.bounds)


def test_cabinet_sits_in_the_rough_opening_flush_with_the_study_face(catlin_model_ro):
    door, door_type, parts = _door(catlin_model_ro)
    assert {part.key for part in parts} == {"bookcase_sides", "bookcase_caps",
                                            "bookcase_shelves", "bookcase_back"}
    cabinet = unary_union([Polygon(solid.ring) for part in parts for solid in part.solids])
    x0, y0, x1, y1 = _bounds_in(cabinet)
    # Face frame on the study finish (nothing over FO-A-STAIR), back 3 3/4" past the loft
    # face: Murphy's 8 1/4" body less a 4 1/2" wall (1/2" board since 2026-10-23).
    assert y0 == pytest.approx(STUDY_FACE_Y_IN)
    assert y1 - LOFT_FACE_Y_IN == pytest.approx(3.75)
    center = (catlin_model_ro.wall("W-A-SN").axis[0][0] + door.center_along_m) / M_PER_IN
    half_ro = door.width_m / 2 / M_PER_IN
    assert center - half_ro < x0 and x1 < center + half_ro
    assert x1 - x0 == pytest.approx(door_type.bookcase_door.body_width.meters / M_PER_IN)


def test_house_oak_casing_laps_the_face_frame_on_the_study_face_only(catlin_model_ro):
    door, door_type, parts = _door(catlin_model_ro)
    casings = [c for c in catlin_model_ro.door_casings if c.opening_ref == "D-A-STUDY"]
    assert [(c.room, c.material_ref) for c in casings] == [("RM-A-STUDY", "oak-trim")]
    pieces = {piece.name: piece for piece in casings[0].pieces}
    assert set(pieces) == {"leg_left", "leg_right", "head"}
    sides = next(part for part in parts if part.key == "bookcase_sides")
    frame = unary_union([Polygon(solid.ring) for solid in sides.solids])
    lap = door_type.bookcase_door.casing_lap.meters / M_PER_IN
    legs = {name: _bounds_in(Polygon(pieces[name].outline)) for name in ("leg_left", "leg_right")}
    assert legs["leg_left"][2] == pytest.approx(_bounds_in(frame)[0] + lap)
    assert legs["leg_right"][0] == pytest.approx(_bounds_in(frame)[2] - lap)
    for x0, y0, x1, y1 in legs.values():
        assert (y0, y1) == pytest.approx((STUDY_FACE_Y_IN - 0.75, STUDY_FACE_Y_IN))
        assert x1 - x0 == pytest.approx(3.5)
    body_top = (catlin_model_ro.wall("W-A-SN").base_ref_z_m
                + door_type.bookcase_door.body_height.meters)
    assert pieces["head"].z0_m == pytest.approx(body_top - lap * M_PER_IN)


def test_one_infill_closes_the_east_leg_to_the_filler_in_the_casing_plane(catlin_model_ro):
    boards = _boards(catlin_model_ro)
    assert set(boards) == set(BOARD_BOUNDS_IN)
    infill = boards["FRONT"]
    assert _bounds_in(Polygon(infill.footprint)) == pytest.approx(BOARD_BOUNDS_IN["FRONT"])
    builtin = next(item for item in catlin_model_ro.canvas_objects
                   if item.tag == "FURN-A-STUDY-BUILTIN")
    assert infill.body_z0_m == pytest.approx(builtin.body_z0_m)
    assert infill.body_z1_m == pytest.approx(builtin.body_z1_m)
    assert Polygon(infill.footprint).distance(Polygon(builtin.footprint)) < 1e-8
    casing = next(c for c in catlin_model_ro.door_casings if c.opening_ref == "D-A-STUDY")
    east_leg = Polygon(next(p for p in casing.pieces if p.name == "leg_right").outline)
    assert Polygon(infill.footprint).distance(east_leg) < 1e-8
    assert Polygon(infill.footprint).intersection(east_leg).area < 1e-10
    assert Polygon(infill.footprint).bounds[1] == pytest.approx(east_leg.bounds[1])


def test_infill_fits_the_study_without_overlapping_partitions_or_the_door(catlin_model_ro):
    model = catlin_model_ro
    door, _door_type, parts = _door(model)
    room = next(room for room in model.rooms if room.tag == "RM-A-STUDY")
    room_face = Polygon(room.clear_face).buffer(1e-8)
    walls = unary_union([Polygon(layer.polygon) for wall in model.walls
                         if wall.tag.startswith("W-A-SN") for layer in wall.layers])
    peers = [item for item in model.canvas_objects
             if item.storey == "attic" and not item.tag.startswith(BRIDGE_PREFIX)]
    for board in _boards(model).values():
        footprint = Polygon(board.footprint)
        assert room_face.covers(footprint), board.tag
        assert footprint.intersection(walls).area < 1e-10
        assert footprint.intersection(Polygon(door.swing_clearance)).area < 1e-10
        assert all(footprint.intersection(Polygon(solid.ring)).area < 1e-10
                   for part in parts for solid in part.solids)
        for peer in peers:
            assert footprint.intersection(Polygon(peer.footprint)).area < 1e-10, peer.tag


def test_viewer_and_gltf_keep_the_oak_infill_with_its_actual_bounds(catlin_model_ro):
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
        assert color == pytest.approx(_authored_material_color(oak))
        accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
        view = gltf["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        coordinates = struct.unpack_from(f"<{accessor['count'] * 3}f", blob, offset)
        x0, y0, x1, y1 = Polygon(board.footprint).bounds
        for axis, expected in enumerate(((x0, x1), (board.body_z0_m, board.body_z1_m), (-y1, -y0))):
            values = coordinates[axis::3]
            assert (min(values), max(values)) == pytest.approx(expected, abs=1e-6)


def test_ifc_keeps_the_infill_board(catlin_model_ro, catlin_ifc_path):
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


def test_the_infill_is_counted_and_its_owner_stock_allowance_is_priced(catlin_model_ro):
    rows = {row["type"]: row for row in placeables_takeoff(catlin_model_ro)
            if row["type"].startswith("FT-A-STUDY-BRIDGE-")}
    assert {tag: row["count"] for tag, row in rows.items()} == {"FT-A-STUDY-BRIDGE-FRONT": 1}
    prices = load_prices(Path(catlin_model_ro.plan.source_root))
    assert prices is not None
    rate = prices.placeables["FT-A-STUDY-BRIDGE-FRONT"]
    assert rate.is_split
    assert (rate.material.low, rate.material.high) == (0, 20)
    assert (rate.labour.low, rate.labour.high) == (60, 140)
    shelves = next(bank for bank in catlin_model_ro.shelf_banks if bank.tag == "SB-A-STUDY")
    assert sum(shelf.count for shelf in shelves.shelves) == 12


def test_catlin_millwork_cuts_the_infill_from_four_quarter_oak(catlin_model_ro):
    rows = [row for row in hardwood_takeoff(catlin_model_ro) if row["use"] == "casework board"]
    assert {(row["finished_thickness_in"], row["finished_width_in"],
             row["finished_length_in"]): row["pieces"] for row in rows} == {(0.75, 6.5, 60): 1}
    assert {tag for row in rows for tag in row["tags"]} == {
        board.tag for board in _boards(catlin_model_ro).values()}
    for row in rows:
        assert (row["material"], row["nominal_stock"], row["milling_profile"], row["layup"]) == (
            "oak-trim", "4/4", "S4S", "one board")
        assert row["also_in_placeables"] is True


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
