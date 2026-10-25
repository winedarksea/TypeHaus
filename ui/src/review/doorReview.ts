import * as THREE from "three";
import type { Model, Opening } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildOpening } from "../three/builders/openings";
import { buildDoorCasing } from "../three/builders/millwork";
import { buildWall } from "../three/builders/walls";
import { buildFloor, buildRoomFloor, buildSolid } from "../three/builders/structure";
import { ALL_TRADES, type Trade } from "../state/vocabulary";

const model: Model = await (await fetch("/__door-review-house")).json();
const params = new URLSearchParams(location.search), view = params.get("view");
const exteriorReview = view?.startsWith("exterior") ?? false;
const dark = params.get("theme") === "dark";
const mode = params.get("theme") === "schematic" ? "schematic" : "nordic";
const palette = RESOLVED_NORDIC_PALETTE[dark ? "dark" : "light"];
const failures: string[] = [], records: unknown[] = [];
const materials = model.catalog!.materials;
const oakRef = materials.find(material => material.species === "oak")?.tag;
const cedarRef = materials.find(material => material.species === "cedar")?.tag;
if (!oakRef || !cedarRef) failures.push("Review requires catalog oak and cedar materials");
if (dark) { document.body.style.background = "#22262a"; document.body.style.color = "#eaeaea"; }
const cases = exteriorReview ? ["D-M-ENTRY", "D-M-BALC"].flatMap(tag => [-1, 1].map(side =>
  ({ tag, side, label: `${tag} · ${side < 0 ? "exterior" : "interior"} · threshold unresolved` })))
  : view === "synthetic" ? [
  { tag: "D-M-MUD", side: 1, label: "Shared swing type · inherited white frame" },
  { tag: "D-M-MUD", side: 1, label: "Shared swing type · oak frame", frame: oakRef },
  { tag: "D-M-MUD", side: -1, label: "Independent oak frame / cedar leaf", frame: oakRef, leaf: cedarRef },
  { tag: "D-M-LAUN", side: -1, label: "Pocket · oak frame / inherited white leaf", frame: oakRef },
] : ["D-M-MUD", "D-M-LAUN"].flatMap(tag => [-1, 1].map(side => ({ tag, side, label: `${tag} · ${side < 0 ? "negative" : "positive"} room face` })));
for (const sample of cases) {
  const original = model.openings.find(o => o.tag === sample.tag)!;
  const spec = sample as typeof sample & { frame?: string; leaf?: string };
  const opening: Opening = { ...original, effective_frame_material_ref: spec.frame ?? original.effective_frame_material_ref,
    effective_leaf_material_ref: spec.leaf ?? original.effective_leaf_material_ref };
  const wall = model.walls.find(w => w.tag === opening.host)!;
  const type = model.catalog!.door_types.find(t => t.tag === opening.type_ref)!;
  const [a, b] = wall.axis, angle = Math.atan2(b[1] - a[1], b[0] - a[0]);
  const center: [number, number] = [a[0] + Math.cos(angle) * opening.center_along_m,
    a[1] + Math.sin(angle) * opening.center_along_m];
  const scene = new THREE.Scene(); scene.background = new THREE.Color(dark ? 0x22262a : 0xe5e3df);
  scene.add(new THREE.HemisphereLight(0xffffff, dark ? 0x46403a : 0xb8b1a7, 0.9));
  const sun = new THREE.DirectionalLight(0xffffff, 2.5); sun.position.set(-3, 5, 6);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -3, right: 3, top: 4, bottom: -2, near: 0.1, far: 20 });
  sun.shadow.normalBias = 0.0005; scene.add(sun);
  const group = new THREE.Group(), picks: THREE.Mesh[] = [], byUid = new Map<string, THREE.Material[]>();
  const groups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
  buildWall(groups, wall, model.openings.filter(o => o.host === wall.tag), center, mode, palette,
    [], new Map(), materials);
  groups.framing.visible = false;
  Object.values(groups).forEach(g => group.add(g));
  buildOpening(group, opening, wall, center, mode, palette, { operation: type.operation,
    glazed: type.glazed, trimless: type.trimless, bookcaseDoor: type.bookcase_door,
    leafSet: type.leaf_set, materials }, picks, byUid);
  for (const casing of model.door_casings ?? []) if (casing.opening_uid === opening.uid) {
    buildDoorCasing(group, casing, center, mode, palette, materials, picks, byUid);
  }
  if (exteriorReview) {
    for (const solid of (model.solids ?? []).filter(s => s.tag.startsWith(`${opening.tag}-FLASH-`))) {
      buildSolid(group, solid, center, mode, palette, model.catalog, [], new Map(), materials);
    }
    for (const adjacent of opening.doorway?.adjacent_floors ?? []) {
      if (!adjacent) continue;
      const deck = model.floors?.find(f => f.tag === adjacent.deck_tag);
      if (deck) buildFloor(group, deck, center, mode, palette, [], new Map(), groups.framing, materials);
      const room = model.rooms.find(r => r.tag === adjacent.room_tag);
      if (room) buildRoomFloor(group, room, adjacent.deck_top_m, center, mode, palette,
        materials, [], new Map());
    }
  }
  const base = opening.cased_product?.base_z_m ?? (wall.plate_base_z_m ?? wall.z0_m) + opening.sill_m;
  group.position.y = -base; group.rotation.y = angle; scene.add(group);
  const floor = new THREE.Mesh(new THREE.BoxGeometry(4, 0.04, 4),
    new THREE.MeshStandardMaterial({ color: dark ? 0x77756e : 0xc2b6a1, roughness: 0.8 }));
  floor.position.y = -0.02;
  if (!exteriorReview) scene.add(floor);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(775, 480); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  scene.traverse(object => { if (object instanceof THREE.Mesh) { object.castShadow = true; object.receiveShadow = true; } });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1;
  const floorView = view === "floor" || view === "exterior-floor";
  const jambView = view === "jamb" || view === "exterior-jamb";
  const detail = jambView || floorView;
  const span = detail ? (exteriorReview ? 0.8 : 0.34) : 2.5;
  const camera = new THREE.OrthographicCamera(-span * 775 / 480 / 2, span * 775 / 480 / 2,
    span / 2, -span / 2, 0.01, 50);
  const target = new THREE.Vector3(jambView ? opening.width_m / 2 - 0.02 : 0,
    floorView ? 0.08 : jambView ? 1.25 : 1.08, 0);
  camera.position.copy(target).add(new THREE.Vector3(detail ? 1.6 : 0.18, detail ? 0.24 : 0.08, -sample.side * 4));
  camera.lookAt(target); renderer.render(scene, camera);
  const figure = document.createElement("figure"), caption = document.createElement("figcaption");
  caption.textContent = sample.label;
  if (opening.cased_product && view === "floor") caption.textContent +=
    ` · ${opening.cased_product.undercut_m * 1000} mm above higher finished floor`;
  if (opening.cased_product && view === "jamb") caption.textContent +=
    ` · ${opening.cased_product.leaf_gap_m * 1000} mm leaf gap / ${opening.cased_product.casing_reveal_m * 1000} mm casing reveal`;
  figure.append(caption, renderer.domElement);
  document.querySelector("#cards")!.append(figure);
  if (!picks.length || !byUid.has(opening.uid)) failures.push(`${opening.tag}: missing selection`);
  records.push({ tag: opening.tag, type: type.tag, side: sample.side,
    frame: opening.effective_frame_material_ref, leaf: opening.effective_leaf_material_ref,
    cased_product: opening.cased_product, selectableMeshes: picks.length });
}
Object.assign(window, { doorReviewReady: true, doorReviewChecks: { failures, records } });
