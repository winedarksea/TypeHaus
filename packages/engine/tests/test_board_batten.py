"""Dimensioned folded skins, including cuts that a normal map cannot represent."""
from dataclasses import replace
import math

import pytest
from _helpers import assert_wire_mesh

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.walls import _add_wall_body
from typehaus.resolve.board_batten import BBD75_PROFILE, profile_mesh
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall
from typehaus.server.model_json_shared import _layer_json


@pytest.fixture
def siding_wall():
    length = 4 * BBD75_PROFILE.pitch_m
    inner = ResolvedLayer('stud','spf','structure',.1,[(0,0),(length,0),(length,.1),(0,.1)])
    skin = ResolvedLayer('cladding','board-batten-24','cladding',BBD75_PROFILE.depth_m,
                         [(0,-.11905),(length,-.11905),(length,-.1),(0,-.1)])
    return ResolvedWall('wall','W','main','BB',((0,0),(length,0)),(inner,skin),0.,3.)


def mesh_for(wall, **kwargs):
    return profile_mesh(wall,wall.layers[-1].polygon,0.,3.,((0,0),(1,0)),
                        layer_name='cladding',**kwargs)


def triangle_centers(mesh):
    return [tuple(sum(mesh.positions[i][axis] for i in tri)/3 for axis in range(3))
            for tri in mesh.triangles]


def opening(**changes):
    return replace(ResolvedOpening('op','O','W',None,.5,1.,.8,.61,'window',False),**changes)


