import type { Model } from "./types";

// Tag → uid for every record a reader can name. The engine's derived surfaces — conditions,
// transitions, panel schedules, take-off rollups — all address elements by their authored
// *tag*, while selection and zoom are keyed by *uid*. This is the one hop between them, built
// once per model and shared by every reader that wants a clickable tag.
//
// First writer wins: tags are unique per element family, and a collision across families would
// mean an authoring error the resolver already reports.
export function uidByTag(model: Model): Map<string, string> {
  const index = new Map<string, string>();
  const add = (records: readonly { tag: string; uid: string }[]) => {
    for (const record of records) if (!index.has(record.tag)) index.set(record.tag, record.uid);
  };
  add(model.walls);
  add(model.openings);
  add(model.rooms);
  add(model.roofs ?? []);
  add(model.solids ?? []);
  add(model.stairs ?? []);
  add(model.floors ?? []);
  // Placeables (outlets, switches, lights, equipment) and PV modules: what the circuits
  // reader's device and array tags resolve against. locateUid() already handles both kinds,
  // so a tag from the panel schedule zooms like any other.
  add(model.canvas_objects ?? []);
  add(model.solar_panels ?? []);
  add(model.light_runs ?? []);
  return index;
}
