// Open-web floor trusses: two 2x4-flat chords between which the engine's derived web layout
// stands: OSB TrimEnd blocks, chase posts and Warren diagonals (`member.web`, served from
// resolve/open_web.py OpenWebShape).
//
// A `floor_truss` used to fall into the rect bucket and draw as one solid 3 1/2 x 11 7/8
// bar. Catlin's second floor is trussed west of x=18' *because* a duct, a drain stack or a
// riser can cross through the webs; a solid bar hides every one of those crossings behind
// wood that is not there.
//
// Viewer-side only, like buildIJoists' three plies: the engine still resolves, bills and
// exports one fabricated member per truss, which is what is bought. No stick is added. No
// panel convention lives here: a truss whose deck quotes no published openings has no `web`
// and draws as its two chords alone, rather than a layout nobody derived.
import * as THREE from "three";

import type { Member } from "../model/types";
import type { MaterialAppearance, ResolvedNordicPalette } from "../nordic/palette";
import { composeCenteredBoxMatrix, UNIT_BOX } from "./memberBox";
import { memberColor } from "./members";
import { memberUidsFor, tagInstancedMemberIdentity } from "./memberPicking";
import { projectPlanDirectionToScene, projectPointToScene, type PlanCenter } from "./planGeometry";
import { markShadowCaster, standardMaterial } from "./surfaces";

// OSB TrimEnd blocks are drawn in OSB, not the chord's lumber colour.
const TRIM_END_COLOR = 0xc9a66b;

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

    // The derived web layout: boxes for TrimEnds and chase posts, centrelines for diagonals.
    for (const [kind, run0, z0, run1, z1] of m.web?.sticks ?? []) {
      if (kind === "diagonal") {
        const diagonal = new THREE.Vector3()
          .addScaledVector(along, run1 - run0).addScaledVector(UP, z1 - z0);
        const run = diagonal.length();
        webs.push({
          center: at((run0 + run1) / 2, (z0 + z1) / 2), along: diagonal.normalize(),
          // Overrun by a web thickness so the square-cut ends bury in the chords instead of
          // stopping short of them at the panel points.
          length: run + webT, across, width: chordW, thickness: webT, color,
        });
      } else {
        webs.push({
          center: at((run0 + run1) / 2, (z0 + z1) / 2), along: UP, length: z1 - z0, across,
          width: chordW, thickness: run1 - run0,
          color: kind === "trim_end" ? TRIM_END_COLOR : color,
        });
      }
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
