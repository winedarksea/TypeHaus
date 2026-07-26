import { uidByTag } from "./tagIndex";
import type { Model } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// Only the fields uidByTag reads; the readers that use it never touch the rest.
function model(): Model {
  return {
    revision: "r1",
    units: "imperial",
    projectNorth: 0,
    findings: [],
    project: { name: "test", uuid: "u" },
    storeys: [],
    walls: [{ tag: "W-1", uid: "wall-uid" }],
    openings: [{ tag: "O-1", uid: "opening-uid" }],
    rooms: [{ tag: "RM-1", uid: "room-uid" }],
    canvas_objects: [
      { tag: "ED-G-EV-1450", uid: "device-uid" },
      { tag: "EQ-B-WH", uid: "equipment-uid" },
    ],
    solar_panels: [{ tag: "SP-A-PV-W1", uid: "panel-uid" }],
    conditions: [],
    stack_edges: [],
  } as unknown as Model;
}

export function runTagIndexTests() {
  const index = uidByTag(model());

  assert(index.get("W-1") === "wall-uid", "Walls index by tag, as the assembly reader relies on");
  assert(index.get("RM-1") === "room-uid", "Rooms index by tag");

  // The circuits reader's panel schedule names devices by tag; without these two families
  // every device chip on the page would render permanently disabled.
  assert(index.get("ED-G-EV-1450") === "device-uid",
    "Electrical devices resolve — the panel schedule's device tags zoom through this");
  assert(index.get("EQ-B-WH") === "equipment-uid", "Equipment on a circuit resolves too");
  assert(index.get("SP-A-PV-W1") === "panel-uid", "PV modules resolve for the array section");

  assert(index.get("NOPE") === undefined, "An unknown tag resolves to nothing, not a stale uid");

  // A model missing the optional families must not throw — older model.json carries neither.
  const sparse = { walls: [], openings: [], rooms: [] } as unknown as Model;
  assert(uidByTag(sparse).size === 0, "Absent optional families degrade to an empty index");

  // First writer wins, so a later family can never shadow an authored element's uid.
  const collided = {
    walls: [{ tag: "X", uid: "wall" }], openings: [], rooms: [],
    canvas_objects: [{ tag: "X", uid: "device" }],
  } as unknown as Model;
  assert(uidByTag(collided).get("X") === "wall", "The first family to claim a tag keeps it");
}
