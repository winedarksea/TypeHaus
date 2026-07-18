/// <reference lib="webworker" />
// Pyodide Web Worker — the offline engine host (→ 40 WP4.2). Loads pyodide + pydantic + shapely,
// unpacks the bundled engine tarball onto sys.path, runs the bootstrap, then serves RPC:
// loadHouse / model / checks / glb. Mutation + IFC are refused in bootstrap.py (stubbed deps),
// so the client surfaces them as "requires local install" without ever reaching here.

import bootstrapSrc from "./bootstrap.py?raw";

const PYODIDE_VERSION = "0.26.2";

interface InitMsg {
  id: number;
  type: "init";
  pyodideIndexUrl: string;
  engineTarUrl: string;
}
interface LoadHouseMsg {
  id: number;
  type: "loadHouse";
  root: string;
  files: Record<string, string>;
}
interface CallMsg {
  id: number;
  type: "model" | "checks" | "glb";
}
type InMsg = InitMsg | LoadHouseMsg | CallMsg;

let pyodide: any = null;
let engine: any = null;
let ready: Promise<void> | null = null;

async function init(msg: InitMsg): Promise<void> {
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
