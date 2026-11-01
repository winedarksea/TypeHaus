"""Screen veneer regressions: east/west datums, actual areas/mass and stopped door."""

import math

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
    # Every face is 3 3/8" east of its 2026-10-25 station: the screen moved with its chord
    # posts onto the garage truss bearing line (2026-10-31).
    for name, expected in {
        "stud": (73.625, 77.125),
        "cdx-out": (73, 73.625),
        "cladding-out": (72.125, 73),
        "packing-in": (77.125, 78.25),
        "siding-in": (78.25, 78.875),
        "wrb-in": (78.875, 78.885),
        "drainage-in": (78.885, 79.135),
        "cement-board-in": (79.135, 79.635),
        "thin-brick-in": (79.76, 80.26),
    }.items():
        xs = [x / INCH for x, _y in layers[name].polygon]
        assert (min(xs), max(xs)) == pytest.approx(expected)
    assert "bond-membrane-in" not in layers
    mortar_xs = [x / INCH for x, _ in layers["setting-mortar-in"].polygon]
    backer_xs = [x / INCH for x, _ in layers["cement-board-in"].polygon]
    assert min(mortar_xs) == pytest.approx(max(backer_xs))
    assert wall.axis[0][0] / INCH == pytest.approx(75.375)
    assert tuple(v / INCH for v in layers["thin-brick-in"].band(wall)) == pytest.approx((2, 47.5))
    assert layers["thin-brick-in"].thickness_m / INCH == pytest.approx(0.5)
    assert min(x for x, _ in layers["siding-in"].polygon) / INCH - 78.125 == pytest.approx(0.125)
    assert catlin_model_ro.plan.by_tag(wall.tag).shear_panel.sheathing_layer == "cdx-out"
    for tag in ("TR-BW-BRICK-BASE", "TR-BW-BRICK-HEAD"):
        flashing = catlin_model_ro.plan.by_tag(tag)
        nose = flashing.path[0].x.meters + flashing.thickness.meters / 2
        assert nose / INCH == pytest.approx(80.385)


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
    # Opening geometry is the 34-inch RO; the 32-inch leaf hinges 1" inside it, at the
    # jamb face (resolve/door_sizing), and sweeps its own width.
    assert door.width_m / INCH == pytest.approx(34)
    assert hinge[0] / INCH == pytest.approx(82)
    assert hinge[0] / INCH - 1 + door.width_m / INCH == pytest.approx(115)
    # Stopped at 81deg, not 90 (the moved screen): the tip sits 32 cos 81 east of the hinge.
    assert (tip[0] - hinge[0]) / INCH == pytest.approx(32 * math.cos(math.radians(81)))
    assert (tip[1] - hinge[1]) / INCH == pytest.approx(-32 * math.sin(math.radians(81)))
    exported = next(o for o in model_to_dict(catlin_model_ro)["openings"] if o["tag"] == door.tag)
    assert exported["maximum_opening_degrees"] == 81
    assert catlin_model_ro.plan.by_tag(
        "SL-D-NORTH-BRIDGE"
    ).cut_origin.x.meters / INCH == pytest.approx(99)


def _service_sweep(model, **overrides):
    from scripts.garage_service_door_clearance import service_door_clearance

    return service_door_clearance(model, **overrides)


def test_stock_leaf_sweep_clears_hold_down_and_screen_with_required_margin(catlin_model_ro):
    """At the authored 81deg stop the landing ties govern; the screen face is under 1"."""
    results = _service_sweep(catlin_model_ro)
    anchor = [result for result in results if result.obstacle == "CN-G-BWHD-S-DR"]
    assert min(result.clearance_m for result in anchor) / INCH == pytest.approx(2.873, abs=1e-3)
    assert results[0].obstacle == "CN-BW-GWTIE-LO"
    assert min(result.clearance_m for result in results) / INCH == pytest.approx(0.320, abs=1e-3)
    assert any(result.obstacle == "W-BW-SCREEN" for result in results)
    assert any(result.obstacle == "PT-BW-CNW" for result in results)
    assert any(result.obstacle.startswith("TR-BW-BRICK-HEAD") for result in results)


