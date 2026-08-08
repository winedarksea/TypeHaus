# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

- **PT-SG-BR2 bearing — recommendation: reinforce locally, don't move it** (investigated
  2026-08-02). The question was lateral; the finding is gravity: BR2 (~2.2 kips tributary)
  stands at the extreme tip of the porch deck's 17" cantilever, catching ~1.5" of one 2x8
  edge plus the rim — a single tip-loaded 2x8 is over allowable moment ~2.4×, and the rest
  of the base bears on 1" composite plank. Moving BR2 south onto the column line was
  rejected (breaks the rear girt line and the frame's symmetry; the column itself cannot
  move north — bell footing vs FT-B-S2). Recommended: sister the joist under the base to
  3-ply PT 2x8, solid blocking so the ABU base bears on framing, and a positive uplift tie
  (~0.45 kips) at the back-span bearing. The global path already lands on PT-SG-COL within
  17". Approve to author the sistered cluster + blocking (wants a way to author it, and
  ideally a check for concentrated loads on cantilever tips).
- **2D-edit sync — fix design proposed** (investigated 2026-08-02). Root cause confirmed: a
  PatchOp rewrites one constructor; derived data recomputes, authored cross-references
  don't. `retype_placeable` (2026-08-01) already re-anchors wall-fitted placeables and
  scans tag references. Still open, ~3–4 days if approved: (i) authored refs +
  advisory checks for geometry-coupled consumers (`Slice.subject_ref`, `DuctRun.serves`),
  (ii) promote retype warnings to durable review findings, (iii) route *opening* retypes
  through a centre-holding macro (raw PATCH still slides them today).
- **Detail stars fan out per-condition**: starring TR-CATLIN-RIM-BAND/FOUNDATION pulls ~10
  interior-condition sheets (e.g. `rim:INT_2X4_PARTITION`) into the primary set. Trimming
  them needs pattern-split transitions or a per-condition star — worth it?

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

- Better representation of the electrical conduit and concrete penetrations in the 3d view.
- **In-plan variant forks + compare UI** (deferred again by decision 2026-08-02).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.

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
- Count/show tile, make sure electrical for mats is in if so
- Garbage disposal in kitchen sink
- Able to see the actual studs (or the end cut view of them) on the 2d when framing on
- Window sealing detail
- Access panels (mechanical, wall hung toilet)
- Curtain rods (on porch, in living room, master bedroom)
- Any rooms with fancy ceilings? Ceilings don't seem well rendered yet. We do know that we want, "Resilient channels on ceiling perpendicular to joists, hat channels maybe better, or sound isolation clips. Whichever the drywall guy prefers/is cheapest" for the Living Room ceiling.
- Reinforcement for exterior doors
- Moving toilet needs to move its flange too in UI
- Getting more estimates prices researched and filled into the price list

### Drainage Outstanding
    is nominal, not computed from a soil infiltration rate.
  - Authored `FrenchDrain` runs beyond the derived bedding tile — **moot for now**: no house
    authors a `FrenchDrain` yet (catlin has drywells only); revisit when one exists.
  - Furring over a monolithic wall is still billed nowhere: `W-B-CS`
    (`SAUNA_LINER_ON_CONCRETE`) carries a `struct-1-plywood` FURRING layer over a concrete
    core, and the strapping frames no members, so the "carried by the framing cut list"
    waiver is false for it. Waived by function in `_WAIVED_LAYER_FUNCTIONS` with that note;
    fix by billing monolithic-wall furring by the lineal foot.

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
Disposal is a 3/4 HP system, stainless steel, likely insinkerator
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
