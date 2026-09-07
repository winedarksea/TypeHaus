// Arrangement for the house's markdown notes: what the kinds are called, what order they
// read in, and how a flat list becomes the Notes tab's grouped index. DOM-free, like
// model/sheets.ts beside it.
//
// The kinds themselves are the engine's (emit/notes_index.py::_kind_of) and are derived from
// evidence — a note a sheet prints is a detail note, a note the engineering register names as
// an oracle is a calculation — never from a filename convention. This side only names them.

import type { NoteEntry } from "../engine/EngineClient";

export type NoteKind = NoteEntry["kind"];

/** Reading order. The brief first: it is the one note that describes the whole house. */
export const KIND_ORDER: readonly NoteKind[] = [
  "brief", "detail", "calc", "design", "superseded",
];

export const KIND_LABEL: Record<NoteKind, string> = {
  brief: "Brief",
  detail: "Construction notes",
  calc: "Calculations",
  design: "Design & product",
  superseded: "Superseded",
};

export const KIND_NOTE: Record<NoteKind, string> = {
  brief: "What this house is meant to be.",
  detail: "Prose that prints on a detail sheet — what a builder reads on the drawing.",
  calc: "The hand-worked notes the engine's calculations are checked against.",
  design: "Why this product, this dimension, this sequence.",
  superseded: "Kept on purpose: the rule usually outlives the design that prompted it.",
};

export interface NoteGroup {
  readonly kind: NoteKind;
  readonly label: string;
  readonly note: string;
  readonly notes: readonly NoteEntry[];
}

/** Notes grouped by kind in `KIND_ORDER`; within a group, the order the engine listed them
 *  (path order), which is the order they sit in the folder. Empty kinds are omitted. */
export function groupNotes(entries: readonly NoteEntry[]): NoteGroup[] {
  const groups: NoteGroup[] = [];
  for (const kind of KIND_ORDER) {
    const notes = entries.filter((entry) => entry.kind === kind);
    if (notes.length) {
      groups.push({ kind, label: KIND_LABEL[kind], note: KIND_NOTE[kind], notes });
    }
  }
  return groups;
}

/** Case-insensitive match on title, path and the sheets a note prints on. */
export function matchesNote(entry: NoteEntry, needle: string): boolean {
  if (!needle) return true;
  const hay = `${entry.title} ${entry.path} ${entry.on_sheets.join(" ")}`.toLowerCase();
  return hay.includes(needle);
}
