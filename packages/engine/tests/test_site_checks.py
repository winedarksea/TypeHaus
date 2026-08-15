"""Site setback check (→ Permit-ready plan set Phase 4)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def _model_with_site(catlin_model, **site_updates):
    """Pydantic models are frozen — model_copy(update=...) is the immutable-edit path."""
    model = copy.copy(catlin_model)
    site = catlin_model.plan.project.site.model_copy(update=site_updates)
    project = catlin_model.plan.project.model_copy(update={"site": site})
    model.plan = catlin_model.plan.model_copy(update={"project": project})
    return model


def test_catlin_site_setback_passes(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.site_setback"]
    assert matched and all(f.result.value == "pass" for f in matched)


def test_shrunk_parcel_fails(catlin_model):
    from typehaus.quantities import ft, pt

    model = _model_with_site(
        catlin_model,
        parcel=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)), pt(ft(0), ft(36))),
    )
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.site_setback"]
    assert matched and any(f.result.value == "fail" for f in matched)


def test_no_parcel_is_unknown(catlin_model):
    model = _model_with_site(catlin_model, parcel=(), setbacks=())
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.site_setback"]
    assert matched and all(f.result.value == "unknown" for f in matched)


def test_catlin_foundation_grading_passes(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_grading"]
    assert matched and all(f.result.value == "pass" for f in matched)
    assert all(f.code_ref == "R401.3" for f in matched)


def test_grading_fails_when_grade_rises_toward_foundation(catlin_model):
    from typehaus.model.site import SpotElevation
    from typehaus.quantities import ft, pt

    # A spot 2' south of the house south wall (y=0) that sits +6" ABOVE the datum: grade
    # rises toward the foundation instead of falling away from it.
    rising = SpotElevation(position=pt(ft(18), ft(-2)), elevation=ft(0, 6))
    model = _model_with_site(catlin_model, spot_elevations=(rising,))
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_grading"]
    assert matched and any(f.result.value == "fail" for f in matched)


def test_grading_unknown_without_spot_elevations(catlin_model):
    model = _model_with_site(catlin_model, spot_elevations=())
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_grading"]
    assert matched and all(f.result.value == "unknown" for f in matched)


def test_catlin_impervious_grading_passes(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_impervious"]
    assert matched and all(f.result.value == "pass" for f in matched)
    assert all(f.code_ref == "R401.3" for f in matched)


def test_impervious_grading_fails_when_surface_slopes_toward_foundation(catlin_model):
    from typehaus.model.site import ImperviousSurface
    from typehaus.quantities import ft, pt

    # A patio abutting the east wall (x=36') whose outer edge sits ABOVE its foundation edge:
    # the slab drains back toward the house instead of away from it.
    back_pitched = ImperviousSurface(
        label="bad patio",
        outline=(pt(ft(36), ft(10)), pt(ft(42), ft(10)),
                 pt(ft(42), ft(22)), pt(ft(36), ft(22))),
        near_elevation=ft(0, -4),
        far_elevation=ft(0, -1),
    )
    model = _model_with_site(catlin_model, impervious_surfaces=(back_pitched,))
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_impervious"]
    assert matched and any(f.result.value == "fail" for f in matched)


def test_impervious_grading_fails_when_slope_below_two_percent(catlin_model):
    from typehaus.model.site import ImperviousSurface
    from typehaus.quantities import ft, pt

    # 6' patio that falls only 1" (1.4%) — away from the foundation but short of the 2% minimum.
    shallow = ImperviousSurface(
        label="shallow patio",
        outline=(pt(ft(36), ft(10)), pt(ft(42), ft(10)),
                 pt(ft(42), ft(22)), pt(ft(36), ft(22))),
        near_elevation=ft(0, -1),
        far_elevation=ft(0, -2),
    )
    model = _model_with_site(catlin_model, impervious_surfaces=(shallow,))
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_impervious"]
    assert matched and any(f.result.value == "fail" for f in matched)


def test_impervious_grading_silent_without_surfaces(catlin_model):
    # With no impervious surfaces modeled the rule does not apply — it emits no finding
    # (never a spurious fail or unknown).
    model = _model_with_site(catlin_model, impervious_surfaces=())
    report = run_from_model(model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "code.R401_3_impervious"]
    assert matched == []
