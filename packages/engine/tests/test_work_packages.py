"""Work packages: stable ids, honest allocation, and an order somebody authored.

There is no phase, stage or sequence concept in the model, and ``emit/trades.TRADES`` is a
3D-viewer visibility axis with no ordering at all. Three properties carry the whole design:

1. **Ids are stable.** ``derive_guid(project_uuid, "task/{trade}/{storey}")`` survives a
   rebuild and a retagging, so re-exporting updates the same task instead of creating a
   second one — the failure that makes every other PM export unusable on the second run.
2. **No money is invented and none is lost.** A BOM row lands on a storey only when every
   element it covers is on that storey; everything else goes to the trade's building-wide
   package. The item estimates therefore sum to exactly the estimate total.
3. **Nothing is derived that the model cannot know.** No durations, no crew sizes, no dates.
"""

from __future__ import annotations

import pytest

from typehaus.cli.prices import estimate_costs, load_prices
from typehaus.emit.trades import CONSTRUCTION_SEQUENCE, TRADE_PREDECESSORS, TRADES
from typehaus.takeoff import bill_of_materials
from typehaus.takeoff.tasks import BUILDING, build_work_items

from _helpers import CATLIN


@pytest.fixture(scope="module")
def packages(catlin_model):
    bom = bill_of_materials(catlin_model)
    estimate = estimate_costs(bom, load_prices(CATLIN))
    return build_work_items(catlin_model, bom, estimate), estimate


# --- the sequence table --------------------------------------------------------------------

def test_the_sequence_covers_every_trade_exactly_once() -> None:
    assert set(CONSTRUCTION_SEQUENCE) == TRADES
    assert len(CONSTRUCTION_SEQUENCE) == len(TRADES)


def test_no_trade_depends_on_one_that_comes_after_it() -> None:
    """The guard that stops the predecessor map and the linear order from disagreeing —
    a cycle here is a schedule that cannot start."""
    rank = {trade: i for i, trade in enumerate(CONSTRUCTION_SEQUENCE)}
    for trade, predecessors in TRADE_PREDECESSORS.items():
        assert all(rank[p] < rank[trade] for p in predecessors), trade


def test_the_three_rough_ins_run_in_parallel() -> None:
    """Plumbing, electrical and mechanical share the open-wall window. A schedule that
    serializes them is one no builder will use, so none may depend on another."""
    for trade in ("plumbing", "electrical", "mechanical"):
        others = {"plumbing", "electrical", "mechanical"} - {trade}
        assert not others & set(TRADE_PREDECESSORS[trade])


# --- stable ids ----------------------------------------------------------------------------

def test_ids_are_byte_identical_across_a_rebuild(catlin_model, catlin_plan) -> None:
    """The property the whole export depends on. Re-resolving the same plan must not mint
    new ids, or a second export duplicates every task in the receiving tool."""
    from typehaus.resolve import resolve

    first = build_work_items(catlin_model, bill_of_materials(catlin_model))
    rebuilt, _ = resolve(catlin_plan)
    second = build_work_items(rebuilt, bill_of_materials(rebuilt))
    assert [item.id for item in first] == [item.id for item in second]
    assert [item.slug for item in first] == [item.slug for item in second]


def test_the_id_is_the_derived_guid_of_a_human_readable_slug(packages, catlin_plan) -> None:
    """The slug stays readable because it is the half a receiving tool can key on when it
    has no GUID field — and, per the plan, what a later syllepsis ``NoteId`` would carry."""
    from typehaus.model.ids import derive_guid

    items, _ = packages
    project_uuid = catlin_plan.project.project_uuid
    for item in items:
        assert item.slug == f"task/{item.trade}/{item.storey}"
        assert item.id == derive_guid(project_uuid, item.slug)


def test_ids_are_unique(packages) -> None:
    items, _ = packages
    assert len({item.id for item in items}) == len(items)
    assert len({item.slug for item in items}) == len(items)


# --- allocation ------------------------------------------------------------------------------

def test_the_package_estimates_sum_to_the_estimate_total(packages) -> None:
    """No money invented, none lost — the property that makes the per-package numbers
    trustworthy at all."""
    items, estimate = packages
    for end in ("low", "high"):
        total = sum(getattr(item.estimate, end) for item in items)
        assert total == pytest.approx(estimate["grand_total"][end], abs=0.05)


def test_a_row_spanning_storeys_goes_building_wide_rather_than_being_split(packages) -> None:
    """Splitting a whole-building framing roll-up pro-rata would be an allocation nobody
    authored, and the per-storey numbers would then be confidently wrong."""
    items, _ = packages
    framing = [item for item in items if item.trade == "framing"]
    assert framing and all(item.storey == BUILDING for item in framing)


def test_a_row_whose_elements_share_a_storey_lands_on_that_storey(packages) -> None:
    items, _ = packages
    per_storey = [item for item in items if item.storey != BUILDING]
    assert per_storey, "every package landed building-wide — the tag join is not working"
    assert {item.storey for item in per_storey} <= {
        storey.tag for storey in _storeys()} | {BUILDING}


def _storeys():
    from typehaus.source import load_plan

    return load_plan(CATLIN).plan.storeys


def test_packages_come_out_in_construction_order(packages) -> None:
    items, _ = packages
    rank = {trade: i for i, trade in enumerate(CONSTRUCTION_SEQUENCE)}
    assert [rank[item.trade] for item in items] == sorted(rank[item.trade] for item in items)


def test_dependencies_only_name_packages_that_exist(packages) -> None:
    """A house with no stairs must not leave a dangling dependency on a stair package
    nobody will ever close."""
    items, _ = packages
    slugs = {item.slug for item in items}
    for item in items:
        assert set(item.depends_on) <= slugs, item.slug


def test_nothing_derives_a_duration_or_a_date(packages) -> None:
    items, _ = packages
    forbidden = {"duration", "start", "finish", "crew", "days", "date"}
    for item in items:
        assert not forbidden & set(item.as_dict()), item.slug


def test_without_prices_the_packages_still_carry_their_work(catlin_model) -> None:
    """Decision #28: dollars are opt-in. Which trades touch which storeys, covering which
    takeoff rows and which elements, is a property of the model and not of anybody's price
    list — so a house that opts out of prices loses the money, not the schedule."""
    items = build_work_items(catlin_model, bill_of_materials(catlin_model), estimate=None)
    assert items
    assert all(item.estimate.low == 0.0 and item.estimate.high == 0.0 for item in items)
    assert any(item.element_tags for item in items)
    assert any(item.rows for item in items)
