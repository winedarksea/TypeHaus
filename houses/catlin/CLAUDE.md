> Current north entry, 2026-09-10 (engineered pass, then an owner revision the same day):
> the canopy is FREESTANDING — `RF-BW-CANOPY`, four 24' trusses between two 3-ply 2x12 KDAT
> headers, each header on TWO 6x6 KDAT columns of its own over cast piers, bearing on the
> garage for nothing but the shared sheathing diaphragm. SIX piers on TWO depths: house-side
> −9'-9 7/16" (cast with the open basement excavation), garage-side −7'-0" (cast with the
> garage footings). The landing touches nothing on the house; the tiers are four CAST pours
> on a compacted base, no wood and no piers; `SC-BW-WEST` is in-fill and `RL-BW-SCREEN` is
> the guard. Garage +30in north; bridge composite finish 0; SL-G-STEP-0,
> pads, glazing and the six invented seat connectors retired; HP3 west in open yard. See
> notes/north_entry_structure.md (the bearing map), notes/north_entry_piers.md (the
> arithmetic) and notes/hp3_north_relocation.md.

# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change. `DESIGN-LOG.md` holds the reasoning behind the numbers here
— derivations, rejected alternatives, engine bugs a rule exists to dodge. It is history,
not instruction: when it disagrees with this file or the model, it is the one that is wrong.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules + params.
- `plan/storeys/{basement,main,second,attic,garage}.py` — `# haus: editable` elements.
- `plan/storeys/attic_studio.py` — `# haus: editable`, holds the west attic's
  guest studio: every new node, wall and door, `FO-A-HALL`, the three Rooms (including
  `RM-A-STUDIO`, which is `RM-A-WEST-UNFIN` moved here whole — **a uid follows the element,
  not the file**), `AL-A-STUDIO`, and the second-storey beam `BM-S-BATH-E` with its tee node.
  It feeds **two** storeys from one file, exporting `ATTIC_ELEMENTS` and `SECOND_ELEMENTS` —
  the `plan/mep_erv.py` precedent — because `attic.py` was already 565 lines against
  `AGENTS.md`'s 500. **What deliberately stayed in `attic.py`:** every WALL SPLIT the change
  forced — `W-A-C2`/`W-A-C2M`/`W-A-C2B`, `W-A-N2`/`W-A-N2B`, `W-A-W1`/`W-A-W1B` — so nobody
  reading a line has to look in two files for a segment of it, and `RB-HOUSE.bearing_refs`
  sits beside the walls it names.
- `plan/lighting_attic.py`, `plan/electrical_attic.py` — `# haus: editable`, split off for the
  same reason (`lighting.py` was 1,158 lines, `electrical.py` 1,700). Split
  by STOREY, which is how `plan/manifest.py` already consumes both. An editable file cannot
  `from plan import ...`, so the manifest composes; nothing imports across.
- `plan/assemblies.py`, `plan/site.py`, `plan/placeables.py` — editable assemblies/site/placeables.
- `plan/mep*.py` — MEP *instances*, split by system so no file runs past ~400 lines:
  `mep_sleeves` (cast penetrations), `mep_drainage`, `mep_venting`, `mep_supply` +
  `mep_supply_devices`, `mep_hvac` (System 1's conditioned-air chase, equipment, terminal
  types), `mep_erv` + `mep_erv_types` (the ventilator, its manifolds, its outdoor side, its
  risers and radials), `mep_registers`, `mep_electrical` (symbols). All ten are
  `# haus: editable`. `plan/mep.py` itself is now only the four storey element lists the
  manifest consumes — NOT editable, because an aggregator needs `from plan import ...` and
  the dialect forbids it. **`mep_erv.py` cannot import `mep_erv_types.py`** for that same
  reason; the aggregator imports both and hands both to `Library(...)`.
- `plan/fixtures.py` — `# haus: editable` plumbing-fixture *instances* (so UI drags
  round-trip). Only explicit constructors in any of these — no functions/generators.
- `plan/electrical.py` — `# haus: editable` electrical service upgrade: meter, backup
  enclosure, 240V/EV/spa devices, conduit trunks, NEC 210.52 fill receptacles.
