"""One trim shape across the live payload, the GLB and the IFC (→ geometry_millwork)."""

from __future__ import annotations

import copy
from collections import Counter

from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.resolve.geometry_millwork import (
    base_run_prisms,
    base_run_trade,
    door_casing_prisms,
)
from typehaus.server.model_json import model_to_dict


def test_trim_reaches_the_viewer_as_drawable_boards(catlin_model_ro):
    """Every base run is sent, a tile base and a flash cove included, with its kind."""
    payload = model_to_dict(catlin_model_ro)
    runs = catlin_model_ro.base_runs
    assert {r.kind for r in runs} == {"trim", "tile", "integral_cove"}
    assert {(row["uid"], row["kind"]) for row in payload["base_runs"]} == {
        (r.uid, r.kind) for r in runs}
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
    # A base lands on its kind's trade: a board on millwork, tile on tile, a cove on flooring.
    # Room floors are flooring|room nodes too, so count against an emit without the base.
    bare = copy.copy(catlin_model_ro)
    bare.base_runs = []
    without, _blob = emit_gltf_dict(bare)

    def room_nodes(doc, trade):
        return Counter(n["extras"]["uid"] for n in doc["nodes"]
                       if n["extras"].get("trade") == trade and n["extras"].get("kind") == "room")

    for trade in ("millwork", "tile", "flooring"):
        drawn = Counter(rooms[r.room] for r in catlin_model_ro.base_runs
                        if base_run_prisms(r) and base_run_trade(r) == trade)
        assert drawn and room_nodes(gltf, trade) - room_nodes(without, trade) == drawn, trade
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
        assert ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]["kind"] == run.kind
    assert {r.kind for r in drawn} == {"trim", "tile", "integral_cove"}
    for casing in catlin_model_ro.door_casings:
        product = coverings[casing.tag]
        assert product.PredefinedType == "MOLDING"
        items = product.Representation.Representations[0].Items
        assert len(items) == len(door_casing_prisms(casing))
        assert {round(item.Depth, 6) for item in items} == {
            round(p.z1_m - p.z0_m, 6) for p in casing.pieces}
        props = ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]
        assert props["door_ref"] == casing.opening_ref
        assert props["material_ref"] == casing.material_ref


def test_trim_is_not_a_solid_so_the_section_goldens_do_not_move(catlin_model_ro):
    categories = {solid.category for solid in catlin_model_ro.solids}
    assert "baseboard" not in categories and "door_casing" not in categories
    kinds = {element.kind for element in catlin_model_ro.geometry.elements}
    assert {"baseboard", "door_casing"} <= kinds
