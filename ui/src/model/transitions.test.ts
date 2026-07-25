import { globMatches, transitionCoverage } from "./transitions";
import type { Condition, Transition } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function transition(tag: string, pattern: string): Transition {
  return { tag, pattern, overlay: null, notes: null, continuity: [], joins: [] };
}
function condition(kind: string, key: string): Condition {
  return { kind, key, elements: [] };
}

export function runTransitionTests() {
  // A Condition.key already carries its kind as a prefix, and the engine fnmatches the pattern
  // against that whole key (model/patterns.py). These are catlin's real keys and patterns.
  assert(globMatches("wall_roof:*", "wall_roof:GARAGE_ROOF|GARAGE_WALL_2X6"),
    "A trailing wildcard covers a whole condition kind");
  assert(globMatches("storey_stack:rim:*", "storey_stack:rim:CATLIN_BASEMENT_12|CATLIN_EXT_2X6"),
    "A pattern may narrow within a kind — the key prefix must not be double-counted");
  assert(!globMatches("storey_stack:rim:*", "storey_stack:sill:CATLIN_BASEMENT_12"),
    "A narrowed pattern must not swallow the rest of its kind");
  assert(globMatches("opening_perimeter:CATLIN_EXT_*", "opening_perimeter:CATLIN_EXT_2X6"),
    "Wildcards work mid-key");
  assert(!globMatches("opening_perimeter:CATLIN_EXT_*", "opening_perimeter:CATLIN_CONC_12_INT"),
    "A prefix that does not match is not covered");
  assert(globMatches("assembly_change:?", "assembly_change:A") &&
    !globMatches("assembly_change:?", "assembly_change:AB"),
    "'?' matches exactly one character, as fnmatch does");
  assert(globMatches("a[bc]d", "acd") && !globMatches("a[bc]d", "aed"),
    "Character classes are honoured");
  assert(globMatches("a[!bc]d", "aed") && !globMatches("a[!bc]d", "abd"),
    "Negated character classes are honoured");
  assert(!globMatches("wall_roof:*", "roof_wall_roof:X"),
    "Matching is anchored at both ends, not a substring search");
  assert(globMatches("a.b", "a.b") && !globMatches("a.b", "axb"),
    "Regex metacharacters in a pattern are literal");

  const transitions = [transition("TR-EAVE", "wall_roof:*"), transition("TR-RIM", "storey_stack:rim:*")];
  const conditions = [
    condition("wall_roof", "wall_roof:CATLIN_ROOF|INT_2X4_PARTITION"),
    condition("storey_stack", "storey_stack:rim:CATLIN_BASEMENT_12|CATLIN_EXT_2X6"),
    condition("roof_ridge", "roof_ridge:CATLIN_ROOF"),
  ];
  const coverage = transitionCoverage(transitions, conditions);
  assert(coverage.matchesByTransition.get("TR-EAVE")?.length === 1, "Each transition reports its own matches");
  assert(coverage.matchesByTransition.get("TR-RIM")?.length === 1,
    "The rim transition must find its conditions — reporting zero was the bug this mirrors away");
  assert(coverage.uncovered.length === 1 && coverage.uncovered[0].kind === "roof_ridge",
    "Conditions no transition documents are surfaced, not silently dropped");
}
