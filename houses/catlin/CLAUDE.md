# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change.

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
- `library/placeables/*.py` (repo root, not this directory) — the shared FixtureType/
  ApplianceType/FurnitureType *catalog*, wired in by `plan/manifest.py`. NOT editable: it
  uses `frozenset(...)`, which the dialect forbids. Type libraries stay non-editable;
  movable instances that reference them live in the editable modules above. **`plan/
  fixture_types.py` holds SEVEN selections** — `FX-KOHLER-UNDERSCORE-6036`
  (the drop-in bath) and `FX-VANITY-51-SINGLE` (RM-M-BATH2's vanity), plus
  the five vanities that replaced this house's remaining bare lavatories:
  `FX-VANITY-24-SHALLOW` (RM-M-BATH1), `FX-VANITY-30-SHALLOW` (RM-S-VANITY, TWICE — a 60"
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
- `params/breezeway.py` — the enclosed breezeway: pads, piers, posts, deck, roof, glazing.
- `notes/*.md` — construction detail notes migrated from the original repo.

**Editability rule (enforced):** any UI-movable element (Furniture/Fixture/Appliance/
Equipment/Register/ElectricalDevice/Door/Window/Wall/Room/Node/Stair) must be authored in a
`# haus: editable` file, or its canvas edits can't be written back. The loader raises
`loader.uneditable_movable_element` (a hard build error) if one is authored in a non-editable
module. Params-generated geometry (no constructor to write back to) is exempt.

## House facts that must stay true
- Four structures: house, freestanding garage (4' north), freestanding sunken-garden/
  porch/balcony concrete structure (5" south gap), enclosed breezeway on freestanding 6x6
  posts spanning that 4' gap door-to-door (`params/breezeway.py`).
  **The breezeway follows the doors, and nothing enforces that but this line.** It is a
  4'-0" enclosure centred between `D-M-ENTRY` and `D-G-SERVICE`; when either door moves,
  `_GLAZING_CENTER_X` moves with it (`code.R311_3_exterior_landing` catches a shelter that
  drifts off its own door). Both doors open onto the deck
  at 0'-0", and they reach it from opposite directions:
  `D-M-ENTRY` from the house floor it shares, `D-G-SERVICE` *up* +1'-0" from a garage storey
  that sits at -1'-0". The breezeway deck did not move with grade — it is a bridge
  between two doors, and only its pads and piers followed the soil down.
- **Grade is 2'-10" below the main floor, and the house is what stands out of the ground.**
  The model's vertical datum is the main floor, so grade is authored as `Site.grade`
  going down with the datum fixed at 0'-0" at -2'-10" — the basement-ceiling overhaul put a
  12 5/8" deck where a 9" slab had been and the
  house rose 4" rather than surrender the headroom under it. **The datum is the top of
  joists, not the finished floor** — walls bear there and the subfloor rides above it, so
  main-floor FFE is +3/4" and every slab meant to land on it needs an explicit
  `top_elevation` (`params/main_deck.py`). The `main`, `second` and `attic` datums have
  never moved. **The basement storey is at -9'-1 7/16", and grade did not move
  with it.** The flat bearing seat lands the EPS deck's soffit on the same plane as the wood
  bays' mudsill: the deck is 14 3/8" deep and the FLOOR meets it, so the house is where it
  was and the basement is shallower. That makes the pour **exactly 8'-0"**, and the basement
  holds **8'-0 15/16"** clear under the joists / **7'-10 7/8"** under the EPS band — the
  number `code.R305_ceiling_height` DERIVES rather than reads off
  `Storey.default_ceiling_height`, which still authors a fictional 9'-0" here. What follows the soil down is everything pinned to it: the garage and
  its whole foundation, the breezeway's frost pads and piers, the hydrant's bury, the sunken
  garden's floor, the site's nine house-perimeter spot elevations and both impervious
  surfaces. The number lives in `params/foundations.py::SITE_GRADE`, is repeated as a
  literal in the editable `plan/site.py`, and `plan/manifest.py` asserts the two agree.
- **The garage storey datum is not the garage floor.** Its wood walls bear on the ICF stem
  at `GARAGE_STEM_REVEAL` (1'-10") *above grade*, which since the lifts puts the `garage`
  storey at -1'-0"; the slab they enclose is poured at grade, 1'-10" lower, and is filed on
  the `garage` storey with an absolute `Slab.top_elevation`. Anything that has to sit on the garage floor must say so explicitly —
  D-G-OVERHEAD carries the plan's only negative `sill_height` to reach it, and the stem
  becomes a grade beam flush with the slab under that door so there is no curb across it.
  D-G-SERVICE no longer does: its threshold stays at 0'-0" with the breezeway deck, so it
  carries `+1'-0"` and the 2'-10" is taken inside the garage in five 6.8" risers — the
  `SL-G-STEP-0` landing pad at the threshold, and `ST-G-SERVICE` below it. `Stair.floor_opening` is optional (`base_elevation`/`top_elevation` state a rise
  directly) so a step-down within one storey does not need a `FloorOpening` linking a pair
  of storey elevations. It matters beyond tidiness:
  `structural.stair_riser_uniformity` and `code.R311_7_8_handrail` both iterate
  `model.stairs`, so a flight modelled as slabs instead of a `Stair` draws no riser or
  handrail finding at all. It is KDAT (pressure-treated) with `RL-G-SERVICE` over it. The garage plates are 8'-4", not 8'-0", for the same reason: the door
  climbed 4" inside its own wall when the storey went down, and its 3-ply LVL header would
  have pushed through the top plate into the truss heels.
  Emitters — and the placeable resolver that decides how high anything in
  the garage stands — read `resolve/room_floor.py::room_floor_elevation` rather than the
  storey elevation for the same reason. Raising the stem means re-dropping the overhead
  door: the tie is enforced by
  `test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade`.
- **The garage's ICF stem and its wood wall are coplanar on the outside.** The 24'x24'
  node line (`GARAGE_Y_SOUTH`/`NORTH` in `plan/storeys/garage.py`) is the wood wall's
  SHEATHING plane *and* the stem's exterior EPS face: the walls carry
  `alignment=face("cdx-ext")` (the layer NAME
  is the alignment key, so a sheathing swap is also an alignment edit or the wall silently
  misplaces) and the stem carries
  `alignment=face("concrete-ext", offset=GARAGE_ICF_EPS)`. Only the 7/8" of corrugated
  panel projects past, so it drips clear. The breezeway's uncut 4'
  panel is measured off the *cladding*, and the core is 6" thick. Do not "fix"
  it by moving the stem's nodes: `resolve/stacking.py::_axis_match` has a 1/2" tolerance
  and would silently drop the whole foundation-to-framed stack. `FT-GF-*` follow the stem
  via `Footing.center_on="wall"`, not the node line.
- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` so the sheathing plane is the vertical datum (#43).
- The side-wall stack is 2x6 throughout — one `EXT_2X6` on main, second and
  attic, sheathing plane continuous, no stud-depth jog. Main-storey studs are LSL,
  the upper storeys standard dimensional 2x6 (a purchasing note recorded in the
  assembly's `source`, not a separate assembly).
- **It is a CATLIN TRUSS WALL outboard of that sheathing, ONE girt tier.** 4" of 2 lb closed-cell spray foam in ONE application, crossed only by the
  blocks, then the block's proud 1/2" as a continuous vent gap, then **one tier of flat
  horizontal KDAT 2x4 girts at 24" o.c.** standing in free air, then the panel. Each crossing
  is **three loose 3-1/2" x 3-1/2" x 1-1/2" KDAT offcuts stacked to 4-1/2" on the sheathing
  over every OTHER stud**, clamped by **one 8" SDWS22800DB** driven through girt + block +
  sheathing, 1-1/2" into the stud. It replaced the **Swinburne truss** — a
  chiral block + plywood tab + KDAT outrigger *on edge* at 16" o.c. — which had in turn
  replaced a sheet WRB + 2" polyiso + 2" EPS + 1/2" furring on 537 eight-inch screws.
  - **THE INNER GIRT TIER IS GONE, and the reason is not economy.** Bands B and C
    used to carry a plain SPF 2x4 flat buried in the foam, with the outer tier's blocks
    bearing on it and a second 5" screw into it. It sat directly ON the sheathing, so it gave
    its own screw no thermal break at all, and it cost a **10.9 % framing fraction in the
    first 1-1/2" of the insulation** to hold up nothing but the tier above it. The foam needs
    no backing (ESR-4073 §4.4.2 permits 7-1/4" on a vertical surface with nothing in it;
    ESL-1372 lists 3-3/4" of ccSPF between steel Z-girts at 28" o.c.), and ccSPF's racking
    contribution is its bond to the sheathing FACE, unchanged. Worth **+2.5 R**.
  - **THE SCREW IS THE ONLY LOAD PATH.** One per crossing, no second tier, no second pass, no
    nail. What makes that defensible is that the **block bears the cladding's gravity in
    direct compression** on the sheathing, so the screw is a pure withdrawal element — 54 %
    utilised at the note's Exposure C basis, 38 % at the site's actual Exposure B. **Mark the
    stud line across the girt face as it is laid**: the screw is otherwise blind through 6" of
    wood into a 1-1/2" target, and a miss is invisible once the foam is on. Inspect the
    pattern from the ground before the sprayer arrives.
  - **There is no WRB.** The foam is air + water + vapour + thermal, bonded and seamless, and
    `plan/transitions.py` names `spray-foam-ext` as the water and thermal plane. The build
    order is part of the spec: **bucks before foam**, always. What is NO LONGER part of it is
    the two-lift order — all the wood and the whole screw pass now happen on the FLAT wall,
    then tilt, then one 4" lift sprayed through the 20-1/2" clear between courses and behind
    them. **Fillet the foam against the block sides** (BSI-048), never butt it square.
  - **Everything outboard of the sheathing is KDAT.** The girt is a horizontal ledge behind
    the cladding that wet-cycles for the life of the wall, and the block plies stand in the
    same foam-face plane. The SPF tier that was encapsulated and never wet no longer exists,
    so there is one BOM row out here, not two — plus `3-2x4:kdat` for the three-ply block.
  - **The blocks are on the STUD module, on every OTHER stud.** Girts climb their own 24"
    elevation module; the blocks land at
    **32"** from the wall's LAYOUT LINE. 32" x 24" = 5.33 ft2 is the crossing tributary every
    load in `notes/catlin_truss_engineering.md` is derived from. Every fastener is
    wood-to-wood with continuous lateral support and nothing bears on foam — which is why IRC
    R703.15's through-foam furring table is not the applicable provision.
    **The block phase is solved for 32", not for 16",** and that is not pedantry: a phase is
    only line-locked modulo the spacing it was solved for, so reusing the stud phase put half
    of a facade's segments on the opposite 32" parity from the rest.
  - **The course module counts from the SILLS' datum, not the wall base, and its
    phase is ZERO.** `course_datum="framing-base"` + `course_offset=inch(0)` on
    the girt band: on a main-storey wall the two datums are 13-7/16" apart (`platform.py`
    extends the wall down over the floor rim band), and that mismatch is what used to leave a
    field course a half inch from an opening's own head or sill course. One module runs
    unbroken from the wall base **through the gable rake**; three edges break it and only
    three — a starter at the band bottom, a top course on a level wall, and a **rake nailer**
    along each gable's raked top with the field held one board clear of it.
    **THE DESIGN RULE FOR A NEW OPENING FLIPPED WITH THE PHASE: head on a 24" multiple above
    the sole plate (24/48/72/96"), or sill 3-1/2" above one.** It was the mirror of that at
    the −3-1/2" phase, and that phase is no longer available — at 24" it opens a 24.75" bay on
    nine walls and `structural.girt_course_spacing` FAILs it. Zero is the swept winner among
    the phases that keep every bay at or under 24.00": 13 opening edges land exactly on a
    course line, 30 sit in the 7" shadow of one.
    `notes/outie_window_truss_detail.md` has the whole sweep.
  - **Windows are OUTIE**, in the mount plane **6"** out from the sheathing, flanges
    bearing on the jamb posts and the head/sill courses. Derived, never authored — the mount
    plane is the outermost FURRING layer's outer face, which is why not one window moved when
    the stack changed. `structural.truss_wall_opening_support` keeps every RO jamb within a
    flange's bearing of wood.
  - **The cladding face stands 7.25" proud of the sheathing** (`_WALL_OUTBOARD_IN` in
    `params/roof_trim.py`, one named constant, with every older value beside it): 1 1/4" of
    exposed-fastener PBR panel where 1/2" of snap-lock seam once stood. Nothing interior moved —
    walls align on `face("sheathing-ext")` — but `params/roof_trim.py`, `params/breezeway.py`, the garage
    wall lines and the exterior electrical all measure off the cladding and moved with it.
    Windows and doors did NOT: they mount on the GIRT plane, which did not move — which is why
    deleting a whole girt tier moved
    nothing outside this wall. The 6" stack simply comes out a different way now (a 4-1/2"
    block plus a 1-1/2" girt instead of four 1-1/2" layers). Only the cladding return depth
    at a jamb changed with the cladding swap. The garage moved just 3/8" of that,
    because `params/breezeway.py` was also carrying a 3/8" rainscreen furring on the garage
    face that `GARAGE_WALL_2X6` dropped — a correction, not a rounding.
  - **The Swinburne truss is one swap away.** Nothing vertical was deleted:
    `resolve/framing/truss_frame.py` and its branch of the pass are untouched behind their own
    predicate (`laid="edge"` + vertical), the girt frame is a sibling selected by
    `standoff="block"`, and the old layer tuple is kept verbatim as `EXT_2X6_SWINBURNE`,
    referenced by nothing. `notes/outie_window_truss_detail.md` has the three-edit revert.
  **The card reads R-43.5 and the honest number is ≈R-39.8 wood-only / ≈R-37.9 with the girt
  screws counted** — the blocks are framed rather than authored as a `CavityFill`, and the
  girt is credited its own R although it stands outboard of the vent gap.
  **`wall_r = 40` is now effectively met on the wood-only basis** (39.85
  against 40) and is 2.1 short with fasteners in. Do not read the card as saying the target is
  met; do not read the shortfall as bigger than it is either. See the engineering note §7,
  and §7.1 for the comparison against a 4" polyiso + furring wall (this wall wins by ≈ +3 R).
  **The stud bay is FIBREGLASS, not mineral wool.** An owner cost review swept mineral wool out of every
  cavity in the house that is not damp, hot or wet: it costs 2x installed, reads the SAME
  116 perm-in, and published STC tables separate assemblies by mass and decoupling, not by
  which wool is in the bay. **The batt is not the lever on `wall_r`** — it is worth 0.9 of
  the 2.7-point shortfall for $4,500-6,300, and the other 1.8 was never in the bay at all.
  **Where mineral wool is KEPT and must not be swept next time:** the tub deck, all three
  sauna assemblies, all three plant-room assemblies, and the shared `_GARDEN_FRAMED_STUD`.
  That list and its reasoning live in `plan/assemblies.py` above `EXT_2X6_SWINBURNE`.
- **`INT_2X4_PARTITION` HAS NO INSULATION AT ALL, AND ONE WALL LEFT IT.**
  The owner's reasoning: none of the 27 walls still on the preset is somewhere sound
  isolation is worth buying, and where it IS, the answer is `INT_2X4_RC` (STC 48, resilient
  channel, a real published test) rather than a batt. `W-S-SS2` took exactly that route —
  the one bedroom-facing wall left on the preset.
  - **Its rating is the USG-tested STC 34, and the SPACING is why.** SA924 / UL U305/U314
    publishes this exact 4-3/4" build at **34 at 16" o.c.**, 37 at 24" o.c., and 46 at 24"
    with 3" SAFB. Catlin frames at 16". **Do not difference 34 against the old insulated 36
    and conclude a batt is worth a point** — the two are different test series, and on USG's
    own 24" rows the batt is worth NINE.
  - **The card over-reports it and cannot say so.** With no `CavityFill`,
    `analysis._layer_rsi` bills the 3-1/2" stud layer as SOLID SPF over 100% of the area:
    the card reads **R-6.4** where the honest whole-assembly value is nearer R-2.5-3. Same
    trap `GARAGE_WALL_2X6` documents. Harmless only because the `INT` token takes an
    interior partition out of `mn_energy` entirely — never quote the card for this one.
  - **KNOWINGLY ACCEPTED, so nobody re-opens it as a defect:** four walls left uninsulated
    are places a designer would normally put a batt — `W-S-SBS` (primary bath to primary
    suite), `W-M-BDN1` (ensuite to bedroom), `W-A-BATH-S` (guest bath to guest bed) and
    `W-M-HS3` (living to LAUNDRY — note `W-M-LS` protects the study from that same laundry,
    and nothing protects the living room). The fix, if any is ever wanted, is a retype to
    `INT_2X4_RC`, not a batt put back in the preset.
  - **On `W-S-SS2` the channel is on the NORTH face and must stay there.** The south face
    carries ST-S2A's flight, its 2x10 stringer ledger, its handrail, and a void boundary
    `attic.py` defines as "W-S-SS2's south gwb face". The channel-side face moves outboard
    1/2"; on the south that is into a stair well cut to EXACTLY 3'-0", leaving 35 1/2"
    against R311.7.1's 36". It would also mean lag-screwing a stringer through resilient
    channel, which shorts the channel out.
  See `notes/outie_window_truss_detail.md` and `notes/catlin_truss_engineering.md`.
- **THE HOUSE WEARS TWO PANELS: BOARD & BATTEN NORTH AND SOUTH, PBR EAST
  AND WEST.** 1,678.3 SF of `board-batten-24` (24 ga concealed-fastener PVDF, 20" net
  coverage) on the twenty walls whose faces run east-west; 1,416.6 SF of `pbr-panel-26`
  stays on the other line. It is a per-wall `Wall.layer_materials` override on those twenty
  and **nothing else** — no sibling assembly, no moved geometry, no new detail keys.
  - **A sibling assembly was the obvious move and is the wrong one.** It would strip the oak
    window stools from every window in a B&B wall (`plan/millwork.py` scopes them to
    `("EXT_2X6",)`), mint new `opening_perimeter:` / `wall_roof:` / `wall_foundation:`
    keys and goldens, break the exact-key star overrides in `plan/transitions.py`, and add a
    key to every table keyed by assembly. `W-S-S1` is `PLANT_EXT_2X6_HUMID` while `W-S-W4` on
    the other line is too — the plant room straddles the split, and the override handles it
    without forking either assembly.
  - **THICKNESS STAYS 1-1/4", AND THAT IS LOAD BEARING.** Four consumers hand-transcribe the
    cladding face and all four feed the *north/south* faces this panel lands on:
    `params/roof_trim.py::_WALL_OUTBOARD_IN`, `params/breezeway.py::_HOUSE_CLADDING_Y`,
    `params/sunken_garden.py`'s `gap_to_house_in`, and the exterior devices in
    `plan/electrical.py`. The roof footprint re-derives itself and those constants do not.
  - **`skin_family="standing-seam"` is on BOTH panels and must stay.**
    `continuous_skin_cladding` wants every wall under a roof to read as one skin; two
    materials declaring it collapse to one key and the flush zero-overhang edge survives the
    mixed case. Drop it and the edge reverts to fascia-and-drip-edge on **all four** edges,
    PBR included.
  - **`exposed_fastener` is deliberately ABSENT on it**, which is what dropped `T09150HWAM`
    from 3,263 to 1,804 (640 garage + 1,164 E/W PBR) and folds the concealed pancake screws
    into the $/SF rate. The `attic` storey vanished from those hardware rows entirely — it is
    all gable, so it has no face-fastened skin left.
  - **The appearance is TEN registrations, each of which falls through silently if missed** —
    `BOARD_BATTEN_PROFILE` + the `metalPanelProfileForFinish` branch (`ui/src/three/materials.ts`),
    `FINISH_BASE` (`ui/src/nordic/palette.ts`), `_FINISH_BASE` and `_METAL_PANEL_FINISHES`
    (`emit/gltf/palette.py`), `DETAIL_FILL` + `DETAIL_HATCH` (`emit/draw/palette.py`), the
    mirrored `DETAIL_FILL` (`ui/src/components/DetailCanvas.tsx`), and `_BATTEN_PITCH_M`
    with a **finish-first** branch in `emit/draw/elevation_finish.py`. That last one is the
    subtle one: this panel is concealed-fastened AND declares `skin_family`, so on the flags
    alone it would draw 16" seam pitch, not 20" battens.
  - **Four wall corners now bill, and did not before.** The engine models NO wall-to-wall
    corner trim: `corner_trim` is exclusively the roof-edge piece. `TrimKind.WALL_CORNER` +
    `Flashing.vertical` (mirroring `GlazingTrim.vertical`) close it — 89.5 LF over the four
    corners, derived in `params/roof_trim.py` off `_WALL_OUTBOARD_IN` rather than
    hand-transcribed a fifth time. Without `vertical` a 22'-4" corner bills as 1-1/4" of
    metal, because `_EdgeRun.path` is a *plan* polyline.
  - **It is ENGINEERED, not prescriptive (decision #65).** PBR's wall capacity is published
    in the manufacturers' own wall span tables (ASC PS230 / Metal Panels Inc. / Homewood,
    144-168 psf at 3'-0"), so PBR stays prescriptive; board & batten appears in no such
    table beyond Metal Sales', and the limit state that governs it — concealed-leg screw
    withdrawal — is published by nobody. `wall_panel/<wall tag>` x 20 in `haus engineering`,
    `INCOMPLETE` **even though bending passes at d/c 0.31** (58 psf allowable at the 24"
    girts), oracled by
    `notes/board_batten_girt_span.md`.
    **ESR-4729 DOES NOT COVER THIS WALL.**
    It is Western States' report, it covers ROOF panels only, and it is written for 24 ga
    minimum over 16 ga STEEL supports. Do not reintroduce it — this file,
    `prices.toml` and `notes/board_batten_girt_span.md` all cite it correctly now.
    **Only Western States and Metal Sales permit open girts** of eight surveyed — and only
    Metal Sales is verified, since Western States' own install guide could not be fetched;
    substituting another forces a second girt course or a continuous deck, which costs more
    than the panel switch.
    **The cladding screw is 1-1/2", stainless or ASTM A153 Class D HDG**, never the 1"
    plated pancake screw a panel order ships with: it has to take the full thickness of the
    1-1/2" KDAT girt, which has no sheathing behind it to catch a short screw. Metal Sales'
    "1/2" past the inside face" clause needs a written variance — open.
  - **The revert is deleting twenty `layer_materials=` lines.** `pbr-panel-26` and its
    `prices.toml` row are still live on the other elevations. Delivered cost of the switch:
    **+$2,200 to +$5,600** measured line-to-line.
- **Every exterior corner is construction-correct, 4-stud.** Three findings and their fix:
  - **The grid is struck from the building's outside sheathing corner.** All four facade
    layout lines have an along-axis origin of `+0.0000"` from a building corner; 217 of 241
    exterior module studs sit on exact 16" multiples from that corner (the 24 exceptions are
    the corner posts themselves); all 31 exterior windows centre exactly on that grid; the
    stand-off band runs the same grid, so the cladding's own line and the stud line are one
    line. This was already correct and the audit did not touch it. It survived the catlin
    truss: the girts are horizontal, so what phase-locks to the 16" module now is their
    BLOCKS rather than the band itself, and the promise is the same one — the screw lands
    on the stud.
  - **The house's corner is 4-stud, not 3.** `EXT_2X6` and `PLANT_EXT_2X6_HUMID`
    (the only two truss-wall assemblies) both carry `corner_style="4-stud"` on the STRUCTURE
    `FramingSpec`, and `preferences.toml`'s `[framing] corner` states it once for the whole
    house. The APA/BASC thermal objection to a solid 4-stud post (an insulable void inside
    it) does not apply here: the primary insulation is the *continuous exterior closed-cell
    foam*, outboard of the post, so the post itself needs no cavity to hold batt in. A
    4-stud corner style authored as `corner_style_end="4-stud"` on only one incident wall
    used to never take effect — the exterior loop is a CCW chain, so every wall's `end` is
    the *next* wall's `start`, and `resolve/topology.py` gives L-corner ownership to
    whichever wall *starts* there. A style authored on the wall that only ever *butts* the
    corner could never take effect; `resolve/framing/solver.py::frame_model` now resolves a
    corner's style from BOTH incident walls (the owner's own authored end-style, else the
    butting wall's), which is what makes an override on either wall reach the pack. The
    freestanding garage (`GARAGE_WALL_2X6`) was NOT changed and stays 3-stud on purpose —
    it has no continuous exterior foam, so the thermal objection still applies there, and
    `structural.corner_style_matches_preference` is scoped to assemblies whose own
    `FramingSpec.corner_style` already matches the house preference for exactly this reason.
  - **The corner box is RETIRED with the outrigger band it closed, and the
    machinery is kept.** It was the Larsen/Swinburne detail (FHB, Jan 2024): two 1/2" OSB
    rips per corner per storey (24 total), one along each wall's own outrigger band, meeting
    at the true building corner to close both outboard faces of the ~5"x5" full-height void
    the band's own 45° mitre left standing open there. A girt band has no such void — the
    courses are horizontal and **butt at the corner**, so each course closes its own band as
    it goes and there is nothing full-height to cap. `FramingSpec.corner_cap` and
    `TrussFrame.corner_box` are untouched and still fire for any band that asks for them;
    `EXT_2X6_SWINBURNE` still does.
  - **The 1/2" sheathing lap at the corner is still undeclared** (all layers mitre 45°
    today; a real lap has one wall's sheet run long and the other stop short by its
    thickness) — logged in `plans/TODO.md`, not built.
- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' spans E-W, on every
  storey and in both materials.
- **The SECOND storey has a fourth bearing line, x=10'-0".**
  `W-S-BA-E`, `W-S-BA-E1B` and `W-S-BD-N1B` carry the cut ends of `FO-A-HALL`'s attic joists
  now, so all three are declared `structural_role=BEARING` — and **the assembly had to change
  with the role.** All three were `INT_2X6_STAGGERED_PLUMBING`, and
  `structural.wet_wall_bearing` FAILs any BEARING wall framed with staggered studs: neither
  face's studs carry the plates' load. They are `INT_2X6_BRG_PLUMBING` — continuous
  2x6 studs plus the 5 1/2" fiberglass batt the staggered wall's cavity had, so the swap does
  not silently strip the insulation as bare `INT_2X6_PLUMBING` would. Total thickness is
  identical (6.77" both ways), so **no face moved, no room area changed, and
  `FX-S-BATH1-LAV`'s `wall_ref` is untouched.** The cost is real and is the honest price of
  the line: studs get bored where the hall bath's stack passes.
  - `stacks_on` is MANDATORY on this line, not decorative. `W-M-STRW` (main, y 26'-6"→36')
    has TWO collinear candidates above it — `W-S-BA-E` and `W-S-BA-E1B` both sit on the same
    x=10' line — and `integrity.stack_ambiguous` is a hard ERROR without a tiebreaker.
    `W-S-BA-E1B` names `W-M-STRW`; **only one upper wall may claim one lower wall**, so
    `W-S-BA-E` carries none at all and stands on the same wall regardless. Do not "fix" that
    by pointing it there too. (`W-M-STRW2`, the 5 3/8" stub south of `W-M-STRW` down to
    `FO-S-STAIR`'s edge, is not part of this: it is too short to clear `resolve/stacking.py`'s
    2' minimum overlap either as an upper or a lower candidate, so it never resolves a stack
    edge — its `stacks_on="W-B-STR3"` is honest geometry, not a load path.)
  - Between y=22'-4" and 26'-6" the line has **no wall under it and can never have one** —
    that 4'-0" gap is the mouth of the hall stub you stand in to open `D-S-BATH1`. `BM-S-BATH-E`
    is there instead: `3-1.75x11.875 LVL`, and **the ply count is a BEARING-WIDTH dimension,
    not a bending one.** The demand is ~600 lb; two plies carry it many times over but are
    3.5" wide, and the 4.77" attic partition standing on the beam would overhang 0.65" each
    side. Three plies is 5.25" — the same section as `BM-S-HALL`, one LVL depth on the job.
    Flush (`top_elevation=ft(20)`) so the vanity stub keeps an unbroken 9'-0" ceiling.
- **The basement's ceiling is mixed, and what the two halves share is ONE FLAT BEARING SEAT
  at -13 7/16", not one depth.** `FS-M-WEST`, `FS-M-MECH`, `FS-M-STAIR` (x 0'-18')
  and `FS-M-EAST` (x 18'-36', y 0'-13') are 11 7/8" I-joists at 16" o.c.; `SL-M-DECK` is what
  is left of the old 1,233 SF cast deck — 414 SF over the dining end, a 10" LiteDeck EPS
  stay-in-place beam (8" base + 2" top hat) under a 4 3/8" cast cover. Every basement concrete
  wall tops out on the seat; the deck's soffit lands on it and so does the underside of the
  gasket under the wood bays' shared 2x6 mudsill. **No step in the forms, one plate for the
  studs and the joists together.** They used to be tuned to one *depth* (12 5/8") instead,
  which matched the finished floors and left the joists resolving inside the top foot of the
  pour with nothing between wood and concrete. `structural.mixed_deck_bearing_seat` is a FAIL
  check that holds it, and `integrity.floor_bearing_grid` holds every joist cut over its own
  wall's structure. The boundary between the two materials is still a line on a drawing and
  moving it is still a one-line edit in `params/main_deck.py` (which is also where the seat
  and the depth constants live, and why they are not in the editable storey file). Ceiling is
  5/8" gypsum end to end — IRC R316.4 over the EPS, `ceiling_below` on the joist fields —
  though the two gypsum faces step **2 1/16"** at the boundary: 1/2" of it is the form's steel
  rib, the other 1 9/16" is the deck being deeper than the wood bay, which is what one flat
  seat costs. **And the step is modelled.** `RM-B-GYM` is the only room the
  boundary crosses, and it resolves TWO ceilings rather than one — 234 SF at -11 7/8" under
  `FS-M-EAST`, 90 SF at -13 7/16" under `SL-M-DECK` — because a room's ceiling is derived per
  *deck region* (`resolve/ceilings.py`, `ceiling_over.ceiling_regions`), not per room. The
  model states the 1 9/16" it can derive; the rib's 1/2" belongs to the EPS form and EPS is
  never modelled here. A room over two decks of the same depth (`RM-M-LIVING` across the
  second floor's truss/I-joist split) stays ONE ceiling — a deck seam is not a step.
  **The floor finish follows the deck**: `SL-M-DECK.floor_finish` is `polished-concrete` (the cap's top
  *is* the finished floor), `RM-M-LIVING.floor_finish="lvp"` is the field finish over the
  wood bays only, and the split is derived — moving `_BAND_Y` moves the finish with it.
  **That derived band is the room's ONLY zone**, and as of **2026-09-05** nothing is authored
  here at all. It carried a sheet-vinyl hall band until that day, then a solid-oak south bay
  for part of it; both are deleted rather than replaced. The hall simply takes the room's
  field `lvp`, `RM-M-BATH1` and `RM-M-LAUNDRY` retyped onto the same plank so `vinyl-sheet`
  has left this storey, and the south bay is that same plank. What breaks the plank is the **mudroom suite** — `RM-M-MUDROOM` plus BOTH its
  closets, `RM-M-MECH` and `RM-M-MUD-CLOSET` — in porcelain over an uncoupling membrane.
  `integrity.concrete_finish_needs_concrete_deck` is still what keeps all three off a
  concrete finish, since `FS-M-MECH`'s I-joists and plywood are what is under them.
  **The two closets are tiled because of the doors they open off, not because they are wet.**
  Both are carved out of the mudroom's own footprint and both doors open INTO it (`D-M-MECH`
  on `W-M-MECH-S`, `D-M-MUDC` on `W-M-MUDC-N`); neither opens off the hall. Put either back
  on plank and the entry's tile becomes an island with three transition strips through it
  rather than the one at `D-M-MUD` — one of them under `D-M-MUDC`'s bypass-slider bottom
  guide, which is the detail that decided it. They took LVP for a few hours on 2026-09-05
  before that adjacency was checked; +$298-627 delivered to put them right.
  **Two walking planes, and they meet flush**: plank at +0.986" against the polished cap's
  +15/16" — 1/64" — on BOTH legs of the L, `y=13'` (17.9 lf) and `x=18'` (13.6 lf). Only the
  mudroom breaks it, at ~+1 5/16", and its ~5/16" strip at `D-M-MUD` is the one threshold on
  the storey. **The oak bay is why that is worth stating.** Oak finishes at +1 1/2", so the
  `y=13'` leg would have been a **9/16" reducer**, and it could not be designed out —
  `structural.mixed_deck_bearing_seat` leaves the cap 1/16" of lift, not 9/16". The height
  difference was not wanted, so the finish gave way: the bay went back to plank the same day,
  -$1,980 to -$2,751 delivered, and the `oak` row fell back under its sand-and-finish
  mobilisation minimum. Oak is still the two studies' floor, where nothing meets a cap.
  **And that zone left a bug behind worth knowing about.** Its outline was deliberately
  over-extended past the room on three sides, on the documented promise that
  `resolve/rooms.py` clips a zone — which it did for the AREA and not for the drawn ring, so
  the living-room floor rendered a foot outside the east and south walls at 0 FAIL. Fixed in
  the engine on 2026-09-05: an authored zone is now drawn clipped, like a derived one always
  was. Before authoring a zone here, prefer a derived one — it follows `_BAND_Y` on its own.
  `notes/mixed_deck_movement_joint.md` has every junction, the L-shaped
  transition and the cream-polish spec — whose "no fibres" clause was **superseded
  2026-09-03** by micro-MONOFILAMENT PP at ~1.5 lb/cy (`POLISHED_MIX`). Macro fibre
  is still excluded here, and so is steel; the distinction is the whole finding.
- **The second floor's deck is mixed too, and for a different reason than the basement's:
  services, not a concrete/wood boundary.** `FS-S-WEST` (x 0'-18') is 11 7/8" open-web
  trimmable floor trusses at 16" o.c.; `FS-S-EAST` (x 18'-36') is 11 7/8" I-joists,
  unchanged from the old whole-floor `FS-SECOND`. West is where nearly every second-floor
  plumbing/HVAC crossing lives — both drain stacks, all four supply risers, the
  radon/plumbing chase, the hydrant distribution and the data conduits — so it is the half
  where a service can cross *through* the webs (8 7/8" clear chord-to-chord opening,
  `resolve/framing/profiles.py::open_web_opening_m`) instead of being bored, soffited or
  chased; east is bedrooms and a study with only incidental crossings, so it keeps the
  cheaper I-joist. Both are the same 11 7/8" depth, deliberately — the deck plane, the
  finished floor and the ceiling below all stay flat across the split, and unlike the
  basement's boundary this one needs **no movement joint and no finish break** (same
  depth, same stiffness class). Trimmable stock is 18' and 20', trimmable up to 6" from
  each end; the west field's *bearing grid* is 18'-0" but the **truss is 17'-11"** — it
  stops behind the 1¼" rim at the west framing face and 3½" onto the x=18' plate, which is
  what `resolve/floor_ends.py` derives and what `haus takeoff`'s fabrication schedule
  states, along with the 17'-3¼" clear span and the seat at each end. An 18' blank trimmed
  1" still covers it (`takeoff/framing.py::_order_length_ft`). **That x=18' plate is shared
  with FS-S-EAST and is split deliberately, 3½" to the truss and 2" to the I-joist**
  (`params/second_deck.py`): an open-web floor truss wants 3" of seat where an I-joist
  wants 1¾", so the centreline split both halves used to take shorted the truss.
  `integrity.floor_end_bearing` grades it. `FO-S-STAIR` falls in the west half, so eight
  joist lines there clip to 10'-1⅝" and fall outside the trimmable range — fabricated to
  length instead. Moving the split is a one-line edit in `params/second_deck.py` (which is
  also where the shared depth constant lives, and which `params/main_deck.py` imports
  rather than restating). The truss price row in `prices.toml` is a placeholder pending a
  fabricator quote, and the span-table row it borrows from the I-joist
  (`checks/structural/checks.py::_IJOIST_SPAN_FT`) is explicitly advisory at this 18'-0"
  span — the fabricator's own table governs.
- Attic is a habitable hot-roofed cathedral space: **rafter plates E/W** (not knee walls),
  gables N/S, ridge N-S, **6:12**, **zero overhang**.

  > **THE ONE LINE EVERY ATTIC STATION ANSWERS TO:**
  > **the roof underside is `1 1/2" + x/2` above the attic finished floor**, mirrored past
  > x = 18'-0". 9'-1 1/2" at the ridge, 7'-0" at x = 13'-9", 5'-0" at x = 9'-9", 3'-0" at
  > x = 5'-9". A window head, a can light, a receptacle, a door, a duct, a piece of
  > furniture, a vent riser — each one is legal or it is not against that line, and every
  > attic comment in `plan/` that quotes a height quotes it from there.
  >
  > The corollary for an opening: a head at `h` needs `h + 2"` of rake (the raked plate plus
  > a flat 2x4 nonbearing header), so **`x_outer_jamb >= 2 x (head + 2")`**.

  It used to be 5'-0" knee walls at 4:12, from a MISREADING of
  R305 — that every square foot of a sloped-ceiling room needs 5'-0" of headroom. Minn. R.
  1309.0305 R305.1 Exception 1 and IRC R304.1/R304.3 scope both clauses to the *required*
  floor area (70 sf), not the whole room, and R304.3 says floor under 5'-0" simply does not
  count rather than disqualifying the room. `code.R305_ceiling_height` used to grade the whole
  room; it was fixed in the same pass that removed the knee walls. With the knee walls gone the pitch was free
  to be whatever the headroom wanted, and 6:12 is the shallowest standard pitch that carries
  the rooms. **The building got 1'-9 1/2" SHORTER** (ridge 32'-0 5/8" -> 30'-3"), the
  envelope lost ~572 sf of `EXT_2X6` for +89 sf of roof, and six windows came out.
  Measured, not asserted: `haus takeoff --csv` before and after puts the redesign at
  **-$19,400 to -$36,200**. (The same before/after run also moves by three PRICING fixes
  found in passing and unrelated to the attic — an `icf-eps` double-bill removed, and the
  missing `closed-cell-spray-foam:1.0` and `WT-2748`/`WT-2748-T` rows added — which net
  **+$3,100** of previously invisible cost. The all-in line-to-line delta between the two
  CSVs is therefore **-$17,200 to -$32,300**; the attic itself is the bigger number.)
  Its deck `FS-ATTIC` is also **the second storey's
  ceiling**, and it authors that board (`ceiling_below`, 5/8" gypsum, restated inline
  because `plan/storeys/attic.py` is `# haus: editable` and cannot import `params/`). It
  was the last deck in the house without one — every second-storey room used to
  resolve open to the I-joists, absent from the 3D model and from the order. The one
  exception is `RM-S-PLANT`, whose `Room.ceiling_lining` humidity liner replaces it over
  that room's own face.
- **THE WEST ATTIC IS A GUEST STUDIO AND A STAIR-HALL VOID.** `RM-A-WEST-UNFIN`
  was 598 sf of loft nothing used. It is now four things, and the fourth is the one to
  understand first:
  - **`FO-A-HALL`, x 10'-0"..18'-0", y 22'-6 3/8"..35'-5 3/8"** — ~109 sf of deck REMOVED, so
    the `ST-M2S` well and the hall band south of it run open from the second floor to the roof
    underside (9'-0" at the void's west edge, ~20'-4" at the ridge). Its four edges are each
    chosen against the resolver, and the two that get "tidied" if they are not read are **miny
    on the partition's north FACE** (on the axis the wall hangs 1.15" over the hole) and
    **`purpose=STAIR`, explicitly** — `code.R312_1_guard` filters on exactly that, and
    `code.R312_1_guard_height` never walks a void, so with `CHASE` this hole would get no
    fall-protection check at all. It passes on WALLS, not a railing. **Never add x=10' to
    `FS-ATTIC.joists.bearing_refs`** to "support" it: that field is global to the deck and
    would cut all ~34 joist lines there, including the 17 over the suite where nothing stands
    below, and `integrity.floor_bearing_grid` does not test across the joist axis.
  - **`RM-A-STUDIO`** — `Occupancy.BEDROOM`, **`floor_finish=None`**, the old room retagged in
    place so uid `CAR401AAAA` and its GlobalId survive. Bare sanded deck is the cheap answer
    and a spec rather than an omission (`FS-ATTIC` is `plywood-underlayment-sanded` *because*
    these rooms walk on it); the sealer is a `prices.toml` allowance and `floor_finish="carpet"`
    is the ~$1,200 alternative to put to the owner. BEDROOM is load-bearing four times: R310
    (PASSing on `WIN-A-S-JUL-W` with nothing added), the whole-house ventilation count,
    R314/R315, and `electrical.receptacle_spacing` evaluating the room at all.
    **R303.1 is answered by Exception 1, not by glazing** — **13.6 sf against 28.5 sf**
    (the four eave windows went with the knee walls), and no
    glazing is added because the south gable's mirror about x=18' is not negotiable and the
    only levers left are a shed dormer or a roof penetration, both excluded. **The studio's
    daylight dropped about a third and the owner should see that stated rather than discover
    it.** Legal, and unchanged in KIND from before — but the lumens below are doing more
    work than they were. Exception 1
    needs a fresh-air SUPPLY register in the room (`REG-A-HP-WEST`, re-pointed — **no
    mini-split**) and **lumens ≥ 12.5 × the room's sq ft**: 4,457 lm at 356.6 sf. Six cans plus
    the sconce give 6,000 lm = **8.08 fc**, chosen over five cans' 6.9 fc so the margin survives
    the room growing 30%. **A `LightRun` counts for nothing here** — `_room_lumens` excludes
    cove and tape by its own docstring.
  - **`RM-A-STUBATH`**, x 9'-10 7/8"..17'-8 5/8", y 17'-6 3/8"..22'-1 5/8", `vinyl-sheet`.
    **The tag is not `RM-A-STUDIO-BATH`, and that is not cosmetic**: `electrical.room_lighting`
    matches devices by `ED-{room.tag[3:]}-*`, so that name would prefix-match the studio and
    merge the two rooms' luminaire sets. **Both of its wall lines are chosen, not rounded:**
    x=9'-7 1/2" is `W-S-DC2`'s axis — the suite bath's staggered drain wall one storey down,
    5.5" of continuous cavity with **no stud to bore** — and y=17'-4" (208" = 13×16) is a joist
    line, so `W-A-BATH-S` gets a joist under its sole plate. All three fixtures take
    `wall_ref="W-A-STU-W"`, the shower included, and the vent **starts over the shower**:
    starting it at the wet-wall axis gives that fixture a 6'-7" trap arm against Table 1002.2's
    5'-0" for 2". **No `humidity_class`** — every other bath in the house is `NORMAL`, and `WET`
    would pull `ROOF` into the humid-room condensation walk for nothing.
  - **`RM-A-POCKET`**, x 0..9'-7 1/2", y 22'-4"..36' — `STORAGE`, bare deck, entered through
    `D-A-POCKET` in `W-A-STU-N`. **The door is in the SOUTH wall, not the x=10' one**: the far
    side of that wall is the void, a shaft. Its station is set by HEADROOM — the wall is raked
    at 5'-0" + x/3 and a 6'-8" head needs x ≥ 5'-9"; the first attempt put jacks and header
    through the raked top plate and `structural.member_interference` said so. It is a door
    rather than a scuttle because the ERV manifold, the OA hood and `VR-M-RADON-VENT`'s head
    all sit inside it and IRC M1305.1.3 wants a passageway, light and receptacle at the
    appliance (`ED-A-POCKET-LT1`, `ED-A-POCKET-RC1`).
    **It is 134 sf of floor and 6 sf of space.** RF-HOUSE's underside runs from 3" over the
    deck at `W-A-W1` to 5'-3" at x=9'-7 1/2", so almost none of it clears the 5'-0" that
    R304.3 makes floor area count. `ResolvedRoom.head_limited_area_m2` is the number the
    dashboard, the plan label and `haus build` now report beside `area_m2`; the whole attic
    reads 496 sf usable against 1,171 sf of built deck. **Every takeoff still reads
    `area_m2`** — the rake is sheathed and heated like anything else.
  - **Three walls SPLIT for it** — `W-A-C2` (twice, at N-A-BW-E and N-A-C3), `W-A-N2` and
    `W-A-W1` — because a partition teeing in mid-span leaves `resolve/topology.py`'s junction
    solver without a shared endpoint. In each case the TAG AND UID stay on the piece keeping a
    hosted opening. `W-A-STU-W`'s own north end is the exception: it dies into `W-A-STU-N`'s
    face 4 1/2" short of that wall's end, so **`N-A-WW-N` carries `open_end=True`** rather than
    splitting off a stub nobody can build. `RB-HOUSE.bearing_refs` names all FIVE centreline
    segments and `test_ridge_beam_depth.py` asserts the exact tuple.
  - **The ERV hoods LEFT THE GABLE ENTIRELY**, after two passes moving them
    along it to get the INTAKE off `FO-A-HALL`'s open well.
    The gable was never survivable: `DU-ERV-EA`'s 18'-0" leg at +23'-0" ran through the rough
    openings of **both** north-gable windows, 8" above a 22'-0" sill in a 25'-0" head, across
    2'-6" of each unit — and `CD-A-DATA-NE`, rerouted into the same band, crossed `WIN-A-N2`
    too. They are now stacked on the **west face at the NW chase**, intake at +4'-0" on main
    and discharge at +17'-0" on second. See `plan/mep_erv.py` and **Mechanical** below.
  - **`DU-A-ERV-R-BED3` and `CD-A-DATA-NE` both go SOUTH**, and there is no alternative: the
    void spans the full band to the north gable (`FO-A-HALL`'s maxy IS `W-A-N2`'s gwb face), so
    every west→east route north of the studio is severed. BED3 runs ~53'-6" —
    **which is fine, and length is not the
    criterion**: BED3 carries 5 cfm and PLANT carries 25, so PLANT is still the run whose
    pressure drop the installer must check, and PLANT is the longer run at 55'-8".
  - **The x=1'-0" chase is inside a finished bedroom, so the 6" left the room instead.**
    `DU-S-ERV-HP-FEED` (100 cfm, the mixing-box feed) sets the chase's section — wide enough
    that the first answer was a 21'-8" bench along the eave. **It turns east one bay sooner, in `y=22'-0"`** — the bay
    `DU-A-ERV-R-BED3` already uses, the last one south of `FO-A-HALL` — and reaches the same
    `SF-S-HP1` drop up `RM-A-EAST-UNFIN`'s deck (it was a `SF-S-DUCT` drop until the
    2026-09-04 HP1 move). `DU-A-ERV-R-STUBATH`'s east leg
    runs into the `y=19'-4"` bay rather than lying across 8'-7" of the
    studio's floor.
  - **`DU-A-ERV-R-PLANT` left too, and the eave line is bare.** It is `DU-M-ERV-R-PLANT` now,
    on the LEVEL-2 manifold: south through `FS-S-WEST`'s **open-web trusses** at x=2'-10",
    east along the y=4'-8" bay, then **up inside `W-S-C1`** to a high sidewall grille at 8'-6".
    Both floors span x, so a north-south run crosses every joist in either — but FS-S-WEST is
    truss, where crossings go through the webs, and `FS-ATTIC` is I-joist, where the same
    crossing at x=1'-0" means ~16 bored webs all within a foot of their west bearing.
    `W-S-C1` is `PLANT_INT_2X6_BRG_HUMID` (5 1/2" cavity, room for the riser **and** a
    vapour-tight boot); the room's north wall `W-S-PS1` is 2x4 and is not.
  - **The terminal is HIGH SIDEWALL, not CEILING, and that does not give up the height
    argument.** Humid air stratifies, so the extract must be in the warm wet air at the top of
    the room; 8'-6" is six inches under the ceiling. The argument was about height, not about
    which direction the boot arrives from. Separation from `REG-S-HP-PLANT` actually improves
    — and it improved again on 2026-09-04 when that supply moved from x=6'-8" to x=9'-4",
    giving 9'-2" across a 159 sf room.
  - **It is LONGER, not shorter — 55'-8" against 47'-5"** (9'-4" of that is the rise, which an
    eyeballed estimate misses). Affordable because **the machine's rating point is 0.4" w.g.,
    not the 0.2" several comments still quote**: HVI certifies the B210E75RT at 206 cfm net
    supply at 0.4" (HVI ID 2004940). It is still the radial whose drop wants checking, and it
    is the longest in the house again.
  - **`EQ-M-ERV-MAN-EXH` IS NOW FULL, 10 of 10.** The x=2'-10" lane was chosen, not inherited:
    going south there crosses exactly ONE sibling radial (`DU-M-ERV-R-BATH1`'s westward leg at
    y=24'-8"); the obvious lane at the manifold's east end would have crossed EIGHT.
  - **`AL-A-COMBO` moved to `RM-A-STUDY`, and `AL-A-STUDIO` is the new one.** Getting the pair
    round the wrong way is a FAIL, not a preference: `code.R315_co_every_sleeping_area` fails
    outright if every CO alarm on a storey is inside a bedroom.
  - ** THE ERV'S HEADROOM IS NEARLY GONE. ** The sixth bedroom took
    `code.N1103_6_whole_house_ventilation` to **210 cfm provided against 203 required**. A
    seventh bedroom, or ~250 sf more conditioned floor, fails it and wants a bigger machine.
- **`W-A-SN` IS A 12 3/4" BOOKCASE WALL, AND ITS SOUTH FACE IS PINNED**
  (`INT_2X4_BOOKCASE_12`). That face is the only thing covering `FO-A-STAIR`'s north
  edge: move the wall north and `code.R312_1_guard` FAILs with ~14'-3" of unguarded well.
  So the wall was **thickened, never moved** — the face stayed at 8'-9 5/8" and the depth
  grew north, which is the whole reason `N-A-C2`/`N-A-E1` sit at **y=9'-4"**
  (`105.625 + 12.75/2 = 112.000"`). Reaching y=9'-4" by MOVING a 4 3/4"
  partition (same axis, opposite meaning) FAILs the same check. Two rules follow:
  - **Do not split the wall** to give its west 1'-6" a thinner assembly — a 4 3/4" wall on
    this axis puts its south face 4" north of the well edge and re-opens the same FAIL.
  - **`interior_room="RM-A-STUDY"` is load-bearing on that `Wall`.** The stack-up is
    asymmetric (millwork south, gwb north); without it `orientation.wall_outward_sign` may
    put the gwb face on the well edge and the case pocket in the storage loft.

  **`RM-A-STUDY` grew 159 sf -> 165 sf, and that is the engine, not the geometry.**
  `resolve/rooms.py` builds a room's face from wall **centrelines** and then insets it by the
  room-wide lining thickness, so the study's north boundary tracks the AXIS — which moved 4"
  north — even though the wall's south face did not move at all. The built face is still on
  the well edge, which is why `code.R312_1_guard` (which reads the wall footprint union)
  still passes. R303.1 gets better, not worse: 21.3 sf of glazing against a 13.2 sf
  requirement. `RM-A-EAST-UNFIN` loses the same 6 sf and is `STORAGE`, where no glazing rule
  binds.

  The casework is **not** a placeable and must not become one: both catalog bookcases are
  1'-0" deep against a 9 7/8" pocket, so each would stand 2 1/8" proud — out over the well,
  the exact lie the built-in exists to avoid. Five bays from x=22'-8" stepping 7'-6" down to
  4'-6" under the rake, recorded in the `W-A-SN` comment and paid for by the
  `prices.toml [allowances]` lump `cabinet-study-bookcase-wall`. The BOM legitimately sees
  only the `case-back` sheet and the nailers. `D-A-STUDY` is hidden in the run as
  `DT-INT-BOOKCASE30`, a Murphy-style bookcase door — a **retype in place**, so it keeps its
  uid and IFC GlobalId. Its `trimless=True` means a millwork case, **not** the drywall
  return jamb it means everywhere else in this house; do not price it off the
  `DT-INT-SWING30-TRIMLESS` row.
- **THE ROOF IS FLASH-AND-BATT IN THE JOIST BAY, AND ALL NINE OUTSULATION LAYERS ARE GONE.**
  It was a vented batten roof, then a screwed nailbase
  stack: 1/2" taped ZIP -> self-adhered deck vapour barrier -> 3" + 3" polyiso -> 5/8" OSB top
  deck on 539 ten-inch SDWH screws -> vapour-permeable synthetic underlayment -> 1/4"
  ventilated mat -> metal. R-55.1 at 19.9" deep, to clear a code minimum of R-49.

  It is now **four layers and two bay fills**, R-53.2 at 13.1", 6.81" (perpendicular)
  thinner: **11-7/8" TJI 230 @ 24" o.c.** holding **5" of ccSPF against the deck underside
  with an R-30C batt compressed into the remaining 6-7/8"**, then **5/8" CDX plywood**, a
  **high-temp self-adhered butyl membrane over the whole deck**, and the same 24 ga
  mechanically-seamed standing seam. **The interior is still paint and nothing else.**
  `notes/roof_flash_and_batt.md` is the hand-worked oracle — R-value arithmetic, the deck-
  face dewpoint, the span reading and the site hold points — and is where to start.

  Five things to know before touching it, each of which reverses a rule this section used
  to state:

  - **It is legal with ZERO above-deck foam, by IRC/MSRC R806.5 item 5.3**: air-impermeable
    insulation in direct contact with the sheathing at the Table R806.5 R-value, with the
    air-permeable insulation directly under it. 5" of ccSPF is R-32.5 against R-25 (zone 6)
    and R-30 (zone 7), so the zone reading cannot go wrong. `code.R806_5_unvented_roof`
    grades it — a check that did not exist before, and one that PASSES the old stack too
    (via item 5.1, the 6" of polyiso above the deck), so it was not written to rescue this
    design.
  - **NO INTERIOR CLASS I VAPOUR RETARDER, EVER.** Paint on gypsum and nothing else. That
    was a design preference under the old stack; under R806.5 item 2 it is a code
    prohibition, and adding a ceiling poly or a vapour-barrier primer FAILS the check.
  - **The condensation gate now reports NOT_APPLICABLE on this roof, and that is the
    verdict, not a hole.** A steady-state Glaser walk cannot grade a stack sealed on its
    cold side by a 0-perm metal panel: with no outward flux it equilibrates every plane to
    interior vapour pressure by construction and reads ~100% RH at the deck for ANY unvented
    metal roof, however designed. The old stack bought its margin by leaving 5.6" of the bay
    deliberately unfilled as a drying path; this one fills the bay and changes the
    criterion. `condensation._r806_5_deferral` defers ONLY where the code check passes — an
    assembly whose foam is below the table, or is not Class II, keeps the Glaser gate and
    its FAIL.
  - **The vent mat and the permeable underlayment were ONE decision, and both are gone.**
    Above the underlayment sits an impermeable panel, so the only thing a 20-perm sheet
    could dry into was the gap the mat made; delete either and the other stops earning its
    cost. The membrane that replaced them is **butyl**, chosen for self-sealing around the
    ~1,160 standing-seam clip screws — which is this roof's real water risk. **Do not
    "restore" a permeable synthetic to save the difference**: it is a mechanically-fastened,
    non-self-sealing water layer under every one of those screws, with no drying path to
    show for it.
  - **24" o.c. forces the heavier joist, and the spacing is NOT FINAL.** At 16" the cheapest
    TJI in the line carries the 18'-0" HORIZONTAL span at Ps = 35 psf; at 24" the first that
    does with margin is the 230. `structural.rafter_span` is UNKNOWN/engineered at BOTH
    spacings and no sheathing-span or gypsum-ceiling rule reads the spacing at all, so the
    5/8" deck and the 5/8" ceiling board at 24" o.c. are on the PE, not on `haus check`. The
    printed TJ-4000 table also assumes bearing at the high end where these joists HANG off
    the ridge on 38 LSSR hangers — confirm in ForteWEB. Fallback: TJI 210 at 19.2" o.c.
    ** Budget for upsizing the eave uplift ties (H10A or equivalent) ** rather than banking
    the H2.5A count falling 378 -> 360: `H2.5A` is published at 700 lbf for SG 0.50 lumber
    and catlin frames SPF at SG 0.42, and the tributary rose 1.5x with the spacing.
  - **The deck OVERSAILS the last rafter and spans the wall girts.** It clips at the
    cladding's back face, not at the wall sheathing plane — with no foam or nailbase out
    there, the plywood is what the panel clips land on. That cantilever is graded by nothing
    in the engine.

  Cost: **-$12,200 to -$24,500** on the construction subtotal, of which $3,400-6,000 is a
  known phantom (roof sheathing is billed twice, in `envelope_layers` and again in
  `sheet_goods`; `also_in_sheet_goods` exists and `cli/prices.py::estimate_costs` never
  reads it). The honest saving is **$8,800-18,500**.

  The stack depth is transcribed by hand into `params/roof_trim.py` (`_DRIP_CEILING_IN`,
  `_CLADDING_HEAD_IN`) and into `test_catlin_eave_water.py`; move a layer and those move.
- **Structural ridge, not a rafter-tie roof.** `RB-HOUSE` bears continuously on the
  `W-A-C1/C1B/C2` bearing wall, which stacks unbroken to the footings. That is what makes the
  rafters simple spans and keeps thrust off the eave line. Opening that center line up
  without a beam under it dumps ~1.5 klf of thrust into a 1 1/2" rafter plate that can take
  none of it. **Its section is `2-1.75x16 LVL`, and the depth is a HANGER dimension**
  (`2-1.75x14` at 4:12, `3-1.75x11.875` before that). At 6:12 an 11 7/8"
  I-joist cuts 13.28" plumb and the face sits 1.75" off the peak plus 0.875" down the plane,
  so the beam has to reach **14.15"** below the ridge line — **14" misses by 0.15"** and 16"
  clears by 1.85". The beam hangs 16" into the room: ~9'-1 1/2" clear between beams,
  ~7'-9 1/2" under it. Because it bears everywhere it spans nothing, so ply count buys nothing;
  what sets the depth is the rafter's plumb cut, which the resolver hangs on the beam's FACE
  with the beam's top pinned to the roof plane. The same arithmetic at 4:12 gave 13.10" and
  put the answer at 14"; before that the beam reached 11.875", leaving the hanger seat and
  the bottom flange 1.52" past the soffit. LVL is made in 9.5/11.875/14/**16**/18"; there is
  no 14 1/4". Three things follow,
  and `notes/ridge_beam_detail.md` is where they live:
  - **3 1/2" wide is only available because the demand is small.** 28 rafter PAIRS land
    opposite each other and LSSR header nails are 2 1/2", so mirrored patterns overlap; the
    escape is ER-280 §3.2.2's NDS penetration reduction (~600 lb per rafter against 1,565 lb),
    which means a SHORTER header nail has to reach the schedule. A ridge sized by bending
    rather than by a plumb cut wants 5 1/4" and the full nail.
  - **The peak carries hardware the eave already had.** Beveled web stiffeners both sides at
    the ridge (38, derived — **23/32" ply ripped 4" wide, not a 2x4**: the cavity between web
    and flange is 15/16" a side and a stick does not go in it) and an
    LSTA24 over the top per pair (19), which Weyerhaeuser's H5S makes mandatory above 3:12.
    Plus 10 H2.5A tying the beam to its plate at 4' o.c. — that joint had NO connector and no
    uplift-path link at all, because `uplift.py` walks the roof's own `bearing_refs` (the
    eave line — the knee walls then, the rafter plates now) and `uplift_path.py` skips a
    `Beam.bearing_ref` that resolves to a wall.
  - **It is ordered as three 12s, not one 36' stick.** A beam supported everywhere splices
    over any bearing point, so `FramedMember.continuously_supported` (derived from the refs
    actually reaching) sends it to the stock ladder — same lineal feet, no offcut at 36', and
    a 106 lb ply instead of a 317 lb one (36' at 8.8 lb/ft/ply — this section's own weight,
    not `notes/ridge_beam_detail.md`'s 7.7 lb/ft/ply, which was struck for the retired 14"
    depth; scale by depth, width is unchanged. A 20' ply at the same rate is 176 lb).
    Every piece here, at any depth this beam has been, is a two-framer carry — **no ply of
    this beam has ever needed a crane, including the 36' one-piece alternative it avoids.**
    The cap is handling, not stock: `_MAX_SPLICE_PIECE_FT`
    in `takeoff/framing.py`. Stagger the plies (6+12+12+6 against 12+12+12).
    `structural.ridge_beam_depth` grades the depth; nothing did before.
- Window rules — **the RO ladder**. Three caps, one rule, and the rule is arithmetic on the
  16" module and a 1.5" stud rather than anything in the code book: *how wide can the RO get
  before it costs one more stud line?* `preferences.toml [framing]` holds the numbers and
  `structural.window_framing_module` enforces them.

  | RO | studs broken | why that width | what frames the head |
  |----|--------------|----------------|----------------------|
  | **14"** | 0 | one bay is `16 - 1.5 = 14.5"` clear | nothing — no header, no jacks, no kings; the bay's own two studs carry the rough sill and head nailer |
  | **30"** | 1 | kill one stud and its two neighbours leave `32 - 1.5 = 30.5"` clear | R602.7.4 lets a NONBEARING header be a single flat 2x4 nailed to the stud each side — no jack eats into the clear width |
  | **27"** | 1 | the same 30.5" less a jack each side: `30.5 - 2x1.5 = 27.5"` | R602.7.5 lands a BEARING header on a jack at each end, and each jack packs against its king |

  **The 3" between the 30" cap and the 27" cap IS the pair of jacks.** That is the entire
  reason the cap is a function of the wall's bearing status and of nothing else — same
  module, same stud, same single broken stud line; the only difference is whether the
  header needs something under its ends. 36" is the next rung up and it breaks **three**
  studs on a stud line (two on a bay centre), which is why the 42" WT-4248 sat on a bay
  centre until it was retired.

  R602.7.5 does also permit "approved framing anchors" instead of a jack, so a header
  hanger would buy the 3" back and put a 30" RO in a bearing wall on one broken stud. The
  house declines it — per-opening hardware and a detail the framer has to be told about is
  exactly the cost the preference exists to avoid — but it is a real option, not a fiction.
  If an opening ever needs it, raise `max_window_ro_bearing_in` deliberately and say so.

  **NOTE A MODELLING GAP:** the solver's `needs_jamb_pack` keys off *whether the RO breaks a
  stud*, not off the wall's `structural_role`, so it frames a king/jack/header pack on every
  stud-breaking window including the nonbearing 30" ones. The 30" cap is therefore correct
  about what is BUILDABLE and conservative about what the model DRAWS. Widening that gap is
  not the same as fixing it.

  **The ideal position is a
  property of the RO width, not of the wall** — narrowing a unit can move it, and
  `structural.window_framing_module` (asserted clean by
  `test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`)
  is what says so. Resize windows to fit the grid, not vice versa. One type per width
  family — WT-1424, WT-2736, WT-3036 (north gables/hall), WT-3048 (the south-glazing size,
  head at 6'-8") — each family sharing the one height that fits its most constrained wall.
  Five WIDTHS carry the whole house; the 27" family carries FOUR heights (36"/48"/54"/64")
  and the 14" family THREE (24"/36"/48"). **WT-2764 and WT-1448 are both CATALOG-ONLY**,
  since the attic's 6:12 rake shortened the juliets to WT-2754 and the gable
  flankers to WT-1436; WT-2464 is also catalog-only, having been an 18"
  WT-1864 family before. A retired size stays priced, which is the convention
  `glazed-green-brick` and `EXT_2X6_SWINBURNE` are also held under. The bearing
  cap is the width every bearing wall has to meet, so when an opening needs area, a head
  line or composition, HEIGHT is the only dimension left to spend. That is a consequence of
  the ladder, not a drift away from "one type per width family" — but the exception list
  below grows every time it happens, which is the honest cost of the rule.
  **Every window in the house is on its ideal station, and the exception list
  is empty.** The juliet family was the last holdout: it centred on a stud line at 18" wide,
  and widening it to 24" could only go outward — the 14" bearing pier under
  the ridge pins the inboard jambs — so each centre landed 3" off and
  `structural.window_framing_module` reported both. What ended it was not a fifth attempt at
  the width but the grid moving under it: with the exterior assembly laying out from the
  layout line, 16'-0"/20'-0" are stud lines, 5" further out, and the pair fits with no
  retype. `test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`
  asserts the empty list; keep it empty, and see **ONE GRID PER FACADE** under Facade rules
  before concluding a window cannot reach its station.
  **Six exceptions**, each an extra height on an existing width family because the rule's
  own remedy — give it its own width family — costs more than the extra height does. The
  first two are about a HEAD LINE; the next two are
  the 27" bearing cap being paid for in height (see the RO ladder above); the fifth is
  composition, on a NONBEARING wall; the sixth is the
  6:12 rake:
  - **WT-1448** (the south gable's flankers, now catalog-only): the rake
    forbids the remedy outright. Any width over 14" breaks a stud and takes a header, and
    the header is what hits the rake (the juliet family at the nearest usable stud line
    missed by 1.8" at 4:12). 14" fits in a bay and takes no pack, so only the glass has to
    clear.
  - **WT-1436** (the south gable's flankers): a THIRD height on the 14"
    family, and the 6:12 rake is the whole reason. `x_outer_jamb >= 2 x (head + 2")` gives
    WT-1448's 6'-8" head 13'-8" of required clearance, which the gable does not have at any
    station a mirrored pair could use; WT-1436's 5'-8" head needs 11'-8" and fits at
    12'-8"/23'-4" with 4" to spare. **It is also what keeps `RM-A-STUDY` on daylight**: at
    165 sf R303.1 asks 13.2 sf and one WT-1436 gives 13.625. Dropping to WT-1424 instead
    would save the type and push a habitable office onto R303.1 Exception 1's electric-light
    substitute — not a trade a high-performance house should make. Same 14" width family, so
    same buck, same header (none), same flashing: the SKU premium is near zero.
  - **WT-3048** (the south glazing): the 30" family's committed height (WT-3036's 36")
    would drop the south head off the 6'-8" door-head line the whole face is built on.
  - **WT-2748** (`WIN-M-EAST-MID`): the east living row's feature window had to
    come 30" → 27" for the bearing cap, and the 27" family's committed 36" would have
    dropped its head from 6'-8" to 5'-8". 48" makes the narrowing a pure retype — same
    2'-8" sill, same 6'-8" head, only the width moves. The cheapest of the four.
    **The datums are 2'-8"/6'-8", not the 2'-6"/6'-6" this entry claimed until 2026-09-06.**
    Commit `c2ed5b9d` ("Close the sunken garden's structural loop") moved all three east
    sills 2'-6" → 2'-8" in one silent hunk of a retaining-wall change, and every comment
    quoting the old pair went stale at once. **The row's head is therefore 6'-8" — the
    house's own door-head line** — which is a better fact than the one it replaced, not
    merely a correction.
  - **WT-2754** (`WIN-S-BED1`/`BED2`): the same 27" cap, but these are
    single-window BEDROOMS, so R303.1 binds on area and 27x48 is 9.00 sf against BED2's
    9.945 sf requirement — it would FAIL. 54" is the height that makes 27" legal
    (10.125 sf), which is why this one is a code necessity and not a composition choice.
  - **WT-2764** (`WIN-A-S-JUL-W`/`-E`, catalog-only — at
    6:12 the rake gives 7'-6 3/4" over the outer jambs and a 64" unit on the gable's 2'-8"
    sill wants 8'-2", so the pair retyped to the width-identical WT-2754): the only one of
    the six that is a
    composition choice outright, and the only one on NONBEARING walls (W-A-S2/W-A-S3, cap
    30"). The juliet pair had to grow to close the gap between the two units without moving
    either centre off its stud line; 27" is what closes it to a 21" pier with the bearing
    point still covered, and 64" is the height the pair has carried. A
    fourth height on the 27" family rather than a sixth width — same trade as the others.
- Facade rules. Windows line up or they are not there:
  - **ONE GRID PER FACADE. The residue rule is dead — read this instead.**
    `EXT_2X6` and `PLANT_EXT_2X6_HUMID` both set `layout_origin="line"`, so a wall
    segment lays its studs out from its **layout line** — the derived chain of collinear,
    stacked walls (`resolve/layout_lines.py`) — not from its own start node. Every segment
    on a facade, on every storey, is therefore on one 16" grid measured from the house
    origin. **A window's legal stations are now a property of the facade, and moving a node
    no longer re-phases anything.** Stations are absolute: x (or y) ≡ 0 mod 16" is a stud
    line, ≡ 8" a bay centre.
    - What this retired, all of it the same defect in different costumes: node moves made
      purely to buy phase (N-A-V1 to 22'-8" for the south gable; four more in the
      E/W pass); the "spent" 31'-4" west column; the east knee band's 4" miss;
      the north gable's asymmetry; and the juliet pair's accepted 3" off-module exception.
      All five dissolved when the grid was unified, at a cost of 20 windows moving 3"–8".
      **`test_catlin_contract_m3.py::test_catlin_window_openings_follow_their_walls_framing_module`
      now asserts an EMPTY exception list.** Keep it empty.
    - **The 8" rule survives, and is now the only phase rule left.**
      `structural.window_framing_module` puts a 14" RO on a **bay centre** and a 27"/30" RO
      on a **stud line** — 8" apart on the one grid. So a 14" unit still cannot column with
      a 27" unit, anywhere on the house, and retyping the narrow unit is still the answer
      (WIN-M-BATH2). This is no longer a per-segment accident to be worked
      around; it is a property of the two widths and it is permanent.
    - **A node move is now cheap and a window move is now global.** The old warning was
      "price a node move before making it". The new one is its mirror: a node may move
      freely, but a window that moves off the grid stays off it, and a facade whose windows
      disagree with the grid can no longer be blamed on authoring order.
    - **A tee is not a wall end, second half of the same fix.** Unifying the
      module was necessary and was not sufficient: each of the six or seven segments a facade
      is authored as still framed its *own end stud* where it met the next, so every seam
      carried two sticks in the same 1-1/2", off the module, at a station the storey above
      split somewhere else. Those seams are gone — where two collinear segments provably
      share one grid, `framing/solver.py::continuation_roles` drops both end studs and lets
      the module run through, one `"owner"` claiming a seam that lands on the grid. The same
      reading now runs the **stand-off band** (`framing/furring.py`), which is the line the
      cladding lands on.
      **The catlin truss turned that band on its side and the reading followed it there**:
      `_furring_module_signature` carries `direction`, so a HORIZONTAL band
      continues through a seam too. Without it every tee in a facade would put a 3" notch in
      every girt course — a course is one stick on the job, and the seam is an artifact of
      where the partitions land inside. What phase-locks to the stud grid is now the girts'
      **blocks**, one under every course on every OTHER stud — **a 32" grid**,
      phase-locked to the layout line at 32" rather than at 16".
      `test_catlin_contract_m3.py::test_each_facade_block_grid_is_one_grid_on_every_storey`
      and `::test_no_facade_stud_stands_off_the_module_except_at_a_corner` pin it, per facade.
      The only members left off the grid are the corner packs (identical on every storey) and
      the jamb packs, which sit where their rough openings put them and always did.
    - **AND THE INSIDE OF THE HOUSE, TOO.** The two
      rounds above were both about facades, and the house is not a facade. Five interior
      bearing assemblies now set `layout_origin="line"` on their STRUCTURE layer:
      `INT_2X6_BRG` and `PLANT_INT_2X6_BRG_HUMID` (the x=18'-0" **centreline**,
      `W-M-C1..C5B` / `W-S-C1..C4B` / `W-A-C1..C2`), and
      `STAIRWALL_INT_2X6_BRG`, `STAIRWALL_INT_2X6_BRG_TYPEX`,
      `MUDROOM_INT_2X6_EXPOSED` (the **stair line**, `W-B-STR/STR2/STR3` under
      `W-M-STRW/STRW2`). The centreline is the one that actually matters: it is what carries
      `RB-HOUSE` continuously to the footings, so a continuous load path is worth more there
      than on any facade. **No code compels it**, and an earlier draft of this passage wrongly
      said one did: R602.3.3 is the *bearing-stud* rule (a joist, truss or rafter landing
      within 5" of a stud, and only where both runs are 24" o.c.), R602.3.2's single-top-plate
      exception is about rafters/joists centred over studs within 1", and in-line framing is
      an APA Advanced Framing technique. `model/assembly.py`'s `layout_origin` note had this
      right all along. It used to run
      three storeys on three different phases, each of its twelve segments restarting the
      module at its own start node.
      `test_catlin_contract_m3.py::test_the_centreline_bearing_wall_is_one_stud_grid_on_every_storey`
      pins it, and `::test_upper_storey_studs_stand_over_studs` pins the whole house — 94 of
      237 stacked upper-storey studs still stand over nothing, down from 113, and that is a
      **ceiling, not a target**: a module stud suppressed under a window on one storey and
      not the other, and jamb packs at differing stations because the windows differ, are
      both correct framing and neither will ever go to zero.
      - **STRUCTURE spec only, unlike the exterior pair.** An interior wall has no vertical
        FURRING band to phase-lock to the studs — both liner bands here are
        `direction="horizontal"` and `furring._layout_horizontal` takes no phase — so the
        paired stud+outrigger opt-in the facades needed has nothing to pair with.
      - **The honest caveat: "stacked" is not "on the house grid".** `layout_lines._orient`
        puts a line's origin at its extreme member end, not at the house origin. The
        centreline chain happens to end at y=0, so its grid *is* the house's 16" grid — by
        luck. `LL-W-B-STR` starts at y=216" and its grid sits 8" off. Interior studs stack
        storey to storey, which is what was asked; do not read more into it than that.
      - **Not opted in, deliberately.** `INT_2X4_PARTITION` and the other non-bearing
        partitions (~46 walls) — bearing lines first. And the *staggered* assemblies, which
        must not be widened into without reading `plans/TODO.md` first:
        `framing/solver.py`'s face-parity rule rounds a station to decide which face a stud
        sits on, and at a phase near 4" or 12" banker's rounding collapses it into runs of
        same-face studs, destroying the acoustic decoupling. It cannot fire while every
        staggered wall has phase 0.0, and a non-zero phase is exactly what opting one in
        would hand it.
  - **Columns.** The south face stacks its columns through main and second at
    x 4'-0" and 32'-0"; the second storey adds 9'-4" and 26'-8" where main has none.
    **Both storeys are mirror-symmetric about the x=18'-0" ridge** — main reads
    4'-0" / 14'-8" / 21'-4"(door) / 32'-0", second reads 4'-0" / 9'-4" / 14'-8"(door) /
    21'-4"(door) / 26'-8" / 32'-0", and every one of those pairs sums to 36'-0". The east
    pair came 8" *inboard* to get there, which was the choice the unified
    grid opened up: the nearest legal station was 8" the other way, and inboard bought the
    mirror for the same 8" (they had been 27'-4"/32'-8" before, when the glazing
    narrowed to WT-3048). The attic does not join them — see **Gables**.
    The **west face stacks FIVE** through main and second (y 5'-4", 10'-8", 20'-0",
    24'-8", 31'-4"), the four lower ones having shifted 4" together when the
    face re-hung on the house grid. The first three use the 27" family on a 3'-0" sill; the
    fourth pairs tempered 14" awnings in RM-M-BATH1 and RM-S-VANITY on a 4'-0" sill; the
    fifth pairs WIN-M-MUD with WIN-S-BATH-W. All share one 6'-0" head line.
    WIN-M-BATH2 was retyped WT-1424-T -> WT-2736-T at a 3'-0" sill to reach the third
    column (the 8" rule), which also buys R303.3's window alternative outright.
    **The fifth column was recovered**, having earlier been spent: the
    second storey's mechanical chase took its south corners 3 1/8" south so its face lands
    on FX-S-BATH1-SH's apron line, N-S-CH3 moved with them, and W-S-W1's grid re-phased out
    from under WIN-S-BATH-W, which rode south to the bay centre that move created. With one
    grid per line there is no per-segment phase left for a node move to disturb, so the
    window returned to 31'-4" under WIN-M-MUD and the chase kept its 3 1/8".
    The 10'-8" suite header used to cross the top ladder-backing rung at W-S-W3's tee, and
    the solver omitted that one nonstructural rung; the 4" the window moved took the header
    off it and **the backing is complete again**. The west attic pair sits at 4'-8" /
    31'-4", symmetric about y=18'-0"; it caps the outer lower-floor groups without
    introducing another width family.
    **The north face has no column any more, and that was a trade taken on purpose.** It
    stacked one at x=29'-4" (WIN-M-KITCH / WIN-S-HALL-N, moved there from x=28'-0") to bring
    WIN-M-KITCH onto FURN-M-KIT-SINKBASE below; it was a three-storey column until the 6:12
    rake pulled `WIN-A-N2` off 29'-4" and inboard to the gable (see **Gables**), leaving a
    two-storey stack. On **2026-09-06** `WIN-S-HALL-N` moved west to 24'-0" and the stack
    went too. What it bought is the whole upper facade: all four upper windows now sit on
    one rectangle — `WIN-A-N1` / `WIN-S-STAIR-N` at **12'-0"** and `WIN-A-N2` /
    `WIN-S-HALL-N` at **24'-0"**, each attic unit stacked EXACTLY on its second-storey
    partner and the pair mirrored about the 18'-0" ridge. `WIN-M-KITCH` stands alone below;
    it cannot follow, being dead-centred on the sink run. **A rectangle of four beat a
    column of two here — that is the precedent, not a general rule.**
    The face got a column back the same day, at the other end and for a different reason:
    `WIN-S-BED3-N` (WT-1424, x 34'-0", sill 4'-0") sits directly over `WIN-M-KITCH-N`,
    taking its `from_node("N-?-NE", ft(1, 5))` offset verbatim off the storey's own NE node.
    It is there to complete a **corner pair** — with `WIN-S-BED3` on the east wall at
    y=34'-0" it wraps the north-east corner the way `WIN-M-KITCH-N` / `WIN-M-KIT-E` wrap it
    below, each unit 2'-0" off the corner — and the two-storey column is what that buys on
    top. It also took `RM-S-BED3` off R303.1 Exception 1 (12.2 sf glazed / 6.1 openable
    against 10.32 required), which the withdrawn 23'-4" unit had also done and the moves had
    given back. **Where a shortfall and a composition want the same window, take both.**
    The sink is the harder-pinned of the two: its counter run is
    exactly full (5/8" scribe + B15 + DW + SINK-36 + B30, pantry wall to corner, no slack
    to slide it), while the window has 16" stations to choose from — so the column moved to
    the sink rather than the other way round. See `plan/placeables.py`'s kitchen header.
  - **Rows.** Where a column is impossible, the storey's own rhythm wins instead — but a
    row must be *centred*, not merely even. The east second storey ran a perfect 9'-0" beat
    that used to sit 10" north of the centreline (5'-4" of wall south, 3'-8"
    north); it now reads 4'-0" / 13'-4" / 22'-8" / 32'-0", exactly mirrored about y=18'-0"
    in station, width (27/30/30/27) and head (6'-0"/7'-0"/7'-0"/6'-0") over one 3'-0" sill.
    **It is even as well as centred** — a 9'-4" beat three times over,
    where 4/13/23/32 used to be 9'-0"/10'-0"/9'-0". The inner pair moved 4" outward onto the
    unified grid and the row got the thing it had been trading away. Centring it first
    took N-S-E2 to 17'-8" and N-S-E3 to 26'-8" to buy phase, and the
    bedroom bays became 8'-8"/9'-0"/9'-4" to pay for it, shrinking BED1 (whose R303.1
    margin is 0.05 sf) and growing BED3 (which has two windows). Those node positions are
    now incidental — the grid no longer depends on them — but the room sizes they set are
    real and still govern.
    **The east MAIN row reads 4'-0" / 13'-4" / 18'-8" / 34'-0", and the last of those is
    the blank kitchen stretch being deliberately ended.** (`WIN-M-LIV-E2` moved 12'-0" →
    13'-4" on 2026-08-27, one stud line north, so it stacks under `WIN-S-BED1`; this bullet
    said 12'-0" until 2026-09-06.) N-M-E1 and W-M-E2 went when the wall was
    merged for WIN-M-EAST-MID, and WIN-M-DIN-E2, the window the blank was measured north of,
    was retired with them. **Look at `out/render/elev_east.png` before touching this.** What
    the row now does, and what it costs: the first three are the row proper — three 27"
    units on one 2'-8" sill and one 6'-8" head — and WIN-M-KIT-E is a 14" unit at a 3'-6" sill, so it
    joins neither the beat nor the head line. It reads as a smaller service window closing
    the row at the north end rather than as a fourth beat, which is the honest description
    and was the trade: the kitchen wanted a second window over its counter more than the
    facade wanted 16'-0" of unbroken wall. It is on a bay centre (408" off N-M-SE, 8" mod
    16") so it breaks no stud and takes no header — see the 8" rule above for why a 14" unit
    can never column with the 27"/30" family beside it. WIN-S-STUDY3 at 4'-0" still columns
    with WIN-M-LIV-E1.
    **2026-09-06: the pier between `WIN-M-LIV-E1` and `WIN-M-LIV-E2` is now the fireplace.**
    A 45 1/2" white-facebrick surround centred on y=8'-8", stopping at a
    walnut mantel at 5'-4", with the eight BESTA units re-laid three south and five north of
    it and the seating turned onto it. **No window moved for it** — the 27" ROs and the
    4'-0"/13'-4" beat are untouched, and the pier centre is a bay centre on `W-M-E1`'s own
    grid. The 2'-8" sill IS the firebox opening's bottom, so one datum serves four openings.
    `notes/east_breast_bearing.md` carries the bearing and the floor opening; nothing in
    `haus check` grades either.
    - **IT IS FIVE WALLS, NOT ONE, AND THE FIREBOX IS A REAL VOID.** `W-M-FIRE-STUB` /
      `-PLINTH` / `-JAMB-S` / `-JAMB-N` / `-HEAD`, all `FIREPLACE_BRICK_WYTHE`, all NONBEARING,
      stacked on the x=35'-1 11/16" axis with **its own `open_end` node pair each** — a stacked
      run sharing a node collapses every junction polygon it touches. A single Wall resolves to
      a 4-point rectangle and there is no `voids` path on a Wall short of a Window or a Door,
      both of which would be lies about a firebox, so the **29 1/2" x 20 5/8" masonry opening
      (sill 32" AFF, head 52 5/8" AFF)** is the gap between the elements rather than a
      subtraction from one. `base_elevation` is absolute and `top` is a HEIGHT off it, so both
      are worked from the +15/16" finished floor: STUB -13 7/16"→+15/16", PLINTH →32 15/16",
      the two 8" jamb piers →53 9/16", HEAD →64 15/16". The visible 45 1/2" and its **zero cut
      closers** (29 1/2" + one whole brick and one head joint each side) are untouched, and the
      opening's head is a deliberate CUT COURSE at 19.7 courses — on a course line it is
      21 1/3" and leaves ~1" of daylight over a trimless unit. Steel angle lintel, not a
      rowlock. **The brick quantity falls 24.8 → 20.4 SF and the $/SF rate deliberately does
      not** — a mason bills the panel on a job this small, and re-rating down would deduct
      twice.
    - **`FO-M-FIRE` is 47 3/4", not 4'-1".** 44 1/4" of stub (1 1/4" narrower than the panel,
      the plinth corbelling 5/8" over it at each end under the lvp) plus 1/2" of mason's
      clearance and one trimmer ply each side. Deliberately not 48.0": `header_size` branches
      on `w_ft <= 4.0` and a span arriving as 4.0000000000000009 after a metre round trip takes
      the wrong branch silently. **The old "this crosses IRC R502.10's 4'-0" line" note was an
      erratum twice over** — `haus check` grades floor-opening headers at EIGHT feet, and
      R502.10.1 is a sawn-lumber rule the engine now gates on a sawn joist profile, so this
      I-joist opening draws the same doubled trimmers and 2-ply LVL header at any span.
    - **The mantel has a body: `FURN-M-FIRE-MANTEL` / `FT-MANTEL-WALNUT-46`.** A
      `ResolvedShelfBank` carries no position and no emitter reads `model.shelf_banks`, so
      `SB-M-FIRE-MANTEL` was a cut list and nothing else — absent from the 3D and from every
      clearance check. It hangs off a wall-mounted placeable now (the `FURN-B-PLAY-TV` idiom),
      45 1/2" x 11 1/2" x 2 1/4" resolving 64"–66 1/4" AFF on `W-M-FIRE-HEAD`'s top, and the
      bank's `depth` is DELETED so `_carcass_depth_m` inherits from the type. **`Mount.elevation`
      is measured off `room_floor_elevation`, which is the SUBFLOOR datum, not the finished
      floor** — hence the authored 64 15/16" for a 64" AFF shelf; 64" would bury it 15/16" in
      the brick at 0 FAIL. `work_surface` is left UNSET, not False, to keep it out of NEC
      210.52(A)'s wall-space rule entirely. Its money moved with it: `[allowances]
      finish-fireplace-mantel-walnut` is **deleted** (not zeroed — both would bill it twice)
      and `[placeables] "FT-MANTEL-WALNUT-46"` carries the same scope, because **an unpriced
      type is silently dropped from the bill**.
  - **Knee band — GONE.** The east and west knee walls each carried a WT-1424
    pair, mirrored at 3'-4" / 32'-8"; the walls are 1 1/2" rafter plates now and a plate has
    nothing to glaze, so `WIN-A-W-S`, `WIN-A-W-N`, `WIN-A-E-S` and `WIN-A-E-N` are all
    deleted. That is where most of the ~572 sf of deleted `EXT_2X6` goes, and with it
    four units, four bucks, four flashings and eight jamb returns. The east/west facades now
    stop at the second storey — `test_each_facade_block_grid_is_one_grid_on_every_storey`
    expects two storeys there and three on the gables. **The stair well's east edge lost its
    guard with the wall**, and `code.R312_1_guard` said so immediately: `RL-A-STAIR` gained a
    3'-0" east leg, which is the honest price of the deletion.
  - **Head lines.** The west face puts every main and second head on one 6'-0" line —
    27" units at a 3'-0" sill, 14" units at 4'-0". The south face shares a 2'-8" sill.
    **The north second storey joined that 6'-0" line on 2026-09-06**: `WIN-S-HALL-N` and
    `WIN-S-STAIR-N` are WT-3036 at a 3'-0" sill and `WIN-S-BED3-N` a WT-1424 at 4'-0", so
    all four of that storey's north windows head together. `WIN-S-BED3` around the corner
    is at 4'-0" as well — **its own source note in `second.py` claimed 3'-0" until
    2026-09-06, and the authored value was `ft(4)` the whole time.** It left the east
    face's 3'-0" datum (which `WIN-S-BED1` / `WIN-S-BED2` still hold) when it was retyped
    down to a 14" unit, which is the rule working, not an exception to it.
  - **Gables** read symmetric about the ridge before they answer to anything below,
    and that symmetry is what the north pair is aimed at second, not first. **The north
    gable is symmetric** — WIN-A-N1 moved 7'-4" -> 8'-0", mirroring WIN-A-N2 at 28'-0"
    about x=18', then to **6'-8" / 29'-4"** when the three-storey column moved to bring
    WIN-M-KITCH onto the kitchen sink below (see **Columns** above), WIN-A-N1 moving
    with it to hold the mirror about x=18'-0". Then the rake moved it again: WT-3036 on
    the gable's 2'-0" sill puts the head at 5'-0", which needs 2 x (60 + 2) = 124" of
    clearance to the outer jamb, and 6'-8" gives 65". That landed the pair on
    12'-0" / 24'-0". It went one bay further in to 13'-4" / 22'-8" (2026-09-03) and
    **came back out to 12'-0" / 24'-0" on 2026-09-06, where it is now.**

    **The return outboard is what squares the facade.** With `WIN-S-STAIR-N` moved to
    12'-0" and `WIN-S-HALL-N` in from 29'-4" to 24'-0", both gable units stack EXACTLY on a
    second-storey partner and the north face reads as one rectangle of four (see
    **Columns**). 144" and 288" are stud lines, which is what a 30" RO must have — it
    breaks studs, so it cannot take a bay centre the way the 14" family does — and they
    mirror about the 18'-0" ridge.

    **The rake is binding at this station and holds by 5".** The outer jambs land 129" from
    their eaves against the 124" the 5'-0" head needs (the 145" once quoted here was the
    slack the inboard 13'-4" / 22'-8" pair had). `structural.truss_wall_opening_support`
    confirms both jamb pairs still bear on an outrigger within 1", but there is no third bay
    outboard: **this pair cannot move out again without a shorter unit.** Two other things
    tightened with it and are the numbers to re-check before any further move — the radon
    riser is now 9 5/8" clear of `WIN-A-N1`'s west jamb rather than 2'-1 5/8"
    (`mep_venting.py`), and the PV junction box 5" clear of its framing bumper
    (`electrical.py`).

    A fourth window (`WIN-S-BED3-N`, a WT-1436 at x 23'-4") was built on 2026-09-06 to fill
    the lower-east corner instead, and **withdrawn the same day in favour of the moves
    above** — 23'-4" was the only station the module and node `N-S-B5` allowed, 8" off the
    ideal and aligned with no column. Its one lasting mark is in `placeables.py`:
    `FURN-S-BED3-WARD` and `FURN-S-DESK3` swapped slots to clear the north wall, and the
    swap is still needed, because the wardrobe stood over x 22'-1.5"..24'-1.5" and
    `WIN-S-HALL-N`'s new RO is 22'-9"..25'-3". The tag itself was reused within hours for
    the WT-1424 at x 34'-0" that stands now (see **Columns**), on a different wall of the
    same room and a different argument entirely.

    This passage said the stair window was at 12'-8" and argued an 8" miss until 2026-09-06;
    it never was — the authored offset always resolved to 13'-4", and correcting that prose
    moved nothing. The move to 12'-0" is a real one.
    `WIN-A-N1` rehosted W-A-N2 -> W-A-N2B on an earlier move and stays there: its RO runs
    10'-9"..13'-3", clearing the x=10'-0" split by 9". At x=12'-0" it fronts `FO-A-HALL` and
    daylights the double-height stair void rather than a room, which is an amenity and not a
    code problem.

    **The south gable carries FOUR openings** (used to be six), exactly mirrored
    about x=18' and reading west→east as S2, JUL-W, JUL-E, S3. The tags gap at S1/S4 rather
    than renumbering, because renumbering would break the surviving units' GlobalIds:

    | station | tag | type | head | outer jamb | allowed | margin |
    |---|---|---|---|---|---|---|
    | 12'-8" / 23'-4" | `WIN-A-S2` / `WIN-A-S3` | **WT-1436** (14x36) | 5'-8" | 145" / 144" | 140" | ✓ 4" |
    | 16'-0" / 20'-0" | `WIN-A-S-JUL-W` / `-E` | **WT-2754** (27x54) | 7'-2" | 178 1/2" | 176" | ✓ 2 1/2" |

    One 2'-8" sill under all four, heads stepping with the rake. The corner pair
    (`WIN-A-S1`/`S4` at 3'-4"/32'-8") died outright — 21 1/2" of roof over the floor there.
    The flankers moved inward AND shortened, WT-1448 -> WT-1436; the juliets are a
    width-identical retype, WT-2764 -> WT-2754, so the centres, the `from_node` offsets and
    the 21" clear pier under `RB-HOUSE`'s south bearing point are all untouched.

    The juliet centres were 16'-8"/19'-4" before a widening pushed each unit 3"
    outward onto a non-module station — the house's one accepted off-module pair — then 5"
    further out, where the unified grid puts a stud line and the exception
    ends. A further widening 24" -> 27" grew each unit 1 1/2" PER SIDE, so the
    centres did not move at all; the clear bearing pier closed 24" -> 21", against a 14"
    requirement. That is still spent slack, not a new constraint.

    **The gable's corner pair (`WIN-A-S1`/`S4` at 3'-4"/32'-8") is deleted, and its 8" column
    miss (against the 4'-0"/32'-0" column the storeys below stack) is permanent.** At 6:12
    there are 21 1/2" of roof over the floor at x=3'-4"; it does NOT cap that column and
    never can: a 14" RO must sit on a BAY CENTRE (8" mod 16") and every south
    column below is on a STUD LINE. **Do not "fix" that 8" by moving these two** — it trades
    a clean framing module for a header the rake will not take.

    The mirror about x=18' is the rule that actually governs a gable and is the one thing
    that survived every one of these positions. Mirroring the east half once required moving
    N-A-V1 from 22'-4" to 22'-8", because W-A-S4's bay centres were then 4" out of phase
    with a mirror of W-A-S1's; that node no longer sets any grid, so the move is now only a
    wall-segmentation choice.
  - WT-1424 still does the work wherever a bigger unit will not fit — chiefly the mudroom.
    It used to do it in the 5' knee walls as well, where its 2'-0" height was the only one
    that cleared the plate; those walls are 1 1/2" rafter plates now and carry
    no glazing at all. Under the south rake it handed off first to WT-1448, then to WT-1436.
  - **Tempered twins.** `WT-1424-T`, `WT-2736-T`, `WT-3036-T` and `WT-3048-T`
    are their parents in every dimension and differ only in the glass, for the ten units
    R308.4 puts in a hazardous location (a wet room, within 24" of a door, within 60" of a
    stair). They are **not** width families and no facade or framing rule sees them: adding
    a tempered unit is a retype, never a move. All three glazed *door* types are tempered
    outright — R308.4.1 has no location test to fail.
  - **~~The east bearing wall now takes a 30" RO~~ — REVERSED, and the reversal
    is the more useful half of this entry.** `WIN-S-BED1`/`BED2` used to carry a
    30" RO in a BEARING wall with `max_window_ro_bearing_in` set to 30 to allow it. The
    reason given was: R303.1 wants 9.95 sf of glazing, a 27x36 gives 6.75, and *"27" cannot
    reach it at any height that fits under the 9'-0" plate."*

    **That last clause was never checked, and it is false.** R303.1 binds on AREA, and area
    is width × height — so the cap on width is only binding if height has run out, and here
    it had not. 27x54 is 10.125 sf / 5.063 sf openable, which clears BED1 (119.66 sf, needs
    9.573/4.786) by +0.55/+0.28 and BED2 (124.32 sf, needs 9.945/4.973 — the binding room)
    by +0.18/+0.09 — **wider margins than the 30x48 it replaced** (+0.43/+0.21 and
    +0.055/+0.027). On the shared 3'-0" sill its head lands at 7'-6",
    leaving 18" to the 9'-0" top of wall; the built framing puts a 2-2x8 header at
    7'-6"→8'-1¼" under a plate whose underside is 8'-9", so **7¾" of cripple is left over**.
    There was never a plate conflict to design around.

    Both rooms are `WT-2754`/`WT-2754-T` now, the preference is back to **27**, and the east
    bearing wall keeps the same rule as every other bearing wall in the house. The general
    lesson is the one the original note itself half-stated — *"the answer then is a taller
    unit, not a wider one"* — it simply never tried one. **When a dimensional cap looks like
    it forces a code failure, check the other dimension before moving the cap.**
- **The ERV is a Broan B210E75RT on a semi-rigid radial install, and three facts about it
  must stay true** (`plan/mep_erv.py`).
  - **The manifolds map to CAVITIES, not storeys, and there are exactly three.** Level 1 is
    the basement ceiling at the machine in RM-B-FURNACE; level 2 is RM-M-MECH, which feeds
    main-storey CEILING grilles *and* second-storey FLOOR boots because both open into the
    one FS-S-WEST/EAST cavity; level 3 is the FS-ATTIC deck at the chase head. A terminal is
    fed from whichever cavity it sits in — moving a terminal between storeys is free, moving
    it between cavities is a new radial off a different manifold.
  - **The machine cannot go back north.** It sits at (3'-11 1/2", 30'-6"),
    12 5/8" south of where a UI drag left it, because `EQ-B-ESS-BATT`'s 36" REQUIRED
    separation zone (x 49 1/4"..145 1/4", y 378"..460") reaches into the furnace room and
    `advisory.ess_clearance` grades it as a RECTANGLE, not a radius — at the old station the
    Broan's north-east corner stood 35.5" away and failed by half an inch. The y=30'-6" line
    leaves 1 1/2" of clear and also takes the case out of `ED-B-BACKUP-ENCL`'s 36" NEC
    110.26 working space. Nothing downstream is anchored to the machine — every branch comes
    off the two manifolds — so the move cost nothing, and moving it back would cost a FAIL.
  - **The radon/plumbing chase at (1', 34'-6") is the only riser, and it is full.** Four
    6" insulated ducts share it with six plumbing vents, `VR-M-RADON-VENT` and eight
    conduits: a row of three at y=33'-7 1/2" and a fourth at (5", 35'-6"), ~25% fill of a
    30 1/8" x 32 3/8" shaft. The arrangement is in `plan/mep_erv.py` and **nothing else
    should be added to that chase.**
  - **The two outdoor hoods are STACKED on the west face at the NW chase**:
    `EQ-M-ERV-HOOD-OA` intake at (0'-0", 33'-11") +4'-0", `EQ-S-ERV-HOOD-EA` discharge at
    (0'-0", 34'-8") +17'-0". 13'-0" apart, **exhaust over intake**, both south of
    `TR-RF-LEADER-W` at y=35'-6", on a facade that is blank on both storeys.
    - They used to be on the north gable at 8'/28', and the argument for the gable did
      not survive measurement. It said "RM-M-MECH is 5'-11" x 2'-7", so no pair of hoods near
      the shaft can make ten feet" — the room is really **5'-3" x 1'-11"** (`resolve/rooms.py`
      polygonizes from wall AXES and insets only by the lining, so an exterior-wall room reads
      6" past its own interior face), and the conclusion was only ever true of a HORIZONTAL
      pair. It also said the main storey was too low at "20"-34" above grade" — that is the
      13 7/16" RIM BAND, not the 10'-0" wall; the interior band is 2'-10"..11'-10" above grade.
    - **Vertical separation is what makes it legal, twice over.** `mep.erv_outdoor_terminals`
      measures a 3-D distance, and 13'-0" of rise clears its 10'-0" alone. Independently, IRC
      M1506.3 waives the ten feet outright "where the exhaust opening is located not less than
      3 feet above the air intake opening" — the engine does not implement that exception and
      does not need to here, but it is why the exhaust is the UPPER one and must stay so.
    - Cost: **−52.6 LF** of R-8 wrapped 6" duct (`DU-ERV-OA` 32.3→8.3, `DU-ERV-EA` 49.6→21.0),
      because both used to climb 24'-6" to the attic. It also empties the chase above the
      second storey, where four ducts used to run and now two do.
    - A 6" duct with R-8 wrap is ~8" OD against a 5 1/2" stud cavity, so **neither hood may
      turn and travel inside the wall** — each is a straight through-wall penetration. That is
      the one part of the old west-facade objection that stands, and it only bites a run that
      travels ALONG the facade. Coming straight out of the chase, neither does.
    - The gable mirror about x=18'-0" no longer applies to the hoods (it is a facade rule for
      a gable, and they are not on one). `test_catlin_erv.py` now pins the stack order instead.
- **A duct or a machine inside a modeled `Soffit` NAMES IT, and the clear section is
  DERIVED.** `DuctRun.soffit_ref` and `Equipment.soffit_ref` mirror `floor_ref`;
  `mep.duct_soffit_occupancy` derives the cavity from the soffit's own drop, `FramingSpec`
  member and 5/8" lining and measures everything claiming it side by side with a 2" hanger
  gap. **Never author a clear width** — it is a second source of truth for a number the
  framing already states, and it drifts the first time a 2x2 becomes a 2x3. `SF-S-DUCT`
  derives 30 3/4" clear x 11 1/4" drop; `SF-S-SUITE` 31 3/4" x 11 1/4"; `SF-S-HP1`
  **36 1/2" x 18 1/4"**.
  - **A box's LONG plan dimension is its axis, and every occupant is measured ACROSS the
    other one.** `SF-S-HP1` is 7'-9 3/8" in y against 40 3/4" in x for exactly that reason:
    turn it the other way and the check grades the trunk's whole travel as its "width" and
    never compares the lane to the machine at all. Whenever a soffit is near-square, the
    ordering is a design decision, not an accident of drawing.
  - **A HATCH THROUGH A SOFFIT IS AUTHORED, AND THE LADDER IS CUT FOR IT.**
    `Soffit.openings` (a tuple of `SoffitOpening`, `model/floors.py`) is what makes
    `resolve/framing/soffit.py` cut the rungs a hole crosses and frame **headers** along the
    box between the two bounding stations. Before it, an access panel was a `Furniture`
    placeable in the ceiling plane and the generator laid a rung straight through the middle
    of it — nothing compared them, because a placeable's footprint is a plan rectangle and
    `structural.member_interference` does not test placeables against members. The model
    asserted a panel that could not be opened, at 0 FAIL.
    - A cut rung becomes **stubs**, not nothing: what is left either side still carries the
      board out to its rail, and the stubs are what the header actually carries. Keys gain a
      letter suffix (`soffit-rung-004a`/`-004b`); a soffit with no opening frames
      **byte-identical** members to before the field existed, which is what kept every
      section golden and take-off row on the other boxes still.
    - An opening edge landing **on** a rail takes no header — the rail is already there.
    - `structural.soffit_opening` grades the header on deflection, oracled by
      `notes/soffit_rung_deflection.md`. It reads huge on catlin's hatch (L/10,279) and that
      is the point of having it: the same 2x4 over a four-foot opening is L/1,169, and δ goes
      as L⁴, so the margin is spent long before it looks spent.
    - It is deliberately NOT a duct penetration. A duct leaves a soffit through its END —
      `duct_occupants`'s `along` clip is built on exactly that — and a hole through a ladder
      rail is a different article with a different check.
  - `CHASE` routing keeps its honest meaning — a framed shaft that is NOT modeled as a
    `Soffit` — and is a *declared* unchecked case. It used to be the flag that turned the
    joist-bay check off, which is why four hand-arithmetic clearance comments lived in the
    plan source unchecked. They are gone; read the check.
  - **The check found two real errors on its first run, both in `EQ-S-HP1-AH`.** It was
    resolving at the 9'-0" storey ceiling (a CEILING mount with no elevation fell back to
    `default_ceiling_height`, which is now soffit-aware), and its case resolved 43" across
    the hall instead of 21" along it, because `EquipmentType.footprint` wins over the
    element's and `EQ-T-GREE-SLIM24` stated (43, 21). It needed `rotation=deg(90)`.
  - **And then the case itself turned out to be fiction.** `EQ-T-GREE-SLIM24`
    was an explicit "REPRESENTATIVE PLACEHOLDER … TODO verify datasheet"; the only real
    43 3/8" cabinet matching it was Gree's discontinued low-static `DUCT24HP230V1AD`, which
    tops out at 589 cfm against the 750 cfm this whole duct system is sized to. So the
    packing this check so carefully graded was a fit for a machine that does not exist, and
    the 4 7/8" slivers it left either side were what kept `DU-S-HP-SOUTH` riserless for a
    fortnight. **A `# TODO verify datasheet` on a type is not documentation debt — every
    clearance, lane and velocity downstream of it is provisional.** The real
    `EQ-T-GREE-DUC24` (44 1/2 x 29 11/16 x 11 13/16, 0.8" ESP) needed a new box, `SF-S-HP1`
    in `RM-S-STUDY2`'s ceiling; it needs no `rotation`, because the type now states the
    cabinet the way it is installed.
  - **AND THE VERIFIED TYPE WAS ITSELF WRONG — `EQ-T-GREE-FLEXX-ULTRA-24-AH`/`-OD`
    replaced it.** The DUC24/VIR24 record's own `source=` claimed 577-1030 cfm; the pair's
    real ceiling is 736 at 0.8" w.c., under the 750 this duct system is sized to. Its 13,500
    Btu/h at design was an interpolation (the read value is 14,606) and either way sat UNDER
    the zone's 15,164 Btu/h block load — `mep.heating_capacity` passed only by crediting a
    strip heater the DUC24 **has no aux-heat terminal to interlock with**. Gree's FLEXX Ultra
    answers all three: 760 cfm at 1.0" w.c., 21,000 Btu/h read at -15 F (137% of load,
    unaided), 24 VAC control with a factory heat kit, HSPF2 9.0 -> 10.0, and ENERGY STAR Cold
    Climate (AHRI 215213329) where the Vireo is not. It costs depth — 18 1/8" against
    11 13/16" — which is what took `SF-S-HP1` from a 17" drop to 21" and its underside to
    7'-3". **The generalisation of the generalisation: a verified datasheet number is only as
    good as the column it was read from, and three of these were read from the wrong one.**
  - **`SF-S-HP1` MOVED TO `RM-S-NCLOSET`'S CEILING ON 2026-09-04, AND THE WHOLE SYSTEM
    REVERSED WITH IT.** The air handler is at the north end of the storey now, the trunk runs
    SOUTH out of it, `DU-S-HP-SOUTH-RISE` is a collinear reducer at the trunk's south cap
    instead of a dogleg round the machine, and `EQ-M-HP1-OD` crossed to the north face on its
    own pad (`params/hp1_north_pad.py`). The box is **40 3/4" x 7'-9 3/8", flush on all four
    finished faces**, and the machine is turned `rotation=deg(90)` so only its 21 1/4" case
    depth competes for the graded width. Three things follow that are not obvious:
    - **`W-S-BW4` had to be retyped `INT_2X4_RC`.** The box spans it and `W-S-BW3`, which is
      already RC; a plain partition left the east face jogging 1/2" at y=30'-10", and
      `_rectangle` returns `None` on a non-rectangle, sending EVERY occupant to UNKNOWN. It
      narrows `RM-S-NCLOSET` by 1/2". The acoustics are a bonus, not the argument.
    - **`DU-S-ERV-HP-FEED` NAMES NO SOFFIT NOW.** `duct_occupants` clips a run ALONG the box
      it names and deliberately not ACROSS it, and the box's new y band is the same band the
      x=1'-0" attic chase runs through, twenty feet west and fourteen inches up. Named, three
      attic legs are graded as occupants of a cavity they never enter — a hard FAIL on correct
      geometry. The drop lands inside `EQ-S-ERV-MIX`'s own graded footprint, so little is lost.
    - **THE RETURN OPENS INTO A BOX, AND IT DID NOT AT FIRST.** `EQ-S-ERV-MIX` is a full
      **return plenum** now — 12" across the east lane by 29 1/2" along by 18", x 20'-5 1/2"..
      21'-5 1/2", y 27'-10 1/2"..30'-4" — and `REG-S-HP-RET`'s whole 336 in² face is inside
      it. For a few hours it was a 10 x 12 mixing box with a 30 x 16 ceiling grille lapping
      **three** things at once: 240 in² into `DU-S-HP-RET`, 120 in² into the box, and 120 in²
      into bare soffit cavity. A return drawing part of its face out of a framed ceiling
      cavity is **IMC 601.5's building-cavity-as-plenum**, and no check in this engine looks
      for it — `mep.register_duct_match` grades the pair in PLAN only, and a boot is
      unmodelled by convention here, so it passed. The three dimensions are each a clearance:
      12" is the east lane less the 2" `HANGER_GAP_M` off `DU-S-HP-SUP`; 29 1/2" stops the
      plenum clear of the cabinet's south face (overlap it ALONG by an inch and the pair is
      graded ACROSS, where the gap is 7/8"); 18" fills the 18 1/4" cavity.
    - **The wall-grille alternative was investigated and is NOT buildable**, which is worth
      recording so nobody re-proposes it. `W-S-C4B` is the only wall on the stair well's east
      side, and it is the **x=18' bearing line** — `RB-HOUSE`'s load path to the footings. Its
      studs resolve at y 369 / 384 / 400 / 416 / 424 5/8 with a double top plate at 225..228,
      so the one bay overlapping the plenum band (400 3/4..415 1/4) is blocked by the cabinet
      below y=408 and leaves **7 1/4" of clear bay**. Cutting a stud puts that plate over a
      ~31" span at ~1,600 plf: f ≈ 1,940 psi against Fb ≈ 1,310. Moving the air handler does
      not help — the wall is the problem, not the cabinet.
    - **`RM-S-NCLOSET` and about 7'-9" of the north hall are at 7'-3"**, and `RM-S-STUDY2`
      gets ~29 sf back to full height with the remainder 7" higher. That is the trade, made
      with open eyes. `RM-S-HALL`'s graded `clear_height` is unchanged at 8'-11 1/2" — the
      unsoffited-area escape holds.
    - **THE AIR-SIDE REVIEW THAT FOLLOWED (2026-09-04) FOUND THREE MORE THINGS, AND TWO OF
      THEM NOTHING GRADES.** The balance itself is sound — 750 leaves the machine and
      80+80+80+50+35+175+250 comes off it, exactly — but:
      - **Four supply grilles were authored 11 1/2" below the plane they are cut into.**
        `REG-S-HP-BED1/2/3` and `REG-S-HP-STAIR` all sat at 8'-0", on the strength of a
        comment reading "9'-0" ceiling less the 12" drop". `SF-S-DUCT` drops **14"**, it stops
        at x=21'-5 1/2" and those grilles are at 22'-6", and `RM-S-BED1/2/3` carry no soffit
        at all (`soffit_area` 0.0 sf) — they finish at 8'-11 1/2". **A `Register` resolves no
        solid, so `Mount.elevation` is a number the schedule and the sections print and NO
        CHECK READS.** Author every ceiling terminal off its own room's ceiling.
      - **`REG-S-HP-STAIR` was a short circuit and is now a SIDEWALL grille.** 50 cfm blown
        straight down 6'-2" from a 650 cfm return in the same room, with the return the
        *lower* of the two (7'-3" against 8'-0"). No size of ceiling grille fixes a direction
        fault. It is `REG-T-HP-SUP-SIDE` in `SF-S-DUCT`'s **west** lining now, throwing west
        across 12'-7" of landing into the stair void — and the take-off is the cleanest in
        the house, because `DU-S-HP-SUP`'s west face stands 3/8" off the cavity's west edge:
        a side collar through 2 1/2" of build-up, no boot. Its 97 1/8" is derived (the trunk
        centreline at 100 1/8" less half a 6" face), not chosen.
      - **`REG-A-HP-STUDY` had a chair on it.** A 100 cfm FLOOR boot at (26'-0", 3'-4") stood
        inside `FURN-A-STUDY-CHAIR2` (x 25'-8"..27'-4", y 3'-3"..5'-1"). Moved to 25'-0",
        which clears both chairs and shortens `DU-S-HP-SOUTH` by a foot; it is still under
        the legged 36" table, because **every** station on that bay line from x 21'-0" to
        27'-3" is under furniture. **Nothing grades a placeable against a register** — see
        the `placeable_column_overlap` note.
      - **`DU-S-HP-SOUTH` came in at both ends**, 19'-4" to 15'-8", the west by most: 6'-8" ->
        9'-4". The old west station's "centred between the two south windows" argument counted
        two of the room's **three** (x 4'-0" / 9'-4" / 14'-8"); 9'-4" is the centroid of all
        three, so one terminal washes the whole south wall.
      - **The riser cannot shortcut up through the joists**, which is worth recording because
        it is the obvious saving and it would give `RM-S-STUDY2` back 7 ft of 14" box.
        `FS-ATTIC`'s joists run in **x**, so any north-south run crosses them, and at x=19'-6"
        every hole lands 15 1/4" off `W-S-C1`'s face — inside the no-hole zone. Nor does "a
        small enough duct" buy it: 250 cfm wants ~51 in² for Manual D's 700 fpm, and the
        largest hole entertained that close to a bearing is ~6 1/2" round = 1,090 fpm.
    - **THE RETURN PATH IS SIX DOOR UNDERCUTS, AND `Opening` CANNOT HOLD ONE.** System 1 has
      **one** return, in `RM-S-HALL`; the ERV's 2 cfm bedroom pickups are tokens, not a path.
      At a conventional 3/4" undercut a 30" leaf passes 42 cfm at the 3 Pa ACCA/ASHRAE
      ceiling, so `RM-S-BED1/2/3` sit at **11 Pa** and `RM-A-STUDY` at **17 Pa**.
      `D-S-BED1/2/3` take 1 1/2", `D-S-SUITE` and `D-A-STUDY` 1 3/4", `D-A-HALVES` 1 1/4";
      `D-S-PLANT` deliberately does not (its pressure is a design output held by an
      interlocked damper). **The A-601 opening schedule has no undercut column, so a door
      with no undercut on it gets cut at 3/4" and six rooms do not get their air.** Full
      arithmetic and the acoustic/carpet costs: `notes/system1_return_path.md`.
    - **The box carries a FRAMED opening, `AO-S-HP1-AP`** — see **Soffit openings** below.
      30" x 29" clear under the machine's north two-thirds and its return face, in the closet
      ceiling. It is gasketed, and that is a code line: leaving the soffit's bottom open in
      the closet for the same convenience makes the closet the return plenum, which is what
      IMC 601.5(7) forbids.
  - **The passage below is HISTORY: it describes the box as it stood in `RM-S-STUDY2`'s
    ceiling, and the seam it argues for is now at y=27'-8" for a different reason (abutting
    `SF-S-DUCT`'s north end). The ledger argument no longer binds anything — a 35"-wide box
    topping out at x=21'-5 1/2" never reaches it.**
  - **`SF-S-HP1` ran UNDER `ST-S2A`'s flight, and that was allowed but bounded.** The stair
    climbs west along `W-S-SS2`, so over the box's north-east corner its underside is at or
    above the box's own 7'-3" face and the two finish as one plane. What may NOT be lapped
    is `ledger-W-S-SS2-stringer-1`, the 2x10 on the wall at y 104 1/8"..105 5/8":
    `structural.member_interference` excuses treads and stringers over a soffit and does not
    excuse that. It is why the `SF-S-DUCT`/`SF-S-HP1` seam is at y=7'-6" and not at the
    wall face 14" further north.
- **`W-M-HS4` is a pocket, and is therefore spoken for.** `D-M-LAUN` is a 4'-0" pocket
  door (was a 56" bifold); its leaf parks east inside `W-M-HS4`, crossing
  node `N-M-E3` where `W-M-LS` tees in. **Nothing may ever go in that wall again** — no
  outlet, no switch, no pipe, no register, no blocking, no towel bar — between 12'-4" and
  16'-5" on y=22'-4" there is no stud to fasten to and no depth to recess into.
  `mep.pocket_occupancy` enforces it; W-M-HS4 hosted nothing when this was built, which is
  the only reason it was possible. The cavity crossing a node is legal because wall
  segmentation at a tee is an authoring convention (`resolve/framing/pockets.py`), and the
  W-M-LS tie survives because a pocket occupies floor to 6'-8" only, so the band's plates
  run continuously over and under it — W-M-LS ties plate to plate and only its vertical
  edge floats. **A split stud that ever reaches the top plate destroys that tie.** 4'-0" is
  the widest leaf that fits: the pack closing the cavity must clear `N-M-C2`, where the
  BEARING `W-M-C3` corners in and `BM-M-HALL` starts. Full detail, including the 1"
  fastener limit, in `notes/pocket_door_at_laundry.md`.
- **THE SLABS WERE THINNED, and the psi grade is stated per use.** The
  basement slab went 3" -> 2" XPS at **>=25 psi** (R-16.1 -> R-11.1 whole-assembly, against
  an owner target of R-10; still PASSes `code.energy_prescriptive`'s R-10 slab row), and the
  detached garage slab 3" -> **1" at 40 psi** — 40 because that is the one slab in the house
  carrying VEHICLE wheel loads, and a loaded wheel is a contact patch, not a distributed
  floor load. `RM-GARAGE` is `conditioned=False`, so nothing grades it and every number
  there is an owner choice. Three things follow:
  - **The psi grade is NOT PRICED.** `library/materials.py` has one `xps` tag with no
    compressive field, and `prices.toml` keys XPS on THICKNESS alone — so the 40 psi board
    and the 25 psi board carry one rate here and do not in the yard (40 psi runs ~20-35%
    over). Fixing that properly means a psi-bearing material tag, not another price key.
  - **XPS IS THICKNESS-QUALIFIED IN `prices.toml`, AND IT HAD TO BE.**
    `envelope_layers` qualifies its price key on `thickness_in` (`cli/prices.py`), and the
    file carried only the bare `"xps"` key — so 1", 2" and 3" board all priced at one $/SF
    blend, which made any change of foam THICKNESS cost exactly $0 in the estimate. A cost
    model that cannot see a design decision is not decision-useful. The three qualified rows
    are DERIVED from the researched blend ($0.372-0.744 per inch-SF) with labour held flat
    across thicknesses, which is the conservative reading.
  - The basement's return to 2" retired a `DECLARED_DIVERGENCES` entry in
    `test_catlin_reference_parity.py` — catlin and the reference detail agree again.
- **THE BASEMENT'S WEST HALF WAS REPLANNED ON 2026-09-05, AND WHAT IT BOUGHT IS
  CIRCULATION.** Two doors were formed through 12" interior pours — `D-B-GYM` in `W-B-CS2`
  and `D-B-NE` in `W-B-CN` — and they were the house's only openings through concrete. The
  money was small (a buck-and-blockout allowance, $500-1,200 the pair, and
  `prices.toml`'s `concrete-window-bucks-and-blockouts` row now drives to zero and is kept
  under the `glazed-green-brick` convention). The defect was that from the stair foot the
  only route to the furnace room was **stair → playroom → gym → aisle → workshop →
  furnace**. Both doors are gone. Nothing on the x=18' bearing grid moved and no concrete
  wall moved.
  - **The sauna rotated onto the south (garden) wall**, long axis east-west, and then
    **shrank east to x=8'-10" the same afternoon — see the round-two entry below.** As
    rotated it ran x 4'-8"..18'-0" by y 0'-0"..9'-5", a 12'-2" x 8'-2" clear box against the
    8'-1" x 12'-7" it was, and its south face crossed two substrates with a **2" jog between
    the two liner faces at x=8'-10"** that nothing in the model drew. The `W-B-S1B` segment
    and the `SAUNA_LINER_ON_BASEMENT_8` assembly that carried it both existed for one
    afternoon and are gone. What survives the rotation: the room keeps `WIN-B-SAUNA` and is
    entered **from the gym** through framed `W-B-CS`, a short walk from `D-B-PATIO` and the
    sunken garden, which is what the brief asks the room for.
  - **x=4'-8" was a footing's doing, and it went away with the split.**
    `structural.frost_depth` lowers a footing's local grade by any open excavation within a
    frost depth (42") of the footing SOLID, and a footing follows its wall. At the 5'-0"
    split the plan was drawn at, `FT-B-S1` — the west half — sat **exactly 42.0"** from
    `SL-SG-FLOOR`'s rim: inside the reach by floating point, and outside `SL-SG-FROST-W`'s
    own 42" shielding radius. 4'-8" bought 46" of clear. With the split retired, `FT-B-S1`
    is one strip beside the court again and the wings protect it as they always did.
  - **The bathroom rotated** north-south along the framed stair wall
    (`W-B-STR3B`/`W-B-STR2`), **3'-3 15/16" x 7'-1 1/4" clear** (3'-5 1/4" until round two
    slid its east wall 1 5/16" west). Its **wet wall is `W-B-BA-E`**,
    a new `INT_2X6_STAGGERED_PLUMBING` east partition carrying the shared vent riser at
    (13'-10 11/16", 19'-3") — and `W-B-BA-N`, which used to be the room's only stud cavity, dropped to
    a dry `INT_2X4_PARTITION` when the plumbing left it. `D-B-BATH` swings out into the
    hall, and **on this wall that takes `flip_swing=True`**: the leaf's default side follows
    the host's direction and `W-B-BA-E` runs north-to-south where `W-B-BA-N` ran west-to-east.
  - **A hall** runs west of `W-B-CN2` from the stair foot south — 3'-3 15/16" clear, part of
    `RM-B-STAIR`'s own loop, no new `Room`. It stopped at the y=18' line and crossed into the
    workshop through `O-B-HALL`, a cased opening in `W-B-CW2B`; **on 2026-09-07 it runs the
    rest of the way to the sauna's north wall** and both of those are gone (next bullet).
  - **THE HALL REACHED THE SAUNA WALL, 2026-09-07 — and it retired the replan's "accepted
    consequence".** That consequence read: the playroom is reached only via the gym
    (stair → hall → workshop → gym → `D-B-PLAY`), and the workshop is the through-route from
    the stair to the gym. Running the hall south from y=18' to y=10' on the **same
    x=13'-10 11/16" well-partition centreline** `W-B-BA-E` and `W-B-WELL` already stand on
    buys three things for the length of one partition, `W-B-HALL-W`:
    - **`D-B-GYM` lands on the hall**, not on the workshop — same uid, same position, same
      32" leaf, retyped to `DT-INT-SWING32-GLAZED`. Circulation is
      stair → hall → gym → `D-B-PLAY`, one room shorter. The glazing is not decoration: the
      hall has no window and the gym's south daylight is the only light it can borrow.
      **It stays 32"** — `W-B-CS3` offers 42 3/16" of framed run and a 36" RO leaves 3/16"
      for two jamb packs.
    - **The workshop is a room, not a corridor**, with `D-B-SHOP` — 3'-0", in `W-B-HALL-W`,
      `flip_swing=True` so the leaf goes west into the shop, hinged at the north jamb. Its
      RO centres on `D-B-GYM`'s at y=12'-3 7/16" so the equipment path is straight through.
    - **The equipment route is the hall**: 3'-0" at `D-B-FURN` (widened, position unmoved —
      it is still pinned west by `PR-B-ERV-COND`) and at `D-B-SHOP`, off a 3'-5 1/16" flight.
    - **`W-B-CW2B` and `O-B-HALL` are deleted.** The note on that wall said it *had* to exist
      or the workshop and stair loops would merge into one room. True, and now deliberate:
      the merge IS the hall. `RM-B-STAIR` goes 114.8 → 147.7 sf and keeps one seed.
    - **`W-B-SA-N` splits at `N-B-HALL-S`**; `W-B-SA-N2` is the east 4'-1 5/16", and
      `WP-B-SAUNA-SPLASH`'s second span re-datums onto it at 9 5/16".
    - **`W-M-CLN2` now stacks on nothing, and that is authored.** `W-B-CW2B` was the only
      wall under it; what is left below is `W-B-CW2`, which overlaps its x 13'-4"..18'-0" run
      by 6 11/16" — short of the 2'-0" minimum, so there is one candidate count of ZERO and
      no `integrity.stack_ambiguous` to arm (the `W-M-STRW2` precedent). The load goes into
      the deck instead: two `JoistReinforcement` blocking entries in `params/main_deck.py` at
      x=14'-6"/16'-9", `at` y=**217"** rather than 216" because `at` snaps to the nearest
      joist line and 216" is exactly equidistant from 208" and 224". They must stay LAST in
      `_WEST_FLOOR_REINFORCEMENT`.
    - **The hall inherited the workshop's service ceiling, and that is the one thing the
      change actually cost.** `RM-B-WORKSHOP` is UTILITY, which is in
      `EXPOSED_SERVICE_OCCUPANCIES`, so nothing graded a pipe in its air. `RM-B-STAIR` is
      not, and `mep.run_in_finished_volume` (3" tolerance) called three runs the moment the
      hall grew: `DU-B-ERV-R-GYM` at 8.4", `PR-B-SAUNA-VENT` at 10.7" and `PR-B-HW-SAUNA` at
      3.8". The first two are not reroutable — the gym register is east of the x=18' bearing
      line and the ERV is west of the hall, so ANY route between them crosses it — so they
      are boxed out by **`SF-B-HALL`**, a full-width bulkhead at the hall's south dead end
      (x 170.0725"..212.615", y 123.8125"..133.4375", underside 85 15/16" storey-relative,
      7'-1 15/16" clear). The third was a modelling artefact worth fixing rather than boxing:
      `PR-B-HW-SAUNA` was **stacked 1 3/16" under `PR-B-CW-SAUNA`** on the same x=17'-4"
      line, which is not how a supply pair gets hung. They are side by side now — x=17'-4"
      and 17'-3", both at 7'-10 5/8" — and both clear at 2.55". There is no elevation pair
      that fixes a stacked one: two 1/2" lines need 5/8" of separation and the band between
      the ceiling and the 3" limit is 3" deep.
    - **Lighting and outlets.** Three more `ED-T-LT-CAN3` on `CKT-LT-BACKUP` at x=190",
      y=19'-6"/15'-0"/11'-6" — 27 VA against the ~52 VA of ALWAYS_ON headroom the withdrawn
      play-room cove was measured against, so `cycle_48h.sustains_always_on` holds
      (`test_backup_calc.py`). The middle one is at 15'-0" and not the ladder's 15'-6"
      because `PR-B-HW-SAUNA` crosses there 2 9/16" below the ceiling and a recessed trim
      wants that plane. `ED-B-WORKSHOP-SW` moves onto `W-B-HALL-W`'s workshop face 5" north
      of `D-B-SHOP`'s north jamb — **the hinge side, and the only side**: the latch jamb has
      5 5/8" of wall to `W-B-SA-N2` and no box fits in it. `ED-B-HALL-RC1` is new, on
      `CKT-RC-BSMT` at y=16': NEC 210.52(H) wants it and `electrical.receptacle_spacing`
      walks {BEDROOM, LIVING, KITCHEN, DINING, OFFICE} only, so nothing will ever ask.
  - **Two things the replan cost that are worth knowing before the next edit.** S-100's
    ARCH D scale went **3/16" → 1/8"** — one new foundation assembly is one more row in the
    FOUNDATION WALL SCHEDULE, that column already carried all three schedules (the sheet has
    no width left to open a fourth with), and the scene passed the 3/16" height by 0.18".
    **Round two handed the scale back** by deleting that assembly, and the 0.18" of margin
    is still all there is: the next `FoundationWall` assembly tag anywhere in this house
    steps ARCH D down again.
    And `test_upper_storey_studs_stand_over_studs` went 112/247 → 124/255, all of it two
    walls: `W-M-C1` (the x=18' line has three basement segments under it now and `stacks_on`
    names one, so `W-B-CS3`'s studs are invisible to the metric though they share its layout
    line) and `W-M-CLN2` (forced onto `W-B-CW2B`, which restarts its module 8" off because
    `INT_2X4_PARTITION` is deliberately not on the interior grid). **`W-M-CLN2` came back off
    that stack on 2026-09-07 when `W-B-CW2B` was deleted** — it stacks on nothing now, and
    `test_catlin_contract_m3.py` moved with it.
  - **`ED-B-GYM-RC1`/`RC2` were on the wrong side of the x=18' line and nobody noticed.**
    They were authored 1" WEST of `W-B-CS`'s west face — inside the sauna, a 120V
    convenience receptacle in a 190 °F room — and `electrical.receptacle_spacing` accepts a
    device within 0.5 m of a room's clear face **regardless of which side it is drawn on**,
    so the gym counted them and nothing said so. Both are on the gym face now, and there are
    three: the line is broken by two doors, and NEC 210.52(A)(2) measures wall space between
    doorways. `ED-B-GYM-RC8` stands in the 15" of `W-B-CS3` north of `D-B-GYM`, because
    everything past `N-B-C1` is `W-B-CS2`'s pour.
- **ROUND TWO, THE SAME DAY: one substrate under the sauna, one plane beside the stair, and
  a closet in the dead space.** The replan above fixed the circulation and left three things
  that read wrong on a drawing. All three had one answer.
  - **The sauna's west wall moved from x=4'-8" to x=8'-10", onto `N-B-S1`.** ~8'-3 15/16" x
    8'-3 11/16" clear, and its south face is now **one plane on `W-B-S2`'s garden curb** —
    the 2" jog is gone, `W-B-S1B` is deleted, `SAUNA_LINER_ON_BASEMENT_8` is unregistered,
    `FT-B-S1` is one unsplit strip and `structural.frost_depth` still passes. The workshop's
    west bay took the four feet: 3'-8 3/16" → **7'-10 3/16"** clear, and
    `ED-B-WORKSHOP-PANEL1` went back to its centre. The 8'-6" two-tier bench does not fit an
    8'-4" room whose north wall gives up 3'-0" to the shower pan, so
    `FURN-SAUNA-BENCH-2T-60` was minted beside it in `library/`; the heater and its junction
    box crossed to the **south-east corner**, the only stretch of south liner clear of the
    window, the benches and the door. **`EQ-T-SAUNA-HEATER`'s 9 kW was always sized for this
    room** — the "~513 cf" in `electrical.py` matched the pre-rotation box and the shrunk one
    (519 cf), not the 745 cf the rotation grew it to.
  - **`W-B-BA-E` slid 1 5/16" west onto the stair well's partition centreline** at
    `inch(166.6875)`. Two nearly-collinear planes an inch and a third apart became one, and
    everything that references `N-B-BA-NE`/`N-B-BA-SE` rode along. The wet-wall risers did
    NOT — they are absolute coordinates in `mep_venting.py`, `mep_supply.py` and
    `mep_supply_devices.py` — and neither did `ED-B-BATH-SW`, which stood 1 5/16" inside the
    studs until `test_wall_mounted_devices_resolve_against_a_wall_face` caught it. **No
    `haus check` rule grades a wall device's depth.**
  - **`W-B-WELL` gives the well partition faces, not framing.**
    `resolve/stairs/u_split.py` already GENERATES the 2x4 plates and studs between the two
    flights — the plan this was written from said it emitted nothing, and the first build
    answered with twelve `structural.member_interference` FAILs. So
    `STAIRWELL_PARTITION_4H`'s structure layer carries **no `FramingSpec`**, which
    `framing/solver.frames_as_members` reads as monolithic — so the wall lands in
    `[wall_structure]` billing 0.47 cy of "placed spf", and `prices.toml` prices it at
    **zero** and says why. Its thickness must stay locked to
    `resolve/stairs/common._WELL_PARTITION_THICKNESS_M` (4 1/2"): `INT_2X4_PARTITION`'s
    4 3/4" pushes 1/8" into each inner stringer.
  - **`RM-B-UNDERSTAIR`, 17.5 sf that nobody could reach** — *superseded by round three
    below, which deleted `W-B-CL-N` and the room with it.* The volume under the arriving
    flight was inside `RM-B-STAIR`'s polygon, so the model called it floor. `W-B-WELL` closes
    the east side, `W-B-CL-N` the north (**47" tall, not the 52" the stringer allows — the
    upper landing's ledger is the lower obstruction and it starts at 47 5/8"**), and
    `D-B-CLOSET` opens it west into the furnace room. `RM-B-STAIR`'s seed had to move out of
    the new partition's footprint.
    - **Do not author `Room.ceiling` here and do not put a `Soffit` under the flight.** The
      real head rakes 96.7" → 54.8" and no field says that; `_clear_head` reads decks and
      soffits, a stringer is neither, so `clear_height_m` resolves to the main-floor deck and
      passes R305.1.1 honestly. An authored 53" ceiling would be taken verbatim and FAIL.
    - `DT-INT-CLOSET24` is **2'-0" x 6'-0"** and the far jamb is why: at y=28'-4" there is
      76.5" of head, a 6'-8" leaf plus header wants 82", a 6'-0" one wants 74".
    - `W-B-STR3` was retyped to `STAIRWALL_INT_2X6_BRG_UNDERSTAIR` — 5/8" Type X in
      place of the 3/4" stair plywood, per R302.7. **That cost the exposed-plywood stair face
      on this segment** (a `Wall` carries one leaf) and moved `FO-M-STAIR`'s west edge to
      `ft(10, 3.25)`, exactly as that opening's own comment predicted it would have to.
  - **The engine changed twice.** `illumination._gypsum_finishes` matched the literal
    `"gyp"`, which **no layer in this catalog contains** — every gypsum layer is `gwb*` on
    `gwb`/`gwb-x` — so `code.R302_7_under_stair_protection` could never verify protection,
    only fail or find nothing to protect. And `topology._through_pair` chose a four-way
    node's through run **alphabetically**, which at `N-B-ESS-SE` picked the two partitions
    over the bearing wall running through and reported a mixed-assembly junction; it prefers
    a continuous bearing pair now, tag order as the tie-break.
  - **`D-B-FURN` is at `ft(3, 3)` and the condensate line fixed it there.** A UI drag had put
    it at 1'-6 1/16" — `from_node` offsets the NEAR JAMB — across `CD-B-SPA`,
    `CD-B-DATA-SHOP` and `PR-B-ERV-COND`. None of the three can move (a `ConduitRun` has one
    flat elevation and `CD-B-SPA`'s south end is sleeve-pinned at -4'-0"), so the door did.
    The king stud's west face lands 0.475" off the condensate pipe: **any move of that door
    east re-opens the clash.**
  - **Two rooms had no light at all and nothing graded it.** `RM-B-SAUNA` and the new closet
    now have one each (`ED-T-LT-SAUNA-VT`, a 125 °C sauna-listed fixture with its switch
    OUTSIDE the hot room; `ED-T-LT-SPOT-SW`, integral-switch). There is **no NEC 210.70 check
    in this engine** — a missing lighting outlet is invisible to `haus check`.
  - **`EQ-B-HP2-GYM` was 5 1/2" into the ceiling and the UI drag did not do it.** Mounted at
    7'-6" AFF, a 10 53/64" cabinet tops out at 100 13/16" in a room `code.R305_ceiling_height`
    measures at 95 3/8". It is at 6'-6" now. The drag itself was kept: it is on `W-B-S3-FR`
    throwing north across the room's 18' depth, which is the better wall.
  - **`LR-B-STAIR-RAIL` still lies under the flight rather than along it** — one `Mount`
    elevation for a whole `LightRun`, measured off the slab, so it cannot rake. Pre-existing,
    now visible because the volume it runs through is a named closet. `PA-B-BFP-SAUNA`'s
    `room=` said `RM-B-SAUNA` and never was (it is 6'-7" north of the sauna); fixed.
  - **Still unresolved and not this change's:** `CD-B-SPA`'s east leg at y=1'-0", 61" over
    the slab, appears to run **through** the rotated sauna.

- **ROUND THREE, THE SAME DAY: the under-stair closet loses its north wall, and the sauna
  takes 7" off the workshop.** Two owner calls, and between them they say something about
  this model worth keeping: **both changes are bounded by things no check grades.**
  - **`W-B-CL-N` is deleted and `RM-B-UNDERSTAIR` with it.** The storage under the arriving
    flight runs the full length of it now and on under the landing deck, instead of stopping
    at y=31'-0". `W-B-WELL` keeps the east side and its north end is free — `open_end=True`
    on `N-B-CL-NE`, which is what `integrity.wall_loop_open` is for and the only honest way
    to say a partition dies in the middle of a stair well.
    - **The `Room` could not survive it.** With nothing closing the north side both seeds
      land in ONE face, and `RM-B-STAIR` and `RM-B-UNDERSTAIR` each resolved the **same
      114.8 sf polygon** — the whole shaft counted twice in every area, finish and load that
      walks rooms, at 0 FAIL. So the closet gives up its label and keeps its use:
      `D-B-CLOSET` still opens it to the furnace room, `ED-B-CLOSET-LT` still lights it (its
      `room=` is `RM-B-STAIR` now, the fixture did not move), and `EQ-B-HP2-GYM`'s
      `zone_rooms` drops the tag.
    - **`W-B-STR3` is NOT retyped back.** `code.R302_7_under_stair_protection` now passes on
      "no enclosed usable space" — the check keys on a room's occupancy and `STAIR` is not in
      `_UNDER_STAIR_OCCUPANCIES` — but the reason for the Type X did not go away with the
      label. The code hook went quiet; the wall stays as built.
  - **`W-B-SA-N` went north 9'-5" → 10'-0", and `D-B-GYM` is what stops it there.** The room
    is 8'-3 15/16" x **8'-10 11/16"** clear, 555 cf against `EQ-T-SAUNA-HEATER`'s 600 cf
    rating — 45 cf of margin, so a deeper sauna from here is a bigger heater and a bigger
    circuit, not a free change. The workshop's north strip pays for it: 8'-7" → 8'-0".
    - **The binding constraint is an opening, and nothing grades it.** The east end of this
      wall lands on `W-B-CS3`, the 4'-5" of framed x=18' line between the sauna and the
      y=13'-10" pour, and `D-B-GYM`'s rough opening starts at y=10'-11 7/16". At 10'-0" the
      wall's north face leaves 7 5/8" for the jamb pack. At **10'-6" the two overlap
      outright and `haus check` says nothing** — no rule tests a tee wall landing beside an
      opening. The coupling runs both ways: if `D-B-GYM` goes back south, this wall follows.
      **It is also why `D-B-GYM` stayed 32" when the hall reached it on 2026-09-07**: 42 3/16"
      of framed run less two jamb packs is a 32" leaf, and a 36" one would spend the 7 5/8"
      this bullet is about.
    - **Everything dimensioned off the north liner moved 7" with it**, and none of it would
      have been reported: `FURN-B-SAUNA-BENCH-E`, `FX-B-SAUNA-SH` (the pan stays in its
      corner), `FX-B-SAUNA-FD`, both `SP-B-SAUNA-*` sleeves, `PR-B-SAUNA-DRAIN`'s first
      three vertices, `PR-B-SAUNA-FD-DROP`, both condensate air gaps and
      `PR-B-SAUNA-VENT`'s riser. `D-B-SAUNA` is `from_node("N-B-SA-NE", …)` and DID report:
      it rode the node north and `structural.door_framing_module` FAILed on the stud module
      within the same build. Its offset grew 7" to hold the leaf still.
  - **A third bench, on the south liner: `FURN-B-SAUNA-BENCH-SW`, and the heater moved to
    let it grow.** `EQ-B-SAUNA-HTR` stood in the middle of the south liner and left
    3'-7 15/16" of it, which is a 2'-6" bench. On the **east liner** — `rotation=deg(270)`,
    18" face to the wall, 16" depth into the room, 2" off both liners as before — it leaves
    4'-7 15/16" and the bench is **4'-0"**. `ED-B-SAUNA-JB` came east with it and butts its
    west face; `REG-B-SUP3` and `DU-B-ERV-R-SAUNA-SUP`'s east leg followed, because "over
    the stones" is a position, not a label.
    - **What stops the bench is `ED-B-SAUNA-JB`**, not the wall: the box's base is at 18"
      AFF, exactly the bench top, so a 4'-6" carcass would reach under it and put a fixed
      seat in front of a live 9 kW junction box. 4'-0" leaves 7 15/16" to the box and
      1'-1 15/16" to the heater. Raising the box over the bench would buy that back and is
      the wrong trade in a room that stratifies.
    - **The heater is deliberately not pushed north against `D-B-SAUNA`'s jamb**, which
      would free another 1'-6" of bench and put a 30" stove at the doorway. Nothing grades
      any of this: `EquipmentType` carries no `clearances` and no rule tests a placeable
      against a wall device or an equipment footprint against a door approach.
    - `FURN-SAUNA-BENCH-48` was minted in `library/` and priced in `prices.toml` — **an
      unpriced type is silently dropped from the takeoff.**

- **Four basement assemblies, and every split is a condition, not a preference.** Two
  independent axes cross here: what covers the exterior XPS, and how thick the pour is.
  All four compose off `library/`'s `FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a house-local
  skin layer, so the core cannot drift between them.
  - *The skin, and there is only one.* `BASEMENT_12`/`_8` cover the
    XPS with a 1/8" `foundation-coating-acrylic` banded from 6" below grade to the top of
    the wall — a trowel-applied acrylic coat over reinforcing mesh, authored as a
    `Layer.extent` off the `GRADE` datum, so a grade lift grows it without an edit here.
    **It was a 1/2" `foundation-protection-panel` until 2026-09-04, and the swap bought a
    verdict, not a saving.** A butted board's installed permeance is its joints, nothing in
    that product class publishes an ASTM E96 number for it, and
    `building_science.condensation` reported UNKNOWN on both assemblies for as long as it
    was authored; a seamless lamina is gradeable and both walls now PASS. Installed, the
    coating bills slightly *above* the board. The board and its price row survive as the
    named alternate, so the revert is one `material_ref` edit.
    `W-B-S1`/`W-B-S4` are on `BASEMENT_8`, which
    retired the stucco: their exposure genuinely *is* a grade band (6'-4" of fill,
    2'-2 9/16" out of the ground), so they get ~37 SF of coating. The court segments in
    between get **no skin at all** — their XPS is inside `W-B-BRICK`'s ventilated cavity,
    with no UV and no impact on it, and 273.7 SF of parge was buying a plasterer's
    mobilization to finish a surface nobody sees. `BASEMENT_8_GARDEN` and
    `_GARDEN_PARGE` survive unreferenced in `plan/assemblies.py`, documented, so the revert
    is two `assembly=` edits.
  - *The pour.* 12" used to be earned wherever a cast concrete deck landed on the
    wall top beside the sill plate and needed a bearing seat inboard of it. After the
    basement-ceiling overhaul the only cast deck left is `SL-M-DECK`, which bears on the
    east wall and the centre line — so `W-B-E1/E2` stay `BASEMENT_12` and the other
    nine segments are 8" carrying `#5 @ 41" o.c.` vertical steel, which IRC Table
    R404.1.2(8) requires at 8" where 12" reads NR (it was `#6 @ 48"` before the flat
    bearing seat made the pour exactly 8'-0", which is the table's 8'-unsupported row
    rather than the 10' row a 9'-4" wall rounds up to). **The "12" is earned only where a cast
    deck lands beside the sill plate" rule is now obsolete** — with a flat seat nothing
    competes for wall-top width, and the 12" segments that are left are left as built for
    reasons written on the walls themselves, not for bearing. `W-B-STR` and `W-B-STR3` are
    2x6 bearing stud walls — `unbalanced_fill`
    is `ft(0)` on both, and what they carry is joists and a wall stack, which is a
    stud-wall job on a footing. `W-B-CS` is the same — it
    carries wood on both faces — leaving `W-B-CS2`/`W-B-CN`/`W-B-CN2` as the interior pour
    that remains. Drop that string on any of the nine and
    `structural.foundation_unbalanced_fill` FAILs, correctly.
  The banded walls carry 4.175" outboard of the concrete face over the band and 4.05" below
  it; the court walls carry 4.05" throughout. `N-B-BRICK-W`/`-E`'s stand-off is
  `inch(-4.05)`, on the court walls' bare XPS, and the veneer's clear cavity is **1-1/2"**
  (IRC R703.8.4 wants 1" minimum). **It was `inch(-4.55)` until 2026-09-04 and that was a
  bug**: the node was struck on the old parge's finished face and did not follow the parge
  when it was deleted, so a 1/2" void sat between the XPS and the veneer's 1" `air-gap`
  layer with no layer describing it — the model said 1" where the build had 1-1/2". Moving
  the node onto the foam and growing `air-gap` to 1-1/2" cancels at the gap's outboard face,
  so the wythe, the arched reveals and the veneer's footing all stay exactly where they
  were. That is why thinning the *wall* did not move the brick, and why changing a
  *skin* thickness moves the cavity rather than the wythe. Because
  the walls align on `face("concrete-ext")`, the 4" came off the INSIDE face: the furnace
  room and the workshop each gained 4" of clear (the model still reports the old number —
  `clear_face` is inset from the wall axis, which did not move). See
  `notes/basement_to_framed_wall_detail.md`.
- **Every exterior deck's plank is the floor system's own sheet. There is no longer an
  exception.** `FS-SG-PORCH` (composite, 3bf2f48), `FS-SG-DECK` (aluminium) and — since
  2026-09-03 — `FS-BW-FLOOR` (composite) all carry their boards as `subfloor=DeckLayer(...)`;
  the `SL-SG-PORCH`, `SL-SG-DECK` and `SL-BW-DECK` slabs that used to stand beside the
  framing are gone, and all three planks bill by the square foot in `[sheet_goods]` instead
  of by the cubic yard out of a table named `[concrete]`. The balcony converted term for term
  because its joists cantilever 6" and the deleted slab's outline *was* that cantilever.
  - **The breezeway needed an engine change, and it is one field.** Its plank oversails the
    joist rim 2 3/4" at each end onto `D-M-ENTRY`'s and `D-G-SERVICE`'s thresholds, and a
    floor system's sheet used to be exactly its joist field (`resolve/floors.py`) — so
    converting it either FAILED `code.R311_3_exterior_landing` on both doors or laid a joist
    through `PT-BW-1..4`. `JoistSpec.cantilever*` cannot help: a bearing line is a span
    boundary, so a cantilever is a joist-AXIS quantity and this oversail is on the
    perpendicular one. **`FloorSystem.subfloor_outline`** is an authored sheet polygon that
    replaces the derived corners and touches nothing else — not the joist solver, not
    `deck_voids`, not the elevations.
  - **Bound it.** `structural.subfloor_oversail` grades an authored sheet against
    `[framing] bearing_plan_tolerance_in` (8"), because past that the uplift pass finds
    neither a derived tie nor a hanger and FAILs every member under the deck, reported
    nowhere near the deck. The breezeway's worst edge is 3 5/8".
  - **The take-off had to move with it.** `sheet_goods_takeoff` computed area from the
    bounding box of `floor.members`, so a wider sheet would have drawn wide, passed R311.3
    and still billed the joist field. The subfloor reads `deck_outline` now; `ceiling_below`
    keeps the framed extent, because a ceiling is nailed to the joists.
- **THE GARAGE WALL WAS REBUILT, and four decisions moved at once.**
  `GARAGE_WALL_2X6` was 2x6 @16" o.c. with **empty bays** and 1.5" Zip-R doing the whole
  thermal job (owner's choice), clad in a 26 ga concealed **nail strip**. It is now
  **2x6 @24" o.c. / 2" ccSPF in the bays / 5/8" CDX / 7/8" corrugated exposed-fastener
  panel**, and the trusses went to 24" o.c. with the studs (`GARAGE_ROOF`, ff 0.09 ->
  0.0625 = 1.5/24, and the two must move together or the R-38 blow is under-credited).
  Everything here is an owner choice, not a code minimum: `RM-GARAGE` is
  `conditioned=False`, so it is exempt from `code.energy_prescriptive`,
  `building_science.condensation` and the MN prescriptive table alike.
  - **The card read R-14.3 and was lying.** With no `CavityFill`, `analysis._layer_rsi`
    bills the 5.5" STRUCTURE layer as SOLID SPF over the full area; the honest whole-wall
    was R-7-8. It reads **R-13.2** now, which is *lower* on the card and roughly double in
    the building. That is the shape of this whole change: the ccSPF spends about a third of
    what the cladding and spacing save, and what it buys is a real air seal.
  - **There is NO WRB**, and that is a decision (IRC R703.2's exception for an
    unconditioned detached accessory building). The ccSPF is the air, water and vapour
    plane — `TR-CATLIN-GARAGE-OPENING` names `stud-cavity` for all four controls, not the
    house's `sheathing-ext`/`spray-foam-ext` tuple — so **bucks before foam**, as on the
    house. The CDX carries no `control` set for exactly this reason: bare sheathing that
    claimed those layers would be a WRB nobody is buying.
  - **There is no furring, and the corrugation IS the rainscreen** — 7/8" of continuous open
    flute behind every sheet, more free area than the 3/8" 1x4 the wall carried before.
    What makes that drain rather than pond is the closures, ~192 LF of them,
    vented at the base and solid at the head. They are priced as
    `[allowances] envelope-garage-corrugated-closure-strips` and **not** through
    `bug_screen:GARAGE_WALL_2X6`, which reads a rainscreen cavity depth out of the layer
    stack and therefore reads 0 SF. Do not "activate" that row by authoring a 7/8" airgap
    layer — it would add 7/8" on top of the 7/8" cladding and move both wall faces.
  - **The whole 24'x24' moved 3/8" north**, `GARAGE_GAP_FT` 4.6875 -> 4.71875, always for
    one reason: 3/8" more panel standing proud of the node line is
    3/8" less breezeway slot. The uncut 4'-0" polycarbonate panel keeps its 1/2" reveal. The
    Zip-R -> CDX swap moves nothing in that chain — the wall's `alignment` puts whichever
    sheathing it carries on the node line — so **do not recess the sheathing to hold the
    cladding face still**, which re-opens the old rain shelf.
  - **NO 16" ZONE AT THE OVERHEAD DOOR, and it was investigated.** `W-G-E` is NONBEARING
    (the ridge runs E-W; the trusses bear on `W-G-S`/`W-G-N`) and the 16'-0" opening is
    carried by its own 2-ply 14" LVL on jamb packs the solver sizes from the opening. Field
    studs beside a nonbearing opening carry nothing extra. It would also not be a local
    override: `FramingSpec.spacing` lives on the ASSEMBLY, so a closer-spaced zone is a
    second assembly tag, a second `prices.toml` row, a second `condition_gates` key and
    fresh section goldens.
  - **Three openings re-stationed onto the 24" grid, and one deliberately did not.**
    `WIN-G-N1` 1'-5" -> 2'-5" and `WIN-G-S1` 21'-5" -> 20'-5" (a 14" RO wants a BAY CENTRE,
    12 + 24n along `W-G-W`); `SERVICE_DOOR_OFFSET` 5'-10" -> 6'-6", which puts that leaf's
    centre on 8'-0" — the same station as `D-M-ENTRY`, so the two doors the breezeway spans
    are finally CONCENTRIC and `_GLAZING_CENTER_X` is simply their shared centre.
    `D-G-OVERHEAD` stays at 4'-0" and its advisory stays suppressed: every legal station
    moves the ICF grade beam and makes the two brick piers 5'-0" and 3'-0".
  - **The 16 garage-wall `S-5-N` seam clamps are gone** (`plan/wind_clamps.py`), the exact
    precedent of the 48 house-wall `S-5-S` clamps — an N clamp closes on a
    nail strip's bulb, and a corrugated panel has no seam. Corner uplift is carried by the
    panel's own 640 face screws. The `S-5-N` price row STAYS: the garage ROOF is still nail
    strip and still carries 12.
  - **`GARAGE_WALL_WIND_CLAMPS` survives as an empty list**, and `standing-seam-nailstrip-26`
    and `zip-r` keep their price rows at 0 — the `glazed-green-brick` convention. The revert
    is layer material refs plus re-authoring sixteen constructors.
- **THE OVERHEAD DOOR FACES NORTH AND THE GARAGE SITS AT x 4'-0"..28'-0" (2026-09-07).**
  It faced east on `W-G-E` for a lot to the SOUTH with a driveway round the east side — a
  premise that survived in two prose comments and no `Driveway` element, and that had never
  agreed with `plan/site.py`'s own `SetbackSpec(edge=2, "FRONT")` on the NORTH edge or with
  the water service entering from the north. The ridge turned with it (`ridge_direction`
  `"x"` -> `"y"`, bearing on `W-G-E`/`W-G-W`), the stem gap moved east -> north, both eaves
  now carry gutters and a leader, and the six south-slope snow guards are gone because south
  is a rake and nothing discharges over `GL-BW-ROOF` any more. **The footprint did not
  rotate** — the garage is square, the windows stayed on `W-G-W` and `D-G-SERVICE` on
  `W-G-S`. Then it moved **6'-0" east onto the house ridge**: the garage is x 6'-0"..30'-0",
  centre x=18'-0". `GARAGE_X_WEST`/`GARAGE_X_EAST` are published beside the two y lines and
  the stem, the slab and the landing all derive from them.
  - **THE MOVE COST THE CONCENTRIC DOORS, AND THAT RED IS DELIBERATE AND OPEN.**
    `D-G-SERVICE` had to travel with its wall — the move is in 24" steps (a 36" RO must land
    on a stud line measured from the wall's own start) and at x=8'-0" its king stud would
    stand **5/8"** inside the corner pack, which owns the first 3 5/8" of wall. Its centre is
    x=10'-0" now. **`D-M-ENTRY` could not follow**: its east jamb is already 6" west of
    `N-M-N2` at x=10'-0", the tee where `W-M-STRW`'s bearing stack lands and runs to the
    footings, and a 36" RO cannot straddle it. So the two doors the breezeway spans are
    **2'-0" out of line**, `params/breezeway.py` is untouched at `_GLAZING_CENTER_X = 8.0`,
    and `code.R311_3_exterior_landing` FAILs on `D-G-SERVICE`. **That is the one deliberate
    red in this house and it is an owner decision** — centre the garage, look at it, adjust
    the breezeway after. Do not answer it by moving the garage back.
  - **`EQ-M-HP1-OD` moved 6'-6" east and `ED-M-HP1-DISC` went to the WEST of it.** That
    cabinet's whole siting argument is that it stands east of the garage's plan extent; the
    garage moved under it. It now oversails the house's NE corner by 3" to keep its 14"
    clearance to the garage's east gutter face (31'-10" to 36'-0" is 50"; cabinet plus
    clearance is 53"), and its disconnect is a 6 1/2" can in the 14" slot with **no NEC
    110.26 working space and nothing grading it**. Both are hard bounds: that machine cannot
    move further either way on this face. **`EQ-M-HP3-OD` did not move** — it sits south of
    the garage's roof edge, in the 48 1/2" slot, which is its documented condition.
  - **Aligning `ST-G-SERVICE` under its own landing fixed a standing FAIL.** The flight ran
    x 5'..8' under a landing at 6'-6"..9'-6", a stale offset nothing graded;
    `code.R312_1_guard_height`'s unguarded-edge FAIL on `SL-G-STEP-0` went with the fix.
  - **`ED-G-SW` / `ED-G-EXT-SW` sit inside `D-G-SERVICE`'s rough opening** — a pre-existing
    defect translated faithfully rather than silently re-sited. Nothing grades a wall device
    against an opening; the fix is ~12'-0"/12'-6", east of the real east jamb.
  - **`notes/garage_orientation_lot.md` is the whole before/after and the revert recipe**,
    including that a genuine south-lot revert must also flip `SetbackSpec` edges 0 and 2,
    which this change deliberately did not touch.
- **The garage has no wainscot. Its base skin is the 24" band on the ICF stem, uniform on
  all four walls, and that is a 2026-09-03 deletion rather than a substitution.** A 4'-0"
  wainscot stood on the two 4'-0" strips of east wall flanking the overhead door, wrapped
  4'-0" around each of the SE/NE corners — four `W-G-WAIN-*` FoundationWalls on
  `GARAGE_METAL_WAINSCOT`, six local nodes, four cap flashings at a round 4'-0". It was
  Glen-Gery Columbia Roman Maximus soldier brick until 2026-09-02 and PVDF-painted aluminium
  sheet after. All of it is gone, along with `GARAGE_BRICK_WAINSCOT`, `GARAGE_ICF_6_BRICKLEDGE`,
  `off-white-brick` and both `_BRICKLEDGE` dicts in `params/foundations.py` — **deleted
  outright, not kept unreferenced**, so git history is the revert path and not a one-line
  `assembly=` swap.
  - **NOTHING REPLACED IT, AND THE PIERS LOST NOTHING.** `GARAGE_ICF_6`'s `coil-gap` +
    `coil-ext` band — 2" below grade to the stem top, on a 1/4" vented standoff — always ran
    BEHIND the wainscot, deliberately: that wainscot was a vented, drained rainscreen open at
    its base, so water reached the foam behind it by design. Those two east segments
    therefore keep exactly the protection the other three walls always had. **156.2 SF is
    unchanged** by the deletion, which is the check that this was a saving and not a
    transfer: the wainscot's own `[wall_structure]` row (65 SF, $1,430–2,730) and 15.5 LF of
    cap simply left the bill.
  - **THE STOCK SHEET STAYED 48" x 120" AND THE GAUGE STAYED 0.040–0.050", AND THAT IS THE
    ONE COUNTER-INTUITIVE CALL HERE.** With only a ~24" band left, 24" trim coil is the
    obvious buy. It is the wrong one: a 48" sheet rips into **exactly two 24" bands with no
    waste**, so the heavier architectural sheet costs nothing per SF over coil, and the band
    is still the plow-and-shovel splash zone the gauge was chosen for. There is no backer —
    the sheet spans its fixings and never touches the foam — so dent resistance is gauge and
    fixing spacing, nothing else. **Second best, only on a supply failure: 0.024"
    heavy-gauge 24" trim coil**, the thickest that product line reaches. **Never 0.019"**,
    which takes a permanent dimple from a shovel corner.
  - **THE STEM-TOP Z IS NEW SCOPE, NOT A LEFTOVER OF THE WAINSCOT.** The band's top and the
    corrugated panel's base both land on the stem top, and until this change that junction
    was modelled by nothing at all — it lived in a `source=` string.
    `STEM_TOP_Z_FLASHING` (`plan/storeys/garage.py`) is six `DRIP_FLASHING` runs, 76.5 LF,
    **broken at both stem gaps** (the 16'-0" overhead door and the 3'-0" service door, where
    the stem drops to a grade beam and there is no band to flash). `DRIP_FLASHING` is a bent
    angle — flat leg plus outboard turn-down — which is what a Z is; `WRB_COUNTERFLASHING` is
    a flat pan and would not do. The inboard kick-out leg cannot be a second bend on the same
    run and is carried in prose, exactly as the deleted caps carried it.
  - **The Z is authored as one counter-clockwise loop and every run is `back_side="left"`.**
    Walked south W→E, east S→N, north E→W, west N→S, each wall's left-hand normal
    (`normal(d) = (-dy, dx)`) points inboard, so the turn-down hangs outboard on all six.
    **Nothing grades `back_side`** — get one direction wrong and the drip points at the wall
    at 0 FAIL. `test_garage_base_skin_is_the_stem_band_alone_and_its_top_is_flashed` pins it;
    confirm it in the viewer too.
  - **THE Z EXPOSED AN ENGINE BUG AND THE FIX IS IN `emit/draw/detail_components/eave.py`.**
    `_water_anchor` picked the eave's drip-edge label by plan proximity with **no elevation
    filter**, so a `flashing` solid 114" below the eave, on the same wall line, was averaged
    into the anchor — the garage's `detail_wall_roof` leader for "drip edge lies ON the top
    deck" pointed at the ground. It now takes only candidates within `_ANCHOR_Z_WINDOW_IN`
    (36") of where the label is expected to land. Generous on purpose: the authored piece and
    the schematic fallback genuinely sit at different elevations, and the window rejects
    another STOREY's flashing, not a few inches of lap order.
  - **ALUMINIUM OVER ALUMINIUM, AND NO CHECK GRADES IT.** `corrugated-panel-26` above the
    band is 26 ga PVDF-coated **steel**; the band and the Z are **aluminium**. They must
    never lap metal-to-metal — sealant or EPDM between, the Z's upper leg behind the
    corrugated — and aluminium must never touch concrete or fresh mortar (alkali strips the
    oxide film). In a salted splash zone that contact line is where the detail fails.
    Naming `aluminum-flat-pvdf` on the Z rather than the envelope's `metal-dark-exterior`
    steel trim coil is the whole enforcement, and it keeps band and Z one colour and one
    coil order.
  - **`OVERHEAD_DOOR_OFFSET`'s 4'-0" LOST ITS DEFENCE AND IS NOW AN OPEN QUESTION.** The
    `structural.door_framing_module:D-G-OVERHEAD` suppression in `preferences.toml` was
    carried on the wainscot: moving the door 12" would have made its two piers 5'-0" and
    3'-0", a visibly asymmetric facade bought with one stud. **That argument is gone** — the
    base band is uniform and does not care where the door sits. What remains is a *cost of
    moving*, not a reason not to: the offset gaps the ICF stem into a grade beam, so the gap
    nodes, two stem segments, their footings, two Z break stations and a water-service
    sleeve all travel with it. Left suppressed so the report stays clean while it is
    decided. **Do not quietly re-decide it either way.**
  - **`W-GF-S3` / `W-GF-N2` ARE A KEPT FOSSIL.** Those stem splits exist only because the
    brick returns once needed ledged stem under them. Both halves are plain `GARAGE_ICF_6`
    and nothing stands on them, but un-splitting would churn four wall uids and four footing
    uids to express no geometric change; the census in
    `test_wall_and_room_counts_by_storey` and `test_wall_structure_takeoff` pins the count so
    a cleanup cannot do it by accident.

- **The garage is white again, and the machinery that briefly made its east wall green is
  worth keeping.** `W-G-E` briefly carried Western States Metal Roofing **"Classic Green"**
  (westernstatesmetalroofing.com/classic-green) nail-strip and was
  reverted; all four garage walls are `GARAGE_WALL_2X6` in white today — and
  that white is `corrugated-panel-26`, not the nail strip this
  paragraph's machinery was built for. The machinery is unchanged and still works; the green
  revert would now be a `corrugated-panel-26`-based colourway, or a return to nail strip
  first.
  `standing-seam-nailstrip-26-green` is still in the catalog, **referenced by nothing** —
  the same convention `glazed-green-brick` is kept under, so going green again is a one-line
  `layer_materials=` change rather than a re-derivation. Two things were built to make it
  work, both still live:
  - **`Wall.layer_materials`** (`model/refs.py::LayerMaterial`) swaps the material of ONE
    named layer on ONE wall. Before it, a colour change *was* a duplicate Assembly restating
    one `material_ref` — and a duplicate assembly tag is also a new `prices.toml` row, a new
    `condition_gates` key and fresh section goldens, all to say "same wall, different paint".
    It is a TUPLE of constructors, not a mapping, because `Wall` is a movable element and the
    editable dialect has no mapping literal. **Appearance only** — thickness, function,
    framing and banding all stay the assembly's; a layer that needs a different *thickness*
    is a different wall and wants its own assembly. A typo in either half is otherwise
    silent (the wall just resolves unchanged), so `integrity.wall_layer_material` FAILs on
    an unknown layer name or material tag.
  - **Both renderers hardcoded the coil white** and had to stop. Every metal skin authors
    `color="#6b7076"` — that is the *drawing hatch* tone, not the paint — so the viewer and
    the GLB emitter both painted seam cladding 0xE8E8E2 unconditionally, and no panel could
    ever state its own colour. Both now consult the material's **declared `finish`** first
    (the mechanism `metal-dark-exterior` already used): `classic-green-seam` → `#2f5233` in
    `FINISH_BASE` (ui/src/nordic/palette.ts) and `_FINISH_BASE` (emit/gltf/palette.py), kept
    in step BY HAND. The green material keeps "seam" in its tag so it still gets the seam
    normal map, and keeps `skin_family="standing-seam"` so the roof edge still reads the
    garage as one continuous skin.
  - The **gable triangle above a wall comes along for free**: `resolve/roof_edge.py` builds
    the wall→roof closure from the host wall's own layers, so an override picks up in the
    closure with nothing authored for it.
- **The garage's roof edge is one coil — fascia and ridge cap both — and it is the house's
  exterior dark.** `metal-dark-exterior` (`#1c1f24`) carries seven members here: the six
  fascia pieces and the vented ridge cap. **The two are named through DIFFERENT fields and
  nothing keeps them in step but this line and one assertion** (`test_model_json.py` pins
  both tags).
  - **The fascia is six pieces** — two eaves and four rakes — named on the `FasciaBoard`
    inside `_GARAGE_EAVE_TRIM` (`plan/storeys/garage.py`); the 2x6 spf sub-fascia nailer
    behind it is unchanged.
  - **The ridge cap is `Roof.edge_trim_material`** on RF-GARAGE, not a fascia field. That
    field drives the ridge cap **and the corner trim**
    (`resolve/roof_trim.py::_edge_trim_material`); a 16" overhang frames fascia + soffit and
    **no** corner trim, which is the only reason naming it recolours exactly one member.
    Give this roof a zero overhang and the trim colour would spread to the corner trim too.
  - **So changing the accent colour is a TWO-PLACE edit.** Change one and the cap and the
    fascia under it drift apart — a cap in a different colour from its own fascia reads as a
    mistake rather than as a choice.
  - **The garage wore "Copper Penny" PVDF metallic here from 2026-08-26 to 2026-09-08**, and
    was the one place on the site departing from the house's single exterior dark. It no
    longer is: the garage's own accents are now the Classic Green door wall and the Charcoal
    Gray stem band. `metal-copper-penny` is **kept and referenced by nothing**, the way
    `metal-fascia-regal-blue` is, so coming back is a one-word swap in the two places above.
  - **The fascia's SUBSTRATE changed with the 2026-08-26 colour, and that half must not be
    reverted.** The weather face was 5/4 cellular PVC; a dark trim colour on cellular PVC is
    the classic failure — PVC's thermal movement forces a solar-reflective vinyl-safe coating
    and trim makers cap the LRV outright, and `#1c1f24` is further past that cap than the
    metallic was. Formed metal over a wood nailer has neither problem and is the ordinary
    detail on a metal-roofed building. **The SOFFIT stays cellular PVC and stays white**:
    vented, out of the weather, and white is what keeps an overhang from reading as a
    shadow.
  - **Tag-keyed in the two renderer palettes**, not keyed by a declared `finish`: a fascia
    and a ridge cap are framed MEMBERS, and `memberColor` is handed the palette and no
    catalog, so a material's authored `color` is invisible to it and only the tag lookup
    reaches. `_FINISH_BASE` (`emit/gltf/palette.py`) and `FINISH_BASE`
    (`ui/src/nordic/palette.ts`), kept in step **by hand**. `metal-dark-exterior` already had
    its rows, so this swap added none — and the `metal-copper-penny` rows stay while that
    material does.
  - Neither tag contains **"seam"**, deliberately: both renderers key the ribbed
    standing-seam finish off that substring and this is flat formed stock. Trim carries no
    `skin_family` either — that field is about the wall/roof continuous-skin reading at a
    zero-overhang edge, and trim is not skin.
- **The garage ICF stem is covered on BOTH faces above grade, and the second face was
  missing until 2026-09-02.** `notes/garage_wall_detail_side.md` has always asked for
  protective covering on both sides of the exposed EPS; only the inside was built.
  - INSIDE, `code.R316_4`: a 5/8" gypsum layer banded from the `GRADE` datum up — the 2.5"
    of interior EPS stood bare from the slab to the stem top, ~176 SF of foam plastic facing
    an occupied space. It continues the board `GARAGE_WALL_2X6` already lines with, so it is
    the same detail, not a new one.
  - OUTSIDE, new: `coil-gap` + `coil-ext`, a PVDF-painted aluminium band
    (`aluminum-flat-pvdf`) from **2" below grade** to the stem top, on a **1/4" vented
    standoff**, fixed with 316 stainless gasketed screws into the ICF webs. 156.2 SF,
    $781-1,562. **Since 2026-09-03 this is the garage's entire base skin** — see the
    no-wainscot entry above — and its top is flashed by `STEM_TOP_Z_FLASHING`.
  - **THE STANDOFF IS NOT OPTIONAL AND IT IS NOT ABOUT DRAINAGE.** A painted sheet is
    **0 perms**. Laid flat on `eps-ext` it is a Class I retarder on the COLD side of the
    stem, and `building_science.condensation` immediately found a January dew point at the
    concrete — a crossing against a monthly MEAN, i.e. a plane that runs wet for weeks. That
    was a real FAIL on the first build of this change, not a modelling artifact. The 1/4"
    gap restores the outward drying path. Delete it and the FAIL comes straight back.
  - **It ran BEHIND the east wainscot too**, deliberately: that wainscot was a vented,
    drained rainscreen open at its base, so water reached the foam behind it by design and
    that foam needed the same continuous protection as the foam beside it. The wainscot was
    a wear layer over this band, never a substitute for it — **which is exactly why deleting
    it on 2026-09-03 took nothing away from the two east piers, and why 156.2 SF did not
    move.**
  - Both bands are banded, not full height: below grade there is no interior to separate
    anything from, and the exterior band's 2" of bury seals its own termination rather than
    leaving a lip for water to stand on. The band pushes the stem's exterior face 0.30"
    east, which nicks the "stem and wood wall are coplanar on the outside" promise — inside
    `_axis_match`'s 1/2" and physically true. **Do not recess the EPS to hold the face
    still**; that re-opens the old rain shelf.
- **One exterior dark, `#1c1f24`**, carried by every dark metal element on the
  envelope so they read at one weight: the opening casings, the roof's rake/eave/ridge trim
  coil, the eave water chain (drip edge, box gutter, downspouts), and the guards.
  - Every window in a clad wall ships a picture-frame casing
    (resolve/geometry_openings.py `exterior_trim`), and every opening in a clad wall —
    doors included — draws its frame/mullion/stile boxes in the same tone. Recolor =
    emit/gltf/palette.py `window_trim` + ui/src/three/members.ts
    `CATEGORY_COLOR.window_trim`, nothing else.
  - The roof edge, the water chain and the guards get there by *material*, not category:
    `metal-dark-exterior` in the catalog, named by `RF-HOUSE.edge_trim_material`, by
    `params/roof_trim.py::_CHAIN_MATERIAL`, and by the `RAILING_DARK_METAL` assembly. Both
    renderers resolve it through `_FINISH_BASE` (emit/gltf/palette.py) and its mirror
    `FINISH_BASE` (ui/src/nordic/palette.ts) — keep the two in step.
  - A gutter/downspout is a *solid*, not a framed member, and a solid could only say "I am
    category gutter" until `ResolvedSolid.material` was added — which is why
    the eaves stayed mill grey while the rakes went black. A solid's own material now wins
    over its category palette in both renderers, but only when it *states* a colour (a
    named finish, or a catalog material with an authored `color`); a generic ref like
    `"aluminum"` still falls through to the category, so nothing else in the model moved.
  - **Why `#1c1f24` and not the `#3a3d40` it started at:** an authored colour is an albedo.
    The viewer lights with 0.8 hemisphere + 0.9 key + 0.6 IBL, over unit irradiance, so a
    dark surface leaves the shader well above its albedo — `#3a3d40` arrived near `#525252`
    and read as generic grey. Author under the tone you want on screen.
  - Guards are `RAILING_DARK_METAL`, split off `POST_WHITE_PAINT` for this. The balcony's
    **two** remaining 6x6 pillars and the stairwell posts still use `POST_WHITE_PAINT` and
    stay white — that shared assembly is why they must not be recoloured together. It was
    six pillars and eight knee braces until 2026-09-03; the four corners are cast concrete
    now and the braces are gone (see the balcony structure passage below).
- **The balcony's structure: four cast columns, two wood posts, three glulam beams**
  (2026-09-03; `houses/catlin/notes/balcony_moment_columns.md` is the design, and it
  supersedes `superseded/balcony_lateral_bracing_design.md`).
  - **The four CORNER pillars are 12" round reinforced concrete, FIXED at the base**, doweled
    into the 12" wall tops of `W-SG-W1`/`E1` they stand on, and **they are the balcony's
    entire lateral system in both plan directions.** The eight 2x6 knee braces and two E-W
    brace rails they replaced are deleted outright. This was the longest-running open item in
    `plans/TODO.md`, and it closed against metal rather than for concrete: **no catalog metal
    moment base survived.** The only stock base with a published base moment is Simpson's
    MPB66Z, for a WOOD post, and its wet-service cap (2,610 lb-ft, ESR-3050 Table A) is
    *below* the 2,502 lb-ft R301.5 guard case on one column before any wind.
  - **12", not 10", and cover is the whole reason.** ACI 318-19 §20.5.1.3's 1-1/2" is a code
    minimum, not a hundred-year number; MnDOT uses 2.5-3" in the same deicing regime. 2" of
    cover on a #5 cage inside #3 ties needs a 6-5/8" bar circle, which needs 12". Centred on
    a 12" wall the round is flush with BOTH faces — no ledge to pond on, and BF3's 3" east
    leader keeps 1-1/2" clear. One assembly, `SUNKEN_GARDEN_COLUMN_12`, serves all five cast
    columns in this structure; `SUNKEN_GARDEN_COLUMN_20` is retired with the 20" round.
  - **Exposure is class F3 + C2, not F2**, and the mix must not be reused from the retired
    20" column: deicing salt below and planter runoff above is external chloride on a
    freeze-thaw member. w/cm <= 0.40, f'c >= 5,000 psi, 6% +/-1.5 air. Bar is **hot-dip
    galvanized** (ASTM A767 cl. 1 or A1094) — the owner's call over epoxy (delaminates) and
    stainless (4-6x, and an austenitic thermal coefficient that fights the concrete).
  - **The beam seat is CAST TO LINE, with no grout island.** An exposed non-shrink grout
    island is a 10-20 year element, not air-entrained and sitting at the wettest point on the
    column. Cast the top to line under the beam footprint, screed the >=15 degree wash and
    drip lip around it, and take tolerance in the `SS316-SHIM-35` standoff shim pack —
    a modelled, priced part at `CN-SG-STDF-*` since 2026-09-03, one per wood-on-concrete beam
    seat. An HGAM10 gusset holds the beam down, Titen Turbo at ~3-3/4" edge on the 12" round.
    `PIER_CONCRETE_12` still carries a grout island at `PT-SG-COL`; aligning it is a
    follow-up, not an oversight.
  - **The two CENTRE pillars stay wood 6x6**, bearing DIRECTLY on the porch framing through
    a ~9"-square plank cut-out — Trex says plainly that composite decking bears nothing, and
    the cut has to clear a 5-1/2" post plus the `L50Z` angle legs beside it — on a
    **3-ply bearing pack** (the authored joist plus two full-length sisters) with squash
    blocks at the beam line. `PT-SG-BF2` moved north onto the deck, which is what let
    `PT-SG-FCOL` shrink from a 20" round to a 12" one, and then the last 3" onto the front
    beam axis itself, where it doubles as the `RL-SG-PORCH` south-leg guard post at x 18'-0".
    A `CCQ46SDS2.5` column cap closes the uplift path at each — a 3-1/2" beam on a 6x6 is
    the unequal-width case the PC6Z is not published for. **The porch joists CROSS both
    beams** since 2026-09-03: `JoistSpec.cantilever_start = 2-3/4"` runs them past the front
    beam instead of stopping on its centreline, which takes both bearing planes at
    `PT-SG-BF2` out of NDS §3.10.4's END case (d/c 0.76 -> 0.35) without moving the pillar.
    The composite sheet followed the framing, so the plank now ends 2-3/4" outboard of
    `RL-SG-PORCH`'s guard line — a deliberate setback, since the guard blocking sits in the
    bay north of the beam and a guard on the new edge would bolt into cantilevered tips.
  - **No standoff post base at either.** The `ABU66SS` went on 2026-09-03: every published
    value an ABU has is measured bearing on CONCRETE through a 5/8" cast-in anchor
    (ESR-1622 §5.6 puts even that anchor outside its own scope), and the 1" standoff was
    cited to IRC R317.1.4, which governs wood on concrete. Neither pillar has stood on
    concrete since. **A `MSTA12Z` strap plus `L50Z` angles** hold each down instead, mixed
    by what each face has beside it: the strap on the one flush vertical pair (both west
    faces at x = 213.25"), an angle wherever there is joist pack to screw into — north at
    both pillars, south at `PT-SG-BR2` alone. Five elements for two pillars, ~$25 the lot,
    1,408 lbf at BR2 and 1,033 lbf at BF2 wet-derated against a hand-worked ~285 lb net
    uplift. **An inverted `CCQ4.62-5.50SDS` cap stood here for one day and CANNOT BE BUILT**:
    at BF2 the rim, joist tips, beam axis and post centre are one line, and at BR2 the squash
    blocks occupy the bays its side plates would hang in — and it was ~20x the demand. Do not
    reach for a part that wraps this joint. The post now stands on the pack with no plate
    between it, wood on wood. The bearing that replaced the ABU is graded:
    `haus engineering --item post_bearing/PT-SG-BR2`, oracled in
    `notes/centre_pillar_bearing.md` — at `plies=1` and against a DRY Fc-perp both pillars
    were over, at 0 FAIL, until that calculation existed.
  - **The two centre pillars are DF-L, not SPF, and the species is a connector requirement.**
    `ESR-2604 §3.2.2`, `ESR-2330 §3.2.2`, `ESR-2105 §3.5.2` and `ESR-3096 §3.2.2` are the
    SAME sentence — SG >= 0.50 at MC <= 19%. At SPF 0.42 **nothing at either end of these two
    posts had a published value** — the `CCQ46SDS2.5` cap on top included. DF-L at 0.50 fixes
    both ends for ~$180-450 of lumber; see `POST_WHITE_PAINT_DF`. The clause being
    family-wide is why that call survived four base parts in one day: only the citation
    moves. **One** condition rides on the seal — MC <= 19%, which an open deck is not. The
    other half is resolvable and IS applied: both reports' §4.1 send wet service to the NDS
    factor, so C_M 0.70 is already inside the 658/375 lbf recorded in `library/hardware.py`.
    Do not derate again. A `DTT2Z` stood here for part of 2026-09-03 and was superseded
    unbuilt — one-sided, no lateral value, and it did not touch the species problem.
  - **The three beams are treated SYP glulam, 3-1/2" x 11-7/8"** (24F-V5M1/SP, Anthony Power
    Preserved / Boise Cascade), clear-finished rather than painted, with no ply seam to hold
    water. Author the size DECIMALLY — `"3.5x11.875"` — or `_RE_NOMINAL` catches a
    nominal-looking string and silently resolves 1-1/4" of depth away. They are engineered
    items (`deck_beam/BM-SG-BL*`): R507.5(1) publishes sawn plies only.
  - **The front row did NOT move when the corners changed.** A 12" column's top runs 3-1/4"
    past the beam end there, and that is a concrete top with a wash and a drip lip, not the
    exposed end grain the 2-3/4" offset was written for. Re-solving the row would move the
    deck edge, the fascia, the drip, the gutter and `BALCONY_FRONT_AXIS_Y_FT`.
  - **The fallback, written down:** New Castle Steel's stock HDG 6x6x3/16" post with a welded
    base plate (~$458/10') if forming and caging four tall tubes proves too much labour. Its
    base still needs a fabricated saddle on a 12" wall top, which is a shop drawing nobody
    has made.
- **Both guards are Williams Architectural Products, ICC-ES ESR-3485, 42" black** (Menards;
  Eagan MN, the Ultralox factory), with Fortress Al13 Home as the alternate — the same alloys
  and coating as Trex Signature at ~$30-45/LF material against $72-98. **The two mounts
  split, and the substrate decides it:**
  - `RL-SG-PORCH` is **surface**-mounted on its own house-local `RAILING-EXT-ALUMINUM-SURFACE`
    type: its west and east legs run along 12" concrete wall tops, which take ESR-3485's four
    1/4" x 3" baseplate anchors directly and buy no bracket kit. Its SOUTH leg has no wall
    under it, so those posts bolt through the plank into blocking in the joist bay north of
    the beam — **never through TR-SG-CAP-FRW/FRE and its butyl**, which is the dielectric
    between an aluminium cap and copper-treated framing.
  - `RL-SG-BALCONY` stays **fascia**-mounted, and that is a roofing decision. `FS-SG-DECK`'s
    aluminium plank is the porch roof and has carried NO penetrations since the heat pumps
    went to grade; surface posts would put ~36 holes through the only waterproof plane here.
    Brackets through-bolt the PVC fascia and the 2x8 rim per Ultralox's own instructions
    (four 5/16" x 4" bolts, nuts on the rim's inside face), landing in rim blocking authored
    in `FS-SG-DECK.reinforcements`.
- **The veneer stands on a grade beam, not on the house footing** (2026-09-05). `W-B-BRICK`
  is 129 SF of masonry exposed on **both** faces at the bottom of an open court, so it runs
  at outdoor temperature all winter. It used to bear on `FT-B-BRICK`, a 10"x5" plinth cast on
  `FT-B-S2`/`FT-B-S3`'s own projecting toe — putting that cold in series with the footings
  whose underside is level with the court floor and whose only frost protection is the R403.3
  wings. It now bears on **`W-SG-BRKBM`**, a 12" x 17 3/4" beam spanning the court's 19'-0"
  between `W-SG-W1` and `W-SG-E1`. Basis: `notes/sunken_garden_veneer_beam.md`.
  - **The break was ordered twice and placed never, and that is the lesson.** `FT-B-BRICK`
    carried `assembly="FOOTING_FPSF_20"`, whose 2" `xps-bearing` layer *did* bill — 16.0 SF
    through `takeoff/envelope.py`'s `_LAYERED_SOLID_SCOPES` — while `FB-B-BRICK` dug a 2"
    `undercut` for that same 2" of space which billed as 0.1 cy of washed crushed stone, with
    `cast_foam_in_aggregate=True` beside it carrying no thickness, no material and no
    R-value. A `Footing` resolves to ONE extruded blob, so neither claim ever had a polygon.
    **Nothing in this engine grades a thermal break for continuity**, so one order of foam
    and one order of stone for one gap sat at 0 FAIL for a fortnight.
  - **A better bed was not available — the geometry says so.** The wythe sits inside the
    footings' 10" toe, and any separate pour bearing on soil has to stay outside the 45 deg
    line off their bearing edge, at y = -12.76". That pushes the brick to -15.95" and opens
    an 11.9" slot to the house: a 19-ft-long, 11.5-ft-deep snow trap with no way to reach the
    bottom. **A beam that SPANS needs no soil bearing, so that constraint does not apply** —
    which is the whole reason this shape was chosen and the reason the gap can be 6".
  - **It reinforces nothing, and do not let anyone say it does.** The tempting story is that
    a beam closing the court's north end props the side walls. It does not: `W-SG-W1`/`E1`
    are already restrained top and bottom (porch beams pocketed in HUCQ410-SDS hangers, the
    deck diaphragm, the garden slab at their feet) and PASS
    `structural.foundation_unbalanced_fill` on the last published row of IRC Table
    R404.1.2(8). This beam earns its ~1.05 cy on the thermal argument alone.
  - **The 2" board is a `Layer`, on a WALL, and the face is asserted.** `SG_VENEER_BEAM_14`
    is the court's 12" pour plus 2" of 40 psi XPS. A wall's layers resolve to real polygons
    on real faces in a stated order, which a Footing's do not — that is the whole reason it
    moved here. **The face is not reliable on its own**: the beam is its own open wall-graph
    chain, so it takes the FALLBACK outward sign, and sign x layer-order decides whether the
    board builds north or south. Authored the wrong way the concrete lands hard against
    `FT-B-S2/S3` and looks perfect in every view.
    `test_catlin_contract_m3.test_the_veneer_beam_isolates_the_house_footing` pins both faces
    in absolute coordinates. Do not trust the sign.
  - **`FT-B-S2`/`FT-B-S3` gave up 2" of south toe, by `offset` and not by width.** The strips
    keep all 20" of bearing and simply sit further under the house; since they carry a 7 1/4"
    curb and three storeys of framed wall standing at y = 0..+9 1/2", moving toward the load
    *reduces* the eccentricity they already had. Their south face is at **-8"** now, and the
    board occupies -8"..-10". Anything that re-centres these footings has to keep that face.
  - **The wythe moved 4 1/2" south and the reveals did not move at all.** On 2026-09-04 the
    6" was taken entirely in `BASEMENT_BRICK_VENEER`'s `air-gap` THICKNESS with the nodes
    held still; on 2026-09-05 the EPS moved the backup's face and `N-B-BRICK-W`/`-E` followed
    it to **-8.05"** while `air-gap` came down to 2", the opposite bookkeeping. Either way
    the invariant is the BRICK's own y, which the beam fixes at -10.05..-13.675" and nothing
    else may move. The reveals are safe under both because `AO-B-BRICK-WIN`/`-DOOR` are
    placed `from_node` along the wall AXIS — a y-move leaves them concentric and
    `integrity.reveal_concentric` still passes.
    `N-B-BRICK-E` did have to come in from 28'-0" to 27'-6": 28'-0" is `W-SG-E1`'s axis, and
    the move walked the wythe's east 6" *inside* that retaining wall — 4.25 SF of brick
    billed into solid concrete, at 0 FAIL, because nothing grades masonry against a pour.
  - **2" of EPS went into that cavity 2026-09-05, and it is on the BACKUP wall, not in
    `BASEMENT_BRICK_VENEER`.** The 6" is fixed — the beam's north face cannot pass -10" —
    so the only question was how to split it, and it is now 2" EPS + 4" of drained air.
    The foam is a layer of `_GARDEN_CURB_CORE` / `_GARDEN_FRAMED_OUTBOARD`, the two outboard
    tuples the four backup walls share and **nothing else uses**, so the blast radius is
    exactly `W-B-S2`/`S3`/`S2-FR`/`S3-FR`. Putting it in the veneer's own stack would have
    been worse than untidy: `code.energy_prescriptive` grades one assembly at a time, so
    foam parked there earns the wall no R and the check keeps reading R-37.0. It reads
    R-45.0 now (R-58.4 sauna, R-29.3/R-43.3 curbs), each exactly +8.0.
    - **The energy is a rounding error and is not the reason.** The backup was already
      R-37/R-50 framed, not the R-21.5 a `BASEMENT_8` reading suggests — about
      **$2/year** at 124.9 SF. The $250-487 buys a *designable anchor*: the beam already
      forced a ~10" brick-to-stud reach, and 6" of that was unbraced air. Now 6" is foam
      and 4" is cavity. **The anchor is still engineered** — see the note, §5.1.
    - **EPS and not more XPS, deliberately.** The stack is already 4" XPS plus damp-proofing
      at ~0.13 perm and can only dry inward; EPS at ~2 perms over 2" adds R without adding a
      second vapour shutter and lets the wall dry OUT into the vented cavity. It also beats
      XPS in long-term ground contact, and this run's foot is in a court that can pond.
      ASTM C578 **Type II** (15 psi) — do not substitute Type I.
    - **`IRC R703.15`'s 4" foam limit does NOT govern here, and the trap is real**, because
      `plans/cost-options.md` §6 kills a *different* foam swap in this house on exactly that
      limit — and this wall now carries 6". R703.15 covers cladding whose dead weight hangs
      on a fastener in bending, and it **explicitly excepts anchored masonry veneer to
      R703.8**. This wythe stands on the beam; its anchors take wind only.
    - **2" AND NOT 4", AND NOTHING GRADED EITHER BOUND.** 4" was built first and sat at
      0 FAIL. It was wrong twice over. (a) `EXT_2X6` stands on this wall's seat with
      its cladding face at **-7.25"**; 4" put the basement's face at -8.05", 0.8" PROUD of
      the wall above, turning the Z-flashing lap that the basement skin is supposed to tuck
      under into an upward-facing ledge. 2" lands at -6.05", a 1.2" setback. (b)
      `resolve/stacking.py` fires `stack_width_change` on |total thickness| against a 0.5"
      `_TOL`, so any thickness added here reshuffles **which junctions get a detail drawn**:
      4" pushed `GARDEN_CURB_6` inside the tolerance and 3" pushed
      `GARDEN_FRAMED_2X6` inside it, each silently deleting a live junction's
      drawing. **2" is the only purely ADDITIVE value** — every HEAD golden survives and the
      two sauna walls gain the detail they now warrant. The golden SET drift is what caught
      this; no check did.
    - **`eps:2.0` is a new price key, for LABOUR not thickness.** 2" is what the bare `eps`
      row was already researched at, so the material rate carries across untouched; what
      does not is open-wall CI labour. This board is set in a slot behind a wythe laid after
      it, held by the veneer anchors, its bottom course worked out of an 11-1/2 ft hole:
      $1.10-2.10. `envelope_layers` qualifies on `thickness_in` only, so any other 2" EPS in
      this house would silently inherit the cavity labour. There is none today.
  - **Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to cut the anchor count.** It cannot
    carry: unreinforced 3-5/8" brick spanning 18'-8" horizontally runs ~400 psi of flexural
    tension at 20 psf against ~50 psi allowable parallel to the bed joints. And it is the
    wrong detail regardless — brick grows, concrete shrinks, and BIA TN 18 puts ~0.15" of
    movement across that run. Those two ends want a **soft joint**, not an anchor. The model
    carries no soft joint and nothing in the engine grades one.
  - **Two engine bugs fell out of this and are fixed.** `local_grade_elevation_m` sheltered a
    footing whose CENTROID sat inside the heated slab, so trimming a perimeter toe 2" walked
    it over the line and turned 3/4" of frost cover into a reported 83" — whole-polygon
    containment now. And `_exterior_shells_by_storey` filled every interior ring, which was
    invisible only while the court was a *disjoint* polygon; the beam connects it to the
    house, and 610 sf of open sky became basement floor area until holes over an open
    excavation floor were kept.

- **The court is ONE surface again, with a single 7 1/4" riser at `D-B-PATIO`** (2026-09-05).
  `SPEC.court_step_down_in` is back to **0**, so `SL-SG-FLOOR` is flush with the basement
  floor plane and the whole 532 sf reads as one floor. Owner's call. It had been dropped
  7 1/4" on 2026-09-03 as a flood step, which is why there were four elevations in a 19'
  court: the court, a 23.7 sf stoop a riser above it, `W-SG-ARCH` standing 3 3/4" proud as a
  mow strip, and the veneer beam.
  - **What it costs is half the freeboard, and that is the trade that was taken.** Water
    climbs 7 1/4" to the threshold instead of 14 1/2" — 321 cf of ponding over the court
    rather than 643, against ~191 cf of direct 100-year/24-hour rain, so about **1.7x**
    where it was 3.4x with the drywell assumed fully failed. The case to watch is not summer
    rain but **snowmelt over a frozen grate**, where DRW-SG-MAIN contributes nothing by
    definition. The 7 1/4" curb is now the entire dam.
  - **7 1/4" is not a preference, it is the only legal court elevation.** R311.3.2 allows one
    riser of 7 3/4" (`_MAX_NONREQUIRED_STEP_DOWN`) at a non-required door that swings inward.
    Lower the court and the step needs a landing; that is exactly what `SL-SG-STOOP` was, and
    why it existed for two days. **The stoop is retired** (uid `SGS503AAAA`, never reuse) —
    the court IS the landing, and `code.R311_3_exterior_landing` now reads "D-B-PATIO lands
    on SL-SG-FLOOR, 7.3" below the threshold".
  - **`W-SG-ARCH` did not move and must not.** It is the only real strut here — it carries
    Pu 62,051 lb and closes the walls' loop before backfill — and dropping its top to the rim
    underside gives phi-Pn 60,712, **d/c 1.02**. Its top and `_rim_underside_in` are now the
    same expression, so the rim bears on it and **`FO-SG-ARCH` is retired** with the stoop.
    `W-SG-BRKBM`, by contrast, carries nothing structural: it is the veneer's thermal
    foundation only.
  - **Two things were PINNED rather than allowed to follow the court up. One of them has
    since been un-pinned; the other must stay.**
    - `_pier_bell_bottom_ft` was pinned for a day and is **DERIVED again** (owner's call,
      later on 2026-09-05): `(_court_top_in - frost_depth_in) / 12`, so both bells carry
      exactly **42"** of cover rather than the 49 1/4" the pin left them with. The pin's
      argument — 0.1 cy of shaft against re-opening every hand-worked term in
      `notes/sunken_garden_piers.md` — was real and was overruled: a pinned literal is what
      silently drifts the next time the court moves, which is precisely how it got to
      49 1/4". The note and both pier test modules were re-worked; the shafts are 128.1875"
      again, exactly what they were before the flood step.
    - `_veneer_beam_bottom` was the garden slab's underside. Flush, that gives a 10 1/2"
      beam over a 19'-0" span, under ACI 318-19 Table 9.3.1.1's L/16 = 14 1/4" minimum depth.
      Held at -120 3/16" so the graded 17 3/4" section survives; the beam is simply buried.
      **This one stays held.**
  - **Frost got BETTER, which is the quiet win.** `FT-B-S2`/`S3`'s cover below `SL-SG-FLOOR`
    goes 1" -> **8"**. The R403.3 wings still do the work, but they are no longer carrying it
    on a fingernail.
  - **`plan/site.py`'s two garden spot elevations had to follow** (-9'-8 11/16" ->
    -9'-1 7/16"), and the comment beside them claiming *"nothing structural reads spot
    elevations — they are drafting annotation"* **was false**.
    `engineering/balcony_wind.ground_below_ft` takes the lowest spot on the site and these
    two win it, so they set `z` for the balcony columns: h 23.3' -> 22.7', q_h 18.8 -> 18.6
    psf, wind base moment 1,395 -> 1,385 lb-ft. Safe direction, no column re-sized, and the
    guard case (2,502 lb-ft) governs regardless — but `notes/balcony_moment_columns.md` and
    `test_pier_calcs`'s schedule both had to move with it.
  - **A latent bug in `space_summary` surfaced here.** The interior-hole filter I added on
    2026-09-04 kept a ring only if it `contains(floor.representative_point())` — ONE point
    per floor — so a floor spanning several rings anchored only one. `W-SG-ARCH` splits the
    court into two bays, both `SL-SG-FLOOR`, and the stoop happened to anchor the second;
    retiring it filled **281 sf** of open court onto the basement's gross area. It is an
    area-overlap test now, which asks the question actually meant.

- **The court's second pass: the porch side joins the lift, the run is capped at 36" above
  grade, and the well is tied to the footings that feed it** (2026-09-05, after the
  re-levelling above). Four separate defects, all found by looking at the model rather than
  by any check — none of them was a FAIL, and none of them could have been.
  - **`SPEC.retaining_top_ft` is derived from grade now**, `(site_grade_in + 36)/12` = +0'-2".
    It was +0'-6", i.e. **40"** out of the -2'-10" yard. One constant does two jobs, because
    `params/raised_garden.py` reads it through `RETAINING_WALL_TOP_FT` as its apron TOP and
    derives BASE as `TOP - drop_ft`: capping the top at 36" lands the SRW base on -34",
    **site grade exactly**, where it used to float **4" in the air**. Nothing grades a
    freestanding wall's base against the ground plane, so five `W-RG-*` legs stood on nothing
    at 0 FAIL while the comment beside them claimed "their base is grade".
  - **`W-SG-W1`/`E1` bottom on `_wall_bottom` like everything else**, and
    `_PORCH_FOOTING_THICKNESS_IN` is gone. They were held back when the three retaining
    strips rose, to keep IRC Table R404.1.2(8)'s last published row (10'-0") and to stop the
    two 13"-thick footings' undersides moving. **Both arguments were weaker than they
    looked**: 10'-0" is a ceiling, not a target — a shorter braced wall over less fill sits
    further inside the same row, and the check still PASSES at 9'-1 7/16" — and the frost
    answer at this edge was never cover but ASCE 32 soil replacement, which is the same 42"
    of stone whatever elevation the footing starts at. Holding them left the whole under-porch
    dig 9" deeper than the identical stack ten feet south, for nothing.
    - `FO-SG-TOE-N-W`/`-N-E` void the rim over them, as `W`/`E`/`S` do over the other three.
    - `FO-SG-TOE-W`/`-E` were cut to the FIELD's north edge and the footings run 6" past it,
      so each left a 4'-0" x 0'-6" tongue of footing under 3 1/2" of rim — **2.0 sf of
      concrete billed twice and cast into itself**, at 0 FAIL, because
      `structural.concrete_interference` grades only ISOLATED pours and every `FT-SG-*`
      carries `under=`. The toes are cut to `_y_ax_mid` now. **The assertion worth keeping is
      that the net rim polygon's intersection with every `FT-SG-*` footprint is 0.000 sf.**
  - **`DRW-SG-MAIN` sits on the WALL beds again, and two lead runs make the tie visible.**
    The well's top was pinned to the DEEPEST bed. That was right while every bed shared one
    underside; after the lift it left the five tiles that actually feed it discharging **9"
    above the top of the stone**, into undisturbed clay. `drainage.discharge_consistency`
    resolves the tag and never asks where the pipe goes, so it passed.
    `_SG_DRYWELL_TOP` is `_SG_WALL_BED_BOTTOM` now, and `FD-SG-LEAD-W`/`-E` carry the ring
    across the 3'-0" of open ground into the well at that invert — **two, not seven**, because the five wall beds abut
    into one connected body of stone (W1 to W2 at y = -11.0', W2 to S through the corner lap)
    and the east side mirrors it. `FB-SG-ARCH` takes none: its bed bottoms 9" BELOW the well
    and stops 2" from the shaft in plan, so it feeds the column through its side and a lead
    there would run uphill.
  - **The dowels were above the footing they dowel into.** `_dowel_z` read
    `-(basement_depth + 0.75) + footing_thickness/24` — mid-height of a garden footing whose
    underside was -118 7/16", two elevation changes ago. The bars resolved at -112 7/16" with
    the garden footing's TOP at -117 7/16": three #5 GFRP bars **5" of open air** above the
    concrete they develop into, and a 12" foam block straddling a joint that was not there.
    Nothing grades a `Dowel` against the two footings it names. Derived off the joint now —
    mid-way through the 8" face the two footings actually share, with the foam block that
    same 8" so it fills the joint instead of standing proud into the slab bed.
  - **What it is worth: 2.32 cy of concrete** (151.10 -> 148.78) and 9" off the whole
    under-porch excavation and the well shaft. Every yard of it was concrete being poured on
    top of something. The engineering all moved the safe way — stem 9.62' -> 9.2865', system
    FS 1.71 -> **1.77**, stem flexure 0.72 -> 0.65, toe flexure 0.61 -> 0.56 — and
    `notes/sunken_garden_court_free_body.md` §4/§6/§7 are re-worked term by term rather than
    recomputed from the engine.

- **The closure's thermal break was 21" long in an 84" joint** (2026-09-05, third pass).
  The two porch side walls meet the house only through a 2" XPS board on -6 3/16"..-4 3/16",
  and the intent — written out at `DW-SG-*-STEM` — is *one continuous board from the house
  footing's underside to the top of the porch wall*. It was not continuous, in two
  independent ways that hid each other, and **nothing in this engine grades a thermal break
  for continuity**, so it read as a designed detail at 0 FAIL.
  - **The block was sized against the WALL, not the FOOTING.** `_resolve_dowel` derives a
    foam block's length along the joint from the bar row — `max(row_span + 8*dia, 12")` —
    which is exactly right for the stem block (12", flush with a 12" wall's end face) and
    wrong for the footing block, which separates an 84"-wide strip. Three bars at 8" gave
    21", leaving **63" of footing-to-footing concrete** running from a heated basement
    footing into a wall that stands in an open court. `Dowel.foam_length` is new for this:
    unset it derives as before, so nothing else in the repo moved. **Do not tidy the two
    blocks into one rule — they are sized against different pours.**
  - **And where the board was missing there was no room for it.** `FT-SG-W1`'s 84" north end
    faces `FT-B-S1` over its outer 52" and `FT-B-S2` over its inner 32". S1/S4 took a 6" toe
    trim on 2026-09-05 and cleared it by 2 3/16"; S2/S3 kept the 2" `offset` bought for
    `W-SG-BRKBM`'s isolation board and **lapped it by 1 13/16" of solid concrete** — a plan
    lap until the porch footings rose to the court plane, a real 0.406 sf x 8" volume after.
    Which strip a given inch of that joint faces is an accident of where `W-B-S1` stops at
    x = 8'-10"; no thermal detail should turn on that. **All four south strips are on one
    face at -4" now**, `_TOE_TRIMMED` is empty and `_SOUTH_TOE_TRIM` is superseded.
  - **The beam's own board is not weakened by the retreat.** It still separates the veneer
    pour from the house pour, across 4" of bedding stone in series with the same 2" of XPS,
    and `W-SG-BRKBM` bears nothing on that toe — it spans between the side walls. What the
    2" was genuinely load-bearing for is the BEAM's north face at -10", which is a fact
    about the beam and did not move.
  - Frost re-checked after the trim, because moving a footing north is exactly how one buys
    a false pass: all four still read **"8" below SL-SG-FLOOR"** on the R403.3 branch, not
    the ~86" `sheltered_by` answer. `test_the_veneer_beam_isolates_the_house_footing` now
    pins the 84" board, the full 8" depth, and a zero plan lap against every house strip —
    both halves, because each passed on its own while the pair was broken.
  - `prices.toml`'s `thermal_break` row was re-based with it: it priced three ~0.3 SF
    structural bearing pads that no longer exist, and now bills the four closure boards
    (27.6 SF of 2" 40 psi XPS) at $90-210 each. The four are not the same size, so check the
    total against the SF rather than the count.
  - **Concrete does not move for any of this**, and that is worth knowing before reading a
    takeoff diff across this date: the toe trim is an `offset`, so each strip slides north
    with its full 20" of bearing intact. Measured by ablation against HEAD — every assembly
    row identical, total 149.31 cy either way — with the thermal break the only quantity
    that changes, 3.43 -> 4.60 cf. Any concrete delta seen across today belongs to another
    change, not this one.

- **The sunken garden's veneer is one flat field of unglazed buff brick** (2026-09-04).
  `W-B-BRICK` has now worn three faces: one flat field of `glazed-green-brick` (`#1b4332`),
  then the Ishtar Gate — a lapis field with golden-yellow register bands over an unglazed
  brown plinth — and since 2026-09-04 the plinth's own brick run full height. **The glaze is
  not wanted.** What is on the wall is `brown-brick` `#a07c5c`, ordinary ASTM C216 Grade SW
  face brick, the cheapest face that was ever on it and the only one a Twin Cities yard
  stocks off the shelf.
  - **The swap also settles a spec conflict.** [BIA Tech Note 13](https://www.gobrick.com/media/file/13-ceramic-glazed-brick-exterior-walls.pdf)
    says glazed brick *"should not be used in locations where they are likely to be
    saturated."* The Ishtar scheme complied only because the unglazed plinth kept the glaze
    above the splash line. An all-unglazed SW field is unconditionally right for a Minnesota
    sunken court, which is a rain sump with walls.
  - **`glazed-green-brick`, `glazed-lapis-brick` and `glazed-gold-brick` are all still in the
    catalog, referenced by nothing.** Any of the three schemes is a `material_ref` swap. Do
    not delete them, and do not delete their `MasonryStyle`s in `ui/src/three/materials.ts`
    or their `_FINISH_BASE` entries in `emit/gltf/palette.py` either — a material's
    appearance is a three-place change and the revert has to find all three. Their
    `prices.toml` rows are commented out rather than removed for the same reason.
  - **The jitter had to move with the job, and it is the one thing that did.** A material
    appearance is `Material` + `MasonryStyle` + `_FINISH_BASE`, and `#a07c5c` is unchanged in
    all three — it is already authored a step under its target for the albedo reason above,
    and re-darkening it is the mistake. `BROWN_BRICK_STYLE.jitterHSL` is NOT: it was
    `[0.004, 0.015, 0.04]`, the glazes' near-zero, and the reason was a **28 SF plinth beside
    a glaze**, where the red brick's full variegation read as mixed pallets with near-black
    units through it. The field is now **129 SF with no glaze to contrast against**, and one
    flat brown at near-zero reads as a printed sheet. It is `[0.008, 0.035, 0.09]` —
    deliberately intermediate, roughly double a glaze and half of `BRICK_STYLE`'s
    `[0.02, 0.08, 0.16]`, which is the failure mode in the other direction and one this
    material has already been in once. Mortar stays `#cfc8ba` (tan), the unglazed pairing.
    **`haus render` cannot show this and never could** — the CLI emitters carry only the flat
    de-jittered `_FINISH_BASE` hex (`emit/gltf/palette.py` annotates `_BROWN_BRICK_BASE` as
    exactly that), and `--view elevation` emits east/west while this wall faces south. Judge
    it in the headless viewer, or compute the recipe's extremes directly: the whole of the
    per-unit jitter is `new THREE.Color(base).offsetHSL(±j[0]/2, ±j[1]/2, ±j[2]/2)`, so a
    five-line node script prints the darkest and lightest unit a setting produces.
  - **The wythe is ONE layer now — no `slot`, no `extent`.** It was five `slot="wythe"`
    regions sharing a single 3 5/8" depth position (without the slot the assembly resolves to
    an 18 1/8" wythe and shoves the wall into the garden). With one region there is nothing
    to co-locate and nothing to band, so it is the ordinary case: a plain full-height
    STRUCTURE layer taking the wall's own base and top. **`Layer.slot` is a live feature that
    catlin no longer exercises** — the machinery, and the emitter regression it exists to
    catch, are guarded on a synthetic fixture in
    `packages/engine/tests/test_emitter_band_parity.py`. Anything that used to be true about
    band heights on the 2 2/3" course, `applyMasonryWallUv`, or the upper register riding
    `D-B-PATIO`'s head line at 88" is history, not a constraint.
  - **STRUCTURE, not CLADDING**: the backer is a *different wall*, so this has to be the
    structure layer or `integrity.assembly_layers` finds none. Same precedent as
    `RETAINING_BLOCK_12`. One BOM row, `BASEMENT_BRICK_VENEER:brown-brick`, 129.2 SF.
  - **The rate could not carry over, and that is the interesting part of the money.** The old
    `$15-28/SF` was the standard-veneer market taken at its LOW end *because the plinth was
    24" off the ground — no scaffold*. A full 8'-5" field needs scaffold for its upper 6', so
    it is `$19-30/SF`: $2,455-3,876 against the Ishtar wall's $2,573-5,467. The $19 low is
    above the $16 the market alone says, because 129 SF is a minimum-mobilisation masonry job
    and `prices.toml` elsewhere says a mason will not set up scaffold under ~$2,500-4,000. So
    the saving is roughly **$120-1,590** — real, modest, and never the point.
  - **Both brick reveals are shorter than the openings they front, and the door reveal's
    height is now a free variable.** `AO-B-BRICK-DOOR` went 88" -> 84" -> 78" and
    `AO-B-BRICK-WIN` 26" -> 20", all by eye and all against the gold register at 88" that no
    longer exists. 78" is kept because it still looks right — nothing requires it, and **84"
    is now available** if more of the door head should be covered. The overlap itself is
    deliberate: a masonry reveal in front of a rectangular hole is *meant* to overlap it, so
    the door's head is covered across its full width and the sauna window loses its top 6".
    Neither opening is a daylight or egress subject.
  - **A REVEAL MUST STAY CONCENTRIC WITH THE OPENING IT REVEALS, and for five days one was
    not.** `AO-B-BRICK-DOOR` was authored against `D-B-PATIO`'s position; on 2026-08-30 the
    door moved 6" west off a different node on a different wall and the reveal did not follow.
    `haus check` reported 0 FAIL the whole time, because the two are individually correct and
    nothing compared them. `integrity.reveal_concentric` grades that now — every rough
    opening with a wall standing behind it, against the nearest door or window in that wall,
    at a 1" tolerance — and `test_catlin_contract_m3` pins both pairs. **Edit the reveal and
    the opening together.** Height is free; width and position are not.
  - **Both arched reveals turn a voussoir ring**,
    `ui/src/three/builders/archRing.ts`. Masonry here is a texture, so the arch heads were
    running bond sliced by a curve; the ring is an annulus with *polar* UVs into that same
    tile, which turns its rectangular bricks into wedges. One header deep (3 5/8") and 3/16"
    proud on every face (the proud offset is what exposes the skewback end caps, and at 3/8"
    each one read as a black shard off the springline). The door's extrados crowns at
    81 5/8", the window's at 52 5/8". **Viewer-only**; an exported `.glb` still shows the
    plain spandrel.

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
- **Five items are deferred to a designer of record** (both roofs' rafters and uplift path,
  and the overhead-door header). `out/calcs/03-open-items.md` names who owns each.
- **Two open engineering questions** are real and are on that page, not hidden: the
  concealed-fastener wall panel's withdrawal allowable over 24" open girts, which no
  manufacturer publishes (`notes/board_batten_girt_span.md`), and the breezeway piers'
  axial demand, which has no modelled plan area to shoelace
  (`notes/breezeway_piers.md` §3 bounds it and says why that is not a doubt about the
  section).

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
