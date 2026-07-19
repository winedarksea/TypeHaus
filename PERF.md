# TypeHaus responsiveness — perf notes

Measured with `packages/engine/scripts/bench_rebuild.py` on `houses/catlin`
(118 resolved walls, 5 storeys). Run:

```
PYTHONPATH=packages/engine/src .venv/bin/python \
    packages/engine/scripts/bench_rebuild.py --house houses/catlin --iters 15
```

## Phase 0 baseline (build 12, before any optimization)

Full rebuild wall time: **median ~2100 ms**. move_nodes commit: **median ~3177 ms**.

| stage | median ms |
|---|---|
| load_plan | 2058 |
| ↳ load_plan.lint_provenance | **2053** |
| ↳ load_plan.import | 5 |
| ↳ load_plan.content_hash | 0.8 |
| resolve (all stages) | 31 |
| ↳ resolve.framing | 7.9 |
| ↳ resolve.junctions | 7.0 |
| ↳ resolve.stacking | 5.6 |
| ↳ resolve.rooms | 5.3 |
| run_checks (5 tiers) | 15 |

**Key finding:** `lint_provenance` (dialect lint + libcst provenance scan of all
editable plan files) is ~98% of rebuild cost — ~2.05 s per edit. The resolve
pipeline and checks are already sub-50 ms combined. This reorders the plan's
expected wins: the dominant latency is the libcst source scan on every rebuild,
which Phase 2 moves off the interactive path (in-memory plan authority; lint +
provenance run only with the async writeback). Restructuring the resolve
pipeline itself would save <50 ms and is not worth prioritizing.

## Phase 0 quick win — share the libcst parse (shipped)

Each editable file was parsed by libcst **three times** per rebuild (lint,
missing-uid, provenance), each independently building a `MetadataWrapper` and
resolving `PositionProvider` (the expensive step). `load_plan` now builds one
`MetadataWrapper` per file and passes it to all three scans.

Full rebuild wall time: **2100 ms → ~977 ms** (`lint_provenance` 2053 → 928).
No behavior change; all 114 engine tests pass. The remaining ~928 ms is inherent
libcst PositionProvider cost, addressed next by a per-file scan cache.

## Phase 1 — client quick wins (shipped)

- **1a Kill the double reload.** `store.ts` now has a revision-deduped
  `reloadIfStale(revision?)`: one in-flight GET /model tagged with its target
  revision; the mutation action and the WS echo both key on the same post-patch
  revision and coalesce into a single fetch. Other-tab sync intact.
- **1b Memoize SVG shapes.** `Canvas2D.tsx` `WallShape`/`OpeningShape`/`StairShape`
  wrapped in `React.memo` with stable, uid-based `onSelect`/`onHover`/`onEdit`
  callbacks (read tool state from the store at call time). Hover/selection now
  re-renders ~2 shapes instead of the whole subtree.
- **1c Panel3D render-on-demand.** Replaced the unconditional RAF loop with a
  coalesced dirty-flag `requestRender()` fired on orbit/dolly, resize, setModel,
  and highlight. GPU/CPU idle when the 3D view is static.
- **1d Serialize once per revision.** `state.py` caches the `model_json()` payload
  keyed by revision (invalidated in `rebuild()`), so repeat GETs skip
  `model_to_dict` + the file re-hash.

`tsc --noEmit` clean, `vite build` clean.

## Phase 2 — server hot path (safe subset shipped)

Phase-2a caches (`resolve_assembly`, `by_tag`, `ResolvedModel.wall`, `content_hash`)
were **measured and skipped**: `resolve_assembly` is <0.001 ms/call, the whole
resolve is ~30 ms, and `content_hash` ~0.8 ms — sub-millisecond gains not worth
adding invalidation state to frozen pydantic models. The plan mandates measuring
first; the bench says these are noise.

**Per-file scan cache** (`loader._SCAN_CACHE`): the libcst lint + provenance scan
depends only on a file's exact bytes, so results are cached keyed by content SHA.
A rebuild after a one-file edit re-scans just the changed file and replays the
rest. Source stays ground truth (the key *is* the file content, so a stale entry
can never be served). Stale entries evicted when files disappear.

**Cached libcst parse** (`writeback.parse_cached`, `lru_cache`): one `_commit`
locates each op, computes its inverse, and reads uids by scanning every file's
source repeatedly. libcst trees are immutable and `Module.visit` returns a fresh
tree, so read paths share one parsed tree per source string; only the write path
re-parses. Coordinator `_read_uid` / `_file_has_kind_list` routed through it too.

### Phase 2 results (bench, `houses/catlin`)