- `plan/circuits.py` — the panel schedule (NOT editable: Circuits are schedule data, not
  geometry). Devices point at circuits via `circuit=`; `electrical.circuit_refs` reconciles.
  **BOTH MAIN-FLOOR WATER CLOSETS ARE BIDET TOILETS, AND THE ELECTRICAL FOR THEM IS TWO
  CIRCUITS THAT MUST NEVER BE GANGED.** `FX-M-BATH1-WC` is a TOTO SP wall-hung on a DuoFit
  carrier — **the carrier brand IS the bidet decision**, because only TOTO's frame carries
  the concealed WASHLET+ supply — and `FX-M-BATH2-WC` is a Carlyle II whose `AT40` suffix is
  that same readiness. Two WASHLET S5 seats ride on them (`plumbing-bidet-seats`, the seats
  only). `CKT-WASHLET-BATH1`/`-BATH2` at slots 25 and 28 feed `ED-M-BATH1-WC-RC` /
  `ED-M-BATH2-WC-RC`, one outlet each, GFCI at the DEVICE (a washlet trips a Class A GFCI
  now and then and a reset in the basement for a toilet seat is the failure mode the
  convention avoids), no AFCI (210.12 exempts bathrooms), `load_va=0`.
  - **Both boxes are in ONE stud bay and there is no second candidate.** `W-M-HS1` is the
    wet wall between the two baths and carries both bowls; the resolved framing leaves
    exactly one clear 2x6 cavity beside them, x 8 1/8"..15" between `stud-000` and the
    carrier's west king. Everything east is the 19 3/4" carrier bay, then the vanity at
    x=41 1/2" on the north face and the tub deck on the south. The two boxes are back to
    back on opposite faces of that one bay — a 4" device cannot be offset inside 6 7/8" —
    with ~1 1/2" of air between them. **Confirm the bay is still free of MEP before putting
    anything else in it**: today no pipe, conduit, duct, sleeve or accessory has a vertex in
    x 4"..22", y 258"..278", and the west end of a wet wall is exactly where a plumber
    reaches for a spare bay.
  - **`load_va=0` IS A COINCIDENCE JUDGEMENT, NOT AN OMISSION** (owner's call). Each seat is
    ~1,400 VA and only while its instantaneous heater runs — seconds per use. At the other
    reading of 220.82 (nameplate under (B)(3)) `electrical.service_load` goes 191.4 A ->
    196.1 A against the 200 A service and still passes, so this is not load-hiding to make a
    check green. **Revisit it if anything with a real duty cycle joins these circuits.**
  - **THE WARM WATER IS THE ELECTRICITY.** An S5 heats from the COLD supply instantaneously.
    No WC in this house takes a hot run and none should — `needs` is `WATER_COLD` on all six
    and every `PR-*-HW-*` deliberately omits the WC. The heated SEAT is switched off by
    owner's choice (heated floors); it is a setting on the same appliance, so it is worth no
    line in the order either way.
- `plan/lighting.py` — `# haus: editable` luminaire/LED-run/control *instances*, room by
  room. Every light names its switch(es) in `controlled_by`; 24V runs name a `psu_ref`
  instead of a circuit. The `ED-*-LT` fixtures still live in `plan/mep_electrical.py` — they were
  re-typed in place from the old generic `ED-T-LIGHT` so their uids (and IFC GlobalIds)
  survived — and each is one corner of a grid completed here.
- `plan/lighting_types.py` — the `LuminaireType` catalog, schedule marks A–P (NOT
  editable: `frozenset` again). Marks must stay unique; the E-602 schedule is keyed on
  them. Also holds the two 24V supply types and the dimmer/timer switch types.
- `params/solar.py` — rooftop PV array (12 × 440 W on the gable ridge, computed max fit).
- `params/roof_trim.py` — the eave water chain on RF-HOUSE's west/east eaves: drip edge →
  box gutter → downspout, each piece's position derived from the one above it so the laps
  hold. RF-HOUSE has **no fascia** (continuous metal skin ⇒ the resolver's corner trim), so
  every offset is measured off the corner trim's face, never a fascia's. "Continuous" is
  `Material.skin_family`, not tag equality — the walls are exposed-fastener PBR and the roof
  is mechanically seamed, and they read as one skin because both declare
  `skin_family="standing-seam"`. Drop that on either and the flush edge silently reverts to
  a fascia-and-drip-edge detail nobody has drawn. The lap
  order is enforced by `packages/engine/tests/test_catlin_eave_water.py` — read it before
  moving any of these numbers. All three pieces are ordered in `_CHAIN_MATERIAL`, the
  house's one exterior dark, so the eave line matches the rake's corner trim.
- `typehaus/library/placeables/*.py` (inside the engine, not this directory) — the shared FixtureType/
  ApplianceType/FurnitureType *catalog*, wired in by `plan/manifest.py`. NOT editable: it
  uses `frozenset(...)`, which the dialect forbids. Type libraries stay non-editable;
  movable instances that reference them live in the editable modules above. **`plan/
  fixture_types.py` holds SEVEN selections** — `FX-KOHLER-UNDERSCORE-6036`
  (the drop-in bath) and `FX-VANITY-51-SINGLE` (RM-M-BATH2's vanity), plus
  the six vanities that replaced this house's remaining bare lavatories:
  `FX-VANITY-24-SHALLOW` (RM-M-BATH1 and, since 2026-09-09, RM-A-STUBATH — 24" is the whole
  width that bath's north wall has between ED-A-STUBATH-GFCI's plate and the neo-angle shower
  it got in the same pass), `FX-VANITY-30-SHALLOW` (RM-S-VANITY, TWICE — a 60"
  double alcove is two 30" bases under one 61" top, which is how one is actually built and
  which keeps two drains and two lavatories in the schedule instead of collapsing them),
  `FX-VANITY-30-SINGLE` (RM-S-SUITEBATH), `FX-VANITY-36-SHALLOW` (RM-B-BATH — 18" deep
  on the pallet-depth argument alone since 2026-09-05; the door-swing argument that forced
  it went with the room's rotation) and
  `FX-VANITY-48-SINGLE` (RM-S-BATH1).
  **`-SHALLOW` is 18" deep and `-SINGLE` is 21"**, and shallow is not the premium it sounds
  like: the cheap big-box combos that arrive boxed with their top and bowl already on them
  are 18.6"-18.75" deep, so 18" is the pallet depth. Widths are the stock ladder
  (24/30/36/48/60) — 18/42/54 are one-SKU-or-special-order, which is why RM-S-BATH1 got 48"
  rather than the 42" that a bounding-box reading of its door swing would have forced.
  **`FX-LAV-24` prices ZERO instances and the row is kept anyway** (the
  `glazed-green-brick` convention). **`RM-A-STUBATH` deliberately keeps its
  `FX-LAV-COMPACT`**: its water closet is on the west wall, and the 24"
  front envelope that creates crosses the only wall a vanity could have used.
  **The 21" front zone on every vanity type is a design convention, NOT a Minnesota code
  minimum** — Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33, ch. 4714 adopts the
  2018 UPC, and UPC 402.5 names only water closets and bidets, so a lavatory has no MN
  plumbing front clearance at all. (An earlier comment cited a UPC "Exception 1" giving
  lavatories 21" in dwelling units; that text is a *Washington* amendment.) The guest
  studio's wet bar uses `FX-LAV-COMPACT` (18" x 14"), dimensionally exact for a bar bowl
  and costing no catalog entry. **Borrowing a catalog type from the other direction** is
  free only while the borrowed type's footprint, symbol and schedule line are all still true
  of the thing in the room — `FX-M-BATH2-SINK` no longer borrows `FX-KITCHEN-SINK-33` (a
  double-bowl kitchen sink) for exactly that reason; it modelled no cabinet.
  **RM-M-BATH2 has storage above the toilet**:
  `FURN-M-BATH2-CAB` / `FT-BATH2-CAB-4506`, a 45" x 6" x 60" flush-fronted box on the room's
  only free wall (W-M-HS1's bath face), bottom at 4'-0" AFF — which is a **code line, not a
  comfort choice**: below `FX-TOILET-STD`'s own 30" top the wall face would move 6" south and
  take the bowl's front clearance 2.8" into the vanity. It is also why
  `resolve/placeables.py::_mounted_over_the_fixture` exists (→ `plans/01-decisions.md` #67,
  `notes/bath2_over_toilet_cabinet.md`): the engine was calling a 6"-deep cabinet 4' up an
  ERROR against UPC 402.5, whose 15" is elbow room for a *seated* person and not a column of
  air.
- `params/sunken_garden.py` — the freestanding arched porch/garden structure (math OK here).
- `params/foundations.py` — house footings, garage ICF stem + slab.
- `params/north_entry_frame.py` — the north entry STRUCTURE: geometry constants, the beam
  factory, the seven beams, six piers and their footings, the four KDAT roof columns and the
  two interior posts. Publishes every constant `breezeway.py` and `plan/views.py` read, so
  the two cannot drift.
- `params/breezeway.py` — what sits on that: the landing, the four cast tier pours, the
  guards, the slat screen, the seat/cap/truss-tie connectors and the annotations. The canopy `Roof` itself is authored in
  `plan/storeys/garage.py`, because a roof belongs to a storey.
- `notes/*.md` — construction detail notes migrated from the original repo.

**Editability rule (enforced):** any UI-movable element (Furniture/Fixture/Appliance/
Equipment/Register/ElectricalDevice/Door/Window/Wall/Room/Node/Stair) must be authored in a
`# haus: editable` file, or its canvas edits can't be written back. The loader raises
`loader.uneditable_movable_element` (a hard build error) if one is authored in a non-editable
## House facts that must stay true

Each section below is the building as it stands. The reasoning behind a number, the
alternatives that were rejected, and the engine bugs these rules dodge live in
`DESIGN-LOG.md` under the same section title.

### Site and the four structures

- Four structures: house, garage (4' north gap), sunken-garden/porch/balcony concrete structure (5" south gap), and the north-entry bridge (4' gap).
- **The north entry is engineered, not schematic** (2026-09-10). `RF-BW-CANOPY` spans 24' between `BM-BW-RW`/`-RE`, which top out at +7'-4" — the garage plate — so the two roof planes are ONE plane; change either and they step apart. **The canopy is freestanding**: each header lands on two 6x6 KDAT columns of its own (`PT-BW-CW`/`-CNW`, `PT-BW-CE`/`-CNE`) and on no garage framing at all. It bore on `W-G-W`/`W-G-E` until the owner revision — a ~3,130 lb reaction on the END of a stud wall, with no bearing post authored, drawn or billed. Its sheathing runs continuous across the garage south wall line and **that diaphragm is the canopy's entire lateral system and its only connection to the garage**; all four column bases are standoffs, not moment connections. Every truss ties to its header with a stainless `H2.5ASS` at both ends (`CN-BW-TRTIE-*`), authored rather than derived — the derived rule would have bought the galvanized H2.5A. **SIX cast piers on TWO bearing planes and the split matters**: `PT-BW-W`/`-E`/`-RE` bottom at −9'-9 7/16" with the house footing ten inches away, so **cast them in the open basement excavation or they undermine it**; `PT-BW-GW`/`-GE`/`-RNE` bottom at −7'-0", coplanar with the garage strip footings, and are cast with the garage foundation. Nothing here names a `W-B-*` or a `W-G-*` tag. See notes/north_entry_structure.md and notes/north_entry_piers.md. (→ DESIGN-LOG.md, "Site and the four structures")
- **Grade is 2'-10" below the main floor.** **Datum is the TOP OF JOISTS, not the finished floor** — main-floor FFE is +3/4", so a slab landing there needs an explicit `top_elevation` (`params/main_deck.py`).
- Basement storey is at -9'-1 7/16", independent of grade. Pour is exactly 8'-0"; clear height 8'-0 15/16" under joists / 7'-10 7/8" under the EPS band. `code.R305_ceiling_height` DERIVES this, not `Storey.default_ceiling_height` (still a fictional 9'-0") (→ DESIGN-LOG.md, "Site and the four structures").
- Grade-dependent: garage + foundation, bridge's frost pads/piers, hydrant bury, sunken garden floor, nine perimeter spot elevations, both impervious surfaces. `SITE_GRADE` lives in `params/foundations.py`, repeated as a literal in `plan/site.py`; `plan/manifest.py` asserts the two agree.
- **Garage storey datum is not the garage floor.** Walls bear on the ICF stem at `GARAGE_STEM_REVEAL` (1'-10") above grade → `garage` storey at -1'-0"; the slab pours at grade (1'-10" lower), absolute `Slab.top_elevation`.
- Sitting on the garage floor must be explicit: `D-G-OVERHEAD` carries the plan's only negative `sill_height`; the ICF stem becomes a curb-free grade beam there.
- `D-G-SERVICE` threshold stays 0'-0" with the bridge deck (`+1'-0"` sill); the 2'-10" drop is five 6.8" risers inside (`ST-G-SERVICE` KDAT, `RL-G-SERVICE`). `SL-G-STEP-0` is retired — `FS-BW-GARAGE` replaces it — though stray comments in `plan/storeys/garage.py` and `plan/assemblies.py` still name it.
- `Stair.floor_opening` is optional (a rise states directly via `base_elevation`/`top_elevation`) — but `structural.stair_riser_uniformity` and `code.R311_7_8_handrail` iterate `model.stairs`, so slabs instead of a `Stair` draw NO riser/handrail finding.
- Garage plates are 8'-4", not 8'-0" — the door climbed 4" when the storey dropped; a shorter plate would push the 3-ply LVL header into the truss heels.
- Emitters/placeable resolver read `resolve/room_floor.py::room_floor_elevation` for garage heights, not storey elevation — enforced by `test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade`.
- **ICF stem and wood wall are coplanar outside.** `GARAGE_Y_SOUTH`/`NORTH` (`plan/storeys/garage.py`) is both the sheathing plane and the stem's EPS face (walls `cdx-ext`, stem `concrete-ext`+`GARAGE_ICF_EPS` offset) — layer NAME is the alignment key, so a sheathing swap is also an alignment edit or the wall silently misplaces. Only 7/8" of the corrugated panel projects past.
- Do not fix alignment by moving stem nodes — `resolve/stacking.py::_axis_match`'s 1/2" tolerance would silently drop the whole foundation-to-framed stack.
- `FT-GF-*` follow the stem via `Footing.center_on="wall"`, not the node line.

### Shell: framing module and envelope

- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` as the vertical datum (#43). Side-wall stack is 2x6
  throughout — one `EXT_2X6` on main, second and attic. Main-storey studs are LSL, upper
  storeys dimensional 2x6 (a purchasing note in the assembly's `source`).
- It is a CATLIN TRUSS WALL outboard of the sheathing, ONE girt tier: 4" ccSPF crossed only
  by the blocks, then the block's proud 1/2" as a continuous vent gap, then one tier of flat
  horizontal KDAT 2x4 girts at 24" o.c. in free air, then the panel. Each crossing: three
  loose 3-1/2"x3-1/2"x1-1/2" KDAT offcuts stacked to 4-1/2" over every OTHER stud, clamped
  by one 8" SDWS22800DB through girt + block + sheathing, 1-1/2" into the stud. There is
  only ONE tier — do not add a second inner one; the foam needs no backing (ESR-4073
  §4.4.2, ESL-1372) (→ DESIGN-LOG.md, "Shell: framing module and envelope").
- THE SCREW IS THE ONLY LOAD PATH per crossing, no second tier, no nail — 54% utilised at
  Exposure C, 38% at Exposure B. Mark the stud line across the girt face as it's laid: the
  screw is blind through 6" of wood into a 1-1/2" target, invisible once the foam is on —
  inspect the pattern before the sprayer arrives.
- There is no WRB — the foam is air/water/vapour/thermal; `plan/transitions.py` names
  `spray-foam-ext` as the water/thermal plane. Wood and the screw pass happen on the FLAT
  wall before tilt; fillet the foam against the block sides (BSI-048), never butt square.
- Everything outboard of sheathing is KDAT — one BOM row, plus `3-2x4:kdat` for the block.
  Blocks are on the STUD module, every OTHER stud, at 32" from the wall's LAYOUT LINE (girts
  run their own 24" module) — 32"x24"=5.33 ft2 is the crossing tributary in
  `notes/catlin_truss_engineering.md`. Block phase is solved for 32", not 16" — reusing the
  stud phase puts half a facade's segments on the wrong parity.
- Girt course module counts from the SILLS' datum, phase ZERO
  (`course_datum="framing-base"` + `course_offset=inch(0)`), not the wall base. One module
  runs unbroken from wall base through the gable rake, breaking only at a starter (band
  bottom), a top course (level wall), and a rake nailer (gable's raked top, field one board
  clear).
- NEW-OPENING RULE: head on a 24" multiple above the sole plate (24/48/72/96"), or sill
  3-1/2" above one — this phase is the only one keeping every bay ≤24.00"
  (`structural.girt_course_spacing` FAILs otherwise) (→ DESIGN-LOG.md, "Shell: framing
  module and envelope").
- Windows are OUTIE, mount plane 6" out from sheathing on the outermost furring layer's
  outer face (derived, never authored, so unaffected by cladding-depth changes).
  `structural.truss_wall_opening_support` keeps every RO jamb within a flange's bearing of
  wood.
- Cladding face stands 7.25" proud of sheathing (`_WALL_OUTBOARD_IN` in
  `params/roof_trim.py`). Consumers that hand-transcribe this and must move together:
  `params/north_entry_frame.py::HOUSE_CLADDING_Y_FT`, `params/sunken_garden.py`'s `gap_to_house_in`,
  exterior devices in `plan/electrical.py`.
- The Swinburne truss (vertical `laid="edge"` framing) is one swap away:
  `resolve/framing/truss_frame.py` sits behind its own predicate, the girt frame is a
  sibling on `standoff="block"`, and the old layer tuple survives verbatim as
  `EXT_2X6_SWINBURNE` (referenced by nothing) — revert steps in
  `notes/outie_window_truss_detail.md`.
- R-value card reads R-43.5; honest is ≈R-39.8 wood-only / ≈R-37.9 with girt screws counted
  (blocks are framed, not a `CavityFill`; girt credited its own R though outboard of the
  vent gap). `wall_r=40` is met wood-only (39.85) and 2.1 short with fasteners in — don't
  read either number as the other. See engineering note §7, §7.1.
- Stud bay is FIBREGLASS, not mineral wool, EXCEPT tub deck, saunas, plant rooms, and
  `_GARDEN_FRAMED_STUD` — do not sweep those next time (list in `plan/assemblies.py` above
  `EXT_2X6_SWINBURNE`).
- `INT_2X4_PARTITION` has NO insulation. Exception: `W-S-SS2` uses `INT_2X4_RC` (resilient
  channel, STC 48) instead of a batt.
  - Rated STC 34 (USG SA924/UL U305/U314) at 16" o.c. — do not difference against the old
    insulated 36; different test series. Card over-reports it too: no `CavityFill` means
    `analysis._layer_rsi` bills the stud layer as solid SPF (R-6.4 vs honest ~R-2.5-3),
    harmless only because `INT` excludes it from `mn_energy` — never quote the card here.
  - Knowingly left uninsulated (fix, if wanted, is a retype to `INT_2X4_RC`, not a batt):
    `W-S-SBS`, `W-M-BDN1`, `W-A-BATH-S`, `W-M-HS3`.
  - On `W-S-SS2` the channel must stay on the NORTH face: the south face carries ST-S2A's
    stringer ledger/handrail and a void boundary `attic.py` defines off it; moving it south
    leaves 35-1/2" against R311.7.1's 36".
- Cladding split by orientation: `board-batten-24` (1,678.3 SF, 24 ga concealed-fastener
  PVDF, 20" net coverage) on the 20 east-west-facing walls; `pbr-panel-26` (1,416.6 SF) on
  the rest — a per-wall `Wall.layer_materials` override, not a sibling assembly (→
  DESIGN-LOG.md, "Shell: framing module and envelope").
  - Thickness stays 1-1/4" — LOAD BEARING for the same four consumers listed above
    (`_WALL_OUTBOARD_IN`, `HOUSE_CLADDING_Y_FT`, `gap_to_house_in`, `plan/electrical.py`).
    `skin_family="standing-seam"` must stay on BOTH panels or the flush zero-overhang edge
    reverts to fascia-and-drip-edge on all four edges. `exposed_fastener` is deliberately
    ABSENT (`T09150HWAM` is 1,804: 640 garage + 1,164 E/W PBR; `attic` storey has none).
  - Ten separate registrations render the appearance across `ui/src/three/materials.ts`,
    `ui/src/nordic/palette.ts`, `emit/gltf/palette.py`, `emit/draw/palette.py`,
    `ui/src/components/DetailCanvas.tsx`, and `emit/draw/elevation_finish.py`'s
    `_BATTEN_PITCH_M` — each silent if missed; full list (→ DESIGN-LOG.md, "Shell: framing
    module and envelope"). The `elevation_finish.py` one is the trap: without its
    finish-first branch it draws 16" seam pitch, not 20" battens.
  - Four wall corners now bill: `TrimKind.WALL_CORNER` + `Flashing.vertical`, 89.5 LF,
    derived off `_WALL_OUTBOARD_IN`. Without `vertical`, a 22'-4" corner bills as 1-1/4" of
    metal (`_EdgeRun.path` is a plan polyline).
  - ENGINEERED, not prescriptive (decision #65): `wall_panel/<wall tag>` x 20 is INCOMPLETE
    even though bending passes (d/c 0.31, 58 psf allowable at 24" girts) — screw-withdrawal
    capacity is published by nobody, oracled by `notes/board_batten_girt_span.md`. PBR stays
    prescriptive (ASC PS230/Metal Panels Inc./Homewood span tables, 144-168 psf at 3'-0").
  - ESR-4729 DOES NOT COVER THIS WALL — Western States' ROOF-panel report, 24 ga min over
    16 ga steel. Do not reintroduce it. Of eight surveyed, only Western States and Metal
    Sales permit open girts, and only Metal Sales is verified — substituting another forces
    a second girt course or a continuous deck. Cladding screw is 1-1/2", stainless or ASTM
    A153 Class D HDG, never the 1" plated pancake screw a panel ships with — must take the
    full girt thickness; Metal Sales' "1/2" past inside face" clause needs a variance (open).
  - Revert = delete the twenty `layer_materials=` overrides; `pbr-panel-26` and its
    `prices.toml` row stay live on the other elevations.
- Every exterior corner is construction-correct, 4-stud. Layout grid is struck from the
  building's outside sheathing corner: all four facade lines origin `+0.0000"`; 217 of 241
  exterior module studs land on exact 16" multiples (24 exceptions are the corner posts);
  all 31 exterior windows centre on that grid.
  - `EXT_2X6` and `PLANT_EXT_2X6_HUMID` carry `corner_style="4-stud"` (`preferences.toml`'s
    `[framing] corner` states it once) — valid because the continuous exterior foam, not the
    post cavity, is the primary insulation. `resolve/framing/solver.py::frame_model`
    resolves a corner's style from BOTH incident walls (→ DESIGN-LOG.md, "Shell: framing
    module and envelope"). `GARAGE_WALL_2X6` stays 3-stud (no continuous exterior foam);
    `structural.corner_style_matches_preference` is scoped accordingly.
  - The corner box is RETIRED for the girt band (courses butt at the corner, nothing
    full-height to cap); `FramingSpec.corner_cap`/`TrussFrame.corner_box` still fire for any
    band that asks (`EXT_2X6_SWINBURNE` still does).
  - The 1/2" sheathing lap at the corner is still undeclared (all layers mitre 45° today) —
    logged in `plans/TODO.md`, not built.

### Bearing lines and floor decks

- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' spans E-W, on every
  storey and in both materials.
- **Second storey has a fourth bearing line, x=10'-0".** `W-S-BA-E`, `W-S-BA-E1B`,
  `W-S-BD-N1B` carry `FO-A-HALL`'s attic joist cut ends: `structural_role=BEARING` and
  `INT_2X6_BRG_PLUMBING` (continuous studs, not staggered — `structural.wet_wall_bearing`
  FAILs a staggered BEARING wall). Thickness unchanged (6.77"): no face/area moved,
  `FX-S-BATH1-LAV.wall_ref` untouched.
  - `stacks_on` is MANDATORY: `W-M-STRW` has two collinear upper candidates (`W-S-BA-E`,
    `W-S-BA-E1B`) and `integrity.stack_ambiguous` is a hard ERROR without one. Only
    `W-S-BA-E1B` names `W-M-STRW` — do not also point `W-S-BA-E` at it, only one upper wall
    may claim a lower wall.
  - y=22'-4" to 26'-6" on this line has no wall and never can (the hall stub mouth to
    `D-S-BATH1`); `BM-S-BATH-E` spans it, `3-1.75x11.875 LVL` flush (`top_elevation=ft(20)`).
    Ply count (3, matching `BM-S-HALL`) is set by bearing WIDTH so the 4.77" attic partition
    doesn't overhang, not by bending demand (→ DESIGN-LOG.md, "Bearing lines and floor decks").
- **Basement ceiling: ONE FLAT BEARING SEAT at -13 7/16", not one depth.** `FS-M-WEST`,
  `FS-M-MECH`, `FS-M-STAIR` (x 0'-18') and `FS-M-EAST` (x 18'-36', y 0'-13') are 11 7/8"
  I-joists at 16" o.c.; `SL-M-DECK` (414 SF) is a 10" LiteDeck EPS SIP beam (8" base + 2" top
  hat) under 4 3/8" cast cover. One plate serves studs and joists, no step in the forms.
  Seat/depth constants live in `params/main_deck.py` — moving the boundary is a one-line
  edit there. `structural.mixed_deck_bearing_seat` (FAIL) and `integrity.floor_bearing_grid`
  hold this.
  - Ceiling is 5/8" gypsum end to end (IRC R316.4, `ceiling_below` on the joist fields), but
    the two faces step 2 1/16" at the boundary. `RM-B-GYM` (only room crossing it) resolves
    TWO ceilings — 234 SF at -11 7/8", 90 SF at -13 7/16" — since ceilings derive per *deck
    region* (`resolve/ceilings.py`, `ceiling_over.ceiling_regions`), not per room. A seam
    alone isn't a step: `RM-M-LIVING` (2nd-floor truss/I-joist split, same depth) is ONE.
  - Floor finish follows the deck via `_BAND_Y`: `SL-M-DECK.floor_finish=polished-concrete`,
    `RM-M-LIVING.floor_finish=lvp` over the wood bays; this band is the room's only zone,
    and nothing is currently authored on it. Prefer a derived zone over authoring one here —
    an authored zone's drawn ring must be clipped to the room, same as its area (fixed
    2026-09-05).
  - `RM-M-MUDROOM` + its closets (`RM-M-MECH`, `RM-M-MUD-CLOSET`) are porcelain over an
    uncoupling membrane (`integrity.concrete_finish_needs_concrete_deck` keeps them off
    concrete since `FS-M-MECH` is I-joist/plywood) — tiled because their doors open INTO the
    mudroom, not because they're wet; don't put either back on plank, it islands the tile.
  - Two walking planes meet flush (plank +0.986" vs polished cap +15/16") on both legs of
    the L; only the mudroom breaks it (~+1 5/16", ~5/16" strip at `D-M-MUD`, the one
    threshold on the storey). Oak (+1 1/2") is the two studies' floor only — never extend it
    to a cap edge (→ DESIGN-LOG.md, "Bearing lines and floor decks"). Junction detail is in
    `notes/mixed_deck_movement_joint.md`; mix is `POLISHED_MIX` (micro-monofilament PP, no
    macro fibre or steel).
- **Second floor's deck is mixed for services, not material.** `FS-S-WEST` (x 0'-18') is
  11 7/8" open-web trimmable floor trusses at 16" o.c.; `FS-S-EAST` (x 18'-36') is 11 7/8"
  I-joists. West carries nearly every 2nd-floor service crossing (both drain stacks, 4
  supply risers, radon/plumbing chase, hydrant distribution, data conduits) through the
  webs (8 7/8" clear opening, `resolve/framing/profiles.py::open_web_opening_m`) rather than
  boring/soffiting/chasing. Both fields stay 11 7/8" deliberately, so the split needs no
  movement joint or finish break.
  - Trimmable stock is 18'/20', up to 6" trim per end. Bearing grid is 18'-0" but the truss
    is 17'-11" (`resolve/floor_ends.py`), clear span 17'-3¼"; an 18' blank trimmed 1" covers
    it (`takeoff/framing.py::_order_length_ft`). The shared x=18' plate splits 3½" to the
    truss / 2" to the I-joist (`params/second_deck.py`, also holds the shared depth constant
    `params/main_deck.py` imports) — don't centreline-split it, it shorts the truss's seat
    (`integrity.floor_end_bearing` grades this). `FO-S-STAIR` clips 8 joist lines in the
    west half to 10'-1⅝", outside the trimmable range, fabricated to length.
  - Truss price row in `prices.toml` is a placeholder pending a fabricator quote; the
    borrowed I-joist span-table row (`checks/structural/checks.py::_IJOIST_SPAN_FT`) is
    advisory only at 18'-0" — the fabricator's table governs.

### Attic and roof

- Attic is a hot-roofed cathedral space: rafter plates E/W (not knee walls), gables N/S,
  ridge N-S, 6:12, zero overhang.
- **The line every attic station answers to**: roof underside is `1 1/2" + x/2` above the
  attic finished floor, mirrored past x=18'-0" — 9'-1 1/2" at the ridge, 7'-0" at
  x=13'-9", 5'-0" at x=9'-9", 3'-0" at x=5'-9". Every height quoted in `plan/` (window
  head, can light, receptacle, door, duct, furniture, vent riser) is measured from this
  line. Corollary for an opening: a head at `h` needs `h + 2"` of rake: `x_outer_jamb >= 2
  x (head + 2")`. (→ log4.md, "Attic and roof" — the 6:12/knee-wall history and cost
  delta)
- `FS-ATTIC` is also the 2nd storey's ceiling: authors `ceiling_below` (5/8" gypsum)
  inline, since `plan/storeys/attic.py` is `# haus: editable` and can't import `params/`.
  Exception: `RM-S-PLANT` uses `Room.ceiling_lining` instead.

- `RM-A-WEST-UNFIN` is now four rooms (was 598 sf unused loft):
  - `FO-A-HALL` (x 10'-0"..18'-0", y 22'-6 3/8"..35'-5 3/8"): stair well + hall run open
    to the roof underside. `purpose=STAIR` must be explicit — `code.R312_1_guard` filters
    on it and `code.R312_1_guard_height` never walks a void, so `CHASE` would drop
    fall-protection checking entirely. Never add x=10' to `FS-ATTIC.joists.bearing_refs`
    for this void — the field is global to the deck and would cut all ~34 joist lines
    including the 17 over the suite.
  - `RM-A-STUDIO`: `Occupancy.BEDROOM`, `floor_finish="vinyl-sheet"` over
    `plywood-subfloor`, uid `CAR401AAAA` (retagged in place). `RM-A-STUDY` next door is
    oak. BEDROOM occupancy is load-bearing for R310, the ventilation bedroom count,
    R314/R315, and whether `electrical.receptacle_spacing` evaluates the room at all. (→
    log4.md, floor-finish history)
    - 13.6 sf glazing, none addable (south gable mirror about x=18' is fixed; dormer/roof
      penetration excluded). R303.1 has passed on daylight since 2026-09-10 via
      `ResolvedRoom.head_limited_area_m2` (146 sf, area under the roof UNDERSIDE per
      R304.3) rather than the whole 356 sf — needs 11.7 sf glazing (has 13.6).
      `code.R305_ceiling_height` still reads 190 sf off the rafter TOP; the two are not
      reconciled. Revert lives in `_r303_floor_area`
      (`checks/code/mn_residential/ventilation.py`). (→ log4.md, literal-reading risk)
    - Exception 1's lumen floor no longer binds this room while it passes on daylight —
      `plan/lighting_attic.py` claims of R303.1-required fittings are stale (room carries
      5,400 lm over 146 sf). `REG-A-HP-WEST` stays regardless (graded on BEDROOM
      occupancy, not Exception 1).
  - `RM-A-STUBATH` (x 9'-10 7/8"..17'-8 5/8", y 17'-6 3/8"..22'-1 5/8", vinyl-sheet). Tag
    must stay `RM-A-STUBATH`, never `RM-A-STUDIO-BATH` — `electrical.room_lighting`
    matches `ED-{room.tag[3:]}-*` and the longer tag would prefix-match the studio,
    merging luminaire sets. x=9'-7 1/2" is `W-S-DC2`'s axis (no stud to bore); y=17'-4" is
    a joist line under `W-A-BATH-S`'s sole plate. Vent starts over the shower (6'-7" trap
    arm vs Table 1002.2's 5'-0"). No `humidity_class` set (NORMAL like every other bath) —
    WET would pull ROOF into the humid-room condensation walk for nothing.
  - `RM-A-POCKET` (x 0..9'-7 1/2", y 22'-4"..36', STORAGE). Door `D-A-POCKET` is in the
    SOUTH wall of `W-A-STU-N`, not the x=10' wall (far side is the void/shaft). Wall raked
    at 5'-0"+x/3; a 6'-8" head needs x ≥ 5'-9" (`structural.member_interference` catches a
    shallower station). Door not scuttle: ERV manifold, OA hood, `VR-M-RADON-VENT` head
    sit inside, so IRC M1305.1.3 wants the passageway plus its light and receptacle
    (`ED-A-POCKET-LT1`, `ED-A-POCKET-RC1`). `ResolvedRoom.head_limited_area_m2` is what the plan label
    and `haus build` report beside `area_m2` (whole attic: 496 of 1,171 sf built); every
    takeoff still reads `area_m2`.
  - Walls split for this void: `W-A-C2` (×2), `W-A-N2`, `W-A-W1` — a mid-span tee leaves
    `resolve/topology.py`'s junction solver without a shared endpoint; TAG/UID stay on the
    piece keeping a hosted opening. Exception: `W-A-STU-W`'s north end dies short into
    `W-A-STU-N`'s face, so `N-A-WW-N` carries `open_end=True`. `RB-HOUSE.bearing_refs`
    names all five segments; `test_ridge_beam_depth.py` pins the tuple.
  - ERV hoods: west face at the NW chase, intake +4'-0" (main), discharge +17'-0" (second)
    — moved off the north gable entirely (`plan/mep_erv.py`). (→ log4.md, why the gable
    failed)
  - `DU-A-ERV-R-BED3` and `CD-A-DATA-NE` both route SOUTH — the only option, since
    `FO-A-HALL`'s maxy is `W-A-N2`'s gwb face, severing every west→east route north of the
    studio. BED3 (5 cfm) runs ~53'-6"; `DU-S-ERV-HP-FEED` (100 cfm) sets the x=1'-0" chase
    section, turning east at y=22'-0" to `SF-S-HP1`'s drop up `RM-A-EAST-UNFIN`.
  - `DU-M-ERV-R-PLANT` (was `-A-`): LEVEL-2 manifold, south through `FS-S-WEST`'s open-web
    trusses at x=2'-10", east along y=4'-8", up inside `W-S-C1` to a high sidewall grille
    at 8'-6" (humid air stratifies). `W-S-C1` is `PLANT_INT_2X6_BRG_HUMID` (5 1/2" cavity
    for riser + vapour-tight boot) — `W-S-PS1` is plain 2x4, not sized for this. It is the
    longer, pressure-critical run at 55'-8", affordable because the ERV's rating point is
    0.4" w.g. — HVI certifies the B210E75RT at 206 cfm net supply at 0.4" (HVI ID
    2004940). (→ log4.md, 0.2" misconception)
  - `EQ-M-ERV-MAN-EXH` is full, 10 of 10; the x=2'-10" lane crosses only one sibling
    radial vs eight at the manifold's east end.
  - `AL-A-COMBO` is in `RM-A-STUDY`, `AL-A-STUDIO` in the studio — reversed is a hard
    FAIL: `code.R315_co_every_sleeping_area` fails if every CO alarm on a storey is inside
    a bedroom.
  - `code.N1103_6_whole_house_ventilation` sits at 210 cfm provided against 205 required
    (MN 1322 R403.5) — a seventh bedroom or ~250 sf more conditioned floor fails it.

- `W-A-SN` is a 12 3/4" bookcase wall (`INT_2X4_BOOKCASE_12`); its south face is the only
  cover for `FO-A-STAIR`'s north edge — moving it north FAILs `code.R312_1_guard` (~14'-3"
  unguarded well). It was thickened, not moved (face held at 8'-9 5/8"), why
  `N-A-C2`/`N-A-E1` sit at y=9'-4". Do not split the wall to thin its west 1'-6" — a 4
  3/4" wall there puts the south face 4" north of the well edge, re-opening the FAIL.
  `interior_room="RM-A-STUDY"` is load-bearing on this `Wall` (asymmetric stack-up) —
  without it `orientation.wall_outward_sign` may put the gwb face on the well edge.
- `RM-A-STUDY` reads 165 sf (was 159) because `resolve/rooms.py` builds the room face from
  wall centrelines and the axis moved 4" north though the south face didn't —
  `code.R312_1_guard` (wall footprint union) still passes. `RM-A-EAST-UNFIN` loses the
  same 6 sf (STORAGE, no glazing rule binds).
- Study casework must NOT become a placeable — catalog bookcases are 1'-0" deep against a
  9 7/8" pocket (2 1/8" proud into the well). Priced via `prices.toml [allowances]` lump
  `cabinet-study-bookcase-wall`. `D-A-STUDY` is `DT-INT-BOOKCASE30` (retyped in place);
  `trimless=True` means a millwork case here, NOT the drywall return jamb it means
  elsewhere — never price off `DT-INT-SWING30-TRIMLESS`.

- **Roof is flash-and-batt in the joist bay**: 11-7/8" TJI 230 @ 24" o.c., 5" ccSPF
  against the deck underside + R-30C batt in the remaining 6-7/8", 5/8" CDX plywood,
  self-adhered butyl membrane, standing seam. R-53.2 at 13.1" deep; interior is paint on
  gypsum only. Oracle: `notes/roof_flash_and_batt.md`. (→ log4.md, prior nailbase stack +
  cost delta)
  - Legal with ZERO above-deck foam under IRC/MSRC R806.5 item 5.1.3 (air-impermeable
    insulation at the sheathing meets Table R806.5, air-permeable insulation directly
    under it): 5" ccSPF = R-32.5 against R-25 (zone 6)/R-30 (zone 7). Graded by
    `code.R806_5_unvented_roof`. NO interior Class I vapour retarder, ever — item 2 makes
    a ceiling poly or vapour-barrier primer a code-FAIL, not just a preference.
  - Condensation check reports NOT_APPLICABLE on this roof by design — a steady-state
    Glaser walk can't grade a stack sealed cold-side by a 0-perm metal panel.
    `condensation._r806_5_deferral` defers ONLY where `code.R806_5_unvented_roof` passes.
  - Do not restore a permeable underlayment/vent mat — the impermeable panel above now
    leaves no gap to dry into. The butyl membrane replacing both self-seals ~1,160
    standing-seam clip screws, this roof's real water risk.
  - 24" o.c. spacing is NOT FINAL: `structural.rafter_span` is UNKNOWN/engineered at both
    16" and 24" o.c., and the printed TJ-4000 table assumes bearing at the high end where
    these joists instead HANG off the ridge on 38 LSSR hangers — confirm in ForteWEB
    (fallback TJI 210 @ 19.2" o.c.). Budget for
    upsized eave uplift ties (H10A+); don't bank the H2.5A count falling 378→360 — catlin
    frames SPF at SG 0.42 against H2.5A's SG 0.50 rating, with 1.5x the tributary.
  - The roof deck oversails the last rafter and spans the wall girts, clipping at the
    cladding's back face — that cantilever is graded by nothing in the engine. Stack depth
    is hand-transcribed into `params/roof_trim.py` (`_DRIP_CEILING_IN`,
    `_CLADDING_HEAD_IN`) and into `test_catlin_eave_water.py` — moving a layer must move
    both.

- **Structural ridge, not a rafter-tie roof**: `RB-HOUSE` bears continuously on the
  `W-A-C1/C1B/C2` bearing wall (unbroken to footings), keeping rafters simple spans and
  thrust off the eave line — a beamless center line dumps ~1.5 klf of thrust into a 1 1/2"
  rafter plate that can't take it.
  - Section is `2-1.75x16 LVL`; depth is a HANGER dimension, not span-driven — the beam
    must reach 14.15" below the ridge at the rafter's plumb cut (14" misses by 0.15", 16"
    clears). LVL comes in 9.5/11.875/14/16/18", no 14 1/4". Beam hangs 16" into the room.
    3 1/2" width only works because demand is small: relies on ER-280 §3.2.2's NDS
    penetration reduction (~600 lb/rafter against 1,565 lb capacity) so mirrored LSSR
    header nails on 28 opposing rafter pairs don't overlap.
  - Peak hardware: 38 beveled web stiffeners both sides (23/32" ply ripped 4" wide — NOT a
    2x4, cavity is 15/16" a side), 19 LSTA24 over the top per pair (mandatory above 3:12
    per Weyerhaeuser H5S), 10 H2.5A tying beam to plate at 4' o.c. (`uplift_path.py` skips
    a `Beam.bearing_ref` that resolves to a wall, so this joint had none before).
  - Ordered as three 12' pieces, not one 36' stick — `FramedMember.continuously_supported`
    sends a beam supported everywhere to the stock ladder. Cap is handling
    (`_MAX_SPLICE_PIECE_FT` in `takeoff/framing.py`), not stock — plies stagger 6+12+12+6.
    `structural.ridge_beam_depth` grades the depth.

### Windows and facade

- **Window RO ladder.** Three caps, arithmetic on the 16" module and 1.5" stud, enforced by
  `structural.window_framing_module` (`preferences.toml [framing]`):

  | RO | studs broken | clear-width math | head framing |
  |----|--------------|-------------------|--------------|
  | **14"** | 0 | one bay: `16 - 1.5 = 14.5"` clear | none — the bay's own two studs carry sill/head nailer |
  | **30"** | 1 | `32 - 1.5 = 30.5"` clear | R602.7.4 NONBEARING: single flat 2x4 header, no jack |
  | **27"** | 1 | 30.5" less a jack each side | R602.7.5 BEARING: header on a jack each end, packed against kings |

  - The 3" between the 30" and 27" caps IS the pair of jacks — the cap is purely a function
    of the wall's bearing status, same module/stud/broken line both ways. R602.7.5's
    approved-framing-anchor alternative would buy the 3" back but is declined deliberately
    (per-opening hardware/detail costs more than it saves); raise `max_window_ro_bearing_in`
    deliberately if ever needed.
  - **Modelling gap:** `needs_jamb_pack` keys off whether the RO breaks a stud, not
    `structural_role`, so it frames a full king/jack/header pack on nonbearing 30" windows
    too — the 30" cap is correct about what's buildable, conservative about what the model
    draws; widening the gap is not fixing it.
  - RO position is a property of the RO **width**, not the wall — resize windows to the grid,
    never move the grid to fit a window
    (`test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`).

- **Width/height families.** Five widths carry the house: WT-1424, WT-2736, WT-3036 (north
  gables/hall), WT-3048 (south glazing, head 6'-8"). The 27" family carries FOUR heights
  (36/48/54/64"); the 14" family THREE (24/36/48"). **WT-2764 and WT-1448 are
  CATALOG-ONLY** (superseded by WT-2754, WT-1436 under the 6:12 rake); WT-2464 is also
  catalog-only. Retired sizes stay priced (same convention as `glazed-green-brick`,
  `EXT_2X6_SWINBURNE`). The bearing cap bounds width, so when an opening needs more
  area/head-line/composition, **height** is the only dimension left to spend — hence the
  exceptions below, not drift from "one type per width family."
  - **Every window is on its ideal station; the exception list is empty**
    (`test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`).
    Keep it empty — see **ONE GRID PER FACADE** before concluding a window can't reach its
    station.
  - **Six height exceptions** (an extra height on an existing family, cheaper than a new one):
    - **WT-1448** (south flankers, catalog-only): 14" takes no header, so only the glass
      answers to the rake; any wider unit's header is what the rake won't take.
    - **WT-1436** (south flankers): third height on the 14" family — 5'-8" head fits the
      6:12 rake's clearance (`2 x (head+2")`) at 12'-8"/23'-4" with 4" to spare, where
      WT-1448's 6'-8" head does not fit anywhere a mirrored pair could use. Also keeps
      `RM-A-STUDY` on R303.1 daylight (165 sf needs 13.2 sf; gives 13.625) without
      Exception 1's electric-light substitute.
    - **WT-3048** (south glazing): the 30" family's committed 36" height would drop the
      south head off the house's 6'-8" door-head line.
    - **WT-2748** (`WIN-M-EAST-MID`): bearing cap forced 30"→27"; 48" is a pure retype
      (same 2'-8" sill, same 6'-8" head) — the cheapest of the six.
    - **WT-2754** (`WIN-S-BED1`/`BED2`): 27" cap, single-window bedrooms — 27x48 (9.00 sf)
      fails BED2's 9.945 sf R303.1 requirement; 27x54 (10.125 sf) passes. Code necessity.
    - **WT-2764→WT-2754** (`WIN-A-S-JUL-W`/`-E`, catalog-only, NONBEARING walls W-A-S2/S3):
      the only composition-choice exception and the only nonbearing one. Growing the pair
      closes the gap between the units to a 21" clear bearing pier (14" required) without
      moving either centre off its stud line.

- **Facade alignment — ONE GRID PER FACADE.** `EXT_2X6`/`PLANT_EXT_2X6_HUMID` set
  `layout_origin="line"`, so a wall segment lays out from its **layout line** (the derived
  chain of collinear, stacked walls, `resolve/layout_lines.py`), not its own start node.
  Every facade segment, every storey, sits on one 16" grid off the house origin: a stud line
  at `x ≡ 0 mod 16"`, a bay centre at `x ≡ 8" mod 16"`. A window's legal stations are a
  property of the facade, not any one node — moving a node no longer re-phases anything.
  `test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`
  asserts an EMPTY exception list. Keep it empty.
  - **The 8" rule is the only phase rule left.** A 14" RO sits on a bay centre, a 27"/30" RO
    on a stud line — 8" apart — so a 14" unit can never column with a 27"/30" unit anywhere
    in the house (e.g. `WIN-M-BATH2`); retyping the narrow unit is the only fix.
  - **A node move is cheap; a window move is global.** A node may move freely, but a window
    off the grid stays off it, and a facade whose windows disagree with the grid can't be
    blamed on authoring order.
  - **A tee is not a wall end.** Where two collinear segments provably share one grid,
    `framing/solver.py::continuation_roles` drops both segments' end studs so the module
    runs through, one `"owner"` claiming the seam. The **stand-off band**
    (`framing/furring.py`, where cladding lands) reads the same way — a HORIZONTAL band
    (the catlin truss girt courses) also continues through a seam via
    `_furring_module_signature`'s `direction`, or every tee would notch every course. The
    girts' **blocks**, one under every course on every OTHER stud, phase-lock to the layout
    line on a 32" grid instead. Pinned per facade by
    `test_catlin_contract_m3.py::test_each_facade_block_grid_is_one_grid_on_every_storey` and
    `::test_no_facade_stud_stands_off_the_module_except_at_a_corner`. Only corner packs and
    jamb packs (which sit where their ROs put them) are off this grid.
  - **Interior bearing walls opt in too**, STRUCTURE layer only (no liner-band phase-lock,
    unlike the exterior pair): `INT_2X6_BRG`/`PLANT_INT_2X6_BRG_HUMID` (the x=18'-0"
    **centreline**, `W-M-C1..C5B`/`W-S-C1..C4B`/`W-A-C1..C2`) and
    `STAIRWALL_INT_2X6_BRG`/`STAIRWALL_INT_2X6_BRG_TYPEX`/`MUDROOM_INT_2X6_EXPOSED` (the
    **stair line**, `W-B-STR/STR2/STR3` under `W-M-STRW/STRW2`). **No code compels this**
    (R602.3.3 is the bearing-stud rule; R602.3.2's single-top-plate exception is about
    rafters/joists centred over studs within 1"; in-line framing is an APA technique) — done
    because the centreline carries `RB-HOUSE` continuously to the footings. Pinned by
    `test_catlin_contract_m3.py::test_the_centreline_bearing_wall_is_one_stud_grid_on_every_storey`
    and `::test_upper_storey_studs_stand_over_studs` — 94 of 237 stacked upper-storey studs
    still stand over nothing (down from 113), a **ceiling, not a target** (correct framing
    never reaches zero). Caveat: a line's grid phase is set by `layout_lines._orient` off its
    own extreme member end, not the house origin — the centreline matches the house's 16"
    grid by luck (it ends at y=0); `LL-W-B-STR` starts at y=216" and sits 8" off.
    **Not opted in, deliberately:** `INT_2X4_PARTITION`/~46 other non-bearing partitions, and
    the *staggered* assemblies — never widen into the latter without reading `plans/TODO.md`
    first (`framing/solver.py`'s face-parity rounding at a 4"/12" phase would collapse runs
    onto one face and destroy the acoustic decoupling; it can't fire at the staggered walls'
    universal phase 0.0, and a non-zero phase is exactly what opting in would hand it).

- **Columns.** South face stacks columns at x 4'-0"/32'-0" (main+second); second adds
  9'-4"/26'-8" (none on main); both mirror about x=18'-0" (main: 4'-0"/14'-8"/21'-4"(door)/
  32'-0"; second: 4'-0"/9'-4"/14'-8"(door)/21'-4"(door)/26'-8"/32'-0" — every pair sums to
  36'-0"). Attic gables do not join these (see **Gables**).
  West face stacks FIVE (y 5'-4", 10'-8", 20'-0", 24'-8", 31'-4"): first three 27" family on
  a 3'-0" sill; fourth pairs tempered 14" awnings (`RM-M-BATH1`/`RM-S-VANITY`) on a 4'-0"
  sill; fifth pairs `WIN-M-MUD`/`WIN-S-BATH-W`; all share one 6'-0" head line.
  `WIN-M-BATH2` is WT-2736-T (retyped from WT-1424-T) at a 3'-0" sill to reach the third
  column (the 8" rule, also satisfying R303.3's window alternative). West attic pair:
  4'-8"/31'-4", symmetric about y=18'-0" (→ DESIGN-LOG.md for the chase/backing history).
  **The north face has no column, a deliberate trade** (→ DESIGN-LOG.md): the upper facade
  reads as one rectangle instead — `WIN-A-N1`/`WIN-S-STAIR-N` at **12'-0"**,
  `WIN-A-N2`/`WIN-S-HALL-N` at **24'-0"**, each attic unit over its second-storey partner,
  mirrored about the ridge. Since 2026-09-10 **all four are 27" wide** (attic WT-2736,
  second WT-2748), so the two stacks are columns of one width and one rough opening rather
  than four squarish 30x36s. `from_node` resolves to the near JAMB, so every one of those
  four offsets grew 1 1/2" to hold its centre — do the same on any future retype here. `WIN-M-KITCH` stands alone below, dead-centred on the sink run.
  `WIN-S-BED3-N` (WT-1424, x 34'-0", sill 4'-0") sits over `WIN-M-KITCH-N`, completing a
  **corner pair** with `WIN-S-BED3` (east wall y=34'-0", each 2'-0" off the corner) — a
  two-storey column — and satisfies R303.1 Exception 1 for `RM-S-BED3` (12.2 sf glazed/6.1
  sf openable against 10.32 required). The kitchen counter run (5/8" scribe + B15 + DW +
  SINK-36 + B30) has no slack; the window column follows the sink, never the reverse
  (`plan/placeables.py` kitchen header).

- **Rows.** Where a column is impossible, the storey's rhythm must be centred, not merely
  even. East second storey: 4'-0"/13'-4"/22'-8"/32'-0", mirrored about y=18'-0" in station,
  width (27/30/30/27), and head (6'-0"/7'-0"/7'-0"/6'-0") over one 3'-0" sill — a 9'-4" beat
  three times over (→ DESIGN-LOG.md).
  East main row: 4'-0"/13'-4"/18'-8"/34'-0" — the last gap deliberately ends a blank kitchen
  stretch. First three: 27" units on one 2'-8" sill, 6'-8" head. `WIN-M-KIT-E` is a 14" unit
  at a 3'-6" sill (bay centre, 408" off `N-M-SE`) — joins neither beat nor head line, closes
  the row's north end as a service window (can never column with the 27"/30" family beside
  it — the 8" rule). `WIN-S-STUDY3` at 4'-0" columns with `WIN-M-LIV-E1`. **Check
  `out/render/elev_east.png` before touching this row.**
  The fireplace pier sits between `WIN-M-LIV-E1`/`E2`: a 45 1/2" white-facebrick surround
  centred y=8'-8", walnut mantel at 5'-4". No window moved for it — the pier centre is a bay
  centre on `W-M-E1`'s grid, and the 2'-8" sill is also the firebox opening's bottom (one
  datum, four openings). `notes/east_breast_bearing.md` carries the bearing/floor opening —
  **`haus check` grades neither**.
  - The firebox is **five walls, not one**: `W-M-FIRE-STUB`/`-PLINTH`/`-JAMB-S`/`-JAMB-N`/
    `-HEAD`, all `FIREPLACE_BRICK_WYTHE`, NONBEARING, stacked on x=35'-1 11/16" with **its
    own `open_end` node pair each** (a shared node collapses every junction polygon it
    touches). Masonry opening **29 1/2" x 20 5/8"** (sill 32" AFF, head 52 5/8" AFF) is the
    gap between elements, not a subtraction from one; elevations off the +15/16" finished
    floor: STUB -13 7/16"→+15/16", PLINTH →32 15/16", jamb piers →53 9/16", HEAD →64 15/16".
    Zero cut closers on the visible 45 1/2" opening; head is a deliberate CUT COURSE at 19.7
    courses (a course line gives 21 1/3", ~1" of daylight) — steel angle lintel, not a
    rowlock. Brick quantity is 24.8→20.4 SF and the $/SF rate deliberately does not drop — a
    mason bills the panel on a job this small; re-rating down would deduct twice.
  - `FO-M-FIRE` is **47 3/4", not 4'-1"** (44 1/4" stub + 1/2" mason's clearance + one
    trimmer ply each side). Deliberately not 48.0" — `header_size` branches on `w_ft <= 4.0`
    and a span arriving as `4.0000000000000009` after a metre round trip would take the
    wrong branch silently. (`haus check` grades floor-opening headers at EIGHT feet, gated
    on a sawn-joist profile, so this I-joist opening draws the same header at any span.)
  - The mantel is `FURN-M-FIRE-MANTEL`/`FT-MANTEL-WALNUT-46`, a wall-mounted placeable
    (`FURN-B-PLAY-TV` idiom), 45 1/2"x11 1/2"x2 1/4", resolving 64"–66 1/4" AFF on
    `W-M-FIRE-HEAD`'s top (`depth` DELETED so `_carcass_depth_m` inherits from the type).
    **`Mount.elevation` is off `room_floor_elevation` — the SUBFLOOR datum, not finished
    floor** — hence the authored 64 15/16" for a 64" AFF shelf (64" would bury it 15/16" in
    the brick at 0 FAIL). `work_surface` is UNSET, not False, to stay out of NEC 210.52(A)'s
    wall-space rule. `[allowances] finish-fireplace-mantel-walnut` is **deleted** (not
    zeroed) and `[placeables] "FT-MANTEL-WALNUT-46"` carries the scope instead — an unpriced
    type is silently dropped from the bill.

- **Knee band — GONE.** East/west knee walls are 1 1/2" rafter plates now with no glazing,
  so `WIN-A-W-S`/`-N` and `WIN-A-E-S`/`-N` are deleted; those facades stop at the second
  storey (two storeys there, three on the gables, per
  `test_each_facade_block_grid_is_one_grid_on_every_storey`). The stair well's east edge
  lost its guard with the wall, so `RL-A-STAIR` gained a 3'-0" east leg (`code.R312_1_guard`).

- **Head lines.** West face: every main/second head on one 6'-0" line — 27" units at a
  3'-0" sill, 14" units at 4'-0". South face shares a 2'-8" sill. `WIN-S-BED3-N` is a
  WT-1424 at a 4'-0" sill (as is `WIN-S-BED3` around the corner), so it heads at 6'-0" —
  leaving the east face's 3'-0" datum (`WIN-S-BED1`/`WIN-S-BED2` still hold it) when it was
  retyped down to a 14" unit, the rule working, not an exception.
  **The north second storey is a ROW, not a head line**, and this entry claimed otherwise
  until 2026-09-10. `WIN-S-HALL-N`/`WIN-S-STAIR-N` are **WT-2748 at a 3'-4" sill**, heading
  at 7'-4" — the highest heads on the storey, 4" over the east row and 16" over
  `WIN-S-BED3-N`. (They were never on the 6'-0" line: commit `5487fd79` had put them at a
  3'-6" sill and a 6'-6" head with no note.) **A 48" unit cannot satisfy either half of the
  NEW-OPENING RULE on a 24" module** — the head half wants a 24" or 48" sill, the sill half
  wants 27 1/2" or 51 1/2", and they never meet, so every exact hit on offer drags a sliver
  with it for no net board saving. The rule's real intent is no redundant board, so this
  pair sits CLEAR of the courses instead, in the 2'-10 1/2"..3'-5" band; 3'-4" is its top
  even inch and it took `test_truss_girt_courses.py` from 33 slivers to 31.

- **Gables** read symmetric about the ridge before answering to anything below. The north
  gable is symmetric at **12'-0" / 24'-0"** (144"/288", both stud lines, mirrored about the
  18'-0" ridge — see **Columns** for why those stations also stack the second storey).
  **The rake is binding here and holds by 6 1/2"**: outer jambs land 130 1/2" from their
  eaves against the 124" a 5'-0" head needs; `structural.truss_wall_opening_support`
  confirms both jamb pairs bear on an outrigger within 1", and there is no third bay
  outboard — **this pair cannot move out again without a shorter unit.** The pair is
  **WT-2736** since 2026-09-10 (30x36 read too square), matching the second storey's new
  27" width so the stack is a column of one width, the attic unit simply 12" shorter under
  the rake. It could not grow taller with the pair below: a 48" unit here needs 148" of run,
  and buying the height off the sill instead lands under R312.2's 24".
  Recheck before any further move: the radon riser is 11 1/8" clear of `WIN-A-N1`'s west
  jamb (`mep_venting.py`), the PV junction box 6 1/2" clear of its framing bumper
  (`electrical.py`) — both widened by the narrowing, and a rewidening spends them back.
  `WIN-A-N1` (hosted on `W-A-N2B`) has RO 10'-10 1/2"..13'-1 1/2", clearing the x=10'-0"
  split by 10 1/2";
  at x=12'-0" it fronts `FO-A-HALL`, daylighting the stair void rather than a room — an
  amenity, not a code problem.
  **The south gable carries FOUR openings**, mirrored about x=18', reading west→east S2,
  JUL-W, JUL-E, S3. Tags gap at S1/S4 rather than renumber (would break the surviving units'
  GlobalIds):

  | station | tag | type | head | outer jamb | allowed | margin |
  |---|---|---|---|---|---|---|
  | 12'-8" / 23'-4" | `WIN-A-S2` / `WIN-A-S3` | **WT-1436** (14x36) | 5'-8" | 145" / 144" | 140" | ✓ 4" |
  | 16'-0" / 20'-0" | `WIN-A-S-JUL-W` / `-E` | **WT-2754** (27x54) | 7'-2" | 178 1/2" | 176" | ✓ 2 1/2" |

  One 2'-8" sill under all four, heads stepping with the rake. Juliets hold a 21" clear
  bearing pier under `RB-HOUSE`'s south bearing point (14" required).
  **The corner pair (`WIN-A-S1`/`S4` at 3'-4"/32'-8") is deleted, and its 8" column miss**
  (against the 4'-0"/32'-0" column below) **is permanent** — at 6:12 there's 21 1/2" of roof
  over the floor there, a 14" RO must sit on a bay centre, and every south column below is
  on a stud line. **Do not "fix" that 8" by moving these two** — it trades a clean framing
  module for a header the rake will not take.
  The mirror about x=18' is the rule that actually governs a gable, and the one thing that
  has survived every position tried here.

- WT-1424 is still used wherever a bigger unit won't fit — chiefly the mudroom. Under the
  south rake it handed off to WT-1448, then WT-1436 (→ DESIGN-LOG.md).

- **Tempered twins.** `WT-1424-T`, `WT-2736-T`, `WT-3036-T`, `WT-3048-T` match their parents
  in every dimension, differing only in glass, for the ten R308.4 units (wet room, within
  24" of a door, within 60" of a stair). Not width families — no facade/framing rule sees
  them; adding a tempered unit is a retype, never a move. All three glazed *door* types are
  tempered outright (R308.4.1 has no location test).

- The east bearing wall (`WIN-S-BED1`/`BED2`) takes the standard bearing cap — 27"
  (`WT-2754`/`WT-2754-T`), same rule as every other bearing wall. An earlier 30" exception
  here was tried and reversed (→ DESIGN-LOG.md). Lesson: when a width cap looks like it
  forces an R303.1 area failure, check height before moving the cap — area is width x
  height.

### Ventilation, ducts and soffits

- **ERV: Broan B210E75RT, semi-rigid radial** (`plan/mep_erv.py`).
  - **Three manifolds map to CAVITIES, not storeys.** Level 1 = basement ceiling, machine in
    RM-B-FURNACE. Level 2 = RM-M-MECH, feeding both main-storey CEILING grilles and
    second-storey FLOOR boots because both open into the one FS-S-WEST/EAST cavity. Level 3 =
    FS-ATTIC deck at the chase head. Moving a terminal between storeys is free; moving it
    between cavities is a new radial off a different manifold.
  - **Machine stays at (3'-11 1/2", 30'-6") — do not move it north.** `EQ-B-ESS-BATT`'s 36"
    REQUIRED clearance zone (x 49 1/4"..145 1/4", y 378"..460") is graded as a RECTANGLE by
    `advisory.ess_clearance`; this station leaves 1 1/2" clear and also clears
    `ED-B-BACKUP-ENCL`'s 36" NEC 110.26 working space. Nothing downstream is anchored to the
    machine, so moving it back would cost a FAIL for no savings.
  - **The radon/plumbing chase at (1', 34'-6") is the only riser and is full**: four 6"
    insulated ducts, six plumbing vents, `VR-M-RADON-VENT`, and eight conduits, ~25% fill of a
    30 1/8" x 32 3/8" shaft (`plan/mep_erv.py`). Nothing else goes in that chase.
  - **The two outdoor hoods are STACKED on the west face at the NW chase**: `EQ-M-ERV-HOOD-OA`
    intake (0'-0", 33'-11") +4'-0"; `EQ-S-ERV-HOOD-EA` discharge (0'-0", 34'-8") +17'-0",
    13'-0" apart, exhaust over intake, south of `TR-RF-LEADER-W` at y=35'-6".
    - Exhaust must stay the UPPER hood: `mep.erv_outdoor_terminals` measures 3-D distance and
      13' of rise alone clears its 10' rule (→ DESIGN-LOG.md, "Ventilation, ducts and
      soffits"). Neither hood may turn and travel inside the wall: an R-8 wrapped 6" duct is
      ~8" OD against a 5 1/2" stud cavity, so each must be a straight through-wall
      penetration. `test_catlin_erv.py` pins this stack order.
- **A duct or machine inside a `Soffit` NAMES IT via `soffit_ref`, and the clear section is
  DERIVED — never author a clear width.** `mep.duct_soffit_occupancy` derives the cavity from
  the soffit's own drop, `FramingSpec` member, 5/8" lining, and a 2" hanger gap; an authored
  width is a second source of truth that drifts the first time framing changes. Current
  derived boxes: `SF-S-DUCT` 30 3/4" x 11 1/4"; `SF-S-SUITE` 31 3/4" x 11 1/4"; `SF-S-HP1`
  40 3/4" x 7'-9 3/8" (in `RM-S-NCLOSET`'s ceiling), drop 21", underside at 7'-3".
  - **A box's LONG plan dimension is its axis; every occupant is measured ACROSS the other
    one.** Near-square soffits (e.g. `SF-S-HP1`) need this ordering chosen deliberately, or
    the check grades the trunk's travel as "width" and never compares lane to machine.
  - **A hatch through a soffit must be AUTHORED as `Soffit.openings` (`SoffitOpening`,
    `model/floors.py`)**, or `resolve/framing/soffit.py` never cuts the rungs it crosses —
    an unauthored `Furniture` access panel is invisible to `structural.member_interference`
    (placeables vs. members is untested), and the model asserts an unopenable panel at 0 FAIL.
    - A cut rung becomes **stubs** carrying the header, keyed `-004a`/`-004b`; an edge landing
      on a rail takes no header. `structural.soffit_opening` grades the header on deflection,
      oracled by `notes/soffit_rung_deflection.md`. Not a duct penetration — a duct leaves
      through a soffit's END (`along` clip); a hatch through a ladder rail is a different
      check.
  - **`CHASE` routing (a framed shaft not modeled as a `Soffit`) is a declared unchecked
    case** — do not rely on it for clearance.
  - **`EQ-T-GREE-FLEXX-ULTRA-24-AH`/`-OD` is the live heat-pump type for
    `EQ-S-HP1-AH`/`EQ-M-HP1-OD`.** 760 cfm at 1.0" w.c., 21,000 Btu/h read at -15 F (**# TODO verify datasheet** — the
    figure carries an AHRI certificate number but no table or column reference, and the two
    types this replaced were both retyped over numbers read from the wrong column; see
    DESIGN-LOG.md and `plans/buildability.md` BLD-08) (137% of
    the zone's 15,164 Btu/h block load, unaided), 24 VAC control with a factory heat kit,
    HSPF2 10.0, ENERGY STAR Cold Climate (AHRI 215213329). Depth is 18 1/8" (→ DESIGN-LOG.md,
    "Ventilation, ducts and soffits" for the two retypes this replaced).
  - **A `# TODO verify datasheet` marker on any equipment type is not documentation debt —
    every clearance, lane, and velocity downstream of it is provisional** until the type is
    replaced with a verified one; re-check all of them when it is.
  - **`SF-S-HP1`'s box is 40 3/4" x 7'-9 3/8", flush on all four finished faces**, in
    `RM-S-NCLOSET`'s ceiling; the air handler is `rotation=deg(90)` so only its 21 1/4" case
    depth competes for the graded width. Consequences that must stay true:
    - **`W-S-BW4` must stay retyped `INT_2X4_RC`.** A plain partition jogs 1/2" at
      y=30'-10" and `_rectangle` returns `None` on a non-rectangle, sending every occupant to
      UNKNOWN.
    - **`DU-S-ERV-HP-FEED` must name NO soffit.** It shares the box's y-band with the attic
      chase legs twenty feet west; naming the soffit would grade those as occupants of a
      cavity they never enter — a false FAIL.
    - **`EQ-S-ERV-MIX` is a full return plenum** (12" x 29 1/2" x 18", x
      20'-5 1/2"..21'-5 1/2", y 27'-10 1/2"..30'-4") — `REG-S-HP-RET`'s whole 336 in² face
      must sit inside it, or part of the return face draws from the bare soffit cavity
      (IMC 601.5's building-cavity-as-plenum, which no check here catches — see
      DESIGN-LOG.md).
    - **A wall grille on `W-S-C4B` is NOT buildable — do not re-propose it.** It is the
      x=18' bearing line (`RB-HOUSE`'s load path); the one bay overlapping the plenum band
      leaves 7 1/4" clear, and cutting the stud puts the plate at f≈1,940 psi against
      Fb≈1,310. `RM-S-NCLOSET` and ~7'-9" of north hall are at 7'-3" clear in trade;
      `RM-S-HALL`'s graded `clear_height` is unchanged at 8'-11 1/2".
    - **`Mount.elevation` on a `Register` is a number NO CHECK READS** (a Register resolves
      no solid) — author every ceiling terminal off its own room's ceiling, never a borrowed
      comment.
    - `REG-S-HP-STAIR` is a SIDEWALL grille (`REG-T-HP-SUP-SIDE`) in `SF-S-DUCT`'s west
      lining at 97 1/8" — do not revert it to a ceiling grille above the room's own return.
      `REG-A-HP-STUDY` floor boot sits at (25'-0", 3'-4") — every station on that bay line
      from x 21'-0" to 27'-3" is under furniture, so this is the best fit, not a clean one.
      **Nothing grades a placeable against a register** — check by hand when moving one.
      `DU-S-HP-SOUTH`'s west terminal is at x=9'-4" (centroid of all three south windows, not
      the middle two).
    - **The riser cannot cut through `FS-ATTIC`'s joists** (they run in x); near x=19'-6"
      every hole lands inside `W-S-C1`'s no-hole zone, and no duct small enough to dodge it
      still moves 250 cfm.
    - **The return path is door undercuts, and `Opening` cannot hold one** — there is no
      undercut column in the A-601 schedule, so an unspecified door defaults to 3/4". Required:
      `D-S-BED1/2/3` 1 1/2", `D-S-SUITE`/`D-A-STUDY` 1 3/4", `D-A-HALVES` 1 1/4"; `D-S-PLANT`
      deliberately none (interlocked damper). Full arithmetic: `notes/system1_return_path.md`.
    - **`AO-S-HP1-AP` (30" x 29" clear) must stay gasketed.** Leaving the soffit's bottom
      open in the closet makes the closet itself the return plenum, which IMC 601.5(7)
      forbids.
    - Where the box passes under `ST-S2A`'s flight, `ledger-W-S-SS2-stringer-1` (the 2x10 on
      `W-S-SS2` at y 104 1/8"..105 5/8") may NOT be lapped — `structural.member_interference`
      excuses treads/stringers over a soffit but not that ledger.
- **`W-M-HS4` is a pocket wall and nothing may ever go in it again** — no outlet, switch,
  pipe, register, blocking, or towel bar between 12'-4" and 16'-5" on y=22'-4" (no stud to
  fasten to, no depth to recess into). `D-M-LAUN`'s 4'-0" pocket leaf parks there, crossing
  node `N-M-E3`. Enforced by `mep.pocket_occupancy`.
  - **A split stud that ever reaches the top plate destroys the `W-M-LS` plate tie** — a
    pocket occupies floor to 6'-8" only, so the tie's plates run continuous over/under it and
    only its vertical edge floats.
  - 4'-0" is the widest leaf that fits: the closing pack must clear `N-M-C2`, where bearing
    `W-M-C3` corners in and `BM-M-HALL` starts. Full detail, including the 1" fastener limit:
    `notes/pocket_door_at_laundry.md`.

### Basement

- **Slabs.** Basement slab: 2" XPS at **>=25 psi** (R-11.1 whole-assembly against an owner
  target of R-10; PASSes `code.energy_prescriptive`'s R-10 slab row). Detached garage slab:
  1" at **40 psi** — a loaded wheel is a contact patch, not a distributed floor load.
  `RM-GARAGE` is `conditioned=False`, so nothing grades the garage number.
  - Do not assume a psi change is priced: `library/materials.py`'s `xps` tag has no
    compressive field and `prices.toml` keys XPS on **thickness only**, so 25 psi and 40 psi
    board bill identically here though 40 psi runs ~20-35% over in the yard. XPS price rows
    ARE qualified by `thickness_in` (`cli/prices.py`'s `envelope_layers`), or any
    foam-thickness change would price at $0. `test_catlin_reference_parity.py` carries no
    `DECLARED_DIVERGENCES` entry for the basement slab; catlin matches the reference detail.

- **Foundation wall assemblies** compose `library/FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a
  house-local skin — the core must not drift between the variants.
  - Skin: `BASEMENT_12`/`_8` cover the XPS with a 1/8" `foundation-coating-acrylic` (troweled
    over mesh) banded from 6" below grade to the wall top, `Layer.extent` off the `GRADE`
    datum so a grade lift grows it with no edit. Do not revert to the old
    `foundation-protection-panel` alternate (kept, priced, as a named alternate only) — its
    joint permeance is unpublished and makes `building_science.condensation` report UNKNOWN,
    where the coating PASSes (→ DESIGN-LOG.md, "Basement").
  - `W-B-S1`/`W-B-S4` use `BASEMENT_8` (no stucco) for ~37 SF of coating. Court segments
    carry **no skin at all** (XPS sits inside `W-B-BRICK`'s ventilated cavity).
    `BASEMENT_8_GARDEN`/`_GARDEN_PARGE` remain defined but unreferenced in
    `plan/assemblies.py` as the documented revert path.
  - Pour thickness: only `W-B-E1`/`E2` are `BASEMENT_12` — they bear `SL-M-DECK`, the one
    remaining cast deck. The other nine segments are 8" with `#5 @ 41" o.c.` vertical steel
    per IRC Table R404.1.2(8). `W-B-STR`/`W-B-STR3` and `W-B-CS` are 2x6 bearing **stud**
    walls, not concrete — `unbalanced_fill` is `ft(0)` on all of them; `W-B-CS2`/`W-B-CN`/
    `W-B-CN2` are the only interior pours left. Do not retype any of the nine to 12" without
    cause — `structural.foundation_unbalanced_fill` FAILs correctly otherwise.
  - Cladding: `N-B-BRICK-W`/`-E` stand off `inch(-4.05)` on bare XPS; veneer clear cavity is
    **1-1/2"** (IRC R703.8.4 min 1"). Never re-strike this node off a parge finish face — it
    must sit on the foam itself (→ DESIGN-LOG.md, "Basement"). Walls align on
    `face("concrete-ext")`: the furnace room and workshop have 4" more clear on the inside
    face than the model reports — `clear_face` is inset from the wall axis and did not move
    with the thinner wall; read the layer polygons instead (`notes/basement_to_framed_wall_detail.md`).

- **Sauna (`RM-B-SAUNA`).** Against the south (garden) wall, long axis east-west; west wall
  at x=8'-10" on `N-B-S1`; south face is one plane on `W-B-S2`'s garden curb, no jog. Clear
  box **8'-3 15/16" x 8'-10 11/16"**, 555 cf against `EQ-T-SAUNA-HEATER`'s 600 cf rating
  (45 cf margin — a deeper room needs a bigger heater and circuit). Entered from the gym
  through framed `W-B-CS`; keeps `WIN-B-SAUNA`.
  - Its north wall (`W-B-SA-N`, split at `N-B-HALL-S`; `W-B-SA-N2` is the east segment) lands
    on `W-B-CS3`'s 4'-5" framed run beside `D-B-GYM`'s rough opening (starts y=10'-11 7/16").
    Do not move `D-B-GYM` south or this wall north of 10'-0" — past 10'-6" the wall and the
    opening overlap outright and no `haus check` rule tests a tee wall beside an opening.
  - Heater `EQ-T-SAUNA-HEATER` (9 kW) is on the **east liner**: `rotation=deg(270)`, 18" face
    to wall, 16" deep, 2" off both liners.
  - Benches: `FURN-SAUNA-BENCH-2T-60` (two-tier), `FURN-B-SAUNA-BENCH-E`, and the south-liner
    bench `FURN-SAUNA-BENCH-48` (**4'-0", do not grow it**) — `ED-B-SAUNA-JB`'s box base sits
    at 18" AFF, the bench-top height, so a longer carcass would reach under a live 9 kW
    junction box. Do not push the heater north to `D-B-SAUNA`'s jamb either —
    `EquipmentType` carries no clearances field and nothing would stop a 30" hot stove at the
    doorway. `FURN-SAUNA-BENCH-48` must stay priced in `prices.toml` — an unpriced type
    silently drops from the takeoff. `REG-B-SUP3`, `DU-B-ERV-R-SAUNA-SUP`'s east leg and
    `ED-B-SAUNA-JB` all sit with the heater on the east liner. Lighting `ED-T-LT-SAUNA-VT`
    (125°C sauna-listed) keeps its switch **outside** the hot room.

- **Bathroom.** Rotated north-south along the framed stair wall (`W-B-STR3B`/`W-B-STR2`);
  clear **3'-3 15/16" x 7'-1 1/4"**. Wet wall is `W-B-BA-E`, an `INT_2X6_STAGGERED_PLUMBING`
  partition at `inch(166.6875)` on the stair well's centreline, carrying the shared vent
  riser at (13'-10 11/16", 19'-3"); `W-B-BA-N` is a dry `INT_2X4_PARTITION`. `D-B-BATH`
  swings out into the hall with `flip_swing=True` on this wall. No `haus check` rule grades
  a wall device's depth — `test_wall_mounted_devices_resolve_against_a_wall_face` is the only
  guard, so verify `ED-B-BATH-SW` sits flush with the studs by eye.

- **Hall and circulation.** The hall runs from the stair foot south, west of `W-B-CN2`, the
  full way to the sauna's north wall, on the x=13'-10 11/16" well-partition centreline shared
  with `W-B-BA-E`/`W-B-WELL`; part of `RM-B-STAIR`'s loop (114.8 -> 147.7 sf, one seed, no
  separate `Room`). Circulation is stair -> hall -> gym (`D-B-GYM`) -> `D-B-PLAY`, and
  stair -> hall -> `D-B-SHOP` -> workshop -> `D-B-FURN`. There are now **no doors through a
  concrete pour** — `prices.toml`'s `concrete-window-bucks-and-blockouts` row drives to zero
  and is kept there under the `glazed-green-brick` convention.
  - `D-B-GYM` is on the hall (not the workshop): same uid/position, 32" leaf, type
    `DT-INT-SWING32-GLAZED` (glazed because the hall has no window of its own and borrows the
    gym's south daylight). Keep it at **32"** — `W-B-CS3` offers 42 3/16" of framed run and a
    36" RO would leave only 3/16" for two jamb packs.
  - The workshop is a room (not a corridor) with `D-B-SHOP` (3'-0", in `W-B-HALL-W`,
    `flip_swing=True`, hinged north, leaf swings west), RO centred on `D-B-GYM`'s at
    y=12'-3 7/16". `D-B-FURN` (3'-0", widened) is pinned west by `PR-B-ERV-COND`. `W-B-CW2B`
    and its cased opening `O-B-HALL` no longer exist.
  - `W-M-CLN2` (upper storey) stacks on nothing: `W-B-CW2` below it overlaps by only
    6 11/16", short of the 2'-0" stacking minimum, so `integrity.stack_ambiguous` does not
    arm. The load routes into the deck instead via two `JoistReinforcement` blocking entries
    in `params/main_deck.py` at x=14'-6"/16'-9", `at` y=**217"** (not 216" — equidistant
    between the 208"/224" joist lines). These two entries must stay **LAST** in
    `_WEST_FLOOR_REINFORCEMENT`.
  - `RM-B-STAIR` (not a `EXPOSED_SERVICE_OCCUPANCIES` room, unlike the workshop) now covers
    the hall's ceiling, so `mep.run_in_finished_volume` (3" tolerance) grades pipes there.
    `DU-B-ERV-R-GYM` and `PR-B-SAUNA-VENT` cannot be rerouted around it — any route between
    the sauna and the ERV crosses this space — so they are boxed out by bulkhead
    **`SF-B-HALL`** (full-width, x 170.0725"..212.615", y 123.8125"..133.4375", 7'-1 15/16"
    clear). Do not remove it without re-solving both runs. `PR-B-HW-SAUNA` and
    `PR-B-CW-SAUNA` run side by side, not stacked, at x=17'-4"/17'-3" — do not restack them;
    two 1/2" lines need 5/8" separation in a band only 3" deep.
  - Lighting/outlets: three `ED-T-LT-CAN3` on `CKT-LT-BACKUP` at x=190",
    y=19'-6"/15'-0"/11'-6" (27 VA; `cycle_48h.sustains_always_on` holds,
    `test_backup_calc.py`). Keep the middle one at **15'-0"**, not 15'-6" — `PR-B-HW-SAUNA`
    crosses 2 9/16" below the ceiling there. `ED-B-WORKSHOP-SW` sits 5" north of
    `D-B-SHOP`'s hinge jamb — the only side with room for the box. `ED-B-HALL-RC1` is on
    `CKT-RC-BSMT` at y=16' (NEC 210.52(H)); note `electrical.receptacle_spacing` only walks
    {BEDROOM, LIVING, KITCHEN, DINING, OFFICE}, so nothing enforces it if it moves.
    `ED-B-GYM-RC1`/`RC2`/`RC8` are on the gym face of `W-B-CS`/`W-B-CS3` — verify a device's
    side by eye: `electrical.receptacle_spacing` accepts one within 0.5 m of a room's clear
    face regardless of which side it's drawn on. `EQ-B-HP2-GYM` mounts at **6'-6" AFF** on
    `W-B-S3-FR` (not 7'-6" — its cabinet would top out above `code.R305_ceiling_height`'s
    95 3/8").

- **Under-stair space.** No `RM-B-UNDERSTAIR` room exists; the storage under the arriving
  stair flight (and on under the landing deck) is part of `RM-B-STAIR`'s single polygon.
  `D-B-CLOSET` opens it to the furnace room; `ED-B-CLOSET-LT` (`room=RM-B-STAIR`) lights it.
  `LR-B-STAIR-RAIL` lies under the flight rather than along it — one `Mount` elevation for
  the whole `LightRun`, measured off the slab, so it cannot rake.
  - `W-B-WELL` gives the well partition its faces only — `resolve/stairs/u_split.py`
    generates the 2x4 plates and studs between the two flights. Never add a `FramingSpec` to
    `STAIRWELL_PARTITION_4H`'s structure layer or `structural.member_interference` FAILs
    (it did, twelve times). Its thickness must stay locked to
    `resolve/stairs/common._WELL_PARTITION_THICKNESS_M` (4 1/2"). Its north end is open
    (`open_end=True` on `N-B-CL-NE`) — the only honest way to model a partition dying
    mid-well; `integrity.wall_loop_open` reads it.
  - `W-B-STR3` is `STAIRWALL_INT_2X6_BRG_UNDERSTAIR` (5/8" Type X in place of 3/4" stair
    plywood, per R302.7) — costs the exposed-plywood stair face on this segment. **Do not
    retype it back**: `code.R302_7_under_stair_protection` now passes on "no enclosed usable
    space" (`STAIR` is not in `_UNDER_STAIR_OCCUPANCIES`), but the Type X's reason didn't go
    away with the room label. `FO-M-STAIR`'s west edge is at `ft(10, 3.25)`.
  - Do not author `Room.ceiling` or a `Soffit` under the arriving flight — the real head
    rakes 96.7" -> 54.8" and no field represents that; `_clear_head` reads only decks/soffits
    (a stringer is neither), so `clear_height_m` resolves to the main-floor deck and passes
    R305.1.1 honestly. An authored ~53" ceiling would be taken verbatim and FAIL.
  - `DT-INT-CLOSET24` is **2'-0" x 6'-0"**: at y=28'-4" there is 76.5" of head, a 6'-8" leaf
    plus header wants 82", a 6'-0" leaf wants 74".
  - `D-B-FURN` is at `ft(3, 3)`, pinned by the condensate line — `CD-B-SPA`,
    `CD-B-DATA-SHOP` and `PR-B-ERV-COND` all pass nearby and none can move (a `ConduitRun`
    has one flat elevation). Moving this door east re-opens the clash (king stud is 0.475"
    off the pipe).

- **Engine behaviour to rely on.** `illumination._gypsum_finishes` matches `gwb*`/`gwb`/
  `gwb-x` (every gypsum layer in this catalog), not the literal string `"gyp"`.
  `topology._through_pair` prefers a continuous bearing pair at a four-way node, tag order as
  tie-break. `test_upper_storey_studs_stand_over_studs` sits at 112/247; `W-M-C1`'s studs are
  invisible to it because `W-B-CS3` shares the x=18' layout line but `stacks_on` names a
  different basement segment. S-100's ARCH D scale is **3/16"**, with only **0.18"** of
  vertical margin left in the FOUNDATION WALL SCHEDULE column (already carrying all three
  schedules, no width for a fourth) — the next new `FoundationWall` assembly tag anywhere in
  this house steps it down to 1/8" again.

### Decks and the garage

- **Every exterior deck's plank is the floor system's own sheet, no exception.**
  `FS-SG-PORCH` (composite, 3bf2f48) and `FS-SG-DECK` (aluminium) carry their boards as
  `subfloor=DeckLayer(...)`; the old `SL-SG-PORCH`/`SL-SG-DECK` slabs beside the framing are
  gone, and both planks bill by the square foot in `[sheet_goods]`, not by the cubic yard out
  of `[concrete]`.
  - **`FloorSystem.subfloor_outline`** is an authored sheet polygon that can replace a floor
    system's derived joist-field corners (for a plank that oversails its rim). Bound it
    against `[framing] bearing_plan_tolerance_in` (8") with `structural.subfloor_oversail` —
    past that the uplift pass FAILs members under the deck, reported nowhere near it.
    `sheet_goods_takeoff` reads `deck_outline` for sheet area; `ceiling_below` keeps the
    framed extent. (→ DESIGN-LOG.md, "Decks and the garage")
- **`PT-BW-1..4`, `SL-BW-DECK`, `GL-BW-ROOF`, the polycarbonate canopy glazing, `RL-BW-WEST`
  and `_EW_FT`/`_GLAZING_CENTER_X` no longer exist.** `BM-BW-RW`/`-RE` DO — the tags are
  deliberately reused for the canopy's two roof headers, on the same bearing lines. The
  landing is `FS-BW-FLOOR`/`FS-BW-GARAGE` on six piers. **`PT-BW-T1W..T4E` and their
  footings are gone too** (2026-09-10): eight 42" piers laid out running EAST from the stair
  foot while the flight runs WEST, so every one stood under open ground. The tiers are
  `carriage="cast"` — four `Slab` pours, `SL-BW-TIER1..4`, wedding-caked on a compacted base
  — so **no member of `ST-BW-ENTRY` is a stringer or a rim**; only its treads resolve, and
  they exist because every code rule grading a flight measures them, not because anything
  bills them. See `notes/north_entry_structure.md`.
- **The garage wall was rebuilt; both the garage wall and its roof are current.**
  `GARAGE_WALL_2X6` is **2x6 @24" o.c. / 2" ccSPF in the bays / 5/8" CDX / 7/8" corrugated
  exposed-fastener panel**, trusses at 24" o.c. to match (`GARAGE_ROOF`, framing factor
  0.0625 = 1.5/24 — the two must move together or the R-38 blow is under-credited).
  `RM-GARAGE` is `conditioned=False`, exempt from `code.energy_prescriptive`,
  `building_science.condensation`, and the MN prescriptive table.
  - Whole-wall value is **R-13.2** with `CavityFill` present — a bare SPF-over-cavity read
    of R-14.3 is a modelling bug, not the real wall. (→ DESIGN-LOG.md, "Decks and the garage")
  - **No WRB by design** (IRC R703.2 exception, unconditioned detached accessory). ccSPF is
    the air/water/vapour plane; `TR-CATLIN-GARAGE-OPENING` names `stud-cavity` for all four
    controls, not the house's `sheathing-ext`/`spray-foam-ext`, so bucks go in before foam.
    CDX carries no `control` set — bare sheathing claiming those layers would be a WRB
    nobody is buying.
  - **No furring; the 7/8" corrugation is the rainscreen itself**, drained by ~192 LF of
    closures (`[allowances] envelope-garage-corrugated-closure-strips`), vented at the base,
    solid at the head, priced there and not through `bug_screen:GARAGE_WALL_2X6` (reads 0 SF
    for a corrugated wall). Do not author a 7/8" airgap layer to "activate" that row — it
    would add 7/8" on top of the existing cladding and move both wall faces.
  - `GARAGE_GAP_FT` is **4.71875** (was 4.6875) — do not recess the sheathing to hold the
    cladding face still, since the wall's `alignment` always puts whichever sheathing it
    carries on the node line.
  - **No 16" stud zone at the overhead door.** `W-G-E` is NONBEARING; the 16'-0" opening is
    carried by its own 2-ply 14" LVL on solver-sized jamb packs — `FramingSpec.spacing` lives
    on the assembly, so a closer-spaced zone would need a whole second assembly.
  - Openings re-stationed onto the 24" grid: `WIN-G-N1` 1'-5" -> 2'-5", `WIN-G-S1`
    21'-5" -> 20'-5", `SERVICE_DOOR_OFFSET` 5'-10" -> 6'-6" (leaf centre x=8'-0"). `D-G-OVERHEAD`
    stays at 4'-0" — every legal station makes the two brick piers 5'-0" and 3'-0", so its
    `structural.door_framing_module` suppression stays in `preferences.toml`.
  - The 16 garage-wall `S-5-N` seam clamps are gone — a corrugated panel has no nail-strip
    seam; corner uplift is the panel's own 640 face screws. The garage ROOF keeps its 12
    `S-5-N` clamps (still nail strip). `GARAGE_WALL_WIND_CLAMPS` survives as an empty list,
    and `standing-seam-nailstrip-26`/`zip-r` keep $0 price rows (the `glazed-green-brick`
    convention).
- **The overhead door faces north; the garage sits at x 6'-0"..30'-0" (centre x=18'-0"),
  2026-09-07.** `GARAGE_X_WEST`/`GARAGE_X_EAST` are published beside the two y lines; stem,
  slab, and landing derive from them. Footprint did not rotate — windows stay on `W-G-W`,
  `D-G-SERVICE` on `W-G-S`. (→ DESIGN-LOG.md, "Decks and the garage")
  - `D-G-SERVICE`'s centre moved to **x=10'-0"**. `D-M-ENTRY` could not follow — its east
    jamb is fixed 6" west of `N-M-N2` at x=10'-0", the bearing tee to the footings — so the
    two doors are 2'-0" out of line. `code.R311_3_exterior_landing` passes both (entry 90.9%,
    service 91.7%, bar 85%). **Do not answer this by moving the garage back.**
  - `EQ-M-HP3-OD` sits at x 12'-4"..15'-2 3/8", `SL-M-HP3PAD` at x 12'-1"..15'-5", clearing
    12 11/16" to the nearest glass (Gree's 12" lesser-side minimum); the front walk's west
    edge is x=15'-9". Nothing grades an Equipment against a deck or clearance envelope, so
    check any future move by hand. **HP3's y-axis clearances are short and it's a deferred
    owner decision** — Gree wants 12"/6'-6", this position has only 8"/25 11/16", and the
    48 1/2" slot can never give more. `params/hp3_pad.py::_BACK_CLEAR_IN` is the only record;
    no check flags it. (→ DESIGN-LOG.md, "Decks and the garage")
  - `EQ-M-HP1-OD` moved 6'-6" east; it oversails the house's NE corner by 3" to keep its 14"
    clearance to the garage's east gutter. Its disconnect `ED-M-HP1-DISC` is a 6 1/2" can in
    a 14" slot, **NEC 110.26 working space ungraded**. Neither can move further on this face.
  - Aligning `ST-G-SERVICE` under its own landing fixed a standing `code.R312_1_guard_height`
    FAIL on `SL-G-STEP-0`. `ED-G-SW`/`ED-G-EXT-SW` sit inside `D-G-SERVICE`'s rough opening —
    a pre-existing, ungraded defect; fix target ~x=12'-0"/12'-6", east of the real jamb.
  - `notes/garage_orientation_lot.md` is the revert recipe; a south-lot revert must also flip
    `SetbackSpec` edges 0 and 2 (deliberately untouched here).
- **The garage has no wainscot; its base skin is a uniform 24" band on the ICF stem, all
  four walls (2026-09-03 deletion).** `GARAGE_BRICK_WAINSCOT`, `GARAGE_ICF_6_BRICKLEDGE`,
  `off-white-brick`, and both `_BRICKLEDGE` dicts in `params/foundations.py` are deleted
  outright (not kept unreferenced) — revert via git history, not a one-line `assembly=` swap.
  - `GARAGE_ICF_6`'s `coil-gap`+`coil-ext` band always ran behind the former wainscot, so the
    deletion cost nothing structural: **156.2 SF unchanged**. (→ DESIGN-LOG.md, "Decks and
    the garage")
  - Stock sheet stays **48"x120" at 0.040-0.050" gauge** — a 48" sheet rips into two 24"
    bands with no waste, so the heavier sheet costs nothing extra per SF over 24" trim coil.
    Second best on supply failure: 0.024" heavy-gauge 24" trim coil. **Never 0.019"** — takes
    a permanent shovel dent. (→ DESIGN-LOG.md, "Decks and the garage")
  - `STEM_TOP_Z_FLASHING` (`plan/storeys/garage.py`) is six `DRIP_FLASHING` runs, 76.5 LF,
    broken at both stem gaps. One counter-clockwise loop, every run `back_side="left"` so
    each wall's inboard normal puts the turn-down outboard on all six. **Nothing grades
    `back_side`** — get one wall wrong and the drip points at the wall at 0 FAIL.
    `test_garage_base_skin_is_the_stem_band_alone_and_its_top_is_flashed` pins it; confirm in
    the viewer too.
  - **Aluminium over aluminium; no check grades it.** `corrugated-panel-26` above the band is
    26 ga PVDF-coated steel; the band and the Z are aluminium — never lap metal-to-metal
    (sealant/EPDM between) or let aluminium touch concrete/mortar. `aluminum-flat-pvdf` on
    the Z, not `metal-dark-exterior`, is the whole enforcement.
  - `OVERHEAD_DOOR_OFFSET`'s 4'-0" has lost its defence (the asymmetric-pier argument died
    with the wainscot) and is now an open question — moving it drags stem/grade-beam gap,
    footings, Z break stations, and a water-service sleeve. Left suppressed while undecided;
    **do not quietly re-decide it either way**. (→ DESIGN-LOG.md, "Decks and the garage")
  - `W-GF-S3` / `W-GF-N2` are a kept fossil (plain `GARAGE_ICF_6`, nothing stands on them) —
    the wall/room census tests pin the count so a cleanup can't un-split them by accident.
- **The garage is white again** (all four walls `GARAGE_WALL_2X6`, `corrugated-panel-26`).
  `standing-seam-nailstrip-26-green` stays in the catalog, referenced by nothing — going
  green again is a one-line `layer_materials=` change. (→ DESIGN-LOG.md, "Decks and the
  garage")
  - **`Wall.layer_materials`** (`model/refs.py::LayerMaterial`) swaps ONE named layer's
    material on ONE wall, appearance only — thickness/function/framing/banding stay the
    assembly's. A typo in either half is otherwise silent; `integrity.wall_layer_material`
    FAILs on an unknown layer name or material tag.
  - Both renderers key metal-skin colour off the material's declared **`finish`**
    (`FINISH_BASE` in `ui/src/nordic/palette.ts`, `_FINISH_BASE` in `emit/gltf/palette.py`,
    kept in step BY HAND) — a bare `color=` attribute is the drawing-hatch tone, not the
    paint, and is invisible to either renderer.
  - The gable triangle above a wall comes for free: `resolve/roof_edge.py` builds the
    wall→roof closure from the host wall's own layers.
- **The garage roof edge — fascia and ridge cap — is `metal-dark-exterior` (`#1c1f24`), the
  house's exterior dark, across seven members: six fascia pieces plus the vented ridge cap.
  The two are named through DIFFERENT fields, kept in step only by this line and one
  assertion (`test_model_json.py`).**
  - Fascia (6 pieces: 2 eaves + 4 rakes) is named on `FasciaBoard` inside `_GARAGE_EAVE_TRIM`
    (`plan/storeys/garage.py`). Ridge cap is `Roof.edge_trim_material` on `RF-GARAGE`, which
    also drives corner trim (`resolve/roof_trim.py::_edge_trim_material`) — this roof's 16"
    overhang frames fascia+soffit and no corner trim, the only reason naming it recolours
    exactly one member. A zero-overhang roof would spread the colour to corner trim too.
  - **Changing the accent colour is a two-place edit** — miss one and the cap and fascia
    drift apart, reading as a mistake.
  - Fascia substrate is formed metal over a wood nailer, not 5/4 cellular PVC — dark colour on
    PVC forces a solar-reflective coating that caps the LRV below `#1c1f24`. **The soffit
    stays cellular PVC and stays white** so the overhang doesn't read as a shadow.
  - Tag-keyed in both renderer palettes (`_FINISH_BASE` / `FINISH_BASE`, kept in step by
    hand), not by declared `finish` — a fascia/ridge cap is a framed MEMBER and `memberColor`
    has no catalog access. Neither tag contains "seam" and trim carries no `skin_family`.
- **The garage ICF stem is covered on both faces above grade.**
  - Inside: 5/8" gypsum banded from `GRADE` up (`code.R316_4`), continuing the board
    `GARAGE_WALL_2X6` already lines with.
  - Outside: `coil-gap`+`coil-ext`, PVDF-painted aluminium (`aluminum-flat-pvdf`) from 2"
    below grade to stem top on a **1/4" vented standoff**, 316 stainless gasketed screws into
    the ICF webs. 156.2 SF, $781-1,562, the garage's entire base skin, flashed at the top by
    `STEM_TOP_Z_FLASHING`.
  - **The standoff is not optional and is not about drainage.** A painted sheet laid flat is
    0 perms — a Class I retarder on the cold side of the stem — and produces a real
    `building_science.condensation` FAIL. The 1/4" gap restores outward drying; delete it and
    the FAIL returns. (→ DESIGN-LOG.md, "Decks and the garage")
  - Both bands are banded, not full height; the band pushes the stem's exterior face 0.30"
    east (inside `_axis_match`'s 1/2" tolerance). **Do not recess the EPS to hold the face
    still** — that re-opens the old rain shelf.

### Exterior colour, balcony and veneer

- One exterior dark, `#1c1f24`, on every dark metal element on the envelope:
  opening casings, roof rake/eave/ridge trim coil, eave water chain (drip edge,
  box gutter, downspouts), and guards.
- Windows/doors in a clad wall draw casing (resolve/geometry_openings.py
  `exterior_trim`) in this tone. Recolor only via `window_trim` in
  emit/gltf/palette.py + ui/src/three/members.ts `CATEGORY_COLOR.window_trim`.
- Roof edge/water chain/guards get the colour by *material*
  (`metal-dark-exterior`), named by `RF-HOUSE.edge_trim_material`,
  `params/roof_trim.py::_CHAIN_MATERIAL`, and `RAILING_DARK_METAL`. Both
  renderers resolve via `_FINISH_BASE`/`FINISH_BASE` (emit/gltf/palette.py,
  ui/src/nordic/palette.ts) — keep in step.
- A gutter/downspout is a solid: `ResolvedSolid.material` wins over category
  palette only when it *states* a colour; a generic ref like `"aluminum"` still
  falls to category.
- Author colours under the tone wanted on screen, not the tone typed: the
  viewer's lighting (0.8 hemisphere + 0.9 key + 0.6 IBL) lifts a dark albedo
  well above itself (→ DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- Guards are `RAILING_DARK_METAL`, split off `POST_WHITE_PAINT`. The balcony's
  two remaining 6x6 centre pillars and the stairwell posts still use
  `POST_WHITE_PAINT` and must stay white.
- Balcony structure (2026-09-03, `notes/balcony_moment_columns.md`, supersedes
  `superseded/balcony_lateral_bracing_design.md`): four cast concrete corners,
  two wood centre posts, three glulam beams. No knee braces exist any more.
- Four CORNER pillars: 12" round reinforced concrete, FIXED at the base,
  doweled into the 12" wall tops of `W-SG-W1`/`E1` — the balcony's entire
  lateral system in both plan directions.
- 12", not 10": 2" cover on a #5 cage inside #3 ties needs a 6-5/8" bar circle,
  flush with both wall faces. `SUNKEN_GARDEN_COLUMN_12` serves all five cast
  columns; `_COLUMN_20` is retired.
- Exposure F3 + C2, not F2: w/cm <= 0.40, f'c >= 5,000 psi, 6% ±1.5 air. Bar is
  hot-dip galvanized (ASTM A767 cl. 1 or A1094) — do not substitute epoxy or
  stainless. **Galvanize AFTER fabrication, and say so on the order.** A767's
  classes are COATING WEIGHTS, not a bend-order distinction, so naming cl. 1 does
  not settle the sequence and these cages are shop-bent: #3 ties to a 6-5/8" bar
  circle. Bending coated bar cracks the coating and needs repair per ASTM A780 —
  which also applies to any field cut or bend. And a WELDED cage is outside A767
  altogether: welding is fabrication of an assembly, which ASTM A123 governs.
  Put "galvanize after fabrication per A767; repair cut/bent coating per A780" on
  the rebar order (→ `plans/buildability.md` BLD-02).
- Beam seat is CAST TO LINE, no grout island: screed the wash/drip lip, take
  tolerance in the `SS316-SHIM-35` shim pack (`CN-SG-STDF-*`), HGAM10 gusset +
  Titen Turbo. `PIER_CONCRETE_12` still carries a grout island at `PT-SG-COL` —
  a known follow-up.
- Two CENTRE pillars stay wood 6x6, bearing on a 3-ply pack (joist + two
  sisters) with squash blocks, through a cut-out in the composite deck
  (composite bears nothing). `CCQ46SDS2.5` cap closes uplift at each.
- Porch joists CROSS both beams (`JoistSpec.cantilever_start = 2-3/4"`) — do
  not move without re-checking NDS §3.10.4 at `PT-SG-BF2`. The composite sheet
  ends 2-3/4" outboard of `RL-SG-PORCH`'s guard line by design.
- No standoff post base at either centre pillar: `MSTA12Z` strap (both west
  faces, x=213.25") + `L50Z` angles (north at both, south at `PT-SG-BR2`) hold
  each down — never an ABU-type base, neither bears on concrete. Graded via
  `haus engineering --item post_bearing/PT-SG-BR2`, oracled in
  `notes/centre_pillar_bearing.md`.
- Centre pillars are DF-L, not SPF — connector requirement
  (ESR-2604/2330/2105/3096, all SG >= 0.50 at MC <= 19%); see
  `POST_WHITE_PAINT_DF`. C_M 0.70 wet-service is already in the 658/375 lbf in
  `library/hardware.py` — do not derate again.
- Three beams: treated SYP glulam, `"3.5x11.875"` (24F-V5M1/SP),
  clear-finished. Author DECIMALLY — `_RE_NOMINAL` silently resolves a
  nominal-looking string 1-1/4" short. Engineered items `deck_beam/BM-SG-BL*`.
- Front-row beam/column line did NOT move with the corner change; its 12"
  column top runs 3-1/4" past the beam end. Re-solving it moves the deck edge,
  fascia, drip, gutter and `BALCONY_FRONT_AXIS_Y_FT` together.
- Fallback: New Castle Steel HDG 6x6x3/16" post w/ welded base plate
  (~$458/10'), still needs a fabricated saddle with no shop drawing made.
- Both guards: Williams Architectural Products, ICC-ES ESR-3485, 42" black
  (Menards; Eagan MN); alternate Fortress Al13 Home.
- `RL-SG-PORCH` is surface-mounted (`RAILING-EXT-ALUMINUM-SURFACE`): west/east
  legs on 12" concrete wall tops take ESR-3485's baseplate anchors directly.
  The south leg bolts through the plank into joist-bay blocking north of the
  beam — never through `TR-SG-CAP-FRW/FRE`, its butyl is the dielectric between
  aluminium cap and copper-treated framing.
- `RL-SG-BALCONY` stays fascia-mounted (through-bolted PVC fascia + 2x8 rim)
  because `FS-SG-DECK`'s aluminium plank is the porch roof and carries no other
  penetrations — do not switch to surface mounting. Needs rim blocking in
  `FS-SG-DECK.reinforcements`.
- Veneer `W-B-BRICK` (129 SF, both faces exposed) stands on `W-SG-BRKBM`, a 12"
  x 17-3/4" grade beam spanning 19'-0" between `W-SG-W1`/`W-SG-E1` — not on the
  house footing (`FT-B-BRICK`, retired). Basis:
  `notes/sunken_garden_veneer_beam.md` (2026-09-05).
- Nothing in the engine grades a thermal break for continuity — a `Footing`
  resolves to one blob with no polygon, so verify an adjacent gap directly (→
  DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- `SG_VENEER_BEAM_14` = 12" pour + 2" of 40 psi XPS `Layer`. The beam is its
  own open wall-graph chain and takes the FALLBACK outward sign — do not trust
  it; verify against
  `test_catlin_contract_m3.test_the_veneer_beam_isolates_the_house_footing`.
- `FT-B-S2`/`FT-B-S3` south face is now at **-8"** (via `offset`, not width,
  keeping all 20" of bearing) — anything re-centring these footings must keep
  that face.
- Brick's y is fixed at -10.05"..-13.675" by the beam; `N-B-BRICK-W`/`-E` sit
  at -8.05". `N-B-BRICK-E` is at 27'-6", not 28'-0" (`W-SG-E1`'s axis), so the
  east wythe does not walk inside the retaining wall.
- 2" EPS (ASTM C578 **Type II**, 15 psi — not Type I) is in the BACKUP wall's
  `_GARDEN_CURB_CORE`/`_GARDEN_FRAMED_OUTBOARD` layers, not in
  `BASEMENT_BRICK_VENEER` — blast radius is `W-B-S2`/`S3`/`S2-FR`/`S3-FR` only.
  `code.energy_prescriptive` grades one assembly at a time, so foam in the
  veneer's own stack would earn no R.
- `eps:2.0` is a distinct price key for labour, not thickness —
  `envelope_layers` qualifies on `thickness_in` only, so any other 2" EPS
  elsewhere would silently inherit this rate. None exists today.
- Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to cut anchor count:
  unreinforced brick can't span 18'-8" horizontally, and both ends want a soft
  joint the model does not carry and the engine does not grade (→
  DESIGN-LOG.md, "Exterior colour, balcony and veneer").
- Do not describe this beam as reinforcing `W-SG-W1`/`E1` — those walls already
  PASS `structural.foundation_unbalanced_fill` independently; the beam's only
  job is the thermal break.
- Two engine bugs fixed here: `local_grade_elevation_m` now uses whole-polygon
  containment, not centroid, for footing shelter; `_exterior_shells_by_storey`
  now keeps holes over an open excavation floor rather than filling every
  interior ring once the court connects to the house.


### Sunken garden court

- **The court is one surface, one riser.** `SPEC.court_step_down_in = 0`; `SL-SG-FLOOR` is
  flush with the basement floor plane and the 532 sf court reads as one floor. The only step
  is the 7 1/4" riser at `D-B-PATIO`. `SL-SG-STOOP` is retired — never reuse uid `SGS503AAAA`.
  `code.R311_3_exterior_landing` reads "D-B-PATIO lands on SL-SG-FLOOR, 7.3" below threshold".
- **Do not lower the court below the flush plane** — 7 1/4" is the legal ceiling, not a
  preference: R311.3.2 caps a non-required, inward-swinging door's riser at 7 3/4"
  (`_MAX_NONREQUIRED_STEP_DOWN`), and any lower step needs its own landing (→ DESIGN-LOG.md,
  "Sunken garden court").
- Ponding over the court is ~321 cf against ~191 cf of 100-yr/24-hr rain (~1.7x); the
  governing case is snowmelt over a frozen grate, where `DRW-SG-MAIN` contributes nothing.
- **`W-SG-ARCH` must not move, and since 2026-09-10 the reason is no longer the ratio.**
  Dropping its top to the rim underside gives a 10 1/4" section at phi-Pn 60,712 lb, which
  FAILED at Pu 62,051 (d/c 1.02) and **passes at today's Pu 49,157 (d/c 0.81)**; the 8 1/2"
  section passes too, by 2%. What holds 12" x 17 1/2" is the SEQUENCING argument — the loop
  must close before backfill, and a strut whose bottom is tied to a surface that moves is a
  residue, not a chosen depth — plus no redundancy and a ~1.1 CY saving. Read
  `notes/sunken_garden_court_free_body.md` §8's three-reason block before shrinking it. Its
  top and `_rim_underside_in` are the same expression. `FO-SG-ARCH` is retired with the stoop.
  `W-SG-BRKBM` carries no structural load — it is the veneer's thermal foundation only.
- `_pier_bell_bottom_ft` is **derived**, not pinned: `(_court_top_in - frost_depth_in) / 12`
  — do not pin it again, a pinned literal silently drifts the next time the court moves (→
  DESIGN-LOG.md, "Sunken garden court"). Both bells carry 42" cover; shafts are 128.1875".
- **Both pier bells are 36" (2026-09-10).** The 36" was a fossil sized for a 20" column
  that shrank to 12"; PT-SG-COL's 30" was set by nothing. One diameter, one under-reamer
  setting, one schedule row, ~$27-43, and the tightest pier in the house goes d/c 0.83 →
  0.60. **What the extra 3" per side spends is the gap to FT-B-S2/S3: 8" → 5" in plan.**
  They still never meet — the bell's top is 22" below the house strip's bottom — so the
  live constraint is SEQUENCING, not clearance: auger both shafts with the open basement
  excavation or they undermine the house footing. `AN-SG-PLACEMENTS` says so on the drawing.
- **One footing type in the court, `COURT_FOOTING_12`** (was `RETAINING_FOOTING_96` +
  `PORCH_FOOTING_84`). Identical stacks — 12" of EXPOSED_MIX — split on a width an Assembly
  does not carry, and the porch card declared **13"** where every strip is built at 12". The
  merge removed the lie and a row off the S-100 FOUNDATION SCHEDULE.
- **All six of the court's 12" cast rounds are `SUNKEN_GARDEN_COLUMN_12`** (PT-SG-COL moved
  off `PIER_CONCRETE_12`, which is now the north-entry piers and nothing else), and that
  assembly finally names `concrete=EXPOSED_MIX`. It stated 5,000 psi in prose only, so the
  register printed **the front column as the weaker of the two identical columns** holding
  the ends of one frame. Consequences: corner φM_n 20,900 → 24,700 lb-ft (re-derived by
  hand in notes/balcony_moment_columns.md §4 — β1 steps to 0.80 and φ reaches 0.900, which
  is half the gain), class B dowel lap 35.6" → 27.6", PT-SG-COL's axial capacity 187k →
  286k. No demand moved. The retype also drops the grout island PIER_CONCRETE_12 carries.
- **One excavation plane again**: `FB-SG-ARCH`'s undercut derives to 33", not the footings'
  42", so all six beds bottom on `_SG_WALL_BED_BOTTOM` with the drywell's top. The 42" was
  copied and is not required — the beam has no `Footing`, so it is not in the frost
  population at all. The BEAM still hangs 9" lower; only its bed came up.
- **Three placements, not four**, and the order is on the drawing (`AN-SG-PLACEMENTS`):
  footings + both belled piers monolithic; then all five walls + the grade beam at one form
  height (house basement wall poured, cured and surveyed FIRST, for the epoxied break
  dowels); then the rim slab with all six columns. `AN-SG-MIX` permits EXPOSED_MIX for the
  whole court so it comes off one ticket — **do not retype PIER_BASE_12**, it is shared with
  the north entry. `AN-SG-COLDWEATHER` puts a hard 1 November milestone on placement 3.
- **`_veneer_beam_bottom` stays held** at -120 3/16", not flush with the slab underside — a
  flush beam is only 10 1/2" deep against ACI 318-19 Table 9.3.1.1's L/16 = 14 1/4" minimum
  for a 19'-0" span. Held, the beam is buried but its 17 3/4" section survives.
- `FT-B-S2`/`S3` cover below `SL-SG-FLOOR` is 8".
- `plan/site.py`'s two garden spot elevations are -9'-1 7/16"; they are a structural input,
  not drafting annotation — `engineering/balcony_wind.ground_below_ft` takes the site's
  lowest spot and these two set it (h 22.7', q_h 18.6 psf, wind base moment 1,385 lb-ft; the
  2,502 lb-ft guard case still governs). Move them only alongside
  `notes/balcony_moment_columns.md` and `test_pier_calcs`'s schedule.
- `space_summary`'s interior-hole filter is an area-overlap test, not a single
  representative-point containment check — a floor spanning two bays (as `W-SG-ARCH` splits
  this court) needs both bays counted.
- **All five court walls top out on the porch datum. One form height.** `SPEC.
  retaining_top_ft` is `porch_top_ft` since 2026-09-10, not `(site_grade_in + 36)/12` — the
  36" was recorded as a MAXIMUM when the owner's call was a band (around 36" out of the
  yard, up to about 48", because the wall may be read as a guard). The exposure is a RESULT
  now: `RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN` is 40" against the -3'-4" yard
  `plan/site.py` authors, pinned by `test_retaining_court`. Keep the terrace name separate
  from the porch-floor name so a future divergence is a one-line change.
  - It doubles as `params/raised_garden.py`'s `RETAINING_WALL_TOP_FT` apron TOP, with
    BASE = TOP - drop_ft — moving one moves both. **`drop_ft` is 4'-0" now, eight whole 6"
    courses**, which buries the apron's base course 8" in the authored yard; at 3'-0" off
    the new top it would have stood 4" in the air, the same negative embedment as before
    arrived at the other way. Nothing grades a freestanding wall's base against the ground
    plane, so a wrong constant here goes to 0 FAIL (→ DESIGN-LOG.md, "Sunken garden court").
  - **The apron's `unbalanced_fill` is the DIFFERENTIAL (3'-4"), never `drop_ft`.** It
    tracks `RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN`: the terrace stands that far above the
    yard and below the yard both faces are in the same ground. Writing the 4'-0" run there
    hits IRC R404.1.1's 48" threshold exactly and sends five segmental landscape walls into
    an R404.4 cantilever analysis they have no footing for — five UNKNOWNs, and the wrong
    model of the wall.
- `W-SG-W1`/`E1` bottom on `_wall_bottom` like every other wall; `_PORCH_FOOTING_THICKNESS_IN`
  no longer exists. IRC Table R404.1.2(8)'s 10'-0" row still passes at 9'-1 7/16".
- `FO-SG-TOE-N-W`/`-N-E` void the rim over them, as `W`/`E`/`S` do over the other three toes.
  `FO-SG-TOE-W`/`-E` are cut to `_y_ax_mid`. **The invariant to hold**: the net rim polygon's
  intersection with every `FT-SG-*` footprint must be 0.000 sf — `structural.concrete_
  interference` only grades ISOLATED pours and will not catch a re-lap.
- `DRW-SG-MAIN` sits on the wall beds: `_SG_DRYWELL_TOP = _SG_WALL_BED_BOTTOM`.
  `FD-SG-LEAD-W`/`-E` are the only two leads — the five wall beds form one connected stone
  body (W1↔W2 at y=-11.0', W2↔S via the corner lap, mirrored east). `FB-SG-ARCH` gets no
  lead: its bed bottoms 9" below the well and stops 2" from the shaft, feeding the column
  through its side. Note: `drainage.discharge_consistency` resolves the tag but never checks
  where the pipe actually terminates — verify inverts by hand.
- `Dowel` z is derived off the shared 8" footing-to-footing joint face (mid-way through it);
  the foam block matches that 8". **Nothing in the engine grades a `Dowel` against the two
  footings it names** — check both footing tops/bottoms by hand after any elevation change.
- Current stem/toe state: system FS **1.80** (d/c 0.833), stem flexure **0.61**, toe
  flexure **0.54**, stem length **9.1198'**. Every schedule in the stem bar table now
  clears, `#6 @ 16"` included at 0.97 — `#6 @ 10"` is held on one-bar-one-spacing with the
  footing mat and on §5's stone-bed dependence, not on arithmetic.
- **ALL FIVE court strips are 8'-0" x 1'-0" with a 6" court-side offset and the same
  `#6 @ 10"` mat (2026-09-10).** FT-SG-W1/E1 were 84" and PLAIN on the argument that they
  are braced and the table answers them. The argument skipped the question: **nothing in
  the engine grades a footing's own flexure except on the retaining set**, and their 3'-0"
  plain HEEL is Mu 8,303 against a plain 12" strip's 3,536, **d/c 2.35** — a row that needs
  no assumption about the bracing credit at all, since §7c drops the upward pressure under
  the heel. The toe reads 2.35-2.94 as a free cantilever. The mat was owed either way, so
  the widening bought a continuous form line for concrete and stone alone. Rebar 4,071 →
  4,750 lb; the ratio 27.0 → 31.2 lb/cy, which is the right direction for a reinforcement
  finding. `SPEC.footing_width_in` (84") is kept, unreferenced, as the revert.
- **THE CLOSURE BOARD IS THE JOINT, AND THE JOINT IS THE FOOTING.** `foam_length` reads
  `_RETAINING_FOOTING_WIDTH_IN` and the block is centred on the FOOTING, not the wall axis
  — all 12" of the widening went to the court side, so a board on the axis hangs 6" past
  one end and leaves 6" of bare footing-to-footing concrete at the other.
- **One thermal-break product: `THERMAL_BREAK_IN` / `THERMAL_BREAK_PSI`.** The thickness
  was stated three times in two files and the rating twice, once in prose because `Layer`
  has no compressive field. **The break cannot go on one purchase order today** — the two
  closure blocks bill by VOLUME into concrete, the beam's board by AREA into insulation,
  and nothing reconciles them — so `test_catlin_contract_m3` pins every site against the
  constants. A comment is not a guard; the retaining top's spot elevations proved that.
- **One bar arrangement on the whole plane**: #5 GFRP at 8" o.c., count derived from board
  width (12 across the 96" footing joint, 2 across the 12" wall end). Neither count was
  required by any computed limit state. **The bars are why the board exists** — a `Dowel`'s
  foam block is the only way the engine resolves an XPS solid at a joint, so `count=0`
  deletes the board from the model, the bill and the drawings (and `_resolve_dowel` lays
  `range(max(count, 1))`, so a zero is silently a one).
- **Do not merge the two closure blocks.** Per end it is already one continuous board on
  one plane; two objects only because the joint is T-shaped in elevation. Widening the
  upper one buys foam standing in backfill, and destroys the property that makes it work —
  the narrow block lands flush with both faces of the 12" pour, so the board is a form face.
- **`SG_VENEER_BEAM_14`'s layer order is load-bearing for a fire check.** `code.R316_4`
  reads the innermost layer as facing a room; reversed, a bare 2" of XPS fails it. The
  tuple order is now pinned as well as the faces, so a sign flip and a tuple flip cannot
  cancel into a drawing that looks right.
- **Every wall-to-house joint here needs one continuous 2" XPS board, house-footing-underside
  to porch-wall-top, and nothing checks that continuity** — verify by hand after any footing
  or wall-top move. Four sequencing traps are written into `params/sunken_garden.py` above
  the dowels: the butt joint lands on the court floor plane (lap the upper board); the
  garden pour cannot lead the house (the stem dowels are epoxied into cured wall with ~1"
  of tolerance); the beam's board depends on the FT-B-S2/S3 toe trim, which is a HOLD POINT
  before the house footing pour; and the beam's 20'-0" board is the one with no positive
  tie at all.
- **The brick stays, and it is load-bearing for five other things.** If `W-B-BRICK` ever
  goes it takes `W-SG-BRKBM`, that beam's isolation board, an engineered masonry-anchor
  item no prescriptive table reaches, the weeps, two soft joints and a slab void with it.
  Retiring it is a design pass, not a deletion.
  - Stem blocks and footing blocks are sized by different rules and must stay that way: a
    stem block derives as `max(row_span + 8*dia, 12")` off the bar row (right for a 12" wall
    end); a footing block is `Dowel.foam_length` (default derives the old way) because it
    must span the full width of the footing-to-footing joint, not the bar row.
  - All four south strips (S1-S4) sit on one face at -4"; `_TOE_TRIMMED` is empty and
    `_SOUTH_TOE_TRIM` is superseded.
  - The beam's own isolation board (2" XPS across 4" bedding stone, at `W-SG-BRKBM`'s north
    face, -10") is a separate detail from the wall-joint boards above and is unaffected by
    them — it isolates the veneer pour from the house pour, not the wall.
  - All four footings read "8" below SL-SG-FLOOR" on the R403.3 frost branch (not the ~86"
    `sheltered_by` answer) — re-check this after any footing move, since moving a footing
    north is exactly how a frost check buys a false pass.
  - `test_the_veneer_beam_isolates_the_house_footing` pins the 84" board, full 8" depth, and
    zero plan lap against every house strip.
  - `prices.toml`'s `thermal_break` row bills the four closure boards by SF of 2" 40 psi
    XPS — the four boards are not the same size, so check totals against SF, never against
    count. (The two footing boards grew 84" → 96" with the strips on 2026-09-10.)
  - **FLAGGED FOR THE ENGINEER, NOT TAKEN: trimming the wall beddings' surplus stone.**
    Worth $835-1,250 and the only four-figure item in the simplification pass, and the one
    that touches a load-bearing claim. It collides with the drywell top, with a 5"
    clearance the model already flags as the one to watch, and with the μ = 0.35 friction
    argument that carries the ENTIRE sliding margin (`notes/sunken_garden_court_free_body.md`
    §5 — at μ = 0.25 the court is at FS 1.29 against 1.50). Do not take it on a takeoff
    reading.
- **`W-B-BRICK` is one flat field of unglazed `brown-brick` (`#a07c5c`)**, ASTM C216 Grade SW,
  full height (plinth to top), 129.2 SF, one BOM row `BASEMENT_BRICK_VENEER:brown-brick`.
  Glazed brick is unsuitable here: [BIA Tech Note 13](https://www.gobrick.com/media/file/13-ceramic-glazed-brick-exterior-walls.pdf)
  says not to use it where it can saturate, and this court is a rain sump with walls.
  - **Do not delete** `glazed-green-brick`, `glazed-lapis-brick`, `glazed-gold-brick` from the
    catalog, their `MasonryStyle`s in `ui/src/three/materials.ts`, or their `_FINISH_BASE`
    entries in `emit/gltf/palette.py` — none is referenced now, but a scheme revert is a
    three-place change and needs all three intact. Their `prices.toml` rows are commented
    out, not removed, for the same reason.
  - `BROWN_BRICK_STYLE.jitterHSL = [0.008, 0.035, 0.09]` — deliberately between a glaze's
    near-zero and `BRICK_STYLE`'s `[0.02, 0.08, 0.16]`; either extreme misreads on a 129 SF
    unglazed field (→ DESIGN-LOG.md, "Sunken garden court"). Mortar is `#cfc8ba` (tan).
  - **`haus render` cannot judge this material** — its CLI emitters carry only the flat
    de-jittered `_FINISH_BASE` hex, and `--view elevation` emits east/west while this wall
    faces south. Judge jitter/albedo in the headless viewer, or compute the extremes directly:
    `new THREE.Color(base).offsetHSL(±j[0]/2, ±j[1]/2, ±j[2]/2)`.
  - The wythe is one plain full-height STRUCTURE layer — no `slot`, no `extent`. It must stay
    a STRUCTURE layer, not CLADDING, or `integrity.assembly_layers` finds none (same
    precedent as `RETAINING_BLOCK_12`). `Layer.slot` itself is still live and is exercised by
    the synthetic fixture in `packages/engine/tests/test_emitter_band_parity.py`, not by
    catlin.
  - Rate is `$19-30/SF` (scaffold-inclusive, for the full 8'-5" field) — do not reuse the old
    `$15-28/SF` no-scaffold rate.
  - `AO-B-BRICK-DOOR` reveal height is 78" (84" is also available if more coverage is
    wanted); `AO-B-BRICK-WIN` reveal height is 20". Neither opening is a daylight or egress
    subject; reveal overlap onto the opening is deliberate.
  - **A reveal must stay concentric with the opening it reveals** — width and position are
    not free, only height is. Edit a reveal and its opening together.
    `integrity.reveal_concentric` grades every rough opening with a wall behind it against the
    nearest door/window in that wall, at 1" tolerance; `test_catlin_contract_m3` pins both
    pairs.
  - Both arched reveals are a voussoir ring (`ui/src/three/builders/archRing.ts`), one header
    deep (3 5/8"), 3/16" proud each face. Door extrados crowns at 81 5/8", window's at
    52 5/8". **Viewer-only** — an exported `.glb` still shows a plain spandrel.

## The engineering workflow

Catlin carries ~46 engineered items across ten kinds — the requirements outside the
prescriptive tables. The workflow lives in the root `CLAUDE.md`; what belongs here is where
this house keeps its half of it.

```
haus engineering .                          # the register: what governs, and who sealed it
haus engineering . --item retaining_wall/W-SG-E2       # one item, term by term
haus engineering . --fingerprint retaining_wall/W-SG-E2  # paste into engineering.toml
haus calcs .                                # -> out/calcs/, the package a PE marks up
haus print . --sealed                       # the submittal gate — exits 1 today, correctly
```

- **`notes/` is the oracle set** and `notes/README.md` is its index: which note checks which
  calculation, which are design reasoning, and which 11 are *drawing content* pinned by
  `test_section_goldens.py` and must not be edited as documentation. `notes/TEMPLATE.md` is
  the shape a new calculation note takes; `notes/superseded/` holds designs that are not
  built, each with a `⛔ SUPERSEDED` banner naming what replaced it.
- **No `engineering.toml` exists yet**, so every item reads `unsealed` and the sealed gate
  is shut. That is the true state, not a gap in the setup — the engine reads that file and
  never writes it, and pinning a seal stays a human act.
- **Seven items are deferred to a designer of record** — all THREE roofs' rafters and uplift
  path, and the overhead-door header. `out/calcs/03-open-items.md` names who owns each.
  `RF-BW-CANOPY` joined on 2026-09-10 and its deferral carries a condition the others do not:
  **quote its trusses against the DRIFT case, not the ground snow.** A fabricator reading
  "50 psf ground snow" prices ordinary trusses, and the surcharge off the house gable also
  reaches 3'-10" into the garage roof, so ITS two southernmost trusses are drift trusses too.
  S-001 prints the number; `preferences.toml [structural] roof_beam_snow_psf` is where it lives.
- **One open engineering question** is real and is on that page, not hidden: the
  concealed-fastener wall panel's withdrawal allowable over 24" open girts, which no
  manufacturer publishes (`notes/board_batten_girt_span.md`). **The old second one is
  closed** — the breezeway piers had no modelled plan area to shoelace, and
  `engineering/pier_basis.py::_roof_fields` now gives a roof-on-beams one. Their successors
  publish a real axial ratio against a real tributary (`notes/north_entry_piers.md` §6).

## The loop: edit → build → check → *look* → fix
```
haus build .            # -> out/model.json (+ IFC when ifcopenshell present)
haus check .            # integrity / code / structural findings
haus render --view plan # -> out/render/plan_*.png  — LOOK at what you made
haus render --view elevation   # -> out/render/elev_{n,s,e,w}.png — the facade rules' own eye
haus ls --summary       # compact whole-plan digest
```
After any spatial edit, **render and look**. After assembly edits,
`haus explain <ASM> --card`.
