// ── Wood planks (T&G paneling / plank and strip flooring / LVP) ──────────────────────────
// Same trick as the masonry section of `materials.ts`: the board module, the joint and the
// per-board tone variation ride shared procedural maps (colour + normal), world-scaled so
// boards sit at true size. No external texture, so the offline PWA still renders it, and —
// like brick — no per-board geometry (plans/01-decisions.md #23 keeps placed members
// wood-framing-only). The board layout and figure live in `plankLayout.ts`.
//
// The recipes, because a paneling board, a milled floor board and a printed plank are not
// the same product:
//   • `tg-board` — 3½" exposed face, a V-groove at each joint, continuous runs. The sauna
//     liner is 7'-6" and the wainscot 3', so neither has end joints worth drawing.
//   • `shiplap` — 5½" exposed face, a wider reveal at each joint, continuous runs. The sauna
//     liner is shiplap, not T&G, so the `*-tg` ref inference below cannot see it — a profile
//     change that renames the tag needs its own needle.
//   • `strip-floor` — 2¼" strip, random 1'–4' lengths, butt joints, white-oak figure.
//   • `plank-floor` — owner-milled 3⅛" face, random 1'–7' lengths, butt joints (sanded
//     flush), every board its own wood.
//   • `lvp-plank` — 7"×48" click-lock, micro-bevelled on all four edges, and a print that
//     repeats every six boards: format, bevel and repeat are how LVP reads as LVP.
//   • `oak-board` — solid oak millwork: one jointless board per piece, no seams.
//
// None carries a fixed unit colour. Every wood material authors its own `Material.color`
// (basswood #e6d4ae, walnut #5d4433, white oak under a water-based clear #c9b08c), and that
// is the colour a species *is* — a recipe that overrode it would make walnut and basswood
// render identically.
import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";
import {
  boardShade, drawBoardFigure, layoutPlankTile, type PlankStyle,
} from "./plankLayout";

export type { PlankStyle } from "./plankLayout";

const INCH = 0.0254;

// 5/4 and 4/4 tongue-and-groove paneling: a 1x4/5/4x4 board shows ~3½" of face once the
// tongue is buried. The V-groove is the only joint a T&G board has — there is no mortar to
// draw and no stagger, because these runs are short enough to be single boards.
const TG_BOARD_STYLE: PlankStyle = {
  key: "tg-board", faceWidthM: 0.0889, boardsPerTile: 6, lengths: { kind: "continuous" },
  tileAlongM: 0.0889 * 6, pxPerM: 960, jointFraction: 0.045, jointProfile: "vee",
  jitter: 0.07, grain: 0.35, figure: "streak", printRepeat: 0, reliefScale: 0.6,
};

// 5/4 shiplap: a 1x6 board shows ~5½" of face once the rabbet is lapped, so the module is
// wider than the T&G's and the reveal at each joint is a broader shadow line. Drawn with the
// same `vee` joint the T&G uses — a square reveal and a V-groove are the same channel at this
// scale.
const SHIPLAP_STYLE: PlankStyle = {
  key: "shiplap", faceWidthM: 0.1397, boardsPerTile: 4, lengths: { kind: "continuous" },
  tileAlongM: 0.1397 * 4, pxPerM: 920, jointFraction: 0.045, jointProfile: "vee",
  jitter: 0.07, grain: 0.35, figure: "streak", printRepeat: 0, reliefScale: 0.6,
};

// 2¼" white-oak strip. Butt joints rather than a groove (a strip floor is sanded flat, so
// the joint is a line, not a channel), short random lengths, and the widest tone spread: a
// strip floor laid from mixed boards is the most variegated surface in the house.
const STRIP_FLOOR_STYLE: PlankStyle = {
  key: "strip-floor", faceWidthM: 2.25 * INCH, boardsPerTile: 12,
  lengths: { kind: "random", minM: 12 * INCH, maxM: 48 * INCH }, tileAlongM: 96 * INCH,
  pxPerM: 800, jointFraction: 0.02, jointProfile: "butt", jitter: 0.13, grain: 0.5,
  figure: "oak", printRepeat: 0, reliefScale: 0.6,
};

