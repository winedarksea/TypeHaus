import * as THREE from "three";
import { ELECTRICAL_HIGHLIGHT_HEX } from "../state/vocabulary";

// Electrical highlight: wiring devices, device boxes and wall plates are drawn in true
// product colour; this tints them one bright colour and restores them when off.

/** Below this relative luminance a material is a slot or recess and stays dark. */
const DARK_LUMINANCE = 0.15;

/** Tag an object (and, via traversal, its meshes) as electrical rough-in. */
export function tagElectrical(object: THREE.Object3D): void {
  object.userData.electrical = true;
}

const isElectrical = (mesh: THREE.Object3D): boolean => {
  for (let node: THREE.Object3D | null = mesh; node; node = node.parent) {
    if (node.userData.electrical) return true;
  }
  return false;
};

type Colored = THREE.Material & { color: THREE.Color };
const hasColor = (m: THREE.Material): m is Colored => (m as Colored).color instanceof THREE.Color;
const slots = (mesh: THREE.Mesh): THREE.Material[] =>
  Array.isArray(mesh.material) ? mesh.material : [mesh.material];

const luminance = (c: THREE.Color) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;

/** Tint (on) or restore (off) every tagged mesh under `root`. Idempotent. */
export function applyElectricalHighlight(root: THREE.Object3D, on: boolean): void {
  const tagged: THREE.Mesh[] = [];
  const plain = new Set<THREE.Material>(); // materials an untagged mesh also draws with
  root.traverse((node) => {
    if (!(node instanceof THREE.Mesh)) return;
    if (isElectrical(node)) tagged.push(node);
    else for (const m of slots(node)) plain.add(m);
  });
  const tint = new THREE.Color(ELECTRICAL_HIGHLIGHT_HEX);
  for (const mesh of tagged) {
    const originals = mesh.userData.trueMaterials as THREE.Material[] | undefined;
    if (!on) {
      if (originals) { // a clone was made for this mesh: swap the true material back
        const clones = slots(mesh);
        mesh.material = Array.isArray(mesh.material) ? originals : originals[0];
        for (const c of clones) c.dispose();
        delete mesh.userData.trueMaterials;
      }
      for (const m of slots(mesh)) {
        if (hasColor(m) && m.userData.trueColor !== undefined) m.color.setHex(m.userData.trueColor);
      }
      continue;
    }
    const next = slots(mesh).map((material) => {
      if (!hasColor(material)) return material;
      if (material.userData.trueColor === undefined) material.userData.trueColor = material.color.getHex();
      const true_ = new THREE.Color(material.userData.trueColor);
      if (luminance(true_) < DARK_LUMINANCE) return material;
      if (!plain.has(material)) { material.color.copy(tint); return material; }
      const clone = material.clone() as Colored;
      clone.userData = { trueColor: material.userData.trueColor };
      clone.color.copy(tint);
      return clone;
    });
    // Shared materials were cloned: keep the originals so "off" can put them back.
    if (!originals && next.some((m, i) => m !== slots(mesh)[i])) {
      mesh.userData.trueMaterials = [...slots(mesh)];
      mesh.material = Array.isArray(mesh.material) ? next : next[0];
    }
  }
}
