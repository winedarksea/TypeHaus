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
  this is a note rather than a check, but it is a real 2'-10" against whatever the local
  limit for this district is. If a limit is close, the levers are the attic's 11' ceiling
  and the 4:12 ridge, not the lift.

  **JURISDICTION CORRECTION, 2026-08-22 — the site is most likely SAINT PAUL, not
  Minneapolis, and "Minneapolis" in this repo has meant the metro generally.** That matters
  because the two cities measure height from different data, so the number this note is
  worried about is not the number `building_height_summary` computes:
  - **St Paul §520.160 measures from NATURAL GRADE at the curb**, or at a point 10 ft from
    the front lot line's centre — not from average grade around the building.
    `peak_above_grade_m` uses average grade, which is the datum every other check in this
    model shares. On a lot that falls away from the street the two disagree by the whole
    fall, and in either direction.
  - So **no `height_limit` and no check is being authored here.** Encoding a limit measured
    from a datum the model does not carry would produce a confident wrong answer, which is
    worse than the note. The item stays ON HOLD pending two facts only a survey and a
    parcel lookup can supply: the zoning district, and the natural grade at the curb.
  - **Two knock-ons of the correction, FLAGGED AND DELIBERATELY NOT CHANGED**, because both
    want confirming against Ramsey County rather than swapping on a guess:
    - `plan/site.py:73` authors the ground snow load as "Hennepin County / Minneapolis".
      Ramsey and Hennepin are adjacent and almost certainly share the value, but the
      *citation* is wrong if the site is in Ramsey, and a sourced number with the wrong
      source is the thing this repo's conventions exist to prevent.
    - `prices.toml [tax]` uses suburban Hennepin's **8.525%**. Ramsey County's combined rate
      is its own figure, and the 2026-08-20 owner decision that picked 8.525% over the
      city's 9.025% was reasoned about Hennepin. On ~$300-600k of taxable material a
      half-point is $1,500-3,000.

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

## Remaining Work

**Deliberately not done, and why:**

- **The four exterior placeables keep their false room refs** (both wall hydrants, both
  porch curtain rods). Giving them an honest home means unconditioned `Room`s for the porch
  and the balcony — enclosing walls, envelope, energy and ventilation consequences — for
  four UNKNOWNs this file already accepts. Not worth the complexity.

- **In-plan variant forks + compare UI** (deferred again by decision 2026-08-02,
  **re-affirmed 2026-08-07**). `model.json` now carries the variant catalog; `prices.toml`
  $-ranges work in `haus variants compare` and takeoff. Still missing: `variant_of`/`active`
  forks with one-active integrity + promote-with-uid-remap, and the UI side-by-side compare
  canvases.

- **Deck post/footing UNKNOWNs (2026-07-26, by design).** Both sunken-garden decks are now
  `service="deck"`: `deck_post_size` has no R507.4 row for the 12" round column PT-SG-COL,
  and PT-SG-COL plus the six balcony pillars bear on non-Pad chains (grouted CMU / bell
  footing) so `deck_footing_size` can't resolve. (`deck_beam_span`'s two genuine R507.5(1)
  overspans were closed 2026-07-31 by going engineered.)
