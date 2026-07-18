# M4 — Offline PWA (Gated)

**Purpose:** lower priority by decision (#15). The `EngineClient` boundary (→ 21 §Stack) and
location-independent house loading (→ 02 §Git topology) are the **only** obligations M1/M2
carry for this; everything else waits behind an explicit go/no-go gate. The local FastAPI
mode remains the primary, fully-supported path regardless of outcome.

## Workpackages

- **WP4.1 Wasm feasibility spike.** The engine's wasm-hostile dependencies are exactly two —
  **IfcOpenShell** (C++ CPython extension; no official pyodide build today) and **libcst**
  (native Rust parser). Everything else either ships in the pyodide distribution (shapely,
  scipy, numpy, matplotlib, pydantic-core) or is pure Python installable via micropip (ezdxf,
  typer, trimesh). Spike outcome is one of:
  - **(a) Full go:** the full engine runs under pyodide (a workable IfcOpenShell wasm build
    exists) → proceed to WP4.2.
  - **(b) Degraded offline mode:** resolve/checks/drawing-IR/DXF/PDF/model.json all run
    in-browser; the 3D panel renders the **glTF (.glb) emitted straight from `ResolvedModel`**
    — which under #51 is already the UI's primary render artifact, so this mode reuses the
    M2 emitter as-is; IFC binary emit and libcst writeback are marked "requires local
    install" → go if still judged useful. The IFC-as-interchange / glTF-as-render split is
    already in place from M2 (#51), so M4 inherits it for free.
  - **(c) Neither viable → skip**, per the locked decision. Document the finding and close
    the milestone.
- **WP4.2 PWA packaging** (only on go): service worker + offline asset caching, pyodide
  engine in a Web Worker behind `PyodideEngineClient` (the second implementation of the
  `EngineClient` interface — no editor code changes by construction), house-directory access
  via the File System Access API, install prompt.

## Acceptance

Gate decision recorded (go / degraded / skip) with the spike evidence; on any "go", the M2
Playwright drawing script passes against `PyodideEngineClient` offline.

## Gate decision

**Recorded 2026-07-18 → (b) Degraded offline mode, GO.** Spike evidence and the full
dependency-reachability audit are in `40-m4-gate.md`. Summary: the `.glb` render path (#51) is
pure stdlib and the only wasm blockers — libcst, ifcopenshell, pyproj — are confined to the
writeback and IFC-emit seams, so resolve/checks/model.json/glb all run offline in-browser while
mutation and IFC export are marked "requires local install". Implemented in WP4.2 below.
