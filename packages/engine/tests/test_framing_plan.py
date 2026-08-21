"""Framing plan builder — first plan-view joist rendering, real S-101.n (→ 20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan


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
    floor = next(f for f in catlin_model.floors if f.tag == "FS-S-EAST")
    scene = build_framing_plan(catlin_model, "FS-S-EAST")
    joist_nodes = [n for n in scene.by_layer()["S-FRAM"] if isinstance(n, Polyline)]
    assert len(joist_nodes) == len(floor.members)


def test_framing_plan_ghosts_bearing_storey_and_marks_bearing_walls(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-S-EAST")
    layers = scene.by_layer()
    assert "S-WALL" in layers and "S-WALL-BELW" in layers
    bearing_tags = {n.tag for n in layers["S-WALL"] if isinstance(n, Polyline)}
    # The deck's declared bearing refs plus every wall below authored StructuralRole.BEARING
    # are drawn heavy; the S-101 schedule keeps the two apart. role_bearing_walls covers
    # every bearing wall on the storey regardless of which half's own refs name it, so all
    # three show up even though FS-S-EAST's own bearing_refs are W-M-C2/W-M-E1/BM-M-HALL.
    assert {"W-M-W2", "W-M-C2", "W-M-E1"} <= bearing_tags
    assert all(catlin_model.wall(tag).storey == "main" for tag in bearing_tags)
    # every non-bearing wall of the same (main) storey is ghosted, not omitted
    ghosted_tags = {n.tag for n in layers["S-WALL-BELW"] if isinstance(n, Polyline)}
    assert ghosted_tags and not (ghosted_tags & bearing_tags)


def test_framing_plan_has_span_callout(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-S-EAST")
    texts = [n.content for n in scene.nodes if isinstance(n, Text) and n.layer == "S-FRAM"]
    assert any("I-JOIST" in t and "O.C." in t for t in texts)


def test_framing_plan_draws_stair_opening(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-S-WEST")
    layers = scene.by_layer()
    assert "S-FRAM-OPEN" in layers
    opening_tags = {n.tag for n in layers["S-FRAM-OPEN"] if isinstance(n, Polyline)}
    assert "FO-S-STAIR" in opening_tags


def test_stair_opening_clips_joists_and_uses_declared_west_bearing(catlin_model):
    floor = next(floor for floor in catlin_model.floors if floor.tag == "FS-S-WEST")
    opening = catlin_model.plan.by_tag("FO-S-STAIR")
    ys = [point.xy_m[1] for point in opening.outline]
    west_face = min(point.xy_m[0] for point in opening.outline)
    crossing_joists = [member for member in floor.members if member.category == "joist"
                       and min(ys) - 1e-9 <= member.p0[1] <= max(ys) + 1e-9]
    assert crossing_joists
    # The opening is drawn to the finished well, so the clip is W-M-STRW's stair-side face
    # (x=10'-3 3/8"); joists resume at the centre bearing line. Nothing is emitted for the
    # 3 3/8" of deck between the well's east edge and that line — that is bearing seat.
    assert west_face / 0.3048 == pytest.approx(10 + 3.375 / 12)
    assert all(member.p1[0] <= west_face + 1e-9 or member.p0[0] >= 18 * 0.3048 - 1e-9
               for member in crossing_joists)
    headers = [member for member in floor.members if member.category == "header"
               and "FO-S-STAIR" in member.child_key]
    # Both long edges bear on wall — W-M-STRW/STRW2 west, W-M-C5/C4B east — so the opening
    # needs no header at all. The bearing test is on the walls' footprints, not their
    # centrelines, which is what lets a well drawn to the finished face be recognised.
    assert headers == []


def test_framing_plan_scene_snapshot_is_deterministic(catlin_model):
    a = build_framing_plan(catlin_model, "FS-S-EAST")
    b = build_framing_plan(catlin_model, "FS-S-EAST")
    assert a.to_json() == b.to_json()


def test_framing_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_framing_plan(catlin_model, "FS-S-EAST")
    path = write_dxf(scene, tmp_path / "framing.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FRAM", "S-WALL", "S-WALL-BELW"} <= names
