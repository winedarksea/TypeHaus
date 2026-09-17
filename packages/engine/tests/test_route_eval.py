"""``--evaluate``: the candidate model, and the two ways it used to lie.

Both failures here were real. The first built a `Length` from raw metres and every
candidate refused to construct, so the evaluation reported "would not build" about every
proposal ever made. The second dropped the *fixture* from the candidate storey — the base
of a branch's tag is the fixture, not a run — and every check that reads the fixture then
reported UNKNOWN, which the evaluation blamed on the proposal.
"""

from __future__ import annotations

import pathlib

import pytest

from typehaus.cli.route_eval import (
    GRADED_PREFIXES,
    _candidate_plan,
    _replaced_tags,
    evaluate_proposals,
    render_reports,
)
from typehaus.routing.proposal import RouteProposal

pytestmark = pytest.mark.slow

_CATLIN = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _wc_branch() -> RouteProposal:
    """A 3" closet branch on the suite bath's own plan point, straight down to the tie."""
    return RouteProposal(
        tag="FX-S-SUITEBATH-WC-PROPOSED", kind="pipe",
        points=[(3.4258, 6.3658, 5.4864), (3.4258, 6.3658, 5.3943),
                (3.4258, 6.2484, 5.3911)],
        diameter_m=3 * 0.0254, serves=("FX-S-SUITEBATH-WC",), system="drain")


def test_the_candidate_keeps_the_fixture_the_branch_drains(catlin_model_ro) -> None:
    """The bug this is written against: `FX-S-SUITEBATH-WC-PROPOSED` has the FIXTURE as its
    base tag, and dropping it deleted the very thing the branch is for."""
    replaced = _replaced_tags(catlin_model_ro, _wc_branch())
    assert "FX-S-SUITEBATH-WC" not in replaced
    assert any(tag.startswith("PR-") for tag in replaced), replaced


def test_the_candidate_plan_builds_and_holds_the_proposed_run(catlin_model_ro) -> None:
    plan = _candidate_plan(catlin_model_ro, _wc_branch())
    tags = {getattr(e, "tag", None) for e in plan.all_elements()}
    assert "FX-S-SUITEBATH-WC-PROPOSED" in tags
    assert "FX-S-SUITEBATH-WC" in tags


def test_an_evaluation_reports_a_diff_and_not_the_house_s_own_report(catlin_model_ro) -> None:
    """Catlin is not clean in the MEP set and is not required to be. What matters about a
    proposal is what it CHANGES; a finding the house already carries is not its fault."""
    reports = evaluate_proposals(_CATLIN, catlin_model_ro, [_wc_branch()])
    assert len(reports) == 1
    assert reports[0].refused is None, reports[0].refused
    assert all(f.check_id.startswith(GRADED_PREFIXES) or f.severity.value == "error"
               for f in reports[0].introduced)
    lines = render_reports(reports)
    assert any("evaluation FX-S-SUITEBATH-WC-PROPOSED" in line for line in lines)


def test_a_duct_routed_exposed_says_the_occupancy_checks_have_nothing_to_grade(
        catlin_model_ro) -> None:
    """A gap reported as a gap. An absent finding reads as a pass."""
    duct = RouteProposal(tag="DU-S-HP-SUITE-PROPOSED", kind="duct",
                         points=[(5.8, 4.3, 2.5), (3.8, 4.3, 2.5)],
                         diameter_m=0.0, width_m=0.254, depth_m=0.2032,
                         system="supply", routing="exposed")
    reports = evaluate_proposals(_CATLIN, catlin_model_ro, [duct])
    assert any("EXPOSED" in note for note in reports[0].coverage), reports[0].coverage
