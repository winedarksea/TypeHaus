// Local-only material study; Vite's production entry remains index.html.
import * as THREE from "three";
import { hashBoard } from "../three/plankLayout";
import { createPlankMaterial, WOOD_PLANK_STYLES } from "../three/plankMaterial";
import { woodMaterialsForGeometry, boardBoxGeometry } from "../three/woodPiece";

const params = new URLSearchParams(location.search);
const legacyColors = [
  ["cherry", "Black cherry", "#a0644a"], ["ash", "White ash", "#d8c49e"],
  ["elm", "American elm", "#b08d5e"], ["walnut", "Black walnut", "#5d4433"],
  ["oak", "White oak", "#c9b08c"], ["locust", "Black locust", "#b59a5c"],
  ["basswood", "Basswood", "#e6d4ae"], ["red-oak", "Red oak", "#c9ab91"],
  ["sugar-maple", "Sugar maple", "#e5d9be"],
];
const samples: { species: string; name: string; color: string }[] =
  await (await fetch("/__wood-review-palette")).json();
const legacy = params.has("legacy");
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(1800, 1350);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.toneMappingExposure = 1;
document.body.append(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color("#e5e3df");
scene.add(new THREE.HemisphereLight(0xffffff, 0xbcb6a8, 0.8));
const light = new THREE.DirectionalLight(0xffffff, 0.9);
light.position.set(-3, 7, 5); scene.add(light);
const camera = new THREE.OrthographicCamera(-3.1, 3.1, 2.325, -2.325, 0.1, 100);
camera.position.set(0, 3.2, 12); camera.lookAt(0, 0, 0);
const solidStyle = WOOD_PLANK_STYLES["solid-board"];
const style = legacy ? { ...solidStyle, key: "legacy-solid", faceWidthM: 0.4064,
  tileAlongM: 2.4384, pxPerM: 600 } : solidStyle;
let houseChecks: unknown;
const room = params.has("room") ? await (await import("./woodHouseReview")).houseWoodRoom() : null;
if (room) {
  houseChecks = room.checks;
  const bounds = new THREE.Box3().setFromObject(room.group);
  room.group.position.sub(bounds.getCenter(new THREE.Vector3())); scene.add(room.group);
  camera.left = -4; camera.right = 4; camera.top = 3; camera.bottom = -3;
  camera.position.set(5, 6, 8); camera.lookAt(0, 0, 0);
  document.querySelector("h1")!.textContent = "Catlin suite · wood at room scale";
  document.querySelector("p")!.textContent = "Actual oak floor, cherry headboard and base, elm posts · full-size geometry";
}
const house = params.has("house") ? await (await import("./woodHouseReview")).houseWoodSamples() : null;
if (house) {
  houseChecks = house.checks;
  document.querySelector("h1")!.textContent = "Catlin · actual resolved wood objects";
  document.querySelector("p")!.textContent = "Production builders · original grain scale · objects uniformly fitted to cards";
  camera.position.set(1, 5.5, 12); camera.lookAt(0, 0, 0);
}
for (const [index, sample] of (room ? [] : samples).entries()) {
  const { species, name } = sample;
  const color = legacy ? legacyColors[index][2] : sample.color;
  const appearance = legacy ? undefined : { species };
  const group = new THREE.Group();
  group.position.set((index % 3 - 1) * 2.05, (1 - Math.floor(index / 3)) * 1.5, 0);
  if (house) {
    const content = house.groups[index].group;
    const box = new THREE.Box3().setFromObject(content);
    const size = box.getSize(new THREE.Vector3());
    const wrapper = new THREE.Group();
    content.position.sub(box.getCenter(new THREE.Vector3())); wrapper.add(content);
    wrapper.scale.setScalar(1.15 / Math.max(size.x, size.y, size.z));
    wrapper.rotation.y = size.z > size.x ? Math.PI / 2 - 0.25 : -0.25; group.add(wrapper);
  }
  if (!house) {
  const material = createPlankMaterial("nordic", style, color, undefined, appearance);
  for (let board = 0; !house && board < 4; board++) {
    const matrix = new THREE.Matrix4().makeScale(0.15, 0.94, 0.075);
    matrix.setPosition(-0.67 + board * 0.17, 0, board % 2 * 0.025);
    let seed = 0;
    while (Math.floor(hashBoard(seed, 1) * style.boardsPerTile) !== board) seed++;
    const geometry = boardBoxGeometry(matrix, style, legacy ? board + 3 : seed);
    group.add(new THREE.Mesh(geometry, legacy ? material : woodMaterialsForGeometry(material, geometry)));
  }
  const panel = legacy ? { ...WOOD_PLANK_STYLES.shiplap, key: "legacy-shiplap", tileAlongM: 0.5588 }
    : WOOD_PLANK_STYLES.shiplap;
  const geo = new THREE.PlaneGeometry(0.66, 0.94);
  const uv = geo.getAttribute("uv");
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 0.66 / (panel.faceWidthM * panel.boardsPerTile),
    uv.getY(i) * 0.94 / panel.tileAlongM);
  const mesh = new THREE.Mesh(geo, createPlankMaterial("nordic", panel, color, undefined, appearance));
  mesh.position.x = 0.43; group.add(mesh);
  }
  const label = document.createElement("canvas"); label.width = 700; label.height = 70;
  const ctx = label.getContext("2d")!;
  ctx.font = "32px system-ui"; ctx.fillStyle = "#302e29"; ctx.textAlign = "center";
  ctx.fillText(house ? house.groups[index].name : name, 350, 45);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(label), depthTest: false }));
  sprite.scale.set(1.65, 0.165, 1); sprite.position.set(0, 0.68, 0); group.add(sprite);
  group.userData.species = species; scene.add(group);
}
if (params.has("far")) camera.zoom = 0.55;
if (params.has("detail")) {
  camera.zoom = 2.85; camera.position.set(-2.05, 3.2, 12); camera.lookAt(-2.05, 1.5, 0);
}
camera.updateProjectionMatrix();
if (house || room) {
  (window as unknown as { woodReviewChecks: unknown }).woodReviewChecks = houseChecks;
} else if (!legacy) {
  const { runWoodBrowserChecks } = await import("../three/woodBrowserChecks");
  (window as unknown as { woodReviewChecks: unknown }).woodReviewChecks = runWoodBrowserChecks(samples);
}
renderer.render(scene, camera);
window.requestAnimationFrame(() => {
  renderer.render(scene, camera);
  document.querySelector("#status")!.textContent = "Ready · production renderer · neutral tone mapping";
  (window as unknown as { woodReviewReady: boolean }).woodReviewReady = true;
});
