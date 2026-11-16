import * as THREE from "three";
import { ELECTRICAL_HIGHLIGHT_HEX } from "../state/vocabulary";
import { applyElectricalHighlight, tagElectrical } from "./electricalHighlight";

export function runElectricalHighlightTests() {
  const white = new THREE.MeshStandardMaterial({ color: 0xf0f0ed });
  const slot = new THREE.MeshStandardMaterial({ color: 0x1a1a1a });
  const shared = new THREE.MeshStandardMaterial({ color: 0xeeeeee });
  const root = new THREE.Group();
  const plate = new THREE.Mesh(new THREE.BoxGeometry(), white);
  const recess = new THREE.Mesh(new THREE.BoxGeometry(), slot);
  const tagged = new THREE.Mesh(new THREE.BoxGeometry(), shared);
  const other = new THREE.Mesh(new THREE.BoxGeometry(), shared); // untagged, same material
  for (const m of [plate, recess, tagged]) tagElectrical(m);
  root.add(plate, recess, tagged, other);

  applyElectricalHighlight(root, true);
  if (white.color.getHex() !== ELECTRICAL_HIGHLIGHT_HEX) throw new Error("plate must take the tint");
  if (slot.color.getHex() !== 0x1a1a1a) throw new Error("a dark slot must stay dark");
  if (shared.color.getHex() !== 0xeeeeee || tagged.material === shared) {
    throw new Error("a material shared with a non-electrical mesh must be cloned, not tinted");
  }
  applyElectricalHighlight(root, true); // idempotent: no second clone, no drift
  applyElectricalHighlight(root, false);
  if (white.color.getHex() !== 0xf0f0ed) throw new Error("off must restore true colour");
  if (tagged.material !== shared || other.material !== shared) {
    throw new Error("off must put the shared material back");
  }
  console.log("Electrical highlight tests passed.");
}
