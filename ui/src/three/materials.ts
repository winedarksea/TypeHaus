import * as THREE from "three";
import { familyOf } from "../nordic/palette";

/**
 * Standing-seam metal — the finish that actually reads as a building, not a massing study.
 *
 * Deliberately no modeled seam geometry and no external texture: the PWA has to work
 * offline and a mechanically seamed roof/wall covers most of the envelope, so the seam
 * rhythm and the sheet-metal "oil canning" waviness are both carried by one procedural
 * normal map shared across every surface. Per-surface `repeat` puts the 16" pan module
 * at true scale (see plans/standing_seam_design_hints.md).
 */

/** Nominal flat-pan width of a mechanically seamed panel. */
export const SEAM_PAN_WIDTH_M = 0.4064; // 16"

const NORMAL_MAP_PX = 256;
/** How many pan modules the shared normal map covers, so `repeat` stays in whole pans. */
const PANS_PER_TILE = 4;

let sharedNormalMap: THREE.Texture | null = null;

/** True when a layer's material should be finished as painted standing-seam metal. */
export function isStandingSeam(materialRef: string | null | undefined): boolean {
  if (!materialRef) return false;
  const s = materialRef.toLowerCase();
  return s.includes("seam") || (familyOf(materialRef) === "metal" && s.includes("standing"));
}

/**
 * One canvas, generated on first use and reused by every surface. Low-frequency noise is
 * the oil canning; the fine vertical striations are the anti-oil-canning ribs rolled into
 * the pan; the hard step at each pan edge is the seam itself.
 */
function standingSeamNormalMap(): THREE.Texture {
  if (sharedNormalMap) return sharedNormalMap;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = NORMAL_MAP_PX;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("2D canvas unavailable for the standing-seam normal map");
  const image = ctx.createImageData(NORMAL_MAP_PX, NORMAL_MAP_PX);
  const panPx = NORMAL_MAP_PX / PANS_PER_TILE;
  const seamPx = panPx * 0.06;

  for (let y = 0; y < NORMAL_MAP_PX; y++) {
    for (let x = 0; x < NORMAL_MAP_PX; x++) {
      const withinPan = x % panPx;
      // dx is the surface slope across the panel: the seam is a sharp pair of opposing
      // slopes at the pan edge, everything else is millimetre-scale waviness.
      let dx = 0;
      if (withinPan < seamPx) dx = -1 + withinPan / seamPx * 2;
      else if (withinPan > panPx - seamPx) dx = -(1 - (panPx - withinPan) / seamPx * 2);
      else {
        const t = (withinPan - seamPx) / (panPx - 2 * seamPx);
        dx += 0.05 * Math.sin(t * Math.PI * 14); // striations
        dx += 0.12 * Math.sin(t * Math.PI * 1.3 + y * 0.02) * Math.sin(y * 0.011); // oil canning
      }
      const dy = 0.04 * Math.sin(y * 0.05 + x * 0.003);
      const n = new THREE.Vector3(-dx, -dy, 1).normalize();
      const i = (y * NORMAL_MAP_PX + x) * 4;
      image.data[i] = (n.x * 0.5 + 0.5) * 255;
      image.data[i + 1] = (n.y * 0.5 + 0.5) * 255;
      image.data[i + 2] = (n.z * 0.5 + 0.5) * 255;
      image.data[i + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.NoColorSpace;
  sharedNormalMap = texture;
  return texture;
}

/**
 * `worldSizeM` is the surface's [across-the-pans, along-the-pans] extent in meters; it
 * only sets the texture repeat, so an approximate bounding size is fine.
 */
export function createStandingSeamMaterial(
  mode: "nordic" | "schematic",
  worldSizeM: readonly [number, number],
  color = 0xE8E8E2,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const material = new THREE.MeshPhysicalMaterial({
    // Architectural Kynar paint is dielectric — the raw metal never shows through, so
    // metalness stays near zero and the gloss comes from the clearcoat instead.
    color, metalness: 0.05, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.1,
  });
  const map = standingSeamNormalMap().clone();
  map.needsUpdate = true;
  map.repeat.set(
    Math.max(1, Math.round(worldSizeM[0] / (SEAM_PAN_WIDTH_M * PANS_PER_TILE))),
    Math.max(1, Math.round(worldSizeM[1] / (SEAM_PAN_WIDTH_M * PANS_PER_TILE))),
  );
  material.normalMap = map;
  material.normalScale = new THREE.Vector2(0.6, 0.6);
  return material;
}

/** Drop the process-wide normal map — only for teardown in tests/hot reload. */
export function disposeStandingSeamTextures(): void {
  sharedNormalMap?.dispose();
  sharedNormalMap = null;
}
