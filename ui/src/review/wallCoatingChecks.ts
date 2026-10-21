import * as THREE from "three";
import type { Model } from "../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { buildSolid } from "../three/builders/structure";
import { buildWall } from "../three/builders/walls";

/** Pixel checks: raycasts cannot detect paint pulled ahead of timber by depth bias. */
export function runWallCoatingChecks(model: Model, renderer: THREE.WebGLRenderer): string[] {
  const failures: string[] = [];
  const wall = model.walls.find(w => w.tag === "W-S-W3")!;
  const posts = model.solids!.filter(s => s.tag.startsWith("P-S-TUDOR"));
  if (posts.length !== 2) return ["Wall coating check requires both suite timbers"];
  const target = new THREE.WebGLRenderTarget(700, 500);
  const previousTarget = renderer.getRenderTarget();
  const camera = new THREE.PerspectiveCamera(50, 1.4, 0.05, 500);
  const pixel = new Uint8Array(4);
  const readPoint = (point: THREE.Vector3) => {
    const projected = point.project(camera);
    renderer.readRenderTargetPixels(target,
      Math.floor((projected.x + 1) * target.width / 2),
      Math.floor((projected.y + 1) * target.height / 2), 1, 1, pixel);
    return [...pixel];
  };
  const postCentres = posts.map(post =>
    (Math.min(...post.outline.map(p => p[1])) + Math.max(...post.outline.map(p => p[1]))) / 2);
  const paintFace = Math.max(...wall.layers.find(layer => layer.material === "latex-paint")!
    .polygon.map(point => point[0]));
  try {
    for (const mode of ["nordic", "schematic"] as const) {
      const scene = new THREE.Scene();
      const groups = Object.fromEntries(ALL_TRADES.map(trade => [trade, new THREE.Group()])) as
        Record<Trade, THREE.Group>;
      Object.values(groups).forEach(group => scene.add(group));
      const picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
      buildWall(groups, { ...wall, members: [], layers: wall.layers.filter(layer =>
        layer.material === "latex-paint" || layer.material === "gwb") }, [], [0, 0], mode,
      RESOLVED_NORDIC_PALETTE.light, picks, selected, model.catalog!.materials);
      for (const post of posts) buildSolid(groups.framing, post, [0, 0], mode,
        RESOLVED_NORDIC_PALETTE.light, model.catalog, picks, selected, model.catalog!.materials);
      // Flat identification colours retain the builder's actual depth settings, so lighting
      // and grain cannot disguise which surface won the depth test.
      scene.traverse(object => {
        if (!(object instanceof THREE.Mesh)) return;
        const originals = Array.isArray(object.material) ? object.material : [object.material];
        const original = originals[0];
        const isPost = posts.some(post => post.uid === object.userData.uid);
        const isPaint = object.userData.trades?.includes("paint");
        object.material = new THREE.MeshBasicMaterial({
          color: isPost ? 0xff0000 : isPaint ? 0x00ff00 : 0x0000ff, toneMapped: false,
          polygonOffset: original.polygonOffset, polygonOffsetFactor: original.polygonOffsetFactor,
          polygonOffsetUnits: original.polygonOffsetUnits,
        });
        for (const material of originals) material.dispose();
      });
      renderer.setRenderTarget(target);
      for (const position of [[4.4, 4.5, -4.75], [3, 7, 0], [3, 7, -9.5], [1.5, 5, 0]]) {
        camera.position.set(position[0], position[1], position[2]);
        camera.lookAt(0, 4.4, -4.75);
        camera.updateMatrixWorld();
        renderer.render(scene, camera);
        posts.forEach((post, index) => {
          const face = Math.max(...post.outline.map(point => point[0]));
          const [red, green] = readPoint(new THREE.Vector3(face, 4.4, -postCentres[index]));
          if (red < 250 || green > 5) failures.push(`${mode}: paint hides ${post.tag} from ${position}`);
        });
        const [red, green] = readPoint(new THREE.Vector3(paintFace, 4.4,
          -(postCentres[0] + postCentres[1]) / 2));
        if (green < 250 || red > 5) failures.push(`${mode}: substrate shows through paint from ${position}`);
      }
      scene.traverse(object => {
        if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments) {
          object.geometry.dispose();
          for (const material of Array.isArray(object.material) ? object.material : [object.material]) material.dispose();
        }
      });
    }
  } finally {
    renderer.setRenderTarget(previousTarget);
    target.dispose();
  }
  return failures;
}
