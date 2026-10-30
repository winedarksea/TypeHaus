"""The selected sink package must connect, fit its reserved space and bill once."""

import math
import tomllib
from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon

from typehaus.resolve.mep_queries import wet_wall_occupancy
from typehaus.takeoff.plumbing import fitting_takeoff
from typehaus.takeoff.plumbing_specialties import install_parts_takeoff

INCH = 0.0254


def test_faucet_base_hole_and_parked_stream_fit_resolved_counter(catlin_model_ro):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    sink = objects["FX-M-KITCH-SINK"]
    counter = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-KIT-N")
    opening = Polygon(counter.cutouts[0])
    faucet = (sink.position[0], opening.bounds[3] + 3 * INCH)
    assert tuple(v / INCH for v in faucet) == pytest.approx((352, 423.5))
    assert Polygon(counter.outline).contains(Point(faucet).buffer(1.0625 * INCH))
    assert not opening.intersects(Point(faucet).buffer(1.375 / 2 * INCH))
    assert opening.contains(Point(faucet[0], faucet[1] - 8.625 * INCH))
    # Steel flange extends one inch past the bowl opening; base must clear it too.
    assert (faucet[1] - 1.0625 * INCH - opening.bounds[3]) / INCH > 1
    assert counter.thickness_m / INCH < 3.375


def test_trap_arm_is_vented_before_the_floor_drop(catlin_plan):
    arm = catlin_plan.by_tag("PR-M-KITCH-TRAP-ARM")
    waste = catlin_plan.by_tag("PR-M-KITCH-LOCAL-DRAIN")
    vent = catlin_plan.by_tag("PR-M-KITCH-LOCAL-VENT")
    assert arm.path[-1] == waste.path[0] == vent.path[0]
    assert arm.elevations[-1] == waste.elevations[0] == vent.elevations[0]
    length = sum(math.dist(a.xy_m, b.xy_m) / INCH
                 for a, b in zip(arm.path, arm.path[1:], strict=False))
    assert 3 < length < 42
    fall = arm.elevations[0].inches - arm.elevations[-1].inches
    assert fall / (length / 12) == pytest.approx(0.25)
    assert waste.path[-1] == catlin_plan.by_tag("FX-M-KITCH-SINK").drain_position
    # Existing basement drop continues up through the sleeve to this return elbow.
    basement = catlin_plan.by_tag("PR-B-KITCH-DRAIN")
    assert waste.elevations[-1].inches == pytest.approx(6.4375)
    assert basement.elevations[0].inches == pytest.approx(115.875)
    roof_branch = catlin_plan.by_tag("PR-M-KITCH-VENT")
    assert vent.path[-1] == roof_branch.path[0]
    assert vent.elevations[-1] == roof_branch.elevations[0]
    for i, (a, b) in enumerate(zip(vent.path, vent.path[1:], strict=False)):
        travel = math.dist(a.xy_m, b.xy_m) / INCH
        rise = vent.elevations[i + 1].inches - vent.elevations[i].inches
        assert rise >= 0
        if vent.elevations[i].inches - 0.9375 < 42:
            assert rise >= travel - 1e-6


def test_local_plumbing_preserves_cabinet_supply_and_window_clearances(catlin_model_ro):
    model = catlin_model_ro
    objects = {item.tag: item for item in model.canvas_objects}
    base = Polygon(objects["FURN-M-KIT-SINKBASE"].footprint).buffer(-0.75 * INCH)
    arm = next(run for run in model.pipe_runs if run.tag == "PR-M-KITCH-TRAP-ARM")
    for point in arm.path:
        assert base.contains(Point(point).buffer(0.95 * INCH))
    # The west-facing disposer elbow/trap avoids the actual cold/hot risers on the east.
    stops = [model.plan.by_tag(f"PA-M-KITCH-STOP-{kind}") for kind in ("CW", "HW")]
    assert all(stop.position.x.inches > arm.path[0][0] / INCH + 10 for stop in stops)
    vent = next(run for run in model.pipe_runs if run.tag == "PR-M-KITCH-LOCAL-VENT")
    # The scoped long-travel advisory must never conceal a cavity/placement failure.
    assert all(problem["kind"] == "long_horizontal" for problem in wet_wall_occupancy(vent, model))
    window = model.plan.by_tag("WIN-M-KITCH")
    assert window.sill_height.inches - 0.9375 > 39.26 + 1.5
    assert vent.path[3][0] / INCH > 365.75 + 3
    cap = model.plan.by_tag("CO-M-KITCH-ARM")
    assert cap.pipe_ref == arm.tag and cap.accessible and cap.access == "cabinet"


def test_selected_products_and_installation_parts_bill_once(catlin_model_ro):
    plan = catlin_model_ro.plan
    products = {product.tag: product for product in plan.library.products}
    assert products["PROD-KRAUS-KPF-1610SFS"].model == "KPF-1610SFS"
    assert products["PROD-DEARBORN-P9703WBG"].model == "P9703WBG"
    assert "PROD-DELTA-9113-AR-DST" not in products
    parts = {row["part"]: row for row in install_parts_takeoff(catlin_model_ro)}
    faucet = "Kraus Bolden KPF-1610SFS faucet, spot-free stainless"
    trap = "Dearborn P9703WBG 1-1/2-inch tubular P-trap with PVC adapter"
    assert parts[faucet]["count"] == parts[trap]["count"] == 1
    assert parts[faucet]["tags"] == ["PA-M-KITCH-STOP-CW"]
    assert parts[trap]["tags"] == ["APPL-M-DISP"]
    prices = tomllib.loads((Path(plan.source_root) / "prices.toml").read_text())
    for part in plan.by_tag("APPL-M-DISP").install_parts:
        assert prices["install_parts"][part]["low"] > 0
    assert prices["install_parts"][faucet]["low"] == 179.95
    # 2026-10-24 lavatory selection: 5 Genta $150-250 + 3 Indy $100-160 + B.2 $160-260.
    assert prices["allowances"]["plumbing-faucets-and-tub-filler"] == {"low": 1210, "high": 1990}
    # This fitting type also serves the attic lav and basement sink branch.
    tie = next(row for row in fitting_takeoff(catlin_model_ro)
               if row["fitting"] == "wye-2x1.5in")
    assert set(tie["tags"]) == {
        "PR-A-STUBATH-LAV-DRAIN", "PR-B-SINK2-DRAIN", "PR-M-KITCH-LOCAL-DRAIN",
    }
    assert tie["count"] == 3
    assert prices["pipe_fittings"][tie["fitting"]] == {"low": 0, "high": 0}
