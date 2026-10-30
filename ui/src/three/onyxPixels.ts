// The onyx face kernel: plain arrays, no DOM and no three, so the worker can run it.
// One kernel, one record per print; a face is bounded by joints, so the noise needs no tiling.
import { fbm2, hashNoise2 } from "./valueNoise";

type RGB = readonly [number, number, number];
export interface OnyxPrint {
  /** Banded translucent body, light to dark, and the opaque crystalline bands. */
  readonly deep: RGB; readonly body: RGB; readonly pale: RGB;
  readonly ivory: RGB; readonly greige: RGB; readonly cloud: RGB; readonly vein: RGB;
  readonly faceMean: string; // sRGB hex; the house Material.color
  readonly faces: number;    // distinct faces before the pattern repeats
  readonly periodM: number;  // one translucent/opaque cycle across the bands
  readonly angleDeg: number; // band tilt off the 48" axis, +- by face
  readonly warp: number;     // domain-warp strength, metres of band shift
  readonly wisp: number;     // white wisp weight
  readonly fracture: number; // light fracture-cell weight
  readonly veinWeight: number;
  readonly opaqueAt: number; // lower is more opaque band
  readonly saturation: number;
}

export const ONYX_PRINTS = {
  "opera-blue": {
    deep: [158, 168, 194], body: [176, 184, 204], pale: [196, 200, 212],
    ivory: [236, 230, 218], greige: [214, 205, 192], cloud: [242, 240, 236], vein: [150, 122, 92],
    faceMean: "#c5c6cc", faces: 7, periodM: 0.62, angleDeg: 12, warp: 0.14, wisp: 0.5,
    fracture: 0.06, veinWeight: 0.4, opaqueAt: 0.82, saturation: 0.9,
  },
  // Softer, more swirled and less strictly banded; golden-brown veining.
  "agua-linda": {
    deep: [150, 176, 206], body: [172, 196, 222], pale: [198, 214, 230],
    ivory: [241, 238, 230], greige: [226, 220, 208], cloud: [246, 246, 244], vein: [176, 140, 90],
    faceMean: "#c7d5e2", faces: 8, periodM: 0.46, angleDeg: 18, warp: 0.24, wisp: 1.0,
    fracture: 0.05, veinWeight: 0.45, opaqueAt: 0.80, saturation: 1.1,
  },
} as const satisfies Record<string, OnyxPrint>;
export type OnyxPrintKey = keyof typeof ONYX_PRINTS;

export const hexRgb = (hex: string): RGB =>
  [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)) as unknown as RGB;

export interface OnyxSample { r: number; g: number; b: number; depth: number }
const clamp = (x: number) => Math.max(0, Math.min(1, x));
const smooth = (a: number, b: number, x: number) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const TAU = Math.PI * 2;
const WARP_STEP = 4; // px between exact warp samples; the warp is smooth, so it is interpolated

interface Kernel {
  readonly print: OnyxPrint; readonly seed: number; readonly cos: number; readonly sin: number;
  readonly phase: readonly number[];
}
function kernelFor(key: OnyxPrintKey, face: number): Kernel {
  const print = ONYX_PRINTS[key];
  const seed = (key === "opera-blue" ? 1000 : 2000) + face * 97;
  const rnd = (i: number) => hashNoise2(seed, i, 5);
  const angle = (rnd(0) < 0.15 ? -1 : 1) * (print.angleDeg * (0.4 + 0.8 * rnd(1))) * Math.PI / 180;
  return { print, seed, cos: Math.cos(angle), sin: Math.sin(angle),
    phase: [rnd(2) * TAU, rnd(3) * TAU, rnd(4) * TAU, rnd(5) * TAU] };
}

type Warp = [number, number, number, number];
function warpAt(k: Kernel, x: number, y: number, nyq: number, out: Warp): Warp {
  const s = k.seed;
  const q0 = 2 * (fbm2(1.5 * x, 1.5 * y, 4, s + 1, 1.5, nyq) - 0.5);
  const q1 = 2 * (fbm2(1.5 * x, 1.5 * y, 4, s + 2, 1.5, nyq) - 0.5);
  out[0] = q0; out[1] = q1;
  out[2] = 2 * (fbm2(3 * x + 4 * q0, 3 * y + 4 * q1, 4, s + 3, 3, nyq) - 0.5);
  out[3] = 2 * (fbm2(3 * x + 4 * q0, 3 * y + 4 * q1, 4, s + 4, 3, nyq) - 0.5);
  return out;
}

const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const tmp: Warp = [0, 0, 0, 0];