// Owner-milled white oak: the 3⅛" exposed face `takeoff/hardwood.py` covers with, random
// 1'–7' lengths off the mill, sanded flush.
const PLANK_FLOOR_STYLE: PlankStyle = {
  key: "plank-floor", faceWidthM: 3.125 * INCH, boardsPerTile: 10,
  lengths: { kind: "random", minM: 12 * INCH, maxM: 84 * INCH }, tileAlongM: 120 * INCH,
  pxPerM: 700, jointFraction: 0.02, jointProfile: "butt", jitter: 0.12, grain: 0.5,
  figure: "oak", printRepeat: 0, reliefScale: 0.5,
};

// White-oak-look click-lock LVP, 7"×48". Low jitter (a print is colour-managed), a shallow
// embossed relief, and the bevel carries the joint instead.
const LVP_PLANK_STYLE: PlankStyle = {
  key: "lvp-plank", faceWidthM: 7 * INCH, boardsPerTile: 6,
  lengths: { kind: "fixed", lenM: 48 * INCH }, tileAlongM: 96 * INCH, pxPerM: 700,
  jointFraction: 0.012, jointProfile: "bevel", jitter: 0.05, grain: 0.45, figure: "oak",
  printRepeat: 6, reliefScale: 0.45,
};

// Solid white-oak millwork (stools, treads, shelves): no joints at all, four 16" boards of
// distinct tone across the tile so each piece can take its own (→ woodPiece.ts).
const OAK_BOARD_STYLE: PlankStyle = {
  key: "oak-board", faceWidthM: 16 * INCH, boardsPerTile: 4, lengths: { kind: "continuous" },
  tileAlongM: 96 * INCH, pxPerM: 600, jointFraction: 0, jointProfile: "butt", jitter: 0.08,
  grain: 0.5, figure: "oak", printRepeat: 0, reliefScale: 0.3,
};

/**
 * The finish recipes a wood material can name via its authored `Material.finish`. Keys are the
 * engine's finish vocabulary (model/materials.py), the same contract MASONRY_STYLES follows.
 */
export const WOOD_PLANK_STYLES: Readonly<Record<string, PlankStyle>> = {
  "tg-board": TG_BOARD_STYLE,
  "shiplap": SHIPLAP_STYLE,
  "strip-floor": STRIP_FLOOR_STYLE,
  "plank-floor": PLANK_FLOOR_STYLE,
  "lvp-plank": LVP_PLANK_STYLE,
  "oak-board": OAK_BOARD_STYLE,
};

// Flooring refs inferred without an authored recipe. Deliberately explicit: the `familyOf`
// substring table in nordic/palette.ts has no wood-species needles at all, and adding some
// there would move colour resolution too — plus its Python mirror in emit/draw/palette.py.
const FLOOR_REF_STYLES: Readonly<Record<string, PlankStyle>> = {
  oak: STRIP_FLOOR_STYLE,
  lvp: LVP_PLANK_STYLE,
};

/**
 * True when a solid-board paneling ref. The library names T&G `<species>-tg` by convention;
 * a shiplap says so in the tag (`sauna-shiplap`). The shiplap needle is not optional — the
 * tag no longer ends in `-tg`, so without it a lined sauna would fall out of `isWoodPlank`
 * entirely and render as flat fill, which is worse than rendering as the wrong profile.
 */
function isBoardPanelingRef(materialRef: string | null | undefined): boolean {
  const s = (materialRef ?? "").toLowerCase();
  return s.endsWith("-tg") || s.includes("tongue") || s.includes("shiplap");
}

/** True when a surface's material should be finished as wood boards, judged by ref alone. */
export function isWoodPlank(materialRef: string | null | undefined): boolean {
  if (!materialRef) return false;
  const s = materialRef.toLowerCase();
  if (WOOD_PLANK_STYLES[s]) return true;
  return isBoardPanelingRef(s) || s in FLOOR_REF_STYLES;
}

/**
 * Pick the wood finish recipe. An authored `finish` from the catalog is definitive — that is
 * the material declaring its own appearance. Absent one (or naming a recipe this build does
 * not know, as `walnut-tg`'s "clear-satin-hardwax-oil" does), infer from the ref: a known
 * flooring ref, else T&G paneling.
 */
