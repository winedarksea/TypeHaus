// SCRATCH (delete after use): dump viewer triangles near the RF-HOUSE NE eave corner.
import { createServer } from "vite";
import { readFileSync, writeFileSync } from "node:fs";
delete globalThis.localStorage;
delete globalThis.sessionStorage;
const DATA = new Uint8ClampedArray(4 * 2048 * 2048);
const noop = new Proxy(function () {}, { get: (t, k) => (k === Symbol.toPrimitive ? () => 0 : k === "data" ? DATA : noop), apply: () => noop, construct: () => noop, set: () => true });
const fakeCanvas = () => ({ width: 1, height: 1, style: {}, getContext: () => noop, toDataURL: () => "", addEventListener() {} });
globalThis.document = { createElement: () => fakeCanvas(), createElementNS: () => fakeCanvas() };
globalThis.OffscreenCanvas = class { constructor(w, h) { Object.assign(this, fakeCanvas(), { width: w, height: h }); } };

const [modelPath, outPath] = process.argv.slice(2);
const server = await createServer({ configFile: false, root: new URL("..", import.meta.url).pathname,
  server: { middlewareMode: true }, appType: "custom", logLevel: "error" });
try {
  const THREE = await server.ssrLoadModule("three");
  const { populateScene } = await server.ssrLoadModule("/src/three/builders/scene.ts");
  const { RESOLVED_NORDIC_PALETTE } = await server.ssrLoadModule("/src/nordic/palette.ts");
  const { ALL_TRADES } = await server.ssrLoadModule("/src/state/vocabulary.ts");
  const full = JSON.parse(readFileSync(modelPath, "utf8"));
  // Boxes in plan metres (x0,x1,y0,y1,z0,z1).
  const boxes = { ne: [10.55, 11.75, 10.45, 11.75, 5.7, 7.0], east: [10.55, 11.75, 4.7, 5.9, 5.7, 7.0] };
  const near = (pts) => pts?.some?.(([x, y]) => x > 9.5 && x < 12.5);
  const model = { ...full,
    walls: full.walls.filter((w) => near(w.axis) && ["second", "attic", "main"].includes(w.storey)),
    roofs: full.roofs.filter((r) => r.tag === "RF-HOUSE"),
    solids: full.solids.filter((s) => s.category !== "plant" && (near(s.outline) || near(s.sweep?.path))),
    plants: [], floors: [], stairs: [], canvas_objects: [], furniture: [], fixtures: [], footing_beddings: [],
    base_runs: [], door_casings: [], countertops: [], panelings: [], window_stools: [], solar_panels: [],
    soffits: full.soffits, light_runs: [], rebar: [] };
  model.openings = full.openings.filter((o) => model.walls.some((w) => w.tag === o.host));
  const tradeGroups = Object.fromEntries(ALL_TRADES.map((t) => [t, new THREE.Group()]));
  const root = new THREE.Group();
  for (const t of ALL_TRADES) root.add(tradeGroups[t]);
  const registry = { picks: [], byUid: new Map() };
  populateScene({ tradeGroups, model, center: [0, 0], mode: "nordic", palette: RESOLVED_NORDIC_PALETTE,
    earthOpacity: 1, earthTone: "soil", registry, generation: 0, currentGeneration: () => 0,
    requestRender: () => {} });
  root.updateMatrixWorld(true);
  const out = [];
  const inBox = (p, b) => p[0] >= b[0] && p[0] <= b[1] && p[1] >= b[2] && p[1] <= b[3] && p[2] >= b[4] && p[2] <= b[5];
  const v = new THREE.Vector3(); const m = new THREE.Matrix4(); const im = new THREE.Matrix4();
  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry?.attributes?.position) return;
    if (obj.userData?.earth) return;
    const g = obj.geometry; const pos = g.attributes.position; const idx = g.index;
    const mat = Array.isArray(obj.material) ? obj.material[0] : obj.material;
    const meta = { name: obj.name, ud: JSON.stringify(obj.userData).slice(0, 200),
      color: mat?.color ? mat.color.getHexString() : null,
      po: mat?.polygonOffset ? [mat.polygonOffsetFactor, mat.polygonOffsetUnits] : null,
      transparent: !!mat?.transparent, opacity: mat?.opacity };
    const count = obj.isInstancedMesh ? obj.count : 1;
    const nTri = idx ? idx.count / 3 : pos.count / 3;
    for (let k = 0; k < count; k++) {
      m.copy(obj.matrixWorld);
      if (obj.isInstancedMesh) { obj.getMatrixAt(k, im); m.multiply(im); }
      const tris = [];
      for (let t = 0; t < nTri; t++) {
        const tri = [];
        for (let c = 0; c < 3; c++) {
          const i = idx ? idx.getX(t * 3 + c) : t * 3 + c;
          v.fromBufferAttribute(pos, i).applyMatrix4(m);
          tri.push([+v.x.toFixed(5), +(-v.z).toFixed(5), +v.y.toFixed(5)]);
        }
        const hit = Object.entries(boxes).some(([, b]) => {
          const lo = [0, 1, 2].map((a) => Math.min(...tri.map((p) => p[a])));
          const hi = [0, 1, 2].map((a) => Math.max(...tri.map((p) => p[a])));
          return lo[0] <= b[1] && hi[0] >= b[0] && lo[1] <= b[3] && hi[1] >= b[2] && lo[2] <= b[5] && hi[2] >= b[4];
        });
        if (hit) tris.push(tri);
      }
      if (tris.length) out.push({ ...meta, inst: k, tris });
    }
  });
  writeFileSync(outPath, JSON.stringify(out));
  console.log("meshes", out.length, "tris", out.reduce((a, o) => a + o.tris.length, 0));
} finally {
  await server.close();
}
