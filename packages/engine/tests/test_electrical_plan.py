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


def test_every_habitable_room_has_a_light_and_a_switch(catlin_model):
    """``electrical.room_lighting`` matches devices to rooms by tag suffix, so a room that
    gains a light also needs its tag to line up — the two ways this regresses (no device at
    all, device tagged for the wrong room) both surface as the same FAIL."""
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.room_lighting"]
    assert findings
    assert all(f.result.value == "pass" for f in findings), \
        [f.message for f in findings if f.result.value != "pass"]


def test_the_previously_dark_habitable_rooms_are_covered(catlin_model):
    """The three rooms that had no lighting at all: the basement gym and both habitable
    attic rooms. Named explicitly so deleting a device from one of them fails here instead
    of quietly shrinking the census in the test above."""
    tags = {element.tag for storey in catlin_model.plan.storeys
            for element in catlin_model.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"}
    for room_suffix in ("B-GYM", "A-EAST", "A-STUDY"):
        assert f"ED-{room_suffix}-LT" in tags
        assert f"ED-{room_suffix}-SW" in tags


def test_electrical_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_electrical_plan(catlin_model, "main")
    path = write_dxf(scene, tmp_path / "electrical.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"E-POWR-DEVC", "E-LITE"} <= names
