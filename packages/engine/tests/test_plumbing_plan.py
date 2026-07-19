"""Plumbing plan builder — P-101/P-102 (→ Permit-ready plan set Phase 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.scene import Leader, Polyline, Symbol
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


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_starter_has_no_plumbing_content(starter_model):
    assert not any(has_plumbing_content(starter_model, s.tag) for s in starter_model.plan.storeys)


def test_basement_plan_shows_drain_run_and_sleeves_from_below(catlin_model):
    scene = build_plumbing_plan(catlin_model, "basement")
    layers = scene.by_layer()
    assert "P-SANR-PIPE" in layers
    pipe_tags = {n.tag for n in layers["P-SANR-PIPE"] if isinstance(n, Polyline)}
    assert "PR-B-MAIN-DRAIN" in pipe_tags
    sleeve_symbols = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "sleeve"]
    assert len(sleeve_symbols) == 4


def test_main_plan_shows_sleeves_in_true_position_and_fixtures(catlin_model):
    scene = build_plumbing_plan(catlin_model, "main")
    layers = scene.by_layer()
    assert "A-FIXT" in layers
    sleeve_symbols = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "sleeve"]
    assert len(sleeve_symbols) == 4
    # No drain pipe polyline on the main plan — the collector run is a basement-storey run.
    pipe_polylines = [n for n in scene.nodes
                     if isinstance(n, Polyline) and n.layer == "P-SANR-PIPE"]
    assert pipe_polylines == []


def test_drain_run_has_slope_leader(catlin_model):
    scene = build_plumbing_plan(catlin_model, "basement")
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert any("DRAIN" in leader.text and "/FT" in leader.text for leader in leaders)


def test_plumbing_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_plumbing_plan(catlin_model, "basement")
    path = write_dxf(scene, tmp_path / "plumbing.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert "P-SANR-PIPE" in names
