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

- **Zoning height is now 2'-10" above average grade.** No `height_limit` exists on a jurisdiction profile, so this is a note, not a check.

- **Porch beam span is a 9" knife-edge.** `FS-SG-PORCH`'s 7.25' joist span reads IRC Table
  R507.5(1)'s 8' row (10.25' beam limit) against a 10.00' actual beam span. At 8.01' the
  lookup drops to the 10' row and **all four porch beams FAIL by 10"**. **DECIDED 2026-09-06:
  the four beams stay 3-ply KDAT 2x12** (not glulam) — the ply seams are covered by butyl tape
  + aluminum cap and never see rain. The span knife-edge itself is still live: re-check any
  PORCH beam-section change against it. (`notes/beam_water_protection.md`)

- ~~PR-B-KITCHEN-DRAIN-RUN cuts through the theater~~ — **DONE 2026-09-07.** It now drops
  through SL-M-DECK's cast cap only and runs west inside the EPS form at y=35'-0". Zero
  exposure in the theater and the gym.
- ~~PR-A-STUBATH-DRAIN-RUN runs through the SUITEBATH's door~~ — **DONE 2026-09-07.** The
  dog-leg is split into a drop and a horizontal; `mep.drain_offset_geometry` now grades the
  shape and `mep.fixture_drain_reach` grades the nine fixtures that named a run and never
  reached one.

### `mep.run_in_finished_volume`: 18 runs still hang in a finished room

The check landed 2026-09-07 (`checks/mep/routing_ceiling.py`). One family is fixed; three
are open and each needs an owner decision before it can be authored, because the fix is a
soffit, a reroute or a ceiling move and only the owner can say which.

- **RM-B-SAUNA, 6 runs.** Its lined ceiling resolves at -15 3/8", 2 7/8" lower than the rest
  of the storey, so everything crossing above it is inside it:
  `DU-B-ERV-R-SAUNA-SUP` 7.49 ft @ 5.6", `-EXH` 6.52 ft @ 5.6", `PR-B-COND` 4.80 ft @ 9.4",
  `PR-B-CW-SAUNA` 3.57 ft @ 42.9", `PR-B-HW-SAUNA` 3.54 ft @ 42.9",
  `PR-B-ERV-COND` 1.50 ft @ 50.5", `PR-B-SAUNA-VENT` 1.50 ft @ 9.6". One perimeter soffit
  would take most of them; the two 42.9" ones are risers standing in the room.
- **RM-B-BATH, 3 runs.** `PR-B-BATH-VENT` 3.33 ft @ 8.2", `PR-B-HW-BATH` 3.33 ft @ 3.8",
  `PR-B-LSINK-DRAIN` 1.47 ft @ 5.8". Small, and one bulkhead over the wet wall takes all
  three.
- **The theater/gym/stair residue, 4 runs.** `CD-B-KITCHEN` 13.32 ft @ 4.3" and
  `CD-B-DATA-MEDIA` 6.07 ft @ 4.3" in RM-B-PLAY-N (both would take the same EPS lane the
  kitchen drain now uses, but each would orphan a wall sleeve); `PR-M-COND-HEADS` 9.07 ft @
  8.0" and `PR-B-COND` 5.80 ft @ 10.7" in RM-B-GYM; `CD-B-GARAGE` 6.05 ft @ 36.1" hanging in
  RM-B-STAIR.
- **4 supply risers stand in a finished room.** `PR-B-CW-SUITE` and `PR-B-HW-SUITE` stop 30"
  above RM-S-SUITEBATH's floor, 47" and 51" from the fixtures they name;
  `PR-B-CW-BATH2` 3.03 ft in RM-M-BATH2; `PR-B-CW-SAUNA` 3.57 ft. None carries `wall_refs`.
  This is `mep.fixture_drain_reach`'s defect for supply, and the fix is the same shape:
  take the riser into the wet wall it is supposed to be in.

