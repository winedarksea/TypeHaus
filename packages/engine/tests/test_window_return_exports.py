"""The same fitted returns in Catlin's viewer payload, exports, estimate, and bid."""

from pathlib import Path

import pytest

from typehaus.cli.prices import Prices, estimate_costs
from typehaus.emit.gltf.emitter import emit_gltf_dict
from typehaus.resolve.solid_categories import solid_category
from typehaus.server.model_json import model_to_dict
from typehaus.takeoff.bid_package import build_bid_packages
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.estimate_csv import estimate_rows
from typehaus.takeoff.labels import LabelIndex


@pytest.fixture(scope='module')
def return_bom(catlin_model_ro):
    return bill_of_materials(catlin_model_ro)


def test_catlin_returns_inherit_finishes_and_skip_other_liners(catlin_model_ro):
    model = catlin_model_ro
    assert len(model.window_returns) == 36
    assert len({r.uid for r in model.window_returns}) == 36
    walls = {w.tag: w for w in model.walls}
    for reveal in model.window_returns:
        layers = walls[reveal.wall_tag].layers
        assert tuple(l.material_ref for l in reveal.layers) == tuple(
            l.material_ref for l in layers[:2])
        assert reveal.layers[1].thickness_m == pytest.approx(layers[1].thickness_m)
    assert sum(r.layers[0].material_ref == 'latex-paint-accent'
               for r in model.window_returns) == 1
    excluded = {o.tag for o in model.openings if o.kind == 'window'} - {
        r.window_ref for r in model.window_returns}
    assert len(excluded) == 5
    assert {walls[o.host_wall].assembly for o in model.openings if o.tag in excluded} == {
        'SAUNA_LINER_ON_GARDEN_FRAMED', 'PLANT_EXT_2X6_HUMID'}
    stool_windows = {s.window_ref for s in model.window_stools}
    assert len([r for r in model.window_returns if r.window_ref not in stool_windows]) == 2


def test_returns_reach_viewer_and_glb_with_material_and_trade(catlin_model_ro):
    model = catlin_model_ro
    solids = {s.uid: s for s in model.solids if s.category == 'window_return'}
    assert len(solids) == 324
    payload = model_to_dict(model)
    rows = [row for row in payload['solids'] if row['category'] == 'window_return']
    assert {row['uid'] for row in rows} == set(solids)
    assert all(row['trades'] == ['drywall'] and row['host_ref'] for row in rows)
    gltf, _ = emit_gltf_dict(model)
    nodes = [n for n in gltf['nodes'] if n['extras'].get('uid') in solids]
    assert len(nodes) == len(solids)
    materials = {m.tag: m for m in model.plan.library.materials}
    from typehaus.emit.gltf.palette import _authored_material_color
    for node in nodes:
        assert node['extras']['trade'] == 'drywall'
        solid = solids[node['extras']['uid']]
        mesh = gltf['meshes'][node['mesh']]
        material = gltf['materials'][mesh['primitives'][0]['material']]
        assert material['pbrMetallicRoughness']['baseColorFactor'] == pytest.approx(
            _authored_material_color(materials[solid.material]))


def test_returns_export_as_ifc_coverings(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell
    import ifcopenshell.util.element

    from typehaus._meta import PSET_SOURCE
    from typehaus.model.ids import derive_guid

    model = catlin_model_ro
    file = ifcopenshell.open(str(catlin_ifc_path))
    products = {p.Name: p for p in file.by_type('IfcCovering')
                if ifcopenshell.util.element.get_psets(p).get(PSET_SOURCE, {}).get(
                    'category') == 'window_return'}
    solids = [s for s in model.solids if s.category == 'window_return']
    assert len(products) == len(solids) == 324
    for solid in solids:
        product = products[solid.tag]
        assert product.PredefinedType == 'CLADDING'
        assert product.GlobalId == derive_guid(model.plan.project.project_uuid, solid.uid)
        source = ifcopenshell.util.element.get_psets(product)[PSET_SOURCE]
        assert source['host_ref'] == solid.host_ref
        assert ifcopenshell.util.element.get_material(product).Name == solid.material
        shape = product.Representation.Representations[0].Items[0]
        assert shape.Depth == pytest.approx(solid.z1_m - solid.z0_m)
        assert {tuple(p.Coordinates) for p in shape.SweptArea.OuterCurve.Points[:-1]} == {
            tuple(p) for p in solid.outline}


def test_bom_estimate_csv_and_drywall_bid_bill_each_item_once(catlin_model_ro, return_bom):
    model = catlin_model_ro
    assert solid_category('window_return').billed_elsewhere
    assert not any(r['category'] == 'window_return' for r in return_bom['structural_solids'])
    rows = [r for r in return_bom['envelope_layers'] if r['scope'] == 'window return']
    assert {r['material'] for r in rows} == {
        'gwb', 'gwb-ar', 'gwb-mr', 'latex-paint', 'latex-paint-accent'}
    assert all(not r['also_in_sheet_goods'] for r in rows)
    board_area = sum(l.area_m2 for r in model.window_returns for l in r.layers
                     if not l.coating)
    # The gypsum family: the plain board plus the AR and MR returns, each rounded to 0.1 SF.
    gypsum = sum(r['net_area_sqft'] for r in rows if r['material'].startswith('gwb'))
    assert gypsum == pytest.approx(board_area / 0.09290304, abs=0.2)
    beads = return_bom['window_return_beads']
    assert len(beads) == 2
    labels = LabelIndex.from_plan(model.plan)
    estimate = estimate_costs(return_bom, Prices(path=Path('unused')), labels=labels)
    unpriced = [r for r in estimate['unpriced'] if r['section'] == 'window_return_beads']
    assert len(unpriced) == 2
    assert not [r for r in estimate_rows(estimate) if r['section'] == 'window_return_beads']
    packages = build_bid_packages(model, return_bom, labels=labels)
    lines = [line for group in packages['drywall'].groups for line in group.lines
             if line.section == 'window_return_beads']
    assert len(lines) == 2
    assert all(line.unit == 'LF' for line in lines)
    assert {line.key for line in lines} == {r['material'] for r in beads}


def test_return_sections_use_the_wall_finish_layer(catlin_model_ro):
    import json

    from typehaus.emit.draw.section import build_center_section

    return_uids = {s.uid for s in catlin_model_ro.solids if s.category == 'window_return'}
    nodes = json.loads(build_center_section(catlin_model_ro).to_json())['nodes']
    outlines = [node for node in nodes if node.get('uid') in return_uids]
    assert outlines
    assert {node['layer'] for node in outlines} == {'A-WALL-FINI'}
