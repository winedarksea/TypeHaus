# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

*2026-07-25: the parallel-workstream sweep cleared most of this file (windows, 2x6, BATH1,
condensation gate, soil ΔT, IFC geometry, detail scaffolding, sunken-garden third pass,
ridge vents, fascia removal, Canvas2D split, variants/BOM/prices, PyPI prep). What follows is
what genuinely remains, with fresh measurements.*

## Needs your decision

- **D2 — winder narrow-end tread depth: the 6x6 newel is not enough.** Tried per your answer
  (ST-S2A authors `newel_profile="6x6"`, the engine consumes it): narrow-end depth went
  0.875" → **1.375"** (exactly half the newel's half-face). IRC R311.7.5.2.1 wants **6"** —
  shortfall **4.625"**. A post alone cannot close that; the remaining levers are more risers
  in the turn (a layout change to the RM-S-STUDY-2 opening) or a much wider well.
  `structural.winder_narrow_tread_depth` keeps measuring and reporting it.
- **NEW — `CATLIN_ROOF` fails the monthly condensation gate.** The ISO 13788-style monthly
  gate (now the pass/fail verdict; the −15 °F walk is a labeled cold-snap screen) shows a
  dew-point crossing at the rafter (93% through the layer) even at January *monthly means*
  (16.2 °F / 74% RH outdoors, 35% RH indoors). This is a real assembly finding, not a
  boundary-condition artifact: the hot roof's interior-side vapour openness vs. its exterior
  foam ratio needs a design pass (more exterior R, an interior retarder class change, or a
  sourced argument the check is missing).

## Remaining Work

- **In-plan variant forks + compare UI** (scoped out of the sweep by decision: catalog only).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.
- **`DuctSystem` enum lacks `EXHAUST`/`HRV`.** The shower detail vocabulary draws an HRV
  takeoff from `model.ducts`, but no real catlin duct can trigger it: `DuctRun` can only be
  SUPPLY or RETURN. Grow the enum, author the ensuite HRV run, and the SL-D-SHOWER slice
  (authored, cut x=5') picks it up. (`ResolvedDuct` also carries no z — the drawn takeoff
  elevation is a documented drawing convention.) Sharper now that the gas furnace is gone:
  `DU-M-ERV-SUP`/`DU-M-ERV-RET` *are* the ERV's balanced pair, modeled as SUPPLY/RETURN
  because the enum has nothing better to call them.
- **The ERV reaches the second storey only.** With no forced-air heat, those trunks are the
  whole fresh-air distribution — the main storey, basement and attic have no ERV terminals
  authored, and upstairs RM-S-SUITE still gets a return but no supply. Needs a distribution
  pass (supply to sleeping/living rooms, return from baths + kitchen). RM-S-BED2 is done:
  the survey re-spacing put the east bedrooms on equal 9'-0" bays and `REG-S-SUP5` landed
  in the middle one (2026-07-25); the four new rooms on that storey — RM-S-SUITEBATH,
  RM-S-VANITY, RM-S-LANDING, RM-S-NCLOSET — have no terminals either.
- **Minisplit sizing is unmodeled.** `CKT-MINI-1`/`-2` carry authored 4,800 / 1,500 VA and
  the equipment types are a large and a small condenser — no block load, no room-by-room
  capacity, no cold-climate derate at the design temperature. The three radiant zones, the
  fireplace and the garage heater (2026-07-25) are explicitly *not* sized to make up any
  shortfall, so this is the pass that decides whether the house is actually heated.
- **The second-storey fixture layout in `RM-S-ENSUITE` overlaps itself.** `FX-S-ENSUITE-WC`
  / `-LAV` / `-SH` are authored at (5,31), (6,31) and (5,33) with default footprints, so the
  WC shares 1.9 ft2 with the lav and 1.6 ft2 with the shower pan. `FH-S-ENSUITE`'s zone is
  drawn to clear their union, which survives any resolution that keeps them in that corner —
  but the room still wants a fixture pass. (`RM-M-BATH2`'s WC floats mid-room too.)
- **The service load estimate exceeds the service.** `service_load_summary` reads ~224A
  (NEC 220.82 optional method) against a 200A service / 225A panel. Driven by the two
  EV circuits at 13.4 kVA continuous plus sauna + water heaters — *not* by the electric
  space heating, which 220.82(C) selects against the minisplits rather than adding.
  Needs load management (an EV EMS per 625.42, or interlocking the sauna) or a service
  upgrade — it is a decision, not a rounding artifact.
- **The panel is out of spaces on paper.** 35 circuits, 13 of them 2-pole = 48 spaces
  against a 42-space enclosure. `Circuit` carries no slot assignment and nothing checks it,
  so this is a note rather than a finding: the 225A panel needs to be a 54-circuit one.
- **Authored gutter runs are still solid bars.** The *derived* eave gutters are open-top
  3-band channels now; `TR-SG-GUTTER`/`TR-RF-GUTTER` (authored `Gutter` runs in
  `resolve/accessories.py::_resolve_edge_run`) should get the same treatment. Exact recipe
  recorded in the roof-eave stream report (E5); purely visual.
- **`lsl` and `fiber-cement` have no sourced permeance** — deliberately UNKNOWN rather than
  invented. (The two library starter walls no longer need it for a verdict: their rainscreen
  is a real FURRING layer now and the Glaser walk truncates at the vented cavity.)
- **Polycarbonate has no authored vapour permeance** (five-wall extrusion ≠ solid-sheet ASTM
  E96 figures). Needs a sourced figure.
- **The sunken-garden porch and balcony decks are still `service="floor"`.** Exterior decks
  on posts/beams; should be graded against R507/DCA6 like the breezeway deck is.
- **KneeBrace paint is authored but not rendered.** `KneeBrace.assembly="POST_WHITE_PAINT"`
  is in the schema and the catlin plan; the diagonal resolves to a `FramedMember`, which has
  no finish slot — rendering the paint needs an IR + emitter change. (The APVKB bands are
  correctly black hardware.)
- **`diff/equivalence.py` storey keys are last-wins** over duplicate reference names (porch
  storeys shadow the house's "basement"); the equivalence test works around it via the
  `building` attribute — a cleanup could prefer the house building when collapsing keys.
- **Windows: 8 residual member-interference overlaps** (junction-proximity clear disabled —
  the honest metric): 4 at two L corners from a neighbouring wall's 1.5" stud/plate
  elevation mismatch, 4 at one T where a jamb pack sits at the junction. Outside the corner
  rule. (Historic: 138 → 8.)
- **`interior_slab_drip_flashing` detail gate** still needs "is there enclosed space
  beneath" (storey elevations on resolved rooms) to distinguish `SL-M-DECK` from
  `SL-G-FLOOR`.

## Phase 2 — Complete Catlin junctions (needs your intent — construction-rule authoring)

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence Catlin nodes with explicit
  bearing and layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions (membrane laps, sealants,
  flashing, thermal-control continuity). `Transition` stays post-resolve documentation.
- Add `Node.junction_override` only if the audit proves a rule cannot express a condition.

## Roof-eave follow-ups (accepted-for-now / awaiting reference drawings)

- **Rake clip rules are extrapolated** from the eave-only golden reference; a rake detail
  drawing would confirm or correct them (same for the rake trim band).
- **Layer end faces stay perpendicular to the slope**, not vertical as the 2D detail draws
  them; serialized setbacks are drift-corrected but the cut face is raked.
- **No closed-cell spray-foam wedge** at the roof/wall foam interface — the closure bands
  follow the slope per-layer so the mismatch never forms; modelling the wedge means
  modelling the flat cut first.
- **The roof-edge metal is a flat band, not a formed cleat + hemmed drip.** Fine at model
  scale; see `plans/standing_seam_design_hints.md`. (House fascia itself is gone: siding and
  roofing are one continuous standing-seam skin with corner trim and a derived ridge-vent
  cap on house + garage.)
- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls (`W-G-E`'s ridge lands where the 16' door is centred).
  Accepted for now. (The gable-closure studs now lie flat in the drop-truss plane — the
  visible-stud defect is fixed.)

## Breezeway — remaining niggles

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a
  `Beam` is a prism). If the wedge becomes a real element the fall moves into it.

## Stair framing follow-ups

- **Winders keep the `tapered tread` 1.5" band** — a trapezoid is not expressible as
  axis + band width in this IR. (These are also the only 3 of 2099 members without a real
  IFC representation, by design.)

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Items after Phase 4
- Ridge vent cap needs a proper shape (and white painted metal look)

- Polycarbonate on breezeway doesn't line up (it should cover the lower beam, and top plate should meet the side place in a shared channel).

- Flooring - let's make second floor bedrooms be carpet, hallways and bathrooms be LVP (luxury vinyl plank, really not so different from hardwood), and RMA-A-STUDY hardwood (oak).

- Frost Free Hydrant in garage
		Frost free hydrant and "hose down" area, in a code compliant way
			72" below ground, gravel sump, interior shutoff where it enters inside, Sleeved through slab
			Sealant on concrete
			Y34SS hydrant + extra coating + hose bib vacuum breaker (small screw on thing)
				Raise pedestal for this, so the sleeve entrance is not the salt water floor (ie melting snow and salt slush in winter)
			NO drain - Most places don't like. Have a gravel pit outside for a wash area and drainage

- Heat rise detector in garage, smoke alarm in each bedroom

- Sweep the BOM for anything newly added beyond placeables/floor-heat/glazing (all three now
  bill through `bill_of_materials`). Looks like some connectors/hangers/screw counts are made but not included there.

- the 2D drawing of the u-shaped stairs got messed up at some point. It's got weird splits on landings and uneven stair marks

- We need to change the raised garden. W-RG-BLOCK should form a U around the sunken garden up to the N-S plane of the balcony railing on the arched concrete. It's 3' wider than the sunken garden wall. For now we should also model it so it starts at the same height as the top of the sunken garden wall, and goes down 3' from there (that puts it mostly below grade, which is fine for now), with this change meaning W-RG-INNER can likely be deleted (W-SG-* replace it effectively).
