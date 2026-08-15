# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

### prices.toml has no materials-vs-labour field
Every row in `houses/catlin/prices.toml` is material-basis except [concrete] and
[wall_structure], which are $/cy placed — and the file says so only in prose at the top.
When real quotes come in they are usually materials+labour merged, and there is nowhere to
record which a row is, so pasting one in silently changes the basis of that section.

Options: (a) leave it as prose and keep quotes out of this file, (b) add an optional
`labour = "included" | "excluded"` per row, (c) split every row into `material` and
`labour` ranges. (c) is the honest one and the most work — most published prices cannot be
split, so most rows would carry a made-up division.


- ~~**PT-SG-BR2 bearing — reinforce locally, don't move it**~~ — **approved and authored
  2026-08-07.** `FloorSystem.reinforcements` is the way to author it: a
  `JoistReinforcement(at, plies, member, blocking, source)` on FS-SG-PORCH, whose `at` is
  read back off the pillar loop so the two cannot drift apart. The resolver finds the
  nearest joist line and emits 2 extra `sister_joist` 2x8 plies face-to-face toward the
  load — full length, cantilever included — plus 2 `blocking` members to the adjacent
  lines, all billing automatically. `CN-SG-TIE-BR2` (H2.5A, ~455 lb vs the ~0.45 kip
  demand) is the uplift tie at the W-SG-ARCH back-span bearing; the part was already in
  `library/hardware.py` and the price table, so nothing new to price.

  The check that was wanted also exists: **`structural.cantilever_point_load`** finds Posts
  standing in a FloorSystem's overhang band, and never passes silently — unmitigated is a
  FAIL advisory, mitigated is UNKNOWN, because the prescriptive span tables assume no
  cantilever point load and "reinforced" is not "verified". PT-SG-BR2 now produces exactly
  one UNKNOWN finding with all four mitigation arms matching. That advisory is the correct
  end state, not a residual.
- **2D-edit sync — fix design proposed** (investigated 2026-08-02). Root cause confirmed: a
  PatchOp rewrites one constructor; derived data recomputes, authored cross-references
  don't. `retype_placeable` (2026-08-01) already re-anchors wall-fitted placeables and
  scans tag references. Still open, ~3–4 days if approved: (i) authored refs +
  advisory checks for geometry-coupled consumers (`Slice.subject_ref`, `DuctRun.serves`),
  (ii) promote retype warnings to durable review findings, (iii) route *opening* retypes
  through a centre-holding macro (raw PATCH still slides them today).
  **Re-affirmed deferred 2026-08-07.** One slice of it did land, though — see "Moving
  toilet needs to move its flange too" below, which was the same class of bug with a
  concrete instance behind it.
- ~~**Detail stars fan out per-condition**~~ — **implemented 2026-08-07.** `Transition`
  gained `starred_conditions` / `unstarred_conditions` and a `stars(key)`: an explicit
  unstar wins over an explicit star, and the pattern-wide `star` stays the default for
  everything else, so nothing authored before this changed meaning. Catlin unstars the
  twelve interior rim/foundation conditions and keeps the envelope crossings; starred
  derived details go 24 → 12 of 39. The UI now sends one PatchOp and flips one entry (it
  used to flip every sibling, which made the wrong behaviour look deliberate), and
  `integrity.condition_star_override` catches an override key that stops deriving.

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

_Batch of 2026-08-15 — permit-completeness pass. `haus check` went 661/6/33 to **683 pass /
4 fail / 25 not evaluable of 712**, and the permit gate passes every one of its (now 46)
checklist items. Six rules were added, five were found to be over-reaching or reading the
wrong field, and six real gaps in the house were closed. The four residual FAILs are the
ones this file already accepts by decision: two ventilation terminals and the two
foundation-wall reinforcement schedules. Detail below; the sources behind each new rule are
named in the module that encodes it._

