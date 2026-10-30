// Piece keys name one board of a door or window (`frame:jamb-left`, `hardware:0`,
// `casing:<uid>:leg_left`); builders stamp them, the inspector reads them
// (→ three/builders/openingPieces.ts).

/** The part of a piece key before its first colon: `frame`, `leaf`, `hardware`, `casing`... */
export function pieceRole(piece: string): string {
  return piece.split(":", 1)[0];
}

/** Human label for a piece key ("frame:jamb-left" -> "Frame, jamb left"). */
export function pieceLabel(piece: string): string {
  const [role, ...rest] = piece.split(":");
  const words = (text: string) => text.replace(/[-_]/g, " ");
  const head = words(role).replace(/^./, (c) => c.toUpperCase());
  // Casing and stool keys lead with a uid; only the leg name reads.
  const tail = role === "casing" ? rest.slice(1) : role === "stool" ? [] : rest;
  return tail.length ? `${head}, ${words(tail.join(" "))}` : head;
}
