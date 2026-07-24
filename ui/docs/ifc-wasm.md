# Client-side IFC export (ifcopenshell-wasm)

The offline PWA can run the whole engine in-browser via pyodide, but IFC export needs
**ifcopenshell**, which has no standard pyodide wheel. The runtime plumbing is fully wired; the
only missing piece is the wheel itself.

## What's needed

Client-side IFC export needs an **ifcopenshell wheel built for pyodide/wasm** (an
`ifcopenshell*.whl` targeting the pyodide/emscripten platform). This wheel is **NOT bundled in
this repo and NOT produced by any build tooling here** — it must be sourced or built externally.
**Producing/building that wheel is out of scope.**

- The native server-side engine uses **ifcopenshell 0.8.4** (see `haus serve`).
- The experimental **ifcopenshell-wasm** build is the reference for a pyodide-compatible artifact.

## How to activate it

Once you have a wheel, either (or both) of these wires it in:

1. **Vendor it (recommended).** Drop the `.whl` at `ui/vendor/`:

   ```
   ui/vendor/ifcopenshell-<version>-<pyodide-tag>.whl
   ```

   `scripts/build-pwa-assets.mjs` copies any `ui/vendor/ifcopenshell*.whl` into `ui/public/`
   during `prebuild`, so it lands in `ui/dist/` and is served **same-origin** by `haus serve`'s
   SPA static mount. Then set `VITE_IFC_WASM_URL` to its same-origin path (e.g.
   `/ifcopenshell-<version>-<pyodide-tag>.whl`).

2. **Point at a URL.** Set the build-time env var `VITE_IFC_WASM_URL` to any URL where the wheel
   is hosted (must be reachable/CORS-OK from the app origin).

`ui/vendor/` is not tracked in the repo; the copy step is a **silent no-op** when no wheel is
present, so the build succeeds unchanged with nothing vendored.

## What happens at runtime

With `VITE_IFC_WASM_URL` set, the already-wired path activates automatically on the first IFC
export:

```
PyodideEngineClient.getArtifact("ifc")
  → worker ensureIfc(): fetch typehaus-ifc-ext.tar → unpackArchive
    → loadPackage("micropip") → micropip.install(ifcWasmUrl)
    → replace the blocking ifcopenshell stub → engine.enable_ifc()
```

Without a wheel and without `VITE_IFC_WASM_URL`, nothing changes: `enable_ifc()` still sees the
blocking `ifcopenshell` stub and raises `RequiresLocalInstall`, which the UI surfaces as the
existing `OfflineUnsupported` "run `haus serve` locally" degradation. IFC export is the only
affected feature; the rest of the offline engine (resolve → checks → model.json → `.glb`) is
unaffected.
