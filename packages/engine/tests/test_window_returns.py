"""Fitted return geometry, inherited finishes, and quantities on small synthetic walls."""

from dataclasses import replace
from itertools import combinations
from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon

from typehaus.library.materials import ALL_MATERIALS
from typehaus.model import Library, Material, Storey, ft
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import (
    ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedRoom, ResolvedWall,
    ResolvedWindowStool,
)
from typehaus.resolve.window_returns import resolve_window_returns
from typehaus.takeoff.window_returns import window_return_bead_rows, window_return_finish_rows


@pytest.fixture
def return_model():
    def make(*, coating=True, boards=(0.015875,), material='gwb', enabled=True,
             occupancy='living', face=-0.18):
        layers = []
        offset = face
        specs = ([('paint', 'latex-paint', 0.000254)] if coating else [])
        specs += [(f'board-{i}', material, thickness) for i, thickness in enumerate(boards)]
        specs += [('stud', 'spf', 0.1397), ('clad', 'fiber-cement', 0.008)]
        for name, ref, thickness in specs:
            layers.append(ResolvedLayer(name, ref, 'cladding' if name == 'clad' else 'finish',
                                        thickness, [(0, offset), (4, offset),
                                                    (4, offset + thickness),
                                                    (0, offset + thickness)]))
            offset += thickness
        wall = ResolvedWall('wall-uid', 'W', 'main', 'EXT', ((0, 0), (4, 0)),
                            tuple(layers), 0, 3)
        opening = ResolvedOpening('window-uid', 'WIN', 'W', None, 1.2, 1.5, 0.8, 2,
                                  'window', False)
        authored = SimpleNamespace(drywall_returns=enabled)
        plan = SimpleNamespace(library=Library(materials=(*ALL_MATERIALS, Material(
            tag="latex-paint-accent", name="Accent paint", coating=True, color="#453344"))),
                               by_tag=lambda tag: authored,
                               storeys=(Storey(tag='main', elevation=ft(0),
                                               default_ceiling_height=ft(10)),))
        model = ResolvedModel(plan=plan, walls=[wall], openings=[opening])
        room = ResolvedRoom('room-uid', 'RM', 'main', occupancy, True,
                            [(0, -3), (4, -3), (4, 0), (0, 0)], 12, None)
        model.rooms.append(room)
        return model
    return make


def _assert_no_overlap(solids):
    for first, second in combinations(solids, 2):
        z = min(first.z1_m, second.z1_m) - max(first.z0_m, second.z0_m)
        if z > 1e-9:
            assert Polygon(first.outline).intersection(Polygon(second.outline)).area < 1e-12


def test_pieces_fit_frame_and_never_overlap_glazing_or_each_other(return_model):
    model = return_model()
    assert not resolve_window_returns(model)
    reveal, = model.window_returns
    assert len(model.solids) == 9
    assert {layer.material_ref for layer in reveal.layers} == {'gwb', 'latex-paint'}
    _assert_no_overlap(model.solids)
    frame = opening_parts(model.walls[0], model.openings[0], None)
    for part in frame:
        for solid in part.solids:
            for lining in model.solids:
                overlap_z = min(solid.z1_m, lining.z1_m) - max(solid.z0_m, lining.z0_m)
                if overlap_z > 1e-9:
                    assert Polygon(solid.ring).intersection(Polygon(lining.outline)).area < 1e-12
    for layer in reveal.layers:
        pieces = [s for s in model.solids if s.material == layer.material_ref]
        # Board area is volume divided by its stated thickness, including the lapped head.
        area = sum(Polygon(s.outline).area * (s.z1_m - s.z0_m)
                   for s in pieces) / layer.thickness_m
        if layer.coating:
            assert layer.area_m2 == pytest.approx(reveal.exposed_area_m2)
        else:
            assert layer.area_m2 == pytest.approx(area)
    assert not reveal.derived_paint
    rows = window_return_finish_rows(model)
    assert {r['material'] for r in rows} == {'gwb', 'latex-paint'}
    beads = window_return_bead_rows(model)
    assert len(beads) == 2
    assert all(row['length_ft'] == round(reveal.bead_length_m / 0.3048, 1) for row in beads)
    assert all(row['tags'] == ['WIN'] for row in beads)
    old_solids = list(model.solids)
    assert not resolve_window_returns(model)
    assert model.solids == old_solids, 'rerunning must replace, not duplicate, returns'


def test_inherits_double_gypsum_and_accent_coating(return_model):
    model = return_model(boards=(0.0127, 0.015875))
    wall = model.walls[0]
    model.walls[0] = replace(wall, layers=(replace(wall.layers[0],
                                                material_ref='latex-paint-accent'),
                                          *wall.layers[1:]))
    assert not resolve_window_returns(model)
    reveal, = model.window_returns
    assert [layer.thickness_m for layer in reveal.layers] == [0.000254, 0.0127, 0.015875]
    assert reveal.layers[0].material_ref == 'latex-paint-accent'
    _assert_no_overlap(model.solids)


@pytest.mark.parametrize('occupancy,painted', [('living', True), ('unconditioned', False)])
def test_derived_paint_uses_the_existing_room_occupancy_rule(return_model, occupancy, painted):
    model = return_model(coating=False, occupancy=occupancy)
    assert not resolve_window_returns(model)
    reveal, = model.window_returns
    assert reveal.derived_paint is painted
    assert ('latex-paint' in {r['material'] for r in window_return_finish_rows(model)}) is painted