Also open, and cheap: the owner raised switching the basement-to-main deck from I-joists to
open-web trusses (as `params/second_deck.py` already does for the second floor's west half).
Every crossing above would become free rather than bored or soffited. Not costed.
- Add soffit lighting to the garage overhead-door side and both side walls (aluminum channel
  integrated with the soffit).
- Add trim/baseboard — we're generally trimless (clean lines, drywall), but maybe a flush-with-drywall baseboard.
- Orientation-tuned glass, particularly second-story south-facing windows.
- Make it easier to "hop" into a given room for 3d viewing and rotate in spot, perhaps with a "fish eye" lens view rendering


- **2D-edit sync** — a PatchOp rewrites one constructor; derived data recomputes but authored
  cross-references don't. `retype_placeable` already re-anchors wall-fitted placeables and
  scans tag references. Still open (~3-4 days if approved): authored refs + advisory checks
  for geometry-coupled consumers, promote retype warnings to review findings, route opening
  retypes through a centre-holding macro. Re-affirmed deferred 2026-08-07.

## Remaining Work

- **1/2" sheathing lap is undeclared.** `_clip_l_corner` mitres all layers on the angular
  bisector with no per-layer thickness logic, so a 4' sheet can break at 48.5" on a stud
  centred at 48" — 1/4" bearing, under APA's 1/2" minimum. Fixing it needs a lap-direction
  field on `ResolvedJunction`; sheathing takeoff also bills from the node axis, not the
  polygon, so the lapping wall's extra 1/2"/corner is unbilled too (a second, independent
  gap). No sheet-layout engine exists to check a break landing on a stud at all.

- **Plywood-by-the-sheet takeoff doesn't carry per-piece install labour.** $16-34/sheet hangs
  a sheet; it doesn't cover setting 156 buck frames square in their ROs or nailing 152
  bevelled stiffener plies. The retired lineal-foot rows were basised on real install labour
  ($401-802 for the bucks alone) that 13 sheets x $16-34 ($208-442) doesn't reach — so the
  ~$500-1,000 the construction total fell is understated labour, not real savings. Fix: add
  `"sheet_goods": "scope"` to `cli/prices.QUALIFIED_KEY_FIELD` plus `"struct-1-plywood:buck
  rip"` rows in `prices.toml`. Also a cost-code note: the buck move (2400/openings ->
  framing) shifts money between two `haus tasks` work packages.

**Deliberately not done, and why:**

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
    declined them in favor of galvanized bar at 2" cover).
  - Beam-bearing audit: is every wood member bearing on concrete covered by a standoff?
    `PT-SG-COL`'s grout island is a known outstanding case.

- **Breezeway piers' axial state is INCOMPLETE, demand not faked.** `BM-BW-RW/RE` bear on
  piers with no plan area behind them (the breezeway roof is neither a `Roof` nor a
  `FloorSystem`), so `deck_post._detailing_only` grades detailing in full but omits the
  §22.4.2 comparison. Bounding estimate is d/c ≈ 0.007 even at 50 psf snow. Closing it needs
  either a modelled roof area or an engineer-stated demand.

### MEP / lighting residuals

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
- **`DU-M-ERV-R-PLANT`'s pressure drop wants checking** before 75mm is committed — 55'-8"
  radial, longest in the house. Check against 0.4" w.g. (HVI-certified rating point for the
  B210E75RT), not 0.2" (that's the fan-curve model-name point, not the rating).
