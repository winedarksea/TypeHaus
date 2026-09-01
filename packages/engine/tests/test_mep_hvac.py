"""HVAC duct/joist-bay resolver + checks (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations


import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier


@pytest.fixture(scope="module")
def second_floor(catlin_model):
    """The east half — I-joist, unchanged since 2026-08-21 — for the generic joist-bay
    tests below. Its x-span is 18'-36' (5.4864m-10.9728m), so the synthetic duct paths
    here sit inside that range rather than the pre-split fixture's 1m-5m."""
    return next(f for f in catlin_model.floors if f.tag == "FS-S-EAST")


@pytest.fixture(scope="module")
def west_floor(catlin_model):
    """The west half — open-web floor truss, since 2026-08-21 — for the open-web
    legality tests. Its x-span is 0'-18' (0m-5.4864m)."""
    return next(f for f in catlin_model.floors if f.tag == "FS-S-WEST")


def test_parallel_in_bay_trunk_ducts_pass(catlin_model):
    for duct in catlin_model.ducts:
        assert duct.conflicts == (), (duct.tag, duct.conflicts)
        assert duct.depth_ok


def test_duct_centered_on_a_joist_line_fails(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 0.4064), (9.0, 0.4064)],  # centered exactly on the joist line at y=16"
        width_m=0.3048, depth_m=0.2032, routing=DuctRouting.JOIST_BAY,
        floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_sixteen_inch_wide_duct_fails_clear_bay_width(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 6.2992), (9.0, 6.2992)], width_m=0.4064, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_perpendicular_run_requires_soffit_or_chase(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 0.0), (6.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts
    conflicts_soffit, _, _ = duct_bay_occupancy(
        [(6.0, 0.0), (6.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.SOFFIT, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts_soffit == []


def test_perpendicular_run_through_open_web_is_legal_within_the_chord_opening(west_floor):
    """A truss's 8 7/8" clear chord-to-chord opening (11.875" depth, two 1.5" chords) lets
    a shallow-enough perpendicular run cross without a soffit or chase; a run too deep for
    the opening still conflicts, and names the real reason."""
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, crossings, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.1524,  # 6" deep, fits the web
        routing=DuctRouting.JOIST_BAY, floor=west_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts == []
    assert crossings

    conflicts_deep, _, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.254,  # 10" deep, too deep
        routing=DuctRouting.JOIST_BAY, floor=west_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts_deep
    assert any("opening" in message for message in conflicts_deep)


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
        [(6.0, 6.2992), (9.0, 6.2992)], width_m=0.3048, depth_m=0.4,  # ~15.75" > 11.875"
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert not depth_ok


# --- mep.duct_connectivity ------------------------------------------------------------
#
# The rule is "no duct ends in mid-air", and every one of these guards a way the first
# drafts of it got a wrong answer confidently. Two runs sharing a plan point on different
# floors is the recurring one, and it is silent in both directions: it hid four real
# orphans behind coincidences, and it would have reported a legitimate tee as one.


def _connectivity(model):
    report = run_from_model(model, [], tier=Tier.INTEGRITY)
    return [f for f in report.findings if f.check_id == "mep.duct_connectivity"]


def test_no_duct_in_catlin_ends_on_nothing(catlin_model):
    findings = _connectivity(catlin_model)
    assert findings
    orphans = [f.message for f in findings if f.result.value == "fail"]
    assert not orphans, orphans


def test_a_branch_tees_into_the_side_of_a_trunk(catlin_model):
    """Against a *segment*, not a vertex. DU-S-HP-SUITE leaves DU-S-HP-SUP 118" from either
    end of the trunk's only leg, which is where a take-off normally lands."""
    landed = [f.message for f in _connectivity(catlin_model)
              if "DU-S-HP-SUITE start" in f.message]
    assert landed == ["duct DU-S-HP-SUITE start lands on DU-S-HP-SUP"]


def test_a_served_trunk_may_be_capped(catlin_model):
    """DU-S-HP-SUP stops past its last bedroom boot. A capped trunk end lands on nothing and
    never will, and that is how a trunk ends — earned from the take-offs on its final leg."""
    capped = [f for f in _connectivity(catlin_model) if "DU-S-HP-SUP end" in f.message]
    assert len(capped) == 1
    assert capped[0].result.value == "pass"
    assert "cap past" in capped[0].message


def test_a_machine_67_inches_above_the_end_is_not_a_joint(catlin_model):
    """The elevation band on the equipment probe. Drop DU-ERV-OA's last vertex to the floor
    and it is no longer in EQ-B-ERV's case, however squarely it still sits in its footprint —
    which is exactly how both ERV chase risers passed a plan-only test while ending 67" under
    the gable hood they were credited to."""
    import dataclasses

    index, duct = next((i, d) for i, d in enumerate(catlin_model.ducts)
                       if d.tag == "DU-ERV-OA")
    catlin_model.ducts[index] = dataclasses.replace(
        duct, z_m=(*duct.z_m[:-1], duct.z_m[-1] - 2.0))  # 6'-7" lower: below the case
    orphans = [f.message for f in _connectivity(catlin_model) if f.result.value == "fail"]
    assert any("DU-ERV-OA end" in message for message in orphans), orphans
