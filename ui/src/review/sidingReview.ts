// Local review of production wall/member builders; no separate siding renderer.
import * as THREE from "three";
import type { Model } from "../model/types";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildWall } from "../three/builders/walls";
import { buildWallSkinMembers } from "../three/builders/wallSkin";
import { buildOpening } from "../three/builders/openings";

const model: Model = await (await fetch("/__siding-review-house")).json();
const params = new URLSearchParams(location.search);
const north = params.get("face") !== "south";
const detail = params.has("detail");
const palette = RESOLVED_NORDIC_PALETTE.light;
const materials = model.catalog!.materials;
const center: [number, number] = [5.4864, 5.4864];
const groups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
const scene = new THREE.Scene();
scene.background = new THREE.Color("#e5e3df");
for (const group of Object.values(groups)) scene.add(group);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(1500, 1100); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0xbcb6a8, 1.4));
const light = new THREE.DirectionalLight(0xffffff, 3);
light.position.set(-14, 15, north ? -8 : 8); light.castShadow = true;
light.shadow.mapSize.set(4096, 4096);
Object.assign(light.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: .1, far: 60 });
light.shadow.normalBias = 0; light.shadow.bias = -.0001;
scene.add(light);
const start = performance.now();
const picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
const walls = model.walls.filter(wall => wall.layers.some(layer =>
  ["board-and-batten", "ribbed-panel"].includes(
    materials.find(material => material.tag === layer.material)?.finish ?? "")));
for (const wall of walls) {
  const openings = model.openings.filter(opening => opening.host === wall.tag);
  buildWall(groups, { ...wall, members: [] }, openings, center, "nordic", palette, picks, selected, materials);
  const closures = (model.roofs ?? []).flatMap(roof => roof.members).filter(member =>
    member.parent_uid === wall.uid && member.category === "cladding");
  buildWallSkinMembers(groups, groups.siding, wall.uid, closures, center, "nordic", palette, materials);
  for (const opening of openings) buildOpening(groups.openings, opening, wall, center, "nordic", palette,
    { materials }, picks, selected);
}
const buildMs = performance.now() - start;
const target = detail ? new THREE.Vector3(north ? -2.7 : 2.7, 4.5, north ? -5.66 : 5.66)
  : new THREE.Vector3(0, 3.5, 0);
const span = detail ? 1.9 : 8;
const camera = new THREE.OrthographicCamera(-span * 1500/1100, span * 1500/1100, span, -span, .01, 100);
camera.position.copy(target).add(new THREE.Vector3(detail ? 3.4 : 7, detail ? .5 : 2.5,
  (north ? -1 : 1) * (detail ? 7 : 23)));
camera.lookAt(target); camera.updateProjectionMatrix();
const errors: string[] = [];
let physicalMeshes = 0, triangles = 0;
scene.traverse(object => {
  if (!(object instanceof THREE.Mesh)) return;
  const position = object.geometry.getAttribute("position");
  triangles += (object.geometry.index?.count ?? position.count)/3;
  const material = object.material;
  if (material instanceof THREE.MeshPhysicalMaterial && material.normalMap === null) physicalMeshes++;
});
if (physicalMeshes === 0) errors.push("No physical siding meshes rendered");
renderer.render(scene,camera);
const info = { buildMs, physicalMeshes, triangles, drawCalls: renderer.info.render.calls, errors };
document.querySelector("#status")!.textContent = `${north ? "North" : "South"} ${detail ? "detail" : "facade"} · 12″ pitch · 2″ crown · ¾″ depth · ${buildMs.toFixed(0)} ms scene build`;
Object.assign(window, { sidingReviewReady: true, sidingReviewChecks: info });
