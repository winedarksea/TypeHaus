// Site and placed-object builders: the translucent ground sheet the building sits on, and the
// furniture / fixtures / equipment dropped onto it.
//
// Split out of components/Panel3D.tsx. These two share nothing with the envelope builders but
// the registry contract — the earth is context with no uid at all, and a canvas object is a
// glb (or a parametric massing) placed by position + rotation rather than resolved geometry.
import * as THREE from "three";
import type { CanvasObject, CanvasObjectType, Model, ModelPart } from "../../model/types";
import type { ResolvedNordicPalette } from "../../nordic/palette";
import {
  createPlanPrismGeometry, projectPlanRotationToSceneRadians, projectPointToScene,
  type PlanCenter,
} from "../planGeometry";
import { makeSurfaceMesh, NORDIC_ROUGHNESS, standardMaterial } from "../surfaces";
import { DEFAULT_EARTH_OPACITY } from "../../state/vocabulary";

/** The default translucency of the site sheet (→ state/vocabulary DEFAULT_EARTH_OPACITY, which
 * owns the number so the store can default to it without importing three). The Views panel can
 * drive it anywhere from here to fully opaque (→ `applyEarthOpacity`). */
export const EARTH_PLANE_OPACITY = DEFAULT_EARTH_OPACITY;
export const EARTH_PLANE_THICKNESS_M = 0.01;
export const EARTH_FALLBACK_HALF_SIZE_M = 50;

export function earthOutline(model: Model, center: PlanCenter): [number, number][] {
  const parcel = model.site?.parcel;
  if (parcel && parcel.length >= 3) return parcel.map(([x, y]) => [x, y]);
  const [cx, cz] = center;
  const half = EARTH_FALLBACK_HALF_SIZE_M;
  return [[cx - half, cz - half], [cx + half, cz - half],
    [cx + half, cz + half], [cx - half, cz + half]];
}

export function earthElevation(model: Model): number {
  return model.site?.grade_m ?? 0;
}

// Holes punched in the site sheet so the translucent earth stops where the ground was dug
// away. The rings are resolved server-side (resolve/site_earth.py → `site.earth_voids`) from
// every slab finishing at or below grade, unioned into disjoint outer boundaries — three for
// Catlin: house, garage, sunken garden.
//
// This used to be derived here from `model.rooms` on the lowest storey, which is structurally
// incapable of seeing more than one storey of one structure: a detached garage and an open-air
// sunken garden share no storey, no room set and no wall loop with the house, so the sheet
// kept cutting through them. Deriving it once engine-side also means the viewer, the IFC lot
// slab, and any future earth emitter cut exactly the same rings.
export function earthVoids(model: Model): [number, number][][] {
  return (model.site?.earth_voids ?? [])
    .filter((ring) => ring.length >= 3)
    .map((ring) => ring.map(([x, y]) => [x, y] as [number, number]));
}

export function buildEarth(
  parent: THREE.Group, model: Model, center: PlanCenter, mode: "nordic" | "schematic",
  opacity: number = EARTH_PLANE_OPACITY,
) {
  const outline = earthOutline(model, center);
  const grade = earthElevation(model);
  const geometry = createPlanPrismGeometry(
    outline, grade - EARTH_PLANE_THICKNESS_M, grade,
    earthVoids(model), center,
  );
  if (!geometry) return;
  const material = standardMaterial(0x806040, mode, {
    side: THREE.DoubleSide,
    roughness: mode === "nordic" ? NORDIC_ROUGHNESS.ground : 1,
  });
  applyEarthOpacity(material, opacity);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.earthSheet = true;
  parent.add(mesh);
}

/**
 * Point the sheet's material at an opacity, live — the Views panel slider drives this without
 * a scene rebuild (→ Panel3D setEarthOpacity).
 *
 * `depthWrite` is the part that is not decoration. A translucent sheet must stay out of the
 * depth buffer or it z-fights the slabs poking through it; a fully opaque one must write depth,
 * or the basement keeps drawing straight through the dirt that is supposed to bury it — which
 * is the whole point of dragging the slider to 100%.
 */
export function applyEarthOpacity(material: THREE.Material, opacity: number): void {
  const clamped = Math.min(1, Math.max(0, opacity));
  const solid = clamped >= 1;
  material.opacity = clamped;
  material.transparent = !solid;
  material.depthWrite = solid;
  material.needsUpdate = true;
}

