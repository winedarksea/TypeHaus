"""Reservoir capacity, real discharge geometry, placement and procurement contracts."""

from collections import Counter

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model.placeable_symbols import model_parts
from typehaus.model.plant_reservoir import RESERVOIR_GEOMETRY as G
from typehaus.model.plant_reservoir import RESERVOIR_WATER_BUDGET as B
from typehaus.quantities import M_PER_IN
from typehaus.takeoff.placeables import placeables_takeoff


def _stop_height_in(model):
    opening = next(o for o in model.openings if o.tag == "D-S-PLANT")
    riser = next(
        p for p in opening.doorway.components[0].specification.parts if p.name == "water-stop riser"
    )
    return max(z for _, z in riser.polygon_m) / M_PER_IN


def test_water_budget_uses_working_volume_and_reserve():
    assert B.nominal_gallons == 10
    assert B.watering_gallons == 7
    assert B.maximum_daily_gallons == pytest.approx(0.7)
    assert B.daily_zone_runtime_seconds == pytest.approx(210)
    assert B.fault_release_gallons == pytest.approx(11.875)
    with pytest.raises(ValueError, match="positive unobstructed"):
        B.spill_depth_m(0.1, 0.1)


def test_water_stop_holds_tank_lines_and_delayed_fill(catlin_model_ro):
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-S-PLANT")
    tank_area = (G.handle_width_in * M_PER_IN) * (G.envelope_depth_in * M_PER_IN)
    depth_in = B.spill_depth_m(room.area_m2, tank_area) / M_PER_IN
    assert 0.14 < depth_in < 0.16  # independent order-of-magnitude oracle, including displacement
    assert depth_in < 0.25 < _stop_height_in(catlin_model_ro)


def test_discharge_is_distinct_from_inlet_and_clear_of_lid(catlin_plan):
    kind = next(t for t in catlin_plan.library.appliance_types if t.tag == "APPL-PLANT-RESERVOIR")
    inlet = next(p for p in kind.ports if p.tag == "supply")
    assert inlet.position[2].meters == pytest.approx(G.inlet_height_in * M_PER_IN)
    assert inlet.certainty.value == "approximate"
    assert G.discharge_height_in - G.rim_height_in == pytest.approx(2)
    parts = model_parts("plant-reservoir", *(v.meters for v in kind.footprint), kind.height.meters)
    outlet = [p for p in parts if p.get("role") == "reservoir:discharge"][-1]
    # Bottom of the opening is modeled separately from the supply hose connection.
    assert outlet["center"][2] - outlet["size"][2] / 2 == pytest.approx(
        G.discharge_height_in * M_PER_IN
    )
    lid = next(p for p in parts if p.get("role") == "reservoir:lid")
    jet = Point(G.discharge_x_in * M_PER_IN, G.discharge_y_in * M_PER_IN)
    assert not Polygon(lid["points"]).covers(jet)
    assert kind.height.meters > G.discharge_height_in * M_PER_IN


def test_service_envelopes_clear_wall_door_and_each_other(catlin_model_ro):
    objects = {o.tag: o for o in catlin_model_ro.canvas_objects}
    tank = objects["APPL-S-PLANT-RESERVOIR"]
    rack = objects["APPL-S-PLANT-IRRIGATION"]
    sensors = objects["APPL-S-PLANT-WIRED-LEAK"]
    shapes = [Polygon(o.footprint) for o in (tank, rack, sensors)]
    for i, shape in enumerate(shapes):
        assert shape.bounds[0] > 145 * M_PER_IN
        assert shape.bounds[2] < 186 * M_PER_IN
        assert shape.bounds[1] > 7.79 * M_PER_IN
        assert all(not shape.intersects(other) for other in shapes[i + 1 :])
    # Remove lid above the rim, without reaching the 32-inch sill.
    assert G.rim_height_in + 6 < 32
    assert G.rack_height_in < 32
    assert shapes[0].bounds[2] - shapes[0].bounds[0] == pytest.approx(18 * M_PER_IN)


def test_bom_counts_two_complete_zones_and_no_legacy_install_strings(catlin_model_ro):
    rows = {r["type"]: r for r in placeables_takeoff(catlin_model_ro)}
    assert rows["PROD-SHURFLO-8000-543-210"]["count"] == 2
    assert rows["PROD-MEANWELL-GST120A12-R7B"]["count"] == 2
    assert rows["PROD-HYDROFARM-TM01715D"]["count"] == 2
    assert rows["PROD-RAINBIRD-XB05PC"]["count"] == 24
    assert rows["PROD-FLOODSTOP-FS14C"]["count"] == 1
    assert rows["PROD-DIVERSITECH-WS1"]["count"] == 1
    tags = Counter(
        t
        for r in rows.values()
        for t in r["tags"]
        if r["type"]
        in {"APPL-PLANT-RESERVOIR", "APPL-PLANT-IRRIGATION-RACK", "APPL-PLANT-WIRED-LEAK"}
    )
    assert set(tags.values()) == {1}
    for appliance in catlin_model_ro.plan.elements_of_kind("Appliance"):
        if appliance.tag.startswith("APPL-S-PLANT-"):
            assert not appliance.install_parts
    stop = next(a for a in catlin_model_ro.pipe_accessories if a.tag == "PA-S-PLANT-RESERVOIR-STOP")
    assert stop.kind == "shutoff" and "APPL-S-PLANT-RESERVOIR" in stop.serves


def test_complete_hardware_allowance_fits_owner_ceiling(catlin_plan):
    import tomllib
    from pathlib import Path

    price_path = Path(__file__).resolve().parents[3] / "houses/catlin/prices.toml"
    prices = tomllib.loads(price_path.read_text())["placeables"]
    selected_types = [
        t
        for t in catlin_plan.library.appliance_types
        if t.tag in {"APPL-PLANT-RESERVOIR", "APPL-PLANT-IRRIGATION-RACK", "APPL-PLANT-WIRED-LEAK"}
    ]
    total = sum(prices[t.tag]["high"] for t in selected_types)
    total += sum(
        prices[part.product_ref]["high"] * part.quantity for t in selected_types for part in t.parts
    )
    assert total == pytest.approx(930.42)
    assert total <= 1000
