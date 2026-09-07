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
- PR-A-STUBATH-DRAIN-RUN runs right through the SUITEBATH's door

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

- **DONE 2026-09-06 — California corners ship as a third `corner_style`.** The literal is
  `"california"` (`CORNER_STYLE_CALIFORNIA`), not a count name: the style builds the SAME one
  supplemental stick `"3-stud"` does and differs only in that it is laid flat, so
  `"2-stud"` would collide and `"3-stud-flat"` would mislead. **Catlin is unchanged** —
  `FramingPreferences.corner` stays `"3-stud"` and all 38 resolved corner members are
  byte-identical, `orient` included. The capability shipped, not a house change.
  - `corner_stud_stations` now returns `tuple[CornerStud, ...]` — `station_m`,
    `along_axis_m` and `laid_flat` — because a flat stud occupies its **depth** (3 1/2")
    along the axis, not its thickness (1 1/2"). `stud_depth_m` RAISES when the style needs it
    and it is absent; a silent fall back to the thickness would place the backer 1" out and
    nothing downstream would notice.
  - The non-obvious part was not the orientation but `_module_stations`' pack limit, which
    kept one *thickness* off the pack. That reads as face-to-face only while every stud is
    1 1/2" wide, so the first module stud would have cut 1" into the flat backer's face. It
    is `corner_pack_limit(...)` now. The midpoint guard also moved from grading the stud's
    centre to its inboard face, which is stricter for `3-stud`/`4-stud` too and bites nowhere
    in catlin.
  - `structural.corner_style_matches_preference` knows the style
    (`_CORNER_STYLE_STUD_COUNT["california"] = 1`), so a house opting in gets a comparison
    rather than an UNKNOWN advisory.

- **DONE 2026-09-06 — plywood is ordered by the sheet** (`takeoff/sheet_rips.py`). Panel
  members never reached `sheet_goods_takeoff`, which reads layers only, so they fell through
  `framing_takeoff` and billed as nested 8-ft sticks with a meaningless board-foot figure:
  156 window bucks ordered as 496 lineal feet of a thing nobody sells.
  - **The model is rip-then-crosscut**, not 1-D nesting. Rip yield is
    `floor((48 + kerf) / (width + kerf))` and the kerf is only free when the width divides
    48 evenly — a 4" rip yields **11** strips per sheet, not the 12 that `48/4` promises,
    because twelve strips need eleven kerfs. Then first-fit-decreasing crosscuts per rip,
    and sheets are summed as fractions across rip widths *within* a row, because a framer
    really does rip a 6" and a 4" strip off one sheet.
  - **Two things worth not rediscovering.** The web stiffener is authored `4 x 1.4375`
    because one modelled member IS the pair straddling the I-joist web, and
    1.4375 = 2 x 23/32 — so 76 members are 152 pieces of real 23/32" rip, and ordering a
    1-7/16" sheet would be ordering a product that does not exist. And the routing predicate
    is the **material** (`SHEET_RIP_MATERIALS`), not the profile grammar, because coil trim,
    sprayed foam and treated furring all wear `panel` profiles and are genuinely bought by
    the foot. 12 such rows were deliberately left on the lineal ladder.
  - `0.625x0.625 panel` sheathing LEFT the "could not be priced" list — 96 LF that had been
    billing at $0.
  - **STILL OPEN, and it is the real remainder: the per-sheet rate does not carry per-piece
    install labour.** $16-34/sheet is what it costs to *hang* a sheet; setting 156 four-sided
    buck frames square in their ROs and nailing 152 bevelled stiffener plies is piecework.
    The retired rows were basised on exactly that ($0.90-1.80/LF x 445.6 LF is $401-802 for
    the bucks alone), and 13 sheets x $16-34 = $208-442 does not reach it. **So the ~$500-1,000
    the construction total fell is essentially all labour, and it is understated, not saved.**
    The material half carries across correctly ($297-462 of ply against the retired $233-357).
    The fix is one line — `"sheet_goods": "scope"` in `cli/prices.QUALIFIED_KEY_FIELD`, the
    pattern `[envelope_layers]` already uses for `thickness_in` — plus
    `"struct-1-plywood:buck rip"` rows in `prices.toml`. The numbers are written into both
    retired rows' comments so they cannot be lost.
  - Cost-code note: the buck **moves trade**, 2400 / 08 80 00 / openings to framing. A framer
    sets a buck before the foam and long before a window arrives, so that is the honest
    reading, but it moves money between two `haus tasks` work packages.

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
      `EXPOSED_MIX` sits exactly at the 25% fly-ash cap — correct, and by coincidence
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

- **DONE 2026-09-06 — `Register.duct_ref` is validated** (`integrity.register_duct_ref`,
  an arm on `checks/integrity/catalog_tags.py`). It reports a typo AND a `None`, which was
  invisible before because every consumer read the field defensively and a bad ref simply
  read as "run unserved". All 35 catlin runs reference correctly; `REG-M-XFER-MUD` is the one
  register with no `duct_ref` and it is a TRANSFER louver, skipped by design.
  The duct-to-duct joint predicate was also factored out of `_meets_another_duct` and
  `resolve/mep_soffit.py::_pair_is_plumbed` — which returned `False` unconditionally for a
  duct-to-duct pair — now uses it, so a real tee in a soffit stops reading as a hanger-gap
  conflict. `mep.duct_joist_bay_occupancy` is the joist-bay analog of the soffit rule, and it
  found something (below).
- **DONE 2026-09-06 (the schema half).** `Equipment` gained `behind_access_panel`,
  `access_panel_ref` and `blower_interlock_ref`; an `AirHandlingProductFacts` mixin
  (`filter_nominal_size`, `filter_merv`, `service_face`) went onto **both** `EquipmentType`
  and `RegisterType` — the latter because the only filter on System 1 sits behind a
  *register*, so the product facts had to be sayable of one. `REG-T-HP-RET` carries catlin's
  values. `PipeAccessoryKind.TRAP_PRIMER` exists now; the `RM-S-PLANT` floor drain and the
  "dry room needs a primer" rule are deliberately NOT authored in that pass. The controls
  fact below is what the interlock field now records:

- **The AH/ERV blower interlock (the fact itself, now recordable).** With the ERV running
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

  <!-- Refreshed 2026-09-06: the three exterior FRENCH60 doors (D-S-DECK-E, D-M-BALC,
       D-B-PATIO) are glazed fenestration and were counted by nothing — 33.3 sf apiece.
       See `resolve/room_openings.room_glazed_doors`. -->

  | room | glazing | floor | ratio | openable | ratio |
  |---|---:|---:|---:|---:|---:|
  | RM-S-STUDY2 | 62.3 sf | 159 sf | **39.2%** | 31.2 sf | 19.6% |
  | RM-S-PLANT | 36.7 sf | 159 sf | **23.1%** | 0.0 sf | 0.0% |
  | RM-M-BED | 33.5 sf | 231 sf | **14.5%** | 16.7 sf | 7.3% |
  | RM-M-LIVING | 81.7 sf | 748 sf | **10.9%** | 40.9 sf | 5.5% |
  | RM-B-GYM | 33.3 sf | 324 sf | **10.3%** | 16.7 sf | 5.1% |
  | RM-S-BED3 | 12.2 sf | 129 sf | **9.4%** | 6.1 sf | 4.7% |
  <!-- BED3 read 9.8 sf / 7.6% and leaned on R303.1 Exception 1 until 2026-09-06, when
       WIN-S-BED3-N (WT-1424 at x 34'-0", sill 4'-0") completed the north-east corner
       pair with WIN-S-BED3 on the east wall, over WIN-M-KITCH-N below. It clears 8%/4%
       outright now. (An earlier WT-1436 at x 23'-4" carried the same tag for a few hours
       the same day and was withdrawn — see plans/pattern_language_review.md.) -->
  | RM-S-SUITE | 13.5 sf | 154 sf | **8.7%** | 6.7 sf | 4.4% |
  | RM-A-STUDY | 13.6 sf | 165 sf | **8.3%** | 6.8 sf | 4.1% |
  | RM-S-BED1 | 9.0 sf | 120 sf | 7.5% | 4.5 sf | 3.8% |
  | RM-S-BED2 | 9.0 sf | 124 sf | 7.2% | 4.5 sf | 3.6% |
  | RM-A-STUDIO | 13.6 sf | 356 sf | 3.8% | 6.8 sf | 1.9% |
  | RM-M-STUDY | 0.0 sf | 19 sf | 0% | 0.0 sf | 0% |
  | RM-B-PLAY-N | 0.0 sf | 324 sf | 0% | 0.0 sf | 0% |

  The top seven clear R303.1's 8% glazing and 4% openable outright. **The bottom six pass
  under R303.1 Exception 1** — artificial light plus mechanical ventilation — and they are
  where the question actually lives:
  - **RM-S-PLANT is short on the OPENABLE half only** — 23.1% glazed and not one operable
    sash, because every plant-room unit is fixed. Light is not its problem.
  - **RM-S-BED2 at 7.2% and RM-S-BED1 at 7.5%** are the two bedrooms that spend Exception 1
    on daylight, by ~1 sf of glass each — the WT-2754 → WT-2748 retype's documented trade.
  - **RM-A-STUDIO at 3.8% on a 356 sf floor** is the largest daylight gap left in the house.
  - **RM-B-PLAY-N has no glass at all** and is lit to 7.4 fc. It is a basement room and
    always was; whether that is acceptable is a use question, not a daylight one. **Its
    neighbour RM-B-GYM is no longer on that list**: D-B-PATIO's French pair is 33.3 sf of
    glazing to the sunken garden and carries the room outright.
  - **RM-M-STUDY's 19 sf** is a nook, not a room. Ignore the 0%.
  - **RM-M-LIVING is off this list too**, at 10.9% — D-M-BALC is 33.3 sf of it. The "one
    more window" this entry used to ask for is not owed to the code; it is only a question
    about how the room feels.

  **Two glazing numbers still leave the French doors out, and both want product data the
  house has not stated:**
  - `checks/building_science/energy_load.py` gives a door a UA and **no solar gain** —
    `DoorType` has no `shgc` field, so ~100 sf of south and east glass contributes nothing
    to the cooling load, which is 63% window solar. Adding the field is easy; the number for
    `DT-EXT-FRENCH60` is a product decision, and inventing one would be worse than the gap.
  - `checks/code/mn_energy.py` grades every `WindowType` against `window_u_max` and **no
    `DoorType` at all**. The three glazed exterior types are authored at U-0.20 / U-0.25 and
    would pass; nothing checks that they do.

 - Basement under the stairs storage closet

- **DONE 2026-09-06 — the guard/coverage trio is closed by one shared helper.** All three
  items below wanted the same idea: the engine grades **distances and overlaps**, and what
  these needed was **coverage**. `checks/code/mn_residential/edge_coverage.py` now projects
  railing sub-segments, wall footprint spans, stair throat quads and glazing closures onto an
  arbitrary segment's own axis (the old helper only handled axis-aligned edges) and reports
  each uncovered run.
  - **`_railing_runs_edge` is deleted.** It was a bare `LineString.distance(seg) <= 0.20`
    boolean over the WHOLE segment, so a guard covering the midpoint satisfied it however
    much of either end was missing. `RL-SG-PORCH`'s 3'-0" east-leg opening now measures: the
    split guard covers 0'-5.2' and 8.2'-8.7', and the 3'-0" between is credited to
    `ST-SG-PORCH`'s stair throat — the same principle `code.R312_1_guard` has always used for
    a well. A test asserts the credit is EARNED by removing the throat and confirming the
    36.0" opening reappears. `PORCH_STAIR_THRESHOLD_RAILS` was already authored (2026-09-04),
    so no house edit was owed.
  - **The slab-edge census landed** on `code.R312_1_guard_height` rather than as a new id, so
    the permit checklist is untouched. **`SL-G-STEP-0` now FAILS** — see the open decision
    below.
  - **`code.R311_7_1_wall_top_landing` is new** and grades a stair whose head lands on a wall
    top: it projects the landing rectangle, subtracts every solid standing on that top, and
    grades the remainder against R311.7.1's 36". `ST-SG-PORCH` PASSES at 36.0" clear, and a
    unit test proves the abandoned north-strip drawing (the 12" round column) would have
    reported 18". It drives off the wall top, not off a landing element, because the
    threshold board is deliberately not an element.
  - **Four false positives had to be fixed in the new rule itself**, each a real gap: two
    floor systems of one storey abut across the wall between them so their deck outlines
    never touch (every main-floor seam read as a fall to grade — the drop is probed outboard
    now); attic gable edges run out under the eaves; a deck outline is the subfloor sheet and
    stands off the finished wall face (FS-SG-PORCH is 2 3/4" off W-M-S1, hence a 6"
    tolerance); and **the breezeway** — `FS-BW-FLOOR` is 35" over grade with no wall and no
    railing, but it is a glazed vestibule, so glazing solids are credited as closures. It
    FAILed without that and PASSes with it.
  - **Severity correction:** `code.R312_1_guard_height` was declared `blocking=False` on the
    permit checklist but raised ERROR — a contradiction invisible until it first fired, and
    one that would have closed catlin's permit gate. Its findings are advisory (WARN
    severity, FAIL result) now: still printed as FAIL, still exit 1 from `haus check`.

- **OPEN DECISION — the R312.1.1 guard on the garage stair's 34" landing.** Now that a rule
  walks slab edges, the engine asks the question `plan/storeys/garage.py:465-474` wrote down
  and declined to answer ("**Nothing in the engine will ask**" — it does now):
  ```
  FAIL code.R312_1_guard_height: SL-G-STEP-0: unguarded edge(s) over a 30" drop —
  (9.5', 41.3')...(9.5', 43.7') 2.4' of open side over a 2.8' drop;
  (9.5', 43.7')...(8.0', 43.7') 1.5' of open side over a 2.8' drop
  ```
  ~4 LF on the east and north sides. Still an owner decision with a cost and a look —
  deliberately NOT authored around and NOT suppressed. Until it is decided, catlin carries
  this FAIL, and `test_cli_check_output.py::test_catlin_carries_no_failures` names it. That
  test's `accepted` allow-list is exactly the place for an owner-decided advisory FAIL with a
  design-record citation, if the answer is "leave it".

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

## Found while doing the 2026-09-06 interior-selections batch — two schema gaps, deliberately not closed

- **A countertop is not an element, and cannot be measured.** `library/placeables/casework.py`
  is explicit about it — "Countertops are not separate elements... continuous 1-inch white
  countertop" — and until this pass that docstring line was the *entire* record of countertops
  in the repo: no material, no price row, unpriced scope. The selections pass closed the
  material half (`quartz-counter` / `oak-counter` in `plan/assemblies.py`, with real
  `product_ref`s — the first Materials in the repo to use that field) and the money half
  (`finish-countertops-quartz` and `finish-peninsula-oak-bar-top` in `[allowances]`), but the
  GEOMETRY half is a schema change and was left alone.

  What that costs, concretely: the countertop's ~63 SF is a hand figure in a `prices.toml`
  comment rather than a model quantity, so it does not move when the casework moves. It is
  also why the peninsula's overhang problem had to be caught by reading Caesarstone's rule
  against `CASE-PENINSULA-120`'s footprint by hand — **nothing in `haus check` grades a
  cantilevered stone top, because there is no top.** A `Countertop` element hosted on a
  `FurnitureType` with a `material_ref`, a thickness and an overhang would make all three of
  those measurable at once, and would let `advisory` grade the ⅓-of-depth rule.

- **Door hardware has no vocabulary in the schema at all.** `DoorType` carries no lockset,
  hinge, lever, function or finish field, and hardware is one `[allowances]` lump. This pass
  chose the products (Schlage Latitude on a square rose in 619, a Yale Assure Lock 2 on the
  one door that earns a smart lock, purpose-built pocket-door privacy latches) and recorded
  them as `Product` records plus prose plus a retuned allowance — deliberately NOT as new
  `DoorType` fields, because a schema change is not a selections pass.

  The gap has a specific cost and this pass measured it: **the $84–306/ea allowance is right
  on average and wrong in distribution.** It is generous on the thirteen swing doors and short
  by $100–200 on each privacy POCKET door, which needs a mechanism rather than a plate, plus
  two pulls (a flush pull on the face *and* an edge pull on the leading edge — once the door
  is three-quarters into the pocket the face pull is unreachable). A `function` field on
  `DoorType` — passage / privacy / entry / pocket-privacy — would let the allowance be driven
  per function instead of averaged, and it is the smallest change that fixes it.

- **Nothing grades a fixture against a code clearance it was authored to clear by a quarter
  inch, because nothing re-checks it when the fixture changes size.** `RM-M-BATH2`'s 54"
  vanity was sized to the water closet's **21" IRC P2705.1** front clearance — a code
  Minnesota deletes (`Minn. R. 1309.0010` subp. 3.D) — and cleared the envelope that is
  actually drawn and enforced, **UPC 402.5's 24"**, by 0.24". The check was correct all along;
  the fixture was an allowance. The moment it became a real product (every TOTO one-piece
  skirted bowl is 28½"–30" deep) the cabinet stood inside a code envelope. The vanity is 51"
  now, but **the test that guarded it was asserting the wrong number too** — see
  `test_catlin_bath2_vanity_heat_and_joists.py`, which still measures against the 21".
  Worth a sweep: any other place a dimension was justified against IRC's plumbing chapters.

## Found while doing the 2026-09-06 fireplace-surround batch

- **DONE — the engine implements IRC R502.10.1, and the interesting half is what it REFUSES
  to do.** `resolve/floors.py::opening_header_profile` asked `framing/tables.header_size` for
  a prescriptive answer and then threw it away except for the leading ply digit — and every
  table row to 8 ft starts with `"2-"` — so 36", 48" and 49" openings all emitted the same
  `2-1.75x11.875 LVL`. R502.10.1's real allowance (a header joist spanning 4 ft or less may be
  a single member the same size as the floor joist, with the trimmer doubling of R502.10.2
  starting only past that line) was implemented nowhere. It is now, together with a
  span-driven `_trimmer_plies` — and the constant it replaces also drives `trim_band`, so
  joist counts and positions move with it, which is the real blast radius.
  - **The allowance is restricted to SAWN-LUMBER decks, deliberately, and that was the
    decision to make rather than the cheap one.** R502.10 is a sawn-lumber table. On an
    I-joist or floor-truss deck "a single member the same size as the floor joist" means a
    single I-joist used as a header, hung on both faces and wanting web stiffeners and backer
    blocks — a manufacturer's table, not a code one, and this engine has none to grade it
    against. Emitting the light member with an advisory naming the gap would have put an
    ungraded member in the frame and a saving in the bill on the strength of a citation that
    does not cover it. `profiles.is_sawn_lumber` is the gate (and a nominal-looking size
    `LUMBER_ACTUAL` does not publish, like `"16x16"`, is deliberately NOT sawn lumber for this
    purpose — it already resolves to a guessed section).
  - **So catlin sees no saving at all**, every deck here being `11.875 I-joist` or
    `11.875 floor truss` — the honest outcome, and the reason no framing golden or takeoff row
    moved. `test_floor_opening_framing.py` pins both halves, including that catlin's trimmers
    are still doubled pairs.
  - **OPEN, and worth knowing before the next sawn-lumber floor is authored:** nothing yet
    grades a single-member header against a span table at all — `structural.floor_opening_header`
    only reports past the prescriptive 8 ft ceiling. The R502.10.1 path is a geometry change
    with no capacity check behind it.

- **DONE — a masonry wall can have a real opening, and the way is FIVE WALLS, not a schema
  change.** `W-M-FIRE` resolved to a plain 4-point rectangle, so the 3D showed a solid brick
  panel with the appliance box stuck on its face. There is no `voids` path on a `Wall` short
  of a `Window` or a `Door`, and both would be lies about a firebox. It is
  `W-M-FIRE-STUB/-PLINTH/-JAMB-S/-JAMB-N/-HEAD` now, stacked on one axis with **its own
  `open_end` node pair each**, and the 29 1/2" x 20 5/8" masonry opening is the gap between
  them. Five thin walls on one axis behave exactly as one did for
  `condensation._nearest_along_each_face` — re-verified rather than assumed, because dropping
  `W-M-E1` as RM-M-LIVING's east bounding wall is the failure this design was shaped around.
  - **STILL OPEN, and this is a workaround rather than a fix:** a `Wall.voids` field (or a
    `RoughOpening` that can host on a wall with no door or window in it) would say the same
    thing in one element. Five walls is buildable and readable, but the elevations are five
    hand-worked pairs of numbers and nothing grades their continuity — author one `top` wrong
    and the panel has a horizontal slot in it at 0 FAIL.

- **DONE — the mantel has geometry, and the general shape of the gap is worth keeping.** A
  `ResolvedShelfBank` carries width/depth/thickness/count and **no position**; no emitter
  reads `model.shelf_banks` and the only consumer in the engine is `takeoff/hardwood.py`. So
  `SB-M-FIRE-MANTEL` was a cut list with no body — invisible to the 3D, to the sections and to
  every interference and clearance check. Re-hosting it on a wall-mounted `Furniture`
  (`FURN-M-FIRE-MANTEL` / `FT-MANTEL-WALNUT-46`) is the house's existing idiom and fixes it
  without engine work, and it closes the accounting gap too: a wall-hosted bank has no priced
  host row, a placeable-hosted one does. **Any ShelfBank hosted on a Wall has both problems**,
  and there are none left in catlin.
  - **A trap found in the doing, and it is not fireplace-specific.** `Mount.elevation` is
    added to `resolve/room_floor.room_floor_elevation`, which returns the wall's
    `base_ref_z_m` — the SUBFLOOR datum. On a storey with a finished floor above that datum
    (RM-M-LIVING is +15/16") every "AFF" number authored on a placeable is short by the floor
    finish. Authoring the mantel at a plain 64" buried it 15/16" into `W-M-FIRE-HEAD` at
    0 FAIL. It is the same 15/16" that the wall `top` lost earlier the same day. **Nothing
    warns**, and every placeable in the house is authored against the same datum.

## Found while doing the 2026-09-06 TODO batch — by the new checks, on their first run

- **DONE 2026-09-06 — the `CATLIN_` prefix is gone from all 34 assemblies**, along with 126
  files of references and 54 golden filenames that embed an assembly name. Two names could
  not simply lose the prefix, because the stripped form already names a Slab ELEMENT in
  `params/sunken_garden.py`: `CATLIN_GARDEN_SLAB` is **`GARDEN_COURT_SLAB`** (its own source
  prose calls it the court floor) and `CATLIN_GARDEN_FIELD` is **`GARDEN_PUTTING_GREEN`**
  (it is a USGA putting-green profile). Leaving them bare would have put two identically
  named constants in one package.
  - **A purely mechanical rename would have shipped four silent regressions**, which is the
    reason to write this down rather than treat the next one as find-and-replace:
    1. **`condition_pattern` globs stop matching.** `"opening_perimeter:CATLIN_EXT_*"` and
       `"CATLIN_BASEMENT_*"` matched nothing afterwards and **every exterior opening lost
       its Transition binding**. `integrity.condition_coverage` caught it.
    2. **Then the widened glob over-matches.** A bare `BASEMENT_*` also swallows
       `BASEMENT_BRICK_VENEER`, whose perimeter `TR-CATLIN-VENEER-OPENING` deliberately
       SUPPRESSES (an open segmental arch has no perimeter work), and a detail sheet
       appeared for it. The pattern is **`BASEMENT_[0-9]*`** now — `matches()` is `fnmatch`,
       so the character class works — with a comment saying the `[0-9]` is load-bearing.
    3. **Condition keys pair assembly names ALPHABETICALLY.** `CATLIN_INT_2X6_BRG` sorted
       before `FOUNDATION_WALL_12_INT`; `INT_2X6_BRG` sorts after it. Three authored
       override keys, four test keys and 11 golden filenames were left naming a pair that no
       longer derives. The 4-way plant-room key needed its internal order fixed too.
    4. **Detail sheets are numbered in sorted order**, so **141 of the 258 changed golden
       lines are renumbering** (`A-522` -> `A-521`), not names. Callouts and the sheet index
       renumbered coherently and the whole detail suite passes — but the drawing set's
       numbers really did move, which matters to anyone holding a printed sheet.
  - Evidence nothing was gained or lost: the `assembly_change` condition set is **16 keys
    before and after**, the same 16 re-sorted; `haus check` is unchanged at 962 pass / 2 fail
    / 1016 rules; the takeoff prices everything with no "could not be priced" section.
  - **Nothing was promoted to `library/`.** `CONTRIBUTING.md`'s criterion 2 is "generally
    reusable", and these encode catlin's specific stack — `BASEMENT_8_GARDEN`'s protection
    band, `GARDEN_PUTTING_GREEN`'s 11.48" rootzone. Promotion is a per-assembly review with
    a card-render smoke test, not a side effect of a rename. Left open deliberately.


- **The level-2 ERV radials are NOT on 4" centres, and six pairs overlap.**
  `plan/mep_erv.py` says in prose that "the twelve lanes leave the closet on 4" centres". For
  two pairs it is **2"**, with 3" ducts: `DU-M-ERV-R-BED`/`R-KITCH` (lanes at x 3'-10" and
  3'-8") and `DU-M-ERV-R-LIVING`/`R-BATH1` (3'-2"/3'-0") overlap by 1", and
  `DU-M-ERV-R-STUDY`/`R-LAUNDRY` share the 20'-8" bay centre outright, overlapping 3" over
  48-70". `mep.duct_joist_bay_occupancy` reports one UNKNOWN on `FS-S-WEST` for it — UNKNOWN
  rather than FAIL because the 12.5" clear bay does hold both and this model gives a run one
  centreline per bay. The drawing says something that is not true; that is the part to fix.

- **Three stair luminaires sit below the nosing line they are supposed to light**, found by
  the new z window on `_lights_near` (which was plan-only — a 4 ft plan buffer with **no z
  filter at all**). None causes a FAIL, because another luminaire still lights each stair:
  - `ST-B2M`: `ED-B-CLOSET-LT` 32.4" below; `LR-B-STAIR-RAIL` **68.1"** below.
  - `ST-M2S`: `ED-M-PANTRY-LT` 41.1" below.
  `LR-B-STAIR-RAIL` is the interesting one: `plan/lighting.py:200-207` documents this exact
  limitation in prose — a `LightRun` carries ONE mount elevation, so the handrail tape lies
  flat at 34" while the flight climbs away — and ends "Nothing grades a light run's room, so
  no check says this." The engine says it now.
  - Two calibrations in that check are load-bearing and should not be "simplified" away: the
    synthetic **arrival** station is one riser above the top nosing and must be excluded
    (`include_arrival=False`) or a correct fixture reads 7.5" buried; and a **one-riser
    allowance** is required because `ED-M-STAIR-LT` is authored 8" under the wall top on
    purpose — `plan/` says "-0'-8" IS A STEP LIGHT, AND THAT IS THE POINT".

- **`resolve/mep_queries.py` is 509 lines**, just over the 500-line rule in `AGENTS.md`,
  after the joist-line extraction. Splitting it was out of that pass's scope.

- **The garage eave detail lost its heel.**
  `detail_wall_roof-GARAGE_ROOF-GARAGE_WALL_2X6` used to draw the bottom chord, the raked top
  chord and the 9 1/4" energy heel; with one member per truss it draws one 26" rectangle with
  two chord lines. That is the specified treatment for a fabricated shape
  (`section_members.py`), but the raised-heel eave is precisely the detail where the heel is
  the point. Closing it means teaching the section cutter to cut the **fink** rather than the
  member envelope. The golden was blessed rather than expand that pass's scope.

## Found while doing the 2026-09-01 batch — recorded so they are not rediscovered

- **DONE 2026-09-06 — `mep.equipment_port_service` is the missing companion rule.**
  `mep.duct_connectivity` grades duct ENDS against terminations, so a manifold with nothing
  arriving at it has no end to orphan and is invisible to it. The new rule grades **at the
  service level, not positionally** — catlin authors all four ERV ports at the same local
  `(0, 0, 21.6")`, so a positional match would be vacuous — via a new `Service` ->
  `DuctSystem` map (SUPPLY_AIR->SUPPLY, RETURN_AIR->RETURN, EXHAUST_AIR->EXHAUST,
  OUTDOOR_AIR->OUTDOOR_AIR). `_rotate_into_plan` was made public to do it. 7 PASS, 3 UNKNOWN.
  - **OPEN DECISION — the 3 UNKNOWNs are one reversible casting typed once.**
    `EQ-B-ERV-MAN-EXH` and `EQ-A-ERV-MAN-EXH` use `EQ-T-ERV-MANIFOLD-6`, which declares a
    SUPPLY_AIR trunk but is placed as an **extract** manifold; `EQ-S-ERV-HOOD-EA` uses
    `EQ-T-ERV-HOOD-6`, which declares OUTDOOR_AIR but is reached by the EXHAUST run
    `DU-ERV-EA`. Graded UNKNOWN rather than FAIL deliberately: a FAIL would report the
    catalog's shape, not the building. Minting `*-EXH` sibling types takes all three to PASS
    — but a minted type with no `prices.toml` row is **silently dropped from the bill**, so
    the rows have to land with it.

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
~~Raise the electric fireplace to seated eye level, buy one that reads as fire at 11 feet, give it a dark surround, and turn the seats toward it (181/185).~~ **DONE 2026-09-06.** The fire left the SE corner for the pier between `WIN-M-LIV-E1` and `WIN-M-LIV-E2`: a 45 1/2" white-facebrick surround (`W-M-FIRE`) centred on y=8'-8", starting on `W-B-E1`'s pour and rising through `FS-M-EAST`, stopping at a one-piece walnut mantel at 5'-4". Flame centre 42 3/16" — **a 14" rise** — against a seated eye of ~46-48". The unit is a real product now, an Amantii BI-30-XTRASLIM, chosen because it is the only *trimless* one in the whole 26-32"-wide, <=6"-deep, hardwireable field, so the brick runs to the glass edge. All eight BESTA units kept, re-laid three south and five north; sofa and two new armchairs turned onto it. **The surround is white, not dark** — the review asked for dark and the owner's call was full white facebrick, which is what a house of white standing seam wanted. Two things it does not fix: no evidence distinguishes any unit in this class at 11 ft (nobody publishes viewing-distance data, and neither Amantii glass is low-iron or anti-glare — the brick reveal and the mantel's shadow are what solve glare here), and turning the sofa east means it no longer addresses `FURN-M-MEDIA`. See `notes/east_breast_bearing.md`.

**Open, and deliberately left as owner calls:** retire `FURN-M-MEDIA` outright (the 98" screen is in the basement and the console duplicates seven BESTA units of storage); and get four things from Amantii in writing before framing (mantel projection, bottom/side/back clearances, junction-block serviceability, and which manual revision ships) — all four are listed on `EQ-T-FIREPLACE-EL` in `houses/catlin/plan/electrical.py`. (`ED-M-DINING-FH-STAT` was on this list and is **done** — moved to y=16'-0" on 2026-09-06, see Items to Fix below.)


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
- **`BASEMENT_12`'s all-in $/cy note says its rate absorbs damp-proofing** on the
  argument that damp-proofing is "not in the model at all". It is now: `damp-proof`
  (`library/assemblies.py:170`) bills in `[envelope_layers]` as `air-barrier`. Either the
  concrete rate should come down ~$7–18/LF or that note should be rewritten. Not touched in
  the 2026-08-30 pass because it is a rate re-derivation, not a defect fix.

## Items to Fix — CLOSED 2026-09-06

All seven are done. The house still reports the same **two** FAILs it reported before this
batch (`code.R312_1_guard_height` on SL-G-STEP-0 and `electrical.receptacle_spacing` in
RM-B-GYM), both pre-existing and neither in this list. **Three of the seven were not what the
write-up said they were**, and those corrections are the useful part of the record.

**1. A thermostat specified inside a window opening — MOVED.**
`ED-M-DINING-FH-STAT` went y=17'-9" → **16'-0"** (`plan/electrical.py`). It stood 2 1/2"
inside `WIN-M-EAST-MID`'s RO (y 210.5"..237.5") at 48", between that window's 32" sill and
80" head. The 37" pier between `WIN-M-LIV-E2` and `WIN-M-EAST-MID` is y 173.5"..210.5" and
16'-0" takes it dead centre: 16 1/2" of clear wall each side, 11" clear of
`ED-M-LIVING-RC3`, and 48" clears the BESTA run's 29 3/4" tops. Still true, and still worth
knowing: **no rule grades a wall device against an opening**, which is how this survived two
weeks of clean reports. `ED-M-LIVING-RC7` is the same defect on `W-M-C3` — y=21'-1 1/4", 16"
AFF, inside `D-M-STUDY`'s jamb pack (y 223.03"..256.97") — found while measuring the switch
move below and **left open**, because a receptacle is a spacing decision in the NEC 210.52
run and not a one-device fix.

**2. Recessed cans that cannot be recessed — HALF OF IT WAS WRONG DATA.**
The write-up said a 6" IC housing eats the roof's whole 6 7/8" batt zone and punches the
ccSPF air barrier. **The 6" was wrong.** Lotus's LL4SR sheet — the product this house has
named all along — reads **2" deep**, "Type IC Rated - No Housing Required", "Driver Inside
Connection Box", Air-Tight, Approved Location "Insulated Ceilings, Open Plenum, Wet". All
three CAN4 marks carried `height=inch(6)`, a generic can housing; corrected in
`plan/lighting_types.py`. At 2" a fitting sits inside the batt and never reaches the foam,
so the thirteen cathedral cans were never the code defect they were written up as. (`ED-T-LT-CAN3`
is left at 5" deliberately — that SKU was never confirmed against a datasheet, and guessing a
depth from a sibling is how the 6" got in.)

*The six under the concrete deck were real and are worse than described.* `SL-M-DECK` is
4 3/8" of cast cap over a 10" EPS stay-in-place form on **1/2" of steel furring**, under the
5/8" gypsum R316.4 requires as the thermal barrier over that foam. Nothing recesses there at
**any** depth, and the only way in is through the one layer that exists to stop a fire
reaching the foam.

- **RM-B-PLAY-N (the theatre):** the four cans are gone. Six `ED-T-LT-SCONCE-UD`, three a side
  on the side walls at the room's quarter points. **The count is arithmetic, not taste** —
  this windowless room is habitable only under R303.1 Exception 1, and `_room_lumens` counts
  POINT luminaires only, so the floor is 6 fc x 324 sf / (0.60 x 0.80) = 4,050 lm. Two
  sconces is 2.1 fc and FAILS; six is 4,200 lm / **6.2 fc**. That is 0.2 fc of margin and it
  is the whole margin.
- **RM-B-GYM:** `CAN3`/`CAN4` were only 6" inside the band, so the grid re-spaced to the
  room's thirds, y 4'-6"/13'-6" → **6'-0"/12'-0"**. All four now sit over wood joists. The
  gym passes R303.1 on glazing, so this cost nothing.
- **The attic (owner's call, beyond what the data required):** twelve of the thirteen cans
  became wall fittings on the centre line — the only full-height walls the storey has, both
  gables raking to a 1 1/2" plate. The real objection to a flat trim there is **aim**, not
  air: 26.6 deg off plumb in a 6:12 plane. `RM-A-STUDIO` is on Exception 1 too and needed
  4,457 lm; it has exactly one mountable wall, ~11 ft of it free of the bar, so the scheme is
  five sconces plus an 1,800 lm bar pendant over `APPL-A-STUDIO-FRIDGE` (new mark **M1**,
  `ED-T-LT-PENDANT-BAR`), landing at 5,900 lm / **8.0 fc** — up from 6,000 lm / 8.08 fc, and
  every uid in the file kept, which the file's own "nothing here may be deleted" rule
  required. `RM-A-STUBATH` gains an over-mirror `ED-T-LT-MIRROR` bar. **One can is kept:**
  `ED-A-STUBATH-CAN1`, over the shower pan, where a sconce is the wrong article and the
  26.6 deg tilt aims *into* the room. `ED-A-EAST-LT` also moved off a station it shared
  *exactly* with the old `ED-A-EAST-CAN3` — the loft has been lit and billed twice.
- **The cove was designed, then withdrawn, and the reason is the battery.** Two surface COB
  channels were the ambient tier; `CKT-LT-BACKUP` is the ALWAYS_ON tier on one 14.3 kWh
  battery, and a PSU sums at its supply's **rating**. A second 200 VA driver takes
  battery-only autonomy 41.3 h → 37.5 h and flips `cycle_48h.sustains_always_on` to False —
  the house's headline two-day answer, spent on decoration. The tier has ~52 VA of headroom
  and every honest version of the cove is over it (a 60 VA driver lands at 39.8 h; a 120 V
  integral-driver run bills its real 93 W and lands at 39.0 h). **If it is wanted it is a
  circuit decision:** its own non-backup breaker and its own switch.

**3. The kitchen's main light switch behind a cabinet — MOVED.**
`ED-M-KITCH-SW` went to `W-M-C3`'s east face at **y=21'-10 1/2"**. It sat 13 1/8" inside
`FURN-M-KIT-PANTRYC`, and **no station on W-M-C5 fixes it**: 87" of wall, 84 5/8" behind a
96" carcass or the fridge/freezer columns, 2 3/8" of corner stud pack left. The new station
is the 11" between `D-M-STUDY`'s jamb pack and `N-M-C2` — the wall you pass walking in
through the `BM-M-HALL` beam line, which is open y 21'-8"..25'-10" and is why the kitchen has
no door-side wall of its own. The extents quoted beside `ED-M-KITCH-SW-UC` were also 4"
stale and are re-measured.

**4. A GFCI device sealed behind a hardwired mirror — BOTH OF THEM MOVED.**
There were **two**, not one: `ED-S-BATH1-RC-MIRROR` and `ED-S-SUITEBATH-RC-MIRROR`, the
second authored from the first a day later. Each was a GFCI *device* on `CKT-RC-SECOND`,
which is deliberately not GFCI at the breaker, so its test/reset button was the entire
protective path — behind glass. **And deleting them was never available:**
`code.E3901_6_bathroom_receptacle` passes RM-S-BATH1 on that outlet and nothing else, so
removing it would have turned a silent defect into a FAIL. BATH1's moved y=31'-0" →
**32'-6 3/4"**, into the 7 1/2" between the mirror's north edge and `FURN-S-BATH1-SHELF`,
still hard against the lav carcass so 210.52(D) is untouched. SUITEBATH's moved x=13'-10" →
**12'-3 1/2"**, west of the glass and stacked over `ED-S-SUITEBATH-RC1`; east was the obvious
side and is inside the tub's own footprint.

**5. The double vanity has no receptacle — IT ALREADY DID.**
`ED-S-VANITY-RC1` exists at 44" and `code.E3901_6_bathroom_receptacle` **PASSES both bowls**
(8.9" and 33.2" against 36"). What was real was that **four separate comments still claimed
the engine had no E3901 rule at all** — `plan/fixtures.py`, two in `plan/electrical.py`,
one in `plan/circuits.py`. All four predate `checks/mep/electrical_receptacles.py` and are
retired. The one that survives, narrowed: 210.11(C)(3)'s *dedicated-circuit* half still has
no rule. **The 2.8" of margin on the far bowl is the thing to re-check if either cabinet
moves** — the 60" run is already at the code minimum for bowl spacing.

**6. The suite's tub-shower stands in two walls — CLOSED, AND THE GAP WAS NOT 10.4".**
`W-S-SBS` was retyped to a 4 3/4" `INT_2X4_PARTITION` on 2026-08-30 and both its faces moved
1", making the real gap **11.42"**. The same 1" shuffle left this **flanged** insert not
touching either wall it is flanged to: 1.05" off `W-S-C2C` to the east and 0.17" *through*
`W-S-SN3`'s finish face to the north — **all of it at 0 FAIL**, because no check tests a
flanged fixture against the faces it is flanged to. Re-seating it on those two planes
(+1.047", −0.173") leaves the south gap at exactly **11 1/4"**, and
`FURN-S-SUITEBATH-RETURN` — a 30" x 11 1/4" x 84" carcass, new type `FT-SUITEBATH-RETURN-3011`
with `SB-S-SUITEBATH` fitting it out — is that third return, its north panel carrying the
flange over a framed 2x4. The old note's "a shelf like FURN-S-BATH1-SHELF will not fit the
leftover" was measured against a 20"-deep box; 11 1/4" is an ordinary linen-tower depth.
Millwork as Furniture, not a wall, for the reason the hall bath already gives: a real return
has to tee into `W-S-C2C`, splitting a **bearing** wall at a new node and re-phasing its stud
grid.

**7. Two estimate defects — ONE OF THEM BLAMED THE WRONG STAIR.**
- **The bookcases were billing $0.** The price key was the library type `FURN-BOOKCASE-32`
  and the house moved to house-local `FT-BOOKCASE-32-90` on 2026-08-24. Key corrected and the
  band raised 25% with the height (6'-0" → 7'-6"): $100–625 each, $400–2,500 for the four.
  ** A price key is a type tag and nothing reconciles the two ** — a rename on the type side
  is a silent price deletion whose only symptom is a line in the "not priced" list.
- **`finish-transitions-and-stair-nosings` billed 143.4 LF, and the extra 12.0 was NOT the
  garage flight.** `ST-G-SERVICE` was already dropping out correctly — `[conditioned=True]`
  excludes it because RM-GARAGE is a real Room carrying `conditioned=False`. The 12.0 LF was
  **`ST-SG-PORCH`**, the exterior sunken-garden stair, added after the note was written and
  coincidentally the same length. It stands in no `Room`, and `_in_conditioned_space` reports
  a stair that lands in no room as **conditioned** — the safe default for a finish schedule
  and exactly wrong outdoors. A driver filter can only *include*, so `stair_finish` gained a
  **`has_nosing`** column off the stair's own authored `nosing_depth`, and the driver is now
  `[conditioned=True,has_nosing=True]`. Both zero-nosing stairs drop on the physical question
  the allowance actually asks. **131.4 LF**, with a test.

### Still open from this batch

- `ED-M-LIVING-RC7` sits inside `D-M-STUDY`'s jamb pack (item 1 above).
- The theatre cove, if wanted, needs its own non-backup breaker and switch (item 2 above).
- `ED-T-LT-CAN3`'s 5" depth is unconfirmed against a datasheet (item 2 above).
- Nothing grades a wall device against an opening, or a flanged fixture against the faces it
  is flanged to. Both cost this batch real defects at 0 FAIL.
