"""Foundation plan builder — real S-100 (Permit-ready plan set Phase 1, → 20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.foundationplan import build_foundation_plan, has_foundation_content
from typehaus.emit.draw.scene import Leader, Polyline
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


def test_catlin_has_foundation_content(catlin_model):
    assert has_foundation_content(catlin_model)


def test_starter_has_no_foundation_content(starter_model):
    # Starter is a simple two-storey box with no FoundationWall/Footing/Pad/Slab —
    # S-100 must be omitted from the sheet index for it (build_sheet_index test covers that).
    assert not has_foundation_content(starter_model)


def test_foundation_plan_draws_basement_walls_and_slab(catlin_model):
    scene = build_foundation_plan(catlin_model)
    layers = scene.by_layer()
    assert "S-FNDN" in layers
    assert "A-SLAB" in layers
    slab_tags = {n.tag for n in layers["A-SLAB"] if isinstance(n, Polyline)}
    assert "SL-B-FLOOR" in slab_tags
    # Walls drawn are all on the lowest (basement) storey — never a re-render of "main".
    wall_tags = {n.tag for n in layers["S-FNDN"] if isinstance(n, Polyline)}
    assert {"W-B-S1", "W-B-CS", "W-GF-N"} <= wall_tags
    assert all(catlin_model.wall(tag).storey == "basement" for tag in wall_tags)


def test_foundation_plan_has_footing_leaders(catlin_model):
    scene = build_foundation_plan(catlin_model)
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert leaders
    assert any("CONT. FTG." in leader.text for leader in leaders)


def test_starter_foundation_plan_is_empty(starter_model):
    scene = build_foundation_plan(starter_model)
    assert scene.nodes == ()


def test_foundation_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_foundation_plan(catlin_model)
    path = write_dxf(scene, tmp_path / "foundation.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FNDN", "S-FNDN-FTNG", "A-SLAB"} <= names
