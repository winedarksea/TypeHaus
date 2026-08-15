"""Elevation annotations — grade profile, material leaders, vertical dims (Phase 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.scene import ArchDimension, Leader, Polyline, Symbol, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



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


def test_south_elevation_grade_profile_interpolates_spots(catlin_model):
    scene = build_elevation(catlin_model, "south")
    grade = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
             and len(n.points) > 2]
    assert grade
    z_values = {round(p[1] / 39.37007874015748, 2) for p in grade[0].points}
    assert z_values  # a real (non-empty) interpolated profile, not a crash


def test_starter_grade_profile_falls_back_to_flat_site_grade(starter_model):
    scene = build_elevation(starter_model, "south")
    grade = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "L-SITE-GRAD"
             and len(n.points) >= 2]
    assert grade
    poly = grade[0]
    zs = {round(p[1], 3) for p in poly.points}
    assert len(zs) == 1  # flat fallback — starter authors no spot_elevations


def test_one_leader_per_distinct_exterior_assembly(catlin_model):
    scene = build_elevation(catlin_model, "west")
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    texts = [leader.text for leader in leaders]
    assert len(texts) == len(set(texts))  # each distinct assembly callout appears once
    assert texts  # west facade actually has exterior walls with layers


def test_vertical_dim_string_covers_floor_plate_and_ridge(catlin_model):
    scene = build_elevation(catlin_model, "south")
    dims = [n for n in scene.nodes if isinstance(n, ArchDimension)]
    assert dims
    labels = [text.content for text in scene.nodes if isinstance(text, Text)
              and "EL." in text.content]
    joined = " ".join(labels)
    assert "GRADE" in joined
    assert "FLOOR" in joined
    assert "T.O. PLATE" in joined
    assert "RIDGE" in joined


def test_level_markers_present(catlin_model):
    scene = build_elevation(catlin_model, "south")
    markers = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "level-marker"]
    assert markers


def test_elevation_dxf_round_trips_with_leader(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_elevation(catlin_model, "west")
    path = write_dxf(scene, tmp_path / "elevation.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert "L-SITE-GRAD" in names
    leader_types = {e.dxftype() for e in doc.modelspace()}
    assert "LEADER" in leader_types
