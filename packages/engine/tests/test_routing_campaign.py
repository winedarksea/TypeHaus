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


# --- alternative conflict orders, and how they are ranked --------------------------------

def test_every_order_strategy_is_named_and_says_what_bet_it_makes() -> None:
    from typehaus.routing.campaign import ORDER_STRATEGIES

    assert [name for name, _why in ORDER_STRATEGIES] == [
        "declared", "biggest_first", "reversed_ties"]
    for name, why in ORDER_STRATEGIES:
        assert len(why) > 20, f"{name} is offered on no stated reason"


def test_the_declared_strategy_is_exactly_the_default_order() -> None:
    """A campaign asked for one alternative gets exactly what it gets today."""
    from typehaus.routing.campaign import _sort_key, reorder

    targets = [_target("PR-A", "drain", depth_m=-1.0), _target("PR-B", "drain", depth_m=-3.0),
               CampaignTarget(tag="DU-A", trade="duct", kind="duct", storey="main",
                              size_m=inch(8).meters)]
    assert reorder(targets, "declared") == sorted(targets, key=_sort_key)


def test_reversing_the_ties_reverses_only_the_ties_and_not_the_trades() -> None:
    """A drain still precedes a duct: the trade order is the design decision, not the tie."""
    from typehaus.routing.campaign import reorder

    shallow = _target("PR-SHALLOW", "drain", depth_m=-0.5)
    deep = _target("PR-DEEP", "drain", depth_m=-3.0)
    duct = CampaignTarget(tag="DU-A", trade="duct", kind="duct", storey="main",
                          size_m=inch(8).meters)
    order = [t.tag for t in reorder([deep, shallow, duct], "reversed_ties")]
    assert order == ["PR-SHALLOW", "PR-DEEP", "DU-A"]


def test_an_unknown_strategy_is_refused_with_the_list() -> None:
    from typehaus.routing.campaign import reorder

    with pytest.raises(ValueError, match="the strategies are"):
        reorder([], "cheapest")


def test_fewest_refusals_outranks_cheapest_always() -> None:
    """They are not two points on one scale.

    A campaign that serves every terminal at a higher price is not a worse answer than one
    that leaves two fixtures unconnected for less.
    """
    from typehaus.routing.campaign import CampaignResult, rank

    expensive = CampaignResult(settings={"order_strategy": "declared"})
    expensive.accepted = [_proposal("PR-A")]
    expensive.accepted[0].cost = 5000.0

    cheap = CampaignResult(settings={"order_strategy": "biggest_first"})
    cheap.accepted = [_proposal("PR-B")]
    cheap.accepted[0].cost = 10.0
    cheap.refused = [("PR-C", "no route")]

    assert [r.settings["order_strategy"] for r in rank([cheap, expensive])] == [
        "declared", "biggest_first"]


def test_cost_breaks_the_tie_between_two_that_serve_the_same_number() -> None:
    from typehaus.routing.campaign import CampaignResult, rank

    dear = CampaignResult(settings={"order_strategy": "declared"})
    dear.accepted = [_proposal("PR-A")]
    dear.accepted[0].cost = 900.0
    lean = CampaignResult(settings={"order_strategy": "biggest_first"})
    lean.accepted = [_proposal("PR-B")]
    lean.accepted[0].cost = 100.0
    assert rank([dear, lean])[0] is lean


def test_the_result_records_which_ordering_produced_it() -> None:
    """A ranked set of results is unreadable if they cannot say which is which."""
    result = run_campaign([_target("PR-A", "drain")],
                          lambda t, o: Outcome(proposal=_proposal(t.tag)),
                          inflate_m=0.0127, strategy="biggest_first")
    assert result.settings["order_strategy"] == "biggest_first"


def test_the_supply_slot_in_trade_order_is_no_longer_decorative() -> None:
    """`TRADE_ORDER` has always named supply fourth and a supply target has never been
    layable: `_pipe_run_endpoints` sent every one of them to `_vent_siblings`, which asks
    an endpoint question about a tee that sits on a segment. `haus route --house --trades
    supply` refused 16 of 20 targets; it now lays 21 of 29.

    Driven through the CLI rather than `run_campaign`, because the campaign runs no search
    of its own — what was broken was the ENDPOINTS, which is the parameter."""
    import pathlib

    from typer.testing import CliRunner

    from typehaus.cli.app import app

    catlin = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = CliRunner().invoke(
        app, ["route", str(catlin), "--house", "--trades", "supply"])
    # Exit 1: six runs are still honestly parentless, which is the campaign reporting a
    # fact about the model rather than failing.
    assert result.exit_code in (0, 1), result.output
    printed = " ".join(result.output.split())
    assert "of 29 targets laid" in printed
    laid = int(printed.split(" of 29 targets laid")[0].split()[-1])
    assert laid >= 20, printed
    # And the refusals that remain say which cause applies, not a sentence about a chase.
    assert "chase" not in printed
