"""The basement stair's covering is separate, continuous, and exportable."""

import pytest

from typehaus.emit.gltf import emit_gltf_dict
from typehaus.emit.gltf.palette import _material_finish_color, authored_colors
from typehaus.quantities import inch
from typehaus.resolve.geometry_build import build_geometry
from typehaus.server.model_json_fabric import framing_json
from typehaus.takeoff.stairs import stair_finish_takeoff, stair_tread_takeoff


def _basement_stair(model):
    return next(stair for stair in model.stairs if stair.tag == "ST-B2M")


def test_carpet_covers_every_stair_surface_without_entering_takeoff(catlin_model_ro):
    stair = _basement_stair(catlin_model_ro)
    assert stair.finish_material == "carpet"
    assert stair.finish_thickness_m == pytest.approx(inch(0.5).meters)
    by_role = {role: [part for part in stair.finish_parts if part.role == role]
               for role in ("walking", "nosing", "riser")}
    assert {role: len(parts) for role, parts in by_role.items()} == {
        "walking": 14, "nosing": 12, "riser": 15}
    assert all(part.material_ref == "carpet" and part.z1_m > part.z0_m
               for part in stair.finish_parts)
    assert {part.key for part in by_role["walking"]} == {
        f"{member.child_key}:top" for member in stair.members
        if member.category in {"tread", "landing"}}
    assert "riser-landing:face" in {part.key for part in by_role["riser"]}

    for member in stair.members:
        if member.category in {"tread", "landing"}:
            finish = next(part for part in by_role["walking"]
                          if part.key == f"{member.child_key}:top")
            assert finish.z0_m == pytest.approx(member.z1_m)
            assert finish.z1_m == pytest.approx(member.z1_m + inch(0.5).meters)
            assert member.z1_m - member.z0_m == pytest.approx(inch(1).meters)
    assert all(member.category != "stair_finish" for member in stair.members)
    assert not [row for row in stair_tread_takeoff(catlin_model_ro)
                if row["stair"] == stair.tag and row["material"] == "carpet"]
    [finish_row] = [row for row in stair_finish_takeoff(catlin_model_ro)
                    if row["stair"] == stair.tag]
    assert (finish_row["treads"], finish_row["risers"],
            finish_row["landing_decks"]) == (12, 15, 2)


def test_carpet_surfaces_reach_model_json_and_geometry_ir(catlin_model_ro):
    stair = _basement_stair(catlin_model_ro)
    [record] = [row for row in framing_json(catlin_model_ro, None)["stairs"]
                if row["tag"] == stair.tag]
    assert len(record["finish_parts"]) == len(stair.finish_parts)
    assert record["finish_material"] == "carpet"
    geometry = build_geometry(catlin_model_ro)
    [element] = [element for element in geometry.elements
                 if element.uid == f"{stair.uid}::finish"]
    assert len(element.parts) == len(stair.finish_parts)
    assert all(part.catalog.material_ref == "carpet" for part in element.parts)


def test_carpet_is_in_gltf_stair_mesh(catlin_model_ro):
    stair = _basement_stair(catlin_model_ro)
    gltf, _ = emit_gltf_dict(catlin_model_ro)
    [node] = [node for node in gltf["nodes"]
              if node.get("extras", {}).get("uid") == stair.uid
              and node.get("extras", {}).get("kind") == "stair"]
    material_ids = {primitive["material"] for primitive in
                    gltf["meshes"][node["mesh"]]["primitives"]}
    carpet_color = _material_finish_color("carpet", "finish", authored_colors(catlin_model_ro))
    assert any(gltf["materials"][material_id]["pbrMetallicRoughness"]
               ["baseColorFactor"] == list(carpet_color)
               for material_id in material_ids)


def test_carpet_is_ifc_covering_under_stair(catlin_ifc_path):
    import ifcopenshell

    model = ifcopenshell.open(str(catlin_ifc_path))
    [stair] = [item for item in model.by_type("IfcStair") if item.Name == "ST-B2M"]
    children = [item for relation in stair.IsDecomposedBy for item in relation.RelatedObjects]
    coverings = [item for item in children if item.is_a("IfcCovering")]
    assert len(coverings) == 41
    assert any(item.Name == "ST-B2M/riser-landing:face" for item in coverings)
    assert all(item.Representation is not None for item in coverings)
