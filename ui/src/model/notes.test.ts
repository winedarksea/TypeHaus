import { KIND_LABEL, KIND_ORDER, groupNotes, matchesNote } from "./notes";
import type { NoteEntry } from "../engine/EngineClient";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function note(path: string, kind: NoteEntry["kind"], on_sheets: string[] = []): NoteEntry {
  return { path, title: path.replace(/^notes\//, "").replace(/\.md$/, ""), kind, on_sheets,
    chars: 100 };
}

// Deliberately shuffled: the engine lists notes in path order, and the tab's reading order
// is a different thing.
const NOTES: NoteEntry[] = [
  note("notes/superseded/old_bracing.md", "superseded"),
  note("notes/interior_selections.md", "design"),
  note("brief.md", "brief"),
  note("notes/catlin_truss_engineering.md", "calc"),
  note("notes/ridge_beam_detail.md", "detail", ["A-401"]),
  note("notes/shower_niche.md", "detail", ["A-402", "A-403"]),
];

export function runNoteGroupingTests() {
  const groups = groupNotes(NOTES);
  assert(
    groups.map((g) => g.kind).join(",") === "brief,detail,calc,design,superseded",
    `groups read in KIND_ORDER: ${groups.map((g) => g.kind)}`,
  );
  assert(groups[0].notes[0].path === "brief.md", "the brief leads");
  assert(groups[1].notes.length === 2, "both detail notes land together");
  assert(groups[1].label === KIND_LABEL.detail, "a group carries its kind's label");
  assert(groups.every((g) => g.note.length > 0), "every group says what it holds");
  assert(
    groups.reduce((n, g) => n + g.notes.length, 0) === NOTES.length,
    "grouping loses no notes",
  );

  // Within a group, the engine's order is preserved rather than re-sorted: it is path
  // order, which is the order the folder reads in.
  assert(groups[1].notes[0].path.endsWith("ridge_beam_detail.md"),
    "a group keeps the order the engine listed");

  assert(groupNotes([]).length === 0, "no notes means no groups, not five empty ones");
  const oneKind = groupNotes([note("brief.md", "brief")]);
  assert(oneKind.length === 1, "a kind with nothing in it is omitted");

  assert(KIND_ORDER.length === Object.keys(KIND_LABEL).length,
    "every kind the engine can emit has a label");

  const ridge = NOTES[4];
  assert(matchesNote(ridge, ""), "an empty filter matches everything");
  assert(matchesNote(ridge, "ridge"), "title matches");
  assert(matchesNote(ridge, "notes/ridge"), "path matches");
  assert(matchesNote(ridge, "a-401"), "the sheet a note prints on is searchable");
  assert(!matchesNote(ridge, "shower"), "an unrelated needle does not match");

  console.log("Note grouping tests passed.");
}
