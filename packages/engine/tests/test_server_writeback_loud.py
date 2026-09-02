"""A writeback that cannot land must fail loudly, not 200-then-snap-back.

The failure mode this guards against: an edit to an element authored in a non-`# haus:
editable` file applies on the in-memory fast path, returns 200, renders — and then the
async writeback raises `WritebackError` into a swallowed log line, after which
`_reconcile` adopts source truth and broadcasts a generic `file-changed` the UI hot-reloads
silently. Two defenses:

* `can_route` rehearses routing *before* the fast path → synchronous 422;
* `_notify_writeback_failed` backstops anything routing can't foresee (lint, external edit).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.server.state import ProjectState
from typehaus.source.loader import load_plan
from typehaus.source.ops import PatchOp
from typehaus.source.writeback import WritebackError
from _helpers import CATLIN, copy_house



@pytest.fixture
def uneditable_house(tmp_path: Path) -> Path:
    dst = tmp_path / "catlin"
    copy_house(CATLIN, dst)
    mep = dst / "plan" / "mep_hvac.py"  # authors EQ-B-WH, a UI-movable placeable
    mep.write_text(mep.read_text().replace("# haus: editable\n", "", 1))
    return dst


def test_edit_to_uneditable_file_raises_synchronously(uneditable_house: Path) -> None:
    state = ProjectState.open(uneditable_house)
    op = PatchOp("update", "Equipment", "EQ-B-WH", {"x": "3'"})
    with pytest.raises(WritebackError) as exc:
        state.apply_edit([op], None)
    assert "EQ-B-WH" in str(exc.value)


def test_editable_target_still_routes(starter_dir: Path, tmp_path: Path) -> None:
    """Control: the pre-check must not reject ordinary edits."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    assert state.plan is not None
    tag = state.model.walls[0].tag  # type: ignore[union-attr]
    state.apply_edit([PatchOp("update", "Wall", tag, {})], None)


def test_failed_async_writeback_fires_the_callback(starter_dir: Path, tmp_path: Path) -> None:
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    seen: list[str] = []
    state._notify_writeback_failed = seen.append

    def boom(*_args, **_kwargs):
        raise WritebackError("staged source fails dialect lint")

    state.coordinator.apply_patch = boom  # type: ignore[method-assign]
    assert state.model is not None
    tag = state.model.walls[0].tag
    state.apply_edit([PatchOp("update", "Wall", tag, {})], None)
    state._flush_writes()
    assert seen and "dialect lint" in seen[0]


def test_rehearse_refuses_uneditable_target_without_mutating(uneditable_house: Path) -> None:
    """The pre-emption half (→ W7b): a client can ask *before* the gesture.

    `apply_edit` already fails synchronously, but only after the user has dragged the element
    across the canvas. `rehearse` raises the same error with nothing applied — no revision
    bump, no journal entry — so a drag can be refused at drag-start instead of at mouseup.
    """
    state = ProjectState.open(uneditable_house)
    before = state._revision
    op = PatchOp("update", "Equipment", "EQ-B-WH", {"x": "3'"})
    with pytest.raises(WritebackError) as exc:
        state.rehearse([op])
    assert "EQ-B-WH" in str(exc.value)
    assert state._revision == before


def test_rehearse_passes_an_editable_target(starter_dir: Path, tmp_path: Path) -> None:
    """Control: rehearsal must not refuse the ordinary case, and must stay side-effect free."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    assert state.plan is not None
    before = state._revision
    tag = state.model.walls[0].tag  # type: ignore[union-attr]
    state.rehearse([PatchOp("update", "Wall", tag, {})])
    assert state._revision == before


def test_reconcile_recovers_when_the_in_memory_plan_diverges(starter_dir, tmp_path) -> None:
    """The divergence backstop must actually run.

    `_reconcile` is the one path that recovers from an applicator bug — it adopts source and
    notifies. It called `_resolve_and_check` with two of its three arguments, so it raised
    TypeError instead of recovering, and nothing caught it: the equivalence gate asserts
    divergence never happens, so no test ever entered this branch.
    """
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    notified = []
    state._notify_diverged = lambda: notified.append(True)

    # Force divergence: drop a storey's elements from the in-memory plan only.
    storey = next(iter(state.plan.elements))
    state.plan = state.plan.with_elements(storey, ())
    assert state.plan.model_dump() != load_plan(dst).plan.model_dump()

    state._reconcile()

    # Source is ground truth again, findings came back with it, and the client was told.
    assert state.plan.model_dump() == load_plan(dst).plan.model_dump()
    assert notified == [True]
    assert state.model is not None
