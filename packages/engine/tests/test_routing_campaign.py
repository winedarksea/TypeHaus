"""Phase 6: many targets, one occupancy, a stated order, bounded rip-up.

The campaign runs no search of its own — ``propose`` is a parameter — so what is pinned here
is everything the campaign *does* decide: the order, the ledger, the rip-up policy and the
honesty of the report. The searches themselves are oracled in ``test_routing_oracle.py``.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.routing.campaign import (
    DEFAULT_RIP_UP_BUDGET,
    TRADE_ORDER,
    CampaignTarget,
    Outcome,
    proposal_prisms,
    run_campaign,
)
from typehaus.routing.proposal import RouteProposal


def _target(tag: str, trade: str, *, size_in: float = 3.0,
            depth_m: float | None = None) -> CampaignTarget:
    return CampaignTarget(tag=tag, trade=trade, kind="pipe", storey="basement",
                          size_m=inch(size_in).meters, depth_m=depth_m)


def _proposal(tag: str, *, x: float = 0.0) -> RouteProposal:
    return RouteProposal(tag=f"{tag}-PROPOSED", kind="pipe", system="drain",
                         diameter_m=inch(3).meters,
                         points=[(x, 0.0, 0.0), (x + 1.0, 0.0, 0.0)])


# --- the order ---------------------------------------------------------------------------

def test_the_order_is_declared_and_every_trade_says_why_it_sits_there() -> None:
    """An order with no reasons is a preference; with them it is a design decision."""
    assert [trade for trade, _why in TRADE_ORDER] == [
        "drain", "vent", "duct", "supply", "conduit"]
    for trade, why in TRADE_ORDER:
        assert len(why) > 20, f"{trade} sits in the order on no stated reason"


def test_the_cli_trade_list_and_the_campaigns_order_stay_in_step() -> None:
    """Two lists of the same five words is one place for them to drift."""
    from typehaus.cli.cmd_route import _CAMPAIGN_TRADES

    assert set(_CAMPAIGN_TRADES) == {trade for trade, _why in TRADE_ORDER}


def test_drains_go_deepest_first_and_ducts_biggest_first() -> None:
    """Least head slack first for a drain; fewest places to fit first for a duct.

    Route length is not a proxy for slack, which is the same reason ``tree.order_terminals``
    orders a Steiner tree's terminals this way.
    """
    from typehaus.routing.campaign import _sort_key

    shallow = _target("PR-SHALLOW", "drain", depth_m=-0.5)
    deep = _target("PR-DEEP", "drain", depth_m=-3.0)
    assert sorted([shallow, deep], key=_sort_key)[0] is deep

    small = CampaignTarget(tag="DU-S", trade="duct", kind="duct", storey="main",
                           size_m=inch(4).meters)
    big = CampaignTarget(tag="DU-B", trade="duct", kind="duct", storey="main",
                         size_m=inch(10).meters)
    assert sorted([small, big], key=_sort_key)[0] is big


def test_a_run_whose_system_names_no_trade_is_reported_rather_than_placed() -> None:
    """A campaign's order is its whole content, so an unassigned run is named, not guessed.

    ``order_targets`` gives it ``trade=""``; the CLI lists it as skipped. Dropping it
    silently would lose a run, and slotting it somewhere would decide on no evidence.
    """
    from typehaus.resolve.model import ResolvedModel, ResolvedPipeRun

    class _Plan:
        storeys = ()

        def storey_elements(self, _tag):
            return []

        def by_tag(self, _tag):
            return None

    from typehaus.routing.campaign import order_targets

    model = ResolvedModel(plan=_Plan())
    model.pipe_runs.append(ResolvedPipeRun(
        uid="PR-X", tag="PR-X", storey="basement", system="brine", path=[(0, 0), (1, 0)],
        diameter_m=inch(1).meters, z_start_m=0.0, z_end_m=0.0, length_m=1.0, z_m=(0.0, 0.0)))
    targets = order_targets(model)
    assert [(t.tag, t.trade) for t in targets] == [("PR-X", "")]


# --- the ledger --------------------------------------------------------------------------

def test_an_accepted_proposal_blocks_the_next_target() -> None:
    """The whole point of a campaign: the second search sees the first one's answer."""
    seen: list[int] = []

    def propose(target, occupancy):
        seen.append(len(occupancy))
        return Outcome(proposal=_proposal(target.tag))

    result = run_campaign([_target("PR-A", "drain"), _target("PR-B", "drain")],
                          propose, inflate_m=0.0127)
    assert seen == [0, 1], "the second target searched against an empty world"
    assert len(result.accepted) == 2
    assert result.termination == "all 2 targets laid with no rip-up"


