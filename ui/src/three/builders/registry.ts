// The bookkeeping every scene builder shares: which meshes a click can land on, which model
// element each one answers to, and which trades it rides.
//
// Split out of components/Panel3D.tsx with the builders themselves. The contract is the same
// one it always was — snapshot `parent.children.length` before you build, pass it here
// afterwards — and having it in one small module is what keeps the four builder families from
// each inventing their own.
import * as THREE from "three";
import { primaryTradeVisible, type VisibleTrades } from "../../model/tradeVisibility";
import { carriesMemberIdentity } from "../memberPicking";
import type { SelectionKind } from "../../state/vocabulary";

/** Whether an object and every ancestor above it is visible — three's own render-time test. */
export function isRenderedInScene(object: THREE.Object3D): boolean {
  for (let node: THREE.Object3D | null = object; node; node = node.parent) {
    if (!node.visible) return false;
  }
  return true;
}

// Stamp every object a builder just added to `parent` with the trade set it rides, so trade
// visibility can flip it without rebuilding the scene. Fill-in semantics: an object a builder
// already tagged (a wall's per-layer bands, a roof's skin buckets) keeps its own, finer set,
// and only the untagged rest takes the element's. Snapshot parent.children.length before
// building and pass it here afterwards — the same contract registerSelectable uses.
export function tagTrades(
  parent: THREE.Object3D, firstChildIndex: number, trades: readonly string[],
) {
  for (let index = firstChildIndex; index < parent.children.length; index++) {
    const child = parent.children[index];
    if (!child.userData.trades) child.userData.trades = [...trades];
  }
}

/** Stamp every object a builder just added to `parent` with the storey it is filed on, so a
 *  hidden level can flip it without a rebuild. `null` (the site sheet) stays untagged. */
export function tagStorey(parent: THREE.Object3D, firstChildIndex: number, storey: string | null) {
  if (!storey) return;
  for (let index = firstChildIndex; index < parent.children.length; index++) {
    parent.children[index].userData.storey = storey;
  }
}

/** Whether a tagged object draws: a hidden storey wins over any trade, then the trade rule. */
export function objectVisible(
  userData: Record<string, unknown>, visible: VisibleTrades, hiddenStoreys: ReadonlySet<string>,
): boolean {
  const storey = userData.storey as string | undefined;
  if (storey && hiddenStoreys.has(storey)) return false;
  const trades = userData.trades as string[] | undefined;
  return trades ? primaryTradeVisible(trades, visible) : true;
}

/** Apply the trade and level filters to everything under `root`. Objects with neither tag are
 *  left alone — their ancestors decide. One traversal, no geometry work, so it runs on every
 *  rebuild. */
export function applyVisibility(
  root: THREE.Object3D, visible: VisibleTrades, hiddenStoreys: ReadonlySet<string>,
) {
  root.traverse((object) => {
    if (object.userData.trades || object.userData.storey) {
      object.visible = objectVisible(object.userData, visible, hiddenStoreys);
    }
  });
}

/** The trade filter alone. */
export function applyTradeVisibility(root: THREE.Object3D, visible: VisibleTrades) {
  applyVisibility(root, visible, new Set());
}

// Make every mesh a builder just added to `parent` resolve to one model element: snapshot
// parent.children.length before building, pass it here afterwards. Nordic edge overlays are
// LineSegments, so they stay out of the raycast set.
//
// Framing-member buckets are the one exception to the "one mesh, one element" rule: they draw
// hundreds of sticks per draw call and carry their own per-instance / per-box identity
// (→ three/memberPicking.ts), so a click on a joist, a tread or a rafter resolves to *that
// member*, not to the floor / stair / roof around it. They still join `picks` (they must stay
// clickable) and still contribute their material to the owner's highlight set, so selecting the
// owner keeps lighting up its framing the way it always did.
export function registerSelectable(
  parent: THREE.Object3D,
  firstChildIndex: number,
  uid: string,
  kind: SelectionKind,
  picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>,
) {
  // Deduped: an opening's frame material is shared by half a dozen boxes, and the highlight
  // pass would otherwise set the same emissive over and over.
  const materials = new Set(byUid.get(uid) ?? []);
  for (let index = firstChildIndex; index < parent.children.length; index++) {
    const child = parent.children[index];
    if (!(child instanceof THREE.Mesh)) continue;
    if (!carriesMemberIdentity(child)) {
      child.userData.uid = uid;
      child.userData.selectionKind = kind;
    }
    picks.push(child);
    const material = child.material;
    for (const one of Array.isArray(material) ? material : [material]) materials.add(one);
  }
  if (materials.size) byUid.set(uid, [...materials]);
}

/** Add the member buckets a builder just appended to `parent` to the raycast set. Used where
 *  there is no registerSelectable pass to sweep them up — wall framing, which selects as its
 *  individual members and never as a single "wall framing" element. */
export function registerMemberPicks(parent: THREE.Object3D, firstChildIndex: number, picks: THREE.Mesh[]) {
  for (let index = firstChildIndex; index < parent.children.length; index++) {
    const child = parent.children[index];
    if (child instanceof THREE.Mesh && carriesMemberIdentity(child)) picks.push(child);
  }
}

