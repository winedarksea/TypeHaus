# M4 — WP4.1 wasm feasibility spike: gate decision

**Decision: (b) Degraded offline mode — GO.** Recorded 2026-07-18.

## Method

The engine was audited for wasm-hostile dependencies by tracing actual imports
(`grep -rln` per package) and by exercising the offline compute path headlessly against
`houses/starter` (load_plan → resolve → `model_to_dict` → `emit_glb`). Pyodide 0.26.x package
availability was checked against the official distribution + micropip (pure-python wheels).

## Findings — dependency reachability

| Dep | Native? | In pyodide? | Reached by | Verdict |
|---|---|---|---|---|
| pydantic / pydantic-core | native (Rust) | **yes** (pyodide dist) | schema, everywhere | ✅ available |
| shapely | native (GEOS) | **yes** (pyodide dist) | `resolve/rooms.py` only | ✅ available |
| numpy / scipy | native | **yes** (pyodide dist) | `diff/matcher.py` only | ✅ (diff is offline-optional) |
| matplotlib | native | **yes** (pyodide dist) | `emit/draw` (PDF/section) | ✅ available |
| typer / rich / ezdxf | pure python | via micropip | CLI, DXF | ✅ available |
| **libcst** | native (Rust) | **no wheel** | `source/writeback.py`, `coordinator` | ❌ blocks *mutation* |
| **ifcopenshell** | native (C++) | **no wheel** | `emit/ifc` only | ❌ blocks *IFC emit* |
| **pyproj** | native (PROJ) | **no wheel** | `emit/ifc` only (georef) | ❌ blocks *IFC emit* |

Key structural facts that make degraded mode clean:

- **The glTF (.glb) emitter is pure stdlib** (`base64`, `json`, `struct`) — the primary render
  artifact under #51 needs *nothing* wasm-hostile. Verified: `emit_glb(starter)` → 13,724 bytes
  with only the pyodide-native pydantic/shapely present.
- The three blockers (**libcst, ifcopenshell, pyproj**) are each reached by exactly one seam —
  writeback and IFC emit — and never by the resolve/checks/model.json/glb path.

## Outcome

- **(a) Full go — not available today.** IfcOpenShell and libcst have no pyodide build; pyproj
  likewise. IFC binary emit and libcst writeback therefore require a local install. Revisit if
  an IfcOpenShell wasm build + a pure-python-or-wasm libcst appears.
- **(b) Degraded offline mode — chosen, GO.** In-browser, offline, via `PyodideEngineClient`
  (pyodide in a Web Worker): **resolve, checks, model.json, and the glTF 3D render all run**;
  the 3D panel renders the `.glb` emitted straight from `ResolvedModel` (#51), reusing the M2
  emitter unchanged. **Marked "requires local FastAPI install":** plan mutation (PATCH /plan,
  macros, undo/redo — libcst writeback) and IFC binary export. The PWA opens a house directory
  read-only via the File System Access API and gives a fully navigable, checkable, 3D house
  offline; editing routes the user back to the local `haus serve` path, which remains the
  primary, fully-supported mode (decision #15).

## Acceptance note

Full-go acceptance ("the M2 Playwright drawing script passes against `PyodideEngineClient`
offline") requires the mutation path, which is libcst-gated and thus deferred with full-go.
Degraded-mode acceptance is: the PWA loads `houses/starter` offline and renders model.json +
checks + the `.glb` 3D view with no server running. `PyodideEngineClient` surfaces mutation and
IFC calls as an explicit "requires local install" degradation (never a silent failure).

**Verified 2026-07-18 against real pyodide 0.26.2 (wasm).** A headless harness mirroring the
Web Worker (`ui/src/engine/pyodide/{worker.ts,bootstrap.py}`) loaded the bundled engine
tarball, then `houses/starter`, entirely in pyodide:

```
loadHouse ok=true findings=0
model: walls=8 rooms=2 openings=3 ok=true
checks: 0 findings
glb: 13724 bytes, magic=glTF
ifc/pyproj refused offline: RequiresLocalInstall (…run `haus serve` locally)
```

The only third-party wheels pulled were pydantic, pydantic-core, shapely, numpy (+ their pure
deps) — all from the pyodide distribution. libcst/ifcopenshell/pyproj were never fetched: the
stub lets `typehaus.source` import, and `rebuild()` loads the manifest via a pure `exec` path
(no dialect-lint/provenance), so the resolved model is identical to the server's.
</content>
