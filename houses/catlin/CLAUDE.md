# Catlin house — agent guide

This directory **is the state**: the house is defined by the editable plan source under
`plan/` plus the parametric modules under `params/`. Edit those; never edit `out/`
(generated). Read `brief.md` (intent) **and** `preferences.toml` (targets) before
proposing any design change.

## Project map
- `plan/manifest.py` — plain-Python assembler (NOT editable); wires modules + params.
- `plan/storeys/{basement,main,second,attic,garage}.py` — `# haus: editable` elements.
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
  hold. RF-HOUSE has **no fascia** (continuous standing-seam skin ⇒ the resolver's corner
  trim), so every offset is measured off the corner trim's face, never a fascia's. The lap
  order is enforced by `packages/engine/tests/test_catlin_eave_water.py` — read it before
  moving any of these numbers. All three pieces are ordered in `_CHAIN_MATERIAL`, the
  house's one exterior dark, so the eave line matches the rake's corner trim.
- `library/placeables/*.py` (repo root, not this directory) — the shared FixtureType/
  ApplianceType/FurnitureType *catalog*, wired in by `plan/manifest.py`. NOT editable: it
  uses `frozenset(...)`, which the dialect forbids. Type libraries stay non-editable;
  movable instances that reference them live in the editable modules above. The house-local
  `plan/fixture_types.py` this line used to name was deleted in the `3d3973a` library
  dedupe; only `plan/furniture_types.py` (the two mudroom closets) is still house-local.
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
  `_GLAZING_CENTER_X` moves with it. It did not, once: the 2026-07-28 mudroom conversion
  pushed the entry 4'-0" east and the shelter stood 3'-6" off its own door until 2026-08-01,
  when `code.R311_3_exterior_landing` finally caught it. Both doors still open onto the deck
  at 0'-0", and since the 2026-08-18 lift they reach it from opposite directions:
  `D-M-ENTRY` from the house floor it shares, `D-G-SERVICE` *up* +1'-0" from a garage storey
  that now sits at -1'-0". The breezeway deck did not move with grade — it is a bridge
  between two doors, and only its pads and piers followed the soil down.
- **Grade is 2'-10" below the main floor, and the house is what stands out of the ground.**
  The model's vertical datum is the main floor, so both lifts are authored as `Site.grade`
  going down with the datum fixed at 0'-0": -2'-6" on 2026-08-18, then -2'-10" on 2026-08-21
  when the basement-ceiling overhaul put a 12 5/8" deck where a 9" slab had been and the
  house rose 4" rather than surrender the headroom under it. **The datum is the top of
  joists, not the finished floor** — walls bear there and the subfloor rides above it, so
  main-floor FFE is +3/4" and every slab meant to land on it needs an explicit
  `top_elevation` (`params/main_deck.py`). The `main`, `second` and `attic` datums have
  never moved. **The basement storey is at -9'-1 7/16" (2026-08-23), and grade did not move
  with it.** It went to -9'-4" with the soil on 2026-08-21 and came back UP 2 9/16" when the
  flat bearing seat landed the EPS deck's soffit on the same plane as the wood bays' mudsill:
  the deck deepened to 14 3/8" and the FLOOR rose to meet it, so the house is where it was
  and the basement is shallower. That makes the pour **exactly 8'-0"**, and the basement
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
  the `garage` storey with an absolute `Slab.top_elevation` (it lived on `main` until
  2026-08-18, when that field was added, purely because `main` was the only storey at
  grade). Anything that has to sit on the garage floor must say so explicitly —
  D-G-OVERHEAD carries the plan's only negative `sill_height` to reach it, and the stem
  becomes a grade beam flush with the slab under that door so there is no curb across it.
  D-G-SERVICE no longer does: its threshold stays at 0'-0" with the breezeway deck, so it
  carries `+1'-0"` and the 2'-10" is taken inside the garage in five 6.8" risers — the
  `SL-G-STEP-0` landing pad at the threshold, and `ST-G-SERVICE` below it. That flight was
  five concrete `Slab`s (`SL-G-STEP-0..4`) until 2026-08-22, because `Stair` took its rise
  from a pair of storey elevations through a `FloorOpening` and a step-down *within* one
  storey has no floor to open. `Stair.floor_opening` is optional now and
  `base_elevation`/`top_elevation` state a rise directly. It matters beyond tidiness:
  `structural.stair_riser_uniformity` and `code.R311_7_8_handrail` both iterate
  `model.stairs`, so a five-riser flight with no handrail drew no finding at all while it
  was slabs. It is KDAT (pressure-treated) with `RL-G-SERVICE` over it. The garage plates are 8'-4", not 8'-0", for the same reason: the door
  climbed 4" inside its own wall when the storey went down, and its 3-ply LVL header would
  have pushed through the top plate into the truss heels.
  Emitters — and, since 2026-08-03, the placeable resolver that decides how high anything in
  the garage stands — read `resolve/room_floor.py::room_floor_elevation` rather than the
  storey elevation for the same reason. Raising the stem means re-dropping the overhead
  door: the tie is enforced by
  `test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade`.
- **The garage's ICF stem and its wood wall are coplanar on the outside.** The 24'x24'
  node line (`GARAGE_Y_SOUTH`/`NORTH` in `plan/storeys/garage.py`) is the wood wall's
  zip-R plane *and* the stem's exterior EPS face: the walls carry
  `alignment=face("zip-r-ext")` and the stem carries
  `alignment=face("concrete-ext", offset=GARAGE_ICF_EPS)`. Only the 7/8" of rainscreen +
  standing seam projects past, so it drips clear. Until 2026-08-15 the stem was unaligned
  and straddled the line, standing 5 5/8" proud of the cladding — a horizontal shelf right
  round the garage. Fixing it moved both wall lines 5 5/8" south (the breezeway's uncut 4'
  panel is measured off the *cladding* now) and took the core from 8" to 6". Do not "fix"
  it by moving the stem's nodes: `resolve/stacking.py::_axis_match` has a 1/2" tolerance
  and would silently drop the whole foundation-to-framed stack. `FT-GF-*` follow the stem
  via `Footing.center_on="wall"`, not the node line.
