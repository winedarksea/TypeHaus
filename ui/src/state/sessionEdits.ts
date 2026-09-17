// What this browser session has changed, folded from each mutation's result. Feeds the
// inspector's "Last edit" block and the agent handoff (model/handoff.ts). Pure: no store.
import type { Impact, MacroRequest, MacroResult, PatchOp } from "../engine/EngineClient";

export interface SessionEdits {
  created: string[];
  changed: string[];
  deleted: string[];
  // Keyed by the element the edit addressed; each edit replaces that element's entry, so a
  // re-move re-evaluates rather than accumulating stale impacts.
  impacts: Record<string, Impact[]>;
}

export function emptySessionEdits(): SessionEdits {
  return { created: [], changed: [], deleted: [], impacts: {} };
}

function addUnique(list: string[], tags: Iterable<string>): string[] {
  const next = [...list];
  for (const tag of tags) if (!next.includes(tag)) next.push(tag);
  return next;
}

// A tag deleted after it was created or changed leaves those lists; a tag re-created leaves
// `deleted`. Each tag sits in the one list that describes its end state.
function settle(edits: SessionEdits, created: string[], changed: string[], deleted: string[]): SessionEdits {
  const gone = new Set(deleted);
  const born = new Set(created);
  const nextCreated = addUnique(edits.created.filter((tag) => !gone.has(tag)), created);
  const nextDeleted = addUnique(edits.deleted.filter((tag) => !born.has(tag)), deleted);
  const nextChanged = addUnique(
    edits.changed.filter((tag) => !gone.has(tag)),
    changed.filter((tag) => !nextCreated.includes(tag) && !gone.has(tag)),
  );
  return { ...edits, created: nextCreated, changed: nextChanged, deleted: nextDeleted };
}

export function foldMacroResult(edits: SessionEdits, request: MacroRequest, result: MacroResult): SessionEdits {
  const addressed = "tag" in request && typeof request.tag === "string" ? request.tag : null;
  const created = Object.keys(result.minted ?? {});
  const deleted = [...new Set([...(result.deleted ?? []), ...(result.remap?.deleted ?? [])])];
  const changed = [
    ...(addressed && !created.includes(addressed) ? [addressed] : []),
    ...Object.keys(result.remap?.renamed ?? {}),
    ...Object.keys(result.remap?.rehost ?? {}),
    ...(result.impacts ?? []).filter((impact) => impact.kind === "carried").map((impact) => impact.tag),
  ];
  const next = settle(edits, created, changed, deleted);
  const impacts = { ...next.impacts };
  if (result.impacts) {
    if (addressed && result.impacts.length) impacts[addressed] = result.impacts;
    else if (addressed) delete impacts[addressed];
    else for (const impact of result.impacts) impacts[impact.tag] = [...(impacts[impact.tag] ?? []), impact];
  }
  for (const tag of deleted) delete impacts[tag];
  return { ...next, impacts };
}

export function foldPatchOps(edits: SessionEdits, ops: PatchOp[]): SessionEdits {
  return settle(
    edits,
    ops.filter((op) => op.op === "add").map((op) => op.tag),
    ops.filter((op) => op.op === "update").map((op) => op.tag),
    ops.filter((op) => op.op === "delete").map((op) => op.tag),
  );
}
