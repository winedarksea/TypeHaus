# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **The garage service-door landing wants a guard, and nothing was asking (2026-09-07).**
  `code.R312_1_guard_height` now walks slab edges, so `SL-G-STEP-0` — the 3'-0" landing at
  D-G-SERVICE, 34" above the garage slab — reports 2.4' of open east side and 1.5' of open
  north side over R312.1.1's 30" threshold. `plan/storeys/garage.py` flagged exactly this
  and called it the owner's. **DEFERRED 2026-09-07**: reworking the landing is the preferred
  answer and it is a known item; the FAIL stays visible rather than being allow-listed.

- **RM-B-BATH is BOXED OUT and the soffit datum was wrong under it (2026-09-07).**
  `SF-B-BATH` takes all three of that room's runs — `PR-B-LSINK-DRAIN`, `PR-B-BATH-VENT`,
  `PR-B-HW-BATH` — in one bulkhead over the north wall, face at 7'-4 7/16" clear. Authoring
  it exposed a real engine gap: `resolve/envelope.py` hung every soffit from
  `storey.default_ceiling_height`, and the basement declared a nominal 9'-0" against a real
  8'-0 15/16", so the box ran 11" up inside FS-M-WEST's joists (22 interference FAILs). A
  soffit now hangs from the DECK UNDERSIDE over its own outline, with the nominal kept only
  as the fallback where no deck is overhead, and `params/main_deck.BASEMENT_CEILING_HEIGHT`
  is what `plan/manifest.py` states — that field also places every ceiling-mounted placeable
  and light in the basement, so it was never cosmetic. One knock-on: SF-S-DUCT's face moved
  1/8" with the plane it dropped from and its duct read 0.1" proud, so its 7'-10" face is
  now PINNED with `underside_elevation` rather than derived with `drop`. Any soffit whose
  face is a stated design elevation should be authored the same way.

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

### `mep.run_in_finished_volume`: 11 runs still hang in a finished room

The check landed 2026-09-07 (`checks/mep/routing_ceiling.py`); catlin was 20 FAIL that day
and is 13 now (11 of these, plus the accepted RM-B-GYM outlet and the deferred garage
landing guard). **Three of the seven that closed were engine bugs the check itself carried,
not house edits**, and they are worth knowing about because each made the report LOOK
better than the house was:

- `_soffit_union` unioned every soffit in the house with no storey filter, so a basement
  bulkhead read as covering the rooms two floors above it. `SF-B-BATH` took 6.8 SF out of
  RM-S-SUITEBATH's ceiling the day it was authored. Keyed by storey now, like the
  `wall_cover` beside it — and fixing it ADDED two honest FAILs (`DU-B-ERV-R-GYM`,
  `PR-B-HW-KITCH`) and lengthened four more.
- `resolve/envelope.py` hung every soffit from `storey.default_ceiling_height` rather than
  the deck actually overhead; see the RM-B-BATH entry above.
- `emit/draw/plumbingplan.storey_above` picked the garage as the storey over the basement
  the moment the basement declared its true ceiling height, dropping eleven of the twelve
  deck sleeves off sheet P-101. It asks `ceiling_decks_over` now instead of comparing
  elevations.

- ~~**RM-B-SAUNA, 6 runs**~~ — **6 of 7 DONE 2026-09-07.** The measured fact that decided it:
  **the basement has no plenum anywhere.** Every ceiling on that storey is 5/8" of gypsum
  straight onto the joist soffit, the workshop included, so "reroute it through the
  workshop" had nowhere to route to. Owner call: drop the sauna instead. `RM-B-SAUNA`'s
  `ceiling_lining` grew an 11 1/4" framed service cavity OUTBOARD of the foil-polyiso —
  vapour control stays continuous on the hot side, services run outside it — putting the
  finished face at 6'-10 13/16", clear of R305.1.1's 6'-8" and a better sauna than 7'-10"
  was. That took the four ceiling crossings. `PR-B-CW-SAUNA`/`-HW-SAUNA` then jogged east
  and drop inside W-B-CS's stud cavity at x=18'-0", which is where the note under them
  always said the mixer was.
  **Still open: `PR-B-ERV-COND`, 1.50 ft @ 39.3".** Not a riser — the transit leg, crossing
  the sauna's north wall at 44" AFF for 22" on its way to the air gap over FX-B-SAUNA-FD.
  The drop itself is excused as a connection; this is the horizontal before it, and it
  cannot simply rise: the run starts at EQ-B-ERV's pan at 4'-6" and falls 0.3"/ft, so there
  is no elevation that clears an 82 13/16" ceiling. Answering it means moving the tie-in,
  not the pipe — see the `PR-B-COND` arithmetic in `plan/mep_drainage.py`.
