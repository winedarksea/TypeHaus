// Solid-wood pieces — stools, oak treads, built-in shelves — drawn as one board each.
import * as THREE from "three";
import type { CanvasObject, Member, ModelPart, Vec2, WindowStool } from "../model/types";
import { RESOLVED_NORDIC_PALETTE, type MaterialAppearance } from "../nordic/palette";
import { buildBoardMembers, buildWindowStool } from "./builders/millwork";
import { buildCanvasObjectParts } from "./builders/site";
import { plankStyleOrNull, plankTileSizeM, WOOD_PLANK_STYLES } from "./plankMaterial";
import { boardBoxGeometry } from "./woodPiece";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const PALETTE = RESOLVED_NORDIC_PALETTE.light;
const OAK = "#c9b08c";
const MATERIALS: MaterialAppearance[] = [
  { tag: "house-tread", color: OAK, finish: "oak-board" },
  { tag: "house-shelf", color: OAK, finish: "oak-board" },
];
const BOARD = WOOD_PLANK_STYLES["oak-board"];

function uvRange(geometry: THREE.BufferGeometry) {
  const uv = geometry.getAttribute("uv");
  const us = Array.from({ length: uv.count }, (_, i) => uv.getX(i));
  const vs = Array.from({ length: uv.count }, (_, i) => uv.getY(i));
  return { u: [Math.min(...us), Math.max(...us)], v: [Math.min(...vs), Math.max(...vs)] };
}

// One board of the tile: inside a single lane across, and never past the tile's end along.
function onOneBoard(geometry: THREE.BufferGeometry, label: string) {
  const { u, v } = uvRange(geometry);
  const lane = 1 / BOARD.boardsPerTile;
  assert(Math.abs(u[0] / lane - Math.round(u[0] / lane)) < 1e-6, `${label}: starts on a lane edge`);
  assert(v[0] >= -1e-9 && v[1] <= 1 + 1e-9, `${label}: stays inside one tile along the grain`);
}

