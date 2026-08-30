"""The schedule stack beside a plan reflows into columns instead of one tall stack.

S-100 printed at 3/32" = 1'-0" on a 24x36 sheet — the bottom of the scale ladder, on the
biggest paper — because the sheet is fitted to the *scene* bounding box and the schedule
column ran to twice the plan's height. The building was being drawn small to make room for
its own tables. These tests pin the two halves of the fix: that ``block_extent`` measures
exactly what the emitters draw (a mirror that silently drifts stacks blocks on top of each
other), and that the reflow actually buys printed scale without cutting a table in half.
"""

from __future__ import annotations

from typehaus.emit.draw.foundation_schedule import foundation_walls
from typehaus.emit.draw.foundationplan import _drawn_plan_points, build_foundation_plan
from typehaus.emit.draw.paper import ARCH_D, LEDGER
from typehaus.emit.draw.scene import SceneBuilder, Text
from typehaus.emit.draw.schedule_block import (
    CHARACTER_WIDTH_RATIO,
    NoteBlock,
    ScheduleTable,
    block_extent,
    emit_block,
    emit_block_columns,
    metrics_for,
)
from typehaus.emit.draw.sheet_writer import frame_for_scene

_TABLE = ScheduleTable(
    title="FOOTING / PAD SCHEDULE",
    columns=("MARK", "TYPE", "SIZE"),
    rows=(("F1", "CONT. STRIP FTG.", '10" W x 5" D'),
          ("F2", "SPREAD FTG.", '30" W x 12" D'),
          ("P1", "PAD", "2'-0\" x 2'-0\" x 12\" THK")),
)
_NOTES = NoteBlock(
    title="FOUNDATION NOTES",
    notes=("ALL FOOTINGS TO BEAR 42\" MIN BELOW THE LOWEST ADJACENT FINISHED GRADE PER "
           "IRC R403.1.4.1, WHICH IS LONG ENOUGH TO WRAP ONTO A SECOND LINE AND THEN SOME "
           "SO THAT THE WRAPPED HEIGHT IS ACTUALLY EXERCISED HERE.",
           "FOOTINGS BEAR AT 6 ELEVATIONS."),
)


def _metrics():
    return metrics_for([(0.0, 0.0), (452.0, 1184.8)])


# --- the measurement mirrors the emitters -------------------------------------


def test_block_extent_height_is_what_the_emitter_draws():
    metrics = _metrics()
    for block in (_TABLE, _NOTES):
        b = SceneBuilder(name="t", units="in")
        bottom = emit_block(b, block, (0.0, 0.0), metrics)
        assert abs(-bottom - block_extent(block, metrics)[1]) < 1e-9, block.title


def test_block_extent_width_covers_every_line_the_emitter_draws():
    metrics = _metrics()
    for block in (_TABLE, _NOTES):
        b = SceneBuilder(name="t", units="in")
        emit_block(b, block, (0.0, 0.0), metrics)
        drawn = max(len(line) * node.height * CHARACTER_WIDTH_RATIO
                    for node in b.build().nodes if isinstance(node, Text)
                    for line in node.content.splitlines())
        assert block_extent(block, metrics)[0] >= drawn - 1e-9, block.title


def test_an_empty_block_takes_no_room_and_draws_nothing():
    metrics = _metrics()
    empty_table = ScheduleTable(title="X", columns=("A",), rows=())
    empty_notes = NoteBlock(title="Y", notes=())
    for block in (empty_table, empty_notes):
        b = SceneBuilder(name="t", units="in")
        assert emit_block(b, block, (0.0, 0.0), metrics) == 0.0
        assert not b.build().nodes
        assert block_extent(block, metrics) == (0.0, 0.0)


# --- the reflow ----------------------------------------------------------------


def _title_anchors(scene, titles) -> dict[str, tuple[float, float]]:
    return {node.content: node.anchor for node in scene.nodes
            if isinstance(node, Text) and node.content in titles}


def test_reflow_columns_read_top_to_bottom_then_left_to_right():
    """Six blocks, deliberately taller than the plan they sit beside."""
    metrics = _metrics()
    blocks = [ScheduleTable(title=f"TABLE {i}", columns=("MARK", "SIZE"),
                            rows=tuple((f"M{r}", "10\" W") for r in range(8)))
              for i in range(6)]
    plan = [(0.0, 0.0), (452.0, 1184.8)]
    b = SceneBuilder(name="t", units="in")
    emit_block_columns(b, blocks, plan, metrics)
    scene = b.build()
    anchors = _title_anchors(scene, {block.title for block in blocks})
    assert len(anchors) == len(blocks)
    order = [anchors[block.title] for block in blocks]
    assert len({x for x, _y in order}) > 1, "a stack this tall must reflow into columns"
    # Reading order: x never goes backwards, and inside one column y only descends.
    for (x0, y0), (x1, y1) in zip(order, order[1:], strict=False):
        assert x1 >= x0
        if x1 == x0:
            assert y1 < y0


def test_a_table_is_never_split_across_columns():
    """Every row of one table shares its table's column — the whole point of a *block*."""
    metrics = _metrics()
    b = SceneBuilder(name="t", units="in")
    emit_block_columns(b, [_TABLE, _NOTES, _TABLE, _NOTES], [(0.0, 0.0), (452.0, 600.0)],
                       metrics)
    xs = sorted({round(node.anchor[0], 6) for node in b.build().nodes
                 if isinstance(node, Text)})
    # One x per column, not one per row: rows are drawn as whole padded strings.
    assert 1 <= len(xs) <= 4


def test_reflow_beats_a_single_column_on_the_sheet(catlin_model):
    """S-100 must print bigger than the 3/32" the single stack forced it down to."""
    scene = build_foundation_plan(catlin_model)
    assert frame_for_scene(scene, ARCH_D).scale_label == "3/16\" = 1'-0\""
    assert frame_for_scene(scene, LEDGER).scale_label == "1/16\" = 1'-0\""


def test_the_schedule_no_longer_governs_the_sheet_height(catlin_model):
    """The plan, not its tables, is what the sheet is now fitted to vertically."""
    from typehaus.emit.draw.pdf_writer import _scene_bounds

    plan_points = _drawn_plan_points(catlin_model, foundation_walls(catlin_model))
    plan_height = (max(p[1] for p in plan_points) - min(p[1] for p in plan_points))
    _u0, z0, _u1, z1 = _scene_bounds(build_foundation_plan(catlin_model))
    # Some slack for the leaders and dimension chain that hang below the plan itself.
    assert z1 - z0 < plan_height * 1.25
