"""Tub enclosure identity, materials and physical extents survive every delivery format."""

import pytest

from typehaus.resolve.tub_enclosures import ENCLOSURE_CATEGORIES

pytestmark = pytest.mark.slow


def test_json_and_glb_preserve_each_enclosure_piece(catlin_model_ro):
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.gltf.palette import _authored_material_color
    from typehaus.server.model_json import model_to_dict

    model = catlin_model_ro
    solids = {s.uid: s for s in model.solids if s.category in ENCLOSURE_CATEGORIES}
    payload = model_to_dict(model)
    rows = {row['uid']: row for row in payload['solids'] if row['uid'] in solids}
    assert rows.keys() == solids.keys()
    for uid, row in rows.items():
        solid = solids[uid]
        assert row['outline'] == [list(p) for p in solid.outline]
        assert row['z0_m'] == solid.z0_m and row['z1_m'] == solid.z1_m
        assert row['host_ref'] == 'FX-M-BATH2-TUB'
        assert row['material'] == solid.material
        expected = 'plumbing' if solid.category == 'tub_mortar_bed' else 'insulation'
        assert row['trades'] == [expected]
    gltf, _binary = emit_gltf_dict(model)
    nodes = {n['extras'].get('uid'): n for n in gltf['nodes']
             if n['extras'].get('uid') in solids}
    assert nodes.keys() == solids.keys()
    materials = {m.tag: m for m in model.plan.library.materials}
    for uid, node in nodes.items():
        solid = solids[uid]
        assert node['extras']['trades'] == rows[uid]['trades']
        assert node['extras']['host_ref'] == solid.host_ref
        assert node['extras']['material_ref'] == solid.material
        primitive = gltf['meshes'][node['mesh']]['primitives'][0]
        accessor = gltf['accessors'][primitive['attributes']['POSITION']]
        xs, ys = zip(*solid.outline, strict=True)
        assert accessor['min'] == pytest.approx((min(xs), solid.z0_m, -max(ys)))
        assert accessor['max'] == pytest.approx((max(xs), solid.z1_m, -min(ys)))
        color = gltf['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor']
        assert color == pytest.approx(_authored_material_color(materials[solid.material]))
        part = model.geometry.part(uid, 'body')
        assert part.catalog.material_ref == solid.material
        if solid.category != 'tub_mortar_bed':
            assert part.layer_group == 'insulation'


def test_framed_ifc_has_materialized_insulation_and_the_open_tub(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell
    import ifcopenshell.util.element

    from typehaus._meta import PSET_SOURCE
    from typehaus.model.ids import derive_guid

    model = catlin_model_ro
    file = ifcopenshell.open(str(catlin_ifc_path))
    products = {p.Name: p for p in file.by_type('IfcProduct')}
    for solid in model.solids:
        if solid.category not in ENCLOSURE_CATEGORIES:
            continue
        product = products[solid.tag]
        if solid.category != 'tub_mortar_bed':
            assert product.is_a('IfcCovering') and product.PredefinedType == 'INSULATION'
        assert product.GlobalId == derive_guid(model.plan.project.project_uuid, solid.uid)
        source = ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]
        assert source['host_ref'] == solid.host_ref
        assert ifcopenshell.util.element.get_material(product).Name == solid.material
        shape = product.Representation.Representations[0].Items[0]
        assert shape.Depth == pytest.approx(solid.z1_m-solid.z0_m)
        assert {tuple(p.Coordinates) for p in shape.SweptArea.OuterCurve.Points[:-1]} == {
            tuple(p) for p in solid.outline}
    tub = products['FX-M-BATH2-TUB']
    assert tub.is_a('IfcSanitaryTerminal')
    assert tub.Representation.Representations[0].RepresentationType == 'Tessellation'
    assert any(item.is_a('IfcTriangulatedFaceSet')
               for item in tub.Representation.Representations[0].Items)
