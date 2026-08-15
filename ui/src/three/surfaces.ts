// One place that knows how a plain lit surface is built, for the ~15 builder sites that used to
// spell out `new THREE.MeshStandardMaterial({ ..., roughness: mode === "nordic" ? X : 1,
// flatShading: mode === "schematic" })` by hand.
//
// The value of collecting them is not line count, it is that the two mode rules were being
// re-derived per site and had drifted: `X` was 0.85 in eleven places, 0.82 in two, 0.9 in two
// and 0.95 in one, with nothing saying whether the differences meant anything. Now they are
// four named surface classes, and a site that genuinely differs (glass, a mill-finish
// extrusion, faceted gravel) overrides and says so.
import * as THREE from "three";

export type ShadingMode = "nordic" | "schematic";

/**
 * Nordic-mode roughness by surface class. Schematic mode ignores these: it is a diagram, so
 * every surface goes fully matte (roughness 1) and picks up flat shading instead.
 *
 *  - `painted` — a finished, site-built surface: wall layers, framing, decks, stairs, casework.
 *    Just enough sheen to catch the key light and read as a plane.
 *  - `massing` — a placeable's generated box stand-in (furniture, fixtures, equipment).
 *    Physically the same painted box as `painted`, and 0.03 apart from it for no reason anyone
 *    recorded. Kept distinct only because folding it into `painted` is a visible change: it is
 *    the sole material edit in this pass that moved `shots-baseline/laptop-light-three-d.png`,
 *    measured at 0 px difference once reverted. Merge it in a change that owns that baseline.
 *  - `matte` — cast, troweled or seamed cladding: roofing layers and concrete/masonry solids.
 *    Flatter than paint; a roof plane that catches a highlight reads as wet, not as metal.
 *  - `ground` — the translucent earth sheet. Context, never a lit subject; the flattest thing
 *    in the scene so it never competes with the building standing on it.
 */
export const NORDIC_ROUGHNESS = {
  painted: 0.85, massing: 0.82, matte: 0.9, ground: 0.95,
} as const;

/**
 * A `MeshStandardMaterial` with the two mode rules already applied: nordic gets soft-lit
 * painted roughness, schematic gets flat-shaded matte. `overrides` is spread last, so a site
 * with a genuine reason to differ (glass, a mill-finish extrusion, faceted gravel) states only
 * what it is changing.
 *
 * `color` may be omitted for a material whose colour arrives per instance/vertex — three warns
 * on an explicitly `undefined` parameter, so it is left out rather than passed through.
 */
export function standardMaterial(
  color: THREE.ColorRepresentation | undefined,
  mode: ShadingMode,
  overrides: THREE.MeshStandardMaterialParameters = {},
): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    ...(color === undefined ? {} : { color }),
    roughness: mode === "nordic" ? NORDIC_ROUGHNESS.painted : 1,
    flatShading: mode === "schematic",
    ...overrides,
  });
}

/**
 * A mesh that both casts and receives the sun. Every solid piece of the building does, and the
 * pair was written out at eight call sites; missing one is invisible until a shadow is absent
 * from a render nobody is looking at.
 */
export function makeSurfaceMesh(
  geometry: THREE.BufferGeometry, material: THREE.Material | THREE.Material[],
): THREE.Mesh {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}
