import * as THREE from "three";
import type { Model } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildFloor, buildSolid, buildStair } from "../three/builders/structure";

declare global {
  interface Window {
    railingReviewReady: boolean;
    railingReviewChecks: { failures: string[]; mounts: number; footBlocks: number; views: number };
  }
}

const model: Model = await (await fetch("/__railing-review-house")).json();
const theme = new URLSearchParams(location.search).get("theme") ?? "light";
const dark = theme === "dark", mode = theme === "schematic" ? "schematic" : "nordic";
const palette = RESOLVED_NORDIC_PALETTE[dark ? "dark" : "light"];
const guard = model.solids!.filter(s => s.host_ref === "RL-SG-BALCONY");
const mounts = guard.filter(s => s.tag.includes("FASCIA-BRACKET"));
const footBlocks = guard.filter(s => s.tag.includes("FASCIA-FOOTBLOCK"));
const posts = guard.filter(s => /-POST\d+$/.test(s.tag));
const failures: string[] = [];
if (mounts.length !== 9 || footBlocks.length !== 8 || posts.length !== 9) {
  failures.push(`Expected 9 posts/mounts and 8 feet; got ${posts.length}/${mounts.length}/${footBlocks.length}`);
}
if (mounts.some(s => !s.body_mesh)) failures.push("A mount has no production body mesh");
const point = (index: number): [number, number, number] => {
  const post = posts.find(s => s.tag.endsWith(`-POST${index}`))!;
  return [post.outline.reduce((sum, p) => sum + p[0], 0) / post.outline.length,
    post.z0_m + 0.08, post.outline.reduce((sum, p) => sum + p[1], 0) / post.outline.length];
};
const overview = point(5);
overview[1] += 0.65;
const stairSolids = model.solids!.filter(s => s.host_ref?.startsWith("RL-SG-PSTAIR-")
  || s.host_ref?.startsWith("RL-SG-PORCH"));
