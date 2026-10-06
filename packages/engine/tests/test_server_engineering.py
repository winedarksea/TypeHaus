"""Read-only live calculation snapshots, including changes not written to source."""

from dataclasses import replace
from threading import RLock
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.server.engineering_api import register_engineering_routes
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def context(starter_dir):
    return build_context(load_plan(starter_dir).plan, starter_dir)[0]


@pytest.fixture
def client(context, starter_dir):
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    state = SimpleNamespace(
        model=context.model, house_dir=starter_dir, _lock=RLock(),
        _resolve_findings=context.resolve_findings, token="r1")
    state.revision = lambda: state.token
    app = fastapi.FastAPI()
    register_engineering_routes(app, state)
    with testclient.TestClient(app) as client:
        yield client, state


def test_unresolved_model_returns_an_explicit_error(client):
    http, state = client
    state.model = None
    response = http.get("/reports/engineering")
    assert response.status_code == 409
    assert response.json()["error"] == "model does not resolve"


def test_live_criteria_read_the_in_memory_edit_not_disk(client):
    http, state = client
    before = http.get("/reports/engineering")
    assert before.status_code == 200
    original_site = state.model.plan.project.site
    site = original_site.model_copy(update={"ground_snow_load_psf": 173})
    project = state.model.plan.project.model_copy(update={"site": site})
    plan = state.model.plan.model_copy(update={"project": project})
    state.model = replace(state.model, plan=plan)
    state.token = "unsaved-r2"
    after = http.get("/reports/engineering")
    assert after.status_code == 200
    payload = after.json()
    assert payload["revision"] == "unsaved-r2"
    criteria = payload["files"]["01-design-criteria.md"]
    assert criteria != before.json()["files"]["01-design-criteria.md"]
    assert "173" in payload["files"]["01-design-criteria.md"]
    assert load_plan(state.house_dir).plan.project.site == original_site
    assert "unsaved-r2" in payload["files"]["00-cover.md"]


def test_a_revision_change_during_calculation_does_not_mix_snapshots(client, monkeypatch):
    http, state = client
    original = state.model
    def calculate(ctx, revision, house, **kwargs):
        state.token = "r2"
        state.model = None
        assert ctx.model is original
        return {"revision": revision, "files": {}, "families": []}
    monkeypatch.setattr("typehaus.takeoff.calculation_report.calculation_report", calculate)
    assert http.get("/reports/engineering").json()["revision"] == "r1"


def test_opening_a_report_does_not_write_files(client, monkeypatch):
    from pathlib import Path
    http, _ = client
    def unexpected_write(*args, **kwargs):
        raise AssertionError("a report read must not write output")
    monkeypatch.setattr(Path, "write_text", unexpected_write)
    assert http.get("/reports/engineering").status_code == 200


def test_cached_package_refreshes_with_preferences_and_signoffs(client, monkeypatch, tmp_path):
    http, state = client
    state.house_dir = tmp_path
    calls = []

    def calculate(ctx, revision, house, **kwargs):
        calls.append(ctx)
        return {"revision": revision, "files": {}, "families": []}

    monkeypatch.setattr("typehaus.takeoff.calculation_report.calculation_report", calculate)
    assert http.get("/reports/engineering").status_code == 200
    assert http.get("/reports/engineering").status_code == 200
    assert len(calls) == 1
    (tmp_path / "preferences.toml").write_text("[envelope]\ninterior_setpoint_f = 74\n")
    assert http.get("/reports/engineering").status_code == 200
    assert len(calls) == 2 and calls[-1].preferences.interior_setpoint_f == 74
    (tmp_path / "engineering.toml").write_text(
        '[[signoff]]\nid="S-1"\nscope="Post"\ncovers=["deck_post/P-1"]\n'
        'engineer="Reviewer"\nlicense="MN 123"\nsealed_on="2026-10-05"\n')
    assert http.get("/reports/engineering").status_code == 200
    assert len(calls) == 3 and calls[-1].engineering_register.signoffs[0].id == "S-1"
