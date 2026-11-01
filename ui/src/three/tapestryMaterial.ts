// ── Wall tapestry (the east wall's woven dragon hanging) ──────────────────────────────────
// One 512x384 CanvasTexture (the hanging is 80"x60"), drawn once and shared by every tapestry.
// No normal map, no extra geometry: the weave is baked into the picture as faint thread lines.
// Without a `document` (geometry tests run in Node) the builder returns null and the caller
// keeps the part's flat colour. Painted onto the engine's 2 mm face sheet (role "tapestry"),
// whose -y local face is the room-facing one: a box's +z face is upright and unmirrored.
import * as THREE from "three";

const W = 512;
const H = 384;
const INK = "#2a1a10";
const PAL = {
  ground: "#2e4a3c", leaf: "#4a7355", rust: "#9a4a2a", ochre: "#c79a3a", cream: "#e8dcb8",
  skin: "#e2c4a2", wing: "#8a3a22", belly: "#d9b45c", dragon: "#5f7a3a",
};

export function isTapestry(role: string | null | undefined): boolean {
  return role === "tapestry";
}

let cached: THREE.CanvasTexture | null | undefined;

function drawBorder(g: CanvasRenderingContext2D): void {
  g.fillStyle = PAL.rust; g.fillRect(0, 0, W, H);
  g.fillStyle = INK; g.fillRect(20, 20, W - 40, H - 40);
  g.fillStyle = PAL.ochre; g.fillRect(23, 23, W - 46, H - 46);
  g.fillStyle = PAL.ground; g.fillRect(27, 27, W - 54, H - 54);
  g.fillStyle = PAL.cream;  // lozenges along the rust band
  for (let x = 12; x < W; x += 24) for (const y of [10, H - 10]) lozenge(g, x, y, 5);
  for (let y = 12; y < H; y += 24) for (const x of [10, W - 10]) lozenge(g, x, y, 5);
}

function lozenge(g: CanvasRenderingContext2D, x: number, y: number, r: number): void {
  g.beginPath(); g.moveTo(x, y - r); g.lineTo(x + r, y); g.lineTo(x, y + r); g.lineTo(x - r, y);
  g.closePath(); g.fill();
}

function poly(g: CanvasRenderingContext2D, fill: string, pts: number[][]): void {
  g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
  for (const [x, y] of pts.slice(1)) g.lineTo(x, y);
  g.closePath(); g.fillStyle = fill; g.fill(); g.stroke();
}

function disc(g: CanvasRenderingContext2D, fill: string, x: number, y: number, rx: number,
  ry = rx, stroke = true): void {
  g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); g.fillStyle = fill; g.fill();
  if (stroke) g.stroke();
}

// Millefleur: small flower heads and leaf tufts scattered on the ground (seeded, repeatable).
function drawFlowers(g: CanvasRenderingContext2D): void {
  let s = 7;
  const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  const hues = [PAL.cream, PAL.ochre, PAL.rust];
  for (let i = 0; i < 90; i++) {
    const x = 40 + rnd() * (W - 80), y = 40 + rnd() * (H - 80);
    g.fillStyle = PAL.leaf; disc(g, PAL.leaf, x, y + 5, 7, 3, false);
    g.fillStyle = hues[i % 3];
    for (let k = 0; k < 5; k++) {
      const a = (k / 5) * Math.PI * 2;
      disc(g, hues[i % 3], x + Math.cos(a) * 3.5, y + Math.sin(a) * 3.5, 2.2, 2.2, false);
    }
    disc(g, PAL.ground, x, y, 1.4, 1.4, false);
  }
}

function drawLady(g: CanvasRenderingContext2D): void {
  g.lineWidth = 2.5; g.strokeStyle = INK; g.lineJoin = "round";
  poly(g, PAL.cream, [[132, 150], [156, 150], [190, 338], [100, 338]]);   // gown
  poly(g, PAL.rust, [[128, 150], [160, 150], [158, 190], [130, 190]]);    // bodice
  poly(g, PAL.ochre, [[128, 188], [160, 188], [162, 198], [126, 198]]);   // girdle
  poly(g, PAL.rust, [[140, 270], [150, 270], [160, 338], [130, 338]]);    // kirtle panel
  poly(g, PAL.rust, [[158, 156], [215, 168], [214, 180], [156, 178]]);    // arm held out
  disc(g, PAL.skin, 217, 174, 5);                                          // hand
  poly(g, PAL.ochre, [[132, 128], [156, 128], [148, 52], [140, 52]]);      // tall hennin
  poly(g, PAL.cream, [[148, 56], [176, 112], [160, 112]]);                 // trailing veil
  disc(g, PAL.skin, 144, 138, 14, 16);                                     // face
  g.fillStyle = INK; disc(g, INK, 139, 136, 1.6, 1.6, false); disc(g, INK, 149, 136, 1.6, 1.6, false);
}