function shade(k: Kernel, x: number, y: number, w: Warp, nyq: number, out: OnyxSample): OnyxSample {
  const p = k.print, s0 = k.seed;
  const a = y * k.cos + x * k.sin, s = x * k.cos - y * k.sin;
  const sw = s + p.warp * (w[1] + 0.2 * w[3]) + 0.03 * Math.sin(2.1 * a + k.phase[0]);
  const t = sw / p.periodM;
  const f1 = fbm2(2 * a, 2 * sw, 3, s0 + 11, 2, nyq);
  const L = 0.5 + 0.30 * Math.sin(TAU * t + 5 * (f1 - 0.5) + k.phase[1])
    + 0.15 * Math.sin(TAU * 2.7 * t + k.phase[2]) + 0.08 * Math.sin(TAU * 7.3 * t + k.phase[3]);
  const edge = 0.24 * (fbm2(4 * a, 40 * sw, 3, s0 + 13, 40, nyq) - 0.5);
  const le = L + edge;
  const opaque = smooth(p.opaqueAt - 0.09, p.opaqueAt + 0.03, le);
  const glow = smooth(0.40, 0.60, L);
  const atten = Math.exp(-0.5 * (260 / nyq) ** 2);
  const stria = Math.pow(0.5 + 0.5 * Math.sin(TAU * 260 * sw
    + 3 * (fbm2(8 * a, 20 * sw, 2, s0 + 17, 20, nyq) - 0.5) * 6), 6) * atten + (1 - atten) * 0.05;
  const cloud = 2 * (fbm2(3 * x, 3 * y, 3, s0 + 19, 3, nyq) - 0.5);
  const bodyT = smooth(0.16, 0.55, L) + 0.1 * cloud;
  const stoneT = clamp(0.7 * stria + 0.2 * fbm2(6 * a, 18 * sw, 3, s0 + 23, 18, nyq) + 0.1 * cloud);
  const wisp = smooth(0.55, 0.8, fbm2(3 * a, 12 * sw, 3, s0 + 29, 12, nyq) + 0.3 * opaque);
  const lineMask = smooth(0.35, 0.65, fbm2(2 * a, 2 * sw, 2, s0 + 31, 2, nyq));
  const line = (1 - smooth(0, 0.016, Math.abs(le - p.opaqueAt + 0.04))) * lineMask;
  const wispMix = 0.5 * p.wisp * wisp * (1 - opaque);
  const lineMix = p.veinWeight * line;
  const o = [0, 0, 0];
  for (let c = 0; c < 3; c++) {
    let v = mix(mix(p.deep[c], p.pale[c], clamp(bodyT)), p.cloud[c], 0.45 * glow);
    v = mix(v, mix(p.ivory[c], p.greige[c], stoneT), opaque);
    v = mix(v, p.cloud[c], wispMix);
    o[c] = mix(v, p.vein[c], lineMix);
  }
  if (p.fracture > 0) {
    const f = fractureEdge(x, y, s0, nyq);
    const lighten = p.fracture * (1 - smooth(0, 0.002, f)) * (1 - opaque);
    for (let c = 0; c < 3; c++) o[c] = mix(o[c], p.cloud[c], lighten);
  }
  // Pull chroma away from the face mean: the scans were shot under flat studio light.
  const m = (o[0] + o[1] + o[2]) / 3;
  out.r = m + (o[0] - m) * p.saturation; out.g = m + (o[1] - m) * p.saturation;
  out.b = m + (o[2] - m) * p.saturation;
  out.depth = (1 - opaque) * (1 - wisp);
  return out;
}

const CELL_M = 0.18;
/** Distance gap F2-F1 to a jittered Voronoi cell edge, metres; zero on a fracture. */
function fractureEdge(x: number, y: number, seed: number, nyq: number): number {
  if (nyq < 100) return 1; // too coarse to resolve a 3 mm line
  const cx = x / CELL_M, cy = y / CELL_M, ix = Math.floor(cx), iy = Math.floor(cy);
  let f1 = 9, f2 = 9;
  for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) {
    const px = ix + i + hashNoise2(ix + i, iy + j, seed + 41);
    const py = iy + j + hashNoise2(ix + i, iy + j, seed + 43);
    const d = Math.hypot(px - cx, py - cy);
    if (d < f1) { f2 = f1; f1 = d; } else if (d < f2) f2 = d;
  }
  return (f2 - f1) * CELL_M;
}

/** One sample inside a face (x across 24", y along 48", metres); `pxPerM` is the raster. */
export function onyxFace(key: OnyxPrintKey, face: number, x: number, y: number,
  pxPerM = 838, out: OnyxSample = { r: 0, g: 0, b: 0, depth: 0 }): OnyxSample {
  const k = kernelFor(key, face % ONYX_PRINTS[key].faces), nyq = pxPerM * 0.5;
  return shade(k, x, y, warpAt(k, x, y, nyq, tmp), nyq, out);
}

