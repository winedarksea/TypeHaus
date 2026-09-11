"""The five milestones partition the trade order, and nothing else may quietly change that."""

from __future__ import annotations

import pytest

from typehaus.emit.trades import CONSTRUCTION_SEQUENCE, TRADES
from typehaus.schedule.milestones import (
    MILESTONE_IDS,
    MILESTONE_OF_TRADE,
    MILESTONE_SPECS,
    build_milestones,
    current_milestone,
    milestone_of_inspection,
)


def test_the_slices_partition_the_trade_order_contiguously() -> None:
    flattened = [trade for _id, _label, trades in MILESTONE_SPECS for trade in trades]
    assert flattened == list(CONSTRUCTION_SEQUENCE)
    assert set(MILESTONE_OF_TRADE) == TRADES


def test_insulated_owns_no_trade_on_purpose() -> None:
    """Insulation is billed inside the assemblies; inventing a trade would break TRADES."""
    by_id = {spec[0]: spec[2] for spec in MILESTONE_SPECS}
    assert by_id["insulated"] == ()


class _Spec:
    def __init__(self, ident, milestone="", after=()):
        self.id, self.milestone, self.after = ident, milestone, after


def test_a_declared_milestone_wins() -> None:
    spec = _Spec("slab", "foundation", ("underground_plumbing",))
    assert milestone_of_inspection(spec, {"slab": spec}) == "foundation"


def test_an_undeclared_one_inherits_the_latest_predecessor() -> None:
    early = _Spec("framing", "rough_ins")
    late = _Spec("drywall", "insulated")
    orphan = _Spec("girt_screws", "", ("framing", "drywall"))
    by_id = {s.id: s for s in (early, late, orphan)}
    assert milestone_of_inspection(orphan, by_id) == "insulated"


def test_an_undeclared_root_falls_to_the_first_milestone() -> None:
    spec = _Spec("something", "")
    assert milestone_of_inspection(spec, {"something": spec}) == MILESTONE_IDS[0]


def test_an_unknown_milestone_raises_rather_than_silently_landing_somewhere() -> None:
    spec = _Spec("x", "weathertite")
    with pytest.raises(ValueError, match="unknown milestone"):
        milestone_of_inspection(spec, {"x": spec})


class _Visit:
    def __init__(self, slug, trade, status):
        self.slug, self.trade, self.status = slug, trade, status
        self.milestone = MILESTONE_OF_TRADE.get(trade, "")


def test_state_is_derived_from_the_visits_in_it() -> None:
    milestones = build_milestones(
        [_Visit("a", "earth", "verified"), _Visit("b", "concrete", "done"),
         _Visit("c", "framing", "todo"), _Visit("d", "floors", "scheduled")], [])
    by_id = {m.id: m for m in milestones}
    assert by_id["foundation"].state == "done"
    assert by_id["weathertight"].state == "in_progress"
    # An EMPTY milestone stays not_started. Claiming "done" for a row with nothing in it
    # would mark a house weathertight because nobody had authored any walls.
    assert by_id["final"].state == "not_started"
    assert current_milestone(milestones) == "weathertight"


def test_current_milestone_on_a_finished_house() -> None:
    milestones = build_milestones([_Visit("a", "earth", "verified")], [])
    # Only 'foundation' has any visits, so it is done and everything after it is empty:
    # the first not-done row is still the answer, and it is an honest one.
    assert current_milestone(milestones) == "weathertight"
