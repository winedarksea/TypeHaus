// Pick keys for the boards of a door or window. They mirror the GPart names in
// resolve/geometry_openings.py so a piece names the same thing in the engine and the viewer.

/** Key for one solid of an engine-authored door part (`frame`, `leaf`, `hardware:0`, ...).
 *  Frame boards are named by where they sit, since the part carries no per-board name. */
export function authoredPiece(
  partKey: string, solidIndex: number, a0: number, a1: number, z0: number, z1: number,
  openingWidth: number, midZ: number,
): string {
  if (partKey === "frame") {
    if (a1 - a0 > openingWidth * 0.6) return (z0 + z1) / 2 > midZ ? "frame:head" : "frame:sill";
    return (a0 + a1) / 2 < 0 ? "frame:jamb-left" : "frame:jamb-right";
  }
  return partKey.includes(":") ? partKey : `${partKey}:${solidIndex}`;
}
