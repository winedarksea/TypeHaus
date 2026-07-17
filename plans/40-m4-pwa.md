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
  typer). Spike outcome is one of:
  - **(a) Full go:** the full engine runs under pyodide (a workable IfcOpenShell wasm build
    exists) → proceed to WP4.2.
  - **(b) Degraded offline mode:** resolve/checks/drawing-IR/DXF/PDF/model.json all run
    in-browser; the 3D panel renders a **glTF (.glb) emitted straight from `ResolvedModel`**
    (trimesh or hand-rolled — the resolver already owns the solids; .glb is native to the web
    and fast) rather than parsing IFC; IFC binary emit and libcst writeback are marked
    "requires local install" → go if still judged useful. This makes IFC purely the
    *interchange* artifact and glTF the *render* artifact — a split worth having anyway
    (it is also risk 4's fallback (b), → 02 §Risk register, so the glTF emitter pays for
    itself even if M4 is skipped).
  - **(c) Neither viable → skip**, per the locked decision. Document the finding and close
    the milestone.
- **WP4.2 PWA packaging** (only on go): service worker + offline asset caching, pyodide
  engine in a Web Worker behind `PyodideEngineClient` (the second implementation of the
  `EngineClient` interface — no editor code changes by construction), house-directory access
  via the File System Access API, install prompt.

## Acceptance

Gate decision recorded (go / degraded / skip) with the spike evidence; on any "go", the M2
Playwright drawing script passes against `PyodideEngineClient` offline.
