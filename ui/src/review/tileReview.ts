import * as THREE from "three";
import type { Model } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildRoomFloor } from "../three/builders/structure";
import { TILE_STYLES, buildTileMaps, disposeTileTextures } from "../three/tileMaterial";

const model: Model = await (await fetch("/__tile-review-house")).json();
const materials = model.catalog!.materials;
const failures: string[] = [];
const detail = new URLSearchParams(location.search).has("detail");
const records: unknown[] = [];
// Exercise the real canvas cache and disposal lifecycle in a browser.
for (const style of Object.values(TILE_STYLES)) {
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
  if (!mesh?.material.map || !mesh.material.normalMap || !mesh.material.roughnessMap) {
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
