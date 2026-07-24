# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Remaining Work
Still missing for full M2: variants/compare, full takeoff/BOM
The 3D UI builds geometry directly from model.json and renders furniture as boxes; it does not yet consume the planned glTF artifact ([Panel3D.tsx (line 7)](/Users/colincatlin/Documents-NoCloud/TypeHaus/ui/src/components/Panel3D.tsx:7)).
M3 details are incomplete: Catlin has transitions, but no authored detail Slices. The permit composer emits placeholder/generic sheets; S-100/S-101 are reused floor/energy views rather than complete foundation/framing sheets ([sheets.py (line 30)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/emit/draw/sheets.py:30)).
M3 site work is incomplete: no parcel/contour GeoJSON basemap support.
M3 equivalence is only hardcoded contract testing, not an actual old-IFC semantic comparison.
Catlin’s full checks still report two failures and 13 building-science UNKNOWNs. The declared permit-check passes only because it intentionally covers a narrow subset.
M5 is not acceptance-complete: condensation analysis lacks material permeance inputs, producing UNKNOWN results ([plans/50-m5-science.md (line 61)](/Users/colincatlin/Documents-NoCloud/TypeHaus/plans/50-m5-science.md:61)).
Emplace furniture (3d files from library or imported models) and able to move furniture. Ideally double click on an view/modify details as appropriate.
Need to be able to cleanly turn parts on/off in the 2d and 3d views, either by trade (ie plumbing on/off) or by role (ie hide the floors in the 3d model so we can see clearly stairway continuity across levels). Another toggle (defaults to on), is for the to 2d viewer of the house plan (ie catlin house) to clearly show the name of each room/area (or perhaps unique id if name is missing), such that a user can easily vibe code a change to that area with the text/id as a reference.

IFC openings (WP7 follow-ups): glTF core-LOD opening cutouts (windows/doors currently emit voids + fillings only in IFC, not the glTF core mesh); shared IfcWindowType/IfcDoorType so repeated openings reference one type rather than per-instance property sets.

French/double-swing doors now render in the 2D plan (PNG + UI), the 3D Panel3D view, and
are editable via a click-to-open door settings popover (type, hinge/swing, position, sill
height). Panel3D cuts real per-opening voids (jamb-split wall layers) and draws a frame +
panel — a full-width door panel or glass pane for single-operation openings, or two leaves
split at a center mullion when the door's type is `double_swing` — see
`Panel3D.tsx:buildOpening`. Still missing: the static glTF export
(`emit/gltf/emitter.py:_add_wall`) is untouched and still cuts plain void rectangles with
no frame/panel/leaf geometry at all.

Site grading should reflect code, "IRC says, within 10 feet of building's foundation, grades away from foundations is to be at a 5% slope. Impervious surfaces at 2%"

## Catlin detail parity — remaining

The fidelity bar is the five hand-authored reference details in
`/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/*_ifc.png`; the
scripts that draw them and the parameter dicts behind them are copied read-only into
`packages/engine/tests/fixtures/catlin_reference/` (see its README). Compare against
`houses/catlin/out/render/detail_*.png` after `haus render . --view details`. 
Right now, the details of the transitions still miss much of the item and style alignment with these reference drawings.

Done so far: cavity fill lives on the structure layer (parallel-path R, no polygon overlap,
IfcMaterialLayerSet summing to true depth); the sauna is a real wall type; exterior walls
span floor-to-floor with framing stopping at the top plate; detail crops/scale/anchoring are
fixed; hatches fill by material; below-grade grade/soil/drain components are derived.

### Drawing vocabulary still missing

Each item names the reference drawing it comes from.

- **Flashings** — `basement_to_framed_wall_detail_ifc.png` (Z-flashing at the sill,
  L-flashing at the slab edge) and `roof_wall_eave_detail_ifc.png` (drip edge, apron).
  Port `_flashing`/`_path_from_steps` from the reference `detail_utils.py` into
  `emit/draw/detail_components.py` and derive them from the resolved faces, the way the
  grade/soil components already are. Supersedes the older "gutter/flashing profiles as
  detail-component symbols" note — they must be polyline+hatch, not `Symbol`, because
  `Symbol` renders as a bare circle in `DetailCanvas.tsx` and a marker in `pdf_writer.py`.
