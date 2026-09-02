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
/** Major-rib pitch of a PBR exposed-fastener panel. */
export const RIBBED_PANEL_PITCH_M = 0.3048; // 12"
/** Corrugation pitch of a 7/8" corrugated exposed-fastener panel. */
export const CORRUGATED_PITCH_M = 0.0677; // 2-2/3"
/** Batten pitch of a concealed-fastener board & batten panel: its 20" net coverage. */
export const BATTEN_PITCH_M = 0.508; // 20"

// 128 px per pan. At 256 (64 px/pan) the seam ridge was only ~4 px wide and mip generation
// ate it unevenly, so the module survived at some distances and not others.
const NORMAL_MAP_PX = 512;
/** How many pan modules the shared normal map covers, so `repeat` stays in whole pans. */
const PANS_PER_TILE = 4;
export const SEAM_TILE_SIZE_M = SEAM_PAN_WIDTH_M * PANS_PER_TILE;

/**
 * One metal-panel profile: the module across the sheet and the shape standing on it.
 *
 * Three recipes share this because they share everything but the cross-section — same Kynar
 * paint, same procedural approach, same band-limiting discipline. What separates a folded
 * seam from a rolled rib from a corrugation is `ribHalfWidth` (a seam is a narrow upstand at
 * the pan edge; a PBR major rib is a wide trapezoid; a corrugation is half its own module,
 * because it has no flat at all) and how much the sheet between them wanders.
 */
export interface MetalPanelProfile {
  readonly key: string;
  /** Module across the sheet: pan width for a seam, rib pitch for a ribbed panel. */
  readonly moduleM: number;
  /** Half-width of the standing rib, as a fraction of the module. */
  readonly ribHalfWidth: number;
  /** 0 = raised cosine (a folded seam); 1 = flat-topped trapezoid (a rolled rib). */
  readonly squareness: number;
  /** Amplitude of the fine anti-oil-canning striations rolled into the flat. */
  readonly striations: number;
  /** Amplitude of the low-frequency sheet waviness — the oil canning itself. */
  readonly oilCanning: number;
}

export const SEAM_PROFILE: MetalPanelProfile = {
  key: "standing-seam", moduleM: SEAM_PAN_WIDTH_M, ribHalfWidth: 0.08, squareness: 0,
  striations: 0.05, oilCanning: 0.03,
};

/**
 * PBR exposed-fastener panel: 1-1/4" major ribs at 12" o.c., screwed flat to its supports.
 *
 * Squarer than a seam because the rib is roll-formed with a flat crown rather than folded
 * to a point, and wider — a PBR rib is roughly an inch across where a snap-lock upstand is
 * a fold. The oil-canning term is deliberately LOWER than the seam profile's: a screwed
 * panel is pulled tight against its girts every 24", where a clipped panel floats and is
 * free to wander between clips. The striations stay, since the flats are still ribbed.
 */
export const RIBBED_PANEL_PROFILE: MetalPanelProfile = {
  key: "ribbed-panel", moduleM: RIBBED_PANEL_PITCH_M, ribHalfWidth: 0.14, squareness: 0.65,
  striations: 0.05, oilCanning: 0.018,
};

/**
 * 7/8" corrugated exposed-fastener panel: a continuous sinusoid at 2-2/3", screwed through
 * its crowns. The garage walls.
 *
 * Every term differs from PBR for a reason, and getting them wrong is what would make this
 * render as PBR with a tighter pitch rather than as corrugated:
 *  - `ribHalfWidth: 0.5` — corrugated has no flat. The whole module IS the rib, so the half
 *    width is half the module; a seam (0.08) and a PBR rib (0.14) are narrow upstands
 *    standing on wide flats.
 *  - `squareness: 0` — a true sine, where PBR's crown is roll-formed flat (0.65).
 *  - `striations: 0` — anti-oil-canning striations are rolled into FLATS, and there are none.
 *  - `oilCanning: 0.010` — below PBR's 0.018: continuous corrugation stiffens the sheet, so
 *    it wanders less between fasteners than a wide flat pan does.
 */
export const CORRUGATED_PROFILE: MetalPanelProfile = {
  key: "corrugated", moduleM: CORRUGATED_PITCH_M, ribHalfWidth: 0.5, squareness: 0,
  striations: 0, oilCanning: 0.010,
};

