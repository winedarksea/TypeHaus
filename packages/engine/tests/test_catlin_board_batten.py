"""The installed panel envelope follows its support face, not the former PBR depth."""
import pytest

from typehaus.emit.gltf import emit_gltf_dict
from typehaus.emit.gltf.validate import validate_gltf


def test_catlin_cladding_depths_supports_and_gable_meshes(catlin_model_ro):
    model = catlin_model_ro
    panel_walls = [wall for wall in model.walls
                   if any(layer.material_ref == 'board-batten-24' for layer in wall.layers)]
    assert len(panel_walls) == 20
    for wall in panel_walls:
        skin = next(layer for layer in wall.layers if layer.name == 'cladding')
        assert skin.thickness_m == pytest.approx(.01905)
        assert skin.surface_mesh is not None
        assert skin.surface_mesh.triangles
        vent_gap = next(layer for layer in wall.layers if layer.name == 'vent-gap')
        outer_girt = next(layer for layer in wall.layers if layer.name == 'outer-girt')
        assert vent_gap.thickness_m == pytest.approx(.0127)
        assert outer_girt.thickness_m == pytest.approx(.0381)
    for wall in model.walls:
        for layer in wall.layers:
            if layer.material_ref == 'pbr-panel-24':
                assert layer.thickness_m == pytest.approx(.03175)
                assert layer.surface_mesh and layer.surface_mesh.triangles
            if layer.material_ref == 'corrugated-panel-24':
                assert layer.thickness_m == pytest.approx(.022225)
                assert layer.surface_mesh and layer.surface_mesh.triangles
    closures = [member for roof in model.roofs for member in roof.members
                if member.material == 'board-batten-24' and member.category == 'cladding']
    assert closures
    assert all(member.surface_mesh and member.surface_mesh.triangles for member in closures)
    south = model.wall('W-M-S1')
    north = model.wall('W-M-N1')
    assert min(y for x,y in south.layers[-1].polygon) == pytest.approx(-6.75*.0254)
    assert max(y for x,y in north.layers[-1].polygon) == pytest.approx((36*12+6.75)*.0254)
    # A 45-degree equal-depth mitre would leave the PBR endpoints half an inch proud.
    for wall in model.walls:
        if wall.storey == 'main' and wall.tag.startswith('W-M-'):
            for layer in wall.layers:
                if layer.material_ref == 'pbr-panel-24':
                    assert all(-6.75*.0254-1e-8 <= y <= (36*12+6.75)*.0254+1e-8
                               for _,y in layer.polygon)



def test_catlin_profiled_export_is_valid_and_has_its_own_painted_material(catlin_model_ro):
    gltf,blob = emit_gltf_dict(catlin_model_ro)
    assert validate_gltf(gltf,buffer_lengths=[len(blob)]) == []
    for material_ref in ('board-batten-24', 'pbr-panel-24', 'corrugated-panel-24'):
        skins = [node for node in gltf['nodes']
                 if node.get('extras',{}).get('material_ref') == material_ref]
        assert skins
        for node in skins:
            assert node['extras']['kind'] == 'wall'
            assert node['extras']['trade'] == 'siding'
            for primitive in gltf['meshes'][node['mesh']]['primitives']:
                material = gltf['materials'][primitive['material']]['pbrMetallicRoughness']
                assert material['roughnessFactor'] == .45
                assert material['metallicFactor'] == .05


def test_garage_north_valleys_clear_the_head_lap_and_continue_through_the_gable(catlin_model_ro):
    model = catlin_model_ro
    wall = model.wall('W-G-N')
    skin = next(layer for layer in wall.layers if layer.function == 'cladding')
    membrane = next(solid for solid in model.solids
                    if solid.tag == 'D-G-OVERHEAD-FLASH-PERIMETER')
    flashing_face = max(y for _, y, _ in membrane.body_mesh.positions)
    assert min(y for _, y, _ in skin.surface_mesh.positions) >= flashing_face - 1e-9
    # Clearance is the thin head lap, never the exposed drip's much larger projection.
    assert min(y for _, y, _ in skin.surface_mesh.positions) == pytest.approx(
        flashing_face, abs=1e-5)
    assert max(y for _, y, _ in skin.surface_mesh.positions) == pytest.approx(
        max(y for _, y in skin.polygon))

    def seam(mesh):
        return {(round(x, 9), round(y, 9)) for x, y, z in mesh.positions
                if abs(z - wall.z1_m) < 1e-9 and 2 < x < 9}

    closures = [member.surface_mesh for roof in model.roofs for member in roof.members
                if member.parent_uid == wall.uid and member.category == 'cladding']
    assert len(closures) == 2
    assert all(min(y for _, y, _ in mesh.positions) >= flashing_face - 1e-9 for mesh in closures)
    assert seam(skin.surface_mesh) == set().union(*(seam(mesh) for mesh in closures))
