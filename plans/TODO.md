# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

## Needs your decision

## Accepted, by decision (2026-07-31 warnings sweep)

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

- **The garage gable is closed by carrying wall skin to the roof underside** rather than by
  real `top=ToRoof` gable walls (`W-G-E`'s ridge lands where the 16' door is centred).
  Accepted for now. (The gable-closure studs now lie flat in the drop-truss plane — the
  visible-stud defect is fixed.)

## Breezeway — remaining niggles

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a `Beam` is a prism). If the wedge becomes a real element the fall moves into it. (It should be a 1" slope by angle of the framing, plus a east to west slope by a small wedge under the centerpoint of each rafter to slightly bend the polycarbonate)

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

### Items after Phase 6
- Confirm the default toilet's 28" body depth vs an elongated bowl (29–31")
- Make sure there is an electric outlet in the kitchen island where usable for appliances in accordance with code
- Add an outdoor, dark sky friendly light to the garage, outside near the garage door. We actually want to add "dark sky friendly" as an advisory check for all outdoor lights.
- Add an outdoor flood light mounted to the porch above the sunken garden, on the porch roof center column (might be able to share a circuit with the ceiling fan on the porch).
- FURN-M-MUD-CLOSET-S needs to be replaced by a fully framed closet (basically a new room). This should aim for 32" to 36" depth, if sufficient space.

Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Is the door opening inside the breezeway code compliant
- Edits in 2d don't always update all the necessary pieces (like when we switched a shower to showertub)
- Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?
- Add tracking costs in the UI (so BOM can show costs if known, possibly check off if/when paid, and extra items not present in the 2d or 3d model), and also tagging in exact chosen products (where not already explicit as a comment, ie a specific model of recessed light)
- Pantry
- Add the plant room wall types
- basement ceiling, some of this wood joists maybe
- study on first floor location adjustments
- Is there a way we can "star" certain details to include in drawings? Right now we have drawings for most (all?) transitions, even some that don't really need details (framers don't need a reference for generic internal framing transitions). It would be nice to have the UI highlight important details and exclude from the primary export any we think we don't really need to show.

### Drainage Outstanding
    is nominal, not computed from a soil infiltration rate.
  - Authored `FrenchDrain` runs beyond the derived bedding tile.
  - Siteplan drainage overlay, and a 2D plan pass for the drainage trade (3D-only today).
  - Flashing/fascia LF take-off: the drainage take-off bills gutter and leader by the foot, the rest of the edge-trim family is still solids-only.
  - RAINWATER / SEWAGE `IfcDistributionSystem`s for the authored plumbing pipe runs.