/**
 * Board & batten concealed-fastener panel: a flat 20" pan with a ~1-1/2" applied batten
 * standing at each edge, screwed through a hidden leg. The house's north and south walls.
 *
 * The terms that separate it from "PBR with a wider module", which is exactly what it would
 * read as if they were copied:
 *  - `moduleM` = 20", the net coverage. Two and a half times a PBR rib pitch — the batten
 *    rhythm is the thing you identify this panel by from across the street.
 *  - `ribHalfWidth: 0.05` — a 2" batten on a 20" module (`ribHalfWidth` is the HALF width,
 *    so the drawn cap spans `2 x 0.05 x 20"`). A batten is NARROW relative to its module in
 *    a way no other profile here is, and copying PBR's 0.14 would draw a 5-1/2" one. 2" is
 *    the wide end of the 1-1/2"-2" the profile is made in, chosen deliberately: the shared
 *    512 px / 4-module canvas gives this cap only 6.4 px, and the module docstring records
 *    that a ridge near 4 px is where mip generation starts eating it unevenly and the
 *    rhythm survives at some distances and not others.
 *  - `squareness: 0.9` — a batten is a square applied cap with parallel sides, squarer than
 *    PBR's roll-formed crown (0.65) and far from a folded seam's point (0).
 *  - `striations: 0` — anti-oil-canning striations are rolled into NARROW flats. A 20" pan
 *    is smooth, which is half the reason it oil-cans as much as it does.
 *  - `oilCanning: 0.028` — ABOVE PBR's 0.018 and near the seam profile's 0.03, and this is
 *    the term that makes it read as board & batten rather than as wide PBR. A concealed
 *    panel floats between its legs instead of being pulled tight to a girt every 24", and
 *    a wider pan wanders more over the same span.
 */
export const BOARD_BATTEN_PROFILE: MetalPanelProfile = {
  key: "board-and-batten", moduleM: BATTEN_PITCH_M, ribHalfWidth: 0.05, squareness: 0.9,
  striations: 0, oilCanning: 0.028,
};

/** Tile size in meters for a profile, i.e. `PANS_PER_TILE` modules of it. */
export function panelTileSizeM(profile: MetalPanelProfile = SEAM_PROFILE): number {
  return profile.moduleM * PANS_PER_TILE;
}

const sharedNormalMaps = new Map<string, THREE.Texture>();

/** True when a layer's material should be finished as painted standing-seam metal. */
export function isStandingSeam(materialRef: string | null | undefined): boolean {
  if (!materialRef) return false;
  const s = materialRef.toLowerCase();
  return s.includes("seam") || (familyOf(materialRef) === "metal" && s.includes("standing"));
}

/**
 * The profile a material's AUTHORED `finish` names, or null if it names none.
 *
 * This is the dispatch that `isStandingSeam` above cannot do. That function is a substring
 * test on the material ref — it was the whole story while every metal skin in the catalog
 * had "seam" in its tag on purpose, and `pbr-panel-26` deliberately does not play that
 * game. A material that declares `finish: "ribbed-panel"` gets the ribbed profile because
 * it SAYS so, and the substring test stays as the fallback for the four that don't.
 */
export function metalPanelProfileForFinish(
  finish: string | null | undefined,
): MetalPanelProfile | null {
  if (finish === "ribbed-panel") return RIBBED_PANEL_PROFILE;
  if (finish === "corrugated") return CORRUGATED_PROFILE;
  if (finish === "board-and-batten") return BOARD_BATTEN_PROFILE;
  if (finish === "standing-seam") return SEAM_PROFILE;
  return null;
}

/**
 * One canvas, generated on first use and reused by every surface. The ridge at each pan edge
 * is the seam itself; the fine vertical striations are the anti-oil-canning ribs rolled into
 * the pan; a trace of low-frequency waviness is the oil canning.
 *
 * Everything here is deliberately band-limited. This map is minified hard (a 12 m wall spans
 * ~18 repeats) and viewed at grazing angles, so any slope discontinuity or any wander that
 * varies pan-to-pan survives filtering only in patches — which reads as random grey streaks
 * rather than as siding. A smooth ridge profile and a waviness term with no per-row phase
 * keep the 16" rhythm identical on every pan and at every distance.
 */
