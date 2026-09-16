# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **NEC 210.52 receptacle checks measure to the vanity carcass, not the basin** (no `FixtureType.basin` field exists). Permissive rather than wrong. The (D)(2) cabinet-face branch reports UNKNOWN for the same reason.

- **`Room.clear_face` is not the wall's finish face** — it's inset from the wall AXIS by the
  room's lining, not the wall's own resolved layer polygons. A vanity authored off it stood
  6" inside the studs at 0 FAIL; nothing grades a *fixture* against a wall face the way
  `test_wall_mounted_devices_resolve_against_a_wall_face` grades a device. **DEFERRED** — the
  real fix is a second `ResolvedRoom` polygon that IS the finish face, but the blast radius is
  279 references across 51 engine modules + tests + houses + ui. Details:
  `clear-face-is-not-the-finish-face.md`.

- **2D-edit sync** — a PatchOp rewrites one constructor; derived data recomputes but authored
  cross-references don't. `retype_placeable` already re-anchors wall-fitted placeables and
  scans tag references. Still open (~3-4 days if approved): authored refs + advisory checks
  for geometry-coupled consumers, promote retype warnings to review findings, route opening
  retypes through a centre-holding macro. Re-affirmed deferred 2026-08-07.

## Remaining Work

- **`PT-BW-W`/`-GW` carry a beam end and a 6x6's `ABU66SS` base on the same 12" circle.** A
  real volumetric overlap, ungraded at 0 FAIL. Same x=6'-0" congestion as the open
  `W-BW-SCREEN` plate item below, and exactly the condition the dead pedestal existed for.
  That pedestal is gone (retired 2026-09-13, unreferenced), so a fix now has to author its
  own — which is the honest cost, since the dead one was a bare 12" concrete layer with no
  post or bearing geometry and would not have solved the overlap on its own.


- **1/2" sheathing lap is undeclared.** `_clip_l_corner` mitres all layers on the angular
  bisector with no per-layer thickness logic, so a 4' sheet can break at 48.5" on a stud
  centred at 48" — 1/4" bearing, under APA's 1/2" minimum. Fixing it needs a lap-direction
  field on `ResolvedJunction`; sheathing takeoff also bills from the node axis, not the
  polygon, so the lapping wall's extra 1/2"/corner is unbilled too (a second, independent
  gap). No sheet-layout engine exists to check a break landing on a stud at all.

