import * as THREE from "three";
import type { Member, Model } from "../model/types";
import { isMemberUid, locateMember, memberUid, parseMemberUid } from "../model/memberIdentity";
import { buildMembers } from "./members";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { seatedProfileVertices, TRIANGLES_PER_MEMBER_BOX } from "./memberBox";
import {
  buildMemberHighlight, carriesMemberIdentity, memberIndexForTriangle, resolveMemberPickUid,
} from "./memberPicking";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function member(overrides: Partial<Member>): Member {
  return {
    key: "stud-000", parent_uid: null, category: "stud", profile: "2x6", p0: [0, 0], p1: [0, 0],
    z0_m: 0, z1_m: 2.44, length_m: 2.44, z0_end_m: null, z1_end_m: null, shape: "rect",
    width_m: 0.038, depth_m: 0.14, flange_width_m: null, flange_thickness_m: null,
    web_thickness_m: null, plies: 1, orient: [1, 0], connection: null, material: null, trade: null,
    ...overrides,
  };
}

const CENTER: [number, number] = [0, 0];

// The uid scheme. Everything downstream (pick → select → inspect → highlight) depends on this
// being reversible and on it never colliding with a minted element uid.
function checkMemberUidScheme() {
  const uid = memberUid("CAW101AAAA", "stud-007");
  const parsed = parseMemberUid(uid);
  assert(parsed?.ownerUid === "CAW101AAAA" && parsed?.memberKey === "stud-007",
    "A member uid round-trips back to its owner uid and child key");
  assert(!isMemberUid("CAW101AAAA"), "A plain minted uid is not a member uid");
  assert(!isMemberUid(""), "An empty uid is not a member uid");
  // Child keys carry hyphens and dots; the separator must survive all of them.
  const hyphenated = memberUid("RF9AAAAAAA", "W-G-E-closure-2-sheathing");
  assert(parseMemberUid(hyphenated)?.memberKey === "W-G-E-closure-2-sheathing",
    "A hyphen-heavy child key survives the join/split");
}

// A prismatic bucket is one InstancedMesh; instance i must be member i.
function checkInstancedBucketResolvesPerStud() {
  const group = new THREE.Group();
  const studs = [member({ key: "stud-000" }), member({ key: "stud-001", p0: [0.4, 0], p1: [0.4, 0] }),
    member({ key: "plate-bottom", category: "plate", p0: [0, 0], p1: [3, 0], z0_m: 0, z1_m: 0.038 })];
  buildMembers(group, studs, CENTER, "schematic", RESOLVED_NORDIC_PALETTE.light, "W1");
  const bucket = group.children.find((child) => child instanceof THREE.InstancedMesh);
  assert(bucket instanceof THREE.InstancedMesh, "Prismatic members share one InstancedMesh");
  assert(carriesMemberIdentity(bucket), "The bucket declares that it owns per-member identity");
  assert(resolveMemberPickUid(bucket, 0, null) === "W1::stud-000", "Instance 0 is the first stud");
  assert(resolveMemberPickUid(bucket, 2, null) === "W1::plate-bottom",
    "Instance 2 is the bottom plate — draw order is member order");
  assert(resolveMemberPickUid(bucket, 99, null) === null,
    "An instanceId past the bucket resolves to nothing rather than to a wrong stud");
  assert(resolveMemberPickUid(bucket, null, 4) === null,
    "An instanced bucket ignores faceIndex — a missing instanceId is not a pick");
}

// A raked bucket is one merged geometry. Members are laid out in member order, but NOT with a
// fixed triangle count each: a birdsmouthed rafter's profile has six points, so its solid is
// not a 12-triangle box. Picking reads a prefix-sum table rather than dividing by a constant.
function checkMergedBucketResolvesPerBox() {
  const group = new THREE.Group();
  const rafters = [
    member({ key: "rafter-000", category: "rafter", p0: [0, 0], p1: [4, 0], z0_m: 3, z1_m: 3.24,
      z0_end_m: 5, z1_end_m: 5.24, orient: null }),
    member({ key: "rafter-001", category: "rafter", p0: [0, 0.6], p1: [4, 0.6], z0_m: 3, z1_m: 3.24,
      z0_end_m: 5, z1_end_m: 5.24, orient: null }),
  ];
  buildMembers(group, rafters, CENTER, "schematic", RESOLVED_NORDIC_PALETTE.light, "RF1");
  const merged = group.children.find(
    (child) => child instanceof THREE.Mesh && carriesMemberIdentity(child)) as THREE.Mesh;
  assert(merged, "Raked members merge into one identity-carrying mesh");
  assert(resolveMemberPickUid(merged, null, 0) === "RF1::rafter-000",
    "The first triangle belongs to the first rafter");
  assert(resolveMemberPickUid(merged, null, TRIANGLES_PER_MEMBER_BOX - 1) === "RF1::rafter-000",
    "The last triangle of the first box still belongs to the first rafter");
  assert(resolveMemberPickUid(merged, null, TRIANGLES_PER_MEMBER_BOX) === "RF1::rafter-001",
    "The next box is the next rafter");
  assert(resolveMemberPickUid(merged, null, TRIANGLES_PER_MEMBER_BOX * 9) === null,
    "A faceIndex past the merge resolves to nothing");
}

