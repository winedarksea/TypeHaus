// The plants: engine-built procedural prototypes (resolve/plant_models.py), drawn instanced.
//
// One InstancedMesh per (storey, prototype, part). A plant's bounding prism still rides in
// `model.solids` under the same uid — it is the pick and Inspector record, and scene.ts skips
// drawing it when an instance draws the plant. The GLB mirrors this (emit/gltf/plants.py):
// same prototypes, same role colours, same base-to-tip shade.
import * as THREE from "three";
import type { PlantInstance, PlantModel, PlantModelPart, Solid } from "../../model/types";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";
import { standardMaterial } from "../surfaces";

/** Vertex shade at the root; 1.0 at the top. Mirrors emit/gltf/plants.py SHADE_BASE. */
export const SHADE_BASE = 0.7;
const PLANT_UID_BY_INSTANCE = "plantUidByInstance";
const HIGHLIGHT_OPACITY = 0.3;

/** A prototype part in scene frame (x, z, -y), indexed, with the engine's vertex normals. */
export function plantPartGeometry(
  model: PlantModel, part: PlantModelPart, shade: boolean,
): THREE.BufferGeometry {
  const q = model.quantum;
  const count = part.positions.length / 3;
  const positions = new Float32Array(count * 3);
  const colors = shade ? new Float32Array(count * 3) : null;
  const height = model.height || 1;
  for (let i = 0; i < count; i++) {
    const x = part.positions[3 * i] * q;
    const y = part.positions[3 * i + 1] * q;
    const z = part.positions[3 * i + 2] * q;
    positions.set([x, z, -y], 3 * i);
    if (colors) {
      const s = SHADE_BASE + (1 - SHADE_BASE) * Math.min(Math.max(z / height, 0), 1);
      colors.set([s, s, s], 3 * i);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  if (colors) geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.setIndex(part.indices);
  // Area-weighted, as resolve/plant_models.vertex_normals computes them for the GLB.
  geometry.computeVertexNormals();
  return geometry;
}

/** Place one plant: plan position and z, a turn about plan z, scale (spread, spread, height). */
export function composePlantMatrix(
  target: THREE.Matrix4, plant: PlantInstance, center: PlanCenter,
): THREE.Matrix4 {
  const [sx, sy, sz] = plant.scale;
  return target.compose(
    new THREE.Vector3(plant.x - center[0], plant.z, -(plant.y - center[1])),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), plant.rotation),
    new THREE.Vector3(sx, sz, sy),
  );
}

/** The uids `model.plants` draws, whose `plant` solids therefore do not. */
export function instancedPlantUids(
  plants: readonly PlantInstance[] | undefined, models: readonly PlantModel[] | undefined,
): Set<string> {
  const refs = new Set((models ?? []).map((model) => model.ref));
  return new Set((plants ?? []).filter((plant) => refs.has(plant.model)).map((p) => p.uid));
}

/** The plant uid a raycast hit resolved to, or null when the hit object draws no plants. */
export function resolvePlantPickUid(
  object: THREE.Object3D, instanceId: number | null | undefined,
): string | null {
  const uids = object.userData[PLANT_UID_BY_INSTANCE] as string[] | undefined;
  if (!Array.isArray(uids) || instanceId == null) return null;
  return uids[instanceId] ?? null;
}

/**
 * Draw every plant in `plants` (all on one storey, the caller groups them) into `parent`.
 * Materials are shared per (colour, sidedness) through `cache`, which the caller keeps for
 * one scene build. Plants cast shadows but do not receive them: grass self-shadowing is noise.
 */
export function buildPlants(
  parent: THREE.Group, plants: readonly PlantInstance[], models: readonly PlantModel[],
  center: PlanCenter, mode: "nordic" | "schematic", picks: THREE.Mesh[],
  cache: Map<string, THREE.Material> = new Map(),
): THREE.InstancedMesh[] {
  const byRef = new Map(models.map((model) => [model.ref, model]));
  const groups = new Map<string, PlantInstance[]>();
  for (const plant of plants) {
    if (!byRef.has(plant.model)) continue;
    const list = groups.get(plant.model) ?? [];
    list.push(plant);
    groups.set(plant.model, list);
  }
  const shade = mode === "nordic";
  const out: THREE.InstancedMesh[] = [];
  const matrix = new THREE.Matrix4();
  for (const [ref, members] of [...groups].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))) {
    const model = byRef.get(ref)!;
    for (const part of model.parts) {
      const color = model.colors[part.role] ?? model.colors.foliage;
      const key = `${color}|${part.two_sided}|${mode}`;
      let material = cache.get(key);
      if (!material) {
        material = standardMaterial(color, mode, {
          roughness: 0.95, vertexColors: shade,
          side: part.two_sided ? THREE.DoubleSide : THREE.FrontSide,
        });
        cache.set(key, material);
      }
      const mesh = new THREE.InstancedMesh(plantPartGeometry(model, part, shade), material,
        members.length);
      members.forEach((plant, index) => mesh.setMatrixAt(index, composePlantMatrix(matrix, plant, center)));
      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
      mesh.castShadow = true;
      mesh.receiveShadow = false;
      mesh.userData[PLANT_UID_BY_INSTANCE] = members.map((plant) => plant.uid);
      parent.add(mesh);
      picks.push(mesh);
      out.push(mesh);
    }
  }
  return out;
}

/** A selected plant: its bounding solid, translucent, since its instances share materials. */
export function buildPlantHighlight(
  solid: Solid, center: PlanCenter, color: THREE.ColorRepresentation,
): THREE.Object3D | null {
  const geometry = createPlanPrismGeometry(solid.outline, solid.z0_m,
    Math.max(solid.z1_m, solid.z0_m + 0.01), [], center);
  if (!geometry) return null;
  const group = new THREE.Group();
  group.add(new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
    color, transparent: true, opacity: HIGHLIGHT_OPACITY, depthWrite: false,
  })));
  group.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 1),
    new THREE.LineBasicMaterial({ color, depthTest: false })));
  group.renderOrder = 999;
  return group;
}
