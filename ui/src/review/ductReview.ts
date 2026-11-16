// Framed looks at the catlin duct joints, built through the production scene stages.
// Each shot is framed by the bounding box of the named run's solids, never by coordinates.
import * as THREE from "three";
import type { Model, Solid } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { planCenterOf, type SceneRegistry } from "../three/builders/scene";
import { sceneStages } from "../three/builders/sceneStages";
import { projectPointToScene } from "../three/planGeometry";
import { ALL_TRADES, type Trade } from "../state/vocabulary";

declare global {
  interface Window {
    ductReviewReady: boolean;
    ductReviewShots: { file: string; name: string; png: string; focusTags: string[]; box: number[] }[];
    ductReviewChecks: { failures: string[] };
  }
}

type Box = [number, number, number, number, number, number]; // x0 y0 z0 x1 y1 z1 (plan x, plan y, z)
const model: Model = await (await fetch("/__duct-review-house")).json();
const params = new URLSearchParams(location.search);
const dark = params.get("theme") === "dark";
const mode = params.get("theme") === "schematic" ? "schematic" : "nordic";
const ghost = params.get("walls") !== "solid";
const eyeParam = params.get("eye")?.split(",").map(Number);
const palette = RESOLVED_NORDIC_PALETTE[dark ? "dark" : "light"];
const solids = model.solids ?? [];
const failures: string[] = [];
const W = 1600, H = 1000;

const boxOf = (s: Solid): Box => {
  const xs = s.outline.map(p => p[0]), ys = s.outline.map(p => p[1]);
  return [Math.min(...xs), Math.min(...ys), s.z0_m, Math.max(...xs), Math.max(...ys), s.z1_m];
};
const union = (boxes: Box[]): Box => boxes.reduce((a, b) =>
  [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.min(a[2], b[2]),
    Math.max(a[3], b[3]), Math.max(a[4], b[4]), Math.max(a[5], b[5])] as Box);
const grow = (b: Box, m: number): Box => [b[0] - m, b[1] - m, b[2] - m, b[3] + m, b[4] + m, b[5] + m];
const meets = (a: Box, b: Box) => a[0] <= b[3] && b[0] <= a[3] && a[1] <= b[4] && b[1] <= a[4]
  && a[2] <= b[5] && b[2] <= a[5];

// A run's pieces however fabrication splits them: host_ref = the tag, tag `{tag}-RUN`, or a uid
// sharing the run's base uid (`{u}-run`, `{u}-run-2`, `{u}-elbow-NN`, `{u}-boot-1`, ...).
const baseUid = (uid: string) => uid.replace(/-(run|elbow)(-\d+)?$/i, "");
function ownedBy(tag: string): Solid[] {
  const bases = new Set(solids.filter(s => s.tag === `${tag}-RUN`).map(s => baseUid(s.uid)));
  return solids.filter(s => s.host_ref === tag || s.tag === `${tag}-RUN`
    || [...bases].some(u => s.uid.startsWith(`${u}-`)));
}
const isElbow = (s: Solid) => /elbow/i.test(s.uid) || /elbow/i.test(s.tag);
const isNeck = (s: Solid) => s.category === "terminal_neck";
const isBoot = (s: Solid) => /boot/i.test(s.uid) || /-BOOT-\d+$/.test(s.tag);

interface Shot { file: string; name: string; focus: () => Solid[]; wall?: string; }
const shots: Shot[] = [
  { file: "1-suite-junction", name: "DU-S-HP-SUITE into REG-S-HP-SUITE on W-S-C2B", wall: "W-S-C2B",
    focus: () => [...ownedBy("DU-S-HP-SUITE"), ...ownedBy("REG-S-HP-SUITE")] },
  { file: "2-loft-takeoff-boot", name: "DU-S-HP-WEST-BOOT: take-off on DU-S-HP-SUP to REG-A-HP-WEST",
    focus: () => {
      const run = [...ownedBy("DU-S-HP-WEST-BOOT"), ...ownedBy("REG-A-HP-WEST")];
      if (!run.length) return run;
      const near = grow(union(run.map(boxOf)), 0.15);
      const takeoffs = ownedBy("DU-S-HP-SUP").filter(s => /takeoff/i.test(s.uid) && meets(boxOf(s), near));
      return [...run, ...takeoffs];
    } },
  { file: "3-return-riser", name: "DU-S-HP-RET riser", focus: () => ownedBy("DU-S-HP-RET") },
  { file: "4-round-elbow", name: "Stamped elbow on 6-inch round DU-S-HP-WEST-BOOT",
    focus: () => {
      const own = ownedBy("DU-S-HP-WEST-BOOT").filter(s => s.category !== "duct_support");
      const elbows = own.filter(isElbow);
      return elbows.length ? elbows : own.filter(s => !isNeck(s) && !isBoot(s));
    } },
];

