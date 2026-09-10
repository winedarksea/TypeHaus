"""`structural.rake_overhang_backspan` — the rule that would have caught the 6'-0" rake.

The defect it exists for: `RF-GARAGE` carried `edge_overhangs=(("south", ft(6)),)` on a roof
whose ridge runs north-south, so "south" was a RAKE. `resolve/framing/roof_gable.py` framed
it as ladder framing — 2x4 outlookers at 24" o.c. cantilevering 88 inches off a 24-inch
backspan on a 2x6 barge rafter, with no truss over the passage at all — and every check in
the tree reported clean, because the only mention of an outlooker anywhere was an
interference *exclusion*.
"""

import pytest

from typehaus.checks.structural.rake_overhang import (
    MAX_OUTLOOKER_CANTILEVER_RATIO,
    rake_overhang_backspan,
)
from typehaus.findings import Result

_M_PER_FT = 0.3048


def _run(ctx):
    fn = getattr(rake_overhang_backspan, "__wrapped__", rake_overhang_backspan)
    return fn(ctx)


def test_the_retired_six_foot_rake_would_have_failed_this_rule():
    """The arithmetic, on the numbers the defect actually resolved.

    Pinned separately from the model so that fixing the house cannot quietly retire the
    rule: catlin has no cantilever left to exercise the FAIL branch, and a threshold nothing
    tests is a threshold that can be loosened by accident.
    """
    backspan_ft = 2.0            # one truss bay at the garage's 24" o.c.
    overhang_ft = 88.0 / 12.0    # the 6'-0" rake plus the 16" it already had
    assert overhang_ft / backspan_ft == pytest.approx(3.67, abs=0.01)
    assert overhang_ft > backspan_ft * MAX_OUTLOOKER_CANTILEVER_RATIO
    # About four times past anything a supplier will seal, which is the point: the rule is
    # deliberately the LOOSER of the two figures in circulation and this still clears it.
    assert overhang_ft / backspan_ft > 3.0


def test_only_the_one_real_rake_is_left_to_grade(catlin_ctx_for_rake):
    """RF-GARAGE's NORTH gable, and nothing else in the house.

    Two rakes retired on 2026-09-10 when ``_FLUSH_RAKE_TOLERANCE_M`` went from 1/2" to 6".
    The garage's SOUTH gable was framing 15 lookouts and a barge rafter to carry a 1 9/16"
    trim projection at a line where the roof does not even end — RF-BW-CANOPY runs on from
    it — and the canopy's own south end was framing 15 more for a 3 3/8" drip edge. Neither
    is built with a ladder; both are close rakes, sheathing cantilevered and a fascia hung on
    it. So RF-BW-CANOPY has no ladder framing at all now and drops out of this report.
    """
    findings = _run(catlin_ctx_for_rake)
    assert {f.result for f in findings} == {Result.PASS}
    by_roof = {f.element_tags[0]: f for f in findings}
    assert set(by_roof) == {"RF-GARAGE"}
    for finding in findings:
        assert "one truss bay" in finding.message
        # The rule reports a ratio against a resolved backspan, never a typed length.
        assert "2.00' backspan" in finding.message


def test_the_rule_reads_the_truss_bay_and_not_the_members_own_length(catlin_ctx_for_rake):
    """The trap this rule fell into once, pinned so it cannot come back.

    `roof_gable._outlookers` builds each member from the first interior truss all the way to
    the barge rafter, so its plan length AND its `length_m` are backspan PLUS overhang.
    Subtracting one from the other gives zero, the member is skipped, and the check reports
    nothing at all — which is exactly how it behaved when first written.
    """
    outlookers = [m for roof in catlin_ctx_for_rake.model.roofs
                  for m in roof.members if m.category == "outlooker"]
    assert {m.parent_uid for m in outlookers} == {
        next(r.uid for r in catlin_ctx_for_rake.model.roofs if r.tag == "RF-GARAGE")}
    assert outlookers, "no ladder framing resolved, so this test proves nothing"
    for member in outlookers:
        plan_length = ((member.p1[0] - member.p0[0]) ** 2
                       + (member.p1[1] - member.p0[1]) ** 2) ** 0.5
        assert plan_length == pytest.approx(member.length_m, abs=1e-6)
    # And the rule still produced findings despite that, which is the whole point.
    assert _run(catlin_ctx_for_rake)


def test_a_roof_with_no_ladder_framing_is_not_applicable_not_silent():
    """N/A must be EARNED — a rule that returns `[]` reports nothing and grades nothing."""

    class _Roof:
        tag = "RF-FLAT"
        assembly = "ANY"
        members = ()

    class _Library:
        def resolve_assembly(self, _tag):
            return None

    class _Plan:
        library = _Library()

    class _Model:
        plan = _Plan()
        roofs = (_Roof(),)

    class _Ctx:
        model = _Model()

    findings = _run(_Ctx())
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE
    assert "flush" in findings[0].message


@pytest.fixture(scope="module")
def catlin_ctx_for_rake(catlin_plan):
    from pathlib import Path

    from _helpers import CATLIN
    from typehaus.checks.run import build_context

    assert Path(CATLIN).exists()
    ctx, _ = build_context(catlin_plan, CATLIN)
    return ctx
