# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Needs your decision

These are blocked on a call only you can make, not on work. Everything else in this file is
work.

- **D2 — winder narrow-end tread depth.** The geometry is fixed: each winder starts where its
  own ray leaves the newel post's *face*, so the narrow ends are distinct rather than
  converging on a point. That buys **0.9"**, and IRC R311.7.5.2.1 wants **6"**. Three winders
  around a 4x4 cannot reach it. The fix is a layout choice — more risers in the turn, or a
  wider newel/well the winders wrap — not a number the generator can invent.
  `structural.winder_narrow_tread_depth` measures and reports the shortfall meanwhile.
- ~~**D3 — the catlin stair does not fit its own well.**~~ RESOLVED, both halves of the fix.
  `W-B-STR`/`W-M-STRW` moved from x=11' to **x=10'** and the basement wall went 8" → **12"
  concrete**, which puts the basement well at **7'-0" clear** (and the furnace room at
  8'-6" — both reference numbers off one wall). Every stair opening is now drawn to the
  **finished well** rather than to the wall centrelines, so the flights are laid out on the
  faces they actually run between: `FO-M-STAIR` on the basement concrete faces (7'-0"),
  `FO-S-STAIR` on the main floor's framed faces (7'-5¼"), each flight sized to fill its own
  storey's well so both outer stringers land on wall. Flights are **3'-3¾"** (basement) and
  **3'-6⅜"** (main), either side of the well partition, which now **occupies its real 4½"**
  instead of being budgeted at zero — that is what "7'-0" including the 2x4 partition" means
  geometrically. Landings are the R311.7.6 36" minimum, floored at the flight width.
  Knock-ons: `structural.member_interference` contacts that only the `_STAIR_SUPPORT`
  whitelist forgives went **315 → 226**, and the wall-cavity part of that is largely gone
  (`W-M-STRW` 24 → 9, `W-M-C5` 15 → 7, `W-M-N2` 16 → 5); the 226 that remain are mostly
  real intra-stair joinery (treads housed in stringers), so the set narrows but cannot be
  deleted. `structural.floor_opening_header` no longer fires on `FO-S-STAIR` at all.
- **Condensation boundary condition.** `building_science.condensation` now emits real results
  and reports 3 FAILs (`CATLIN_EXT_2X6`, `CATLIN_EXT_2X4`, `CATLIN_ROOF` — dew point at the
  sheathing at −15 °F / 35% RH). The walls are vapour-open mineral wool with no interior
  retarder. That is correct **for the boundary condition `plans/50-m5-science.md:13` mandates**
  (the 99% design hour). ISO 13788, which Glaser comes from, uses **monthly means** precisely
  because a design-day walk flags code-compliant CI walls; at Minneapolis' winter mean these
  same walls are comfortably safe. Whether this check is a pass/fail gate or a cold-snap
  screening signal is a plan decision — the implementation follows the plan as written.
- ~~**Knee brace count.**~~ RESOLVED — the balcony is now braced at its **4 corner pillars in
  both plan directions**: 8 braces, 8 `APVKB45-6`, matching the original "4 corners × 2" note.
  The old 12 was never buildable (every pillar is a beam *end*, so only one brace fits in the
  beam's plane; the "matched pair per joint" rule assumed a beam continuing past its post).
  The real gap was that all six connectors were `axis="y"` — the freestanding deck had **no
  E-W lateral system at all**, and no E-W member to brace against. Two `2-2x8` girts
  (`BM-SG-GIRT-R/F`) now run the pillar rows under the N-S beams to give the E-W braces a
  soffit. Braces are 2x6 wood diagonals with a 3' leg, through-bolted, APVKB at the joint;
  the centre pillars stay unbraced leaning columns so thrust never lands on `PT-SG-BR2`,
  which bears on the porch decking rather than on grouted masonry.
- **`RM-M-BATH1` is too small.** Clear face is 3'-2" × 4'-3¼". A 2'-6" WC plus a 1'-9" lav is
  4'-3" of that 4'-3¼". The fixtures now pack wall-to-wall with ~⅛" at each end and nothing
  between them. The design fix is a bigger bath or no lav.
- **`D-G-OVERHEAD` needs an engineered header.** The 16' garage door exceeds the prescriptive
  table. A genuine engineering input, not a modelling gap. ANSWER: Double-Ply 14" LVL
- **`advisory.window_size_variety`** — 10 unique window sizes. Fewer eases ordering; whether
  to consolidate is a design call. ANSWER: for now, consolidate down to one size per width
  Note: most common window widths here are sized to fit with a given number of stud breaks in the 16" OC framing spacing here.
- **Phase 2 junctions** (own section below) — every item there is construction-rule authoring
  that needs your intent, not mechanical work.
- **`install.sh` installs a package that does not exist.** `landing/install.sh` runs
  `pipx install "typehaus[server]"`, but `typehaus` is not on PyPI. Either publish it or drop
  the install link; `/app` (the PWA) does not depend on it.

## Remaining Work

- **M2 variants/compare — engine + CLI in, UI + forks missing.** `variants.toml` declares
  named variants (assembly swaps, layer-thickness overrides); `haus variants
  list|compare|assemblies` builds them and reports element, take-off, R-value/thickness and
  check deltas, including the `#53` assembly delta compare. Still missing: in-plan forks
  (`variant_of`/`active`/`forked_from` on storeys, one-active integrity check,
  promote-with-uid-remap) and the UI's side-by-side compare canvases (→ 21b §Variant compare).
  `model.json` also does not carry the variant catalog — `model_to_dict` has no house
  directory to read `variants.toml` from; variants surface as `out/variants.json` instead.
- **No `$` ranges in the delta compare.** `prices.toml` (#28) is unimplemented everywhere.
- **IFC storeys carry no elevation.** The exporter gives `IfcBuildingStorey` neither an
  `Elevation` nor a placement, so the M3 semantic equivalence cannot compare storey
  elevations at all. `test_catlin_equivalence_m3.py` asserts the current state explicitly, so
  it will fail loudly and demand a real comparison once elevations are emitted.
- **Most IFC framing members still have no geometry.** Measured on the current export:
  **383 of 2005 `IfcMember`s carry a representation — and all 383 are roof members.** The
  roof case was fixed; **1515 wall members and 107 stair members are still bare
  aggregation**. Same class of gap, and it directly undermines the "clean export to
  Revit/SketchUp/IFC" reminder at the top of this file: a consultant opening the IFC sees an
  empty stud wall. Port the swept-solid emission the roof members now use
  (`emit/ifc/roof.py`) to wall and stair framing.
- **Opening details are never scaffolded.** 70 `opening_perimeter` conditions exist and 9
  overlay ids target them, but `derive_detail_slices` produces no slice for any (it requires a
  host wall + junction elevation). Same for the single `roof_ridge` condition. This is the
  largest remaining gap in detail coverage, and the fix is in `details.py` scaffolding, not in
  the vocabulary. Recorded in `UNDRAWN_RECIPES`.
- **Shower detail vocabulary** (`saunashowerdetail.json` `shower`: glass, recess, tile,
  backer, HRV duct) is undrawn. The four sauna items all draw.
- **Below-grade walls are modelled against outdoor air** in `energy.py`. Foundation UA is 915
  of 1,650 total — the biggest single inaccuracy in the block load. A correct fix needs ASHRAE
  below-grade F-factors or a design soil temperature, i.e. a new `Site`/`Preferences` input.
- **An unconditioned garage's clad walls still count as envelope** in the block load;
  excluding them needs room adjacency, not just storey occupancy.
- **Two library starter walls report UNKNOWN vapour permeance.** Their cladding layer carries
  `FramingSpec(1x4, vertical)` — it *is* a back-vented rainscreen — but is authored as
  CLADDING rather than a separate FURRING layer, so the rainscreen truncation misses it. Fix
  by re-authoring those two assemblies, or by sourcing a fibre-cement perm rating.
- **`lsl` and `fiber-cement` have no sourced permeance** and deliberately report UNKNOWN
  rather than carry an invented number.

## Catlin detail parity — remaining

The fidelity bar is the five hand-authored reference details in
`/Users/colincatlin/Documents-NoCloud/house/catlin-house/catlin_house/out/*_ifc.png`; the
scripts that draw them and the parameter dicts behind them are copied read-only into
`packages/engine/tests/fixtures/catlin_reference/` (see its README). Compare against
`houses/catlin/out/render/detail_*.png` after `haus render . --view details`.

**The drawing vocabulary is now largely present** — flashings (Z/L, drip edge, apron), box
gutter, vent path, insect screen, sill gasket, sealant beads, thermal-break wedge, birdsmouth
seat-cut and I-joist flange dashes all draw as polyline+hatch derived from resolved faces, and
`Transition.overlay` recipe ids now dispatch through `OVERLAY_RECIPES` (4 recipes) with
`UNDRAWN_RECIPES` recording the 9 that deliberately draw nothing and why. What remains is
**style and item alignment** against the reference drawings, plus the opening-detail
scaffolding gap noted above.

- **`assembly-change-jog` is deliberately undrawn.** The jog runs *along* the wall while the
  derived detail cuts perpendicular at the wall midpoint, so that junction is not in the cut
  plane. Drawing it would be linework describing something the view does not contain.
- **`interior_slab_drip_flashing` was built and deleted.** Every derivable gate fired on the
  wrong details, because `SL-M-DECK` (suspended deck over the basement) and `SL-G-FLOOR`
  (slab-on-grade) are geometrically indistinguishable — both tops at z=0, both with their own
  thickness below. The distinction is "is there enclosed space beneath", which needs storey
  elevations the resolved `Room` does not carry. (The *assemblies* now encode the distinction;
  the geometry still does not.)

### Model fields the details still want

- **French drain.** `FootingBedding` models the drain as a bare `drain_tile: bool`. It needs
  `drain_diameter`, `drain_rock_width`, `drain_rock_depth` (or a `DrainTile` sub-model). The
  reference fixes 4"; the values are pinned in `detail_components/config.py` with docstrings
  naming the field that should replace them.
- **Sill gasket** wants a `FramingSpec.sill_gasket` thickness (reference: 1/4").
- **Slab thermal break** wants a perimeter-edge layer on the slab assembly (reference: 1"). Sauna wall also has a thermal break.

## Phase 2 — Complete Catlin junctions

Phase 1 resolves same-assembly L/T/X geometry and ordinary exterior-wall/interior-partition
tees, and now resolves real corner squares from the junction solver's own output. Catlin
currently reports **zero** `integrity.junction_fallback` warnings. The remaining conditions
below are construction-rule authoring — they need your intent:

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

## Editor
- **Console noise:** `THREE.Color: Unknown color model var(--material-siding)` from
  `nordic/palette`.

## Framing follow-ups

- **Windows: 8 residual member-interference overlaps** (measured with the check's
  junction-proximity clear disabled — the honest metric). 4 at two L corners where the
  *neighbouring* wall's studs run 1.5" above the wall's plate stack (an elevation mismatch
  between walls, not a corner-layout bug), and 4 at one T where an opening's jamb pack sits at
  the junction. Both are outside the corner rule. Total went 138 → 8; corner-stud 17 → 0;
  T-junction stud-stud 88 → 1.
- `FramingPreferences.max_window_ro_unbroken_in` no longer drives the ideal-position choice
  (geometry does); it survives as the declared header-free width and feeds a fix hint.

## Roof-eave follow-ups

- **Rake clip rules are extrapolated.** The golden reference draws the *eave* only, so the
  west/east-vs-south/north setbacks for a rake come from applying the same wall-stack clip
  faces there. A rake detail drawing would confirm (or correct) them. Same for the rake trim
  band: at a gable it stands in as rake trim, which is real construction but not something the
  reference confirms.
- **Layer end faces stay perpendicular to the slope**, not vertical as the 2D detail draws
  them: the mitered offsetter is what gives each layer its true thickness. The serialized
  setbacks are drift-corrected (`d·sinθ` at the eaves) so the edges land at the right *plan*
  positions, but the cut face itself is still raked.
- **No closed-cell spray-foam wedge at the roof/wall foam interface.** The reference cuts the
  wall foam flat at one elevation and fills the resulting angled mismatch against the sloped
  roof foam with spray foam. Each closure band here instead follows the slope at its own
  layer's plan position, so the mismatch never forms — the idealised version of the same
  detail. Modelling the wedge means modelling the flat cut first.
- **The roof-edge cladding band is a flat panel, not a formed edge.** A real standing-seam
  edge is a formed cleat + hemmed drip, and the band's four runs simply lap at the corners.
  Fine at model scale; a detail drawing would want the profile. See
  `plans/standing_seam_design_hints.md`.
- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls: a raked wall top is a straight line, so a gable wall must
  split at the ridge, and `W-G-E`'s ridge is exactly where the 16' overhead door is centred.
  Accepted for now; a second pass on the roof/wall eave detail should revisit it.

## Stair framing follow-ups

- **Framed-wall ledger emission.** `_bear_stair_on_walls` annotates a stringer/rim borne by a
  framed wall with `framed-wall-ledger:{tag}` but emits no member, so the take-off is missing
  the 2x ledger a framer installs. **No longer blocked** — D3 is resolved, so `ST-M2S`'s outer
  stringers now sit exactly on `W-M-STRW`'s and `W-M-C5`'s finished faces, and a ledger band
  drawn there is real geometry rather than something invented inside a stud cavity. Port the
  hanger-band emission the concrete case already uses (`concrete-wall-hanger`).
- **Winders keep the `tapered tread` 1.5" band.** A trapezoid is not expressible as axis +
  band width in this IR, and a going-wide band would make the fan self-overlap.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in the
future.

## File-size debt (AGENTS.md wants < 500 lines)

- `ui/src/components/Canvas2D.tsx` — **1812**
- `ui/src/components/Panel3D.tsx` — **1652**
- `ui/src/state/store.ts` — **680**
- `packages/engine/src/typehaus/resolve/stairs.py` — **736** (a clean three-way split —
  straight / u-split-landing / winder — exists but is a large diff)
- `houses/catlin/plan/assemblies.py` — **523**

(`emit/gltf/emitter.py` is done: 1425 → 182 across 10 modules, GLB byte-identical.
`detail_components.py` and `takeoff.py` are likewise now packages.)

## General polishing
- Make sure new items get added to BOM

## Third Pass Follow Up
- Gutter TR-SG-GUTTER-1 needs to be moved up to align wih flashing TR-SG-DRIP-1 and the gutter needs to look like a gutter
- Slab SL-SG-PORCH should be replaced by decking like SL-SG-DECK, but be composite material instead of aluminum, and be shown in the viewer like wood
- The porch floor which is currently SL-SG-PORCH should show up in the 2d viewer on the "main" floor, and the deck floor which is currently "SL-SG-DECK" should show up in the second floor 2d floorplan. It might be awkward to do but inspectors will likely expect that as they align with those floor's doors.
- Porch knee braces should be painted white, and have a more accurate knee brace connector (a band between the beams, APVKB45-6, one at top and one at the bottom)
- Front beam (that runs E-W and is part of the front knee braces) needs to go properly on top of the 6x6 pillars, meeting the N-S beams cleanly (and likely sized down to 2x10 to match, it's for lateral stability, not holding up the joists above).
- It looks like the concrete sonotube (sunken garden up to porch near house) needs to be move slightly south so it doesn't overlap the house wall.
- Garage gable end walls (like W-G-E-CLOSURE-0-CLADDING) still have studs visible. Perhaps the framing just needs to push the gable end framing inward a tiny bit, or the cladding outward a tiny bit.
- Garage fascia boards should probably count as part of the framing
- Garage roof sheathing is visible around the fascia, likely the fascia needs to go up a tiny bit higher
- The garage should be much closer to the house.
- House roof really won't have fascia like RAKE-HI-1-FASCIA-1 nor RAKE-HI-1-EDGE-CLADDING. In reality, the furring strips of the siding will continue up to meet the furring strips of the roof very nearly, and it will be full continous standing seam siding and roofing (with a trim piece over the corner). It may be hard to show this, but in the real world standing seam panels will be pretty much constant from grade level, up to roof level, and across the house and down the other side.
- Switch all exterior walls to 2x6s, and remove the 2x4 exterior wall type (for simplicity). Note main floor is LSL, others are standard dimensional 2x6 (this can be a note, rather than a different assembly). This will require careful updates to make sure assembly details still match.
- At the corners where exterior wall meets exterior wall, use a 4 stud corner instead for framing (since we use outsulation, the extra strength here is worth it). That should just be the main four corners.
- Build out the kitchen with appliances and counters, make sure pantry is present (may need design layout help here)

- Align details and floorplans better
  - **Basement is done** against `catlin_floorplan/Colin House_Basement_Level 1.png`. Every
    clear dimension now matches the reference to within ¾" except the sauna's depth, and the
    stair shaft is enclosed the way the reference draws it (`W-B-STR` runs the full north-row
    depth, `RM-B-STAIR` claims the shaft, `D-B-STAIR` lets out into the workshop instead of
    through the mechanical room). Measured, reference → model:
    furnace 8'6" → **8'6"**; stair shaft 7'0" → **7'0"**; both playrooms 16'6" → **16'6"**;
    workshop west leg 7'6" → **7'6³⁄₁₆"**; sauna 8'0" → **8'0¹¹⁄₁₆"**.
  - **Sauna depth is the one deliberate shortfall**: reference 13'2½", model **12'6³⁄₁₆"**.
    Its north wall is held back so the aisle it leaves against the center wall stays
    **3'4³⁄₁₆"** — the `D-B-GYM` doorway lives in that aisle, and the reference gets its extra
    8" only because its walls are drawn 10" where these are 12" concrete + a 7⅝" liner stack.
    Going deeper means either giving up the workshop→gym door or accepting an aisle under 3'.
  - **Room areas on the plan sheets are gross, not net.** `Room.clear_face` is built on the
    wall *alignment* lines, so `RM-B-STAIR` reads 144 SF where its clear face is 115.5 SF
    (the reference says 115.67). The layout matches; the labels are measuring a different
    thing, and the name `clear_face` claims otherwise. Worth reconciling before the areas go
    on a permit sheet.
  - Main/second/attic have not been compared against their reference pages yet.
