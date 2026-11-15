"""Screen mdo regions, geometry, quantities and stopped door regressions."""

import math

import pytest

from typehaus.resolve.assembly_weight import dead_load_plf
from typehaus.takeoff.envelope import (
    envelope_layer_takeoff,
    wall_layer_net_area_m2,
    wall_net_areas_m2,
)

INCH = 0.0254


def test_mdos_keep_posts_exposed_and_west_structure_fixed(catlin_model_ro):
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    layers = {layer.name: layer for layer in wall.layers}
    for name, expected in {"stud": (72.625, 76.125), "cdx-out": (72, 72.625),
                           "cladding-out": (71.125, 72)}.items():
        xs = [x / INCH for x, _y in layers[name].polygon]
        assert (min(xs), max(xs)) == pytest.approx(expected)
    # The MDO stops at the north chord post; the end pack and its ties stay exposed.
    expected_runs = ((0.125, 7.875), (13.625, 37.750), (43.500, 67.625))
    assert "mdo-in-4" not in layers
    for index, expected in enumerate(expected_runs, 1):
        layer = layers[f"mdo-in-{index}"]
        xs = [x / INCH for x, _ in layer.polygon]
        assert (min(xs), max(xs)) == pytest.approx((76.125, 76.875))
        assert tuple(value / INCH for value in layer.run_span_m) == pytest.approx(expected)
        assert tuple(value / INCH for value in layer.band(wall)) == pytest.approx((2, 47.5))
    assert catlin_model_ro.plan.by_tag(wall.tag).shear_panel.sheathing_layer == "cdx-out"
    assert not {"thin-brick-in", "packing-in", "cement-board-in"} & layers.keys()
    # The supplemental nailer layout reserves these existing studs; a framing change
    # must not silently put new supports or clips through existing timber.
    stud_stations = sorted((member.p0[1] - wall.axis[0][1]) / INCH
                           for member in wall.members if member.category == "stud")
    assert stud_stations == pytest.approx([0.75, 16, 32, 48, 64, 77.75])



def test_mdo_area_and_weight_use_the_same_bounded_regions(catlin_model_ro):
    from types import SimpleNamespace

    wall = catlin_model_ro.wall("W-BW-SCREEN")
    net = wall_net_areas_m2(catlin_model_ro)[wall.tag]
    layers = [layer for layer in wall.layers if layer.name.startswith("mdo-in-")]
    area = sum(wall_layer_net_area_m2(catlin_model_ro, wall, layer, net) for layer in layers)
    assert area * 10.7639104 == pytest.approx(17.694444, abs=0.001)
    rows = [row for row in envelope_layer_takeoff(catlin_model_ro)
            if row["material"] == "entry-screen-white-mdo"]
    assert len(rows) == 1
    assert rows[0]["net_area_sqft"] == pytest.approx(area * 10.7639104, abs=0.05)
    weight = dead_load_plf(SimpleNamespace(plan=catlin_model_ro.plan), wall, wall.z1_m - wall.z0_m)
    assert weight == pytest.approx(37.53005, abs=0.02)


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
    # Stopped at 87deg, not 90 (the slat band): the tip sits 32 cos 87 east of the hinge.
    assert (tip[0] - hinge[0]) / INCH == pytest.approx(32 * math.cos(math.radians(87)))
    assert (tip[1] - hinge[1]) / INCH == pytest.approx(-32 * math.sin(math.radians(87)))
    exported = next(o for o in model_to_dict(catlin_model_ro)["openings"] if o["tag"] == door.tag)
    assert exported["maximum_opening_degrees"] == 87
    assert catlin_model_ro.plan.by_tag(
        "SL-D-NORTH-BRIDGE"
    ).cut_origin.x.meters / INCH == pytest.approx(99)


def _service_sweep(model, **overrides):
    from scripts.garage_service_door_clearance import service_door_clearance

    return service_door_clearance(model, **overrides)


def test_stock_leaf_sweep_clears_hold_down_and_screen_with_required_margin(catlin_model_ro):
    """At the authored 87deg stop the lever to the screen cap governs.

    Re-pinned 2026-11-01 when the MMI frame was anchored flush with the sheathing
    (``factory_frame_depth`` 6-9/16"), which moved the leaf plane: ties 0.320 -> 0.381",
    hold-down 2.873 -> 2.865".
    """
    results = _service_sweep(catlin_model_ro)
    anchor = [result for result in results if result.obstacle == "CN-G-BWHD-S-DR"]
    assert min(result.clearance_m for result in anchor) / INCH == pytest.approx(2.865, abs=1e-3)
    assert results[0].obstacle == "TR-BW-SCREEN-CAP"
    assert min(result.clearance_m for result in results) / INCH == pytest.approx(0.641, abs=1e-3)
    assert any(result.obstacle == "W-BW-SCREEN" for result in results)
    assert any(result.obstacle == "PT-BW-CNW" for result in results)
    assert any(result.obstacle.startswith("TR-BW-MDO-") for result in results)


