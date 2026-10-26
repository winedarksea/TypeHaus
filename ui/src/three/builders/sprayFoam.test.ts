import * as THREE from "three";
import type { Catalog, Roof, Solid, Wall } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import { ALL_TRADES, type Trade } from "../../state/vocabulary";
import { buildSolid, buildRoof } from "./structure";
import { buildWall } from "./walls";
import { buildSprayFoamMaps } from "../sprayFoamMaterial";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runSprayFoamBuilderTests(): void {
  // A custom tag proves that the authored finish, rather than a name match, dispatches.
  const catalog = {
    materials: [{ tag: "custom-fill", name: "Fill", finish: "spray-foam", color: "#e8d9b5" }],
    assemblies: [{ tag: "A", layers: [{ name: "foam", function: "insulation", material: "custom-fill", thickness_m: 0.1 }] }],
  } as Catalog;
  const palette = RESOLVED_NORDIC_PALETTE.light;
  const wall = {
    uid: "W", tag: "W", axis: [[0, 0], [4, 0]], z0_m: 0, z1_m: 3, members: [], trades: ["insulation"],
    layers: [{ name: "foam", function: "insulation", material: "custom-fill", thickness_m: 0.1,
      polygon: [[0, 0], [4, 0], [4, 0.1], [0, 0.1]], control: [], trades: ["insulation"] }],
  } as unknown as Wall;
  const solid = {
    uid: "S", tag: "S", category: "rim_spray_foam", material: "custom-fill", assembly: null,
    outline: [[0, 0], [4, 0], [4, 0.1], [0, 0.1]], voids: [], z0_m: 0, z1_m: 0.2,
  } as unknown as Solid;
  const roof: Roof = {
    uid: "R", tag: "R", storey: "attic", form: "gable", footprint: [[0, 0], [4, 0], [4, 3], [0, 3]],
    eave_z_m: 3, ridge_z_m: 4, ridge_direction: "x", assembly: "A", surface_area_m2: 15, members: [], provenance: null,
  };
  for (const mode of ["nordic", "schematic"] as const) {
    const tradeGroups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as Record<Trade, THREE.Group>;
    const picks: THREE.Mesh[] = [], byUid = new Map<string, THREE.Material[]>();
    buildWall(tradeGroups, wall, [], [0, 0], mode, palette, picks, byUid, catalog.materials);
    const solids = new THREE.Group(), roofs = new THREE.Group();
    buildSolid(solids, solid, [0, 0], mode, palette, catalog, picks, byUid);
    buildRoof(roofs, roof, [0, 0], mode, palette, catalog, picks, byUid);
    const meshes: THREE.Mesh[] = [];
    for (const group of [...Object.values(tradeGroups), solids, roofs]) group.traverse(object => {
      if (object instanceof THREE.Mesh) meshes.push(object);
    });
    assert(meshes.length === 3, "Wall, roof and solid all render their foam");
    for (const mesh of meshes) {
      const material = mesh.material as THREE.MeshStandardMaterial;
      const positions = mesh.geometry.getAttribute("position"), uv = mesh.geometry.getAttribute("uv");
      assert(uv?.count === positions.count && Array.from(uv.array).every(Number.isFinite), "Every foam vertex receives finite UVs");
      assert(material.color.getHexString() === "e8d9b5", "All builders retain the authored foam color");
      assert(mode === "nordic" ? material.normalMap === buildSprayFoamMaps().normal
        : material.normalMap === null && material.flatShading, "All builders respect the presentation mode");
    }
    assert(picks.length === 3 && byUid.has("W") && byUid.has("S") && byUid.has("R"), "Texture routing preserves selection registration");
  }
}
