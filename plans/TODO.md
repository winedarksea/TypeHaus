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

- ~~**Structured cabling (CAT6) up the chase + a low-voltage schedule**~~ DONE 2026-08-02.
  `Service.DATA`, `ConduitRun.service` (`None` = capped spare), `DeviceKind.DATA_OUTLET`.
  Catlin gets a patch enclosure in `RM-B-FURNACE` home-running three PoE access points
  (kitchen ceiling, porch soffit, attic NE) up the radon/vent chase, plus a 2" capped spare.
  Four risers now share the y=34'-6" line at 6" centres: vent bundle 1'-0", PV 1'-6", data
  2'-0", spare 2'-6".
  - **`ElectricalDeviceType.ifc_entity`/`ifc_predefined_type`/`ifc_type_entity`** is the
    lever that keeps this a catalog: `DeviceKind` stays the plan-symbol axis, and the IFC
    class rides the product type. The APs export as `IfcCommunicationsAppliance`/
    `NETWORKAPPLIANCE` (Revit → Communication Devices), grouped in one
    `IfcDistributionSystem`/`COMMUNICATION`. **A PoE camera is one `DEVICE_TYPES` entry and
    zero engine edits** — `IfcAudioVisualAppliance`/`CAMERA`, and it appears on E-603 and in
    the Data reader automatically. The capped spare is where its cable goes.
  - New: `electrical.data_reachability` (ADVISORY, pure `from_ref`/`to_ref` graph walk — no
    invented distance tolerance, because branch cable is undrawn by doctrine),
    `takeoff/data.py`, sheet **E-603**, UI reader **Data**, AIA layers `E-COMM-DEVC`/
    `E-COMM-CNDT`.
  - `conduit_takeoff` now bills **power only**; data and the spare are billed by
    `takeoff/data.py`. Comms and power may not share a raceway (NEC 800.133/725), so one
    merged lineal-foot row is not an order either trade can buy against.
  - PoE load moved from `CKT-FRIDGE` (where a single notional 15 W allowance sat) to
    `CKT-HA`, which feeds the switch. **Consequence: battery-only always-on autonomy fell
    ~50 h → 46.3 h**, because two of the three APs had never been counted anywhere. The 48-h
    *solar* cycle still sustains the always-on tier (net +2.5 kWh), which is the question the
    backup design is actually built around.
- ~~**Conduit was invisible to the pour-day sleeve walk**~~ DONE 2026-08-02, found while
  doing the above. `concrete_crossings` walked only `model.pipe_runs`, so **15 raceway
  crossings of cast concrete had no sleeve** and nothing could say so. It now walks conduit
  too. Three consequences worth remembering:
  - `CD-B-GARAGE` and `CD-B-SPA` were routed *along* the y=36'/y=0' sheathing lines, i.e.
    **inside** the foundation walls for 14' and 6'-6". Pulled 1' inboard; each now crosses
    once, where a sleeve is.
  - `_matching_sleeve` matched on proximity alone, so a 1" power raceway could claim a 3"
    drain sleeve 2" away — a false PASS that *also* stole the sleeve from the drain, which
    is how `mep.sewer_exit_invert` came to grade `CD-B-SPA` as a drain. It now checks
    `SleevePenetration.purpose` against the crossing's system.
  - `CD-B-ATTIC-RISER`/`CD-B-PV-INV` still ended at **(3', 33')**, the pre-2026-07-28 chase
    location — 4" outside `W-M-MECH-S`, floating in the mudroom. Repointed, uids kept.
- **No porch deck penetration, and that is correct** (settled 2026-08-02). `SL-SG-DECK`
  resolves at 10'-0"; `ED-M-PORCH-FAN`, `ED-M-PORCH-AP` and `CD-M-DATA-PORCH` are all at
  8'-6"–9'-2", i.e. *under* it. The raceways leave through the framed south wall, which
  takes a drilled hole, not a cast sleeve. `ED-M-PORCH-FAN`'s supply is still undrawn — a
  branch-wiring gap like every other device's, not a penetration gap.
