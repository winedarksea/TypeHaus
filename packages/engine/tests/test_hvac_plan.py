"""HVAC plan builder — M-101 (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.hvacplan import build_hvac_plan, has_hvac_content
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


def test_second_floor_has_hvac_content(catlin_model):
    assert has_hvac_content(catlin_model, "second")
    assert not has_hvac_content(catlin_model, "attic")


def test_hvac_plan_symbol_census(catlin_model):
    scene = build_hvac_plan(catlin_model, "second")
    layers = scene.by_layer()
    assert "M-HVAC-SDFF" in layers and "M-HVAC-RDFF" in layers
    registers = [n for n in scene.nodes if isinstance(n, Symbol)
                 and n.name.startswith("register-")]
    assert len(registers) == 6
    duct_polys = [n for n in scene.nodes if isinstance(n, Polyline)
                 and n.layer in ("M-HVAC-SDFF", "M-HVAC-RDFF")]
    assert duct_polys


def test_hvac_plan_has_bearing_crossing_leader(catlin_model):
    scene = build_hvac_plan(catlin_model, "second")
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert any("FIRE BLOCKING" in leader.text for leader in leaders)


def test_hvac_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_hvac_plan(catlin_model, "second")
    path = write_dxf(scene, tmp_path / "hvac.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"M-HVAC-SDFF", "M-HVAC-RDFF"} <= names
