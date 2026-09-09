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
    # houses/starter/plan/storeys/main.py:FLOOR is wired to a real FloorSystem.
    assert [f.tag for f in starter_model.floors] == ["FS-MAIN"]


def test_catlin_second_floor_joist_count_matches_resolved(catlin_model):
    """One sheet per STOREY, so the count is every deck on it — three, not one."""
    floors = [f for f in catlin_model.floors if f.storey == "second"]
    assert len(floors) > 1, "the storey merge is only interesting on a multi-deck storey"
    scene = build_framing_plan(catlin_model, "second")
    joist_nodes = [n for n in scene.by_layer()["S-FRAM"] if isinstance(n, Polyline)]
    assert len(joist_nodes) == sum(len(floor.members) for floor in floors)


def test_framing_plan_ghosts_bearing_storey_and_marks_bearing_walls(catlin_model):
    scene = build_framing_plan(catlin_model, "second")
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
    scene = build_framing_plan(catlin_model, "second")
    texts = [n.content for n in scene.nodes if isinstance(n, Text) and n.layer == "S-FRAM"]
    assert any("I-JOIST" in t and "O.C." in t for t in texts)


def test_framing_plan_draws_stair_opening(catlin_model):
    scene = build_framing_plan(catlin_model, "second")
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
    a = build_framing_plan(catlin_model, "second")
    b = build_framing_plan(catlin_model, "second")
    assert a.to_json() == b.to_json()


def test_framing_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_framing_plan(catlin_model, "second")
    path = write_dxf(scene, tmp_path / "framing.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FRAM", "S-WALL", "S-WALL-BELW"} <= names


# --- one sheet per storey -----------------------------------------------------


def test_marks_are_unique_across_a_multi_deck_storey(catlin_model):
    """The merge is only honest if the marks are. Six decks each numbering their own
    joists ``J1`` would put six different members under one mark on one sheet."""
    from typehaus.emit.draw.framing_schedule import framed_levels

    levels = framed_levels(catlin_model, "main")
    assert len(levels) > 1
    marks = levels[0].marks
    assert all(level.marks is marks for level in levels), "one shared table"
    joist_marks = [mark for key, mark in marks.items() if key.endswith("/category:joist")]
    assert len(joist_marks) == len(set(joist_marks)) == len(levels)


def test_a_beam_two_decks_share_gets_one_mark(catlin_model):
    """Beams are keyed on globally unique element tags, so numbering them in one pass over
    the storey's decks makes a shared beam one mark for free."""
    from typehaus.emit.draw.framing_schedule import (
        build_storey_framing_schedules,
        framed_levels,
    )

    levels = framed_levels(catlin_model, "second")
    shared = [beam.tag for level in levels for beam, _span in level.beams]
    assert len(shared) > len(set(shared)), "catlin's second storey shares a beam"
    table = next(t for t in build_storey_framing_schedules(levels)
                 if t.title.startswith("BEAM / POST"))
    tags = [row[1] for row in table.rows]
    assert len(tags) == len(set(tags)), "a shared beam is scheduled once"
    marks = [row[0] for row in table.rows]
    assert len(marks) == len(set(marks))


def test_walls_below_are_drawn_once_not_once_per_deck(catlin_model):
    """Six coincident copies of one wall is not a heavier line — it is a broken DXF.

    ``emit_wall`` draws one polyline per layer (and two layers can be geometrically
    identical), so the invariant is per WALL: the sheet must contain exactly as many nodes
    for a wall as one ``emit_wall`` call produces, no matter how many decks sit over it.
    """
    from typehaus.emit.draw._shared import emit_wall
    from typehaus.emit.draw.lineweights import CUT
    from typehaus.emit.draw.scene import SceneBuilder

    scene = build_framing_plan(catlin_model, "main")
    drawn = [n for layer in ("S-WALL", "S-WALL-BELW")
             for n in scene.by_layer().get(layer, []) if isinstance(n, Polyline)]
    counts: dict[str, int] = {}
    for node in drawn:
        counts[node.tag] = counts.get(node.tag, 0) + 1
    assert counts

    for tag, count in counts.items():
        builder = SceneBuilder(name="one", units="in")
        emit_wall(builder, catlin_model.wall(tag), layer_override="S-WALL",
                  weight_override=CUT, members=False)
        once = len([n for n in builder.build().nodes if isinstance(n, Polyline)])
        assert count == once, f"{tag} is drawn {count} times over, not {once}"
