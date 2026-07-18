# M3 — Catlin Port + MN Permit Set

**Purpose:** the proof milestone — the real catlin house reauthored in the new engine, and a
complete, honest MN permit package out the other end. Everything M1/M2 built gets exercised
by a non-toy house: four structures, a walkout basement with a sunken garden, an ICF garage,
a habitable attic under a `FollowRoof` ceiling, and one wall line that changes assembly on
every storey (#43's motivating case).

## Details and sheets

- `detail_utils.py` primitives (`_batt_insulation`, `_lumber`, `_flashing`, `_stud_pattern`,
  `_dim_h/_dim_v`, leaders, `MATERIAL_COLORS`) **port mechanically** to drawing-IR emitters —
  same math, different sink (the assembly card, → 12, already pulled part of this forward).
  The five existing wall-section details become **detail Slices + the first `library/`
  Transitions** (→ 11b): structure cut from the resolved model, flashing/sealant/screen
  content as anchored overlay recipes, thin layers exaggerated per `ExaggerationSpec` with
  true-dimension labels.
- **Sheet composer:** `SheetSet` model — title-block template (project/site/owner from
  `Project`/`Site`; sheet number/name/scale/date/revision), auto sheet index. Standard set:

  | Sheet | Content |
  |---|---|
  | A-000 | Cover, sheet index, code summary (from checks output — worded per #32) |
  | C-101 | Site plan (parcel basemap, setbacks, north arrow) |
  | S-100 | Foundation plan (foundation walls, footings, pads, posts — → 11 §Foundations) |
  | A-101… | Dimensioned floor plans (one per storey; plumbing fixtures + smoke/CO alarm and egress life-safety symbols) |
  | A-104 | Roof plan (planes, pitch arrows, ridge/valley lines — #29) |
  | A-201… | Exterior elevations |
  | A-301 | Building sections |
  | A-401 | Wall sections / details (detail Slices + bound Transitions + notes/*.md; assembly card header per assembly — → 12; condensation-risk plot joins in M5) |
  | A-601 | Door/window schedules (from DoorType/WindowType) + plumbing fixture schedule |
  | S-101… | Framing plans (from framed-LOD generators) |
  | EN-1 | Energy compliance summary (Assembly R-values vs preferences + MN code; block heat/cool load joins in M5) |

  Basic electrical planning (outlet/switch/light symbols as annotations, no circuit
  modeling) rides the annotation system — an E-101 sheet is composed from
  `Annotation(symbol=...)` entries when present, but is not required for the M3 acceptance
  bar. **Smoke/CO alarms are not optional:** an `Alarm(kind=smoke|co|combo, room)` annotation
  element + an R314/R315 placement check (one per bedroom, outside sleeping areas, per
  storey) land with the M3 checks.
- Sheet sizes: 11×17 and Arch D 24×36 presets (many MN cities accept 11×17 residential).
- `haus print` = build → render all sheets → single bookmarked `out/permit_set.pdf` +
  per-sheet DXF.
- **`haus print --handoff`** additionally emits `out/handoff/` — the "give this to your
  architect" bundle: core-LOD IFC, all DXFs, the permit-set PDF, `brief.md`, the decision log
  (from `/import-review` rounds if any), and the diff baseline. This is the exit-ramp-2
  deliverable (→ 00 §Success): a package a professional imports and builds on directly.

## Elevations & sections approach

Orthographic projection of IfcOpenShell geometry-iterator output (triangles → coplanar
merge → outlines, painter's-order occlusion). Prior art: `ifcopenshell.draw` (used by
Bonsai's documentation system). Deliberately scheduled last among 2D outputs — risk 3 — and
painter's-order silhouette is acceptable for residential; plans/details/schedules carry most
submittal value regardless.

## Editor intelligence — M3 features

(Continues the → 21b list; same derive-from-`model.json` rule.)

- **Sun indicator:** toggleable sun icon at the canvas edge showing true solar azimuth
  (+ altitude readout) computed from `Site` lat/long + true north (in the model since M1),
  with time-of-day and day-of-year sliders. Pure client-side solar-position math (NOAA
  algorithm, ~50 lines of TS). No shadow casting in v1 — orientation awareness only.
- **Space dashboard + storage ratio:** HUD panel totaling conditioned / unconditioned /
  usable floor area per storey and overall (derived Rooms + `conditioned` flag), plus
  **storage ratio** = (storage-occupancy rooms + `Furniture` with `storage=True` footprints)
  ÷ usable area.
- **Service filters:** filter modes that dim everything except elements whose type `needs` a
  selected `Service` — "show me everything needing hot water" (likewise gas, 240 V, drain,
  vent) — for planning wet walls and gas runs. Groundwork for the MEP future
  (→ 10 §Schema headroom).
- **Clearance overlays:** a translucent overlay layer with three sources, conflicts rendered
  hatched red **and** surfaced as warn `Finding`s through the standard checks framework so
  the UI and `haus check` always agree:
  - **Code clearances:** door swing arcs, bathroom fixture clearances (IRC/MN tables),
    stair/landing zones.
  - **Use clearances** from `FurnitureType`: the space a thing actually needs in use — a
    coat rack's depth *including the coats*, chair pull-out at a table.
  - **Framing bumpers:** the rough-opening + king/jack-stud + header envelope around every
    door and window, derived from `DoorType`/`WindowType` rough-opening size + the wall
    assembly's `FramingSpec` — so openings can't be placed where the framing physically
    can't fit.
- **Scaled underlays:** import an image or PDF page (survey, existing plan, hand sketch,
  parcel print) as a locked, dimmed layer under the canvas; calibrate by clicking two points
  and typing the known distance between them; drag/rotate to register. Underlays are
  view-only references — recorded in `preferences.toml` (path, transform), never emitted to
  any artifact. Shares the "reference geometry under the plan" machinery with the basemap
  import.
- **Wet-wall depth advisory (new):** a `Fixture` whose `needs` include `drain` hosted on a
  wall whose STRUCTURE layer is too shallow for its stack (e.g. a 3" drain in a 2x4 wall) is
  a warn finding with the required depth stated — the "too narrow places for plumbing"
  problem caught at design time. Joins `checks/advisory/` (→ 12 §Checks) once fixtures land
  in WP3.10.

## Workpackages

- **WP3.1 Catlin port.** `houses/catlin/` — declarative storeys (floorplans drawn in the
  UI), `params/` modules for arches + sunken garden extracted from `catlin_house.py` math,
  `preferences.toml`, notes migrated. **Then flip the `haus new` default template to catlin
  verbatim** (#22; `--template minimal` keeps the starter available).
- **WP3.2 Details ported as slices + transitions.** The five wall-section details become
  detail `Slice`s over the resolved catlin model plus the first `library/` `Transition`s
  (zero-overhang eave, basement↔framed-wall, sauna liner + base course, window
  head/jamb/sill flashing) with anchored overlay recipes, `ExaggerationSpec` for thin
  layers, references to resolved `ConstructionRule`s (web stiffeners, beveled plates), and
  bound notes. A Transition documents/validates the rule but never changes the resolved model
  (→ 11b, #45). **Per #43,
  two more library transitions land here: the rim-band air-sealing detail (storey-stack
  condition) and the stack-width-change shelf detail (catlin's 2x6 → 2x4 jog)** — with
  continuity declarations so the control-layer walk passes vertically. Transition-coverage
  check live on catlin.
- **WP3.3 Elevations/sections.** Geometry-iterator projection per §Elevations above.
- **WP3.4 Schedules + full sheet composer.** Door/window + plumbing-fixture schedules, sheet
  index, code summary (#32 wording), energy sheet, **S-100 foundation plan and A-104 roof
  plan**, smoke/CO + egress life-safety symbols on floor plans, the full sheet set above;
  `haus print` end-to-end.
- **WP3.5 Basemap import + underlays.** Parcel/contour GeoJSON → reference geometry in UI +
  C-101 site plan; **scaled image/PDF underlays** with two-point calibration.
- **WP3.6 Structural checks + bearing view.** I-joist span table (18-ft catlin spans),
  header sizing, frost-depth check on footings; `haus explain --bearing` + the UI load-path
  overlay (derived — walks bearing refs, geometry, and #43 stack edges, → 11 §Foundations).
- **WP3.7 Migration equivalence test.** Compare new-engine catlin IFC against old-model
  semantics — element counts/volumes/placements by category, generalizing
  `tests/test_catlin_house_ifc.py`.
- **WP3.8 MN submittal checklist as a check** + docs (permit guide); archive old repo.
- **WP3.9 Library contribution seam.** Per-item validation CI for `library/` (schema check +
  render smoke test per item), CONTRIBUTING.md documenting the promote-from-house-to-library
  PR flow (→ 02 §Git topology). **Curated STC partition presets (#50)** land here: a handful
  of interior partition assemblies transcribed from published tested data (single-stud +
  mineral wool, resilient-channel, staggered-stud, double-stud; double-gyp variants), each
  with `stc` + its test-reference `source` note, framing truthfully via the → 11 partition
  layouts. Shipping these flips the acoustic-adjacency advisory (→ 12 §Checks) from
  off-by-default to available.
- **WP3.10 UI intelligence pack.** `Furniture` + `Fixture` models with starter
  `FurnitureType`/`FixtureType` library entries; **furniture mesh import (#49):**
  `haus import furniture <file.glb|.gltf|.dae>` (trimesh) writes a `FurnitureType` with the
  mesh as a `.glb` sidecar, footprint auto-derived (projected outline, simplified) and height
  from the bounding box — clearance zones and `needs` filled by the user/agent afterward;
  the 3D panel renders the mesh, plans render the footprint symbol, core-LOD IFC emits
  `IfcFurnishingElement`. This is the IKEA/3D-Warehouse path (docs cover downloading
  glTF/Collada or converting .skp); imported Warehouse meshes stay house-local — `library/`
  furniture must be original or redistributably licensed. Also: `Alarm` elements + R314/R315
  placement check; sun indicator; space dashboard + storage ratio; service filters; clearance overlays
  + framing bumpers (with their warn-tier checks); kitchen work-triangle advisory (unblocked
  by fixtures landing here); **wet-wall depth advisory** (above); **`FloorHeat` end-to-end**
  (serpentine plan rendering, slice dots, wire-length/mat takeoff, fixture keep-out warnings
  — keep-outs need the fixture footprints landing here).
- **WP3.11 Roof designer panel (#29) + roof/gable framing.** **Strictly gable/shed** —
  pitch/ridge/bearing selection, live section preview showing the roof assembly, attic
  headroom shading (the ≥ 5' / ≥ 7' R305 zones over the floor below), overhang entry where
  **0 is a first-class value** (catlin; per-edge overrides), `FollowRoof` ceiling resolution +
  R305 check wired through, `Roof(...)` writeback; **activates the framing solver's raked-top
  arm (→ 11 §Framing solver):** `ToRoof` walls frame with individually-cut gable studs and
  sloped top plates, roof planes frame rafters from the roof assembly's `FramingSpec`
  (birdsmouth/bearing via `ConstructionRule`), rake overhangs get ladder/lookout framing, and a
  roof-assembly `FURRING` layer frames battens/counter-battens via the same furring path
  (vented over-batten metal — catlin's hot roof grows none) —
  all feeding the S-101 sheets, section slices, 3D view, and takeoffs; golden gable-end
  fixtures join the framing matrix; valley-requiring footprints and other unsupported forms
  (→ 10 §Element model) detected and rejected with findings; out-of-range attic
  configurations render red with the code ref, same as stairs. Exercised end-to-end by the
  catlin attic.

## M3 acceptance

New-engine catlin IFC is semantically equivalent to the old one (WP3.7 test); the catlin
attic is modeled as a habitable room under a `FollowRoof` ceiling passing R305, over
foundation elements that appear on S-100; **the attic gable-end walls frame with raked studs
and sloped plates, visible in the section slices and counted in the takeoff** (→ 11 §Framing
solver); an imported 3D-Warehouse furniture mesh (`haus import furniture`) places in a room,
renders in the 3D panel, and shows its footprint + clearance overlay on the plan (#49); the hallway duct soffit shows framed in 3D, dashed
on the floor plan, and passes per-room ceiling checks; slab `FloorHeat` zones appear on plans
and in the slab detail slice with wire-length takeoffs; **every derived boundary condition on
the catlin model is transition-covered**, and bumping the exterior CI from 2 to 3 layers
re-flows the eave and basement details without hand edits; **the side wall line's
2x6 → 2x4 → 2x4 stack resolves with sheathing-plane continuity (#43/#44), its storey-stack and
stack-width-change conditions are transition-covered, and the air-barrier continuity walk
passes vertically from foundation to roof**; `haus print` produces a complete permit PDF
passing the encoded MN checklist; `haus print --handoff` produces the full architect bundle
(verified by import into Bonsai/Blender — the tested target, #48, → 02 §Verification);
old repo archived.

## Risks owned

- **Risk 3 — permit-quality elevations/sections.** Mitigation pattern: §Elevations above —
  scheduled last, prior art reused, silhouette quality bar stated honestly.
- **Risk 7 — overlay/transition anchor robustness** (shared with → 11b): WP3.2's golden-image
  sweeps (CI thickness bumps, layer swaps, lining overrides) re-render every library
  transition; the M3 acceptance CI-bump clause is the end-to-end version of the same test.

## Open questions — resolved in this doc

- **Where the old detail scripts go** → §Details and sheets (reauthored as slices +
  transitions; primitives arrive via the ported `detail_utils.py`).
- **Is electrical required for permit acceptance** → §Details and sheets (no — E-101
  composes from annotations when present; smoke/CO alarms *are* required and are elements +
  a check).
