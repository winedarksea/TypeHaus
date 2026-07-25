import {
  formatPerms, INCHES_PER_METER, vaporPermeanceAt, vaporReadings, vaporRetarderClass,
} from "./vapor";
import type { MaterialSpec } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function material(overrides: Partial<MaterialSpec>): MaterialSpec {
  return { tag: "m", name: "M", r_per_inch: null, perm_rating: null, density: null, ...overrides };
}

export function runVaporTests() {
  // Mirrors Material.vapor_permeance_at. Whole-sheet perms win outright: dividing a published
  // ASTM E96 sheet rating by a nominal thickness would invent a number nobody measured.
  assert(vaporPermeanceAt(material({ vapor_permeance_perms: 12, perm_rating: 50 }), 0.5) === 12,
    "An authored whole-sheet permeance takes precedence over perm-inch");
  assert(vaporPermeanceAt(material({ perm_rating: 5 }), 2) === 2.5,
    "Perm-inch is divided by the layer's own thickness");
  assert(vaporPermeanceAt(material({ vapor_permeance_perms: 0 }), 4) === 0,
    "0 perms is a sourced vapour barrier, not missing data");
  assert(vaporPermeanceAt(material({}), 2) === null,
    "A material authoring neither field is UNKNOWN, never a substituted default");
  assert(vaporPermeanceAt(material({ perm_rating: 5 }), 0) === null,
    "A zero thickness cannot resolve a permeability");
  assert(vaporPermeanceAt(undefined, 1) === null, "A layer naming no catalog material is UNKNOWN");

  // IRC R702.7 / ASHRAE 160 class boundaries are inclusive at the top of each band.
  assert(vaporRetarderClass(0.1) === "I" && vaporRetarderClass(0.05) === "I", "Class I ≤ 0.1 perm");
  assert(vaporRetarderClass(1) === "II" && vaporRetarderClass(0.5) === "II", "Class II ≤ 1 perm");
  assert(vaporRetarderClass(10) === "III" && vaporRetarderClass(5) === "III", "Class III ≤ 10 perms");
  assert(vaporRetarderClass(11) === "permeable", "Above 10 perms is permeable");
  assert(vaporRetarderClass(null) === "unknown", "No permeance has no class");

  // A half-inch sheet of a 1.0 perm-inch material is 2 perms.
  const halfInchM = 0.5 / INCHES_PER_METER;
  const readings = vaporReadings(
    [
      { name: "wrb", material: "housewrap", thickness_m: 0.0005 },
      { name: "poly", material: "polyethylene", thickness_m: 0.00015 },
      { name: "sheath", material: "plywood", thickness_m: halfInchM },
      { name: "mystery", material: "unpriced", thickness_m: 0.02 },
      // Repeated across dozens of walls — the lens describes the assembly, not instances.
      { name: "wrb", material: "housewrap", thickness_m: 0.0005 },
    ],
    [
      material({ tag: "housewrap", vapor_permeance_perms: 58, source: "ASTM E96 datasheet" }),
      material({ tag: "polyethylene", vapor_permeance_perms: 0.03 }),
      material({ tag: "plywood", perm_rating: 1 }),
    ],
  );
  assert(readings.length === 4, "Readings are deduped per distinct material × layer");
  assert(readings[0].material === "polyethylene" && readings[0].retarderClass === "I",
    "Tightest layer first — the vapour retarder is what the reviewer is looking for");
  assert(Math.abs((readings[1].perms ?? 0) - 2) < 1e-9 && readings[1].retarderClass === "III",
    "A 1/2\" sheet of a 1.0 perm-inch material resolves to 2 perms (Class III)");
  assert(readings[2].material === "housewrap" && readings[2].source === "ASTM E96 datasheet",
    "The material's provenance rides along with its number");
  assert(readings[3].material === "unpriced" && readings[3].perms === null,
    "An unauthored material sorts last and stays UNKNOWN");

  assert(formatPerms(null) === "—", "No permeance renders as a dash, never as zero");
  assert(formatPerms(0).includes("barrier"), "Zero perms is labelled a barrier");
  assert(formatPerms(0.03) === "0.030 perms", "Tight permeances keep their precision");
}
