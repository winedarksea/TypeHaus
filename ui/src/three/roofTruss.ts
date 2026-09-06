// Shop-fabricated roof trusses: a bottom chord, two raking top chords with their eave
// tails, and a fink web pattern — drawn inside the one member the engine resolves.
//
// The engine bills, exports and picks ONE member per truss (`truss_member`, the Python twin
// of this file's subject), which is what is ordered and set. That member is an ENVELOPE:
// p0/p1 are its two bearings and z0_m/z1_m the plate top and the ridge. Drawn as a bar —
// the rect bucket's default — it fills the whole attic with wood that is not there, which
// is exactly the failure `floorTruss.ts` exists to avoid one storey down.
//
// WHAT IS DRAWING AND WHAT IS MODEL. The chord depth and the truss's own thickness are real
// (flange_thickness_m / width_m), and so are the three facts on `m.truss`: the raised heel
// the top chords spring from, the eave tails they run out to, and whether this is a studded
// gable end. The WEB PATTERN is the one convention left — real panel points come off the
// fabricator's plate layout, which no model here holds — so it is drawn as the fink a
// residential truss of this span is plated as, closing on the apex the member states.
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
// A fink's bottom-chord panel points, as fractions of the span: the two webs off the apex
// land at the third points and the pair below them rise to the top chords' midpoints,
// which is the W the pattern is named for.
const FINK_PANEL_FRACTION = 1 / 3;
const TOP_CHORD_PANEL_FRACTION = 1 / 4;
// A gable end is infilled at ordinary stud spacing, and a sliver shorter than this is not a
// stud — the chords already meet there.
const GABLE_STUD_SPACING_M = 16 * 0.0254;
const MIN_GABLE_STUD_M = 1.5 * 0.0254;

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

/** A point in the truss's own plane: `u` along the span from the p0 bearing, `z` above the plate. */
type Pt = readonly [number, number];

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
    // A stick between two points of the truss's own plane, grown by `overrun` at each end so
    // a joint reads as a joint rather than as two boxes touching at a corner.
    const push = (a: Pt, b: Pt, thickness: number, overrun = 0) => {
      const axis = new THREE.Vector3()
        .addScaledVector(along, b[0] - a[0]).addScaledVector(UP, b[1] - a[1]);
      const length = axis.length();
      if (length < 1e-9) return;
      sticks.push({
        center: at((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), along: axis.normalize(),
        length: length + 2 * overrun, across, width, thickness, color,
      });
      stickUids.push(uids[i]);
    };

    // The top chord line, as the centreline it is: it springs a raised heel above the plate
    // at each bearing and closes on the member's stated ridge at mid-span. A truss whose
    // heel would not fit under its own apex is drawn springing off the bottom chord, which
    // is what this did before the heel was carried at all.
    const heel = m.truss?.heel_m ?? chord;
    const footZ = (heel >= rise - chord ? chord : heel) + chord / 2;
    const peakZ = rise - chord / 2;
    const slope = (peakZ - footZ) / (span / 2);
    const topChordZ = (u: number) => footZ + slope * Math.min(u, span - u);
    // Bottom chord: bearing to bearing, sitting on the plate.
    push([0, chord / 2], [span, chord / 2], chord);
    // Top chords, each from its eave tail up to the apex. The tails are the truss's own
    // overhang — what the fascia and the soffit land on.
    const tailLo = m.truss?.tail_lo_m ?? 0;
    const tailHi = m.truss?.tail_hi_m ?? 0;
    push([-tailLo, topChordZ(-tailLo)], [span / 2, peakZ], chord);
    push([span / 2, peakZ], [span + tailHi, topChordZ(span + tailHi)], chord);

    // Webs (or a gable end's verticals) run between the bottom chord's top and the top
    // chord's underside, and stop a chord short of it so the plate joint reads.
    const bayBottom = chord;
    const bayAt = (u: number) => topChordZ(u) - chord / 2;
    if (bayAt(span / 2) - bayBottom < webT) return;  // too shallow for any pattern

    if (m.truss?.gable) {
      // A drop truss: the plant plates verticals in at stud spacing, so the gable end
      // sheathes like a wall. They are inside the one member, not studs beside it.
      for (let u = GABLE_STUD_SPACING_M; u < span - 1e-9; u += GABLE_STUD_SPACING_M) {
        if (bayAt(u) - bayBottom < MIN_GABLE_STUD_M) continue;
        push([u, bayBottom], [u, bayAt(u)], webT);
      }
      return;
    }

    // Fink: a V off the apex down to the third points, and a pair rising from those points
    // back to the top chords' midpoints — the W. A truss too shallow for the pair gets the
    // king post that a short span is really plated with.
    const apex: Pt = [span / 2, bayAt(span / 2)];
    const kingOnly = bayAt(span * FINK_PANEL_FRACTION) - bayBottom < webT;
    if (kingOnly) {
      push([span / 2, bayBottom], apex, webT, webT / 2);
      return;
    }
    for (const side of [-1, 1] as const) {
      const uFoot = span / 2 + side * span * (0.5 - FINK_PANEL_FRACTION);
      const uTop = span / 2 + side * span * (0.5 - TOP_CHORD_PANEL_FRACTION);
      const foot: Pt = [uFoot, bayBottom];
      push(foot, apex, webT, webT / 2);
      push(foot, [uTop, bayAt(uTop)], webT, webT / 2);
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