function drawDragon(g: CanvasRenderingContext2D): void {
  g.lineWidth = 2.5; g.strokeStyle = INK; g.lineJoin = "round"; g.lineCap = "round";
  poly(g, PAL.wing, [[370, 220], [330, 120], [372, 150], [392, 96], [418, 150], [450, 120],
    [430, 220]]);                                                          // bat wing
  g.beginPath(); g.moveTo(420, 290);                                       // tail
  g.bezierCurveTo(470, 320, 450, 350, 410, 335); g.bezierCurveTo(440, 345, 470, 330, 440, 300);
  g.lineWidth = 14; g.strokeStyle = INK; g.stroke(); g.lineWidth = 9; g.strokeStyle = PAL.dragon;
  g.stroke(); g.lineWidth = 2.5; g.strokeStyle = INK;
  for (const lx of [350, 410]) poly(g, PAL.dragon, [[lx - 8, 290], [lx + 8, 290],    // legs
    [lx + 12, 335], [lx - 6, 335]]);
  disc(g, PAL.dragon, 385, 262, 58, 36);                                   // body
  disc(g, PAL.belly, 380, 278, 40, 18, false);                             // belly plates
  g.beginPath(); g.moveTo(340, 245);                                       // S-neck up to head
  g.bezierCurveTo(300, 230, 330, 180, 305, 160);
  g.lineWidth = 22; g.strokeStyle = INK; g.stroke(); g.lineWidth = 17; g.strokeStyle = PAL.dragon;
  g.stroke(); g.lineWidth = 2.5; g.strokeStyle = INK;
  poly(g, PAL.dragon, [[286, 150], [322, 140], [330, 156], [284, 166]]);   // head
  poly(g, PAL.rust, [[290, 164], [330, 160], [288, 174]]);                 // open jaw
  poly(g, PAL.ochre, [[308, 140], [314, 120], [320, 140]]);                // horn
  disc(g, PAL.ochre, 310, 150, 3, 3, false);                               // eye
  poly(g, PAL.cream, [[285, 154], [289, 162], [292, 154]]);                // fang
  g.beginPath(); g.moveTo(278, 160); g.bezierCurveTo(262, 164, 262, 176, 248, 176);
  g.strokeStyle = PAL.rust; g.lineWidth = 3; g.stroke();                   // flame breath
}

function drawTrees(g: CanvasRenderingContext2D): void {
  g.lineWidth = 2; g.strokeStyle = INK;
  for (const [x, h] of [[58, 150], [462, 130]]) {
    g.fillStyle = "#5a3c24"; g.fillRect(x - 4, 340 - h * 0.4, 8, h * 0.4);
    disc(g, PAL.leaf, x, 340 - h * 0.7, 30, 38);
    g.fillStyle = PAL.ochre;
    for (let k = 0; k < 7; k++) disc(g, PAL.ochre, x - 16 + (k % 4) * 11, 340 - h * 0.7 - 16 + k * 5,
      2.2, 2.2, false);
  }
}

function drawWeave(g: CanvasRenderingContext2D): void {
  g.fillStyle = "rgba(0,0,0,0.07)";
  for (let y = 0; y < H; y += 2) g.fillRect(0, y, W, 1);
  g.fillStyle = "rgba(255,240,200,0.04)";
  for (let x = 0; x < W; x += 2) g.fillRect(x, 0, 1, H);
}

/** The shared tapestry face, or null where no canvas exists (headless scenes). */
export function buildTapestryMap(): THREE.CanvasTexture | null {
  if (cached !== undefined) return cached;
  cached = null;
  if (typeof document === "undefined") return cached;
  const canvas = document.createElement("canvas");
  canvas.width = W; canvas.height = H;
  const g = canvas.getContext("2d");
  if (!g) return cached;
  drawBorder(g); drawFlowers(g); drawTrees(g); drawLady(g); drawDragon(g); drawWeave(g);
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  map.anisotropy = 4;
  cached = map;
  return map;
}

/** A matte cloth material around the shared map, or null (→ flat colour). */
export function createTapestryMaterial(): THREE.MeshStandardMaterial | null {
  const map = buildTapestryMap();
  return map ? new THREE.MeshStandardMaterial({ map, roughness: 1, metalness: 0 }) : null;
}

/** Drop the shared texture — teardown in tests/hot reload only. */
export function disposeTapestryTextures(): void {
  if (cached) cached.dispose();
  cached = undefined;
}
