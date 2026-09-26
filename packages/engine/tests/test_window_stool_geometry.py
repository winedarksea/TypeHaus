"""One resolved stool shape across the live payload, GLB, and IFC."""

from __future__ import annotations

from dataclasses import replace

import pytest
from shapely.geometry import Polygon

from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_millwork import window_stool_prism
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.server.model_json import model_to_dict


def test_stools_fit_their_windows_and_reverse_with_the_wall(catlin_model_ro):
    walls = {wall.tag: wall for wall in catlin_model_ro.walls}
    openings = {opening.tag: opening for opening in catlin_model_ro.openings}
    stools = catlin_model_ro.window_stools
    assert len(stools) == 33
    assert len({stool.uid for stool in stools}) == 33
    for stool in stools:
        opening = openings[stool.window_ref]
        wall = walls[stool.wall_tag]
        prism = window_stool_prism(wall, opening, stool)
        assert prism is not None
        assert prism.z1_m - prism.z0_m == pytest.approx(stool.thickness_m)
        frame = next(part for part in opening_parts(wall, opening, None)
                     if part.key == "frame")
        assert prism.z1_m == pytest.approx(frame.solids[-1].z1_m)
        assert len(prism.ring) == 8, "the horns stop at the interior wall face"
        assert Polygon(prism.ring).area == pytest.approx(
            opening.width_m * stool.depth_m + 2 * stool.horn_m * stool.overhang_m)

    stool = stools[0]
    opening = openings[stool.window_ref]
    wall = walls[stool.wall_tag]
    _origin, _tangent, _normal, wall_length = wall_frame(wall)
    reversed_wall = replace(wall, axis=(wall.axis[1], wall.axis[0]))
    reversed_opening = replace(opening, center_along_m=wall_length - opening.center_along_m)
    original = window_stool_prism(wall, opening, stool)
    reversed_prism = window_stool_prism(reversed_wall, reversed_opening, stool)
    assert original is not None and reversed_prism is not None
    assert {tuple(round(value, 8) for value in point) for point in original.ring} == {
        tuple(round(value, 8) for value in point) for point in reversed_prism.ring}
    assert window_stool_prism(wall, opening, replace(stool, depth_m=None)) is None


def test_stool_shape_reaches_the_viewer_and_glb(catlin_model_ro):
    payload = model_to_dict(catlin_model_ro)
    rows = payload["window_stools"]
    assert len(rows) == 33
    assert {row["profile"] for row in rows} == {"eased"}
    assert {row["material_ref"] for row in rows} == {"oak-stool"}
    openings = {opening.uid for opening in catlin_model_ro.openings}
    assert all(row["opening_uid"] in openings for row in rows)

    gltf, _blob = emit_gltf_dict(catlin_model_ro)
    nodes = [node for node in gltf["nodes"]
             if node["extras"].get("trade") == "millwork"
             and node["extras"].get("kind") == "opening"]
    assert len(nodes) == 33
    assert {node["extras"]["uid"] for node in nodes} == {
        row["opening_uid"] for row in rows}
    for node in nodes:
        mesh = gltf["meshes"][node["mesh"]]
        material = gltf["materials"][mesh["primitives"][0]["material"]]
        assert material["pbrMetallicRoughness"]["baseColorFactor"] == pytest.approx(
            [198 / 255, 156 / 255, 109 / 255, 1.0])


def test_stools_export_as_oak_ifc_moldings(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell
    import ifcopenshell.util.element

    from typehaus._meta import PSET_SOURCE
    from typehaus.model.ids import derive_guid

    file = ifcopenshell.open(str(catlin_ifc_path))
    payload = {row["tag"]: row for row in model_to_dict(catlin_model_ro)["window_stools"]}
    stools = {item.Name: item for item in file.by_type("IfcCovering")
              if item.Name.startswith("STOOL-")}
    assert len(stools) == 33
    assert set(stools) == {stool.tag for stool in catlin_model_ro.window_stools}
    for stool in catlin_model_ro.window_stools:
        product = stools[stool.tag]
        assert product.PredefinedType == "MOLDING"
        assert product.GlobalId == derive_guid(catlin_model_ro.plan.project.project_uuid,
                                               stool.uid)
        assert ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]["window_ref"] == (
            stool.window_ref)
        representation = product.Representation.Representations[0].Items[0]
        assert representation.Depth == pytest.approx(stool.thickness_m)
        assert representation.Position.Location.Coordinates[2] == pytest.approx(
            payload[stool.tag]["z0_m"])
        assert len(representation.SweptArea.OuterCurve.Points) == 9
        assert {tuple(round(value, 8) for value in point.Coordinates)
                for point in representation.SweptArea.OuterCurve.Points[:-1]} == {
                    tuple(round(value, 8) for value in point)
                    for point in payload[stool.tag]["outline"]}
        materials = [relation.RelatingMaterial.Name
                     for relation in file.by_type("IfcRelAssociatesMaterial")
                     if product in relation.RelatedObjects]
        assert materials == ["oak-stool"]
