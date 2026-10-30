import * as THREE from "three";
import type { Model } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildRoomFloor } from "../three/builders/structure";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { TILE_STYLES, applyTileUv, buildTileMaps, createTileMaterial, disposeTileTextures,
  tileRepeatSizeM } from "../three/tileMaterial";
import { onyxMapsSettled } from "../three/onyxMaps";

const model: Model = await (await fetch("/__tile-review-house")).json();
const materials = model.catalog!.materials;
const failures: string[] = [];
const detail = new URLSearchParams(location.search).has("detail");
const records: unknown[] = [];
// Exercise the real canvas cache and disposal lifecycle in a browser.
for (const style of Object.values(TILE_STYLES)) {
  if (style.print) continue; // onyx has its own lazy pipeline, reviewed below
  const maps = buildTileMaps(style);
  if (!maps || maps !== buildTileMaps(style)) failures.push("Tile maps were not cached");
}
let disposed = 0;
const old = buildTileMaps(TILE_STYLES["tile-carrara-grid"])!;
for (const map of Object.values(old)) map.addEventListener("dispose", () => { disposed++; });
disposeTileTextures();
if (disposed !== 3 || old === buildTileMaps(TILE_STYLES["tile-carrara-grid"])) {
  failures.push("Texture disposal failed to release and rebuild maps");
}
const probe = new THREE.WebGLRenderer();
const environment = new THREE.PMREMGenerator(probe).fromScene(new RoomEnvironment(), 0.04).texture;
probe.dispose();
function render(scene: THREE.Scene, camera: THREE.Camera, caption: string) {
  scene.environment = environment; scene.environmentIntensity = 0.6;
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(760, 475); renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1;
  renderer.render(scene, camera);
  const figure = document.createElement("figure"), cap = document.createElement("figcaption");
  cap.textContent = caption;
  figure.append(cap, renderer.domElement); document.querySelector("main")!.append(figure);
}
// Onyx prints: a synthetic 2x2-repeat floor, top-down and at a grazing angle.
await onyxMapsSettled();
for (const key of Object.keys(TILE_STYLES).filter(k => TILE_STYLES[k].print)) {
  const style = TILE_STYLES[key];
  const [w, h] = tileRepeatSizeM(style);
  const plane = new THREE.PlaneGeometry(w * 2, h * 2).rotateX(-Math.PI / 2).translate(w, 0, h);
  applyTileUv(plane, [w, h], style);
  const material = createTileMaterial("nordic", style, "#ffffff");
  if (!(material instanceof THREE.MeshPhysicalMaterial)) failures.push(`${key}: not a physical material`);
  await onyxMapsSettled();
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xe7e4de);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xb6afa3, 2), new THREE.Mesh(plane, material));
  const key1 = new THREE.DirectionalLight(0xffffff, 2.6); key1.position.set(-3, 6, 4); scene.add(key1);
  const top = new THREE.OrthographicCamera(-w * 1.1, w * 1.1, w * 0.69, -w * 0.69, 0.01, 50);
  top.position.set(w, 8, h); top.lookAt(w, 0, h);
  render(scene, top, `${key} · top`);
  const graze = new THREE.PerspectiveCamera(40, 760 / 475, 0.01, 50);
  graze.position.set(w, 0.9, h + 4.2); graze.lookAt(w, 0, h - 0.6);
  render(scene, graze, `${key} · grazing`);
}
for (const tag of ["RM-M-BATH2", "RM-S-SUITEBATH", "RM-S-VANITY", "RM-S-BATH1"]) {
  const room = model.rooms.find(room => room.tag === tag)!;
  const material = materials.find(material => material.tag === room.floor_finish)!;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xe7e4de);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xb6afa3, 2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.6);
  sun.position.set(-3, 6, 4); scene.add(sun);
  const floor = new THREE.Group(), picks: THREE.Mesh[] = [];
  buildRoomFloor(floor, room, 0, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light,
    materials, picks, new Map());
  scene.add(floor);
  const bounds = new THREE.Box3().setFromObject(floor);
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const span = detail ? 0.60 : Math.max(size.x, size.z) * 1.15;
  const camera = new THREE.OrthographicCamera(-span * 1.6 / 2, span * 1.6 / 2,
    span / 2, -span / 2, 0.01, 50);
  camera.position.copy(center).add(new THREE.Vector3(0, 8, 2)); camera.lookAt(center);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(760, 475); renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1;
  renderer.render(scene, camera);
  const mesh = floor.children[0] as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>;
  // A stale snapshot may still name a retired finish; only declared recipes owe maps.
  if (TILE_STYLES[material.finish ?? ""] && (!mesh?.material.map || !mesh.material.normalMap || !mesh.material.roughnessMap)) {
    failures.push(`${tag}: missing product surface maps`);
  }
  if (!mesh.geometry.getAttribute("uv") || picks.length === 0) failures.push(`${tag}: missing UVs/picking`);
  const figure = document.createElement("figure"), caption = document.createElement("figcaption");
  caption.textContent = `${tag} · ${material.name}`;
  figure.append(caption, renderer.domElement); document.querySelector("main")!.append(figure);
  records.push({ tag, finish: room.floor_finish, widthM: size.x, depthM: size.z,
    meshCount: floor.children.length, textured: !!mesh.material.map });
}
await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
Object.assign(window, { tileReviewReady: true, tileReviewChecks: { failures, records } });
