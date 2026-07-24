import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";
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
const SEAM_TILE_SIZE_M = SEAM_PAN_WIDTH_M * PANS_PER_TILE;

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
  worldScaledUv = false,
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
  // Wall extrusion UVs are based on the polygon's local shape and therefore rotate or
  // collapse as wall runs change direction. Wall cladding opts into explicit world-scaled
  // UVs below; roof surfaces retain the legacy surface-size repeat until they have their
  // own slope-aware coordinate frame.
  map.repeat.set(
    worldScaledUv ? 1 : Math.max(1, Math.round(worldSizeM[0] / SEAM_TILE_SIZE_M)),
    worldScaledUv ? 1 : Math.max(1, Math.round(worldSizeM[1] / SEAM_TILE_SIZE_M)),
  );
  material.normalMap = map;
  material.normalScale = new THREE.Vector2(0.6, 0.6);
  return material;
}

/**
 * Give a wall's standing-seam map a stable architectural coordinate frame. The map's
 * x-axis is across the 16-inch pans, so its seam ridges stay constant along the wall's
 * horizontal run and continue vertically from the wall base to its top.
 */
export function applyStandingSeamWallUv(
  geometry: THREE.BufferGeometry,
  wallAxis: readonly [readonly [number, number], readonly [number, number]],
  center: PlanCenter,
): void {
  const [[x0, y0], [x1, y1]] = wallAxis;
  const dx = x1 - x0;
  const dy = y1 - y0;
  const length = Math.hypot(dx, dy);
  if (length < 1e-9) return;
  const directionX = dx / length;
  const directionY = dy / length;
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    const elevation = positions.getY(index);
    const along = (projectX - x0) * directionX + (projectY - y0) * directionY;
    uv[index * 2] = along / SEAM_TILE_SIZE_M;
    uv[index * 2 + 1] = elevation / SEAM_TILE_SIZE_M;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/** Drop the process-wide normal map — only for teardown in tests/hot reload. */
export function disposeStandingSeamTextures(): void {
  sharedNormalMap?.dispose();
  sharedNormalMap = null;
}

// ── Masonry (brick / CMU / stone veneer) ──────────────────────────────────────────────
// The old path painted masonry as one flat fill, so a brick veneer read as drywall. Like
// the standing-seam finish above, the coursing + recessed mortar + per-unit colour variation
// are carried by shared procedural maps (colour + normal), world-scaled so units sit at true
// size. No external texture, so the offline PWA still renders it.
//
// A masonry layer is finished according to a MasonryStyle named by the material's authored
// `finish` (catalog), or inferred from its ref when the material declares none:
//   • CMU / concrete block → the big 16"×8" nominal face module, grey, tight uniform coursing
//     (visually distinct from brick, which shares the "masonry" hatch family but is 8"×2⅔").
//   • white brick → the brick module but a whitewashed unit colour over GREY mortar (a
//     selectable finish variant; `finish: "white-brick"`, or a ref saying "white"/"limewash").
//   • everything else (default) → the classic red-brick running bond over tan mortar.

/** Nominal running-bond module including joints: modular brick is 8" × 2⅔" with ⅜" joints. */
export const BRICK_UNIT_M: readonly [number, number] = [0.2032, 0.0679]; // [length, course]
/** Nominal CMU face module including joints: a standard block is 16" × 8" with ⅜" joints. */
export const CMU_UNIT_M: readonly [number, number] = [0.4064, 0.2032]; // [length, course]
const MASONRY_TEX_PX = 512;

/**
 * The recipe for one masonry finish: unit module, how many units/courses a repeat tile spans,
 * the running-bond offset, joint width (as a fraction of the unit length), mortar colour, an
 * optional fixed unit colour (null → use the palette-resolved family colour), and the per-unit
 * HSL jitter magnitude. `key` seeds the map cache so distinct styles never collide.
 */
export interface MasonryStyle {
  readonly key: string;
  readonly unitM: readonly [number, number]; // [length, course], nominal incl. joints
  readonly unitsPerTile: number;
  readonly coursesPerTile: number;
  readonly jointFraction: number; // joint width ÷ unit length
  readonly halfLap: number; // bond offset ÷ unit length on odd courses (0.5 = running bond)
  readonly mortar: string; // CSS hex
  readonly base: string | null; // fixed unit hex, or null to take the palette family colour
  readonly jitterHSL: readonly [number, number, number]; // [hue, sat, light] jitter magnitude
}

const BRICK_STYLE: MasonryStyle = {
  key: "brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.05, halfLap: 0.5, mortar: "#cfc8ba", base: null,
  jitterHSL: [0.02, 0.08, 0.16],
};
// White brick over grey mortar. The unit colour is fixed (whitewashed clay), so it ignores the
// brick-red family colour; jitter is muted because painted/whitewashed brick reads uniform.
const WHITE_BRICK_STYLE: MasonryStyle = {
  key: "white-brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.06, halfLap: 0.5, mortar: "#8f8f8c", base: "#e9e6df",
  jitterHSL: [0.006, 0.02, 0.05],
};
// Concrete block: the large face module, a fixed neutral grey, tighter joints and very low
// jitter so it reads as cast block rather than laid brick.
const CMU_STYLE: MasonryStyle = {
  key: "cmu", unitM: CMU_UNIT_M, unitsPerTile: 2, coursesPerTile: 3,
  jointFraction: 0.028, halfLap: 0.5, mortar: "#b6b3ac", base: "#9c988f",
  jitterHSL: [0.004, 0.015, 0.05],
};

/** True when a wall layer's cladding should be finished as brick/block/stone masonry. */
export function isMasonry(materialRef: string | null | undefined): boolean {
  return familyOf(materialRef) === "masonry";
}

/** True when a masonry material is concrete masonry unit / block, not brick or stone. */
export function isCmu(materialRef: string | null | undefined): boolean {
  if (familyOf(materialRef) !== "masonry") return false;
  const s = (materialRef ?? "").toLowerCase();
  return s.includes("cmu") || s.includes("block") || s.includes("concrete mason");
}

/** True when a brick material opts into the whitewashed / white-brick finish variant. */
function isWhiteBrickRef(materialRef: string | null | undefined): boolean {
  const s = (materialRef ?? "").toLowerCase();
  return s.includes("white") || s.includes("limewash") || s.includes("whitewash");
}

/**
 * The finish recipes a material can name via its authored `Material.finish`. Keys are the
 * engine's finish vocabulary (model/materials.py); the Python glTF emitter mirrors this table.
 */
export const MASONRY_STYLES: Readonly<Record<string, MasonryStyle>> = {
  brick: BRICK_STYLE,
  "white-brick": WHITE_BRICK_STYLE,
  cmu: CMU_STYLE,
};

/**
 * Pick the masonry finish recipe. An authored `finish` from the catalog is definitive — that
 * is the material declaring its own appearance. Absent one (or naming a recipe this build does
 * not know), fall back to inferring from the ref: CMU → white brick → default red brick.
 */
export function masonryStyleFor(
  materialRef: string | null | undefined, finish?: string | null,
): MasonryStyle {
  const declared = finish ? MASONRY_STYLES[finish] : undefined;
  if (declared) return declared;
  if (isCmu(materialRef)) return CMU_STYLE;
  if (isWhiteBrickRef(materialRef)) return WHITE_BRICK_STYLE;
  return BRICK_STYLE;
}

/** World size (meters) of one repeat tile for a style: [along-wall length, up-wall height]. */
export function masonryTileSizeM(style: MasonryStyle): readonly [number, number] {
  return [style.unitM[0] * style.unitsPerTile, style.unitM[1] * style.coursesPerTile];
}

/** Default (red brick) repeat tile size, retained for callers/tests keyed to the brick module. */
export const MASONRY_TILE_SIZE_M: readonly [number, number] = masonryTileSizeM(BRICK_STYLE);

// Keyed by style + base-colour hex: the colour is baked into the map, so each finish/colour
// combination needs one tile. The map stays small (only a couple ever exist per session).
const masonryMapCache = new Map<string, { colorMap: THREE.Texture; normalMap: THREE.Texture }>();

// Deterministic per-unit jitter so a course looks laid, not printed — no Math.random, so the
// two shared maps stay reproducible across reloads.
function hashUnit(course: number, unit: number): number {
  const h = Math.sin(course * 12.9898 + unit * 78.233) * 43758.5453;
  return h - Math.floor(h);
}

// `unitColor` is already resolved (authored → style.base → family) by createMasonryMaterial;
// this only lays the bond and jitters each unit around it.
function buildMasonryMaps(
  style: MasonryStyle, unitColor: THREE.Color,
): { colorMap: THREE.Texture; normalMap: THREE.Texture } {
  const key = `${style.key}:${unitColor.getHexString()}`;
  const cached = masonryMapCache.get(key);
  if (cached) return cached;
  const colorCanvas = document.createElement("canvas");
  const normalCanvas = document.createElement("canvas");
  colorCanvas.width = colorCanvas.height = MASONRY_TEX_PX;
  normalCanvas.width = normalCanvas.height = MASONRY_TEX_PX;
  const cctx = colorCanvas.getContext("2d");
  const nctx = normalCanvas.getContext("2d");
  if (!cctx || !nctx) throw new Error("2D canvas unavailable for masonry maps");

  const courseH = MASONRY_TEX_PX / style.coursesPerTile;
  const unitW = MASONRY_TEX_PX / style.unitsPerTile;
  const jointPx = Math.max(2, unitW * style.jointFraction);
  const offsetPx = unitW * style.halfLap;

  cctx.fillStyle = style.mortar;
  cctx.fillRect(0, 0, MASONRY_TEX_PX, MASONRY_TEX_PX);
  // Normal map: flat (recessed joints are drawn as darker steps, i.e. z-facing everywhere,
  // joints tilted). Base is the neutral +Z normal (128,128,255).
  nctx.fillStyle = "rgb(128,128,255)";
  nctx.fillRect(0, 0, MASONRY_TEX_PX, MASONRY_TEX_PX);

  const base = unitColor.clone();
  for (let course = 0; course < style.coursesPerTile; course++) {
    const y = course * courseH;
    const offset = course % 2 === 0 ? 0 : offsetPx; // running bond: alternate half-lap
    for (let unit = -1; unit < style.unitsPerTile + 1; unit++) {
      const x = unit * unitW + offset;
      const jitter = hashUnit(course, unit);
      const shade = base.clone().offsetHSL(
        (jitter - 0.5) * style.jitterHSL[0],
        (jitter - 0.5) * style.jitterHSL[1],
        (jitter - 0.5) * style.jitterHSL[2],
      );
      cctx.fillStyle = `#${shade.getHexString()}`;
      cctx.fillRect(x + jointPx / 2, y + jointPx / 2, unitW - jointPx, courseH - jointPx);
      // Bevel the unit edges in the normal map so the recessed mortar catches light.
      nctx.fillStyle = "rgb(150,128,235)"; // faces +X near the left joint
      nctx.fillRect(x + jointPx / 2, y + jointPx / 2, jointPx, courseH - jointPx);
      nctx.fillStyle = "rgb(106,128,235)"; // faces −X near the right joint
      nctx.fillRect(x + unitW - jointPx * 1.5, y + jointPx / 2, jointPx, courseH - jointPx);
      nctx.fillStyle = "rgb(128,150,235)";
      nctx.fillRect(x + jointPx / 2, y + jointPx / 2, unitW - jointPx, jointPx);
      nctx.fillStyle = "rgb(128,106,235)";
      nctx.fillRect(x + jointPx / 2, y + courseH - jointPx * 1.5, unitW - jointPx, jointPx);
    }
  }

  const colorMap = new THREE.CanvasTexture(colorCanvas);
  colorMap.wrapS = colorMap.wrapT = THREE.RepeatWrapping;
  colorMap.colorSpace = THREE.SRGBColorSpace;
  const normalMap = new THREE.CanvasTexture(normalCanvas);
  normalMap.wrapS = normalMap.wrapT = THREE.RepeatWrapping;
  normalMap.colorSpace = THREE.NoColorSpace;
  const maps = { colorMap, normalMap };
  masonryMapCache.set(key, maps);
  return maps;
}

/**
 * Brick/CMU/stone masonry finish. `style` selects the module + mortar + jitter recipe (see
 * masonryStyleFor). The unit colour resolves authored → recipe default → family: an authored
 * `Material.color` is the material speaking for itself and outranks the recipe's stock hex, so
 * two white-brick materials with different whites render differently; `style.base` covers the
 * recipes that carry a fixed unit colour (CMU, white brick); `color` — the palette family
 * colour — is the last resort for a recipe that leaves its unit colour open (default red brick).
 */
export function createMasonryMaterial(
  mode: "nordic" | "schematic", style: MasonryStyle, color: THREE.ColorRepresentation,
  authoredColor?: string | null,
): THREE.Material {
  const unitColor = authoredColor ?? style.base ?? color;
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({
      color: unitColor, roughness: 1, metalness: 0, flatShading: true,
    });
  }
  const { colorMap, normalMap } = buildMasonryMaps(style, new THREE.Color(unitColor));
  return new THREE.MeshStandardMaterial({
    color: 0xffffff, // colour lives in the map; white base avoids double-tinting
    map: colorMap,
    normalMap,
    normalScale: new THREE.Vector2(0.5, 0.5),
    roughness: 0.94,
    metalness: 0,
  });
}

