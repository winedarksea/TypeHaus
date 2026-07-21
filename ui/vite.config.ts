import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies engine calls to `haus serve` (default :8000) so the
// EngineClient can use same-origin relative paths (→ 21 §EngineClient boundary).
declare const process: { env: Record<string, string | undefined> };
const ENGINE = process.env.HAUS_ENGINE ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  // Built assets ship inside the wheel and are served by `haus serve`, so use a
  // relative base for portability.
  base: "./",
  server: {
    // Keep this list in sync with the routes registered in `create_app`
    // (packages/engine/src/typehaus/server/app.py): a POST to an un-proxied
    // path hits Vite itself and 404s, surfacing as a "Not found" toast. Vite
    // matches by path prefix, so `/macro` covers `/macro/preview`, `/model`
    // covers `/model.glb`, and `/underlay` covers `/underlays/calibrate`.
    proxy: {
      "/model": ENGINE,
      "/checks": ENGINE,
      "/details": ENGINE,
      "/detail": ENGINE,
      "/plan": ENGINE,
      "/build": ENGINE,
      "/undo": ENGINE,
      "/redo": ENGINE,
      "/model.ifc": ENGINE,
      "/macro": ENGINE,
      "/preview": ENGINE,
      "/asset": ENGINE,
      "/underlay": ENGINE,
      "/events": { target: ENGINE, ws: true },
    },
  },
  build: { outDir: "dist", sourcemap: true },
});
