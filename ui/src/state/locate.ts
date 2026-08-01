// Turning a uid into something the UI can talk about, and the two finding filters every
// surface shares. Split out of state/store.ts: none of this touches the store — it is pure
// lookup over a Model — and keeping it here is what lets the inspector, the issues drawer and
// the 2D/3D panels agree on what a uid *is* without importing the store machinery.
import type { Finding, Model, Provenance, Vec2 } from "../model/types";
import { locateMember, memberCentroid } from "../model/memberIdentity";
import type { SelectionKind } from "./vocabulary";

// uid resolution ------------------------------------------------------------

export interface LocatedElement {
  kind: SelectionKind;
  tag: string;
  storey: string | null;
  centroid: [number, number] | null; // plan-space centre, for the 2D pan-to-element
  source: string | null; // "file:line" of the authoring statement, when the loader captured one
  // Can an edit to this element be written back to source? false → the authoring statement
  // lives outside a `# haus: editable` file (params-generated), so a drag or a field edit
  // would 422 at commit. `null` means the loader captured no provenance at all — unknown, so
  // callers must not pre-empt on it; only an explicit `false` refuses a gesture up front.
  editable: boolean | null;
}

function ringCentroid(points: readonly Vec2[]): [number, number] | null {
  if (!points.length) return null;
  return [
    points.reduce((sum, p) => sum + p[0], 0) / points.length,
    points.reduce((sum, p) => sum + p[1], 0) / points.length,
  ];
}

function sourceOf(provenance: Provenance | null | undefined): string | null {
  return provenance ? `${provenance.file}:${provenance.line}` : null;
}

// null (no provenance) is deliberately *not* folded into false: "we don't know" and "we know
// it can't be written back" drive different UI — see LocatedElement.editable.
function editableOf(provenance: Provenance | null | undefined): boolean | null {
  return provenance ? provenance.editable : null;
}

// Resolve a uid against every selectable record — authored elements first, then the derived
// geometry a 3D pick can land on. One lookup shared by zoomToUid, deleteSelection, and the
// Inspector, so all three agree on what a uid *is*.
export function locateUid(model: Model, uid: string): LocatedElement | null {
  const wall = model.walls.find((w) => w.uid === uid);
  if (wall) return { kind: "wall", tag: wall.tag, storey: wall.storey, source: sourceOf(wall.provenance),
    editable: editableOf(wall.provenance),
    centroid: [(wall.axis[0][0] + wall.axis[1][0]) / 2, (wall.axis[0][1] + wall.axis[1][1]) / 2] };

  const opening = model.openings.find((o) => o.uid === uid);
  if (opening) {
    const host = model.walls.find((w) => w.tag === opening.host);
    return { kind: "opening", tag: opening.tag, storey: host?.storey ?? null,
      source: sourceOf(opening.provenance), editable: editableOf(opening.provenance),
      centroid: host ? [(host.axis[0][0] + host.axis[1][0]) / 2, (host.axis[0][1] + host.axis[1][1]) / 2] : null };
  }

  const room = model.rooms.find((r) => r.uid === uid);
  if (room) return { kind: "room", tag: room.tag, storey: room.storey,
    source: sourceOf(room.provenance), editable: editableOf(room.provenance),
    centroid: ringCentroid(room.clear_face) };

  const stair = (model.stairs ?? []).find((x) => x.uid === uid);
  if (stair) return { kind: "stair", tag: stair.tag, storey: stair.storey,
    source: sourceOf(stair.provenance), editable: editableOf(stair.provenance),
    centroid: ringCentroid(stair.outline) };

  // Placeables carry no provenance in model.json — they are addressed by tag, not file:line.
  const item = (model.canvas_objects ?? []).find((x) => x.uid === uid);
  if (item) return { kind: "canvas_object", tag: item.tag, storey: item.storey,
    source: null, editable: null, centroid: item.position_m ?? null };

  const solid = (model.solids ?? []).find((x) => x.uid === uid);
  if (solid) return { kind: "solid", tag: solid.tag, storey: solid.storey,
    source: sourceOf(solid.provenance), editable: editableOf(solid.provenance),
    centroid: ringCentroid(solid.outline) };

  const bedding = (model.footing_beddings ?? []).find((x) => x.uid === uid);
  if (bedding) return { kind: "footing_bedding", tag: bedding.tag, storey: bedding.storey,
    source: sourceOf(bedding.provenance), editable: editableOf(bedding.provenance),
    centroid: ringCentroid(bedding.outline) };

  const roof = (model.roofs ?? []).find((x) => x.uid === uid);
  if (roof) return { kind: "roof", tag: roof.tag, storey: roof.storey,
    source: sourceOf(roof.provenance), editable: editableOf(roof.provenance),
    centroid: ringCentroid(roof.footprint) };

  const floor = (model.floors ?? []).find((x) => x.uid === uid);
  if (floor) return { kind: "floor", tag: floor.tag, storey: floor.storey,
    source: sourceOf(floor.provenance), editable: editableOf(floor.provenance),
    // A framed floor carries no outline of its own; its joist endpoints bound the deck.
    centroid: ringCentroid(floor.members.flatMap((member) => [member.p0, member.p1])) };

  // Framing members last: their uid is a composite (`<owner uid>::<child key>`) that can never
  // collide with a minted uid above, and resolving one costs a scan of every framed parent.
  const framed = locateMember(model, uid);
  if (framed) return { kind: "member", tag: `${framed.ownerTag} · ${framed.member.key}`,
    storey: framed.storey, source: null, editable: null,
    centroid: memberCentroid(framed.member) };

  return null;
}

// Selector helpers ----------------------------------------------------------

// Passing checks still travel through model.findings (the tri-state PASS/FAIL/UNKNOWN
// result is tracked separately from severity), but the UI only surfaces the ones that
// need attention.
export function visibleFindings(findings: Finding[]): Finding[] {
  return findings.filter((f) => f.result !== "pass");
}

export function findingsFor(model: Model | null, uid: string | null): Finding[] {
  if (!model || !uid) return [];
  return visibleFindings(
    model.findings.filter((f) => f.element === uid || (f.elements ?? []).includes(uid)),
  );
}
