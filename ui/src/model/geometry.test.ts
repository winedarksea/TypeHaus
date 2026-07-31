import { memberFootprint, openingFitsWall, openingHostWall, openingStartFromCenter } from "./geometry";
import type { Member, Opening, Wall } from "./types";

export function runModelGeometryTests() {
  const wall = { uid: "W101AAAAAA", tag: "W-101" } as Wall;
  const opening = { host: "W-101" } as Opening;
  if (openingHostWall([wall], opening) !== wall) {
    throw new Error("Opening host tags must resolve to their wall even when the UID differs");
  }
  if (openingHostWall([wall], { ...opening, host: "W101AAAAAA" }) !== undefined) {
    throw new Error("Opening host lookup must not treat a wall UID as an authored host tag");
  }
  const host = { ...wall, axis: [[0, 0], [4, 0]] } as Wall;
  if (openingStartFromCenter(2, 1) !== 1.5 || !openingFitsWall(host, 2, 1)) {
    throw new Error("Opening drags must convert center stations to fitting start-jamb stations");
  }
  if (openingFitsWall(host, .2, 1)) {
    throw new Error("Opening drag previews must reject a width that extends beyond the host wall");
  }
  // A stair landing deck must draw as its platform rectangle, not its centreline —
  // p0->p1 swept by the pre-resolved width, matching the engine's _member_footprint.
  const landing = { p0: [0, 0], p1: [0, 2], width_m: 1 } as unknown as Member;
  const rect = memberFootprint(landing);
  const xs = rect.map((point) => point[0]);
  const ys = rect.map((point) => point[1]);
  if (rect.length !== 4 || Math.max(...xs) - Math.min(...xs) !== 1
    || Math.max(...ys) - Math.min(...ys) !== 2) {
    throw new Error("memberFootprint must sweep the axis by the member's full width");
  }
  if (memberFootprint({ ...landing, p1: [0, 0] } as unknown as Member).length !== 0) {
    throw new Error("memberFootprint must return no rectangle for a zero-run member");
  }
}
