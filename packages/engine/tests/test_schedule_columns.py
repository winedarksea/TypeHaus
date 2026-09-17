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
    SHEET_VIEWPORT_ASPECT,
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
    """S-100 must print bigger than the 3/32" the single stack forced it down to.

    ** ARCH D WENT 3/16" -> 1/8" AND BACK ON 2026-09-05, AND THE MARGIN IS 0.18". ** The
    basement's west-side replan minted one new foundation assembly that morning
    (``SAUNA_LINER_ON_BASEMENT_8``, the sauna's liner over the buried south pour), which was
    one more row in the FOUNDATION WALL SCHEDULE. That column already carries all three
    schedules — the reflow puts them there because the sheet has no width left to open a
    fourth column with, the plan being 37'-8" wide — so one row is 29.6 drawing-inches on the
    tallest column, the scene went 1412" -> 1442" tall, and 3/16" needed 1424". The
    afternoon's shrink pulled the sauna onto the garden curb, deleted that assembly, and
    handed the scale back.

    ** THAT 0.18" IS SPENT, AND THE TITLE BLOCK SPENT IT (2026-09-06). ** The margin at
    3/16" was 0.18" of scene height against a schedule row's 29.6", and the sheet is 94% of
    the ARCH D width as well — a knife-edge in both directions. Giving every sheet a real
    NCS title block (revision block, seal box, issue stamp) costs more than that in either
    geometry: as a bottom strip it takes the height, and on the right edge it takes the
    width this sheet has only 2.17" of to spare. So ARCH D is 1/8" now, deliberately.

    **The assertion this test exists for still holds**, and it is not the scale label: the
    reflow keeps S-100 well above the 3/32" the single stack forced it down to. What changed
    is one step, not the defect.

    The lever, if 3/16" is wanted back, is `sheet_writer.TITLE_W` — and the honest options
    are a narrower block or a schedule that does not need a full column, not a smaller
    drawing.

    ** THE LEDGER CHECK PRINT WENT 1/16" -> 1" = 20' ON 2026-09-17, AND THE SCHEDULE BOUGHT
    IT. ** The rebar work gave S-100 two blocks it did not have: the FOUNDATION
    REINFORCEMENT SCHEDULE and the 25-entry FOUNDATION CALLOUTS key. At 1/8" no split of the
    stack puts the scene under 2,848" wide, and ledger's viewport needs 2,669" for 1/16".
    ARCH D — the sheet that gets sealed — is unaffected and still 1/8"; ledger is the check
    print, and one step there is the price of scheduling the reinforcement at all. Getting
    it back means fewer full-width tables, not a tighter drawing.
    """
    scene = build_foundation_plan(catlin_model)
    assert frame_for_scene(scene, ARCH_D).scale_label == "1/8\" = 1'-0\""
    assert frame_for_scene(scene, LEDGER).scale_label == "1\" = 20'"


#: What "the tables do not govern the sheet" is actually worth, as a ratio against the drawn
#: plan's own height. Kept as a *reported* number rather than the assertion: the guard below
#: asserts the property directly, and this is here so a failure can say how far the tables
#: have drifted from the drawing they annotate.
#:
#: ** THIS USED TO BE THE ASSERTION, AT 1.35, AND IT WAS MEASURING THE WRONG THING. ** The
#: defect the module is about is a scene TWICE the plan's height, which put S-100 at 3/32"
#: on ARCH D — but the plain ratio only stands in for that while HEIGHT is what
#: ``select_scale`` runs out of. Catlin's foundation plan is 446" wide against 1,187" deep,
#: a portrait drawing on a landscape sheet, so the schedule columns fill width the plan
#: was never going to use and WIDTH is what binds. On 2026-09-17 the ratio read 1.354
#: against a 1.35 limit while the sheet printed at full 1/8" with 172" of vertical room to
#: spare — a red test over a sheet with nothing wrong with it.
SCENE_TO_PLAN_HEIGHT_REPORTED = 1.4


def test_the_schedule_no_longer_governs_the_sheet_height(catlin_model):
    """The plan, not its tables, is what the sheet is fitted to.

    Stated as ``select_scale`` sees it: of the two spans it fits, the one that runs out
    first must be the width — the schedule stack may not be the taller constraint. That is
    the property the reflow buys, and it holds no matter which way round the plan is.
    """
    from typehaus.emit.draw.pdf_writer import _scene_bounds

    plan_points = _drawn_plan_points(catlin_model, foundation_walls(catlin_model))
    plan_height = (max(p[1] for p in plan_points) - min(p[1] for p in plan_points))
    u0, z0, u1, z1 = _scene_bounds(build_foundation_plan(catlin_model))
    binding_width = (u1 - u0) / SHEET_VIEWPORT_ASPECT
    assert z1 - z0 < binding_width, (
        f"the schedule stack is what the sheet is fitted to: {z1 - z0:.1f}\" of scene height "
        f"against {binding_width:.1f}\" of width-equivalent, and the drawn plan is only "
        f"{plan_height:.1f}\" tall. Split the stack differently or shorten a table — do not "
        "reach for a lettering multiplier, which widens every table and costs printed scale")
    ratio = (z1 - z0) / plan_height
    assert ratio < SCENE_TO_PLAN_HEIGHT_REPORTED, (
        f"the scene is {ratio:.4f}x the drawn plan's height. One schedule row is worth "
        "0.025 of this ratio. This is the loose bound, not the property above — if it fires "
        "the tables have grown a long way past the drawing they annotate")
