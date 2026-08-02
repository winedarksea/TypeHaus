# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Needs your decision

(nothing right now)

- ~~**The building drain is at 3" and the basement's real load is now ~42 DFU.**~~
  **Done 2026-07-31, both halves.** The building drain is 4" whole-run (inverts stayed
  put — the 4" crown still clears the slab underside by 5.7" against the 1" bedding
  minimum; `SP-B-SLAB-MAIN`, `SP-B-CW-MAIN` and `SP-B-SEWER-EXIT` re-cast at 4"/6" with
  re-solved centres). And the class of error is closed at the engine: `mep.pipe_sizing`
  and the reader's fixture-unit rows now roll every drain's load up through the routed
  geometry (`resolve/mep.py::drain_tie_ins`/`accumulated_serves` — union by fixture tag,
  never a sum of branch loads), so a branch's DFU can no longer escape the main it
  discharges into by not being re-listed in `serves`.

## Permit + code sweep, 2026-08-01

Every blocking item in the `mn-2024` permit subset now passes: `haus permit-check` reads
**35 pass / 0 fail / 5 unknown**, and the five unknowns are the modelling gaps already
tracked below (handrail role, guard infill, window well, floor protection over the basement,
TPR discharge). The whole registry went 67 FAIL → 6, and all six survivors are decisions
already recorded on this page.

What changed, grouped by what the finding actually was:

- **Real deficiencies, fixed.**
  - GFCI: five dedicated circuits picked up breaker protection (CKT-SUMP, CKT-HA,
    CKT-KETTLE, CKT-DISHWASHER, CKT-LAUNDRY) and eight outlets on the two storey receptacle
    circuits became GFCI *devices*. The split is deliberate — CKT-RC-MAIN/SECOND each reach
    a whole floor, and nobody puts thirty outlets behind one 5 mA trip.
  - AFCI declared on the fourteen 120V 15/20A circuits E3902.16 actually reaches.
  - Safety glazing: all four glazed door types are tempered (R308.4.1 has no location test),
    and ten windows in hazardous locations moved to four new tempered twin types
    (`WT-1424-T`, `WT-2736-T`, `WT-3036-T`, `WT-3048-T`) — same RO, same height, same
    position on the module, so no facade or framing rule sees them.
  - The five wet-room ERV pickups are `EXHAUST` rather than `RETURN` and each states the
    20 cfm it is balanced to. A bathroom's air is thrown away, not recirculated.
  - `EQ-T-ERV` 197 → 210 cfm: the conditioned area had drifted to 5,115 ft2 and the ASHRAE
    62.2 rate with it, leaving N1103.6 one cfm short.
  - `D-G-SERVICE` now opens off the garage slab, with the ICF stem gapped to a grade beam
    under it — the same treatment `D-G-OVERHEAD` has always had. The "22" step at the garage
    door" that `params/breezeway.py` recorded as a deferred mismatch is closed.
  - **The breezeway was standing 3'-6" west of the door it exists for.** `params/breezeway.py`
    was written on 2026-07-27 against a house entry at x=4'-0"; the 2026-07-28 mudroom
    conversion moved `D-M-ENTRY` to x=8'-0" and nothing followed it. The enclosure's centre
    moved 4'-6" → 7'-3", midway between the doors as actually built. Its 4'-0" width cannot
    cover two doors whose outer jambs span 4'-6", so each door's outer 3" of leaf oversails
    the deck at one corner — accepted to keep the brief's three-sheets-one-cut enclosure,
    and both doors still clear R311.3's landing patch at 92%.
  - RM-B-PLAY-N got its fresh-air register back (old uid, old hole) and two more cans.
- **Design decisions taken with the user.**
  - `RM-A-WEST` is STORAGE, not MEDIA: 598 sf under a 4:12 cathedral whose only glazable
    wall is a 5' knee wall cannot carry R303.1's 8%, and the room joins RM-A-EAST/RM-A-DEN
    which were already storage for the same reason.
  - `WIN-S-BED1`/`BED2` widened 27" → 30" (`WT-3048`) in the east *bearing* wall, framed
    with the ordinary jack/king/header pack; `preferences.toml`'s bearing RO cap went 27 →
    30 with them. Margin against R303.1 is 0.05 sf — see the note in `storeys/second.py`.
