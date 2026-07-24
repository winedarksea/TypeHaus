"""MEP plumbing — sleeves, drain runs, checks (→ Permit-ready plan set Phase 2)."""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_wc_expected_drain_point_is_fixture_position(catlin_model):
    sleeve = next(s for s in catlin_model.sleeves if s.tag == "SP-M-WC1")
    fixture = catlin_model.plan.by_tag("FX-M-BATH1-WC")
    assert sleeve.expected_center == fixture.position.xy_m


def test_lav_expected_drain_point_projects_onto_wet_wall(catlin_model):
    sleeve = next(s for s in catlin_model.sleeves if s.tag == "SP-M-LAV1")
    wall = catlin_model.wall("W-M-BAE")
    # The projected point lies on the infinite line through the wall axis (x is constant).
    assert sleeve.expected_center[0] == pytest.approx(wall.axis[0][0], abs=1e-6)


def test_drain_position_override_wins():
    from typehaus.model.mep import SleevePenetration
    from typehaus.model.spatial import Fixture
    from typehaus.quantities import ft, inch, pt
    from typehaus.resolve.mep import _expected_drain_point

    fixture = Fixture(uid="FX1", tag="FX-OVR", type_ref="FX-LAV", room="RM-1",
                      position=pt(ft(3), ft(3)), wall_ref="W-1",
                      drain_position=pt(ft(99), ft(99)))

    class _Library:
        fixture_types = ()

    class _Plan:
        library = _Library()

        def by_tag(self, tag):
            return fixture if tag == fixture.tag else None

    class _Model:
        plan = _Plan()

    point = _expected_drain_point(_Model(), fixture.tag)
    assert point == (ft(99).meters, ft(99).meters)


def test_sleeve_alignment_fails_at_one_inch_offset(catlin_model):
    model = copy.copy(catlin_model)
    model.sleeves = [
        dataclasses.replace(s, center=(s.center[0] + 0.0254, s.center[1]),
                            offset_m=0.0254)
        if s.tag == "SP-M-WC1" else s
        for s in catlin_model.sleeves
    ]
    report = run_from_model(model, [], tier=Tier.CODE)
    fails = [f for f in report.findings
             if f.check_id == "mep.sleeve_alignment" and "SP-M-WC1" in f.element_tags
             and f.result.value == "fail"]
    assert fails, [f.message for f in report.findings if f.check_id == "mep.sleeve_alignment"]


def test_sleeve_rejected_when_inside_floor_opening():
    from typehaus.model.mep import SleevePenetration
    from typehaus.quantities import ft, inch, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedSolid
    from typehaus.resolve.mep import resolve_mep

    class _FakeOpening:
        outline = (pt(ft(0), ft(0)), pt(ft(2), ft(0)), pt(ft(2), ft(2)), pt(ft(0), ft(2)))

    class _FakeSlab:
        tag = "SL-TEST"
        openings = ("FO-TEST",)

    sleeve = SleevePenetration(uid="X", tag="SP-BAD", host_ref="SL-TEST",
                               position=pt(ft(1), ft(1)), pipe_diameter=inch(3),
                               sleeve_diameter=inch(4))

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [sleeve]

        def by_tag(self, tag):
            return {"SL-TEST": _FakeSlab(), "FO-TEST": _FakeOpening()}.get(tag)

    class _FakeStorey:
        tag = "main"

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    model.solids.append(ResolvedSolid(
        uid="S1", tag="SL-TEST", storey="main", category="slab",
        outline=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)], z0_m=-0.2, z1_m=0.0,
    ))
    findings = resolve_mep(model)
    assert any(f.check_id == "integrity.sleeve_in_opening" for f in findings)


def test_drain_slope_pass_for_catlin_main_run(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "mep.drain_slope"]
    assert matched and all(f.result.value == "pass" for f in matched)


def test_drain_slope_unknown_without_inverts():
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import PipeRun
    from typehaus.quantities import ft, inch, pt
    from typehaus.resolve.model import ResolvedModel
    from typehaus.resolve.mep import resolve_mep

    run = PipeRun(uid="X", tag="PR-TEST", system=PipeSystem.DRAIN,
                 path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))), diameter=inch(3))

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [run]

        def by_tag(self, tag):
            return None

    class _FakeStorey:
        tag = "basement"
        elevation = ft(-9)

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    resolve_mep(model)
    assert model.pipe_runs[0].z_start_m is None
    assert model.pipe_runs[0].z_end_m is None


