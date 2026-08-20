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
      // The three takeoff reads. Omitted until 2026-08-20, which meant the BOM and
      // Estimate readers fetched the SPA fallback under `npm run dev` — index.html with
      // status 200, dying in res.json() as "Unexpected token '<'".
      "/bom": ENGINE,
      "/costs": ENGINE,
      "/tasks": ENGINE,
      "/preview": ENGINE,
      "/asset": ENGINE,
      "/underlay": ENGINE,
      "/events": { target: ENGINE, ws: true },
    },
  },
  build: {
    outDir: "dist",
    // Off by default: landing/build-site.mjs copies ui/dist wholesale to the public site, so
    // `sourcemap: true` was publishing a 3.79 MB .js.map — bigger than everything else the
    // site ships put together — to every visitor. Set HAUS_SOURCEMAP=1 for a build you intend
    // to debug.
    sourcemap: process.env.HAUS_SOURCEMAP === "1",
    rollupOptions: {
      output: {
        // three.js is the one dependency big enough to be worth its own chunk, and it is
        // reached only through the lazily-imported 3D panel (components/Panel3DLazy.tsx), so
        // naming it here keeps it out of the entry chunk *and* lets it stay cached across
        // deploys that only touch app code.
        manualChunks: { three: ["three"] },
      },
    },
  },
});
