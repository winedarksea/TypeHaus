// Door and window fills cut into a wall's opening void. The engine serves every product part
// as resolved rings (`opening.opening_parts`, server/model_json_opening_parts.py) and this file
// extrudes them as served: it owns the materials and the picking, never a dimension.
import * as THREE from "three";
import type { DoorTypeSpec, Opening, OpeningPart, Vec2, Wall } from "../../model/types";
import { authoredAppearance, materialColor, type MaterialAppearance } from "../../nordic/palette";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { categoryColor } from "../members";
import { createPlanPrismGeometry, projectPointToScene, type PlanCenter } from "../planGeometry";
import { NORDIC_ROUGHNESS, standardMaterial } from "../surfaces";
import { buildDoorway } from "./doorway";
import { authoredPiece } from "./openingPieces";
import { registerSelectable } from "./registry";
import { boardBoxGeometry, pieceSeed, woodMaterialsForGeometry } from "../woodPiece";
import { boardStyleFor } from "./millwork";
import { createPlankMaterial } from "../plankMaterial";
import type { PlankStyle } from "../plankLayout";

// The door's charcoal wrap is a sub-millimetre skin over a red isolation film. At normal
// house-view distances, the flashing material's coating bias can put that film ahead of the
// wrap in the depth buffer. Let the visible steel win the tie without changing either layer's
// measured geometry.
const DOOR_TRIM_WRAP_DEPTH_BIAS = {
  polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2,
} as const;

// Finishes the engine keys flat; every other product key is a satin paint.
const MATTE_KEYS = new Set(["shadow_gap", "overhead_door"]);

export interface OpeningProductOptions {
  // The bookcase body's species: its boards carry the `oak_bookcase` key and no catalog ref.
  bookcaseDoor?: DoorTypeSpec["bookcase_door"];
  materials?: readonly MaterialAppearance[];
}

type PartMaterial = { material: THREE.Material; style: PlankStyle | null };

/** One material per finish, shared by every solid of the opening that carries it. */
function partMaterials(mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined, bookcaseRef: string | undefined) {
  const cache = new Map<string, PartMaterial>();
  const cached = (key: string, build: () => PartMaterial) => {
    let entry = cache.get(key);
    if (!entry) cache.set(key, entry = build());
    return entry;
  };
  const product = (ref: string) => cached(`ref:${ref}`, () => {
    const color = materialColor(ref, palette, materials);
    const style = boardStyleFor(ref, materials);
    return { style, material: style
      ? createPlankMaterial(mode, style, color, undefined, authoredAppearance(ref, materials))
      : standardMaterial(color, mode, { roughness: 0.45 }) };
  });
  return (part: OpeningPart): PartMaterial => {
    const key = part.material_key;
    // A glazed leaf stays glass whatever finish its catalog names for the leaf.
    if (key === "glass") return cached(key, () => ({ style: null, material: standardMaterial(
      categoryColor("glass"), mode, { transparent: true, opacity: 0.48, roughness: 0.2,
        metalness: 0.05, depthWrite: false }) }));
    if (part.material_ref) return product(part.material_ref);
    if (key === "oak_bookcase" && bookcaseRef) return product(bookcaseRef);
    const exteriorTrim = part.key.split(":")[0] === "exterior_trim";
    return cached(exteriorTrim ? "exterior_trim" : key, () => ({ style: null, material:
      key === "door_hardware" ? standardMaterial(categoryColor(key), mode,
        { metalness: 0.8, roughness: 0.35 })
      // An interior schematic frame is the member wood, which the palette themes.
      : key === "opening_frame" ? standardMaterial(palette.member.wood, mode)
      : key === "window_trim" && !exteriorTrim ? standardMaterial(categoryColor(key), mode)
      : MATTE_KEYS.has(key) || exteriorTrim ? standardMaterial(categoryColor(key), mode,
        { roughness: NORDIC_ROUGHNESS.matte })
      : standardMaterial(categoryColor(key), mode, { roughness: 0.45 }) }));
  };
}