// The prefix-sum table itself: a merge of members with *different* triangle counts. Dividing
// by 12 gets every one of these wrong after the first, silently, in the browser.
function checkPrefixSumHandlesMixedShapes() {
  const starts = [0, 12, 32, 44];
  assert(memberIndexForTriangle(starts, 0) === 0, "The first triangle is the first member");
  assert(memberIndexForTriangle(starts, 11) === 0, "The last of member 0 is still member 0");
  assert(memberIndexForTriangle(starts, 12) === 1, "The boundary starts the next member");
  assert(memberIndexForTriangle(starts, 31) === 1, "A 20-triangle member holds its whole span");
  assert(memberIndexForTriangle(starts, 32) === 2, "And hands over at its own end");
  assert(memberIndexForTriangle(starts, 44) === null, "One past the merge resolves to nothing");
  assert(memberIndexForTriangle(starts, -1) === null, "A negative faceIndex is not a pick");
}

// A birdsmouthed rafter draws its notch, and still resolves to itself when picked.
function checkSeatedRafterIsNotchedAndPickable() {
  const group = new THREE.Group();
  const seated = member({
    key: "rafter-000", category: "rafter", p0: [0, 0], p1: [3, 0],
    z0_m: 3, z1_m: 3.3, z0_end_m: 4, z1_end_m: 4.3, orient: null,
    seat: { plate_top_z_m: 3, heel: [0.3, 0], seat_run_m: 0.3 },
  });
  const plain = member({ key: "rafter-001", category: "rafter", p0: [0, 0.6], p1: [3, 0.6],
    z0_m: 3, z1_m: 3.3, z0_end_m: 4, z1_end_m: 4.3, orient: null });
  buildMembers(group, [seated, plain], CENTER, "schematic", RESOLVED_NORDIC_PALETTE.light, "RF1");
  const merged = group.children.find(
    (child) => child instanceof THREE.Mesh && carriesMemberIdentity(child)) as THREE.Mesh;
  assert(merged, "Seated and plain rafters merge together");
  const starts = merged.userData.triangleStarts as number[];
  assert(starts[1] !== TRIANGLES_PER_MEMBER_BOX,
    "A notched rafter contributes a different triangle count than a box");
  assert(resolveMemberPickUid(merged, null, starts[1] - 1) === "RF1::rafter-000",
    "The notched rafter's last triangle is still its own");
  assert(resolveMemberPickUid(merged, null, starts[1]) === "RF1::rafter-001",
    "And the plain rafter starts exactly where the table says");

  // The notch itself: a flat seat at the plate top, one seat run long.
  const verts = seatedProfileVertices(seated, CENTER);
  assert(verts && verts.length === 12, "A seated member is a six-point profile, twice");
  const onSeat = verts!.filter(([, y]) => Math.abs(y - 3) < 1e-9);
  assert(onSeat.length === 4, "Two profile corners sit on the plate, on each face");
}

// All three i-joist plies share one instance index per member, so clicking a flange and
// clicking the web select the same joist.
function checkIJoistPliesShareOneIdentity() {
  const group = new THREE.Group();
  const joists = [
    member({ key: "joist-000", category: "joist", shape: "i_joist", p0: [0, 0], p1: [4, 0],
      z0_m: 2.4, z1_m: 2.7, flange_width_m: 0.06, flange_thickness_m: 0.03,
      web_thickness_m: 0.01, orient: null }),
    member({ key: "joist-001", category: "joist", shape: "i_joist", p0: [0, 0.4], p1: [4, 0.4],
      z0_m: 2.4, z1_m: 2.7, flange_width_m: 0.06, flange_thickness_m: 0.03,
      web_thickness_m: 0.01, orient: null }),
  ];
  buildMembers(group, joists, CENTER, "schematic", RESOLVED_NORDIC_PALETTE.light, "FL1");
  const plies = group.children.filter((child) => child instanceof THREE.InstancedMesh);
  assert(plies.length === 3, "An i-joist bucket is three plies (top flange, bottom flange, web)");
  for (const ply of plies) {
    assert(resolveMemberPickUid(ply, 1, null) === "FL1::joist-001",
      "Every ply resolves instance 1 to the same joist");
  }
}

