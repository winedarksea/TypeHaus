> **SUPERSEDED (2026-07-17):** this plan has been reviewed, amended (decision #43 vertical
> stacking; early assembly section card), and split into the document set at
> `~/Documents-NoCloud/TypeHaus/plans/` (start at `00-overview.md`).

# Type:Haus — Residential "House as Code" Platform: Architecture & Implementation Plan

## 1. Context

**Why:** The existing `catlin-house` repo (`~/Documents-NoCloud/house/catlin-house`) proved the concept:
a residential house defined in Python, compiled to an IFC4 model via IfcOpenShell (viewed in
Blender + Bonsai), with matplotlib wall-section details driven by parameters stored in IFC property
sets. But it has hit its architectural ceiling: the house is one 3,445-line imperative function
(`ifcplot/catlin_house.py`) over flat scalar dataclasses; there are no first-class Wall/Room/Opening
types; assembly layer definitions are duplicated between `assemblies.py` (3D) and `detail_utils.py`
(2D); there are no windows, no `IfcOpeningElement`, no `IfcSpace`, no georeferencing, no DXF, no PDF,
no UI, and no agent scaffolding.

**The product vision**: an open-source
"infrastructure as code, but the infrastructure is a residential house" tool. Software developers (and adjacent users) author a house plan as typed,
declarative code; get a 3D IFC model; edit the 2D floorplan in a local web UI on one screen while
Claude Code edits the same plan source in VSCode on the other; users can then export their vision for an architect to load and polish in their own software, and for more ambitious, experience users, be able to complete a permit-ready set of plans straight from this program.

**What success looks like:** Type:Haus helps a capable person turn a house idea into a coherent,
inspectable residential design, then offers two exit ramps — both first-class:

1. **Refine in place:** disciplined checks (integrity / code / structural), professional inputs,
   and agentic iteration carry the design all the way to a permit-ready set.
2. **Hand off, preserving the work:** an architect/engineer imports the model and is *genuinely
   accelerated* — the IFC carries typed layered walls, real spaces, openings with schedules,
   georeferencing, and standard psets; the DXF follows AIA layer conventions. The user's "sketch"
   is something a professional builds on directly, not a napkin they redraw. Handoff quality is a
   **tested property** (§15 M3 verification), and `haus print --handoff` produces the
   "give this to your architect" bundle (§7.2). A semantic diff + agentic merge (§10) brings the
   professional's revisions back in.

**Non-goals:** commercial buildings, multi-family beyond duplex-scale, full CAD generality,
cloud/collaboration service (git is the collaboration layer), replacing the architect/engineer of
record.

---