def test_a_proposals_prisms_are_the_solid_it_will_occupy_once_pasted() -> None:
    """The same ``run_envelope`` reading the checks use — never a second, looser shape."""
    prisms = proposal_prisms(_proposal("PR-A"), inflate_m=0.0)
    assert len(prisms) == 1
    assert prisms[0].kind == "run"
    # 3" pipe, no clearance: the band is the radius either side of a level run.
    assert prisms[0].z1_m == pytest.approx(inch(1.5).meters)
    assert prisms[0].z0_m == pytest.approx(-inch(1.5).meters)


# --- rip-up ------------------------------------------------------------------------------

def test_a_blocked_target_lifts_the_most_recent_blocker_and_requeues_it() -> None:
    """Most recent, because lifting an early trunk for a late branch inverts the order."""
    attempts: list[str] = []

    def propose(target, occupancy):
        attempts.append(target.tag)
        if target.tag == "PR-B" and occupancy:
            return Outcome(reason="PR-A is in the way", blockers=("PR-A",))
        return Outcome(proposal=_proposal(target.tag))

    result = run_campaign([_target("PR-A", "drain"), _target("PR-B", "drain")],
                          propose, inflate_m=0.0127)
    assert result.lifts == [("PR-A", "PR-B")]
    assert attempts == ["PR-A", "PR-B", "PR-B", "PR-A"]
    assert {p.tag for p in result.accepted} == {"PR-B-PROPOSED", "PR-A-PROPOSED"}
    assert "after 1 rip-up" in result.termination


def test_nothing_the_campaign_did_not_lay_is_ever_lifted() -> None:
    """A blocker that is a fact about the building is a finding, not a scheduling problem."""
    def propose(target, occupancy):
        return Outcome(reason="a beam is in the way", blockers=("BM-MAIN",))

    result = run_campaign([_target("PR-A", "drain")], propose, inflate_m=0.0127)
    assert result.lifts == []
    assert result.refused == [("PR-A", "a beam is in the way")]
    assert result.termination == "0 of 1 targets laid; 1 refused"


def test_the_same_run_is_never_lifted_twice_in_one_campaign() -> None:
    """Two runs that each want the other's lane: lifting swaps them, forever.

    A lifts for B, B lifts for A, A lifts for B again — and the third time round the
    campaign stops trading them, because lifting the same run twice is a loop and not a
    search. The run that is dropped is REPORTED as skipped, so the deliverable says a lane
    was contested rather than quietly returning one of the two.
    """
    def propose(target, occupancy):
        if occupancy:
            other = "PR-B" if target.tag == "PR-A" else "PR-A"
            return Outcome(reason=f"{other} is in the way", blockers=(other,))
        return Outcome(proposal=_proposal(target.tag))

    result = run_campaign([_target("PR-A", "drain"), _target("PR-B", "drain")],
                          propose, inflate_m=0.0127)
    assert any("a loop rather than a search" in reason for _tag, reason in result.skipped)
    laid = [p.tag for p in result.accepted]
    assert len(laid) == len(set(laid)), "a run was laid twice"


def test_the_budget_is_a_count_and_a_spent_budget_refuses_with_the_reason() -> None:
    """A count rather than a clock, so the same campaign decides the same on any machine."""
    def propose(target, occupancy):
        if occupancy:
            return Outcome(reason="blocked", blockers=tuple(
                t.tag for t in targets if t.tag != target.tag))
        return Outcome(proposal=_proposal(target.tag))

    targets = [_target(f"PR-{i}", "drain") for i in range(6)]
    result = run_campaign(targets, propose, inflate_m=0.0127, rip_up_budget=1)
    assert len(result.lifts) == 1
    assert result.refused, "a spent budget must refuse rather than loop"
    assert result.settings["rip_up_budget"] == 1


def test_the_default_budget_is_stated_in_the_settings_it_reports() -> None:
    """Contract 3: every result records the effective settings it ran under."""
    result = run_campaign([], lambda t, o: Outcome(), inflate_m=0.0127)
    assert result.settings["rip_up_budget"] == DEFAULT_RIP_UP_BUDGET
    assert result.settings["trade_order"] == [trade for trade, _why in TRADE_ORDER]
    assert result.as_dict()["termination"] == "all 0 targets laid with no rip-up"
