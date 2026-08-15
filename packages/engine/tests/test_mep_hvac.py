"""HVAC duct/joist-bay resolver + checks (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations


import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier


@pytest.fixture(scope="module")
def second_floor(catlin_model):
    return next(f for f in catlin_model.floors if f.tag == "FS-SECOND")


def test_parallel_in_bay_trunk_ducts_pass(catlin_model):
    for duct in catlin_model.ducts:
        assert duct.conflicts == (), (duct.tag, duct.conflicts)
        assert duct.depth_ok


def test_duct_centered_on_a_joist_line_fails(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(1.0, 0.4064), (5.0, 0.4064)],  # centered exactly on the joist line at y=16"
        width_m=0.3048, depth_m=0.2032, routing=DuctRouting.JOIST_BAY,
        floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_sixteen_inch_wide_duct_fails_clear_bay_width(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(1.0, 6.2992), (5.0, 6.2992)], width_m=0.4064, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_perpendicular_run_requires_soffit_or_chase(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts
    conflicts_soffit, _, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.SOFFIT, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts_soffit == []


def test_bearing_crossing_reported_with_fire_blocking_note(catlin_model):
    """A duct crossing a bearing line is legal, not a defect — the resolver lays identical
    perpendicular positions on both sides of the line. What the builder still owes is the
    R302.11 draftstop, so the crossing rides along as a *note on a PASS* rather than as a
    failure that would have to be waived on every through-duct in the house."""
    report = run_from_model(catlin_model, [], tier=Tier.STRUCTURAL)
    matched = [f for f in report.findings if f.check_id == "mep.duct_joist_bay"]
    assert matched
    assert all(f.result.value == "pass" for f in matched)
    assert all(f.severity.value == "warn" for f in matched)  # never a permit-gate blocker
    noted = [f for f in matched if "crosses bearing wall" in f.message]
    assert noted
    assert all("R302.11" in f.message and "fire blocking" in f.message for f in noted)


def test_depth_exceeding_joist_depth_fails(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    _, _, depth_ok = duct_bay_occupancy(
        [(1.0, 6.2992), (5.0, 6.2992)], width_m=0.3048, depth_m=0.4,  # ~15.75" > 11.875"
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert not depth_ok
