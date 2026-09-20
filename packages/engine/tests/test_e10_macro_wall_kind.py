"""The graph macros must name the wall's REAL class, not a hardcoded ``"Wall"``.

`writeback_py._call_kind` matches the constructor `Name` literally, so an op addressed to a
`FoundationWall` as `"Wall"` cannot land (the 422 of `test_server_writeback_loud`). The macros
mint their own ops, so they have to read `element_kind` off the element they are editing.
"""

from __future__ import annotations

from typehaus.source.macros_rooms import delete_wall
from typehaus.source.macros_split import split_wall_ops

STOREY = "basement"


def _foundation_wall(plan):
    return next(w for w in plan.storey_elements(STOREY)
                if w.element_kind == "FoundationWall")


def test_split_ops_carry_the_foundation_wall_class(catlin_plan) -> None:
    plan = catlin_plan
    wall = _foundation_wall(plan)
    result = split_wall_ops(plan, STOREY, wall, 0.5, "N-E10-MID", "W-E10-NEW")
    kinds = {op.type for op in result.ops if op.tag in (wall.tag, "W-E10-NEW")}
    assert kinds == {"FoundationWall"}


def test_delete_wall_ops_carry_the_foundation_wall_class(catlin_plan) -> None:
    plan = catlin_plan
    wall = _foundation_wall(plan)
    result = delete_wall(plan, STOREY, wall.tag)
    deletes = [op for op in result.ops if op.tag == wall.tag and op.op == "delete"]
    assert [op.type for op in deletes] == ["FoundationWall"]
