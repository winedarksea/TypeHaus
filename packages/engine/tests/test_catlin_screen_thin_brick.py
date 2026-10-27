"""Screen veneer regressions: east/west datums, actual areas/mass and stopped door."""

import pytest

from typehaus.resolve.assembly_weight import dead_load_plf, wall_line_plf
from typehaus.takeoff.envelope import (
    envelope_layer_takeoff,
    wall_layer_net_area_m2,
    wall_net_areas_m2,
)

INCH = 0.0254


def test_east_brick_does_not_move_studs_or_west_skin(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    layers = {layer.name: layer for layer in wall.layers}
    for name, expected in {
        "stud": (70.25, 73.75),
        "cdx-out": (69.625, 70.25),
        "cladding-out": (68.75, 69.625),
        "packing-in": (73.75, 74.875),
        "siding-in": (74.875, 75.5),
        "wrb-in": (75.5, 75.51),
        "drainage-in": (75.51, 75.76),
        "cement-board-in": (75.76, 76.26),
        "thin-brick-in": (76.385, 76.885),
    }.items():
        xs = [x / INCH for x, _y in layers[name].polygon]
        assert (min(xs), max(xs)) == pytest.approx(expected)
    assert "bond-membrane-in" not in layers
    mortar_xs = [x / INCH for x, _ in layers["setting-mortar-in"].polygon]
    backer_xs = [x / INCH for x, _ in layers["cement-board-in"].polygon]
    assert min(mortar_xs) == pytest.approx(max(backer_xs))
    assert wall.axis[0][0] / INCH == pytest.approx(72)
    assert tuple(v / INCH for v in layers["thin-brick-in"].band(wall)) == pytest.approx((2, 47.5))
    assert layers["thin-brick-in"].thickness_m / INCH == pytest.approx(0.5)
    assert min(x for x, _ in layers["siding-in"].polygon) / INCH - 74.75 == pytest.approx(0.125)
    assert catlin_model_ro.plan.by_tag(wall.tag).shear_panel.sheathing_layer == "cdx-out"
    for tag in ("TR-BW-BRICK-BASE", "TR-BW-BRICK-HEAD"):
        flashing = catlin_model_ro.plan.by_tag(tag)
        nose = flashing.path[0].x.meters + flashing.thickness.meters / 2
        assert nose / INCH == pytest.approx(77.010)


def test_veneer_uses_its_own_net_area_and_purchased_slip_appearance(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    veneer = next(layer for layer in wall.layers if layer.name == "thin-brick-in")
    net = wall_net_areas_m2(catlin_model_ro)[wall.tag]
    screen_ft2 = wall_layer_net_area_m2(catlin_model_ro, wall, veneer, net) * 10.7639104
    assert screen_ft2 == pytest.approx(79.375 * 45.5 / 144, abs=0.1)
    # Rows carry no wall tags; the takeoff's one thin-brick row is the screen's area alone.
    envelope_rows = envelope_layer_takeoff(catlin_model_ro)
    rows = [
        row
        for row in envelope_rows
        if row["material"] == "thin-brick-brown"
    ]
    assert not any(
        row["material"] == "mvis-air-water-barrier"
        for row in envelope_rows
    )
    assert len(rows) == 1
    assert rows[0]["net_area_sqft"] == pytest.approx(screen_ft2, abs=0.05)  # row rounds to 0.1
    material = next(
        m for m in catlin_model_ro.plan.library.materials if m.tag == "thin-brick-brown"
    )
    assert (material.finish, material.color) == ("brown-brick", "#a07c5c")
    assert material.product_ref == "PROD-BW-THIN-BRICK"


def test_screen_load_is_known_and_skirt_is_not_its_bearing(catlin_ctx):
    from typehaus.checks.structural.masonry_load import support_at

    wall = catlin_ctx.model.wall("W-BW-SCREEN")
    own = dead_load_plf(catlin_ctx, wall, wall.z1_m - wall.z0_m)
    assert own == pytest.approx(74.84, abs=0.02)
    total, basis = wall_line_plf(catlin_ctx, wall)
    assert total is not None and total > own
    assert "SB-BW-BAND" in basis
    assert support_at(catlin_ctx, wall, wall.axis[0])[1] != "W-BW-SCREEN-SKIRT"


def test_normal_swing_reaches_exports_and_preserves_east_jamb(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    hinge = door.swing_clearance[0]
    tip = door.swing_clearance[-1]
    assert door.type_ref == "DT-EXT-SWING32-G"
    assert door.width_m / INCH == pytest.approx(32)
    assert hinge[0] / INCH == pytest.approx(83)
    assert (hinge[0] + door.width_m) / INCH == pytest.approx(115)
    assert (tip[0] - hinge[0]) / INCH == pytest.approx(0)
    assert (tip[1] - hinge[1]) / INCH == pytest.approx(-32)
    exported = next(o for o in model_to_dict(catlin_model_ro)["openings"] if o["tag"] == door.tag)
    assert exported["maximum_opening_degrees"] == 90
    assert exported["swing_assembly"]["supplier_confirmed"] is False
    assert catlin_model_ro.plan.by_tag(
        "SL-D-NORTH-BRIDGE"
    ).cut_origin.x.meters / INCH == pytest.approx(99)


def test_schematic_sweep_reports_hold_down_conflict_without_claiming_release(catlin_model_ro):
    from typehaus.resolve.door_swing_envelope import clearance_results

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    assert not door.swing_assembly.supplier_confirmed
    results = clearance_results(catlin_model_ro, door, 90)
    conflicts = [result for result in results
                 if result.obstacle == "CN-G-BWHD-S-DR" and result.component == "leaf"]
    assert conflicts
    assert min(result.clearance_m for result in conflicts) / INCH == pytest.approx(-0.125)
    assert any(result.obstacle == "W-BW-SCREEN" for result in results)
    assert any(result.obstacle == "PT-BW-CNW" for result in results)
    assert any(result.obstacle.startswith("TR-BW-BRICK-HEAD") for result in results)


def test_schematic_eastward_hold_down_study_clears_without_moving_authored_connector(
        catlin_model_ro):
    from dataclasses import replace

    from typehaus.resolve.door_swing_envelope import clearance_results

    model = catlin_model_ro
    door = next(o for o in model.openings if o.tag == "D-G-SERVICE")
    connector = model.plan.by_tag("CN-G-BWHD-S-DR")
    elements = []
    for element in model.geometry.elements:
        if element.uid == connector.uid:
            parts = []
            for part in element.parts:
                solids = tuple(replace(solid, positions=tuple(
                    (x + 1.5 * INCH, y, z) for x, y, z in solid.positions))
                    for solid in part.solids)
                parts.append(replace(part, solids=solids))
            element = replace(element, parts=tuple(parts))
        elements.append(element)
    study = replace(model, geometry=replace(model.geometry, elements=tuple(elements)))
    results = clearance_results(study, door, 90)
    assert any(result.obstacle == connector.tag for result in results)
    assert all(result.clearance_m >= door.swing_assembly.minimum_clearance.meters
               for result in results)
    assert connector.position.x.meters / INCH == pytest.approx(115.75)


def test_service_door_takeoff_uses_masonite_32in_price(catlin_model_ro):
    from _helpers import CATLIN

    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.openings import opening_takeoff

    rows = [r for r in opening_takeoff(catlin_model_ro) if "D-G-SERVICE" in r["tags"]]
    assert len(rows) == 1
    assert (rows[0]["type"], rows[0]["width_in"], rows[0]["count"]) == ("DT-EXT-SWING32-G", 32, 1)
    door_type = next(t for t in catlin_model_ro.plan.library.door_types if t.tag == rows[0]["type"])
    assert door_type.product_ref == "PROD-MASONITE-STEEL-FLUSH"
    prices = load_prices(CATLIN)
    assert "finish-door-closer-hold-open" not in prices.allowances
    from dataclasses import replace

    estimate = estimate_costs({"openings": rows}, replace(prices, allowances={}))
    assert estimate["sections"]["openings"]["subtotal"]["low"] >= 620
    assert estimate["sections"]["openings"]["subtotal"]["high"] >= 1320
    assert not estimate["unpriced"]