export function runWoodPieceTests() {
  assert(plankStyleOrNull("house-tread", "oak-board")?.key === "oak-board",
    "a declared oak-board recipe boards a house-local millwork material");
  assert(BOARD.jointFraction === 0 && BOARD.lengths.kind === "continuous",
    "a solid piece draws no joints and no end joints");

  // --- a box: grain along its longest side ---------------------------------------------
  const [tileU, tileV] = plankTileSizeM(BOARD);
  const shelf = boardBoxGeometry(new THREE.Matrix4().makeScale(0.8, 0.038, 0.3), BOARD, 7);
  const { u, v } = uvRange(shelf);
  assert(Math.abs((v[1] - v[0]) * tileV - 0.8) < 1e-6,
    "a shelf's grain runs its 0.8 m length");
  assert(Math.abs((u[1] - u[0]) * tileU - 0.3) < 1e-6, "…and across its 0.3 m depth");
  onOneBoard(shelf, "shelf");
  const again = boardBoxGeometry(new THREE.Matrix4().makeScale(0.8, 0.038, 0.3), BOARD, 7);
  assert(JSON.stringify(uvRange(again)) === JSON.stringify(uvRange(shelf)),
    "a piece's board is deterministic");

  // --- stair treads leave the instanced bucket; framing stays in it ---------------------
  const member = (key: string, category: string, material: string | null): Member => ({
    key, category, profile: "deck 11x1.5", shape: "rect", width_m: 0.279, depth_m: 0.038,
    p0: [0, 0], p1: [1, 0], z0_m: 0, z1_m: 0.038, length_m: 1, z0_end_m: null,
    z1_end_m: null, orient: null, connection: null, material, trade: null, plies: 1,
    flange_width_m: null, flange_thickness_m: null, web_thickness_m: null,
  } as unknown as Member);
  const group = new THREE.Group();
  const rest = buildBoardMembers(group, [
    member("tread-001", "tread", "house-tread"), member("tread-002", "tread", "house-tread"),
    member("stringer-L", "stringer", null),
  ], [0, 0], "nordic", PALETTE, MATERIALS, "ST-1");
  assert(rest.length === 1 && rest[0].key === "stringer-L",
    "only the board members are drawn here; the stringer goes to the member buckets");
  assert(group.children.length === 2, "one textured mesh per oak tread");
  const [t1, t2] = group.children as THREE.Mesh[];
  assert(t1.userData.memberKey === "tread-001", "a tread mesh carries its member key");
  assert("#" + (t1.material as THREE.MeshStandardMaterial).color.getHexString() === OAK,
    "a tread takes its material's authored colour");
  onOneBoard(t1.geometry, "tread");
  assert(JSON.stringify(uvRange(t1.geometry)) !== JSON.stringify(uvRange(t2.geometry)),
    "two identical treads are two boards, not one figure twice");

  // A winder's grain follows its physical nosing even when another edge is longer.
  const winderGroup = new THREE.Group();
  const winder = { ...member("winder-001", "winder", "house-tread"),
    plan_outline: [[0, 0], [1, 0], [2, 3], [0, 2]],
    nosing_line: [[0, 0], [1, 0]],
  } as Member;
  const plywood = member("stair-subdeck-001", "stair_subdeck", "plywood-subfloor");
  const framing = buildBoardMembers(winderGroup, [winder, plywood], [0, 0], "nordic",
    PALETTE, MATERIALS, "ST-WINDER");
  assert(framing.length === 1 && framing[0].category === "stair_subdeck",
    "structural plywood stays in framing and receives no hardwood board texture");
  const winderMesh = winderGroup.children[0] as THREE.Mesh;
  const positions = winderMesh.geometry.getAttribute("position");
  const uv = winderMesh.geometry.getAttribute("uv");
  const noseIndices = Array.from({ length: positions.count }, (_, i) => i)
    .filter(i => Math.abs(positions.getZ(i)) < 1e-7);
  assert(noseIndices.length >= 2, "the physical nosing is present in the viewer mesh");
  const across = noseIndices.map(i => uv.getX(i));
  assert(Math.max(...across) - Math.min(...across) < 1e-6,
    "grain UV runs along the serialized nosing rather than the longest polygon edge");

  // --- a built-in's wood part is textured; its other parts stay flat -------------------
  const item = { uid: "FURN-1", position_m: [0, 0] as Vec2, rotation: 0 } as CanvasObject;
  const parts: ModelPart[] = [
    { center: [0, 0, 0.5], size: [0.8, 0.3, 0.038], color: OAK, material_ref: "house-shelf" },
    { center: [0, 0.14, 1], size: [0.8, 0.02, 2], color: "#735233" },
  ];
  const furniture = buildCanvasObjectParts(new THREE.Group(), item, parts, [0, 0], "nordic", 0,
    [], new Map(), MATERIALS) as THREE.Group;
  const [shelfMesh, backMesh] = furniture.children as THREE.Mesh[];
  onOneBoard(shelfMesh.geometry, "built-in shelf");
  assert(Math.abs(new THREE.Box3().setFromObject(shelfMesh).getCenter(new THREE.Vector3()).y
    - 0.5) < 1e-6, "a board part lands where its centre says");
  assert(backMesh.position.y === 1 && shelfMesh.material !== backMesh.material,
    "the back is a plain box in its own colour");

  // --- a stool's grain runs along the wall ----------------------------------------------
  const stool: WindowStool = {
    uid: "STOOL-1", tag: "STOOL-1", window_ref: "W-1", opening_uid: "OP-1", storey: "main",
    material_ref: "house-tread", profile: "eased",
    outline: [[0, 0], [1.2, 0], [1.2, 0.3], [0, 0.3]] as Vec2[], z0_m: 0.9, z1_m: 0.93,
  };
  const stools = new THREE.Group();
  buildWindowStool(stools, stool, [0, 0], "nordic", PALETTE, MATERIALS, [], new Map());
  const stoolMesh = stools.children[0] as THREE.Mesh;
  assert(Math.abs((uvRange(stoolMesh.geometry).v[1] - uvRange(stoolMesh.geometry).v[0]) * tileV
    - 1.2) < 1e-4, "a stool's grain runs its 1.2 m length along the wall");
  onOneBoard(stoolMesh.geometry, "stool");

  console.log("Wood piece tests passed.");
}