export function plankStyleFor(
  materialRef: string | null | undefined, finish?: string | null,
): PlankStyle {
  const declared = finish ? WOOD_PLANK_STYLES[finish] : undefined;
  if (declared) return declared;
  const ref = (materialRef ?? "").toLowerCase();
  const floor = FLOOR_REF_STYLES[ref];
  if (floor) return floor;
  return ref.includes("shiplap") ? SHIPLAP_STYLE : TG_BOARD_STYLE;
}

/**
 * The recipe, or null when the surface is not boards. A declared recipe wins whatever the
 * tag — a house-local floor (`oak-floor-custom`) is boards because it says so, not because
 * its name matches a needle. Without one, only a ref `isWoodPlank` recognises is boarded.
 */
export function plankStyleOrNull(
  materialRef: string | null | undefined, finish?: string | null,
): PlankStyle | null {
  if (finish && WOOD_PLANK_STYLES[finish]) return WOOD_PLANK_STYLES[finish];
  return isWoodPlank(materialRef) ? plankStyleFor(materialRef, finish) : null;
}

/** World size (metres) of one repeat tile: [across the boards, along them]. */
export function plankTileSizeM(style: PlankStyle): readonly [number, number] {
  return [style.faceWidthM * style.boardsPerTile, style.tileAlongM];
}

// Keyed by recipe alone. Unlike the masonry maps, these bake in no colour: they are pure
// LUMINANCE (white face, darker joints and grain), and the species colour arrives as the
// material's `color`, which three multiplies the map by. That is deliberate and it buys two
// things — one cached tile serves basswood, walnut and oak instead of one per species, and
// `material.color` stays the authored species colour, which is the invariant the .glb parity
// argument and `roomFloor.test.ts` both rest on.
const plankMapCache = new Map<string, { colorMap: THREE.Texture; normalMap: THREE.Texture }>();

/** A luminance fill — the maps are greyscale, so one value fills R, G and B. */
function lumFill(value: number): string {
  const b = Math.max(0, Math.min(255, Math.round(value * 255)));
  return `rgb(${b},${b},${b})`;
}

// Normal-map depth of each joint profile: a V-groove is a channel, a factory bevel nearly
// as deep, and a butt seam on a sanded floor barely a line.
const JOINT_DEPTH = { vee: 40, bevel: 34, butt: 14 } as const;

/**
 * One tile of boards, as luminance. `u` runs ACROSS the boards (so board edges are vertical
 * lines in the canvas) and `v` runs ALONG them; `applyPlank*Uv` maps that onto the world.
 *
 * Returns null where there is no 2D canvas — SSR and the headless geometry tests, which build
 * real scenes in Node. The caller falls back to a flat material in the board's own colour.
 */
