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
    assert len(model.window_returns) == 39
    assert len({r.uid for r in model.window_returns}) == 39
    walls = {w.tag: w for w in model.walls}
    for reveal in model.window_returns:
        if reveal.fabricated:
            continue
        layers = walls[reveal.wall_tag].layers
        assert tuple(layer.material_ref for layer in reveal.layers) == tuple(
            layer.material_ref for layer in layers[:2])
        assert reveal.layers[1].thickness_m == pytest.approx(layers[1].thickness_m)
    assert sum(r.layers[0].material_ref == 'latex-paint-accent'
               for r in model.window_returns) == 1
    excluded = {o.tag for o in model.openings if o.kind == 'window'} - {
        r.window_ref for r in model.window_returns}
    assert len(excluded) == 1
    assert {walls[o.host_wall].assembly for o in model.openings if o.tag in excluded} == {
        'SAUNA_LINER_ON_GARDEN_FRAMED'}
    stool_windows = {s.window_ref for s in model.window_stools}
    assert len([r for r in model.window_returns if r.window_ref not in stool_windows]) == 2


def test_plant_windows_take_the_stools_corian_frame(catlin_model_ro):
    """O4-105: the liner has no gypsum, so the stool's authored picture frame is the return."""
    from typehaus.takeoff.countertops import countertop_takeoff

    model = catlin_model_ro
    framed = [r for r in model.window_returns if r.fabricated]
    assert sorted(r.window_ref for r in framed) == [f'WIN-S-PLANT{i}' for i in range(1, 5)]
    for reveal in framed:
        # The frame, then the liner's layers closing the strip under the stool.
        assert [layer.material_ref for layer in reveal.layers] == [
            'solid-surface-fabricated', 'pvc-panel', 'spf', 'humid-room-membrane', 'gwb']
        assert reveal.bead_length_m == 0.0
        assert [p.edge for p in reveal.pieces] == ['jamb-left', 'jamb-right', 'head']
    row = next(r for r in countertop_takeoff(model)
               if r['material'] == 'solid-surface-fabricated')
    assert row['returns'] == sorted(r.tag for r in framed)


def test_returns_reach_viewer_and_glb_with_material_and_trade(catlin_model_ro):
    model = catlin_model_ro
    solids = {s.uid: s for s in model.solids if s.category == 'window_return'}
    # 39 returns x jambs + head, 3 laps on each of the 37 bucked, and a sill lap per board
    # under 33 gypsum stools and 4 liners' 4 layers; paint has no solid.
    assert len(solids) == 277
    payload = model_to_dict(model)
    rows = [row for row in payload['solids'] if row['category'] == 'window_return']
    assert {row['uid'] for row in rows} == set(solids)
    # A solid-surface frame is the fabricator's, gypsum the drywaller's, and a liner's
    # layers under a stool go to whoever hangs that layer on the wall.
    trade = {'solid-surface-fabricated': 'countertops', 'pvc-panel': 'carpentry',
             'spf': 'framing', 'humid-room-membrane': 'insulation'}
    assert all(row['host_ref'] and row['trades'] == [trade.get(row['material'], 'drywall')]
               for row in rows)
    gltf, _ = emit_gltf_dict(model)
    nodes = [n for n in gltf['nodes'] if n['extras'].get('uid') in solids]
    assert len(nodes) == len(solids)
    materials = {m.tag: m for m in model.plan.library.materials}
    from typehaus.emit.gltf.palette import _authored_material_color
    for node in nodes:
        solid = solids[node['extras']['uid']]
        assert node['extras']['trade'] == trade.get(solid.material, 'drywall')
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
    assert len(products) == len(solids) == 277
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
        'gwb', 'gwb-ar', 'gwb-mr', 'paint-wall', 'paint-wet', 'latex-paint-accent',
        'pvc-panel', 'spf', 'humid-room-membrane'}
    assert all(not r['also_in_sheet_goods'] for r in rows)
    board_area = sum(layer.area_m2 for r in model.window_returns
                     for layer in (r.layers[1:] if r.fabricated else r.layers)
                     if layer.material_ref.startswith('gwb'))
    # The gypsum family: the plain board plus the AR and MR returns, each rounded to 0.1 SF.
    gypsum = sum(r['net_area_sqft'] for r in rows if r['material'].startswith('gwb'))
    assert gypsum == pytest.approx(board_area / 0.09290304, abs=0.2)
    beads = [r for r in return_bom['drywall_trims']
             if r['kind'] in ('window_corner', 'window_frame')]
    assert {r['kind'] for r in beads} == {'window_corner', 'window_frame'}
    returns_ft = sum(r.bead_length_m for r in model.window_returns) / 0.3048
    for kind in ('window_corner', 'window_frame'):
        assert sum(r['length_ft'] for r in beads if r['kind'] == kind) == pytest.approx(
            returns_ft, abs=0.05 * len(beads))
    labels = LabelIndex.from_plan(model.plan)
    estimate = estimate_costs(return_bom, Prices(path=Path('unused')), labels=labels)
    unpriced = [r for r in estimate['unpriced'] if r['section'] == 'drywall_trims']
    assert len(unpriced) == len(return_bom['drywall_trims'])
    assert not [r for r in estimate_rows(estimate) if r['section'] == 'drywall_trims']
    packages = build_bid_packages(model, return_bom, labels=labels)
    lines = [line for group in packages['drywall'].groups for line in group.lines
             if line.section == 'drywall_trims']
    assert lines and all(line.unit == 'LF' for line in lines)
    assert {r['material'] for r in beads} <= {line.key for line in lines}


