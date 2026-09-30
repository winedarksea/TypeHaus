// Resolve the public browser bundle under the same Pyodide runtime and GEOS as the worker.
import { loadPyodide } from "pyodide";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const asset = (name) => resolve(repo, "ui/public", name);
const files = JSON.parse(readFileSync(asset("catlin-house.json"), "utf8"));
const pyodide = await loadPyodide();
await pyodide.loadPackage(["pydantic", "shapely"]);
pyodide.unpackArchive(new Uint8Array(readFileSync(asset("typehaus-engine.tar.gz"))), "gztar", { extractDir: "/engine" });
pyodide.runPython("import sys; sys.path.insert(0, '/engine')");
await pyodide.runPythonAsync(readFileSync(resolve(repo, "ui/src/engine/pyodide/bootstrap.py"), "utf8"));
const engine = pyodide.globals.get("ENGINE");
const fileProxy = pyodide.toPy(files);
try {
  const state = engine.load_house("/house", fileProxy);
  const result = state.toJs({ dict_converter: Object.fromEntries });
  state.destroy();
  const payloadProxy = engine.model_json();
  const payload = payloadProxy.toJs({ dict_converter: Object.fromEntries });
  payloadProxy.destroy();
  if (!result.ok || !payload.storeys?.length || !payload.walls?.length) {
    throw new Error(`bundled house did not resolve: ${JSON.stringify(result.findings?.slice(0, 5))}`);
  }
  writeFileSync(asset("catlin-model.json"), JSON.stringify(payload));
  console.log(`[pwa] wrote ${asset("catlin-model.json")} (${readFileSync(asset("catlin-model.json")).length} bytes, revision ${payload.revision})`);
} finally {
  fileProxy.destroy();
  engine.destroy();
}
