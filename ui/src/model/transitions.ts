// Transition ↔ condition matching, mirroring the engine (model/patterns.py::matches, used by
// checks/integrity, the detail emitter, and the scaffolder). A `Condition.key` already carries
// its kind as a prefix — "storey_stack:rim:BASEMENT_12|EXT_2X6" — and a
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

/** The transition that binds a condition: the FIRST whose pattern matches, in authored order
 *  (model/patterns.py::first_match). A later, narrower pattern behind a wildcard binds nothing. */
export function bindingTransition(transitions: Transition[], condition: Condition): Transition | undefined {
  return transitions.find((transition) => transitionMatchesCondition(transition, condition));
}

/** Conditions each transition binds (first match), and the conditions no transition covers. */
export function transitionCoverage(transitions: Transition[], conditions: Condition[]): {
  matchesByTransition: Map<string, Condition[]>;
  uncovered: Condition[];
} {
  const matchesByTransition = new Map<string, Condition[]>(
    transitions.map((transition) => [transition.tag, []]));
  const uncovered: Condition[] = [];
  for (const condition of conditions) {
    const binder = bindingTransition(transitions, condition);
    if (binder) matchesByTransition.get(binder.tag)?.push(condition);
    else uncovered.push(condition);
  }
  return { matchesByTransition, uncovered };
}
