"""``structural.bearing_wall_footing``: a framed bearing wall on a slab stands on footings.

The case that motivated it is catlin's W-B-CS3 — 46" of framed x=18' bearing wall between the
sauna and the W-B-CS2 pour, carrying FS-M-WEST/EAST, standing on the 3 1/2" slab with no
footing and no finding. The fix lengthens FT-B-CS north and FT-B-CS2 south past D-B-GYM's jamb
packs by the footing depth (params/foundations.py); the opening itself stays unfooted.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus.checks.structural.bearing_wall_footing import bearing_wall_footing
from typehaus.findings import Result

_IN = 0.0254


@pytest.fixture(scope="module")
def catlin_findings(catlin_ctx):
    return {f.element_tags[0]: f for f in bearing_wall_footing(catlin_ctx) if f.element_tags}


def _y_extent_in(model, tag):
    solid = next(s for s in model.solids if s.tag == tag)
    ys = [p[1] / _IN for p in solid.outline]
    return round(min(ys), 4), round(max(ys), 4)


def test_the_gym_door_wall_stands_on_its_neighbours_footings(catlin_findings) -> None:
    finding = catlin_findings["W-B-CS3"]
    assert finding.result is Result.PASS, finding.message
    assert "FT-B-CS" in finding.element_tags and "FT-B-CS2" in finding.element_tags


def test_the_strips_reach_past_the_jamb_packs_and_leave_the_opening_bare(catlin_ctx) -> None:
    # Jamb packs at y 124 7/16"..127 7/16" and 163 7/16"..166 7/16", + T = 8" each way.
    assert _y_extent_in(catlin_ctx.model, "FT-B-CS") == (0.0, 135.4375)
    assert _y_extent_in(catlin_ctx.model, "FT-B-CS2") == (155.4375, 216.0)
    # The bedding (and its drain tile) follow the footing's own outline.
    bed = next(b for b in catlin_ctx.model.footing_beddings if b.tag == "FB-B-CS")
    assert round(max(p[1] for p in bed.outline) / _IN, 4) == 135.4375


def test_without_the_extensions_it_fails_on_every_jamb_member(catlin_plan) -> None:
    from _helpers import CATLIN

    from typehaus.checks.run import build_context

    ctx, _ = build_context(catlin_plan, CATLIN)
    walls = {w.tag: w for w in ctx.model.walls}
    for tag, wall in (("FT-B-CS", "W-B-CS"), ("FT-B-CS2", "W-B-CS2")):
        index = next(i for i, s in enumerate(ctx.model.solids) if s.tag == tag)
        solid = ctx.model.solids[index]
        (_, y0), (_, y1) = walls[wall].axis
        xs = [p[0] for p in solid.outline]
        lo, hi = sorted((y0, y1))
        outline = [(min(xs), lo), (max(xs), lo), (max(xs), hi), (min(xs), hi)]
        ctx.model.solids[index] = replace(solid, outline=outline)
    finding = next(f for f in bearing_wall_footing(ctx) if f.element_tags[0] == "W-B-CS3")
    assert finding.result is Result.FAIL
    assert "4 of 4 bearing points" in finding.message
    for key in ("king-0-l0", "jack-0-l0", "jack-0-r0", "king-0-r0"):
        assert key in finding.message


def test_catlin_reports_every_framed_bearing_wall_on_the_slab(catlin_findings) -> None:
    assert set(catlin_findings) == {"W-B-CS", "W-B-CS3", "W-B-STR", "W-B-STR3", "W-B-STR3B"}
    assert all(f.result is Result.PASS for f in catlin_findings.values())
    # A thin END margin is disclosed, not graded: R403.1.1's P is a face projection.
    assert "1.88\" of footing past it" in catlin_findings["W-B-STR3B"].message


def test_a_nonbearing_partition_is_out_of_scope(catlin_findings) -> None:
    # W-B-CW2 stands on the slab with no footing, and nothing bears on it.
    assert "W-B-CW2" not in catlin_findings


def test_starter_earns_not_applicable(starter_dir) -> None:
    from typehaus.checks.run import build_context
    from typehaus.source import load_plan

    ctx, _ = build_context(load_plan(starter_dir).plan, starter_dir)
    findings = bearing_wall_footing(ctx)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]
    assert "none stands on a slab-on-grade" in findings[0].message