- ~~**Handrail schema + real R311.7.8 check**~~ DONE 2026-08-02. The schema and check had
  in fact already shipped; what was missing was authoring and a resolver. This batch:
  wall-mounted handrails authored for all three stairs (`role="handrail"`, `serves_stair`,
  36" top, Type I round), `_resolve_railing` now **rakes** a `serves_stair` railing along
  the flight nosing line (shared math in `resolve/stairs/walkline.py`; guards still resolve
  flat, pinned), and `code.R311_7_1_stair_width` gained the 31.5"/27" clear-past-handrail
  measurement. R311.7.8: UNKNOWN → PASS on every 4+-riser flight.
- ~~**Stair/well guard check (R312)**~~ — shipped earlier than this file remembered
  (`code.R312_1_guard`, `code.R312_1_guard_height`, `code.R312_1_3_guard_opening_limit`).
  2026-08-02: the four guards now author `infill="balusters"` + 4" spacing, flipping
  R312.1.3 UNKNOWN → PASS.
- **In-plan variant forks + compare UI** (deferred again by decision 2026-08-02).
  `model.json` now carries the variant catalog; `prices.toml` $-ranges work in
  `haus variants compare` and takeoff. Still missing: `variant_of`/`active` forks with
  one-active integrity + promote-with-uid-remap, and the UI side-by-side compare canvases.

- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span`'s two genuine R507.5(1)
  overspans were closed 2026-07-31 by going engineered — see "Accepted, by decision".)
- ~~**KneeBrace paint is authored but not rendered.**~~ DONE 2026-08-02:
  `_resolve_knee_brace` resolves the assembly to the structure layer's material via the new
  shared `resolve/assembly_material.py`, `FramedMember.material` carries it (the slot
  already existed), `_FINISH_BASE` knows `post-paint-white`, and `_emit_brace` associates
  the `IfcMaterial`. The braces render white in glb, viewer, and IFC.
- ~~**`diff/equivalence.py` storey keys are last-wins**~~ — stale entry: fixed some time ago
  via `datum_buildings` (`pick_datum_storey` raises `AmbiguousStoreyDatum` rather than
  picking silently). Removed.
- **Windows: 8 residual member-interference overlaps** — now **pinned** by
  `test_catlin_window_member_overlaps_pinned_at_eight` (junction clear disabled — the
  honest metric). Measured composition drifted from this file's memory of 4+4: it is 6 at
  one T (CSW148 jamb pack), 1 L corner, 1 vs the stair soffit plate. (Historic: 138 → 8.)
- ~~**`interior_slab_drip_flashing` detail gate**~~ DONE 2026-08-02: `slab_is_on_grade`
  asks whether any lower-storey room's clear face covers the slab centroid below its z0 —
  `SL-G-FLOOR` gates in, `SL-M-DECK` out, no assembly-name matching. Draws at
  `wall_foundation:GARAGE_ICF_8|GARAGE_WALL_2X6`.

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
- ~~**Per-wall paint colour.**~~ DONE 2026-08-02, exactly as the `_PAINT_FINISH` comment
  prescribed: `latex-paint-accent` (colour on the `Material`, physics identical) +
  `Room.wall_lining`/`WallLiningException` now actually reach resolved wall layers
  (`resolve/rooms.py::wall_lining_overrides` → `resolve_wall_geometry(lining_override=)`;
  shared-wall conflicts and lining-less assemblies warn instead of silently applying).
  First accent: `W-S-BED1`'s east wall in deep spruce `#2e4a44`. Fixing this also fixed the
  glb↔viewer parity gap — the glTF palette now honours authored `Material.color` on wall
  layers, so latex-paint itself finally matches the browser. IFC wall types split per
  resolved layer stack (`{assembly}~lining{n}`).

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

### Items after Phase 6 — all closed 2026-08-02
- ~~Toilet 28" vs elongated~~ — **decided: keep the 28" round bowl.** No model change.
- ~~Kitchen island outlet~~ — `ED-M-LIVING-KGF4` on the island's east end face at 32", on
  CKT-KITCH-SA2, placed per 2023-NEC 210.52(C) (not on the south seating face). A new
  advisory `electrical.island_receptacle` now grades any free-standing work surface.
- ~~Garage dark-sky light + advisory~~ — `ED-G-EXT-LT` (mark **R**, full-cutoff wet
  sconce, 3000K) on the pier south of the overhead door at 8'-10" over the slab, switched
  inside the service door. `LuminaireType.full_cutoff` is the shielding declaration, and
  `advisory.dark_sky_lighting` grades every geometrically-exterior luminaire (cutoff +
  CCT ≤ 3000K; ceiling-mounted fixtures exempt from the cutoff test — the deck above is
  the shield, which is what lets the porch fan pass).
- ~~Porch flood on the roof center column~~ — `ED-M-PORCH-FLOOD` (mark **S**, narrow-throw
  wet sconce) on PT-SG-BR2 at 8', sharing CKT-LT-MAIN with the fan as hoped, but on its
  **own** switch beside `ED-M-PORCH-SW` — the fan runs whole evenings; the flood shouldn't
  glare with it.
- ~~FURN-M-MUD-CLOSET-S → framed closet~~ — `RM-M-MUD-CLOSET`, 34¾" interior depth (in the
  32"–36" band), partition at y=29'-7½" stopping ⅛" shy of the bench, 48"
  `DT-INT-BYPASS48` sliding door (slide is handled end-to-end, so the bypass intent
  survived), `W-M-W1` split at the new tee per the endpoint rule. RC9 stays inside as an
  in-closet receptacle (NEC restricts closet *luminaires*, not receptacles; the mudroom is
  STORAGE so no 210.52 wall space loses coverage). Bonus finds: `WIN-M-MUD` had silently
  slid 2'-8" south since the 2026-07-28 MECH split (`from_node` measures from the host's
  start node — re-authored to the true bench/aisle line), and the `PR-B-HW-SBATH` riser
  sat half inside the new corner pack (moved one bay east with its sleeve).

