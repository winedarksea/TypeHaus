// Door and window fills cut into a wall's opening void: frame, leaves, glazing, exterior
// casing, and (→ ./doorProducts) the concealed frame and lever sets. Mirrors
// resolve/geometry_openings.py; split out of ./walls.
import * as THREE from "three";
import type { DoorOperation, Opening, Wall } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import { categoryColor } from "../members";
import { projectPointToScene, type PlanCenter } from "../planGeometry";
import { NORDIC_ROUGHNESS, standardMaterial } from "../surfaces";
import {
  type AddBox, buildConcealedFrame, buildLeverSet, concealedLeaf, finishFaces, handing,
} from "./doorProducts";
import { registerSelectable } from "./registry";
import { baseRefZ } from "./wallFrame";
import { rakedTopAt } from "./walls";

// Exterior window casing — mirrors the exterior_trim part in resolve/geometry_openings.py
// (constants _WINDOW_TRIM_FACE_WIDTH_M / _WINDOW_TRIM_PROUD_DEPTH_M): a picture-frame of
// flat boards proud of the cladding plane, windows in clad walls only. The colour rides
// members.ts CATEGORY_COLOR ("window_trim"), keeping recolors a palette-only edit.
// 1 1/4" face: the visible width of standard J-channel/flat trim, chosen over a heavier
// 2 1/2" face that read as too heavy in 3D — casing and window frame are both charcoal
// here and blur into one band.
const WINDOW_TRIM_FACE_WIDTH_M = 0.032;
const WINDOW_TRIM_PROUD_DEPTH_M = 0.019;

// Mirrors resolve/geometry_openings.py::_exterior_face — the exterior cladding plane as a
// signed offset along the wall's right-hand normal, or null when the outermost depth layer
// is not cladding (a concrete wall or interior partition has no plane to sit a casing on).
function exteriorFace(wall: Wall): { plane: number; sign: number } | null {
  const layers = wall.layers.filter((layer) => !layer.is_cavity);
  if (layers.length < 2) return null;
  const outerLayer = layers[layers.length - 1];
  if (outerLayer.function.trim().toLowerCase() !== "cladding") return null;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return null;
  const nx = -(y1 - y0) / length, ny = (x1 - x0) / length;
  const project = (ring: [number, number][]) =>
    ring.map(([px, py]) => (px - x0) * nx + (py - y0) * ny);
  const outer = project(outerLayer.polygon), inner = project(layers[0].polygon);
  if (!outer.length || !inner.length) return null;
  const mean = (values: number[]) => values.reduce((a, b) => a + b, 0) / values.length;
  const outward = mean(outer) - mean(inner);
  if (Math.abs(outward) < 1e-9) return null;
  const sign = outward > 0 ? 1 : -1;
  return { plane: sign > 0 ? Math.max(...outer) : Math.min(...outer), sign };
}

