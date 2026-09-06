// Shop-fabricated roof trusses: bottom chord, two raking top chords, a king post and a pair
// of diagonal webs — a plain fink, drawn inside the one member the engine resolves.
//
// The engine bills, exports and picks ONE member per truss (resolve/framing/roof_gable.ts's
// Python twin, `truss_member`), which is what is ordered and set. That member is an
// ENVELOPE: p0/p1 are its two bearings and z0_m/z1_m the plate top and the ridge. Drawn as a
// bar — the rect bucket's default — it fills the whole attic with wood that is not there,
// which is exactly the failure `floorTruss.ts` exists to avoid one storey down.
//
// WHAT IS DRAWING AND WHAT IS MODEL. The chord depth and the truss's own thickness are real
// (flange_thickness_m / width_m). Everything else here is convention:
//   * the web pattern — real panel points come off the fabricator's plate layout, which no
//     model here holds;
//   * the RAISED HEEL. A raised-heel truss's top chords spring a heel above the bottom
//     chord, and the heel height is not recoverable from the envelope, so the top chords are
//     drawn springing from the bottom chord instead. The apex and both bearings land exactly
//     where the member says; the chord slope reads a little steeper than the roof's pitch
//     over the last foot at the eave. The eave itself is drawn by the roof's own
//     sheathing/fascia/soffit members, which are unaffected.
// No stick is added to any bill by any of this.
import * as THREE from "three";

import type { Member } from "../model/types";
import type { MaterialAppearance, ResolvedNordicPalette } from "../nordic/palette";
import { composeCenteredBoxMatrix, UNIT_BOX } from "./memberBox";
import { memberColor } from "./members";
import { memberUidsFor, tagInstancedMemberIdentity } from "./memberPicking";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";
import { markShadowCaster, standardMaterial } from "./surfaces";

// Fallback chord depth when the section carries none: a 2x4 chord on edge.
const DEFAULT_CHORD_DEPTH_M = 3.5 * 0.0254;
// Where the diagonals meet the bottom chord, as a fraction of the span — the quarter points
// of a fink, which is the pattern the engine's own multi-stick truss used to emit.
const DIAGONAL_FOOT_FRACTION = 0.25;

const UP = new THREE.Vector3(0, 1, 0);
const _matrix = new THREE.Matrix4();
const _color = new THREE.Color();

interface Stick {
  center: THREE.Vector3;
  along: THREE.Vector3;   // the stick's own long axis
  length: number;
  across: THREE.Vector3;  // horizontal, across the truss's thickness
  width: number;
  thickness: number;      // depth in the truss's own vertical plane
  color: THREE.ColorRepresentation;
}

export function buildRoofTrusses(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[]) {
  if (!members.length) return;

  const uids = memberUidsFor(ownerUid, members);
  const sticks: Stick[] = [];
  const stickUids: string[] = [];

  members.forEach((m, i) => {
    const dx = m.p1[0] - m.p0[0];
    const dz = m.p1[1] - m.p0[1];
    const span = Math.hypot(dx, dz);
    const rise = m.z1_m - m.z0_m;
    if (span < 1e-9 || rise < 1e-9) return;
    const along = projectPlanDirectionToScene([dx / span, dz / span]);
    const across = new THREE.Vector3(-along.z, 0, along.x);
    const chord = m.flange_thickness_m ?? DEFAULT_CHORD_DEPTH_M;
    const width = m.flange_width_m ?? m.width_m;
    const webT = m.web_thickness_m ?? m.width_m;
    const color = memberColor(m, palette, materials);
    const start = projectPointToScene(m.p0, m.z0_m, center);
    const at = (u: number, z: number) =>
      start.clone().addScaledVector(along, u).addScaledVector(UP, z);
    const push = (stick: Stick) => { sticks.push(stick); stickUids.push(uids[i]); };

    // Bottom chord: bearing to bearing, sitting on the plate.
    push({
      center: at(span / 2, chord / 2), along, length: span, across, width,
      thickness: chord, color,
    });

    // Top chords, bottom-chord top to the apex. `peak` is the underside of the chord at the
    // ridge, so the pair of them close on the member's stated ridge elevation.
    const peak = rise - chord / 2;
    const foot = chord / 2;
    for (const side of [-1, 1] as const) {
      const u0 = side < 0 ? 0 : span;
      const diagonal = new THREE.Vector3()
        .addScaledVector(along, side * span / 2).addScaledVector(UP, peak - foot);
      const length = diagonal.length();
      // NO overrun at either end, unlike the webs below. The two chords meet centreline to
      // centreline at the apex and stop on the bottom chord at the heel, which keeps the
      // truss inside the two elevations the member states — a chord run long at the peak
      // stands above its own ridge, and one run long at the heel hangs under its plate.
      push({
        center: at(u0 + side * span / 4, (foot + peak) / 2), along: diagonal.normalize(),
        length, across, width, thickness: chord, color,
      });
    }

    // King post and the two diagonals: bottom-chord top to the top chords' underside. Every
    // web stops a chord short of the top chord line so the joint reads as a joint.
    const bayTop = peak - chord;
    const bayBottom = chord;
    if (bayTop - bayBottom < webT) return;  // a shallow truss has no room for a web pattern
    push({
      center: at(span / 2, (bayBottom + bayTop) / 2), along: UP, length: bayTop - bayBottom,
      across, width, thickness: webT, color,
    });
    for (const side of [-1, 1] as const) {
      const u0 = span / 2 + side * span * DIAGONAL_FOOT_FRACTION;
      const diagonal = new THREE.Vector3()
        .addScaledVector(along, -side * span * DIAGONAL_FOOT_FRACTION)
        .addScaledVector(UP, bayTop - bayBottom);
      const length = diagonal.length();
      push({
        center: at((u0 + span / 2) / 2, (bayBottom + bayTop) / 2),
        along: diagonal.normalize(), length: length + webT, across, width,
        thickness: webT, color,
      });
    }
  });

  if (!sticks.length) return;
  const mesh = new THREE.InstancedMesh(UNIT_BOX, standardMaterial(undefined, mode),
    sticks.length);
  sticks.forEach((stick, index) => {
    const normal = new THREE.Vector3().crossVectors(stick.across, stick.along).normalize();
    composeCenteredBoxMatrix(_matrix, stick.center, stick.across, stick.width, stick.along,
      stick.length, normal, stick.thickness);
    mesh.setMatrixAt(index, _matrix);
    mesh.setColorAt(index, _color.set(stick.color));
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  markShadowCaster(mesh);
  // Chord, post and diagonal all resolve to the one truss they belong to: the model has a
  // single member there, and picking a web has to select it, not a piece of drawing.
  tagInstancedMemberIdentity(mesh, stickUids);
  group.add(mesh);
}