def test_published_dimensions_and_thin_folded_skin(siding_wall):
    mesh = mesh_for(siding_wall)
    crowns = [p for p,n in zip(mesh.positions,mesh.normals,strict=True)
              if n == pytest.approx((0,-1,0)) and p[1] == pytest.approx(-.11905)]
    # A full crown centred on the first interior station is exactly two inches wide.
    station = BBD75_PROFILE.pitch_m
    selected = [p[0] for p in crowns if abs(p[0]-station) < .03]
    assert max(selected)-min(selected) == pytest.approx(.0508)
    assert min(p[1] for p in mesh.positions) == pytest.approx(-.11905)
    assert max(p[1] for p in mesh.positions) == pytest.approx(-.1)
    # Away from webs, there is sheet only at the crown or support, never a filled rib.
    assert not any(abs(p[0]-station) < .01 and -.118 < p[1] < -.102
                   for p in mesh.positions)
    assert all(math.isfinite(v) for p in mesh.positions for v in p)
    for tri in mesh.triangles:
        a,b,c = [mesh.positions[i] for i in tri]
        ab,ac = [b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
        cross = (ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
        normal = mesh.normals[tri[0]]
        assert sum(v*v for v in cross) > 1e-24
        assert sum(v*n for v,n in zip(cross,normal,strict=True)) > 0
        assert sum(v*v for v in normal) == pytest.approx(1.)


@pytest.mark.parametrize('arch_rise',[0.,.25])
def test_openings_cut_all_folds_and_preserve_sheet_above(siding_wall,arch_rise):
    op = opening(arch_rise_m=arch_rise)
    mesh = mesh_for(siding_wall,openings=[op])
    # Entire straight jamb region is empty, including the rib sides and rear sheet.
    assert not any(.361 < x < .859 and .801 < z < 1.549
                   for x,_,z in triangle_centers(mesh))
    assert any(.4 < x < .8 and z > 1.801 for x,_,z in triangle_centers(mesh))
    if arch_rise:
        assert any(.36 < x < .43 and 1.56 < z < 1.76 for x,_,z in triangle_centers(mesh))


def test_overlapping_openings_are_subtracted_as_a_union(siding_wall):
    mesh = mesh_for(siding_wall,openings=[opening(),opening(center_along_m=.8,sill_m=1.2)])
    assert not any(.551 < x < 1.049 and 1.201 < z < 2.199
                   for x,_,z in triangle_centers(mesh))


def test_interior_blind_recess_leaves_exterior_skin(siding_wall):
    mesh = mesh_for(siding_wall,openings=[opening(depth_m=.03,depth_from='interior')])
    assert mesh == mesh_for(siding_wall)
    cut = mesh_for(siding_wall,openings=[opening(depth_m=.03,depth_from='exterior')])
    assert cut != mesh


def test_reversed_wall_and_split_segments_keep_facade_phase(siding_wall):
    original = mesh_for(siding_wall)
    reversed_wall = replace(siding_wall,axis=tuple(reversed(siding_wall.axis)))
    assert mesh_for(reversed_wall) == original
    # A cut through a pan does not shift the next crown.
    skin = siding_wall.layers[-1]
    polygon = [(max(x,.17),y) for x,y in skin.polygon]
    split = replace(siding_wall,layers=(*siding_wall.layers[:-1],replace(skin,polygon=polygon)))
    mesh = mesh_for(split)
    crowns = [x for (x,y,_),n in zip(mesh.positions,mesh.normals,strict=True)
              if y == pytest.approx(-.11905) and n == pytest.approx((0,-1,0))]
    assert min(crowns) == pytest.approx(.3048-.0254)


def test_mitred_polygon_and_raked_band_clip_every_fold(siding_wall):
    skin = siding_wall.layers[-1]
    polygon = [(0,-.11905),(1.1,-.11905),(1.15,-.1),(.01905,-.1)]
    wall = replace(siding_wall,layers=(*siding_wall.layers[:-1],replace(skin,polygon=polygon)))
    mesh = profile_mesh(wall,polygon,1.,2.,((0,0),(1,0)),upper_at=lambda x,y:1.2+.5*x)
    assert mesh.triangles
    assert all(1.-1e-9 <= z <= 1.2+.5*x+1e-9 for x,y,z in mesh.positions)
    assert all(x >= y+.11905-1e-9 for x,y,z in mesh.positions)


def test_serialization_and_gltf_use_the_same_surface(siding_wall):
    mesh = mesh_for(siding_wall)
    layer = replace(siding_wall.layers[-1],surface_mesh=mesh)
    assert_wire_mesh(_layer_json(layer)['surface_mesh'], mesh.positions, mesh.triangles)
    builder = _MeshBuilder()
    _add_wall_body(builder,replace(siding_wall,layers=(layer,)),'core')
    buckets = list(builder.buckets())
    assert len(buckets) == 1
    _,positions,indices = buckets[0]
    assert positions == [(x,z,-y) for x,y,z in mesh.positions]
    assert len(indices) == 3*len(mesh.triangles)


def test_incompatible_layer_depth_reports_error(siding_wall):
    polygon = [(0,-.13),(1,-.13),(1,-.1),(0,-.1)]
    with pytest.raises(ValueError,match='3/4 inch'):
        profile_mesh(siding_wall,polygon,0,3,((0,0),(1,0)))


def test_rotated_facade_preserves_dimensions_and_outward_normals(siding_wall):
    angle = .73
    c,s = math.cos(angle),math.sin(angle)
    def rotate(p):
        return (4+c*p[0]-s*p[1],6+s*p[0]+c*p[1])
    wall = replace(siding_wall,axis=tuple(rotate(p) for p in siding_wall.axis),
                   layers=tuple(replace(layer,polygon=[rotate(p) for p in layer.polygon])
                                for layer in siding_wall.layers))
    mesh = profile_mesh(wall,wall.layers[-1].polygon,0,3,(rotate((0,0)),rotate((1,0))))
    baseline = mesh_for(siding_wall)
    assert len(mesh.triangles) == len(baseline.triangles)
    for actual,point in zip(mesh.positions,baseline.positions,strict=True):
        x,y = rotate(point)
        assert actual == pytest.approx((x,y,point[2]))


def test_band_cap_remains_flat_where_it_intersects_a_rake(siding_wall):
    mesh = profile_mesh(siding_wall,siding_wall.layers[-1].polygon,1.,2.,((0,0),(1,0)),
                        upper_at=lambda x,y: 1.5+x)
    assert max(z for _,_,z in mesh.positions) == pytest.approx(2.)
    assert all(z <= min(2.,1.5+x)+1e-9 for x,_,z in mesh.positions)
    assert any(x > .8 and z == pytest.approx(2.) for x,_,z in mesh.positions)


def test_empty_band_has_no_surface(siding_wall):
    assert not profile_mesh(siding_wall,siding_wall.layers[-1].polygon,2,2,((0,0),(1,0))).triangles