- **Deck post/footing and concrete-spec follow-ups**, each blocked on something specific:
  - `SUNKEN_GARDEN_COLUMN_12` still reads the presumptive f'c (3,000 psi) vs
    `PIER_CONCRETE_12`'s migrated 5,000 — blocked on re-oracling `notes/balcony_moment_columns.md`.
  - Schema can't say the water-soluble chloride-ion limit, the class-S cementitious type, or
    SCM caps for F3+deicing exposure. ASR/aggregate reactivity (ASTM C1778) unaddressed.
  - `ConcreteSpec` says nothing about chromate passivation waivers (ASTM A767).
  - Curing, cold-weather placement, slab joint layout aren't modelled — only in prose.
  - 3" cover on the balcony's lateral-system columns needs re-running through
    `deck_post._pm_point` (a moment question), not just asserted. Also a real argument for
    staying at 2.5" — ACI's 3" earth-cast rule doesn't apply to Sonotube-formed columns.
  - Galvashield XPX anodes for the salt-splash sunken-garden walls: undecided (columns already
    declined them in favor of galvanized bar at 3" cover).

- **Breezeway piers' axial state is INCOMPLETE, demand not faked.** `BM-BW-RW/RE` bear on
  piers with no plan area behind them (the breezeway roof is neither a `Roof` nor a
  `FloorSystem`), so `deck_post._detailing_only` grades detailing in full but omits the
  §22.4.2 comparison. Bounding estimate is d/c ≈ 0.007 even at 50 psf snow. Closing it needs
  either a modelled roof area or an engineer-stated demand.

### From the 2026-09-10 `plans/notes.md` triage

- **No low-voltage security or sensing devices exist anywhere** (cameras, video doorbell,
  access control/readers, water-leak sensors, an outdoor weather station). Grepping every
  `ED-T-` declaration for `camera|doorbell|lock|access` returns nothing but one comment —
  `plan/electrical.py` says "future PoE cameras are just another entry here", which is the
  right shape but nobody made the entries. The structured-cabling half is finished and
  careful (`ED-T-NET-ENCLOSURE`, three `ED-T-AP-*`, `ED-T-DATA-JACK`, a star topology whose
  home runs `electrical.data_reachability` actually walks), so this is new device types plus
  placement plus a PoE budget re-check, on the pattern the access-point rollout already set.
  **Why it is worth doing before drywall and not after:** a camera or a reader that has no
  authored position has no authored cable path either, and the AP work already had to fix
  one device whose footprint collided with the studs it was supposed to sit between. Every
  one of these is a retrofit at full price once the board is up. -- DEFERRED

- **Basement equipment sits on the storey datum, and the flood note wanted it on a plinth.
  MAYBE — needs research first.** `EQ-B-WH` (Rheem ProTerra, `plan/mep_hvac.py`) is authored
  as `MountKind.FLOOR` with `elevation=None`, and floor-mounted equipment with no elevation
  bases on the storey datum. **The scope is smaller than it first looked:** the ESS is
  already off the floor — `EQ-B-ESS-BATT` is wall-mounted at 18" and `EQ-B-ESS-INV` at 4'-0"
  — so the water heater is the real case, with `EQ-B-SAUNA-HTR` the only other floor-based
  unit and a sauna stove wanting to be at floor level anyway. The sump half of flood
  protection IS done (`CKT-SUMP` on the backup panel, `ED-B-SUMP-RC`). **What to research
  before authoring anything:** (1) whether this basement has a flood exposure worth a plinth
  at all — it is a walk-out onto the sunken garden, which is itself a drained rain sump with
  a 7 1/4" threshold, so the honest answer may be that the risk is a burst pipe or a tank
  failure rather than groundwater, and a 4" housekeeping pad answers that; (2) whether a
  heat-pump water heater wants the pad for its condensate pan and service clearance
  regardless of flooding; (3) the cost, which is a few square feet of pad. **The trap if it
  is authored:**
  `EQ-B-WH.position` is quoted verbatim as a path endpoint by `PR-B-HW-TRUNK`, `PR-B-CW-WH`
  and `PR-B-HW-BATH1` and is the datum for `PR-B-WH-TPR` — four literals, one position, and
  `test_water_heater_connections.py` is what catches a move. Raising the tank means moving
  all four.

- **Drain-water heat recovery has no model presence. OPTIONAL, probably skipped, tracked so
  the decision is recorded rather than forgotten.** Grepping the house for `dwhr`,
  `drain water heat recovery`, `powerpipe` and `equidrain` returns nothing, while every other
  hot-water efficiency measure in the same block of the brainstorm has a counterpart. A DWHR
  coil is a vertical section of drain stack wrapped in copper that pre-heats incoming cold
  with outgoing shower warmth; it only works on a run where hot and cold flow at once, so it
  wants a **vertical** drain under a shower. **The reason this is probably a skip and not a
  buy:** the machinery already exists to carry it (it would be a `PipeAccessory`-shaped device
  on a DWV riser, exactly as `water_hammer_arrestor` and `backflow_preventer` are) — the
  question is whether any shower in this house drains through enough vertical stack to make
  a coil pay back, and the second-floor showers are the only candidates. Measure the
  available vertical before pricing anything.

### MEP / lighting residuals

- **`_ATTIC_BAY_Z` may repeat the 1 1/2" error level 2 already fixed.** `plan/mep_erv.py:949`
  sets the level-3 bay datum to `inch(-9.875)`, which puts the duct **invert** at the bottom
  of FS-ATTIC's bottom chord (228 1/8") rather than its centreline — the same mistake the
  level-2 note records having corrected on 2026-09-12, when `_BAY_Z` moved to `inch(-8.375)`.
  Found during the 2026-09-13 prose pass and deliberately not touched: it is a model change,
  not a comment. Check it against the level-2 derivation before moving it.
- **Two dead prose paragraphs in `plan/mep_erv.py`.** `DU-M-ERV-R-LAUNDRY` carries an older
  route paragraph ("on east to x=15'-0"") superseded by "ONE CORNER, NOT THREE" — the
  authored path turns at 14'-6". And `DU-M-ERV-R-STUDY`'s comment gives FS-S-WEST's joist
  lines as "8" + n*16"", which is the bay-CENTRE formula; the joists are at 16n.

- **The AH/ERV blower interlock is a controls fact with no model field.** With the ERV running
  and the air handler off, 100 cfm enters a still return chamber and exits through
  `REG-S-HP-RET` into `RM-S-STUDY2` — the only low-resistance path. Distribution to the rest of
  the house needs the blower on. `code.N1103_6_whole_house_ventilation` is already tight at
  210 cfm provided / 203 required.
- **No `Equipment` field records a filter or access panel anywhere.** `REG-T-HP-RET` is the
  only serviceable face on System 1; the model knows it only as a rectangle with a port.
- **ERV condensate shares `FX-B-SAUNA-FD`** rather than `PR-B-COND` — no gravity connection
  exists (main is at 85"+ where it crosses x=13'-6", best a 21.6" unit can manage under the
  basement ceiling is ~75"). The mechanical-room-sink alternative still has no drain.
- **Duct-against-duct crossings are ungraded outside a modelled `Soffit`.** Radials cross in
  the `FS-S-WEST` field; fits in an 11 7/8" bay with an 8 7/8" web opening but the model can't
  say so. `mep.duct_soffit_occupancy` is the shape a joist-bay version would take.
- ~~**`DU-ERV-RISER-EXH` passes 2" from `DU-A-ERV-R-BATH1`** ... 46" short of the manifold~~
  — **FIXED 2026-09-15.** Re-stationed 4 5/8" east and the feed drawn north to y=34'-6" then
  east into `EQ-A-ERV-MAN-EXH`. It cost 3.94 ft, three elbows and 0.056 in. w.g., which is the
  honest number that column never carried.
- **Nothing can grade a duct against a conduit, because a conduit has no elevation.**
  `ResolvedConduit` carries `z_start_m`/`z_end_m` and no per-vertex `z_m`, so the NW chase's
  nine conduits resolve as two-point schematics — `CD-B-ATTIC-RISER` "rises" 24 ft while
  travelling 5'-6" horizontally. **This, and not the radial plane, is what actually blocks
  `mep.duct_interference`**: a duct cannot be proven clear of something the model does not
  place in z. Per-vertex elevations on `ConduitRun` are the prerequisite.
- **`haus route --run` refuses every duct.** `cli/cmd_route.py`'s `_endpoints` indexes only
  `model.pipe_runs`, so `--run DU-ERV-OA` answers "not a run in this model" — and so does the
  `--run DU-M-ERV-R-KITCH` example the repo `CLAUDE.md` advertises. `routing/trades/duct.py`
  exists and is wired into `corridors.py`/`obstacles.py`; only the dispatch is missing.
- **37 MEP interpenetrations remain in the NW column** (x 0..7', y 32'..36'-6"), ducts and
  pipes only, measured 2026-09-15. The ERV's own twelve were cleared by moving both outdoor
  hoods to the north face; what is left is plumbing against plumbing and plumbing against the
  main-storey radial lanes — `PR-M-WC-VENT`'s westward leg at y=34'-6" crosses ten radials,
  and `PR-B-BATH-VENT`/`PR-B-SAUNA-VENT` share solid with `PR-B-KITCH-DRAIN`. None of it is
  the ERV's to fix and nothing grades any of it.
- **`EQ-M-ERV-MAN-SUP` and `EQ-M-ERV-MAN-EXH` still have no drawn feed.** Thirteen radials
  leave them and no trunk arrives; `mep.erv_manifold_ports` passes both because it counts
  ports, and only the two plenums with a drawn trunk report a "trunk collar". Until they are
  drawn there is also no tap elevation, which is why `notes/erv_static_budget.md` §9 had to
  withdraw its segmented-riser figure rather than restate it.
- **`FS-M-MECH` still carries the vents, the radon riser and nine conduits through its joist
  field undrawn.** `FO-M-ERV-OA` and `FO-M-ERV-EA` were added 2026-09-15 for the two ERV
  risers; the rest of the chase cluster has no floor opening, and nothing grades a duct or a
  pipe against a floor member.
- **`REG-S-HP-PLANT` throw is 11'-7" across an 18'x9' room** (deliberate — see
  `plan/mep_registers.py`), leaving the west 14' unswept by the room's only moisture-removal
  extract. A middle station (~x 12'-6") would halve the duct run if the saving is wanted.
### Structural/framing residuals

- **`FT-SG-*` frost cover (12"-21" vs 42" required) routes to UNKNOWN**, not FAIL —
  IRC R404.4 makes a retaining excavation an engineered design, same as
  `structural.foundation_unbalanced_fill`. Permit checklist's "Foundation frost depth" is
  UNKNOWN because of it; pinned by `test_catlin_contract_m3.py`.
- **French drains could be a form-a-drain product** (doubles as footing form); we probably also have more drains than needed.
- **Four matchers still separately answer "is this wall above that one"**, at three
  tolerances (`platform._collinear_overlap`, `stacking._axis_match`,
  `construction_geometry._stack_overlap`, `layout_lines._collinear`). Not a mechanical
  unification: `layout_lines` measures on the datum face, `_axis_match` on the raw node axis,
  and they differ by 43.8mm (basement) / 57.0mm (garage) — 13 stack pairs stack in one pass and
  not the other (`W-B-S1`->`W-M-S1` + 8 garage walls). All under-framed-wall pours, so nothing
  reads the difference today.
- **`_append_track_jamb_legs` bottoms garage door track jambs on a plate that's been removed**
  by `sole_plate_breaks` — pre-existing (stops 22" above slab), now a member bearing on
  nothing. Contract test deliberately asserts nothing about them.
- **`IfcBuildingElementPart` bodies carry no voids** while glTF cuts openings from banded
  layers — inconsistent between exports where a band crosses a window; more likely to hit on
  cross-storey `LINE_BASE` bands.
- **A `Slab`/`FloorSystem` rim has no cladding concept.** `SL-M-DECK`'s exposed edge takes no
  fascia/trim/drip — the roof-edge machinery (`resolve/roof_edge.py`, `resolve/trim_bands.py`)
  has no horizontal-element analog.

### Schema gaps found during selections/fireplace passes

- **A resilient channel is framed as a 2x6, in the shared library.** `INT_2X4_RC` and
  `INT_2X4_RC_DOUBLE_GWB` (`library/assemblies.py:317,343`) spell their furring
  `"25 ga. resilient channel"` — a real product no lumber pattern will ever match, so
  `cross_section` hands back the 1 1/2" x 5 1/2" fallback and **64 resolved strapping
  members** draw, plan-cut, clash-check and bill as a 2x6 instead of a 1/2" hat channel.
  `prices.toml` already prices 488 LF of it. Found by `integrity.member_profile_parses`
  (2026-09-13), which is the only reason it is visible; it reports UNKNOWN because the
  engine cannot say what section the string names. The fix is a real section for the
  product, not a parser branch — and it is a LIBRARY change, so it moves every house.

- **The fireplace elevation is checkable by no drawing.** The firebox, its lintel and the
  mantel are on the INTERIOR face of `W-M-E1`; `--view elevation` emits the four exterior
  faces, `--view section` cuts mid-house and misses y=8'-8", and `--view 3d` emits only a
  `.glb`. So the 2026-09-11 coursing drop was verified numerically off `out/model.json`
  (wall z-extents, the equipment's resolved z, the lintel's solid outline, the 20.4 SF brick
  row) and by eye by nobody. `haus check` grades none of it either — `mn_residential/profile.py`
  explicitly disclaims IRC R1001-R1004 — so an interior elevation or a section cut at the
  breast is the only thing that would ever show a mistake here.
- **There is no lintel element type, and a `Beam` standing in for one costs two things.**
  `BM-M-FIRE-LINTEL` (2026-09-11) is the fireplace's steel angle authored as a `Beam` because
  that is the closest honest schema — free-string `size`, two ends, a span — and it did not
  fight: the jamb piers' existing `open_end` nodes let it run the whole 45 1/2" panel with 8"
  of bearing each end, so no node had to be invented. The two costs:
  1. **`cross_section` parses `"WxD"` and only that.** `"3.5x3.5"` resolves; `"L3-1/2x3-1/2x1/4"`
     and `"3.5x3.5 STEEL"` both fall **silently** to the 1.5x5.5 fallback. So the size field
     holds the angle's BOUNDING BOX and the drawn solid is **7.3x** the steel (12.25 in²
  against the real section's 1.69 in²). The real piece is
     in `engineering_note` (a `Beam` has no `source` field) — where nothing reads it.
  2. **It bills $0.** A `Beam` reaches the estimate only through its `assembly`, as a
     `beam · <assembly>` **cubic-yard** row. Leaving `assembly` unset is deliberate — a $/cy
     rate is the wrong shape for a steel angle and inventing a steel assembly would file it
     in the concrete ladder — so the dollars are an `[allowances]` lump instead.
  Wants either a steel-section branch in `cross_section` plus a per-LF/per-EA beam price
  path, or a real `Lintel` / `MasonrySpec` opening. **The same trap is live for any steel
  member anywhere in the house**, not just this one.
- **Nothing grades a placeable against the wall it is mounted on.** `FURN-M-FIRE-MANTEL` was
  authored `inch(64.9375)` against a comment claiming `Mount.elevation` reads the SUBFLOOR
  datum. It reads the FINISHED floor (`resolve/placeables.py::_floor_elevation` returns
  `room_finished_floor_elevation` as `floor_m`; the structural plane is passed separately and
  only a CEILING mount reads it), so the hand-added 15/16" was applied twice and the shelf
  floated 15/16" clear of the brick it caps — **at 0 FAIL**. Fixed 2026-09-11. A placeable is
  graded against clearance zones, doors and protruding-object rules, never against its host
  surface, so the stale comment was the only thing that was ever wrong and the only thing
  that could have caught it. **The sweep is done and came back clean** — no remaining
  hand-added floor-finish offset anywhere in `houses/catlin/plan`. What survives is prose:
  the comments at `plan/millwork.py` and `plan/electrical.py` still describe the pre-fix
  mantel.
- **`light_run_materials` is an unread price table, and a `[placeables]` row for a
  `LuminaireType` on a `LightRun` matches nothing.** The table is keyed on `item`
  ("channel", "tape"), not on a type, so a per-each row bills $0 with no warning — found
  authoring the garage exterior linear on 2026-09-11, which is priced as a driven
  `[allowances]` row instead. The table itself stays unpriced house-wide, so `channel` and
  `tape` footage keeps appearing in the takeoff's `unpriced` list.
- **A `LightRun`'s load is invisible to the panel schedule.**
  `takeoff/electrical._connected_va` sums ElectricalDevices only and `connected_lighting_va`
  skips runs, so `CKT-LT-MAIN` reads 821 VA where the truth is 981 VA. Authoring `load_va`
  is NOT the fix — an authored value preempts the derivation outright and freezes the other
  38 fixtures against a hand-sum. Harmless today (54% of a 1,800 VA breaker, 68% of what an
  NEC 210.19(A)(1) continuous load may occupy) and wrong in principle.

- **Door hardware has no schema vocabulary** — `DoorType` has no lockset/hinge/lever/function/
  finish field; it's one `[allowances]` lump. Measured cost: the $84-306/ea allowance is right
  on average but short $100-200 on each privacy POCKET door (needs a mechanism + two pulls,
  not a plate). A `function` field (passage/privacy/entry/pocket-privacy) would let the
  allowance be driven per function.
- **Nothing re-checks a fixture against a code clearance once the fixture's size changes.**
  `RM-M-BATH2`'s 54" vanity was sized to IRC P2705.1's 21" (which MN deletes) instead of the
  enforced UPC 402.5's 24", clearing it by only 0.24" — then a real TOTO bowl (28.5-30" deep)
  put the cabinet inside the code envelope. That one is closed: the vanity is
  `FX-VANITY-48-SHALLOW` (48") and `test_catlin_bath2_vanity_heat_and_joists.py` measures
  against the 24" and says why. The general gap stays — worth a sweep for other dimensions
  justified against IRC's plumbing chapters instead of MN's amendments.
- **R502.10.1's single-member header allowance is sawn-lumber only, deliberately** — an
  I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  have, so catlin (all I-joist/floor-truss decks) sees no saving from it. **Still open:**
  nothing grades a single-member header against a span table at all —
  `structural.floor_opening_header` only reports past the prescriptive 8' ceiling.
- **A masonry wall opening (`W-M-FIRE`) is five stacked thin walls, not a schema feature.**
  Works (verified against `condensation._nearest_along_each_face`), but there's no
  continuity check across the five hand-worked elevation pairs — get one `top` wrong and the
  panel gets a horizontal slot in it at 0 FAIL. A `Wall.voids` field (or a `RoughOpening` host
  with no door/window) would say it in one element.
## Phase 2 — Complete Catlin junctions (deferred by decision 2026-08-02)

- Resolve mixed-assembly L corners and collinear assembly changes through named
  `AssemblyInterface` roles rather than layer-name or layer-index matching.
- Author concrete-to-framed basement returns, sauna-liner returns, foundation-foam returns,
  and porch/masonry returns as pre-resolve construction rules.
- Resolve the porch/basement five-way and other high-valence nodes with explicit bearing and
  layer-continuity ownership.
- Render transition/detail overlays from the resolved junctions. `Transition` stays
  post-resolve documentation.
- Add `Node.junction_override` only if the audit proves a rule cannot express a condition.
- `model/views.py::ConditionKey` (+ `Continuity`/`LayerJoin`) is schema-only until WP1.4
  condition derivation lands — keep it, don't flag it dead.

## Current Orientation

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Questions

- Floor drains in laundry room — deferred 2026-07-30: neither, for now.
- **Showers: one of four classified.** `FX-M-BATH2-SH` has a modelled surround
  (`WP-M-BATH2-SURR`); `FX-A-STUBATH-SH` and two flanged inserts still don't, and the same
  logic points at giving `FX-A-STUBATH-SH` the same panel.
- **`FX-S-BALC-HYD`'s sleeve** — a freeze-proof wall hydrant through the plant room's liner
  into a -15°F wall needs a sealed, insulated sleeve detail (`SleevePenetration` doesn't cover
  this condition).
- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists. (desired but not as explicitly modeled)
- **`RM-S-PLANT`'s clear face doesn't know about its liner** — `_lining_inset` uses one uniform
  figure (0.635") rather than each wall's own resolved lining, so the room polygon doesn't move
  when a liner does. Confirmed worse on `RM-M-STUDY`: published 19.3 sf vs a measured 15.4 sf
  clear box (14.4 sf to the wainscot face) — retyping two walls thicker didn't move
  `clear_face` at all. Fixing it moves every room's area at once, so it's its own change; until
  then, don't size millwork off `Room.clear_face` — use `out/model.json`'s wall layer polygons.
- Make sure all desired access panels are in — deferred pending more design settling.
- looks like the garage got switched back to concrete footings. The plan was for compacted aggregate footings (which last I checked are allowed per code as footings)
- **`TR-SG-LEADER-SE`'s outlet needs a shoe.** Closing the apron's north notches on 2026-09-12 put `W-RG-EAST-BALCONY` under the leader, crest 6" below the outlet, so 200 sf of balcony discharge lands on the cap of a dry-stacked segmental wall unless the outlet turns south. A cast elbow and a 1'-0" shoe to y -11'-3" is the detail; `Downspout` is a vertical run with one outlet elevation, so the model cannot hold it and nothing in `haus check` grades a downspout against a landscape wall. It has to reach the drawings from `params/raised_garden.py`.
- Make sure the plant room can be hooked up to an automatic watering system in the future. No, the hydrant doesn't count as it is on the exterior side.
 - frost free wall hydrants fail to full render as penetrations through the exterior cladding, and may also be rendering slightly too low
- Double check the electric fireplace will mount into the brick. Brick likely needs a metal lintel to hold the brick part above the fireplace. Oksana also wants the fireplace lower (not eye level, but just a bit above floor level, like a traditional fireplace)
- Kitchen has lights stuck above cabinets. Might want to swap some cans for under counter lighting. **Still open, and the geometry under it moved 2026-09-11:** the uppers are 15" deep hung at 53", not 13" at 54", so their fronts are 2" further into the room and 1" lower than whatever this item was last looked at against. The five under-cabinet tape runs moved with them.
 - **The selection is a 60-mil self-adhered rubberised-asphalt sheet** (Bituthene 3000, or Polyguard 650 / MiraDRI 860 as equals) — subp. 2's item 5 and the strongest published numbers of the eight: 0.05 perm, 300% elongation, 200 ft head, crack-cycled 100x at -25 F. **Spec `Bituthene Low Temperature` + `Primer B2 LVC` if the pour lands below 40 F** — the standard grade needs 40 F and would otherwise gate the whole foundation on a warm week.
 - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row reads "GCP Bituthene 3000". `Material.product_ref` can only be set where the material is authored; the material has to live in `library/materials.py` because a LIBRARY assembly (`FOUNDATION_WALL_XPS4_OUTBOARD`) references it; and a library material may not name a house-owned `Product` tag — `Library.products` is populated from `plan/products.py` and every other house would resolve it to `None`. There is no override path: `PlanModel.material()` returns the FIRST match, so a house appending a duplicate tag is shadowed for geometry while WINNING in `product_labels`, which is worse than not doing it. The identity lives in the material's `source` and in the `prices.toml` selection note instead. Closing it properly means either a house-level material-override mechanism or moving the foundation tail out of the library.
 - **Still open, small:** `FS-SG-DECK`'s joists are one flat plane on the now-tilted beams, so the model's deck is the deck's SOUTH (low) edge and the real north edge stands up to 2.45" higher. Closing it means teaching `resolve/floors.py` to take each joist's z from its tilted bearings, which reaches `ResolvedFloor.deck_z0_m`/`deck_z1_m` and every room, energy, section and guard consumer that reads them. (make sure the D-S-DECK-E door is aligned with the real height closely enough for easy entrance)
 - **Disciplines toggles: three of the four complaints are closed, one is real.** Verified
   against a fresh build on 2026-09-13 — `footing_bedding` is `("drainage","earth")`, the six
   north-entry piers stamp `["concrete"]`, and every `TR-H-CORNER-*` is `wall_corner` ->
   `siding`. `TrimKind.BEAM_CAP` was the one genuine misfile and is fixed.
   **What is left is the multi-trade case.** A foundation wall's trade set is
   `("concrete","insulation")` — 2 walls exactly, plus 20 more on wider sets like
   `("concrete","siding","insulation","drywall")` — and `anyTradeVisible()` in
   `ui/src/model/tradeVisibility.ts` draws a solid when **any** trade in its set is visible,
   so turning Concrete off still leaves the wall on screen under Insulation and a foundation
   wall can never be isolated away. Closing it needs a primary-trade axis for VISIBILITY:
   `primaryTrade()` already exists (`tradeVisibility.ts:158`) but the three.js builders
   (`walls.ts:85`, `structure.ts:505`, `scene.ts:156`) use it only to pick which
   `tradeGroups` container an object files under. Recorded, not scheduled.
 - Model a rain garden to the west of the garage gathering water with drain tile from TR-G-LEADER-W and TR-RF-LEADER-W
 - **Soffits: three retired 2026-09-13, three stay.** `SF-B-HALL`, `SF-B-GYM` and
   `SF-S-SUITE` are gone; `RM-B-STAIR`, `RM-B-GYM` and `RM-S-SUITE` carry
   `Room.exposed_services` instead — a sentence the check quotes back in a PASS, so the
   decision is in the report rather than suppressed. `DU-S-HP-SUITE` is `DuctRouting.EXPOSED`
   with an authored centreline and `REG-S-HP-SUITE` sits in its underside at 8'-0 1/8".
   `prices.toml`'s aggregate soffit row re-derived: 196.5 SF / 5.06 cy over three boxes.
   `SF-S-DUCT` (a duct trunk) and `SF-S-HP1` (the air-handler enclosure) stay.
   **`SF-B-BATH` stays too, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided
   a bathroom ceiling should be open. That is a design question, not a cleanup.
 - **Rebar (~5 tons, $10,000-18,000) is deliberately inside the `[concrete]` $/cy rates.** If
  it's ever authored as real elements, cut the concrete rates the same day. We may want to model rebar so it is clearly shown as a model element (selectable separately from concrete in the 3d view)
 - Add trim/baseboard — we're generally trimless (clean lines, drywall), but maybe a flush-with-drywall baseboard.
- Orientation-tuned glass, particularly second-story south-facing windows.
- Make it easier to "hop" into a given room for 3d viewing and rotate in spot, perhaps with a "fish eye" lens view rendering
- Possibly in second floor study, a bookshelf continuing hallways to make an alcove under the stairs
- Consider making the dining room "candelier" a TV screen (direct-lit/FALD Mini-LED LCD, 65") screen, perhaps connected to an exterior webcam, set recessed in the ceiling a bit (still replaceable, likely with the joist space above open for more room for airflow).
 - **The published web app runs a GEOS version behind the dev venv, and a geometry bug can ship
  green.** `.venv` is GEOS 3.13.1; the Pyodide-based web app is GEOS 3.12.1, which previously
  raised a fatal `TopologyException` unioning basement wall bodies (fixed by routing through
  `resolve/overlay.py`'s fixed-precision helper). **The class of bug is still the open item**:
  pin a Pyodide smoke test into CI, or bump Pyodide to 0.28.x (newer GEOS). Until then,
  `pytest` passing proves nothing about the published app's geometry.
- **`source/macros_walls.py` still hardcodes `"Wall"` in its split/heal/draw ops** (`:74`,
  `:198-199`, `:272-273`), so those macros 422 on a foundation wall even though a plain
  PATCH now works. Residual of the 2026-09-13 writeback fix, which taught `model.json` to
  emit each wall's authored `kind` and the UI to send it back; the macros mint their own
  ops and never see it. The same `_wall_kind` answer applies — they need the tag's real
  class, not a constant.
- **`W-B-CW3`/`W-B-STR2` are over-specified** (steel-stud ESS-closet assembly, closet is gone)
  — deliberately not re-specified; would widen each 2" and re-open condition coverage on a
  line nothing else asked about. Revisit only if that wall line opens for another reason.
- Make sure the EV charger is a Leviton 1450r 50A EV Charging Receptacle
- **OPEN, and it is the root cause above: `_y_in_n` is datumed off the ABOVE-GRADE cladding
  face, and nothing at the porch deck's own elevation faces cladding.** Below z=0 the house's
  south face is `W-B-BRICK`, which stands **6.435" south of that line** (cladding −7.25",
  brick −13.685"). `house_ext_layers_in = 5.0` is itself stale against `_WALL_OUTBOARD_IN`'s
  7.25" — `houses/catlin/CLAUDE.md` lists it as a consumer that must move with it and it
  never did. Two things fall out:
  - **`code.R311_3_exterior_landing` now FAILs (ERROR) on `D-M-BALC`**, and it is an honest
    finding rather than a regression: the deck covers 78.5% of the 36" patch and the check
    wants 85%, which needs a north edge at −12.3425" — **inside the wythe**. There is no deck
    position that both clears the masonry and lands the door. The previous PASS was bought by
    burying the joists in brick. **This needs an owner decision, not a nudge**: the gap at the
    door is 7.435" of which 3 5/8" is brick top (at z=0, level with the threshold) and 4" is
    the veneer's open drainage cavity. A threshold saddle over it, dropping the brick's top
    course, or cantilevering the deck boards north on `FloorSystem.subfloor_outline` (the
    plank plane, z 0..+1", clears the brick top — the JOISTS are what could not) are the three
    options; each decides whether the cavity gets capped and whether the two separately
    founded structures touch. **Do not author the board oversail blind** — it lands flush on
    the brick at 0" clearance, trading a visible defect for an invisible one.
  - **The check cannot union two surfaces into one landing.** A landing built of a threshold
    plate plus a deck — which is what this door actually wants — fails
    `_landing_surfaces`/`_LANDING_COVERAGE` however it is built, because each surface is
    tested alone. Worth fixing in the check independently of the design decision.
- **Nothing in the engine can catch a framing member buried in a wall layer.** A cantilevered
  floor end is pure arithmetic on the authored value (`resolve/floor_ends.py`), and
  `structural.member_interference` builds candidates from members and `column`/`beam` solids
  only — wall layers and masonry wythes are not candidates. That is why 31 porch joists ran
  through a brick wythe at 0 FAIL for as long as they did, and nothing will catch the next
  one. Scope: framing-member vs. wall-structure-layer plan overlap.
- Almost every flat roof I have seen uses joists on hangers between beams. Yet our balcony here has joists above the beams (presumably held down by hurricane ties). If we put the joists lower onto the beams, we end up with the 6x6 posts being possibly too tall (over 10' it said earlier, but R507.4 says it's good up to 14').
- Figure out a space for a cat litter box.
- Have the UI resolve pages and reports under /app, so we can give a URL to them directly, type-haus.com/app/?= (for example)
- Part of the attic is open to the stairs below. It should say that in the printed plan.
- The printed plans draw the stair lines wrong (the 3d model seems more accurate)

# Project Management

**Built 2026-09-11** (decision #69, `docs/site-state-format.md`): visits, inspections,
readiness, milestones, handoff lists, and the `#/site/board` surface. `haus schedule` and
`haus inspections` are the phone-free version. What was on this list and is now done: the
inspection list and pass registration; tracking work to completion (the board replaces the
Kanban idea — a kanban column is a status somebody drags, and readiness is derived);
final costs (`haus takeoff --csv` / `costs import`, and a visit shows its holdback).

Still deferred, and each for its own reason:
* **Photos, and voice notes.** Deliberately cut from v1: the two needs this surface exists
  for are answered by derived checklists, and a photo is storage, sync and a privacy
  question before it is a feature. A visit's `note` carries text today.
* **Bids as a GC.** Bidders should see the material estimate for their own scope and not the
  costed total — that is an access-control model, not a page, and there is no auth here yet.
* **A calendar.** There is no calendar because there are no engine-computed dates; if one
  arrives it renders authored `scheduled` values and nothing more.
* **Show the backside of the house as the main bid image** (so the design reads cheaper).
* **Local-first sync** (drive, S3, or Cloudflare Workers) for anything the phone writes.

Firstly design a house (with permit checks, building science review, floorplan editing in the 2d UI, 3d review, cost reduction and BOM review).
Secondly gather bids, organize the timeline (inspection gates, etc), then track completed progress.
Thirdly use the house design as a reference (ie for agents understanding live data on home assistant in context), potentially with feedback loop of updating the design or later running a remodel