@pytest.mark.parametrize('kwargs', [{'enabled': False}, {'material': 'cedar-tg'},
                                  {'material': 'pvc-panel'}])
def test_opt_out_and_non_gypsum_liners_produce_nothing(return_model, kwargs):
    model = return_model(**kwargs)
    assert not resolve_window_returns(model)
    assert not model.window_returns
    assert not model.solids
    assert not window_return_bead_rows(model)


def test_jambs_meet_the_actual_stool_top(return_model):
    model = return_model()
    model.window_stools.append(ResolvedWindowStool(
        'stool-uid', 'STOOL', 'main', 'WIN', 'W', 'EXT', 'oak-stool',
        0.0254, 1.25, 0.15905, 0.01905, 0.0254, 'eased', None, None))
    assert not resolve_window_returns(model)
    from typehaus.resolve.geometry_millwork import window_stool_prism
    stool = window_stool_prism(model.walls[0], model.openings[0], model.window_stools[0])
    assert stool is not None
    assert all(s.z0_m == pytest.approx(stool.z1_m) for s in model.solids if 'jamb' in s.tag)
    assert all('sill' not in s.tag for s in model.solids)


def test_wall_axis_reversal_and_rotation_preserve_physical_shape(return_model):
    model = return_model()
    assert not resolve_window_returns(model)
    expected = {s.tag: (Polygon(s.outline), s.z0_m, s.z1_m) for s in model.solids}
    wall = model.walls[0]
    model.walls[0] = replace(wall, axis=tuple(reversed(wall.axis)))
    _, _, _, run = wall_frame(wall)
    model.openings[0] = replace(model.openings[0], center_along_m=run - 2)
    assert not resolve_window_returns(model)
    for solid in model.solids:
        assert any(polygon.symmetric_difference(Polygon(solid.outline)).area < 1e-12
                   and (low, high) == (solid.z0_m, solid.z1_m)
                   for polygon, low, high in expected.values())
    def rotate(point):
        x, y = point
        return (-y, x)
    wall = model.walls[0]
    model.walls[0] = replace(wall, axis=tuple(map(rotate, wall.axis)),
                            layers=tuple(replace(l, polygon=list(map(rotate, l.polygon)))
                                         for l in wall.layers))
    assert not resolve_window_returns(model)
    for solid in model.solids:
        unrotated = Polygon([(y, -x) for x, y in solid.outline])
        assert any(polygon.symmetric_difference(unrotated).area < 1e-12
                   for polygon, _, _ in expected.values())


@pytest.mark.parametrize('failure', ['arch', 'no-depth', 'band', 'too-thick'])
def test_unsupported_geometry_reports_a_finding_without_partial_solids(return_model, failure):
    model = return_model(boards=(0.08,) if failure == 'too-thick' else (0.015875,),
                         face=-0.02 if failure == 'no-depth' else -0.18)
    if failure == 'arch':
        model.openings[0] = replace(model.openings[0], arch_rise_m=0.3)
    if failure == 'band':
        wall = model.walls[0]
        model.walls[0] = replace(wall, layers=(replace(wall.layers[0], z1_m=1),
                                             *wall.layers[1:]))
    findings = resolve_window_returns(model)
    assert len(findings) == 1
    assert findings[0].result.value == 'unknown'
    assert not model.window_returns and not model.solids


def test_raked_wall_uses_the_clipped_frame_head(return_model):
    model = return_model()
    model.walls[0] = replace(model.walls[0], top_z0_m=2, top_z1_m=3)
    assert not resolve_window_returns(model)
    frame = next(p for p in opening_parts(model.walls[0], model.openings[0], None)
                 if p.key == 'frame')
    assert max(s.z1_m for s in model.solids) == pytest.approx(frame.solids[2].z1_m)


def test_beads_load_and_price_by_length_and_reach_estimate_csv(return_model, tmp_path):
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.estimate_csv import estimate_rows

    model = return_model()
    assert not resolve_window_returns(model)
    beads = window_return_bead_rows(model)
    (tmp_path / 'prices.toml').write_text(
        '[window_return_beads]\n'
        'drywall-corner-bead = 2.0\n'
        'drywall-frame-termination-bead = 3.0\n')
    prices = load_prices(tmp_path)
    assert prices is not None
    estimate = estimate_costs({'window_return_beads': beads}, prices)
    assert not estimate['unpriced']
    rows = estimate_rows(estimate)
    assert len(rows) == 2
    assert {row['trade'] for row in rows} == {'drywall'}
    assert all(row['unit'] == 'LF' for row in rows)
    for row in rows:
        rate = 2 if row['key'] == 'drywall-corner-bead' else 3
        assert row['total_low'] == pytest.approx(row['quantity'] * rate)


def test_zero_thickness_coating_bills_surface_without_degenerate_solids(return_model):
    model = return_model()
    wall = model.walls[0]
    model.walls[0] = replace(wall, layers=(replace(wall.layers[0], thickness_m=0),
                                         *wall.layers[1:]))
    assert not resolve_window_returns(model)
    assert len(model.solids) == 3
    assert all(s.material == 'gwb' for s in model.solids)
    assert next(r['net_area_sqft'] for r in window_return_finish_rows(model)
                if r['material'] == 'latex-paint') > 0
