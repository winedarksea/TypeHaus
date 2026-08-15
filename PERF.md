# Type:Haus responsiveness — perf notes

## How to reproduce every number here

```
PYTHONPATH=packages/engine/src .venv/bin/python \
    packages/engine/scripts/bench_rebuild.py --house houses/catlin --iters 20 --skip-macro
```

Drop `--skip-macro` to also time the two `move_nodes` commit paths (slower — it writes to
source and undoes, per iteration).

**Take the numbers on an idle machine.** Everything below has a 2–3× spread between an idle
laptop and a loaded one; a single run under load is not evidence of anything. Where a
measurement mattered, it was taken as an interleaved A/B — alternating baseline and candidate
in one process so drift hits both arms — not as two separate runs.

---

## Current measurements

`houses/catlin`, **154 resolved walls**, 5 storeys. Median of 20 rebuilds.

| stage | median ms |
|---|---|
| **full rebuild** | **242** (min 218) |
| ↳ `resolve` (all stages) | 191 |
| &nbsp;&nbsp;↳ `resolve.junctions` | 79 |
| &nbsp;&nbsp;↳ `resolve.placeables` | 27 |
| &nbsp;&nbsp;↳ `resolve.geometry` | 21 |
| &nbsp;&nbsp;↳ `resolve.mep` | 14 |
| &nbsp;&nbsp;↳ `resolve.framing` | 12 |
| &nbsp;&nbsp;↳ `resolve.construction` | 10 |
| ↳ `load_plan` | 71 |
| &nbsp;&nbsp;↳ `load_plan.import` | 64 |
| &nbsp;&nbsp;↳ `load_plan.lint_provenance` | 4.8 |
| &nbsp;&nbsp;↳ `load_plan.content_hash` | 1.8 |

`resolve` is now ~79% of a rebuild and `resolve.junctions` is ~41% of resolve. That is where
the next win is, and it is the polygon clipping in `topology.py`, not the stage around it.

### The two `move_nodes` commit paths

| path | median ms |
|---|---|
| slow path (source writeback + rebuild) | ~2200 |
| fast path (in-memory apply, async writeback) | ~610 |

**These two are the least trustworthy numbers in this file**, for two reasons. They were taken
on a loaded machine — a clean re-measure is worth doing before anyone acts on them. And the
fast path here is not the ~44 ms Phase 2b once recorded: that figure timed the in-memory apply
against a warm process, where `bench_rebuild` drives `apply_edit` → resolve → `_flush_writes`
→ undo per iteration, so it includes a full resolve and contends with the writeback thread.
Read them as *"the slow path is roughly 3.5× the fast path"*, not as absolute latencies, until
someone re-measures them deliberately.

---

## Read this before trusting any table in this file

This document was wrong for a long time, in a way that cost real work, and the reason is
worth stating plainly.

The five phases below were measured, shipped, and written up honestly **at the time**. Then
the house grew, the code around them changed, and nobody re-measured — because the document
said the problem was solved. By the time anyone did, the closing "Summary: ~44 ms" was off by
a factor of ~50, and the Phase-2a conclusion — *"the resolve pipeline is already sub-50 ms;
restructuring it would save <50 ms and is not worth prioritizing"* — had become exactly
backwards: `resolve` was 488 ms of a 533 ms rebuild, 91% of the cost.

That conclusion was **correct when written** (resolve really was ~31 ms) and it was **used as
a reason not to look** for months after it stopped being true. A perf document is a
measurement with an expiry date, not a fact.

Two things now guard against a repeat:

1. **`bench_rebuild.py --assert-under MS` / `--assert-stage-under STAGE=MS`** — budgets, with
   every breach printed, exiting non-zero.
2. **`packages/engine/tests/test_resolve_perf_guard.py`** — runs the above in the suite, with
   budgets set at roughly 2.5× the medians above. It is a tripwire for an order-of-magnitude
   regression, not a benchmark; the headroom is deliberate, because a flaky perf test gets
   deleted rather than fixed.

If you make something faster, **update the table above and the guard's budgets in the same
commit.** If you make something slower on purpose, say so there too.

---

## History — what was done, and what it was worth when it was done

