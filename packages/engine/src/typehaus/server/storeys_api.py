"""``POST /storeys``, ``GET /project``, ``POST /project/new`` — house-level editing routes.

Adding a floor writes a new loader-discovered storey module (``source/storey_modules.py``).
Creating a file is not an undoable op: the journal is sealed first, exactly as for an external
edit, and only the optional layout copy that follows is one undoable entry. The server stays
single-house: ``/project/new`` scaffolds a directory and hands back the ``haus serve`` command.
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

EXTRA_CAPABILITIES = ("add_storey", "project_new", "saved_events")


class StoreyRequestError(ValueError):
    """The add-floor request is invalid (422)."""


def capabilities() -> list[str]:
    from typehaus.server.macros_api import _DISPATCH

    return sorted({*_DISPATCH, *EXTRA_CAPABILITIES})


def add_storey(state: Any, body: dict[str, Any]) -> Any:
    """Write ``plan/storeys/<tag>.py``, seal the journal and rebuild. Blocking."""
    from typehaus.model.ids import new_uid
    from typehaus.source.coordinator import _atomic_write
    from typehaus.source.macros_common import MacroError, _as_length, _round_len
    from typehaus.source.storey_modules import TAG_RE, render_storey_module

    tag = str(body.get("tag") or "")
    if not TAG_RE.match(tag):
        raise StoreyRequestError(f"storey tag {tag!r} must match {TAG_RE.pattern}")
    try:
        elevation = _round_len(_as_length(body["elevation"]).meters).to_source()
        ceiling = _round_len(_as_length(body["ceiling_height"]).meters).to_source()
    except KeyError as exc:
        raise StoreyRequestError(f"missing {exc.args[0]!r}") from exc
    except (MacroError, ValueError, TypeError) as exc:
        raise StoreyRequestError(f"bad length: {exc}") from exc
    path = state.house_dir / "plan" / "storeys" / f"{tag}.py"
    with state._lock:
        if state.plan is None:
            raise StoreyRequestError("model does not load; fix it before adding a floor")
        if state.plan.storey(tag) is not None or path.exists():
            raise StoreyRequestError(f"storey {tag!r} already exists")
        copy_from = body.get("copy_from")
        if copy_from and state.plan.storey(copy_from) is None:
            raise StoreyRequestError(f"no storey {copy_from!r} to copy from")
        state._flush_writes()
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(path, render_storey_module(tag, elevation, ceiling, new_uid()))
        state.coordinator.check_external_edit()
        state.rebuild()
        state._undo_depth, state._redo_depth = state.coordinator._journal.depth()
        if not copy_from or state.plan is None or state.plan.storey(tag) is None:
            return None
        return state.apply_macro({"macro": "copy_storey_layout", "storey": tag,
                                  "from": copy_from})


def new_project(body: dict[str, Any]) -> dict[str, Any]:
    """Scaffold a house into a new or empty directory; never switches the live state."""
    from typehaus.cli.scaffold import TEMPLATES, ScaffoldError, scaffold_house

    raw = str(body.get("directory") or "").strip()
    if not raw:
        raise StoreyRequestError("missing 'directory'")
    directory = Path(raw).expanduser().resolve()
    template = str(body.get("template") or "starter")
    if template not in TEMPLATES:
        raise StoreyRequestError(f"unknown template {template!r} ({' | '.join(TEMPLATES)})")
    if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
        raise StoreyRequestError(f"{directory} exists and is not an empty directory")
    try:
        written = scaffold_house(directory, str(body.get("name") or "My House"), template)
    except ScaffoldError as exc:
        raise StoreyRequestError(str(exc)) from exc
    return {"house_dir": str(directory),
            "written": [p.relative_to(directory).as_posix() for p in written],
            "command": f"haus serve {shlex.quote(str(directory))}"}


def register_storeys_routes(app: Any, state: Any, bus: Any) -> None:
    """Register before the SPA catch-all (see ``register_documents_routes``)."""
    from fastapi.responses import JSONResponse
    from starlette.concurrency import run_in_threadpool

    from typehaus.server.macros_api import MacroRequestError
    from typehaus.source.coordinator import ExternalEdit
    from typehaus.source.ops import WritebackError

    @app.get("/project")
    def get_project() -> Any:
        from typehaus.cli.scaffold import TEMPLATES

        plan = state.plan
        return JSONResponse({
            "house_dir": str(state.house_dir),
            "name": plan.project.name if plan is not None else state.house_dir.name,
            "revision": state.revision(),
            "templates": list(TEMPLATES),
            "capabilities": capabilities(),
        })

    @app.post("/project/new")
    async def post_project_new(body: dict[str, Any]) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(new_project, body))
        except StoreyRequestError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/storeys")
    async def post_storeys(body: dict[str, Any]) -> Any:
        try:
            copied = await run_in_threadpool(add_storey, state, body)
        except StoreyRequestError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except (MacroRequestError, WritebackError, ExternalEdit) as exc:
            # The floor exists; only the copy failed. Tell the client both.
            await bus.broadcast({"type": "file-changed", "revision": state.revision(),
                                 "ok": state.ok})
            return JSONResponse({"error": f"floor added, layout copy failed: {exc}",
                                 "tag": body.get("tag"), "revision": state.revision()},
                                status_code=422)
        await bus.broadcast({"type": "file-changed", "revision": state.revision(),
                             "ok": state.ok})
        payload: dict[str, Any] = {"tag": body.get("tag"), "revision": state.revision(),
                                   "ok": state.ok}
        if copied is not None:
            result, patch = copied
            payload.update(undo=patch.undo_depth, redo=patch.redo_depth,
                           impacts=[impact.to_json() for impact in result.impacts])
        return JSONResponse(payload)
