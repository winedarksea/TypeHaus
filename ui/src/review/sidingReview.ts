// Local review of production wall/member builders; no separate siding renderer.
import * as THREE from "three";
import type { Model } from "../model/types";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildWall } from "../three/builders/walls";
import { buildWallSkinMembers } from "../three/builders/wallSkin";
import { buildOpening } from "../three/builders/openings";
import { buildSolid } from "../three/builders/structure";
import { disposeGroup } from "../three/members";

const model: Model = await (await fetch("/__siding-review-house")).json();
const params = new URLSearchParams(location.search);
const face = params.get("face") ?? "north";
const profileKey = params.get("profile") ?? "board-and-batten";
const detail = params.has("detail");
const baseDetail = params.get("detail") === "base";
const headDetail = params.get("detail") === "head";
const JUNCTION_TOLERANCE_M = 1e-6;
const palette = RESOLVED_NORDIC_PALETTE.light;
const materials = model.catalog!.materials;
const center: [number, number] = [5.4864, 5.4864];
const groups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
const finishByTag = new Map(materials.map(material => [material.tag, material.finish]));
const faceDirection: Record<string, readonly [number, number]> = {
  north: [0, 1], south: [0, -1], east: [1, 0], west: [-1, 0],
};
function meanPlanPoint(ring: readonly [number, number][]): [number, number] {
  return [ring.reduce((sum, point) => sum + point[0], 0) / ring.length,
    ring.reduce((sum, point) => sum + point[1], 0) / ring.length];
}
function wallOutward(wall: Model["walls"][number]): [number, number] {
  const inside = meanPlanPoint(wall.layers[0].polygon);
  const outside = meanPlanPoint(wall.layers[wall.layers.length - 1].polygon);
  const dx = outside[0] - inside[0], dy = outside[1] - inside[1];
  const length = Math.hypot(dx, dy) || 1;
  return [dx / length, dy / length];
}
function onFace(wall: Model["walls"][number]): boolean {
  const direction = faceDirection[face];
  const normal = wallOutward(wall);
  return normal[0] * direction[0] + normal[1] * direction[1] > 0.65;
}
const walls = model.walls.filter(wall => onFace(wall) && wall.layers.some(layer =>
  finishByTag.get(layer.material) === profileKey));
if (walls.length === 0) throw new Error(`No ${profileKey} walls face ${face}`);
const wallTags = new Set(walls.map(wall => wall.tag));
const selectedOpenings = model.openings.filter(opening => wallTags.has(opening.host));
const exteriorLayerPolygons = walls.flatMap(wall => wall.layers
  .filter(layer => finishByTag.get(layer.material) === profileKey)
  .map(layer => layer.polygon));
const planPoints = exteriorLayerPolygons.flat();
const planBounds = {
  minX: Math.min(...planPoints.map(point => point[0])),
  maxX: Math.max(...planPoints.map(point => point[0])),
  minY: Math.min(...planPoints.map(point => point[1])),
  maxY: Math.max(...planPoints.map(point => point[1])),
};
const profileCenterPlan: [number, number] = [
  (planBounds.minX + planBounds.maxX) / 2, (planBounds.minY + planBounds.maxY) / 2,
];
const wallBase = Math.min(...walls.map(wall => wall.z0_m));
const wallTop = Math.max(...walls.map(wall => wall.z1_m));
const profileCenterElevation = (wallBase + wallTop) / 2;
const chosenOpening = selectedOpenings.sort((a, b) =>
  b.width_m * b.height_m - a.width_m * a.height_m)[0];
const openingWall = chosenOpening && walls.find(wall => wall.tag === chosenOpening.host);
const detailPlan = openingWall && chosenOpening ? (() => {
  const [[x0, y0], [x1, y1]] = openingWall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0) || 1;
  return [x0 + (x1 - x0) * chosenOpening.center_along_m / length,
    y0 + (y1 - y0) * chosenOpening.center_along_m / length] as [number, number];
})() : profileCenterPlan;
const detailElevation = openingWall && chosenOpening
  ? openingWall.z0_m + chosenOpening.sill_m + chosenOpening.height_m * (headDetail ? 1 : 0.5)
  : profileCenterElevation;
