"""The live reader shares the CLI's emitter and preserves unfinished/seal states."""

from dataclasses import replace
from datetime import date

import pytest

from typehaus.checks import (
    CheckReport,
    build_context,
    build_context_from_model,
)
from typehaus.engineering import EngineeringRecord, LimitState, Quantity, Status, fingerprint
from typehaus.engineering.register import EngineeringRegister, Signoff
from typehaus.source import load_plan
from typehaus.takeoff.calculation_report import calculation_report


@pytest.fixture(scope="module")
def context(starter_dir):
    return build_context(load_plan(starter_dir).plan, starter_dir)[0]


@pytest.mark.parametrize("status", list(Status))
@pytest.mark.parametrize("seal", ["unsealed", "unpinned", "fresh", "stale"])
def test_calculation_and_seal_states_survive_the_payload(context, monkeypatch, status, seal):
    record = EngineeringRecord(
        item_id="deck_post/P-1", kind="deck_post", key="P-1", status=status,
        basis="Test basis", summary="Post under review",
        inputs=(Quantity("load", 12, "lb"),),
        limit_states=() if status is Status.NO_CALC else (
            LimitState("axial", 12 if status is Status.OVER else 6, 10, "lb", "Test clause"),),
        missing=("soil bearing",) if status is Status.INCOMPLETE else (),
        notes=("An authored assumption",),
    )
    pins = {} if seal == "unpinned" else {record.item_id:
        fingerprint(record) if seal == "fresh" else "old-fingerprint"}
    register = EngineeringRegister() if seal == "unsealed" else EngineeringRegister((Signoff(
        id="S-1", scope="Post", covers=(record.item_id,), engineer="Reviewer",
        license="MN 123", sealed_on=date(2026, 10, 5), fingerprints=pins,
    ),))
    ctx = replace(context, engineering={record.item_id: record}, engineering_register=register)
    report = CheckReport(findings=[], ran=(), engineering=ctx.engineering,
                         engineering_register=register)
    monkeypatch.setattr("typehaus.takeoff.calculation_report.run_checks", lambda ctx: report)
    payload = calculation_report(ctx, "r1", "starter", generated="2026-10-05")
    sheet = payload["files"]["appendix/deck_post__P-1.md"]
    assert "Test basis" in sheet and "An authored assumption" in sheet
    assert record.item_id in payload["files"]["02-item-register.md"]
    assert register.freshness(record)[0].value in payload["files"]["02-item-register.md"]
    if status is Status.INCOMPLETE:
        assert "soil bearing" in payload["files"]["03-open-items.md"]
    if status is Status.OVER:
        assert "Over capacity" in payload["files"]["03-open-items.md"]
    if status is Status.NO_CALC:
        assert "Deferred" in payload["files"]["03-open-items.md"]


def test_a_house_without_engineered_items_still_has_front_matter(context, monkeypatch):
    ctx = replace(context, engineering={})
    monkeypatch.setattr("typehaus.takeoff.calculation_report.run_checks", lambda ctx:
                        CheckReport(findings=[], ran=(), engineering={}))
    payload = calculation_report(ctx, "empty", "starter")
    assert payload["families"] == []
    assert "No engineered item" in payload["files"]["README.md"]


def test_context_from_model_does_not_resolve_again(context, starter_dir, monkeypatch):
    def unexpected_resolve(*args):
        raise AssertionError("the live context must use the supplied model")
    from importlib import import_module
    monkeypatch.setattr(import_module("typehaus.checks.run"), "resolve", unexpected_resolve)
    ctx = build_context_from_model(context.model, context.resolve_findings, starter_dir)
    assert ctx.model is context.model and ctx.plan is context.model.plan
    assert ctx.preferences == context.preferences
    assert ctx.profile == context.profile
