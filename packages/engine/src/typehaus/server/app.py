"""FastAPI server — ``haus serve`` (→ 20 §FastAPI server, WP2.1).

Endpoints: ``GET /model``, ``GET /model.ifc``, ``GET /checks``, ``PATCH /plan``,
``POST /build|/undo|/redo``, ``WS /events``. ``watchfiles`` watches plan source so edits
by VSCode/Claude hot-reload the UI — the two-screen workflow is symmetric by design. Every
mutation flows through the :class:`ProjectCoordinator` (revision precondition + undo journal).
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any

from typehaus.server.events import EventBus
from typehaus.server.state import ProjectState
from typehaus.source.coordinator import ExternalEdit, RevisionMismatch
from typehaus.source.ops import PatchOp
from typehaus.source.writeback import WritebackError


def create_app(house_dir: Path) -> Any:
    from contextlib import asynccontextmanager

    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse

    state = ProjectState.open(house_dir)
    bus = EventBus()

    @asynccontextmanager
    async def lifespan(app: Any):  # watchfiles reloader lives for the server's lifetime
        task = asyncio.create_task(_watch(state, bus))
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="Type:Haus serve", lifespan=lifespan)
    app.state.project = state
    app.state.bus = bus

    @app.get("/model")
    def get_model() -> Any:
        return JSONResponse(state.model_json())

    @app.get("/checks")
    def get_checks() -> Any:
        return JSONResponse({"findings": state.findings_json()})

    @app.get("/model.ifc")
    def get_ifc() -> Any:
        out = state.house_dir / "out" / "model.ifc"
        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        try:
            from typehaus.emit.ifc import emit_ifc

            emit_ifc(state.model, out, lod="core")
        except RuntimeError as exc:  # ifcopenshell absent
            return JSONResponse({"error": str(exc)}, status_code=503)
        return FileResponse(out, media_type="application/x-step")

    @app.patch("/plan")
    async def patch_plan(body: dict[str, Any]) -> Any:
        try:
            ops = [PatchOp.from_json(o) for o in body.get("ops", [])]
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        try:
            result = state.coordinator.apply_patch(ops, body.get("revision"))
        except RevisionMismatch as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except (WritebackError, ExternalEdit) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        state.rebuild()
        await bus.broadcast({"type": "patched", "revision": result.revision,
                             "minted": result.minted_uids,
                             "undo": result.undo_depth, "redo": result.redo_depth})
        return JSONResponse({"revision": result.revision, "minted": result.minted_uids,
                             "undo": result.undo_depth, "redo": result.redo_depth})

    @app.post("/macro")
    async def post_macro(body: dict[str, Any]) -> Any:
        from typehaus.server.macros_api import build_macro_ops, MacroRequestError

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        try:
            result = build_macro_ops(state.model.plan, body)
        except MacroRequestError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        try:
            patch = state.coordinator.apply_patch(result.ops, body.get("revision"))
        except RevisionMismatch as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except (WritebackError, ExternalEdit) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        state.rebuild()
        await bus.broadcast({"type": "patched", "revision": patch.revision,
                             "minted": patch.minted_uids,
                             "undo": patch.undo_depth, "redo": patch.redo_depth})
        return JSONResponse({
            "revision": patch.revision, "minted": patch.minted_uids,
            "undo": patch.undo_depth, "redo": patch.redo_depth,
            "remap": {"renamed": result.remap.renamed,
                      "deleted": sorted(result.remap.deleted),
                      "rehost": result.remap.rehost},
            "deleted": list(result.deleted_tags),
            "warnings": list(result.warnings),
        })

    @app.get("/model.glb")
    def get_glb() -> Any:
        out = state.house_dir / "out" / "model.glb"
        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        from typehaus.emit.gltf import emit_glb

        emit_glb(state.model, out)
        return FileResponse(out, media_type="model/gltf-binary")

    @app.post("/build")
    async def post_build() -> Any:
        state.rebuild()
        await bus.broadcast({"type": "build", "revision": state.coordinator.revision()})
        return JSONResponse({"ok": state.ok, "revision": state.coordinator.revision()})

    @app.post("/undo")
    async def post_undo() -> Any:
        return await _history(state, bus, undo=True)

    @app.post("/redo")
    async def post_redo() -> Any:
        return await _history(state, bus, undo=False)

    @app.websocket("/events")
    async def events(ws: WebSocket) -> None:
        await bus.connect(ws)
        try:
            while True:
                await ws.receive_text()  # keep-alive; server is push-only
        except WebSocketDisconnect:
            bus.disconnect(ws)

    return app


async def _history(state: ProjectState, bus: EventBus, undo: bool) -> Any:
    from fastapi.responses import JSONResponse

    try:
        result = state.coordinator.undo() if undo else state.coordinator.redo()
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)
    state.rebuild()
    await bus.broadcast({"type": "undo" if undo else "redo", "revision": result.revision,
                         "undo": result.undo_depth, "redo": result.redo_depth})
    return JSONResponse({"revision": result.revision,
                         "undo": result.undo_depth, "redo": result.redo_depth})


async def _watch(state: ProjectState, bus: EventBus) -> None:
    """Watch plan source; on an external edit, seal the journal, rebuild, and notify (< 2 s)."""
    from watchfiles import awatch

    plan_dir = state.house_dir / "plan"
    async for _changes in awatch(plan_dir):
        if state.coordinator.check_external_edit():
            state.rebuild()
            await bus.broadcast({"type": "file-changed",
                                 "revision": state.coordinator.revision(),
                                 "ok": state.ok})
