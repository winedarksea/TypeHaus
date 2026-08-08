import { nextStarFields } from "./detailStar";
import type { DetailIndexEntry } from "../engine/EngineClient";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function entry(fields: Partial<DetailIndexEntry> & { key: string }): DetailIndexEntry {
  return {
    kind: "storey_stack",
    title: fields.key,
    transition: "TR-RIM",
    overlay: null,
    elements: [],
    state: "seed",
    star: false,
    transition_star: false,
    starred_conditions: [],
    unstarred_conditions: [],
    ...fields,
  };
}

const RIM = "storey_stack:rim:CATLIN_EXT_2X6";
const INT = "storey_stack:rim:INT_2X4_PARTITION";

export function runDetailStarTests() {
  // A transition nobody has curated: the toggle has to *create* the override, because
  // flipping the pattern-wide default would star every sibling condition at once.
  const first = nextStarFields(entry({ key: RIM }));
  assert(first.star === true, "Toggling an unstarred detail stars it");
  assert(first.fields.starred_conditions.join() === RIM,
    "Starring against a false default records the key as an exception");
  assert(first.fields.unstarred_conditions.length === 0,
    "The opposite list is left alone");

  // Toggling back to the transition's own default drops the override rather than moving
  // it across — the authored source should keep only exceptions that still mean something.
  const back = nextStarFields(entry({ key: RIM, star: true, starred_conditions: [RIM] }));
  assert(back.star === false, "Toggling a starred detail unstars it");
  assert(back.fields.starred_conditions.length === 0 &&
    back.fields.unstarred_conditions.length === 0,
    "Returning to the pattern default clears the override instead of inverting it");

  // The catlin shape: a starred pattern with interior keys carved out of it.
  const carve = nextStarFields(entry({ key: INT, star: true, transition_star: true }));
  assert(carve.star === false && carve.fields.unstarred_conditions.join() === INT,
    "Unstarring against a true default records the key in unstarred_conditions");

  // Siblings' overrides survive the edit — this is the whole point of the change.
  const sibling = nextStarFields(entry({
    key: RIM, star: true, transition_star: true, unstarred_conditions: [INT],
  }));
  assert(sibling.fields.unstarred_conditions.join() === [INT, RIM].join(),
    "Another condition's override is preserved and the toggled key joins it");

  const restore = nextStarFields(entry({
    key: INT, transition_star: true, unstarred_conditions: [INT, RIM],
  }));
  assert(restore.star === true && restore.fields.unstarred_conditions.join() === RIM,
    "Re-starring drops only the toggled key from the override list");

  // A key can only appear once per list, and a contradictory pair (both lists) resolves the
  // way the engine resolves it — unstar wins — so the toggle reads it as currently off.
  const both = nextStarFields(entry({
    key: RIM, transition_star: true, starred_conditions: [RIM], unstarred_conditions: [RIM],
  }));
  assert(both.star === true, "An unstar override wins, so the toggle turns the star back on");
  assert(both.fields.starred_conditions.length === 0 &&
    both.fields.unstarred_conditions.length === 0,
    "Toggling back to the default clears the contradictory pair from both lists");
}