- ~~**RM-B-BATH, 3 runs**~~ — **DONE 2026-09-07**, `SF-B-BATH`. See the entry above.
- **The theater/gym/stair residue, 6 runs**, and the numbers below are the honest ones now
  that the soffit-union bug is fixed. `CD-B-KITCHEN` 16.50 ft @ 4.3" and `CD-B-DATA-MEDIA`
  9.25 ft @ 4.3" in RM-B-PLAY-N (both would take the same EPS lane the kitchen drain now
  uses, but each would orphan a wall sleeve); `PR-M-COND-HEADS` 11.40 ft @ 8.0", `PR-B-COND`
  8.72 ft @ 10.7" and `DU-B-ERV-R-GYM` 0.72 ft @ 8.4" in RM-B-GYM; `PR-B-HW-KITCH` 3.33 ft
  @ 3.9" and `CD-B-GARAGE` 6.05 ft @ 36.1" hanging in RM-B-STAIR. SF-B-HALL already boxes
  the hall's share of the last two; what is left is what leaves the hall.
- **3 supply risers stand in a finished room** (`PR-B-CW-SAUNA` was the fourth and is done).
  `PR-B-CW-SUITE` and `PR-B-HW-SUITE` stop 30" above RM-S-SUITEBATH's floor, 47" and 51"
  from the fixtures they name and **9 7/16" from W-S-SBS**, the partition they belong in;
  `PR-B-CW-BATH2` 3.03 ft in RM-M-BATH2, **20 3/8" from W-M-W3**. This is
  `mep.fixture_drain_reach`'s defect for supply and the fix is the same shape the sauna pair
  just took: jog at ceiling level, drop inside the wet wall. The suite pair is a short move
  and looks routine; PR-B-CW-BATH2's 20" is far enough that it is a reroute, not a nudge.

~~Also open, and cheap: switch the basement-to-main deck from I-joists to open-web trusses,
and every crossing above becomes free.~~ **COSTED AND REJECTED 2026-09-07.** It was trialled
against the real model, not reasoned about: catlin goes **20 -> 27 FAIL**. Two families
break. `integrity.floor_end_bearing` throws three ERRORs — a 5 1/2" plate does not seat two
3" truss chords the way it seats two 2 1/2" I-joist flanges — and `structural.member_
interference` picks up four more, because `_TRANSITION_DOUBLE` is dimensioned off that same
2 1/2" flange. "Every crossing becomes free" was never measured; the bearing is what pays
for it.
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

### From the 2026-09-10 `plans/notes.md` triage

Eight sonnet agents read the 2,434-line brainstorm against the built house. Almost all of it
was already incorporated or decided against; four items survived, and one of those
(`CKT-SPD` plus the grounding-electrode note in `plan/electrical.py`) is **DONE** rather
than tracked here. These three are the rest.

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
  one of these is a retrofit at full price once the board is up.

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
- **mypy is no longer a gate anywhere (2026-09-09).** `mypy --strict packages/engine/src`
  reports 2781 errors in 333 files; relaxing implicit-optional, missing imports and
  `no-untyped-def`/`type-arg`/`misc` still leaves 1119 in 158. It was removed from
  `ci.yml` and `scripts/verify.sh` for 0.1.0, because a `set -e` script stopping at stage 4
  meant the builds, `haus check houses/catlin`, the full IFC build and the UI stages were
  never running. Roughly 2000 of the strict errors are mechanical (missing annotations, bare
  generics, `no_implicit_reexport` wanting `__all__` on hub modules, absent third-party
  stubs); about 450 — `arg-type`, `call-overload`, `union-attr`, `index` — want individual
  review and may be latent bugs. Work it module by module and restore both steps at zero.
