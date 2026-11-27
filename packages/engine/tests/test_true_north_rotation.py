"""Rotating catlin by ``Site.true_north`` moves compass outputs and nothing else (#153).

The audit behind decision #153 found compass readers that ignored the angle and others that
read it with the wrong sign. This module resolves catlin at θ = 37° and holds every finding
outside the orientation-dependent checks, and the whole takeoff, to the θ = 0 run.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import deg

pytestmark = pytest.mark.slow

THETA = 37.0
# Checks whose verdict or numbers honestly depend on where the glass faces.
_ORIENTATION_CHECKS = (
    "building_science.window_to_wall_ratio", "building_science.solar",
    "code.energy_prescriptive", "mep.cooling_capacity", "mep.heat_pump_turndown",
)


def _rotated(plan, theta: float):
    site = plan.project.site.model_copy(update={"true_north": deg(theta)})
    return plan.model_copy(update={"project": plan.project.model_copy(update={"site": site})})


@pytest.fixture(scope="module")
def pair(catlin_plan, _catlin_resolved):
    from conftest import CATLIN

    from typehaus.checks.registry import run_checks
    from typehaus.checks.run import build_context_from_model
    from typehaus.resolve import resolve

    rotated, findings = resolve(_rotated(catlin_plan, THETA))
    base = _catlin_resolved.copy()
    reports = (
        run_checks(build_context_from_model(base, _catlin_resolved.findings, CATLIN)),
        run_checks(build_context_from_model(rotated, findings, CATLIN)),
    )
    return {"models": (base, rotated), "reports": reports}


def _key(finding) -> tuple:
    return (finding.check_id, finding.result.value, finding.severity.value,
            tuple(finding.element_tags), finding.message)


def _orientation_dependent(check_id: str) -> bool:
    return check_id.startswith(_ORIENTATION_CHECKS)


def test_elevations_keep_four_names_with_a_bearing(pair) -> None:
    from typehaus.emit.draw.elevation import FACINGS, display_bearing, display_facing

    base, rotated = pair["models"]
    for key in FACINGS:
        assert display_facing(base, key) == key
        assert display_bearing(base, key) is None
    names = {display_facing(rotated, key) for key in FACINGS}
    assert names == set(FACINGS)
    assert display_bearing(rotated, "north") == "faces N 37° W"


def test_lot_lines_turn_by_theta(pair) -> None:
    from typehaus.emit.draw.site_metrics import lot_line_dimensions

    base, rotated = pair["models"]
    before = lot_line_dimensions(base.plan.project.site)
    after = lot_line_dimensions(rotated.plan.project.site)
    assert [(i, round(length, 6)) for i, length, _ in before] == \
        [(i, round(length, 6)) for i, length, _ in after]
    assert [b for *_, b in before] != [b for *_, b in after]


def test_wwr_bins_follow_the_nearest_cardinal(pair) -> None:
    import dataclasses

    from typehaus.checks.building_science.wwr import analyze_wwr

    base, rotated = pair["models"]
    glass = [{f.facade: round(f.glazing_area_m2, 4) for f in analyze_wwr(m)}
             for m in (base, rotated)]
    assert glass[0] == glass[1]  # 37° leaves every axis-aligned face on its cardinal
    # The geometry does not depend on θ (the takeoff test holds it), so a site swap is a
    # faithful 90° turn: project north now faces true west.
    turned = dataclasses.replace(base, plan=_rotated(base.plan, 90.0))
    quarter = {f.facade: round(f.glazing_area_m2, 4) for f in analyze_wwr(turned)}
    assert quarter == {"N": glass[0]["E"], "E": glass[0]["S"],
                       "S": glass[0]["W"], "W": glass[0]["N"]}


def test_solar_gain_follows_the_continuous_azimuth(pair) -> None:
    from typehaus.checks.building_science.solar import fenestration_gain

    base, rotated = (
        fenestration_gain(m, {w.tag: w for w in m.walls}, m.openings).design_btu_per_hour
        for m in pair["models"])
    assert not math.isclose(base, rotated, rel_tol=1e-6)


def test_every_other_finding_is_invariant(pair) -> None:
    base, rotated = (
        {_key(f) for f in report.findings if not _orientation_dependent(f.check_id)}
        for report in pair["reports"])
    assert sorted(base - rotated) == [] and sorted(rotated - base) == []


def test_takeoff_is_invariant(pair) -> None:
    from typehaus.takeoff.bom import bill_of_materials

    base, rotated = pair["models"]
    assert bill_of_materials(base) == bill_of_materials(rotated)