function metalPanelNormalMap(profile: MetalPanelProfile = SEAM_PROFILE): THREE.Texture {
  const cached = sharedNormalMaps.get(profile.key);
  if (cached) return cached;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = NORMAL_MAP_PX;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error(`2D canvas unavailable for the ${profile.key} normal map`);
  const image = ctx.createImageData(NORMAL_MAP_PX, NORMAL_MAP_PX);
  const panPx = NORMAL_MAP_PX / PANS_PER_TILE;
  const seamPx = panPx * profile.ribHalfWidth;

  // A trapezoid's slope is zero across its flat crown and constant up its two webs. Blending
  // the sine bump toward that shape by `squareness` is what turns a folded seam into a rolled
  // rib without introducing the slope STEP a true trapezoid would have at the crown edges —
  // and a step is exactly what mip filtering could not carry when the seam was a linear ramp.
  const ribSlope = (u: number): number => {
    const round = Math.sin(u * Math.PI);
    // A plateau, not a bump: zero at the crown (u→0) and at the toe (u→1), and a constant
    // slope over the flank between them. That IS the trapezoid this is blending toward — one
    // lit face and one shaded one, not a highlight-and-shadow crease within the flank.
    const square = Math.sin(Math.min(1, u * 2.2) * Math.PI * 0.5)
      * Math.sin(Math.min(1, (1 - u) * 2.2) * Math.PI * 0.5);
    return round * (1 - profile.squareness) + square * profile.squareness;
  };

  for (let y = 0; y < NORMAL_MAP_PX; y++) {
    for (let x = 0; x < NORMAL_MAP_PX; x++) {
      const withinPan = x % panPx;
      // dx is the surface slope across the panel: the rib stands off the module boundary,
      // everything else is millimetre-scale waviness. The rib's slope is one full period
      // straddling that boundary — a lit face and a shaded face, meeting the flat at zero
      // slope on both sides, so mip filtering carries no discontinuity across it.
      let dx = 0;
      if (withinPan < seamPx) dx = -ribSlope(withinPan / seamPx);
      else if (withinPan > panPx - seamPx) dx = ribSlope((panPx - withinPan) / seamPx);
      else {
        const t = (withinPan - seamPx) / (panPx - 2 * seamPx);
        dx += profile.striations * Math.sin(t * Math.PI * 14);
        dx += profile.oilCanning * Math.sin(t * Math.PI * 1.3);
      }
      const dy = 0.015 * Math.sin(y * 0.05 + x * 0.003);
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
  sharedNormalMaps.set(profile.key, texture);
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
  profile: MetalPanelProfile = SEAM_PROFILE,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const material = new THREE.MeshPhysicalMaterial({
    // Architectural Kynar paint is dielectric — the raw metal never shows through, so
    // metalness stays near zero and the gloss comes from the clearcoat instead.
    color, metalness: 0.05, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.1,
  });
  const map = metalPanelNormalMap(profile).clone();
  map.needsUpdate = true;
  const tileM = panelTileSizeM(profile);
  // Wall extrusion UVs are based on the polygon's local shape and therefore rotate or
  // collapse as wall runs change direction. Wall cladding opts into explicit world-scaled
  // UVs below; roof surfaces retain the legacy surface-size repeat until they have their
  // own slope-aware coordinate frame.
  map.repeat.set(
    worldScaledUv ? 1 : Math.max(1, Math.round(worldSizeM[0] / tileM)),
    worldScaledUv ? 1 : Math.max(1, Math.round(worldSizeM[1] / tileM)),
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
  profile: MetalPanelProfile = SEAM_PROFILE,
): void {
  const tileM = panelTileSizeM(profile);
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
    uv[index * 2] = along / tileM;
    uv[index * 2 + 1] = elevation / tileM;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/** Drop the process-wide normal maps — only for teardown in tests/hot reload. */
export function disposeStandingSeamTextures(): void {
  for (const texture of sharedNormalMaps.values()) texture.dispose();
  sharedNormalMaps.clear();
}

// ── Masonry (brick / CMU / stone veneer) ──────────────────────────────────────────────
// Like the standing-seam finish above, the coursing + recessed mortar + per-unit colour
// variation are carried by shared procedural maps (colour + normal), world-scaled so units
// sit at true size. No external texture, so the offline PWA still renders it.
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
/** Glen-Gery Roman Maximus including joints: 23⅝" × 1⅝" unit + ⅜" joints both ways
 * (garage wainscot) — a 24" × 2" module, long and low next to modular's 8" × 2⅔". */
export const ROMAN_MAXIMUS_UNIT_M: readonly [number, number] = [0.6096, 0.0508]; // [length, course]
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
// Glazed forest-green brick over a dark mortar. Like the white brick the unit colour is fixed
// (a ceramic glaze, not a clay body), so it ignores the brick-red family colour, and jitter is
// muted lower still — a fired glaze is the most uniform masonry face on this house.
const GLAZED_GREEN_BRICK_STYLE: MasonryStyle = {
  key: "glazed-green-brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.06, halfLap: 0.5, mortar: "#4a4f49", base: "#1b4332",
  jitterHSL: [0.004, 0.015, 0.04],
};
// The Ishtar scheme on the sunken garden's veneer. Lapis field and gold
// registers are the same fired glaze as the green above, so they take the same near-zero
// jitter and a dark mortar; they differ only in the unit colour, which is fixed for the same
// reason the green's is — a ceramic glaze is not a clay body and must not take the
// brick-red family colour.
const GLAZED_LAPIS_BRICK_STYLE: MasonryStyle = {
  key: "glazed-lapis-brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.06, halfLap: 0.5, mortar: "#3c4756", base: "#10386a",
  jitterHSL: [0.004, 0.015, 0.04],
};
// The register bands sit inside the lapis field, so they share its mortar — a band that
// changed the joint colour too would read as a separate wall rather than a course of this one.
const GLAZED_GOLD_BRICK_STYLE: MasonryStyle = {
  key: "glazed-gold-brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.06, halfLap: 0.5, mortar: "#3c4756", base: "#c08a12",
  jitterHSL: [0.004, 0.015, 0.04],
};
// The plinth under them: a light, uniform brown over tan mortar, near-zero jitter like the
// glazes above it. Full red-brick jitter at this wall's scale reads as mixed pallets rather
// than clay variegation, so the glaze/no-glaze contrast is carried by the sheen and the tan
// mortar joint instead.
const BROWN_BRICK_STYLE: MasonryStyle = {
  key: "brown-brick", unitM: BRICK_UNIT_M, unitsPerTile: 3, coursesPerTile: 6,
  jointFraction: 0.05, halfLap: 0.5, mortar: "#cfc8ba", base: "#a07c5c",
  jitterHSL: [0.004, 0.015, 0.04],
};
// The garage wainscot: Glen-Gery Columbia Roman Maximus, ASTM C216 Grade SW Type FBA,
// THROUGH-BODY — takes the brown plinth's unglazed recipe retinted, not the glazes' low-jitter
// one; near-zero jitter for the same reason the plinth has it, since a wide jitter at a 4'
// wainscot's scale reads as mixed pallets, not clay. `unitsPerTile: 1` because the Maximus
// unit is itself 24" long, unlike modular's 3-per-tile 8" unit.
// Kept in step with _FINISH_BASE in packages/engine/src/typehaus/emit/gltf/palette.py BY
// HAND — the two tables mirror each other and nothing enforces it.
const ROMAN_MAXIMUS_BRICK_STYLE: MasonryStyle = {
  key: "roman-maximus-brick", unitM: ROMAN_MAXIMUS_UNIT_M, unitsPerTile: 1, coursesPerTile: 8,
  jointFraction: 0.016, halfLap: 0.5, mortar: "#b9b2a2", base: "#e4ddc9",
  jitterHSL: [0.004, 0.015, 0.04],
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
  "glazed-green-brick": GLAZED_GREEN_BRICK_STYLE,
  "glazed-lapis-brick": GLAZED_LAPIS_BRICK_STYLE,
  "glazed-gold-brick": GLAZED_GOLD_BRICK_STYLE,
  "brown-brick": BROWN_BRICK_STYLE,
  "roman-maximus-brick": ROMAN_MAXIMUS_BRICK_STYLE,
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
 *
 * `baseZM` is the elevation the coursing is laid FROM, and it matters more than it looks: a
 * bricklayer starts at the bottom and only cuts at the top, so this measures from the wall's
 * own `z0_m`, not project zero — the sunken garden's veneer sits with its base at -101", so
 * measuring from zero would render its bottom course as a third of a brick and cut every band
 * above it too. The reference house's register bands are all whole multiples of the 2⅔"
 * course off `WALL_BASE`, so once the wall courses from its base every band lands on a bed
 * joint by construction.
 */
export function applyMasonryWallUv(
  geometry: THREE.BufferGeometry,
  wallAxis: readonly [readonly [number, number], readonly [number, number]],
  center: PlanCenter,
  tileSizeM: readonly [number, number] = MASONRY_TILE_SIZE_M,
  baseZM = 0,
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
    uv[index * 2 + 1] = (elevation - baseZM) / tileSizeM[1];
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

// ── Aluminum deck boards (Wahoo AridDeck-style) ───────────────────────────────────────
// Same trick as the standing seam above — one shared procedural normal map, world-scaled
// UVs, no external texture — but the module is a 5½" plank and the modulation is a
// *recessed* drainage gap between planks rather than a raised seam. An extruded aluminum
// plank is far stiffer than roll-formed sheet, so there is deliberately no oil canning
// here; only a faint lengthwise mill/brush grain.

/** Nominal face width of one aluminum deck plank. */
export const DECK_BOARD_WIDTH_M = 0.1397; // 5½"
/** Drainage gap between adjacent planks — the visible groove. */
const DECK_BOARD_GAP_M = 0.00635; // ¼"
/** How many planks the shared normal map covers, so `repeat` stays in whole boards. */
const BOARDS_PER_TILE = 4;
const DECK_TILE_SIZE_M = DECK_BOARD_WIDTH_M * BOARDS_PER_TILE;
const DECK_NORMAL_MAP_PX = 256;
/** Mill-finish aluminum plank; mirrors the `aluminum-deck` material colour. */
export const ALUMINUM_DECK_BASE_COLOR = 0xb9bcc0;

let sharedDeckBoardNormalMap: THREE.Texture | null = null;

/** True when a surface's material should be finished as aluminum plank decking. */
export function isAluminumDeckBoard(materialRef: string | null | undefined): boolean {
  if (!materialRef) return false;
  const s = materialRef.toLowerCase();
  return s.includes("deck") && (s.includes("alum") || familyOf(materialRef) === "metal");
}

/**
 * One canvas, generated on first use and shared by every deck surface. Each plank edge is a
 * pair of opposing slopes falling into the gap (the inverse of a standing seam's raised
 * ridge); the pan between them carries only a faint high-frequency grain.
 */
function deckBoardNormalMap(): THREE.Texture {
  if (sharedDeckBoardNormalMap) return sharedDeckBoardNormalMap;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = DECK_NORMAL_MAP_PX;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("2D canvas unavailable for the deck-board normal map");
  const image = ctx.createImageData(DECK_NORMAL_MAP_PX, DECK_NORMAL_MAP_PX);
  const boardPx = DECK_NORMAL_MAP_PX / BOARDS_PER_TILE;
  const halfGapPx = boardPx * (DECK_BOARD_GAP_M / DECK_BOARD_WIDTH_M) / 2;

  for (let y = 0; y < DECK_NORMAL_MAP_PX; y++) {
    for (let x = 0; x < DECK_NORMAL_MAP_PX; x++) {
      const withinBoard = x % boardPx;
      // dx is the surface slope across the plank. Both halves of a groove straddle a board
      // boundary, so the wall on this board's left edge falls the opposite way from the
      // wall on its right edge — together they read as a channel, not a ridge.
      let dx = 0;
      if (withinBoard < halfGapPx) dx = 1 - withinBoard / halfGapPx;
      else if (withinBoard > boardPx - halfGapPx) dx = -(1 - (boardPx - withinBoard) / halfGapPx);
      else dx = 0.03 * Math.sin(withinBoard * 1.7); // extrusion/brush grain along the plank
      const n = new THREE.Vector3(-dx, 0, 1).normalize();
      const i = (y * DECK_NORMAL_MAP_PX + x) * 4;
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
  sharedDeckBoardNormalMap = texture;
  return texture;
}

/**
 * Plank decking finish. Always paired with applyDeckBoardUv, which supplies the world-scaled
 * UVs this material's `repeat` of 1 assumes.
 */
export function createDeckBoardMaterial(
  mode: "nordic" | "schematic",
  color: THREE.ColorRepresentation = ALUMINUM_DECK_BASE_COLOR,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true });
  }
  const material = new THREE.MeshPhysicalMaterial({
    // Powder-coated extrusion: mostly dielectric paint over metal, with a low clearcoat for
    // the satin sheen. Slightly more metallic than painted siding, far less than raw mill.
    color, metalness: 0.2, roughness: 0.55, clearcoat: 0.2, clearcoatRoughness: 0.25,
  });
  const map = deckBoardNormalMap().clone();
  map.needsUpdate = true;
  material.normalMap = map;
  material.normalScale = new THREE.Vector2(0.8, 0.8);
  return material;
}

/**
 * Give a deck surface's board map a stable architectural coordinate frame: the map's x-axis
 * is across the 5½" planks, so tying it to project X makes every board run north–south —
 * perpendicular to the house (and to the balcony's east–west joists), which is how plank
 * decking is actually laid. The prism's thin edge faces inherit the same frame; at 1½" of
 * plank thickness the smear is invisible next to getting the top face right.
 */
export function applyDeckBoardUv(geometry: THREE.BufferGeometry, center: PlanCenter): void {
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    uv[index * 2] = projectX / DECK_TILE_SIZE_M;
    uv[index * 2 + 1] = projectY / DECK_TILE_SIZE_M;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/** Drop the process-wide deck-board normal map — only for teardown in tests/hot reload. */
export function disposeDeckBoardTextures(): void {
  sharedDeckBoardNormalMap?.dispose();
  sharedDeckBoardNormalMap = null;
}
