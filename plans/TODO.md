# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" configs.

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
  - ~~RAINWATER / SEWAGE `IfcDistributionSystem`s~~ DONE 2026-08-02: DRAIN runs → SEWAGE
    (IFC4's sanitary member), VENT → VENT, the radon riser deliberately **not** grouped
    with plumbing vents (USERDEFINED/"RADON"), and the silent discard of non-supply
    systems in the emitter is gone. Rainwater stays with the STORMWATER solids system, on
    purpose — the storm run is gutters/leaders/tile, not `PipeRun`s.

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

## Hardwood — DONE 2026-08-02
Landed as the `wood_surfaces` BOM section: one row per (species, material, kind), driven
by the new `Material.species`/`stock_bf_per_sqft` fields and the new room-scoped
`WallPaneling` element (`model/paneling.py` → `resolve/paneling.py` →
`takeoff/wood_surfaces.py`; tests in `test_wood_surfaces.py`). Against each line:
- **Sauna basswood T&G** — billed off the SAUNA assemblies' `sauna-tg` FINISH layers
  (`species="basswood"`, 5/4 → 1.25 bf/sf): ~252 sf net / 278 sf order / ~348 bf. The
  shower corner's two 36" splash walls are `WP-B-SAUNA-SPLASH`, a `replaces_wall_finish`
  tile override to the full 7'-6" liner height — 45 sf net of tile, subtracted from the
  wood. (Known carry-over: W-B-CS bills at full foundation height, the envelope_layers
  convention.) The sauna *ceiling* T&G is still unbilled — the design extends to a
  ceiling variant when wanted.
- **Tudor posts** — four elm `Post`s (`P-S-TUDOR1..4`, `size="6.125x6.125"`, new
  `ELM_TIMBER` finish assembly) standing in W-S-W3's stud line, sheathing face to drywall
  face, tops flush with the 9' plate; no change to CATLIN_EXT_2X6. Billed as 4 pc /
  40 LF ordered (10' sections) / 125.1 bf, mirrored from `structural_solids`.
- **Oak floors** — solid oak retreated to the studies: main-floor living/study went LVP,
  bed/closet carpet; **RM-S-STUDY2 keeps oak alongside RM-A-STUDY** (decision
  2026-08-02), so the oak row bills exactly those two rooms (~318 sf net).
- **Walnut wainscot** — `WP-M-STUDY-WAINSCOT` panels RM-M-STUDY's bounding walls to 36"
  (door punch subtracted): ~50 sf net / 55 sf order = 55 bf of 4/4 (`walnut-tg`).
- **Generality** — any future T&G on walls is a `WallPaneling` (full-height or band,
  per-wall spans, override-or-applied); floors already flow through `floor_finish` +
  species; ceilings are the one surface still without a home.

## Backup Power System Refactor — DONE 2026-08-02
Built as decision #54; the design and its numbers are recorded in
`houses/catlin/notes/backup_power.md`. What landed against each line of the original ask:

- **A proper microgrid, solar + a limited number of circuits.** `Circuit.backup_tier`
  (ALWAYS_ON / SHED) on six circuits, re-homed to `ED-B-BACKUP-PANEL` — a 12-space subpanel
  on the inverter's dedicated load output. The array now lands on the inverter's MPPTs
  instead of backfeeding on its own.
- **EG4 spec.** `EQ-T-EG4-12KPV` + `EQ-T-ESS-BATT` (EG4 PowerPro WallMount Indoor,
  14.3 kWh). Note the 12kPV puts out **8 kW AC continuous**; the 12k is its PV input.
- **How long can it run.** `takeoff/backup_calc.py` answers it, on the E-601 sheet and in
  the viewer: 53.0 h on the always-on tier unaided, and with strong sun every other day the
  always-on tier is net **+4.19 kWh** per 48 h — it rides indefinitely. Both tiers together
  do not (−30.61 kWh), which is what the shed tier is for. **One battery is enough; no need
  to size up.** The numbers rest on authored `duty_cycle` estimates — meter and revise.
- **RSD every other panel.** Computed, not assumed, and the answer came back no: the Aptos
  440 W module is 44.40 V cold at the −30 °C design low, so a pair sums to 88.8 V against
  690.12's 80 V. Every module carries a transmitter. `code.NEC_690_12_rapid_shutdown` reads
  `voc_cold`, so a lower-Voc module would change the verdict without changing the check.
- **What is on backup, and what is behind a relay.** Exactly as asked — see the tier table
  in the note.
- **Battery in the mechanical room, heat + smoke alarm, 3' clearance, metal studs, Type X.**
  `RM-B-ESS` in the furnace room's SE corner on `INT_ESS_CLOSET_STEEL`, with
  `AL-B-ESS-SMOKE` + `AL-B-ESS-HEAT` inside it on the always-on tier. The 3' separation is a
  REQUIRED `ClearanceZone` graded by `advisory.ess_clearance` against other equipment and
  panels **through walls** — the resolver's own clearance test exempts peers in another
  room, and a stud wall does not make the distance.
- **40 kWh indoor max, UL 9540.** `code.R327_ess_capacity` and `code.R327_ess_listing`.
  (R327, not R328: this profile's base is the 2018 IRC, where the article is numbered R327.)
- **Keep the future switches easy.** Both are recorded as seams in the note: the garage
  relocation is a re-room (the capacity check already exempts garage occupancy), and V2H is
  a second `source=True` circuit that needs a feeder element first — the one thing the
  705.12 check cannot yet do is find a subpanel's own main OCPD.

Still open, and deliberately not built (nothing to author against yet):
- High-flow water spigot near the battery.
- Mechanical ventilation from the cabinet direct to exterior.

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)