export interface OnyxPixelJob {
  readonly print: OnyxPrintKey;
  readonly face: number;
  readonly pitchM: readonly [number, number]; // face + one joint, metres
  readonly jointM: number;
  readonly grout: RGB;
  readonly width: number;  // colour map px for the cell; ORM/normal are half
  readonly height: number;
}
export interface OnyxPixels {
  readonly width: number; readonly height: number;
  readonly color: Uint8ClampedArray;
  readonly mapWidth: number; readonly mapHeight: number;
  readonly normal: Uint8ClampedArray;
  readonly orm: Uint8ClampedArray; // R clearcoat mask, G roughness, B depth mask
}
export const ONYX_SURFACE = { faceRoughness: 0.07, groutRoughness: 0.85, groutDepthM: 0.0006, bevelM: 0.0007 };

/** Analytic face coverage and metric distance inside the face edge, for a point in the cell. */
function coverage(lx: number, ly: number, job: OnyxPixelJob, pxPerM: number) {
  const [px, py] = job.pitchM;
  const d = Math.min(lx, px - lx, ly, py - ly) - job.jointM / 2;
  return { d, cov: clamp(d * pxPerM + 0.5) };
}

export function renderOnyxFacePixels(job: OnyxPixelJob): OnyxPixels {
  const { width, height, pitchM: [px, py] } = job;
  const pxPerM = width / px, nyq = pxPerM * 0.5;
  const k = kernelFor(job.print, job.face % ONYX_PRINTS[job.print].faces);
  const color = new Uint8ClampedArray(width * height * 4);
  const mapWidth = width >> 1, mapHeight = height >> 1;
  const normal = new Uint8ClampedArray(mapWidth * mapHeight * 4);
  const orm = new Uint8ClampedArray(mapWidth * mapHeight * 4);
  const half = job.jointM / 2;
  // Warp on a coarse grid; bilinear between exact samples.
  const gw = Math.ceil(width / WARP_STEP) + 2, gh = Math.ceil(height / WARP_STEP) + 2;
  const grid = new Float32Array(gw * gh * 4);
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    warpAt(k, (i * WARP_STEP - half * pxPerM) / pxPerM, (j * WARP_STEP - half * pxPerM) / pxPerM, nyq, tmp);
    grid.set(tmp, (j * gw + i) * 4);
  }
  const depth = new Float32Array(mapWidth * mapHeight);
  const w: Warp = [0, 0, 0, 0], out: OnyxSample = { r: 0, g: 0, b: 0, depth: 0 };
  const fx = px - job.jointM, fy = py - job.jointM;
  for (let y = 0; y < height; y++) {
    const gy = y / WARP_STEP, j = Math.floor(gy), ty = gy - j;
    for (let x = 0; x < width; x++) {
      const gx = x / WARP_STEP, i = Math.floor(gx), tx = gx - i;
      const o00 = (j * gw + i) * 4, o10 = o00 + 4, o01 = o00 + gw * 4, o11 = o01 + 4;
      for (let c = 0; c < 4; c++) {
        w[c] = mix(mix(grid[o00 + c], grid[o10 + c], tx), mix(grid[o01 + c], grid[o11 + c], tx), ty);
      }
      const lx = (x + 0.5) / pxPerM, ly = (y + 0.5) / pxPerM;
      const { cov } = coverage(lx, ly, job, pxPerM);
      const fxp = Math.min(fx, Math.max(0, lx - half)), fyp = Math.min(fy, Math.max(0, ly - half));
      shade(k, fxp, fyp, w, nyq, out);
      const o = (y * width + x) * 4;
      color[o] = mix(job.grout[0], out.r, cov); color[o + 1] = mix(job.grout[1], out.g, cov);
      color[o + 2] = mix(job.grout[2], out.b, cov); color[o + 3] = 255;
      depth[(y >> 1) * mapWidth + (x >> 1)] += out.depth * cov * 0.25;
    }
  }
  const mapPx = mapWidth / px;
  const height_ = (lx: number, ly: number) =>
    ONYX_SURFACE.groutDepthM * clamp(coverage(lx, ly, job, mapPx).d / ONYX_SURFACE.bevelM);
  const e = 0.5 / mapPx;
  for (let y = 0; y < mapHeight; y++) for (let x = 0; x < mapWidth; x++) {
    const lx = (x + 0.5) / mapPx, ly = (y + 0.5) / mapPx;
    const dx = (height_(lx + e, ly) - height_(lx - e, ly)) / (2 * e);
    const dy = (height_(lx, ly + e) - height_(lx, ly - e)) / (2 * e);
    const len = Math.hypot(dx, dy, 1), o = (y * mapWidth + x) * 4;
    normal[o] = (0.5 - dx / len * 0.5) * 255; normal[o + 1] = (0.5 - dy / len * 0.5) * 255;
    normal[o + 2] = (0.5 + 0.5 / len) * 255; normal[o + 3] = 255;
    const cov = coverage(lx, ly, job, mapPx).cov;
    orm[o] = cov * 255;
    orm[o + 1] = mix(ONYX_SURFACE.groutRoughness, ONYX_SURFACE.faceRoughness, cov) * 255;
    orm[o + 2] = depth[y * mapWidth + x] * 255; orm[o + 3] = 255;
  }
  return { width, height, color, mapWidth, mapHeight, normal, orm };
}
