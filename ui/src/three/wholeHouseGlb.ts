// How a whole-house glb maps back onto the interactive model (→ emit/gltf/emitter.py).
//
// Split out of components/Panel3D.tsx: this is a pure contract test between two codebases —
// which node names / glTF `extras` the emitter writes and what the viewer will accept — and it
// is easier to keep the two in step when it is not buried in a React component.
import type { SelectionKind, Trade } from "../state/vocabulary";
import { ALL_SELECTION_KINDS, ALL_TRADES } from "../state/vocabulary";

// Whether a fully-tagged whole-house glb may take over from the model.json baseline scene.
//
// OFF by decision, not by missing parity. The gaps that used to hold it back are closed: the
// emitter no longer derives any geometry of its own, it reads the same derived-geometry IR the
// IFC export reads (engine `resolve/geometry_*.py`), so walls rake to their roof slope, studs
// carry their true section, and the two exports agree by construction rather than by review.
//
// What is left is not a bug, it is a difference in kind. The glb ships one flat portable colour
// per surface — which is exactly what Revit and SketchUp want — while the viewer maps the same
// material key to a procedural, themed material (standing seam, CMU, grain). Promoting the glb
// to the primary scene would trade the live finishes for the export's flat ones and gain
// nothing the viewer does not already have.
//
// So the glb stays the export artifact it is good at (Revit / SketchUp / viewer handoff), and
// this flag stays false. Do not read it as unfinished work; flip it only if the viewer's render
// path is deliberately being retired.
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