// A member skipped at build time (no plan run, so no raked box) must not shift the identities
// of the members after it — that is exactly the off-by-one an index-based scheme invites.
function checkSkippedMemberDoesNotShiftIdentities() {
  const group = new THREE.Group();
  const degenerate = member({ key: "rafter-bad", category: "rafter", p0: [2, 2], p1: [2, 2],
    z0_m: 3, z1_m: 3.24, z0_end_m: 5, z1_end_m: 5.24, orient: null });
  const good = member({ key: "rafter-good", category: "rafter", p0: [0, 0], p1: [4, 0],
    z0_m: 3, z1_m: 3.24, z0_end_m: 5, z1_end_m: 5.24, orient: null });
  buildMembers(group, [degenerate, good], CENTER, "schematic", RESOLVED_NORDIC_PALETTE.light, "RF1");
  const merged = group.children.find(
    (child) => child instanceof THREE.Mesh && carriesMemberIdentity(child)) as THREE.Mesh;
  assert(merged, "The drawable rafter still produces a merged mesh");
  assert(resolveMemberPickUid(merged, null, 0) === "RF1::rafter-good",
    "The first drawn box is the first member that actually drew, not the first in the list");
}

// The outline the panel draws over a picked member has to land on the member. Assert its
// bounds against the member's own extents for both a prism and a raked stick.
function checkHighlightOutlineMatchesTheMember() {
  const stud = member({ key: "stud-000", p0: [1, 2], p1: [1, 2], z0_m: 0.5, z1_m: 3 });
  const outline = buildMemberHighlight(stud, CENTER, 0xff0000);
  assert(outline, "A prismatic member gets an outline");
  outline!.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(outline!);
  assert(Math.abs(box.min.y - 0.5) < 1e-6 && Math.abs(box.max.y - 3) < 1e-6,
    "The stud outline spans exactly z0..z1");
  assert(Math.abs(box.getCenter(new THREE.Vector3()).x - 1) < 1e-6,
    "The stud outline is centred on the stud's plan position");

  const rafter = member({ key: "rafter-000", category: "rafter", p0: [0, 0], p1: [4, 0],
    z0_m: 3, z1_m: 3.24, z0_end_m: 5, z1_end_m: 5.24, orient: null });
  const raked = buildMemberHighlight(rafter, CENTER, 0xff0000);
  assert(raked, "A raked member gets an outline");
  raked!.updateMatrixWorld(true);
  const rakedBox = new THREE.Box3().setFromObject(raked!);
  assert(Math.abs(rakedBox.min.y - 3) < 1e-6 && Math.abs(rakedBox.max.y - 5.24) < 1e-6,
    "The rafter outline follows the rake, low end to high end");

  const degenerate = member({ key: "rafter-bad", category: "rafter", p0: [2, 2], p1: [2, 2],
    z0_end_m: 5, z1_end_m: 5.24, orient: null });
  assert(buildMemberHighlight(degenerate, CENTER, 0xff0000) === null,
    "A member with no drawable box gets no outline rather than a degenerate one");
}

// locateMember is what turns a pick back into something the inspector can render.
function checkLocateMemberAgainstTheModel() {
  const stud = member({ key: "stud-003" });
  const model = {
    walls: [{ uid: "W1", tag: "W-101", storey: "L1", members: [stud] }],
    roofs: [], floors: [], stairs: [],
  } as unknown as Model;
  const located = locateMember(model, "W1::stud-003");
  assert(located?.member === stud && located?.ownerKind === "wall" && located?.ownerTag === "W-101"
    && located?.storey === "L1", "A member uid resolves to its member and its owner");
  assert(locateMember(model, "W1::stud-999") === null,
    "A member key the rebuild dropped resolves to null, not to a neighbour");
  assert(locateMember(model, "W9::stud-003") === null, "An unknown owner resolves to null");
  assert(locateMember(model, "W1") === null, "A plain element uid is not a member");
}

export function runMemberPickingTests() {
  checkMemberUidScheme();
  checkInstancedBucketResolvesPerStud();
  checkMergedBucketResolvesPerBox();
  checkPrefixSumHandlesMixedShapes();
  checkSeatedRafterIsNotchedAndPickable();
  checkIJoistPliesShareOneIdentity();
  checkSkippedMemberDoesNotShiftIdentities();
  checkHighlightOutlineMatchesTheMember();
  checkLocateMemberAgainstTheModel();
}