function buildPlankMaps(
  style: PlankStyle,
): { colorMap: THREE.Texture; normalMap: THREE.Texture } | null {
  const cached = plankMapCache.get(style.key);
  if (cached) return cached;
  if (typeof document === "undefined") return null;
  const [acrossM, alongM] = plankTileSizeM(style);
  const width = Math.max(16, Math.round(acrossM * style.pxPerM));
  const height = Math.max(16, Math.round(alongM * style.pxPerM));
  const colorCanvas = document.createElement("canvas");
  const normalCanvas = document.createElement("canvas");
  colorCanvas.width = normalCanvas.width = width;
  colorCanvas.height = normalCanvas.height = height;
  const cctx = colorCanvas.getContext("2d");
  const nctx = normalCanvas.getContext("2d");
  if (!cctx || !nctx) return null;

  const boardW = width / style.boardsPerTile;
  const pxAlong = height / alongM; // exact, so a wrapped board meets itself
  const jointPx = style.jointFraction > 0 ? Math.max(1, boardW * style.jointFraction) : 0;
  const ends = style.lengths.kind !== "continuous";
  const depth = JOINT_DEPTH[style.jointProfile];
  const bevel = style.jointProfile === "bevel";

  // The joint is the board in shadow, not a separate material: a groove, a bevel and a butt
  // seam are all a shadow line in the same wood, unlike a mortar joint.
  cctx.fillStyle = lumFill(bevel ? 0.5 : 0.62);
  cctx.fillRect(0, 0, width, height);
  nctx.fillStyle = "rgb(128,128,255)";
  nctx.fillRect(0, 0, width, height);

  layoutPlankTile(style).forEach((lane, index) => {
    const x = index * boardW;
    for (const board of lane) {
      const shade = boardShade(board.printId, style);
      // A board past the tile's end wraps: draw it again one tile back.
      for (const shift of board.v1 > alongM ? [0, -alongM] : [0]) {
        const y0 = (board.v0 + shift) * pxAlong;
        const y1 = (board.v1 + shift) * pxAlong;
        const face = {
          x: x + jointPx / 2, w: boardW - jointPx,
          y: ends ? y0 + jointPx / 2 : y0, h: ends ? y1 - y0 - jointPx : y1 - y0,
        };
        cctx.fillStyle = lumFill(shade);
        cctx.fillRect(face.x, face.y, face.w, face.h);
        drawBoardFigure(cctx, face, board.printId, style);
        // Normal map: each edge slopes down into its joint. A bevel also darkens its band.
        const band = bevel ? jointPx * 1.5 : jointPx;
        if (bevel) {
          cctx.fillStyle = "rgba(0,0,0,0.18)";
          cctx.fillRect(face.x, face.y, band, face.h);
          cctx.fillRect(face.x + face.w - band, face.y, band, face.h);
          if (ends) {
            cctx.fillRect(face.x, face.y, face.w, band);
            cctx.fillRect(face.x, face.y + face.h - band, face.w, band);
          }
        }
        nctx.fillStyle = `rgb(${128 - depth},128,235)`;
        nctx.fillRect(face.x, face.y, band, face.h);
        nctx.fillStyle = `rgb(${128 + depth},128,235)`;
        nctx.fillRect(face.x + face.w - band, face.y, band, face.h);
        if (ends) {
          // Canvas y runs down while texture v runs up (flipY), so the top edge faces +v.
          nctx.fillStyle = `rgb(128,${128 + depth},235)`;
          nctx.fillRect(face.x, face.y, face.w, band);
          nctx.fillStyle = `rgb(128,${128 - depth},235)`;
          nctx.fillRect(face.x, face.y + face.h - band, face.w, band);
        }
      }
    }
  });

  const colorMap = new THREE.CanvasTexture(colorCanvas);
  colorMap.wrapS = colorMap.wrapT = THREE.RepeatWrapping;
  colorMap.colorSpace = THREE.SRGBColorSpace;
  const normalMap = new THREE.CanvasTexture(normalCanvas);
  normalMap.wrapS = normalMap.wrapT = THREE.RepeatWrapping;
  normalMap.colorSpace = THREE.NoColorSpace;
  const maps = { colorMap, normalMap };
  plankMapCache.set(style.key, maps);
  return maps;
}

/**
 * Wood board finish. `style` selects the module + joint + jitter recipe (see plankStyleFor);
 * `color` is the board colour, which for wood is always the material's own — every wood
 * material in the library authors one, and a species IS its colour.
 *
 * `roughness` is passed through so a floor keeps the sheen `floorSurface()` already assigns
 * it (oak 0.55) while a sauna liner stays matte.
 */
export function createPlankMaterial(
  mode: "nordic" | "schematic", style: PlankStyle, color: THREE.ColorRepresentation,
  roughness = 0.8,
): THREE.Material {
  if (mode === "schematic") {
    return new THREE.MeshStandardMaterial({
      color, roughness: 1, metalness: 0, flatShading: true,
    });
  }
  const maps = buildPlankMaps(style);
  // No 2D canvas (SSR, the headless geometry tests): a flat fill in the board's own colour.
  // Never a throw — a missing texture is a degraded picture, not a broken scene.
  if (!maps) return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  return new THREE.MeshStandardMaterial({
    // The species colour, TINTED onto a neutral luminance map. Keeping it here rather than
    // baking it into the tile is what lets `material.color` still answer "what colour is this
    // floor" — the invariant the .glb parity check and roomFloor.test.ts rest on.
    color,
    map: maps.colorMap,
    normalMap: maps.normalMap,
    normalScale: new THREE.Vector2(style.reliefScale, style.reliefScale),
    roughness,
    metalness: 0,
  });
}

