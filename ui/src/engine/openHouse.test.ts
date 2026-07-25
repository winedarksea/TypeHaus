import bundlerSource from "../../scripts/build-house-asset.mjs?raw";
import { TEXT_EXT } from "./openHouse";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Two independent code paths load a house's plan source into the pyodide engine: the bundled
// asset (scripts/build-house-asset.mjs, baked at build time) and the "Open house folder" picker
// (openHouse.ts, at runtime). They must agree on which files are plan source, because a plan
// module that opens a path at *import* time — houses/catlin/plan/manifest.py reads
// plan/basemap.geojson — turns a missing extension into "Cannot reach engine" rather than into
// a missing basemap. The same omission has now shipped on both paths, so it gets a test.
export function runOpenHouseTests() {
  const declared = /const PLAN_TEXT_EXTENSIONS = \/\\\.\(([^)]+)\)\$\/i;/.exec(bundlerSource);
  assert(declared, "build-house-asset.mjs must declare PLAN_TEXT_EXTENSIONS as a literal regex");
  const bundled = declared[1].split("|").sort();

  const pickerMatch = /\\\.\(([^)]+)\)\$/.exec(TEXT_EXT.source);
  assert(pickerMatch, "openHouse TEXT_EXT must stay an alternation of bare extensions");
  const picked = pickerMatch[1].split("|").sort();

  assert(picked.join() === bundled.join(),
    `Folder-pick and bundled-asset extensions must match: picker=[${picked}] bundler=[${bundled}]`);

  // Named explicitly so a future edit that drops one fails on the reason, not just the diff.
  for (const extension of ["py", "toml", "json", "geojson", "csv"]) {
    assert(TEXT_EXT.test(`plan/thing.${extension}`),
      `A picked house must load .${extension} — plan modules open these by path at import time`);
  }
  assert(!TEXT_EXT.test("out/model.glb"), "Binary build output is never plan source");
}
