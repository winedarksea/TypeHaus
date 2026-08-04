// Presentation for the engine's bill of materials — the *only* BOM implementation (→ TODO
// item 2). The browser used to compute its own in `model/bom.ts`: it billed footing beddings
// the engine did not, missed families the engine had, and nothing tested that the two agreed.
// That file is gone; this one only arranges what `takeoff/bom.py::bill_of_materials` returns.
//
// The payload is a dict of sections — mostly `list[dict]` row sets, plus a few scalar/dict
// summaries (service_load, lighting_load). Nothing here knows what a row *means*: columns are
// inferred from the keys the rows actually carry, so a section that grows a field shows it
// without a change on this side, and a section the engine adds cannot silently vanish from
// the view (unknown keys land in a trailing "Other" group).

import type { EngineBom } from "../engine/EngineClient";

export interface BomSectionGroup {
  readonly id: string;
  readonly title: string;
  // One line on what the group covers — the ReaderSection note.
  readonly note: string;
  // Section keys, in the order they should read within the group.
  readonly sections: readonly string[];
}

/**
 * The engine's sections, grouped and ordered for reading rather than alphabetically.
 *
 * Kept in step with `bill_of_materials`'s key set by two tests: `engineBom.test.ts` here, and
 * `packages/engine/tests/test_bom_sweep.py` on the engine side, which pins the section keys as
 * this view's contract.
 */
export const SECTION_GROUPS: readonly BomSectionGroup[] = [
  {
    id: "structure",
    note: "Sticks, sheets, solids and the steel that joins them.",
    title: "Structure",
    // `wall_structure` sits beside `structural_solids`, not with the envelope layers: a
    // concrete or masonry wall core is a pour, not a covering, and it is ordered by the yard.
    sections: ["framing", "framing_by_size", "structural_solids", "wall_structure",
      "sheet_goods", "construction_returns", "hardware", "footing_bedding"],
  },
  {
    id: "envelope",
    note: "The layers that separate inside from out, and the holes through them.",
    title: "Envelope & openings",
    sections: ["envelope_layers", "wood_surfaces", "glazing_panels", "glazing_trim",
      "edge_trim", "bug_screens", "openings", "floor_finishes", "stair_finish", "railings"],
  },
  {
    id: "mep",
    note: "Pipe, valves, insulation, duct, cast-in sleeves, radiant floor element and the storm run.",
    title: "Mechanical & plumbing",
    sections: ["pipe_runs", "plumbing_specialties", "install_parts", "pipe_insulation",
      "ducts", "sleeves", "floor_heat", "drainage"],
  },
  {
    id: "electrical",
    note: "Devices, the panel schedule and service load, raceway, conductors, PV and backup.",
    title: "Electrical",
    sections: ["electrical_devices", "panel_schedule", "service_load", "conduit",
      "conductors", "solar", "backup_power"],
  },
  {
    id: "lighting",
    note: "The luminaire schedule by mark, switch legs, LED runs and connected load.",
    title: "Lighting",
    sections: ["luminaire_schedule", "lighting_controls", "light_runs", "lighting_load"],
  },
  {
    id: "data",
    // Its own group rather than a tail on Electrical, for the reason the trades are split on
    // site: comms conductors may not share a raceway with power, so the pipe is a separate
    // order and the PoE load lands on the switch instead of on the panel schedule.
    note: "Low-voltage devices, the comms and spare raceways, and the PoE load on the switch.",
    title: "Data & low-voltage",
    sections: ["data_devices", "data_raceways", "poe_budget"],
  },
  {
    id: "placeables",
    note: "Casework, appliances and fixtures — everything placed rather than framed.",
    title: "Placeables",
    sections: ["placeables"],
  },
];

/** Section keys the groups above claim — everything else falls through to "Other". */
const GROUPED = new Set(SECTION_GROUPS.flatMap((group) => group.sections));