- **Check bugs, fixed in the engine rather than papered over in the house.**
  - `code.E3902_16_afci` screened on rooms only, so it wrote up eight 240V circuits (range,
    dryer, three heat pumps, air handler, kettle, PV) that no AFCI breaker is made for. Now
    scoped to 120V 15/20A, which is what NEC 210.12 says.
  - `code.M1502_dryer_exhaust` demanded a duct from a *ventless heat-pump* dryer. M1502.1
    exempts listed condensing dryers; `ApplianceType.ductless` says so and
    `APPL-WASHER-DRYER-STACKED` sets it.
  - `code.R303_1_light_and_ventilation` had no Exception 1 path, so every windowless
    habitable room was a violation with no lawful answer. It now adjudicates the exception —
    6 fc of installed lumens (stated CU/LLF, both named in the message) plus mechanical
    outdoor air to the room from a whole-house system that meets its own rate — and reports
    UNKNOWN, never PASS, where an input is missing.
  - `code.R303_3_local_exhaust` read a shared trunk's `design_cfm` as one bathroom's
    exhaust. Rate now comes off `Register.design_cfm`, falling back to the run only where
    the run has exactly one terminal on it.
  - `mep.footing_clearance` measured the 45° influence line off construction joints in
    continuous concrete: splitting the south stem for the service door gave the hydrant line
    a "footing edge" 3" away that is not an edge. Abutting footings at one bearing elevation
    are now measured as one pour.
- **Data defect found on the way through:** `plan/circuits.py` had duplicate uids —
  CKT-HP1-AH and CKT-HP2 reused CKT031/032AAAA from the radiant-floor circuits. Renumbered
  to CKT036/037AAAA.

## Accepted, by decision (2026-07-31 warnings sweep)

- **The 200A service stays, and `electrical.service_load` stays failing at 220.9A.**
  Accepted rather than fixed: NEC 220.82 is a whole-house estimate and this house never runs
  range + spa + sauna + both EVs at once. The lever if it ever needs pulling is a second
  `LoadManagement` over `CKT-SPA` + `CKT-SAUNA` capped at 11,500 VA — they are mutually
  exclusive by use, and the 9,000 VA credit lands the estimate near 183A without touching
  the meter. (`LM-EV` already caps the two EV circuits; that credit is in the 220.9A.)

