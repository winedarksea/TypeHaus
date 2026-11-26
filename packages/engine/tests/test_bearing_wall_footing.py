"""``structural.bearing_wall_footing``: a framed bearing wall on a slab stands on footings.

The case that motivated it is catlin's W-B-CS3 — 60 5/8" of framed x=18' bearing wall between
the sauna and the hall's south end, carrying FS-M-WEST/EAST, which stood on the 3 1/2" slab with
no footing and no finding. The fix runs FT-B-CS north under it and past D-B-GYM's south jamb
pack (on W-B-CS2) by the footing depth; FT-B-CS2 starts 8" short of the north pack
(params/foundations.py). The opening itself stays unfooted.
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
    assert "FT-B-CS" in finding.element_tags
    # D-B-GYM's south pack (W-B-CS2) stands on the same strip, past the opening's edge.
    assert "FT-B-CS" in catlin_findings["W-B-CS2"].element_tags


def test_the_strips_reach_past_the_jamb_packs_and_leave_the_opening_bare(catlin_ctx) -> None:
    # D-B-GYM's opening is y 163"..199"; jamb packs at 158 1/2"..163" and 199"..203 1/2", + T = 8".
    assert _y_extent_in(catlin_ctx.model, "FT-B-CS") == (0.0, 171.0)
    assert _y_extent_in(catlin_ctx.model, "FT-B-CS2") == (191.0, 216.0)
    # The bedding (and its drain tile) follow the footing's own outline.
    bed = next(b for b in catlin_ctx.model.footing_beddings if b.tag == "FB-B-CS")
    assert round(max(p[1] for p in bed.outline) / _IN, 4) == 171.0


def test_without_the_extension_it_fails_on_every_bearing_member(catlin_plan) -> None:
    from _helpers import CATLIN

    from typehaus.checks.run import build_context

    ctx, _ = build_context(catlin_plan, CATLIN)
    walls = {w.tag: w for w in ctx.model.walls}
    index = next(i for i, s in enumerate(ctx.model.solids) if s.tag == "FT-B-CS")
    solid = ctx.model.solids[index]
    (_, y0), (_, y1) = walls["W-B-CS"].axis       # FT-B-CS cut back to its own wall
    xs = [p[0] for p in solid.outline]
    lo, hi = sorted((y0, y1))
    ctx.model.solids[index] = replace(
        solid, outline=[(min(xs), lo), (max(xs), lo), (max(xs), hi), (min(xs), hi)])
    found = {f.element_tags[0]: f for f in bearing_wall_footing(ctx) if f.element_tags}
    finding = found["W-B-CS3"]
    assert finding.result is Result.FAIL
    assert "4 of 4 bearing points" in finding.message
    # D-B-GYM's south king and two jacks stand in the gap between the strips.
    gym = found["W-B-CS2"]
    assert gym.result is Result.FAIL
    assert "3 of 7 bearing points" in gym.message
    for key in ("king-0-l0", "jack-0-l1", "jack-0-l0"):
        assert key in gym.message


def test_catlin_reports_every_framed_bearing_wall_on_the_slab(catlin_findings) -> None:
    walls = {k: f for k, f in catlin_findings.items() if k.startswith("W-")}
    # W-B-CS2/CN2/CN joined on 2026-11-01: 2x6 on their footings, no longer pours (#112).
    assert set(walls) == {"W-B-CS", "W-B-CS2", "W-B-CS3", "W-B-CN", "W-B-CN2", "W-B-STR",
                          "W-B-STR3", "W-B-STR3B"}
    assert all(f.result is Result.PASS for f in walls.values())
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


@pytest.mark.parametrize("tag, said", [
    # 25" strips since 2026-11-05: each grew 5" inboard; the N/S/W outboard face held.
    ("FT-B-N1", '9.03" / 7.97"'),   # 8.03" outboard until the 1/16" trim (C3-E18)
    ("FT-B-E1", '8.03" / 6.97"'),   # 7.03" / 5.97" on the 12" pour, until W-B-E1 went 10"
    ("FT-B-S2", '15.00" / 4.00"'),  # the 6" curb's 15" toe on a 15" strip
])
def test_the_trimmed_strips_hold_r403_1_1_projection(catlin_findings, tag, said) -> None:
    finding = catlin_findings[tag]
    assert finding.result is Result.PASS, finding.message
    assert said in finding.message


def test_reinforced_and_stone_footings_are_not_graded_for_projection(catlin_findings) -> None:
    # FT-SG-* are designed in flexure (rebar sets); FT-GF-* are R403.5 crushed stone.
    assert not any(k.startswith(("FT-SG-", "FT-GF-")) for k in catlin_findings)
