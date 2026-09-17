// Server push events the store must not swallow. `writeback-failed` says an edit the user
// already saw applied was reverted on disk; hot-reloading it away silently (the old
// `file-changed` behaviour) is exactly the bug this event exists to end.
import type { EngineEvent } from "../engine/EngineClient";
import { handleEvent } from "./store";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function harness(initial: Record<string, unknown> = {}) {
  const state: Record<string, unknown> = { writebackFailure: null, ...initial };
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

  // A lost edit also flips the chip and drops the overlays that showed it.
  const lost = harness({ saveState: "saving", pendingTransforms: { U1: { position_m: [1, 1], seq: 1 } } });
  lost.fire({ type: "writeback-failed", revision: "r4", detail: "not editable" });
  assert(lost.state.saveState === "failed", "a writeback failure reads Save failed");
  assert(Object.keys(lost.state.pendingTransforms as object).length === 0,
    "overlays of a reverted edit are cleared");

  // Saved: the writeback drained at the revision on screen, nothing queued.
  const saved = harness({ saveState: "saving", savedRevision: null, model: { revision: "r5" } });
  saved.fire({ type: "saved", revision: "r5" });
  assert(saved.state.saveState === "saved", "a drained writeback at the shown revision reads Saved");
  const early = harness({ saveState: "saving", savedRevision: null, model: { revision: "r5" } });
  early.fire({ type: "saved", revision: "r6" });
  assert(early.state.saveState === "saving" && early.state.savedRevision === "r6",
    "a saved event for a revision not yet on screen is remembered, not shown");

  // Checks for the revision on screen patch findings in place; a newer one reloads.
  const findings = [{ severity: "error", message: "R311 riser" }];
  const same = harness({ model: { revision: "r7", findings: [], ok: true, checksPending: true } });
  same.fire({ type: "checks", revision: "r7", ok: false, findings } as EngineEvent);
  const patched = same.state.model as { findings: unknown[]; ok: boolean; checksPending: boolean };
  assert(patched.findings.length === 1 && patched.ok === false && patched.checksPending === false,
    "checks for the shown revision patch findings without a reload");
  assert(same.reloaded.length === 0, "no GET /model for a same-revision checks event");
  const behind = harness({ model: { revision: "r7", findings: [] } });
  behind.fire({ type: "checks", revision: "r8", ok: true, findings: [] });
  assert(behind.reloaded[0] === "r8", "checks for a newer revision reload the model");

  console.log("Store event tests passed.");
}
