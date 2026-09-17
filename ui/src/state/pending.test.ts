// Pending transforms: the overlay shows the instant a gesture commits, survives until the
// commit that set it settles, and a later commit's overlay is never cleared by an earlier one.
import type { MacroRequest, MacroResult } from "../engine/EngineClient";
import { createPendingSlice, type PendingSlice } from "./pending";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => { resolve = res; });
  return { promise, resolve };
}

const REQUEST: MacroRequest = { macro: "move_placeable", storey: "main", tag: "F-1", position: [0, 0] };

function harness() {
  const replies: ReturnType<typeof deferred<MacroResult | null>>[] = [];
  const reloads: string[] = [];
  const state: Record<string, unknown> = { model: { revision: "r0" } };
  const set = (partial: Record<string, unknown> | ((s: Record<string, unknown>) => Record<string, unknown>)) =>
    Object.assign(state, typeof partial === "function" ? partial(state) : partial);
  const get = () => state as never;
  Object.assign(state, createPendingSlice(set as never, get, {} as never));
  Object.assign(state, {
    runMacro: () => { const reply = deferred<MacroResult | null>(); replies.push(reply); return reply.promise; },
    reloadIfStale: async (revision: string) => {
      reloads.push(revision);
      (state.model as { revision: string }).revision = revision;
    },
  });
  return { slice: state as unknown as PendingSlice, state, replies, reloads };
}

function ok(revision: string): MacroResult {
  return { revision, minted: {}, undo: 1, redo: 0, remap: { renamed: {}, deleted: [], rehost: {} }, deleted: [], warnings: [] };
}

export async function runPendingTransformTests(): Promise<void> {
  const h = harness();
  const item = { uid: "U1" };
  const first = h.slice.commitTransform(item, { position_m: [1, 1] }, REQUEST);
  const shown = h.slice.pendingTransforms.U1;
  assert(shown?.position_m?.[0] === 1, "the overlay is visible before the engine answers");

  const second = h.slice.commitTransform(item, { rotation: 90 }, REQUEST);
  const merged = (h.state.pendingTransforms as PendingSlice["pendingTransforms"]).U1;
  assert(merged.position_m?.[0] === 1 && merged.rotation === 90, "a second commit merges into the overlay");

  h.replies[0].resolve(ok("r1"));
  await first;
  assert((h.state.pendingTransforms as PendingSlice["pendingTransforms"]).U1,
    "an earlier commit settling does not clear a later commit's overlay");
  assert(h.reloads.includes("r1"), "the model is brought to the commit's revision before clearing");

  h.replies[1].resolve(ok("r2"));
  await second;
  assert(!(h.state.pendingTransforms as PendingSlice["pendingTransforms"]).U1,
    "the last commit settling clears the overlay onto the authoritative model");

  const failed = harness();
  const rejected = failed.slice.commitTransform(item, { position_m: [5, 5] }, REQUEST);
  failed.replies[0].resolve(null);
  await rejected;
  assert(!(failed.state.pendingTransforms as PendingSlice["pendingTransforms"]).U1,
    "a rejected commit snaps back to the authoritative position");
  assert(failed.reloads.length === 0, "a rejected commit does not force a reload");

  console.log("Pending transform tests passed.");
}
