// Transition ↔ condition matching, mirroring the engine (model/patterns.py::matches, used by
// checks/integrity, the detail emitter, and the scaffolder). A `Condition.key` already carries
// its kind as a prefix — "storey_stack:rim:CATLIN_BASEMENT_12|CATLIN_EXT_2X6" — and a
// Transition's `condition_pattern` is an fnmatch glob over that whole key. Getting this wrong
// does not fail loudly; it just reports the wrong coverage, so the semantics are mirrored here
// rather than approximated.

import type { Condition, Transition } from "./types";

const GLOB_SPECIALS = /[.+^${}()|\\]/g;

/** fnmatch semantics: `*` any run, `?` one character, `[seq]` / `[!seq]` a character class. */
export function globMatches(pattern: string, key: string): boolean {
  let source = "^";
  for (let index = 0; index < pattern.length; index++) {
    const character = pattern[index];
    if (character === "*") {
      source += ".*";
    } else if (character === "?") {
      source += ".";
    } else if (character === "[") {
      const close = pattern.indexOf("]", index + 1);
      if (close === -1) {
        source += "\\[";
      } else {
        const body = pattern.slice(index + 1, close);
        source += `[${body.startsWith("!") ? `^${body.slice(1)}` : body}]`;
        index = close;
      }
    } else {
      source += character.replace(GLOB_SPECIALS, "\\$&");
    }
  }
  return new RegExp(`${source}$`).test(key);
}

export function transitionMatchesCondition(transition: Transition, condition: Condition): boolean {
  return globMatches(transition.pattern, condition.key);
}

/** Conditions each transition documents, and the conditions no transition covers. */
export function transitionCoverage(transitions: Transition[], conditions: Condition[]): {
  matchesByTransition: Map<string, Condition[]>;
  uncovered: Condition[];
} {
  const matchesByTransition = new Map<string, Condition[]>();
  const covered = new Set<Condition>();
  for (const transition of transitions) {
    const matched = conditions.filter((condition) => transitionMatchesCondition(transition, condition));
    matchesByTransition.set(transition.tag, matched);
    for (const condition of matched) covered.add(condition);
  }
  return { matchesByTransition, uncovered: conditions.filter((condition) => !covered.has(condition)) };
}
