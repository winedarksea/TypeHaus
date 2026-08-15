"""Equivalence gate for the in-memory op applicator (→ responsiveness plan, Phase 2b risk).

The fast edit path applies ops to the pydantic ``PlanModel`` in memory; the background path
writes the ops to source with libcst and reloads. These two must produce the *same* plan or
the in-memory model silently diverges from the ground truth on disk. This test asserts exactly
that over a corpus of ops (the plan's mandated apply-in-memory-vs-apply-to-source check).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.inmemory import apply_ops_to_plan, can_apply_in_memory
from typehaus.model.ids import new_uid
from typehaus.source.macros import draw_wall, move_nodes
from typehaus.source.ops import PatchOp
from _helpers import copy_house


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    return dst


def _elements_by_tag(plan) -> dict[str, dict]:
    """{tag: element dump} across all storeys — order-independent structural comparison."""
    out: dict[str, dict] = {}
    for el in plan.all_elements():
        out[el.tag] = el.model_dump(mode="python")
    return out


def _assert_equivalent(house: Path, ops: list[PatchOp]) -> None:
    base = load_plan(house)
    assert base.plan is not None

    # Path B (in memory) first — before source changes underneath us.
    assert can_apply_in_memory(base.plan, ops)
    mem_plan, _minted = apply_ops_to_plan(base.plan, ops)

    # Path A (source writeback + reload).
    ProjectCoordinator(house).apply_patch(ops, None)
    reloaded = load_plan(house)
    assert reloaded.plan is not None, [f.message for f in reloaded.findings]

    assert _elements_by_tag(mem_plan) == _elements_by_tag(reloaded.plan)


def test_move_node_update_equivalent(house: Path):
    base = load_plan(house).plan
    ops = move_nodes(base, "main", ["N-2"], "1'-0\"", 0.0).ops
    assert ops and ops[0].op == "update"
    _assert_equivalent(house, ops)


def test_update_field_equivalent(house: Path):
    # Change a window's authored width via a hand update op.
    ops = [PatchOp("update", "Window", "WIN-101", {"sill_height": "3'-0\""})]
    _assert_equivalent(house, ops)


def test_delete_equivalent(house: Path):
    ops = [PatchOp("delete", "Window", "WIN-101", {})]
    _assert_equivalent(house, ops)


def test_multi_node_move_equivalent(house: Path):
    base = load_plan(house).plan
    ops = move_nodes(base, "main", ["N-2", "N-3"], 0.0, "-0'-6\"").ops
    _assert_equivalent(house, ops)


def test_draw_wall_add_equivalent(house: Path):
    # draw_wall adds a Node + Wall. Pin uids into the add ops so both paths (writeback mints,
    # in-memory mints) agree on identity — the same pinning the fast path uses in production.
    base = load_plan(house).plan
    ops = draw_wall(base, "main", ("20'-0\"", 0.0), ("24'-0\"", 0.0),
                    assembly="EXT").ops
    for op in ops:
        if op.op == "add" and "uid" not in op.fields:
            op.fields["uid"] = new_uid()
    _assert_equivalent(house, ops)