- **Box gutter and vent path** — `roof_wall_eave_detail_ifc.png`. The eave is zero-overhang
  with a box gutter; neither the gutter nor the ventilation path is drawn.
- **Insect screen, sill gasket, sealant beads, thermal-break wedge** —
  `basement_to_framed_wall_detail_ifc.png`. The reference params fix the sill gasket at
  1/4" and the slab thermal break at 1".
- **Sauna and garage details have no components at all** —
  `sauna_basement_wall_detail_ifc.png`, `sauna_shower_basement_detail_ifc.png`,
  `garage_wall_detail_side_ifc.png`. The sauna's benches, heater clearance, floor slope and
  drop ceiling are all in `saunashowerdetail.json` and none are drawn.
- **Birdsmouth seat-cut** so the eave rafter reads as a notched member (currently a straight
  raked bar), and **I-joist flange dashes** in section.

### Sheet composition (Phase 3d, not started)

- **Dimension strings.** `ArchDimension` nodes for what the reference dimensions — total CI,
  XPS layer count × thickness, footing width/depth, stud depth — derived from resolved layer
  thicknesses. Today a detail carries only the per-layer callout ladder.
- **Legend.** One swatch per distinct material in the scene with its resolved thickness,
  in a reserved band. Now that hatches carry `material`, the data is there.
- **Notes column.** `Transition.notes` points at `houses/catlin/notes/*.md` and only the
  *filename* reaches the drawing. Load, wrap and lay out in a right-hand column — port
  `load_markdown_notes`/`_wrap_notes` semantics from the reference `detail_utils.py`.
- **Title / attribution block** from `model.plan.project`.

### Model questions surfaced by the details

- **Per-layer corner junctions — Phase 1 complete.** Same-assembly L/T/X nodes and ordinary
  exterior-wall/interior-partition tees now resolve per layer and feed 2D, 3D, DXF, and IFC
  from the same polygons. Mixed/high-valence Catlin construction details remain in the
  Phase 2 list below.
- **French drain diameter has nowhere to live.** The reference fixes 4"
  (`basementconstruction.json`), but `FootingBedding` models drain tile as a bool.
  `detail_components.py` hardcodes the 4"/10"/8" drain and rock dimensions; they should come
  from the model once the fields exist.
- **`Transition.overlay` recipe ids are unused.** `zero-overhang-eave`,
  `basement-framed-wall`, `rim-band-air-seal`, `stack-width-shelf` etc. are authored in
  `houses/catlin/plan/transitions.py` and printed, but nothing dispatches components off
  them. That dispatch is how the per-detail vocabulary above should be wired.
- **Opening void lines run the full crop height** in details where the cut passes through a
  window (visible as long blue verticals in the foundation detail). They are inside the crop
  and dimensionally correct, but at detail scale a glazing centreline through the whole
  drawing reads as an error; the cut should show the actual jamb/head/sill instead.

### Phase 2 — Complete Catlin junctions

Phase 1 resolves same-assembly L/T/X geometry and ordinary exterior-wall/interior-partition
tees. The remaining Catlin conditions intentionally emit `integrity.junction_fallback`
warnings and conservative non-overlapping geometry until their construction rules are
authored:

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence Catlin nodes with explicit
  bearing and layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions, including membrane laps,
  sealants, flashing, and thermal-control continuity. `Transition` remains post-resolve
  documentation and must not mutate construction geometry.
- Add `Node.junction_override` only if the Catlin audit proves an assembly/interface rule
  cannot express a real condition.
- Re-import the completed Catlin IFC/DXF in Revit and SketchUp and verify scale, storeys,
  wall categorization, openings, layer returns, and the absence of gaps or overlapping faces.

### Editor