## 2. Locked Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Source of truth | Typed declarative Python model (Pydantic v2, frozen, `mypy --strict`). IFC/DXF/PDF are compiled, always-regenerable build artifacts. "Terraform for houses." |
| 2 | Engine language | Python (IfcOpenShell + ezdxf are Python-native). Rust deferred (possible future validator/diff crate). |
| 3 | UI | Local web app: React/TypeScript 2D floorplan editor (SVG) + embedded 3D IFC viewer (ThatOpen/web-ifc), served by a local FastAPI server that watches plan files and rebuilds. Blender/Bonsai remains the power-user 3D path. |
| 4 | Architect round-trip | Semantic diff (`haus diff`) keyed on stable element IDs → GlobalIds, plus agentic merge via a Claude skill. No CRDT (architect tools rewrite files wholesale; CRDTs can't see those edits). |
| 5 | Repo | **Fresh monorepo** (engine + ui + houses + agent scaffolding). `catlin-house` stays untouched as reference until M3 migration completes, then archived. |
| 6 | UI↔code seam | Plan files are a constrained declarative Python subset parsed AND re-emitted via **libcst** (comments/formatting preserved). Full-Python parametric modules are separate; the UI renders their output read-only. |
| 7 | Milestones | **M1** = typed schema + proof-of-life compiler. **M2** = barebones complete product (CLI + UI editing loop + IFC/DXF out) — UI required because the catlin floorplans will be designed in it. **M3** = catlin house ported + permit-ready MN set. |
| 8 | Checks | All three tiers scaffolded from the start: (a) **model integrity — the main focus** (wall loop closure, no unconfigured segments, openings fit, assemblies resolve, IDS/ifctester), (b) residential code (generic **MN State Building Code** profile: MN Rules 1309, current edition — **2021 IRC base** — with profiles versioned as `mn-2024`, `mn-2020`, … so editions swap cleanly; start with a few high-value rules e.g. egress, door widths), (c) structural sizing (start with catlin-relevant items: 18-ft-span I-joists, headers). |
| 9 | Name | **`Type:Haus`** — PyPI package `typehaus` (verified 404, as were `sillplate`, `ridgeline`), domain `type-haus.com`, CLI binary `haus`. |
| 10 | Jurisdiction | Generic MN state code (no city-specific submittal profile yet). |
| 11 | Georeferencing | Site model (lat/long, EPSG CRS, true north → `IfcMapConversion`) in **M1**; parcel/basemap import + rendering in **M3** (with the site-plan sheet). |
| 12 | Units | Canonical SI (meters/radians) internally; authored + displayed in the user's units (imperial for US market first; the quantity types preserve authored units through round-trips). |
| 13 | License / owner | MIT. Colin Catlin <colin.catlin@gmail.com>. |
| 14 | UI form factor | **Touch-first, tablet-class and up** (iPad-landscape minimum); not smartphone-focused. Hover/keyboard are desktop accelerators only, never required. |
| 15 | Offline / PWA | `EngineClient` boundary in the UI from day one (§9); pyodide-powered fully-offline PWA is a **stretch M4** behind an explicit wasm-feasibility gate — skipped if the wasm-hostile deps (IfcOpenShell, libcst) can't be made viable. |
| 16 | Element identity | Every authored element carries an **immutable `uid`, generated once and retained in source**. IFC GlobalId is derived from `uid` — never from position/path — so retags and storey moves preserve round-trip continuity (§5.2). |
| 17 | Repo topology | The active catlin house lives **inside the app monorepo** (dogfood + canonical example + CI integration gate); `haus new` scaffolds standalone pinned repos for everyone else; `library/` is the community contribution seam (§4.1). |
| 18 | Design brief | Every house carries a `brief.md` (spatial program, budget, climate, style, accessibility, phasing, must-haves, dislikes, priorities) — scaffolded by `haus new`, read by Claude before proposing designs, included in the architect handoff bundle (§11). |
| 19 | Open development | Repo is **public on GitHub from day one** (README flags pre-alpha); the catlin house keeps its **real site coordinates** in-repo when it lands in M3 — permit and county-parcel data are already public record, so no overlay mechanism is built. |
| 20 | Framing = signature | **The framing solver runs in the core resolve pipeline** (not a build-time LOD extra). True per-member platform framing — studs, plates, headers, king/jack/cripples, corner conditions, floor-to-floor stud stacking — is the visual identity of the product: floorplans cut through real framing + full assembly layers (insulation hatch, sheathing, drywall — never gray-box walls) and the 3D view always shows it. `--lod` now selects only what is *emitted to IFC* (§6); `core` remains the architect-handoff artifact. |
| 21 | Horizontal layers | **Two-tier floor model** (§5.7): per-storey `FloorSystem` (structural deck — joists spanning bearing walls, subfloor, ceiling-below) owning first-class `FloorOpening`s shared by the Stair and both adjacent storeys; a per-room **finish tier** (`FloorFinish` derived from Room faces, with in-room override zones) drives material takeoffs. |
| 22 | Template | `haus new` scaffolds from the **catlin house verbatim** once it lands (it's where the polish investment goes); until WP3.1 the minimal `houses/starter/` is the interim template. Long-term both ship: `haus new --template catlin\|minimal`, catlin default. |
| 23 | Masonry depth | CMU + ICF supported at first pass as **layered solids + computed unit quantities** (block/form counts, rebar length from coursing rules via `MasonrySpec`) — per-member placed geometry stays wood-framing-only. |
| 24 | Presentation preset | A built-in **"Nordic" presentation preset** — one centralized muted material palette shared by the 3D viewer, the SVG editor, and 2D detail hatches — plus edge/outline rendering and SSAO in the 3D panel, is the **default** view: pretty out of the box, zero user work (§9.2). |
| 25 | Takeoffs | The catlin-house quantity feature is kept and promoted: **framing member counts and per-material areas** (insulation panels, carpet, drywall, sheathing…) are first-class outputs — a UI dashboard (§9.1 #7), a BOM/takeoff sheet in the permit set, and `haus takeoff --json`. |
| 26 | Driven dimensions | **Editable dimensions without a constraint solver** (M2, §9.3): click a dimension, type a new value, the engine moves the less-anchored side as one ordinary `move_nodes` op (undoable, journaled). A per-node **anchor pin** is the only persistent "constraint". No constraint graph, no solver in the hot path, no over-constrained failure mode. |
| 27 | Foundations early | `FoundationWall`/`Footing`/`Pad`/`Post`/`Beam` are **real M1 schema elements** (promoted out of §5.6 headroom — catlin's basement + ICF garage need them in M3 regardless); foundation-plan and roof-plan **sheets** land in M3. Bearing/load-path stays a **derived view** over what the framing solver already knows, not an authored graph. |
| 28 | Costs | **Quantities are the product; dollars are opt-in and user-supplied.** If `prices.toml` exists (the user's own $/unit numbers), `haus takeoff` multiplies through and shows low/high ranges. No built-in price data, ever — no prices provided → no dollars shown. |
| 29 | Roof designer | Dedicated **roof designer panel in M3** (stair-designer pattern): pitch/ridge/bearing refs with live section preview. With it: **roof planes can define room ceilings** (habitable attic), the **R305 sloped-ceiling check** (avg 7' over area counted at ≥ 5'), zero-overhang eave support (catlin's metal-roof-onto-siding detail), and the roof plan sheet. |
| 30 | Write safety | Writes go through a **project-wide mutation coordinator** (§9): a patch may span several source files, so the transaction unit is the project, not the file — revision hash over *all* source inputs as the precondition, ops applied to a staged in-memory tree, the whole staged project parsed + validated, then per-file atomic replaces (hashes rechecked immediately before each — editors don't honor advisory locks), journal entry recorded only after every file lands, watcher rebuilds suppressed until the commit event. A stale-source **conflict banner** in the UI replaces silent last-write-wins. CRDT re-rejected (decision #4 stands). |
| 31 | Versioning | `manifest.py` declares `format_version` + `requires_engine` (a compatible range); the engine refuses builds outside the range and ships **tested source migrations** for format bumps. Library items carry provenance metadata (author, license, reviewed-by, validation status). A `library.lock` waits until the library is distributed separately from the engine — today the engine pin covers it. |
| 32 | Code-check honesty | A code profile ships with **citations, effective date, amendment history vs. its IRC base, per-rule test fixtures, and a declared coverage statement**. Rule results are **tri-state — PASS / FAIL / UNKNOWN(reason)** — a rule that can't evaluate (missing data, unsupported geometry) reports UNKNOWN, counted separately everywhere, never as a pass. Output wording is constrained: "N pass, F fail, U not evaluable, of M encoded rules (a declared subset of the code)" — **never** "code compliant". |
| 33 | Mutation contract | Every topology-changing op (split/join/trim, macros) returns a **`MutationResult` with an explicit uid remap** (§9.3): deterministic survivor rules, every referencing subsystem processes the remap through the element registry, and **undo restores the exact original uids** from the journal — never merely equivalent geometry. Identity continuity through edits is what decisions #16 and #4 were bought for; this is its enforcement mechanism. |
| 34 | Two-tier walls | **Wall assembly = core (structure + envelope); interior finish = a room-owned lining tier** mirroring the two-tier floor model (#21): every wall face bounding a Room resolves its lining from the assembly's `default_lining` unless the Room overrides it. The sauna liner is authored once on the room and lands on every bounding wall — exterior and partitions, asymmetric per side (§5.10). |
| 35 | Assembly variants | **Derived assemblies:** `variant_of` + layer-span substitutions that resolve live against the base — unchanged layers track the base forever (bump the exterior CI once; brick-clad and standing-seam sections both follow). Applying a variant to part of a run auto-splits the wall; the resulting assembly-change node becomes a derived boundary condition (§5.10, §5.12). |
| 36 | Slices | **One first-class `Slice` view mechanism** for floorplans, building sections, and details: cut plane + crop + scale over the resolved model, a 2D-only anchored overlay layer for build-science content (flashing, sealant, screens — never modeled in 3D), thin-layer exaggeration with true-dimension labels, and **shared annotations placed per view** (§5.11). |
| 37 | Transitions | **Boundary conditions are derived and enumerable; `Transition` bindings ("bridge details") cover them.** Wall↔roof, wall↔foundation, opening perimeters, and assembly-change nodes each resolve to a condition key (junction kind + participating assemblies). A Transition binds a condition pattern to an anchored overlay recipe, notes, and optional solver directives (web stiffeners, beveled plates). Unbound conditions are warn findings; `/permit-check` requires coverage (§5.12). |
| 38 | Fork/compare | **In-plan variants, not git-in-git:** duplicate an assembly or storey file with `variant_of` provenance + fresh uids (`forked_from` retained per element); exactly one active member per variant set builds; inactive variants still resolve to feed the side-by-side compare view; **promote remaps uids back to the originals** (#33 machinery) so identity continuity survives (§5.13). |
| 39 | Floor heat | **Zone-level `FloorHeat` element** (polygon/room ref, electric \| hydronic, spacing, embed depth, stat/sensor positions) on the Slab/FloorSystem: schematic serpentine on plans, wire dots in slab slices, wire-length/mat-area takeoffs, fixture keep-out warnings. No routing solver (§5.7). |
| 40 | Soffits | **`Soffit` is a storey-level element** whose polygon may span rooms (the hallway duct drop), with optional `FramingSpec` so drop framing is solver-generated — framed in 3D, dashed-overhead on plans, counted in the BOM; ceiling-height checks evaluate per overlapped room (§5.7). |
| 41 | Building-science schema | **M1 carries the scalars a Glaser-method / block-load / WWR toolset needs**, at near-zero cost: a `Temperature` quantity type; `Material.perm_rating/density/specific_heat`; `WindowType`/`DoorType.shgc/vt`; `Site.design_temp_heating/design_temp_cooling`; `Room.occupancy` promoted to a closed Enum (already needed for R310 egress applicability); Room's already-derived clear-face polygon asserted zero-gap against bounding walls for future energy-modeling exporters. Embodied carbon deliberately gets **no** Material field — it follows the costs precedent (#28) instead (§5.14). |
| 42 | Building-science tools | **Three physics-grounded tools land in a new, dedicated M5 milestone** (after M4 — genuinely last): a Glaser-method condensation-risk check (plots on A-401), a window-to-wall-ratio analyzer (per façade, via `true_north`), and a block heating/cooling load estimator (`haus energy`). All three read the already-resolved model — no new authored elements, no UI editing surface. Condensation risk + WWR live in a new `checks/building_science/` tier, physics-grounded like `checks/structural/` (§5.14, §8). |

---

## 3. Naming & Rename-Ease Strategy

The name may change. Contain it:

- **One import root:** all Python code lives under `packages/engine/src/typehaus/`. No sub-package
  embeds the brand (they're `typehaus.model`, `typehaus.emit`, …). A rename = rename one directory +
  one `pyproject.toml` `name` + find/replace `typehaus` imports.
- **CLI is `haus`**, not `typehaus` — user muscle memory survives a rename.
- **Brand strings centralized:** `typehaus/_meta.py` exposes `PROJECT_NAME`, `PROJECT_URL`,
  `IFC_APP_NAME` (used in IFC headers, pset prefixes `Pset_HF_*` → keep the pset prefix short and
  brand-agnostic: use `Pset_HF_Source` but define the prefix as a constant in `_meta.py`).
- **UI:** brand only in one `branding.ts` constant file.
- Include a `docs/RENAME.md` checklist (pyproject name, src dir, npm package name, GitHub repo,
  docs site, `_meta.py`, `branding.ts`).

---

## 4. New Repo Layout

Create at `~/Documents-NoCloud/house/type-haus/` (sibling of `catlin-house`).

```
type-haus/
├── pyproject.toml               # uv workspace root
├── ARCHITECTURE.md              # this document
├── LICENSE                      # MIT
├── README.md
├── packages/
│   └── engine/                  # PyPI package: typehaus (hatchling backend)
│       ├── pyproject.toml
│       ├── src/typehaus/
│       │   ├── _meta.py         # name/brand constants (§3)
│       │   ├── quantities/      # Length, Angle, Pitch, Area, RValue, UFactor
│       │   ├── model/           # Pydantic elements, assemblies, materials, types
│       │   ├── resolve/         # topology graph, junction solver, room derivation,
│       │   │                    #   framing generator, stairs, roof planes
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
│       │   │                    #   structural/, ids_export, pytest plugin
│       │   ├── diff/            # GlobalId + geometric matchers, report, diff.json
│       │   ├── server/          # FastAPI app, watchfiles, WebSocket events
│       │   └── cli/             # typer app (`haus …`)
│       └── tests/               # unit tests + golden IFC/DXF snapshots + fixtures
├── ui/                          # pnpm + Vite + React + TS (editor, 3D viewer)
├── houses/
│   ├── starter/                 # template used by `haus new`
│   └── catlin/                  # M3: the real house (plan/, params/, notes/, brief.md, preferences.toml)
├── library/                     # shared assemblies, materials, door/window types (Python modules)
├── .claude/
│   ├── CLAUDE.md → ../CLAUDE.md (or place at root)
│   └── skills/                  # add-room, add-assembly, import-review, permit-check, port-detail
├── .github/workflows/ci.yml     # ruff, mypy --strict, pytest, determinism check,
│                                #   ui typecheck+build, starter-house build smoke test
└── docs/                        # mkdocs-material: tutorial, schema ref, permit guide, RENAME.md
```

Packaging: **uv** (workspace + env) with **hatchling** build backend. Python **≥3.11**.
UI distributed pre-built inside the wheel so `pip install typehaus && haus serve` works without node.

### 4.1 Git topology — app repo, active house, community

**Decision: the active catlin house lives inside the app monorepo** (`houses/catlin/`).
Rationale: every engine PR builds the real house in CI — the strongest possible regression test;
it doubles as the canonical, non-toy example; and it keeps feature development honest (nothing
ships that the flagship house can't use).

- **Location-independence rule (the thing that makes this elegant):** the engine treats a house
  as *any directory* containing `plan/manifest.py` (+ `brief.md`, `preferences.toml`) — it must
  never assume the house sits inside the monorepo. In-repo and external houses are byte-identical
  in structure; `houses/` placement is a convenience, not a coupling.
- **`houses/starter/`** is the template `haus new` consumes. **External users:** `haus new`
  outside the monorepo scaffolds a **standalone git repo** — same layout, plus a `pyproject.toml`
  pinning `typehaus>=X,<Y` and a CI workflow stub (build + check on push). Their house = their
  repo, their privacy, their git history. In-repo houses build against workspace HEAD (that's the
  dogfood point); external houses pin releases and upgrade deliberately.
- **Contribution seam = `library/`, not `houses/`:** shareable content (assemblies, materials,
  door/window/fixture types, furniture symbols, details) is one self-contained module per item
  with a small metadata header — name, author, license, plus provenance fields per decision #31:
  `reviewed_by` (filled at PR merge) and `validation` (what the per-item CI actually proved:
  schema-valid, renders, R-value computes). A user "promotes" an item by moving it
  from their house's `plan/` locals into a PR against `library/`; CI validates each item in
  isolation (schema check + render smoke test: R-value computes, detail renders, symbol draws).
  **Houses are personal; library items are the community currency** — this is how "design
  furniture, PR it back" works without ever putting someone's house in the app repo.
- **Trust model — plan code is code:** `haus build` imports the plan package, so building a
  downloaded house or library item **executes its Python** (`params/*.py` especially) — the same
  trust decision as `pip install`. Mitigations, not sandboxing theater: (a) `library/` items
  accepted via PR review + per-item CI stay the *only* first-party distribution channel — the
  docs never suggest downloading random houses; (b) library items are declarative wherever
  possible (the `# haus: editable` dialect has no executable surface — the linter proves it),
  and any library item needing full Python is flagged in review; (c) `haus build --inspect`
  (cheap: dialect-only load path, §6) parses editable files *without importing* `params/`, so a
  user can preview a foreign plan's declarative content before ever executing it; (d) README/docs
  state the trust model plainly. Full sandboxing (subprocess isolation, wasm) is out of scope —
  documented honestly rather than half-built.
- **Git-mergeable plans (branch two layouts, merge one):** plan files are the state, so textual
  merge conflicts are the failure mode when two branches touch the same storey file. Two-layer
  answer: (a) **the `haus fmt` canonical style is merge-friendly by construction** — exactly one
  element declaration per statement, one statement per line-block, stable ordering (grouped by
  kind, then tag) — so independent edits to *different* elements land in different hunks and
  vanilla git merges them; two branches *appending* walls still collide textually, which leads
  to (b) a **libcst-aware git merge driver** (`haus merge-file`, registered for `plan/**` via
  `.gitattributes`): parse base/ours/theirs, merge at the *element* level keyed on uid — both
  new uids are kept, same-uid-edited-differently becomes a per-field conflict report instead of
  a text splat. (a) ships with `haus fmt` (WP2.2); (b) is backlog after M3 — the uid scheme
  (§5.2) is what makes it a small tool rather than a research project, and until it ships the
  fmt convention keeps ordinary conflicts rare and readable.
- **Repo hygiene:** commit scoping (`engine:` / `ui:` / `haus(catlin):` / `library:`); CI path
  filters so house-only commits skip the full engine matrix; `houses/*/out/` gitignored.
- **Privacy — decided (§2 #19):** the repo is public from day one, and the catlin house keeps its
  real site coordinates/address when it lands in M3 — building permits and county parcel GIS are
  already public record. No private-overlay mechanism is built.

---

## 5. Domain Schema (the heart — M1)

### 5.1 Typed quantities — custom frozen value types (NOT pint)

Pint defeats `mypy --strict` and drags a registry everywhere; we need ~7 dimensions. Hand-roll:

```python
# typehaus/quantities/length.py (sketch)
@final
class Length:
    """Canonical meters. Remembers authored unit for display + source round-trip."""
    __slots__ = ("_m", "_authored")          # _authored: AuthoredUnit enum + original args
    def __add__(self, other: Length) -> Length: ...
    def __mul__(self, k: float) -> Length: ...          # Length * Length -> Area (separate overload)
    def fmt(self, system: UnitSystem) -> str: ...        # 36'-0"  or  10 973 mm
    def to_source(self) -> str: ...                      # exact constructor call: ft(12, 6)
    @classmethod
    def __get_pydantic_core_schema__(cls, ...): ...      # pydantic v2 validation/serialization

def ft(feet: float, inches: float = 0) -> Length: ...
def inch(x: float) -> Length: ...
def mm(x: float) -> Length: ...
def m(x: float) -> Length: ...
# Length.parse("12'-6 1/2\"") for UI input fields
```

- Same pattern for `Angle` (canonical radians, authored degrees), `Pitch(rise=4, run=12)`
  (first-class; `.to_angle()`), `Area`, `RValue` (canonical RSI; `r_us(40)`), `UFactor`,
  `Temperature` (canonical Celsius; authored °F for the imperial market — feeds `Site`'s design
  temperatures, §5.14).
- Dimensional arithmetic is closed and type-checked: `Length + Length → Length`,
  `Length * Length → Area`, `Length + float` = **type error**. This is the "Rust-like type safety"
  story, tier zero.
- `to_source()` is the unit-preservation mechanism: a wall authored at `ft(12, 6)` survives a UI
  drag as `ft(13, 0)` — never `m(3.9624)`.
- Port constants `M_PER_FT = 0.3048`, `M_PER_IN = 0.0254` from `ifcplot/units.py`.

### 5.2 Stable IDs — immutable uid + human tag + derived GUID

Three-layer scheme. (Design note: an earlier draft derived GUIDs from a storey-qualified element
path — rejected because moving an element between storeys or retagging it would change the GUID,
turning the change into a delete-plus-add and destroying round-trip continuity.)

- **`uid` — immutable identity, the round-trip anchor.** Every authored element carries
  `uid: str`: a 10-char Crockford-base32 random string (e.g. `uid="7Q3K9M2XVT"`), **generated once
  at element creation and retained in source forever**. Never derived from position, storey, or
  tag — retagging a wall or moving it to another storey preserves identity. Uniqueness enforced
  by an integrity check (collision → regenerate).
- **`tag` — human name, freely mutable.** `W-101`, `D-103`, `WIN-204`, `RM-Kitchen`, `N-17` —
  unique per plan; used in dimensions, schedules, findings, and the UI. Renaming is a non-event
  for diff because identity is the uid. Convention: prefix by kind; hundreds digit by storey; UI
  auto-suggests next-in-series.
- **IFC GlobalId — derived, never stored:**
  `ifcopenshell.guid.compress(uuid.uuid5(project_uuid, uid).hex)`. `Project` holds one
  `project_uuid` generated by `haus new`. Generated children (studs, joists) extend
  deterministically under their parent: `uuid5(project_uuid, f"{parent_uid}/stud-007")`.
  → Same source = byte-stable GUIDs; moved/renamed elements **keep** their GUIDs.
- **Ergonomics — humans never mint uids:** the UI writeback path and Claude skills assign uids at
  creation; a hand-authored element missing its uid is a lint finding that `haus fmt` auto-fixes
  (inserts a fresh `uid=` kwarg via libcst). `haus build` never mutates source; only
  `fmt`/writeback do.
- **DXF:** uid + tag written to each entity's XDATA (`{"uid": "7Q3K9M2XVT", "tag": "W-101"}`);
  AIA layer names carry the class (§7); DXF handles are never relied on.

### 5.3 Wall topology — node graph + junction solver (the "no gaps" fix)

The single most important structural decision. Walls are **edges between shared nodes**, not
independent segments:

- **`Node`** — a 2D point per storey (auto-tagged `N-1…`, user-nameable).
- **`Wall`** — connects exactly two nodes. Required fields: `assembly` (a wall cannot exist without
  one), a **top constraint** — `top: Length | ToRoof(ref)` from **day one in the schema**, because
  real walls terminate against sloped roof planes (gable-end walls, walls under sheds): a
  scalar-height-only wall model produces flat tops jutting through or gapping under roofs and
  cannot be retrofitted without rewriting the wall core. M1 implements only the `Length` arm;
  `ToRoof` resolves in M3 (the resolver clips the wall's layer polygons against the referenced
  roof's plane — a shapely/boolean step in the junction-solved pipeline, and the IFC emitter
  already receives arbitrary polygons per §5.3 so it needs no change). An unresolved `ToRoof`
  (missing/non-adjacent roof) is an integrity error. And **alignment**: which assembly face lies on the node-to-node axis
  (`"center"` | `"face:sheathing-ext"` | `"face:stud-int"` | center+offset). Residential dimensions
  reference face-of-stud / face-of-sheathing, so alignment is first-class.
- The **junction solver** (in `resolve/`) builds the planar graph and resolves every node:
  - **L-corner:** mitered layer geometry.
  - **T-junction:** butt per layer priority — structure runs through, sheathing/membrane continuity
    per the layer's `function`, finishes wrap. Default policy "structure-butts, finish-wraps";
    per-assembly overrides later.
  - **X-junction:** split into four resolved corners.
  - Output per wall: a **polygonal body per layer** (replacing the old rectangle-between-points),
    so corners are geometrically complete *by construction*.
- **Gaps cannot be silent:** any node with exactly one wall edge not flagged `open_end=True`
  (wing walls) is an integrity **error** with coordinates and tag.

### 5.4 Element model (Pydantic v2, frozen, `mypy --strict`)

```
Project ── Site (lat, lon, elevation, crs="EPSG:26915", true_north, parcel refs, grade,
                 design_temp_heating, design_temp_cooling — §5.14)
  └─ Building
       ├─ Slice (plan | section | detail views over the resolved model — §5.11;
       │         plan slices auto-scaffolded per storey)
       └─ Storey (elevation, default ceiling height)
            ├─ Node, Wall, Opening (Door | Window | RoughOpening)
            ├─ FoundationWall, Footing, Pad, Post, Beam (§5.9 — M1 schema, decision #27)
            ├─ FloorSystem (structural deck; owns FloorOpenings — §5.7), Slab (slab-on-grade)
            ├─ Soffit (storey-level; polygon may span rooms; optional drop framing — §5.7, #40)
            ├─ FloorHeat (zone-level radiant on Slab/FloorSystem — §5.7, #39)
            ├─ Room (claims face; owns FloorFinish + ceiling + wall-lining overrides — §5.7/§5.10)
            ├─ Stair, Roof, GridAxis, Annotation (anchored once, placed per Slice — §5.11)
            ├─ Fixture (type_ref, room, position) — M3, plumbing symbols + schedule (§5.6 note)
            └─ Furniture (type_ref, position, rotation) — M3, drives §9.1 dashboards/overlays
Libraries: Assembly (+ variants — §5.10), Material, DoorType, WindowType,
           Transition (bridge details — §5.12),
           FurnitureType/FixtureType (footprint, height, clearance zones, storage: bool,
                                      needs: set[Service])  # Service = water_hot | water_cold |
                                                            #   drain | gas | power_240 | vent
```

- **Opening** (`Door`/`Window`): `host="W-101"`, position along wall
  (`from_node("N-3", ft(4))` or `centered()`), sill height, ref to `DoorType`/`WindowType`
  (carrying U-factor, **`shgc: float` and `vt: float | None`** — solar heat gain coefficient and
  visible transmittance, decision #41; neither is derivable from anything else on the type, and
  both feed the §5.14 load estimator and future daylighting work — glazing, operation,
  rough-opening size → drive schedules + energy checks).
  Compiles to `IfcOpeningElement` + `IfcRelVoidsElement` + `IfcDoor`/`IfcWindow` +
  `IfcRelFillsElement` — replacing today's voids baked into wall profiles.
- **Room:** rooms are **derived** from the wall graph (face extraction via
  `shapely` — node the axis network, `polygonize`), then **claimed** by declaration:
  `Room(tag="RM-Kitchen", seed=pt(ft(6), ft(22)), ceiling=None, occupancy=Occupancy.KITCHEN,
  conditioned=True)`. **`occupancy` is a closed Enum** (`BEDROOM | BATHROOM | KITCHEN | LIVING |
  UTILITY | …`, decision #41), not free text — this isn't purely future-proofing: the existing
  R310 egress-window check (§8) already needs to know which rooms are sleeping rooms, so this
  tightens a check already planned, and it happens to be exactly what a future ASHRAE 62.2
  bedroom-count ventilation calculator would need too — one Enum, two consumers.
  A seed landing in no closed face → "loop not closed here" integrity error. Rooms carry ceiling
  overrides and **wall-lining overrides** (`wall_lining=[…]`, with per-wall exceptions — the
  sauna liner, §5.10); soffits are storey-level elements (decision #40) whose overlap subtracts
  from the room's ceiling derivation.
  Compiles to `IfcSpace` (missing entirely today) using the room's **clear-face polygon** —
  because that polygon is already derived from core + resolved lining thickness (§5.10) rather
  than independently drawn, it touches the interior faces of its bounding walls with zero gap by
  construction, which is exactly the space-boundary closure future energy-modeling exporters
  (EnergyPlus, Radiance) require (decision #41, §5.14) — an integrity check (WP1.5) asserts it
  stays true as a tested regression rather than an implicit hope.
- **Assembly** — unifies the duplicated `assemblies.py` (3D) and `detail_utils.py` (2D) models.
  Ordered `Layer(name, material_ref, thickness: Length, function: STRUCTURE|SHEATHING|MEMBRANE|
  INSULATION|AIRGAP|FURRING|CLADDING|FINISH, framing: FramingSpec | None,
  control: set[AIR|WATER|VAPOR|THERMAL] = ∅)` — `control` tags which layers are the building's
  control layers, feeding the continuity checks (§5.12, §8). **Two-tier split (decision #34):**
  the assembly proper is the **core** (the structural layer and everything outboard); the
  interior-of-structure finish stack is its **`default_lining`**, overridable per room-face
  (§5.10). **Variants (decision #35):** `variant_of` + layer-span substitutions resolving live
  against the base (§5.10). **One Assembly definition drives:** (a) 3D layer solids /
  `IfcMaterialLayerSet`, (b) the layer stacks every Slice cuts (§5.11), (c) R-value computation
  (from `Material.r_per_inch`/conductivity; core + per-face lining), (d) BOM lines, (e) the
  named face references that transitions and overlay anchors resolve against (§5.12).
  Ship existing presets (`HOUSE_WALL_2X4_WITH_CI`, `HOUSE_WALL_2X6_WITH_ZIPR`, `GARAGE_ICF`,
  `HOUSE_ROOF`) in `library/`.
- **Material** (decision #41): `r_per_inch` already drives R-value (§5.1); joined by
  `perm_rating: float | None` (vapor permeance, US perms — the Glaser-method input, §5.14),
  `density: float | None` (kg/m³ — thermal mass now, dead-load math later), and
  `specific_heat: float | None` (J/kg·K — pure headroom for a future dynamic-simulation tool;
  unused until one is scheduled). **Embodied carbon deliberately does *not* become a Material
  field:** GWP factors are exactly the externally-sourced, database-version-dependent numbers
  decision #28 already ruled out building in for costs — a future embodied-carbon estimator would
  read a user-supplied `carbon.toml` (kg CO2e per unit, parallel to `prices.toml`) and multiply
  through the BOM volumes decision #25 already computes. Same rationale, same shape, zero new
  schema surface. All fields are optional; a material missing one is simply excluded from the
  calc that needs it — a Finding, not a crash (decision #32's UNKNOWN pattern).
- **Detail → superseded by `Slice` + `Transition` (decisions #36/#37):** a detail is a
  `Slice(kind="detail")` cut from the resolved model, cropped tight around a boundary condition,
  with its build-science overlay (flashing, sealant, screens) supplied by the `Transition` bound
  to that condition (§5.11–§5.12). Keeps the `notes/*.md` YAML-frontmatter convention:
  frontmatter `applies_to:` binds notes to slice/transition tags; the sheet composer pulls them in.
- **Roof:** constrained vocabulary — gable/shed first (hip later), `Pitch`, overhangs (**zero is
  a first-class value** — catlin's metal roof lands directly on standing-seam siding;
  **per-edge overhang overrides** allowed, one roof-wide value the shortcut), bearing
  wall refs, roof assembly. Generated planes/ridges/eaves get **deterministic child uids under
  the roof's uid** (§5.2 pattern, `uuid5(project_uuid, f"{roof_uid}/plane-N")`, N by stable
  geometric ordering) — but **authored elements never reference generated planes**:
  `FollowRoof(roof_ref)` points at the **Roof system**, and the resolver selects whichever
  planes cover the room — a room spanning the ridge is clipped against both, correctly, and the
  reference survives any designer regeneration. The ceiling follows the **interior finish face
  of the roof assembly** (hot roof: underside of the assembly stack, not the exterior plane),
  which is also the surface the R305 average-height check (avg ≥ 7' over floor area counted at
  ≥ 5') measures. **Unsupported roof forms fail loudly:** footprints requiring valleys, dormers,
  intersecting masses, crickets, or partial gables are *detected and rejected* with an integrity
  finding — never quietly approximated. **Stair:** rise derived from storey elevations; solves
  tread/riser against code constraints; errors if unsolvable.
- **Psets, repurposed** (source of truth flipped): every emitted element gets
  `Pset_HF_Source = {uid, tag, plan_content_hash, assembly}` — the round-trip anchor and
  a Bonsai-user affordance. Also emit *standard* psets now: `Pset_WallCommon` (IsExternal,
  ThermalTransmittance from Assembly), `Pset_DoorCommon`, `Pset_SpaceCommon`, `Qto_*` quantities.
  The old `Pset_ifcPlot_DetailParams` JSON-blob pattern dies — 2D outputs read the resolved model,
  not psets.

### 5.5 Plan-source dialect (the UI seam)

A house is a Python package:

```
houses/catlin/
├── plan/
│   ├── site.py           # haus: editable
│   ├── assemblies.py     # haus: editable (refs into library/ + local overrides)
│   ├── storeys/
│   │   ├── basement.py   # haus: editable
│   │   └── main.py       # haus: editable
│   └── manifest.py       # assembles Project from modules; registers params/
├── params/
│   └── arches.py         # full Python: loops/math; returns list[Element]; UI shows output read-only
├── notes/*.md
├── brief.md              # design brief (§11): program, budget, climate, style, priorities
├── preferences.toml
└── out/                  # gitignored build artifacts
```

- Files opt in with a `# haus: editable` header. A **libcst-based dialect linter** enforces the
  constrained subset there: module-level typed constructor calls, literals, quantity constructors
  (`ft()`, `inch()`), named constants, tuple/list literals — **no loops, conditionals, or function
  defs**. Violations are build errors pointing at file:line.
- Parametric logic (catlin's arched openings, sunken-garden geometry) lives in `params/*.py` —
  arbitrary Python, functions returning `list[Element]`, registered in `manifest.py`. The UI
  renders their elements read-only with a "generated by params/arches.py — edit in code" badge.
- **Versioning (decision #31):** `manifest.py` declares `format_version=N` and
  `requires_engine=">=X,<Y"`. The engine refuses to build outside the declared range (clear
  error, upgrade hint) rather than misinterpreting a plan. Both declarations are **readable via
  the libcst dialect path without importing anything** — an incompatible plan must be
  diagnosable without executing its code. A `format_version` bump ships with a
  `haus migrate` source migration applied via libcst, and every migration carries before/after
  fixture plans as tests — **including chained tests (N → N+1 → N+2)**, not only adjacent pairs.
  `haus migrate` requires a clean git tree, supports `--dry-run`, and validates (full build)
  before declaring success — rollback is `git checkout`, which the clean-tree requirement makes
  safe. Migrations are automatic for `# haus: editable` files only; `params/*.py` is arbitrary
  Python, so engine API breaks there are handled by deprecation shims for one version window,
  then flagged for manual migration (a finding listing the offending calls).
- **Compatibility ≠ reproducibility:** a version *range* prevents known breakage but doesn't
  pin what actually built. External house repos scaffold with a committed **`uv.lock`** (exact
  engine + transitive environment); every build writes **`out/build_meta.json`** recording
  exact engine version, Python and IfcOpenShell versions, active code-profile version, plan
  source revision hash, and the content hashes of consumed `library/` items — so "rebuild the
  permit set from last year" is answerable, and a drifted rebuild is *detectable* even when the
  version range permitted it.

### 5.6 Schema headroom — designed-for, not yet built

MEP zones, penetrations, terrain/grading, and site utilities are explicitly **not first-pass
features**, but the M1 architecture must make each one an *additive* change (new element kind +
emitters) — never a schema break. (Foundations, posts/beams, and plumbing fixtures were
originally in this table and have been **promoted**: foundations + posts/beams to the M1 schema
per decision #27 — see §5.9 — and `Fixture` to M3 alongside Furniture, because the permit set
needs plumbing-fixture symbols and life-safety annotations.)

| Future element | Reserved design | IFC target |
|---|---|---|
| MEP zones | `Zone(polygon, storey, kind=duct\|chase\|mechanical)` — the storey-level `Soffit` (#40) generalizes into this; actual route modeling stays out of scope | `IfcZone`/`IfcSpatialZone` |
| Penetrations | generalize the Opening host+cut machinery to any host (wall/floor/roof) with a `service` ref; air-sealing checklist hook | `IfcOpeningElement` + service element |
| Terrain / grading | `Terrain(contours \| TIN)` on `Site`; grade lines appear in sections; cut/fill analysis much later | `IfcGeographicElement` / site mesh |
| Site utilities | `UtilityRun(kind=water\|sewer\|power, polyline, depth)` on `Site` → C-101 layers | annotation-first, `IfcPipeSegment`-lite later |
| Dynamic thermal simulation | `Material.specific_heat`/`density` already carried (decision #41, §5.14); no exporter built | EnergyPlus IDF / gbXML (not built) |
| ASHRAE 62.2 ventilation | `Room.occupancy` bedroom count + `FloorFinish` area already sufficient (decision #41); no CFM calculator built | annotation-first (not built) |

Three M1 architectural requirements that make the above cheap later:

1. **Open element registry:** the model's element union stays explicit and typed, but emitters,
   checks, and the drawing IR dispatch on element kind via a **registry** — adding a kind = one
   model class + registered emitter functions, with a unit test asserting every model kind has an
   emitter (completeness enforced by test, not by `match` statements scattered across the code).
2. **Generalized host+cut:** the `IfcOpeningElement` machinery is written against a `Host`
   protocol from day one (walls first; slabs/roofs become parameter changes, unlocking
   penetrations for free).
3. **Capability protocols:** drawing IR and checks consume `HasFootprint`/`HasAxis`/`HasProfile`
   protocols, not concrete classes.

### 5.7 Horizontal layers — the two-tier floor model (decision #21)

The tension: joists span between bearing walls and ignore interior partitions, while floor
finishes vary per room (or within one). These are **two different tiers with two natural
owners** — model them separately and the tension disappears:

- **`FloorSystem` (owner: Storey) — the structural deck.** One per framed level (a storey may
  have zero for slab-on-grade — that's what `Slab` remains for). Carries:
  - `JoistSpec(member, spacing, direction, bearing_refs)` — bearing refs are wall/beam tags; the
    framing solver (§5.8) generates joists between them, running straight over partitions.
  - `subfloor` layer (material + thickness) and `ceiling_below` layer (the drywall on the
    underside), so the deck is a real assembly-like stack: its total depth **feeds the storey
    elevation delta**, which is exactly what the stair designer's derived floor-to-floor rise
    (§9.1 #2) reads — one source of truth for the number beginners get wrong.
  - **`FloorOpening(polygon, purpose=stair|chase|hatch)`** — first-class, owned by the
    FloorSystem, **referenced by tag from the `Stair`** (and from anything else that passes
    through). This is what makes stair openings *consistent between levels by construction*:
    there is exactly one opening object, the stair points at it, and integrity checks verify
    (a) the stair's referenced opening exists in the FloorSystem above it, (b) headroom clears
    per R311.7, (c) the solver generated trimmer/header joists around it (doubled members at
    opening edges fall out of the framing solver, not hand modeling).
- **Finish tier (owner: Room) — `FloorFinish`.** Each Room's finish polygon is **derived from
  its claimed face** (no re-drawing, no drift when walls move): `Room.floor_finish="carpet-x"`
  covers the face; optional `FinishZone(polygon, material)` children handle in-room variation
  (tile inlay at an entry, hearth pad). Ceiling finish is likewise Room-level and composes with
  overlapping storey `Soffit`s (below). **All area takeoffs (decision #25) — carpet, tile, underlayment sq ft —
  read this tier;** structural BOM (joist count/length, subfloor sheets) reads the FloorSystem.
- **Emission:** FloorSystem → `IfcSlab` (deck) + aggregated `IfcMember` joists at framed LOD +
  `IfcOpeningElement` per FloorOpening; FloorFinish → `IfcCovering(FLOORING)` per room —
  which is also exactly how Revit expects to receive floor finishes.
- **`Soffit` — storey-level dropped ceiling (decision #40).** `Soffit(polygon,
  drop | underside_elevation, framing: FramingSpec | None = None)` owned by the Storey — the
  polygon may cross room boundaries (the catlin case: a duct chase running down the hallway and
  into part of one room). With a `FramingSpec`, the framing solver generates the drop framing
  (2x4 ladder below primary structure) — visible in 3D at framed LOD, cut by slices, counted in
  the BOM. Floorplans render it with the dashed above-cut-plane convention plus a ceiling-height
  annotation; ceiling-height checks evaluate residual clear height **per overlapped room**
  (hallway vs. habitable-room minimums separately — the "fits the duct without blocking the
  hallway" question is answered by a finding, not by eyeballing). Rooms don't own soffits; a
  room's ceiling derivation subtracts overlapping soffits geometrically.
- **`FloorHeat` — zone-level radiant heat (decision #39).** `FloorHeat(zone=polygon | room_ref,
  system=electric | hydronic, spacing, embed=in_slab(depth) | under_subfloor, stat=pt(...),
  sensors=[...])`, owned by the Slab or FloorSystem it heats. Resolves to: a schematic
  serpentine clipped to zone-minus-keep-outs on floorplans (symbol layer; also the E/M sheet),
  wire/tube dots at spacing + embed depth in any slice cutting the slab (§5.11), wire-length /
  mat-area + stat/sensor counts in takeoffs (decision #25), and warn findings where the zone
  runs under fixed fixtures or cabinet footprints (shares clearance-overlay geometry, §9.1 #6).
  Deliberately no routing solver — the serpentine is schematic (decision #39).

### 5.8 Framing solver & FramingSpec (decision #20 — the signature)

Platform framing is a small closed rule system — that's the "inherent mathematical beauty" —
so it lives as a **library of framing rules in `resolve/framing/`, running on every build** as a
core pipeline stage. It is a pure, deterministic function
`(resolved wall/floor polygons, FramingSpec) -> list[FramedMember]`; members carry deterministic
child uids under their parent (§5.2) so GUIDs are stable build-to-build.

`FramingSpec` (per Assembly's STRUCTURE layer):

- **Layout:** stud spacing (16"/24" o.c., configurable), member size (2x4/2x6…), layout origin
  rule (from which node the grid counts), bottom plate + double top plate (single-top /
  advanced-framing option).
- **Openings:** king + jack (trimmer) studs per opening-width table, header sizing pulled from
  the same tables `checks/structural/` uses (one table module, two consumers), cripple studs
  above headers and below sills, sill plates — driven by the `DoorType`/`WindowType`
  rough-opening size. This is also what powers the §9.1 #6 "framing bumpers" overlay.
- **Corners & intersections:** junction-solver output tells the framer the condition; default
  three-stud California corner (four-stud and ladder-blocking T options per spec) — corners are
  framed correctly *because* walls are edges in a solved graph, not independent boxes.
- **Stacking:** an opt-in advanced-framing flag aligns stud layout grids across storeys and with
  joist layout (in-line framing), giving visibly aligned load paths in section views.
- **Masonry (decision #23):** CMU/ICF STRUCTURE layers carry `MasonrySpec(unit_size, coursing,
  core_fill, rebar_spacing)` instead — the walls render as accurate layered solids (insulation
  and air-barrier layers hatched exactly like wood assemblies), and the takeoff computes block /
  form counts and rebar length arithmetically. No per-block geometry.

**Where the output goes (one solve, four sinks):** (a) 3D members (`IfcMember` aggregated under
the parent wall at framed LOD), (b) **2D plan cuts — the signature look:** the floor-plan cut
plane slices real stud rectangles, insulation hatch between them, sheathing/drywall linework
from the assembly, replacing gray-box wall poché (a per-sheet `simplified_poche` toggle exists
for jurisdictions that want conventional plans), (c) S-101 framing plan sheets, (d) BOM/takeoff
counts (decision #25).

**Performance budget:** framing a whole house is thousands of rectangles from closed-form rules —
target < 200 ms for the full solve; members stay lightweight records (no geometry kernel) until
emit; the UI receives them as instanced primitives (§9.2).

### 5.9 Foundations & bearing (decision #27 — schema in M1, sheets in M3)

Promoted from §5.6 headroom because the flagship house needs them (basement + ICF garage) and a
permit set without a foundation plan isn't a permit set:

- **`FoundationWall`** — a `Wall` in every structural sense (edges between nodes, assembly-driven,
  junction-solved; `GARAGE_ICF` already models one), distinguished by kind so checks (frost depth,
  anchor-bolt notes), sheets (foundation plan, not floor plan), and IFC class selection
  (`IfcWall` with foundation pset) treat it correctly. Reuses everything — no second wall system.
- **`Footing(under=<wall-or-post tag>, width, depth)`** — strip footings under foundation walls,
  spread footings under posts; auto-follows its parent's geometry so moving a wall moves its
  footing. → `IfcFooting`. **`Pad(polygon, thickness)`** for isolated pads/thickened slabs.
- **`Post` / `Beam`** — point/axis structural members reusing `add_rect_member_between_points`;
  beams are valid `bearing_refs` for `JoistSpec` (§5.7), which is how a mid-span beam line enters
  the floor solve. → `IfcColumn`, `IfcBeam`.
- **Load path: authored facts, derived graph.** Geometry alone cannot tell bearing from
  spatial adjacency — a wall under a joist isn't necessarily carrying it. So the elements carry
  **minimal authored structural intent**: `Wall(structural_role="bearing"|"nonbearing"|"unknown")`
  (default `unknown`), and explicit `bearing_refs`/`supported_by` tags where load transfers —
  `Beam(bearing_refs=("POST-1","FW-2"))`, `Post(supported_by="PAD-3")`, plus the
  `JoistSpec`/`Roof` bearing refs already in the schema. The load-path **graph stays derived**
  (never authored as a graph — it would drift): `haus explain --bearing` and the UI overlay
  follow these references plus geometry, and **`unknown` breaks the chain visibly** — rendered
  as a gap with a warn finding, never silently treated as nonbearing. Advisory structural
  checks (§8) walk the same derivation, and a bearing wall whose joists land on nothing below
  is exactly the kind of finding this exists for.
- **Foundation scope, stated honestly:** `FoundationWall` carries top and bottom elevations
  (the catlin walkout/sunken-garden condition needs them). **Stepped footings and engineered
  retaining-wall conditions are out of scope through M3** — a foundation wall whose retained
  height exceeds the prescriptive table limit, or a footing that would need to step, produces
  an explicit "requires engineering / not modeled" finding rather than plausible-looking
  geometry.

M1 ships the schema + resolve + core-LOD IFC emission; the S-100 foundation-plan sheet and
frost-depth check land with the M3 permit set.

### 5.10 Wall variation — lining tier + assembly variants (decisions #34, #35)

The sauna exposed the general shape of the problem: walls vary **by face** (what a room does to
its side) and **by segment** (what the exterior does along a run). Two mechanisms, both keeping
the base assembly single-source:

- **Lining tier — per room-face (decision #34).** Mirrors §5.7's two-tier floor model. The
  assembly proper is the **core** — the structural layer and everything outboard of it — plus a
  **`default_lining`** (the interior-of-structure stack, e.g. `[5/8" drywall]`). Every wall face
  bounding a Room resolves a lining: the assembly default unless the Room overrides —
  `Room(wall_lining=[Layer(polyiso, inch(2)), Layer(furring, inch(0.5)), Layer(t_and_g, inch(1))])`,
  with per-wall exceptions allowed. The sauna authors its liner **once**; it lands on the
  exterior wall face *and* both partition faces, while each partition's other side keeps the
  neighboring room's drywall — per-side asymmetry by construction, no `INT-2X4-SAUNA-SIDE-A`
  assembly zoo. Consequences that fall out:
  - **Floorplans update automatically:** room clear faces derive from core + resolved lining
    thickness, so a lining change moves the finished face and every dimension chain referencing
    `face:finish-int` (§9.3) — and a drywall spec change (1/2" → 5/8") visibly moves the plan.
  - **R-value & takeoffs:** the wall's thermal path is core + per-face lining; lining areas roll
    into the finish takeoff tier exactly like `FloorFinish` (decision #25).
  - **Junctions:** the junction solver wraps linings under the finish-wraps default, so lining
    meets lining at inside corners (the sauna's taped polyiso continuity in the existing detail).
  - Bottom/base conditions (the sauna's 6" fiber-cement base course with membrane up-turn) are
    transition content (§5.12), not schema.

- **Assembly variants — per segment (decision #35).**

  ```python
  Assembly(tag="EXT-1-BRICK", variant_of="EXT-1",
           substitute={outside_of("membrane"): [Layer(air_gap, inch(1)),
                                                Layer(brick_veneer, inch(3.625))]})
  ```

  Layer-span selectors (`outside_of(name)`, `inside_of(name)`, `layers(a, b)`) substitute one
  contiguous span; **everything else resolves live against the base** — bump the base's CI from
  2 to 3 layers of 2" polyiso once, and the brick-clad and standing-seam sections both follow.
  Guardrails: a variant must keep the base's STRUCTURE layer (different structure = an honestly
  different assembly, authored as one), and alignment faces (§5.3) resolve through shared layers
  so segments stay structurally aligned even where finished faces jog.
  - **Segment application:** assigning a variant to part of a run auto-splits the wall at the
    boundary (the §9.3 split op under the #33 remap contract). The node where base and variant
    (or any two assemblies) meet becomes a derived **assembly-change condition** (§5.12): face
    jogs are computed per layer and surfaced, and a Transition binding is expected where the
    change is intentional — a swap can never *silently* create a discontinuity.
  - Variants are also the fork target for assembly experiments (§5.13) — same mechanism; the
    `active` flag decides what builds.

Whole-assembly swaps (2x4 partition → staggered-stud) are neither of these — walls are simply
re-pointed (this wall, this contiguous run, or select-same bulk swap — §9.1 #10) and the graph
re-resolves. **The cascade is the harmony contract:** one authored change → junction solver →
wall polygons → room faces → dimension chains → framing solve → every Slice, the 3D view,
checks, and takeoffs. Nothing is drawn twice, so plans, details, and the 3D model cannot
disagree — which is also the working loop the product assumes: tune assemblies, tune floorplans,
confirm in 3D, then layer in fixtures/electrical/HRV.

### 5.11 Slices — one view mechanism for plans, sections, details (decision #36)

A **`Slice`** is an authored view of the resolved model produced by cutting it:

```python
Slice(tag="A-101", kind="plan", storey="main")                        # auto-scaffolded
Slice(tag="A-A", kind="section", plane=vertical(("N-3", "N-9")))
Slice(tag="DTL-EAVE", kind="detail", plane=vertical(("N-3", "N-9")),
      crop=around(("W-201", "RF-A"), pad=ft(2)),
      exaggerate=ExaggerationSpec(min_draw=inch(0.35)))
```

- **Floorplans are plan slices** (auto-scaffolded per storey at the 4' cut, overridable);
  sections are vertical slices at building extent; details are slices cropped tight around a
  boundary condition. All render through the one drawing IR (§7.1) and cut **real resolved
  geometry** — studs, plates, I-joists with bevel cuts and web stiffeners, layer polygons,
  concrete — the eave detail's structure is *cut from the model*, never re-drawn beside it.
- **Overlay layer — 2D-only build-science content.** Flashing profiles, sealant beads, insect
  screens, gravel hatch, grade lines are deliberately never 3D-modeled. A detail slice carries
  overlay elements drawn in its 2D frame but **anchored to model references** — the same
  `(uid, face-role)` scheme dimensions use (§9.3), plus named points ("top of foundation wall",
  "outer face of wall EPS") — so when an assembly gains a CI layer, anchors move and the overlay
  **re-flows**; an anchor that no longer resolves is an error finding, never a silently stale
  drawing. Most overlay content arrives packaged in `Transition` recipes (§5.12) rather than
  authored per slice.
- **Exaggeration, honestly labeled:** `ExaggerationSpec` clamps thin layers (membranes, gaskets,
  sill seal) to a minimum draw thickness and re-lays-out the stack 1-D along the assembly normal
  so neighbors stay adjacent; annotations and dimensions always state **true** dimensions.
  A detail-slice affordance only — plans and sections stay true-scale.
- **Annotations are shared, placed per view.** An `Annotation` exists once, anchored to model
  refs; each Slice holds `AnnotationPlacement(annotation_ref, visible, leader/text overrides)`.
  The same note can appear as a pin in the 3D panel, on the working floorplan, and on the
  permit detail — each placement independent, so "permit-ready" composition is show/hide/move,
  not re-authoring. `notes/*.md` frontmatter binds prose to slice/transition tags as before.
- **UI slice manager** (§9.1 #12): list of all views; draw a cut line on the plan to create a
  section/detail; the 3D panel shows slice planes as widgets with cross-highlighting.

### 5.12 Transitions — bridge details as first-class boundary conditions (decision #37)

Assemblies describe the *field* of a wall; buildings fail at the **boundaries between** fields.
The existing eave and basement details are exactly this — not drawings of a wall but of the
wall↔roof and wall↔foundation conditions; window waterproofing is the wall↔opening condition.
So boundaries are modeled explicitly:

- **Conditions are derived, never authored.** The resolver enumerates every boundary condition
  in the model: wall↔roof edges (eave/rake, per plane), wall↔foundation bearing lines, opening
  perimeters (head/jamb/sill × host assembly), assembly-change nodes (§5.10), wall↔slab,
  soffit↔wall. Each gets a **condition key** — `(kind, participating assembly/type refs)`, e.g.
  `(eave, EXT-2X6-CI, ROOF-IJOIST-CI)` or `(window-sill, WIN-CASEMENT-A, EXT-1-BRICK)`.
  `haus explain --transitions` prints the distinct conditions with instance counts — the
  model's detail schedule is **enumerable by construction**.
- **A `Transition` binds a condition pattern** (exact key or wildcard — "any assembly whose
  outer layers end furring + cladding") **to:**
  1. an **overlay recipe** — parametric 2D elements (§5.11) anchored to *both* sides' faces
     (membrane lapping from sheathing onto foundation foam; Z-flashing + drip edge into the
     gutter; window sill pan turning up the jambs). Anchoring to both sides is what makes the
     bridge re-flow when either side's assembly changes;
  2. **notes** (the `notes/*.md` binding, printed with the detail);
  3. optional **solver directives** — real 3D consequences the framing/roof solver executes
     (birdsmouth vs. beveled bearing plate, I-joist web stiffeners at bearing, blocking) so the
     3D model, the framing takeoff, and the detail slice agree by construction.
- **Coverage is checked; change is safe:**
  - an unbound condition → warn finding ("(eave, EXT-1-BRICK, ROOF-A): no transition — 2
    instances"); `/permit-check` requires full coverage;
  - swapping an assembly re-keys its conditions: still matched → overlays re-flow silently; no
    longer matched → the finding names exactly the detail work the change created. **This is
    the answer to "when does a local swap become a discontinuity": the moment it creates a
    condition no transition covers.**
  - a transition whose anchors no longer resolve (the layer it flashed over was removed) is an
    error finding, never a silently wrong drawing.
- **Library seam:** transitions are prime `library/` content — the zero-overhang metal-roof
  eave, CI-wall-onto-ICF sill, flanged-window flashing kit — each shipping its overlay recipe,
  notes, and the assembly patterns it covers. The existing catlin details port as the first
  library transitions (WP3.2).
- **Control-layer continuity rides on this:** layers tagged with `control` roles (§5.4) let an
  advisory check walk each control layer (air/water/vapor/thermal) across junctions; a control
  layer that dead-ends at a junction whose transition doesn't declare continuity for it is a
  warn — the eave and sill details exist precisely to close these paths, and now the model can
  say whether they do.

### 5.13 Fork & compare — in-plan variants (decision #38)

Early design is a usable mess on purpose. Forking is duplication with provenance — no git
re-implementation, no CRDT:

- **Fork units:** an assembly forks as a sibling declaration (`variant_of=…, active=False` —
  the §5.10 variant mechanism with the substitution left open-ended); a storey forks as a
  sibling file (`plan/storeys/main__b.py`, its storey declared `variant_of="main",
  active=False`).
- **One active member per variant set** builds into IFC/sheets/checks. Inactive variants still
  parse and resolve (their own resolve pass) so compare is live. Yes, that is a full duplicate
  resolve — heavy and pragmatic; a resolve is seconds, and the honest copy beats overlay/patch
  schemes that drift (rejected, §14.1).
- **Identity:** forked elements get **fresh uids** (uniqueness holds) with `forked_from`
  retained per element, so compare aligns elements pairwise without heuristics (the §10
  Hungarian matcher covers additions); cross-variant references are integrity errors.
- **Compare view** (§9.1 #11): side-by-side canvases, linked pan/zoom, element-level delta list
  (same classifier as `haus diff`), takeoff/R-value deltas.
- **Promote = swap `active` + uid remap:** promoting a variant deactivates the original and
  remaps surviving elements **back to their `forked_from` uids** (decision #33 machinery), so
  GUID/diff continuity and external references survive; the demoted original can be kept as a
  variant or deleted. One journaled, undoable operation.
- **Bounded mess:** variants don't nest (a fork of a fork joins the same set), and `haus build`
  nags (warn finding) when a set's inactive members exceed a preference or go long untouched —
  a nudge to promote or delete, never a blocker.

### 5.14 Building science — schema now, tools last (decisions #41, #42)

A reviewer flagged three physics-grounded tools worth adding — a Glaser-method condensation-risk
calculator, a block heating/cooling load estimate ("Manual J lite"), and a window-to-wall-ratio
analyzer — plus the schema scalars that make them cheap later. All three are explicitly
**lowest priority** (a dedicated **M5**, after the M4 PWA gate) but the schema is **M1**:
additive optional fields cost nothing now and are expensive to retrofit onto a model already
carrying hundreds of authored elements.

**Schema additions (decision #41, M1):**

- **`Temperature`** joins the §5.1 quantity family — canonical Celsius, authored °F for the
  imperial market.
- **`Material`** (§5.4): `perm_rating`, `density`, and `specific_heat` join `r_per_inch`.
  **Embodied carbon deliberately does *not* become a Material field** — it follows the costs
  precedent (decision #28) via a future user-supplied `carbon.toml`, never a built-in database.
- **`WindowType`/`DoorType`** (§5.4): `shgc` and `vt` join U-factor.
- **`Site`**: `design_temp_heating`/`design_temp_cooling` — the 99%/1% design-day boundary
  conditions every load calc needs (for catlin, roughly -15°F / 90°F).
  `preferences.toml [envelope] ach50` (air leakage target) is **already in the schema** (§8) —
  the reviewer's ask here was already covered, no change needed.
- **`Room.occupancy`** is promoted from free text to a closed Enum (§5.4) — not purely
  future-proofing, since it also tightens the existing R310 egress check.
- **Space-boundary closure — already true, now asserted** (§5.4): Room's clear-face `IfcSpace`
  polygon already touches its bounding walls' interior faces with zero gap, by construction of
  the §5.10 lining derivation; WP1.5 adds the integrity check that keeps it a tested regression.
- **Headroom, not scope:** dynamic simulation (EnergyPlus/IDF, Radiance daylighting) and
  ASHRAE 62.2 ventilation — the reviewer's other two suggestions — stay **unscheduled**. Both are
  now cheap *if* ever picked up (§5.6's headroom table gains the two rows).

**The tools themselves (decision #42, M5 — dedicated milestone, after M4, genuinely last):**

- **Condensation risk (Glaser method).** For each Assembly, walk its layers in order computing
  the steady-state **temperature gradient** (from cumulative R-value between
  `design_temp_heating` and an assumed interior setpoint) and the **vapor-pressure gradient**
  (from each layer's `perm_rating` and thickness, interior/exterior humidity assumptions in
  `preferences.toml`). Where the saturation curve and actual vapor pressure cross inside a layer,
  emit a WARN `Finding` naming the layer ("dew point reached at Layer 3: Sheathing") and render a
  temperature/vapor-pressure plot on the A-401 sheet beside that assembly's detail Slice (§7.2) —
  the same per-Assembly walk the R-value calc (§5.4) already does, one more consumer of the same
  data.
- **Window-to-wall ratio.** Per façade (N/E/S/W, from `Site.true_north` + each wall's resolved
  outward normal — already computed, §6), glazing area ÷ gross wall area. A WARN when
  south-facing WWR exceeds a `preferences.toml [envelope]` threshold without adequate overhang
  coverage (reads roof/eave overhang geometry the same way the R305 check reads the roof).
  Advisory, not code: MN residential doesn't hard-cap WWR the way commercial ASHRAE 90.1 does.
- **Block heating/cooling load ("Manual J lite").** Sum UA (U-factor × resolved area) across
  every envelope element — walls, roof, slab/foundation, windows/doors, the last two also
  SHGC-weighted for solar gain — against `design_temp_heating/cooling`. Not a pass/fail check —
  a **report**: `haus energy` (CLI + `--json`), a UI dashboard panel (§9.1, same pattern as the
  takeoff dashboard) showing required BTU/h and a rough tonnage suggestion, and an EN-1 sheet
  line item. This is the tool that answers "what does 2x4 → 2x6 actually save me" directly,
  because it's summing Assembly R-values the framing solver already resolves — no new geometry,
  just a new consumer.
- **New tier: `checks/building_science/`** (condensation risk + WWR; the load estimator is a
  report, not a check, so it doesn't live here). Physics-grounded like `checks/structural/`
  ("advisory, not engineering") — distinct from code citations (`checks/code/`) and design
  opinions (`checks/advisory/`). Full framing in §8.
- **Why M5 and not earlier:** all three read the resolved model and nothing else — no new
  authored elements, no UI editing surface, no compiler-pipeline change. Scheduling them last
  costs nothing architecturally; scheduling the *schema* last would have meant touching Material/
  WindowType/Site/Room again after houses already depend on them.

---

## 6. Compiler Pipeline (M1 core)

```
plan source ──parse────► PlanModel      (Pydantic; authored units preserved)
            ──validate─► cross-element  (refs resolve, tags unique, dialect lint)
            ──resolve──► ResolvedModel  (IR: junction-solved wall polygons, derived rooms,
            │                            framing members, stair/roof geometry, SI coords,
            │                            provenance map tag → file:line)
            ──emit─────► IFC │ DXF │ PDF sheets │ model.json (UI) │ diff baseline
```

- **Two load paths, one truth:** `haus build` imports the plan package normally (fast; runs
  parametric modules). The **provenance/writeback path** parses editable files with libcst into
  `{tag → (file, CST node span)}`. A consistency check asserts both views agree.
- **Determinism:** uuid5 GUIDs (§5.2); sorted canonical iteration; IFC OwnerHistory/timestamps
  pinned via build config (SOURCE_DATE_EPOCH-style). CI golden test: two consecutive builds are
  **byte-identical**.
- **No incremental compilation in M1/M2** — a house resolves in low seconds; add per-storey caching
  only if profiling demands.
- **LOD flag — reinterpreted under decision #20:** framing **always resolves** (it's a core
  pipeline stage, §5.8, feeding floorplan cuts, the UI, and takeoffs regardless of flags);
  `--lod` selects only what is *emitted to the IFC file*:
  - `--lod framed` (default; what the UI 3D panel and Bonsai load): parent walls **plus**
    generated studs/plates/joists/layer solids (`IfcMember`/`IfcCovering`) aggregated under the
    wall via `IfcRelAggregates` — the signature visible-framing view.
  - `--lod core` (the architect-handoff artifact; what `--handoff` bundles): one `IfcWall` per
    wall with `IfcMaterialLayerSetUsage` + shared `IfcWallType` per assembly — what Revit
    digests cleanly. **Parent GUIDs identical across LODs** so diff stays stable.
- **Schema: IFC4 (Add2 TC1)**, not 4.3 — materially better Revit/Bonsai/web-ifc support; IFC4 has
  everything residential needs including georeferencing. Emitters behind an interface so 4.3 is a
  future flag.
- **Georeferencing (M1):** `Site(lat, lon, elevation, crs, true_north)` →
  `IfcSite.RefLatitude/RefLongitude/RefElevation` + `IfcProjectedCRS`/`IfcMapConversion`
  (eastings/northings/rotation). `pyproj` for transforms. Basemap import (parcel/contours GeoJSON
  → reference geometry under the UI plan + site-plan sheet) is M3.
  **Project north vs. true north (never tilt the canvas):** all authoring — plan source, the UI
  canvas, floor-plan sheets, dimensions — happens in **project-north coordinates**, an orthogonal
  local frame where the house's walls are axis-aligned. `true_north` is a single `Angle` on
  `Site` recording how project north deviates from true north; it is consumed *only* by the
  georef emit (`IfcMapConversion` rotation), the sun indicator (§9.1 #3), the north arrow, and
  the M3 basemap import (which rotates *imported* parcel geometry into the project frame — the
  house never rotates). Users draw orthogonal walls on an orthogonal grid, always.
- **IfcOpenShell:** pin **0.8.x**; use module-style API (`ifcopenshell.api.root.create_entity`).
  Port from `ifcplot/ifc_utils.py` nearly verbatim into `emit/ifc/lowlevel.py` (typed):
  `placement_matrix`, `translation_matrix`, `add_prism_from_profile[_with_voids]`,
  `add_rect_member_between_points`, surface styles, trade groups, `ensure_pset`. **Rewrite** the
  wall builder: consumes junction-solved polygons; cuts real `IfcOpeningElement`s.
  Beware the mm-units scaling gotcha documented at `ifc_utils.py:395-406` (raw profile entities
  need `calculate_unit_scale` division) — or standardize project length unit and centralize scaling
  in lowlevel.py.

---

## 7. 2D Outputs — DXF + PDF Permit Set

### 7.1 One drawing IR, two writers

A small 2D **drawing IR** (scenegraph: polylines, hatches, text, architectural dimensions, symbols,
viewport placements) generated from `ResolvedModel`, with two writers: **ezdxf** and
**matplotlib-PDF**. Guarantees DXF and PDF agree; the team already knows matplotlib deeply.
(Fallback if we change our minds: ezdxf's `drawing` add-on can render DXF→matplotlib directly.)

- **Every 2D view is a `Slice` (§5.11, decision #36).** Floorplans are the auto-scaffolded plan
  slices — cut plane 4' above each storey floor; wall polygons/openings/stairs projected from
  the IR. Never redrawn from scalar specs (today's failure mode). Sections and details are the
  same mechanism at other planes/crops, so all 2D output shares one cut/projection/annotation
  path. **The cut slices real framing (§5.8):** stud sections, insulation hatch, sheathing and
  drywall linework per assembly layer — the signature framed-floorplan look is the default in the
  UI and on printed plans, with a per-sheet `simplified_poche` toggle for jurisdictions that
  prefer conventional gray poché.
- **Dimensions:** auto-generated chains from the node graph + grid (overall → grid line → opening
  centers), plus explicit `Dimension` annotations in plan source for anything the auto-dimensioner
  shouldn't guess.
- **DXF conventions:** AIA CAD Layer Guidelines (`A-WALL`, `A-WALL-PATT`, `A-DOOR`, `A-GLAZ`,
  `A-ANNO-DIMS`, `A-ANNO-TEXT`, `A-AREA-IDEN`, `S-FRAM`, `C-TOPO`/`C-PROP` site). Model space in
  **inches**, `INSUNITS=1` (configurable to mm). Paperspace layout per sheet, viewports at standard
  scales, architectural DIMSTYLE (tick marks, ft-in text). Tag in XDATA per §5.2.
- **Elevations/sections (M3):** orthographic projection of IfcOpenShell geometry-iterator output
  (triangles → coplanar merge → outlines, painter's-order occlusion). Prior art:
  `ifcopenshell.draw` (used by Bonsai's documentation system). Deliberately last; risk-flagged §12.

### 7.2 Details and sheets

- `detail_utils.py` primitives (`_batt_insulation`, `_lumber`, `_flashing`, `_stud_pattern`,
  `_dim_h/_dim_v`, leaders, `MATERIAL_COLORS`) **port mechanically** to drawing-IR emitters — same
  math, different sink. The five existing wall-section details become **detail Slices + the
  first `library/` Transitions** (§5.11–§5.12): structure cut from the resolved model,
  flashing/sealant/screen content as anchored overlay recipes, thin layers exaggerated per
  `ExaggerationSpec` with true-dimension labels.
- **Sheet composer:** `SheetSet` model — title-block template (project/site/owner from
  `Project`/`Site`; sheet number/name/scale/date/revision), auto sheet index. Standard set:

  | Sheet | Content |
  |---|---|
  | A-000 | Cover, sheet index, code summary (from checks output — worded per decision #32) |
  | C-101 | Site plan (M3: parcel basemap, setbacks, north arrow) |
  | S-100 | Foundation plan (M3: foundation walls, footings, pads, posts — §5.9) |
  | A-101… | Dimensioned floor plans (one per storey; plumbing fixtures + smoke/CO alarm and egress life-safety symbols from M3) |
  | A-104 | Roof plan (M3: planes, pitch arrows, ridge/valley lines — decision #29) |
  | A-201… | Exterior elevations (M3) |
  | A-301 | Building sections (M3) |
  | A-401 | Wall sections / details (detail Slices + bound Transitions + notes/*.md; condensation-risk plot per assembly — M5, decision #42) |
  | A-601 | Door/window schedules (from DoorType/WindowType) + plumbing fixture schedule (M3) |
  | S-101… | Framing plans (from framed-LOD generators) |
  | EN-1 | Energy compliance summary (Assembly R-values vs preferences + MN code; block heat/cool load — M5, decision #42) |

  Basic electrical planning (outlet/switch/light symbols as annotations, no circuit modeling)
  rides the annotation system — an E-101 sheet is composed from `Annotation(symbol=...)` entries
  when present, but is not required for the M3 acceptance bar. **Smoke/CO alarms are not
  optional:** an `Alarm(kind=smoke|co|combo, room)` annotation element + an R314/R315 placement
  check (one per bedroom, outside sleeping areas, per storey) land with the M3 checks.

- Sheet sizes: 11×17 and Arch D 24×36 presets (many MN cities accept 11×17 residential).
- `haus print` = build → render all sheets → single bookmarked `out/permit_set.pdf` + per-sheet DXF.
- **`haus print --handoff`** additionally emits `out/handoff/` — the "give this to your
  architect" bundle: core-LOD IFC, all DXFs, the permit-set PDF, `brief.md`, the decision log
  (from `/import-review` rounds if any), and the diff baseline. This is the §1 exit-ramp-2
  deliverable: a package a professional imports and builds on directly.

---

## 8. Checks Framework

- **Shape:** a check is a pure function
  `(ResolvedModel, Preferences, JurisdictionProfile) -> list[Finding]` registered via decorator.
  `Finding(severity: ERROR|WARN, check_id, message, element_tags, code_ref, source_loc, fix_hint)`.
  Rule *results* are **tri-state** (decision #32): `PASS | FAIL | UNKNOWN(reason)` — a rule that
  cannot evaluate (data not modeled, unsupported geometry, e.g. R305 before the roof exists)
  reports UNKNOWN with the reason, is counted in its own column in every output surface, and is
  never folded into the pass count.
- **Checks tiers** (integrity/code/advisory/structural all scaffolded early — integrity is the
  deep one; `building_science` is the exception, scaffolded last per decision #42):
  - `checks/integrity/` — **main focus**: wall-loop closure / dangling nodes; every wall has an
    assembly and its alignment resolves to a real layer; openings fit host with min edge distances;
    room seeds resolve to closed faces; storey/height consistency; tag uniqueness; assembly layer
    sanity (thicknesses > 0, functions ordered sensibly); **boundary-condition coverage** —
    every derived condition (§5.12) bound to a Transition or warn-flagged, transition/overlay
    anchors resolve; assembly-change nodes audited with per-layer face jogs quantified (§5.10);
    lining stacks resolve on every claimed face (§5.10); variant sets have exactly one active
    member and no cross-variant refs (§5.13).
  - `checks/code/mn_residential/` — profiles are **versioned by edition**: `mn-2024` first (the
    current MN Residential Code — 2021 IRC base with MN Rules 1309 amendments — what a 2026+
    catlin submittal is reviewed against); other editions are additional profiles. Start with ~5
    high-value rules: egress window area/dimensions/sill height (R310), door clear widths, minimum
    ceiling heights (**including Soffit drops** and the R305 sloped-ceiling average for
    roof-defined attic ceilings, §5.4/decision #29), stair riser/tread/headroom (R311.7), hallway
    width; smoke/CO alarm placement (R314/R315) joins in M3.
    **Profile rigor (decision #32):** every rule carries its code citation; the profile module
    declares its edition, effective date, and amendment history vs. its IRC base; each rule ships
    with pass/fail fixture plans; and the profile exposes a **coverage statement** (which code
    chapters it encodes, which it doesn't). All rendered output — CLI table, A-000 code summary,
    UI panel — says "N pass, F fail, U not evaluable, of M encoded rules; this profile covers a
    declared subset of the code" and **never** the words "code compliant".
  - `checks/advisory/` — **design intelligence, warn-only, reasoning shown** (these are opinions
    with arithmetic behind them, never authority): habitable rooms without an exterior window;
    count of unique door and window sizes (fewer sizes = cheaper ordering — reported as a fact,
    with the size histogram); kitchen work-triangle perimeter outside the 12'–26' rule of thumb
    (sink/range/refrigerator positions from `Fixture`/`Furniture`, so this activates in M3);
    door-swing collisions (two swing arcs intersecting, or a swing hitting a fixture clearance
    box — shares geometry with the §9.1 #6 clearance overlays so UI and CLI always agree);
    **control-layer continuity** (§5.12): walk each tagged air/water/vapor/thermal layer across
    junctions and warn where one dead-ends at a junction whose transition doesn't declare
    continuity for it; `FloorHeat` zones running under fixed fixtures or cabinet footprints
    (§5.7).
    Every advisory finding states *why* in the message and is individually suppressible in
    `preferences.toml`.
  - `checks/structural/` — table-driven, clearly labeled "advisory, not engineering": I-joist span
    lookup (covers catlin's 18-ft spans), header sizing over openings.
  - `checks/building_science/` — **physics-grounded, not code-mandated** (decision #42; schema
    lands in M1, tools land last in the dedicated **M5**, §5.14): a **Glaser-method condensation
    check** walks each Assembly's layers computing the temperature and vapor-pressure gradients
    from `Site.design_temp_heating` and each `Material.perm_rating`; a crossing inside a layer is
    a WARN naming that layer, paired with a plot rendered on the A-401 sheet (§7.2). A
    **window-to-wall-ratio check** computes per-façade glazing percentage from `true_north` +
    resolved wall normals, WARN on south-facing glass over a `preferences.toml` threshold without
    overhang coverage. (The block heating/cooling load estimator is a report, not a check — it
    ships as `haus energy` + a UI dashboard, §5.14 — so it doesn't live in this tier.)
- **Dual invocation:** a small pytest plugin parametrizes the registry so plain `pytest` runs every
  check as a test (the agent-native feedback loop); `haus check --profile mn-2024 --json` runs the same
  registry with human table + machine JSON output.
- **Preferences feed targets:** `preferences.toml` `[envelope]` (PGH: `wall_r=40, roof_r=60,
  window_u=0.25, ach50=1.0`) consumed by warn-tier envelope checks against computed Assembly R-values.
- **IDS/ifctester:** `haus check --ifc` generates an `.ids` from the active profile (required
  psets/attributes/classifications) and runs `ifctester` against the built IFC — validating the
  **emitter**, not just the model. Integrity-tier post-build gate.

---

## 9. UI Architecture (local web app — M2)

- **Stack:** React + TypeScript + Vite; **SVG** editor (hundreds of elements — DOM hit-testing,
  crisp linework, native text beat canvas complexity; revisit only if profiling says so). State via
  zustand. **The server owns all geometry math**; the UI is a view + patch emitter.
- **`EngineClient` boundary (day one):** all engine access goes through one typed TS interface —
  `getModel() / getChecks() / patchPlan(ops) / build(opts) / getArtifact(kind) / events()` — with
  the M2 implementation `HttpEngineClient` (fetch + WebSocket). No component touches the network
  directly. This is deliberately the seam that lets a `PyodideEngineClient` (in-browser engine in
  a Web Worker) slot in for the offline PWA (§13 M4) without touching any editor code.
- **Touch-first, tablet-class (not smartphone):** the editor targets iPad-landscape viewports and
  up. Tap = select; oversized drag handles and snap radii (scaled with zoom; ≥44 px hit targets);
  two-finger pan / pinch zoom; long-press = context menu; **no hover-only actions or menus** —
  but hover **is** used for passive feedback where it exists (snap-target dots on nodes/midpoints,
  pre-highlight before click: near-mandatory ergonomics in 2D drafting); touch gets the equivalent
  feedback *during* the drag (snap indicators render while dragging, before commit). On-screen
  ft-in keypad for dimension entry.
  Keyboard shortcuts remain as desktop accelerators. The M2 Playwright suite runs the drawing
  script in a touch-emulated tablet viewport as well as desktop (§15).
- **Editing loop:** UI renders the server's `model.json` (resolved geometry + provenance +
  `editable` flags) → user edits → element-level **patch ops** → server applies via libcst
  writeback → rebuild → WebSocket push → re-render. Target < 2 s round trip.
- **Write safety (decision #30) — because the files are the state, writes get database manners.**
  A patch is not a file operation: one op set can touch a storey file, `assemblies.py`, and an
  annotation at once. So the transaction unit is the **project**, coordinated by one server-side
  mutation path:
  1. Every `PATCH /plan` carries the **project revision hash** — a hash over all source inputs,
     served with `model.json`. Mismatch → `409`, no write, client re-syncs.
  2. The coordinator takes the project mutation lock, applies all ops to a **staged in-memory
     CST tree**, and parses + validates the entire staged project before anything touches disk.
  3. Affected files are then replaced one by one — each an **atomic temp + fsync + rename**,
     with the on-disk hash **rechecked immediately before each replace** (VSCode and Claude
     don't honor advisory locks); any mismatch aborts and restores from the pre-commit
     snapshots, which are retained until the commit completes.
  4. The **journal entry (one per patch, with inverse ops) is recorded only after every file
     lands**, and watcher-triggered rebuilds are suppressed until the single project-commit
     event fires. Room macros and driven dimensions (§9.3) get multi-file atomicity for free.
  - **Conflict UI:** when the source changed under the editor (external-edit hash mismatch — the
    same event that seals the undo journal), the canvas shows a banner: what changed on disk
    (element-level summary via the provenance map), with **reload** as the only mutation path.
    In-flight local edits are rejected by the precondition, never silently merged over.
- **Undo/redo — server-owned, because the file is the state:** Ctrl+Z in the browser cannot be a
  client-side state pop when the truth lives in `main.py`. The server keeps a per-session
  **op journal**: every applied `PATCH /plan` op is recorded with its computed **inverse op**
  (add↔delete with the full element payload; update stores prior field values — cheap because ops
  are element-level). Undo/redo = `POST /undo|/redo` → apply the inverse/original through the
  *same* libcst writeback path as any edit, rebuild, push. Consequences that fall out correctly:
  undo works identically from any client; the file on disk always matches what the UI shows; and
  an **external edit** (VSCode/Claude, detected by watchfiles content hash ≠ hash after our last
  write) **truncates the redo branch and seals the journal up to that point** — you can't undo
  "through" someone else's edit, which is the honest behavior. Journal is in-memory per serve
  session; durable history is git's job. (WP2.2/WP2.4.)
  (Performance note: updates apply at the **element level** — rebuild the one changed frozen
  element and re-resolve, never deep `model_copy(update=…)` through nested frozen Pydantic trees,
  which is a known v2 hot-loop bottleneck. The flat PATCH-ops design already enforces this; keep
  it that way.)
- **Wall-drawing UX that guarantees closure:** draw = click node → click node; cursor snaps to
  existing nodes/endpoints/axis alignments/grid. Every new wall gets the preferences-default
  assembly immediately, flagged with a "confirm assembly" badge — *unconfigured is a visible state,
  never a silent one*. Open-ended nodes render as red pulsing markers driven by the integrity
  checker (same findings as `haus check`).
- **Rooms:** derived faces render tinted; click-to-claim opens name/ceiling/occupancy editor;
  soffits = draw polygon within room + set drop.
- **Room macros — rubber-band, split, heal (server-side ops, same PATCH/undo path as any edit):**
  - **Rubber-band stretch:** drag a wall perpendicular to its axis → its two nodes translate,
    every connected wall stretches/shrinks, dimensions live-update during the drag; openings on
    stretched walls keep their `from_node` anchor (or flag if they no longer fit — a framing-
    bumper/integrity finding, never silent). Implemented as one `move_nodes` op so undo is atomic.
  - **Split:** draw a partition across a claimed room face → the engine inserts the wall (default
    interior assembly, confirm-badge per the standard flow), splits the face, and prompts to
    claim the two resulting rooms; T-junction nodes heal into the existing walls automatically.
  - **Heal/merge:** delete a shared wall → the two rooms' faces merge (the surviving Room claim
    wins by prompt), stranded collinear nodes are removed, and the neighbors' wall segments fuse
    back into single edges. "Heal" is the inverse of "split" and round-trips in the op journal.
- **Openings:** drag door/window from palette onto a wall; snaps to dimension increments; type
  picker from library.
- **Assembly picker:** sidebar listing plan + `library/` assemblies (variants grouped under
  their base, §5.10) with live computed R-value; swap scopes — this wall / contiguous run
  (auto-split at the boundary) / all walls with this assembly — with the ghost preview per
  §9.1 #10.
- **3D panel:** `@thatopen/components` + `web-ifc` loading the fresh `core`-LOD IFC; element click
  cross-highlights the 2D plan and shows `file:line` provenance (jump-to-VSCode affordance).
- **FastAPI server** (`haus serve`):
  - `GET /model` → resolved model.json
  - `GET /model.ifc` → latest core-LOD build
  - `GET /checks` → current findings
  - `PATCH /plan` → ops `{op: add|update|delete, type, tag, fields}` — fields carry authored-unit
    strings (`"12'-6\""`) which serialize to `ft(12, 6)` in source
  - `POST /build`, `WS /events` (build done / findings changed / file changed)
  - `watchfiles` watches plan source, so edits by VSCode/Claude hot-reload the UI — the two-screen
    workflow is symmetric by design.

### 9.1 Editor intelligence features (the UI feature backlog)

Spec'd here so it's approved with the architecture; WP1.1 may split this subsection out as
`docs/ui-roadmap.md` and point back. Common rule for all of these: **every number derives from
`ResolvedModel` — the UI never re-measures geometry.**

1. **Extents & dimensions HUD (M2, in WP2.4):** persistent readout of overall building
   width/depth/height (X, Y, Z) and current-storey extents, each split **structural**
   (face-of-sheathing envelope) vs. **open space** (clear interior). Clicking a value flashes the
   governing dimension chain on the canvas.
2. **Stair designer (M2, WP2.13) — flagged major value-add:** stairs are the hardest element for
   an inexperienced designer. Floor-to-floor rise is *derived, never typed* — the storey elevation
   delta already includes joist depth + subfloor + finish floor from the floor assembly, which is
   exactly the part beginners get wrong. The panel live-solves riser count/height and tread depth
   against code (MN/IRC R311.7: riser ≤ 7¾", tread ≥ 10", headroom ≥ 6'-8"), shows total run and
   landing requirements, checks headroom against the floor opening above, and writes back a valid
   `Stair(...)` declaration. Out-of-range configurations render red with the violated code ref —
   never silently accepted.
3. **Sun indicator (M3):** toggleable sun icon at the canvas edge showing true solar azimuth
   (+ altitude readout) computed from `Site` lat/long + true north (in the model since M1), with
   time-of-day and day-of-year sliders. Pure client-side solar-position math (NOAA algorithm,
   ~50 lines of TS). No shadow casting in v1 — orientation awareness only.
4. **Space dashboard + storage ratio (M3):** HUD panel totaling conditioned / unconditioned /
   usable floor area per storey and overall (derived Rooms + `conditioned` flag), plus
   **storage ratio** = (storage-occupancy rooms + `Furniture` with `storage=True` footprints) ÷
   usable area.
5. **Service filters (M3):** filter modes that dim everything except elements whose type `needs`
   a selected `Service` — "show me everything needing hot water" (likewise gas, 240 V, drain,
   vent) — for planning wet walls and gas runs. Groundwork for the §5.6 MEP future.
6. **Clearance overlays (M3):** a translucent overlay layer with three sources, conflicts
   rendered hatched red **and** surfaced as warn `Finding`s through the standard checks framework
   so the UI and `haus check` always agree:
   - **Code clearances:** door swing arcs, bathroom fixture clearances (IRC/MN tables),
     stair/landing zones.
   - **Use clearances** from `FurnitureType`: the space a thing actually needs in use — a coat
     rack's depth *including the coats*, chair pull-out at a table.
   - **Framing bumpers:** the rough-opening + king/jack-stud + header envelope around every door
     and window, derived from `DoorType`/`WindowType` rough-opening size + the wall assembly's
     `FramingSpec` — so openings can't be placed where the framing physically can't fit.

7. **Takeoff dashboard (M2, ships with WP2.8) — the kept catlin feature (decision #25):** a HUD
   panel totaling framing member counts (studs/plates/headers/joists by size), sheet goods
   (sheathing, drywall, subfloor), insulation panel/batt area by assembly layer, and per-material
   floor-finish areas (carpet, tile — from the §5.7 finish tier). Every number derives from the
   resolved framing solve + finish tier; clicking a line highlights the counted members on the
   canvas. Same data ships as the BOM/takeoff sheet in the permit set and `haus takeoff --json`.
   **Costs (decision #28):** if the house carries a `prices.toml` (user-supplied $/unit, each
   entry optionally a low–high range), the dashboard, sheet, and CLI multiply through and show
   dollar ranges with an "own prices, not estimates" label; absent the file, no dollars appear
   anywhere.

8. **Scaled underlays (M3, with WP3.5):** import an image or PDF page (survey, existing plan,
   hand sketch, parcel print) as a locked, dimmed layer under the canvas; calibrate by clicking
   two points and typing the known distance between them; drag/rotate to register. Underlays are
   view-only references — recorded in `preferences.toml` (path, transform), never emitted to any
   artifact. Shares the "reference geometry under the plan" machinery with the basemap import.

9. **Roof designer panel (M3, WP3.11 — decision #29):** the stair-designer pattern applied to
   the roof: pick bearing walls/ridge, set `Pitch`, live cross-section preview showing the roof
   assembly, attic headroom shading (the ≥ 5' / ≥ 7' R305 zones over the floor below), and
   overhang entry where **0 is a first-class value** (catlin). Writes back a valid `Roof(...)`
   declaration; out-of-range attic configurations render red with the code ref, same as stairs.

10. **Assembly swap preview (M2, WP2.4):** swapping an assembly offers three scopes — this
    wall, this contiguous run (auto-split at the chosen boundary), or select-same (every wall
    with the assembly) — with a ghost preview before commit: thickness delta, which finished
    faces move, which dimension chains change value, and **which new boundary conditions the
    swap creates** (§5.12 — the "did I just make a discontinuity?" answer, shown before it
    happens). One journaled op-set; undo restores everything.
11. **Variant compare view (M2, WP2.14):** side-by-side canvases with linked pan/zoom over the
    active and a forked variant (§5.13), element-level delta list, takeoff/R-value deltas
    ("variant B: +142 sf drywall, kitchen +18 sf"), promote/discard actions.
12. **Slice manager (plans M2; sections/details M3):** the list of all views (§5.11) — plan
    slices per storey, sections, details; draw a cut line on the plan to create a
    section/detail; per-slice annotation show/hide/placement; the 3D panel renders slice planes
    as widgets.
13. **Building-science dashboard (M5, decision #42):** per-façade WWR readout, block heat/cool
    load summary (BTU/h, rough tonnage) with a live 2x4-vs-2x6 wall-assembly comparison, and a
    condensation-risk list (assemblies with a dew-point crossing, linking to their A-401 plot).
    Every number reads the resolved model exactly like the takeoff dashboard (#7).

Model prerequisites (already reflected in §5.4): `FurnitureType`/`FixtureType` library entries
(footprint polygon, height, clearance zones, `storage`, `needs`), `Furniture` placement element
(optionally emitted as `IfcFurniture` at core LOD), `Room.conditioned`, the `Service` enum.
Furniture types are prime `library/` contribution-seam content (§4.1).

### 9.2 Presentation preset — "Nordic" by default (decision #24)

Pretty output with zero user work and low code complexity, by concentrating all appearance in
one place:

- **One palette module** — a single material→color map (muted Nordic range: warm wood tones for
  framing, off-whites for gyp, muted mineral blue-greens for insulation, soft grays for concrete)
  defined once and consumed by **all three surfaces**: IFC surface styles (3D), SVG editor fills,
  and 2D detail/plan hatches (superseding `MATERIAL_COLORS` in `detail_utils.py`). The 2D plan,
  the 3D view, and the printed details always agree on what wood looks like.
- **3D panel rendering, three cheap standard passes** on the ThatOpen/three.js scene: soft
  neutral environment lighting, an **SSAO pass** (three.js `N8AO`/`SAOPass` — postprocessing
  config, not custom shaders), and **edge/outline rendering** (`EdgesGeometry` at a crease-angle
  threshold — reads as clean architectural linework and makes stud arrays legible). All three are
  configuration on the existing pipeline; they survive the §14 #4 fallback paths including the
  glTF route, since they attach to the three.js scene, not to IFC parsing.
- **Instancing for framing:** studs/joists at framed LOD render as `InstancedMesh` per member
  profile (hundreds of identical boxes → a handful of draw calls), which is what keeps the
  signature framing view fast on a tablet.
- Preset is the default; a plain "schematic" mode (flat colors, no passes) remains for
  low-power devices.

### 9.3 Driven dimensions & drafting commands (M2 — decisions #26, #30)

**Driven dimensions — the missing interaction, without a solver.** Every dimension on the canvas
is editable: tap `12'-6"`, the ft-in keypad opens, type `13'-0"`, and the wall moves. The rule
system is deliberately tiny:

- **Dimensions reference elements, not coordinates:** a dimension is stored as
  `(element uid, face role)` per end (e.g. `W-101 / face:stud-int`), resolving to node sets via
  the §5.3 alignment — so dimensions survive moves, resizes, and split/join remaps like any
  other reference.
- On edit, the engine picks the **less-anchored side** to move: fewer connected walls loses;
  exterior beats interior; a tie moves the side farther from the plan origin. Users are never
  asked to internalize that rule — **the proposed result is ghosted before commit**: "moves the
  east wall 6" → **[Apply] [Move west side instead]**". The heuristic is just the default
  ordering of a two-choice preview. The commit is one ordinary transactional `move_nodes` op —
  journaled, undoable, rubber-banding connected walls exactly like the §9 stretch macro (it *is*
  that macro with a typed delta).
- **Whole node sets move, never one endpoint:** a dimension edit translates the complete node
  set of the moving side rigidly — an op that would rotate or distort a wall (one endpoint
  pinned, the other free) is rejected with a message, not "solved".
- The only persistent "constraint" is a per-node **anchor pin** (📌 toggle; stored as
  `anchored=True` in source): pinned nodes never move as a side effect, so the user controls
  which side gives way by pinning the other. Editing a dimension between two pinned sets is a
  rejected op with a clear message — never a solver deadlock, because there is no solver.
- Openings on affected walls keep their `from_node` anchors; no-longer-fits becomes the standard
  framing-bumper/integrity finding.

**Drafting command set (WP2.4c)** — high-frequency actions the room macros don't cover, each an
ordinary transactional patch through the same journal:

- **Clipboard:** copy/paste selection (fresh uids minted on paste, tags auto-suggested);
  duplicate wall parallel at typed offset (new nodes, same assembly).
- **Transforms:** mirror selection about an axis; rotate selection 90°; move selection by exact
  typed distance/direction.
- **Layout:** align selected elements (node coordinates or opening centers); distribute evenly
  along an axis.
- **Topology (junction-solver-backed):** extend/trim wall to intersection with another wall's
  axis (inserts the shared node); split wall at a point (one edge → two edges + midnode, openings
  re-hosted by position); join collinear walls (inverse of split — same op the heal macro uses).
- **Selection:** select-same (all elements of the same kind, or all walls with the same
  assembly) — which is also how bulk assembly swaps work.

All of these operate on the node graph and re-run the junction solver — none introduce geometry
math in the client (the §9 "server owns all geometry" rule holds).

**Topology mutation contract (decision #33) — identity through surgery.** Split, join, trim,
and the macros can invalidate far more than geometry: hosted openings, dimensions, details,
notes bindings, footing `under=` refs, roof/joist `bearing_refs`, room claims, and IFC diff
continuity all point at uids. So every topology-changing op returns, alongside its patch ops:

```python
MutationResult(
    ops=[...],
    reference_remap={old_wall_uid: [surviving_uid, new_uid],   # split: 1 → 2
                     old_node_uid: surviving_node_uid},         # merge: 2 → 1
    deleted_uids=[...],
    warnings=[...],   # e.g. "opening D-103 re-hosted to W-101b; note N-4 now ambiguous"
)
```

- **Deterministic survivor rules:** on **split**, the original uid stays with the segment
  attached to the wall's first node (`a`-side); the other segment gets a fresh uid. On **join**,
  the survivor is the wall contributing the joined edge's `a` node. Openings re-host to
  whichever segment their position falls in, keeping their own uids. The rules are boring on
  purpose — predictability beats cleverness here.
- **Remap is processed, not broadcast-and-hoped:** the element registry (§5.6) requires every
  element kind that can hold a reference to register a remap handler; a CI completeness test
  asserts no reference-bearing field lacks one. Dangling refs after remap are integrity errors
  with the mutation named.
- **Undo restores exact uids:** the journal's inverse op carries the full pre-mutation payload
  including original uids — undoing a split brings back *the* wall (same uid, same GUID, diff
  continuity intact), never an equivalent-shaped stranger.

---

## 10. Diff / Architect Round-Trip

- `haus diff <external.ifc>` compares against the deterministic baseline (rebuilt from source):
  1. **Match by GlobalId** (uid-derived GUIDs survive tools that preserve GUIDs — most do; and
     because identity is the immutable uid (§5.2), retags and storey moves on our side never
     break matching).
  2. **Fallback matcher** for unkeyed/new elements: cost matrix over (IFC class, storey, centroid
     distance, oriented-bounding-box dims, axis direction), solved with
     `scipy.optimize.linear_sum_assignment` (Hungarian).
  3. **Replace detection (same pass, no new machinery):** after keyed matching, the leftover
     "deleted" and "added" sets go through the *same* Hungarian cost matrix — a delete+add pair of
     the same IFC class in near-identical bounding boxes reports as **replaced (was W-101)** with
     the attribute delta, instead of two unrelated changes. Matters because some architect tools
     regenerate elements with fresh GUIDs; below a confidence threshold it stays delete+add, with
     the near-miss candidate noted in `diff.json`.
  4. Classify: added / deleted / **replaced** / moved / resized / attribute-changed, deltas in **authoring units**
     (`W-101 moved 3 1/2" north`; `WIN-204 widened to 3'-0"`).
- Output: human table + `out/diff.json` (structured per-change deltas + match confidence).
- **Agentic merge — `/import-review` skill:** Claude reads `diff.json` + plan source, walks through
  accept/reject per change, applies accepted changes as plan-source edits (same libcst writeback
  path the UI uses), rebuilds, re-diffs until the report is empty or intentionally deferred.
  Rejections are logged to a decision file for the reply to the architect.

---

## 11. Agent Scaffolding

- **CLAUDE.md:** project map; invariants (never edit `out/`; always `haus build && haus check`
  after edits; all dimensions via quantity constructors, never bare floats; tag conventions;
  editable-dialect rules; read `brief.md` **and** `preferences.toml` before proposing designs);
  command crib sheet. Keep this concise, hints rather than full descriptions.
- **Skills** (`.claude/skills/`):
  - `/add-room` — nodes + walls + room claim + run checks
  - `/add-assembly` — Assembly (or variant) + detail Slice/Transition stubs + notes + R-value check vs preferences
  - `/import-review` — §10 flow
  - `/permit-check` — full check suite + sheet-completeness audit, summarize gaps
  - `/port-detail` — migrate an old matplotlib detail to the drawing IR (M3 helper)
- **preferences.toml schema:** `[project]` (display_units="imperial", jurisdiction="mn"),
  `[envelope]` PGH targets (§8), `[structure]` (preferred members, spacing, species/grade),
  `[style]` (e.g. "simple gable massing"), `[gc_notes]` free text. Read by checks **and** by Claude.
- **`brief.md` — the design brief** (scaffolded by `haus new`, lives beside `preferences.toml`):
  YAML frontmatter for the machine-readable fields + prose sections for humans and Claude.
  Template sections: **spatial program** (rooms, target areas, adjacencies), **budget level**
  (tier + optional hard cap), **climate** (zone, e.g. MN 6A/7 — sets envelope expectations),
  **style** (massing, references), **accessibility** (e.g. aging-in-place / ADA-ish clearances →
  feeds door-width and turning-radius checks), **phasing** (build now vs. rough-in for later),
  **must-haves**, **dislikes**, **priorities** (ranked tradeoffs, e.g. "envelope > sqft >
  finishes"). Division of labor: **brief = intent** (what/why — read by Claude before proposing
  anything; included in the `--handoff` bundle so the architect gets the why, not just the
  geometry), **preferences.toml = targets** (machine-read thresholds consumed by checks).
  Structured brief fields that map to checks (climate zone, accessibility standard) are copied
  into preferences by `haus new` so checks read exactly one file.
- **Feedback loop:** every failure surface is structured and points at source — build errors carry
  element tag + file:line; `haus check --json` likewise; `mypy --strict` + pytest complete the
  loop. The agent loop is: edit → build → check → fix, entirely from CLI output.

---

## 12. CLI

**Typer** (type-hint-native, matches the pydantic/mypy-strict house style; rich help).

```
haus new <name>       scaffold from template (generates project_uuid); interim template is
                       houses/starter — flips to catlin verbatim after WP3.1 (decision #22:
                       --template catlin|minimal, catlin default)
haus build            [--lod core|framed] [--only ifc|dxf|pdf|json] [--inspect]  # --inspect: parse-only, never imports params/ (§4.1 trust model)
haus check            [--profile mn-2024] [--tier integrity|code|structural] [--json] [--ifc]
haus print            [--handoff] full permit set → out/permit_set.pdf + DXFs (+ architect bundle §7.2)
haus diff <file.ifc>  semantic diff vs rebuilt baseline
haus serve            [--port] FastAPI + UI + file watching
haus fmt              normalize editable plan files through the libcst printer; assigns missing uids (§5.2)
haus takeoff          [--json] framing counts + material areas (decision #25); shows $ ranges iff prices.toml exists (decision #28)
haus energy           [--json] block heating/cooling load estimate (decision #42, M5, §5.14)
haus migrate          [--dry-run] apply the format_version source migration (decision #31); requires clean git tree, validates with a full build
haus compare <a> <b>  resolve two members of a variant set for the side-by-side compare view (§5.13)
haus ls / explain <tag>   element inspection for humans and agents; explain --bearing walks the derived load path (§5.9); explain --transitions lists derived boundary conditions + coverage (§5.12)
```

---

## 13. Milestones & Workpackages (Sonnet-executable)

Each workpackage (WP) is roughly one PR: implement + tests + `mypy --strict` clean + ruff clean.
Order within a milestone is the dependency order.

### M1 — Typed schema + proof-of-life compiler

- **WP1.1 Repo scaffold:** monorepo tree (§4), created as a **public GitHub repo** (README flags
  pre-alpha, §2 #19), uv workspace, hatchling, CI (ruff, mypy --strict, pytest), ARCHITECTURE.md
  (this doc), CLAUDE.md v1, LICENSE, README; `houses/starter/` includes `brief.md` +
  `preferences.toml` templates.
- **WP1.2 Quantities:** `Length/Angle/Pitch/Area/RValue/UFactor/Temperature` with pydantic core
  schemas, arithmetic, `parse`, `fmt`, `to_source`. Property-based tests (hypothesis):
  parse/fmt/to_source round-trip fixpoint.
- **WP1.3 Model:** Pydantic frozen elements (§5.4), `Material`/`Assembly`/`Layer`,
  `DoorType`/`WindowType`, uid + tag scheme (§5.2), wall `top: Length | ToRoof(ref)` schema with
  only the `Length` arm resolving (§5.3), `FloorSystem`/`FloorOpening`/`FloorFinish` (§5.7),
  `FramingSpec`/`MasonrySpec` (§5.8), foundation elements `FoundationWall`/`Footing`/`Pad`/
  `Post`/`Beam` with `structural_role`/`bearing_refs`/`supported_by` intent fields (§5.9),
  `Room.ceiling=FollowRoof(ref)` schema arm (resolves in M3),
  open element registry + capability protocols (§5.6), manifest `format_version`/
  `requires_engine` enforcement (decision #31), `library/` starter assemblies ported from
  `ifcplot/assemblies.py`. Two-tier Assembly (core + `default_lining`) with `control` roles and
  `variant_of` substitution (§5.10); storey-level `Soffit` + `FloorHeat` (§5.7); `Slice` +
  `Annotation` placements (§5.11); `Transition` schema + condition keys (§5.12); variant-set
  `active`/`forked_from` machinery (§5.13). Building-science scalars land here too (decision #41,
  §5.14): `Material.perm_rating/density/specific_heat`, `WindowType`/`DoorType.shgc/vt`,
  `Site.design_temp_heating/design_temp_cooling`, `Room.occupancy` as a closed Enum.
- **WP1.4 Topology + junction solver:** node graph, L/T/X junction resolution per layer, alignment
  offsets, polygonal wall bodies. Emits derived boundary conditions keyed for Transition
  matching (assembly-change nodes, wall↔foundation, wall↔slab; wall↔roof activates with M3
  roofs — §5.12); resolves per-face linings into the layer polygons (§5.10). Golden-image test
  matrix: enumerate junction cases (L/T/X × alignments × lining overrides) as snapshot tests.
- **WP1.4b Wall framing solver (§5.8, core stage):** stud layout, plates, king/jack/cripple +
  header generation at openings, corner conditions from junction output; deterministic child
  uids; golden test matrix (spacing × opening widths × corner types); < 200 ms whole-house
  budget asserted in CI. Masonry walls take the `MasonrySpec` quantity path (no members).
- **WP1.5 Room derivation + finish tier:** shapely polygonize face extraction, seed claiming,
  storey-soffit overlap subtraction; `FloorFinish` polygons derived from claimed faces with
  `FinishZone` overrides; wall-lining tier resolution (room clear faces offset by per-face
  lining; lining areas join the rollup — §5.10); per-material area rollup (feeds WP2.8 takeoffs);
  a zero-gap assertion that every Room's clear-face polygon touches the interior faces of its
  bounding walls (decision #41, §5.14 — the space-boundary-closure requirement future
  energy-modeling exporters need).
- **WP1.6 Plan loader + dialect:** plan package import path (location-independent per §4.1);
  libcst dialect linter for `# haus: editable` files (including missing-uid findings);
  provenance map; consistency check between load paths.
- **WP1.7 IFC emitter (core LOD):** port `ifc_utils.py` → `emit/ifc/lowlevel.py` (typed);
  walls with `IfcMaterialLayerSetUsage`/`IfcWallType`; real
  `IfcOpeningElement`/`IfcDoor`/`IfcWindow`/`IfcRelFillsElement`; `IfcSpace`; georeferencing
  (`IfcMapConversion`/`IfcProjectedCRS` via pyproj); deterministic GUIDs; pinned OwnerHistory.
- **WP1.8 Integrity checks + pytest plugin:** registry, Finding model, the §8 integrity set,
  pytest parametrization; deliberately-broken fixture plans (gap node, orphan opening, missing
  assembly) each producing exactly one precise finding.
- **WP1.9 CLI v1:** `haus build | check | ls | explain`.

**M1 acceptance:** a hand-written 2-storey demo plan (in `houses/starter/`) builds to valid IFC4 —
passes an ifctester baseline IDS and opens in Bonsai with correct walls/openings/spaces/georef;
two consecutive builds are **byte-identical** (CI-enforced); broken fixtures fail precisely;
every Room's `IfcSpace` polygon touches its bounding walls' interior faces with zero gap
(decision #41); `mypy --strict` and ruff clean.

### M2 — Barebones complete product (the loop closes)

- **WP2.1 FastAPI server:** endpoints (§9), watchfiles, WebSocket events.
- **WP2.2 libcst writeback:** `PATCH /plan` op application (assigns uids on element creation);
  **write safety per decision #30** (project mutation coordinator: project-revision-hash
  preconditions → 409, staged-tree apply + whole-project validation, per-file atomic replaces
  with pre-replace hash recheck, journal-after-commit, watcher suppression until the commit
  event);
  op journal with computed inverse ops + `POST /undo|/redo` + external-edit journal sealing (§9);
  `haus fmt` incl. missing-uid auto-fix and the merge-friendly canonical style (§4.1:
  one element per statement, stable ordering); property-based tests (random op sequences →
  parse/emit/parse fixpoint; comments preserved; op→inverse→op is an identity on the file).
- **WP2.3 React app shell:** Vite + zustand + model.json rendering (walls, nodes, rooms, openings),
  provenance display, editable/read-only flags; all engine access through the `EngineClient`
  interface with the `HttpEngineClient` implementation (§9).
- **WP2.4 Editor interactions:** node-snap wall drawing, default-assembly badge, open-end markers,
  assembly picker (live R-value), opening drag-drop, room claiming + ceiling/soffit editor;
  **framed floorplan rendering** (real stud cuts + layer hatching from the §5.8 solve, with the
  schematic toggle); touch-first per §9 (tap select, pinch pan/zoom, long-press menus, oversized
  handles, ft-in keypad); extents & dimensions HUD (§9.1 #1); **assembly swap flows with ghost
  preview** (scopes, moved faces, new-boundary-condition warnings — §9.1 #10).
- **WP2.4b Room macros:** rubber-band stretch (atomic `move_nodes` op, live dimensions, opening
  refit findings), split (partition insert + face split + claim prompts), heal/merge (wall delete
  + node cleanup + edge fusion) — all through the standard PATCH/undo journal (§9). Includes the
  **conflict banner** (stale-source detection + element-level summary + reload, §9/decision #30).
- **WP2.4c Driven dimensions + drafting commands (§9.3):** editable dimensions (uid+face-role
  references, ghost preview with the move-other-side alternative, rigid node-set moves, anchor
  pins); copy/paste, parallel-offset duplicate, mirror, rotate 90°, move-by-distance, align,
  distribute, extend/trim, split/join wall, select-same. Split/join/trim implement the
  **`MutationResult` remap contract (decision #33)** with the registry completeness test; tests
  assert op→undo→redo round-trips the file **and restores exact uids**.
- **WP2.5 3D panel:** ThatOpen/web-ifc embed behind a `ModelViewer` interface (pin versions;
  fallback = plain web-ifc + three.js mesh dump); loads the **framed-LOD** IFC; **Nordic
  presentation preset** (§9.2: palette module, SSAO + edge passes, `InstancedMesh` framing,
  schematic fallback mode).
- **WP2.6 DXF floorplan export:** drawing IR core + ezdxf writer, AIA layers, auto dimension
  chains, architectural dimstyle, XDATA tags.
- **WP2.7 Minimal PDF sheet:** title block + one floor-plan sheet via matplotlib writer.
- **WP2.8 Floor framing + framed IFC emit + takeoffs:** joist generation from `JoistSpec`
  (bearing spans, trimmers/headers at `FloorOpening`s — completes the §5.8 solver begun in
  WP1.4b); framed-LOD IFC emission (members aggregated under parents via `IfcRelAggregates`,
  parent GUIDs stable across LODs); **BOM/takeoff rollup** (member counts, sheet goods,
  insulation + finish areas), `haus takeoff --json` (+ `prices.toml` dollar ranges, decision
  #28), takeoff dashboard (§9.1 #7), takeoff sheet in the sheet set; storey-`Soffit` drop
  framing generation (§5.7, decision #40).
- **WP2.9 First MN code checks + preferences.toml** (the §8 starter five + PGH envelope warns);
  **profile rigor scaffolding per decision #32** (citation/effective-date/coverage fields on the
  profile, per-rule fixtures, the constrained "N of M encoded rules" output wording); first
  geometry-only advisory checks (windowless habitable rooms, unique door/window size counts,
  door-swing collisions — work triangle waits for M3 fixtures).
- **WP2.10 `haus diff` v1:** GlobalId matcher + Hungarian fallback + diff.json + human table.
- **WP2.11 Agent scaffolding v1:** CLAUDE.md complete, `/add-room`, `/import-review` skills.
- **WP2.12 CLI complete:** `new | serve | print | diff | fmt`.
- **WP2.13 Stair designer panel** (§9.1 #2): derived floor-to-floor rise, live riser/tread/
  headroom solve against R311.7, writeback of a valid `Stair(...)` declaration.
- **WP2.14 In-plan variants + compare view (§5.13):** fork an assembly or storey (`variant_of`
  + `active` + `forked_from`), one-active integrity check, side-by-side compare canvases with
  linked pan/zoom + element/takeoff deltas, promote-with-uid-remap (decision #33 machinery),
  `haus compare`.

**M2 acceptance:** a user draws a small house entirely in the UI — closed loops enforced, every
wall carries an assembly, **floorplans showing true studs/headers and layer hatching, the 3D
panel showing framed walls under the Nordic preset** — while the plan file stays human-readable
with comments intact after 50 UI edits; a rubber-band stretch and a room split/heal round-trip
through undo; **typing a new value into a canvas dimension moves the correct wall** (ghost
preview shown, anchor pins respected) and undoes cleanly; **a wall split then undone comes back
with its original uid and its openings correctly hosted**; a patch sent against a stale revision hash is rejected with 409
and the conflict banner appears after an external VSCode edit; the takeoff dashboard's stud
count matches the framed IFC's member count exactly; **swapping an interior wall's assembly to
a wider one visibly widens the wall on the plan and updates every dimension chain referencing
its faces** (with the new-boundary-condition warning shown before commit); a forked storey is
edited, compared side-by-side, and promoted with original uids restored;
Claude edits the same file in VSCode and the UI hot-reloads; `haus diff` on a Blender-modified
copy correctly reports a moved wall and an added window. **This unblocks designing the catlin
floorplans in the UI.**

### M3 — Catlin house ported + MN permit set

- **WP3.1 Catlin port:** `houses/catlin/` — declarative storeys (floorplans drawn in the UI),
  `params/` modules for arches + sunken garden extracted from `catlin_house.py` math,
  `preferences.toml`, notes migrated. **Then flip the `haus new` default template to catlin
  verbatim** (decision #22; `--template minimal` keeps the starter available).
- **WP3.2 Details ported as slices + transitions:** the five wall-section details become detail
  `Slice`s over the resolved catlin model plus the first `library/` `Transition`s
  (zero-overhang eave, basement↔framed-wall, sauna liner + base course, window head/jamb/sill
  flashing) with anchored overlay recipes, `ExaggerationSpec` for thin layers, solver
  directives (web stiffeners, beveled plates), and bound notes; transition-coverage check live
  on catlin (§5.11–§5.12).
- **WP3.3 Elevations/sections:** IfcOpenShell geometry-iterator projection (reuse
  `ifcopenshell.draw` prior art); painter's-order occlusion is acceptable for residential.
- **WP3.4 Schedules + full sheet composer:** door/window + plumbing-fixture schedules, sheet
  index, code summary (decision #32 wording), energy sheet, **S-100 foundation plan and A-104
  roof plan**, smoke/CO + egress life-safety symbols on floor plans, full §7.2 set;
  `haus print` end-to-end.
- **WP3.5 Basemap import + underlays:** parcel/contour GeoJSON → reference geometry in UI +
  C-101 site plan; **scaled image/PDF underlays** with two-point calibration (§9.1 #8).
- **WP3.6 Structural checks + bearing view:** I-joist span table (18-ft catlin spans), header
  sizing, frost-depth check on footings; `haus explain --bearing` + the UI load-path overlay
  (derived, §5.9).
- **WP3.7 Migration equivalence test:** compare new-engine catlin IFC against old-model semantics —
  element counts/volumes/placements by category, generalizing `tests/test_catlin_house_ifc.py`.
- **WP3.8 MN submittal checklist as a check** + docs (permit guide); archive old repo.
- **WP3.9 Library contribution seam:** per-item validation CI for `library/` (schema check +
  render smoke test per item), CONTRIBUTING.md documenting the promote-from-house-to-library PR
  flow (§4.1).
- **WP3.10 UI intelligence pack** (§9.1 #3–6): Furniture + `Fixture` models with starter
  `FurnitureType`/`FixtureType` library entries; `Alarm` elements + R314/R315 placement check;
  sun indicator; space dashboard + storage ratio; service filters; clearance overlays +
  framing bumpers (with their warn-tier checks); kitchen work-triangle advisory (unblocked by
  fixtures landing here); **`FloorHeat` end-to-end** (serpentine plan rendering, slice dots,
  wire-length/mat takeoff, fixture keep-out warnings — keep-outs need the fixture footprints
  landing here).
- **WP3.11 Roof designer panel** (§9.1 #9, decision #29): **strictly gable/shed** — pitch/
  ridge/bearing selection, live section preview, `FollowRoof` ceiling resolution + R305 check
  wired through, zero-overhang eave details (per-edge overrides), `Roof(...)` writeback;
  valley-requiring footprints and other unsupported forms (§5.4) detected and rejected with
  findings. Exercised end-to-end by the catlin attic.

**M3 acceptance:** new-engine catlin IFC is semantically equivalent to the old one (WP3.7 test);
the catlin attic is modeled as a habitable room under a `FollowRoof` ceiling passing R305, over
foundation elements that appear on S-100; the hallway duct soffit shows framed in 3D, dashed on
the floor plan, and passes per-room ceiling checks; slab `FloorHeat` zones appear on plans and
in the slab detail slice with wire-length takeoffs; **every derived boundary condition on the
catlin model is transition-covered**, and bumping the exterior CI from 2 to 3 layers re-flows
the eave and basement details without hand edits;
`haus print` produces a complete permit PDF passing the encoded MN checklist;
`haus print --handoff` produces the full architect bundle; old repo archived.

### M4 — Offline PWA

Lower priority by decision (§2 #15). The `EngineClient` boundary (§9) and location-independent
house loading (§4.1) are the **only** obligations M1/M2 carry for this; everything else waits
behind an explicit go/no-go gate:

- **WP4.1 Wasm feasibility spike:** the engine's wasm-hostile dependencies are exactly two —
  **IfcOpenShell** (C++ CPython extension; no official pyodide build today) and **libcst**
  (native Rust parser). Everything else either ships in the pyodide distribution (shapely, scipy,
  numpy, matplotlib, pydantic-core) or is pure Python installable via micropip (ezdxf, typer).
  Spike outcome is one of:
  - (a) full engine runs under pyodide (a workable IfcOpenShell wasm build exists) → **go**;
  - (b) **degraded offline mode** — resolve/checks/drawing-IR/DXF/PDF/model.json all run
    in-browser; the 3D panel renders a **glTF (.glb) emitted straight from `ResolvedModel`**
    (trimesh or hand-rolled — the resolver already owns the solids; .glb is native to the web and
    fast) rather than parsing IFC; IFC binary emit and libcst writeback are marked "requires
    local install" → go if still judged useful. This makes IFC purely the *interchange* artifact
    and glTF the *render* artifact — a split worth having anyway (see §14 #4);
  - (c) neither viable → **skip**, per the locked decision.
- **WP4.2 PWA packaging** (only on go): service worker + offline asset caching, pyodide engine in
  a Web Worker behind `PyodideEngineClient`, house-directory access via the File System Access
  API, install prompt. The local FastAPI mode remains the primary, fully-supported path.

### M5 — Building science analysis tools

Lowest priority by decision (§2 #42) — genuinely last, after the M4 PWA gate. All schema this
depends on landed in M1 (§5.14); nothing here touches the compiler pipeline, the UI editing
surface, or adds authored element kinds — three new report/check consumers of the
already-resolved model.

- **WP5.1 Condensation risk (Glaser method):** `checks/building_science/condensation.py` —
  per-Assembly temperature + vapor-pressure gradient walk, WARN `Finding` on a crossing, plot
  renderer wired into the A-401 sheet beside each assembly's detail Slice (§7.2); fixture
  assemblies with a known condensation point and a known-safe point as golden tests.
- **WP5.2 Window-to-wall ratio analyzer:** `checks/building_science/wwr.py` — per-façade glazing
  percentage from `true_north` + resolved wall normals, overhang-aware south-glass WARN against
  `preferences.toml [envelope]`; UI dashboard panel (§9.1 #13).
- **WP5.3 Block heating/cooling load estimator:** `haus energy` CLI (`--json`), UA-sum +
  SHGC-weighted solar gain against `Site.design_temp_heating/cooling`; UI dashboard panel
  (§9.1 #13, same pattern as the takeoff dashboard); EN-1 sheet line item (§7.2).

**M5 acceptance:** for the catlin house, `haus check --tier building_science` reports the
eave/sauna assemblies' condensation margins with no unexplained UNKNOWNs; the WWR dashboard
matches a hand count of the south-façade glazing; `haus energy` output brackets a sane MN
heating BTU/h figure and visibly drops when a wall assembly swaps 2x4→2x6 on the same run.

### Port vs. rewrite (from `catlin-house` /Users/colincatlin/Documents-NoCloud/house/catlin-house/ )

| Old module | Disposition |
|---|---|
| `ifcplot/units.py` | Rewritten as `quantities/` (constants kept) |
| `ifcplot/ifc_utils.py` | **Ported ~80%** → `emit/ifc/lowlevel.py` (typed, 0.8 module API); wall builder rewritten polygonal |
| `ifcplot/assemblies.py` + `detail_utils` assembly classes | Unified into new `Assembly`; presets → `library/` |
| `ifcplot/detail_utils.py` drawing primitives | **Ported mechanically** to drawing IR (same math) |
| Root detail scripts (`roof_wall_eave_detail.py`, `sauna_basement_wall_detail.py`, `basement_to_framed_wall_detail.py`, …) | **Reauthored** as detail `Slice`s + `library/` `Transition` recipes (WP3.2); primitives arrive via the `detail_utils.py` port |
| `ifcplot/catlin_house.py` (3,445 lines) | **Not ported** — reauthored declaratively in M3; arch/sunken-garden math → `params/` |
| `tests/test_catlin_house_ifc.py` | Style generalized into integrity checks + golden tests; specifics → WP3.7 |
| `notes/*.md` | Copied; convention formalized into `Slice`/`Transition` binding (§5.11–§5.12) |

---

## 14. Top Technical Risks & Mitigations

1. **libcst writeback complexity** (the novel part). → Strict editable dialect keeps the CST
   surface tiny; property-based round-trip tests; `haus fmt` normalizer; worst-case degradation =
   regenerate one element's statement (losing only that statement's comments).
2. **Junction/topology solver math** (mitered multi-layer corners, T-junction layer priorities).
   → Lean on shapely; enumerate junction cases as a golden test matrix in M1; ship
   "structure-butts, finish-wraps" defaults, refine per-assembly later.
3. **Permit-quality elevations/sections** (hidden-line projection is the hardest 2D output).
   → Scheduled last (M3); reuse `ifcopenshell.draw` prior art; painter's-order silhouette is
   acceptable for residential; plans/details/schedules carry most submittal value regardless.
4. **ThatOpen/web-ifc churn** (young ecosystem). → Viewer isolated behind a `ModelViewer`
   interface; pin versions; fallbacks in order: (a) raw web-ifc + three.js; (b) emit **glTF from
   `ResolvedModel`** and render with plain three.js — sidestepping in-browser IFC parsing entirely
   (IFC stays the interchange artifact, glb becomes the render artifact; same emitter WP4.1(b)
   wants); (c) "open in Bonsai" (UI fully usable 2D-only).
5. **IfcOpenShell API instability** (0.7→0.8 reshape already bit the ecosystem). → Pin 0.8.x; all
   calls confined to `emit/ifc/lowlevel.py` (~600-line adapter, exactly what `ifc_utils.py` proved
   out); golden IFC snapshots detect drift on any bump.
6. **Framing solver in the hot path** (decision #20 makes it run on every build and edit —
   correctness *and* latency now gate the core loop). → It's closed-form arithmetic, no geometry
   kernel: members are records until emit; CI asserts the < 200 ms whole-house budget from
   WP1.4b onward; the golden junction/opening test matrix covers the rule combinatorics; and the
   2D cut + UI consume the same member list as the IFC emit, so there is exactly one solver to
   get right.
7. **Overlay/transition anchor robustness** (details must re-flow, not drift, when assemblies
   change). → Anchors reuse the dimension reference scheme (uid + face role, §9.3) — one
   resolver, one failure surface; an unresolvable anchor is an error finding, never a silently
   wrong drawing; golden-image tests re-render every `library/` transition across assembly
   parameter sweeps (CI thickness bumps, layer swaps, lining overrides).
8. **Transition-coverage noise** (a strict coverage check could nag early-stage mess into
   unusability). → Coverage findings are warn-tier during design and only hard-gate in
   `/permit-check`; wildcard condition patterns let one library transition cover whole assembly
   families, keeping the distinct-condition count low.

### 14.1 Reviewer items considered and rejected/deferred (so they don't resurface unexamined)

- **Loro / CRDT sync** — rejected again (decision #4's rationale is unchanged): the round-trip
  counterparty is an architect's tool rewriting files wholesale, invisible to any CRDT; local
  concurrency is handled by decision #30's preconditions + locking; multi-user collaboration is
  git's job. Revisit only if real-time co-editing becomes a goal, which it is not (§1 non-goals).
- **"Reframe round-trip as controlled change review"** — already the design: §10 *is* a change
  review (semantic diff → per-change accept/reject via `/import-review` → decision log in the
  handoff bundle). No change needed.
- **`library.lock`** — deferred, not rejected: while `library/` ships inside the engine package,
  the `requires_engine` pin (decision #31) transitively pins every library item. A lockfile
  becomes necessary exactly when library items are distributed/versioned independently of engine
  releases — add it then, not before.
- **Built-in regional cost data** — rejected (decision #28): guaranteed wrong somewhere, high
  maintenance, and it would launder guesses into authority. User-supplied `prices.toml` gives
  the same UI with honest provenance.
- **Persistent constraint solver for dimensions** — rejected in favor of the §9.3 anchor-pin
  scheme (decision #26): no solver in the < 2 s edit loop, no over/under-constrained failure
  modes, every dimension edit stays one journaled op. Revisit only if real usage shows anchor
  pins are insufficient.

---

## 15. Verification Strategy (per milestone, end-to-end)

- **Always-on CI gates:** ruff, `mypy --strict`, pytest, build-determinism (two builds
  byte-identical), starter-house build smoke test, UI typecheck + build.
- **M1:** open the built demo IFC in Blender/Bonsai — verify walls/corners/openings/spaces
  visually; run `ifctester` against the baseline IDS; run the broken-fixture suite.
- **M2:** scripted UI session (Playwright): draw walls → close loop → place window → claim room;
  assert plan-file diff is minimal and comments survive; edit the file in a text editor and assert
  UI hot-reload; modify a copy of the IFC in Blender, run `haus diff`, assert the change report;
  repeat the drawing script in a touch-emulated tablet viewport (§9).
- **M3:** WP3.7 equivalence test vs old catlin model; print the permit set and review each sheet
  against the encoded MN checklist; verify DXF opens correctly in a second CAD tool (e.g. LibreCAD
  or an online viewer) with correct layers/units; **handoff-quality bar (§1):** import the
  `--handoff` IFC into a professional BIM tool (Revit or Archicad; trial/viewer acceptable) and
  verify walls arrive as typed layered walls with spaces and schedules populated — i.e. an
  architect could continue the model rather than redraw it.

---