The numbers in this section are **historical**. They were true when measured against the
then-current house and code. Do not read them as current; the table above is current.

### Phase 0 — the libcst source scan (shipped)

At build 12 a full rebuild was ~2100 ms, of which `load_plan.lint_provenance` was ~2053 ms —
98% of the cost. The dialect lint, the missing-uid scan and the provenance scan each parsed
every editable plan file separately, each building its own `MetadataWrapper` and resolving
`PositionProvider` (the expensive step).

- **Share the parse**: one `MetadataWrapper` per file, passed to all three scans. 2100 → ~977 ms.
- **Per-file scan cache** (`loader._SCAN_CACHE`): the scan result depends only on a file's
  exact bytes, so it is cached keyed by content SHA. The key *is* the content, so a stale
  entry cannot be served. A rebuild after a one-file edit re-scans one file and replays the
  rest. ~977 → ~50 ms idempotent, ~263 ms after a one-file edit.
- **Cached libcst parse** (`writeback.parse_cached`): libcst trees are immutable and
  `Module.visit` returns a fresh tree, so every read path can share one parsed tree per source
  string. Only the write path re-parses.

This work **held up**: `lint_provenance` is 4.8 ms today.

### Phase 1 — client quick wins (shipped)

Revision-deduped `reloadIfStale` (one in-flight `GET /model`, coalescing the mutation action
and the WS echo); `React.memo` on the plan shapes with stable uid-based callbacks; Panel3D
render-on-demand behind a coalesced dirty flag instead of an unconditional RAF loop; and a
revision-keyed `model_json()` cache in `state.py`.

⚠️ Two of these had **silently stopped working** and were repaired later — see *Phase 6* below.
A memoization that is never re-measured is a memoization that has probably lapsed.

### Phase 2a — caches that were measured and correctly skipped (at the time)

`resolve_assembly`, `PlanModel.by_tag`, `ResolvedModel.wall` and `content_hash` were profiled
and skipped: sub-millisecond each against a ~30 ms resolve. **This conclusion expired.** By
the time the house reached 154 walls, `PlanModel.by_tag` alone was 4,018 calls per resolve
driving 1,183,656 `all_elements` yields — the single hottest entry in the profile. It is now
an index (see Phase 5).

### Phase 2b — in-memory plan authority + async writeback (shipped)

`typehaus.source.inmemory` applies a macro's `PatchOp`s directly to the loaded `PlanModel`,
reusing the same `encode_value` → eval-in-dialect-namespace path the libcst writeback uses, so
there is one value encoding rather than two. `ProjectState.apply_edit()` takes this path when
`can_apply_in_memory()` says every op targets a known element/kind; it resolves + checks the
in-memory result, answers immediately, and queues the *same* ops on a background thread doing
the classic source writeback. Undo/redo and anything the fast path cannot handle fall back to
the slow path. Source stays ground truth throughout.

Two safety nets bound the risk of a dual mutation path:

- **Equivalence gate** (`test_inmemory_equivalence.py`) — the in-memory apply and the
  source-writeback-then-reload must produce byte-identical plans. This must stay green for the
  fast path to be trusted.
- **Reconciliation backstop** (`ProjectState._reconcile`) — after each queued writeback lands,
  the worker reloads from source, compares, and on divergence adopts source, logs loudly and
  notifies clients: an applicator bug becomes a flicker, not corruption.

⚠️ That backstop **raised `TypeError` when it fired** — `_reconcile` called
`_resolve_and_check` with two arguments against a three-argument signature. It was unreachable
from the suite precisely *because* the equivalence gate asserts divergence never happens.
Fixed, with a regression test that reproduces the exact `TypeError` against the old code. A
safety net nothing exercises is a safety net you do not have.

### Phase 3 — async checks (shipped)

Resolve returns as soon as `resolve()` lands; the check tiers are queued onto a single-slot
background thread. `checks_pending` surfaces the window in `model_json()`; when the job lands
it merges findings **in place without bumping the revision**, because checks landing should not
look like a new edit. A newer edit mid-check discards the in-flight result.

### Phase 4 — live drag preview (shipped)

