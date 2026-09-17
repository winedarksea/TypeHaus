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


def test_foundation_wall_patch_applies_rather_than_422(tmp_path: Path) -> None:
    """A PATCH addressed to a FoundationWall lands in source (was: WritebackError → 422).

    `writeback_py._call_kind` matches the constructor `Name` literally — deliberately, so a
    rewrite is honest about which constructor it edits — so the op has to carry the element's
    real class name. model.json now emits it per wall (`server/model_json_fabric._wall_kind`)
    and the UI sends it back instead of a hardcoded "Wall".
    """
    dst = tmp_path / "catlin"
    copy_house(CATLIN, dst)
    state = ProjectState.open(dst)
    basement = dst / "plan" / "storeys" / "basement.py"
    assert 'FoundationWall(uid="CBW101AAAA", tag="W-B-S1"' in basement.read_text()
    before = basement.read_text().count('assembly="BASEMENT_12"')

    state.apply_edit([PatchOp("update", "FoundationWall", "W-B-S1",
                              {"assembly": "BASEMENT_12"})], None)
    state._flush_writes()
    assert 'tag="W-B-S1"' in basement.read_text()
    assert basement.read_text().count('assembly="BASEMENT_12"') > before

    # The literal match is the point: the base kind is NOT a valid address for a subclass.
    with pytest.raises(WritebackError):
        state.apply_edit([PatchOp("update", "Wall", "W-B-S1", {})], None)


def test_model_json_kind_is_what_the_writeback_accepts(tmp_path: Path) -> None:
    """The emitted `kind` and the writeback's constructor match are one contract."""
    from typehaus.resolve import resolve
    from typehaus.server.model_json import model_to_dict

    dst = tmp_path / "catlin"
    copy_house(CATLIN, dst)
    result = load_plan(dst)
    model, _ = resolve(result.plan)
    kinds = {w["tag"]: w["kind"] for w in model_to_dict(model)["walls"]}
    assert kinds["W-B-S1"] == "FoundationWall"

    state = ProjectState.open(dst)
    state.apply_edit([PatchOp("update", kinds["W-B-S1"], "W-B-S1",
                              {"assembly": "BASEMENT_12"})], None)
    state._flush_writes()
    assert 'assembly="BASEMENT_12"' in (
        dst / "plan" / "storeys" / "basement.py").read_text()


def test_missing_placeables_list_is_a_clear_422(starter_dir: Path, tmp_path: Path) -> None:
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    placeables = dst / "plan" / "placeables.py"
    placeables.write_text(placeables.read_text().replace("# haus: editable\n", "", 1))
    with fastapi_testclient.TestClient(create_app(dst)) as c:
        response = c.post("/macro", json={"macro": "place_placeable", "storey": "main",
                                          "type_ref": "FURN-ARMCHAIR-35",
                                          "position": [3.5, 3.0]})
    assert response.status_code == 422
    assert "MAIN_PLACEABLES" in response.json()["error"]
    assert "plan/placeables.py" in response.json()["error"]


def test_saved_callback_fires_after_queue_drains(starter_dir: Path, tmp_path: Path) -> None:
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    saved: list[str] = []
    state._notify_saved = saved.append
    assert state.model is not None
    edit = state.apply_edit([PatchOp("update", "Window", "WIN-101",
                                     {"sill_height": "3'-0\""})], None)
    assert edit.fast
    state._flush_writes()
    state._idle.wait(5)
    assert saved == [state.revision()]
    window = next(e for e in load_plan(dst).plan.all_elements() if e.tag == "WIN-101")
    assert window.sill_height.inches == pytest.approx(36)


def test_placed_element_gains_provenance_without_invalidating_pending_commits(
        starter_dir: Path, tmp_path: Path) -> None:
    """A fresh add has no source location until its writeback lands; the reconcile then bumps
    the revision so clients refetch it — while a commit naming the old revision still applies."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    result, edit = state.apply_macro({"macro": "place_placeable", "storey": "main",
                                      "type_ref": "FURN-ARMCHAIR-35", "position": [3.5, 3.0]})
    tag = result.ops[0].tag
    assert state.provenance.location(tag) is None
    state._flush_writes()
    state._idle.wait(5)
    assert state.provenance.location(tag) is not None
    assert state.revision() != edit.revision
    state.apply_macro({"macro": "move_placeable", "storey": "main", "tag": tag,
                       "position": [4.0, 3.0], "revision": edit.revision})


def test_edit_to_an_element_whose_add_is_still_queued_routes(
        starter_dir: Path, tmp_path: Path) -> None:
    """Place then drag at once: the add is not on disk yet, and that must not be a 422."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    state._ensure_worker()
    gate = __import__("threading").Event()
    real = state.coordinator.apply_patch
    state.coordinator.apply_patch = lambda *a, **k: (gate.wait(10), real(*a, **k))[1]  # type: ignore[method-assign]
    result, _ = state.apply_macro({"macro": "place_placeable", "storey": "main",
                                   "type_ref": "FURN-ARMCHAIR-35", "position": [3.5, 3.0]})
    tag = result.ops[0].tag
    state.apply_macro({"macro": "move_placeable", "storey": "main", "tag": tag,
                       "position": [4.0, 3.0]})
    gate.set()
    state._flush_writes()
    moved = next(e for e in load_plan(dst).plan.all_elements() if e.tag == tag)
    assert moved.position.xy_m == pytest.approx((4.0, 3.0))


def test_reconcile_never_adopts_a_reload_older_than_the_plan(
        starter_dir: Path, tmp_path: Path) -> None:
    """An undo landing while the reconcile's source load runs must not be reverted by it."""
    dst = tmp_path / "starter"
    copy_house(starter_dir, dst)
    state = ProjectState.open(dst)
    result, _ = state.apply_macro({"macro": "place_placeable", "storey": "main",
                                   "type_ref": "FURN-ARMCHAIR-35", "position": [3.5, 3.0]})
    tag = result.ops[0].tag
    state.apply_macro({"macro": "retype_placeable", "storey": "main", "tag": tag,
                       "type_ref": "FURN-SOFA-84"})
    state._flush_writes()
    state._idle.wait(5)
    stale = load_plan(dst)
    print("DBG stale", [e.type_ref for e in stale.plan.all_elements() if e.tag == tag], state._undo_depth)  # the sofa; the undo below puts the armchair back on disk
    import typehaus.server.state as state_mod

    original = state_mod.load_plan
    fired: list[bool] = []

    def load_then_undo(house):
        if fired:  # the undo's own rebuild loads for real
            return original(house)
        fired.append(True)
        state.history(True)  # lands mid-reconcile, after the reload started
        return stale

    state_mod.load_plan = load_then_undo
    try:
        state._reconcile()
    finally:
        state_mod.load_plan = original
    assert next(e for e in state.plan.all_elements() if e.tag == tag).type_ref == "FURN-ARMCHAIR-35"
