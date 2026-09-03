"""``structural.concrete_interference`` — the pour nothing else was grading.

Three things this pins, in the order they matter:

1. **The breezeway's four pads stand clear.** They did not until 2026-09-03: with the posts
   on the frame line, ``PD-BW-1/2`` sat 6 1/16" inside the house basement wall's band and
   ``PD-BW-3/4`` 8 3/8" inside the garage ICF stem's, invisible to every rule in the repo.
   ``test_a_pad_moved_back_onto_the_frame_line_is_caught`` re-creates that geometry and
   asserts the check finds it, so the guard is proved rather than assumed.
2. **The scope is isolated pours only.** Continuous foundation work laps at every corner by
   design; the check must stay silent about strip footings, foundation walls and the
   basement slab, and it is silent about them here.
3. **It reports.** A check that returns nothing has graded nothing.
"""

from __future__ import annotations

from _helpers import CATLIN as CATLIN_DIR

from typehaus.checks import build_context
from typehaus.checks.structural.concrete_interference import concrete_interference
from typehaus.findings import Result
from typehaus.model.structure import Pad
from typehaus.quantities import ft, pt
from typehaus.source import load_plan


def _findings(ctx):
    return concrete_interference(ctx)


def test_the_breezeway_pads_stand_clear_of_both_buildings():
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    fails = [f for f in _findings(ctx) if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]


def test_it_reports_the_pours_it_cleared_by_name():
    """A silent PASS is indistinguishable from a check that never ran."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    passes = [f for f in _findings(ctx) if f.result is Result.PASS]
    assert len(passes) == 1
    assert set(passes[0].element_tags) == {"PD-BW-1", "PD-BW-2", "PD-BW-3", "PD-BW-4"}


def test_continuous_foundation_work_is_out_of_scope():
    """Strip footings lap at every corner and the basement slab crosses all of them.

    None of that may reach this check — it graded ~80 findings of correct construction
    before the scope was narrowed to isolated pours, which is worse than grading none.
    """
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    named = {t for f in _findings(ctx) for t in f.element_tags}
    assert not {t for t in named if t.startswith(("FT-", "W-", "SL-"))}


def test_a_pad_moved_back_onto_the_frame_line_is_caught():
    """The 2026-09-02 geometry, re-created: PD-BW-1 back on the south frame line.

    ``_FRAME_Y0`` is 36.8333' and the house basement wall's outboard XPS face is at
    36.3375', so a 2'-0" pad centred there reaches 6 1/16" into it — and the pad's full 12"
    of thickness is inside the wall's own band, which spans -9.12' to -1.12'.
    """
    result = load_plan(CATLIN_DIR)
    plan = result.plan
    old = plan.by_tag("PD-BW-1")
    assert isinstance(old, Pad), old
    x = sum(p.xy_m[0] for p in old.outline) / len(old.outline) / ft(1).meters
    y = 36.833333
    moved = old.model_copy(update={"outline": (
        pt(ft(x - 1.0), ft(y - 1.0)), pt(ft(x + 1.0), ft(y - 1.0)),
        pt(ft(x + 1.0), ft(y + 1.0)), pt(ft(x - 1.0), ft(y + 1.0)))})
    storey = next(tag for tag, group in plan.elements.items()
                  if any(el is old for el in group))
    plan = plan.model_copy(update={"elements": {
        **plan.elements,
        storey: tuple(moved if el is old else el for el in plan.elements[storey]),
    }})

    ctx, _ = build_context(plan, CATLIN_DIR)
    fails = [f for f in _findings(ctx) if f.result is Result.FAIL]
    assert fails, "a pad buried in the house foundation wall must not pass"
    assert all("PD-BW-1" in f.element_tags for f in fails)