`resolve_preview()` is a reduced resolve — junctions, openings, envelope, rooms — skipping the
stages a ghost overlay never renders. `POST /macro/preview` applies ops to the current
in-memory plan and runs it: no revision bump, no writeback, no checks, no undo entry. The
client fires it on `pointermove`, self-throttled to one in-flight request. Measured ~16 ms at
the time.

### Phase 5 — tag indices (shipped)

`PlanModel.by_tag`, `storey()` and `elements_of_kind()` are index-backed. `PlanModel` is a
frozen pydantic model and `with_elements` returns a new instance, so the index cannot go
stale — but it is keyed on the identity of `elements`, because `model_copy` carries an
instance-only cache onto the copy. That was **verified stale, then fixed**.

`ResolvedModel` gets a `_tag_index` built once at the true end of `resolve()`, after every
stage has finished mutating it — it is a *mutable* dataclass, so anything lazier risks
staleness. `resolve_preview`'s reduced model never gets an index built, so `by_tag`/`wall()`
fall back to the old linear scan; that path is explicitly tested.
`GeometryModel.by_uid` gets the same identity-keyed lazy cache.

Result: resolve 488 → 424 ms, rebuild 533 → 471 ms.

### Phase 6 — the resolve pipeline itself (shipped)

The phase Phase 2a said was not worth doing. Measured by interleaved A/B, 20 rounds, both arm
orders:

| stage | before | after |
|---|---|---|
| `resolve` | 350–377 ms | **216–220 ms** |
| `resolve.junctions` | 120–138 ms | **67–77 ms** |
| `resolve.placeables` | 72–77 ms | **21–22 ms** |

`topology.py`:
- `_polygon_component` short-circuits when there is exactly one candidate. `max(containing or
  candidates, …)` over a one-element list returns that element regardless, so the containment
  test was provably redundant — and instrumented, **792 of 792 calls per resolve** took that
  branch. This was the single largest win.
- `_normalized_ring` uses `shapely.get_coordinates(...).tolist()` (2.6 µs/ring vs 15) and a
  signed shoelace rather than `Polygon(points).exterior.is_ccw`; `component` is a valid polygon
  so its exterior is simple, where the two agree by definition. Verified equal over all 792
  rings before landing.
- The per-storey `{tag: Node}` map is built once per storey instead of once per wall — it was
  67k `element_kind` property reads per resolve.
- One `_with_layer_polygons` rebuild per clip pass replaces a per-layer tuple copy (quadratic).
- The final validity sweep is one batched `shapely.is_valid(list)` rather than
  `Polygon(...).is_valid` per ring, ~840 rings: 31.7 → 20.2 ms. Finding order preserved.

`placeables.py`: room polygons built once per storey rather than once per (room × placeable)
(~1,700 GEOS builds/resolve); footprint polygons built once per object and shared by both
conflict passes; the O(n²) peer filter keyed on `(storey, room)` — the only thing the predicate
read — making it O(rooms × objects).

`framing/profiles.py`: `cross_section` is `lru_cache`d. It is a pure function of one string,
called 15,160 times per resolve for a few dozen distinct profiles, driving 116k regex matches
underneath. `resolve.geometry` 33 → 21 ms.

**Rejected, with measurements** — recorded so nobody re-derives them:
- Memoizing `_through_envelope`: 69 calls/resolve, **69 distinct**, zero repeats. Pure overhead.
- `numpy.asarray(..., dtype=object)` for the batched `is_valid`: *slower* (22.9 vs 20.2 ms),
  and it would have added the engine's only direct numpy import.
- Inlining `unit`/`length`/`rect_between` in `geometry.py`: ~3 ms of ~190 ms, not worth the
  readability.
- `geometry_openings.opening_parts`: the "84 calls / 18 ms" that motivated looking at it was
  *profiled* time; real cost is ~1.9 ms.