- Anchor-relative annotation drag → PatchOp editor; the v1 detail viewer is read-only.
- 3D model naviagation (pan, zoom) is functional but awkward. Also the "default zoom" for reset is poorly calculated.
- Toast popups of done tasks don't have a 'clear' option
- The "air", "water", and "thermal" views are great ideas but don't seem to be hooked up to any real backend yet
- 3d model doesn't seem to show the gravel footing beds anywhere
- Door opening drawings in 2d view aren't very accurate. The swing lines aren't always accurately concave and the double doors often look a bit weird (one convex, one concave for the swing lines)
- improve the appearance of brick and masonry in the 3d viewer to be more accurate.
- the "site earth" plane interests interior spaces where it should be excluded
- clean import/export (so ship to another computer running this app)

### Framing follow-ups found while working on the above

- Most corners don't show proper 3-stud framing (it's defined in code but not present in
  most corners).
- Stairs aren't framed properly (no support for landings, note the basement stair is special in that it anchors off hangers from the concrete walls). Landings don't have a size input in the stair designer and aren't rendered correctly. The partition wall between the up and down sides of a U of stairs is also not present and not framed correctly. It actually looks like there are partition walls but they extend below the house's foundation.
- Garage needs trusses for the roof instead (raised heel trusses)
- Roof-eave-wall still needs works. The 3d model still shows the roof exposed at the edges, not integrated into the wall cleanly (fully designed in reference packages/engine/tests/fixtures/catlin_reference/scripts/roof_wall_eave_detail_ifc.py, just not implemented here yet fully)
- The framing of "floors" seems to be incomplete. The double top plates, rim joist, floor joists, subfloor, sole plate, and sheathing all need to follow proper platform framing conventions (and be counted by length buckets in the BOM). Sills and sill anchor positions should be improved as well.
- Windows smaller (by 1.5" I believe) than the stud spacing (here 14" probably should fit between 16" oc studs) don't need a header. Furthermore, we probably want windows to have some more clear guidance on when they are breaking the stud line with their position awkwardly, and how many studs they break with their given width (relative to the configured OC framing spacing)
- Support for adding blocking in stud line

### Other Catlin House
Sump with radon vent. This radon vent runs up the same mechanical space that the plumbing vent does. The radon and plumbing vent both exit near the attic ceiling, making a 90 degree (ish) turn outside, then 90 degrees straight back up where they are attached to the siding using standing seam clamps (S-5! or similar) and terminate 12" above the roof. Also running out here (mounted on the siding also with an S-5! clamp) is an outdoor-rated (NEMA 3R weatherproof) junction box on the exterior wall sealed with a gasketed, weatherproof blank cover plate.

## PWA
* bypass libcst entirely for the mutation path for fully offline PWA (high risk, deferred), pure python (needs to be efficient)
* isolate IFC export as a future extension. It should be feasible using the experimental ifcopenshell wasm build and possibly replacing pyproj if needed
* build landing page and app deployment for type-house.com and type-house.com/app. Likely include an install script link like /Users/colincatlin/Documents-NoCloud/MinimapPR/landing/install.sh alongside the fully web-backed PWA.
* catlin house should be loaded up by default for new users of the PWA

## Sunken garden / porch / balcony — follow-ups

The freestanding porch/balcony was redesigned in `params/sunken_garden.py` (16" arched
front wall with two arches + three piers; no north wall — the deck's north edge rides a 12"
sonotube column + two PT 2x12 back beams into the side-wall hangers; a white-brick/air-gap/
grouted-CMU/stucco masonry railing; six 6x6 pillars carrying three double-2x10 beams, 2x8 joists, and
aluminum decking; composite decking on the porch). Posts→IfcColumn, standalone Beams→IfcBeam,
and floor joists now resolve and render in glTF; deck slabs carry composite/aluminum
assemblies (material in glTF + IFC). Still deferred:

- **Arched opening voids.** DONE in resolve, glTF, the browser viewer, and IFC. `ResolvedOpening`
  carries `arch_rise_m`; glTF and the viewer emit continuous curved concrete heads, while IFC
  emits a vertical `IfcArbitraryClosedProfileDef` with a true circular curve swept through the wall.
- **Metal fascia-mounted balcony guardrail** as a first-class `Railing` element (model + resolve
  + emit + UI). The masonry railing is modeled (as a parapet wall); the metal guardrail is not.
- **PVC fascia, front gutter, front-edge flashing into the gutter, rear flashing into the house
  WRB** (detail layer; ties into the box-gutter/flashing items above).
- **Connector hardware** — joist hangers, hurricane ties, kneebraces (APVKB), standoff post
  bases — are text/notes only, not modeled geometry.
- **Fiberglass rebar dowels + 40 psi XPS foam thermal-break block** between the shared
  house/garden footings: recorded via `FootingBedding.cast_foam_in_aggregate` + a note; no dowel
  primitive in the schema yet. (The porch/balcony floor joists render in the 2D framing plan +
  glTF but are still not emitted as IFC members — same gap as the house floors.)
- **Per-component outward sign.** `resolve/orientation.storey_outward_sign` derives one scalar
  per storey from the largest closed loop, so the house basement and the sunken garden filed on
  that same storey key are forced to share a winding — every garden wall must be authored
  against the garden's own natural direction or its layer stack builds inside out (B5 fixed
  three by hand). Trace an outward sign per connected wall component instead, so each structure
  can wind independently; `advisory.cladding_side_mismatch` is the interim guard.