| path | before Phase 2 | after |
|---|---|---|
| idempotent rebuild (no file change) | ~977 ms | **~50 ms** |
| rebuild after 1-file edit (`lint_provenance`) | ~928 ms | **~263 ms** |
| move_nodes commit (build ops + apply_patch + rebuild) | ~3177 ms | **~939 ms** |

All 114 engine tests pass.

## Phase 2b — in-memory plan authority + async writeback (shipped)

`typehaus.source.inmemory` applies a macro's `PatchOp`s directly to the loaded
`PlanModel` (update/delete/add), reusing the exact `encode_value` → eval-in-
dialect-namespace path the libcst writeback uses, so there is one value
encoding, not two. `ProjectState.apply_edit()` takes this fast path whenever
`can_apply_in_memory()` says every op targets a known element/kind; it resolves
+ checks the in-memory result, answers immediately, and queues the *same* ops
on a background worker thread that does the classic source writeback. Undo/redo
and any op the fast path can't handle fall back to the flush-then-writeback
slow path, keeping source as ground truth throughout.

Two safety nets bound the risk of a dual mutation path:

- **Equivalence gate** (`test_inmemory_equivalence.py`): asserts the in-memory
  apply and the source-writeback-then-reload produce byte-identical plans over
  a move/update/delete/add corpus. This must stay green for the fast path to be
  trusted.
- **Reconciliation backstop** (`ProjectState._reconcile`): after each queued
  writeback lands, the worker reloads from source and compares against the
  in-memory plan; on any divergence it adopts source, logs loudly, and notifies
  connected clients — bounding an applicator bug to a flicker, not corruption.

### Phase 2b results (bench, `houses/catlin`, `move_nodes`)

| path | time |
|---|---|
| slow path (writeback + rebuild, unchanged) | ~882 ms |
| **fast path (in-memory apply, async writeback)** | **~44 ms** |

All 119 engine tests pass, including the 5-case equivalence gate.

## Phase 3 — async checks (shipped)

Every resolve (rebuild, the fast edit path, and reconciliation) now returns as
soon as `resolve()` lands; the check tiers (`run_from_model`, the ~14 ms
building-science/dialect rule registry) are queued onto a single-slot
background thread (`ProjectState._checks_loop`) instead of running inline.
`self.ok`/`self.findings` reflect resolve-time findings alone for that window
(`checks_pending` surfaces this in `model_json()`); when the check job lands it
merges in the check-tier findings **in place, without bumping the client
revision** (checks landing shouldn't look like a new edit to the client). A
newer edit arriving mid-check discards the in-flight job's result instead of
queueing it — only the latest resolve's checks are ever worth computing.
`app.py` broadcasts a `"checks"` WS event when a job lands so a connected
client can refresh findings without polling.

On `houses/catlin` this was already a ~14 ms cost, so the wall-clock win is
small; the change matters for larger houses / heavier future check tiers where
the check registry is no longer sub-frame, and it keeps the interactive path's
latency independent of how many checks are registered.

## Phase 4 — live drag preview (shipped)

`resolve_preview()` (`resolve/pipeline.py`) is a reduced resolve — junctions,
openings, envelope, and rooms only, skipping framing/floors/floor_heat/
stacking/conditions, which a ghost overlay never renders. `ProjectState.preview()`
applies ops to the *current* in-memory plan (reusing the Phase 2b applicator)
and runs it: no revision bump, no writeback, no checks, no undo journal entry —
a pure read. `POST /macro/preview` exposes this in the macro-request shape
(`build_macro_ops` builds the same per-node ops `/macro` would), so a client
dragging a node reuses the exact request it will later commit with `runMacro`.

The client (`ui/src/components/Canvas2D.tsx`) fires `previewMacro` on every
node-drag `pointermove`; the store (`state/store.ts`) self-throttles it to one
in-flight request, coalescing a fast pointermove stream to the latest position
rather than queuing. The returned wall axes / room outlines are matched by tag
and swapped into the SVG render in place of the committed model's geometry —
connected walls visibly stretch and rooms visibly reshape while the mouse is
still down, before the real `PATCH`/`runMacro` commit lands on mouseup.

### Phase 4 results (bench, `houses/catlin`, one `preview()` call)

| | time |
|---|---|
| reduced resolve preview (`state.preview()`) | ~16 ms median |

Comfortably inside a per-frame budget. 122 engine tests pass (2 new: the
happy-path preview and the not-in-memory-applicable 422); `tsc --noEmit` and
`vite build` are clean.

## Summary

All five phases are shipped. End-to-end `move_nodes` commit went from ~3177 ms
(build 12 baseline) to ~44 ms (fast path, Phase 2b/3), with a live ~16 ms
cascading preview (Phase 4) during the drag itself — comfortably under the
sub-200 ms perceived-latency target this plan set out to hit.
