# Architecture — Repo, Pipeline, CLI, Risks

Cross-phase structure: everything here is built incrementally across M1–M3 but must be agreed
before WP1.1. Decisions referenced as `#N` (→ 01).

## Repo layout

Create at `~/Documents-NoCloud/house/type-haus/` (sibling of `catlin-house`).

```
type-haus/
├── pyproject.toml               # uv workspace root
├── LICENSE                      # MIT
├── README.md
├── plans/                       # THIS document set (00–50), the decision log, and TODO
├── packages/
│   └── engine/                  # PyPI package: typehaus (hatchling backend)
│       ├── pyproject.toml
│       ├── src/typehaus/
│       │   ├── _meta.py         # name/brand constants (→ 01 §Naming)
│       │   ├── quantities/      # Length, Angle, Pitch, Area, RValue, UFactor, Temperature
│       │   ├── model/           # Pydantic elements, assemblies, materials, types
│       │   ├── resolve/         # topology graph, junction solver, vertical stacking pass,
│       │   │                    #   room derivation, framing generator, stairs, roof planes
│       │   ├── source/          # plan loader, editable-dialect linter (libcst),
│       │   │                    #   provenance map, writeback engine, `haus fmt`
│       │   ├── emit/
│       │   │   ├── ifc/         # lowlevel.py (ported ifc_utils), walls, openings,
│       │   │   │                #   spaces, georef, framed-LOD, psets
│       │   │   ├── draw/        # 2D drawing IR + primitives (ported detail_utils)
│       │   │   ├── dxf/         # ezdxf writer: AIA layers, dimstyles, paperspace
│       │   │   └── pdf/         # matplotlib sheet renderer, title blocks
│       │   ├── sheets/          # sheet-set composer, sheet index, schedules
│       │   ├── checks/          # registry, integrity/, code/mn_residential/,
│       │   │                    #   structural/, building_science/ (M5), ids_export,
│       │   │                    #   pytest plugin
│       │   ├── diff/            # GlobalId + geometric matchers, report, diff.json
│       │   ├── server/          # FastAPI app, watchfiles, WebSocket events
│       │   └── cli/             # typer app (`haus …`)
│       └── tests/               # unit tests + golden IFC/DXF snapshots + fixtures
├── ui/                          # pnpm + Vite + React + TS (editor, 3D viewer)
├── houses/
│   ├── starter/                 # template used by `haus new`
│   └── catlin/                  # M3: the real house (plan/, params/, notes/, brief.md,
│                                #   preferences.toml)
├── library/                     # shared assemblies, materials, door/window types,
│                                #   transitions (Python modules)
├── .claude/
│   ├── CLAUDE.md → ../CLAUDE.md (or place at root)
│   └── skills/                  # add-room, add-assembly, import-review, permit-check,
│                                #   port-detail
├── .github/workflows/ci.yml     # ruff, mypy --strict, pytest, determinism check,
│                                #   ui typecheck+build, starter-house build smoke test
└── docs/                        # mkdocs-material: tutorial, schema ref, permit guide,
                                 #   RENAME.md, plan/ (this set)
```

Packaging: **uv** (workspace + env) with **hatchling** build backend. Python **≥3.11**.
UI distributed pre-built inside the wheel so `pip install typehaus && haus serve` works
without node.

## Git topology — app repo, active house, community