def _vent_termination_context(authored_termination):
    """A one-roof, one-vent context for the termination check.

    Gable, ridge along y, eave 3 m, ridge 5 m over a 10x10 footprint: the riser at x=2 m
    sits 40% of the way up the rake, so the roof plane there is 3.8 m and the derived
    termination 12" above it.
    """
    from typehaus.checks.registry import CheckContext, JurisdictionProfile, Preferences
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import VentRun
    from typehaus.quantities import inch, m, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedRoof

    vent = VentRun(uid="V1", tag="VR-TEST", systems=(PipeSystem.VENT,), diameter=inch(3),
                   chase_position=pt(m(2), m(2)), start_elevation=m(0), exit_elevation=m(3),
                   exit_offset=pt(m(0), m(1)),
                   roof_termination_elevation=authored_termination)

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [vent]

        def by_tag(self, tag):
            return vent if tag == vent.tag else None

    class _FakeStorey:
        tag = "attic"

    _FakePlan.storeys = [_FakeStorey()]
    plan = _FakePlan()
    model = ResolvedModel(plan=plan)
    model.roofs.append(ResolvedRoof(
        uid="R1", tag="RF-TEST", storey="attic", form="gable",
        footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
        eave_z_m=3.0, ridge_z_m=5.0, ridge_direction="y", assembly="A",
        surface_area_m2=100.0,
    ))
    return CheckContext(plan=plan, model=model, preferences=Preferences(),
                        profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                                     irc_base="t", coverage_statement="t"))


def test_vent_termination_height_flags_an_authored_elevation_above_the_roof():
    from typehaus.checks.mep.plumbing import vent_termination_height
    from typehaus.quantities import m

    findings = vent_termination_height(_vent_termination_context(m(5.5)))
    assert [f.result.value for f in findings] == ["fail"]
    assert "1.4" in findings[0].message or "too high" in findings[0].message
    # Advisory findings never block the permit gate (see plumbing.py's _advisory_fail).
    assert findings[0].severity.value == "warn"


def test_vent_termination_height_passes_an_authored_elevation_that_matches():
    from typehaus.checks.mep.plumbing import vent_termination_height
    from typehaus.quantities import inch, m

    matching = m(3.8 + inch(12).meters)
    findings = vent_termination_height(_vent_termination_context(matching))
    assert [f.result.value for f in findings] == ["pass"]


def test_vent_termination_height_passes_when_the_elevation_is_left_derived():
    from typehaus.checks.mep.plumbing import vent_termination_height

    findings = vent_termination_height(_vent_termination_context(None))
    assert [f.result.value for f in findings] == ["pass"]


def test_catlin_vent_termination_height_passes(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    matched = [f for f in report.findings if f.check_id == "mep.vent_termination_height"]
    assert matched and all(f.result.value == "pass" for f in matched)


def test_missing_sleeve_over_slab_fails():
    from typehaus.checks.mep.plumbing import _missing_sleeve_findings
    from typehaus.checks.registry import CheckContext, JurisdictionProfile, Preferences
    from typehaus.model.enums import Service
    from typehaus.model.types import FixtureType
    from typehaus.quantities import ft, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedSolid

    class _FakeFixture:
        element_kind = "Fixture"
        tag = "FX-TEST-WC"
        type_ref = "FX-TOILET"
        position = pt(ft(1), ft(1))

    class _Library:
        fixture_types = (FixtureType(tag="FX-TOILET", name="WC", footprint=(ft(2), ft(2)),
                                      height=ft(2), needs=frozenset({Service.DRAIN})),)

    class _FakePlan:
        library = _Library()
        storeys: list = []

        def storey_elements(self, tag):
            return [_FakeFixture()]

    class _FakeStorey:
        tag = "main"

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    model.solids.append(ResolvedSolid(
        uid="S1", tag="SL-TEST", storey="main", category="slab",
        outline=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)], z0_m=-0.2, z1_m=0.0,
    ))
    ctx = CheckContext(plan=_FakePlan(), model=model, preferences=Preferences(),
                       profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                                    irc_base="t", coverage_statement="t"))
    findings = _missing_sleeve_findings(ctx)
    assert findings and findings[0].result.value == "fail"
