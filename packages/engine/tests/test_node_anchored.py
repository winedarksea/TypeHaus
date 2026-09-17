"""P5: ``Node.anchored`` pins a node against ``move_nodes`` (wall-body drag)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source.macros import MacroError, move_nodes
from typehaus.source.ops import PatchOp
from _helpers import copy_house


def test_move_nodes_holds_anchored_node(tmp_path: Path, starter_dir: Path):
    from typehaus.server.state import ProjectState

    house = copy_house(starter_dir, tmp_path / "house")
    state = ProjectState.open(house)
    # The Inspector's "Pin start" checkbox: a plain update op, written back to source.
    state.apply_edit([PatchOp("update", "Node", "N-1", {"anchored": True})], None)
    state._flush_writes()
    assert "anchored=True" in (house / "plan" / "storeys" / "main.py").read_text()

    plan = load_plan(house).plan
    before = {n.tag: n.position.xy_m for n in plan.storey_elements("main")
              if n.tag in ("N-1", "N-2")}
    ops = move_nodes(plan, "main", ["N-1", "N-2"], 0.5, 0.0).ops
    moved = {op.tag for op in ops if op.type == "Node"}
    assert moved == {"N-2"}, "the anchored end holds; the free end follows the drag"
    assert before["N-1"] == (0.0, 0.0)

    with pytest.raises(MacroError, match="anchor-pinned"):
        move_nodes(plan, "main", ["N-1"], 0.5, 0.0)
