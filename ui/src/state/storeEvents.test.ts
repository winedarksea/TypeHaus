// Server push events the store must not swallow. `writeback-failed` says an edit the user
// already saw applied was reverted on disk; hot-reloading it away silently (the old
// `file-changed` behaviour) is exactly the bug this event exists to end.
import type { EngineEvent } from "../engine/EngineClient";
import { handleEvent } from "./store";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function harness() {
  const state: Record<string, unknown> = { writebackFailure: null };
  const reloaded: string[] = [];
  const get = () => ({
    ...state,
    reloadIfStale: async (rev: string) => { reloaded.push(rev); },
  }) as never;
  const set = (partial: Record<string, unknown>) => Object.assign(state, partial);
  return { state, reloaded, fire: (e: EngineEvent) => handleEvent(get, set as never, e) };
}

export function runStoreEventTests(): void {
  const h = harness();
  h.fire({ type: "writeback-failed", revision: "r2", detail: "no editable file hosts EQ-B-WH" });
  assert(h.state.writebackFailure === "no editable file hosts EQ-B-WH",
    "the failure detail is surfaced, not logged away");
  assert(h.reloaded.length === 1 && h.reloaded[0] === "r2",
    "the client re-syncs to the reverted source truth");

  // An ordinary external edit stays silent — the banner is reserved for lost edits.
  const quiet = harness();
  quiet.fire({ type: "file-changed", revision: "r3", ok: true });
  assert(quiet.state.writebackFailure === null,
    "an external edit does not claim the user's edit was reverted");
  assert(quiet.reloaded.length === 1 && quiet.reloaded[0] === "r3",
    "an external edit still triggers the ordinary stale reload");

  console.log("Store event tests passed.");
}
