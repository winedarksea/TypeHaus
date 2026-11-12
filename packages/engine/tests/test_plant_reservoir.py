"""Reservoir capacity, manual-fill geometry, placement and procurement contracts."""

from collections import Counter

import pytest
from shapely.geometry import Polygon

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
    assert B.fault_release_gallons == pytest.approx(11.75)
    with pytest.raises(ValueError, match="positive unobstructed"):
        B.spill_depth_m(0.1, 0.1)


def test_existing_water_stop_holds_finite_tank_and_distribution_release(catlin_model_ro):
    room = next(r for r in catlin_model_ro.rooms if r.tag == "RM-S-PLANT")
    tank_area = (G.handle_width_in * M_PER_IN) * (G.envelope_depth_in * M_PER_IN)
    depth_in = B.spill_depth_m(room.area_m2, tank_area) / M_PER_IN
    assert 0.14 < depth_in < 0.16  # independent order-of-magnitude oracle, including displacement
    assert depth_in < 0.25 < _stop_height_in(catlin_model_ro)


def test_manual_fill_tank_has_no_domestic_connection_or_automatic_fill_parts(catlin_plan):
    from typehaus import Service

    kind = next(t for t in catlin_plan.library.appliance_types if t.tag == "APPL-PLANT-RESERVOIR")
    assert Service.WATER_COLD not in kind.needs
    assert not kind.ports
    parts = model_parts("plant-reservoir", *(v.meters for v in kind.footprint), kind.height.meters)
    roles = {p.get("role") for p in parts}
    assert {"reservoir:lid", "reservoir:suction", "reservoir:low-water"} <= roles
    assert not roles & {
        "reservoir:bracket",
        "reservoir:float-valve",
        "reservoir:float",
        "reservoir:fill",
        "reservoir:discharge",
        "reservoir:float-arm",
    }
    assert not any(t.tag == "APPL-PLANT-FILL-VALVE" for t in catlin_plan.library.appliance_types)
    assert not any(
        a.tag == "APPL-S-PLANT-FILL-VALVE" for a in catlin_plan.elements_of_kind("Appliance")
    )
    stop = next(
        a
        for a in catlin_plan.elements_of_kind("PipeAccessory")
        if a.tag == "PA-S-PLANT-RESERVOIR-STOP"
    )
    assert stop.kind.value == "shutoff" and not stop.serves
    stub = next(a for a in catlin_plan.elements_of_kind("PipeRun") if a.tag == "PR-M-CW-PLANT-STUB")
    assert not stub.serves


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
    for tag, quantity in {
        "PROD-HYDROCHECK-WATERWATCHER": 1,
        "PROD-MADISON-M8000-NO": 1,
        "PROD-FUNCTIONAL-RIBU1C": 1,
        "PROD-FUNCTIONAL-TR40VA001": 1,
        "PROD-SHURFLO-255-323": 2,
        "PROD-RAINBIRD-RBY075MPTX": 2,
        "PROD-PLANT-NPSM-ADAPTER": 2,
        "PROD-PLANT-KYCON-CONNECTOR": 2,
        "PROD-PLANT-FUSE-HOLDER": 2,
        "PROD-PLANT-MOTOR-FUSE": 2,
    }.items():
        assert rows[tag]["count"] == quantity
    assert not set(rows) & {
        "PROD-FLOODSTOP-FS14C",
        "PROD-KERICK-MA252",
        "PROD-PLANT-FLOAT-BRACKET",
        "PROD-JOHNGUEST-PPSV040808W",
        "PROD-DIVERSITECH-WS1",
        "PROD-FUNCTIONAL-RIB2401D",
        "PROD-MADISON-M8000",
        "PROD-PLANT-IRRIGATION-FITTINGS",
        "APPL-PLANT-FILL-VALVE",
    }
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


def test_itemized_procurement_matches_takeoff_and_every_cost(catlin_plan, catlin_model_ro):
    import csv
    import tomllib
    from decimal import Decimal
    from pathlib import Path

    house = Path(__file__).resolve().parents[3] / "houses/catlin"
    prices = tomllib.loads((house / "prices.toml").read_text())["placeables"]
    with (house / "notes/plant_reservoir_procurement.csv").open() as stream:
        ledger = list(csv.DictReader(stream))
    selected_types = [
        t
        for t in catlin_plan.library.appliance_types
        if t.tag in {"APPL-PLANT-RESERVOIR", "APPL-PLANT-IRRIGATION-RACK", "APPL-PLANT-WIRED-LEAK"}
    ]
    expected_quantities = Counter({t.tag: 1 for t in selected_types})
    for kind in selected_types:
        for part in kind.parts:
            expected_quantities[part.product_ref] += part.quantity
    # Zero-cost parent symbols remain explicit; every nonzero cost has a ledger row.
    ledger_quantities = {row["cost_ref"]: int(row["quantity"]) for row in ledger}
    assert len(ledger_quantities) == len(ledger)
    assert ledger_quantities == {
        tag: count for tag, count in expected_quantities.items() if prices[tag]["high"]
    }
    assert prices["APPL-PLANT-IRRIGATION-RACK"]["high"] == 0
    assert prices["APPL-PLANT-WIRED-LEAK"]["high"] == 0
    takeoff = {row["type"]: row for row in placeables_takeoff(catlin_model_ro)}
    for row in ledger:
        tag = row["cost_ref"]
        assert takeoff[tag]["count"] == int(row["quantity"])
        assert Decimal(row["unit_usd"]) == Decimal(str(prices[tag]["high"]))
        assert row["supplier"] and row["price_date"] and row["price_basis"] and row["availability"]
        # Unresolved SKUs and estimates must never be represented as order-ready.
        assert row["purchasing_status"].startswith("HOLD:")
        if tag.startswith("PROD-") and row["sku"]:
            assert catlin_plan.library.product(tag).model == row["sku"]
    total = sum(Decimal(row["unit_usd"]) * int(row["quantity"]) for row in ledger)
    assert total == Decimal("1026.61")
    assert total <= Decimal("1200")
    assert total + Decimal("300") <= Decimal("1500")
