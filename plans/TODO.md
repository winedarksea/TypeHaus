# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Remaining Work
M2 variants/compare: the engine + CLI side is in (`variants.toml` declares named variants —
assembly swaps and layer-thickness overrides; `haus variants list|compare|assemblies` builds
them and reports element, takeoff, R-value/thickness and check deltas; `#53` assembly delta
compare included). Still missing: in-plan forks (`variant_of`/`active`/`forked_from` on
storeys, one-active integrity check, promote-with-uid-remap) and the UI's side-by-side
compare canvases (→ 21b §Variant compare).
M3 details are incomplete: Catlin has transitions, but no authored detail Slices. The permit composer emits placeholder/generic sheets; S-100/S-101 are reused floor/energy views rather than complete foundation/framing sheets ([sheets.py (line 30)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/emit/draw/sheets.py:30)).
M3 site work is incomplete: no parcel/contour GeoJSON basemap support.
M3 equivalence now *is* an old-IFC semantic comparison: the archived builder's export is
committed at `packages/engine/tests/fixtures/catlin_reference/catlin_house_reference.ifc.gz`
and `test_catlin_equivalence_m3.py` diffs both models entity by entity through
`typehaus.diff.semantic` / `.equivalence`. The declared design constants moved to
`test_catlin_contract_m3.py`. Open follow-up surfaced by it: the IFC export gives
`IfcBuildingStorey` neither an `Elevation` nor a placement, so storey elevations cannot be
compared at all.
Catlin’s full checks still report two failures and 13 building-science UNKNOWNs. The declared permit-check passes only because it intentionally covers a narrow subset.
M5 is not acceptance-complete: condensation analysis lacks material permeance inputs, producing UNKNOWN results ([plans/50-m5-science.md (line 61)](/Users/colincatlin/Documents-NoCloud/TypeHaus/plans/50-m5-science.md:61)).
Emplace furniture (3d files from library or imported models) and able to move furniture. Ideally double click on an view/modify details as appropriate.
Need to be able to cleanly turn parts on/off in the 2d and 3d views, either by trade (ie plumbing on/off) or by role (ie hide the floors in the 3d model so we can see clearly stairway continuity across levels). Another toggle (defaults to on), is for the to 2d viewer of the house plan (ie catlin house) to clearly show the name of each room/area (or perhaps unique id if name is missing), such that a user can easily vibe code a change to that area with the text/id as a reference.

French/double-swing doors now render in the 2D plan (PNG + UI), the 3D Panel3D view, and
are editable via a click-to-open door settings popover (type, hinge/swing, position, sill
height). Panel3D cuts real per-opening voids (jamb-split wall layers) and draws a frame +
panel — a full-width door panel or glass pane for single-operation openings, or two leaves
split at a center mullion when the door's type is `double_swing` — see
`Panel3D.tsx:buildOpening`. Still missing: the static glTF export
(`emit/gltf/emitter.py:_add_wall`) is untouched and still cuts plain void rectangles with
no frame/panel/leaf geometry at all.

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

### Editor

- Anchor-relative annotation drag → PatchOp editor; the v1 detail viewer is read-only.
- 3D model naviagation (pan, zoom) is functional but awkward. Also the "default zoom" for reset is poorly calculated (I always find myself clicking the right arrow and the down arrow a bunch to get to a better starting view)
- The "air", "water", and "thermal" views are great ideas but don't seem to show much on the actual 2d ui for catlin house.
- Door opening drawings in 2d view aren't very accurate. The swing lines aren't always accurately concave and the double doors often look a bit weird (one convex, one concave for the swing lines)
- the "site earth" plane interests interior spaces where it should be excluded. It excludes house already, but should also exclude sunken garden and garage.
- Have UI buttons to show assembly details (ie transitions) and the BOM of all parts. Perhaps replacing the rather useless "analyze" and "design" buttons which functions they have can be broken into Views toggle options

### Framing follow-ups found while working on the above

- Most corners don't show proper 3-stud framing (it's defined in code but not present in
  most corners).
