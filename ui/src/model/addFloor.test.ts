// Add-floor defaults stack on the top storey and never collide with an existing tag.
import type { Storey } from "./types";
import { newFloorDefaults, storeyTagError } from "./addFloor";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runAddFloorTests(): void {
  const storeys: Storey[] = [
    { tag: "upper", elevation_m: 2.7432, ceiling_m: 2.4384 },
    { tag: "main", elevation_m: 0, ceiling_m: 2.7432 },
    { tag: "level_3", elevation_m: -3, ceiling_m: 2.5 },
  ];
  const d = newFloorDefaults(storeys);
  assert(Math.abs(d.elevation_m - (2.7432 + 2.4384)) < 1e-9, "stacks on the highest storey");
  assert(d.ceiling_m === 2.4384, "reuses the top storey's ceiling");
  assert(d.tag === "level_4", `skips a used tag, got ${d.tag}`);
  const empty = newFloorDefaults([]);
  assert(empty.elevation_m === 0 && empty.tag === "level_1", "an empty house starts at grade");
  assert(storeyTagError("attic", storeys) === null, "a fresh lowercase tag is fine");
  assert(storeyTagError("main", storeys) !== null, "an existing tag is refused");
  assert(storeyTagError("Attic", storeys) !== null, "uppercase is refused");
  assert(storeyTagError("2nd", storeys) !== null, "a leading digit is refused");
  console.log("Add-floor tests passed.");
}
