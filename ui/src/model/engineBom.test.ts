// The engine BOM's presentation layer. What is worth pinning here is not formatting but the
// two ways this view could silently lie: a column that exists in the payload and never reaches
// a header, and a section the engine bills that no group claims and that therefore disappears.
// Both were live failure modes of the browser-side BOM this replaces (TODO item 2).

import {
  formatCell, groupBom, prettifyHeader, SECTION_GROUPS, sectionRows,
} from "./engineBom";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// A payload shaped like `bill_of_materials`: row sections, a dict summary, a bare scalar.
const FIXTURE = {
  framing: [
    { size: "2x6", pieces: 412, length_ft: 3_296, board_feet: 3_296 },
    { size: "2x10", pieces: 64, length_ft: 768, board_feet: 1_067 },
  ],
  floor_finishes: [
    { finish: "oak", material: "White oak", known: true, coating: false,
      net_area_sqft: 812.4, rooms: ["RM-M-LIVING", "RM-M-DINING"] },
    // A second row with a key the first lacks: the union has to reach the header row, or the
    // companion's `under` column vanishes from a table that visibly has the data.
    { finish: "carpet-pad", material: "Carpet pad", known: true, coating: false,
      net_area_sqft: 300, rooms: ["RM-S-BED1"], under: "carpet" },
  ],
  service_load: { calculated_amps: 223.7, service_amps: 200, method: "NEC 220.82" },
  lighting_load: 1_840,
  placeables: [],
};

export function runEngineBomTests() {
  // --- columns are inferred from the rows, in first-seen order ---------------------------

  const framing = sectionRows(FIXTURE.framing);
  assert(framing.kind === "rows", "A list section is a row table");
  assert(framing.columns.join(",") === "size,pieces,length_ft,board_feet",
    "Columns keep the engine's own key order — the identifying column stays leftmost");
  assert(framing.rows.length === 2 && framing.rows[0][0] === "2x6",
    "Every row is projected onto the column order");

  const finishes = sectionRows(FIXTURE.floor_finishes);
  assert(finishes.columns.includes("under"),
    "A key only the second row carries still becomes a column — the union, not the first row");
  assert(finishes.rows[0][finishes.columns.indexOf("under")] === undefined,
    "…and the row that lacks it reads as missing rather than shifting its other cells");

  // --- summaries and scalars still render ------------------------------------------------

  const load = sectionRows(FIXTURE.service_load);
  assert(load.kind === "pairs" && load.rows.length === 3,
    "A dict summary becomes a key/value table, not an empty panel");
  assert(load.rows[0][0] === "calculated (amps)",
    "Summary keys are prettified the same way headers are");
  const scalar = sectionRows(FIXTURE.lighting_load);
  assert(scalar.kind === "pairs" && scalar.rows[0][0] === 1_840,
    "A bare scalar section shows its number");
  assert(sectionRows([]).rows.length === 0, "An empty section yields no rows, and no columns");

  // --- headers ---------------------------------------------------------------------------

  assert(prettifyHeader("length_ft") === "length (ft)", "A trailing unit token reads as a unit");
  assert(prettifyHeader("net_area_sqft") === "net area (sqft)", "…including multi-word names");
  assert(prettifyHeader("board_feet") === "board feet",
    "A trailing word that is not a unit token stays part of the name");
  assert(prettifyHeader("finish") === "finish", "A single-word key is left alone");

  // --- grouping: nothing the engine bills may vanish --------------------------------------

  const groups = groupBom(FIXTURE);
  const shown = groups.flatMap((group) => group.sections.map((section) => section.key));
  assert(shown.length === Object.keys(FIXTURE).length,
    "Every section in the payload reaches the view exactly once");
  assert(new Set(shown).size === shown.length, "…and no section is rendered twice");
  assert(groups[0].id === "structure" && shown[0] === "framing",
    "Groups render in the authored reading order, not the payload's key order");

  // The fallback is the guarantee: a section this file has never heard of still shows up.
  const withNovel = groupBom({ ...FIXTURE, brand_new_section: [{ thing: 1 }] });
  const other = withNovel.find((group) => group.id === "other");
  assert(other && other.sections[0].key === "brand_new_section",
    "A section no group claims lands in Other rather than disappearing");

  // A group whose sections are all absent from the payload draws no empty heading.
  assert(!groups.some((group) => group.id === "lighting" && group.sections.length === 0),
    "An empty group is omitted, not rendered blank");
  assert(SECTION_GROUPS.every((group) => group.note.length > 0),
    "Every group explains what it covers");
  // No section key may be claimed by two groups — that is how a row gets billed twice on screen.
  const claimed = SECTION_GROUPS.flatMap((group) => group.sections);
  assert(new Set(claimed).size === claimed.length,
    "No section key appears in two groups");

  // --- cells ------------------------------------------------------------------------------

  assert(formatCell(null) === "—" && formatCell(undefined) === "—",
    "A missing cell reads as a dash, never as empty or as 'undefined'");
  assert(formatCell(["RM-A", "RM-B"]) === "RM-A, RM-B", "A list cell joins");
  assert(formatCell(true) === "yes" && formatCell(false) === "no", "Booleans read as words");
  assert(formatCell(3.14159).startsWith("3.14"), "A float is trimmed, not printed raw");
  // Framing's stock buckets are nested records. Rendering them as JSON is what made the
  // stock column wide enough to push board feet off the table.
  assert(formatCell({ length_ft: 10, count: 2 }) === "length (ft) 10 · count 2",
    "A nested record reads as its fields, not as JSON");
  assert(formatCell([{ length_ft: 8, count: 2 }, { length_ft: 12, count: 4 }])
    === "length (ft) 8 · count 2, length (ft) 12 · count 4",
    "…and a list of them joins without a brace in sight");

  console.log("Engine BOM presentation tests passed.");
}