function buildScene(focus: Solid[], wallTag?: string) {
  const full = union(focus.map(boxOf)), local = grow(full, 0.6);
  const context = solids.filter(s => {
    const b = boxOf(s);
    const huge = b[3] - b[0] > 6 || b[4] - b[1] > 6; // slabs and roofs would bury the duct
    return meets(b, local) && !huge;
  });
  const ids = new Set(context.map(s => s.uid));
  const wallBox = grow(full, 1.5);
  const walls = model.walls.filter(w => w.tag === wallTag || (meets([
    Math.min(w.axis[0][0], w.axis[1][0]), Math.min(w.axis[0][1], w.axis[1][1]), w.z0_m,
    Math.max(w.axis[0][0], w.axis[1][0]), Math.max(w.axis[0][1], w.axis[1][1]), w.z1_m], wallBox)));
  const wallTags = new Set(walls.map(w => w.tag));
  const focusTags = new Set(focus.map(s => s.tag.replace(/-(RUN|NECK|BOOT-\d+)$/, "")));
  const subset: Model = { ...model, solids: solids.filter(s => ids.has(s.uid)), walls,
    openings: (model.openings ?? []).filter(o => wallTags.has(o.host)),
    floors: [], roofs: [], stairs: [], rooms: [], panelings: [], window_stools: [], base_runs: [],
    door_casings: [], countertops: [], soffits: [], braces: [], footing_beddings: [], plants: [],
    solar_panels: [], alarms: [], light_runs: [], site: undefined as unknown as Model["site"],
    canvas_objects: (model.canvas_objects ?? []).filter(c => focusTags.has(c.tag)) };
  const tradeGroups = Object.fromEntries(ALL_TRADES.map(t => [t, new THREE.Group()])) as Record<Trade, THREE.Group>;
  const registry: SceneRegistry = { picks: [], byUid: new Map() };
  const center = planCenterOf(model);
  const wallObjects: THREE.Object3D[] = [];
  const known = new Set<THREE.Object3D>();
  const everything = () => Object.values(tradeGroups).forEach(g => g.traverse(o => known.add(o)));
  for (const stage of sceneStages({ tradeGroups, model: subset, center, mode, palette,
    earthOpacity: 0, earthTone: "brown", registry, generation: 0, currentGeneration: () => 0,
    requestRender: () => {} })) {
    everything();
    const before = new Set(known);
    for (const item of stage.items) item();
    everything();
    if (stage.name === "walls" || stage.name === "openings") {
      for (const g of Object.values(tradeGroups)) g.traverse(o => { if (!before.has(o)) wallObjects.push(o); });
    }
  }
  if (ghost) for (const o of wallObjects) if (o instanceof THREE.Mesh) {
    const ghosted = (m: THREE.Material) => Object.assign(m.clone(),
      { transparent: true, opacity: 0.16, depthWrite: false });
    o.material = Array.isArray(o.material) ? o.material.map(ghosted) : ghosted(o.material);
  }
  return { tradeGroups, center, full };
}

const status = document.querySelector("#status")!;
const out: Window["ductReviewShots"] = [];
for (const shot of shots) {
  const focus = shot.focus();
  if (!focus.length) { failures.push(`${shot.name}: no solids matched`); continue; }
  const { tradeGroups, center, full } = buildScene(focus, shot.wall);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(dark ? 0x22262a : 0xe5e3df);
  scene.add(new THREE.HemisphereLight(0xffffff, dark ? 0x46403a : 0x9b8f80, 2));
  const sun = new THREE.DirectionalLight(0xffffff, 3); sun.position.set(-3, 5, 4); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 1); fill.position.set(3, -1, -4); scene.add(fill);
  Object.values(tradeGroups).forEach(g => scene.add(g));
  // Fit the focus box: project its corners on the camera's right/up axes, pad 50 %.
  const lo = projectPointToScene([full[0], full[1]], full[2], center);
  const hi = projectPointToScene([full[3], full[4]], full[5], center);
  const mid = lo.clone().add(hi).multiplyScalar(0.5);
  const eye = new THREE.Vector3(...(eyeParam?.length === 3 ? eyeParam : [1, 0.8, 1])).normalize();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 200);
  camera.position.copy(mid).addScaledVector(eye, 20); camera.lookAt(mid); camera.updateMatrixWorld();
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
  const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
  let halfW = 0, halfH = 0;
  for (const x of [lo.x, hi.x]) for (const y of [lo.y, hi.y]) for (const z of [lo.z, hi.z]) {
    const d = new THREE.Vector3(x, y, z).sub(mid);
    halfW = Math.max(halfW, Math.abs(d.dot(right))); halfH = Math.max(halfH, Math.abs(d.dot(up)));
  }
  const half = Math.max(halfW / (W / H), halfH, 0.05) * 1.5;
  Object.assign(camera, { left: -half * W / H, right: half * W / H, top: half, bottom: -half });
  camera.updateProjectionMatrix();
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H); renderer.setPixelRatio(1);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.render(scene, camera);
  if (renderer.info.render.triangles === 0) failures.push(`${shot.name}: empty scene`);
  out.push({ file: shot.file, name: shot.name, png: renderer.domElement.toDataURL("image/png"),
    focusTags: [...new Set(focus.map(s => s.tag))], box: full });
  const figure = document.createElement("figure"), caption = document.createElement("figcaption");
  caption.textContent = shot.name; figure.append(caption, renderer.domElement);
  document.querySelector("#cards")!.append(figure);
}
window.ductReviewShots = out;
window.ductReviewChecks = { failures };
status.textContent = `${out.length} framed duct looks · walls ${ghost ? "ghosted" : "solid"} · production viewer geometry`;
window.ductReviewReady = true;