- **Level-2 ERV radials are not on the claimed 4" centres.** `DU-M-ERV-R-BED`/`R-KITCH` and
  `DU-M-ERV-R-LIVING`/`R-BATH1` overlap by 1"; `R-STUDY`/`R-LAUNDRY` share a bay centre
  outright (3" overlap over 48-70"). `mep.duct_joist_bay_occupancy` reports UNKNOWN (the
  12.5" clear bay does hold both) rather than FAIL. The drawing's prose claim is wrong; that's
  the part to fix.
- **`DU-ERV-RISER-EXH` passes 2" from `DU-A-ERV-R-BATH1`** at the same elevation but is 46"
  short of the manifold it's described as reaching — an interference, not a tee. Same issue on
  `DU-S-ERV-HP-FEED`.
- **`REG-S-HP-PLANT` throw is 11'-7" across an 18'x9' room** (deliberate — see
  `plan/mep_registers.py`), leaving the west 14' unswept by the room's only moisture-removal
  extract. A middle station (~x 12'-6") would halve the duct run if the saving is wanted.
- **Three ERV manifold/hood types are cast to the wrong service** (`EQ-T-ERV-MANIFOLD-6` on
  two extract manifolds, `EQ-T-ERV-HOOD-6` on an exhaust-fed hood) — `mep.equipment_port_service`
  reports 3 UNKNOWN rather than FAIL, since a FAIL would report the catalog's shape, not the
  building. Minting `*-EXH` sibling types fixes it, but they need `prices.toml` rows or they
  silently drop from the bill.
- **No check is elevation-aware about a luminaire and the stair it lights** —
  `ED-S-STUDY2-STAIR-SC1` sits 2'-11 1/2" below its own tread with its plan point inside the
  stair outline, and nothing compares a wall-mount elevation against a stair.
- **`resolve/mep_queries.py` is 509 lines**, just over the 500-line rule in `AGENTS.md`.
  Splitting it out of scope for now.

### Structural/framing residuals

- **`FT-SG-*` frost cover (12"-21" vs 42" required) routes to UNKNOWN**, not FAIL —
  IRC R404.4 makes a retaining excavation an engineered design, same as
  `structural.foundation_unbalanced_fill`. Permit checklist's "Foundation frost depth" is
  UNKNOWN because of it; pinned by `test_catlin_contract_m3.py`.
- **Basement flood-step threshold (7 1/4" on `W-B-S2`/`S3`) is a literal, not a check.** A
  check walking the step would catch a future regression.
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

- **A countertop is not an element** (`library/placeables/casework.py` docstring only). The
  2026-09-06 selections pass priced material + allowance but left geometry unaddressed: the
  ~63 SF is a hand figure in a `prices.toml` comment, doesn't move with the casework, and
  nothing grades a cantilevered stone top (no top exists to grade). A `Countertop` element
  hosted on `FurnitureType` (material_ref, thickness, overhang) would fix all three.
- **Door hardware has no schema vocabulary** — `DoorType` has no lockset/hinge/lever/function/
  finish field; it's one `[allowances]` lump. Measured cost: the $84-306/ea allowance is right
  on average but short $100-200 on each privacy POCKET door (needs a mechanism + two pulls,
  not a plate). A `function` field (passage/privacy/entry/pocket-privacy) would let the
  allowance be driven per function.
- **Nothing re-checks a fixture against a code clearance once the fixture's size changes.**
  `RM-M-BATH2`'s 54" vanity was sized to IRC P2705.1's 21" (which MN deletes) instead of the
  enforced UPC 402.5's 24", clearing it by only 0.24" — then a real TOTO bowl (28.5-30" deep)
  put the cabinet inside the code envelope. Vanity is 51" now, but
  `test_catlin_bath2_vanity_heat_and_joists.py` still asserts against 21" — worth a sweep for
  other dimensions justified against IRC's plumbing chapters instead of MN's amendments.
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
- **`Mount.elevation` resolves against the SUBFLOOR datum, not the finished floor.** On a
  storey with finish above that datum (e.g. RM-M-LIVING at +15/16"), any placeable authored at
  a plain AFF number is short by the finish thickness, with nothing warning. Bit the mantel
  once; applies to every placeable in the house.

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
- Rename wall assemblies to just their type (no "CATLIN" prefix needed) and get them into the
  library.
- **Showers: one of four classified.** `FX-M-BATH2-SH` has a modelled surround
  (`WP-M-BATH2-SURR`); `FX-A-STUBATH-SH` and two flanged inserts still don't, and the same
  logic points at giving `FX-A-STUBATH-SH` the same panel.
- **`FX-S-BALC-HYD`'s sleeve** — a freeze-proof wall hydrant through the plant room's liner
  into a -15°F wall needs a sealed, insulated sleeve detail (`SleevePenetration` doesn't cover
  this condition).
- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists.
- **The humidifier isn't modelled.** ERV loses ~16% of moisture per air change — 1.5-2 gal/day
  unrecovered at -15°F. Needs an `Equipment` with water supply + drain.
- **`RM-S-PLANT`'s clear face doesn't know about its liner** — `_lining_inset` uses one uniform
  figure (0.635") rather than each wall's own resolved lining, so the room polygon doesn't move
  when a liner does. Confirmed worse on `RM-M-STUDY`: published 19.3 sf vs a measured 15.4 sf
  clear box (14.4 sf to the wainscot face) — retyping two walls thicker didn't move
  `clear_face` at all. Fixing it moves every room's area at once, so it's its own change; until
  then, don't size millwork off `Room.clear_face` — use `out/model.json`'s wall layer polygons.
- **A floor drain in RM-S-PLANT** (room should be hoseable) implies a drain line, a trap
  primer, and slope in `FS-SECOND`.
- Study on first-floor location adjustments — deferred by decision 2026-08-02.
- Nest/loft design.
- Window sealing detail — RM-S-PLANT's is drawn (strictest case); rest of envelope rides
  `TR-CATLIN-FRAMED-OPENING`.
- Make sure all desired access panels are in — deferred pending more design settling.
- Floor truss GLB/IFC exports still show the one-box representation even though the viewer
  draws chords + webs — only worth doing if it ever matters.
- Basement under-stairs storage closet.
- **OPEN DECISION — R312.1.1 guard on the garage stair's 34" landing.** `SL-G-STEP-0` now
  FAILs `code.R312_1_guard_height` (~4 LF unguarded on the east/north sides over a 2.8' drop).
  Deliberately not authored around or suppressed — an owner cost/look decision.
  `test_cli_check_output.py::test_catlin_carries_no_failures`'s `accepted` allow-list is where
  to record "leave it" if that's the answer.

**Is this enough glazing for light-feeling rooms (along with LED strips, etc)?** 8% is the
code minimum, not an answer about feel. `code.R303_1_light_and_ventilation` prints per-room
numbers, pass or fail — refreshed 2026-09-06 to count the three exterior FRENCH60 doors as
glazed fenestration (33.3 sf apiece, previously counted by nothing):

| room | glazing | floor | ratio | openable | ratio |
|---|---:|---:|---:|---:|---:|
| RM-S-STUDY2 | 62.3 sf | 159 sf | **39.2%** | 31.2 sf | 19.6% |
| RM-S-PLANT | 36.7 sf | 159 sf | **23.1%** | 0.0 sf | 0.0% |
| RM-M-BED | 33.5 sf | 231 sf | **14.5%** | 16.7 sf | 7.3% |
| RM-M-LIVING | 81.7 sf | 748 sf | **10.9%** | 40.9 sf | 5.5% |
| RM-B-GYM | 33.3 sf | 324 sf | **10.3%** | 16.7 sf | 5.1% |
| RM-S-BED3 | 12.2 sf | 129 sf | **9.4%** | 6.1 sf | 4.7% |
| RM-S-SUITE | 13.5 sf | 154 sf | **8.7%** | 6.7 sf | 4.4% |
| RM-A-STUDY | 13.6 sf | 165 sf | **8.3%** | 6.8 sf | 4.1% |
| RM-S-BED1 | 9.0 sf | 120 sf | 7.5% | 4.5 sf | 3.8% |
| RM-S-BED2 | 9.0 sf | 124 sf | 7.2% | 4.5 sf | 3.6% |
| RM-A-STUDIO | 13.6 sf | 356 sf | 3.8% | 6.8 sf | 1.9% |
| RM-M-STUDY | 0.0 sf | 19 sf | 0% | 0.0 sf | 0% |
| RM-B-PLAY-N | 0.0 sf | 324 sf | 0% | 0.0 sf | 0% |

The top seven clear R303.1 outright. The bottom six pass under Exception 1 (artificial light +
mechanical ventilation) and are where the real question lives:
- **RM-S-PLANT** is short on OPENABLE only (every plant-room unit is fixed) — light isn't the
  problem.
- **RM-S-BED1/BED2** spend Exception 1 on daylight by ~1 sf each (the WT-2754->WT-2748 trade).
- **RM-A-STUDIO at 3.8%** on a 356 sf floor is the largest daylight gap left.
- **RM-B-PLAY-N has no glass** — a basement room, always was; whether that's acceptable is a
  use question. RM-B-GYM is no longer on this list (D-B-PATIO's French pair carries it).
- RM-M-STUDY (19 sf, a nook) and RM-M-LIVING (10.9%, D-M-BALC carries it) can be ignored.

Two glazing gaps still leave the French doors out entirely, both wanting product data:
- `checks/building_science/energy_load.py` gives a door a UA but no solar gain — `DoorType`
  has no `shgc` field, so ~100 sf of south/east glass contributes nothing to a cooling load
  that's 63% window solar.
- `checks/code/mn_energy.py` grades every `WindowType` against `window_u_max` and no
  `DoorType` at all — the three glazed exterior door types (U-0.20/0.25) would pass, but
  nothing checks it.

## Found while doing the 2026-08-23 batch

- **The published web app runs a GEOS version behind the dev venv, and a geometry bug can ship
  green.** `.venv` is GEOS 3.13.1; the Pyodide-based web app is GEOS 3.12.1, which previously
  raised a fatal `TopologyException` unioning basement wall bodies (fixed by routing through
  `resolve/overlay.py`'s fixed-precision helper). **The class of bug is still the open item**:
  pin a Pyodide smoke test into CI, or bump Pyodide to 0.28.x (newer GEOS). Until then,
  `pytest` passing proves nothing about the published app's geometry.
- **No trap-primer element/field/`PipeAccessoryKind` exists** — blocks the RM-S-PLANT floor
  drain (`library/placeables/fixtures.py:108-110`: existing drain type is for wet rooms only).
- **The HPWH (80-gal Rheem ProTerra) has no combustion/air-volume provision** — no `DuctRun`/
  `Register`/louvre authored, nothing in `haus check` grades it.
- **The writeback can't address a `FoundationWall` as `type: "Wall"`** — a PATCH comes back
  422 even though the wall is authored in an editable file. A UI drag of a foundation wall
  presumably fails the same way.
- **`W-B-CW3`/`W-B-STR2` are over-specified** (steel-stud ESS-closet assembly, closet is gone)
  — deliberately not re-specified; would widen each 2" and re-open condition coverage on a
  line nothing else asked about. Revisit only if that wall line opens for another reason.

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
number, the pattern and the reasoning against every one of these; rows with a MEASURED number
are ready to move to `plans/cost-options.md` whenever the owner wants them):

**Open, owner calls:** retire `FURN-M-MEDIA` outright (98" screen is in the basement, console
duplicates seven BESTA units of storage). The electric fireplace re-lay is done
(2026-09-06 — Amantii BI-30-XTRASLIM, white facebrick surround, see `notes/east_breast_bearing.md`);
still need from Amantii in writing before framing: mantel projection, clearances,
junction-block serviceability, manual revision — tracked on `EQ-T-FIREPLACE-EL` in
`houses/catlin/plan/electrical.py`.

## Takeoff and price-model gaps found by the 2026-08-30 allowance audit

All five were handled **price-side** in `houses/catlin/prices.toml` (rate corrected for the
true quantity, comment says so). Each is really a takeoff-code fix and a takeoff change alters
quantities for every house, so each deserves its own commit/test rather than riding in with
documentation.

- **No fabricated ROOF-truss profile exists** (`resolve/framing/profiles.py` has only
  `_RE_FLOOR_TRUSS`) — a trussed roof bills its chords as plain 2x4 stick rates.
  `prices.toml` carries a dormant `"36 roof truss"` row that activates once the profile lands.

Two pricing decisions correct today that become double bills the moment anything moves:

- **Rebar (~5 tons, $10,000-18,000) is deliberately inside the `[concrete]` $/cy rates.** If
  it's ever authored as real elements, cut the concrete rates the same day — nothing enforces
  that.
- **`BASEMENT_12`'s all-in rate absorbs damp-proofing** on the argument that damp-proofing
  wasn't modelled — it is now (`damp-proof` bills in `[envelope_layers]`). Either the concrete
  rate should come down ~$7-18/LF or the note should be rewritten.
