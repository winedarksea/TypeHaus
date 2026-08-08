import type { DetailIndexEntry } from "../engine/EngineClient";

// Per-condition detail curation (→ 11b). A Transition binds a *pattern*, so one transition
// usually owns many condition keys; `Transition.star` is its pattern-wide default and
// `starred_conditions`/`unstarred_conditions` name the exact keys that disagree with it.
// Toggling one row therefore means editing those two lists — never flipping `star`, which
// would re-curate every sibling detail at once (the old behaviour, and the bug).
export interface StarToggle {
  // The toggled entry's star value after the edit — what the optimistic update writes.
  star: boolean;
  // The PatchOp `fields` payload: both lists, always sent whole (a PatchOp update replaces
  // a field, it does not merge into it).
  fields: { starred_conditions: string[]; unstarred_conditions: string[] };
}

function without(list: readonly string[] | undefined, key: string): string[] {
  return (list ?? []).filter((k) => k !== key);
}

/** The single PatchOp that flips one detail's star, leaving its siblings alone.
 *
 * An override only survives while it disagrees with the pattern-wide flag: toggling a key
 * back to the transition's own default *removes* it from both lists rather than moving it
 * to the other one, so the authored source keeps only the exceptions that mean something.
 * The engine reads the same precedence (`Transition.stars`): unstar wins over star, and a
 * key in neither list falls back to `transition_star`.
 */
export function nextStarFields(entry: DetailIndexEntry): StarToggle {
  const star = !entry.star;
  const starred = without(entry.starred_conditions, entry.key);
  const unstarred = without(entry.unstarred_conditions, entry.key);
  if (star !== entry.transition_star) {
    (star ? starred : unstarred).push(entry.key);
  }
  return { star, fields: { starred_conditions: starred, unstarred_conditions: unstarred } };
}
