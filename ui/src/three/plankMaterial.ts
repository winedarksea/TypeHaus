// ── Wood planks (T&G paneling / strip flooring) ───────────────────────────────────────
// The sauna's basswood liner, the study's walnut wainscot and the two oak floors all used to
// paint as one flat fill, so a lined sauna read as tan drywall and a strip-oak floor read as
// a sheet of MDF. Same trick as the masonry section of `materials.ts`: the board module, the
// joint and the per-board tone variation ride shared procedural maps (colour + normal),
// world-scaled so boards sit at true size. No external texture, so the offline PWA still
// renders it, and — like brick — no per-board geometry (plans/01-decisions.md #23 keeps
// placed members wood-framing-only).
//
// Two recipes, because a paneling board and a floor strip are not the same product:
//   • `tg-board` — 3½" exposed face, a V-groove at each joint, continuous runs. The sauna
//     liner is 7'-6" and the wainscot 3', so neither has end joints worth drawing.
//   • `shiplap` — 5½" exposed face, a wider reveal at each joint, continuous runs. The sauna
//     liner became shiplap on 2026-08-28 and would otherwise have gone on rendering as T&G
//     forever: the `*-tg` ref inference below cannot see a profile change that renames the tag.
//   • `strip-floor` — 2¼" strip with butt end joints on a hashed stagger, and the highest
//     tone jitter in the house: strip oak is genuinely that variegated.
//
// Unlike the masonry recipes, neither carries a fixed unit colour. Every wood material in
// the library authors its own `Material.color` (basswood #e6d4ae, walnut #5d4433, oak
// #c69c6d), and that is the colour a species *is* — a recipe that overrode it would make
// walnut and basswood render identically.
import * as THREE from "three";
import { projectScenePointToPlan, type PlanCenter } from "./planGeometry";

const PLANK_TEX_PX = 512;

/**
 * The recipe for one wood finish: the board module, how many boards/lengths a repeat tile
 * spans, the joint profile, and the per-board HSL jitter magnitude. `key` seeds the map cache
 * so distinct styles never collide.
 *
 * `boardLenM` is 0 for a continuous run (no end joints drawn); anything else is the mean
 * board length, staggered per row so a floor does not read as a grid.
 */
export interface PlankStyle {
  readonly key: string;
  readonly faceWidthM: number; // exposed face of one board, across the run
  readonly boardsPerTile: number;
  readonly boardLenM: number; // 0 = continuous run
  readonly lengthsPerTile: number; // ignored when boardLenM is 0
  readonly jointFraction: number; // joint width ÷ face width
  readonly jointProfile: "vee" | "butt";
  // Per-board tone spread, as a fraction of full brightness. LIGHTNESS ONLY: the maps are
  // luminance (see buildPlankMaps), so hue and saturation cannot vary per board the way the
  // masonry recipes vary them. That is a fair trade — board-to-board variation in a run of
  // one species reads almost entirely as lightness anyway, and keeping the map neutral is
  // what lets `material.color` stay the species colour.
  readonly jitter: number;
  readonly grain: number; // lengthwise figure amplitude, 0..1
}

// 5/4 and 4/4 tongue-and-groove paneling: a 1x4/5/4x4 board shows ~3½" of face once the
// tongue is buried. The V-groove is the only joint a T&G board has — there is no mortar to
// draw and no stagger, because these runs are short enough to be single boards.
const TG_BOARD_STYLE: PlankStyle = {
  key: "tg-board", faceWidthM: 0.0889, boardsPerTile: 6, boardLenM: 0, lengthsPerTile: 1,
  jointFraction: 0.045, jointProfile: "vee", jitter: 0.07, grain: 0.35,
};

// 2¼" white-oak strip. Butt joints rather than a groove (a strip floor is sanded flat, so
// the joint is a line, not a channel), staggered lengths, and the widest tone spread here:
// a strip floor laid from mixed boards is the most variegated surface in the house.
const STRIP_FLOOR_STYLE: PlankStyle = {
  key: "strip-floor", faceWidthM: 0.0572, boardsPerTile: 8, boardLenM: 0.9144,
  lengthsPerTile: 2, jointFraction: 0.02, jointProfile: "butt", jitter: 0.13, grain: 0.5,
};

/**
 * The finish recipes a wood material can name via its authored `Material.finish`. Keys are the
 * engine's finish vocabulary (model/materials.py), the same contract MASONRY_STYLES follows.
 */