- **HP2 passes on real Gree data once supplemental resistance heat is counted
  (2026-08-01, workstreams W2 + W3).** `EQ-T-GREE-MULTI-U30` is the Gree
  MUL30HP230V1R32AO: 30,000 Btu/h at 47F, 23,500 Btu/h at the -15F design temp
  (interpolated between the datasheet's -13F/-22F chart points). Block load over the
  basement plus the main-floor bedroom/bath/living side is 30,764 Btu/h at design, so the
  condenser alone is short 7,264 Btu/h. W3 changed `mep.heating_capacity` to count the
  resistance heat inside a zone's rooms, which is real heat at design temp: FH-M-BATH2
  (500 W), FH-M-DINING (700 W) and EQ-M-FIREPLACE (1,500 W) total **9,195 Btu/h**, giving
  32,695 Btu/h available against 30,764 — **margin +1,931 Btu/h, PASS**. Supplemental heat
  is keyed by room and never opens a zone of its own, so it cannot be double-counted.

- **HP1 stays short by ~1,100 Btu/h at the design temp, accepted by decision.**
  `EQ-T-GREE-VIREO-GEN3` is the Gree VIR24HP230V1R32AO: 27,000 Btu/h at 47F (valid because
  it feeds the EQ-T-GREE-SLIM24 ducted air handler, not a wall head), 13,500 Btu/h at -15F
  design (interpolated, includes the ducted static-pressure derate). Block load over the
  attic plus the second-storey bedroom/bath side is 16,338 Btu/h. The only supplemental
  heat on that zone is FH-S-BATH1 (510 W = 1,740 Btu/h), so available capacity is
  15,240 Btu/h — **margin -1,098 Btu/h, FAIL**. Accepted rather than fixed: it is a 6.7%
  shortfall at the -15F design temperature only, the zone's own thermal mass and the
  stack effect from the (passing, +1,931 Btu/h) floor below cover the gap in practice, and
  the alternative is upsizing the condenser for a handful of hours a year. The levers if
  it ever needs pulling, in order of cost: a resistance element in the EQ-S-HP1-AH air
  handler (authored as another `supplemental_heat` type), a second radiant mat in
  RM-S-SUITEBATH, or the next Vireo frame size. Revisit if the blower-door result comes in
  worse than the 900 cfm50 the block load assumes.
  - HP3 (Sapphire) is unaffected: real data gives it +6,765 Btu/h margin, comfortably
    passing.

- **The basement and sunken-garden foundation walls exceed the plain-concrete unbalanced-fill
  limit, and stay failing until the engineer's schedule lands (2026-08-01, workstream W5).**
  The new `structural.foundation_unbalanced_fill` reads IRC Table R404.1.2(1) at the MN
  profile's presumptive GM soil class (45 psf/ft equivalent fluid), where a 12" *plain*
  concrete wall is good for 7' of unbalanced backfill:
  - 10 `CATLIN_BASEMENT_12` walls retain 9.0' — **FAIL**.
  - 5 `SUNKEN_GARDEN_WALL` walls retain 9.8' — **FAIL**.
  - `SUNKEN_GARDEN_ARCH_16` is 16" thick, past the table's 12" maximum — UNKNOWN, engineered
    either way.
  - The 6 `GARAGE_ICF_8` stem walls retain 3.5' against a 5' limit — PASS.
  - `RETAINING_BLOCK_12` (2.5') passes; the interior basement cross walls now author
    `unbalanced_fill=ft(0)` because they have soil on neither side, so they are not screened.

  This is expected and is **not** being papered over with an invented rebar spec. A 9'
  basement wall in Minnesota is a reinforced wall — it always was — and the model simply had
  no field to say so until now. Resolution: author `FoundationWall.engineering_spec` with the
  structural engineer's vertical reinforcement schedule when it arrives, which flips these to
  PASS citing the spec. Until then the FAIL is the correct reading: the prescriptive path
  does not cover these walls.

## Remaining Work

- **Handrail schema + real R311.7.8 check** (2026-07-31). `Railing` needs a
  role/kind (handrail vs guard) plus per-flight authoring before presence, 34"–38" height
  and continuity can be measured; `code.R311_7_8_handrail` reports the gap as UNKNOWN on
  every 4+-riser flight until then. (Headroom is now really measured —
  `code.R311_7_2_stair_headroom` samples the sloped nosing line plumb against floor/roof/
  soffit structure; `code.R311_7_1_stair_width` and `code.R311_7_6_landing_depth` measure
  the built members. The old check reported the arrival storey's nominal ceiling height as
  "headroom".)
- **Stair/well guard check (R312)** — next in line after headroom: classify each floor
  opening's edges as wall-backed vs open (against resolved wall faces), and require a
  `railing` solid path at >= 36" along the open ones. Measurable today from resolved
  geometry, no new authoring; catlin's RL-S-STAIR/RL-S-STAIRHEAD guards are the first
  real fixture.
- **In-plan variant forks + compare UI** (scoped out of the sweep by decision: catalog only).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.
- **Refrigerant linesets are unmodeled** — only the indoor→outdoor pairing is recorded
  (`Equipment.outdoor_ref`). (Heat-pump *condensate* is modeled as of the plumbing pass:
  `PR-M-COND-HEADS` drops the two main-storey wall heads through `SP-M-COND` to
  `PR-B-COND`, the collected air-gap line falling to terminate over the mechanical-room
  sink — which now has the drain that was the blocker. `EQ-S-HP1-AH`'s line down the
  second-floor chase is still undrawn.)
- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span`'s two genuine R507.5(1)
  overspans were closed 2026-07-31 by going engineered — see "Accepted, by decision".)
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

### Residuals from the 2026-07-30 batch

- **The mudroom 6" jog has to stay its own `Wall`** — a standing constraint, not a task.
  `resolve/topology.py` builds junction incidents from wall endpoints only, so the
  W-M-STOS2 tee needs a node both walls terminate at; merging the jog re-opens `N-M-STRJ`.
- **RM-S-PLANT has no fresh-air terminal, by decision (2026-07-30)** — a dedicated mini-HRV
  just for the plant room is under consideration. RM-S-STUDY2 likewise has no fresh-air
  terminal, by decision. `mep.ventilation_distribution` names exactly these two rooms and
  the test pins that set.
- **Workshop ERV intake is positioned off the light** `ED-B-WORKSHOP-PANEL1` ("over a
  bench") — no workbench placeable exists in RM-B-WORKSHOP yet; move the register when the
  bench is actually placed.
- **The ERV→System 1 fresh feed's vertical is undrawn.** `DU-S-ERV-HP-FEED` (2026-07-30)
  taps `DU-M1-ERV-SUP` in its FS-SECOND joist bay under the hall at y=12'-8" and runs in
  SF-S-DUCT's box to the wye behind `REG-S-HP-RET`, but the rise from the joist bay up
  into the soffit is not modeled (`DuctRun` carries no elevation) — same status as
  EQ-S-HP1-AH's condensate drop. Physically it wants the hall/bedroom wall corner furred
  or the soffit's east cheek; decide when the chase details get drawn.
- **Per-wall paint colour.** `latex-paint` over gwb is modeled (Class III, IRC R702.7.1) but
  `Layer` has no colour slot; a second colour needs a second paint `Material` plus per-room
  `wall_lining` overrides. Rationale in the comment above `_PAINT_FINISH` in
  `houses/catlin/plan/assemblies.py`.

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
  them; serialized setbacks are drift-corrected but the cut face is raked. Each closure band
  therefore tops out at its *own* mating face (`resolve/roof_edge.py::_closure_segment`), so
  the stack ends as a per-layer staircase and **no wedge-shaped gap ever opens for the
  closed-cell spray foam to fill** — modelling the wedge in 3D means modelling the flat cut
  first. The 2D detail *does* draw one (`emit/draw/joints.py` builds the quad and hatches it
  `spray-foam`, pinned by `test_transition_details.py::test_eave_has_per_layer_roof_bands_and_wedge`);
  it is the 3D model the wedge is absent from.
- ~~**The roof-edge metal is a flat band, not a formed cleat + hemmed drip.**~~ **Done.**
  `resolve/trim_bands.py::formed_edge_bands` gives the corner trim the cleat / face / hem a
  fabricator actually folds, the way `open_channel_bands` gives the gutter its U — so the
  piece reads as sheet with air behind it rather than as a billet as thick as the joint is
  deep. Pinned by `test_roof_gable_and_heel.py::test_the_corner_trim_is_formed_metal_not_a_billet`.
  Each of the six runs is now three members; anything counting corner-trim members counts 18.
  (House fascia itself is gone: siding and roofing are one continuous standing-seam skin with
  corner trim and a derived ridge-vent cap on house + garage. Seam/panel modelling proper is
  still out of scope — see `plans/standing_seam_design_hints.md`.)
- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls (`W-G-E`'s ridge lands where the 16' door is centred).
  Accepted for now. (The gable-closure studs now lie flat in the drop-truss plane — the
  visible-stud defect is fixed.)

## Breezeway — remaining niggles

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a
  `Beam` is a prism). If the wedge becomes a real element the fall moves into it. (It should be a 1" slope by angle of the framing, plus a east to west slope by a small wedge under the centerpoint of each rafter to slightly bend the polycarbonate)

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

### Items after Phase 6
- Confirm the default toilet's 28" body depth vs an elongated bowl (29–31") — the code
  clearance is already modeled separately (`_water_closet_required_clearance` in
  `library/placeables/fixtures.py`), so this is a one-line footprint question.
- It looks like beams BM-S-HALL and BM-M-HALL are not getting grouped as part of the framing in the view. Also want to double check that beams are properly considered as a type of framing, for example the hall beams should likely be defined similarly to RIDGE-BEAM, garage header HEADER-0, the porch beams such as BM-SG-BKW, and possibly some of the window and door headers. We also may have some cases where we have headers specified over windows or doors when a large beam
- Make sure there is an electric outlet in the kitchen island where usable for appliances in accordance with code

Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Is the door opening inside the breezeway code compliant
- No overhang roof 
- Outdoor hydrants plus more complete internal plumbing 
- Edits in 2d don't always update all the necessary pieces (like when we switched a shower to showertub)
- Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?
- Add tracking costs in the UI (so BOM can show costs if known, possibly check off if/when paid, and extra items not present in the 2d or 3d model)
- Pantry
- Add the plant room wall types
- Is there a way we can "star" certain details to include in drawings? Right now we have drawings for most (all?) transitions, even some that don't really need details (framers don't need a reference for generic internal framing transitions). It would be nice to have the UI highlight important details and exclude from the primary export any we think we don't really need to show.
- ~~Add french drains (sump pump, down spouts, around footings) and possibly a drywell (probably 6 feet or so deep) or two in the sunken garden (so we have more than the sump pump as options for getting water out from there)~~
  Done 2026-07-31: a `drainage` trade/toggle; the perimeter drain tile grew real geometry
  instead of being a bool; `FrenchDrain`, `Drywell` and `Sump.pump` are first-class; the two
  leaders that existed only in slope notes (TR-G-LEADER-E, TR-SG-LEADER-SE) are authored; the
  garage hydrant pit is a `Drywell` (DRW-G-HYDRANT) rather than a deepened footing bedding;
  DRW-SG-MAIN is a 6'-deep soakaway under the middle of the sunken garden with its top at the
  underside of the 42" bearing bed — the bed is a bearing course that happens to drain, *not*
  a drywell, and the two are now separate things — taking the balcony leader and the garden's
  footing tile, which cannot daylight 9' down; and the whole family exports as
  `IfcPipeSegment` / `IfcDistributionChamberElement` / `IfcPump` under one STORMWATER
  `IfcDistributionSystem`. (Drywell tags are `DRW-`: `DW-` is already the dowel prefix.)
  Deliberately left for later:
  - A second garden well, if percolation testing says one 5'x6' is not enough — the sizing
    is nominal, not computed from a soil infiltration rate.
  - Authored `FrenchDrain` runs beyond the derived bedding tile.
  - Siteplan drainage overlay, and a 2D plan pass for the drainage trade (3D-only today).
  - Flashing/fascia LF take-off: the drainage take-off bills gutter and leader by the foot,
    the rest of the edge-trim family is still solids-only.
  - RAINWATER / SEWAGE `IfcDistributionSystem`s for the authored plumbing pipe runs.

### Plumbing
Irrigation system for plants on upper balcony
		Frost free hydrant, insulated metal pipe, to PEX to reduce thermal bridging, silicone gasket, plastic mounting bracket
			This is probably a case to use closed cell spray foam to keep moisture off the cold metal hydrant part
Backflow preventer on basement fixtures connection
Pipes will be lacquered copper where visible in the basement. In other places, PEX.
Water hammer arrestors on valve for washing machine
Main water shutoff that is accessible
BOM include insulation of main hot water lines
Have lighting in the shower niche of master bedroom, it looks cool, Schluter®-KERDI-BOARD-SNLT
Provision for a reverse osmosis tap next to the main sink

### Other visual ideas
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)