export function buildCanvasObject(
  parent: THREE.Group,
  item: CanvasObject,
  type: CanvasObjectType | undefined,
  center: PlanCenter,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
  elevation: number,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
): THREE.Object3D | null {
  if (!item.position_m) return null;
  const [width, depth] = type?.footprint_m ?? [0.45, 0.45];
  const height = type?.height_m ?? 0.25;
  const parts = type?.model_parts ?? [];
  if (parts.length) {
    return buildCanvasObjectParts(parent, item, parts, center, mode, elevation, picks, byUid);
  }
  const color = item.domain === "electrical" ? 0xd69e2e
    : item.domain === "plumbing" ? 0x4299e1 : item.domain === "mechanical" ? 0x718096 : palette.member.wood;
  const material = standardMaterial(color, mode,
    { roughness: mode === "nordic" ? NORDIC_ROUGHNESS.massing : 1 });
  // Keep a configured primitive visible while a potentially large GLB loads.
  const mesh = new THREE.Mesh(canvasObjectFallbackGeometry(
    item.model_primitive ?? type?.model_primitive, width, height, depth,
  ), material);
  mesh.position.copy(projectPointToScene(item.position_m, elevation + height / 2, center));
  mesh.rotation.y = projectPlanRotationToSceneRadians(item.rotation ?? 0);
  mesh.userData.uid = item.uid;
  mesh.userData.selectionKind = "canvas_object";
  parent.add(mesh);
  picks.push(mesh);
  byUid.set(item.uid, [material]);
  return mesh;
}

/**
 * A generated multi-part massing: one BoxGeometry mesh per part, one material per distinct
 * colour, all under a single group. Every mesh carries the object's uid and lands in `picks`
 * and `byUid`, so clicking any part selects the whole object and highlights all of it — the
 * same contract the GLB-loaded branch honours.
 *
 * Parts arrive in the type's local frame (origin at the footprint centre, z=0 at the base);
 * the group carries the placement, exactly as the single-box fallback does.
 */
export function buildCanvasObjectParts(
  parent: THREE.Group,
  item: CanvasObject,
  parts: ModelPart[],
  center: PlanCenter,
  mode: "nordic" | "schematic",
  elevation: number,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
): THREE.Object3D {
  const group = new THREE.Group();
  const materials = new Map<string, THREE.MeshStandardMaterial>();
  for (const part of parts) {
    let material = materials.get(part.color);
    if (!material) {
      material = standardMaterial(new THREE.Color(part.color), mode,
        { roughness: mode === "nordic" ? NORDIC_ROUGHNESS.massing : 1 });
      materials.set(part.color, material);
    }
    const [sx, sy, sz] = part.size;
    const mesh = makeSurfaceMesh(new THREE.BoxGeometry(sx, sz, sy), material);
    // Scene axes are (plan x, height, -plan y); projectPointToScene owns that mapping for the
    // object's origin, so a part only needs its own local offset expressed the same way.
    const [cx, cy, cz] = part.center;
    mesh.position.set(cx, cz, -cy);
    mesh.userData.uid = item.uid;
    mesh.userData.selectionKind = "canvas_object";
    group.add(mesh);
    picks.push(mesh);
  }
  group.position.copy(projectPointToScene(item.position_m!, elevation, center));
  group.rotation.y = projectPlanRotationToSceneRadians(item.rotation ?? 0);
  parent.add(group);
  byUid.set(item.uid, [...materials.values()]);
  return group;
}

export function canvasObjectFallbackGeometry(
  primitive: string | null | undefined,
  width: number,
  height: number,
  depth: number,
): THREE.BufferGeometry {
  switch (primitive?.toLowerCase()) {
    case "cylinder":
      return new THREE.CylinderGeometry(Math.max(width, depth) / 2, Math.max(width, depth) / 2, height, 24);
    case "sphere":
      return new THREE.SphereGeometry(Math.max(width, height, depth) / 2, 24, 16);
    default:
      return new THREE.BoxGeometry(width, height, depth);
  }
}

// A ToRoof wall's raked top elevation at a plan point, interpolated along the wall axis
// (mirrors emit/draw/section.py::_wall_top_at_cut). Falls back to the flat z1_m top for
// ordinary rectangular walls (top_z0_m/top_z1_m both null).