@pytest.mark.parametrize("inset_in", [0.5, 1.0, 2.0])
def test_stock_leaf_clears_across_the_hinge_inset_range(catlin_model_ro, inset_in):
    """The 1/2in pivot inset is the LOWER bound at the 87deg stop: the 32in leaf passes from
    1/2in to 2in, and a flush hinge fails."""
    from typehaus.quantities import inch

    results = _service_sweep(catlin_model_ro, hinge_inset=inch(inset_in))
    assert min(result.clearance_m for result in results) / INCH >= 0.25


def test_a_90_degree_stop_meets_the_band(catlin_model_ro):
    """The lever strikes the slat band at 90 degrees; the leaf now clears the ties."""
    from scripts.garage_service_door_clearance import clearance_results, service_door_envelope

    door = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    results = clearance_results(catlin_model_ro, door, 90, service_door_envelope())
    hit = {r.obstacle for r in results if r.clearance_m < 0}
    assert "SB-BW-BAND" in hit and "CN-BW-GWTIE-LO" not in hit


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
    # The deduction at 90deg, less what the leaf still crosses at its 87deg stop.
    assert sizing.clear_w_m / 0.0254 == pytest.approx(
        32 - 2 - 11 / 16 - 32 * math.cos(math.radians(87)))
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


def test_mdo_regions_reach_viewer_and_ifc(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell

    from typehaus.server.model_json import model_to_dict

    wall = catlin_model_ro.wall("W-BW-SCREEN")
    exported = next(w for w in model_to_dict(catlin_model_ro)["walls"] if w["tag"] == wall.tag)
    regions = [layer for layer in exported["layers"] if layer["name"].startswith("mdo-in-")]
    assert len(regions) == 3
    for region in regions:
        actual = next(layer for layer in wall.layers if layer.name == region["name"])
        assert region["polygon"] == [list(point) for point in actual.polygon]
    ifc = ifcopenshell.open(str(catlin_ifc_path))
    parts = {part.Name for part in ifc.by_type("IfcBuildingElementPart")}
    assert {f"W-BW-SCREEN:mdo-in-{index}" for index in range(1, 4)} <= parts
    assert not any(name.startswith("W-BW-SCREEN:mdo-in-4") for name in parts)


def test_run_spans_reject_invalid_or_overlapping_slot_regions():
    from typehaus import Layer, LayerFunction, inch
    from typehaus.checks.integrity.checks import _slot_findings

    def panel(name, start, end):
        return Layer(name=name, material_ref="metal", thickness=inch(0.05),
                     function=LayerFunction.CLADDING, slot="mdo",
                     run_span=(inch(start), inch(end)))

    with pytest.raises(ValueError):
        panel("invalid", 4, 3)
    assert not _slot_findings("test", [panel("a", 0, 4), panel("b", 4, 8)])
    assert _slot_findings("test", [panel("a", 0, 5), panel("b", 4, 8)])


def test_mdo_has_edge_supports_without_metal_rail_hardware(catlin_model_ro):
    tags = {element.tag for element in catlin_model_ro.plan.all_elements()}
    assert {f"TR-BW-MDO-NAILER-{i}" for i in (1, 2, 4, 6, 7)} <= tags
    assert "TR-BW-MDO-NAILER-5" not in tags
    assert not any(tag.startswith("TR-BW-METAL-") for tag in tags)
    wall = catlin_model_ro.wall("W-BW-SCREEN")
    assert not {"vent-in", "wrb-in"} & {layer.name for layer in wall.layers}


def _supplemental_bounds(model, tag):
    from typehaus.emit.draw.elevation_project import solid_faces

    uid = model.plan.by_tag(tag).uid
    geometry = next(element for element in model.geometry.elements if element.uid == f"{uid}-00")
    vertices = [point for part in geometry.parts for solid in part.solids
                for face in solid_faces(solid) for point in face]
    return tuple((min(point[axis] for point in vertices) / INCH,
                  max(point[axis] for point in vertices) / INCH) for axis in range(3))


def test_lower_timber_is_one_solid_6x6_and_backs_panel_edges(catlin_model_ro):
    model = catlin_model_ro
    wall = model.wall("W-BW-SCREEN")
    south = wall.axis[0][1] / INCH
    assert model.plan.by_tag("TR-BW-MDO-NAILER-3") is None
    bounds = _supplemental_bounds(model, "TR-BW-MDO-TIMBER")
    # Both faces are the band's centre post's and the chord posts'.
    assert bounds[0] == pytest.approx((72.625, 78.125))
    assert bounds[1] == pytest.approx((south + 37.875, south + 43.375))
    assert bounds[2] == pytest.approx((0.56, 45))
    for tag, station, panel_edge in (("TR-BW-MDO-NAILER-6", 37, 37.750),
                                     ("TR-BW-MDO-NAILER-7", 44.25, 43.500)):
        bounds = _supplemental_bounds(model, tag)
        assert bounds[1] == pytest.approx((south + station - 0.75, south + station + 0.75))
        # A screw 3/8in inside each new cut lands in solid framing.
        screw_station = panel_edge - 0.375 if station < 40 else panel_edge + 0.375
        assert bounds[1][0] < south + screw_station < bounds[1][1]
    # The supplemental pack does not add a Post to the engineering model.
    assert model.plan.by_tag("TR-BW-MDO-TIMBER").host_ref == wall.tag


def test_timber_schedule_weights_and_stock_nesting_are_derived_once(catlin_plan):
    from scripts.entry_screen_mdo_report import spec

    assert [(row["profile"], row["cuts"], row["boards"]) for row in spec.PURCHASING] == [
        ("2x4", 5, 3), ("6x6", 1, 1)]
    assert all(row["cuts_per_board"] * (row["cut_length_in"] + spec.SAW_KERF_IN)
               <= row["stock_length_in"] for row in spec.PURCHASING)
    assert pytest.approx(54.4263434) == spec.SUPPORT_WEIGHT_LB
    assert spec.HARDWARE_QUANTITIES == {"S10ACN": 8}
    assert pytest.approx(2.16) == spec.HARDWARE_AND_PAINT_RESERVE_LB
    material = catlin_plan.library.material("entry-screen-white-mdo")
    effective_weight = (material.areal_density_kg_m2 * spec.NET_PANEL_AREA_IN2
                        * INCH**2 * 2.2046226218)
    panel_weight = spec.NET_PANEL_AREA_IN2 * spec.PANEL_THICKNESS_IN * spec.LB_PER_IN3
    assert effective_weight == pytest.approx(panel_weight + spec.SUPPORT_WEIGHT_LB + 2.16)


def test_local_timber_and_its_end_nails_are_graded(catlin_ctx):
    from scripts.entry_screen_mdo_report import concentrated_sill_delta, local_timber_checks

    from typehaus.engineering.roof_lateral import roof_winds

    pressure = roof_winds(catlin_ctx.engineering.context)["RF-BW-CANOPY"].pressure_psf
    rows = {row["name"]: row for row in local_timber_checks(pressure)}
    # 200 lb x 44.44in / 4 / 27.729 in3 = 80.13 psi on Fb 850.
    assert rows["guard concentrated/infill: 6x6 bending"]["ratio"] == pytest.approx(
        0.09427, abs=1e-4)
    # Four S10ACN through each plate, end grain, wet, at the assumed 60 ksi floor: 196.3 lb.
    assert rows["end nails: guard reaction"]["ratio"] == pytest.approx(0.5093, abs=1e-3)
    assert all(row["status"] == "ok" for row in rows.values())
    local = concentrated_sill_delta(catlin_ctx.model)
    assert sum(row["load_lb"] for row in local["point_loads"]) == pytest.approx(34.197083)
    assert local["maximum_additional_moment_lb_in"] == pytest.approx(445.46517, abs=0.01)


def test_lower_timber_reaches_ifc_and_viewer_geometry(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell

    from typehaus.server.model_json import model_to_dict

    tags = {"TR-BW-MDO-TIMBER"}
    ifc = ifcopenshell.open(str(catlin_ifc_path))
    names = {product.Name for product in ifc.by_type("IfcProduct")}
    assert {f"{tag}-1" for tag in tags} <= names
    # Viewer exports serialize the same geometry IR, including supplemental solids.
    payload = str(model_to_dict(catlin_model_ro))
    assert all(tag in payload for tag in tags)