Questions:
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
- ~~Cost tracking in the UI~~ — DONE 2026-08-02. `houses/catlin/costs.toml` (paid flags,
  exact-product tags, extra non-modeled line items) keyed by the same `(section, key)` join
  `prices.toml` uses, served over `GET/PUT /costs` (outside the undo journal — paying a
  bill is not a plan edit), rendered in the BOM view: cost columns, paid checkboxes,
  extras, and **stale entries surfaced, never dropped** when the model stops matching a
  key. A starter `prices.toml` ships with every section header and ~300 commented rows
  keyed from the real BOM — fill in quotes as they arrive.
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
- Any rooms with fancy ceilings
- Count/show tile, make sure electrical for mats is in if so
- Garbage disposal in kitchen sink
- Able to see the actual studs (or the end cut view of them) on the 2d when framing on
- Window sealing detail
- Access panels (mechanical, wall hung toilet)
- Curtain rods (on porch, in living room, master bedroom)
- Show LED trips better, note drywall channels as needed in BOM
- Reinforcement for exterior doors
- Moving toilet needs to move its flange too in UI

### Drainage Outstanding
    is nominal, not computed from a soil infiltration rate.
  - Authored `FrenchDrain` runs beyond the derived bedding tile — **moot for now**: no house
    authors a `FrenchDrain` yet (catlin has drywells only); revisit when one exists.
  - ~~Siteplan drainage overlay + 2D drainage plan~~ DONE 2026-08-02: `drainageplan.py`
    (P-201 series, buried work dashed, per-storey gate) and a `C-STRM-DRAN` overlay on
    C-101.
  - ~~Flashing/fascia LF take-off~~ DONE 2026-08-02: new `edge_trim` BOM section bills
    authored fascia/soffit/flashing runs plus the derived roof-trim family by the foot
    (band-deduped; derived gutters stay in `drainage`; rows cross-reference their
    solids/framing mirrors).
  - ~~Monolithic wall structure take-off~~ DONE 2026-08-03: new `wall_structure` BOM section
    bills the wall cores that frame no members and are not solids — pours, ICF, CMU/SRW
    courses, the sunken-garden brick wythe — by net area and cubic yards (43 of catlin's 154
    walls, ~131 cy, previously in no row at all). Split from `framing` by
    `resolve.framing.solver.frames_as_members`, the one predicate `frame_wall` branches on,
    and gated by a per-wall-layer coverage test in `test_framing_takeoff.py`.
  - Furring over a monolithic wall is still billed nowhere: `W-B-CS`
    (`SAUNA_LINER_ON_CONCRETE`) carries a `struct-1-plywood` FURRING layer over a concrete
    core, and the strapping frames no members, so the "carried by the framing cut list"
    waiver is false for it. Waived by function in `_WAIVED_LAYER_FUNCTIONS` with that note;
    fix by billing monolithic-wall furring by the lineal foot.
  - ~~RAINWATER / SEWAGE `IfcDistributionSystem`s~~ DONE 2026-08-02: DRAIN runs → SEWAGE
    (IFC4's sanitary member), VENT → VENT, the radon riser deliberately **not** grouped
    with plumbing vents (USERDEFINED/"RADON"), and the silent discard of non-supply
    systems in the emitter is gone. Rainwater stays with the STORMWATER solids system, on
    purpose — the storm run is gutters/leaders/tile, not `PipeRun`s.

### Plumbing

  Deliberately left for later:
  - **No hose reel, hanger or splash block** at either hydrant, and no water leak/freeze
    `Alarm` anywhere in the house. (Re-affirmed deferred, 2026-08-02.)
  - **The RO unit itself.** `PA-M-RO-STUB` is a capped 1/4" tee with no fixture and no
    fixture units — the provision, not the machine.
  - ~~A second niche in `RM-S-BATH1`~~ — added 2026-08-02 (`LR-S-BATH1-NICHE` in
    `W-S-CH-W`, board stood vertical, own PSU per the per-area-supply rule;
    `notes/shower_niche.md` updated).
  - ~~SANITARY / RAINWATER `IfcDistributionSystem`s~~ — closed 2026-08-02, see the
    drainage block above.
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
