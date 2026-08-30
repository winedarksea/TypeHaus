import { findingsForElements, junctionDiagnosticMarkers, openEndMarker } from "./planWarnings";
import { humanizeOccupancy, spaceLabel, spaceLabelLineBudget } from "./spaceLabels";
import type { Model, Wall } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function wall(tag: string, uid: string): Wall {
  return {
    uid, tag, storey: "basement", assembly: "CATLIN_CONC_8_INT", provenance: null,
    axis: [[3.3528, 5], [3.3528, 7.62]], z0_m: 0, z1_m: 3, top_z0_m: null, top_z1_m: null, plate_base_z_m: null, plate_top_z_m: null, layout_axis: null,
    is_foundation: true, layers: [], members: [],
  };
}

function model(overrides: Partial<Model>): Model {
  return {
    revision: "r", units: "imperial", projectNorth: 0, findings: [],
    project: { name: "Catlin", uuid: "u" }, storeys: [], walls: [], openings: [], rooms: [],
    conditions: [], stack_edges: [], ...overrides,
  };
}

export function runPlanWarningTests() {
  const strWall = wall("W-B-STR", "WB1");
  const base = model({
    walls: [strWall],
    nodes: [{ tag: "N-B-STR", storey: "basement", x_m: 3.3528, y_m: 7.62, open_end: true,
      provenance: null }],
  });

  // The catlin case from the TODO: the pulsing dot at the south end of W-B-STR. The plan
  // *declares* that end open, so the marker must read as advisory, name itself, and say so.
  const declared = openEndMarker(base, "basement", [3.3528, 7.62], [strWall], 0.1);
  assert(declared.id === "N-B-STR", "An open-end marker identifies itself by its node tag");
  assert(declared.tier === "info", "A declared open end is advisory, not a warning");
  assert(declared.message.includes("open_end"), "The message names the authored field to look for");
  assert(declared.elementTags.includes("W-B-STR"), "The marker lists the wall it belongs to");

  const undeclaredModel = model({
    walls: [strWall],
    nodes: [{ tag: "N-B-STR", storey: "basement", x_m: 3.3528, y_m: 7.62, open_end: false,
      provenance: null }],
  });
  const undeclared = openEndMarker(undeclaredModel, "basement", [3.3528, 7.62], [strWall], 0.1);
  assert(undeclared.tier === "warn", "An undeclared free end stays a warning");

  // Findings are addressed by uid *or* authored tag, so both must resolve onto the marker.
  const withFindings = model({
    walls: [strWall],
    findings: [
      { severity: "warn", message: "by uid", element: "WB1", result: "fail" },
      { severity: "info", message: "by tag", elements: ["W-B-STR"], result: "unknown" },
      { severity: "info", message: "passing", element: "WB1", result: "pass" },
      { severity: "warn", message: "elsewhere", element: "OTHER", result: "fail" },
    ],
  });
  const related = findingsForElements(withFindings, ["W-B-STR"], ["WB1"]);
  assert(related.length === 2, "Findings resolve by uid and by authored tag, passing ones excluded");

  const diagnostic = junctionDiagnosticMarkers(model({
    walls: [strWall],
    junctions: [
      { node: "N-1", storey: "basement", point: [1, 1], kind: "t", incidents: [], through_walls: [],
        branch_walls: [], framing_owner: null, supported: false, diagnostic: "mixed assembly" },
      { node: "N-2", storey: "basement", point: [2, 2], kind: "l", incidents: [], through_walls: [],
        branch_walls: [], framing_owner: null, supported: true, diagnostic: null },
      { node: "N-3", storey: "main", point: [3, 3], kind: "x", incidents: [], through_walls: [],
        branch_walls: [], framing_owner: null, supported: true, diagnostic: "other storey" },
    ],
  }), "basement");
  assert(diagnostic.length === 1 && diagnostic[0].id === "N-1",
    "Only annotated junctions on the active storey become markers");
  assert(diagnostic[0].tier === "error", "An unsupported junction fallback is an error");
  assert(diagnostic[0].message === "mixed assembly", "The resolver's own diagnostic is the message");
}

export function runSpaceLabelTests() {
  assert(humanizeOccupancy("half_bath") === "Half Bath", "Occupancy enums read as titles");
  const label = spaceLabel({ tag: "RM-B-FURNACE", occupancy: "mechanical", area_m2: 30.100584 });
  assert(label.name === "Mechanical" && label.id === "RM-B-FURNACE" && label.area === "324 SF",
    "A space label carries its name, its addressable id, and its area");
  assert(spaceLabel({ tag: "RM-X", occupancy: "", area_m2: 1 }).name === "RM-X",
    "With no occupancy to name it, the id is the name");

  assert(spaceLabelLineBudget(200, 100) === 3, "A large space holds name, id and area");
  assert(spaceLabelLineBudget(200, 20) === 1, "A short space keeps the id alone");
  assert(spaceLabelLineBudget(30, 200) === 0, "A space too narrow to read draws no label at all");
}
