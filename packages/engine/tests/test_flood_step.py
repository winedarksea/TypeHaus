"""The sunken garden's curb, graded instead of asserted.

``test_catlin_invariants.py`` pins the 7 1/4" flood threshold from the *door* side and from
above — R311.3.1 allows a non-required door one riser of step DOWN, and the curb spends all
but half an inch of it. Nothing bounded it from below: the curb could shrink, or the court
floor rise, and the only thing that would have noticed is a comment. ``Wall.min_threshold_
step`` states the premise the engine cannot derive (this court holds water) and
``building_science.flood_step_threshold`` grades the arithmetic that follows from it.

Both curbs are pinned, not just the one with a door in it: W-B-S2 carries the sauna and
W-B-S3 the gym, and a sauna's bottom plate drowns exactly as well.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.findings import Result

INCH = 0.0254
CURBS = ("W-B-S2", "W-B-S3")
COURT_FLOOR = "SL-SG-FLOOR"
FLOOD_STEP_IN = 7.25


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    from typehaus.checks import build_context

    context, _findings = build_context(catlin_plan)
    return context


def _set_wall_top(ctx, tag: str, z1_m: float):
    """Lower one resolved wall's top, through both the list and the tag index."""
    index = next(i for i, w in enumerate(ctx.model.walls) if w.tag == tag)
    original = ctx.model.walls[index]
    moved = dataclasses.replace(original, z1_m=z1_m)
    ctx.model.walls[index] = moved
    if ctx.model._tag_index:
        ctx.model._tag_index[tag] = moved
    return original


def _restore_wall(ctx, wall):
    index = next(i for i, w in enumerate(ctx.model.walls) if w.tag == wall.tag)
    ctx.model.walls[index] = wall
    if ctx.model._tag_index:
        ctx.model._tag_index[wall.tag] = wall


def test_both_garden_curbs_declare_the_flood_step(catlin_plan):
    """The premise is authored, and on BOTH walls — that is what makes the rule apply."""
    # ``element_kind`` is "FoundationWall" here — the field is on ``Wall``, which every
    # foundation wall is one of, so the census is by attribute rather than by class name.
    walls = {e.tag: e for e in catlin_plan.all_elements()
             if getattr(e, "min_threshold_step", None) is not None}
    for tag in CURBS:
        declared = walls[tag].min_threshold_step
        assert declared is not None, f"{tag} declares no flood step"
        assert declared.meters == pytest.approx(FLOOD_STEP_IN * INCH, abs=1e-9), tag


def test_the_curbs_stand_their_declared_step_over_the_court(ctx):
    """7 1/4" exactly — one 2x8 on edge — measured against the court floor, not the landing.

    The court is one plane flush with the basement slab since 2026-09-05, so this curb is
    the whole dam and the check names the surface it measured to.
    """
    from typehaus.checks.building_science.flood_step import flood_step_threshold

    findings = flood_step_threshold(ctx)
    by_tag = {tag: next(f for f in findings if f.message.startswith(tag)) for tag in CURBS}
    for tag in CURBS:
        finding = by_tag[tag]
        assert finding.result is Result.PASS, finding.message
        assert COURT_FLOOR in finding.message, finding.message
        assert f'{FLOOD_STEP_IN:.2f}" above' in finding.message, finding.message


def test_a_shortened_curb_fails(ctx):
    """The direction nothing bounded before: lower the curb and the dam is reported gone."""
    from typehaus.checks.building_science.flood_step import flood_step_threshold

    original = _set_wall_top(ctx, "W-B-S3", ctx.model.wall("W-B-S3").z1_m - 4 * INCH)
    try:
        finding = next(f for f in flood_step_threshold(ctx)
                       if f.message.startswith("W-B-S3"))
    finally:
        _restore_wall(ctx, original)
    assert finding.result is Result.FAIL, finding.message
    assert '3.25" above' in finding.message, finding.message
    # WARN severity, not ERROR: a house rule with no code article behind it reports as a
    # failure without bricking the permit gate, which keys off ERROR alone.
    assert finding.severity.value == "warn", finding.severity


def test_a_plan_that_declares_no_ponding_surface_is_not_applicable(starter_dir):
    """N/A is earned here: no wall states the premise, so the rule governs nothing.

    Not a PASS — a pass would be claiming the starter house has no court that ponds, which
    is a fact about its drainage nobody has stated.
    """
    from typehaus.checks import build_context
    from typehaus.checks.building_science.flood_step import flood_step_threshold
    from typehaus.source import load_plan

    plan = load_plan(starter_dir).plan
    context, _ = build_context(plan)
    findings = flood_step_threshold(context)
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE, findings[0].message