**Decision (#17): the active catlin house lives inside the app monorepo** (`houses/catlin/`).
Rationale: every engine PR builds the real house in CI — the strongest possible regression
test; it doubles as the canonical, non-toy example; and it keeps feature development honest
(nothing ships that the flagship house can't use).

- **Location-independence rule (the thing that makes this elegant):** the engine treats a
  house as *any directory* containing `plan/manifest.py` (+ `brief.md`, `preferences.toml`) —
  it must never assume the house sits inside the monorepo. In-repo and external houses are
  byte-identical in structure; `houses/` placement is a convenience, not a coupling.
- **`houses/starter/`** is the template `haus new` consumes. **External users:** `haus new`
  outside the monorepo scaffolds a **standalone git repo** — same layout, plus a
  `pyproject.toml` pinning `typehaus>=X,<Y` and a CI workflow stub (build + check on push).
  Their house = their repo, their privacy, their git history. In-repo houses build against
  workspace HEAD (that's the dogfood point); external houses pin releases and upgrade
  deliberately.
- **Contribution seam = `library/`, not `houses/`:** shareable content (assemblies, materials,
  door/window/fixture types, furniture symbols, transitions) is one self-contained module per
  item with a small metadata header — name, author, license, plus provenance fields per #31:
  `reviewed_by` (filled at PR merge) and `validation` (what the per-item CI actually proved:
  schema-valid, renders, R-value computes). A user "promotes" an item by moving it from their
  house's `plan/` locals into a PR against `library/`; CI validates each item in isolation
  (schema check + render smoke test: R-value computes, detail renders, symbol draws).
  **Houses are personal; library items are the community currency** — this is how "design
  furniture, PR it back" works without ever putting someone's house in the app repo.
- **Trust model — plan code is code:** `haus build` imports the plan package, so building a
  downloaded house or library item **executes its Python** (`params/*.py` especially) — the
  same trust decision as `pip install`. Mitigations, not sandboxing theater: (a) `library/`
  items accepted via PR review + per-item CI stay the *only* first-party distribution
  channel — the docs never suggest downloading random houses; (b) library items are
  declarative wherever possible (the `# haus: editable` dialect has no executable surface —
  the linter proves it), and any library item needing full Python is flagged in review;
  (c) `haus build --inspect` (cheap: dialect-only load path, §Pipeline below) parses editable
  files *without importing* `params/`, so a user can preview a foreign plan's declarative
  content before ever executing it; (d) README/docs state the trust model plainly. Full
  sandboxing (subprocess isolation, wasm) is out of scope — documented honestly rather than
  half-built.
- **Git-mergeable plans (branch two layouts, merge one):** plan files are the state, so
  textual merge conflicts are the failure mode when two branches touch the same storey file.
  Two-layer answer: (a) **the `haus fmt` canonical style is merge-friendly by construction**
  — exactly one element declaration per statement, one statement per line-block, stable
  ordering (grouped by kind, then tag) — so independent edits to *different* elements land in
  different hunks and vanilla git merges them; two branches *appending* walls still collide
  textually, which leads to (b) a **libcst-aware git merge driver** (`haus merge-file`,
  registered for `plan/**` via `.gitattributes`): parse base/ours/theirs, merge at the
  *element* level keyed on uid — both new uids are kept, same-uid-edited-differently becomes a
  per-field conflict report instead of a text splat. (a) ships with `haus fmt` (WP2.2);
  (b) is backlog after M3 — the uid scheme (→ 10 §Stable IDs) is what makes it a small tool
  rather than a research project, and until it ships the fmt convention keeps ordinary
  conflicts rare and readable.
- **Repo hygiene:** commit scoping (`engine:` / `ui:` / `haus(catlin):` / `library:`); CI
  path filters so house-only commits skip the full engine matrix; `houses/*/out/` gitignored.
- **Privacy — decided (#19):** the repo is public from day one, and the catlin house keeps its
  real site coordinates/address when it lands in M3 — building permits and county parcel GIS
  are already public record. No private-overlay mechanism is built.

## Transition kernel spike (WP0.1 — required before M1)

The main uncertainty is not IFC or the editor; it is whether one resolved model can express a
wall field, floor/roof/foundation interface, and layer/control continuity without a special-case
drawing. Prove that in a small, disposable spike before committing to the general schema.

- **Inputs:** parameterized fixtures distilled from `roof_wall_eave_detail.py` and
  `basement_to_framed_wall_detail.py`, plus a three-storey 2x6 → 2x4 → 2x4 width-change
  fixture. Preserve the meaningful conditions: sloped roof bearing/foam interface,
  rainscreen/vent path, wall-to-foundation waterproofing and CI, sill/rim, and the
  sheathing-plane datum.
- **Kernel:** resolve layer faces into named `AssemblyInterface`s; derive a
  `VerticalInterface`; apply an explicit pre-resolve `ConstructionRule`; then bind a
  post-resolve `Transition` overlay. Render one vertical slice and emit a machine-readable
  interface/continuity report. No UI, IFC, generic junction matrix, or permit sheets belong
  in this spike.
- **Exit gate:** each fixture changes exterior-CI and lining thickness without hand-moving an
  overlay; all anchors still resolve; members/takeoff change only when their construction rule
  requires it; the report either proves declared AIR/WATER/THERMAL continuity or names an
  intentional gap. If this fails, revise the interface/rule model before WP1.1.

WP0.1 code may be promoted into M1 only after the gate; its fixtures and golden images become
permanent M1 regression tests.

## Compiler pipeline

```
plan source ──parse────► PlanModel      (Pydantic; authored units preserved)
            ──validate─► cross-element  (refs resolve, tags unique, dialect lint)
            ──resolve──► ResolvedModel  (IR: junction-solved wall polygons, wall-line stacks,
            │                            derived rooms, framing members, stair/roof geometry,
            │                            derived boundary conditions, SI coords,
            │                            provenance map tag → file:line)
            ──emit─────► IFC │ glTF (render artifact, #51) │ DXF │ PDF sheets │
                         model.json (UI) │ diff baseline
```

- **`ResolvedModel` is whole-building, not per-storey.** Each storey resolves in the shared
  project-north plan frame; storeys are then placed at **derived elevations** (the
  FloorSystem deck depth feeds each storey's elevation delta, → 11 §Floors) into one
  building-frame model. This is a stated requirement, not an implementation detail: building
  **sections and details cut across storeys** (→ 11b §Slices), and the **vertical stacking
  pass (#43)** runs between adjacent storeys after the per-storey junction solves (→ 11
  §Vertical stacking). Nothing downstream may assume a storey resolves in isolation.
- **Two load paths, one truth:** `haus build` imports the plan package normally (fast; runs
  parametric modules). The **provenance/writeback path** parses editable files with libcst
  into `{tag → (file, CST node span)}`. A consistency check asserts both views agree.
- **Determinism:** uuid5 GUIDs (→ 10 §Stable IDs); sorted canonical iteration; IFC
  OwnerHistory/timestamps pinned via build config (SOURCE_DATE_EPOCH-style). CI golden test:
  two consecutive builds are **byte-identical**.
- **No incremental compilation in M1/M2** — a house resolves in low seconds; add per-storey
  caching only if profiling demands.
- **LOD flag — reinterpreted under #20:** framing **always resolves** (it's a core pipeline
  stage, → 11 §Framing solver, feeding floorplan cuts, the UI, and takeoffs regardless of
  flags); `--lod` selects only what is *emitted to the IFC file*:
  - `--lod framed` (default; what the UI 3D panel and Bonsai load): parent walls **plus**
    generated studs/plates/joists/layer solids (`IfcMember`/`IfcCovering`) aggregated under
    the wall via `IfcRelAggregates` — the signature visible-framing view.
  - `--lod core` (the architect-handoff artifact; what `--handoff` bundles): one `IfcWall` per
    wall with `IfcMaterialLayerSetUsage` + shared `IfcWallType` per assembly — what Revit
    digests cleanly. **Parent GUIDs identical across LODs** so diff stays stable.
- **Project north vs. true north (never tilt the canvas):** all authoring — plan source, the
  UI canvas, floor-plan sheets, dimensions — happens in **project-north coordinates**, an
  orthogonal local frame where the house's walls are axis-aligned. `true_north` is a single
  `Angle` on `Site` recording how project north deviates from true north; it is consumed
  *only* by the georef emit (`IfcMapConversion` rotation), the sun indicator (→ 30), the north
  arrow, and the M3 basemap import (which rotates *imported* parcel geometry into the project
  frame — the house never rotates). Users draw orthogonal walls on an orthogonal grid, always.
- IFC schema choice, IfcOpenShell pinning, and emitter details: (→ 12 §IFC emission).

## CLI

**Typer** (type-hint-native, matches the pydantic/mypy-strict house style; rich help).

```
haus new <name>       scaffold from template (generates project_uuid); interim template is
                       houses/starter — flips to catlin verbatim after WP3.1 (#22:
                       --template catlin|minimal, catlin default)
haus build             [--lod core|framed] [--only ifc|dxf|pdf|json] [--inspect]
                       # --inspect: parse-only, never imports params/ (§Git topology trust model)
haus check             [--profile mn-2024] [--tier integrity|code|structural|building_science]
                       [--json] [--ifc]
haus print             [--handoff] full permit set → out/permit_set.pdf + DXFs
                       (+ architect bundle, → 30 §Sheets)
haus diff <file.ifc>   semantic diff vs rebuilt baseline (→ 20 §Diff)
haus serve             [--port] FastAPI + UI + file watching
haus fmt               normalize editable plan files through the libcst printer; assigns
                       missing uids (→ 10 §Stable IDs)
haus takeoff           [--json] framing counts + material areas (#25); shows $ ranges iff
                       prices.toml exists (#28)
haus energy            [--json] block heating/cooling load estimate (#42, M5, → 50)
haus migrate           [--dry-run] apply the format_version source migration (#31); requires
                       clean git tree, validates with a full build
haus compare <a> <b>   resolve two members of a variant set for the side-by-side compare
                       view (→ 11b §Fork); given assembly names, renders the assembly delta
                       compare card instead (#53, → 21b)
haus variants list     the house's declared variants (variants.toml: assembly swaps + layer
                       thickness overrides on one base plan, → 21b §Variant compare)
haus variants compare <a> <b>
                       build two declared variants → element, framing-takeoff, R-value and
                       check deltas → out/compare.json
haus variants assemblies <asm-a> <asm-b> [<asm-c>]
                       the assembly delta compare row (#53): R / thickness / layers /
                       framing / STC, no build required
haus import furniture <file.glb|.gltf|.dae>
                       trimesh-based mesh import → FurnitureType with derived footprint +
                       height (#49, M3, → 30 WP3.10)
haus render            [--view plan|section|3d] [--storey N] [--out png|svg] headless
                       snapshots for agent visual feedback (#52): plan/section from the
                       drawing IR, 3d offscreen from the glTF render artifact (#51)
haus ls / explain <tag|assembly>
                       element inspection for humans and agents; ls --summary emits the
                       compact whole-plan digest (#52); explain --bearing walks the
                       derived load path (→ 11 §Foundations); explain --transitions lists
                       derived boundary conditions + coverage (→ 11b §Transitions);
                       explain <assembly> --card renders the assembly section card
                       (→ 12 §Assembly card)
```

## Migration from catlin-house (port vs. rewrite)

| Old module (`catlin-house/`) | Disposition |
|---|---|
| `ifcplot/units.py` | Rewritten as `quantities/` (constants kept: `M_PER_FT`, `M_PER_IN`) |
| `ifcplot/ifc_utils.py` | **Ported ~80%** → `emit/ifc/lowlevel.py` (typed, 0.8 module API); wall builder rewritten polygonal (WP1.7) |
| `ifcplot/assemblies.py` + `detail_utils` assembly classes | Unified into new `Assembly`; presets → `library/` (WP1.3) |
| `ifcplot/detail_utils.py` drawing primitives | **Ported mechanically** to drawing IR (same math); also powers the assembly section card (→ 12) |
| Root detail scripts (`roof_wall_eave_detail.py`, `sauna_basement_wall_detail.py`, `basement_to_framed_wall_detail.py`, …) | **Reauthored** as detail `Slice`s + `library/` `Transition` recipes (WP3.2) |
| `ifcplot/catlin_house.py` (3,445 lines) | **Not ported** — reauthored declaratively in M3; arch/sunken-garden math → `params/` (WP3.1) |
| `tests/test_catlin_house_ifc.py` | Style generalized into integrity checks + golden tests; specifics → WP3.7 |
| `notes/*.md` | Copied; convention formalized into `Slice`/`Transition` binding (→ 11b) |

## Risk register

Each risk is owned by the phase doc that builds its mitigation; that doc must state the
mitigating design pattern concretely.

| # | Risk | Mitigation (pattern) | Owner |
|---|---|---|---|
| 1 | **libcst writeback complexity** (the novel part) | Strict editable dialect keeps the CST surface tiny; property-based round-trip tests; `haus fmt` normalizer; worst-case degradation = regenerate one element's statement (losing only that statement's comments) | → 20 |
| 2 | **Junction/topology solver math** (mitered multi-layer corners, T-junction layer priorities) | Lean on shapely; enumerate junction cases as a golden test matrix in M1; ship "structure-butts, finish-wraps" defaults via `JunctionPolicy`, refine per-assembly later | → 11 |
| 3 | **Permit-quality elevations/sections** (hidden-line projection is the hardest 2D output) | Scheduled last (M3); reuse `ifcopenshell.draw` prior art; painter's-order silhouette is acceptable for residential; plans/details/schedules carry most submittal value regardless | → 30 |
| 4 | **ThatOpen/web-ifc churn** (young ecosystem) | **Largely retired by #51:** the primary render path is now **glTF emitted from `ResolvedModel`**, rendered with plain three.js — self-owned end-to-end, no in-browser IFC parsing in the hot path (IFC stays the interchange artifact, glb is the render artifact; same emitter WP4.1(b) wants). Viewer still isolated behind a `ModelViewer` interface; web-ifc/ThatOpen loading of the built IFC is the secondary path (and an emitter cross-check); "open in Bonsai" the final fallback (UI fully usable 2D-only) | → 21 |
| 5 | **IfcOpenShell API instability** (0.7→0.8 reshape already bit the ecosystem) | Pin 0.8.x; all calls confined to `emit/ifc/lowlevel.py` (~600-line adapter, exactly what `ifc_utils.py` proved out); golden IFC snapshots detect drift on any bump | → 12 |
| 6 | **Framing solver in the hot path** (#20 makes it run on every build and edit — correctness *and* latency now gate the core loop) | Closed-form arithmetic, no geometry kernel: members are records until emit; CI asserts the < 200 ms whole-house budget from WP1.4b onward; the golden junction/opening test matrix covers the rule combinatorics; the 2D cut + UI consume the same member list as the IFC emit, so there is exactly one solver to get right | → 11 |
| 7 | **Overlay/transition anchor robustness** (details must re-flow, not drift, when assemblies change) | Anchors reuse the dimension reference scheme (uid + face role) — one resolver, one failure surface; an unresolvable anchor is an error finding, never a silently wrong drawing; golden-image tests re-render every `library/` transition across assembly parameter sweeps (CI thickness bumps, layer swaps, lining overrides) | → 11b, → 30 |
| 8 | **Transition-coverage noise** (a strict coverage check could nag early-stage mess into unusability) | Coverage findings are warn-tier during design and only hard-gate in `/permit-check`; wildcard condition patterns let one library transition cover whole assembly families, keeping the distinct-condition count low | → 11b |

## Verification strategy (per milestone, end-to-end)

- **Always-on CI gates:** ruff, `mypy --strict`, pytest, build-determinism (two builds
  byte-identical), starter-house build smoke test, UI typecheck + build.
- **M1:** open the built demo IFC in Blender/Bonsai — verify walls/corners/openings/spaces
  visually; run `ifctester` against the baseline IDS; run the broken-fixture suite; render the
  assembly section card for every library assembly.
- **M2:** scripted UI session (Playwright): draw walls → close loop → place window → claim
  room; assert plan-file diff is minimal and comments survive; edit the file in a text editor
  and assert UI hot-reload; modify a copy of the IFC in Blender, run `haus diff`, assert the
  change report; repeat the drawing script in a touch-emulated tablet viewport (#14).
  **Cold-start gate (time-to-first-delight):** on a clean machine without node,
  `pip install typehaus && haus new && haus serve` reaches a navigable Nordic-preset 3D view
  of the starter house — a complete, attractive small house, not an empty canvas — within a
  minutes-scale budget; the first UI edit round-trips < 2 s. The experimenter's first 20
  minutes are an acceptance surface, not a hope.
- **M3:** WP3.7 equivalence test vs old catlin model; print the permit set and review each
  sheet against the encoded MN checklist; verify DXF opens correctly in a second CAD tool
  (e.g. LibreCAD or an online viewer) with correct layers/units; **handoff-quality bar
  (→ 00 §Success, #48):** import the `--handoff` IFC into **Bonsai (Blender)** — the tested
  target — and verify walls arrive as typed layered walls with spaces and schedules
  populated — i.e. an architect could continue the model rather than redraw it. (Revit/
  Archicad import stays untested-aspirational; `--lod core` is shaped for it regardless.)
