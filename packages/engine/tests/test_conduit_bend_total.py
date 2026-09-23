"""``mep.conduit_bend_total`` — NEC 358.26's 360° between pull points, on synthetic runs.

Every raceway here is flat at 9' and turns 90° in plan at each interior vertex, so a
section's total is 90° times the bends it holds and nothing is left to a tolerance.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.conduit_bends import conduit_bend_total
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result
from typehaus.model import (
    Building,
    ConduitRun,
    Library,
    PlanModel,
    Project,
    Site,
    Storey,
    ft,
    m,
    pt,
)
from typehaus.resolve import resolve
from typehaus.resolve.conduit_pulls import pull_sections

#: A plan staircase: each vertex after the first two turns 90°, alternately left and right.
_STAIR = [(0, 0), (10, 0), (10, 10), (20, 10), (20, 20), (30, 20), (30, 30)]


def _run(tag, points, z=9, **kwargs):
    return ConduitRun(tag=tag, trade_size=ft(0, 1), path=tuple(pt(ft(x), ft(y)) for x, y in points),
                      elevations=tuple(ft(z) for _ in points), **kwargs)


def _model(*runs):
    plan = PlanModel(
        project=Project(name="t", project_uuid="00000000-0000-0000-0000-000000000007",
                        building=Building(name="t"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(), elements={"main": tuple(runs)})
    model, findings = resolve(plan)
    return model, findings


def _check(*runs):
    model, findings = _model(*runs)
    assert not [f for f in findings if f.severity.value == "error"]
    return conduit_bend_total(check_context(model=model))


def _advisory(finding) -> bool:
    return finding.result is Result.PASS and finding.message.startswith("ADVISORY — ")


def test_registered_as_advisory() -> None:
    assert "mep.conduit_bend_total" in {cid for cid, _ in registered(Tier.ADVISORY)}


def test_four_quarter_bends_pass_at_exactly_360() -> None:
    [finding] = _check(_run("CD-1", _STAIR[:6]))
    assert finding.result is Result.PASS and not _advisory(finding)
    assert "360.0°" in finding.message


def test_five_quarter_bends_are_an_advisory() -> None:
    [finding] = _check(_run("CD-1", _STAIR))
    assert _advisory(finding)
    assert "450.0°" in finding.message and "pull box" in finding.message
    assert finding.element_tags == ("CD-1",)


def test_an_authored_pull_point_splits_the_section_and_takes_its_bend() -> None:
    findings = _check(_run("CD-1", _STAIR, pull_points=(3,)))
    assert [f.result for f in findings] == [Result.PASS, Result.PASS]
    assert not any(_advisory(f) for f in findings)
    assert all("180.0°" in f.message for f in findings)


def test_end_to_start_runs_chain_and_the_joint_counts() -> None:
    """1 bend + the 90° joint + 3 bends: 450°, though neither run alone exceeds 270°."""
    model, _ = _model(_run("CD-A", _STAIR[:3]), _run("CD-B", _STAIR[2:]))
    [section] = pull_sections(model.conduits)
    assert section.run_tags == ("CD-A", "CD-B")
    assert section.total_deg == pytest.approx(450.0)
    [finding] = conduit_bend_total(check_context(model=model))
    assert _advisory(finding) and finding.element_tags == ("CD-A", "CD-B")


def test_a_riser_joint_is_a_3d_bend() -> None:
    """A run that ends by rising, chained to a flat run at the top: two 90° bends in z."""
    riser = ConduitRun(tag="CD-R", trade_size=ft(0, 1),
                       path=(pt(ft(0), ft(0)), pt(ft(10), ft(0)), pt(ft(10), ft(0))),
                       elevations=(ft(0), ft(0), ft(9)))
    model, _ = _model(riser, _run("CD-T", [(10, 0), (20, 0)]))
    [section] = pull_sections(model.conduits)
    assert section.total_deg == pytest.approx(180.0)


def test_several_runs_leaving_one_point_is_a_box_not_a_chain() -> None:
    feeder = _run("CD-F", [(-10, 0), (0, 0)])
    east = _run("CD-E", [(0, 0), (10, 0), (10, 10)])
    north = _run("CD-N", [(0, 0), (0, 10), (10, 10)])
    model, _ = _model(feeder, east, north)
    assert sorted(s.run_tags for s in pull_sections(model.conduits)) == [
        ("CD-E",), ("CD-F",), ("CD-N",)]


def test_a_schematic_profile_is_unknown() -> None:
    schematic = ConduitRun(tag="CD-S", trade_size=ft(0, 1),
                           path=tuple(pt(ft(x), ft(y)) for x, y in _STAIR),
                           start_elevation=ft(9), end_elevation=ft(9))
    [finding] = _check(schematic)
    assert finding.result is Result.UNKNOWN


def test_no_conduit_is_not_applicable() -> None:
    from typehaus.model import DeviceKind, ElectricalDevice

    [finding] = _check(ElectricalDevice(tag="ED-P", kind=DeviceKind.PANEL,
                                        position=pt(m(0), m(0))))
    assert finding.result is Result.NOT_APPLICABLE


@pytest.mark.parametrize("pulls", [(0,), (6,), (3, 3), (4, 2)])
def test_pull_points_must_be_ascending_unique_interior_indices(pulls) -> None:
    _, findings = _model(_run("CD-1", _STAIR, pull_points=pulls))
    assert [f.check_id for f in findings if f.severity.value == "error"] == [
        "integrity.conduit_run_path"]
