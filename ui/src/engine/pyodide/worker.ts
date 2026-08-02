/// <reference lib="webworker" />
// Pyodide Web Worker — the offline engine host (→ 40 WP4.2). Loads pyodide + pydantic + shapely,
// unpacks the bundled engine tarball onto sys.path, runs the bootstrap, then serves RPC:
// loadHouse / model / checks / glb / ifc. IFC export lazily unpacks the packaged extension
// tarball (see ensureIfc); without a bundled ifcopenshell-wasm wheel it surfaces a precise
// "requires local install" degradation rather than a silent failure.

import bootstrapSrc from "./bootstrap.py?raw";

const PYODIDE_VERSION = "0.26.2";

interface InitMsg {
  id: number;
  type: "init";
  pyodideIndexUrl: string;
  engineTarUrl: string;
  // Optional IFC extension (loaded lazily on the first IFC export, not at boot):
  ifcExtTarUrl?: string; // typehaus-ifc-ext.tar (the emit/ifc sources excluded from core)
  ifcWasmUrl?: string; // ifcopenshell-wasm wheel to micropip-install, when available
}
interface LoadHouseMsg {
  id: number;
  type: "loadHouse";
  root: string;
  files: Record<string, string>;
}
interface CallMsg {
  id: number;
  type: "model" | "checks" | "bom" | "costs" | "glb" | "ifc" | "detailIndex" | "undo" | "redo";
}
interface DetailMsg {
  id: number;
  type: "detail";
  key: string;
}
interface PatchMsg {
  id: number;
  type: "patch";
  ops: unknown[];
  revision: string | null;
}
type InMsg = InitMsg | LoadHouseMsg | CallMsg | DetailMsg | PatchMsg;

let pyodide: any = null;
let engine: any = null;
let ready: Promise<void> | null = null;
// IFC extension: URLs captured at init, loaded lazily (once) on the first IFC export.
let ifcExtTarUrl: string | undefined;
let ifcWasmUrl: string | undefined;
let ifcReady: Promise<void> | null = null;

async function init(msg: InitMsg): Promise<void> {
  ifcExtTarUrl = msg.ifcExtTarUrl;
  ifcWasmUrl = msg.ifcWasmUrl;
  const { loadPyodide } = await import(
    /* @vite-ignore */ `${msg.pyodideIndexUrl}pyodide.mjs`
  );
  pyodide = await loadPyodide({ indexURL: msg.pyodideIndexUrl });
  // pydantic (+ pydantic-core) and shapely ship in the pyodide distribution — the only
  // third-party imports the offline compute path reaches.
  await pyodide.loadPackage(["micropip", "pydantic", "shapely"]);

  // Unpack the engine source tree onto sys.path.
  const res = await fetch(msg.engineTarUrl);
  if (!res.ok) throw new Error(`engine tarball ${res.status} @ ${msg.engineTarUrl}`);
  const buf = await res.arrayBuffer();
  pyodide.unpackArchive(buf, "tar", { extractDir: "/engine" });
  pyodide.runPython("import sys; sys.path.insert(0, '/engine')");

  // Run the bootstrap; ENGINE lives in the pyodide global namespace.
  await pyodide.runPythonAsync(bootstrapSrc);
  engine = pyodide.globals.get("ENGINE");
}

function ensureReady(): Promise<void> {
  if (!ready) throw new Error("worker not initialized");
  return ready;
}

