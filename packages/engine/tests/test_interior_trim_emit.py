"""One trim shape across the live payload, the GLB and the IFC (→ geometry_millwork)."""

from __future__ import annotations

from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.resolve.geometry_millwork import base_run_prisms, door_casing_prisms
from typehaus.server.model_json import model_to_dict


def test_trim_reaches_the_viewer_as_drawable_boards(catlin_model_ro):
    payload = model_to_dict(catlin_model_ro)
    boards = [r for r in catlin_model_ro.base_runs if r.kind == "trim"]
    assert len(payload["base_runs"]) == len(boards)
    assert {row["uid"] for row in payload["base_runs"]} == {r.uid for r in boards}
    rooms = {room.uid for room in catlin_model_ro.rooms}
    assert all(row["room_uid"] in rooms for row in payload["base_runs"])
    assert len(payload["door_casings"]) == len(catlin_model_ro.door_casings)
    for row, casing in zip(sorted(payload["door_casings"], key=lambda r: r["uid"]),
                           sorted(catlin_model_ro.door_casings, key=lambda c: c.uid),
                           strict=True):
        assert len(row["pieces"]) == len(casing.pieces)
        assert row["opening_uid"] == casing.opening_uid


def test_glb_draws_the_same_boards_selecting_as_room_and_door(catlin_model_ro):
    gltf, _blob = emit_gltf_dict(catlin_model_ro)
    millwork = [node for node in gltf["nodes"] if node["extras"].get("trade") == "millwork"]
    rooms = {room.tag: room.uid for room in catlin_model_ro.rooms}
    base_nodes = [n for n in millwork if n["extras"].get("kind") == "room"]
    drawn = [r for r in catlin_model_ro.base_runs if base_run_prisms(r)]
    assert len(base_nodes) == len(drawn)
    assert {n["extras"]["uid"] for n in base_nodes} == {rooms[r.room] for r in drawn}
    doors = {o.uid for o in catlin_model_ro.openings if o.is_door}
    casing_nodes = [n for n in millwork if n["extras"].get("kind") == "opening"
                    and n["extras"]["uid"] in doors]
    assert len(casing_nodes) == len(catlin_model_ro.door_casings)
    assert {n["extras"]["uid"] for n in casing_nodes} == {
        c.opening_uid for c in catlin_model_ro.door_casings}


def test_trim_exports_as_ifc_skirting_and_moldings(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell
    import ifcopenshell.util.element

    from typehaus._meta import PSET_SOURCE
    from typehaus.model.ids import derive_guid

    file = ifcopenshell.open(str(catlin_ifc_path))
    coverings = {item.Name: item for item in file.by_type("IfcCovering")}
    project = catlin_model_ro.plan.project.project_uuid
    drawn = [r for r in catlin_model_ro.base_runs if base_run_prisms(r)]
    for run in drawn:
        product = coverings[run.tag]
        assert product.PredefinedType == "SKIRTINGBOARD"
        assert product.GlobalId == derive_guid(project, run.uid)
        assert ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]["room"] == run.room
    # A tile base and a flash cove are not boards: no covering.
    assert not [r for r in catlin_model_ro.base_runs
                if r.kind != "trim" and r.tag in coverings]
    for casing in catlin_model_ro.door_casings:
        product = coverings[casing.tag]
        assert product.PredefinedType == "MOLDING"
        items = product.Representation.Representations[0].Items
        assert len(items) == len(door_casing_prisms(casing))
        assert {round(item.Depth, 6) for item in items} == {
            round(p.z1_m - p.z0_m, 6) for p in casing.pieces}
        props = ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]
        assert props["door_ref"] == casing.opening_ref
        assert props["material_ref"] == "oak-trim"


def test_trim_is_not_a_solid_so_the_section_goldens_do_not_move(catlin_model_ro):
    categories = {solid.category for solid in catlin_model_ro.solids}
    assert "baseboard" not in categories and "door_casing" not in categories
    kinds = {element.kind for element in catlin_model_ro.geometry.elements}
    assert {"baseboard", "door_casing"} <= kinds
