// The room-floor builder: `Room.floor_finish` made visible.
//
// The finish resolved and exported since M1 and nothing drew it — buildFloor renders
// `floor.subfloor` and stops, so a house of carpet, oak, LVP and tile read as bare subfloor
// everywhere. What these tests pin is the part that is easy to get silently wrong: the finish
// string is a *material tag*, so its colour has to come off the catalog rather than off a
// second table that can drift; and four flat fills of similar value are hard to tell apart
// under one light, so the surface has to differ too.
import * as THREE from "three";
import type { Floor, Member, Room, Vec2 } from "../../model/types";
import {
  buildRoomFloor, ROOM_FINISH_THICKNESS_M, storeyFloorTopM,
} from "./structure";
import {
  DEFAULT_FLOOR_SURFACE, FLOOR_FINISH_SURFACE, floorSurface, materialColor,
  RESOLVED_NORDIC_PALETTE, type MaterialAppearance,
} from "../../nordic/palette";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const PALETTE = RESOLVED_NORDIC_PALETTE.light;

// The floor-finish slice of library/materials.py, as the catalog ships it.
const MATERIALS: MaterialAppearance[] = [
  { tag: "oak", color: "#c69c6d" },
  { tag: "lvp", color: "#a08a72" },
  { tag: "carpet", color: "#9c8f80" },
  { tag: "tile", color: "#dfe3e5" },
  // Sealed concrete is a *coating*: a sealer on the slab, no thickness of its own.
  { tag: "sealed-concrete", color: "#b3b1ad", coating: true },
  { tag: "rubber", color: "#54585c" },
];

// The coverings — everything the builder is expected to draw a plane for.
const COVERINGS = MATERIALS.filter((material) => !material.coating);

function room(finish: string | null, storey = "second"): Room {
  return {
    uid: `RM-${finish ?? "none"}`, tag: `RM-${finish ?? "none"}`, storey,
    occupancy: "living", provenance: null, conditioned: true, area_m2: 16,
    clear_face: [[0, 0], [4, 0], [4, 4], [0, 4]] as Vec2[], floor_finish: finish,
  };
}

function registry() {
  return { picks: [] as THREE.Mesh[], byUid: new Map<string, THREE.Material[]>() };
}

function build(r: Room, top = 3, openings: Vec2[][] = []) {
  const group = new THREE.Group();
  const reg = registry();
  buildRoomFloor(group, r, top, openings, [0, 0], "nordic", PALETTE, MATERIALS,
    reg.picks, reg.byUid);
  return { group, reg };
}

