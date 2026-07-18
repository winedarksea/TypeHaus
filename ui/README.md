# Type:Haus UI (M2)

React + TypeScript + Vite editor — the local web app half of M2 (→ `docs/plan/21-m2-ui.md`,
`21b-m2-editor.md`). An SVG 2D floorplan editor + a three.js 3D panel, both pure views over
the engine's `model.json`. **The server owns all geometry math**; the UI is a view + patch
emitter (→ 20).

## Architecture

- **`src/engine/EngineClient.ts`** — the single typed boundary for all engine access
  (`getModel/getChecks/patchPlan/build/undo/redo/getArtifact/events`, #15). The M2
  implementation is `HttpEngineClient` (fetch + WebSocket). A `PyodideEngineClient` can slot
  in for the offline PWA (→ 40) without touching editor code.
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
