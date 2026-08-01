"""Server session state — one resolved project + its mutation coordinator (→ 20 §Server).

Holds the loaded plan, the resolved model, and the :class:`ProjectCoordinator` that owns
write safety + the undo journal.

Two mutation paths (→ responsiveness plan, Phase 2b):

* **Fast path** (``apply_edit`` when the ops apply cleanly in memory): apply ops to the
  in-memory :class:`PlanModel`, resolve, and return immediately — no disk, no re-import,
  no full source re-scan. The libcst source writeback is queued on a background worker and
  reconciled against a fresh source load afterwards (source stays the ground truth; the
  in-memory model is a cache of it, guarded by the ``test_inmemory_equivalence`` gate).
* **Slow path** (ops that can't be applied in memory, or a load failure): the classic
  writeback-then-``rebuild`` from source.

The client-facing *revision* is a monotonic token, not the source content hash, so the push
need not wait for the write to land. The content hash is used only to detect *external*
edits in the watcher.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from typehaus.checks import load_preferences
from typehaus.findings import Finding, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve import resolve, resolve_preview
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json import load_variant_catalog, model_to_dict, preview_to_dict
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.inmemory import InMemoryApplyError, apply_ops_to_plan, can_apply_in_memory
from typehaus.source.ops import PatchOp
from typehaus.source.provenance import Provenance

log = logging.getLogger("typehaus.server")


@dataclass
class EditResult:
    revision: str
    minted_uids: dict[str, str]
    undo_depth: int
    redo_depth: int
    fast: bool


@dataclass
class ProjectState:
    house_dir: Path
    coordinator: ProjectCoordinator
    model: ResolvedModel | None = None
    plan: PlanModel | None = None
    provenance: Provenance = field(default_factory=Provenance)
    findings: list[Finding] = field(default_factory=list)
    # Load-time (loader/dialect) findings from the last source load, kept apart so the fast
    # path — which never reloads source — can carry them forward instead of dropping them.
    _load_findings: list[Finding] = field(default_factory=list)
    ok: bool = False
    # True between a resolve landing and its (async, Phase 3) check-tier job completing;
    # `findings`/`ok` reflect resolve-time findings only for that window.
    checks_pending: bool = False
    # Per-stage rebuild timings in milliseconds (Phase 0). Surfaced via model_json()["perf"].
    timings: dict[str, float] = field(default_factory=dict)
    # Client-facing monotonic revision token (Phase 2b): decoupled from the source content
    # hash so a fast push need not wait for the source writeback to land.
    _revision: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    # Optimistic undo/redo depths shown in the UI. Each fast edit adds one undo entry; the
    # authoritative journal is built by the background writeback and reconciled if it drifts.
    _undo_depth: int = 0
    _redo_depth: int = 0
    _model_cache: tuple[str, dict[str, Any]] | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)
    # Background source-writeback worker (lazily started): a single thread applies queued
    # writebacks in order, so disk source is a faithful, serialized replay of the fast edits.
    _write_q: "queue.Queue[list[PatchOp] | None]" = field(default_factory=queue.Queue)
    _worker: threading.Thread | None = None
    _idle: threading.Event = field(default_factory=threading.Event)
    # Optional callback (app-provided) to notify clients when reconciliation adopts source
    # truth after a divergence — scheduled thread-safely onto the server event loop.
    _notify_diverged: Callable[[], None] | None = None
    # Optional callback (app-provided) reporting a *failed* async source writeback, whose
    # edit the following reconcile silently reverts. Takes the failure detail.
    _notify_writeback_failed: Callable[[str], None] | None = None
    # Background checks worker (Phase 3): a single-slot request coalesces to the latest
    # resolve, so an edit landing mid-check supersedes the in-flight check job's result.
    _checks_cv: threading.Condition = field(default_factory=threading.Condition)
    _checks_request: tuple[str, PlanModel, ResolvedModel, list[Finding]] | None = None
    _checks_worker: threading.Thread | None = None
    _checks_idle: threading.Event = field(default_factory=threading.Event)
    # Optional callback (app-provided) notifying clients that async check-tier results landed.
    _notify_checks: Callable[[], None] | None = None

    @classmethod
    def open(cls, house_dir: Path) -> ProjectState:
        house_dir = house_dir.resolve()
        state = cls(house_dir=house_dir, coordinator=ProjectCoordinator(house_dir))
        state._idle.set()
        state._checks_idle.set()
        state.rebuild()
        return state

    # --- revision -----------------------------------------------------------
    def revision(self) -> str:
        return self._revision

    def _bump_revision(self) -> None:
        self._revision = uuid.uuid4().hex[:16]
        self._model_cache = None

    # --- full rebuild from source (open, undo/redo, watcher, build) ----------
    def rebuild(self) -> None:
        """Reload plan source, re-resolve, and refresh findings (the shared rebuild path)."""
        with self._lock:
            self._model_cache = None
            timings: dict[str, float] = {}
            t0 = time.perf_counter()
            result = load_plan(self.house_dir)
            timings["load_plan"] = (time.perf_counter() - t0) * 1000.0
            timings.update({f"load_plan.{k}": v for k, v in result.timings.items()})
            self.provenance = result.provenance
            self.findings = list(result.findings)
            self._load_findings = list(result.findings)
            self.plan = result.plan
            if result.plan is None:
                self.model = None
                self.ok = False
                self.timings = timings
                self._bump_revision()
                return
            self._resolve_and_check(result.plan, timings, list(result.findings))

    def _resolve_and_check(
        self, plan: PlanModel, timings: dict[str, float], base_findings: list[Finding]
    ) -> None:
        """Resolve ``plan`` synchronously and queue the (slower, tiered) checks to run on a
        background thread (→ Phase 3): the interactive path never waits on `run_from_model`.

        ``base_findings`` are the load-time (loader/dialect) findings this resolve sits on
        top of; they are carried through the whole pipeline so an ERROR like
        ``loader.uneditable_movable_element`` reaches ``GET /model`` instead of being
        overwritten here.

        ``self.ok``/``self.findings`` reflect load+resolve-time findings alone until the queued
        check job lands and merges in the check-tier findings — a brief window (a handful of
        ms on this house; the plan's whole point is that some future check tier may not be).
        ``self.checks_pending`` is surfaced in ``model_json()`` so the UI can show it."""
        t0 = time.perf_counter()
        model, rfindings = resolve(plan)
        timings["resolve"] = (time.perf_counter() - t0) * 1000.0
        timings.update({f"resolve.{k}": v for k, v in model.timings.items()})
        self._load_findings = list(base_findings)
        combined = base_findings + list(rfindings)
        self.model = model
        self.plan = plan
        self.findings = combined
        self.ok = not any(f.severity is Severity.ERROR for f in combined)
        self.timings = timings
        self.checks_pending = True
        self._bump_revision()
        self._queue_checks(self._revision, plan, model, combined)

    # --- background checks worker (Phase 3) ---------------------------------
    def _queue_checks(
        self, revision: str, plan: PlanModel, model: ResolvedModel, rfindings: list[Finding]
    ) -> None:
        """Replace any pending check job with this one — only the latest resolve matters,
        so an edit that lands mid-check makes the in-flight result moot, not queued work."""
        with self._checks_cv:
            self._checks_request = (revision, plan, model, rfindings)
            self._checks_idle.clear()
            self._checks_cv.notify()
        if self._checks_worker is None:
            self._checks_worker = threading.Thread(
                target=self._checks_loop, name="haus-checks", daemon=True
            )
            self._checks_worker.start()

    def _checks_loop(self) -> None:
        from typehaus.checks import run_from_model

        while True:
            with self._checks_cv:
                while self._checks_request is None:
                    self._checks_cv.wait()
                revision, plan, model, rfindings = self._checks_request
                self._checks_request = None
            t0 = time.perf_counter()
            report = run_from_model(model, rfindings, self.house_dir)
            elapsed = (time.perf_counter() - t0) * 1000.0
            with self._lock:
                stale = revision != self._revision
                if not stale:
                    self.findings = report.findings
                    self.ok = report.ok
                    self.timings["run_checks"] = elapsed
                    self.checks_pending = False
                    self._model_cache = None
            with self._checks_cv:
                if self._checks_request is None:
                    self._checks_idle.set()
            if not stale and self._notify_checks is not None:
                self._notify_checks()

    def _flush_checks(self) -> None:
        """Block until the queued check-tier job has landed (used by tests / before /checks)."""
        self._checks_idle.wait()

    # --- unified mutation entry ---------------------------------------------
    def apply_edit(
        self, ops: list[PatchOp], expected_revision: str | None
    ) -> EditResult:
        """Apply ``ops`` (from PATCH /plan or a macro). Fast path when the ops apply cleanly
        in memory; otherwise the classic writeback-then-rebuild. Raises RevisionMismatch on a
        stale precondition, WritebackError/ExternalEdit on a bad op."""
        from typehaus.source.coordinator import RevisionMismatch

        with self._lock:
            if expected_revision is not None and expected_revision != self._revision:
                raise RevisionMismatch(
                    f"revision {expected_revision} != {self._revision}; reload and retry"
                )
            # Rehearse routing first: an op targeting a non-`# haus: editable` file can be
            # applied in memory but never written back, so without this the edit would 200,
            # render, and then silently snap back when the async writeback failed.
            self.coordinator.can_route(ops)
            if self.plan is not None and can_apply_in_memory(self.plan, ops):
                try:
                    return self._apply_fast(ops)
                except InMemoryApplyError as exc:
                    log.warning("fast apply failed (%s); falling back to source path", exc)
            return self._apply_slow(ops)

    def _apply_fast(self, ops: list[PatchOp]) -> EditResult:
        assert self.plan is not None
        new_plan, minted = apply_ops_to_plan(self.plan, ops)
        # Pin minted uids into the ops so the queued source writeback uses identical identity.
        pinned: list[PatchOp] = []
        for op in ops:
            if op.op == "add" and op.tag in minted and "uid" not in op.fields:
                pinned.append(PatchOp(op.op, op.type, op.tag, {**op.fields, "uid": minted[op.tag]},
                                      hint_file=op.hint_file, hint_list=op.hint_list))
            else:
                pinned.append(op)
        timings: dict[str, float] = {}
        # The fast path doesn't reload source, so load-time findings still hold: carry the
        # prior ones forward rather than zeroing them (they'd reappear on the next rebuild).
        self._resolve_and_check(new_plan, timings, list(self._load_findings))  # bumps _revision
        self._undo_depth += 1
        self._redo_depth = 0
        self._enqueue_writeback(pinned)
        return EditResult(self._revision, minted, self._undo_depth, self._redo_depth, fast=True)

    def _apply_slow(self, ops: list[PatchOp]) -> EditResult:
        self._flush_writes()
        result = self.coordinator.apply_patch(ops, None)
        self.rebuild()
        self._undo_depth, self._redo_depth = result.undo_depth, result.redo_depth
        return EditResult(self._revision, result.minted_uids,
                          self._undo_depth, self._redo_depth, fast=False)

    def rehearse(self, ops: list[PatchOp]) -> None:
        """Ask *before* the gesture whether ``ops`` could ever be written back, raising the
        same WritebackError/ExternalEdit :meth:`apply_edit` would raise at commit.

        This is the pre-emption half of the editable-writeback contract: apply_edit already
        fails synchronously (422) so an edit never silently snaps back, but by then the user
        has dragged an element across the canvas for nothing. A client calls this once at
        drag-*start* to refuse the gesture up front. It re-reads every editable file, so it is
        far too heavy to call per move — hence "once per gesture", not per preview frame."""
        self.coordinator.can_route(ops)

    # --- live drag preview (→ Phase 4) --------------------------------------
    def preview(self, ops: list[PatchOp]) -> dict[str, Any] | None:
        """A read-only, reduced-resolve preview of ``ops`` against the current plan: no
        revision bump, no writeback, no checks, no undo entry. Returns ``None`` if ``ops``
        can't be applied in memory (caller keeps showing the last-good preview/committed
        geometry). Safe to call at drag-move frequency — resolve_preview skips the pipeline's
        costlier stages a ghost overlay never renders (framing/floors/stacking/conditions)."""
        with self._lock:
            if self.plan is None or not can_apply_in_memory(self.plan, ops):
                return None
            try:
                new_plan, _minted = apply_ops_to_plan(self.plan, ops)
            except InMemoryApplyError:
                return None
        model = resolve_preview(new_plan)
        return preview_to_dict(model)

    # --- undo / redo (flush pending writes, then classic source replay) ------
    def history(self, undo: bool) -> EditResult:
        with self._lock:
            self._flush_writes()
            result = self.coordinator.undo() if undo else self.coordinator.redo()
            self.rebuild()
            self._undo_depth, self._redo_depth = result.undo_depth, result.redo_depth
            return EditResult(self._revision, {}, self._undo_depth, self._redo_depth, fast=False)

    # --- background writeback worker ----------------------------------------
    def _ensure_worker(self) -> None:
        if self._worker is None:
            self._worker = threading.Thread(
                target=self._writeback_loop, name="haus-writeback", daemon=True
            )
            self._worker.start()

    def _enqueue_writeback(self, ops: list[PatchOp]) -> None:
        self._ensure_worker()
        self._idle.clear()
        self._write_q.put(ops)

    def _writeback_loop(self) -> None:
        while True:
            ops = self._write_q.get()
            if ops is None:
                self._write_q.task_done()
                return
            try:
                self.coordinator.apply_patch(ops, None)
            except Exception as exc:  # noqa: BLE001 - a failure must not kill the worker
                log.exception("source writeback failed; reconciling from source")
                # Backstop for anything can_route couldn't foresee (lint failure, external
                # edit): the reconcile below reverts the in-memory model, so the client must
                # be told *why* its edit vanished rather than seeing a silent hot-reload.
                if self._notify_writeback_failed is not None:
                    self._notify_writeback_failed(str(exc) or exc.__class__.__name__)
            finally:
                self._write_q.task_done()
            if self._write_q.empty():
                self._reconcile()
                self._idle.set()

    def _flush_writes(self) -> None:
        """Block until all queued writebacks have landed on disk (used before undo/external)."""
        if self._worker is not None:
            self._write_q.join()

    def _reconcile(self) -> None:
        """Compare the source-of-truth reload against the in-memory plan; on divergence adopt
        source and notify. Divergence should never happen (equivalence gate) — it bounds the
        blast radius of an applicator bug to a brief flicker + a loud log, not corruption."""
        try:
            reloaded = load_plan(self.house_dir)
        except Exception:  # noqa: BLE001
            log.exception("reconcile reload failed")
            return
        with self._lock:
            in_mem = self.plan
            if reloaded.plan is None or in_mem is None:
                return
            if reloaded.plan.model_dump() != in_mem.model_dump():
                log.error(
                    "in-memory plan diverged from source after writeback; adopting source"
                )
                self.findings = list(reloaded.findings)
                self.provenance = reloaded.provenance
                self._resolve_and_check(reloaded.plan, {})  # bumps _revision
                if self._notify_diverged is not None:
                    self._notify_diverged()
            else:
                # Refresh provenance (line numbers shifted by the writeback) for pick→source.
                self.provenance = reloaded.provenance
                self._model_cache = None

    # --- serialization ------------------------------------------------------
    def model_json(self) -> dict[str, Any]:
        with self._lock:
            revision = self._revision
            if self.model is None:
                return {
                    "revision": revision,
                    "units": "imperial", "projectNorth": 0.0,
                    "findings": [f.model_dump(mode="json") for f in self.findings],
                    "ok": False,
                    "perf": dict(self.timings),
                    "checksPending": self.checks_pending,
                }
            if self._model_cache is not None and self._model_cache[0] == revision:
                return self._model_cache[1]
            payload = model_to_dict(
                self.model,
                revision=revision,
                provenance=self.provenance,
                findings=self.findings,
                preferences=load_preferences(self.house_dir),
                # Graceful: absent or malformed variants.toml serves an empty catalog
                # rather than failing the GET /model contract.
                variants=load_variant_catalog(self.house_dir),
            )
            payload["ok"] = self.ok
            payload["perf"] = dict(self.timings)
            payload["checksPending"] = self.checks_pending
            self._model_cache = (revision, payload)
            return payload

    def findings_json(self) -> list[dict[str, Any]]:
        with self._lock:
            return [f.model_dump(mode="json") for f in self.findings]