- 36'x36' at sheathing; everything on the 16" o.c. module; exterior walls carry
  `alignment=face("sheathing-ext")` so the sheathing plane is the vertical datum (#43).
- The side-wall stack is 2x6 throughout — one `CATLIN_EXT_2X6` on main, second and
  attic, sheathing plane continuous, no stud-depth jog. Main-storey studs are LSL,
  the upper storeys standard dimensional 2x6 (a purchasing note recorded in the
  assembly's `source`, not a separate assembly).
- **It is a CATLIN TRUSS WALL outboard of that sheathing (2026-08-26).** 4" of 2 lb
  closed-cell spray foam around **two tiers of flat horizontal 2x4 girts**, each course
  bearing on 3-1/2" blocks at the stud module: band A foam over block-1 (SPF), the inner
  girt (SPF, 24" o.c., buried), band C foam + a 1/2" vent gap over block-2 (KDAT), the outer
  girt (KDAT, same courses at the same elevations), then the standing seam. It replaced the
  **Swinburne truss** of 2026-08-23 — a chiral block + plywood tab + KDAT outrigger *on edge*
  at 16" o.c. — which had in turn replaced a sheet WRB + 2" polyiso + 2" EPS + 1/2" furring on
  537 eight-inch screws. Five things follow, each load-bearing elsewhere:
  - **There is no WRB.** The foam is air + water + vapour + thermal, bonded and seamless,
    and `plan/transitions.py` names `spray-foam-ext` as the water and thermal plane. The
    build order is therefore part of the spec: **bucks before foam**, always — and now also
    **band A before the inner girts**, because spray foam cannot reach behind a flat girt
    lying 1-1/2" off the sheathing.
  - **Materials are by exposure.** Inboard of the foam face (block-1, inner girt, inner jamb
    posts and courses) is plain SPF — encapsulated, never wet. In or outboard of the vent gap
    (block-2, outer girt, outer posts and courses) is KDAT — the outer girt is a horizontal
    ledge behind the cladding that wet-cycles for the life of the wall. The two blocks are two
    BOM rows because of it.
  - **The blocks are on the STUD module; block-2 is offset half a bay.** Girts climb their own
    24" elevation module from the wall base; the blocks land on 16" stud stations, and block-2
    on those stations plus 8". No screw passes through both tiers, so every fastener is
    wood-to-wood with continuous lateral support and nothing bears on foam — which is why
    IRC R703.15's through-foam furring table is not the applicable provision. See
    `notes/catlin_truss_engineering.md`.
  - **Windows are OUTIE**, in the mount plane **6"** out from the sheathing (was 5"), flanges
    bearing on the jamb posts and the head/sill courses. Derived, never authored — the mount
    plane is the outermost FURRING layer's outer face, which is why not one window moved when
    the stack changed. `structural.truss_wall_opening_support` keeps every RO jamb within a
    flange's bearing of wood.
  - **The cladding face moved out 1"** (6.5", was 5.5", was 5.02"). Nothing interior moved —
    walls align on `face("sheathing-ext")` — but `params/roof_trim.py` (one named constant,
    `_WALL_OUTBOARD_IN`, with both older values beside it), `params/breezeway.py`, the garage
    wall lines and the exterior electrical all measure off the cladding and moved with it.
  - **The Swinburne truss is one swap away.** Nothing vertical was deleted:
    `resolve/framing/truss_frame.py` and its branch of the pass are untouched behind their own
    predicate (`laid="edge"` + vertical), the girt frame is a sibling selected by
    `standoff="block"`, and the old layer tuple is kept verbatim as `CATLIN_EXT_2X6_SWINBURNE`,
    referenced by nothing. `notes/outie_window_truss_detail.md` has the three-edit revert.
  **The card reads R-40.7 and the honest number is ≈R-37.5** — the blocks are framed rather
  than authored as a `CavityFill`, and the outer girt is credited its own R although it stands
  outboard of the vent gap. `wall_r = 40` is NOT met. See the engineering note §7.
  See `notes/outie_window_truss_detail.md` and `notes/catlin_truss_engineering.md`.
- **Every exterior corner is construction-correct, 4-stud, with a plywood box outboard of
  it (2026-08-25 audit).** Three findings and their fix:
  - **The grid is struck from the building's outside sheathing corner.** All four facade
    layout lines have an along-axis origin of `+0.0000"` from a building corner; 217 of 241
    exterior module studs sit on exact 16" multiples from that corner (the 24 exceptions are
    the corner posts themselves); all 31 exterior windows centre exactly on that grid; the
    stand-off band runs the same grid, so the cladding's own line and the stud line are one
    line. This was already correct and the audit did not touch it. It survived the catlin
    truss: the girts are horizontal, so what phase-locks to the 16" module now is their
    BLOCKS rather than the band itself, and the promise is the same one — the screw lands
    on the stud.
  - **The house's corner is 4-stud, not 3.** `CATLIN_EXT_2X6` and `PLANT_EXT_2X6_HUMID`
    (the only two truss-wall assemblies) both carry `corner_style="4-stud"` on the STRUCTURE
    `FramingSpec`, and `preferences.toml`'s `[framing] corner` states it once for the whole
    house. The APA/BASC thermal objection to a solid 4-stud post (an insulable void inside
    it) does not apply here: the primary insulation is the *continuous exterior closed-cell
    foam*, outboard of the post, so the post itself needs no cavity to hold batt in. Before
    2026-08-25 the house had ZERO 4-stud corners despite four walls authoring
    `corner_style_end="4-stud"` — the exterior loop is a CCW chain, so every wall's `end` is
    the *next* wall's `start`, and `resolve/topology.py` gives L-corner ownership to
    whichever wall *starts* there. A style authored on the wall that only ever *butts* the
    corner could never take effect; `resolve/framing/solver.py::frame_model` now resolves a
    corner's style from BOTH incident walls (the owner's own authored end-style, else the
    butting wall's), which is what makes an override on either wall reach the pack. The
    freestanding garage (`GARAGE_WALL_2X6`) was NOT changed and stays 3-stud on purpose —
    it has no continuous exterior foam, so the thermal objection still applies there, and
    `structural.corner_style_matches_preference` is scoped to assemblies whose own
    `FramingSpec.corner_style` already matches the house preference for exactly this reason.
  - **The corner box is RETIRED with the outrigger band it closed (2026-08-26), and the
    machinery is kept.** It was the Larsen/Swinburne detail (FHB, Jan 2024): two 1/2" OSB
    rips per corner per storey (24 total), one along each wall's own outrigger band, meeting
    at the true building corner to close both outboard faces of the ~5"x5" full-height void
    the band's own 45° mitre left standing open there. A girt band has no such void — the
    courses are horizontal and **butt at the corner**, so each course closes its own band as
    it goes and there is nothing full-height to cap. `FramingSpec.corner_cap` and
    `TrussFrame.corner_box` are untouched and still fire for any band that asks for them;
    `CATLIN_EXT_2X6_SWINBURNE` still does.
  - **The 1/2" sheathing lap at the corner is still undeclared** (all layers mitre 45°
    today; a real lap has one wall's sheet run long and the other stop short by its
    thickness) — logged in `plans/TODO.md`, not built.
- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' spans E-W, on every
  storey and in both materials.