def test_an_outie_return_rides_the_buck_to_the_frame_on_a_furred_jamb(catlin_model_ro):
    """C2-E1: one gypsum plane from the room to the frame; the stud zone furred to it."""
    from typehaus.resolve.geometry import opening_center, wall_frame
    from typehaus.resolve.geometry_members import member_box

    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "WIN-M-BED-W1")
    wall = model.wall(opening.host_wall)
    _origin, tangent, _normal, _ = wall_frame(wall)
    centre = opening_center(wall, opening)

    def along(x, y):
        return ((x - centre[0]) * tangent[0] + (y - centre[1]) * tangent[1]) / 0.0254

    half = opening.width_m / 2 / 0.0254
    jamb = next(s for s in model.solids if s.tag == "WIN-M-BED-W1-return-1-jamb-left")
    # 3/8" buck + 20 mil membrane inside the framed RO, the board 1/2" on it.
    assert min(along(*p) for p in jamb.outline) == pytest.approx(-half + 0.395, abs=1e-6)
    furs = [m for m in wall.members if m.child_key.endswith("-WIN-M-BED-W1")
            and m.child_key.startswith("buck-fur-jamb")]
    assert len(furs) == 2
    left = next(m for m in furs if "jamb-l" in m.child_key)
    xs = [along(*p[:2]) for p in member_box(left).corners_bottom]
    assert (min(xs), max(xs)) == (pytest.approx(-half), pytest.approx(-half + 0.375))


def test_a_stool_bears_on_a_packer_over_a_full_depth_buck_sill(catlin_model_ro):
    """The buck sill reaches the rough sill, a packer carries the stool, the board closes up."""
    from typehaus.resolve.framing.footprint import member_footprint
    from typehaus.resolve.geometry import wall_frame
    from typehaus.resolve.geometry_millwork import window_stool_prism

    model = catlin_model_ro
    openings = {o.tag: o for o in model.openings}
    checked = 0
    for stool in model.window_stools:
        opening = openings[stool.window_ref]
        wall = model.wall(opening.host_wall)
        packers = [m for m in wall.members
                   if m.child_key.startswith("buck-fur-stool") and opening.tag in m.child_key]
        if not packers:
            continue  # an unlined opening
        origin, tangent, normal, _ = wall_frame(wall)

        def at(member, axis, base=origin):
            ring = member_footprint(member)[0]
            values = [(x - base[0]) * axis[0] + (y - base[1]) * axis[1] for x, y in ring]
            return min(values), max(values)

        ro_sill = wall.base_ref_z_m + opening.sill_m
        rough = next(m for m in wall.members if m.category == "sill"
                     and not m.child_key.startswith("buck-") and m.z1_m == pytest.approx(ro_sill)
                     and abs(sum(at(m, tangent)) / 2 - opening.center_along_m)
                     < opening.width_m / 2)
        buck = next(m for m in wall.members if m.child_key.startswith("buck-sill-")
                    and m.z0_m == pytest.approx(ro_sill)
                    and abs(sum(at(m, tangent)) / 2 - opening.center_along_m) < 1e-6)
        r_lo, r_hi = at(rough, normal)
        b_lo, b_hi = at(buck, normal)
        assert b_lo <= r_lo + 1e-6 and b_hi >= r_hi - 1e-6, opening.tag
        underside = window_stool_prism(wall, opening, stool).z0_m
        assert 0 <= underside - max(m.z1_m for m in packers) <= 0.25 * 0.0254, opening.tag
        laps = [s for s in model.solids if s.host_ref == opening.tag
                and s.tag.endswith("-lap-sill")]
        assert laps and all(s.z0_m == pytest.approx(ro_sill)
                            and s.z1_m == pytest.approx(underside) for s in laps), opening.tag
        checked += 1
    assert checked == 37