**Same-day correction: the house had two water heaters, and should have one (2026-08-15).**
Authoring `EQ-B-WH`'s TPR relief discharge above surfaced a modelling defect the owner
caught on review: `EQ-B-WH` (120V, "compressor only") and `EQ-B-WH2` (240V, "resistance
element") were two `Equipment` instances standing in for one product's two internal power
draws. The house now carries a single 80-gal Rheem ProTerra hybrid HPWH on one 240V/4,500 VA
circuit (`CKT-WH-240`, moved to the backup subpanel's SHED tier), governed to a ~500 VA
Heat-Pump-Only ceiling during a backup event or near the 200A peak by a Home Assistant
automation (ESPHome's `esphome-econet` bridging the unit's EcoNet API) — modelled as
`LM-WH`, a single-circuit `LoadManagement`, the same NEC 625.42/220.82 mechanism `LM-EV` and
`LM-WELLNESS` already use. `takeoff/backup_calc.py` gained `_governed_va` so a load-managed
circuit's contribution to the backup peak and autonomy averages reflects its enforced
ceiling rather than its nameplate — previously latent (nothing exercised it), now load-
bearing. Net effect on the service-load margin: **192.1A against 200A (7.9A of margin)**,
up from 199.6A that morning, because the water heater's peak-avoidance behavior is now
credited instead of silently absent. Explicitly supported for later: reverting to a single
120V plug-in HPWH (no 240V circuit, ~450W, entirely on backup) needs only a `type_ref` swap
on `EQ-B-WH`, a circuit retag, and deleting `LM-WH` — see the note above
`EQ-T-WATER-HEATER` in `plan/mep.py`.

**Rules added** (all six on the permit checklist, all six blocking, all six passing):

- **`code.MN_1303_2402_radon`** — Minnesota's own passive radon system rule (MN Rules
  1303.2400-.2402), which has no IRC parent and which nothing graded, even though this
  house has modelled the whole system — sealed sump, shared radon/vent riser, exterior
  junction box — for months. Grades the collection point, the sealed cover, the exhaust's
  separation from openings, and subpart 6's fan box being outside conditioned space. It
  found the one thing worth finding on the first run and then unfound it: measured from the
  *riser line* the exhaust stands 3.2' from WIN-S-BATH-N, but MN's sentence is a copy of IRC
  AF103's, which measures from the *exhaust point* and exempts any opening 2 ft or more
  below it. The rule now reads it that way and says so in the finding. See `checks/code/
  mn_residential/radon.py::_separation_findings` for the argument.
- **`code.R403_1_6_foundation_anchorage`** — grades the sill-anchor *schedule rule* (4 ft
  o.c., min 2 per plate run) against R403.1.6's 6 ft maximum, and reports UNKNOWN rather
  than PASS when no sill-plate construction return resolves at all.
- **`code.R405_1_foundation_drainage`** and **`code.R406_1_dampproofing`** — the footing
  tile and the damp-proof layer, both scoped by their own text to walls that *enclose*
  below-grade interior space. That scoping is the whole rule: screening on "retains fill"
  alone produced four FAILs against the sunken-garden walls, the yard retaining blocks and
  the garage ICF stem, none of which has a room behind it.
- **`code.R303_7_stairway_illumination` / `code.R303_8_exterior_stairway_illumination`** —
  a light over the treads, and a wall switch at *each* floor level for a flight of six or
  more risers. The switch half is what drawings miss and what `controlled_by` already
  records. Illuminance is deliberately not graded: the model carries lamp types, not IES
  files.
- **`code.R302_7_under_stair_protection`** — 1/2" gypsum in an enclosed usable space under
  a stair reached by a door. Scope-passes here; the house has no such closet.

**Checks that were wrong, and are now right:**

- **`code.R310_2_3_window_well` screened every opening big enough**, not the openings R310.1
  makes the house depend on. Three false subjects: a segmental arch in the basement brick
  veneer and the two arches in the freestanding garden porch wall, none of which is anybody's
  way out of a bedroom. It now walks the credited escape openings; the basement escapes
  through D-B-FURN, so no well is required and the rule says so.
- **`code.R302_13_floor_protection` only looked for a `FloorSystem`.** The floor over this
  basement is SL-M-DECK, a 9" cast slab, which has no floor framing member to fasten a
  membrane to and nothing in it that burns. UNKNOWN became a PASS naming the slab.
- **`code.P2804_water_heater_relief` read `heater.storey`**, a field elements do not carry,
  so every heater in every house reported "termination height unmeasured". It walks the
  plan's own storey grouping now, and the 6"-24" band is actually measured.
- **Every door got a 90-degree leaf sweep**, whatever its `DoorType.operation`. D-M-MUDC is a
  bypass slider and carried a permanent `integrity.door_swing_conflict` against the mudroom
  bench in front of it — and the plan sheets drew an arc for a slider besides. `resolve/
  pipeline.py::_LEAF_SWEEP_FRACTION` gives a slider, a pocket door and an overhead sectional
  no sweep, a bifold and a French leaf half a width.
- **`electrical.service_load` credited a load-management group at 100% of its connected
  excess**, whatever bucket the load was counted in. An interlock over two fixed appliances
  is worth 40% of its excess, not 100% — the 220.82(B) remainder factor is the only rate at
  which that load ever reached the demand. The credit is taken per bucket in
  `takeoff/electrical.py` now, and the check reads the result rather than recomputing it.
- **The service size was the literal `200` inside `takeoff/electrical.py`**, so no house
  could state anything else. `ElectricalDeviceType.service_amps` carries it now (authored on
  ED-T-METER), distinct from the panel's `bus_amps` that NEC 705.12 measures against.

**Gaps closed in the house:**

- **Both water heaters' TPR relief discharge is drawn** (`PR-B-WH-TPR`, `PR-B-WH2-TPR`,
  plan/mep.py). 3/4" copper, full size, vertical to 8" then 1'-0" at 2"/ft to an air gap 6"
  over the slab. It is the one pipe on a water heater whose job is to stop the tank
  exploding and the model had no instance of it. The east run stands at x=9'-0" rather than
  against the tank because W-B-STR's inside face is 6" further east and the first attempt
  cored it — `mep.sleeve_coverage` said so.
