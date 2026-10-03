import * as THREE from "three";
import type { CanvasObject, Countertop, ModelPart } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE, materialColor, type MaterialAppearance } from "../../nordic/palette";
import { buildCountertop } from "./millwork";
import { buildCanvasObject } from "./site";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runCountertopTests() {
  const materials: MaterialAppearance[] = [
    { tag: "oak-counter", color: "#c9a978", finish: "hardwax-oil" },
  ];
  const palette = RESOLVED_NORDIC_PALETTE.light;
  // A 3 m x 0.3 m cantilever with a notch-free ring and a 0.1 m hole (a cut-out sink).
  const top: Countertop = {
    uid: "CT-UID", tag: "CT-BAR", storey: "main", material_ref: "oak-counter",
    profile: "eased", hosts: ["FURN-A"], host_uid: "FURN-A-UID",
    parts: [{ outline: [[0, 0], [3, 0], [3, 0.3], [0, 0.3]],
      holes: [[[1, 0.1], [1.1, 0.1], [1.1, 0.2], [1, 0.2]]] }],
    z0_m: 0.9, z1_m: 0.93,
  };
  const group = new THREE.Group();
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  buildCountertop(group, top, [0, 0], "nordic", palette, materials, picks, byUid);
  assert(group.children.length === 1, "One part draws one slab mesh");
  const mesh = group.children[0] as THREE.Mesh;
  mesh.geometry.computeBoundingBox();
  const box = mesh.geometry.boundingBox!;
  assert(Math.abs(box.min.y - 0.9) < 1e-6 && Math.abs(box.max.y - 0.93) < 1e-6,
    "The slab spans its own z0..z1");
  assert(Math.abs(box.max.x - box.min.x - 3) < 1e-6, "The slab covers its whole outline");
  assert(mesh.userData.uid === "FURN-A-UID" && mesh.userData.selectionKind === "canvas_object",
    "A slab selects its first host");
  assert(picks.length === 1, "The slab is pickable");
  const material = mesh.material as THREE.MeshStandardMaterial;
  assert(material.color.getHexString() === new THREE.Color(
    materialColor("oak-counter", palette, materials)).getHexString(),
  "The slab takes its own material's colour, not the symbol's grey");

  // A hosted cabinet drops its symbol's counter part; an unhosted one keeps it.
  const parts: ModelPart[] = [
    { center: [0, 0, 0.45], size: [0.6, 0.6, 0.9], color: "#ece6da" },
    { center: [0, 0, 0.92], size: [0.6, 0.6, 0.03], color: "#85807a", role: "counter" },
  ];
  const type = { tag: "B24", footprint_m: [0.6, 0.6], height_m: 0.93, model_parts: parts };
  const draw = (countertop_ref: string | null) => {
    const item = { uid: "FURN-A-UID", position_m: [0, 0], rotation: 0, countertop_ref } as
      unknown as CanvasObject;
    const parent = new THREE.Group();
    buildCanvasObject(parent, item, type as never, [0, 0], "nordic", palette, 0, [], new Map());
    return (parent.children[0] as THREE.Group).children.length;
  };
  assert(draw("CT-BAR") === 1, "A hosted cabinet skips its symbol counter");
  assert(draw(null) === 2, "An unhosted cabinet keeps its symbol counter");
  console.log("Countertop tests passed.");
}
