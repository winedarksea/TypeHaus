// How a whole-house glb maps back onto the interactive model (→ emit/gltf/emitter.py).
//
// Split out of components/Panel3D.tsx: this is a pure contract test between two codebases —
// which node names / glTF `extras` the emitter writes and what the viewer will accept — and it
// is easier to keep the two in step when it is not buried in a React component.
import type { SelectionKind, Trade } from "../state/vocabulary";
import { ALL_SELECTION_KINDS, ALL_TRADES } from "../state/vocabulary";

// Whether a fully-tagged whole-house glb may take over from the model.json baseline scene.
// Held OFF until the glTF emitter reaches visual parity with the model.json render path: it
// still (a) extrudes walls flat between z0..z1 rather than raking gable/ToRoof tops to the roof
// slope, and (b) ships flat palette colors instead of the procedural standing-seam / CMU wall
// finishes. Promoting it before then silently downgrades those envelope details, so the glb —
// though now correctly per-object tagged (its identity metadata is still emitted and consumed
// for anything that reads it) — stays a secondary artifact until the emitter closes those gaps.
export const WHOLE_HOUSE_GLB_PRIMARY = false;

// How a whole-house glb node maps back to an interactive element. A node earns an assignment
// via glTF `extras` (GLTFLoader copies these onto object.userData) or, as a fallback, a
// "<trade>|<kind>|<uid>" node name. `kind`/`uid` are optional: untagged envelope geometry only
// needs a trade (to land in the right visibility group), while a selectable node also carries
// its model uid so picking and highlight resolve to the same record model.json uses. The `kind`
// vocabulary is the shared SelectionKind (→ state/store.ts, emit/gltf/emitter.py).
export interface GlbNodeAssignment {
  trade: Trade;
  uid: string | null;
  kind: SelectionKind | null;
}

export function wholeHouseGlbAssignment(
  name: string | undefined,
  userData: Record<string, unknown> | undefined,
): GlbNodeAssignment | null {
  const parts = (name ?? "").split("|");
  const tradeRaw = typeof userData?.trade === "string" ? userData.trade : parts[0];
  if (!tradeRaw || !(ALL_TRADES as readonly string[]).includes(tradeRaw)) return null;
  const kindRaw = typeof userData?.kind === "string" ? userData.kind : parts[1];
  const kind = (ALL_SELECTION_KINDS as readonly string[]).includes(kindRaw)
    ? kindRaw as SelectionKind : null;
  const uidRaw = typeof userData?.uid === "string" ? userData.uid : parts[2];
  return { trade: tradeRaw as Trade, uid: uidRaw || null, kind };
}