- Windows smaller (by 1.5" I believe) than the stud spacing (here 14" probably should fit between 16" oc studs) don't need a header. Furthermore, we probably want windows to have some more clear guidance on when they are breaking the stud line with their position awkwardly, and how many studs they break with their given width (relative to the configured OC framing spacing)

### Roof-eave follow-ups (noted out of scope in the roof-eave pass)

- **IFC roof stays a flat plate.** `emit/ifc/emitter.py::_emit_roof` extrudes the footprint at
  `eave_z_m` and ignores `layer_edge_setbacks` entirely (TODO comment in place). Port the
  setback-aware shell when the IFC roof gains faceted plane geometry.
- **Garage/truss roof deferred.** `deck_rise_m` returns `None` for truss-framed assemblies, so
  RF-GARAGE keeps `eave_z_m == plate top` (its raised-heel lift is the correction) and gets no
  layer setbacks — its edges are still closed by the wall-skin band, per the note under
  "Framing interference" about `W-G-E`'s un-splittable gable. Garage gutter/drip trim is
  likewise unauthored.
- **Rake clip rules are extrapolated.** The golden reference draws the *eave* only, so the
  west/east-vs-south/north setbacks for a rake come from applying the same wall-stack clip
  faces there. A rake detail drawing would confirm (or correct) them.
- **Layer end faces stay perpendicular to the slope**, not vertical as the 2D detail draws
  them: the mitered offsetter is what gives each layer its true thickness. The serialized
  setbacks are drift-corrected (`d·sinθ` at the eaves) so the edges land at the right *plan*
  positions, but the cut face itself is still raked.
- **No closed-cell spray-foam wedge at the roof/wall foam interface.** The reference cuts the
  wall foam flat at one elevation and fills the resulting angled mismatch against the sloped
  roof foam with spray foam. Each closure band here instead follows the slope at its own
  layer's plan position, so the mismatch never forms — the idealised version of the same
  detail. Modelling the wedge means modelling the flat cut first.
- **The roof-edge cladding band is a flat panel, not a formed edge.** It closes what the
  reference leaves to the drip edge and the flashing behind the box gutter, but a real
  standing-seam edge is a formed cleat + hemmed drip, and the band's four runs simply lap at
  the corners. Fine at model scale; a detail drawing would want the profile.
- **The rake is still extrapolated.** The reference draws the eave only, and its answer there
  is the gutter. At a gable the same band stands in as rake trim, which is real construction
  but not something the reference confirms.
- **Gable-end skin still reads as insulation from inside.** The wall→roof closure carries the
  full weather skin (zip-r sheathing, rainscreen, cladding) up the garage gable, which is
  right — but with the roof trade hidden the zip-r band is the outermost thing left and looks
  like cavity fill in a garage that is only insulated at the ceiling. Only a rendering
  ambiguity, not geometry; a per-layer visibility control would settle it.

### Stair framing follow-ups (noted out of scope in the stair-framing pass)

- Coincident trimmer plies and unsized single-ply I-joist opening headers in
  `resolve/floors.py:134-153`.
- **Framed-wall ledger emission.** `resolve/stairs.py` `_bear_stair_on_walls` now annotates a
  stringer/rim borne by a framed wall with `framed-wall-ledger:{tag}` but emits no member, so
  the take-off is missing the 2x ledger a framer actually installs. A wall's `axis` is its
  *centreline*, so any band drawn on it would be invented geometry inside the stud cavity —
  blocked on D3 below.
- **D3 — stair members are not inset to the host wall's finished face.** `_stair_fits_opening`
  validates the flight against the `FloorOpening` bbox, and catlin's openings are drawn to wall
  axes / outer faces rather than to the finished well. Measured: `FO-S-STAIR` offers 84", but
  the finished well between `W-M-STRW`'s and `W-M-C5`'s stair-side gwb faces is **77.25"** — the
  two 3'-6" flights are 6.75" too wide for their own well. **This, not missing annotation, is
  the real prerequisite for narrowing `checks/structural/interference.py`'s `_STAIR_SUPPORT`**:
  the ~80 whitelisted catlin contacts are stair members physically inside stud cavities, and an
  annotation does not move geometry. Once the inset lands, drop the stud kinds and plates.
- **D2 — winder narrow ends converge on a point**, so narrow-end tread depth is 0. IRC
  R311.7.5.2.1 wants 6" there; the newel now carries them structurally, but the tread outlines
  still meet at the newel centreline.
- **`sill` is absent from `_STAIR_SUPPORT`.** No catlin exposure today (none of the
  stair-adjacent walls hosts an opening), so a stair running past a rough opening would report.
- **Load path of a landing post is unverified.** `landing-post-*` lands on whatever deck is
  below it; nothing checks that deck is bearing. Belongs in the STRUCTURAL tier as a WARN
  advisory, not in `resolve_envelope_geometry` (whose contract is bad-ref findings only).
- Treads rendering as 1.5"-wide strips (cosmetic).

## Landing Page
* build landing page and app deployment for type-house.com and type-house.com/app. Likely include an install script link like /Users/colincatlin/Documents-NoCloud/MinimapPR/landing/install.sh alongside the fully web-backed PWA.
* catlin house should be loaded up by default for new users of the PWA

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

# Second Follow Up Set
- Raised garden: a 36" high garden that utilizes on the inside the top of the sunken garden retaining wall, and on the outside concrete retaining wall blocks


### New items surfaced while doing the work
- the 6x6 posts of the porch should be embedded in the CMU wall (using ABU66SS) and thus are a bit shorter (from the top of the railing wall)
- Sliding and pocket doors still fall through to the swing glyph. They now have enum values,
  framing dispatch and IFC mapping, but no dedicated 2D symbol.
- Foam thermal breaks between the sunken garden and the house are rotated the wrong way, need a 90 degree rotation (to be long side between house and garden) 
- Fascia/soffit runs overlap at the four rake corners instead of mitering.
- Wall framing members are not individually pickable (wall bodies are). Per-stud selection
  needs `InstancedMesh` instanceId picking plus a member-uid scheme the engine doesn't emit.
- Roof members still export to IFC as bare `IfcMember` aggregation with no geometry — the
  pre-existing behaviour for all roof framing, now inherited by the new closure/trim members.
- `emit/draw/floorplan.py` emits `Symbol(name="alarm")`, but `"alarm"` is missing from
  `_MARKER_STYLE` in `pdf_writer.py` and from `_add_symbol` in `dxf_writer.py`, so every
  smoke/CO alarm draws as a blue window-glass bar on the plan.
- `storey_outward_sign` is one scalar per storey derived from the largest closed loop, so the
  house basement and the sunken garden — two independent structures sharing a storey key —
  cannot have independent windings. A per-connected-component sign removes the bug class that
  `advisory.cladding_side_mismatch` currently only detects.
- The garage gable is closed by carrying wall skin to the roof underside rather than by real
  `top=ToRoof` gable walls: a raked wall top is a straight line, so a gable wall must split at
  the ridge, and `W-G-E`'s ridge is exactly where the 16' overhead door is centred. Accepted
  for now; a second pass on the roof/wall eave detail should revisit it.
- `Panel3D.tsx` (~1350 lines), `store.ts` (~650) and `emit/gltf/emitter.py` (~1190) are all
  well over the 500-line guideline and were left unsplit only to avoid cross-worktree conflicts.
  - **Radon Vent horizontal jog** is four stacked square bands, not a swept round section. The two
  risers are true 12-gons; only the jog still reads faceted.
  - there is a glowing red dot on the basement in 2d view, near the corner of ST-B2M and southern end of the wall W-B-STR. Some sort of warning, however you can't click on it to tell what it is, so it isn't very helpful in this form.
  - Very small windows that don't break the stud line don't need a header added. We added support for this, however the two studs to either side of these small windows (14" or so) are now missing, so another error here
  - The (NEMA 3R weatherproof) junction box on the exterior wall should be higher up (closer to CN-M-VENT-CLAMP)
  - Fascia are also part of the framing, and should be under that view toggle
  - Garage also needs its gutter on the south wall

  ## Hardware
  We want to better show the count of some critical hardware pieces in the BOM
  - How many structural wood screws we need to hold the furring strips (over the exterior insulation), currently mainly in wall type CATLIN_EXT_2X6. We expect these to be every 24" vertically and every 16" horizontal (16" oc matching the OC of the furring strips, which matches the stud spacing). This should be calculated accurately across floors. The roof needs the same thing done separately (it's the same OC spacing but longer screws).
  - count of joist hangers where they are needed (ie they hang on beam) which I believe is only the top ridge beam here (Simpson LSSR)
  - properly show 4 knee braces (the main corners) using 2x each APVKB45-6
  - Mudsill anchors (MASA, looks like about every 4 feet) and Embedded Strap holdowns for all sill plates on concrete
  - Stud-to-Plate Ties, Coil strapping across floors at corners, hurricane ties (H2.5A and H1.81Z as appropriate)

  ## General Polishing Tasks
- Make sure all warnings are cleared up
- Make sure the BOM shows all members listed out, grouped usually by size and type
