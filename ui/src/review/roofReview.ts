// Production roof/wall builders, photographed at each sheet-to-trim junction.
import * as THREE from "three";
import type { Model } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { buildRoof } from "../three/builders/structure";
import { buildWall } from "../three/builders/walls";

const model: Model = await (await fetch("/__siding-review-house")).json();
const roof = model.roofs!.find(roof => roof.tag === "RF-HOUSE")!;
const center: [number, number] = [5.4864, 5.4864];
const palette = RESOLVED_NORDIC_PALETTE.light;
const scene = new THREE.Scene();
scene.background = new THREE.Color("#e5e3df");
const group = new THREE.Group(); scene.add(group);
const trades = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
for (const trade of Object.values(trades)) scene.add(trade);
const picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
for (const wall of model.walls.filter(wall => wall.storey === "attic" || wall.storey === "second")) {
  buildWall(trades, wall, model.openings.filter(opening => opening.host === wall.tag), center,
    "nordic", palette, picks, selected, model.catalog?.materials);
}
buildRoof(group, roof, center, "nordic", palette, model.catalog, picks, selected,
  undefined, undefined, trades);
scene.add(new THREE.HemisphereLight(0xffffff, 0xa9a39b, 2));
const light = new THREE.DirectionalLight(0xffffff, 3);
light.position.set(-12, 22, -9); scene.add(light);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(1500, 1100); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.NeutralToneMapping;
document.body.append(renderer.domElement);
const view = new URLSearchParams(location.search).get("view") ?? "roof";
const targets: Record<string, [number, number, number, number]> = {
  roof: [0, roof.ridge_z_m, 0, 19],
  eave: [-5.5, roof.eave_z_m, 0, 2.6],
  rake: [-2.5, roof.eave_z_m + 1.5, 5.5, 3.5],
  ridge: [0, roof.ridge_z_m, 0, 2.3],
};
const [x, y, z, distance] = targets[view];
const target = new THREE.Vector3(x, y, z);
const camera = new THREE.PerspectiveCamera(38, 1500 / 1100, .1, 100);
camera.position.copy(target).add(new THREE.Vector3(-.7, .65, .9).normalize().multiplyScalar(distance));
camera.lookAt(target); renderer.render(scene, camera);
const sheet = roof.layer_surface_meshes?.find(item => item.layer === "roofing")?.surface_mesh;
const errors = [];
if (!sheet?.triangles.length) errors.push("Missing resolved roofing sheet");
if (!roof.members.some(member => member.category === "ridge_closure")) errors.push("Missing ridge closures");
const checks = { view, triangles: sheet?.triangles.length, errors };
document.querySelector("#status")!.textContent = JSON.stringify(checks);
Object.assign(window, { sidingReviewChecks: checks, sidingReviewReady: true });
