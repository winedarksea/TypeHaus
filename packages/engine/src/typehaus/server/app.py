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


def create_app(house_dir: Path, ui_dist: Path | None = None) -> Any:
    """Build the FastAPI app.

    ``ui_dist`` — when given a built UI directory (``ui/dist`` holding ``index.html``) the
    compiled single-page app is served at ``/`` alongside the API, so a user on another
    machine runs one ``haus serve`` command and opens the app in a browser (V6). The API
    routes are registered first and always win; a trailing SPA catch-all serves real static
    files and falls back to ``index.html`` for client-side routes. Omit it (the default) to
    keep the historical API-only server used by the test-suite.
    """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse

    state = ProjectState.open(house_dir)
    bus = EventBus()

    @asynccontextmanager
    async def lifespan(app: Any):  # watchfiles reloader lives for the server's lifetime
        loop = asyncio.get_running_loop()

        def _notify_diverged() -> None:
            async def _broadcast() -> None:
                await bus.broadcast({"type": "file-changed", "revision": state.revision(),
                                     "ok": state.ok})
            loop.call_soon_threadsafe(lambda: asyncio.create_task(_broadcast()))

        state._notify_diverged = _notify_diverged

        def _notify_checks() -> None:
            async def _broadcast() -> None:
                await bus.broadcast({"type": "checks", "revision": state.revision(),
                                     "ok": state.ok, "findings": state.findings_json()})
            loop.call_soon_threadsafe(lambda: asyncio.create_task(_broadcast()))

        state._notify_checks = _notify_checks
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

    @app.get("/details")
    def get_details() -> Any:
        from typehaus.emit.draw.details import detail_index

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        return JSONResponse({"details": detail_index(state.model)})

    @app.get("/bom")
    def get_bom() -> Any:
        """The bill of materials, exactly as ``bill_of_materials`` builds it.

        Served raw rather than remapped: the browser used to keep a second, partial BOM
        implementation of its own (``ui/src/model/bom.ts``) that billed some families the
        engine did not and missed others, with nothing testing that the two agreed. This
        endpoint is what retires it — one implementation, one set of numbers.
        """
        from typehaus.takeoff.bom import bill_of_materials

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        return JSONResponse(bill_of_materials(state.model))

    @app.get("/detail")
    def get_detail(key: str) -> Any:  # key carries '|'/':' — a query param, not a path seg
        from typehaus.emit.draw.details import detail_payload

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        payload = detail_payload(state.model, key)
        if payload is None:
            return JSONResponse({"error": f"no detail {key!r}"}, status_code=404)
        return JSONResponse(payload)

    @app.post("/detail/notes")
    def append_detail_note(body: dict[str, Any]) -> Any:
        """Append a construction note to the detail's ``Transition.notes`` markdown.

        Markdown notes are house-authored prose, not plan elements, so the ``# haus:
        editable`` dialect guard does not apply. The write is gated instead by
        provenance: the target is the file the detail's own Transition references —
        never a client-supplied path — and must still resolve under the house's
        ``notes/`` directory (same sandbox philosophy as ``/underlay``).
        """
        from typehaus.emit.draw.details import derive_detail_slices

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        key = body.get("key")
        # Collapse all whitespace (incl. newlines) so a note cannot smuggle in extra
        # markdown structure — one note, one bullet.
        text = " ".join(str(body.get("text", "")).split())
        if not key or not text:
            return JSONResponse({"error": "key and text are required"}, status_code=400)
        derived = next((d for d in derive_detail_slices(state.model) if d.key == key), None)
        tr = derived.transition if derived is not None else None
        rel = getattr(tr, "notes", None) if tr is not None else None
        if not rel:
            return JSONResponse({"error": f"detail {key!r} has no notes file"},
                                status_code=404)
        notes_root = (state.house_dir / "notes").resolve()
        target = (state.house_dir / rel).resolve()
        if notes_root not in target.parents or target.suffix != ".md":
            return JSONResponse({"error": "notes path escapes the house notes directory"},
                                status_code=403)
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        sep = "" if not existing or existing.endswith("\n") else "\n"
        target.write_text(f"{existing}{sep}- {text}\n", encoding="utf-8")
        return JSONResponse({"ok": True,
                             "notes_markdown": target.read_text(encoding="utf-8")})

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
            result = state.apply_edit(ops, body.get("revision"))
        except RevisionMismatch as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except (WritebackError, ExternalEdit) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        await bus.broadcast({"type": "patched", "revision": result.revision,
                             "minted": result.minted_uids,
                             "undo": result.undo_depth, "redo": result.redo_depth})
        return JSONResponse({"revision": result.revision, "minted": result.minted_uids,
                             "undo": result.undo_depth, "redo": result.redo_depth})

    @app.post("/preview")
    def post_preview(body: dict[str, Any]) -> Any:
        """→ Phase 4: a live drag preview. Read-only reduced-resolve geometry for ``ops``
        against the current plan — no revision bump, no writeback, no checks. The client
        polls this while the mouse is down and commits with the real PATCH /plan on mouseup."""
        try:
            ops = [PatchOp.from_json(o) for o in body.get("ops", [])]
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        preview = state.preview(ops)
        if preview is None:
            return JSONResponse({"error": "ops cannot be previewed in memory"}, status_code=422)
        return JSONResponse(preview)

    @app.post("/macro/preview")
    def post_macro_preview(body: dict[str, Any]) -> Any:
        """→ Phase 4: the macro-request form of ``/preview`` — builds the same ops
        ``/macro`` would (e.g. move_nodes' dx/dy → per-node PatchOps) but only previews them,
        so a client dragging a node can reuse the macro request shape it already sends on
        mouseup instead of hand-building dialect PatchOps for a live overlay."""
        from typehaus.server.macros_api import build_macro_ops, MacroRequestError

        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        try:
            result = build_macro_ops(state.model.plan, body)
        except MacroRequestError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        preview = state.preview(result.ops)
        if preview is None:
            return JSONResponse({"error": "macro ops cannot be previewed in memory"},
                                status_code=422)
        return JSONResponse(preview)

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
            patch = state.apply_edit(result.ops, body.get("revision"))
        except RevisionMismatch as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except (WritebackError, ExternalEdit) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
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

    @app.get("/underlay/{asset_path:path}")
    def get_underlay(asset_path: str) -> Any:
        """Serve only configured project-reference files, never arbitrary local paths."""
        candidate = (state.house_dir / asset_path).resolve()
        root = _reference_root(state.house_dir)
        try:
            candidate.relative_to(root)
        except ValueError:
            return JSONResponse({"error": "underlay path escapes the project reference root"}, status_code=403)
        if not candidate.is_file():
            return JSONResponse({"error": "underlay file not found"}, status_code=404)
        return FileResponse(candidate)

    @app.get("/asset/{asset_path:path}")
    def get_placeable_asset(asset_path: str) -> Any:
        """Serve only project-local imported visual assets, never arbitrary house files."""
        roots = ((state.house_dir / "assets" / "placeables").resolve(),
                 (state.house_dir / "furniture" / "meshes").resolve())
        candidate = (state.house_dir / asset_path).resolve()
        if not any(root in candidate.parents for root in roots) or not candidate.is_file():
            return JSONResponse({"error": "asset not found"}, status_code=404)
        return FileResponse(candidate)

    @app.put("/underlays/calibrate")
    async def calibrate_underlay(body: dict[str, Any]) -> Any:
        """Persist a view-only underlay transform without touching authored plan geometry."""
        try:
            _write_underlay_calibration(state.house_dir / "preferences.toml", body)
        except (KeyError, TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        state.rebuild()
        await bus.broadcast({"type": "file-changed", "revision": state.revision(),
                             "ok": state.ok})
        return JSONResponse({"ok": state.ok})

    @app.post("/build")
    async def post_build() -> Any:
        state.rebuild()
        await bus.broadcast({"type": "build", "revision": state.revision()})
        return JSONResponse({"ok": state.ok, "revision": state.revision()})

    @app.post("/undo")
    async def post_undo() -> Any:
        return await _history(state, bus, undo=True)

    @app.post("/redo")
    async def post_redo() -> Any:
        return await _history(state, bus, undo=False)

    async def events(ws) -> None:
        await bus.connect(ws)
        try:
            while True:
                await ws.receive_text()  # keep-alive; server is push-only
        except WebSocketDisconnect:
            bus.disconnect(ws)

    # `from __future__ import annotations` stores the parameter annotation as the *string*
    # "WebSocket", and FastAPI resolves it against this module's globals — where the deferred
    # `fastapi` import above is invisible. Recent FastAPI leaves such a name as an unresolved
    # ForwardRef instead of raising, so an annotated `ws: WebSocket` silently degrades into a
    # required `ws` query parameter and every handshake is closed unaccepted (uvicorn: 403).
    # Binding the class object itself keeps the deferred import and the endpoint contract.
    events.__annotations__["ws"] = WebSocket
    app.websocket("/events")(events)

    # V6 — serve the compiled SPA (must be registered LAST so every API route above wins the
    # match; this GET catch-all only fires for paths no API route claimed).
    if ui_dist is not None:
        _mount_spa(app, ui_dist)

    return app


def _mount_spa(app: Any, ui_dist: Path) -> None:
    """Serve the compiled UI at ``/`` with a single-page-app fallback (V6).

    Real files under ``ui_dist`` (``index.html``, hashed ``assets/*``, the PWA tarballs, the
    service worker) are returned directly; any other GET path falls back to ``index.html`` so
    client-side routes deep-link. Paths that escape ``ui_dist`` (``..`` traversal) 404.
    """
    from fastapi.responses import FileResponse, JSONResponse

    root = ui_dist.resolve()
    index = root / "index.html"

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> Any:
        if full_path:
            candidate = (root / full_path).resolve()
            if candidate.is_file() and (candidate == root or root in candidate.parents):
                return FileResponse(candidate)
        if index.is_file():
            return FileResponse(index, media_type="text/html")
        return JSONResponse(
            {"error": "UI not built — run `npm run build` in ui/ to produce ui/dist"},
            status_code=404,
        )


def _reference_root(house_dir: Path) -> Path:
    """A checkout may keep reference drawings beside ``houses/``; standalone houses stay local."""
    return house_dir.parent.parent if house_dir.parent.name == "houses" else house_dir


def _write_underlay_calibration(preferences_path: Path, body: dict[str, Any]) -> None:
    """Replace one repeated TOML underlay table while preserving unrelated preferences.

    Underlays are a deliberately small, schema-owned TOML surface.  Rewriting just the matched
    table avoids introducing a general-purpose TOML formatter into the source-writeback path.
    """
    path = str(body["path"])
    storey = str(body["storey"])
    numeric_keys = ("origin_x_m", "origin_y_m", "width_m", "height_m", "rotation_deg", "opacity")
    values = {key: float(body[key]) for key in numeric_keys}
    if values["width_m"] <= 0 or values["height_m"] <= 0 or not 0 < values["opacity"] <= 1:
        raise ValueError("underlay width/height must be positive and opacity must be in (0, 1]")
    lines = preferences_path.read_text().splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.strip() == "[[underlay]]"]
    for start in starts:
        end = next((index for index in range(start + 1, len(lines))
                    if lines[index].lstrip().startswith("[")), len(lines))
        fields = {}
        for line in lines[start + 1:end]:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip().strip('"')
        if fields.get("path") != path or fields.get("storey") != storey:
            continue
        replacement = ["[[underlay]]\n", f'path = "{path}"\n', f'storey = "{storey}"\n']
        replacement.extend(f"{key} = {values[key]:.8g}\n" for key in numeric_keys)
        lines[start:end] = replacement
        preferences_path.write_text("".join(lines))
        return
    raise ValueError(f"configured underlay not found for {storey}: {path}")


