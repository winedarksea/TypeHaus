"""Exterior trim follows the layers a recess reaches, including at panel bottoms."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.checks.integrity.cladding_trim_coverage import _bases, _window_like
from typehaus.checks.integrity.cladding_trim_runs import metal_wall_openings
from typehaus.findings import Result
from typehaus.model.cladding_trim import TrimCondition
from typehaus.resolve.cladding_trim.base import resolve_base_trim
from typehaus.resolve.cladding_trim.openings import (
    opening_cuts_profiled_metal_cladding,
    resolve_small_opening_trim,
)
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall


@pytest.fixture
def metal_wall_model():
    def layer(name, function, inner, outer):
        return ResolvedLayer(name=name, function=function, material_ref=name,
                             thickness_m=outer - inner,
                             polygon=((0, inner), (2, inner), (2, outer), (0, outer)))

    wall = ResolvedWall(uid="wall", tag="W", storey="main", assembly="test",
                        axis=((0, 0), (2, 0)), z0_m=0, z1_m=3, layers=(
                            layer("stud", "structure", 0, 0.14),
                            layer("sheathing", "sheathing", 0.14, 0.15),
                            layer("panel", "cladding", 0.15, 0.18)))
    opening = ResolvedOpening(uid="opening", tag="RO", host_wall="W", type_ref=None,
                              width_m=0.6, height_m=0.6, sill_m=0,
                              center_along_m=1, kind="rough_opening", is_door=False)
    material = SimpleNamespace(tag="panel", finish="ribbed-panel",
                               trim_kit={TrimCondition.BASE: "PBR_BASE"})
    library = SimpleNamespace(materials=(material,), resolve_assembly=lambda tag: None)
    return SimpleNamespace(walls=[wall], wall=lambda tag: wall if tag == wall.tag else None,
                           openings=[opening], solids=[],
                           plan=SimpleNamespace(library=library, project=SimpleNamespace(
                               opening_flashing_material="metal")))


@pytest.mark.parametrize("face,depth,expected", [
    ("interior", None, True),
    ("interior", 0.10, False),
    ("interior", 0.15 - 2e-6, False),
    ("interior", 0.15, False),
    ("interior", 0.15 + 0.5e-6, False),
    ("interior", 0.15 + 2e-6, True),
    ("exterior", 0.05, True),
])
def test_trim_and_checks_follow_cladding_cut_depth(metal_wall_model, face, depth, expected):
    model = metal_wall_model
    opening = replace(model.openings[0], depth_m=depth, depth_from=face)
    model.openings = [opening]
    assert opening_cuts_profiled_metal_cladding(model, model.walls[0], opening) is expected
    assert bool(list(metal_wall_openings(model, ("rough_opening",)))) is expected
    resolve_small_opening_trim(model)
    assert len(model.solids) == (4 if expected else 0)
    ctx = SimpleNamespace(model=model)
    assert not any(f.result is Result.FAIL for f in _window_like(ctx, model.solids))
    assert bool(_window_like(ctx, [])) is expected
    if expected:
        assert all(f.result is Result.FAIL for f in _window_like(ctx, []))


@pytest.mark.parametrize("face,depth,expected_length", [
    ("interior", 0.10, 2.0), ("interior", None, 1.4), ("exterior", 0.05, 1.4),
])
def test_base_stays_continuous_unless_opening_cuts_panel(
        metal_wall_model, face, depth, expected_length):
    model = metal_wall_model
    model.openings = [replace(model.openings[0], depth_m=depth, depth_from=face)]
    resolve_base_trim(model)
    assert sum(s.trim_length_m for s in model.solids) == pytest.approx(expected_length)
    assert len(model.solids) == (1 if expected_length == 2.0 else 2)
    assert all(f.result is Result.PASS for f in _bases(SimpleNamespace(model=model), model.solids))
    assert any(f.result is Result.FAIL for f in _bases(SimpleNamespace(model=model), []))


@pytest.mark.parametrize("width,expected_count", [(0.1524 - 1e-6, 0), (0.1524, 4)])
def test_exterior_blind_penetration_keeps_six_inch_threshold(
        metal_wall_model, width, expected_count):
    model = metal_wall_model
    model.openings = [replace(model.openings[0], width_m=width, height_m=width,
                              depth_m=0.05, depth_from="exterior")]
    resolve_small_opening_trim(model)
    assert len(model.solids) == expected_count
    assert not any(f.result is Result.FAIL
                   for f in _window_like(SimpleNamespace(model=model), model.solids))
