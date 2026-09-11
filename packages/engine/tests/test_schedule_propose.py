"""The proposal is dialect-legal TOML, and it is never persisted.

"The engine proposes, the person commits" is only true if the proposal is *pasteable*:
a split the owner has to retype is a split nobody accepts.
"""

from __future__ import annotations

import tomllib

from typehaus.cli.prices import ZERO
from typehaus.schedule.propose import ARRIVAL_CONSTRAINTS, propose_all, propose_visits
from typehaus.takeoff.tasks import WorkItem


class _Spec:
    def __init__(self, ident, gates):
        self.id, self.gates = ident, gates


def _item(rows, tags, trade="concrete", depends_on=("task/earth/building",)):
    return WorkItem(id="x", slug=f"task/{trade}/building", trade=trade, storey="building",
                    cost_code="", rows=tuple(rows), element_tags=tuple(tags),
                    estimate=ZERO, depends_on=tuple(depends_on))


_ITEM = _item(
    [("concrete", "footing"), ("concrete", "slab"), ("concrete", "slab:DECK_EPS_INT")],
    ["FT-B-E2", "FT-B-W1", "SL-B-SLAB"])


def test_one_row_family_is_not_worth_splitting() -> None:
    assert propose_visits(_item([("concrete", "footing")], ["FT-B-E2"])) == []


def test_a_split_follows_the_bom_row_families() -> None:
    proposals = propose_visits(_ITEM)
    assert [p["slug"] for p in proposals] == ["task/concrete/building/footing",
                                              "task/concrete/building/slab"]
    # `slab` and `slab:DECK_EPS_INT` are the same pour billed twice — one arrival.
    slab = proposals[1]
    assert [f"{r['section']}:{r['key']}" for r in slab["rows"]] == [
        "concrete:slab", "concrete:slab:DECK_EPS_INT"]


def test_tags_become_globs_the_owner_can_widen() -> None:
    proposals = propose_visits(_ITEM)
    assert proposals[0]["element_tags"] == ["FT-B-*"]


def test_only_the_first_arrival_inherits_the_packages_predecessors() -> None:
    proposals = propose_visits(_ITEM, (_Spec("footing_insp", ("concrete",)),))
    assert proposals[0]["depends_on"] == ["task/earth/building", "insp/footing_insp"]
    assert proposals[1]["depends_on"] == ["task/concrete/building/footing"]


def test_every_proposal_carries_the_arrival_list_and_its_trade_defaults() -> None:
    proposals = propose_visits(_ITEM)
    constraints = proposals[0]["constraints"]
    assert set(ARRIVAL_CONSTRAINTS).issubset(constraints)
    assert any("rebar" in label for label in constraints)


def test_no_constraint_names_a_lead_time() -> None:
    """Labels only. How many weeks a supplier quoted is not in this model."""
    from typehaus.schedule.propose import DEFAULT_CONSTRAINTS

    every = [label for labels in DEFAULT_CONSTRAINTS.values() for label in labels]
    every += list(ARRIVAL_CONSTRAINTS)
    assert not [label for label in every
                if any(word in label for word in ("week", "lead time", "days ahead"))
                and "48 hours" not in label]


def test_the_toml_parses_back_into_a_visit_table() -> None:
    for proposal in propose_visits(_ITEM):
        parsed = tomllib.loads(proposal["toml"])
        table = parsed["visits"][proposal["slug"]]
        assert table["label"] and table["rows"]
        assert all(set(c) == {"label"} for c in table["constraints"])


def test_the_parsed_proposal_is_accepted_by_the_loader(tmp_path) -> None:
    """The proof that "paste this" is a real instruction."""
    from typehaus.takeoff.task_state import load_tasks

    text = "\n\n".join(p["toml"] for p in propose_visits(_ITEM))
    (tmp_path / "tasks.toml").write_text(text + "\n")
    state = load_tasks(tmp_path)
    assert set(state.visits.entries) == {"task/concrete/building/footing",
                                         "task/concrete/building/slab"}


def test_propose_all_skips_packages_with_nothing_to_split() -> None:
    out = propose_all([_ITEM, _item([("framing", "stud")], ["W-M-1"], trade="framing")])
    assert set(out) == {"task/concrete/building"}