async def _history(state: ProjectState, bus: EventBus, undo: bool) -> Any:
    from fastapi.responses import JSONResponse

    try:
        result = state.history(undo=undo)
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)
    await bus.broadcast({"type": "undo" if undo else "redo", "revision": result.revision,
                         "undo": result.undo_depth, "redo": result.redo_depth})
    return JSONResponse({"revision": result.revision,
                         "undo": result.undo_depth, "redo": result.redo_depth})


async def _watch(state: ProjectState, bus: EventBus) -> None:
    """Watch plan source; on an external edit, seal the journal, rebuild, and notify (< 2 s)."""
    from watchfiles import awatch

    # Watch the stable house root rather than only an already-existing assets directory.
    # The event filter below excludes `out/` and other runtime byproducts, while allowing
    # the very first confirmed catalog import to create assets/placeables.json after serve.
    async for changes in awatch(state.house_dir):
        if not any(_is_project_source_change(state.house_dir, Path(path)) for _kind, path in changes):
            continue
        if state.coordinator.check_external_edit():
            state.rebuild()
            await bus.broadcast({"type": "file-changed",
                                 "revision": state.revision(),
                                 "ok": state.ok})


def _is_project_source_change(house_dir: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(house_dir.resolve())
    except ValueError:
        return False
    return relative.parts[:1] in {("plan",), ("assets",)}