/** The box a rectangular ring extrudes to, for a wood finish's grain; null for any other ring. */
function ringBoxMatrix(ring: readonly Vec2[], z0: number, z1: number,
  center: PlanCenter): THREE.Matrix4 | null {
  if (ring.length !== 4) return null;
  const [a, b, c, d] = ring;
  const u = [b[0] - a[0], b[1] - a[1]], v = [c[0] - b[0], c[1] - b[1]];
  const lu = Math.hypot(u[0], u[1]), lv = Math.hypot(v[0], v[1]);
  if (lu < 1e-9 || lv < 1e-9 || Math.abs(u[0] * v[0] + u[1] * v[1]) > 1e-4 * lu * lv
    || Math.hypot(d[0] - a[0] - v[0], d[1] - a[1] - v[1]) > 1e-5) return null;
  return new THREE.Matrix4().compose(
    projectPointToScene([(a[0] + c[0]) / 2, (a[1] + c[1]) / 2], (z0 + z1) / 2, center),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.atan2(u[1], u[0])),
    new THREE.Vector3(lu, z1 - z0, lv));
}

export function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  options: OpeningProductOptions, picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return;
  const { materials, bookcaseDoor } = options;
  const firstChildIndex = parent.children.length;
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const openingCenter: [number, number] = [
    x0 + direction[0] * opening.center_along_m,
    y0 + direction[1] * opening.center_along_m,
  ];
  const rotation = Math.atan2(direction[1], direction[0]);
  // Section normal offsets are relative to the wall axis.
  buildDoorway(opening, openingCenter, direction, center, parent, (ref, materialKey) =>
    standardMaterial(materialKey === "window_trim" ? categoryColor("window_trim")
      : new THREE.Color(materialColor(ref, palette, materials)), mode,
      materialKey === "door_hardware" ? { metalness: 0.8, roughness: 0.35 }
        : { metalness: 0, roughness: 0.45 }));
  if (opening.kind === "rough_opening") {   // only its floor-transition strip draws
    if (parent.children.length > firstChildIndex) {
      registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
    }
    return;
  }
  for (const board of opening.doorway?.exterior_placement?.boards ?? []) {
    const material = standardMaterial(board.role && board.role !== "door_installation"
      ? materialColor(board.material_ref, palette, materials)
      : categoryColor(board.material_key === "window_trim" ? "window_trim" : "door_frame"),
    mode, {
      roughness: 0.45,
      ...(board.role === "door_trim_wrap" ? DOOR_TRIM_WRAP_DEPTH_BIAS : {}),
    });
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(board.width_m, board.height_m,
      board.depth_m), material);
    mesh.position.copy(projectPointToScene([
      openingCenter[0] + direction[0] * board.along_m - direction[1] * board.normal_m,
      openingCenter[1] + direction[1] * board.along_m + direction[0] * board.normal_m,
    ], board.z_m, center));
    mesh.rotation.y = rotation;
    mesh.userData.doorInstallation = board.name;
    mesh.userData.piece = `installation:${board.name}`;
    parent.add(mesh);
  }
  const materialOf = partMaterials(mode, palette, materials, bookcaseDoor?.material_ref ?? undefined);
  const along = ([x, y]: Vec2) =>
    (x - openingCenter[0]) * direction[0] + (y - openingCenter[1]) * direction[1];
  for (const part of opening.opening_parts ?? []) {
    const { material, style } = materialOf(part);
    // Frame boards are named by where they sit within the part (→ ./openingPieces).
    const spans = part.solids.map(solid => solid.ring.map(along));
    const partA0 = Math.min(...spans.flat()), partA1 = Math.max(...spans.flat());
    const partMid = (partA0 + partA1) / 2;
    const midZ = (Math.min(...part.solids.map(s => s.z0_m))
      + Math.max(...part.solids.map(s => s.z1_m))) / 2;
    for (const [index, solid] of part.solids.entries()) {
      const box = style && ringBoxMatrix(solid.ring, solid.z0_m, solid.z1_m, center);
      const geometry = box
        ? boardBoxGeometry(box, style, pieceSeed(`${opening.uid}|${part.key}|${index}`))
        : createPlanPrismGeometry(solid.ring, solid.z0_m, solid.z1_m, [], center);
      if (!geometry) continue;
      const mesh = new THREE.Mesh<THREE.BufferGeometry, THREE.Material | THREE.Material[]>(
        geometry, box ? woodMaterialsForGeometry(material, geometry) : material);
      mesh.userData.piece = authoredPiece(part.key, index, Math.min(...spans[index]) - partMid,
        Math.max(...spans[index]) - partMid, solid.z0_m, solid.z1_m, partA1 - partA0, midZ);
      parent.add(mesh);
    }
  }
  // Frame, leaf, glazing, casing and hardware are one door or window: clicking any of them
  // selects the opening record, which the Inspector already knows how to edit.
  registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
}