export function runRoomFloorTests() {
  // --- 1. the finish is actually drawn, and only when there is one ------------------------

  const oak = build(room("oak"));
  assert(oak.group.children.length === 1, "A finished room builds exactly one slab");
  assert(oak.reg.picks.length === 1 && oak.reg.picks[0].userData.uid === "RM-oak",
    "The finish slab is pickable and resolves to its room, not to the floor under it");
  assert(oak.reg.picks[0].userData.selectionKind === "room",
    "A click on the finish selects the room");
  assert((oak.reg.byUid.get("RM-oak") ?? []).length === 1,
    "The slab's material joins the room's highlight set");

  assert(build(room(null)).group.children.length === 0,
    "A room with no authored finish draws bare deck — no slab, not a grey one");

  // A coating is a sealer, not a covering. The slab under it already carries the colour, so
  // a plane here would read as a second floor — which is exactly what the garage showed.
  // It still bills: takeoff/finishes.py keeps the sealer row.
  assert(build(room("sealed-concrete")).group.children.length === 0,
    "A coating finish draws no plane — the sealed slab is one floor, not two");
  assert(build(room("sealed-concrete")).reg.picks.length === 0,
    "…and nothing invisible is left behind for a click to land on");

  // --- 2. colour comes off the catalog material, not a second table -----------------------

  const colors = new Map<string, string>();
  for (const { tag, color } of COVERINGS) {
    const built = build(room(tag));
    const material = (built.group.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    assert("#" + material.color.getHexString() === color,
      `A ${tag} floor takes the material's authored colour ${color}`);
    assert(materialColor(tag, PALETTE, MATERIALS) === color,
      `materialColor resolves ${tag} through the catalog, which is what keeps the .glb in step`);
    colors.set(tag, color);
  }
  assert(new Set(colors.values()).size === colors.size,
    "The finishes are distinct colours — otherwise the viewer separates nothing");
  // A coating draws nothing here, but it still has to resolve: the .glb's room prism and the
  // 2D plan both colour by it.
  assert(materialColor("sealed-concrete", PALETTE, MATERIALS) === "#b3b1ad",
    "A coating still resolves through the catalog for the surfaces that do colour by it");

  // A finish with no catalog entry still renders, in the family fallback, rather than
  // vanishing: a typo has to look wrong, not look like an unfinished room.
  assert(build(room("no-such-finish")).group.children.length === 1,
    "An unrecognised finish still builds a slab, so a typo is visible rather than silent");

  // --- 3. surface, because colour alone does not separate them --------------------------

  const coatings = new Set(MATERIALS.filter((m) => m.coating).map((m) => m.tag));
  const roughness = new Set<number>();
  for (const tag of Object.keys(FLOOR_FINISH_SURFACE)) {
    roughness.add(FLOOR_FINISH_SURFACE[tag].roughness);
    // A coating builds no mesh of its own; its sheen belongs to the slab that carries it.
    if (coatings.has(tag)) continue;
    const built = build(room(tag));
    const material = (built.group.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    assert(material.roughness === FLOOR_FINISH_SURFACE[tag].roughness,
      `A ${tag} floor takes its own roughness`);
  }
  assert(roughness.size >= 5,
    "Carpet, oak, LVP, tile and sealed concrete catch light differently, not just in hue");
  assert(floorSurface("carpet").roughness > floorSurface("tile").roughness,
    "Carpet scatters and glazed tile does not — the ordering is the point");
  assert(floorSurface("no-such-finish") === DEFAULT_FLOOR_SURFACE,
    "An unlisted finish gets a plausible matte default rather than undefined");
  assert(floorSurface(null) === DEFAULT_FLOOR_SURFACE, "A null finish never throws");

  // --- 4. geometry: over the deck, and not capping the stair well ------------------------

  // Box3.setFromObject measures Float32 vertex data, so ~1e-7 is the available precision.
  const box = new THREE.Box3().setFromObject(build(room("oak"), 3).group);
  assert(Math.abs(box.min.y - 3) < 1e-6, "The finish sits on the deck it was given, not on 0");
  assert(Math.abs((box.max.y - box.min.y) - ROOM_FINISH_THICKNESS_M) < 1e-6,
    "It draws at the same thickness the .glb extrudes its room prism");

  // A deck opening is cut out of the finish too. Without this the finish caps the stair well
  // the subfloor correctly leaves open.
  const hole: Vec2[] = [[1, 1], [3, 1], [3, 3], [1, 3]];
  const solid = build(room("oak")).group.children[0] as THREE.Mesh;
  const holed = build(room("oak"), 3, [hole]).group.children[0] as THREE.Mesh;
  const count = (mesh: THREE.Mesh) => mesh.geometry.getAttribute("position").count;
  assert(count(holed) > count(solid),
    "A deck opening is cut out of the finish, not drawn over");

  // --- 5. the deck elevation the finish lands on ----------------------------------------

  const member = (z1: number): Member => ({
    key: "J-1", category: "joist", profile: "2x10", shape: "rect", width_m: 0.038,
    depth_m: 0.235, p0: [0, 0], p1: [4, 0], z0_m: z1 - 0.235, z1_m: z1, length_m: 4,
    z0_end_m: null, z1_end_m: null, orient: null, connection: null, material: null,
    trade: null, plies: 1, flange_width_m: null, flange_thickness_m: null,
    web_thickness_m: null,
  } as unknown as Member);
  const floor = (storey: string, z1: number): Floor => ({
    uid: `FL-${storey}`, tag: `FL-${storey}`, storey, direction: "x", provenance: null,
    openings: [], subfloor: { material: "osb", thickness_m: 0.019 }, members: [member(z1)],
  });
  assert(Math.abs(storeyFloorTopM([floor("second", 3.1)], "second", 3) - 3.119) < 1e-9,
    "A framed storey's finish lands on the subfloor's top face, not on the storey datum");
  // A slab-on-grade storey has no Floor at all — the storey elevation is the answer, and
  // falling back to 0 instead would drop every upper-storey finish onto the ground plane.
  assert(storeyFloorTopM([floor("second", 3.1)], "garage", 1.5) === 1.5,
    "A storey with no framed floor falls back to its own elevation");

  console.log("Room floor finish tests passed.");
}