const stairPoint = (tag: string): [number, number, number] => {
  const solid = stairSolids.find(s => s.tag === tag)!;
  return [solid.outline.reduce((sum, p) => sum + p[0], 0) / solid.outline.length,
    solid.z0_m + 0.04, solid.outline.reduce((sum, p) => sum + p[1], 0) / solid.outline.length];
};
const foot = stairPoint("RL-SG-PSTAIR-S-BASE1"), head = stairPoint("RL-SG-PORCH-SE-BASE1");
const stairMid = foot.map((v, i) => (v + head[i]) / 2) as [number, number, number];
const footBlock = footBlocks[3];
const footTarget: [number, number, number] = [
  footBlock.outline.reduce((sum, p) => sum + p[0], 0) / footBlock.outline.length,
  (footBlock.z0_m + footBlock.z1_m) / 2,
  footBlock.outline.reduce((sum, p) => sum + p[1], 0) / footBlock.outline.length,
];
const cases = [
  { name: "Complete guard · continuous deck slope", target: overview, span: 8,
    eye: [-5, 3.5, 6] },
  { name: "Straight fascia mount", target: point(5), span: 0.65, eye: [0.3, 0.22, 1] },
  { name: "Southwest outside corner", target: point(3), span: 0.7, eye: [-1, 0.3, 1] },
  { name: "Southeast outside corner", target: point(7), span: 0.7, eye: [1, 0.3, 1] },
  { name: "Through-bolts and nuts · framing cutaway", target: point(5), span: 0.7,
    eye: [0.25, -0.45, -1] },
  { name: "Flank mount · sloping rim", target: point(2), span: 0.75,
    eye: [-1, 0.2, 0.2] },
  { name: "Rear end · washers fully backed by rim", target: point(1), span: 0.8,
    eye: [-1, 0.3, -0.7] },
  { name: "Panel support · fascia and bottom-rail attachments", target: footTarget, span: 0.5,
    eye: [0.3, 0.2, 1] },
  { name: "Porch stair · one bay, shared head and complete handrail", target: stairMid,
    span: 3.2, eye: [2, 1.5, 3] },
  { name: "Stair foot · concrete pad", target: foot,
    span: 0.5, eye: [1, 0.45, 1] },
  { name: "Shared head · concrete wall top", target: head,
    span: 0.65, eye: [1, 0.4, 1] },
  { name: "Porch leg · rails into PT-SG-BF3", target: stairPoint("RL-SG-PORCH-SE-COLBRK1"),
    span: 1.2, eye: [1, 0.5, 1] },
  { name: "Porch leg · house-end post on W-SG-E1", target: stairPoint("RL-SG-PORCH-E-HOUSE-BASE2"),
    span: 0.8, eye: [1, 0.45, -1] },
  { name: "Porch leg · south-leg plank base over its block", target: stairPoint("RL-SG-PORCH-BASE1"),
    span: 0.65, eye: [1, 0.7, 1] },
];
if (dark) { document.body.style.background = "#22262a"; document.body.style.color = "#eee"; }
for (const sample of cases) {
  const center: [number, number] = [sample.target[0], sample.target[2]];
  const target = new THREE.Vector3(0, sample.target[1]
    + (sample.name.startsWith("Porch stair") ? 0.45 : 0), 0);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(dark ? 0x22262a : 0xe5e3df);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9b8f80, 2));
  const sun = new THREE.DirectionalLight(0xffffff, 3); sun.position.set(-3, 5, 4); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 1); fill.position.set(3, -1, -4); scene.add(fill);
  const group = new THREE.Group(), frame = new THREE.Group(); scene.add(group, frame);
  const picks: THREE.Mesh[] = [], byUid = new Map<string, THREE.Material[]>();
  const isStair = sample.name.startsWith("Porch stair") || sample.name.startsWith("Stair foot")
    || sample.name.startsWith("Shared head") || sample.name.startsWith("Porch leg");
  const context = model.solids!.filter(s => s.tag.startsWith("TR-SG-FASCIA-")
    || s.tag.startsWith("TR-SG-GUTTER-") || s.tag.startsWith("TR-SG-APRON-")
    || (sample.name.startsWith("Rear end") && s.tag.startsWith("TR-SG-BASE-FLASH-")));
  // The cast columns are the porch guard's posts at its leg ends.
  const visible = isStair ? [...stairSolids, ...model.solids!.filter(s => s.tag === "SL-SG-STAIRPAD"
    || /^PT-SG-B[RF][13]$/.test(s.tag))] : [...guard, ...context];
  if (isStair) {
    const stair = model.stairs!.find(s => s.tag === "ST-SG-PORCH")!;
    buildStair(group, stair, center, mode, palette, picks, byUid, model.catalog?.materials);
    if (sample.name.startsWith("Porch leg")) {
      buildFloor(group, model.floors!.find(f => f.tag === "FS-SG-PORCH")!, center, mode,
        palette, picks, byUid, frame, model.catalog?.materials);
    }
    const wall = model.walls.find(w => w.tag === "W-SG-E1")!;
    for (const layer of wall.layers.filter(l => l.polygon.length >= 3)) {
      buildSolid(group, { uid: `review-${layer.name}`, tag: wall.tag, category: "concrete",
        storey: wall.storey, outline: layer.polygon, z0_m: wall.z0_m, z1_m: wall.z1_m,
        material: layer.material, voids: [], assembly: null, provenance: null }, center, mode, palette, model.catalog, picks, byUid,
        model.catalog?.materials);
    }
  }
  for (const solid of visible) {
    const previousPickCount = picks.length;
    const pickUid = solid.group
      ? model.solids!.find(candidate => candidate.group === solid.group)?.uid : undefined;
    buildSolid(group, solid, center, mode, palette, model.catalog, picks, byUid,
      model.catalog?.materials, undefined, pickUid);
    if (solid.body_mesh && picks.length === previousPickCount) {
      failures.push(`${solid.tag}: mounting mesh has no selection target`);
    }
    if (pickUid && picks.slice(previousPickCount).some(pick => pick.userData.uid !== pickUid)) {
      failures.push(`${solid.tag}: mounting mesh lost its railing selection`);
    }
  }
  const deck = model.floors!.find(f => f.tag === "FS-SG-DECK")!;
  const cutaway = sample.name.includes("cutaway") ? { ...deck, subfloor: null,
    members: deck.members.filter(member => Math.abs(member.p0[1] - sample.target[2]) < 0.15
      && Math.abs(member.p1[1] - sample.target[2]) < 0.15) } : deck;
  if (!isStair) buildFloor(group, cutaway, center, mode, palette, picks, byUid, frame, model.catalog?.materials);
  const camera = new THREE.OrthographicCamera(-sample.span * 1.35 / 2, sample.span * 1.35 / 2,
    sample.span / 2, -sample.span / 2, 0.01, 100);
  camera.position.copy(target).add(new THREE.Vector3(...sample.eye)); camera.lookAt(target);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(775, 575); renderer.setPixelRatio(1);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.render(scene, camera);
  if (renderer.info.render.triangles === 0) failures.push(`${sample.name}: empty production scene`);
  const figure = document.createElement("figure"), caption = document.createElement("figcaption");
  caption.textContent = sample.name; figure.append(caption, renderer.domElement);
  document.querySelector("#cards")!.append(figure);
}
window.railingReviewChecks = { failures, mounts: mounts.length, footBlocks: footBlocks.length,
  views: cases.length };
document.querySelector("#status")!.textContent = "9 post mounts · 2 outside corners · 8 fascia foot blocks · production viewer geometry";
window.railingReviewReady = true;
