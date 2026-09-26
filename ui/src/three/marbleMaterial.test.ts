import * as THREE from "three";
import { buildMarbleMap, createMarbleMaterial, isVeinedMarble } from "./marbleMaterial";
import { tiledFbm } from "./valueNoise";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Pure (no-canvas) assertions: the recipe routing, the SSR fallback and the seamless noise.
// The map itself needs a 2D canvas and is exercised in the browser.
export function runMarbleMaterialTests() {
  assert(isVeinedMarble("veined-marble"), "the declared finish selects the marble recipe");
  assert(!isVeinedMarble("vinyl-sheet") && !isVeinedMarble(null) && !isVeinedMarble("tile"),
    "only the declared FINISH selects it, never a material tag");

  assert(buildMarbleMap() === null, "no 2D canvas: no map, and no throw");
  const flat = createMarbleMaterial("nordic", "#f0ede7", 0.5) as THREE.MeshStandardMaterial;
  assert(flat.map === null && flat.roughness === 0.5 && flat.color.getHexString() === "f0ede7",
    "without a canvas the floor is a flat fill in its own colour and sheen");
  const schematic = createMarbleMaterial("schematic", "#f0ede7", 0.5) as THREE.MeshStandardMaterial;
  assert(schematic.map === null && schematic.roughness === 1 && schematic.flatShading,
    "schematic mode is a flat diagram fill");

  // Integer frequencies wrap: the tile edge matches the opposite edge.
  const octaves = [[2, 1], [4, 0.5], [8, 0.25]] as const;
  for (const t of [0, 0.13, 0.5, 0.87]) {
    assert(Math.abs(tiledFbm(0, t, octaves) - tiledFbm(1, t, octaves)) < 1e-9
      && Math.abs(tiledFbm(t, 0, octaves) - tiledFbm(t, 1, octaves)) < 1e-9,
      "the noise is seamless across the tile edge");
  }
}