- **`typehaus/library/hardware.py` is 1236 lines** and now counts against the engine's own
  file-size rule — the shared catalog moved inside the package for 0.1.0 (2026-09-09) so a
  wheel could not collide with the unrelated `library` project on PyPI. It is a flat catalog
  of connector records, so the split is by family (anchors, hangers, straps, ties) rather
  than by behaviour. Left alone deliberately: the move was already a 30-import-site change
  and a catalog reshuffle on top of it would have made the release diff unreviewable.

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
- Window sealing detail — RM-S-PLANT's is drawn (strictest case); rest of envelope rides `TR-CATLIN-FRAMED-OPENING`.
- Make sure all desired access panels are in — deferred pending more design settling.
- **OPEN DECISION — R312.1.1 guard on the garage stair's 34" landing.** `SL-G-STEP-0` now
  FAILs `code.R312_1_guard_height` (~4 LF unguarded on the east/north sides over a 2.8' drop).
  Deliberately not authored around or suppressed — an owner cost/look decision.
  `test_cli_check_output.py::test_catlin_carries_no_failures`'s `accepted` allow-list is where
  to record "leave it" if that's the answer.
- Do we need to cover the underside of ST-S2A in anyway, or is code fine with exposed wood here? If not we could frame it in as a small closet or as shelves

Both glazing gaps CLOSED 2026-09-11. `DoorType` carries `shgc`/`vt`;
`energy_load.py` accumulates a door solar term (and names an UNKNOWN for a glazed exterior
leaf that states no SHGC, exactly as a window does); `mn_energy.py` grades EXTERIOR door
types against `door_u_max`, which is the same N1102.1.2 fenestration column as
`window_u_max` because R202 makes a glazed door fenestration. The count in the old note was
wrong and is worth recording: there are **two** glazed exterior door types, `DT-EXT-FRENCH60`
(U-0.20) and `DT-EXT-SLIDE60` (U-0.25) — the third U-0.20 leaf, `DT-EXT-SWING36`, is exterior
but OPAQUE. Both glazed types now state SHGC 0.35 / VT 0.5 (the house glazing package), which
moved the block cooling load from 17,752 to 21,579 BTU/h (1.48 -> 1.80 tons).

One thing did NOT come for free, and the assumption that it would is worth killing:
`emit/draw/schedules/openings.py` prints only the U-factor column for a door
(`_energy_columns(spec, is_door=True)` returns a 1-tuple and the door header set stops at
"U-factor"), so A-601 still does not show the new SHGC/VT. Lighting it up means widening the
door table and re-blessing `test_energy_sheet.py`'s column-count assertion — a schedule-sheet
change, not an energy one, and deliberately left out of the 2026-09-11 batch.

## Found while doing the 2026-08-23 batch

- **The published web app runs a GEOS version behind the dev venv, and a geometry bug can ship
  green.** `.venv` is GEOS 3.13.1; the Pyodide-based web app is GEOS 3.12.1, which previously
  raised a fatal `TopologyException` unioning basement wall bodies (fixed by routing through
  `resolve/overlay.py`'s fixed-precision helper). **The class of bug is still the open item**:
  pin a Pyodide smoke test into CI, or bump Pyodide to 0.28.x (newer GEOS). Until then,
  `pytest` passing proves nothing about the published app's geometry.

- Remove any floor drain from the plant room (it's not likely to flood, smaller water spills are the more likely concern) and then add a mop sink basin with a cold water fill (no hot). It can likely reuse the hydrant's existing PR-M-CW-BALC-HYD-RUN. Or else perhaps https://www.ikea.com/us/en/p/sunnersta-kitchenette-40313363/
- Pocket door possibly for basement bathroom
- Optimize the sunken garden wall heights and corners for a single pour with basement (XPS in forms)
- Double check the electric fireplace will mount into the brick. Brick likely needs a metal lintel to hold the brick part above the fireplace. Oksana also wants the fireplace lower (not eye leve, but just a bit above floor level, like a traditional fireplace)
- Kitchen has lights stuck above cabinets. Might want to swap some cans for under counter lighting.
- Make sure the kitchen cabinets align with IKEA sizes (we plan to do mostly an IKEA kitchen). It looks like their MAXIMERA style drawers and make for tall pantry cabinets.

- **The writeback can't address a `FoundationWall` as `type: "Wall"`** — a PATCH comes back
  422 even though the wall is authored in an editable file. A UI drag of a foundation wall
  presumably fails the same way.
- **`W-B-CW3`/`W-B-STR2` are over-specified** (steel-stud ESS-closet assembly, closet is gone)
  — deliberately not re-specified; would widen each 2" and re-open condition coverage on a
  line nothing else asked about. Revisit only if that wall line opens for another reason.

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

Two pricing decisions correct today that become double bills the moment anything moves:

- **Rebar (~5 tons, $10,000-18,000) is deliberately inside the `[concrete]` $/cy rates.** If
  it's ever authored as real elements, cut the concrete rates the same day — nothing enforces
  that.
- **`BASEMENT_12`'s all-in rate absorbs damp-proofing** on the argument that damp-proofing
  wasn't modelled — it is now (`damp-proof` bills in `[envelope_layers]`). Either the concrete
  rate should come down ~$7-18/LF or the note should be rewritten.
