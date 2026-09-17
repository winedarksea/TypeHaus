// The lazy bar fetch, once per model revision (decision #75). The payload is ~700 KB, so a
// theme flip or a chip toggle must not refetch it; an edit (a new revision) must.
import type { Model, RebarSet } from "../model/types";
import type { EngineClient } from "./EngineClient";

/** What names one model's bars: the per-process revision plus the on-disk content hash. */
export function rebarKeyOf(model: Pick<Model, "revision" | "contentHash">): string {
  return `${model.revision}|${model.contentHash ?? ""}`;
}

const cache = new WeakMap<EngineClient, { key: string; sets: Promise<RebarSet[]> }>();

/** The bars for `model`, fetched at most once per (client, revision). A house with no
 *  reinforced host skips the round trip. A failure is not cached. */
export function loadRebar(client: EngineClient, model: Model): Promise<RebarSet[]> {
  if (model.rebar && model.rebar.length === 0) return Promise.resolve([]);
  const key = rebarKeyOf(model);
  const hit = cache.get(client);
  if (hit?.key === key) return hit.sets;
  const sets = client.getRebar().then((payload) => payload.rebar ?? []);
  sets.catch(() => { if (cache.get(client)?.sets === sets) cache.delete(client); });
  cache.set(client, { key, sets });
  return sets;
}
