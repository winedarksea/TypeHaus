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
    """A silent PASS is indistinguishable from a check that never ran.

    ** THE HOUSE HAS ISOLATED POURS AGAIN SINCE 2026-09-14. ** This asserted ``not passes``
    for a while and the assertion was honest: every isolated pour catlin had went with the
    foundation bridge, so the rule's subject set was empty and the mutation below was the
    only thing exercising it. The north entry's three HOUSE-side piers became ``Pad``s that
    day — ``PD-BW-W``/``-E``/``-RE``, a Pad being the one thing this rule scopes
    unconditionally — and they stand clear of `FT-B-N1`..`-N4`, the basement's north strip
    footing on their own plane, by 1 1/16". The 18" north-south dimension is what buys that
    clearance and is the reason those pads are rectangles rather than the 24" squares their
    Footings drew.

    ** AND THE GARAGE-SIDE THREE ARE HERE TOO NOW, BY THE OTHER ROUTE. ** The docstring above
    used to close by saying they were absent: they lap the garage strip footing by ~7 1/2" on
    one plane, cannot be pulled clear, and so stayed ``Footing`` with an ``under``. They are
    ``Pad``s as of 2026-09-14, declaring ``cast_with`` — the lap is a real lap and the answer
    is that it is one POUR, not that it is no overlap. Each such declaration is its own PASS
    naming both sides, because a reader has to be able to see which footing each pad is
    monolithic with; the pours that simply stand clear stay aggregated into one line.

    So the count is two shapes of PASS, and the test asserts both rather than a total: a
    single aggregate for the clear-standing pours, and one per declared pour. ``PD-SG-COL``
    and ``PD-SG-FCOL`` joined the aggregate the same day, when the two centre-garden bells
    became pads.
    """
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    passes = [f for f in _findings(ctx) if f.result is Result.PASS]
    declared = [f for f in passes if "CAST WITH" in f.message]
    clear = [f for f in passes if f not in declared]

    assert len(clear) == 1, [f.message for f in clear]
    assert set(clear[0].element_tags) == {
        "PD-BW-W", "PD-BW-E", "PD-BW-RE", "PD-SG-COL", "PD-SG-FCOL"}

    # One per (pad, footing) lap, not one per pad: PD-BW-GW and PD-BW-RNE each cross two
    # legs of the garage strip, and a reader owed "which footing" is owed it for each.
    assert {tuple(sorted(f.element_tags)) for f in declared} == {
        ("FT-GF-S-DR", "PD-BW-GE"),
        ("FT-GF-S1", "PD-BW-GW"),
        ("FT-GF-W", "PD-BW-GW"),
        ("FT-GF-E", "PD-BW-RNE"),
        ("FT-GF-S3", "PD-BW-RNE"),
    }
    for finding in declared:
        # The grant is narrow and the message must keep saying so — a declared pour buys a
        # joint, never bearing area (ACI 318-19 §13.3.4's combined-footing line).
        assert "takes no credit" in finding.message


def test_continuous_foundation_work_is_never_the_SUBJECT_of_a_finding():
    """Strip footings lap at every corner and the basement slab crosses all of them.

    None of that may be GRADED here — the check produced ~80 findings about correct
    construction before its scope was narrowed to isolated pours, which is worse than
    producing none.

    ** THE ASSERTION MOVED FROM "never named" TO "never the subject" ON 2026-09-14 ** and the
    distinction is the whole point of ``cast_with``. A pad that declares it is cast with
    ``FT-GF-S1`` produces a finding that has to say *which* footing, or the reader cannot
    check the declaration against the drawing. So continuous work is named — as the
    counterparty of somebody else's declaration, never as a thing this rule grades. Going
    back to a blanket "no FT- may appear" would either delete that name from the message or
    stop the check scoping declared pours at all, and both are worse than the lap.
    """
    from typehaus.model.structure import Pad

    plan = load_plan(CATLIN_DIR).plan
    ctx, _ = build_context(plan, CATLIN_DIR)
    declared = {pad.tag: set(pad.cast_with or ()) for pad in plan.all_elements()
                if isinstance(pad, Pad)}

    for finding in _findings(ctx):
        tags = set(finding.element_tags)
        pads = {t for t in tags if t in declared}
        assert pads, f"a finding about no Pad at all: {sorted(tags)}"
        # Everything else it names must be something one of those pads declared.
        continuous = {t for t in tags - pads if t.startswith(("FT-", "W-", "SL-"))}
        allowed = set().union(*(declared[tag] for tag in pads))
        assert continuous <= allowed, (
            f"{sorted(continuous)} is graded here without being declared by "
            f"{sorted(pads)}: {finding.message}")


def test_a_pad_moved_back_onto_the_frame_line_is_caught():
    """The 2026-09-02 geometry, re-created: PD-BW-1 back on the south frame line.

    ``_FRAME_Y0`` is 36.8333' and the house basement wall's outboard XPS face is at
    36.3375', so a 2'-0" pad centred there reaches 6 1/16" into it — and the pad's full 12"
    of thickness is inside the wall's own band, which spans -9.12' to -1.12'.
    """
    result = load_plan(CATLIN_DIR)
    plan = result.plan
    old = Pad(uid="TESTPAD001", tag="PD-TEST", outline=(), thickness=ft(1),
              bottom_elevation=ft(-6), assembly="PIER_BASE_12")
    x = 7.0
    y = 36.833333
    moved = old.model_copy(update={"outline": (
        pt(ft(x - 1.0), ft(y - 1.0)), pt(ft(x + 1.0), ft(y - 1.0)),
        pt(ft(x + 1.0), ft(y + 1.0)), pt(ft(x - 1.0), ft(y + 1.0)))})
    plan = plan.model_copy(update={"elements": {
        **plan.elements, "main": (*plan.elements["main"], moved),
    }})

    ctx, _ = build_context(plan, CATLIN_DIR)
    fails = [f for f in _findings(ctx) if f.result is Result.FAIL]
    assert fails, "a pad buried in the house foundation wall must not pass"
    assert all("PD-TEST" in f.element_tags for f in fails)