// 5/4 shiplap: a 1x6 board shows ~5½" of face once the rabbet is lapped, so the module is
// wider than the T&G's and the reveal at each joint is a broader shadow line. Drawn with the
// same `vee` joint the T&G uses — a square reveal and a V-groove are the same channel at this
// scale, and adding a third joint profile to `buildPlankMaps` would buy nothing visible.
const SHIPLAP_STYLE: PlankStyle = {
  key: "shiplap", faceWidthM: 0.1397, boardsPerTile: 4, boardLenM: 0, lengthsPerTile: 1,
  jointFraction: 0.045, jointProfile: "vee", jitter: 0.07, grain: 0.35,
};

export const WOOD_PLANK_STYLES: Readonly<Record<string, PlankStyle>> = {
  "tg-board": TG_BOARD_STYLE,
  "shiplap": SHIPLAP_STYLE,
  "strip-floor": STRIP_FLOOR_STYLE,
};

// Flooring refs that are laid as strips rather than as paneling. Deliberately explicit: the
// `familyOf` substring table in nordic/palette.ts has no wood-species needles at all (it
// returns null for `oak`, `sauna-shiplap`, `walnut-tg` and `cedar-tg` alike), and adding some there
// would move colour resolution too — plus its Python mirror in emit/draw/palette.py.
const STRIP_FLOOR_REFS = new Set(["oak", "lvp"]);

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

/** True when a surface's material should be finished as wood boards. */
export function isWoodPlank(materialRef: string | null | undefined): boolean {
  if (!materialRef) return false;
  const s = materialRef.toLowerCase();
  if (WOOD_PLANK_STYLES[s]) return true;
  return isBoardPanelingRef(s) || STRIP_FLOOR_REFS.has(s);
}

/**
 * Pick the wood finish recipe. An authored `finish` from the catalog is definitive — that is
 * the material declaring its own appearance. Absent one (or naming a recipe this build does
 * not know, as `walnut-tg`'s "clear-satin-hardwax-oil" does), infer from the ref: a flooring
 * strip, else T&G paneling.
 */
export function plankStyleFor(
  materialRef: string | null | undefined, finish?: string | null,
): PlankStyle {
  const declared = finish ? WOOD_PLANK_STYLES[finish] : undefined;
  if (declared) return declared;
  const ref = (materialRef ?? "").toLowerCase();
  if (STRIP_FLOOR_REFS.has(ref)) return STRIP_FLOOR_STYLE;
  return ref.includes("shiplap") ? SHIPLAP_STYLE : TG_BOARD_STYLE;
}

/**
 * World size (metres) of one repeat tile: [across the boards, along them]. A continuous-run
 * style has no end joints, so its along-run extent is arbitrary — one board width keeps the
 * tile square-ish and the grain from stretching.
 */
export function plankTileSizeM(style: PlankStyle): readonly [number, number] {
  const along = style.boardLenM > 0
    ? style.boardLenM * style.lengthsPerTile
    : style.faceWidthM * style.boardsPerTile;
  return [style.faceWidthM * style.boardsPerTile, along];
}

// Keyed by recipe alone. Unlike the masonry maps, these bake in no colour: they are pure
// LUMINANCE (white face, darker joints and grain), and the species colour arrives as the
// material's `color`, which three multiplies the map by. That is deliberate and it buys two
// things — one cached tile serves basswood, walnut and oak instead of one per species, and
// `material.color` stays the authored species colour, which is the invariant the .glb parity
// argument and `roomFloor.test.ts` both rest on.
const plankMapCache = new Map<string, { colorMap: THREE.Texture; normalMap: THREE.Texture }>();

// Deterministic per-board jitter — no Math.random, so the maps stay reproducible across
// reloads. Same hash as materials.ts `hashUnit`, kept local so neither file owns the other's
// texture generation.
function hashBoard(row: number, board: number): number {
  const h = Math.sin(row * 12.9898 + board * 78.233) * 43758.5453;
  return h - Math.floor(h);
}

/** A luminance byte, clamped — the maps are greyscale, so one value fills R, G and B. */
function lum(value: number): number {
  return Math.max(0, Math.min(255, Math.round(value * 255)));
}

/**
 * One tile of boards, as luminance. `u` runs ACROSS the boards (so board edges are vertical
 * lines in the canvas) and `v` runs ALONG them; `applyPlank*Uv` maps that onto the world.
 *
 * Returns null where there is no 2D canvas — SSR and the headless geometry tests, which build
 * real scenes in Node. The caller falls back to a flat material in the board's own colour,
 * which is exactly what this surface looked like before this module existed.
 */
