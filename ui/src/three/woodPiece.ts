import * as THREE from "three";
import { hashBoard, type PlankStyle } from "./plankLayout";
import { plankTileSizeM } from "./plankMaterial";

/** Stable seed from a model identity; identical parts still get distinct boards. */
export function pieceSeed(identity: string): number {
  let h = 0;
  for (let i = 0; i < identity.length; i++) h = (h * 31 + identity.charCodeAt(i)) % 1_000_003;
  return h;
}

/** Put face UVs within one lane; end UVs have their own square cross-section atlas. */
export function seatPieceUv(geometry: THREE.BufferGeometry, style: PlankStyle, seed: number) {
  const uv = geometry.getAttribute("uv") as THREE.BufferAttribute | undefined;
  if (!uv) return;
  const end = geometry.getAttribute("woodEnd");
  let minU = Infinity, minV = Infinity, maxV = -Infinity;
  for (let i = 0; i < uv.count; i++) {
    if (end?.getX(i)) continue;
    minU = Math.min(minU, uv.getX(i));
    minV = Math.min(minV, uv.getY(i)); maxV = Math.max(maxV, uv.getY(i));
  }
  const lane = Math.floor(hashBoard(seed, 1) * style.boardsPerTile) / style.boardsPerTile;
  const start = hashBoard(seed, 2) * Math.max(0, 1 - (maxV - minV));
  for (let i = 0; i < uv.count; i++) {
    if (end?.getX(i)) continue;
    uv.setXY(i, uv.getX(i) - minU + lane, uv.getY(i) - minV + start);
  }
  uv.needsUpdate = true;
}

/** Materials remain separate so grain on a crosscut cannot turn into longitudinal streaks. */
export function woodMaterialsForGeometry(material: THREE.Material, geometry: THREE.BufferGeometry)
  : THREE.Material | THREE.Material[] {
  const end = material.userData.endGrainMaterial as THREE.Material | undefined;
  return end && geometry.getAttribute("woodEnd") ? [material, end] : material;
}

/**
 * Project any flat-faced solid along an explicit scene-space grain direction. The direction
 * is an authored nosing for treads, the wall direction for stools, or vertical for posts.
 */
export function applyPieceGrainUv(geometry: THREE.BufferGeometry, grainDirection: THREE.Vector3,
  style: PlankStyle, seed: number) {
  const grain = grainDirection.clone().normalize();
  const positions = geometry.getAttribute("position");
  const normals = geometry.getAttribute("normal");
  if (!positions || !normals || grain.lengthSq() === 0) return;
  const [tileU, tileV] = plankTileSizeM(style);
  const up = Math.abs(grain.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
  const cross = new THREE.Vector3().crossVectors(grain, up).normalize();
  const secondCross = new THREE.Vector3().crossVectors(grain, cross).normalize();
  const points = Array.from({ length: positions.count }, (_, i) => new THREE.Vector3().fromBufferAttribute(positions, i));
  const minProjection = (axis: THREE.Vector3) => Math.min(...points.map(p => p.dot(axis)));
  const minAlong = minProjection(grain), minCross = minProjection(cross), minSecond = minProjection(secondCross);
  const lane = Math.floor(hashBoard(seed, 1) * style.boardsPerTile) / style.boardsPerTile;
  const uv = new Float32Array(positions.count * 2), end = new Float32Array(positions.count);
  for (let i = 0; i < positions.count; i++) {
    const normal = new THREE.Vector3().fromBufferAttribute(normals, i);
    const p = points[i];
    const isEnd = Math.abs(normal.dot(grain)) > 0.7;
    end[i] = Number(isEnd);
    if (isEnd) {
      uv[i * 2] = (p.dot(cross) - minCross) / tileU + lane;
      uv[i * 2 + 1] = (p.dot(secondCross) - minSecond) / style.faceWidthM;
    } else {
      const useCross = Math.abs(normal.dot(secondCross)) >= Math.abs(normal.dot(cross));
      uv[i * 2] = useCross ? (p.dot(cross) - minCross) / tileU
        : (p.dot(secondCross) - minSecond) / tileU;
      uv[i * 2 + 1] = (p.dot(grain) - minAlong) / tileV;
    }
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  geometry.setAttribute("woodEnd", new THREE.BufferAttribute(end, 1));
  geometry.clearGroups();
  const index = geometry.getIndex();
  const count = index?.count ?? positions.count;
  // Adjacent triangles sharing a treatment use one draw group, including indexed boxes.
  for (let triangle = 0; triangle < count; triangle += 3) {
    const materialIndex = end[index?.getX(triangle) ?? triangle] ? 1 : 0;
    const previous = geometry.groups[geometry.groups.length - 1];
    if (previous?.materialIndex === materialIndex) previous.count += 3;
    else geometry.addGroup(triangle, 3, materialIndex);
  }
  seatPieceUv(geometry, style, seed);
}

/** Grain follows the longest local dimension before the box is rotated into place. */
export function boardBoxGeometry(matrix: THREE.Matrix4, style: PlankStyle,
  seed: number, grainAxis?: number): THREE.BufferGeometry {
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const axes = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  matrix.extractBasis(axes[0], axes[1], axes[2]);
  const extent = axes.map(axis => axis.length());
  const grainIndex = grainAxis ?? extent.indexOf(Math.max(...extent));
  geometry.scale(extent[0], extent[1], extent[2]);
  const grain = new THREE.Vector3().setComponent(grainIndex, 1);
  applyPieceGrainUv(geometry, grain, style, seed);
  const rotation = matrix.clone().scale(new THREE.Vector3(1 / extent[0], 1 / extent[1], 1 / extent[2]));
  geometry.applyMatrix4(rotation);
  return geometry;
}