/** `length_ft` → "length (ft)"; `net_area_sqft` → "net area (sqft)". */
export function prettifyHeader(key: string): string {
  const words = key.split("_");
  const tail = words[words.length - 1];
  const unit = UNIT_SUFFIXES.has(tail) ? ` (${tail})` : "";
  const head = unit ? words.slice(0, -1) : words;
  return `${head.join(" ")}${unit}`;
}

// Trailing tokens that read as a unit rather than as part of the name. Anything else stays a
// plain word: guessing wrong here would mislabel a column, and a plain name is never wrong.
const UNIT_SUFFIXES = new Set([
  "ft", "in", "m", "m2", "m3", "sqft", "sf", "lf", "cf", "yd", "cy", "lb", "kg",
  "va", "amps", "watts", "btuh", "pct",
]);

export interface BomTable {
  readonly kind: "rows" | "pairs";
  readonly columns: readonly string[];
  readonly headers: readonly string[];
  readonly rows: readonly (readonly unknown[])[];
}

/**
 * One section's payload as a table.
 *
 * A `list[dict]` becomes a row table whose columns are the union of the rows' keys **in
 * first-seen order** — the engine authors row dicts in a deliberate order and preserving it is
 * what keeps the identifying column leftmost. A scalar or a plain dict (a summary such as
 * `service_load`) becomes a two-column key/value table instead. An empty list yields no rows.
 */
export function sectionRows(value: unknown): BomTable {
  if (Array.isArray(value)) {
    const columns: string[] = [];
    const seen = new Set<string>();
    for (const row of value) {
      if (!row || typeof row !== "object") continue;
      for (const key of Object.keys(row as Record<string, unknown>)) {
        if (seen.has(key)) continue;
        seen.add(key);
        columns.push(key);
      }
    }
    const rows = value.map((row) => columns.map((column) =>
      (row && typeof row === "object") ? (row as Record<string, unknown>)[column] : undefined));
    return { kind: "rows", columns, headers: columns.map(prettifyHeader), rows };
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    return {
      kind: "pairs",
      columns: ["key", "value"],
      headers: ["Field", "Value"],
      rows: entries.map(([key, entry]) => [prettifyHeader(key), entry]),
    };
  }
  // A bare scalar section (`lighting_load` is a number) still deserves a row rather than a
  // blank panel — the number *is* the section.
  return { kind: "pairs", columns: ["value"], headers: ["Value"], rows: [[value]] };
}

/** A cell as text. Lists (a finish's `rooms`) join; null/undefined read as an em dash. */
export function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.map(formatCell).join(", ");
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  // A nested record — `framing`'s stock buckets are `{length_ft, count}` — reads as its
  // fields, not as JSON. Raw `JSON.stringify` is how the stock column turned into a wall of
  // braces and quotes wide enough to push the board-foot column off the table.
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, entry]) => `${prettifyHeader(key)} ${formatCell(entry)}`)
      .join(" · ");
  }
  return String(value);
}

export interface BomSection {
  readonly key: string;
  readonly title: string;
  readonly table: BomTable;
}
export interface BomGroup {
  readonly id: string;
  readonly title: string;
  readonly note: string;
  readonly sections: readonly BomSection[];
}

/**
 * The whole payload, grouped and ordered.
 *
 * Sections absent from the payload are skipped; sections the payload has and `SECTION_GROUPS`
 * does not are collected into a trailing "Other" group. That fallback is the point: a new
 * engine section shows up unarranged rather than not at all.
 */
export function groupBom(bom: EngineBom): BomGroup[] {
  const groups: BomGroup[] = [];
  for (const group of SECTION_GROUPS) {
    const sections = group.sections
      .filter((key) => key in bom)
      .map((key) => ({ key, title: prettifyHeader(key), table: sectionRows(bom[key]) }));
    if (sections.length) groups.push({ ...group, sections });
  }
  const other = Object.keys(bom).filter((key) => !GROUPED.has(key));
  if (other.length) {
    groups.push({
      id: "other",
      title: "Other",
      note: "Sections the engine bills that this view has not been told where to put.",
      sections: other.map((key) => ({
        key, title: prettifyHeader(key), table: sectionRows(bom[key]),
      })),
    });
  }
  return groups;
}
