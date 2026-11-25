"""``structural.veneer_lintel`` against IRC Table R703.8.3.1 (notes/sunken_garden_veneer_beam.md
§6l): both brick reveals are flat-headed on one L3x3x1/4 hot-dip galvanized angle each."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus.checks.structural import veneer_lintel
from typehaus.findings import Result


def test_table_rows_read_the_angle_not_a_guess() -> None:
    assert veneer_lintel.table_row("L3x3x0.25") == ((3.0, 3.0, 0.25), 72.0)
    assert veneer_lintel.table_row("L4x3x0.25")[1] == 96.0
    # A larger angle in every leg reads at the largest row it meets.
    assert veneer_lintel.table_row("L3.5x3.5x0.25") == ((3.0, 3.0, 0.25), 72.0)
    assert veneer_lintel.table_row("L3x3x0.1875") is None      # thinner than the 1/4" row
    assert veneer_lintel.table_row("2x6") is None


def test_both_reveals_pass_on_the_3x3x1_4_row(catlin_brick_ctx) -> None:
    findings = veneer_lintel.veneer_lintel(catlin_brick_ctx)
    assert {f.message.split(":")[0] for f in findings} == {"AO-B-BRICK-WIN", "AO-B-BRICK-DOOR"}
    assert all(f.result is Result.PASS for f in findings), [f.message for f in findings]
    door = next(f for f in findings if f.message.startswith("AO-B-BRICK-DOOR"))
    # R703.8.3: 4" of bearing a side; the table's 6'-0" with no story above (the porch joists
    # clear the wythe's top by 2"); 63 5/16" is the RO's clear width.
    assert "63.31\" clear under BM-B-BRICK-LINTEL-DOOR" in door.message
    assert "spans 6' with no story above, 4.00\" of bearing a side" in door.message
    # R703.8.5: the head flashing is a model fact now, not a note about a wall section.
    assert "flashed over per R703.8.5 by FL-B-BRICK-DOOR-HEAD" in door.message
    # Owner: stainless flashing, kept off the HDG angle by a 1/16" EPDM strip.
    assert ("on the EPDM strip FL-B-BRICK-DOOR-ISOL, so stainless and zinc never touch"
            in door.message)


def test_an_opening_with_no_lintel_is_a_fail(catlin_brick_ctx) -> None:
    model = replace(catlin_brick_ctx.model, solids=[
        s for s in catlin_brick_ctx.model.solids if s.tag != "BM-B-BRICK-LINTEL-DOOR"])
    results = {f.message.split(":")[0]: f
               for f in veneer_lintel.veneer_lintel(replace(catlin_brick_ctx, model=model))}
    assert results["AO-B-BRICK-DOOR"].result is Result.FAIL
    assert results["AO-B-BRICK-WIN"].result is Result.PASS


def test_framing_over_the_wythe_makes_the_no_story_column_unanswerable(catlin_brick_ctx) -> None:
    from shapely.geometry import Polygon

    wythe = catlin_brick_ctx.model.wall("W-B-BRICK")
    brick = next(ly for ly in wythe.layers if ly.function == "structure" and ly.polygon)
    assert veneer_lintel._framed_over(catlin_brick_ctx, wythe, Polygon(brick.polygon)) == []
    assert wythe.z1_m == pytest.approx(-13.333 * 0.0254, abs=1e-3)


def test_stainless_on_the_galvanized_angle_with_no_strip_is_a_fail(catlin_brick_ctx) -> None:
    model = replace(catlin_brick_ctx.model)
    plan = catlin_brick_ctx.model.plan

    class _Plan:
        def __getattr__(self, name):
            return getattr(plan, name)

        def all_elements(self):
            return [e for e in plan.all_elements()
                    if getattr(e, "tag", "") != "FL-B-BRICK-DOOR-ISOL"]

    ctx = replace(catlin_brick_ctx, plan=_Plan(), model=model)
    results = {f.message.split(":")[0]: f for f in veneer_lintel.veneer_lintel(ctx)}
    assert results["AO-B-BRICK-DOOR"].result is Result.FAIL
    assert "no EPDM strip" in results["AO-B-BRICK-DOOR"].message
    assert results["AO-B-BRICK-WIN"].result is Result.PASS