- **The basement's ceiling is mixed, and what the two halves share is ONE FLAT BEARING SEAT
  at -13 7/16" (2026-08-23), not one depth.** `FS-M-WEST`, `FS-M-MECH`, `FS-M-STAIR` (x 0'-18')
  and `FS-M-EAST` (x 18'-36', y 0'-13') are 11 7/8" I-joists at 16" o.c.; `SL-M-DECK` is what
  is left of the old 1,233 SF cast deck — 414 SF over the dining end, a 10" LiteDeck EPS
  stay-in-place beam (8" base + 2" top hat) under a 4 3/8" cast cover. Every basement concrete
  wall tops out on the seat; the deck's soffit lands on it and so does the underside of the
  gasket under the wood bays' shared 2x6 mudsill. **No step in the forms, one plate for the
  studs and the joists together.** They were tuned to one *depth* (12 5/8") until 2026-08-23,
  which matched the finished floors and left the joists resolving inside the top foot of the
  pour with nothing between wood and concrete. `structural.mixed_deck_bearing_seat` is a FAIL
  check that holds it, and `integrity.floor_bearing_grid` holds every joist cut over its own
  wall's structure. The boundary between the two materials is still a line on a drawing and
  moving it is still a one-line edit in `params/main_deck.py` (which is also where the seat
  and the depth constants live, and why they are not in the editable storey file). Ceiling is
  5/8" gypsum end to end — IRC R316.4 over the EPS, `ceiling_below` on the joist fields —
  though the two gypsum faces step **2 1/16"** at the boundary: 1/2" of it is the form's steel
  rib, the other 1 9/16" is the deck being deeper than the wood bay, which is what one flat
  seat costs. **And the step is modelled (2026-08-25).** `RM-B-GYM` is the only room the
  boundary crosses, and it resolves TWO ceilings rather than one — 234 SF at -11 7/8" under
  `FS-M-EAST`, 90 SF at -13 7/16" under `SL-M-DECK` — because a room's ceiling is derived per
  *deck region* (`resolve/ceilings.py`, `ceiling_over.ceiling_regions`), not per room. The
  model states the 1 9/16" it can derive; the rib's 1/2" belongs to the EPS form and EPS is
  never modelled here. A room over two decks of the same depth (`RM-M-LIVING` across the
  second floor's truss/I-joist split) stays ONE ceiling — a deck seam is not a step.
  **The floor finish follows the deck**: `SL-M-DECK.floor_finish` is `polished-concrete` (the cap's top
  *is* the finished floor), `RM-M-LIVING.floor_finish="lvp"` is the field finish over the
  wood bays only, and the split is derived — moving `_BAND_Y` moves the finish with it.
  Since 2026-08-25 that room carries a second, **authored** zone as well: the hall band
  (x 6'-0 5/8"-18'-0", y 22'-4 5/8"-26'-3 3/8") is `vinyl-sheet`, continuous with the
  mudroom, laundry and powder bath. Authored zones win over derived ones, but these two do
  not overlap — the hall is west of x=18' and `SL-M-DECK` starts there.
  `notes/mixed_deck_movement_joint.md` has the T-moulding (a reducer until 2026-08-23 —
  the two walking surfaces are flush within a plank's tolerance now), the L-shaped
  transition and the cream-polish spec.
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
  each end; the west field's spans are exactly 18'-0", the 18' truss untrimmed
  (`takeoff/framing.py::_order_length_ft`). `FO-S-STAIR` falls in the west half, so seven
  joist lines there clip to ~10'-3⅜" and fall outside the trimmable range — fabricated to
  length instead. Moving the split is a one-line edit in `params/second_deck.py` (which is
  also where the shared depth constant lives, and which `params/main_deck.py` imports
  rather than restating). The truss price row in `prices.toml` is a placeholder pending a
  fabricator quote, and the span-table row it borrows from the I-joist
  (`checks/structural/checks.py::_IJOIST_SPAN_FT`) is explicitly advisory at this 18'-0"
  span — the fabricator's own table governs.
- Attic is a habitable hot-roofed cathedral space: 5' knee walls E/W, gables N/S,
  ridge N-S, 4:12, **zero overhang**. Its deck `FS-ATTIC` is also **the second storey's
  ceiling**, and it authors that board (`ceiling_below`, 5/8" gypsum, restated inline
  because `plan/storeys/attic.py` is `# haus: editable` and cannot import `params/`). It
  was the last deck in the house without one: until 2026-08-25 every second-storey room
  resolved open to the I-joists, absent from the 3D model and from the order. The one
  exception is `RM-S-PLANT`, whose `Room.ceiling_lining` humidity liner replaces it over
  that room's own face.
- **The roof is a screwed nailbase, and three of its layers exist only because the
  condensation gate says so** (2026-08-20; it was a vented batten roof before). Stack above
  the rafters: 1/2" taped ZIP -> self-adhered deck vapour barrier -> 3" + 3" polyiso
  (staggered seams) -> 5/8" OSB top deck on 10" SDWH screws -> vapour-PERMEABLE synthetic
  underlayment -> 1/4" ventilated mat -> 24 ga standing seam. R-55.1, and that is the honest
  number, not the R-60 the brief asks for: the library de-rates polyiso to 5.6/in and the
  cavity is an R-19 batt. **The interior is paint and nothing else** — every control layer
  is outboard of the structure, which is the whole point of the arrangement.
  Three things will silently break it, and each has cost a rebuild already:
  - **The field underlayment must stay vapour-open.** High-temp peel-and-stick over the
    whole deck is the obvious spec and it fails the gate at 1.50 — at 0.05 perm it is as
    tight as the deck barrier under the foam, so the polyiso and the OSB are sealed on both
    faces with no way to dry either direction. Self-adhered ice barrier at the eaves and
    valleys only; that band is priced as an allowance, not modelled.
  - **The vent mat is not optional and is not a furring strip.** It is the assembly's only
    drying path. Without it the Glaser walk runs to the standing seam, which is rated 0
    perm, so every plane sits at interior vapour pressure and **no unvented stack under a
    metal roof can pass at any foam thickness**. It is an AIRGAP layer, so the envelope
    takeoff skips it — it is carried in `prices.toml [allowances]` instead.
  - **The taped ZIP is the air barrier, not the vapour barrier.** At 2 perm it is Class III.
    It was survivable while the layer outboard of the foam was a 54-perm membrane and
    stopped being survivable when the nailbase deck went on, because 5/8" OSB is 0.64 perm —
    three times tighter than the ZIP under it, so vapour entered the foam more easily than
    it left. Thinning the OSB is not the lever it looks like (7/16" only reaches 1.21, and
    APA has 1/2" at 0.70 perm against 5/8" at 0.72). The deck vapour barrier is.
  The stack depth is transcribed by hand into `params/roof_trim.py` (`_DRIP_CEILING_IN`,
  `_CLADDING_HEAD_IN`) and into `test_catlin_eave_water.py`; move a layer and those move.
- **Structural ridge, not a rafter-tie roof.** `RB-HOUSE` bears continuously on the
  `W-A-C1/C2` bearing wall, which stacks unbroken to the footings. That is what makes the
  rafters simple spans and keeps thrust off the 5' knee walls. Opening that center line up
  without a beam under it dumps ~1.5 klf of thrust into knee walls that can take ~0.1.
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
  centre until it was retired (2026-08-01).

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
  `test_catlin_contract_m3.py::test_catlin_window_openings_follow_the_sixteen_inch_framing_module`)
  is what says so. Resize windows to fit the grid, not vice versa. One type per width
  family — WT-1424, WT-2464 (the attic gable's juliet pair, head at 8'-0"; an 18" WT-1864
  family until 2026-08-24), WT-2736, WT-3036 (north gables/hall), WT-3048 (the
  south-glazing size, head at 6'-8") — each family sharing the one height that fits its
  most constrained wall. Five WIDTHS carry the whole house, and after the 2026-08-25
  narrowing the 27" family carries three of the nine heights (36"/48"/54"): the bearing cap
  is the width every bearing wall has to meet, so when a bearing-wall opening needs area or
  a head line, HEIGHT is the only dimension left to spend. That is a consequence of the
  ladder, not a drift away from "one type per width family".
  **Every window in the house is on its ideal station (2026-08-25), and the exception list
  is empty.** The juliet family was the last holdout: it centred on a stud line at 18" wide,
  and widening it to 24" on 2026-08-24 could only go outward — the 14" bearing pier under
  the ridge pins the inboard jambs — so each centre landed 3" off and
  `structural.window_framing_module` reported both. What ended it was not a fifth attempt at
  the width but the grid moving under it: with the exterior assembly laying out from the
  layout line, 16'-0"/20'-0" are stud lines, 5" further out, and the pair fits with no
  retype. `test_catlin_contract_m3.py::test_catlin_window_openings_follow_the_sixteen_inch_framing_module`
  asserts the empty list; keep it empty, and see **ONE GRID PER FACADE** under Facade rules
  before concluding a window cannot reach its station.
  **Four exceptions**, each an extra height on an existing width family because the rule's
  own remedy — give it its own width family — costs more than the extra height does. The
  first two are 2026-08-01 and are about a HEAD LINE; the last two are 2026-08-25 and are
  the 27" bearing cap being paid for in height (see the RO ladder above):
  - **WT-1448** (the south gable's flankers): the 4:12 rake forbids the remedy outright.
    Any width over 14" breaks a stud and takes a header, and the header is what hits the
    rake (the juliet family at the nearest usable stud line misses by 1.8"). 14" fits in a bay
    and takes no pack, so only the glass has to clear.
  - **WT-3048** (the south glazing): the 30" family's committed height (WT-3036's 36")
    would drop the south head off the 6'-8" door-head line the whole face is built on.
  - **WT-2748** (`WIN-M-EAST-MID`, 2026-08-25): the east living row's feature window had to
    come 30" → 27" for the bearing cap, and the 27" family's committed 36" would have
    dropped its head from 6'-6" to 5'-6". 48" makes the narrowing a pure retype — same
    2'-6" sill, same 6'-6" head, only the width moves. The cheapest of the four.
  - **WT-2754** (`WIN-S-BED1`/`BED2`, 2026-08-25): the same 27" cap, but these are
    single-window BEDROOMS, so R303.1 binds on area and 27x48 is 9.00 sf against BED2's
    9.945 sf requirement — it would FAIL. 54" is the height that makes 27" legal
    (10.125 sf), which is why this one is a code necessity and not a composition choice.
- Facade rules (2026-07-30 pass, gable revised 2026-08-01, E/W revised 2026-08-15).
  Windows line up or they are not there:
  - **ONE GRID PER FACADE (2026-08-25). The residue rule is dead — read this instead.**
    `CATLIN_EXT_2X6` and `PLANT_EXT_2X6_HUMID` both set `layout_origin="line"`, so a wall
    segment lays its studs out from its **layout line** — the derived chain of collinear,
    stacked walls (`resolve/layout_lines.py`) — not from its own start node. Every segment
    on a facade, on every storey, is therefore on one 16" grid measured from the house
    origin. **A window's legal stations are now a property of the facade, and moving a node
    no longer re-phases anything.** Stations are absolute: x (or y) ≡ 0 mod 16" is a stud
    line, ≡ 8" a bay centre.
    - What this retired, all of it the same defect in different costumes: node moves made
      purely to buy phase (N-A-V1 to 22'-8" for the south gable; four of them in the
      2026-08-15 E/W pass); the "spent" 31'-4" west column; the east knee band's 4" miss;
      the north gable's asymmetry; and the juliet pair's accepted 3" off-module exception.
      All five dissolved when the grid was unified, at a cost of 20 windows moving 3"–8".
      **`test_catlin_contract_m3.py::test_catlin_window_openings_follow_the_sixteen_inch_framing_module`
      now asserts an EMPTY exception list.** Keep it empty.
    - **The 8" rule survives, and is now the only phase rule left.**
      `structural.window_framing_module` puts a 14" RO on a **bay centre** and a 27"/30" RO
      on a **stud line** — 8" apart on the one grid. So a 14" unit still cannot column with
      a 27" unit, anywhere on the house, and retyping the narrow unit is still the answer
      (WIN-M-BATH2, 2026-08-15). This is no longer a per-segment accident to be worked
      around; it is a property of the two widths and it is permanent.
    - **A node move is now cheap and a window move is now global.** The old warning was
      "price a node move before making it". The new one is its mirror: a node may move
      freely, but a window that moves off the grid stays off it, and a facade whose windows
      disagree with the grid can no longer be blamed on authoring order.
    - **A tee is not a wall end (2026-08-25, second half of the same fix).** Unifying the
      module was necessary and was not sufficient: each of the six or seven segments a facade
      is authored as still framed its *own end stud* where it met the next, so every seam
      carried two sticks in the same 1-1/2", off the module, at a station the storey above
      split somewhere else. Those seams are gone — where two collinear segments provably
      share one grid, `framing/solver.py::continuation_roles` drops both end studs and lets
      the module run through, one `"owner"` claiming a seam that lands on the grid. The same
      reading now runs the **stand-off band** (`framing/furring.py`), which is the line the
      cladding lands on.
      **The catlin truss turned that band on its side and the reading followed it there
      (2026-08-26)**: `_furring_module_signature` carries `direction`, so a HORIZONTAL band
      continues through a seam too. Without it every tee in a facade would put a 3" notch in
      every girt course — a course is one stick on the job, and the seam is an artifact of
      where the partitions land inside. What phase-locks to the 16" module is now the girts'
      **blocks**, one under every course at every stud station, and block-2 on the same
      stations plus 8".
      `test_catlin_contract_m3.py::test_each_facade_block_grid_is_one_grid_on_every_storey`
      and `::test_no_facade_stud_stands_off_the_module_except_at_a_corner` pin it, per facade.
      The only members left off the grid are the corner packs (identical on every storey) and
      the jamb packs, which sit where their rough openings put them and always did.
    - **AND THE INSIDE OF THE HOUSE, TOO (2026-08-25, third and last round).** The two
      rounds above were both about facades, and the house is not a facade. Five interior
      bearing assemblies now set `layout_origin="line"` on their STRUCTURE layer:
      `CATLIN_INT_2X6_BRG` and `PLANT_INT_2X6_BRG_HUMID` (the x=18'-0" **centreline**,
      `W-M-C1..C5B` / `W-S-C1..C4B` / `W-A-C1..C2`), and
      `CATLIN_STAIRWALL_INT_2X6_BRG`, `CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX`,
      `CATLIN_MUDROOM_INT_2X6_EXPOSED` (the **stair line**, `W-B-STR/STR2/STR3` under
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
    **Both storeys are now mirror-symmetric about the x=18'-0" ridge** — main reads
    4'-0" / 14'-8" / 21'-4"(door) / 32'-0", second reads 4'-0" / 9'-4" / 14'-8"(door) /
    21'-4"(door) / 26'-8" / 32'-0", and every one of those pairs sums to 36'-0". The east
    pair came 8" *inboard* on 2026-08-25 to get there, which was the choice the unified
    grid opened up: the nearest legal station was 8" the other way, and inboard bought the
    mirror for the same 8". They had been 27'-4"/32'-8" since 2026-08-01, when the glazing
    narrowed to WT-3048. The attic does not join them — see **Gables**.
    The **west face stacks FIVE** through main and second (y 5'-4", 10'-8", 20'-0",
    24'-8", 31'-4"), all four lower ones having shifted 4" together on 2026-08-25 when the
    face re-hung on the house grid. The first three use the 27" family on a 3'-0" sill; the
    fourth pairs tempered 14" awnings in RM-M-BATH1 and RM-S-VANITY on a 4'-0" sill; the
    fifth pairs WIN-M-MUD with WIN-S-BATH-W. All share one 6'-0" head line.
    WIN-M-BATH2 was retyped WT-1424-T -> WT-2736-T at a 3'-0" sill to reach the third
    column (the 8" rule), which also buys R303.3's window alternative outright.
    **The fifth column was recovered on 2026-08-25**, having been spent on 2026-08-21: the
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
    The north face stacks one three-storey column at x=28'-0" (WIN-M-KITCH /
    WIN-S-HALL-N / WIN-A-N2).
  - **Rows.** Where a column is impossible, the storey's own rhythm wins instead — but a
    row must be *centred*, not merely even. The east second storey ran a perfect 9'-0" beat
    that sat 10" north of the centreline until 2026-08-15 (5'-4" of wall south, 3'-8"
    north); it now reads 4'-0" / 13'-4" / 22'-8" / 32'-0", exactly mirrored about y=18'-0"
    in station, width (27/30/30/27) and head (6'-0"/7'-0"/7'-0"/6'-0") over one 3'-0" sill.
    **And since 2026-08-25 it is even as well as centred** — a 9'-4" beat three times over,
    where 4/13/23/32 was 9'-0"/10'-0"/9'-0". The inner pair moved 4" outward onto the
    unified grid and the row got the thing it had been trading away. The 2026-08-15 pass
    that first centred it took N-S-E2 to 17'-8" and N-S-E3 to 26'-8" to buy phase, and the
    bedroom bays became 8'-8"/9'-0"/9'-4" to pay for it, shrinking BED1 (whose R303.1
    margin is 0.05 sf) and growing BED3 (which has two windows). Those node positions are
    now incidental — the grid no longer depends on them — but the room sizes they set are
    real and still govern.
    **The east MAIN row reads 4'-0" / 12'-0" / 18'-8" / 34'-0", and the last of those is
    the blank kitchen stretch being deliberately ended** (2026-08-24). This bullet used to
    say the opposite — *"the blank is the composition, so the 8" hitch is not worth moving
    N-M-E1 for"* — and by then it was doubly stale: N-M-E1 and W-M-E2 went when the wall was
    merged for WIN-M-EAST-MID, and WIN-M-DIN-E2, the window the blank was measured north of,
    was retired with them. **Look at `out/render/elev_east.png` before touching this.** What
    the row now does, and what it costs: the first three are the row proper — two 27" units
    and a 30" one on one 2'-6" sill — and WIN-M-KIT-E is a 14" unit at a 3'-6" sill, so it
    joins neither the beat nor the head line. It reads as a smaller service window closing
    the row at the north end rather than as a fourth beat, which is the honest description
    and was the trade: the kitchen wanted a second window over its counter more than the
    facade wanted 16'-0" of unbroken wall. It is on a bay centre (408" off N-M-SE, 8" mod
    16") so it breaks no stud and takes no header — see the 8" rule above for why a 14" unit
    can never column with the 27"/30" family beside it. WIN-S-STUDY3 at 4'-0" still columns
    with WIN-M-LIV-E1.
  - **Knee band.** Both 5' knee walls carry a WT-1424 pair, and **both are now exactly
    mirrored at 3'-4" / 32'-8"** (2026-08-25). The east end had been 4" off at 32'-4" since
    it was built, and the entry here used to explain why it had to stay off: W-A-E2's grid
    started at N-A-E1 (y=9'-0"), and the only fixes moved that node, dragging N-A-C2 and
    therefore W-A-SN, whose south face closes FO-A-STAIR's north edge — 9'-4" put 3'-0" of
    unguarded stair well on `code.R312_1_guard`. The line-based module removed the premise:
    W-A-E2's grid is the house grid now, so the window moved 4" on its own and the stair
    was never touched. A worked example of what "one grid per facade" buys.
  - **Head lines.** The west face puts every main and second head on one 6'-0" line —
    27" units at a 3'-0" sill, 14" units at 4'-0". The south face shares a 2'-8" sill.
  - **Gables** read symmetric about the ridge before they answer to anything below:
    that is why WIN-A-N1 does not stack on WIN-S-STAIR-N, and why the 2026-08-01 pass gave
    the south gable up as a column-capper. **The north gable became symmetric on
    2026-08-25** — WIN-A-N1 moved 7'-4" -> 8'-0", mirroring WIN-A-N2 at 28'-0" about x=18'.
    It had never been, and the reason was phase, not composition. The south gable carries
    four openings, exactly mirrored about x=18': WT-1448 flankers at 8'-8"/27'-4"
    (head 6'-8") around the WT-2464 juliet pair at **16'-0"/20'-0"** (head 8'-0"), one 2'-8"
    sill under all four, heads stepping with the rake. The juliet centres were 16'-8"/19'-4"
    until the 2026-08-24 widening pushed each unit 3" outward onto a non-module station —
    the house's one accepted off-module pair — and 5" further out on 2026-08-25, where the
    unified grid puts a stud line and the exception ends. The clear bearing pier between
    them went 14" -> 24" with that move; 14" is the requirement, so it is spent slack, not a
    new constraint. The mirror about x=18' is the rule that actually governs a gable and is
    the one thing that survived all three positions. The corner pair at 3'-4"/33'-8" was
    retired — the rake leaves ~6'-0" of wall there and nothing stands in it without reading
    as a stamp. Mirroring the east half once required moving N-A-V1 from 22'-4" to 22'-8",
    because W-A-S4's bay centres were then 4" out of phase with a mirror of W-A-S1's; that
    node no longer sets any grid, so the move is now only a wall-segmentation choice.
  - WT-1424 still does the work wherever a bigger unit will not fit — in the 5' knee
    walls, where its 2'-0" height is the only one that clears the plate, and in the
    mudroom. Under the south rake it handed off to WT-1448.
  - **Tempered twins (2026-08-01).** `WT-1424-T`, `WT-2736-T`, `WT-3036-T` and `WT-3048-T`
    are their parents in every dimension and differ only in the glass, for the ten units
    R308.4 puts in a hazardous location (a wet room, within 24" of a door, within 60" of a
    stair). They are **not** width families and no facade or framing rule sees them: adding
    a tempered unit is a retype, never a move. All three glazed *door* types are tempered
    outright — R308.4.1 has no location test to fail.
  - **~~The east bearing wall now takes a 30" RO~~ — REVERSED 2026-08-25, and the reversal
    is the more useful half of this entry.** For three weeks `WIN-S-BED1`/`BED2` carried a
    30" RO in a BEARING wall and `max_window_ro_bearing_in` sat at 30 to allow it. The
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
  must stay true** (2026-08-25, `plan/mep_erv.py`).
  - **The manifolds map to CAVITIES, not storeys, and there are exactly three.** Level 1 is
    the basement ceiling at the machine in RM-B-FURNACE; level 2 is RM-M-MECH, which feeds
    main-storey CEILING grilles *and* second-storey FLOOR boots because both open into the
    one FS-S-WEST/EAST cavity; level 3 is the FS-ATTIC deck at the chase head. A terminal is
    fed from whichever cavity it sits in — moving a terminal between storeys is free, moving
    it between cavities is a new radial off a different manifold.
  - **The radon/plumbing chase at (1', 34'-6") is the only riser, and it is now full.** Four
    6" insulated ducts share it with six plumbing vents, `VR-M-RADON-VENT` and eight
    conduits: a row of three at y=33'-7 1/2" and a fourth at (5", 35'-6"), ~25% fill of a
    30 1/8" x 32 3/8" shaft. The arrangement is in `plan/mep_erv.py` and **nothing else
    should be added to that chase.**
  - **The two outdoor hoods are on the north gable at x=12'-0" and x=24'-0", mirrored about
    the ridge.** IRC M1602.2 wants 10 ft between an intake and a discharge and RM-M-MECH is
    5'-11" x 2'-7", so no pair of hoods near the shaft can make the distance — the gable
    costs ~30 ft of insulated riser each way and buys 12'-0" of separation, 25'-10" above
    grade, and distance from both the garage and `EQ-M-HP3-OD`'s ground-level slot.
    `mep.erv_outdoor_terminals` grades all three of those; the mirror about x=18'-0" is the
    facade rule (see **Gables**) and nothing but this line enforces it.
- **A duct or a machine inside a modeled `Soffit` NAMES IT, and the clear section is
  DERIVED** (2026-08-25). `DuctRun.soffit_ref` and `Equipment.soffit_ref` mirror `floor_ref`;
  `mep.duct_soffit_occupancy` derives the cavity from the soffit's own drop, `FramingSpec`
  member and 5/8" lining and measures everything claiming it side by side with a 2" hanger
  gap. **Never author a clear width** — it is a second source of truth for a number the
  framing already states, and it drifts the first time a 2x2 becomes a 2x3. `SF-S-DUCT`
  derives 30 3/4" clear x 11 1/4" drop; `SF-S-SUITE` 31 3/4" x 11 1/4".
  - `CHASE` routing keeps its honest meaning — a framed shaft that is NOT modeled as a
    `Soffit` — and is a *declared* unchecked case. It used to be the flag that turned the
    joist-bay check off, which is why four hand-arithmetic clearance comments lived in the
    plan source unchecked. They are gone; read the check.
  - **The check found two real errors on its first run, both in `EQ-S-HP1-AH`.** It was
    resolving at the 9'-0" storey ceiling (a CEILING mount with no elevation fell back to
    `default_ceiling_height`, which is now soffit-aware), and its case resolved 43" across
    the hall instead of 21" along it, because `EquipmentType.footprint` wins over the
    element's and `EQ-T-GREE-SLIM24` states (43, 21). It needed `rotation=deg(90)`.
- **`W-M-HS4` is a pocket, and is therefore spoken for.** `D-M-LAUN` became a 4'-0" pocket
  door on 2026-08-21 (was a 56" bifold); its leaf parks east inside `W-M-HS4`, crossing
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
- **Four basement assemblies, and every split is a condition, not a preference.** Two
  independent axes cross here: what covers the exterior XPS, and how thick the pour is.
  All four compose off `library/`'s `FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a house-local
  skin layer, so the core cannot drift between them.
  - *The skin.* `CATLIN_BASEMENT_12`/`_8` (N/E/W) cover the XPS with a 1/2"
    `foundation-protection-panel` banded from 6" below grade to the top of the wall —
    2'-10" of exposure the two lifts created, ~360 SF, authored as a `Layer.extent` off the
    `GRADE` datum. `CATLIN_BASEMENT_8_GARDEN` (south: `W-B-S1/S3`) keeps the full-height
    parge coat, because the sunken garden exposes that face from -9'-0" to 0'-0" and a
    grade-datum band cannot describe that. `W-B-S2` is that same stack under a fourth tag,
    `SAUNA_LINER_ON_BASEMENT_8_GARDEN` (2026-08-18): the sauna's south face, carrying the
    hot-side liner *inboard* of the pour, banded to the room's 7'-6" ceiling. It aligns on
    `face("concrete-ext")` with **no** offset, so the pour sits exactly where W-B-S1/S3
    leave it.
  - *The pour* (2026-08-21). 12" is earned only where a cast concrete deck lands on the
    wall top beside the sill plate and needs a bearing seat inboard of it. After the
    basement-ceiling overhaul the only cast deck left is `SL-M-DECK`, which bears on the
    east wall and the centre line — so `W-B-E1/E2` stay `CATLIN_BASEMENT_12` and the other
    nine segments are 8" carrying `#5 @ 41" o.c.` vertical steel, which IRC Table
    R404.1.2(8) requires at 8" where 12" reads NR. (It was `#6 @ 48"` until 2026-08-23: the
    flat bearing seat made the pour exactly 8'-0", which is the table's 8'-unsupported row
    rather than the 10' row a 9'-4" wall rounds up to. **The "12" is earned only where a cast
    deck lands beside the sill plate" rule is now obsolete** — with a flat seat nothing
    competes for wall-top width, and the 12" segments that are left are left as built for
    reasons written on the walls themselves, not for bearing. There were four until
    2026-08-24; `W-B-STR` and `W-B-STR3` are 2x6 bearing stud walls now — `unbalanced_fill`
    was already `ft(0)` on both, and what they carry is joists and a wall stack, which is a
    stud-wall job on a footing. The centre line's three interior segments
    `W-B-CS`/`W-B-CS2`/`W-B-CN` are the interior pour that remains.) Drop that string on any of the nine and
    `structural.foundation_unbalanced_fill` FAILs, correctly.
  Every one of the four carries exactly 4.55" outboard of the concrete face — the panel is
  the same 1/2" as the parge it replaces, and neither is part of the pour — which is what
  `N-B-BRICK-W`/`-E`'s `inch(-4.55)` stand-off is measured from. That is why thinning the
  wall did not move the brick veneer, and why changing a *skin* thickness would. Because
  the walls align on `face("concrete-ext")`, the 4" came off the INSIDE face: the furnace
  room and the workshop each gained 4" of clear (the model still reports the old number —
  `clear_face` is inset from the wall axis, which did not move). See
  `notes/basement_to_framed_wall_detail.md`.
- **Every exterior deck's plank is the floor system's own sheet, with ONE exception.**
  `FS-SG-PORCH` (composite, 3bf2f48) and `FS-SG-DECK` (aluminium, 2026-08-22) carry their
  boards as `subfloor=DeckLayer(...)`; the `SL-SG-PORCH` and `SL-SG-DECK` slabs that used to
  stand beside the framing are gone, and both planks bill by the square foot in
  `[sheet_goods]` instead of by the cubic yard out of a table named `[concrete]`. The
  balcony converted term for term because its joists cantilever 6" and the deleted slab's
  outline *was* that cantilever.
  **`SL-BW-DECK` stays a Slab and must not be "finished".** The breezeway plank oversails
  its joist rim 2 3/4" at each end onto D-M-ENTRY's and D-G-SERVICE's thresholds, and a
  floor system's sheet is exactly its joist field (`resolve/floors.py`). Converting it
  either FAILS `code.R311_3_exterior_landing` on both doors or lays a joist through
  `PT-BW-1..4`. It was tried and reverted on 2026-08-22; the reasoning is in
  `params/breezeway.py`.
- **The garage's east elevation carries a 4'-0" buff brick wainscot, and the cap flashing
  is the part not to value-engineer away.** The two 4'-0" strips of wall flanking the 16'
  overhead door are the most-abused surface on the building — apron splash, snow piled off
  the drive, trimmers, car doors — so they get full 3 5/8" face brick (`buff-brick`, ASTM
  C216 **Grade SW**, through-body single light body; a chip exposes the same colour, and
  Grade SW is not optional at 40+ freeze-thaw cycles a year). Not thin brick, so real
  bearing: `W-GF-E1`/`W-GF-E2` are formed with a mid-stack ICF brick-ledge block
  (`GARAGE_ICF_6_BRICKLEDGE`), and the veneer itself is its own short wall
  (`W-G-BRICK-S`/`-N`, `GARAGE_BRICK_WAINSCOT`) standing in front of the existing one,
  exactly `W-B-BRICK`'s precedent.
  - **The 4'-0" pier widths are not a free choice.** Those two stem segments exist only
    because the stem drops to a grade beam under the door, so their width IS
    `OVERHEAD_DOOR_OFFSET` and their inboard ends ARE the door jambs. Moving the door
    moves the brick. Held by
    `test_catlin_contract_m3.py::test_garage_brick_wainscot_piers_are_the_door_jambs_and_cap_at_four_feet`.
  - **Coursing, modular 2 2/3", off grade at -2'-10":** shelf top 2 2/3" (-2'-7 1/3"),
    15 courses of field brick 40" (+0'-8 2/3"), sloped rowlock cap 4" (+1'-0 2/3"), metal
    cap flashing 1 1/3" — **top of cap 4'-0" above grade on the nose**, every course a
    whole module. The shelf sits one module *above* finish grade rather than at it: the
    cheapest durability move available, lifting the base course clear of the worst splash
    and snow-contact zone.
  - **The backing changes mid-wainscot and so do the ties.** The garage storey datum is
    -1'-0", so ~19 3/8" of brick backs onto the ICF stem and ~24 5/8" onto the wood wall
    above it. Corrugated ties are valid only where the brick back is within 1" of framing,
    and across the zip-R it is not: **screw-on adjustable two-piece ties into studs above
    the datum** (IRC R703.8.4), ICF ties below. Easiest thing on this wall to get wrong.
  - **The cap is the durability crux.** A 4' wainscot that stops mid-wall is a horizontal
    termination, and that is where these details fail here. Through-wall flashing + weeps
    at 33" o.c. max at the base course on the ledge (IRC R703.8 — a weep near each end at
    this length), a second through-wall flashing under the cap, and a formed metal cap
    flashing with a **drip edge** in the house's `#1c1f24`, kicked out over the rainscreen
    above so water leaves the wall instead of tracking behind the cladding. The cap is a
    modelled `Flashing` (`TR-G-BRICK-CAP-S/N`, `TrimKind.DRIP_FLASHING`); the inboard
    kick-out is not — `DRIP_FLASHING` has only the one outboard turn-down and `TrimKind`
    has no coping kind. Do not invent one.
  - The veneer is filed on the **garage** storey, never `basement`. `RM-GARAGE` is
    unconditioned, so it drops out of the block load cleanly; on `basement` it would read
    as an envelope foundation wall and silently inflate `building_science.energy_load` and
    `mep.heating_capacity` instead of erroring. Its four nodes are new, local and
    `open_end=True` — node lookup is storey-scoped and the stem's nodes are filed on
    `basement`, so a `N-GF-*` reference would resolve to nothing with no finding at all.
  - Its layout line runs on the **brick face**, not the node line, and `face("brick-ext")`
    is why: on x = 24'-0" it would sit on top of the stem's and W-G-E's layout lines,
    inside `_axis_match`'s 1/2" tolerance, and `integrity.stack_ambiguous` is a hard ERROR.
  - `FT-GF-E1`/`FT-GF-E2` widened 20" -> 24" and sit **2" east** of their un-ledged
    neighbours: `center_on="wall"` re-centres on the stepped section, ledge band included.
    Correct, but nothing downstream may be dimensioned off their edges.
- **The garage ICF stem is boarded above grade, and `code.R316_4` is why.** `GARAGE_ICF_6`
  carries a 5/8" gypsum layer on its INSIDE face, banded from the `GRADE` datum up — the
  2.5" of interior EPS stood bare from the slab to the stem top, ~176 SF of foam plastic
  facing an occupied space. It continues the board `GARAGE_WALL_2X6` already lines with, so
  it is the same detail, not a new one. Banded, not full height: below grade there is no
  interior to separate anything from, and a full-height layer would bill board into the
  soil.
- **One exterior dark, `#1c1f24`** (2026-08-01), carried by every dark metal element on the
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
    category gutter" until `ResolvedSolid.material` was added (2026-08-01) — which is why
    the eaves stayed mill grey while the rakes went black. A solid's own material now wins
    over its category palette in both renderers, but only when it *states* a colour (a
    named finish, or a catalog material with an authored `color`); a generic ref like
    `"aluminum"` still falls through to the category, so nothing else in the model moved.
  - **Why `#1c1f24` and not the `#3a3d40` it started at:** an authored colour is an albedo.
    The viewer lights with 0.8 hemisphere + 0.9 key + 0.6 IBL, over unit irradiance, so a
    dark surface leaves the shader well above its albedo — `#3a3d40` arrived near `#525252`
    and read as generic grey. Author under the tone you want on screen.
  - Guards are `RAILING_DARK_METAL`, split off `POST_WHITE_PAINT` for this. The balcony's
    six 6x6 pillars and its knee braces still use `POST_WHITE_PAINT` and stay white — that
    shared assembly is why they must not be recoloured together.
- **The sunken garden's veneer is the Ishtar Gate** (2026-08-20). `W-B-BRICK` was one flat
  field of `glazed-green-brick` (`#1b4332`); the green was liked on its own but did not sit
  with white standing seam and `#1c1f24` trim. It now reads after the Ishtar Gate of
  Babylon — a lapis field with golden-yellow register bands over an unglazed brown plinth:
  - `glazed-lapis-brick` `#10386a`, `glazed-gold-brick` `#c08a12`, `brown-brick` `#a07c5c`.
    Each is a three-place change like every other material appearance here — the `Material`
    in `plan/assemblies.py`, a `MasonryStyle` in `ui/src/three/materials.ts`, and a
    `_FINISH_BASE` entry in `emit/gltf/palette.py`. The lapis and the brown are both authored
    a step darker than their reference colour, for the albedo reason above: the first pass at
    `#144a86`/`#7a5340` arrived on screen as cobalt and rust. The plinth went the other way
    on 2026-08-21: it was authored dark AND at the red brick's full `jitterHSL`, on the
    argument that an unglazed body beside a glaze is what makes the glaze read as a glaze,
    and on the wall that came out as a plinth laid from mixed pallets with near-black units
    through it. **The plinth is ONE light brick** — the jitter is now the glazes' near-zero,
    and the no-glaze contrast is carried by sheen and the tan mortar joint instead.
  - **`glazed-green-brick` is still in the catalog, referenced by nothing.** Reverting the
    wall to one flat forest-green field is a one-word `material_ref` swap. Do not delete it.
  - Band heights off `WALL_BASE`, on the 2 2/3" course: brown 0"–24", gold 24"–29 1/3",
    lapis 29 1/3"–88", gold 88"–93 1/3", lapis 93 1/3"–top. Every one of those is a whole
    number of courses off `WALL_BASE` (9 / 11 / 33 / 35), which is what makes each band land
    on a bed joint now that the viewer courses masonry from the wall's own base rather than
    from project zero (2026-08-21, `applyMasonryWallUv`). Keep any new band on the module or
    it will render cut. The upper register sits **on
    D-B-PATIO's head line** at 88", so the band runs across the top of the opening rather
    than floating above it. Move that line and the band goes with it.
  - **Both brick reveals are shorter than the openings they front** (2026-08-21).
    `AO-B-BRICK-DOOR` went 88" -> 84" -> 78" and `AO-B-BRICK-WIN` 26" -> 20", all by eye. At
    88" the door's crown landed exactly on the gold register and its springline exactly on
    D-B-PATIO's 80 1/4" head: no course above the arch, no haunch below it, and it read as an
    arch someone had sawn off. At 78" there is 10" of lapis between crown and register. The
    consequence is deliberate: the door's head is covered across its full width and the sauna
    window loses its top 6", because a masonry reveal in front of a rectangular hole is
    *meant* to overlap it. Neither opening is a daylight or egress subject.
  - **All five are ONE row**, `slot="wythe"` (`Layer.slot`, new with this): they share a
    single 3 5/8" depth position instead of taking one each. Without the slot the assembly
    resolves to an 18 1/8" wythe. Every region must keep the same thickness and its own
    non-overlapping `extent`; `integrity.assembly_layers` refuses the rest.
  - Each colour bills its own band area on its own BOM row, priced by a material-qualified
    key in `prices.toml` (`BASEMENT_BRICK_VENEER:brown-brick`, …). 28.3 / 90.1 / 14.8 SF — the lapis grew from
    79.0 when the two reveals were shortened on 2026-08-21.
  - **Both arched reveals turn a voussoir ring** (2026-08-21),
    `ui/src/three/builders/archRing.ts`. Masonry here is a texture, so the arch heads were
    running bond sliced by a curve; the ring is an annulus with *polar* UVs into that same
    tile, which turns its rectangular bricks into wedges. One header deep (3 5/8") and 3/16"
    proud on every face (the proud offset is what exposes the skewback end caps, and at 3/8"
    each one read as a black shard off the springline). The door's extrados crowns at
    81 5/8", the window's at 52 5/8". The depth is not free: the door crowns at 84", so 3 5/8" puts the
    extrados at 87 5/8", 3/8" under the gold register — a full 7 5/8" ring would punch
    through it. **Viewer-only**; an exported `.glb` still shows the plain spandrel.

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