/**
 * World-scaled UVs for a masonry wall layer: courses run true-height up the wall and units
 * run true-length along it, so the bond stays put as walls change direction (same coordinate
 * frame idea as the standing-seam wall UV). `tileSizeM` is the chosen style's repeat extent.
 */
export function applyMasonryWallUv(
  geometry: THREE.BufferGeometry,
  wallAxis: readonly [readonly [number, number], readonly [number, number]],
  center: PlanCenter,
  tileSizeM: readonly [number, number] = MASONRY_TILE_SIZE_M,
): void {
  const [[x0, y0], [x1, y1]] = wallAxis;
  const dx = x1 - x0;
  const dy = y1 - y0;
  const length = Math.hypot(dx, dy);
  if (length < 1e-9) return;
  const directionX = dx / length;
  const directionY = dy / length;
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    const elevation = positions.getY(index);
    const along = (projectX - x0) * directionX + (projectY - y0) * directionY;
    uv[index * 2] = along / tileSizeM[0];
    uv[index * 2 + 1] = elevation / tileSizeM[1];
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/** Drop the process-wide masonry maps — only for teardown in tests/hot reload. */
export function disposeMasonryTextures(): void {
  for (const { colorMap, normalMap } of masonryMapCache.values()) {
    colorMap.dispose();
    normalMap.dispose();
  }
  masonryMapCache.clear();
}