const faceNormals = walls.map(wallOutward);
const outwardPlan: [number, number] = [
  faceNormals.reduce((sum, normal) => sum + normal[0], 0),
  faceNormals.reduce((sum, normal) => sum + normal[1], 0),
];
const outwardLength = Math.hypot(...outwardPlan) || 1;
outwardPlan[0] /= outwardLength; outwardPlan[1] /= outwardLength;
const outwardScene = new THREE.Vector3(outwardPlan[0], 0, -outwardPlan[1]);
const targetPlan = detail && !baseDetail ? detailPlan : profileCenterPlan;
const target = new THREE.Vector3(targetPlan[0] - center[0],
  baseDetail ? wallBase : detail ? detailElevation : profileCenterElevation, center[1] - targetPlan[1]);
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
light.position.copy(target).addScaledVector(outwardScene, 8).add(new THREE.Vector3(-8, 15, 0));
light.castShadow = true;
light.shadow.mapSize.set(4096, 4096);
Object.assign(light.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: .1, far: 60 });
light.shadow.normalBias = 0; light.shadow.bias = -.0001;
scene.add(light);
function buildFacades(targetGroups: Record<Trade, THREE.Group>, profiled: boolean) {
  const picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
  for (const wall of walls) {
    const openings = selectedOpenings.filter(opening => opening.host === wall.tag);
    const displayed = { ...wall, layers: wall.layers.map(layer =>
      profiled ? layer : { ...layer, surface_mesh: null }) };
    buildWall(targetGroups, displayed, openings, center, "nordic", palette, picks, selected, materials);
    const closures = (model.roofs ?? []).flatMap(roof => roof.members).filter(member =>
      member.parent_uid === wall.uid).map(member =>
        profiled ? member : { ...member, surface_mesh: null });
    buildWallSkinMembers(targetGroups, targetGroups.siding, wall.uid, closures, center, "nordic", palette, materials);
    for (const opening of openings) {
      const product = model.catalog?.door_types.find(type => type.tag === opening.type_ref);
      buildOpening(targetGroups.openings, opening, wall, center, "nordic", palette,
        { materials, operation: product?.operation, glazed: product?.glazed,
          trimless: product?.trimless, bookcaseDoor: product?.bookcase_door,
          leafSet: product?.leaf_set }, picks, selected);
    }
  }
  const openingTags = new Set(selectedOpenings.map(opening => opening.tag));
  for (const flashing of model.solids?.filter(solid => openingTags.has(solid.host_ref ?? "")) ?? []) {
    buildSolid(targetGroups.roofing, flashing, center, "nordic", palette,
      model.catalog, picks, selected, materials);
  }
  if (profileKey === "corrugated") {
    for (const wall of model.walls.filter(wall => onFace(wall)
      && wall.is_foundation && Math.abs(wall.z1_m - wallBase) < JUNCTION_TOLERANCE_M)) {
      buildWall(targetGroups, wall, model.openings.filter(opening => opening.host === wall.tag),
        center, "nordic", palette, picks, selected, materials);
    }
    for (const flashing of model.solids?.filter(solid => solid.category === "flashing"
      && solid.z0_m <= wallBase && solid.z1_m >= wallBase) ?? []) {
      buildSolid(targetGroups.roofing, flashing, center, "nordic", palette,
        model.catalog, picks, selected, materials);
    }
  }
}
// Warm the shared procedural textures before comparing geometry build costs.
const warmGroups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
buildFacades(warmGroups, true);
for (const group of Object.values(warmGroups)) { disposeGroup(group); group.clear(); }
// Same resolved dimensions and materials: this comparison isolates the added mesh cost.
const flatGroups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
const flatStart = performance.now(); buildFacades(flatGroups, false);
const flatBuildMs = performance.now() - flatStart;
const start = performance.now(); buildFacades(groups, true);
const buildMs = performance.now() - start;
const span = baseDetail || headDetail ? 0.3 : detail ? 1.9 : Math.max(4.5, Math.min(8, (wallTop - wallBase) * 0.7));
// Match Panel3D's perspective depth range: an orthographic review conceals thin-sheet fights.
const camera = new THREE.PerspectiveCamera(50, 1500/1100, .05, 500);
const distance = Number(params.get("distance") ?? (detail ? 7 : 23));
camera.position.copy(target).addScaledVector(outwardScene, distance)
  .add(new THREE.Vector3(0, distance * (detail ? 0.4/7 : 2.5/23), 0));
camera.zoom = camera.position.distanceTo(target) * Math.tan(THREE.MathUtils.degToRad(25)) / span;
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
const info = { buildMs, flatBuildMs, physicalMeshes, triangles, drawCalls: renderer.info.render.calls, errors };
document.querySelector("#status")!.textContent = `${profileKey} · ${face} ${headDetail ? "head" : detail ? "detail" : "facade"} · ${physicalMeshes} profiled meshes · ${triangles.toLocaleString()} triangles · ${buildMs.toFixed(0)} ms build`;
Object.assign(window, { sidingReviewReady: true, sidingReviewChecks: info });