- **System 1's design-temperature shortfall has an answer**: `EQ-S-HP1-STRIP`, a 2 kW duct
  heater in the supply plenum on `CKT-HP1-STRIP` (the panel's former spare 2-pole, breaker
  down 30A -> 15A). 16,309 Btu/h of block load against 13,500 + FH-S-BATH1's mat was -1,069
  Btu/h; it is +5,755 now. This is the ordinary cold-climate detail, not a workaround.
- **The service fits, with management and no margin.** 254.2A unmanaged; the dryer at its
  830 W heat-pump nameplate instead of the 14-30R's 5 kVA is -7.0A; `LM-WELLNESS` (spa and
  sauna interlocked, one at a time) is -15.0A; `LM-EV` tightened 5,760 -> 5,600 VA is -0.7A.
  **199.6A against 200A — 0.4A of margin, and that is the number to remember.** The next
  load added to this house puts it over, and the answer then is the 400A service this pass
  deliberately did not buy (decision, 2026-08-15; the arithmetic is in plan/circuits.py
  above `LOAD_MANAGEMENTS`).
- **`ED-M-STORAGE-CAN1` names the room it is in.** The 2026-08-02 closet conversion framed
  RM-M-MUD-CLOSET around it and the light kept naming the mudroom; its sibling CAN2 took
  the same correction in July. A label catching up with a wall — nothing moved.

**Deliberately not done, and why:**