/**
 * World-scaled UVs for a wood-lined wall layer, mirroring `applyMasonryWallUv`'s frame: `u`
 * runs along the wall and `v` up it, both measured from the wall's own start and base rather
 * than from project zero, so boards start at a corner and at the floor exactly as they are
 * laid. Only the last cut board is short, which is what a carpenter actually does.
 *
 * `run` is the direction the BOARDS run, derived by the engine from the furring behind them
 * (`ResolvedLayer.board_run`). Boards land perpendicular to their furring, so the sauna's
 * horizontal 1x4 strapping gives vertical boards. When it is "vertical" the tile is rotated a
 * quarter turn — the map's `u` axis (across the boards) is mapped along the wall instead of up
 * it — because the texture is generated once, boards-across-u, for both cases.
 */
export function applyPlankWallUv(
  geometry: THREE.BufferGeometry,
  wallAxis: readonly [readonly [number, number], readonly [number, number]],
  center: PlanCenter,
  tileSizeM: readonly [number, number],
  baseZM = 0,
  run: "horizontal" | "vertical" | null = null,
): void {
  const [[x0, y0], [x1, y1]] = wallAxis;
  const dx = x1 - x0;
  const dy = y1 - y0;
  const length = Math.hypot(dx, dy);
  if (length < 1e-9) return;
  const directionX = dx / length;
  const directionY = dy / length;
  // Boards vertical  → across-boards runs ALONG the wall, along-boards runs UP it.
  // Boards horizontal → across-boards runs UP the wall, along-boards runs ALONG it.
  const vertical = run !== "horizontal";
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    const along = (projectX - x0) * directionX + (projectY - y0) * directionY;
    const up = positions.getY(index) - baseZM;
    const across = vertical ? along : up;
    const down = vertical ? up : along;
    uv[index * 2] = across / tileSizeM[0];
    uv[index * 2 + 1] = down / tileSizeM[1];
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/**
 * World-scaled UVs for a horizontal wood plane — a room's floor finish, or a boarded ceiling.
 * `longAxis` is the plan direction the boards run in, which for these surfaces is the room's
 * own long axis (see `planLongAxis`): boards are laid the long way, so a run of 14' reads as
 * fewer, longer boards than one of 11'.
 */
export function applyPlankPlaneUv(
  geometry: THREE.BufferGeometry,
  center: PlanCenter,
  longAxis: readonly [number, number],
  tileSizeM: readonly [number, number],
): void {
  const [ax, ay] = longAxis;
  const length = Math.hypot(ax, ay) || 1;
  const alongX = ax / length;
  const alongY = ay / length;
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  for (let index = 0; index < positions.count; index++) {
    const [projectX, projectY] = projectScenePointToPlan(
      positions.getX(index), positions.getZ(index), center,
    );
    // u across the boards (perpendicular to the run), v along them.
    const across = projectX * -alongY + projectY * alongX;
    const along = projectX * alongX + projectY * alongY;
    uv[index * 2] = across / tileSizeM[0];
    uv[index * 2 + 1] = along / tileSizeM[1];
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

/**
 * The long axis of a plan outline, as a unit vector — the direction boards run on a floor or
 * a boarded ceiling. Taken from the outline's longest edge rather than from a bounding box,
 * so an L-shaped room follows its own geometry instead of the box that contains it.
 */
export function planLongAxis(outline: readonly (readonly [number, number])[]): [number, number] {
  let best: [number, number] = [1, 0];
  let bestLen = -1;
  for (let index = 0; index < outline.length; index++) {
    const [x0, y0] = outline[index];
    const [x1, y1] = outline[(index + 1) % outline.length];
    const dx = x1 - x0;
    const dy = y1 - y0;
    const len = Math.hypot(dx, dy);
    if (len > bestLen) {
      bestLen = len;
      best = [dx / (len || 1), dy / (len || 1)];
    }
  }
  return best;
}

/** Drop the process-wide plank maps — only for teardown in tests/hot reload. */
export function disposePlankTextures(): void {
  for (const { colorMap, normalMap } of plankMapCache.values()) {
    colorMap.dispose();
    normalMap.dispose();
  }
  plankMapCache.clear();
}
