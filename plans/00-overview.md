# Type:Haus — Plan Overview & Contents

**Status:** pre-implementation design plan for the Type:Haus monorepo. This document set
supersedes the single-file plan (`~/.claude/plans/our-goal-with-the-effervescent-clock.md`).
At WP1.1 these docs migrate into the new repo as `docs/plan/` and remain the living design
documentation — there is no separate `ARCHITECTURE.md`; this set is it.

## Why

The existing `catlin-house` repo (`~/Documents-NoCloud/house/catlin-house`) proved the concept:
a residential house defined in Python, compiled to an IFC4 model via IfcOpenShell (viewed in
Blender + Bonsai), with matplotlib wall-section details driven by parameters stored in IFC
property sets. But it has hit its architectural ceiling: the house is one 3,445-line imperative
function (`ifcplot/catlin_house.py`) over flat scalar dataclasses; there are no first-class
Wall/Room/Opening types; assembly layer definitions are duplicated between `assemblies.py`
(3D) and `detail_utils.py` (2D); there are no windows, no `IfcOpeningElement`, no `IfcSpace`,
no georeferencing, no DXF, no PDF, no UI, and no agent scaffolding.

## Product vision

An open-source "infrastructure as code, but the infrastructure is a residential house" tool.
Software developers (and adjacent users) author a house plan as typed, declarative code; get a
3D IFC model; edit the 2D floorplan in a local web UI on one screen while Claude Code edits the
same plan source in VSCode on the other; users can then export their vision for an architect to
load and polish in their own software, and — for more ambitious, experienced users — complete a
permit-ready set of plans straight from this program.

Two views define the product, and the design must make them one model:

- **Wall assemblies** — detailed, building-science-backed layer stacks, seen mostly in
  *vertical* slices, driven mostly by **agentic AI coding** (organizing layers into a coherent
  building envelope is a rules problem, and the checks framework makes the rules explicit),
  optionally inspected in the UI.
- **Floorplans** — the use of the space, seen in *horizontal* slices, designed mostly in the
  **UI**, which carries helpers for the classically hard parts (stair design, roof design,
  closure guarantees).

They combine in a (fairly basic) 3D rendering, with the product's signature feature everywhere:
**the actual framing in the walls** — floorplan cuts show real studs, headers, insulation hatch,
never a generic gray box — which supports design-exact material takeoffs within a declared
scope. The riskiest seam — how assemblies vary and transition across storeys and how they bind
to the floorplan — is addressed head-on by decisions #34–#37 and #43–#47. It is proved *before*
the general compiler is built: the eave, basement-to-framed-wall, and a width-changing stack
are the acceptance fixtures for WP0.1 (→ 02 §Transition kernel spike).

## What success looks like

Type:Haus helps a capable person turn a house idea into a coherent, inspectable residential
design, then offers two exit ramps — both first-class:

1. **Refine in place:** disciplined checks (integrity / code / structural), professional
   inputs, and agentic iteration carry the design all the way to a permit-ready set.
2. **Hand off, preserving the work:** an architect/engineer imports the model and is
   *genuinely accelerated* — the IFC carries typed layered walls, real spaces, openings with
   schedules, georeferencing, and standard psets; the DXF follows AIA layer conventions. The
   user's "sketch" is something a professional builds on directly, not a napkin they redraw.
   Handoff quality is a **tested property** (→ 02 §Verification), and `haus print --handoff`
   produces the "give this to your architect" bundle (→ 30 §Sheets). A semantic diff + agentic
   merge (→ 20 §Diff) brings the professional's revisions back in.

## Non-goals

Commercial buildings, multi-family beyond duplex-scale, full CAD generality, cloud/collaboration
service (git is the collaboration layer), replacing the architect/engineer of record.

## Contents

