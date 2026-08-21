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
  `mep_supply_devices`, `mep_hvac` (ducts, equipment, terminal types), `mep_registers`,
  `mep_electrical` (symbols). All eight are `# haus: editable`. `plan/mep.py` itself is
  now only the four storey element lists the manifest consumes — NOT editable, because an
  aggregator needs `from plan import ...` and the dialect forbids it.
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
  never moved; the basement storey went to -9'-4" with the soil, so it holds 8'-3" clear to
  the lower of its two ceiling planes. What follows the soil down is everything pinned to it: the garage and
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
  carries `+1'-0"` and `SL-G-STEP-0..4` take the 2'-10" down to the slab inside the garage
  in five 6.8" risers. The garage plates are 8'-4", not 8'-0", for the same reason: the door
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
- Bearing lines: west wall, center N-S wall (x=18'), east wall; 18' spans E-W, on every
  storey and in both materials.
- **The basement's ceiling is mixed, and that is the point.** `FS-M-WEST` (x 0'-18') and
  `FS-M-EAST` (x 18'-36', y 0'-13') are 11 7/8" I-joists at 16" o.c.; `SL-M-DECK` is what is
  left of the old 1,233 SF cast deck — 414 SF over the dining end, an 8" EPS stay-in-place
  form with a 4 5/8" cast cap. Both are 12 5/8" deep and both span 18'-0" to the x=18' line,
  so the boundary between them is a line on a drawing rather than a structural decision, and
  moving it is a one-line edit in `params/main_deck.py` (which is also where the two depth
  constants live, and why they are not in the editable storey file). Ceiling is 5/8" gypsum
  end to end — IRC R316.4 over the EPS, `ceiling_below` on the two joist fields, though the
  two gypsum faces step 1/2" at the boundary because the board screws to the form's steel
  rib on one side and to joists on the other. **The floor finish follows the deck**: `SL-M-DECK.floor_finish` is `polished-concrete` (the cap's top
  *is* the finished floor), `RM-M-LIVING.floor_finish="lvp"` is the field finish over the
  wood bays only, and the split is derived — moving `_BAND_Y` moves the finish with it.
  `notes/mixed_deck_movement_joint.md` has the reducer, the L-shaped transition and the
  cream-polish spec.
- Attic is a habitable hot-roofed cathedral space: 5' knee walls E/W, gables N/S,
  ridge N-S, 4:12, **zero overhang**.
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
- Window rules: 14" RO fits a stud bay (centre on a bay centre); 27" RO max bearing
  (centre on a stud line, jacks added); 30" RO max non-bearing on a STUD LINE (one stud
  broken); above that the RO has to move to a bay centre and break two, which is why the
  42" WT-4248 sat on one until it was retired (2026-08-01). **The ideal position is a
  property of the RO width, not of the wall** — narrowing a unit can move it, and
  `structural.window_framing_module` (asserted clean by
  `test_catlin_contract_m3.py::test_catlin_window_openings_follow_the_sixteen_inch_framing_module`)
  is what says so. Resize windows to fit the grid, not vice versa. One type per width
  family — WT-1424, WT-1864 (the attic gable's juliet pair, head at 8'-0"), WT-2736,
  WT-3036 (north gables/hall), WT-3048 (the south-glazing size, head at 6'-8") —
  each family sharing the one height that fits its most constrained wall. Five sizes
  carry the whole house; the 18" family breaks one stud and so centres on a stud line,
  which is also what lets the juliet pair sit 32" apart instead of 48".
  **Two exceptions, both 2026-08-01**, each a second height on an existing width family
  because the rule's own remedy — give it its own width family — costs more than the
  second height does:
  - **WT-1448** (the south gable's flankers): the 4:12 rake forbids the remedy outright.
    Any width over 14" breaks a stud and takes a header, and the header is what hits the
    rake (WT-1864 at the nearest usable stud line misses by 1.8"). 14" fits inside a bay
    and takes no pack, so only the glass has to clear.
  - **WT-3048** (the south glazing): the 30" family's committed height (WT-3036's 36")
    would drop the south head off the 6'-8" door-head line the whole face is built on.
- Facade rules (2026-07-30 pass, gable revised 2026-08-01, E/W revised 2026-08-15).
  Windows line up or they are not there:
  - **The residue rule — read this before moving any window.** A wall segment lays its
    studs out from **its own start node** (`resolve/framing/stud_module.py`), so where a
    window may legally sit is a property of that node, not of the facade. Two segments are
    in phase only if their start nodes share the same residue mod 16"; a **column** between
    storeys needs the two host segments to have the **same** residue, and a **mirror pair**
    within one storey needs the two residues to **sum to 0** mod 16". A near-miss on a
    facade is almost always this and never a window's own offset — no amount of moving the
    *window* fixes an out-of-phase *segment*. It is why the south gable needed N-A-V1 at
    22'-8" (see **Gables**), and why the 2026-08-15 E/W pass is four node moves and only
    then some window moves.
    - **Corollary, the 8" rule.** `structural.window_framing_module` puts a 14" RO on a
      **bay centre** and a 27"/30" RO on a **stud line** — 8" apart on one grid. So a 14"
      unit can only column with a 27" unit when the two segments are 8" out of phase, and
      *never* when they share a residue. Retyping the narrow unit is usually the answer
      (WIN-M-BATH2, 2026-08-15).
  - **Columns.** The south face stacks four columns clean through main and second
    (x 4'-0", 9'-4", 27'-4", 32'-8" — all four moved 8" inboard on 2026-08-01 when the
    glazing narrowed to WT-3048 and the module's ideal position went with it, both pairs
    shifted the same way so the storeys still stack and the two segments' 8" phase miss
    is unchanged). The attic no longer joins them — see **Gables**.
    The **west face stacks three** through main and second (y 5'-0", 19'-8", 31'-4"). It
    had exactly one (31'-4", and only because both its hosts start at y=33'-4") until
    2026-08-15, when N-M-W3 went 13'-4" -> 13'-0" and N-M-W2 went 22'-2" -> 22'-4" to put
    the main storey's west stud grid in phase with the second's — the residue rule, applied
    to the two tees rather than to the six windows. WIN-M-BATH2 was retyped WT-1424-T ->
    WT-2736-T at a 3'-0" sill to reach the 19'-8" column (the 8" rule), which also buys
    R303.3's window alternative outright. RM-M-BED gave up 4" and RM-M-BATH2 gained 6".
    **The fourth column is deliberately absent** and is pinned absent by
    `test_the_west_suite_window_pair_is_left_uncolumned_on_purpose`: WIN-M-BED-W2 (10'-4")
    and WIN-S-SUITE1 (13'-0") are the same unit on the same head line, and the only two
    shared stud lines their hosts offer are 10'-4" and 11'-8" — each leaving ~16" of wall
    to the far tee where the jamb pack wants ~16 1/2". At 11'-8" the king stud came out
    sharing 83% of a 2x6 with W-M-W3's end stud; at 10'-4" the identical clash lands on the
    second storey. **When a column costs a stud, it is not a column** — buy the alignment
    only with a whole 16" module of room depth, or not at all.
    The north face stacks one three-storey column at x=28'-0" (WIN-M-KITCH /
    WIN-S-HALL-N / WIN-A-N2).
  - **Rows.** Where a column is impossible, the storey's own rhythm wins instead — but a
    row must be *centred*, not merely even. The east second storey ran a perfect 9'-0" beat
    that sat 10" north of the centreline until 2026-08-15 (5'-4" of wall south, 3'-8"
    north); it now reads 4'-0" / 13'-0" / 23'-0" / 32'-0", exactly mirrored about y=18'-0"
    in station, width (27/30/30/27) and head (6'-0"/7'-0"/7'-0"/6'-0") over one 3'-0" sill.
    That took N-S-E2 to 17'-8" and N-S-E3 to 26'-8" — again the residue rule — and the
    bedroom bays became 8'-8"/9'-0"/9'-4" to pay for it, shrinking BED1 (whose R303.1
    margin is 0.05 sf) and growing BED3 (which has two windows). The east main row keeps
    its 8'-0"/7'-4" beat and its blank kitchen stretch north of WIN-M-DIN-E2: the blank is
    the composition, so the 8" hitch is not worth moving N-M-E1 for. WIN-S-STUDY3 at 4'-0"
    now also columns with WIN-M-LIV-E1.
  - **Knee band.** Both 5' knee walls carry a WT-1424 pair; the west is exactly mirrored at
    3'-4"/32'-8" and the east is 4" off at its north end, at 3'-4"/32'-4". It stays off:
    W-A-E2's grid starts at N-A-E1 (y=9'-0"), and both fixes for it — 9'-4" for the pair's
    own mirror, 8'-8" for a column under WIN-S-BED3 at 32'-0" — drag N-A-C2 and therefore
    W-A-SN, whose south face is what closes FO-A-STAIR's north edge. Building 9'-4" put
    3'-0" of unguarded stair well on `code.R312_1_guard`. The band reads as its own row
    across 5'-6" of blank wall, so neither alignment is worth reworking the stair for.
  - **Head lines.** The west face puts every main and second head on one 6'-0" line —
    27" units at a 3'-0" sill, 14" units at 4'-0". The south face shares a 2'-8" sill.
  - **Gables** read symmetric about the ridge before they answer to anything below:
    that is why WIN-A-N1 stays at 7'-4" rather than stacking on WIN-S-STAIR-N, and why
    the 2026-08-01 pass gave the south gable up as a column-capper. It now carries four
    openings, exactly mirrored about x=18': WT-1448 flankers at 8'-8"/27'-4" (head 6'-8")
    around the WT-1864 juliet pair at 16'-8"/19'-4" (head 8'-0"), one 2'-8" sill under all
    four, heads stepping with the rake. The corner pair at 3'-4"/33'-8" was retired — the
    rake leaves ~6'-0" of wall there and nothing stands in it without reading as a stamp.
    Mirroring the east half at all required moving N-A-V1 from 22'-4" to **22'-8"**: a
    wall's stud grid lays out from its start node, and 36' − 22'-4" is not a multiple of
    16", so W-A-S4's bay centres were 4" out of phase with a mirror of W-A-S1's.
  - WT-1424 still does the work wherever a bigger unit will not fit — in the 5' knee
    walls, where its 2'-0" height is the only one that clears the plate, and in the
    mudroom. Under the south rake it handed off to WT-1448.
  - **Tempered twins (2026-08-01).** `WT-1424-T`, `WT-2736-T`, `WT-3036-T` and `WT-3048-T`
    are their parents in every dimension and differ only in the glass, for the ten units
    R308.4 puts in a hazardous location (a wet room, within 24" of a door, within 60" of a
    stair). They are **not** width families and no facade or framing rule sees them: adding
    a tempered unit is a retype, never a move. All three glazed *door* types are tempered
    outright — R308.4.1 has no location test to fail.
  - **The east bearing wall now takes a 30" RO** (2026-08-01): `WIN-S-BED1`/`BED2` had 6.75
    sf of glass against R303.1's 9.95 sf, and 27" cannot reach it at any height that fits
    under the 9'-0" plate. `preferences.toml`'s `max_window_ro_bearing_in` went 27 → 30 with
    them; the jack/king/header pack is what pays for it. The margin is 0.05 sf — growing
    either room's clear face fails R303.1 again, and the answer then is a taller unit, not
    a wider one.
- **Two basement assemblies, and the split is a condition, not a preference.**
  `CATLIN_BASEMENT_12` (N/E/W: `W-B-E1/E2`, `W-B-N1/N2/N3`, `W-B-W1/W2`) covers its exterior
  XPS with a 1/2" `foundation-protection-panel` banded from 6" below grade to the top of the
  wall — 2'-10" of exposure the two lifts created, ~360 SF, authored as a
  `Layer.extent` off the `GRADE` datum. `CATLIN_BASEMENT_12_GARDEN` (south: `W-B-S1/S3`)
  keeps the full-height parge coat, because the sunken garden exposes that face from -9'-0"
  to 0'-0" and a grade-datum band cannot describe that. `W-B-S2` is the same stack under a
  third tag, `SAUNA_LINER_ON_BASEMENT_12_GARDEN` (2026-08-18): it is the sauna's south face,
  so it carries the hot-side liner *inboard* of the pour, banded to the room's 7'-6" ceiling.
  Its outboard five layers are the shared `_GARDEN_CONCRETE_STACK` tuple, so the two tags
  cannot drift; it aligns on `face("concrete-ext")` with **no** offset, so the pour sits
  exactly where W-B-S1/S3 leave it. Both carry exactly 4.55" outboard of
  the concrete face — the panel is the same 1/2" as the parge it replaces — which is what
  `N-B-BRICK-W`/`-E`'s `inch(-4.55)` stand-off is measured from; changing either thickness
  moves the brick veneer. See `notes/basement_to_framed_wall_detail.md`.
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
