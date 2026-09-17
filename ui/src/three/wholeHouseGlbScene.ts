// Promoting the engine's whole-house glb to the primary scene, when it carries per-object
// trade metadata (→ wholeHouseGlb.ts for the contract, WHOLE_HOUSE_GLB_PRIMARY for why it
// stays off). Split out of components/Panel3D.tsx: it is a self-contained load-classify-adopt
// step over the trade containers, and the panel only needs to know whether it happened.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { Trade } from "../state/vocabulary";
import { ALL_TRADES } from "../state/vocabulary";
import type { SceneRegistry } from "./builders/scene";
import { disposeGroup } from "./members";
import {
  wholeHouseGlbAssignment, WHOLE_HOUSE_GLB_PRIMARY, type GlbNodeAssignment,
} from "./wholeHouseGlb";

/** Parse `blob` and hand the scene to `adopt`, unless `stillCurrent` says the scene it was
 *  fetched for has been rebuilt since. Every failure keeps the model.json baseline. */
export function loadWholeHouseGlb(
  blob: Blob, stillCurrent: () => boolean, adopt: (root: THREE.Object3D) => void,
) {
  blob.arrayBuffer().then((buffer) => {
    if (!stillCurrent()) return;
    new GLTFLoader().parse(buffer, "", (gltf) => {
      if (!stillCurrent()) { disposeGroup(gltf.scene); return; }
      adopt(gltf.scene);
    }, () => { /* parse failure → keep the model.json baseline */ });
  }).catch(() => { /* read failure → keep the model.json baseline */ });
}

/**
 * Take over the trade containers with the glb's nodes when every renderable node classifies
 * to a trade set; otherwise dispose it and return false. Walks up from each mesh so a tagged
 * parent covers its (often untagged) child primitives. Nodes are re-parented in place with
 * their world transform baked, into the container of their primary trade, carrying the full
 * set on userData so the trade filter reaches them like any built mesh.
 */
export function applyWholeHouseGlb(
  root: THREE.Object3D, tradeGroups: Record<Trade, THREE.Group>, registry: SceneRegistry,
): boolean {
  // Gated off by decision, not by missing geometry parity (see WHOLE_HOUSE_GLB_PRIMARY):
  // promoting the glb would trade the procedural standing-seam/CMU finishes for the export's
  // flat portable colours.
  if (!WHOLE_HOUSE_GLB_PRIMARY) { disposeGroup(root); return false; }
  const tagged: { mesh: THREE.Mesh; assignment: GlbNodeAssignment }[] = [];
  let renderable = 0;
  let unstructured = false;
  root.traverse((node) => {
    if (unstructured || !(node instanceof THREE.Mesh)) return;
    renderable++;
    let assignment: GlbNodeAssignment | null = null;
    for (let o: THREE.Object3D | null = node; o && !assignment; o = o.parent) {
      assignment = wholeHouseGlbAssignment(o.name, o.userData);
    }
    if (!assignment) { unstructured = true; return; }
    tagged.push({ mesh: node, assignment });
  });
  if (renderable === 0 || unstructured) { disposeGroup(root); return false; }

  for (const trade of ALL_TRADES) {
    disposeGroup(tradeGroups[trade]);
    tradeGroups[trade].clear();
  }
  registry.picks = [];
  registry.byUid.clear();
  root.updateMatrixWorld(true);
  for (const { mesh, assignment } of tagged) {
    const world = mesh.matrixWorld.clone();
    const group = tradeGroups[assignment.trade];
    group.add(mesh); // trade groups sit at the world origin, so world == local below
    world.decompose(mesh.position, mesh.quaternion, mesh.scale);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    // The engine's sets, unrefined: the glTF extras stamp `framing`, and the Views panel's
    // framing FACETS (model/tradeVisibility.ts) are derived from a layer function this path
    // never sees. Whoever promotes the GLB has to carry the function into the extras first,
    // or "just the wooden sticks" comes back as a plywood box.
    // Nor is `userData.storey` stamped, so the 3D level filter would not reach these meshes.
    mesh.userData.trades = [...assignment.trades];
    if (assignment.uid) {
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      registry.byUid.set(assignment.uid, [...(registry.byUid.get(assignment.uid) ?? []), ...materials]);
      if (assignment.kind) {
        mesh.userData.uid = assignment.uid;
        mesh.userData.selectionKind = assignment.kind;
        registry.picks.push(mesh);
      }
    }
  }
  disposeGroup(root); // drop any leftover empty container nodes
  return true;
}
