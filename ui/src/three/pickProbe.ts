// Headless test hook (`window.__haus.probe`): aim the camera so a given piece is the first
// thing under its own centre, and report where to click. `npm run pick-check` then clicks
// with a real pointer event, so the whole chain (raycast, identity, store) is exercised.
import * as THREE from "three";
import { resolveMemberPickUid } from "./memberPicking";
import { isRenderedInScene } from "./builders/registry";

export interface ProbeQuery {
  /** Element uid a plain mesh answers to, or the member uid of a framing stick. */
  uid: string;
  piece?: string;
  /** Model-space [x, y, z] to aim at: required for a stick inside a shared bucket (no mesh
   *  of its own), and for one part of a group that shares a uid (a baluster). */
  at?: [number, number, number];
}

export interface ProbeDeps {
  camera: THREE.PerspectiveCamera;
  dom: HTMLElement;
  picks: () => THREE.Mesh[];
  planCenter: () => readonly [number, number];
  /** Re-aim the orbit camera at `target`, `radius` away, from `theta`, and redraw. */
  frame: (target: THREE.Vector3, radius: number, theta: number, draw: boolean) => void;
}

const ANGLES = Array.from({ length: 24 }, (_, i) => (i * Math.PI) / 6);

export function installPickProbe(deps: ProbeDeps) {
  const haus = (window as unknown as { __haus?: Record<string, unknown> }).__haus;
  if (!haus) return;
  const raycaster = new THREE.Raycaster();
  const matches = (hit: THREE.Intersection, query: ProbeQuery) => {
    const object = hit.object;
    const member = resolveMemberPickUid(object, hit.instanceId, hit.faceIndex);
    if (member) return member === query.uid;
    return object.userData.uid === query.uid && (!query.piece || object.userData.piece === query.piece);
  };
  haus.probe = (query: ProbeQuery) => {
    const picks = deps.picks().filter(isRenderedInScene);
    const centre = deps.planCenter();
    const target = new THREE.Vector3();
    if (query.at) target.set(query.at[0] - centre[0], query.at[2], -(query.at[1] - centre[1]));
    else {
      const box = new THREE.Box3();
      for (const mesh of picks) {
        if (mesh.userData.uid === query.uid && (!query.piece || mesh.userData.piece === query.piece)) {
          box.expandByObject(mesh);
        }
      }
      if (box.isEmpty()) return null;
      box.getCenter(target);
    }
    const rect = deps.dom.getBoundingClientRect();
    for (const radius of [0.5, 1, 2, 4, 8]) {
      for (const theta of ANGLES) {
        deps.frame(target, radius, theta, false);
        deps.camera.updateMatrixWorld();
        raycaster.setFromCamera(new THREE.Vector2(0, 0), deps.camera);
        const first = raycaster.intersectObjects(picks, false)[0];
        if (first && matches(first, query)) {
          deps.frame(target, radius, theta, true);
          return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, theta, radius };
        }
      }
    }
    return null;
  };
}
