"""The uplift load-path check (checks/structural/uplift_path.py).

The check's job is to be loud about a joint with no hardware, and its risk is being loud
about a joint that HAS hardware in a form it did not think to look for. Every false positive
it shipped with was of that kind, and each has a test here:

* a joist framed flush into its beam is connected by a **hanger**, not a tie;
* a cast column on a cast footing is connected by **reinforcement**, which this model does
  not carry, so the joint is not gradeable rather than broken;
* a beam bearing on a concrete column is connected by an authored **hurricane tie**, not
  only by the strap the derived rule would use;
* a post that never declares what it stands on is a **modelling gap**, not a break.

Those are why catlin reports 0 FAIL under this check, and why that number is worth pinning:
the reference house is held to a clean report by ``scripts/verify.sh``, so a regression in
any of the four takes the whole gate down with it.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.registry import Tier, registered
from typehaus.checks.structural.uplift_path import uplift_load_path
from typehaus.findings import Result


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    return check_context(catlin_plan, profile=None)


@pytest.fixture(scope="module")
def findings(ctx):
    return uplift_load_path(ctx)


def test_the_check_is_registered_in_the_structural_tier() -> None:
    assert "structural.uplift_load_path" in {cid for cid, _ in registered(Tier.STRUCTURAL)}


def test_catlin_reports_no_break_in_the_load_path(findings) -> None:
    """The gate. ``scripts/verify.sh`` holds catlin to 0 FAIL across every check."""
    broken = [f.message for f in findings if f.result is Result.FAIL]
    assert not broken, broken


def test_no_link_is_ever_reported_as_a_pass(findings) -> None:
    """Coverage is not capacity, and this model carries no design wind speed.

    Same contract as ``cantilever.py``'s mitigated case: hardware being present is a
    different claim from the joint being adequate, and a PASS would retire a question that
    still needs an engineer. Every finding is therefore UNKNOWN or FAIL, never PASS.
    """
    assert findings
    assert not [f for f in findings if f.result is Result.PASS]
    assert all("[advisory, not engineering]" in f.message for f in findings)


def test_both_roofs_are_covered_at_their_bearings(findings) -> None:
    covered = {f.element_tags[0]: f for f in findings if f.result is Result.UNKNOWN}
    for roof in ("RF-HOUSE", "RF-GARAGE"):
        assert "derived uplift ties" in covered[roof].message, roof


def test_a_flush_framed_deck_is_covered_by_its_hangers(findings) -> None:
    """FS-BW-FLOOR's four 2x8 joists sit IN their beams, so no tie can be derived for them.

    Before hangers counted, this floor was the check's loudest false positive: every one of
    its joist ends carries a LUS hanger and the report called it a break in the load path.
    """
    deck = next(f for f in findings if f.element_tags[:1] == ("FS-BW-FLOOR",))
    assert deck.result is Result.UNKNOWN
    assert "hangers" in deck.message


def test_a_cast_column_is_not_evaluable_rather_than_broken(findings) -> None:
    """A concrete column on a concrete footing is doweled; there is no connector to miss.

    Grading it against a wood post base reported a break at a joint that has none — and
    handed the reader an ABU that does not fit a 12" round pour.
    """
    for column in ("PT-SG-COL", "PT-SG-FCOL"):
        finding = next(f for f in findings
                       if f.element_tags[:1] == (column,) and "cannot be graded" in f.message)
        assert finding.result is Result.UNKNOWN
        assert "reinforcement" in finding.message


def test_a_post_with_no_declared_bearing_is_not_evaluable(findings) -> None:
    """The three stairwell posts declare no ``supported_by``: a gap, not a missing connector.

    Keeping these out of the FAIL column is what the tri-state is for (#32). Reporting a
    thing the model never said as a thing the model got wrong would exit ``haus check`` 1
    over an omission.
    """
    for post in ("P-M-STRWELL-S", "P-M-STRWELL-N", "P-M-STRLAND-SE"):
        finding = next(f for f in findings if f.element_tags[:1] == (post,))
        assert finding.result is Result.UNKNOWN
        assert "declares no `supported_by`" in finding.message


def test_an_authored_hurricane_tie_connects_a_beam_to_its_column(findings) -> None:
    """``CN-SG-TIE-COL`` / ``CN-SG-TIE-FCOL`` are the uplift connection at the two columns.

    They are HURRICANE_TIE, not HOLD_DOWN. A check that only recognised straps and caps
    reported all four of these beam ends as breaks while the plan had already modelled them.
    """
    for beam, column in (("BM-SG-BKW", "PT-SG-COL"), ("BM-SG-BKE", "PT-SG-COL"),
                         ("BM-SG-FRW", "PT-SG-FCOL"), ("BM-SG-FRE", "PT-SG-FCOL")):
        finding = next(f for f in findings if f.element_tags == (beam, column))
        assert finding.result is Result.UNKNOWN
        assert "an authored strap or cap" in finding.message


def test_an_authored_strap_is_not_credited_to_a_neighbouring_beam(findings) -> None:
    """The breezeway straps its two ROOF beams to PT-BW-1..4; the FLOOR beams are separate.

    Matching an authored connector on either tag alone handed ``CN-BW-KBS-*`` to
    ``BM-BW-FW``/``FE``, which land on the same four posts and carry none of those straps.
    That is why the guard keys on the tag PAIR, and why the four floor-beam joints must read
    as *derived* rather than authored.
    """
    for beam in ("BM-BW-RW", "BM-BW-RE"):
        roof = [f for f in findings if f.element_tags[:1] == (beam,)]
        assert roof and all("an authored strap or cap" in f.message for f in roof)
    for beam in ("BM-BW-FW", "BM-BW-FE"):
        floor = [f for f in findings if f.element_tags[:1] == (beam,)]
        assert floor and all("a derived KBS1Z strap" in f.message for f in floor)


def test_the_sill_and_the_stacked_walls_are_both_reported(findings) -> None:
    """Links 3 and 4 — the two joints between a wall and whatever is under it."""
    messages = [f.message for f in findings]
    assert any("MASA mudsill anchors" in m for m in messages)
    assert any("CS16 strapping" in m for m in messages)


def test_a_broken_joint_really_does_fail(ctx) -> None:
    """The check must still bite. Strip catlin's roof of its bearing declaration and it does.

    Without this, every assertion above is satisfied by a check that returns UNKNOWN for
    everything, and the file would pass while grading nothing.
    """
    roof = next(e for e in ctx.plan.all_elements() if e.tag == "RF-HOUSE")
    stripped = roof.model_copy(update={"bearing_refs": ()})
    by_tag = {e.tag: e for e in ctx.plan.all_elements()}
    by_tag["RF-HOUSE"] = stripped

    class _Plan:
        """The real plan, with ``all_elements`` swapped. Everything else delegates.

        A hand-rolled stand-in is not enough here: ``_is_concrete`` reaches through the plan
        to the assembly library to tell a cast column from a wood post, and a stub without
        one made the check raise instead of grading.
        """

        def __init__(self, real):
            self._real = real

        def all_elements(self):
            return list(by_tag.values())

        def __getattr__(self, name):
            return getattr(self._real, name)

    broken_ctx = type(ctx)(plan=_Plan(ctx.plan), model=ctx.model,
                           preferences=ctx.preferences, profile=ctx.profile,
                           resolve_findings=ctx.resolve_findings)
    failed = [f for f in uplift_load_path(broken_ctx) if f.result is Result.FAIL]
    assert [f for f in failed if "RF-HOUSE" in f.element_tags], \
        "a roof that declares no bearing has no derivable tie and must FAIL"
