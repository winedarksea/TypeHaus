// Which resolved layers get an extruded prism in 3D. The subject is catlin's EXT_2X6 girt
// band: `furring` with a FramingSpec, so the girts are real members the viewer already draws,
// and a solid over them both hid them and sealed the 1/2" vent gap they stand off the foam on.
import type { Layer } from "../../model/types";
import { layerDrawsBandSolid } from "./walls";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

type Band = Pick<Layer, "function" | "is_cavity" | "framed">;
const band = (over: Partial<Band>): Band =>
  ({ function: "cladding", is_cavity: false, framed: false, ...over });

// Called by scripts/run-geometry-tests.mjs.
export function runWallBandSolidTests(): void {
  // EXT_2X6's `outer-girt`: KDAT 2x4 laid flat at 24" o.c. on blocks.
  assert(!layerDrawsBandSolid(band({ function: "furring", framed: true })),
    "a framed furring band must not draw a solid over the girts it stands for");

  // A furring layer with no FramingSpec is a genuine continuous sheet.
  assert(layerDrawsBandSolid(band({ function: "furring", framed: false })),
    "unframed furring is a real sheet and keeps its solid");

  // The wall body has to stay opaque from outside; the `framing:*` facets answer the
  // stud/sheathing double-draw instead.
  assert(layerDrawsBandSolid(band({ function: "structure", framed: true })),
    "a framed structure band still draws");
  assert(layerDrawsBandSolid(band({ function: "sheathing" })), "sheathing still draws");

  // Cavity fill shares its host's polygon.
  assert(!layerDrawsBandSolid(band({ function: "insulation", is_cavity: true })),
    "cavity fill draws no solid of its own");

  // The payload may predate `framed`; an older model.json keeps every band it had.
  assert(layerDrawsBandSolid({ function: "furring" } as Band),
    "a payload with no `framed` flag falls back to drawing the band");

  console.log("Wall band solid tests passed.");
}
