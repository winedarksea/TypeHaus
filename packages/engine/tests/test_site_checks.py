"""Site setback check (→ Permit-ready plan set Phase 4)."""

from __future__ import annotations

import copy
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