// Lazily wire the optional IFC export path (runs at most once, on the first IFC export):
//  1. fetch + unpack typehaus-ifc-ext.tar — the `typehaus/emit/ifc` sources the core bundle
//     excludes — onto the same /engine sys.path,
//  2. when an ifcopenshell-wasm wheel URL is configured, micropip-install it and drop the
//     bootstrap's blocking `ifcopenshell` stub so the real module is imported,
//  3. assert a real ifcopenshell is present (engine.enable_ifc raises a documented degradation
//     otherwise).
// If no wasm wheel is bundled, steps 1+3 still run: the emitter sources load, and the user gets
// a precise "requires the ifcopenshell-wasm module / run haus serve locally" message instead of
// a silent failure. Wiring the actual wasm wheel is the one remaining piece (see U9/40 notes).
async function ensureIfc(): Promise<void> {
  if (ifcReady) return ifcReady;
  ifcReady = (async () => {
    if (!ifcExtTarUrl) {
      throw new Error(
        "IFC export is not configured in this build (no typehaus-ifc-ext.tar) — run `haus serve` locally",
      );
    }
    const res = await fetch(ifcExtTarUrl);
    if (!res.ok) throw new Error(`IFC extension tarball ${res.status} @ ${ifcExtTarUrl}`);
    pyodide.unpackArchive(await res.arrayBuffer(), "tar", { extractDir: "/engine" });
    if (ifcWasmUrl) {
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip");
      try {
        await micropip.install(ifcWasmUrl);
      } finally {
        micropip.destroy?.();
      }
      // Drop the bootstrap's blocking ifcopenshell stub so the freshly installed real module
      // (and its submodules) are imported on next access.
      pyodide.runPython(
        "import sys\n" +
          "for _m in [m for m in sys.modules if m == 'ifcopenshell' or m.startswith('ifcopenshell.')]:\n" +
          "    del sys.modules[_m]\n",
      );
    }
    engine.enable_ifc(); // raises RequiresLocalInstall if no real ifcopenshell is present
  })().catch((err) => {
    ifcReady = null; // allow a later retry (e.g. after configuring a wheel URL)
    throw err;
  });
  return ifcReady;
}

async function handle(msg: InMsg): Promise<unknown> {
  switch (msg.type) {
    case "init": {
      ready = init(msg);
      await ready;
      return { ok: true, pyodide: PYODIDE_VERSION };
    }
    case "loadHouse": {
      await ensureReady();
      const filesProxy = pyodide.toPy(msg.files);
      try {
        const result = engine.load_house(msg.root, filesProxy);
        const out = result.toJs({ dict_converter: Object.fromEntries });
        result.destroy();
        return out;
      } finally {
        filesProxy.destroy();
      }
    }
    case "model": {
      await ensureReady();
      const d = engine.model_json();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    case "checks": {
      await ensureReady();
      const d = engine.findings_json();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    case "glb": {
      await ensureReady();
      const b = engine.glb_bytes();
      const bytes = b.toJs(); // Uint8Array
      b.destroy();
      return bytes;
    }
    case "ifc": {
      await ensureReady();
      await ensureIfc();
      const b = engine.ifc_bytes();
      const bytes = b.toJs(); // Uint8Array
      b.destroy();
      return bytes;
    }
    case "bom": {
      await ensureReady();
      const d = engine.bom_json();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    case "costs": {
      await ensureReady();
      const d = engine.costs_json();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    case "detailIndex": {
      await ensureReady();
      const d = engine.detail_index();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    case "detail": {
      await ensureReady();
      const d = engine.detail_payload(msg.key);
      if (d === undefined || d === null) return null;
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
    // Mutation surface — served by the pure-Python (libcst-free) writeback backend (U9).
    case "patch": {
      await ensureReady();
      const opsProxy = pyodide.toPy(msg.ops);
      try {
        const d = engine.patch(opsProxy, msg.revision);
        const out = d.toJs({ dict_converter: Object.fromEntries });
        d.destroy();
        return out;
      } finally {
        opsProxy.destroy();
      }
    }
    case "undo":
    case "redo": {
      await ensureReady();
      const d = msg.type === "undo" ? engine.undo() : engine.redo();
      const out = d.toJs({ dict_converter: Object.fromEntries });
      d.destroy();
      return out;
    }
  }
}

self.onmessage = async (e: MessageEvent<InMsg>) => {
  const msg = e.data;
  try {
    const result = await handle(msg);
    // Transfer the glb bytes to avoid a copy.
    const transfer =
      result instanceof Uint8Array ? [result.buffer] : [];
    (self as unknown as Worker).postMessage(
      { id: msg.id, ok: true, result },
      transfer,
    );
  } catch (err) {
    (self as unknown as Worker).postMessage({
      id: msg.id,
      ok: false,
      error: (err as Error).message ?? String(err),
    });
  }
};
