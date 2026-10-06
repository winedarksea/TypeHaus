import type { EngineeringCalculations } from "../engine/engineeringTypes";
import { calculationGroups, matchesCalculation, selectedCalculation } from "./calculationNavigation";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runCalculationNavigationTests() {
  const payload: EngineeringCalculations = {
    revision: "r1",
    files: {
      "README.md": "# Reading guide",
      "00-cover.md": "# Cover",
      "calcs/deck_post.md": "# Deck posts",
      "appendix/deck_post.md": "# Post data",
      "appendix/deck_post__P-1.md": "# P-1",
    },
    families: [{ kind: "deck_post", calculation: "calcs/deck_post.md", appendix: "appendix/deck_post.md",
      members: [{ item_id: "deck_post/P-1", path: "appendix/deck_post__P-1.md" }] }],
  };
  const groups = calculationGroups(payload);
  const paths = groups.flatMap((group) => [
    ...group.pages.map((page) => page.path),
    ...(group.members ?? []).flatMap((family) => family.pages.map((page) => page.path)),
  ]);
  assert(paths.length === Object.keys(payload.files).length && new Set(paths).size === paths.length,
    "every package file appears exactly once");
  assert(groups[0].pages[0].path === "00-cover.md", "overview starts with the cover");
  assert(groups[2].members?.[0].family === "deck post", "member sheets stay nested by family");
  assert(matchesCalculation(groups[1].pages[0], "  POSTS  "), "filter matches readable family titles");
  assert(matchesCalculation(groups[2].members![0].pages[0], "P-1"), "filter finds member IDs");
  assert(!matchesCalculation(groups[1].pages[0], "missing"), "unmatched filter does not invent pages");
  assert(selectedCalculation(payload, "appendix/deck_post__P-1.md") === "appendix/deck_post__P-1.md",
    "a selection survives regeneration when its sheet survives");
  assert(selectedCalculation(payload, "deleted.md") === "00-cover.md", "a removed sheet returns to the cover");
}