**Also fixed here**: a `RuntimeWarning: invalid value encountered in oriented_envelope` that
fired on every load of `houses/catlin`. There is no NaN in our data — it is a false positive
generated inside GEOS 3.13, which emits it for *any* convex hull carrying an axis-parallel edge
(it takes an edge slope, so `dy/dx` is ±inf and `inf - inf` is NaN, setting the IEEE flag numpy
reports, while the returned rectangle is correct). The sole caller was `_short_axis`, which now
computes the minimum-area rectangle by rotating calipers instead. Minimum *area*, not minimum
*width* — the two agree for a rectangle and diverge for an L-shaped slab, and substituting one
for the other moved real sleeve bores.

### Phase 7 — client and bundle (shipped)

- **The dead whole-house glTF round-trip.** `Panel3D` fetched the entire house GLB on every
  model change and fully `GLTFLoader.parse()`d it — into a code path whose first statement
  bails, because `WHOLE_HOUSE_GLB_PRIMARY` is permanently `false` by decision. The fetch is now
  gated on the flag (the promotion path is intact, it just does not run), and `GET /model.glb`
  gained the revision-keyed cache `GET /model` already had. Verified over CDP: 2 model reloads
  went from 2 `/model.glb` fetches to **0**.
- **Restored memoization.** `Canvas2D` allocated a fresh `displayedOpenings` array per wall per
  render and handed it to a `memo()`'d `WallShape` with the default shallow comparator — so the
  reference miss was guaranteed and every wall re-rendered on hover, at O(walls × openings).
  Now a `useMemo`'d `Map<hostTag, Opening[]>`. Eight more plan layers gained `memo()`, and the
  inline arrow props feeding them gained `useCallback` — without which the new comparators
  would never hit.
- **Three.js churn.** A shared `standardMaterial()` / `makeSurfaceMesh()` factory replaced 16
  inline `MeshStandardMaterial` sites; `GLTFLoader` and its parsed results are cached per URL
  instead of constructed per placeable inside a loop.
- **`preserveView`** was keyed on `renderedModel.current === model`, always false after a
  reload (new identity from `JSON.parse`), so the camera re-framed on every edit. It is now
  keyed on the `EngineClient` identity — *not* on the revision or content hash, which change on
  exactly the edits the camera should survive.
- **Bundle**: `Panel3D` + `three/` and the seven readers are lazy; `manualChunks` splits three;
  `sourcemap` is behind `HAUS_SOURCEMAP=1`. Entry chunk **1,072 kB → 357 kB** (gzip 299 → 110),
  and a 3.98 MB `.js.map` is no longer deployed publicly.
  `manualChunks` alone was not enough — three 2D modules reached into `three/` for pure
  helpers, so the entry statically imported 12 three symbols and `index.html` modulepreloaded
  the 551 kB chunk anyway. Moving those helpers out is what actually cut it.

---

## Where the time goes now

Of a 242 ms rebuild: `resolve` 191 ms, `load_plan` 71 ms.

- **`resolve.junctions` (79 ms)** is the largest single stage and the obvious next target. It
  is polygon clipping in `topology.py`. A bbox shortcut in `_butt_branches`, to skip
  `difference` on layers that cannot overlap, was considered and **not** attempted: GEOS
  overlay may renormalize the ring, and that could not be proven neutral beyond one house.
  Anything done here must be gated on a full permit-set render, not just `model.json` — see
  below.
- **`load_plan.import` (64 ms)** is Python import cost for the house's plan modules. Largely
  fixed overhead.
- **`resolve.geometry` (21 ms)** is dominated by `geometry_members.member_box`, ~15,160 calls
  per resolve.

### A gate that is necessary but not sufficient

`model.json` byte-identity is the standing parity check, and it does cover more than it looks
like it does — `walls[].layers[].polygon` is serialized, so ring vertex order is in there.

It is still not the whole picture. The A-4xx transition details are cut from the resolved
geometry by `section.py::ring_cut_intervals`, and the permit set exercises paths `model_to_dict`
does not. For anything touching junction polygons, render the permit set and compare:

```
PYTHONPATH=packages/engine/src .venv/bin/python -m typehaus.cli.app build houses/catlin
pdftoppm -r 60 -png houses/catlin/out/permit_set.pdf <dir>/p
```

Render each set to its **own** directory and let it finish before comparing hashes. Comparing
against a directory another process is still writing produces a phantom diff — that happened
during this work and cost an hour of chasing a regression that did not exist.
