// Open-web floor trusses: two 2x4-flat chords, a bearing block standing at each end, and a
// zig-zag of diagonal webs between them.
//
// A `floor_truss` used to fall into the rect bucket and draw as one solid 3 1/2 x 11 7/8
// bar. Catlin's second floor is trussed west of x=18' *because* a duct, a drain stack or a
// riser can cross through the webs (8 7/8" clear chord to chord); a solid bar hides every
// one of those crossings behind wood that is not there.
//
// Viewer-side only, like buildIJoists' three plies: the engine still resolves, bills and
// exports one fabricated member per truss, which is what is bought. No stick is added.
//
// The panel layout is a drawing convention — real panel points come off the fabricator's
// plate layout, which no model here holds. Panels are sized to about twice the depth and
// divided evenly between the end blocks, landing the webs near the 40-50 degrees a floor
// truss carries.
import * as THREE from "three";

import type { Member } from "../model/types";
import type { MaterialAppearance, ResolvedNordicPalette } from "../nordic/palette";
import { composeCenteredBoxMatrix, UNIT_BOX } from "./memberBox";
import { memberColor } from "./members";
import { memberUidsFor, tagInstancedMemberIdentity } from "./memberPicking";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";
import { markShadowCaster, standardMaterial } from "./surfaces";

// Target panel length as a multiple of the truss depth. An 11 7/8" truss lands near 24",
// which is what a floor truss of that depth is usually plated at.
const PANEL_PER_DEPTH = 2;
// A truss shorter than this many panels is drawn with the minimum a zig-zag needs.
const MIN_PANELS = 2;
// The vertical block at each end, standing between the chords over the bearing. 3 1/2"
// square in plan — the same 2x4 flat the chords are, turned on end.
const END_BLOCK_THICKNESS_M = 3.5 * 0.0254;

const UP = new THREE.Vector3(0, 1, 0);
const _matrix = new THREE.Matrix4();
const _color = new THREE.Color();

interface Web {
  center: THREE.Vector3;
  along: THREE.Vector3;   // the web's own long axis
  length: number;
  across: THREE.Vector3;  // horizontal, the chord's 3 1/2" face
  width: number;
  thickness: number;
  color: THREE.ColorRepresentation;
}

/** Panel points along a truss of clear run `run`, as fractions of it. */
function panelCount(run: number, depth: number): number {
  const target = Math.max(depth * PANEL_PER_DEPTH, 1e-6);
  return Math.max(MIN_PANELS, Math.round(run / target));
}

export function buildFloorTrusses(group: THREE.Group, members: Member[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette, ownerUid: string,
  materials?: readonly MaterialAppearance[]) {
  if (!members.length) return;

  const chords = new THREE.InstancedMesh(UNIT_BOX, standardMaterial(undefined, mode),
    members.length * 2);
  const chordUids: string[] = [];
  const uids = memberUidsFor(ownerUid, members);
  const webs: Web[] = [];
  const webUids: string[] = [];
  let chordIndex = 0;

  members.forEach((m, i) => {
    const dx = m.p1[0] - m.p0[0];
    const dz = m.p1[1] - m.p0[1];
    const length = Math.hypot(dx, dz);
    if (length < 1e-9) return;
    const along = projectPlanDirectionToScene([dx / length, dz / length]);
    const across = new THREE.Vector3(-along.z, 0, along.x);
    const depth = m.z1_m - m.z0_m;
    const chordT = m.flange_thickness_m ?? depth * 0.126;
    const chordW = m.flange_width_m ?? m.width_m;
    const webT = m.web_thickness_m ?? chordT;
    const color = memberColor(m, palette, materials);
    const start = projectPointToScene(m.p0, m.z0_m, center);
    const at = (u: number, z: number) =>
      start.clone().addScaledVector(along, u).addScaledVector(UP, z);

    for (const z of [chordT / 2, depth - chordT / 2]) {
      composeCenteredBoxMatrix(_matrix, at(length / 2, z), across, chordW,
        along, length, UP, chordT);
      chords.setMatrixAt(chordIndex, _matrix);
      chords.setColorAt(chordIndex, _color.set(color));
      chordUids[chordIndex] = uids[i];
      chordIndex += 1;
    }

    // The open bay between the chords: everything below stands in it, nothing crosses it.
    const bay = Math.max(depth - 2 * chordT, 1e-4);
    const bayMid = chordT + bay / 2;
    for (const u of [END_BLOCK_THICKNESS_M / 2, length - END_BLOCK_THICKNESS_M / 2]) {
      webs.push({
        center: at(u, bayMid), along: UP, length: bay, across, width: chordW,
        thickness: END_BLOCK_THICKNESS_M, color,
      });
      webUids.push(uids[i]);
    }

    const clear = length - 2 * END_BLOCK_THICKNESS_M;
    if (clear <= bay * 0.5) return;  // too short to hold a zig-zag; the blocks are the web
    const panels = panelCount(clear, depth);
    const panel = clear / panels;
    for (let p = 0; p < panels; p += 1) {
      const u0 = END_BLOCK_THICKNESS_M + p * panel;
      const rising = p % 2 === 0;
      const z0 = rising ? chordT : depth - chordT;
      const z1 = rising ? depth - chordT : chordT;
      const diagonal = new THREE.Vector3()
        .addScaledVector(along, panel).addScaledVector(UP, z1 - z0);
      const run = diagonal.length();
      webs.push({
        center: at(u0 + panel / 2, (z0 + z1) / 2), along: diagonal.normalize(),
        // Overrun by a web thickness so the square-cut ends bury in the chords instead of
        // stopping short of them at the panel points.
        length: run + webT, across, width: chordW, thickness: webT, color,
      });
      webUids.push(uids[i]);
    }
  });

  const webMesh = new THREE.InstancedMesh(UNIT_BOX, standardMaterial(undefined, mode),
    Math.max(webs.length, 1));
  webs.forEach((web, index) => {
    const normal = new THREE.Vector3().crossVectors(web.across, web.along).normalize();
    composeCenteredBoxMatrix(_matrix, web.center, web.across, web.width, web.along,
      web.length, normal, web.thickness);
    webMesh.setMatrixAt(index, _matrix);
    webMesh.setColorAt(index, _color.set(web.color));
  });
  chords.count = chordIndex;
  webMesh.count = webs.length;
  for (const [mesh, memberUids] of [[chords, chordUids], [webMesh, webUids]] as const) {
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    markShadowCaster(mesh);
    // Chord, block and diagonal all resolve to the one truss they belong to: the model has
    // a single member there, and picking a web has to select it, not a piece of drawing.
    tagInstancedMemberIdentity(mesh, memberUids as string[]);
    group.add(mesh);
  }
}
