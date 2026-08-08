# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

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

_Batch of 2026-08-07: thirteen packages landed — the PT-SG-BR2 cluster and its cantilever
check, per-condition detail stars, the disposal branch, curtain rods, access panels, the
door-jamb hold-downs, the living-room ceiling, 2D stud end-cuts, conduit/sleeve solids,
furring-as-strapping, the coupled toilet-flange move, and the price research. Each item
below and in **Questions** carries its own note. `haus check` came out of it at 661 pass /
6 fail / 33 not evaluable of 700 — the same six accepted FAILs it went in with._


- ~~Better representation of the electrical conduit and concrete penetrations in the 3d
  view.~~ — **done 2026-08-07.** Conduit runs and cast-in sleeves now emit solids: 82
  `conduit_power`, 45 `conduit_data`, 276 `pipe_sleeve` (1367 solids -> 1770). Conduit
  geometry comes off the same `_conduit_vertical_profile` the pour-day `concrete_crossings`
  list walks, so the viewer and the crossing list cannot disagree. Sleeves are a
  `circle_outline` cylinder when vertical and a bore along the host normal when horizontal —
  catlin authors 40 horizontal ones, 6 of them under footings. Violet/teal/cream sit outside
  the riser-diagram hues on purpose, so a raceway never reads as a supply line where
  CD-B-KITCHEN parallels the hot and cold trunks.
  Filed, not fixed: the IFC generic solid loop has no `_SOLID_IFC_CLASS` entry for
  `pipe_*` / `conduit_*` / `pipe_sleeve`, so all of these export as the `IfcFooting`
  fallback — the same pre-existing wart the 895 pipe solids already had.
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

### Drainage Outstanding
    is nominal, not computed from a soil infiltration rate.
  - Authored `FrenchDrain` runs beyond the derived bedding tile — **moot for now**: no house
    authors a `FrenchDrain` yet (catlin has drywells only); revisit when one exists.
  - ~~Furring over a monolithic wall is still billed nowhere~~ — **fixed 2026-08-07,** and
    the fix was better than the lineal-foot workaround this entry proposed: a FURRING layer
    with a `FramingSpec` now frames real `strapping` members in its own band, whether or not
    the wall frames anything else. 470 members, all 1x4, 3976 LF cut — and **W-B-CS goes
    from 0 to 8**, eight horizontal courses at 16" o.c. up the 9' concrete wall. It bills
    through the ordinary framing takeoff, so the `_WAIVED_LAYER_FUNCTIONS` entry is deleted
    rather than reworded, and the test now asserts the credit instead of apologising for it.
    Worth recording: the first run threw 42 `structural.member_interference` FAILs at the
    corners and **none of them earned an exemption** — every one was the new code's own
    geometry (a flat-laid strip's along-wall run is `depth_m`, not `width_m`; a mitre's far
    tip is a corner of the band, not a station its centreline reaches). Both fixed, zero
    findings, check left policing the category.

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

### The garbage disposal with safety toggle system
Disposal is a 3/4 HP system, stainless steel, likely insinkerator.
We don't need to show all of these exact switches and toggles, just the main underly electrical branch.

1. The Power & Protection (The Breaker Panel)

    Dedicated Circuit: Run a dedicated 12/2 Romex cable for the disposal. (If you want an instant-hot or dishwasher under the same sink, run a second dedicated circuit for them).

    Upstream GFCI: Install a 20-Amp GFCI Circuit Breaker at your main electrical panel. This protects the entire wire run, the contactor, and the outlet, and eliminates the need for a bulky GFCI receptacle under the sink.

2. The Backsplash Controls (The UI)

Moving to a momentary "RUN" switch is a brilliant safety upgrade. It acts as a "dead man's switch." You flip the missile guard up, toggle the switch to ARM the system (the red light turns on), and then you push and hold the RUN button to grind the food. If a spoon falls in, you just let go of the button and it stops instantly.

    The Wire: Run 18/6 CL2 thermostat/control wire in the wall. You only need 4 conductors, but the extra two wires give you a backup if a wire is nicked by a drywall screw, or allows for future expansion.

    The Arming Switch: An aircraft-style guarded toggle switch. (Note: Because we are moving to 24V DC, you must buy a 24V-rated illuminated toggle, often sold for heavy-machinery/marine use, or simply use a standard 12V switch and wire a 1k-ohm resistor in series with the switch's ground pin to protect the LED from the 24V).

    The Run Switch: A 24V DC momentary push button. A stainless steel "Anti-Vandal" push button (often used in elevators or custom PCs) looks incredibly premium and fits a round cutout perfectly.

    The Plate: A custom 2-gang metal plate with two round cutouts (sized to your specific switches, usually 12mm, 16mm, or 19mm).

3. The Under-Sink Hardware (The Engine)

    The Receptacle: Install a standard, commercial-grade 20A single receptacle (not a duplex). Because the GFCI breaker protects it, this is perfectly code-compliant.

    The Contactor (Motor Relay): Instead of a generic relay, use a Definite Purpose (DP) Contactor with a 24V DC (or 24V AC) coil. These are specifically built for the brutal inrush current of electric motors. (e.g., a 1-pole or 2-pole 30-Amp contactor by Eaton, Schneider, or Packard).

    The Enclosure: Mount the contactor inside a standard 6x6x4 metal NEMA 1 enclosure (junction box) under the sink.

    The Power Supply: A UL-Listed Class 2 power supply. You can use a hardwired 24V DC transformer mounted directly to the side of the NEMA enclosure.

4. The Wiring Logic

High Voltage (Inside the NEMA Enclosure):

    The 120V AC Line (Black) from the breaker connects to the L1 (Line) terminal on the Contactor.

    The T1 (Load) terminal on the Contactor goes to the Hot (Brass) screw on your 20A Receptacle.

    Neutral and Ground bypass the contactor and go directly to the Receptacle.
    Result: The receptacle is dead until the contactor pulls shut.

Low Voltage (The 24V Control Loop):

    24V Positive (+) from the power supply goes up the wall (via Wire 1) to the Power pin on the ARM Toggle Switch.

    24V Negative (-) from the power supply splits:

        One branch goes to the Negative Coil terminal on the under-sink Contactor.

        One branch goes up the wall (via Wire 2) to the Ground pin on the ARM Toggle Switch (this provides the ground path so the red LED lights up).

    A jumper wire goes from the Accessory/Load pin on the ARM Toggle Switch to one side of the momentary RUN button.

    The other side of the momentary RUN button goes down the wall (via Wire 3) to the Positive Coil terminal on the Contactor.

Main BOM additions:
GFCI Breaker: A dedicated 20-Amp GFCI Circuit Breaker in the main panel (Brands: Square D, Siemens, Eaton—must match your home's electrical panel).
Receptacle: A commercial-grade 20A Single Receptacle (e.g., Leviton 5361-W). Note: Use a "Single" receptacle (one plug), not a standard "Duplex" (two plugs), as this is a dedicated, switched circuit.
Low Voltage Wire: 50 feet of 18/6 CL2 In-Wall Thermostat Wire.
Boxes: A 2-gang low-voltage mounting ring for the backsplash, and a 4x4 metal junction box for under the sink.

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)

### Potential cost cutting (just ideas, not a TODO)
Remove the attic level and switch to truss/blown in insulation
Remove the arched concrete and switch to a metal railing on wood beam and columns