- **Windows: 4 residual member-interference overlaps** — now **pinned** by
  `test_catlin_window_member_overlaps_pinned_at_four` (junction clear disabled — the
  honest metric). Measured composition drifted from this file's memory of 4+4: it is 2 at
  one T (CSW148's king stud), 1 L corner, 1 vs the stair soffit plate. The T was 6 until
  2026-08-22, when O-S-VANITY moved off the corner square that the 8" suite sound wall grew
  the day before — its whole jamb pack had been standing inside it. (Historic: 138 → 8 → 4.)

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
- ~~**Wood solids still bill as concrete, and two deck planks now bill nowhere**~~ —
  **CLOSED 2026-08-22.** All three sub-items landed, and the shape of the fix is the one this
  note argued for: author assemblies, do not widen the guard.
  - `BEAM_LVL`, `BEAM_KDAT`, `POST_KDAT` and `PIER_CONCRETE_12` are authored in
    `plan/assemblies.py`, with `lvl` and `kdat` added to `library/materials.py`. Every one of
    the twenty `Beam` solids and all nine bare `Post` solids now states a material, which
    splits `beam/None` and `column/None` into `(category, assembly)` groups.
  - `cli/prices.MATERIAL_ONLY` widened from one tag to a **set** of accepted
    `structure_material` values (`frozenset[str | None]`, where `None` means "the model never
    said" and marks the catch-all section), and a new **`[timber]`** section prices the wood
    half of `structural_solids` end to end — `_SECTIONS`, a `Prices` field, `ESTIMATE_PLANS`,
    `ALTERNATE_UNITS`, `SECTION_CODES`, a `[basis]` and a `[basis_notes]` line.
    `SOLID_SECTION` became `SOLID_SECTIONS`, because two sections read that table now.
  - The re-key is the part that could have silently zeroed a line, and did not: the bare
    `"beam"` and `"column"` keys in `[concrete]` are **deleted**, replaced by
    `column:PIER_CONCRETE_12` and `column:SUNKEN_GARDEN_COLUMN_16` there and
    `beam:BEAM_LVL` / `beam:BEAM_KDAT` / `column:POST_KDAT` in `[timber]`. The before/after
    `haus takeoff` diff is clean: every beam and column row still prices and the `unpriced`
    list is unchanged, line for line.
  - The LVL beams now bill at **$2,041–4,317** against the retired row's $954–2,120. The
    2026-08-21 note on that row predicted "the rate is wrong in kind, and probably in size
    ... ~$1,860–3,530/cy". It was.
  - `SL-SG-DECK` is gone: the aluminium plank is `FS-SG-DECK`'s `subfloor` and bills as
    182.0 SF in `[sheet_goods]`. The conversion was exact — the balcony joists cantilever 6"
    and the deleted slab's outline *was* that cantilever.
  - **`SL-BW-DECK` stays a Slab, and that is the finding.** It was converted with the
    balcony and converted back the same day. `resolve/floors.py` draws a subfloor
    bearing-line to bearing-line by the outline's perpendicular extent, so a floor system's
    sheet is exactly its joist field; the breezeway plank oversails its rim 2 3/4" at each
    end onto the two door thresholds. Keeping the post-box outline FAILS
    `code.R311_3_exterior_landing` on D-M-ENTRY and D-G-SERVICE (a door has to open onto
    something); stretching the outline to the faces lays a joist through PT-BW-1..4 and its
    own neighbour, five `structural.member_interference` FAILs. These joists are hung flush
    between the beams and cannot cantilever. **The engine has no way to say "sheet wider
    than joist field", and that is the change this wants** — not a re-model of the deck.
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- Window sealing detail (RM-S-PLANT's is drawn — TR-CATLIN-PLANT-OPENING, 2026-08-18 — and
  is the strictest case in the house; the rest of the envelope still rides
  TR-CATLIN-FRAMED-OPENING)
- Does balcony access have to pass through the plant room? `D-S-DECK-W` is a 60" exterior
  French door in a 70 %-RH room and its threshold will condense (raised 2026-08-18)
- Floor drain in RM-S-PLANT — confirm, with the trap primer it implies (raised 2026-08-18)
- Make sure all desired access panels are in
- Small windows on corners?
- Improve the symmetry of the windows on the east and west side
- Permit drawings
- The house's own strip footings are eccentric under their walls, the same way the garage
  stem's were before 2026-08-15: `FT-B-*` is a 20" strip centred on the y=0 node line,
  under a `face("concrete-ext")` wall whose 12" of concrete runs 0..12" inboard, so the
  south toe is 10" and the north one is -2". `Footing.center_on="wall"` now exists to
  fix it, but it is deliberately *not* authored there: the glazed-brick plinth's whole
  derivation (`params/foundations.py`, `FT-B-BRICK`) leans on that 10" toe being there
  to bear on. Correcting the footings means re-deriving the plinth with them.

* Is this enough glazing for light feeling rooms (along with LED strips, etc)
* Plan a revamp off the plumbing to see if we can make any of the runs more efficiently routed. Try to run things through the NW corner of the house's maintenance shaft, and make sure there are plumbing shutoffs in appropriate places.
* How can we properly anchor the heat pumps on the upper porch without compromising the waterproofing of the aluminum decking? Perhaps we need a different subtype of flooring there?
* **Move EQ-B-ESS-BATT and its enclosure to the NE corner of the mechanical room** —
  **BLOCKED, investigated 2026-08-22, nothing moved.** `EQ-B-WH`, the 24"x24" water heater,
  stands at **(6'-2", 32'-10")**, which is itself in that corner. The battery type carries a
  REQUIRED +/-48"/+/-41" separation zone (`mep_hvac.py`, an owner rule) and
  `advisory.ess_clearance` has no room exemption and no wall exemption — "the wall between
  them does not make the distance". Clearing the water heater needs the battery east of
  x=11'-2" or north of y=37'-3", and the room is x 0..10, y 18..36: **no position in the NE
  corner works.** Confirmed by moving it to (9'-0", 35'-0") and running the check, which
  FAILED naming EQ-B-WH; the move was reverted. Three ways forward, all owner decisions:
  move the water heater (it has a T&P relief line `PR-B-WH-TPR`, a 240V circuit, a pan and a
  vent), narrow the authored zone, or leave the closet in the SE corner where it clears.
  Enclosure fire-proofing is deferred to its own pass — `INT_ESS_CLOSET_STEEL` is untouched
  and `advisory.ess_enclosure` passes on all four walls today.
* garage stairs should probably be pressure treated wood or a prebuilt metal staircase
* 3d models of the stair handrails need some work
* Add two workbenches, outlets above them, and a hard-wired ethernet cable run to the RM-B-Workshop. Can likely share the spa conduit.
* Add a hardwired ethernet connection to the RM-M-STUDY, and one to the center of the north wall of the media room.
* Model a large U-shaped couch and TV in the basement media room. Billy bookshelves on W-B-CE to either side of the door in the media room.
* is the under basement slab foam and polyethylene modeled completely? It's R-10 of XPS.
* We need to review the frost risk of the sunken garden around the house footings. Perhaps make the brick wall on an ICF footing. May need to put some ICF footings for the house near there too.


## Questions from 08-15 session

The starter template gained 4 advisory FAILs. Clearing its radon ERROR required a junction box for the future fan (the code requires it), and electrical.room_lighting / receptacle_spacing both gate on "any electrical device exists" — so one box flips them from "not modeled" to "modeled and incomplete." They're honest findings and advisory only, but the alternatives are adding a full electrical package to a deliberately minimal template or loosening those checks. Your call.

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

## Basement Ceiling

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
  **The *finish* half is derived as of 2026-08-21** — `Slab.floor_finish` on `SL-M-DECK`
  resolves the band as a `FinishZone` inside `RM-M-LIVING`, so the polish and the plank bill,
  draw and price separately and the split tracks `_BAND_Y`. What is still missing is the
  **joint**: the derived condition a `Transition` could bind to bill the 31.5 lf of reducer
  and the soft joint along the y=13' leg of it.
- **`room_floor_elevation` never adds a FloorSystem's subfloor**, so a room over joists
  resolves its floor 3/4" below the surface people stand on. It prefers a slab top under the
  room and otherwise falls back to the wall base — which is the storey datum, i.e. the top
  of the joists, with the plywood still above it. Placeables are measured off that
  (`resolve/placeables.py`), so every switch, receptacle, pendant and register in a
  wood-floored room sits 3/4" low. Invisible until 2026-08-21, because every main-storey
  room agreed with every other; now `RM-M-LIVING` reads +3/4" (it is over `SL-M-DECK`,
  whose cap is pinned to the finished floor) and its nine neighbours still read 0'-0". The
  living room is the one that is right. Fixing it means adding the subfloor to the wall-base
  fallback, which moves every placeable in every wood-floored room in the house by the
  subfloor thickness — a real cascade, worth its own pass with the goldens re-blessed
  deliberately. `test_canvas_placeables.py` derives the offset rather than asserting it, so
  it stays honest either way.
- **Basement HVAC could ride the new joist bays.** `DU-B-ERV-SUP`/`-RET` are
  `DuctRouting.CHASE` because the ceiling had no bays at all; two thirds of it does now, and
  the west half's run east-west the way the trunk does. Left as chase because the runs also
  cross the concrete band, and splitting a trunk between bay and chase is its own pass.

# Project Management (deferred)
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

Once an idea here has a number against it, it moves to `plans/cost-options.md` — the
priced upgrade/downgrade menu (started 2026-08-08).