- **RM-B-ESS and RM-M-MUD-CLOSET stay in no HVAC zone.** They were added to the zone lists
  during this pass and then reverted: `test_heating_capacity.py` records why each is
  unclaimed on purpose (a sealed Type X battery closet whose occupant is a heat source; a
  storage closet behind a 48" bypass slider that is open air transfer). Unclaimed is the
  true statement there, not a gap.
- **The four exterior placeables keep their false room refs** (both wall hydrants, both
  porch curtain rods). Giving them an honest home means unconditioned `Room`s for the porch
  and the balcony — enclosing walls, envelope, energy and ventilation consequences — for
  four UNKNOWNs this file already accepts. Not worth the complexity.
- **The IRC reinforced-foundation tables were not encoded.** Tables R404.1.2(2)-(5) would
  turn the two foundation FAILs into a prescriptive rebar schedule, which is the right
  eventual answer, but no source consulted reproduced the table rows and a made-up
  reinforcement schedule is worse than an honest FAIL. The engineer's schedule still lands
  in `FoundationWall.engineering_spec`.

_Batch of 2026-08-07: thirteen packages landed — the PT-SG-BR2 cluster and its cantilever
check, per-condition detail stars, the disposal branch, curtain rods, access panels, the
door-jamb hold-downs, the living-room ceiling, 2D stud end-cuts, conduit/sleeve solids,
furring-as-strapping, the coupled toilet-flange move, and the price research. Each item
below and in **Questions** carries its own note. `haus check` came out of it at 661 pass /
6 fail / 33 not evaluable of 700 — the same six accepted FAILs it went in with._

- **In-plan variant forks + compare UI** (deferred again by decision 2026-08-02,
  **re-affirmed 2026-08-07**). `model.json` now carries the variant catalog; `prices.toml`
  $-ranges work in `haus variants compare` and takeoff. Still missing: `variant_of`/`active`
  forks with one-active integrity + promote-with-uid-remap, and the UI side-by-side compare
  canvases.

- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span`'s two genuine R507.5(1)
  overspans were closed 2026-07-31 by going engineered — see "Accepted, by decision".)
- ~~**`diff/equivalence.py` storey keys are last-wins**~~ — stale entry: fixed some time ago
  via `datum_buildings` (`pick_datum_storey` raises `AmbiguousStoreyDatum` rather than
  picking silently). Removed.
- **Windows: 8 residual member-interference overlaps** — now **pinned** by
  `test_catlin_window_member_overlaps_pinned_at_eight` (junction clear disabled — the
  honest metric). Measured composition drifted from this file's memory of 4+4: it is 6 at
  one T (CSW148 jamb pack), 1 L corner, 1 vs the stair soffit plate. (Historic: 138 → 8.)

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

## Phase 2 — Complete Catlin junctions (deferred by decision 2026-08-02 — construction-rule authoring)

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
  **Re-affirmed deferred 2026-08-07:** framing the fall means a sloped-`Beam` schema change,
  which is a bigger piece of work than the batch it kept coming up in.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- ~~Is the door opening inside the breezeway code compliant~~ — **answered 2026-08-02:
  yes.** Both `D-M-ENTRY` and `D-G-SERVICE` are 3'-0" × 6'-8" exterior doors — PASS
  R311 width, and the new `code.R311_2_door_height` (78" min) passes both 80" leaves. The
  breezeway's N-S beam soffits at +6'-3½" over the walk line remain authored-deliberate
  (`params/breezeway.py:38-45`).
- ~~Edits in 2d don't always update all the necessary pieces~~ — investigated 2026-08-02;
  root cause + proposed fix under **Needs your decision** above.
- ~~Should porch column PT-SG-BR2 bear more directly on PT-SG-COL?~~ — investigated
  2026-08-02; recommendation under **Needs your decision** above.
- Pantry (deferred by decision 2026-08-02)
- Add the plant room wall types (deferred by decision 2026-08-02)
- basement ceiling, some of this wood joists maybe (deferred by decision 2026-08-02)
- study on first floor location adjustments (deferred by decision 2026-08-02)
- ~~"Star" certain details~~ — the machinery already existed (`Transition.star`, UI toggle,
  `details="primary"` filter); 2026-08-02 curated the stars (6 of 14 transitions: eave,
  foundation sill, rim band, framed opening, garage/breezeway threshold, sauna-liner
  opening — 31 of 46 A-4xx sheets in the primary set) and flipped `haus print` to
  primary-by-default (`--details all` still there). Per-condition fan-out is under
  **Needs your decision**.
- Nest/loft design
- House being a bit higher, cladding detail
- ~~Count/show tile, make sure electrical for mats is in if so~~ — **answered 2026-08-07.**
  Tile was already counted: `floor_finish_rows` bills it by the room, so there was nothing
  to add. On the mats, the decision is **none added** — FH-M-BATH2, FH-S-BATH1 and
  FH-M-DINING are the three zones the house wants, each already its own 120V circuit with
  breaker-level GFCI and its own thermostat. Recorded as a decision, not a deferral: the
  next tiled floor to get a mat should be a deliberate addition, not a gap someone finds.
- ~~Garbage disposal in kitchen sink~~ — **answered 2026-08-07,** and answered the way this
  file asked for it ("just the main underlying electrical branch"). `APPL-M-DISP` hangs off
  FX-M-KITCH-SINK's flange in the sink base; `CKT-DISPOSAL` (slot 39, 20A, GFCI+AFCI at the
  breaker) is its own branch, off CKT-DISHWASHER, because a 3/4 HP motor's inrush on top of
  a dishwasher heater is the nuisance trip that gets a breaker taped on; `ED-M-LIVING-KDS1`
  is the single 5-20R disconnect 9" west of the dishwasher's box.
  The 24V control loop is **counted, not drawn**: `Appliance.install_parts` now feeds the
  same `[install_parts]` BOM section the hydrant kits do, so the transformer, DP contactor,
  NEMA 1 enclosure, guarded toggle, momentary button, LV ring/plate and 50 ft of 18/6 CL2
  all reach the order without inventing conduit routes nobody has designed. The spec
  section further down this file is kept as the build instruction it is.
- ~~Able to see the actual studs (or the end cut view of them) on the 2d when framing on~~ —
  **done 2026-08-07.** Members now draw their plan footprint, not a centreline: a vertical
  stud is its oriented `width_m × depth_m` end cut, a horizontal one a band on the plate
  rule, ported from `resolve/framing/footprint.py`. Below 2px of cross-width the old line
  stays, because a fill that thin antialiases into a smudge. Filed follow-up: the engine
  does not populate `plan_outline`, so the **PDF/DXF sheets still draw centrelines** — the
  viewer and the printed set disagree until that lands.
- Window sealing detail
- ~~Access panels (mechanical, wall hung toilet)~~ — **answered 2026-08-07.** The wall-hung
  WC gets `FURN-M-BATH1-AP`, a 14x29 in BATH1's face of the W-M-BAE carrier wall. Three tub
  traps were surveyed and two got 14x14 panels, both opening from the *adjacent* space
  rather than over the tub: BATH2's through W-M-BA2E into the laundry (its drain is
  authored behind the tub, not at an end), and the suite tub-shower's through W-S-SN3 into
  the hall. FX-S-BATH1-SH gets none — its drain end backs onto the plumbing chase, with
  nowhere to stand. **Mechanical: none, deliberately** — the equipment all stands in open
  rooms and is reached without opening anything.
  Loose end: neither second-storey tub-shower carries a `drain_position`, so their ends
  were read off resolved footprints and the walls touching them. Author one and the suite
  panel should be re-checked against it.
- ~~Curtain rods (on porch, in living room, master bedroom)~~ — **done 2026-08-07.** Nine
  interior rods on one 7'-0" head line for the whole storey — above the tallest head
  (6'-8"), so the living room reads as one line instead of stepping three times — plus two
  114" outdoor rods across the porch's front pillar bays, which are 9'-6 1/2" clear between
  6x6 faces. **"Master bedroom" was read as RM-M-BED**, the main-storey bedroom, not the
  second-storey suite; say so if that was wrong, and the four rods move.
- ~~Any rooms with fancy ceilings? ... "Resilient channels on ceiling perpendicular to
  joists, hat channels maybe better, or sound isolation clips. Whichever the drywall guy
  prefers/is cheapest" for the Living Room ceiling.~~ — **minimal treatment authored
  2026-08-07,** which is the decision: bill the two things that get ordered, and leave
  full layered ceiling assemblies deferred.
  FS-SECOND gained `ceiling_below` gypsum, so the main-floor ceiling finally bills — 1226
  sf net, 39 sheets, previously ordered by nobody. `CR-LIVING-CEIL-RC` is the channel:
  16" o.c. over RM-M-LIVING only, 523.7 LF. The new `floor:ceiling_channel` finder computes
  length as field area / spacing and deliberately ignores joist direction — the runs do
  cross the joists, but parallel runs at a fixed spacing over an area come to the same
  length however the field is turned.
  **The product choice is still open and still yours** — the rule is authored as resilient
  channel because that is what the note above names first; hat channel or isolation clips
  are a `takeoff_category` swap, not a re-model.
  **Gap worth knowing:** `construction_returns` is not in `cli/prices.py::_SECTIONS`, so
  those 523.7 LF reach the BOM and never the cost estimate. Verified empirically, noted on
  the rule, not fixed here.
- ~~Getting more estimates prices researched and filled into the price list~~ — **done
  2026-08-07.** 68 keys filled across `[framing]`, `[concrete]`, `[openings]`,
  `[envelope_layers]` and `[sheet_goods]`, plus the five new placeable types, each a
  low/high range with its basis and sources written into the section header and dated. The
  estimate resolves end to end for the first time: **$149k - $284k**, material only.
  Read the caveats in the file, not just the total. Everything is material-only with no
  waste factor and no labour; published window/door/insulation costs are almost all
  *installed*, so those were backed out at roughly 55-65% material rather than copied; and
  `[envelope_layers]` is keyed by material tag with no thickness in the key, so each range
  is the $/SF at the thickness *this* house's assemblies use — change an assembly's
  thickness and the number silently stops being right.
  Left blank on purpose, because a made-up number is worse than a gap: the `* panel`
  profiles and `deck *` widths in `[framing]`, and `composite-deck` — all bought by the
  piece from named suppliers, not as stock. They want quotes.
- ~~Reinforcement for exterior doors~~ — **clarified and authored 2026-08-07.** The
  reinforcement wanted was uplift, not the lockset: `strap_holdown_rows` derives STHDs at
  the *ends* of each sill-plate run, so the jamb studs beside a door punched through the
  middle of a run had no load path past the sill plate. Four authored STHDs now tie the
  first-floor exterior-wall framing at D-M-ENTRY's and D-M-BALC's jambs into the basement
  concrete. **D-G-SERVICE is deferred** — it stands in the garage ICF stem wall, and an
  ICF-embedded holdown is a different part with a different embedment.
- ~~Moving toilet needs to move its flange too in UI~~ — **fixed 2026-08-07, and it was
  live.** A drive-by edit in `76c1871` had already moved FX-M-BATH2-WC 6.46" off its
  cast-in sleeve SP-M-WC2 and drain PR-B-WC2-DRAIN, with nothing complaining; the fixture
  is back on its flange. `move_placeable` now emits follower ops for every sleeve serving
  the fixture and every path vertex of every pipe run within snap of the old flange —
  *every* vertex, because the riser is authored as a duplicated pair and rewriting one
  leaves the run kinked. Warnings go both ways, so a partial follow is visible instead of
  silent, and SleevePenetration/PipeRun joined `_UI_EDITABLE_KINDS` so authoring one
  outside an editable file fails loudly.
- Possibly moving house and sunken garden up (not garage), accounting for split layer
- Small windows on corners?
- Balcony railing?
- Pipe sleeve SP-GF-W-HYD-B3 is either unnecessary or misplaced (only one needed through garage floor slab there, not sideways like this one)
- Do "drain tile" and "french drain" duplicate at all here?
- The "draw stud end cuts" of e597019 doesn't seem to have worked? Or else it is just showing the top plate or sill, not the vertical members?
- EQ-M-HP3-STAIR should be on the north wall of the stairs (on the northwest corner, wall W-M-N2 I believe), not the west wall. It also should have a register of some kind (passive, not hooked to the minisplit, just next to it) to allow air to flow from next to it into MUDROOM through wall W-M-STRW
- We are thinking of switching W-SG-ARCH to be a column and beams like PT-SG-COL and BM-SG-BKE, then replacing the masonry railing right above it with a metal railing more like RL-SG-BALCONY
- Add a packed gravel bed under the retaining wall blocks (W-RG-*)
- Improve the symmetry of the windows on the east and west side so they look better from outside, where possible
- Permit drawings

### Plumbing

  Deliberately left for later:
  - **No hose reel, hanger or splash block** at either hydrant, and no water leak/freeze
    `Alarm` anywhere in the house. (Re-affirmed deferred, 2026-08-02.)
  - **The RO unit itself.** `PA-M-RO-STUB` is a capped 1/4" tee with no fixture and no
    fixture units — the provision, not the machine.
  - **`mep.backflow_prevention` grades hose connections only.** The basement's two dual-check
    preventers are reported where authored but are not *required* by the check — a general
    cross-connection survey (hose-end sprayers, the boiler fill that does not exist yet) is
    not encoded.
  - **The wall hydrants draw an `integrity.placeable_room_mismatch` apiece**, which is the
    true description of an exterior hose bib hosted by an interior room's wall rather than a
    defect. The model has no outdoor-room concept to file them under.

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)

### Potential cost cutting (just ideas, not a TODO)
Remove the attic level and switch to truss/blown in insulation
Remove the arched concrete and switch to a metal railing on wood beam and columns

Once an idea here has a number against it, it moves to `plans/cost-options.md` — the
priced upgrade/downgrade menu (started 2026-08-08). Both of the two above are in it now.
