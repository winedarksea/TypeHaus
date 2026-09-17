// The mutation queue: journaled writes run one at a time, each reading the revision its
// predecessor produced, and an external conflict pauses the queue instead of stacking 409s.
import type { MacroRequest, MacroResult, PreviewGeometry } from "../engine/EngineClient";
import { RevisionConflict } from "../engine/EngineClient";
import { createMutationActions, impactSummary, mutationQueueIdle } from "./mutations";
import { emptySessionEdits } from "./sessionEdits";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (err: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

const MOVE: MacroRequest = { macro: "move_placeable", storey: "main", tag: "F-1", position: [1, 2] };

function harness() {
  const sent: string[] = [];
  const replies: ReturnType<typeof deferred<MacroResult>>[] = [];
  const toasts: string[] = [];
  const state: Record<string, unknown> = {
    model: { revision: "r0" }, conflict: null, offline: false, saveState: "idle",
    savedRevision: null, sessionEdits: emptySessionEdits(),
  };
  const client = {
    runMacro: (_request: MacroRequest, revision: string) => {
      sent.push(revision);
      const reply = deferred<MacroResult>();
      replies.push(reply);
      return reply.promise;
    },
  };
  const set = (partial: Record<string, unknown>) => Object.assign(state, partial);
  const get = () => ({
    ...state,
    client,
    toast: (message: string) => { toasts.push(message); },
    // A reload lands the revision the mutation produced.
    reloadIfStale: async (revision: string) => { (state.model as { revision: string }).revision = revision; },
  }) as never;
  const actions = createMutationActions(set as never, get);
  return { state, sent, replies, toasts, actions };
}

function result(revision: string, extra: Partial<MacroResult> = {}): MacroResult {
  return {
    revision, minted: {}, undo: 1, redo: 0, remap: { renamed: {}, deleted: [], rehost: {} },
    deleted: [], warnings: [], ...extra,
  };
}

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

export async function runMutationQueueTests(): Promise<void> {
  // Two drags fired back to back: the second waits, then sends the first's revision.
  const h = harness();
  const first = h.actions.runMacro(MOVE);
  const second = h.actions.runMacro(MOVE);
  await tick();
  assert(h.sent.length === 1 && h.sent[0] === "r0", "only the first write is on the wire");
  assert(!mutationQueueIdle(), "the queue reports work in flight");
  assert(h.state.saveState === "saving", "a started write shows Saving…");
  h.replies[0].resolve(result("r1"));
  await first;
  await tick();
  assert(h.sent.join(",") === "r0,r1",
    "the queued write reads the revision the first produced, not the one it was fired at");
  h.replies[1].resolve(result("r2"));
  await second;
  assert(mutationQueueIdle(), "the queue drains");

  // A failure does not wedge the chain.
  const f = harness();
  const failing = f.actions.runMacro(MOVE);
  const after = f.actions.runMacro(MOVE);
  await tick();
  f.replies[0].reject(new Error("boom"));
  assert(await failing === null, "a failed write resolves null");
  await tick();
  assert(f.sent.length === 2, "the next write still runs after a failure");
  f.replies[1].resolve(result("r5"));
  await after;

  // A 409 raises the banner and pauses every queued write behind it.
  const c = harness();
  const conflicted = c.actions.runMacro(MOVE);
  const paused = c.actions.runMacro(MOVE);
  await tick();
  c.replies[0].reject(new RevisionConflict("changed on disk"));
  await conflicted;
  assert(await paused === null, "a write queued behind a conflict does not run");
  assert(c.sent.length === 1, "nothing reached the engine while the conflict stands");
  assert(c.state.conflict !== null && c.state.saveState === "failed", "the conflict is shown, unsaved");

  // Impacts replace the warning toasts with one summary line, and land in sessionEdits.
  const i = harness();
  const impacted = i.actions.runMacro(MOVE);
  await tick();
  i.replies[0].resolve(result("r1", {
    warnings: ["PR-1 moved", "SL-1 moved", "wall_ref dropped"],
    impacts: [
      { tag: "PR-1", kind: "carried", reason: "drain vertex follows" },
      { tag: "SL-1", kind: "carried", reason: "sleeve follows" },
      { tag: "F-1", kind: "needs_review", reason: "re-point wall_ref" },
    ],
  }));
  await impacted;
  assert(i.toasts.length === 1 && i.toasts[0] === "2 carried, 1 needs review",
    `one summary toast, got ${JSON.stringify(i.toasts)}`);
  const edits = i.state.sessionEdits as ReturnType<typeof emptySessionEdits>;
  assert(edits.changed.includes("F-1") && edits.changed.includes("PR-1"), "the mover and carried runs are changed");
  assert(edits.impacts["F-1"]?.length === 3, "impacts are filed under the element the edit addressed");
  assert(impactSummary([]) === "", "no impacts, no summary");

  await deletingAWallWarnsBeforeItDangles();
  console.log("Mutation queue tests passed.");
}

// Deleting a wall no longer refuses when something still names it — the engine reports what
// will dangle and the first Delete shows it, so a house is never quietly holed.
async function deletingAWallWarnsBeforeItDangles() {
  const wall = { uid: "u-w1", tag: "W-1", storey: "main" };
  const previews: PreviewGeometry[] = [];
  const toasts: string[] = [];
  const ran: MacroRequest[] = [];
  const sentCount = () => ran.length;  // via a call, or tsc narrows the length to a literal
  const selection = { kind: "wall" as const, uid: wall.uid };
  const state: Record<string, unknown> = { model: { revision: "r0", walls: [wall] }, selection };
  const get = () => ({
    ...state,
    selection,
    client: { previewMacro: async () => previews.shift() ?? { walls: [], openings: [], rooms: [] } },
    toast: (message: string) => { toasts.push(message); },
    runMacro: async (request: MacroRequest) => { ran.push(request); return result("r1"); },
    select: () => {},
  }) as never;
  const actions = createMutationActions((() => {}) as never, get);

  const dangling = { walls: [], openings: [], rooms: [],
    impacts: [{ tag: "FS-Main", kind: "needs_review" as const, reason: "FS-Main.joists names W-1" },
              { tag: "W-201", kind: "needs_review" as const, reason: "W-201.stacks_on names W-1" }] };
  previews.push(dangling);
  await actions.deleteSelection();
  assert(sentCount() === 0, "the first Delete must not delete");
  assert(toasts.length === 1 && toasts[0].includes("2 references") && toasts[0].includes("FS-Main"),
    `the warning names what dangles, got ${JSON.stringify(toasts)}`);

  await actions.deleteSelection();  // armed by the warning: this one goes through
  assert(sentCount() === 1 && ran[0].macro === "delete_wall", "the second Delete deletes");

  // A wall nothing names is deleted on the first press — no confirmation theatre.
  ran.length = 0;
  toasts.length = 0;
  await actions.deleteSelection();
  assert(sentCount() === 1, "a clean wall deletes straight away");
}
