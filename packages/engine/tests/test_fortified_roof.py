"""The FORTIFIED Roof checklist checks (checks/structural/fortified_roof.py).

Three sub-checks, each advisory (`[advisory, not engineering]`, never a hard block) and
each scoped to the conditioned envelope — the garage's unconditioned roof is not part of
what a FORTIFIED Roof designation on the house covers, and must never be graded.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.registry import Tier, registered
from typehaus.checks.structural.fortified_roof import (
    fortified_roof_drip_edge,
    fortified_roof_load_path,
    fortified_roof_sealed_deck,
)
from typehaus.findings import Result


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    return check_context(catlin_plan, profile=None)


@pytest.fixture(scope="module")
def sealed_deck(ctx):
    return fortified_roof_sealed_deck(ctx)


@pytest.fixture(scope="module")
def drip_edge(ctx):
    return fortified_roof_drip_edge(ctx)


@pytest.fixture(scope="module")
def load_path(ctx):
    return fortified_roof_load_path(ctx)


def test_all_three_checks_are_registered_in_the_structural_tier() -> None:
    ids = {cid for cid, _ in registered(Tier.STRUCTURAL)}
    assert "structural.fortified_roof_sealed_deck_present" in ids
    assert "structural.fortified_roof_drip_edge_present" in ids
    assert "structural.fortified_roof_load_path" in ids


def test_every_finding_is_advisory_and_says_what_it_did_not_grade(
        sealed_deck, drip_edge, load_path) -> None:
    """Inverted on 2026-08-30 with ``structural.uplift_path_coverage``, and for its reason.

    These asserted that nothing here is ever a PASS, so that "presence" could not be read as
    "FORTIFIED compliance". The rules are now named for what they grade —
    ``..._sealed_deck_present``, ``..._drip_edge_present`` — so a PASS claims presence and
    nothing more, and every message still names what it did not grade.

    Deliberately NOT hoisted into the engineering register, unlike the uplift capacity
    question: what is outstanding here is a gauge, an ASTM/ICC listing and a fastening
    schedule. Those are submittal documents, and a professional seal is the wrong instrument
    to track them with.
    """
    for findings in (sealed_deck, drip_edge, load_path):
        assert findings
        assert all("[advisory, not engineering]" in f.message for f in findings)
    for findings in (sealed_deck, drip_edge):
        for finding in findings:
            if finding.result is Result.PASS:
                assert "presence only" in finding.message
                assert "documentation facts this model does not carry" in finding.message


def test_catlin_reports_no_fail_across_all_three(sealed_deck, drip_edge, load_path) -> None:
    """The gate. ``scripts/verify.sh`` holds catlin to 0 FAIL across every check."""
    for findings in (sealed_deck, drip_edge, load_path):
        broken = [f.message for f in findings if f.result is Result.FAIL]
        assert not broken, broken


def test_the_garage_roof_is_out_of_scope(sealed_deck, drip_edge) -> None:
    """RF-GARAGE is a detached, unconditioned structure — not what a FORTIFIED Roof
    designation on the house covers, and grading it would fail a structure nobody is
    submitting for certification."""
    for findings in (sealed_deck, drip_edge):
        assert not [f for f in findings if f.element_tags[:1] == ("RF-GARAGE",)]


def test_the_house_roof_deck_is_sealed(sealed_deck) -> None:
    finding = next(f for f in sealed_deck if f.element_tags[:1] == ("RF-HOUSE",))
    assert finding.result is Result.PASS
    assert "carries a sealed underlayment layer" in finding.message
    assert "presence only" in finding.message


def test_the_house_roof_has_a_drip_edge_on_every_footprint_edge(drip_edge) -> None:
    """Eaves (W/E) and rakes (N/S) both need one — §4.5 wants both, and the rakes were the
    gap this closed (2026-08-30): they used to carry only the derived corner-trim angle."""
    house = [f for f in drip_edge if f.element_tags[:1] == ("RF-HOUSE",)]
    assert len(house) == 4
    assert all(f.result is Result.PASS for f in house)
    eave_msgs = [f.message for f in house if "eave edge" in f.message]
    rake_msgs = [f.message for f in house if "rake edge" in f.message]
    assert len(eave_msgs) == 2, "the west/east eaves"
    assert len(rake_msgs) == 2, "the north/south rakes"


def test_removing_a_rake_flashing_fails_that_edge_only(ctx) -> None:
    """The branch must still bite. Strip catlin's south rake flashing back off and the
    check reports exactly that edge broken, not the whole roof.

    The south rake is two short corner returns (params/roof_trim.py::_rake_corner_drips,
    ``TR-RF-DRIP-S`` at the west corner and ``TR-RF-DRIP-S-E`` at the east), so both have to
    go — leaving either one behind still covers the S side, which is the point of authoring
    two of them."""
    from typehaus.model.trim import Flashing

    by_tag = {e.tag: e for e in ctx.plan.all_elements()}
    del by_tag["TR-RF-DRIP-S"]
    del by_tag["TR-RF-DRIP-S-E"]

    class _Plan:
        def __init__(self, real):
            self._real = real

        def all_elements(self):
            return list(by_tag.values())

        def __getattr__(self, name):
            return getattr(self._real, name)

    stripped_ctx = type(ctx)(plan=_Plan(ctx.plan), model=ctx.model,
                             preferences=ctx.preferences, profile=ctx.profile,
                             resolve_findings=ctx.resolve_findings)
    findings = fortified_roof_drip_edge(stripped_ctx)
    house = [f for f in findings if f.element_tags[:1] == ("RF-HOUSE",)]
    broken = [f for f in house if f.result is Result.FAIL]
    assert len(broken) == 1
    assert "S rake edge" in broken[0].message
    still_ok = [f for f in house if f.result is Result.PASS]
    assert len(still_ok) == 3
    assert Flashing  # imported for readability of the fixture setup above


def test_the_load_path_check_re_presents_uplift_paths_roof_findings(load_path) -> None:
    """A thin re-labeling wrapper, not a re-derivation: every finding must reference a roof
    tag and carry the FORTIFIED framing on top of ``uplift_path``'s own message."""
    tags = {f.element_tags[0] for f in load_path}
    assert {"RF-HOUSE", "RF-GARAGE"} <= tags
    assert all("FORTIFIED roof-to-wall/foundation continuous load path" in f.message
               for f in load_path)


def test_the_load_path_check_carries_no_wall_or_floor_findings(load_path, ctx) -> None:
    """Filtering must be by roof tag, not by accident — a floor or wall link slipping
    through here would misrepresent the roof checklist's own scope."""
    roof_tags = {roof.tag for roof in ctx.model.roofs}
    assert all(f.element_tags[0] in roof_tags for f in load_path)
