/** Product-sized bathroom finishes. Joint widths are visual allowances unless noted. */
import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";
import { buildOnyxMaps, disposeOnyxTextures } from "./onyxMaps";
import { buildTileMaps, disposeTileMaps } from "./tileMaps";
import { tileRepeatSizeM, type TileStyle } from "./tilePixels";

export {
  sampleTile, TILE_RENDER_SETTINGS, TILE_STYLES, tileRepeatSizeM, tileStyleOrNull, type TileStyle,
} from "./tilePixels";
export { buildTileMaps, onTileMapsReady, tileMapsSettled } from "./tileMaps";

export function createTileMaterial(mode: "nordic" | "schematic", style: TileStyle,
  schematicColor: THREE.ColorRepresentation): THREE.MeshStandardMaterial {
  if (style.print && mode === "nordic") {
    const onyx = buildOnyxMaps(style);
    if (onyx) return new THREE.MeshPhysicalMaterial({
      color: 0xffffff, metalness: 0, roughness: 1, map: onyx.color, normalMap: onyx.normal,
      roughnessMap: onyx.orm, clearcoatMap: onyx.orm, clearcoat: 0.25, clearcoatRoughness: 0.12, ior: 1.5,
    });
  }
  const maps = mode === "nordic" ? buildTileMaps(style) : null;
  return new THREE.MeshStandardMaterial({
    color: maps ? 0xffffff : schematicColor, metalness: 0,
    roughness: mode === "schematic" ? 1 : maps ? 1 : style.roughness,
    map: maps?.color ?? null, normalMap: maps?.normal ?? null, roughnessMap: maps?.roughness ?? null,
    flatShading: mode === "schematic",
  });
}

/** Project coordinates keep phase through clipped room parts and independent of camera. */
export function applyTileUv(geometry: THREE.BufferGeometry, center: PlanCenter, style: TileStyle): void {
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  const [width, height] = tileRepeatSizeM(style);
  for (let i = 0; i < positions.count; i++) {
    const [x, y] = projectScenePointToPlan(positions.getX(i), positions.getZ(i), center);
    uv[i * 2] = x / width; uv[i * 2 + 1] = y / height;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

export function disposeTileTextures(): void {
  disposeTileMaps();
  disposeOnyxTextures();
}
