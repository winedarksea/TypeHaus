# Revit-Model Transition Details: Live-Cut 2D Drawings, Editable Annotations, IFC Openings

## Context

Transitions in TypeHaus (where waterproofing/air-sealing is managed between assemblies — framed wall onto ICF foundation, eave, rim band, opening perimeters) have a full data model (`Transition` in `packages/engine/src/typehaus/model/views.py:54` with condition patterns, continuity claims, markdown notes, and an `overlay` id) but no drawings: the UI shows only 1D layer cards, and the `overlay` recipe ids are never rendered. The user wants full 2D details in the UI, in the style of the reference eave drawing (`/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/roof_wall_eave_detail_ifc.py` — per-layer laps, spray-foam wedge, flashing, leaders, notes panel), **and long-term these drawings must become a permit-ready detail editor** (edit note text, drag notes/leaders, eventually modify assemblies in the drawing).

The design must be the industry-standard (Revit) way. That is: a detail is a **live section cut of real model geometry** overlaid with **editable 2D annotation** (notes, leaders, detail components) — not a composed schematic. Revit's answer to per-layer laps is unlocked wall layers with Top/Base Extension Distances. This also matches TypeHaus doc 11b's own intent ("details cut real resolved geometry, never re-drawn beside it"). An earlier recipe-composer design was rejected for deviating from this.

### Industry-standard answers (settled during planning)

- **Assemblies stay 1D; transitions become 2D live-cut details.** Wall types are 1D layer schedules (SectionCard stays unchanged); junction details are 2D section views. Per-layer "x inches above/below the interface" = Revit layer extension distances = new `LayerJoin` data on `Transition`.
- **"Plumbing" wall: keep as-is, zero code.** `INT_2X6_PLUMBING` (`houses/catlin/plan/assemblies.py:223`) is already a plain internal assembly; "wet wall" is standard naming, not a type. Add an optional `Assembly.service` annotation only when a concrete check consumer exists.
- **Openings: model is sound (Door/Window/RoughOpening + generated king/jack/header framing + advisory checks; headers-as-ephemeral matches Revit), but IFC export emits no openings at all** — solid walls in Revit/SketchUp. Fixed in WP7.

### Verified feasibility facts

- `emit/draw/section.py::_emit_wall_cut` (line 135): per-layer u-intervals already come from each layer's own plan polygon; **all layers share one z-band** (`wall.z0_m .. _wall_top_at_cut`) — a per-layer z override + sloped-top quads (`_quad_nodes` sibling of `_rect_nodes`, line 73) threads in without a cutter rewrite. `_emit_roof_cut` (line 222) draws the roof as one monolithic band — needs a contained ~50-line per-layer rewrite (detail-mode only). Neither wall nor roof cuts currently show framing members; `_emit_floor_cut` (line 264) has the member-crossing math to generalize (raked members have `z0_end_m/z1_end_m`, `resolve/model.py:47-50`).
- Writeback: `AssemblyEditor` → `runMacro("edit_assembly_layers")` → `server/macros_api.py:92` → `source/assembly_ops.py:73` → one generic `PatchOp` → journal → libcst writeback. **`PatchOp` is generic over any registered element kind** (`source/ops.py:35-50`) — a new registered `DetailAnnotation` element is editable via plain `patchPlan` with no new macro machinery.
- UI: `Canvas2D.tsx` already renders the plan as React-managed **SVG DOM** with per-element hit-testing and pan/zoom — a client-side scene renderer is the established pattern.
- Scene IR (`emit/draw/scene.py:114`): 7 node kinds (Polyline, Hatch, Text, ArchDimension, Leader, Symbol, Viewport); only Polyline has `uid`/`tag` — other nodes need an optional `uid` for hit-testing.
- Conditions are assembly-set keyed (typical details, one per junction family); `condition.element_tags` gives representative instances. Catlin authors 12 transitions (`houses/catlin/plan/transitions.py`); authored detail slices live in `plan/views.py::DETAIL_SLICES` via `manifest.py:73`.
- IFC diff adapter already predicts window/door GUIDs as `derive_guid(project_uuid, opening.uid)` (`diff/ifc_adapter.py:61`) — emitting with those GUIDs closes the round-trip.
- Env: repo-root `.venv` Python 3.9.6, no uv. **ifcopenshell 0.8.4 and matplotlib 3.9.4 ARE present in the venv** (memory note saying absent is stale). Engine declares `requires-python >=3.11` but runs under 3.9 — avoid 3.11-only runtime constructs. Tests: `PYTHONPATH=packages/engine/src .venv/bin/python -m pytest packages/engine/tests -q` (smoke-verified). Keep `pytest.importorskip("ifcopenshell")` in IFC tests for portability (existing pattern).

## Architecture

A transition detail = **DETAIL Slice cutting the live ResolvedModel** through `build_section`, three layers like a Revit detail view:

