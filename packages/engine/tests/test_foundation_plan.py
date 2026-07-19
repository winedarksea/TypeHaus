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


def test_catlin_house_footings_resolve_bedding(catlin_model):
    house_footings = {tag for tag in
                      (s.tag for s in catlin_model.solids if s.category == "footing")
                      if tag.startswith("FT-B-")}
    bedding_hosts = {fb.host_footing for fb in catlin_model.footing_beddings}
    assert house_footings
    assert house_footings <= bedding_hosts


def test_footing_bedding_undercut_and_insulation(catlin_model):
    bedding = next(fb for fb in catlin_model.footing_beddings if fb.host_footing == "FT-B-S1")
    assert bedding.z1_m > bedding.z0_m  # bed sits below the footing underside
    assert 0.15 < bedding.z1_m - bedding.z0_m < 0.22  # ~7" undercut
    assert bedding.geotextile and bedding.drain_tile
    assert bedding.perimeter_insulation_m is not None
    assert "#57" in bedding.aggregate


def test_foundation_plan_has_footing_bedding_leader(catlin_model):
    scene = build_foundation_plan(catlin_model)
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert any("WASHED CRUSHED STONE" in leader.text for leader in leaders)
    assert any("GEOTEXTILE" in leader.text for leader in leaders)


def test_starter_foundation_plan_is_empty(starter_model):
    scene = build_foundation_plan(starter_model)
    assert scene.nodes == ()


def test_footing_bedding_rejects_missing_host():
    from typehaus.model.structure import FootingBedding
    from typehaus.quantities import inch
    from typehaus.resolve.envelope import _resolve_footing_bedding
    from typehaus.resolve.model import ResolvedModel

    class _Plan:
        pass

    bedding = FootingBedding(uid="FB1", tag="FB-MISSING", host_ref="FT-NOPE",
                             undercut=inch(7))
    model = ResolvedModel(plan=_Plan())
    resolved, findings = _resolve_footing_bedding(model, bedding, "basement")
    assert resolved is None
    assert findings and findings[0].check_id == "integrity.footing_bedding_host"


def test_foundation_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_foundation_plan(catlin_model)
    path = write_dxf(scene, tmp_path / "foundation.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FNDN", "S-FNDN-FTNG", "A-SLAB"} <= names
