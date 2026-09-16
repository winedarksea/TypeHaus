"""``/sheets`` and ``/notes`` — the contractor reference the viewer's Documents hub reads.

Its own module because ``server/app.py`` is already at the file-size limit and because
these routes share nothing with the editing loop: both are read-only, neither touches the
coordinator, and one of them serves a file the CLI wrote rather than anything the server
computes.

The permit set is deliberately *not* composed on demand. ``haus print`` is gated on the
permit checklist; a route that rendered a set would be a second door around that gate. So
the server serves what ``haus print`` left in ``out/``, and says plainly when nothing is
there.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: The only PDFs this server will hand out, by name. All four are ``haus print`` outputs
#: — two papers times two sets (``--set full`` writes its own file rather than overwriting
#: the submittal). Anything else under ``out/`` is not a drawing set and has no business
#: on this route.
ALLOWED_PDFS = ("permit_set.pdf", "permit_set_24x36.pdf",
                "permit_set_full.pdf", "permit_set_full_24x36.pdf")

#: Manifests in preference order. The PERMIT set wins over the full one and ledger over
#: ARCH D: the Documents tab should open on what was submitted, not on the superset.
MANIFEST_NAMES = ("permit_set.json", "permit_set_24x36.json",
                  "permit_set_full.json", "permit_set_full_24x36.json")


def find_manifest(house_dir: Path) -> tuple[Path, dict[str, Any]] | None:
    """The newest-printed set's manifest, or ``None`` when ``haus print`` has not run."""
    out = house_dir / "out"
    for name in MANIFEST_NAMES:
        path = out / name
        if path.is_file():
            try:
                return path, json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
    return None


#: What ``haus render`` leaves in ``out/render/``, with the type each is served as.
RENDER_FORMATS = {".png": "image/png", ".svg": "image/svg+xml",
                  ".psd": "image/vnd.adobe.photoshop"}

#: Stem prefix -> menu group. First match wins; anything else is "other".
_RENDER_GROUPS = (("plan_", "plan"), ("elev_", "elevation"), ("section_", "section"),
                  ("site_", "site"), ("detail_", "detail"))


def list_renders(house_dir: Path) -> list[dict[str, Any]]:
    """Every rendered image in ``out/render/``, one entry per stem with its formats."""
    root = house_dir / "out" / "render"
    if not root.is_dir():
        return []
    by_stem: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(root.iterdir()):
        if path.suffix in RENDER_FORMATS and path.is_file():
            by_stem.setdefault(path.stem, []).append(
                {"name": path.name, "format": path.suffix[1:], "bytes": path.stat().st_size})
    return [{"stem": stem,
             "group": next((g for prefix, g in _RENDER_GROUPS if stem.startswith(prefix)),
                           "other"),
             "files": files}
            for stem, files in sorted(by_stem.items())]


def register_documents_routes(app: Any, state: Any) -> None:
    """Register the read-only document routes on ``app``.

    Called from ``create_app`` **before** the SPA catch-all: ``_mount_spa`` claims
    ``/{full_path:path}``, so a route registered after it is never reached.
    """
    from fastapi.responses import FileResponse, JSONResponse

    from typehaus.emit.notes_index import notes_index, read_note

    @app.get("/sheets")
    def get_sheets() -> Any:
        """The printed set's table of contents: number, title, page, and the issue stamp."""
        found = find_manifest(state.house_dir)
        if found is None:
            return JSONResponse({"error": "no permit set — run `haus print`"},
                                status_code=404)
        return JSONResponse(found[1])

    @app.get("/sheets/{name}")
    def get_sheet_pdf(name: str) -> Any:
        """One of the two permit-set PDFs, by exact name. An allow-list, not a sandbox
        check: there is no path arithmetic to get wrong."""
        if name not in ALLOWED_PDFS:
            return JSONResponse({"error": f"unknown sheet file {name!r}"}, status_code=404)
        path = state.house_dir / "out" / name
        if not path.is_file():
            return JSONResponse({"error": f"{name} not printed — run `haus print`"},
                                status_code=404)
        return FileResponse(path, media_type="application/pdf")

    @app.get("/renders")
    def get_renders() -> Any:
        """What ``haus render`` left, for download. Empty, not a 404, when nothing ran."""
        return JSONResponse({"renders": list_renders(state.house_dir)})

    @app.get("/renders/{name}")
    def get_render(name: str) -> Any:
        """One rendered image as an attachment. Allow-listed by the directory's own
        listing, so a name that is not a file in it never becomes a path."""
        listed = {f["name"] for r in list_renders(state.house_dir) for f in r["files"]}
        if name not in listed:
            return JSONResponse({"error": f"no rendered image {name!r} — run `haus render`"},
                                status_code=404)
        path = state.house_dir / "out" / "render" / name
        return FileResponse(path, media_type=RENDER_FORMATS[path.suffix], filename=name)

    @app.get("/notes")
    def get_notes() -> Any:
        """Every design/product note in the house, with the sheets each one prints on."""
        if state.model is None:
            return JSONResponse({"error": "model does not resolve"}, status_code=409)
        entries = notes_index(state.house_dir, state.model)
        return JSONResponse({"notes": [entry.to_dict() for entry in entries]})

    @app.get("/notes/{relative:path}")
    def get_note(relative: str) -> Any:
        """One note's markdown. Sandboxed to ``brief.md`` and ``notes/**.md``."""
        text = read_note(state.house_dir, relative)
        if text is None:
            # One status for "outside the sandbox" and one for "inside it but absent": a
            # 404 on an escaping path would confirm what does and does not exist above the
            # house directory, which is exactly what the sandbox is for.
            root = state.house_dir.resolve()
            target = (root / relative).resolve()
            inside = target == root / "brief.md" or (root / "notes") in target.parents
            if not inside or target.suffix != ".md":
                return JSONResponse({"error": "path escapes the house notes directory"},
                                    status_code=403)
            return JSONResponse({"error": f"no note {relative!r}"}, status_code=404)
        return JSONResponse({"path": relative, "markdown": text})