Very small windows that don't break the stud line don't need a header added.

## Current Orientation:
+X: east
+Y: north
+Z: vertical/up
will need to support rotating the house off axis in the future

## Framing interference (structural.member_interference)
The new model-wide `structural.member_interference` check (a WARN-tier regression guard)
now flags any two wood members that share plan area *and* interpenetrate vertically. The
sunken-garden deck bearing stack (post → beam → joist, with 6" cantilevered joist tips) is
fixed and reports **zero** findings. The check still surfaces ~2.6k pre-existing overlaps in
other, known-incomplete framing — corner/T-junction studs, doubled corner plates,
rafter-on-plate bearings, and stair stringer/tread joints. These are tracked to-dos, not the
deck fix; work them down here (or suppress `structural.member_interference` per-check in
`preferences.toml` until then).

## Follow Up after First Subagent Pass

Addressed across seven parallel worktrees (B1–B7). Most of the list turned out to be a
handful of shared root causes, not fourteen separate defects.

### Still open
- CMU look like bricks. They should look like full CMU.
- **Glowing red dot on the basement** — deliberately deferred, and the premise was wrong:
  there is no findings→3D marker system at all. `Finding` (`findings.py`) carries no
  coordinates and findings surface only as DOM rows in `IssuesDrawer.tsx`; the only red in
  the 3D palette is the masonry wall-layer colour. It is near-certainly a small brick sliver.
  Re-check now that white brick and per-solid selection have landed — every solid is
  clickable, so identifying it is one click.
- Sliding and pocket doors still fall through to the swing glyph — they need their own
  2D symbols (they do now have enum values, framing dispatch and IFC mapping).
- The vent's horizontal jog is four stacked square bands, not a swept round section. The
  risers are true 12-gons; the jog still reads faceted up close.
- Fascia/soffit runs overlap at the four rake corners instead of mitering.
- Wall framing members are not individually pickable (wall bodies are). Per-stud selection
  was scoped out; it needs `InstancedMesh` instanceId picking plus a member-uid scheme.

### Done
- ~~White (with gray mortar) brick as a colour option~~ — `white-brick` material clads the
  porch railing. Appearance is now *authored*, not guessed: `Material.color`/`Material.finish`
  ship in `model.json`'s catalog and outrank the substring family inference in both the viewer
  and the glTF export.
- ~~Arches are 'striped'~~ — two real causes. `createSmoothArchedWallLayerGeometry` bailed
  unless the polygon had exactly 4 points, and junction resolution leaves collinear vertices,
  so Catlin's arches always took the 32-stacked-box fallback; *and* both tessellators stepped
  the semicircle evenly in x, which collapses at the springlines. Both now reduce collinear
  vertices and walk the arc by angle, with the segment count solved from the radius against a
  0.5 mm chord tolerance. Also fixed `_thin_rect_edges`, which mis-measured **182 of 607**
  layers in the glTF export — the 16" arched wall exported as 8". IFC was already exact.
- ~~More items selectable~~ — solids, footing beds, roofs, floors, stairs and openings all
  register `uid` + `selectionKind` and raycast; `SelectionKind` widened to nine kinds shared
  by the store, the viewer and the exporter. Deleting derived geometry now explains itself
  instead of silently no-opping.
- ~~Garage door 2D look + framing; bifold doors~~ — `DoorOperation` is a closed enum,
  `door-overhead`/`door-bifold` symbols draw in the canvas + PDF + DXF from one shared
  geometry contract, and overhead doors get a span-sized jamb pack, a real engineered header
  depth and track framing.
- ~~Gable ends of garage (truss exposed)~~ + ~~fascia, raised heel, soffit~~ — the blocker was
  pipeline ordering: `apply_to_roof_wall_tops` ran in the envelope stage but truss framing
  lifted the roof plane by the raised-heel delta afterwards, so any `ToRoof` wall was raked
  to a stale plane. The lift now happens in the envelope stage. Gable triangles and the heel
  band are closed by carrying each wall's skin up to the roof underside (a `ToRoof` gable wall
  would have needed `W-G-E` split at the ridge, which is exactly where the 16' overhead door
  sits). `TrimKind.SOFFIT` + `EaveSoffit` are new; fascia/soffit derive from the resolved
  plane rather than authored absolutes.
