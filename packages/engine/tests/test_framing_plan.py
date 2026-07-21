"""Framing plan builder — first plan-view joist rendering, real S-101.n (→ 20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.scene import Polyline, Text
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


def test_starter_wires_floor_system(starter_model):
    # houses/starter/plan/storeys/main.py:FLOOR used to be an unwired bare JoistSpec.
    assert [f.tag for f in starter_model.floors] == ["FS-MAIN"]


def test_catlin_second_floor_joist_count_matches_resolved(catlin_model):
    floor = next(f for f in catlin_model.floors if f.tag == "FS-SECOND")
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    joist_nodes = [n for n in scene.by_layer()["S-FRAM"] if isinstance(n, Polyline)]
    assert len(joist_nodes) == len(floor.members)


def test_framing_plan_ghosts_bearing_storey_and_marks_bearing_walls(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    layers = scene.by_layer()
    assert "S-WALL" in layers and "S-WALL-BELW" in layers
    bearing_tags = {n.tag for n in layers["S-WALL"] if isinstance(n, Polyline)}
    assert bearing_tags == {"W-M-W2", "W-M-C2", "W-M-E1"}
    # every non-bearing wall of the same (main) storey is ghosted, not omitted
    ghosted_tags = {n.tag for n in layers["S-WALL-BELW"] if isinstance(n, Polyline)}
    assert ghosted_tags and not (ghosted_tags & bearing_tags)


def test_framing_plan_has_span_callout(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    texts = [n.content for n in scene.nodes if isinstance(n, Text) and n.layer == "S-FRAM"]
    assert any("I-JOIST" in t and "O.C." in t for t in texts)


def test_framing_plan_draws_stair_opening(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    layers = scene.by_layer()
    assert "S-FRAM-OPEN" in layers
    opening_tags = {n.tag for n in layers["S-FRAM-OPEN"] if isinstance(n, Polyline)}
    assert "FO-S-STAIR" in opening_tags


def test_stair_opening_clips_joists_and_uses_declared_west_bearing(catlin_model):
    floor = next(floor for floor in catlin_model.floors if floor.tag == "FS-SECOND")
    crossing_joists = [member for member in floor.members if member.category == "joist"
                       and 25 <= member.p0[1] / 0.3048 <= 36]
    assert crossing_joists
    assert all(member.p1[0] <= 11 * 0.3048 + 1e-9 or member.p0[0] >= 18 * 0.3048 - 1e-9
               for member in crossing_joists)
    headers = [member for member in floor.members if member.category == "header"
               and "FO-S-STAIR" in member.child_key]
    # The west edge bears on W-M-STRW/W-M-STRW2, so only the unsupported east edge needs a header.
    assert len(headers) == 1


def test_framing_plan_scene_snapshot_is_deterministic(catlin_model):
    a = build_framing_plan(catlin_model, "FS-SECOND")
    b = build_framing_plan(catlin_model, "FS-SECOND")
    assert a.to_json() == b.to_json()


def test_framing_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_framing_plan(catlin_model, "FS-SECOND")
    path = write_dxf(scene, tmp_path / "framing.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FRAM", "S-WALL", "S-WALL-BELW"} <= names
