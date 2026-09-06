# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **NEC 210.52 receptacle-distance checks measure to the whole vanity carcass, not the basin**
  (named in the check's docstring). The model carries no basin extent, so the distance is a
  lower bound on the real 210.52(D) distance — permissive rather than wrong. Tightening it
  means a `FixtureType.basin`. The (D)(2) cabinet-face branch reports UNKNOWN for the same
  kind of reason — it is bounded 12" below the countertop and `FixtureType.height` is the
  whole assembly, not the deck.

- **`Room.clear_face` is not the wall's finish face, and something should say so louder
  (2026-08-29).** It is inset from the wall AXIS by the room's lining, so on RM-M-BATH2's
  13 7/8" exterior wall it reports x=5/8" where the paint is at x=6 5/8". A 54" vanity was
  authored off the reported number during this pass and stood **six inches inside the
  studs** — and `haus check` reported 0 FAIL throughout, because nothing in the engine
  grades a *fixture* against a wall face the way
  `test_catlin_contract_m3.py::test_wall_mounted_devices_resolve_against_a_wall_face` grades
  a device. The floor-heat polygon beside it went into the wall the same way, and that has
  no face check either.
  - **DEFERRED — explicitly not in the 2026-09-06 TODO batch, in either form.** The fix that
    actually removes the trap is a second `ResolvedRoom` polygon that IS the finish face, so
    the honest number is available to author from. It is deferred because of its blast
    radius, which has now been measured **twice** — this inventory is recorded here so it is
    not rediscovered a third time:

    | Where | `clear_face` references |
    |---|---|
    | `packages/engine/src/` | **126**, across **51** modules |
    | `packages/engine/tests/` | 43 |
    | `houses/` | 93 |
    | `ui/src/` | 17 |
    | **total** | **279** |

    The 51 engine modules are not a tail — they are every layer at once: `resolve/`
    (`rooms`, `room_walls`, `room_floor`, `room_openings`, `ceilings`,
    `construction_ceiling`, `construction_rim`, `paneling`, `placeables`, `floor_heat`,
    `site_earth`, `model`), 20 check modules spanning code/MEP/building-science/advisory,
    the drawing emitters (`floorplan`, `plan_labels`, `section_annotate`,
    `foundation_schedule`, `detail_components/wall_base`), both exporters (glTF, IFC), four
    `server/` JSON modules, two `source/` macro modules, and five takeoffs. Because
    `clear_face` is what `room_floor.py` measures, the change moves **every room's area**
    and therefore every area-derived check in one commit.

    Two traps to carry forward: `resolve/floor_heat.py` falls back to `room.clear_face` when
    no zone is authored, so the fallback pushes the error into every unauthored mat; and
    nothing grades a *fixture* against a wall face the way
    `test_catlin_contract_m3.py::test_wall_mounted_devices_resolve_against_a_wall_face`
    grades a device, so the trap is silent at 0 FAIL. See
    `.claude/.../memory/clear-face-is-not-the-finish-face.md`.

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

- **Two porch/balcony span knife-edges, written down 2026-08-28.** Neither is a finding
  today and neither had been recorded anywhere before. `structural.deck_beam_span` looks IRC
  Table R507.5(1) up on the **joist** span the beam carries, and the table's rows are
  6/8/10/12/14/16/18', so the lookup steps down in cliffs rather than sliding — a small
  change in a joist span can fail four beams at once.
  - **Porch: 9" of joist-span headroom.** `FS-SG-PORCH`'s joists span 7.25', which reads the
    8' row → a 10.25' limit against the four porch beams' 10.00' span. At a joist span of
    8.01' the lookup drops to the 10' row (9.17') and **all four porch beams FAIL by 10"**.
    Deepening the porch, or moving the back-beam line north, is what would do it.
  The porch half above is unchanged and still live. Anything that changes a PORCH beam
  section has to be re-checked against it. Also in
  `houses/catlin/notes/beam_water_protection.md`.

- **Eight heat-pump stand legs on `SL-SG-HPPAD` are ungraded for bearing.** Neither
  `structural.deck_post_bearing` (scoped to posts on a `FloorSystem`) nor
  `landing_post_bearing` (scoped to resolver-generated stair landing posts) reaches a post
  standing on a slab — and their anchors, not their bearing, are what actually governs.

- PR-B-KITCHEN-DRAIN-RUN is right through the middle of the theater. It should likely run more west first, bypassing the theater/media room as much as possible.

- Let's add soffit lighting to the overhead garage door side of the garage, and then to both side walls of that. Likely an aluminum channel cleanly integrated with the soffit of the garage.

- Add some trim/baseboard to the design. Note we are generally going with trimless for now, in our design, clean lines, drywall more often, but we do maybe want a flush-with-drywall baseboard.

- Orientation tuned glass (particularly second story south facing windows)

- **DECIDED 2026-09-06 — the four porch beams stay 3-ply KDAT 2x12.** The eight ply seams
  are real, but the water argument that moved the balcony beams to glulam is **overstated
  here because the porch beams are fully covered**: butyl `butyl-tape-beam` on the framing
  top and a formed 5 1/2" aluminium `TR-SG-CAP-*` over it, so the seams never see rain.
  The glulam trade remains available at roughly the same money if the porch is ever
  reworked, but nothing is owed today. `notes/beam_water_protection.md` carries the same
  decision. **The 9" joist-span knife-edge above is unaffected and stays live** — any change
  to a PORCH beam section still has to be re-checked against it.

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

### Framing follow-ups from the 2026-08-25 corner audit

- **The 1/2" sheathing lap is undeclared.** `_clip_l_corner` (`resolve/topology.py:630-643`)
  mitres **all** layers on the angular bisector through the node; there is no per-layer logic
  and thickness is not an input, so the sheathing course mitres exactly like the studs
  behind it. Real sheathing laps: one wall's sheet runs long and the other's stops short by
  its thickness. Whichever wall loses the 1/2"x1/2" square starts its first sheet 1/2" late,
  so a 4' sheet breaks at 48.5" on a stud centred at 48" — 1/4" bearing, under APA's 1/2"
  minimum. `junction.framing_owner` **is** already available at `_clip_l_corner` time (a free
  input, zero plumbing) but the `PlanModel` is not, so an authored lap direction would need a
  field on `ResolvedJunction` populated in `_classify_tier`. `test_junction_solver.py:85`
  asserts no-gap/no-overlap but does **not** pin the 50/50 split, so a lap would still pass
  it. Sheathing takeoff area comes from the node axis (`takeoff/framing.py:265-272`), not the
  polygon, so the lapping wall's extra 1/2" per corner is never billed today — a second,
  pre-existing gap independent of the first. And nothing in the engine lays out sheathing
  sheets at all, so a "sheet break lands >=1/2" onto a stud" check has no home yet.

- **California corners as the next `corner_style` value.** `corner_stud_stations`
  (`resolve/framing/corners.py:125-143`) packs supplemental studs face-to-face with
  `orient=d` — the wall direction, same as the module studs. A California corner is one stud
  turned **flat** instead — `orient=normal(d)` — so it stands the same way a batten laid flat
  does, closing more of the corner cavity to a batt but landing a bay off the drywall
  screw-line. The extension is a third `Literal` value (`FramingSpec.corner_style` and
  `Wall.corner_style_start/end`) plus an orientation flag threaded through
  `corner_stud_stations`, not just a count change like 3-stud -> 4-stud was.

- **Plywood ordered by the sheet.** `takeoff/framing.py:117-141` bills every framing member
  by lineal foot, so a panel-profile member is billed as nested 8-ft sticks of
  `"NxN panel"` with a board-foot figure. There is no member-fed sheet-goods path
  (`sheet_goods_takeoff` at `takeoff/framing.py:253-310` reads **layers** only, never
  `model.all_members()`). Ordering plywood by the sheet — nesting panel-profile members onto
  4x8 stock the way `_bucket_cut_lengths` nests lumber onto stock lengths — is separate work.
  **Shrunk on 2026-08-26 by the catlin truss**, which is why this is worth less than it was:
  the corner box and the plywood tab both went with the Swinburne outrigger band, so the
  only panel members left on an exterior wall are the 176 window **bucks** (`6x0.375 panel`,
  560 LF ordered). The item stands, but it is now a ~$300 line, not a ~$1,200 one.

**Deliberately not done, and why:**

- **Deck post/footing and concrete-spec follow-ups still open**, each blocked on something
  specific:
    - **`SUNKEN_GARDEN_COLUMN_12` still reads the presumptive f'c**, alone now.
      `PIER_CONCRETE_12` was migrated 2026-09-03 and `notes/sunken_garden_piers.md` /
      `notes/breezeway_piers.md` re-oracled with it. The consequence is visible and ugly in
      the register: `PT-SG-FCOL` grades at 3,000 psi and `PT-SG-COL` at 5,000, so the front
      column reads *weaker* than the back one when both are poured from the same truck. It
      is left because attaching the mix re-oracles `notes/balcony_moment_columns.md`, which
      another session had open;
    - **the schema still cannot say three things ACI ties to the classes this house claims**:
      the water-soluble chloride-ion limit (C1 0.30% / C2 0.15% by mass of cement — the half
      of class C that actually protects the bar), the cementitious material TYPE the S rows
      require (and `exposure_s` is unset on every mix, deliberately, because no soil sulfate
      test has been run), and the SCM caps for an F3 mix exposed to deicing chemicals.
      `CATLIN_EXPOSED_MIX` sits exactly at the 25% fly-ash cap — correct, and by coincidence
      rather than by a rule. ASR/aggregate reactivity (ASTM C1778) is unaddressed; the 25%
      Class F fly ash is the standard mitigation, so the mix is probably right and nothing
      records or grades it;
    - **`ConcreteSpec` says nothing about chromate passivation.** ASTM A767 requires it
      *unless the purchaser waives it*, and a waived passivation is the hydrogen-evolution
      bond-loss case. Nothing in this house says "do not waive";
    - **curing, cold-weather placement and slab joint layout are modelled nowhere.** For a
      0.40 w/cm fly-ash mix in Minnesota those are the field items durability actually turns
      on (ACI 308, ACI 306), and they live only in `Assembly.source` prose;
    - **3" cover on those columns has NOT been re-run through `deck_post._pm_point`**, and
      it must be rather than asserted: `PT-SG-BR1/BR3/BF1/BF3` are the balcony's entire
      lateral system, so the bar circle shrinking 30% is a moment question. The fallback
      ladder is 2.5" cover, then #4 ties, then six bars, all inside the owner's 12" cap.
      There is also a real argument for NOT going to 3" here: ACI's 3" is for concrete cast
      against EARTH, and these are Sonotube-formed on plastic wheel spacers;
    - the **Galvashield XPX anodes** for the salt-splash sunken-garden walls are still
      undecided. `notes/balcony_moment_columns.md` declines them on the COLUMNS as a belt on
      braces over galvanized bar at 2" cover; the walls are a separate question;
    - the **beam-bearing audit** — `PIER_CONCRETE_12` and `SUNKEN_GARDEN_COLUMN_12` already
      specify a 1/2"-1" stainless standoff, a >=15 degree wash and EPDM/HDPE isolation, and
      the breezeway posts sit on `ABU66SS` standoff bases. What is unaudited is whether EVERY
      wood member bearing on concrete is covered, and `PT-SG-COL`'s grout island is a known
      outstanding follow-up.
- **The breezeway piers' axial state is INCOMPLETE, and the demand is not faked.**
  `_Pier.unmodelled_load` derives which beams bear on a pier with no plan area behind them —
  here `BM-BW-RW/RE`, the breezeway roof, which is neither a `Roof` nor a `FloorSystem` — and
  `deck_post._detailing_only` grades the six load-independent detailing states in full while
  OMITTING the §22.4.2 comparison. The note's §3 carries a bounding estimate (d/c ≈ 0.007
  even with 50 psf of snow on the roof), so nobody reads the INCOMPLETE as "the pier might be
  too small"; the register publishes no ratio, because a bound is not a design. **Closing it
  is upstream work**: give the roof a modelled area to divide, or have the engineer state the
  demand.

### Found in passing, 2026-08-30 (System 1's south branch)

- **Nothing validates that a duct actually connects to anything.** No check tests that a
  `DuctRun` endpoint reaches equipment or another run, and `Register.duct_ref` is an
  unvalidated string. The whole `DU-S-HP-SOUTH`/`DU-A-HP-STUDY` tree was joined to nothing
  for a fortnight and every check passed. The only duct-to-equipment geometry in the
  codebase, `resolve/mep_soffit.py::_pair_is_plumbed`, exists to *suppress* a clash — the
  same predicate run the other way round is the check that was missing.
- **The AH/ERV blower interlock has nowhere to live in the schema.** With the ERV running
  and the air handler off, 100 cfm enters a still return chamber and leaves through
  `REG-S-HP-RET` into `RM-S-STUDY2`, the only low-resistance path; distribution to the rest
  of the house needs the blower turning (continuously, or on ERV call). That is a controls
  fact, no `Equipment` field holds it, and it matters because
  `code.N1103_6_whole_house_ventilation` is already tight at 210 cfm provided / 203 required.
- **No `Equipment` field records a filter or an access panel anywhere in the model.**
  `REG-T-HP-RET` is a filter-back grille and the only serviceable face on System 1; the
  model knows it as a rectangle with a `RETURN_AIR` port.

### ERV residuals (2026-08-25)

- **The ERV's condensate shares FX-B-SAUNA-FD rather than tying into `PR-B-COND`.** The
  arithmetic is in `plan/mep_drainage.py`: the condensate main is at 85"-and-change where it
  passes x=13'-6", and the highest a 21.6" case can put its spigot under an 8'-0 15/16"
  basement ceiling is about 75". There is no gravity connection to be made. The alternative
  the plan floated — the mechanical-room sink — still has no drain, which is the open item
  below and the one that would actually fix this.
- **Radials cross one another in the FS-S-WEST field, ungraded.** Nothing in the engine
  grades duct-against-duct outside a modeled `Soffit`; an 11 7/8" bay with an 8 7/8" web
  opening has room for one 3" duct to pass under another, so it builds, but the model cannot
  say so. `mep.duct_soffit_occupancy` is the shape the joist-bay version would take.
- **`DU-M-ERV-R-PLANT` is the longest radial in the house at 55'-8"** — level-2 manifold at
  the north end, south through the `FS-S-WEST` trusses, then up inside `W-S-C1` to a high
  sidewall grille (it moved off the attic manifold and out of the guest studio 2026-08-29,
  and 9'-4" of that length is the rise). Its pressure drop wants checking before 75 mm is
  committed to; there is no airflow solver here and there will not be one. **Check it against
  0.4" w.g., not 0.2":** HVI certifies the B210E75RT at 206 cfm net supply at 0.4" (HVI ID
  2004940), and the 0.2"/210 cfm figure several comments quote is the model-name point off
  the manufacturer's fan curve, not the rating point. **The comments were corrected
  2026-09-01** at 9 sites; `ventilation_cfm=210` is deliberately still authored (moving it to
  206 takes N1103.6 from 210/203 to 206/203 and breaks `test_catlin_erv`), so the pressure-drop
  check itself is what is left here.

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
- `model/views.py::ConditionKey` (plus `Continuity`/`LayerJoin` alongside it) is schema-only,
  unreferenced until WP1.4 condition derivation lands (→ 11b §Transitions, decision #37) —
  keep it in place, don't flag it dead.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions:
- Do we want floor drains in kitchen/laundry room (deferred 2026-07-30: neither, for now)
- Rename all the wall assemblies to just their type (no need for "CATLIN" in them) and make sure they are in the library
- **The showers are still unclassified — one of four is answered (2026-09-02).**
    Same axis, same rules, same question to answer first: what is actually behind the tile.
    The sauna is the worked example of what answering it costs — a liner variant on the wall
    that turned out not to have one. `FX-M-BATH2-SH` now has a modelled surround:
    `WP-M-BATH2-SURR`, a marble-look cast panel on the pan's two closed sides, priced as an
    upgrade delta against the fixture row that already buys a kit surround. `FX-A-STUBATH-SH`
    and the two flanged inserts still have nothing, and the same logic points at giving
    `FX-A-STUBATH-SH` the same panel.
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
    **Confirmed again on RM-M-STUDY, 2026-08-29, and it bites hardest in a small room.**
    The study's published area is 19.3 sf on the axis box; measured off the four bounding
    walls' own resolved layer polygons it is a 48 5/8" x 45 5/8" clear box — **15.4 sf**, a
    fifth smaller — and off the wainscot faces the joiner actually scribes to, 14.4 sf.
    Retyping two of its walls to `INT_2X4_STAGGERED_DOUBLE_GWB` took another 1 5/8" off each
    axis and **`clear_face` did not move at all**, because `_lining_inset` is a constant.
    No check saw the room shrink. The call booth's bench and desk are therefore dimensioned
    off `out/model.json`'s wall layer polygons, the way the sauna benches are — nothing in
    `houses/catlin/plan/` should size millwork off `Room.clear_face`.
  - **A floor drain in RM-S-PLANT** (the room should be hoseable): implies a drain line, a
    trap primer — the trap *will* dry — and slope in `FS-SECOND`. See the Questions list.
- study on first floor location adjustments (deferred by decision 2026-08-02)
- Nest/loft design
- Window sealing detail (RM-S-PLANT's is drawn — TR-CATLIN-PLANT-OPENING, 2026-08-18 — and
  is the strictest case in the house; the rest of the envelope still rides
  TR-CATLIN-FRAMED-OPENING)
- Make sure all desired access panels are in (deferred pending more design items settling)
- **Floor truss GLB/IFC exports still keep the one-box representation**, even though the
  viewer draws chords + end blocks + diagonal webs (`ui/src/three/floorTruss.ts`). Only
  worth doing if it ever matters.
- **DONE 2026-09-06 — `FT-B-*` on `center_on="wall"`, with one residue left open.** The
  house's strip footings were eccentric under their walls the way the garage stem's were
  before 2026-08-15: a 20" strip on the raw y=0 node line under a `face("concrete-ext")`
  wall whose pour runs inboard of it. Measured before the change, an 8" segment had 10" of
  toe outside the pour and 2" inside, and on the 12" segments (`W-B-E1`/`E2`) the wall's
  inboard face stood **2" past the footing altogether** — the wall was not all on its own
  footing, at 0 FAIL. That is the defect this item was really about, and it is fixed: eight
  strips (N1-N4, W1/W2, E1/E2) now centre on the resolved section, and the three interior
  12" pours (CS2/CN/CN2) carry the flag and do not move.
  - **The residue is an ENGINE item, not a house one.** `band_axis` is handed every layer's
    polygon, so the 4" of exterior XPS pulls the datum 2 3/32" outboard of the pour's
    midline: the toes land at 8 3/32"/3 29/32" on an 8" wall and 6 3/32"/1 29/32" on a 12"
    one, not a symmetric 6"/6". Closing it means centring on the STRUCTURE layer, which no
    house edit can reach.
  - **Eight strips deliberately stay on the node line**, and the reasoning is worth keeping.
    The four garden-end strips are pinned at -4" by the closure joint against
    `FT-SG-W1/E1` — the old note's "keep that face where it is, or the beam's concrete meets
    the footing again" constraint, which still holds. With that face pinned and the width
    fixed at 20" the strip occupies -4"..+16" *whatever datum the offset is measured from*,
    so re-centring buys no geometry and only re-expresses the same number against a worse
    datum. Worse because their band centres disagree (+1 29/32" S1/S4, +1 3/4" S2, -1/32"
    S3) so one trim constant could no longer land three walls on one face — and S2's would
    move the next time someone changed the **sauna's shiplap liner thickness**, which is in
    its band. The four framed walls are excluded for the same class of reason: the node line
    already is the stud centre, and `W-B-CS`'s liner would pull its strip 1 7/16" off the
    studs it carries.
  - `_GARDEN_END_TOE_TRIM` therefore stays at 6". Concrete is unchanged (`haus takeoff`
    byte-identical, 0.00 cy delta — re-centring translates a strip without resizing it), and
    `haus check --only all` is byte-identical, `structural.frost_depth` and
    `structural.concrete_interference` included. The two section goldens that moved are pure
    coordinate translations of the footing/bedding/undercut, no annotation or layer change.
    `test_catlin_contract_m3.test_the_house_strip_footings_sit_under_the_walls_they_carry`
    now pins all 19 strips' toes.
* **Is this enough glazing for light-feeling rooms (along with LED strips, etc)?** Still
  open, and deliberately: 8% is the code minimum, not an answer about how a room feels. But
  the numbers are knowable, so here they are —
  `code.R303_1_light_and_ventilation` prints them for every habitable room, pass or fail:

  | room | glazing | floor | ratio | openable | ratio |
  |---|---:|---:|---:|---:|---:|
  | RM-S-PLANT | 26.7 sf | 159 sf | **16.8%** | 13.4 sf | 8.4% |
  | RM-S-STUDY2 | 26.7 sf | 159 sf | **16.8%** | 13.4 sf | 8.4% |
  | RM-M-BED | 33.5 sf | 231 sf | **14.5%** | 16.7 sf | 7.2% |
  | RM-S-BED3 | 14.2 sf | 129 sf | **11.0%** | 7.1 sf | 5.5% |
  | RM-A-STUDY | 15.0 sf | 159 sf | **9.4%** | 7.5 sf | 4.7% |
  | RM-S-SUITE | 13.5 sf | 154 sf | **8.8%** | 6.7 sf | 4.4% |
  | RM-S-BED1 | 10.0 sf | 120 sf | **8.3%** | 5.0 sf | 4.2% |
  | RM-S-BED2 | 10.0 sf | 124 sf | **8.1%** | 5.0 sf | 4.0% |
  | RM-M-LIVING | 49.3 sf | 766 sf | 6.4% | — | — |
  | RM-M-STUDY | 0.0 sf | 19 sf | 0% | — | — |
  | RM-B-GYM | 0.0 sf | 324 sf | 0% | — | — |
  | RM-B-PLAY-N | 0.0 sf | 324 sf | 0% | — | — |

  The top eight clear R303.1's 8% glazing and 4% openable outright, and two of them do it
  twice over. **The bottom four pass under R303.1 Exception 1** — artificial light plus
  mechanical ventilation — and they are where the question actually lives:
  - **RM-M-LIVING at 6.4%** is the one worth arguing about. It is a 766 sf open plan and it
    is 12 sf of glass short of the code line, which on a room that size is one more window.
  - **RM-S-BED2 at 8.1% and RM-S-BED1 at 8.3%** clear by 0.1 and 0.4 sf. That is not comfort,
    that is a rounding margin — and `houses/catlin/CLAUDE.md` already records that growing
    either room's clear face fails R303.1 again.
  - **RM-B-GYM and RM-B-PLAY-N have no glass at all** and are lit to 7.4 fc. They are
    basement rooms and always were; whether that is acceptable is a use question, not a
    daylight one.
  - **RM-M-STUDY's 19 sf** is a nook, not a room. Ignore the 0%.

 - Basement under the stairs storage closet

- **The R312.1.1 guard on the garage stair's 34" landing.** An owner decision with a cost
  and a look to it, flagged in `plan/storeys/garage.py`. It comes with an engine gap worth
  its own item: `code.R312_1_guard_height` censuses `FloorSystem`s and `code.R312_1_guard`
  censuses `FloorOpening`s, so `SL-G-STEP-0` — a `Slab` — is in neither census and its 34"
  drop is graded by nothing. A rule that walks slab edges would close it.
- **A guard opening at the END of a deck edge is invisible to `code.R312_1_guard_height`**
  (2026-09-03, same shape as the item above). `_railing_runs_edge`
  (`checks/code/mn_residential/fall_protection.py:353`) is a plain `LineString` distance test
  of the guard path against the WHOLE edge segment, so a guard that covers the segment's
  midpoint satisfies it however much of either end is missing. `RL-SG-PORCH`'s east leg was
  shortened 3'-0" on 2026-09-03 to open `ST-SG-PORCH`'s doorway and the check reports PASS
  either way — with the opening, without it, and with a 12'-0" opening it has never seen.
  The guard return at the opening is on the author (`PORCH_STAIR_THRESHOLD_RAILS` is that
  return, and `notes/porch_stair.md` says so). The fix is the same shape as the slab-edge
  rule: grade the guard's COVERAGE of each edge, not its distance from it. **Confirmed
  worse on 2026-09-04**: the flight moved to the middle of that leg, `RL-SG-PORCH` split into
  itself plus `RL-SG-PORCH-NE`, and the check still reports PASS — now with the two pieces
  straddling a hole it cannot see at all.
- **A stair whose head lands on a WALL TOP is graded against nothing that stands on that
  top** (2026-09-04). `ST-SG-PORCH` springs from `W-SG-E1`'s top and crosses 12" of it as a
  threshold. Drawn in the pocket's north strip, that threshold ran straight through
  `PT-SG-BR3` — a 12" ROUND column on a 12" wall, so it filled the top edge to edge and left
  10" of passage one side and 14" the other. **Zero findings.** Two things have to be true at
  once for a check to catch it and neither is: the threshold board is 3 sf of trim over
  concrete with nothing to frame, so it is deliberately not an element and there was nothing
  to overlap; and the flight itself starts at the wall's east face, x 28'-6", which is
  *exactly* the column's east face, so the two solids are tangent and
  `structural.member_interference` reports no interference because there is none. The stair
  moved to y -9'-0"..-6'-0" between the two columns instead. The rule that would close it:
  for any stair whose top landing is a wall top rather than a `FloorSystem`, project the
  landing's plan rectangle and grade the CLEAR WIDTH left by every solid standing on that
  wall, against R311.7.1's 36". It is the same missing idea as the two items above — the
  engine grades distances and overlaps, and what these three want is *coverage*.
- **`FT-SG-*`'s frost cover**, 12"-21" below the sunken garden's own floor against 42".
  `structural.frost_depth` routes all seven to UNKNOWN — a structure retaining the
  excavation it stands in is an engineered design under IRC R404.4, and
  `structural.foundation_unbalanced_fill` already sends the same walls to the same
  consultant. The permit checklist's "Foundation frost depth" item is UNKNOWN because of it,
  and `test_catlin_contract_m3.py` pins exactly that so nothing else can regress behind it.

- **Nothing in the engine enforces the basement door's 7" flood-step threshold** — it is
  currently 7 1/4" on `W-B-S2`/`W-B-S3`, but the curb height is a literal on two walls, and a
  check that walks the step would catch a future regression a literal can't.
- The french drains can likely be a type of form-a-drain product (a drain that doubles as footing form). We also can probably have fewer drains slightly.

## Found while doing the 2026-09-01 batch — recorded so they are not rediscovered

- **No check validates that every equipment port naming a service is reached by a run of that
  service.** `mep.duct_connectivity` grades duct ENDS against terminations (another duct,
  a machine footprint, a register, or a cap), so a manifold with nothing arriving at it has
  no end to orphan and is invisible to it — `EQ-B-ERV` once had no duct to either manifold and
  nothing reported it. The missing companion rule is not written.

  **The machine had to come down 18" before any of it could be drawn.**
  `EQ-T-BROAN-B210E75RT`'s four air ports are all 6" round on its TOP face. Hung at 6'-0" the
  21.6" case topped out at 7'-9 5/8" under a 8'-0 15/16" ceiling — 3 5/16" for four collars,
  which is not an installation, and is why nothing had ever been drawn to it. It hangs at
  4'-6" now (case top 6'-3 5/8"), which opens the 6'-10 7/16" crossing band the outdoor legs
  and the return trunk use: 1 5/8" under the 7'-6" radial layer, 6 13/16" over the case,
  6'-7 3/8" of headroom beneath. `PR-B-ERV-COND`'s inverts came down the same 18" at the same
  0.3"/ft.

- **`DU-ERV-RISER-EXH`'s top passes 2" from `DU-A-ERV-R-BATH1` at the same elevation.** The
  connectivity check reads that as its joint — correctly, by its own rule — but the riser is
  46" short of `EQ-A-ERV-MAN-EXH`, which is what it is described as reaching, and two ducts
  2" apart on centre at one elevation is an interference, not a tee. Worth a look; the same
  is true of `DU-S-ERV-HP-FEED` passing the same point.

- **`REG-S-HP-PLANT` was NOT moved east, and the reason is the short circuit.** Trimming
  `DU-S-HP-SOUTH` back to the plant room's door would save about 10'-4" of 10x6, but
  `REG-S-ERV-PLANT-EXH` is at (17'-7", 7'-4") and the supply at (6'-8", 3'-4") — an 11'-7 1/2"
  throw across an 18' x 9' room that `plan/mep_registers.py` argues for explicitly: the air
  lands on the south glass and crosses the planting before it is pulled out. Both terminals
  within a foot of the east wall leaves the west 14 feet of a 70%-RH room unswept, and that
  extract is its only moisture removal path. A middle station (x ~12'-6") would take about
  half the duct and keep a 5'-0" throw, if the saving is wanted.

- **No check is elevation-aware about a luminaire and the stair it lights.**
  `ED-S-STUDY2-STAIR-SC1` sat 2'-11 1/2" BELOW its own tread and 2'-0" under the stringer
  soffit, with its plan point inside the stair outline, and `haus check` was silent:
  `code.R303_7_stairway_illumination` counts luminaires serving the flight (nine for ST-S2A),
  `electrical.room_lighting` counts by room, and the fc advisory is planar. Nothing compares a
  wall-mount elevation against the stair. Worth a check.

## Found while doing the 2026-08-23 batch — recorded so they are not rediscovered

- **The published web app runs a GEOS a version behind the dev venv, and a geometry bug can
  therefore ship green.** `.venv` is Shapely 2.1.2 / GEOS **3.13.1**; the app runs the engine
  under Pyodide 0.26.2, which is Shapely 2.0.2 / GEOS **3.12.1**
  (`ui/src/engine/pyodide/worker.ts`). GEOS 3.13 hardened OverlayNG's noding, so 3.12 raised
  a **fatal** `TopologyException` unioning the basement wall bodies in
  `server/space_summary.gross_area_sf` — it killed the worker, so type-haus.com/app never
  rendered — on input rings that carry no defect of their own and that 3.13 absorbs
  silently. Fixed by routing that overlay through `resolve/overlay.py`'s fixed-precision
  (1 micron) helper; measured area-neutral to within a square millimetre per storey.
  **The class of bug is the item.** Either pin a Pyodide smoke test into CI
  (`.github/workflows/deploy-site.yml` already builds the site, and a headless
  `node` + `pyodide` run reproduces it in about 90 seconds) or bump Pyodide — 0.28.x ships a
  newer GEOS. Until one of those, `pytest` passing proves nothing about the published app's
  geometry.
- **There is no trap-primer element, field or `PipeAccessoryKind` member.** This is what
  blocks the `RM-S-PLANT` floor drain: `library/placeables/fixtures.py:108-110` says the
  existing `FX-FLOOR-DRAIN` type is for wet-room floors and *"a floor drain in a room that
  stays dry for months wants a primer line, which would be a different type."*
- **The HPWH has no combustion/air-volume provision.** An 80-gal Rheem ProTerra in a 160 sf
  mechanical room has a manufacturer air-volume requirement, and no `DuctRun`, `Register` or
  louvre is authored for it. Nothing in `haus check` grades it. The room got 7.7 sf smaller
  on 2026-08-23 when the ESS closet took its NE corner, which does not help.
- **The writeback cannot address a `FoundationWall` as `type: "Wall"`.** A PATCH with
  `{"type": "Wall", "tag": "W-B-STR3"}` comes back 422 *"no editable file hosts update Wall"*
  even though the wall is authored in an editable file. Pre-existing; it surfaced on
  2026-08-23 only because `model["walls"]` is uid-ordered and a new wall landed first in
  `test_server_loader_findings`. A UI drag of any foundation wall presumably fails the same
  way.
- **`W-B-CW3` and `W-B-STR2` are over-specified.** Both are `INT_ESS_CLOSET_STEEL` (steel
  studs, Type X both faces) because they used to bound the ESS closet in the SE corner. The
  closet left on 2026-08-23 and they were deliberately NOT re-specified: matching them to
  their neighbours would widen each by 2", move a room face an inch, and re-open
  `integrity.condition_coverage` on a line nothing else asked about. Worth revisiting the
  next time that wall line is opened for another reason; not worth opening it for.



- **Four matchers still answer "is this wall above that one", at three tolerances.**
  `platform._collinear_overlap` (tol = wall *thickness*, returns a bool),
  `stacking._axis_match` (tol = `inch(0.5)`, returns overlap length),
  `construction_geometry._stack_overlap` (returns the segment), and — since 2026-08-25 —
  `layout_lines._collinear`, which is `_axis_match`'s rule copied deliberately. Making
  `model.layout_lines` the source of truth for all four is the right end state and is
  **not** a mechanical swap: platform's thickness-scale tolerance is what covers the 8 of
  catlin's 15 second-storey walls that never authored `stacks_on`, and tightening it risks
  re-opening the bare-rim ring `test_platform_continuity` exists to catch. Migrate one
  consumer at a time, behind that test.
  **Narrowed, not fixed, on 2026-08-25:** `layout_lines._stacks` dropped its vertical-
  adjacency gate, so it and `stacking._axis_match` now ask the same *question*. What is
  still not shared is the geometry each is handed — `layout_lines` measures on the
  **datum face** (`Storey.vertical_datum`, so a width change stacks), `_axis_match` on the
  raw **node** axis. On concrete under wood those differ by 43.8 mm (basement) and 57.0 mm
  (garage), outside both `_TOL`s, so **13 stack pairs stack in one pass and not the other**:
  `W-B-S1`→`W-M-S1` and the eight garage `W-GF-*`→`W-G-*`. All 13 are pours under framed
  walls, which frame no studs, so nothing reads the difference today — which is exactly why
  it will be a surprise when something does.
- **`_append_track_jamb_legs` bottoms its track jambs on a plate that is no longer there.**
  `framing/openings.py` puts `trackjamb-0-l`/`-r` inside `D-G-OVERHEAD`'s rough opening,
  standing on the sole plate that 2026-08-30's `sole_plate_breaks` correctly removes. They were
  already wrong — they stop 22" above the slab — so this is not a regression, but it is now
  a member bearing on nothing at all. The garage contract test deliberately asserts nothing
  about them.
- **`IfcBuildingElementPart` bodies carry no voids** (`ifc/lowlevel.py:435-436`) while glTF
  cuts openings out of banded layers, so a banded band crossing a window is already
  inconsistent between the two exports. Cross-storey `LINE_BASE` bands make it likelier hit.
- **A `Slab` or `FloorSystem` rim has no cladding concept at all.** `SL-M-DECK`'s exposed
  perimeter edge takes no fascia, no edge trim and no drip: the machinery for that
  (`resolve/roof_edge.py`, `resolve/trim_bands.py`) is roof-only and has no analog for a
  horizontal element's edge. Noted 2026-08-24 while closing the *wall* side of the same gap:
  `resolve/platform.extend_walls_to_foundation` now runs a framed wall's skin down over the
  mudsill and rim to lap the foundation below, which covers the basement-to-main line — and
  does nothing whatever for a slab edge, which is a different element with a different
  detail. Scope it on its own.

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

**From the pattern-language review, 2026-08-29** (`plans/pattern_language_review.md` has the
number, the pattern and the reasoning against every one of these; the rows with a MEASURED
number are ready to move to `plans/cost-options.md` whenever the owner wants them):

Implement now:
Raise the electric fireplace to seated eye level, buy one that reads as fire at 11 feet, give it a dark surround, and turn the seats toward it (181/185). Likely a small section of oak, walnut, or cherry wainscot.

Deferred:
Two lounge chairs on the porch -- it is roofed, fanned, lit, wired and curtained, and has nothing on it (241).


## Takeoff and price-model gaps found by the 2026-08-30 allowance audit

All five were handled **price-side** in `houses/catlin/prices.toml` — the rate was corrected
for the true quantity and the row's comment says so. Each is really a takeoff-code fix, and a
takeoff change alters quantities for **every** house, so each deserves its own commit with its
own test rather than riding inside a documentation restructure.

- **No fabricated ROOF-truss profile exists.** `resolve/framing/profiles.py` has exactly one
  fabricated-member shape, `_RE_FLOOR_TRUSS` (`"<depth> floor truss"`). A trussed roof
  therefore resolves its chords as plain `2x4` sticks and bills at stick rates — which is why
  the 2026-08-29 trussed-cold-attic measurement had to be corrected by hand and made the
  framing swap look like a wash. `prices.toml` now carries a **dormant** `"36 roof truss"` row
  that starts working the day the profile lands.

Two pricing decisions that are correct today and become double bills the moment anything moves:

- **Rebar, ~5 tons, $10,000–18,000, is deliberately inside the `[concrete]` $/cy rates** and
  documented at both ends. It is the strongest "could be authored as real elements" candidate
  in the file. **If it is ever authored, cut the `[concrete]` rates the same day** — nothing
  enforces that, and nothing can.
- **`CATLIN_BASEMENT_12`'s all-in $/cy note says its rate absorbs damp-proofing** on the
  argument that damp-proofing is "not in the model at all". It is now: `damp-proof`
  (`library/assemblies.py:170`) bills in `[envelope_layers]` as `air-barrier`. Either the
  concrete rate should come down ~$7–18/LF or that note should be rewritten. Not touched in
  the 2026-08-30 pass because it is a rate re-derivation, not a defect fix.