1. **Model geometry** — the section cut (per-layer walls, foundation solids, per-layer sloped roof bands, cut framing members, opening voids), with per-layer terminations honored *by the cutter* via `LayerJoin` on the matched `Transition`.
2. **Derived joint geometry** — lap lines and treatment fills (spray-foam wedge, sealant, tape, flashing) computed from the same interface planes (wedge = quad bounded by wall-CI top, roof-CI underside, wall sheathing face — exactly how the reference script builds `spray_poly`); never authored, always re-derived.
3. **Authored annotations** — `DetailAnnotation` elements (notes/leaders/dimensions) anchored `(element uid, face role) + 2D slice-frame offset relative to the anchor point`, stored in plan source, edited via ordinary `PatchOp`s. Unresolvable anchor → error finding, never a silently stale drawing.

UI receives **scene JSON** (not opaque SVG) and renders SVG DOM client-side — every node hit-testable; the read-only v1 viewer and the future permit-ready editor share one contract. No new Python SVG writer: CLI output uses existing matplotlib `write_raster` (`pdf_writer.py:195`).

## Work packages

### WP1 — Model additions (`model/views.py`, new `model/patterns.py`)
- `LayerJoin(HausModel)`: `layer` (name/function glob), `side` ("from"|"to", matching `Continuity`), `termination: Length` (signed offset from interface plane; + extends past), `treatment: str | None`. Register constructor.
- `Transition.joins: tuple[LayerJoin, ...] = ()` (backward-compatible). `Transition.overlay` shrinks to a **default-annotation seed-set id** (catlin's 12 ids stay valid as seed names; update comment at `views.py:63`).
- `Slice.condition_key: str | None = None` — authored detail slice can claim a condition, suppressing its auto-scaffold.
- `DetailAnnotation(Element)`: `condition_key`, `kind` ("note"|"leader"|"dimension"), `anchor_uid`, `anchor_face`, `offset: Point2D | None`, `text`. `register_element` + constructor.
- `model/patterns.py`: extract fnmatch `_matches` from `checks/integrity/checks.py:129` (shared by coverage check, scaffolder, annotation binding).

### WP2 — Joint resolution + cutter extensions (new `emit/draw/joints.py`, `emit/draw/section.py`)
- `joints.py`: `JointPlan` — per (element uid, layer name) → termination plane (constant z or sloped (u,z) line) + treatment polygons + lap polylines. `build_joint_plan(model, condition, transition, slice_frame)`: interface planes from `ResolvedRoof` pitch/eave, `ResolvedSolid` tops, stack edges; **default joins by layer function/control** (air-tagged sheathing runs to far structure plane; CI stops short with wedge; cladding/furring run long with drip gap; membranes lap); authored `LayerJoin` overrides by glob.
- `section.py` (all gated on optional `joints: JointPlan | None` param to `build_section` — existing callers/goldens untouched):
  - `_emit_wall_cut`: per-layer z override + sloped-top quads.
  - `_emit_roof_cut`: per-layer sloped bands (cumulative offsets) in detail mode; single-band preserved for plain sections.
  - New `_emit_member_cuts` (walls + roofs, detail mode): generalize `_emit_floor_cut` crossing math to raked members → top plates and eave rafter/I-joist appear.
  - Append JointPlan treatment `Hatch`/`Polyline` nodes.

### WP3 — Scaffolding + annotations (new `emit/draw/details.py`, one macro)
- `derive_detail_slices(model)`: one derived DETAIL slice per distinct bound condition key (skip keys claimed by authored `Slice.condition_key`); representative instance from `element_tags`; cut perpendicular to host wall at midpoint; crop = junction z-window × u-window. Opening perimeters: head+sill from vertical cut through opening center (`_opening_splits` already voids), jamb as cropped plan cut (small sub-builder).
- `build_detail(model, derived) -> Scene` = `build_section(..., joints=...)` + annotation nodes.
- `resolve_anchor(model, frame, uid, face)`: v1 faces — walls "top"/"bottom"/"ext-face"/"int-face"/"layer:<name>:out|in"; roofs "eave"/"deck-top"; solids "top". Unresolved → new integrity finding `detail.anchor_unresolved`, annotation drawn at last offset with error marker.
- Annotation `Text`/`Leader` nodes carry `uid` = DetailAnnotation uid (the hit-test → PatchOp hook). No authored annotations → seed nodes from `overlay` seed set + `notes` markdown (wrapped notes column, reference style), `uid=None` until materialized.
- `seed_detail_annotations` macro (follows `edit_assembly_layers` pattern; `server/macros_api.py` + source op): materializes seeds into authored adds (`hint_file="plan/details.py"`, `hint_list="DETAIL_NOTES"`). Only new macro; all subsequent editing is plain `patchPlan`.

### WP4 — Scene IR ids (`emit/draw/scene.py`)
Optional `uid: str | None = None` on `Hatch`, `Text`, `Leader`, `ArchDimension`, `Symbol` (Polyline has it). Golden churn low (within-run determinism, no stored snapshots).

### WP5 — Sheets + CLI (`emit/draw/sheets.py`, `cli/app.py`, `emit/draw/render.py`)
- `build_sheet_index`: after authored-DETAIL loop (lines 77-81), append derived details sorted by key, continuing A-4xx. **Breaking test change**: `test_detail_sheets.py`/`test_sheet_index.py` assert exactly A-401..A-404; update in same commit.
- `haus render --view details` → `write_raster` PNG/SVG per detail (`out/render/detail_<key>.png`); `haus explain <TR-TAG> --detail` (mirrors `--card`, `cli/app.py:339`).

### WP6 — Server / Pyodide / UI
- `server/model_json.py`: add `"transitions"` array (tag, pattern, overlay, notes, continuity, joins) — joins with existing `conditions` (line 296).
- `server/app.py`: `GET /details` (index) + `GET /detail?key=<urlencoded>` → `{scene: Scene.model_dump, annotations, notes}` (query param — keys contain `|`/`:`).
- `ui/src/engine/`: `getDetailIndex()`/`getDetail(key)` on `EngineClient.ts`, in `HttpEngineClient.ts`; Pyodide `worker.ts` cases + `bootstrap.py` methods returning dicts (pure Python, offline-safe).
- New `ui/src/components/DetailCanvas.tsx`: TS renderer, 6 drawable node kinds → SVG DOM (`<defs><pattern>` per hatch: batt/rigid/concrete/lumber/osb; feet-inches formatter ported from `pdf_writer._feet_inches`), `data-uid` on nodes.
- New `ui/src/components/DetailViewer.tsx`: modal (AssemblyEditor pattern) — condition list grouped by kind (unbound/seed badges), DetailCanvas with pan/zoom (Canvas2D transform approach), notes panel. Entry: Toolbar "Details" button + Sidebar link next to SectionCard when selected wall appears in a condition. v1 read-only; editor later = hit node → DetailAnnotation by uid → `patchPlan` update of `offset`/`text` — no engine rework.

### WP7 — IFC openings (`emit/ifc/lowlevel.py`, `emit/ifc/emitter.py`)
- `lowlevel.py`: `add_opening`/`add_filling` wrappers (ifcopenshell.api `void.add_opening`/`void.add_filling`) per its all-api-calls-here charter.
- Per opening: `IfcOpeningElement` (GUID `derive_child_guid(uuid, opening.uid, "void")`; prism via `rect_between` along host axis, z = `wall.z0_m + sill_m` → `+ height_m`, full wall thickness) + `IfcRelVoidsElement`; then `IfcWindow`/`IfcDoor` with **GUID `derive_guid(uuid, opening.uid)`** (matches diff adapter prediction), `OverallWidth`/`OverallHeight`, thin frame prism, `PSET_SOURCE` + `Pset_WindowCommon`/`Pset_DoorCommon` (IsExternal), `IfcRelFillsElement`.
- Headers stay generated-ephemeral (Revit parity). Follow-ups → `plans/TODO.md`: glTF core-LOD cutouts, shared IfcWindowType/IfcDoorType.

### WP8 — Plumbing wall: no code (see Context).

## Sequencing

1. WP1 + WP4 (pure additive model/IR) → full pytest green.
2. WP2 (joints + cutter) + `tests/test_transition_details.py` (promote catlin fixture from `test_detail_sheets.py` to `conftest.py`): eave detail has per-layer sloped roof bands, wall sheathing quad reaching deck plane, wedge hatch, `to_json()` determinism. **Prototype the eave first and render/look before building other kinds.**
3. WP3 (scaffolder + anchors + seed macro) incl. failure-path test (delete layer → `detail.anchor_unresolved` finding, no crash).
4. WP5 (sheets/CLI) + assertion updates; agent-eyes loop: `haus build houses/catlin && haus check houses/catlin && haus render houses/catlin --view details` — visually compare eave PNG against `/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/roof_wall_eave_detail_ifc.png`.
5. WP6 (server/UI): server tests per `test_server_m2.py` pattern; `cd ui && npm run typecheck && npm run build`; open Details browser in HTTP and Pyodide modes.
6. WP7 (IFC): `tests/test_ifc_openings.py` (importorskip; entity/rel counts; GUID equals adapter prediction; self-emitted IFC diffs clean per `test_diff_m2.py`); sanity via `scripts/verify_bonsai_import.py`.

Verification command base: `PYTHONPATH=packages/engine/src .venv/bin/python -m pytest packages/engine/tests -q`.

## Risks (flagged)

1. **Eave at reference quality**: v1 carries all the information (per-layer bands, laps, plates/rafter, wedge) but not the sculpted **birdsmouth notch** (resolved rafter is a straight raked bar; later: let the ConstructionRule annotate a seat-cut depth the cutter honors), gutter/flashing profiles land as annotation-level symbols, I-joist flange dashes are cosmetic-later. Highest-effort package — prototype first.
2. **Annotations surviving model edits**: offsets are relative to the anchor point, so notes ride their anchors when thicknesses/heights change; orphaned anchors degrade to an error finding + marker, never silent staleness. Large representative-instance changes shift the slice frame but not anchor-relative notes.
3. **Sheet-count growth** (~8–12 new A-4xx on catlin) — deliberate breaking test change, same commit as WP5.
4. **Per-layer roof bands** gated to DETAIL slices so A-301 building sections and their tests stay stable.
5. **Python version skew**: venv 3.9 vs declared 3.11 — no 3.11-only runtime constructs.
