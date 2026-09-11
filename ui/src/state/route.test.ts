// Hash routing. It exists so the PWA icon on a phone opens the board, so the one thing
// that must hold is that `#/site/board` resolves without the design surface being touched.
import { hashFor, parseHash } from "./route";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runRouteTests(): void {
  assert(parseHash("#/site/board")?.surface === "site", "the site surface is addressable");
  assert(parseHash("#/site/board")?.sitePage === "board", "and so is the page");
  assert(parseHash("#/site/inspections")?.sitePage === "inspections", "both pages");
  assert(parseHash("#/site")?.sitePage === "board", "a bare /site lands on the board");
  assert(parseHash("#/site/")?.sitePage === "board", "trailing slash tolerated");
  assert(parseHash("#/site/nonsense")?.sitePage === "board",
    "an unknown page falls to the board rather than rendering nothing");

  assert(parseHash("")?.surface === "design", "an empty hash is the design surface");
  assert(parseHash("#/")?.surface === "design", "and so is a bare hash");
  // Anything this app does not own is left alone: the route sync ignores a null.
  assert(parseHash("#some-anchor") === null, "a foreign anchor is not ours to claim");

  assert(hashFor({ surface: "site", sitePage: "inspections" }) === "#/site/inspections",
    "round-trips");
  assert(hashFor({ surface: "design", sitePage: "board" }) === "",
    "the design surface keeps an empty hash — nothing about the existing app's addresses "
    + "changes");
  const round = parseHash(hashFor({ surface: "site", sitePage: "inspections" }))!;
  assert(round.surface === "site" && round.sitePage === "inspections", "and back again");

  console.log("Hash-route tests passed.");
}