- ~~Vents too high / not pipe-like~~ — termination is derived as 12" above the roof surface at
  the riser's plan point (27.14', was a hand-authored 33' — 2 ft above the ridge), guarded by
  a new `mep.vent_termination_height` check. Risers are round sections.
- ~~6x6 posts and beams not wood~~ — `buildSolid` hardcoded concrete grey for *every* solid.
  It now resolves assembly → material → colour with a category palette mirroring the
  exporter's. `Beam.assembly` added so beams can carry a finish like posts already could.
- ~~Weird walls beneath the foundation near the stairs~~ and ~~floors ~6" too low~~ — one bug.
  `UNIT_BOX` was base-at-origin on local Y only, so passing world-up into one of the two
  *centred* axis slots drew every horizontal member spanning `z0 ± depth/2`. An 11-7/8" rim
  landed 5.94" low; the U-stair well partition (basement −9' → main 0') drew −13.5' to −4.5',
  through the footings. The box is now symmetric on all three axes so no slot can be misused.
- ~~Masonry porch railing flipped~~ — `W-SG-RAIL-E` was authored NE→ME, mirroring the other
  two, so its stack built inside out; the same latent winding on `W-SG-E1`/`W-SG-E2` is
  corrected too. New `advisory.cladding_side_mismatch` guards the class of bug.
- ~~Ceiling lights sitting on the floor~~ — `mount_height` was authored on the lights but read
  by nothing except IFC, which then shadowed it with the floor elevation. `Mount` is now the
  single authoritative field (`mount_height` removed, 25 Catlin devices migrated), so glTF,
  the viewer and IFC agree.
- ~~Gutters and flashings not shown in 3D~~ — they were modelled, resolved and exported all
  along, just rendered as grey slivers by `buildSolid`. Now visible and selectable. (Roof-eave
  gutters/fascia are newly authored on the garage; before this only the balcony had any.)

### Found while working, fixed here
- Deck walking surfaces were embedded inside the top inch of their own joists — slabs hung
  below the storey datum while `FloorSystem.subfloor` sat above it. `Slab.datum`
  (`structure` | `walking_surface`) makes the choice explicit.
- Both guards measured 42" from the *structural* datum, so raising the walking surface left
  them 40.5" (balcony) and 41" (porch) above the deck underfoot. Both now measure a true 42".
- Merging B2 and B3 exposed a `resolve.framing` ↔ `roof_geometry` import cycle: the framing
  package root eagerly imported the solver and roof framer, so importing a *leaf* module
  dragged them in. Re-exports are lazy now, and `truss_chord_depth_m` moved to `profiles`.

## General Polishing Tasks
- Make sure all warnings are cleared up
- Make sure the BOM shows all members listed out, grouped usually by size and type
