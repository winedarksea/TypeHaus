// Outline for one picked piece of an opening (a casing leg, a jamb, a hinge). Pieces share
// materials with the rest of the door or window, so they are outlined rather than tinted —
// the same treatment a framing member gets (→ memberPicking.buildMemberHighlight).
import * as THREE from "three";

const FILL_OPACITY = 0.35;

/** Disposable outline over `meshes`, in `root`'s local space. All geometry is cloned, so the
 *  caller may dispose the result without touching the scene. */
export function buildPieceHighlight(
  meshes: readonly THREE.Mesh[], root: THREE.Object3D, color: THREE.ColorRepresentation,
): THREE.Object3D | null {
  if (!meshes.length) return null;
  const group = new THREE.Group();
  root.updateWorldMatrix(true, false);
  const toRoot = root.matrixWorld.clone().invert();
  for (const mesh of meshes) {
    mesh.updateWorldMatrix(true, false);
    const matrix = toRoot.clone().multiply(mesh.matrixWorld);
    const fill = new THREE.Mesh(mesh.geometry.clone(), new THREE.MeshBasicMaterial({
      color, transparent: true, opacity: FILL_OPACITY, depthWrite: false }));
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, 1),
      new THREE.LineBasicMaterial({ color, depthTest: false }));
    for (const object of [fill, edges]) {
      object.matrixAutoUpdate = false;
      object.matrix.copy(matrix);
      group.add(object);
    }
  }
  group.renderOrder = 999;
  return group;
}
