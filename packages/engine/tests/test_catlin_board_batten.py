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
        assert next(layer for layer in wall.layers if layer.name == 'vent-gap').thickness_m == pytest.approx(.0127)
        assert next(layer for layer in wall.layers if layer.name == 'outer-girt').thickness_m == pytest.approx(.0381)
    for wall in model.walls:
        for layer in wall.layers:
            if layer.material_ref == 'pbr-panel-24':
                assert layer.thickness_m == pytest.approx(.03175)
                assert layer.surface_mesh is None
    closures = [member for roof in model.roofs for member in roof.members
                if member.material == 'board-batten-24' and member.category == 'cladding']
    assert closures
    assert all(member.surface_mesh and member.surface_mesh.triangles for member in closures)
    south = model.wall('W-M-S1')
    north = model.wall('W-M-N1')
    assert min(y for x,y in south.layers[-1].polygon) == pytest.approx(-6.75*.0254)
    assert max(y for x,y in north.layers[-1].polygon) == pytest.approx((36*12+6.75)*.0254)


def test_catlin_profiled_export_is_valid_and_has_its_own_painted_material(catlin_model_ro):
    gltf,blob = emit_gltf_dict(catlin_model_ro)
    assert validate_gltf(gltf,buffer_lengths=[len(blob)]) == []
    skins = [node for node in gltf['nodes'] if node.get('extras',{}).get('material_ref') == 'board-batten-24']
    assert skins
    for node in skins:
        assert node['extras']['kind'] == 'wall'
        assert node['extras']['trade'] == 'siding'
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            material = gltf['materials'][primitive['material']]['pbrMetallicRoughness']
            assert material['roughnessFactor'] == .45
            assert material['metallicFactor'] == .05