export function buildOpening(parent: THREE.Group, opening: Opening, wall: Wall, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, operation: DoorOperation | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>, isGlazed = false, isTrimless = false) {
  if (opening.kind === "rough_opening") return;
  const firstChildIndex = parent.children.length;
  const [[x0, y0], [x1, y1]] = wall.axis;
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 1e-9) return;
  const direction: [number, number] = [(x1 - x0) / length, (y1 - y0) / length];
  const position: [number, number] = [x0 + direction[0] * opening.center_along_m, y0 + direction[1] * opening.center_along_m];
  const availableHeight = Math.max(0, Math.min(opening.height_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m - opening.width_m / 2), y0 + direction[1] * (opening.center_along_m - opening.width_m / 2)) - baseRefZ(wall) - opening.sill_m,
    rakedTopAt(wall, x0 + direction[0] * (opening.center_along_m + opening.width_m / 2), y0 + direction[1] * (opening.center_along_m + opening.width_m / 2)) - baseRefZ(wall) - opening.sill_m));
  if (availableHeight <= 1e-9) return;
  const rotation = Math.atan2(direction[1], direction[0]);
  const frameWidth = Math.min(0.075, opening.width_m / 4, availableHeight / 4);
  const depth = 0.08;
  // An opening in a clad wall is an exterior product: frame/mullion/stile boxes take the
  // charcoal exterior tone, doors and windows alike, and the frame extends from its
  // interior face out to the casing's proud face so the reveal reads charcoal instead of
  // exposing the wall layers' cut foam. Mirrors resolve/geometry_openings.py.
  const exterior = exteriorFace(wall);
  const frameMaterial = standardMaterial(
    exterior ? categoryColor("window_trim") : palette.member.wood, mode);
  // A solid leaf is white enamel indoors and the charcoal frame tone in a clad wall. Mirrors
  // resolve/geometry_openings.py::_DOOR_LEAF_KEY. Satin, not the walls' matte, so the leaf
  // catches a highlight the flat gypsum around it does not.
  const solidLeafMaterial = exterior ? frameMaterial
    : standardMaterial(categoryColor("door_leaf"), mode, { roughness: 0.45 });
  let frameDepth = depth, frameOffset = 0;
  if (exterior) {
    const outerEdge = exterior.plane + exterior.sign * WINDOW_TRIM_PROUD_DEPTH_M;
    const innerEdge = -exterior.sign * (depth / 2);
    frameDepth = Math.abs(outerEdge - innerEdge);
    frameOffset = (outerEdge + innerEdge) / 2;
  }
  const addBox = (width: number, height: number, thickness: number, along: number, elevation: number, material: THREE.Material, normalOffset = 0) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, thickness), material);
    mesh.position.copy(projectPointToScene([
      position[0] + direction[0] * along - direction[1] * normalOffset,
      position[1] + direction[1] * along + direction[0] * normalOffset], elevation, center));
    mesh.rotation.y = rotation;
    parent.add(mesh);
  };
  const midElevation = baseRefZ(wall) + opening.sill_m + availableHeight / 2;
  const floorZ = baseRefZ(wall) + opening.sill_m;
  const [hingeSign, swingSign] = handing(opening);
  const swingLeaf = operation === undefined || operation === "swing";
  const hardwareMaterial = standardMaterial(categoryColor("door_hardware"), mode,
    { metalness: 0.8, roughness: 0.35 });
  const addHardware: AddBox = (w, h, t, a, e, n) => addBox(w, h, t, a, e, hardwareMaterial, n);
  const faces = finishFaces(wall);
  if (isTrimless && opening.kind === "door" && faces && swingLeaf) {
    // A concealed frame: flush with the face the leaf swings toward, a 1/8" reveal, and the
    // rebated stop on the push side. Mirrors resolve/geometry_door_products.py.
    const linerMaterial = standardMaterial(categoryColor("door_leaf"), mode);
    const shadowMaterial = standardMaterial(categoryColor("shadow_gap"), mode,
      { roughness: NORDIC_ROUGHNESS.matte });
    const withMaterial = (material: THREE.Material): AddBox =>
      (w, h, t, a, e, n) => addBox(w, h, t, a, e, material, n);
    buildConcealedFrame(faces, swingSign, opening.width_m, floorZ, availableHeight, {
      liner: withMaterial(linerMaterial), leaf: withMaterial(solidLeafMaterial),
      stop: withMaterial(linerMaterial), shadow: withMaterial(shadowMaterial),
    });
    const [leafW, , , flush, back] = concealedLeaf(faces, swingSign, opening.width_m, floorZ,
      availableHeight);
    buildLeverSet(addHardware, -hingeSign * leafW / 2, hingeSign, [flush, back], floorZ);
    registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
    return;
  }
  if (!isTrimless) {
    addBox(frameWidth, availableHeight, frameDepth, -opening.width_m / 2 + frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(frameWidth, availableHeight, frameDepth, opening.width_m / 2 - frameWidth / 2, midElevation, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, baseRefZ(wall) + opening.sill_m + availableHeight - frameWidth / 2, frameMaterial, frameOffset);
    addBox(opening.width_m, frameWidth, frameDepth, 0, baseRefZ(wall) + opening.sill_m + frameWidth / 2, frameMaterial, frameOffset);
  }
  const panelHeight = Math.max(0.01, availableHeight - 2 * frameWidth);
  const glassMaterial = standardMaterial(0x8fb7c9, mode, { transparent: true, opacity: 0.48,
    roughness: 0.2, metalness: 0.05, depthWrite: false });
  if (opening.kind === "door" && operation === "double_swing") {
    // Two leaves meeting at a center mullion, matching the 2D French-door symbol.
    const mullionWidth = Math.min(frameWidth, (opening.width_m - 2 * frameWidth) / 6);
    const leafWidth = Math.max(0.01, (opening.width_m - 2 * frameWidth - mullionWidth) / 2);
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    addBox(mullionWidth, availableHeight, depth, 0, midElevation, frameMaterial);
    const leafMaterial = isGlazed ? glassMaterial : solidLeafMaterial;
    const leafThickness = isGlazed ? 0.015 : 0.045;
    addBox(leafWidth, panelHeight, leafThickness, -mullionWidth / 2 - leafWidth / 2, panelElevation, leafMaterial);
    addBox(leafWidth, panelHeight, leafThickness, mullionWidth / 2 + leafWidth / 2, panelElevation, leafMaterial);
    for (const side of [-1, 1]) {
      buildLeverSet(addHardware, side * mullionWidth / 2, side,
        [-leafThickness / 2, leafThickness / 2], floorZ);
    }
  } else if (opening.kind === "door" && operation === "slide") {
    // The 3D product stays closed and coplanar; a narrow meeting stile plus bottom track
    // makes the pair read as a slider without staging one panel over the wall.
    const clearWidth = opening.width_m - 2 * frameWidth;
    const stileWidth = Math.min(frameWidth / 2, clearWidth / 12);
    const panelWidth = Math.max(0.01, (clearWidth - stileWidth) / 2);
    const panelOffset = stileWidth / 2 + panelWidth / 2;
    const trackHeight = Math.min(0.02, panelHeight);
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    const panelMaterial = isGlazed ? glassMaterial : solidLeafMaterial;
    const panelThickness = isGlazed ? 0.015 : 0.045;
    addBox(stileWidth, panelHeight, depth, 0, panelElevation, frameMaterial);
    addBox(clearWidth, trackHeight, depth, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + trackHeight / 2, frameMaterial);
    addBox(panelWidth, panelHeight, panelThickness, -panelOffset, panelElevation, panelMaterial);
    addBox(panelWidth, panelHeight, panelThickness, panelOffset, panelElevation, panelMaterial);
  } else if (opening.kind === "door" && operation === "bifold") {
    // Four leaves are a centre-opening bifold's closed product arrangement. Small reveals
    // keep the fold joints legible while the leaves remain in the wall plane.
    const clearWidth = opening.width_m - 2 * frameWidth;
    const foldGap = Math.min(frameWidth / 8, clearWidth / 40);
    const leafWidth = Math.max(0.01, (clearWidth - 3 * foldGap) / 4);
    const firstLeafCenter = -clearWidth / 2 + leafWidth / 2;
    const panelElevation = baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2;
    for (let index = 0; index < 4; index++) {
      addBox(leafWidth, panelHeight, 0.045,
        firstLeafCenter + index * (leafWidth + foldGap), panelElevation, solidLeafMaterial);
    }
  } else if (opening.kind === "door" && operation === "pocket") {
    // Closed and coplanar, like the slider above. The wall over a pocket is drywalled on
    // both faces and genuinely reads solid, so the leaf is drawn filling its opening
    // rather than parked in the cavity — the cavity is modelled, but as framing members.
    // A pocket has no floor track, so unlike the slider the rail sits at the head.
    const clearWidth = Math.max(0.01, opening.width_m - 2 * frameWidth);
    const trackHeight = Math.min(0.02, panelHeight);
    const leafHeight = Math.max(0.01, panelHeight - trackHeight);
    const base = baseRefZ(wall) + opening.sill_m + frameWidth;
    addBox(clearWidth, trackHeight, depth, 0, base + panelHeight - trackHeight / 2, frameMaterial);
    addBox(clearWidth, leafHeight, 0.045, 0, base + leafHeight / 2, solidLeafMaterial);
  } else if (opening.kind === "door") {
    // A sectional overhead door's panel is a factory-finished product in its own charcoal,
    // not the wood leaf of an interior door nor the near-black trim coil its frame is drawn
    // in — at 16' wide the trim tone read as matte black across the whole elevation. The
    // colour rides the generated vocabulary ("overhead_door"), mirroring
    // resolve/geometry_openings.py::_OVERHEAD_KEY.
    const leafMaterial = isGlazed ? glassMaterial
      : operation === "overhead"
        ? standardMaterial(categoryColor("overhead_door"), mode,
          { roughness: NORDIC_ROUGHNESS.matte })
        : solidLeafMaterial;
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, isGlazed ? 0.015 : 0.045, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2, leafMaterial);
    if (swingLeaf) {
      const thickness = isGlazed ? 0.015 : 0.045;
      buildLeverSet(addHardware, -hingeSign * (opening.width_m - 2 * frameWidth) / 2, hingeSign,
        [-thickness / 2, thickness / 2], floorZ);
    }
  } else {
    addBox(Math.max(0.01, opening.width_m - 2 * frameWidth), panelHeight, 0.015, 0,
      baseRefZ(wall) + opening.sill_m + frameWidth + panelHeight / 2, glassMaterial);
  }
  if (opening.kind === "window") {
    if (exterior) {
      // Picture-frame casing on the cladding plane: two jambs beside the RO, a head band
      // over it, an apron under the sill. Mirrors resolve/geometry_openings.py, including
      // the per-board rake clip — a head band reaches past the RO span the availableHeight
      // clip already honoured, so each board checks the raked top over its own footprint.
      const trimW = WINDOW_TRIM_FACE_WIDTH_M;
      const trimOffset = exterior.plane + exterior.sign * (WINDOW_TRIM_PROUD_DEPTH_M / 2);
      const trimMaterial = standardMaterial(categoryColor("window_trim"), mode,
        { roughness: NORDIC_ROUGHNESS.matte });
      const rakedHost = wall.top_z0_m != null || wall.top_z1_m != null;
      const sillZ = baseRefZ(wall) + opening.sill_m;
      const bands: [number, number, number, number][] = [
        [trimW, availableHeight, -opening.width_m / 2 - trimW / 2, sillZ],
        [trimW, availableHeight, opening.width_m / 2 + trimW / 2, sillZ],
        [opening.width_m + 2 * trimW, trimW, 0, sillZ + availableHeight],
        [opening.width_m + 2 * trimW, trimW, 0, sillZ - trimW],
      ];
      for (const [bandW, bandH, along, baseZ] of bands) {
        let zTop = baseZ + bandH;
        if (rakedHost) {
          for (const end of [-1, 1]) {
            zTop = Math.min(zTop, rakedTopAt(wall,
              position[0] + direction[0] * (along + end * bandW / 2),
              position[1] + direction[1] * (along + end * bandW / 2)));
          }
        }
        if (zTop - baseZ <= 1e-9) continue;
        addBox(bandW, zTop - baseZ, WINDOW_TRIM_PROUD_DEPTH_M, along,
          baseZ + (zTop - baseZ) / 2, trimMaterial, trimOffset);
      }
    }
  }
  // Frame, leaf/mullion, glazing and exterior casing are one door or window: clicking any of
  // them selects the opening record, which the Inspector already knows how to edit.
  registerSelectable(parent, firstChildIndex, opening.uid, "opening", picks, byUid);
}

