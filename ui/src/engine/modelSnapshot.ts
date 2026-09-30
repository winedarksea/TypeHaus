import type { Model } from "../model/types";

// A missing, stale HTML fallback, or truncated asset must leave boot on the engine path.
export async function loadModelSnapshot(file = "catlin-model.json"): Promise<Model> {
  const url = new URL(file, document.baseURI).href;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`model snapshot ${response.status} @ ${url}`);
  const model: unknown = await response.json();
  if (!model || typeof model !== "object") throw new Error("model snapshot is invalid");
  const candidate = model as Partial<Model>;
  if (typeof candidate.revision !== "string" ||
      typeof candidate.project?.name !== "string" ||
      !Array.isArray(candidate.storeys) || !Array.isArray(candidate.walls) ||
      candidate.storeys.length === 0 || candidate.walls.length === 0 ||
      !candidate.storeys.every((storey) => typeof storey?.tag === "string") ||
      !candidate.walls.every((wall) => typeof wall?.uid === "string" &&
        Array.isArray(wall.axis) && wall.axis.length === 2 &&
        Array.isArray(wall.layers))) {
    throw new Error("model snapshot has no resolved house geometry");
  }
  return candidate as Model;
}
