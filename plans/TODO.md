# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

- **Zoning height, after the lift — now 2'-10" (raised 2026-08-18, grew 2026-08-21).**
  Grade moved to -2'-6" so the house stands out of the ground, and to -2'-10" when the
  basement-ceiling overhaul put a 12 5/8" deck where a 9" slab had been and the house rose
  4" to keep the basement's headroom. The building's peak above average grade grew by
  exactly that much both times (`building_height_summary.peak_above_grade_m`, and the
  north/south elevations' ridge dimension). Nothing in the engine enforces a height limit —
  `SetbackSpec` is plan-only, and there is no `height_limit` on a jurisdiction profile — so
  this is a note rather than a check, but it is a real 2'-10" against whatever the
  Minneapolis limit for this district is. Worth confirming against the zoning code before
  the lift is committed to; if a limit is close, the levers are the attic's 11' ceiling and
  the 4:12 ridge, not the lift.

- **What braces the porch and balcony east-west, now that the arch is gone?**
  (raised 2026-08-18, and the one item on this list that the arch swap *created*.) Removing
  `W-SG-ARCH` and the three `W-SG-RAIL-*` parapets removed the structure's only E-W shear
  element: the two side walls run N-S and brace that direction only, and the masonry the
  balcony pillars were grouted into was the de facto fixity for five of the six. Simpson say
  so themselves — ESR-1622/ESR-3050: *"post bases do not provide adequate resistance to
  prevent members from rotating about the base"*, and they are *"not recommended for
  non-top-supported installations (such as … guard rails)."* Nothing is authored for this and
  **nothing should be until it is decided** — a number invented in the model is worse than an
  open question. The options, in ascending cost:
  - **Extend the knee-brace rule to the centre pillars.** DCA6-2015 p.10 wants a brace on any
    post over 2'-0"; `PT-SG-BR2`/`BF2` are deliberately left as leaning columns today
    (`params/sunken_garden.py`, KNEE_BRACES) because bracing them pushes thrust into
    `PT-SG-BR2`, the one pillar bearing on porch decking. That reasoning is still right, so
    this is the cheap option and not obviously the correct one.
  - **A moment base at the four corner pillars.** `MPB66Z`, ESR-3050 Table 11: 2,680 lb-ft
    unreinforced — but it needs **5" of side cover**, which the new 16" square `PT-SG-FCOL`
    has and the 12" round `PT-SG-COL` does not. The four pillars that want it bear on 12"
    concrete wall tops, so it is not free there either.
  - **An engineer's lateral design.** The honest answer, and the same consultant the two
    side walls below already need.

- **The exposed LVL beams are untreated, and ICC-ES says they should not be.**
  (raised 2026-08-18, deliberately out of scope of that day's change.) `BM-SG-BKW`/`BKE`,
  `BM-SG-FRW`/`FRE` and the three balcony beams are all authored as plain LVL. **ESR-1387
  §5.3** limits Microllam/Parallam/TimberStrand to *"covered end-use installations with dry
  conditions of use in which the in-service equilibrium moisture content is less than 16
  percent"* — an open porch under a slatted balcony generally is not "covered". The right
  product is treated **Parallam Plus PSL** (Weyerhaeuser TJ-7102). It was not folded into the
  arch swap on purpose: PSL comes in 9¼ / 11⅞ / 14 / 16" depths, and 11.25" was chosen
  precisely so derived elevations would not move (`params/sunken_garden.py`'s `back_beam`
  note). Changing it moves the porch joist soffit, the column tops and the hanger elevations
  together, which is its own change with its own check diff.

- **`CN-SG-HGR-W`/`E` are wood-to-wood hangers landing in 12" of concrete.**
  (raised 2026-08-18.) They are `LUS210`. The front pair authored the same day are
  `HUCQ410-SDS` — the concealed-flange hanger Simpson publishes for a wood member on concrete
  or masonry (`library/hardware.py`, `ROLE_CONCRETE_FACE_MOUNT_HANGER`) — which is what these
  two should be as well. Left alone only because it is a different decision from the arch
  swap and deserves its own line rather than a silent retype.

- **Do the porch side walls `W-SG-W1` / `W-SG-E1` count as laterally supported at the top?**
  (raised 2026-08-16) These two 12" walls hold 9'-9" of fill and carry `FS-SG-PORCH`'s
  framing through `CN-SG-HGR-W`/`E`, with the garden slab at their foot. That is the *shape*
  of permanent lateral support top and bottom — but whether a porch deck of two 2x12 back
  beams actually braces the head of a wall retaining 9'-9" is a judgment about the real
  structure, not something the model can read off its own geometry, and it decides which code
  path the walls are on. They are the last unanswered foundation walls in the house; the
  check reports them UNKNOWN until this is authored.
  - **"top_and_bottom"** puts them on IRC Table R404.1.2(8)'s 10' x 10' row, which asks for
    **#6 @ 38" o.c.** vertical, at 1 1/4" cover from the inside face (footnote h), Grade 60.
    That is a *prescriptive* answer — R404.1.3 says drawings using that section need no
    engineer's seal — so it needs no consultant, just `vertical_reinforcement` authored.
  - **"unsupported"** puts them with `W-SG-E2`/`S`/`W2` under R404.4: engineered design, 1.5
    safety factor against sliding and overturning.
  - The 16" `W-SG-ARCH` used to be the free rider here — off every IRC table and engineered
    either way, so folding these two into its scope cost little. It was retired 2026-08-18,
    and these two are now the *only* unanswered walls in the house; nobody else is paying
    for the engineer.

- ~~**PT-SG-BR2 bearing — reinforce locally, don't move it**~~ — **approved and authored
  2026-08-07.** `FloorSystem.reinforcements` is the way to author it: a
  `JoistReinforcement(at, plies, member, blocking, source)` on FS-SG-PORCH, whose `at` is
  read back off the pillar loop so the two cannot drift apart. The resolver finds the
  nearest joist line and emits 2 extra `sister_joist` 2x8 plies face-to-face toward the
  load — full length, cantilever included — plus 2 `blocking` members to the adjacent
  lines, all billing automatically. `CN-SG-TIE-BR2` (H2.5A, ~455 lb vs the ~0.45 kip
  demand) is the uplift tie at the far bearing of that line — the arch-wall sill until
  2026-08-18, the `BM-SG-FRW`/`FRE` hangers since; the part was already in
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

- ~~**The basement and sunken-garden foundation walls exceed the plain-concrete
  unbalanced-fill limit**~~ — **withdrawn 2026-08-16: there was no such limit, and the two
  FAILs were the check's, not the house's.**

  `structural.foundation_unbalanced_fill` screened against a table it cited as "IRC Table
  R404.1.2(1)", capping a 12" wall at 7' of unbalanced fill at 45 psf/ft. R404.1.2(1) is
  *"MINIMUM HORIZONTAL REINFORCEMENT FOR CONCRETE BASEMENT WALLS"* — two rows about where
  horizontal bars go, no backfill limits in it at all. No IRC edition from 2009 through 2021
  publishes any maximum-unbalanced-fill table for plain **concrete** walls, and the numbers
  the check used match nothing: not R404.1.2(8), not the plain **masonry** table
  R404.1.1(1), not IBC 1807.1.6.3(1). They were also wrong in the *unsafe* direction — they
  rejected walls the code plainly permits.

  The governing table is **R404.1.2(8)**, "MINIMUM VERTICAL REINFORCEMENT FOR 6-, 8-, 10-
  AND 12-INCH NOMINAL FLAT BASEMENT WALLS", now transcribed in full in
  `checks/structural/_r404_table.py` (all 324 cells, read from four independent renderings
  of the chapter in agreement and cross-checked against all 243 comparable cells of the IBC
  twin, Table 1807.1.6.2). It is indexed on unsupported wall height **as well as** backfill
  height, and most of its cells read `NR` — no vertical reinforcement required.
  - 10 `CATLIN_BASEMENT_12` walls: 12", 9' storey, 9' of fill → the 9' x 9' cell, **NR**.
    **PASS**, no steel and no engineer. This is the one the old table got wrong.
  - 3 `SUNKEN_GARDEN_WALL` walls (`W-SG-E2`/`S`/`W2`): free retaining walls, open along
    their whole top. R404.4 sends them to an engineered design at a 1.5 safety factor
    against sliding and overturning whatever the table would have said — the table is a
    *basement* wall table and presumes bracing top and bottom (footnote g). They author
    `lateral_support="unsupported"` and report **UNKNOWN — engineered**, honestly.
  - 2 `SUNKEN_GARDEN_WALL` walls (`W-SG-W1`/`E1`): **open question, see Questions below.**
  - The 8 `GARAGE_ICF_6` stem walls retain 3.5', under the 4' at which R404.1.1 and the
    table engage at all — PASS. Watch footnote d if that ever crosses 4': a 6" wall in a
    stay-in-place form still takes #4 @ 48 even where the cell reads NR.
  - `RETAINING_BLOCK_12` (2.5') likewise; the interior basement cross walls author
    `unbalanced_fill=ft(0)` because they have soil on neither side, so they are not screened.

  Two new fields carry this: `FoundationWall.lateral_support` (the precondition for the
  whole prescriptive path — unauthored, a wall retaining 4'+ is UNKNOWN rather than assumed
  braced, because assuming bracing is the unsafe direction) and
  `FoundationWall.vertical_reinforcement` (what the wall *has*, against what the table says
  it *needs*). `engineering_spec` still short-circuits both.

  One transcription caveat is recorded in `_r404_table.py`: the 8"/60 psf/9' wall/6' backfill
  cell reads `#6 @ 39` in all four IRC sources and `#5 at 39` in both IBC editions. The
  conservative `#6 @ 39` is encoded, flagged rather than silently "corrected". It is the lone
  break in that column's monotonicity, so the IBC is probably right; a printed ICC copy would
  settle it. No catlin wall lands on that cell.

## Remaining Work

**Deliberately not done, and why:**

- **The four exterior placeables keep their false room refs** (both wall hydrants, both
  porch curtain rods). Giving them an honest home means unconditioned `Room`s for the porch
  and the balcony — enclosing walls, envelope, energy and ventilation consequences — for
  four UNKNOWNs this file already accepts. Not worth the complexity.

- ~~**The IRC reinforced-foundation tables were not encoded.**~~ — done 2026-08-16, and it
  turned out to be the fix for the two foundation FAILs rather than a nicety. The rows *are*
  reproducible; see the withdrawn item under "Accepted, by decision" above. Only
  R404.1.2(8) (flat walls, 6/8/10/12") is encoded — the waffle- and screen-grid ICF tables
  R404.1.2(5)-(7) are not, so an ICF wall past 4' of fill will read UNKNOWN, correctly.

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
- **RM-S-PLANT / RM-S-STUDY2 fresh-air terminals — DRAWN (2026-08-16), closing the
  2026-07-30 "by decision" gap.** The study was always the anomaly: `EQ-S-HP1-AH` hangs in
  RM-S-STUDY2's own ceiling soffit, and a room does not breathe by being next to the
  machine. Both now take System 1 air from `DU-S-HP-SOUTH`, a new 8x6 branch in the
  FS-ATTIC joist bay at y=3'-4" — nothing can leave the trunk southward inside SF-S-DUCT
  (the 21"x43" air-handler case fills the box y 6'-0"..9'-7"), and nothing can run west
  along the attic deck (W-A-C1/C1B, the bearing wall under RB-HOUSE), so the branch goes
  over both rooms inside the floor cavity and passes under that wall's bottom plate.
  Terminals: `REG-S-HP-STUDY2` (22'-8", 3'-4") and `REG-S-HP-PLANT` (6'-8", 3'-4"), ceiling
  grilles at 9'-0". 150 cfm is taken out of the trunk's 750 by damper, not added to it.
  The mini-HRV idea for the plant room is dropped — it was solving a distribution problem.
  `mep.ventilation_distribution` now names no unserved room and the test pins the empty set.
  Residual: `DU-S-HP-SOUTH`'s rise out of the trunk head at x=19'-4" is undrawn, same
  status as `DU-S-ERV-HP-FEED`'s (below) — it rides the riser `DU-A-HP-STUDY` already
  leaves from.
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

## Breezeway

- **The 1" fall toward the garage is drawn, not framed** (lives in the drainage wedges; a `Beam` is a prism). If the wedge becomes a real element the fall moves into it. (It should be a 1" slope by angle of the framing, plus a east to west slope by a small wedge under the centerpoint of each rafter to slightly bend the polycarbonate)
  **Re-affirmed deferred 2026-08-07:** framing the fall means a sloped-`Beam` schema change,
  which is a bigger piece of work than the batch it kept coming up in.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Pantry (deferred by decision 2026-08-02)
- ~~Add the plant room wall types (deferred by decision 2026-08-02)~~ — **done 2026-08-18.**
  `PLANT_EXT_2X6_HUMID` / `PLANT_INT_2X6_BRG_HUMID` / `PLANT_INT_2X4_HUMID`, a shared
  `HumidityClass` axis on `Room` and four rules that read it, the U-0.14 glazing retype, the
  sheet-vinyl coved floor, the dedicated dampered extract off `EQ-B-ERV`, and wet-location /
  UL 8800 electrical. The whole argument and the numbers are in
  `houses/catlin/notes/plant_room.md`; decisions #55 and #56. What it deliberately did NOT
  close, each for a stated reason:
  - **The plant room's ceiling is specified but unmodelled.** PVC panel on furring over the
    same membrane, continuous with the wall membrane at the perimeter, and explicitly *not*
    a suspended/tile ceiling. `FS-ATTIC` carries no `ceiling_below`, and that field is one
    `DeckLayer` for the whole storey below — there is no room-scoped ceiling construction in
    the schema, so authoring it would give every second-storey room a PVC ceiling. Needs
    either a `CeilingPaneling` element (the `WallPaneling` shape, one surface up) or a
    per-room override on `FloorSystem`.
  - ~~**`RM-B-SAUNA` is still `humidity_class=NORMAL`, and that is a finding.**~~ — **closed
    2026-08-18, same day.** The axis surfaced a real gap (`W-B-S2`, the sauna's whole south
    side, was bare 12" concrete on the room face while
    `notes/sauna_basement_wall_detail.md` says the liner runs "walls + ceiling"), and
    `SAUNA_LINER_ON_BASEMENT_12_GARDEN` closed it: the liner variant on that wall, the room
    marked `WET`, and all four faces now passing `humid_room_liner` and `humid_room_finish`
    on the foil-faced polyiso at 0.015 perm. `glazing_dew_point` clears `WIN-B-SAUNA` by
    2.5 F at centre-of-glass with the frame accepted as condensing — recorded on the Room
    rather than hidden. Two details worth carrying forward: the liner's three layers carry a
    `LayerExtent` off `WALL_TOP` so a 7'-6" room does not bill 9'-0" of basswood off a
    foundation wall (and `takeoff/wood_surfaces.py` had to start honouring that band, which
    it was ignoring), and the 3 1/2" the liner grows inward moved `FURN-B-SAUNA-BENCH-S`,
    `FURN-B-SAUNA-BENCH-E` and `REG-B-EXH2` north with it — no check fires on
    furniture-vs-wall overlap, so those were hand edits the gate could not have caught.
  - **The showers are still unclassified.** Same axis, same rules, same question to answer
    first: what is actually behind the tile. The sauna is the worked example of what
    answering it costs — a liner variant on the wall that turned out not to have one.
  - **`FX-S-BALC-HYD`'s sleeve.** A freeze-proof wall hydrant passes through the plant room's
    liner into a −15 °F wall — a vapour leak and a cold surface at once. Needs a sealed,
    insulated sleeve detail; `SleevePenetration` exists but not for this condition.
  - **Cavity "canary" RH sensors** in a south and a west stud bay. The liner has no
    redundancy, and this is how a failure is caught in month three rather than year five.
    There is no sensor element kind.
  - **The humidifier.** An ERV loses ~16 % of the moisture in every air change; at this flow
    against −15 °F outdoor air that is 1.5–2 gal/day unrecovered. Not modelled — it wants an
    `Equipment` with a water supply and a drain.
  - **The room's clear face does not know about the liner.** `RM-S-PLANT` still resolves at
    159.15 sf; the 1 1/4" liner should take it to about 152. `resolve/rooms.py::_lining_inset`
    insets a claimed face by a single uniform figure derived from `Room.wall_lining` (0.635",
    the painted-gypsum stack) rather than by each bounding wall's own resolved lining, so the
    face sits on the node lines less that constant — which is why the sauna's 3 1/2" liner
    does not move its room polygon either. Systemic and pre-existing; fixing it moves every
    room's area and every `clear_face`-derived check at once, so it is its own change. Until
    then R303.1, the clear-floor checks and the finishes takeoff all grade RM-S-PLANT on a
    floor slightly larger than the one that gets built (which is the conservative direction
    for the glazing ratio, and the wrong one for clear floor).
  - **A floor drain in RM-S-PLANT** (the room should be hoseable): implies a drain line, a
    trap primer — the trap *will* dry — and slope in `FS-SECOND`. See the Questions list.
- **Wood solids still bill as concrete, and two deck planks now bill nowhere** (2026-08-19).
  `structural_solids` keys on solid CATEGORY, and a category is not a material.
  `cli/prices.MATERIAL_ONLY` now stops `[concrete]` pricing a row whose assembly's
  STRUCTURE layer is not concrete, and records the suppression in the unpriced list rather
  than dropping it silently. Three things are still open:
  - `beam` (1.06 cy, $276 – $445) and four of the nine `column` solids carry **no
    assembly**, so the model never states a material and the guard cannot fire. Every
    `Beam` in the house is LVL or dimensional (`SPEC.back_beam` = 2-1.75x11.25 LVL,
    `BM-M-HALL`/`BM-S-HALL` are LVL flitches, `BM-BW-*` is breezeway KDAT), and they bill
    **nowhere else** — a standalone `Beam` resolves to a solid, not a framed member, so
    this is a mis-price, not a double-count. Fix by authoring assemblies, not by widening
    the guard. `PR-BW-1..4` and `PT-SG-COL` are 12" sonotube piers that genuinely ARE
    concrete and also carry no assembly, so they must gain one before the wood ones can be
    excluded by default.
  - `ELM_TIMBER` (0.34 cy) and `POST_WHITE_PAINT` (0.40 cy) were reaching the estimate
    *through* `[concrete]` on purpose — `ESTIMATE_PLANS` says timber rows "price as 0 here
    — they bill via structural_solids". They are now honestly unpriced instead of priced
    as ready-mix. **There is no price section that bills a wood solid by volume**; that
    gap is the real fix.
  - `SL-SG-DECK` (balcony, aluminium plank) and `SL-BW-DECK` (breezeway, composite plank)
    are wood-framed walking surfaces modelled as `Slab`. Their concrete billing is gone,
    but `aluminum-deck` bills in no section at all and the breezeway's `composite-deck`
    only billed through that slab, so both planks are now unbilled. The fix is the one
    `SL-SG-PORCH` already had: delete the `Slab` and move the plank into its
    `FloorSystem`'s `subfloor=DeckLayer(...)`, where it bills as sheet goods. Trim
    `host_ref` is metadata only — never resolved or validated — so `TR-SG-FASCIA` and
    `TR-SG-WRB-FLASH` do not block it; the cost is rewriting the ~6 tests that assert on
    those two slabs (test_site_earth, test_detail_vocabulary, test_accessories x2,
    test_catlin_contract_m3 x2).
- ~~basement ceiling, some of this wood joists maybe (deferred by decision 2026-08-02)~~
  — priced 2026-08-18, **decided and built 2026-08-21**. See `## Basement Ceiling` below
  for what was done, and `plans/cost-options.md` for the money.
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- Window sealing detail (RM-S-PLANT's is drawn — TR-CATLIN-PLANT-OPENING, 2026-08-18 — and
  is the strictest case in the house; the rest of the envelope still rides
  TR-CATLIN-FRAMED-OPENING)
- Does balcony access have to pass through the plant room? `D-S-DECK-W` is a 60" exterior
  French door in a 70 %-RH room and its threshold will condense (raised 2026-08-18)
- Floor drain in RM-S-PLANT — confirm, with the trap primer it implies (raised 2026-08-18)
- Make sure all desired access panels are in
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
- Small windows on corners?
- Do "drain tile" and "french drain" duplicate at all here?
- ~~We are thinking of switching W-SG-ARCH to be a column and beams like PT-SG-COL and BM-SG-BKE, then replacing the masonry railing right above it with a metal railing more like RL-SG-BALCONY~~ — **done 2026-08-18.**
  `PT-SG-FCOL` (16" square cast concrete, chamfered, on its own spread footing) carries
  `BM-SG-FRW`/`FRE` into the side walls on `HUCQ410-SDS` hangers, mirroring the back edge.
  The beams are **flush** and the column stops at their soffit, which is not a style choice:
  a 16"-o.c. joist grid cannot miss a 16" column at midspan, so a column reaching the deck
  datum reads as three clashes in `structural.member_interference`. All three masonry guard
  walls went, not just the front one, and `RL-SG-PORCH` (36.3 LF of the balcony's own
  fascia-mount product) replaced them — a pair of LVL beams cannot carry ~420 plf of parapet
  the way 16" of concrete could. Measured saving **$5,395 – $11,257**; see
  `plans/cost-options.md`. Three follow-ons are open under "Needs your decision" above.
- ~~Add a packed gravel bed under the retaining wall blocks (W-RG-*)~~ — **done 2026-08-15.**
  `FootingBedding.host_ref` takes a FoundationWall as well as a Footing now, because a
  dry-stacked SRW wall stands on the levelling pad itself and inventing a footing to hang
  the bed off would order concrete nobody pours. `FB-RG-*` is 6" of MnDOT Class 5 on
  non-woven geotextile, 24" wide under the 12" block (6" past each face), topping out at
  the block underside (-2'-6"): 3.0 cy. No drain tile — it is bearing prep, and the
  drainage aggregate *behind* the block is still not modelled.
  The wall-hosted band is `rect_between` on the wall axis with no end extension, the same
  convention `_resolve_footing` follows, so the legs butt at the shared corner nodes: the
  stone is billed once and each 90° corner gives up a 2'x2' notch of its own footprint,
  ~0.15 cy over the three of them.
  **Its price is a placeholder** — `prices.toml` carries $22-45/cy for Class 5, set at
  about half the researched #57 rate rather than off a quote.
- Improve the symmetry of the windows on the east and west side
- Extend the outdoor curtain rods to cover all three exposed side of the porch (possibly as a single continuous curtain, if that is possible, or else as 4 single bay panels)
- Permit drawings
- The house's own strip footings are eccentric under their walls, the same way the garage
  stem's were before 2026-08-15: `FT-B-*` is a 20" strip centred on the y=0 node line,
  under a `face("concrete-ext")` wall whose 12" of concrete runs 0..12" inboard, so the
  south toe is 10" and the north one is -2". `Footing.center_on="wall"` now exists to
  fix it, but it is deliberately *not* authored there: the glazed-brick plinth's whole
  derivation (`params/foundations.py`, `FT-B-BRICK`) leans on that 10" toe being there
  to bear on. Correcting the footings means re-deriving the plinth with them.

## Questions from 08-15 session
The two ventilation FAILs were real gaps. RM-S-STUDY2 had System 1's air handler hanging in its own ceiling soffit and no supply terminal — a room doesn't breathe by being next to the machine. Both it and RM-S-PLANT now take air from DU-S-HP-SOUTH, a new branch in the FS-ATTIC joist bay; the air-handler case fills the hall soffit and the x=18' bearing wall blocks the attic deck, so the floor cavity over both rooms is the only continuous route

Do the porch side walls W-SG-W1/W-SG-E1 count as laterally supported at the top? This is the one genuine open item. They hold 9'-9" of fill and carry the porch framing, with the garden slab at their foot — the shape of support top and bottom — but whether a deck of two 2x12 back beams braces the head of a wall retaining that much is a judgment about the real structure. "top_and_bottom" puts them on the 10'×10' row: #6 @ 38" o.c., prescriptive, no engineer's seal needed. "unsupported" puts them under R404.4 with the free garden walls. They report UNKNOWN until you decide; it's written up under "Needs your decision."

One disputed table cell. 8"/60 psf/9' wall/6' backfill reads #6 @ 39 in all four IRC sources and #5 at 39 in both IBC editions. I encoded the conservative #6 @ 39 and flagged it rather than silently "correcting" it — it's the lone break in that column's monotonicity, so the IBC is probably right and up.codes probably carries a typo. A printed ICC copy would settle it. No catlin wall lands on that cell.

The starter template gained 4 advisory FAILs. Clearing its radon ERROR required a junction box for the future fan (the code requires it), and electrical.room_lighting / receptacle_spacing both gate on "any electrical device exists" — so one box flips them from "not modeled" to "modeled and incomplete." They're honest findings and advisory only, but the alternatives are adding a full electrical package to a deliberately minimal template or loosening those checks. Your call.

scripts/verify.sh still exits 1 — at ruff, not at anything I touched. The engine carries ~560 ruff findings and ~2171 mypy errors, all present at HEAD (I confirmed against a clean worktree; my changes are at exact parity on both). The distribution — line-length, import sorting, PEP-604 annotations, zip strict — is tool-version drift from ruff 0.16.3, not code rot. That's a lint migration of a few thousand call sites, well outside "tests, build checks, permit checks," so I left it. I did run every gate step past ruff manually: builds, bench, UI typecheck/test/build all pass.

The sunken garden's 16" arch wall and three free retaining walls remain UNKNOWN — engineered. That's unchanged and correct: R404.4 sends a free-standing wall retaining 9'-9" to an engineered design regardless of thickness, and no research closes that. (The arch wall itself went on 2026-08-18, taking its UNKNOWN with it; the three retaining walls still stand and still report exactly this.)

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

Make sure the basement door keeps the 7" step threshold (reduces flood risk)

## Basement Ceiling — done 2026-08-21

The brief that stood here is built. What it asked for and what was actually done:

- **Mixed deck.** `SL-M-DECK` was 1,233 SF x 9" of cast suspended concrete, the largest
  single line in the model (34.26 cy at $930-1,760/cy). It is now 414 SF — the band over
  the dining end, x 18'-36' / y 13'-36' — as an 8" BuildDeck/LiteDeck EPS stay-in-place form
  with a 4 5/8" cast cap. The other 819 SF is `FS-M-WEST` and `FS-M-EAST`, 11 7/8" I-joists
  at 16" o.c. on the same 18'-0" span to the x=18' line. The two systems are 12 5/8" deep
  each, matching `FS-SECOND`'s joist + subfloor, so re-apportioning the ceiling later is a
  matter of moving one boundary line. Both numbers live in `houses/catlin/params/main_deck.py`
  as `EPS_FORM_DEPTH` / `EPS_CAP`, with the 10" + 3" alternative (same depth class, ~21%
  less concrete, R-31) documented beside them as a one-line swap.
- **The lift was 4", not the 3" the brief guessed.** The soffit dropped 4 1/4" (9" of slab
  to 12 5/8" of deck plus 5/8" of gypsum), so grade went to -2'-10" and the basement storey
  to -9'-4"; the basement holds ~8'-2 3/4" clear. The main, second and attic datums did not
  move at all.
- **Walls.** `W-B-CW`, `W-B-CW2`, `W-B-CW3`, `W-B-CE` and `W-B-STR2` are framed — 2x6
  plumbing, 2x4 partition, steel-stud Type X, 2x6 staggered and steel-stud Type X
  respectively — each keeping its tag and uid. Four strip footings, four `FootingBedding`s
  and four socked drain-tile runs went with them.
- **`W-B-STR` stayed 12" concrete**, against the brief's guess that it would become a
  bearing 2x6. Three things are measured off its east face at x=10'-6": the stair shaft's
  7'-0", ST-B2M's flight width, and `FO-M-STAIR`'s west bearing edge — which is a real
  edge now that the hole is cut in joists rather than in a pour, and off this wall would
  take a 9'-0" engineered header. It keeps `FT-B-STR` either way, so framing it would have
  bought only its own ~4.9 cy.
- **Ceiling.** Drywall everywhere — IRC R316.4 wants a thermal barrier over the EPS, and
  stopping the board at the boundary was not worth 414 SF of exposed soffit. That retired
  `visible_basement_material` / `visible_basement_finish` from `preferences.toml`: the rule
  was written to re-derive from what is overhead, and with a covered ceiling there is no
  visible pipe left to have a rule about.
- **The bathroom heat mat did become tile over wood** — `FH-M-BATH2` is over `FS-M-WEST`'s
  subfloor now, on an uncoupling membrane rather than in thinset on a slab.

Left open, and worth doing next:

- **No check enforces IRC R316.4.** The gypsum thermal barrier over the EPS deck is
  authored (`CATLIN_DECK_EPS_INT`'s FINISH layer, and `ceiling_below` on both
  `FloorSystem`s) and nothing would notice if it were deleted. A `code.R316_4` reading foam
  plastic exposed to a room's interior would.
- **`code.R305_ceiling_height` reads `Storey.default_ceiling_height`, never the real clear
  height.** The basement's is authored 9'-0" and its actual clear is 8'-2 3/4"; the check
  did not notice the change in either direction, which means it would not notice a real
  violation either.
- **No boundary condition for "two decks meet in plan".** The mixed deck's wood/concrete
  line at y=13'-0" is a real movement joint — matched depths, unmatched stiffness — and the
  finish, the ceiling board and any tile field have to break on it
  (`houses/catlin/notes/mixed_deck_movement_joint.md`). It is a note and a drawing
  instruction only: a `Transition` binds to a derived boundary condition and there is no
  `deck_change:<assembly>|<assembly>` deriving on the shared edge of two floor elements, and
  a `ConstructionRule` bills along a wall or a ceiling rather than along a line between two
  floors. Nothing in `haus check` will notice if the finish is run straight through.
- **Basement HVAC could ride the new joist bays.** `DU-B-ERV-SUP`/`-RET` are
  `DuctRouting.CHASE` because the ceiling had no bays at all; two thirds of it does now, and
  the west half's run east-west the way the trunk does. Left as chase because the runs also
  cross the concrete band, and splitting a trunk between bay and chase is its own pass.

# Project Management
* Track to inspection (list of inspections, calendar, pass registration). Likely includes Kanban somehow
* Report final costs (but also reusable plan)
* Upload pictures/notes/voice notes
* system for collecting bids as a GC (bidders should see estimates for materials for their job but not the estimate cost already, that would give them numbers to aim at).
* Show for bids as the main image the backside of the house (so the design looks cheaper, for lower bids)
* local first (with drive, S3 bucket, or such for backup) or Cloudflare workers

Firstly design a house (with permit checks, building science review, floorplan editing in the 2d UI, 3d review, cost reduction and BOM review).
Secondly gather bids, organize the timeline (inspection gates, etc), then track completed progress.
Thirdly use the house design as a reference (ie for agents understanding live data on home assistant in context), potentially with feedback loop of updating the design or later running a remodel

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)

### Potential cost cutting (just ideas, not a TODO)
Remove the attic level and switch to truss/blown in insulation
~~Remove the arched concrete and switch to a metal railing on wood beam and columns~~ —
priced, then **taken 2026-08-18**; it is in `plans/cost-options.md` under "Taken".

Once an idea here has a number against it, it moves to `plans/cost-options.md` — the
priced upgrade/downgrade menu (started 2026-08-08).
