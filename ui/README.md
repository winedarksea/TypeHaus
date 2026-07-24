# Type:Haus UI (M2)

React + TypeScript + Vite editor — the local web app half of M2 (→ `docs/plan/21-m2-ui.md`,
`21b-m2-editor.md`). An SVG 2D floorplan editor + a three.js 3D panel, both pure views over
the engine's `model.json`. **The server owns all geometry math**; the UI is a view + patch
emitter (→ 20).

## Architecture

- **`src/engine/EngineClient.ts`** — the single typed boundary for all engine access
  (`getModel/getChecks/patchPlan/build/undo/redo/getArtifact/events`, #15). The M2
  implementation is `HttpEngineClient` (fetch + WebSocket). `PyodideEngineClient` slots in for
  the offline PWA (→ 40, M4) without touching editor code.
- **`src/engine/pyodide/`** — the offline engine host (M4 WP4.2, gate outcome b). `worker.ts`
  loads pyodide + pydantic + shapely, unpacks the bundled engine tarball
  (`public/typehaus-engine.tar`, built by `scripts/build-pwa-assets.mjs`), and runs
  `bootstrap.py`, which stubs the three wasm-hostile deps (libcst/ifcopenshell/pyproj) and
  serves resolve → checks → model.json → `.glb`. Editing (libcst writeback) and IFC export are
  refused offline with a clear "requires local install" — the local `haus serve` stays the
  primary editing path (#15).
- **`src/pwa/register.ts`** — service-worker registration, online/offline tracking, and the
  `beforeinstallprompt` install flow. The SW (`public/sw.js`) precaches the app shell and
  cache-firsts the pyodide CDN so the app boots and resolves fully offline after first load.
- **`src/model/`** — `types.ts` mirrors the `model.json` contract; `geometry.ts` holds
  presentation-only helpers (SI→px, ft-in formatting/parsing, node/extents derivation).
- **`src/nordic/palette.ts`** — the Nordic preset mirror of `emit/draw/palette.py` (#24),
  shared by the 2D fills, 3D materials, and the section card.
- **`src/state/store.ts`** — the zustand store; the editing loop (render → edit → patch →
  rebuild → WebSocket push → re-render).
- **`src/components/`** — `Canvas2D` (SVG editor: framed studs + layer hatching, tap-select,
  pinch/drag pan-zoom, open-end markers, ft-in keypad dimension edits), `Panel3D`
  (three.js scene built from `model.json` with the Nordic passes; click → 2D cross-highlight
  + `file:line` provenance), `Sidebar` (assembly inspector + section card + findings),
  `ExtentsHUD`, `ConflictBanner` (#30), `FtInKeypad`.

## Develop

```bash
npm install
# In another terminal, run the engine on the starter house:
#   PYTHONPATH=packages/engine/src python -m typehaus serve houses/starter --port 8000
npm run dev            # proxies /model,/plan,/events,… to $HAUS_ENGINE (default :8000)
```

`npm run build` emits `dist/`, distributed pre-built inside the wheel so
`pip install typehaus && haus serve` works without node (→ 02). `npm run typecheck` is the CI
gate (`tsc -b --noEmit`, strict).

## Offline PWA (M4)

The built app is an installable PWA. When the engine is unreachable, on a File System
Access-capable browser the engine-error screen offers **Open house folder (offline)**: pick any
Type:Haus house directory and the pyodide worker resolves it in-browser — view, checks, and 3D,
no server. Editing routes back to `haus serve`. `scripts/build-pwa-assets.mjs` (run by
`prebuild`) bundles the `typehaus` + `library` sources into `public/typehaus-engine.tar`.

The degraded-mode path is verified end-to-end against real pyodide in
`../plans/40-m4-gate.md` (load `houses/starter` → model.json + checks + valid `.glb`).

### Client-side IFC export

IFC export is the one offline feature still gated on an external artifact: an ifcopenshell wheel
built for pyodide/wasm, which is not bundled here. The runtime path is fully wired — drop a wheel
at `ui/vendor/` (the build copies it to `public/`) and/or set `VITE_IFC_WASM_URL`, and it
activates automatically; without it the export cleanly degrades. Sourcing/building the wheel is
out of scope. See [docs/ifc-wasm.md](docs/ifc-wasm.md).
