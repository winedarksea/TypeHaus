# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

## Needs your decision

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

- **The basement and sunken-garden foundation walls exceed the plain-concrete unbalanced-fill
  limit, and stay failing until the engineer's schedule lands (2026-08-01, workstream W5).**
  The new `structural.foundation_unbalanced_fill` reads IRC Table R404.1.2(1) at the MN
  profile's presumptive GM soil class (45 psf/ft equivalent fluid), where a 12" *plain*
  concrete wall is good for 7' of unbalanced backfill:
  - 10 `CATLIN_BASEMENT_12` walls retain 9.0' — **FAIL**.
  - 5 `SUNKEN_GARDEN_WALL` walls retain 9.8' — **FAIL**.
  - `SUNKEN_GARDEN_ARCH_16` is 16" thick, past the table's 12" maximum — UNKNOWN, engineered
    either way.
  - The 8 `GARAGE_ICF_6` stem walls retain 3.5' against a 4' limit — PASS. The limit
    dropped with the core (8" → 6", 2026-08-15), so the margin is now 6" rather than
    1'-6"; still a pass, and worth watching if the frost depth ever deepens.
  - `RETAINING_BLOCK_12` (2.5') passes; the interior basement cross walls now author
    `unbalanced_fill=ft(0)` because they have soil on neither side, so they are not screened.

  This is expected and is **not** being papered over with an invented rebar spec. A 9'
  basement wall in Minnesota is a reinforced wall — it always was — and the model simply had
  no field to say so until now. Resolution: author `FoundationWall.engineering_spec` with the
  structural engineer's vertical reinforcement schedule when it arrives, which flips these to
  PASS citing the spec. Until then the FAIL is the correct reading: the prescriptive path
  does not cover these walls.

## Remaining Work

**Deliberately not done, and why:**

- **The four exterior placeables keep their false room refs** (both wall hydrants, both
  porch curtain rods). Giving them an honest home means unconditioned `Room`s for the porch
  and the balcony — enclosing walls, envelope, energy and ventilation consequences — for
  four UNKNOWNs this file already accepts. Not worth the complexity.

- **The IRC reinforced-foundation tables were not encoded.** Tables R404.1.2(2)-(5) would
  turn the two foundation FAILs into a prescriptive rebar schedule, which is the right
  eventual answer, but no source consulted reproduced the table rows and a made-up
  reinforcement schedule is worse than an honest FAIL. The engineer's schedule still lands
  in `FoundationWall.engineering_spec`.

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
