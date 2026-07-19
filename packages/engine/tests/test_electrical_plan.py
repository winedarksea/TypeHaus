"""Electrical plan builder — E-101+ (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.scene import Symbol
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


def test_starter_has_no_electrical_content(starter_model):
    assert not any(has_electrical_content(starter_model, s.tag) for s in starter_model.plan.storeys)


def test_main_plan_symbol_census(catlin_model):
    scene = build_electrical_plan(catlin_model, "main")
    symbols = [n for n in scene.nodes if isinstance(n, Symbol)]
    kinds = {n.name for n in symbols}
    assert {"light", "switch"} <= kinds


def test_basement_plan_has_panel(catlin_model):
    scene = build_electrical_plan(catlin_model, "basement")
    symbols = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "panel"]
    assert symbols


def test_legend_reflects_present_device_kinds(catlin_model):
    from typehaus.emit.draw.scene import Text

    scene = build_electrical_plan(catlin_model, "second")
    texts = {n.content for n in scene.nodes if isinstance(n, Text)}
    assert "LEGEND" in texts
    assert "LIGHT" in texts and "SWITCH" in texts


def test_electrical_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_electrical_plan(catlin_model, "main")
    path = write_dxf(scene, tmp_path / "electrical.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"E-POWR-DEVC", "E-LITE"} <= names
