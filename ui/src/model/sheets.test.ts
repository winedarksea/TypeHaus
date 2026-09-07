import { findSheet, groupSheets, nextSheet, prevSheet, seriesOf } from "./sheets";
import type { SheetEntry } from "../engine/EngineClient";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

// A miniature permit set, deliberately NOT in NCS order: the point of grouping is that the
// manifest's composed order and the reading order are two different things.
const SHEETS: SheetEntry[] = [
  { number: "G-001", title: "Cover", page: 1 },
  { number: "A-101", title: "Level 1", page: 2 },
  { number: "A-102", title: "Level 2", page: 3 },
  { number: "S-101", title: "Foundation", page: 4 },
  { number: "E-101", title: "Power", page: 5 },
  { number: "P-101", title: "Plumbing", page: 6 },
  { number: "M-101", title: "HVAC", page: 7 },
];

export function runSheetGroupingTests() {
  assert(seriesOf("A-101") === "A", "the leading letter is the series");
  assert(seriesOf("g-002") === "G", "series matching is case-insensitive");
  assert(seriesOf("XY-1") === "?", "a number outside the NCS series falls to Other");
  assert(seriesOf("") === "?", "an empty number does not throw");

  const groups = groupSheets(SHEETS);
  assert(
    groups.map((g) => g.series).join(",") === "G,S,A,P,M,E",
    `groups read in NCS order, not composed or alphabetical order: ${groups.map((g) => g.series)}`,
  );
  assert(groups[0].label === "General", "a group carries its discipline's name");
  const arch = groups.find((g) => g.series === "A");
  assert(arch?.sheets.length === 2, "both architectural sheets land in one group");
  assert(arch!.sheets[0].number === "A-101", "within a group, page order");

  // An unrecognised number is shown, never dropped: a sheet missing from the list is worse
  // than one filed under Other.
  const withOdd = groupSheets([...SHEETS, { number: "Z-9", title: "Odd", page: 8 }]);
  const other = withOdd[withOdd.length - 1];
  assert(other.series === "?" && other.sheets[0].number === "Z-9",
    "an unknown series lands in a trailing Other group");
  assert(
    withOdd.reduce((n, g) => n + g.sheets.length, 0) === SHEETS.length + 1,
    "grouping loses no sheets",
  );

  assert(groupSheets([]).length === 0, "an empty set groups to nothing, not to empty groups");

  assert(findSheet(SHEETS, "S-101")?.title === "Foundation", "lookup is by exact number");
  assert(findSheet(SHEETS, "S-10") === null, "a sheet number is not a prefix");
  assert(findSheet(SHEETS, null) === null, "no selection resolves to no sheet");

  // Stepping is through the *set*, in page order — across series boundaries, the way you
  // page through the PDF.
  assert(nextSheet(SHEETS, "A-102")?.number === "S-101", "next crosses into the next series");
  assert(prevSheet(SHEETS, "A-101")?.number === "G-001", "prev walks back a page");
  assert(nextSheet(SHEETS, "M-101") === null, "next past the last sheet is null, not a wrap");
  assert(prevSheet(SHEETS, "G-001") === null, "prev before the cover is null, not a wrap");
  assert(nextSheet(SHEETS, null)?.number === "G-001", "with nothing selected, next is page 1");
  assert(prevSheet(SHEETS, null)?.number === "M-101", "with nothing selected, prev is the last");
  assert(nextSheet([], null) === null, "stepping an empty set does not throw");

  console.log("Sheet grouping tests passed.");
}