@pytest.mark.parametrize("inset_in", [0.5, 1.0, 2.0])
def test_stock_leaf_clears_across_the_hinge_inset_range(catlin_model_ro, inset_in):
    """The 1/2in pivot inset is the LOWER bound the landing ties need, not a conservative
    pick: the 32in leaf passes from 1/2in to 2in, and a flush hinge fails."""
    from typehaus.quantities import inch

    results = _service_sweep(catlin_model_ro, hinge_inset=inch(inset_in))
    assert min(result.clearance_m for result in results) / INCH >= 0.25


def test_a_90_degree_stop_meets_the_moved_screen(catlin_model_ro):
    """Why the stop is 81deg: the screen moved 3 3/8" east with the canopy posts."""
    from scripts.garage_service_door_clearance import clearance_results, service_door_envelope

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    results = clearance_results(catlin_model_ro, door, 90, service_door_envelope())
    hit = {r.obstacle for r in results if r.clearance_m < 0}
    assert {"W-BW-SCREEN", "TR-BW-BRICK-BASE-1", "CN-BW-GWTIE-LO"} <= hit


def test_a_flush_hinge_fails(catlin_model_ro):
    from typehaus.quantities import inch

    results = _service_sweep(catlin_model_ro, hinge_inset=inch(0))
    assert results[0].clearance_m / INCH < 0.25


def test_the_old_schematic_leaf_overlaps_the_hold_down(catlin_model_ro):
    """34in leaf at the old x=83in hinge: the pass depends on the purchased 32in leaf."""
    from typehaus.quantities import inch

    results = _service_sweep(catlin_model_ro, hinge_inset=inch(2), leaf_end=inch(34))
    anchor = [result for result in results if result.obstacle == "CN-G-BWHD-S-DR"]
    assert min(result.clearance_m for result in anchor) < 0


def test_r311_2_grades_the_purchased_leaf_not_the_rough_opening(catlin_ctx):
    """D-G-SERVICE is sized off its 32in leaf, not its published 34in RO, and is not the
    designated egress door, so R311.2 says nothing about it (decision #97)."""
    from typehaus.checks.code.mn_residential.egress_door import (
        egress_door_height,
        egress_door_width,
    )

    door_type = next(t for t in catlin_ctx.plan.library.door_types
                     if t.tag == "DT-EXT-SWING32-G")
    ro = door_type.rough_opening
    assert (ro.width.inches, ro.height.inches) == pytest.approx((34, 81.5))
    sizing = next(o.sizing for o in catlin_ctx.model.openings if o.tag == "D-G-SERVICE")
    assert sizing.leaf_w_m / 0.0254 == pytest.approx(32)
    # The deduction at 90deg, less what the leaf still crosses at its 81deg stop.
    assert sizing.clear_w_m / 0.0254 == pytest.approx(
        32 - 2 - 11 / 16 - 32 * math.cos(math.radians(81)))
    for check in (egress_door_width, egress_door_height):
        assert not [f for f in check(catlin_ctx) if "D-G-SERVICE" in f.message]


def test_service_door_takeoff_uses_mmi_32in_price(catlin_model_ro):
    from _helpers import CATLIN

    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.openings import opening_takeoff

    rows = [r for r in opening_takeoff(catlin_model_ro) if "D-G-SERVICE" in r["tags"]]
    assert len(rows) == 1
    assert (rows[0]["type"], rows[0]["width_in"], rows[0]["count"]) == ("DT-EXT-SWING32-G", 32, 1)
    door_type = next(t for t in catlin_model_ro.plan.library.door_types if t.tag == rows[0]["type"])
    assert door_type.product_ref == "PROD-MMI-STEEL-SIX-PANEL"
    prices = load_prices(CATLIN)
    assert "finish-door-closer-hold-open" not in prices.allowances
    from dataclasses import replace

    row = prices.openings["DT-EXT-SWING32-G"]
    estimate = estimate_costs({"openings": rows}, replace(prices, allowances={}))
    subtotal = estimate["sections"]["openings"]["subtotal"]
    assert (subtotal["low"], subtotal["high"]) == pytest.approx((row.low, row.high))
    assert not estimate["unpriced"]