function buildPlankMaps(
  style: PlankStyle,
): { colorMap: THREE.Texture; normalMap: THREE.Texture } | null {
  const cached = plankMapCache.get(style.key);
  if (cached) return cached;
  if (typeof document === "undefined") return null;
  const colorCanvas = document.createElement("canvas");
  const normalCanvas = document.createElement("canvas");
  colorCanvas.width = colorCanvas.height = PLANK_TEX_PX;
  normalCanvas.width = normalCanvas.height = PLANK_TEX_PX;
  const cctx = colorCanvas.getContext("2d");
  const nctx = normalCanvas.getContext("2d");
  if (!cctx || !nctx) return null;

  const boardW = PLANK_TEX_PX / style.boardsPerTile;
  const rows = style.boardLenM > 0 ? style.lengthsPerTile : 1;
  const rowH = PLANK_TEX_PX / rows;
  const jointPx = Math.max(1.5, boardW * style.jointFraction);

  // The joint is the board in shadow, not a separate material: a T&G groove and a butt seam
  // are both a shadow line in the same wood, unlike a mortar joint.
  const jointLum = 0.62;
  cctx.fillStyle = `rgb(${lum(jointLum)},${lum(jointLum)},${lum(jointLum)})`;
  cctx.fillRect(0, 0, PLANK_TEX_PX, PLANK_TEX_PX);
  nctx.fillStyle = "rgb(128,128,255)";
  nctx.fillRect(0, 0, PLANK_TEX_PX, PLANK_TEX_PX);

  for (let row = 0; row < rows; row++) {
    // Stagger each row by a hashed fraction of a board length so end joints never line up.
    const stagger = rows > 1 ? hashBoard(row, 0) * rowH : 0;
    const y = row * rowH + stagger;
    for (let board = -1; board < style.boardsPerTile + 1; board++) {
      const x = board * boardW;
      // Centred on 1.0 so the tinted result averages to the authored species colour rather
      // than drifting darker than the material says it is.
      const shade = 1 - style.jitter / 2 + hashBoard(row, board) * style.jitter;
      const faceX = x + jointPx / 2;
      const faceW = boardW - jointPx;
      const faceY = y + jointPx / 2;
      const faceH = rowH - jointPx;
      const wrapY = rows > 1 ? rowH : 0;
      cctx.fillStyle = `rgb(${lum(shade)},${lum(shade)},${lum(shade)})`;
      cctx.fillRect(faceX, faceY, faceW, faceH);
      if (rows > 1) cctx.fillRect(faceX, faceY - rowH, faceW, faceH); // wrap the stagger

      // Lengthwise grain: a few darker streaks running ALONG the board (down the canvas).
      // Cheap, and it is what stops a wide board reading as a painted panel.
      for (let streak = 0; streak < 3; streak++) {
        const g = hashBoard(row * 31 + streak, board * 17);
        const grainLum = shade * (1 - 0.09 * style.grain * (0.4 + g));
        cctx.fillStyle = `rgb(${lum(grainLum)},${lum(grainLum)},${lum(grainLum)})`;
        cctx.fillRect(faceX + g * faceW, faceY - wrapY,
          Math.max(1, faceW * 0.06), faceH + wrapY);
      }

      // Normal map. A V-groove is two opposing slopes falling into the joint (a channel); a
      // butt seam on a sanded floor is a much shallower version of the same thing.
      const depth = style.jointProfile === "vee" ? 40 : 14;
      nctx.fillStyle = `rgb(${128 + depth},128,235)`; // faces +U on the left edge
      nctx.fillRect(faceX, faceY - wrapY, jointPx, faceH + wrapY);
      nctx.fillStyle = `rgb(${128 - depth},128,235)`; // faces -U on the right edge
      nctx.fillRect(x + boardW - jointPx * 1.5, faceY - wrapY, jointPx, faceH + wrapY);
      if (rows > 1) {
        // End joints only exist on a staggered style, and they are always shallow butts.
        nctx.fillStyle = "rgb(128,142,235)";
        nctx.fillRect(faceX, faceY, faceW, jointPx);
      }
    }
  }

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
  // No 2D canvas (SSR, the headless geometry tests): a flat fill in the board's own colour,
  // which is what this surface was before the boards existed. Never a throw — a missing
  // texture is a degraded picture, not a broken scene.
  if (!maps) return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
  return new THREE.MeshStandardMaterial({
    // The species colour, TINTED onto a neutral luminance map. Keeping it here rather than
    // baking it into the tile is what lets `material.color` still answer "what colour is this
    // floor" — the invariant the .glb parity check and roomFloor.test.ts rest on.
    color,
    map: maps.colorMap,
    normalMap: maps.normalMap,
    normalScale: new THREE.Vector2(0.6, 0.6),
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
