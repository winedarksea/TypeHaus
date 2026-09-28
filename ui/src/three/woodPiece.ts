// ── One solid-wood piece: a stool, a tread, a shelf ─────────────────────────────────────
// A floor tiles its boards across the world; a piece of millwork is ONE board, so its UVs are
// seated on the piece itself: grain along its longest extent, starting at a lane edge of the
// recipe's tile, and at a hashed point along the lane so two identical treads are not one
// figure twice.
import * as THREE from "three";
import { hashBoard, type PlankStyle } from "./plankLayout";
import { plankTileSizeM } from "./plankMaterial";

/** A stable numeric seed from an identity string (a uid, a member key). */
export function pieceSeed(identity: string): number {
  let h = 0;
  for (let i = 0; i < identity.length; i++) h = (h * 31 + identity.charCodeAt(i)) % 1_000_003;
  return h;
}

/**
 * Shift a piece's UVs (already in tile units, grain along v) onto one board of the tile: u
 * from a lane's edge, v from a hashed start chosen so the piece never runs past the tile's
 * end, where a continuous lane's figure does not wrap.
 */
export function seatPieceUv(geometry: THREE.BufferGeometry, style: PlankStyle, seed: number) {
  const uv = geometry.getAttribute("uv") as THREE.BufferAttribute | undefined;
  if (!uv) return;
  let minU = Infinity, minV = Infinity, maxV = -Infinity;
  for (let i = 0; i < uv.count; i++) {
    minU = Math.min(minU, uv.getX(i));
    minV = Math.min(minV, uv.getY(i));
    maxV = Math.max(maxV, uv.getY(i));
  }
  const lane = Math.floor(hashBoard(seed, 1) * style.boardsPerTile) / style.boardsPerTile;
  const start = hashBoard(seed, 2) * Math.max(0, 1 - (maxV - minV));
  for (let i = 0; i < uv.count; i++) {
    uv.setXY(i, uv.getX(i) - minU + lane, uv.getY(i) - minV + start);
  }
  uv.needsUpdate = true;
}

/**
 * A unit box placed by `matrix` (a member box, or a furniture part's translate-and-scale), UV'd
 * as one board: grain along whichever local axis the matrix stretches longest, the end grain
 * on the faces across it.
 */
export function boardBoxGeometry(matrix: THREE.Matrix4, style: PlankStyle,
  seed: number): THREE.BufferGeometry {
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const axes = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  matrix.extractBasis(axes[0], axes[1], axes[2]);
  const extent = axes.map((axis) => axis.length());
  const grain = extent.indexOf(Math.max(...extent));
  const [tileU, tileV] = plankTileSizeM(style);
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  const uv = geometry.getAttribute("uv") as THREE.BufferAttribute;
  for (let i = 0; i < position.count; i++) {
    const s = [position.getX(i), position.getY(i), position.getZ(i)]
      .map((c, k) => (c + 0.5) * extent[k]);
    const n = [normal.getX(i), normal.getY(i), normal.getZ(i)].map(Math.abs);
    const face = n.indexOf(Math.max(...n));
    const [a, b] = [0, 1, 2].filter((k) => k !== grain);
    const [u, v] = face === grain ? [s[a], s[b]] : [s[3 - grain - face], s[grain]];
    uv.setXY(i, u / tileU, v / tileV);
  }
  seatPieceUv(geometry, style, seed);
  geometry.applyMatrix4(matrix);
  return geometry;
}
