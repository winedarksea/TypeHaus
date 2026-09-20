// Pyodide GEOS smoke test — runs the engine's real compute path under the GEOS the
// PUBLISHED app runs, not the one `.venv` runs.
//
// Why this exists: `.venv` is Shapely 2.1.2 / GEOS 3.13.1; the Pyodide wheel the web app
// loads is Shapely 2.0.2 / GEOS **3.12.1**. GEOS 3.13 hardened OverlayNG's noding, so 3.12
// throws `TopologyException` on inputs 3.13 absorbs — and in the worker that throw is a JS
// `CppException` that kills the worker outright, so the app never renders. `pytest` passing
// on 3.13.1 proves nothing about that class of bug. A bare `shapely.unary_union` that should
// have gone through `resolve/overlay.py`'s fixed-precision `union_all` is exactly how one
// ships green. (→ plans/TODO.md, memory: pyodide-geos-repro-harness)
//
// Usage:  node scripts/pyodide/smoke.mjs [houseRelPath]        (default houses/starter)
// Pyodide is pinned in scripts/pyodide/package.json; run `npm ci` here first.

import { loadPyodide } from "pyodide";
import { readFileSync } from "node:fs";
import { dirname, join, resolve as resolvePath } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolvePath(HERE, "..", "..");
const HOUSE = process.argv[2] ?? "houses/starter";
const t0 = Date.now();
const step = (m) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${m}`);

// --- dynamic half: the real overlay/union code under GEOS 3.12 --------------------------
const py = await loadPyodide();
step("pyodide booted");
await py.loadPackage(["micropip", "pydantic", "shapely"]); // exactly what worker.ts loads
step("packages loaded");

py.FS.mkdirTree("/repo");
py.FS.mount(py.FS.filesystems.NODEFS, { root: REPO }, "/repo"); // live tree, no tarball

await py.runPythonAsync(`
import sys
sys.path.insert(0, "/repo/packages/engine/src")
import shapely
print("shapely", shapely.__version__, "geos", shapely.geos_version_string)
`);

// bootstrap.py is the published app's own entry point: same stubs, same env, same engine.
await py.runPythonAsync(readFileSync(join(REPO, "ui/src/engine/pyodide/bootstrap.py"), "utf8"));
step("engine bootstrapped");

// The compute path the worker drives. Every step below unions or overlays real geometry;
// a TopologyException anywhere surfaces as a JS CppException and fails this script.
const report = await py.runPythonAsync(`
import json
from pathlib import Path

ENGINE.house_dir = Path("/repo/${HOUSE}")
state = ENGINE.rebuild()
assert state["ok"], "rebuild not ok: " + json.dumps(state["findings"][:5])

payload = ENGINE.model_json()
bom = ENGINE.bom_json()
glb = ENGINE.glb_bytes()

from typehaus.server.space_summary import build_space_summary
spaces = build_space_summary(ENGINE.model)

json.dumps({
    "solids": len(payload.get("solids") or []),
    "rooms": len(payload.get("rooms") or []),
    "findings": len(state["findings"]),
    "framing_lines": len(bom.get("framing") or []),
    "glb_bytes": len(glb),
    "conditioned_sf": spaces["overall"]["conditioned_sf"],
    "geos": __import__("shapely").geos_version_string,
})
`);

const r = JSON.parse(report);
step(`compute path clean under GEOS ${r.geos}`);
console.log(JSON.stringify(r, null, 2));
if (!r.glb_bytes || !r.solids || !r.rooms || !r.framing_lines) {
  console.error("smoke produced an empty model — the compute path did not really run");
  process.exit(1);
}
console.log(`OK — ${HOUSE} resolved, billed and emitted under Pyodide GEOS ${r.geos}`);
