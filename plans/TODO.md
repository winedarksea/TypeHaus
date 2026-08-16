# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

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
  - Either way `W-SG-ARCH` (16", off every IRC table) stays engineered, so if an engineer is
    being engaged for the arch anyway, folding these two into that scope costs little.

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
  - `SUNKEN_GARDEN_ARCH_16` is 16", off every IRC table — UNKNOWN, engineered either way.
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
- Add the plant room wall types (deferred by decision 2026-08-02)
- basement ceiling, some of this wood joists maybe (deferred by decision 2026-08-02)
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- House being a bit higher, cladding detail
- Window sealing detail
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
- Possibly moving house and sunken garden up (not garage), accounting for split layer
- Small windows on corners?
- Balcony railing?
- Do "drain tile" and "french drain" duplicate at all here?
- We are thinking of switching W-SG-ARCH to be a column and beams like PT-SG-COL and BM-SG-BKE, then replacing the masonry railing right above it with a metal railing more like RL-SG-BALCONY
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

The sunken garden's 16" arch wall and three free retaining walls remain UNKNOWN — engineered. That's unchanged and correct: R404.4 sends a free-standing wall retaining 9'-9" to an engineered design regardless of thickness, and no research closes that.

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

### Other visual ideas (just ideas, not a TODO)
Dark base to the house
Dark panel along the panel of the corner most panels
Standing seam clamps to anchor decorative elements, possibly at gable peak, or lightning rod
Architectural lighting on facade (try to aim to be dark sky friendly)

### Potential cost cutting (just ideas, not a TODO)
Remove the attic level and switch to truss/blown in insulation
Remove the arched concrete and switch to a metal railing on wood beam and columns

Once an idea here has a number against it, it moves to `plans/cost-options.md` — the
priced upgrade/downgrade menu (started 2026-08-08). Both of the two above are in it now.