### Plumbing
- ~~Irrigation system for plants on upper balcony (frost-free hydrant, insulated metal pipe
  to PEX to reduce thermal bridging, silicone gasket, plastic mounting bracket, closed-cell
  spray foam); backflow preventer on the basement fixtures connection; lacquered copper
  where visible in the basement and PEX elsewhere; water-hammer arrestors at the washing
  machine valve; an accessible main shutoff; hot-water line insulation in the BOM; a lit
  shower niche in the master bath (Schluter-KERDI-BOARD-SNLT); a reverse-osmosis tap
  provision at the main sink~~
  Done 2026-08-01, as one pass, because seven of the eight items were the same missing
  element: the model had 44 authored `PipeRun`s and nothing that could say *"there is a
  valve here"*. `mep.hydrant_freeze_depth` said so in its own output — it emitted an UNKNOWN
  reading "the model has no valve or backflow-preventer element, so neither can be evaluated
  here" — and the rest of the list lived in this file.

  `PipeAccessory` is that element (`MAIN_SHUTOFF`, `SHUTOFF`, `BACKFLOW_PREVENTER`,
  `VACUUM_BREAKER`, `WATER_HAMMER_ARRESTOR`, `RO_STUB`, `PENETRATION_SEAL`), authored-only
  like `PipeRun`, with a small brass solid on the plumbing trade. It locates itself on its
  host run: an accessory with no authored elevation takes the run's invert at the nearest
  vertex, because a valve *is on* a pipe and a copied number goes stale. `PipeRun` gained
  `finish` and `insulation` beside `material` — three fields because they are three
  purchases, and folding them together would bill the same copper twice the moment one run
  was left bare. The house now carries 16 accessories; `haus check` is clean.

  **Two south-face wall hydrants, not one balcony hydrant** (owner's call, 2026-08-01):
  `FX-M-PORCH-HYD` on `W-M-S1` at x=12' and `FX-S-BALC-HYD` on `W-S-S1` at x=16'-8", with
  the plant room behind it. The proposed north-face hydrant was dropped — `FX-G-HYDRANT`
  already stands 26' off the north-west corner and reaches everything it would have. These
  are a different fixture family from the garage's: a **wall** hydrant's seat is inside the
  conditioned envelope and the barrel self-drains outward, so it has no bury depth at all
  and is never winterised, where the garage's **yard** hydrant puts its seat 6' down. Both
  hydrants are fed out of the second floor's joist space, because a supply cannot reach an
  exterior stud cavity from below: 12" of cast concrete (`W-B-S1`) stands directly under it.
  `notes/balcony_irrigation.md` has the routing and the penetration detail.

  The **material rule is geometric, not a tag list**, which is what the owner asked for:
  `mep.pipe_material_preference` (ADVISORY) asks what is *directly overhead* each basement
  supply segment. Cast concrete means the pipe is hung in the open and reads as finish;
  a framed floor means it will be covered. So swapping `SL-M-DECK` for wood joists retires
  the rule under it with nothing to edit, and a new trunk on the same ceiling inherits it.
  19 runs converted to lacquered copper; the finish half is waived on insulated runs,
  because a jacketed pipe's visible surface is the jacket.

  Also landed with it, because the checks asked: `mep.hot_water_insulation` (CODE,
  N1103.4.2 — 7 hot runs at 3/4"+ now author a spec), `mep.main_shutoff`,
  `mep.backflow_prevention` and `mep.water_hammer_arrestor` (CODE, one permit line between
  them), `mep.exterior_hydrant_protection` (ADVISORY), and `ApplianceType.quick_closing` —
  declared rather than guessed from a product name. That last one surfaced a real gap: the
  **dishwasher was taking hot water from a branch that never declared it**, so its 1.5 WSFU
  was missing from the trunk's load and P2903.5 had no supply to ask about. Fixed, and it
  has an arrestor now. New BOM sections `plumbing_specialties`, `install_parts` and
  `pipe_insulation`; new `DomesticColdWater`/`DomesticHotWater` `IfcDistributionSystem`s
  grouping the supply segments and their devices (`IfcValve` with the PredefinedType that
  says which valve it is, rather than the `IfcFooting` fallback).

  The niche light is `ED-T-LT-NICHE-SNLT` (mark **E1** — "Q" was taken), a wet-rated 24V
  variant of the cove tape, in `W-S-C2C` inside the tub-shower alcove.
  `notes/shower_niche.md` records the waterproofing tie-in — the board *is* the membrane,
  and the driver lead is the only penetration it may have.

  Deliberately left for later:
  - **No hose reel, hanger or splash block** at either hydrant, and no water leak/freeze
    `Alarm` anywhere in the house.
  - **The RO unit itself.** `PA-M-RO-STUB` is a capped 1/4" tee with no fixture and no
    fixture units — the provision, not the machine.
  - **A second niche in `RM-S-BATH1`**, which has a shower and no niche authored at all.
  - **SANITARY / RAINWATER `IfcDistributionSystem`s** are still deferred (see the drainage
    block above); only the two domestic-water systems landed here.
  - **`mep.backflow_prevention` grades hose connections only.** The basement's two dual-check
    preventers are reported where authored but are not *required* by the check — a general
    cross-connection survey (hose-end sprayers, the boiler fill that does not exist yet) is
    not encoded.
  - **The wall hydrants draw an `integrity.placeable_room_mismatch` apiece**, which is the
    true description of an exterior hose bib hosted by an interior room's wall rather than a
    defect. The model has no outdoor-room concept to file them under.

## Hardwood
- Need to calculate and show in BOM the square feet required for sauna wall cladding tongue and groove. Note the shower in the corner is tile on the two walls of its spash area, not wood. This is basswood.
- In the second floor suite bedroom, we are going to have four custom oversized 6.125" by 6.125" posts that sit in the stud framing line but extend out to level with the drywall on the west wall. We would like to show these here, a sort of "tudor framing", but this should not be a change to the wall assembly (while a deviation, it is still effectively part of the stud line as such)
- Room RM-A-STUDY is the only room that has full hardwood floors, we want the sq ft of hardwood floor needed there (it's oak).
- We want to calculate the board feet of walnut required to panel the walls of the small first floor study up to 36" high
- We may add other tongue and groove paneling on walls, floors, or ceilings, and want to make sure this is designed generally to support calculating necessary sq ft by need (split by species)

## Backup Power System Refactor
- Backup power should be a proper microgrid, with solar panels and a limited number of circuits.
- EG4 is likely the system we should spec to start with https://eg4electronics.com/categories/inverters/eg4-12kpv-all-in-one-hybrid-inverter/
- We are starting with the 12 kV size but want a calculation of how long we can likely run this system (assuming strong solar every other day), to know if we need to size up.
- EG4 sends a message to Sunspec-compliant RSD devices. Can do every other panel (sum VOC < 80V), possibly even every third panel for RSD. If you aren't roof mounted, probably still a good idea but you can just do the last one (+ end) in a string.
- What's on the backup the kitchen fridge and freezer, an outlet in the mechnical room (that does router and home assistant power), mechanical room lights (should be a small load), and the kitchen lights and a kitchen outlet (meant for charging phones, etc)
- What's on the backup behind a relay (or several relays, ie like the Shelly Pro 4PM) that we shut off when the battery is low and sun is not out: the smallest minisplit (9K BTU Sapphire R32), the heat pump water heater (just the heat pump part, no electric resistance heating connection to backup), and the sump pump
- Backup battery is in mechanical room. Paired with another heat rise alarm and a smoke alarm. Keep a 3' clearance from other devices. Inside a small utility closet using metal studs, and 5/8" Type X drywall.
- Code enforces a 40 kWh maximum indoors. UL 9540 battery certification required.
- We might in the future redesign this to use a car as the battery. We might also redesign this to place the enclosure in the garage. The code doesn't need to implement these but should be designed to make the switch easier in the future.
- Future improvements might be: high flow water spigot near battery, mechanical ventilation directly to exterior of cabinet.

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)
