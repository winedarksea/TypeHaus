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
    """The rules are named for what they grade — ``..._sealed_deck_present``,
    ``..._drip_edge_present`` — so a PASS claims presence and nothing more ("presence"
    must not be read as "FORTIFIED compliance"), and every message still names what it
    did not grade.

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
                assert ("presence only" in finding.message
                        or "flange length graded" in finding.message)
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
    """Eaves (W/E) and rakes (N/S) both need one — §4.5 wants both."""
    house = [f for f in drip_edge if f.element_tags[:1] == ("RF-HOUSE",)]
    assert len(house) == 4
    assert all(f.result is Result.PASS for f in house)
    eave_msgs = [f.message for f in house if "eave edge" in f.message]
    rake_msgs = [f.message for f in house if "rake edge" in f.message]
    assert len(eave_msgs) == 2, "the west/east eaves"
    assert len(rake_msgs) == 2, "the north/south rakes"


def _with_house_drip(ctx, keep):
    """``ctx`` with RF-HOUSE's derived drip-edge members filtered/edited by ``keep``."""
    import dataclasses

    roofs = [dataclasses.replace(roof, members=tuple(
        m for m in (keep(m) if m.category == "drip_edge" else m for m in roof.members)
        if m is not None)) if roof.tag == "RF-HOUSE" else roof for roof in ctx.model.roofs]

    class _Model:
        def __getattr__(self, name):
            return roofs if name == "roofs" else getattr(ctx.model, name)

    stripped = type(ctx)(plan=ctx.plan, model=_Model(), preferences=ctx.preferences,
                         profile=ctx.profile, resolve_findings=ctx.resolve_findings)
    return [f for f in fortified_roof_drip_edge(stripped)
            if f.element_tags[:1] == ("RF-HOUSE",)]


def test_the_house_drip_edge_is_the_derived_formed_piece(drip_edge) -> None:
    """All four RF-HOUSE edges are credited to the one formed piece, graded on its flange."""
    house = [f for f in drip_edge if f.element_tags[:1] == ("RF-HOUSE",)]
    assert all('formed drip edge (derived), 2.00" on the deck' in f.message for f in house)


def test_removing_a_rake_drip_edge_fails_that_edge_only(ctx) -> None:
    """The branch must still bite: strip the south rake's derived piece (``rake-lo-*``; the
    ridge runs N-S, so the low rake is the south one) and exactly that edge FAILs."""
    house = _with_house_drip(
        ctx, lambda m: None if m.child_key.startswith("rake-lo-") else m)
    broken = [f for f in house if f.result is Result.FAIL]
    assert len(broken) == 1
    assert "S rake edge" in broken[0].message
    assert len([f for f in house if f.result is Result.PASS]) == 3


def test_a_short_flange_fails_on_geometry_not_presence(ctx) -> None:
    """A piece that is present but laps only 1" onto the deck is not §4.5's drip edge."""
    import dataclasses

    def shorten(m):
        if not (m.child_key.startswith("eave-hi-") and m.child_key.endswith("-flange")):
            return m
        ring = tuple((s * 0.5, t) for s, t in m.section_ring)
        return dataclasses.replace(m, section_ring=ring)

    house = _with_house_drip(ctx, shorten)
    broken = [f for f in house if f.result is Result.FAIL]
    assert len(broken) == 1
    assert "E eave edge" in broken[0].message and '1.00" on the deck' in broken[0].message


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