| Doc | Covers | Phase |
|---|---|---|
| `00-overview.md` | This file — vision, goals, contents, conventions | — |
| `01-decisions.md` | The 47 locked decisions; naming/rename strategy; rejected & deferred items | — |
| `02-architecture.md` | Repo layout & git topology; compiler pipeline; CLI; migration from catlin-house; risk register; verification strategy | — |
| `10-m1-schema.md` | Typed quantities; stable IDs; element model; plan-source dialect (grammar resolved); schema headroom; building-science scalars; WP1.1–1.3, 1.6 | M1 |
| `11-m1-resolve.md` | Wall topology & junction solver; **vertical stacking (#43)**; floors; framing solver; foundations; wall variation; WP1.4, 1.4b, 1.5 | M1 |
| `11b-m1-views.md` | Slices; transitions & boundary conditions (condition-key grammar resolved; storey-stack conditions added); fork & compare | M1 |
| `12-m1-emit.md` | IFC emission; **assembly section card**; checks framework; WP1.7–1.9; M1 acceptance | M1 |
| `20-m2-engine.md` | Server; write safety; undo; libcst writeback; `model.json` contract; drawing IR + DXF/PDF; diff; agent scaffolding; WP2.1–2.2, 2.6–2.7, 2.10–2.12 | M2 |
| `21-m2-ui.md` | UI architecture; touch-first editor; assembly inspector; 3D panel + Nordic preset; WP2.3–2.5 | M2 |
| `21b-m2-editor.md` | Room macros; driven dimensions; drafting commands & mutation contract; editor intelligence (M2 features); WP2.4b–c, 2.8–2.9, 2.13–2.14; M2 acceptance | M2 |
| `30-m3-permit.md` | Permit sheets; elevations; catlin port; library transitions; M3 UI pack; roof designer; WP3.1–3.11; M3 acceptance | M3 |
| `40-m4-pwa.md` | Offline PWA gate, wasm spike, packaging | M4 |
| `50-m5-science.md` | Glaser condensation, WWR, energy load; WP5.1–5.3; M5 acceptance | M5 |

## Conventions

- **Cross-doc references** are written `(→ NN §Heading)`, where `NN` is the doc number above;
  `(→ NN)` alone points at the whole doc.
- **`#N`** references a locked decision (→ 01).
- **`WPx.y`** workpackages live in their phase doc; each is roughly one PR: implement + tests +
  `mypy --strict` clean + ruff clean. Order within a milestone is the dependency order.
- **Doc budget:** every file in this set stays under 500 lines — the plan obeys the project's
  own LLM-agent-friendliness rule.
- Every phase doc follows one skeleton: purpose & exit criteria → design patterns (data shapes,
  interfaces) → per-WP detail (scope, interfaces, tests, done-when) → risks owned (mapped to
  → 02 §Risk register) → open questions resolved inline.

## Milestones at a glance

| M | Deliverable | One-line acceptance |
|---|---|---|
| M1 | Typed schema + proof-of-life compiler | Transition-kernel fixtures and demo plan build to valid, byte-deterministic IFC4; broken fixtures fail precisely (→ 12) |
| M2 | Barebones complete product — the loop closes | A small house drawn entirely in the UI; plan file stays human-readable after 50 edits; undo, diff, framed floorplans all live (→ 21b) |
| M3 | Catlin house ported + MN permit set | Semantically equivalent catlin IFC; `haus print` yields a complete permit PDF; `--handoff` bundle imports cleanly (→ 30) |
| M4 | Offline PWA | Gated: wasm feasibility spike decides go / degraded / skip (→ 40) |
| M5 | Building-science tools | Condensation, WWR, and load reports over the already-resolved model (→ 50) |

## Goal traceability

| Product goal | Where it lands |
|---|---|
| Building-science-backed assemblies, seen in vertical slices | Element model (→ 10), wall variation (→ 11), slices/transitions (→ 11b), assembly section card (→ 12 §Assembly card) |
| Floorplans designed in the UI, with helpers | Editor (→ 21), stair designer (→ 21b), roof designer (→ 30), closure-guaranteeing drawing UX (→ 21) |
| Assemblies driven mostly by agentic AI | Checks-as-pytest (→ 12 §Checks framework), agent scaffolding (→ 20 §Agent scaffolding), card feedback loop (→ 12) |
| Real framing visible in floorplan + 3D; scoped design-exact takeoffs | #20/#25/#47; framing solver (→ 11 §Framing solver); takeoff dashboard + BOM (→ 21b) |
| Permit-ready drawings, or architect-friendly DXF/IFC | Sheet set + `haus print` + `--handoff` (→ 30); DXF/IFC emission (→ 20, → 12) |
| **Assembly transitions across floor levels** (the flagged uncertainty) | **#43 vertical stacking** (→ 11 §Vertical stacking), storey-stack conditions (→ 11b §Transitions), catlin 2x6→2x4→2x4 acceptance test (→ 30 §Acceptance) |
| Coherent transitions as layers change | **#44/#45 interface contracts + construction rules** (→ 11, → 11b): resolver-owned geometry first, transition-owned presentation second |
| Building-science-backed assemblies | **#46 evidence/provenance** on materials and assemblies (→ 10): applicability and missing inputs appear as UNKNOWN, never as authority |

## Decisions still needing owner direction

The conservative defaults in the phase docs keep implementation moving, but these alter the
product boundary and should be confirmed before M3:

1. **First permit target:** retain MN-only as the first encoded profile, or make M3 a
   jurisdiction-neutral drawing/handoff package and defer a jurisdiction-specific permit bar?
2. **Handoff acceptance target(s):** which one or two applications should be the tested IFC
   import targets? Interoperability is practical only when verified against named software.
3. **Catalog evidence policy:** may the bundled material/assembly library include clearly
   marked generic assumptions, or must every bundled entry be source-backed?
