"""A writeback that cannot land must fail loudly, not 200-then-snap-back.

Before this, an edit to an element authored in a non-`# haus: editable` file applied on the
in-memory fast path, returned 200, rendered — and then the async writeback raised
`WritebackError` into a swallowed log line, after which `_reconcile` adopted source truth and
broadcast a generic `file-changed` the UI hot-reloaded silently. Two defenses:

* `can_route` rehearses routing *before* the fast path → synchronous 422;
* `_notify_writeback_failed` backstops anything routing can't foresee (lint, external edit).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from typehaus.server.state import ProjectState
from typehaus.source.ops import PatchOp
from typehaus.source.writeback import WritebackError

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture
def uneditable_house(tmp_path: Path) -> Path:
    dst = tmp_path / "catlin"
    shutil.copytree(CATLIN, dst)
    mep = dst / "plan" / "mep.py"  # authors EQ-B-WH, a UI-movable placeable
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
    shutil.copytree(starter_dir, dst)
    state = ProjectState.open(dst)
    assert state.plan is not None
    tag = state.model.walls[0].tag  # type: ignore[union-attr]
    state.apply_edit([PatchOp("update", "Wall", tag, {})], None)


def test_failed_async_writeback_fires_the_callback(starter_dir: Path, tmp_path: Path) -> None:
    dst = tmp_path / "starter"
    shutil.copytree(starter_dir, dst)
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
