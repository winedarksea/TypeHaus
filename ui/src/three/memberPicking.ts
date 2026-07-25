// Per-member picking for the 3D panel (→ plans/TODO.md "wall framing members are not
// individually pickable").
//
// Framing members are drawn in shared buckets — an InstancedMesh for prismatic lumber, three
// more for i-joist plies, one merged BufferGeometry per raked/seam group — so a member is not
// an Object3D and cannot carry userData of its own. What each bucket *can* carry is an ordered
// list of the member uids it drew, in the exact order it drew them:
//
//   • InstancedMesh  → `memberUidByInstance[intersection.instanceId]`
//   • merged mesh    → `memberUidByBox[floor(intersection.faceIndex / TRIANGLES_PER_BOX)]`
//
// Both are recorded at build time by the builders in three/members.ts, so the index a raycast
// hands back resolves to an engine-authored `<owner uid>::<child key>` identity (→
// model/memberIdentity.ts) rather than to a draw-call ordinal that the next rebuild reshuffles.
import * as THREE from "three";
import type { Member } from "../model/types";
import { memberUid } from "../model/memberIdentity";
import {
  composeMemberBoxMatrix, isRakedMember, rakedBoxGeometry, TRIANGLES_PER_MEMBER_BOX, UNIT_BOX,
} from "./memberBox";
import type { PlanCenter } from "./planGeometry";

const MEMBER_UID_BY_INSTANCE = "memberUidByInstance";
const MEMBER_UID_BY_BOX = "memberUidByBox";

/** Tag an InstancedMesh so instance `i` resolves to `memberUids[i]`. */
export function tagInstancedMemberIdentity(mesh: THREE.InstancedMesh, memberUids: string[]) {
  mesh.userData[MEMBER_UID_BY_INSTANCE] = memberUids;
}

/** Tag a merged mesh so its i-th 12-triangle box resolves to `memberUids[i]`. */
export function tagMergedMemberIdentity(mesh: THREE.Mesh, memberUids: string[]) {
  mesh.userData[MEMBER_UID_BY_BOX] = memberUids;
}

/** Whether this object draws framing members and therefore owns its own per-member identity. */
export function carriesMemberIdentity(object: THREE.Object3D): boolean {
  return Array.isArray(object.userData[MEMBER_UID_BY_INSTANCE])
    || Array.isArray(object.userData[MEMBER_UID_BY_BOX]);
}

/**
 * The member uid a raycast hit landed on, or null when the hit object draws no members.
 * Takes the two index fields rather than the intersection so it is testable without a
 * WebGL context.
 */
export function resolveMemberPickUid(
  object: THREE.Object3D,
  instanceId: number | null | undefined,
  faceIndex: number | null | undefined,
): string | null {
  const byInstance = object.userData[MEMBER_UID_BY_INSTANCE] as string[] | undefined;
  if (Array.isArray(byInstance)) {
    return instanceId == null ? null : byInstance[instanceId] ?? null;
  }
  const byBox = object.userData[MEMBER_UID_BY_BOX] as string[] | undefined;
  if (Array.isArray(byBox)) {
    if (faceIndex == null) return null;
    return byBox[Math.floor(faceIndex / TRIANGLES_PER_MEMBER_BOX)] ?? null;
  }
  return null;
}

/** The uids a bucket will draw, in draw order — what the two tag functions record. */
export function memberUidsFor(ownerUid: string, members: Member[]): string[] {
  return members.map((member) => memberUid(ownerUid, member.key));
}

// A picked member is one stick inside a shared draw call, so it cannot be highlighted the way
// a wall is (by pushing emissive onto its own material — that material is shared with every
// other stud in the bucket). Instead the panel draws a throwaway outline over the member:
// edge lines with depth testing off, so a stud buried inside a finished wall is still visible
// once picked, over a faint translucent fill that gives the outline a body to read against.
const HIGHLIGHT_FILL_OPACITY = 0.35;
const HIGHLIGHT_EDGE_WIDTH_DEG = 1; // every box edge is a real crease; keep them all

/**
 * A disposable outline of one member, in scene space, or null if the member has no drawable
 * box. A raked member (rafter, raked plate, sloped i-joist) is outlined from its own sheared
 * 8-corner box; everything else from the same prism transform the instanced buckets use, so
 * the outline lands exactly on the drawn stick.
 */
export function buildMemberHighlight(
  member: Member, center: PlanCenter, color: THREE.ColorRepresentation,
): THREE.Object3D | null {
  const group = new THREE.Group();
  let geometry: THREE.BufferGeometry;
  if (isRakedMember(member)) {
    const raked = rakedBoxGeometry(member, center);
    if (!raked) return null;
    geometry = raked;
  } else {
    geometry = UNIT_BOX.clone();
    geometry.applyMatrix4(composeMemberBoxMatrix(new THREE.Matrix4(), member, center));
  }
  group.add(new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
    color, transparent: true, opacity: HIGHLIGHT_FILL_OPACITY, depthWrite: false,
  })));
  group.add(new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, HIGHLIGHT_EDGE_WIDTH_DEG),
    new THREE.LineBasicMaterial({ color, depthTest: false }),
  ));
  // Above every opaque pass, so the outline is not eaten by the wall the stud sits in.
  group.renderOrder = 999;
  return group;
}
