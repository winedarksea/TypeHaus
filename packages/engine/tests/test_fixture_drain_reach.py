"""``mep.fixture_drain_reach`` — a run naming a fixture in ``serves`` has to get near it.

``serves`` was an unchecked claim, and it is not decoration: it feeds
``accumulated_serves`` -> ``branch_load`` -> ``mep.pipe_sizing``. Nine catlin fixtures named
a drain run that never reached them, and the whole second-storey bathroom group had stacks
with no branch or trap-arm piping drawn at all — which is why the suite bath's water closet
read as undrained in the viewer.

**This check lands red on purpose.** Per the plan of record, checks go in as hard FAILs and
the fixes follow; the branches are the next commit. What these tests pin meanwhile is the
part that survives the fix: the vertical gate, the empty-``serves`` verdict, and the
threshold's basis.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == "mep.fixture_drain_reach"]


def test_the_check_is_actually_registered() -> None:
    """**The trap.** A check module missing from ``checks/mep/__init__.py``'s import list
    registers nothing and emits nothing, which is indistinguishable from finding nothing."""
    assert "mep.fixture_drain_reach" in {cid for cid, _ in registered(Tier.ADVISORY)}


def test_every_drained_fixture_is_graded(findings) -> None:
    """No UNKNOWNs: every drained fixture in this house resolves a drain point, so the
    check has an opinion about all of them. An UNKNOWN here would mean
    ``_expected_drain_point`` stopped deriving one, and ``mep.trap_arm_length`` would have
    gone quiet on the same fixture at the same moment."""
    assert findings
    assert not [f for f in findings if f.result is Result.UNKNOWN], \
        [f.message for f in findings if f.result is Result.UNKNOWN]


def test_the_distribution_is_bimodal_with_a_hole_at_the_threshold(findings) -> None:
    """Where the 12" comes from, asserted rather than asserted-in-a-docstring.

    Every PASS measures 8" or less; every FAIL measures 15" or more. The threshold sits in
    an empty band, so it is a reading of the house rather than a knob. If a future branch
    lands at 11" this test fails and the number needs re-deriving — which is the point."""
    import re

    def inches(finding):
        return float(re.search(r"(\d+\.\d)\"", finding.message).group(1))

    reached = [inches(f) for f in findings if f.result is Result.PASS]
    missed = [inches(f) for f in findings if f.result is Result.FAIL]
    assert reached and missed
    assert max(reached) <= 8.0, sorted(reached)
    assert min(missed) >= 15.0, sorted(missed)


def test_a_fixture_no_run_names_fails_rather_than_unknowns(catlin_model) -> None:
    """Positive evidence of absence. The model can see perfectly well that nothing names
    this fixture; a fixture standing over no drain is a defect, not a gap in what is
    knowable. ``Result.NOT_APPLICABLE`` and ``UNKNOWN`` would both be a lie here."""
    stripped = tuple(
        dataclasses.replace(run, serves=tuple(t for t in run.serves
                                              if t != "FX-B-BATH-WC"))
        for run in catlin_model.pipe_runs)
    model = dataclasses.replace(catlin_model, pipe_runs=stripped)
    findings = [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
                if f.check_id == "mep.fixture_drain_reach"
                and "FX-B-BATH-WC" in f.element_tags]
    assert [f.result for f in findings] == [Result.FAIL]
    assert "nothing drains it" in findings[0].message


def test_the_vertical_gate_stops_a_pipe_on_another_floor_reaching_up(catlin_model) -> None:
    """Distance is measured in plan, so without the gate any pipe passing beneath a fixture
    "reaches" it through the deck.

    ``FX-M-KITCH-SINK`` drops into the basement ceiling, where ``PR-B-KITCH-DRAIN``'s head
    is waiting 0.0" away — that is what the band's two feet of reach *downward* is for, and
    is why the gate cannot simply be "same storey". ``PR-B-MAIN-DRAIN`` names the sink too,
    so it is stripped first: this test is about one run's elevation, not about which of two
    runs is nearer. Drop the remaining one six feet and the plan geometry is untouched while
    every vertex is now a storey away, so the run stops counting at all."""
    def restated(run):
        if run.tag == "PR-B-KITCH-DRAIN":
            return dataclasses.replace(
                run, z_m=tuple(z - 6.0 / 3.280839895013123 for z in run.z_m))
        return dataclasses.replace(
            run, serves=tuple(t for t in run.serves if t != "FX-M-KITCH-SINK"))

    model = dataclasses.replace(
        catlin_model, pipe_runs=tuple(restated(r) for r in catlin_model.pipe_runs))
    findings = [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
                if f.check_id == "mep.fixture_drain_reach"
                and "FX-M-KITCH-SINK" in f.element_tags]
    assert [f.result for f in findings] == [Result.FAIL]
    assert "on this fixture's floor at all" in findings[0].message
