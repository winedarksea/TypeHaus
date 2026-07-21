import { openingHostWall } from "./geometry";
import type { Opening, Wall } from "./types";

export function runModelGeometryTests() {
  const wall = { uid: "W101AAAAAA", tag: "W-101" } as Wall;
  const opening = { host: "W-101" } as Opening;
  if (openingHostWall([wall], opening) !== wall) {
    throw new Error("Opening host tags must resolve to their wall even when the UID differs");
  }
  if (openingHostWall([wall], { ...opening, host: "W101AAAAAA" }) !== undefined) {
    throw new Error("Opening host lookup must not treat a wall UID as an authored host tag");
  }
}
