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

- **The SDPW's published spacing table is read but not GRADED, and the joist maker's side is
  not read at all.** `takeoff/partition_fasteners.py` bills 188 SDPW19600s at every interior
  partition top as a *schedule*: one per crossing, 24" o.c. under a parallel member, one
  blocked bay per module between them. Simpson publish a **Maximum SDPW Deflector Screw
  Spacing** table (8'/10' walls at 5 psf, C_D = 1.6) whose worst case for this part is
  **42"/36"**, and the schedule sits inside it — but that is an assertion in a comment, not a
  `PublishedSpan` a reviewer can re-read against the model. It should be one: it is a
  published manufacturer table, so a prescriptive read and not an engineered item (root
  `CLAUDE.md`). Not `engineered()` — this engine carries no interior-partition out-of-plane
  load to compare a capacity against, so neither half of a ratio exists.
  The other half is wholly unread: **every member these screws land in is an engineered
  product** — 11-7/8" TJI 230 rafters, I-joists, open-web floor trusses. ER-192 permits them
  at a flange ≥ 1-1/8", but the JOIST maker's own fastener rules govern as much as Simpson's
  and nobody has opened TJ-4000 or a truss fabricator's schedule on this joint. Source for
  both: IAPMO UES ER-192 Table 37 and C-F-2025TECHSUP pp. 100-101;
  `houses/catlin/notes/partition_top_deflection.md`.

- **The blocking an SDPW lands in, where a partition runs BETWEEN the framing above, is billed
  nowhere.** 80 of the 188 screws are that case. It is a required framing condition the model
  does not carry — `resolve/floor_blocking.py` blocks a bearing line *under* a wall, which is
  the mirror joint. The row's `basis` says so; the lumber still is not on anybody's order.

- **~220 sf of gypsum is still billed through the joist band** on every storey-line partition.
  `resolve/partition_top.py` deliberately moves only the FRAMING top: cutting the body at the
  joist soffit as well costs four FAILs (`code.R312_1_1_stair_open_side` on `ST-S2A`,
  `mep.wet_wall_occupancy` x3 on the basement and suite risers). Answering it means moving
  `W-S-SS2`'s guard coverage and re-authoring three riser extents — a design pass.

- **`structural.member_interference` cannot see a plate inside a rafter.**
  `checks/structural/interference.py` clears a plate-against-rafter contact unconditionally as
  a birdsmouth seat, which is right for a bearing wall and is why the attic partitions stood
  11-7/8" inside their rafters undetected for the life of the model. The clause's own comment
  already calls moving interference onto the IR "a separate and larger job".

- **A member-level short-framing finding.** `integrity.wall_shorter_than_plates` grades a
  WALL; the real defect it was masking in the attic is that the shortest stud on `W-A-STU-N`
  is **1-1/4"**. `resolve/framing/solver.py::short_post_findings` is the precedent for the
  shape. It will light up on walls the partition-top change never touched.

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
- ~~**`haus route --run` refuses every duct.**~~ **Done 2026-09-17.** `cli/route_support.py`'s
  `_endpoints` now branches over `model.ducts` and `model.conduits`; a duct keeps its own two
  ends and searches the full multi-level lattice, and a proposal prints
  `routing=`/`floor_ref=`/`soffit_ref=` read back out of the corridors the winning legs rode.
  `routing/trades/duct.crossing_admissible` imported a name that has never existed and raised
  on every call, so it was dead code with a note behind it; it is fixed and `test_routing_trades.py`
  calls it. `--run DU-M-ERV-R-KITCH` still refuses on catlin, but now for the true reason and
  with the tags: the ERV manifold packs ten ports 4" apart, so every lane out of one is inside
  a neighbour's envelope and 3 of 33,439 lattice nodes are reachable.
- ~~**Ports are position + service only; bay sharing is one centreline; no duct sizing rule.**~~
  **Done 2026-09-17 (roadmap Phase 3).** `ServicePort` now carries `direction`, a rectangular
  `width`/`depth` beside the round `connection_size`, and a `PortCertainty` whose default is
  APPROXIMATE — so the catlin ERV's four ports at one point read as what the datasheet gave (a
  face), and a DIMENSIONED port is graded where it is instead of dropping the whole house to a
  service-level verdict. `resolve/mep_ports.py` is the one placement of a declared port and the
  router reads it too, so a duct is re-routed to the same spigot `mep.equipment_port_service`
  grades it against. `resolve/mep_packing.py` replaces the two "sum every occupant's width"
  readings with a TIER reading — runs that stack do not share a channel's width — which
  `mep.duct_joist_bay_occupancy` (now in `checks/mep/bay_packing.py`) grades and
  `routing/corridors` prices; an over-subscribed bay is a FAIL no arrangement can fix.
  `resolve/duct_sizing.py` holds the Darcy-Weisbach/Colebrook physics `erv_static` used to own
  privately, plus the Manual D equal-friction rule at `[mep.routing]
  duct_friction_in_wg_per_100ft` (0.08). `FloorOpening(purpose=CHASE)` survives resolution as
  `ResolvedFloor.chases` and becomes a riser corridor rather than merely a void a run is
  allowed through.
  - **It found something.** `DU-B-ERV-SUP-TRUNK` carries 210 cfm in 6" galvanized at **0.322
    in. w.g./100 ft**, four times the design rate — the same fact `notes/erv_static_budget.md`
    reaches from the fan-curve end ("210 at 0.2 or 206 at 0.4" is a duct too small for its
    air). Not a FAIL: an authored size is a decision. `--explain` prints it so it stops being
    invisible.
- ~~**No blocker mobility, no counterfactuals, no fixture-movement diagnostic.**~~
  **Done 2026-09-17 (roadmap Phase 4).** `routing/diagnostics.py` classifies every blocker —
  `fixed` (opening, void, concrete), `movable` (another run), `priced` (soft prism), `unknown`
  (`--avoid`, or geometry too thin) — read off `HardPrism.kind` and never guessed from a tag,
  and a `Refusal` record carries the blockers with their conflict locations and z, the
  quantified shortage, what was attempted, and whether impossibility is **established** or
  merely "not within this search". Those were one sentence before and they are different facts.
  `--counterfactual` re-searches with one MOVABLE blocker lifted at a time (bounded, four deep)
  and prices what opens; `routing/counterfactual.py` labels every exit a diagnosis rather than
  a proposal, because the lifted run still has to go somewhere and that is a search nobody ran.
  `--sweep N` walks a fixture's derived drain point along its `wall_ref` in 2" steps, clamped
  ALONG the wall and skipped where it would land in a stud, and prints the best station as a
  `Fixture(...)` with `drain_position` set. Contract 3's `refusals` array is in `--json`.
- ~~**A whole-storey duct problem exceeds `MAX_LATTICE_NODES`.**~~ **Done 2026-09-17
  (roadmap Phase 7).** The measurement was right about where the time goes — build-graph
  4,128 ms against a 0.0 ms search, so pruning the SEARCH would have bought nothing — and
  wrong about the lever. It was not that the lines ran too far; it was that **every** line was
  laid down on **every** z level, so a footing nine feet under the attic nominated turn points
  at its corners *in the attic*. `graph.candidate_lines_at` derives them per level, which is a
  correction and not a heuristic: an obstacle a plane does not cut through has no corner on
  that plane to turn at. `DU-M-ERV-R-KITCH` went 780,066 nodes (a flat refusal) -> 27,618 and
  routes; the house's worst duct went 780,066 -> 123,248, and `MAX_LATTICE_NODES` is raised to
  150,000 — this constant's own documented instruction followed, with the measurement behind
  it. Two things stay level-independent on purpose: a corridor's plan line on a PLAN search (a
  gravity run's z is a derived potential, not the plane it searches in — filtering those took
  `PR-B-KITCH-DRAIN` from a route to a four-node lattice), and the world-query memo, which is
  off by default because it costs ~45% of a single build and pays only across reuse.
  `tests/test_routing_perf_guard.py` states the criterion in node COUNT rather than wall clock:
  a count is exact, machine-independent, and is the quantity the cap is written in.
- ~~**No fitting is a part; a turn is a mitre.**~~ **Done 2026-09-17 (roadmap Phase 5).**
  `library/fittings.py` + `hardware/fittings.py` hold the catalogued patterns with their
  standards (ASTM D3311 for DWV, ASME B16.22 for copper, SMACNA for round duct), and
  `resolve/mep_fittings.py` is the one reading the pipe take-off, the duct take-off,
  `mep.fitting_pattern`, the IFC emitter and the router's proposal all share. Two answers are
  deliberately kept apart: what a turn is BILLED as (the row `prices.toml` joins, unchanged)
  and what PART it is. They disagree on catlin and the disagreement is the point —
  `elbow-22.5-1in` is a priced row for a fitting B16.22 does not make. **Every laying length
  is `None` and says why**: no manufacturer submittal has been read into this repo, which is
  also why no fitting BODY is drawn — without a centre-to-face there is no way to turn a
  mitred vertex into a solid, and `mep.fitting_pattern` reports that rather than inventing a
  dimension. 239 of catlin's 259 fittings name a catalogued pattern; the other 20 are
  UNKNOWN with the reason and the remedy attached. `IfcPipeFitting`/`IfcDuctFitting` are
  emitted as placed records with no body, for the same reason.
- ~~**No whole-house coordination.**~~ **Done 2026-09-17 (roadmap Phase 6).**
  `haus route --house` lays every run in scope against ONE occupancy ledger — every accepted
  proposal becomes hard prisms via the same `run_envelope` the checks use — in a declared
  order (`routing/campaign.TRADE_ORDER`), with bounded rip-up that never touches anything the
  campaign did not lay. Still no `--write`; `--out` writes a report and a paste file, and the
  test asserts every plan file's sha256 is unchanged. On catlin's basement drainage: 6 laid,
  4 rip-ups, the rest refused with a reason.
- ~~**Nothing can picture the routing space.**~~ **Done 2026-09-17 (roadmap Phase 8).**
  `haus route --space <target>` classifies it into green / orange / red / gray, each naming
  the action it implies, read off `HardPrism.kind` through the same `diagnostics.mobility_of`
  the refusals use. `--json` carries the polygons; `--out` writes one SVG overlay per level on
  a new `routing` review layer. `emit` does not import `routing` and cannot — the regions are
  a parameter — which is also why `haus render --view plan` does not draw it on its own: a
  render has no target, and "the routing space" is only defined for one.
- **188 MEP interpenetrations house-wide, and they are now GRADED.** `mep.run_interference`
  (`checks/mep/run_interference.py`, added 2026-09-17) compares every pair of runs envelope
  against envelope — real outside diameter plus insulation, one prism per segment over that
  segment's own z range — and exempts a CONTACT only where it lies within a fitting's reach
  of a joint between the two, a rough opening names them both, or the two are bundled risers
  of one `VentRun`. 75 pipe-against-pipe, 74 duct-against-pipe, 37 duct-against-duct, 2
  pipe-against-vent-riser; median overlap **2.06"**, worst **4.00"**, which is one 4" duct
  entirely inside another. The hand count of "37 in the NW column"
  (x 0..7', y 32'..36'-6", 2026-09-15) was the same defect seen through a keyhole.
  - **A `VentRun` is now a run everywhere, not only in the viewer.** Its riser route is
    derived once in `resolve/vent_termination.riser_polylines`; `resolve/accessories` reads
    it for the solids and `resolve/mep_envelopes` for the envelope, so the pipe the viewer
    draws, the pipe `mep.run_interference` grades and the pipe `routing/obstacles` avoids are
    one pipe. It also made `mep.run_through_stud` able to see the radon riser, which reported
    a 3" bore in a 2x4 the day it could: the bundled risers spread perpendicular to the wall
    EXIT, which on catlin put the two 3" pipes on ONE line for the whole 8'-7 1/2" jog (they
    cannot share a bore through a joist web) and drove the east one into W-A-BA-E's studs.
    The spread now takes the LONGEST horizontal leg. catlin is back to 0 FAIL.
  - **`mep.drain_inlet_spacing` (new, 2026-09-18) grades two branches landing on one stack**
    — and can only ever be UNKNOWN, which is the point. catlin's attic branch and suite WC
    branch land 2 1/2" apart on `PR-M-S-SUITE-DRAIN`, and whether two wyes fit that close is a
    question about laying length: every `center_to_face_in` in `library/fittings.py` is `None`
    with a `data_note` saying no submittal has been read. It names the pair, the spacing and
    the missing datum. Never a FAIL.
  - **A floor bay's clear width is decremented by what is already in it**
    (`routing/corridors.floor_corridors`), through the same `mep_packing.pack` tier sweep
    `soffit_corridors` and `chase_corridors` already read. It was the purely structural
    figure, so `admits` answered "does this fit the bay" rather than "is the bay free", and a
    campaign would lay a fourteenth radial into a bay that already holds thirteen. Two limits
    are disclosed on the corridor rather than papered over: one band per run at its MEAN z,
    and a `ConduitRun` names no `floor_ref` and is not an occupant.
  - **A branch vent can be proposed into a SIBLING** (`cli/route_roots._vent_siblings`). A
    vent's downstream is a chase, not another run, so `drain_tie_ins` derives nothing for it
    and `--run` refused outright — two branch vents on a common vent is ordinary IRC P3104
    work and the router could not propose it. The goal set is now every sibling landing on
    the same station, over its whole polyline. `--tree` still refuses a vent main, which is
    honest: it is a directed Steiner tree under a gravity search, and head budgets, inverts
    and a fall profile do not describe a vent.
  - **A route that is already AT its goal is a finding, not a paste.** It used to print a
    one-point polyline as dialect — a 1-tuple that will not parse.
  - **`haus check --no-suppress` reads the campaign's score** without editing
    `preferences.toml` and putting it back. 201 FAIL unsuppressed against 0 suppressed, on
    2026-09-18.
  - **THE ATTIC ERV RADIALS CANNOT BE RE-LANED BY SEARCH, AND THIS WAS TRIED.** The largest
    class in the 188 is `DU-A-ERV-R-*`: several 4" radials drawn on ONE line at ONE elevation
    out of the manifold at (5', 34'-6") — e.g. `DU-A-ERV-R-ATTIC` and `DU-A-ERV-R-BATH1` share
    (5',34'-6")->(1',34'-6") at z=20'-4" exactly. A1 is why they report at all: they share a
    joint at the manifold, so the old pair-wide bool exempted every one of them.
    `haus route --house --trades duct --storey attic --alternatives 3 --evaluate` laid 4 of 5
    and **its own `--evaluate` rejects the result**: every alternative lane bores 4.00"
    through 2x6 studs (R602.6 allows 3.30") in `W-S-N1B`, `W-S-N2`, `W-S-N3`, `W-A-N1`,
    `W-A-STU-W`, two run EXPOSED and ungraded, and `DU-A-ERV-R-BATH1` refuses outright
    (blocked by `CD-A-PV-EAST`, movable). That is the same sentence this file's
    `mep.run_through_stud` entry already carries: **a 4" round duct is not bored through a
    stud at all** — it goes over the plate, through a soffit, or in a floor bay. So this
    group needs a DESIGN answer (soffits, or distinct elevations in the attic floor band),
    not another search, and pasting the campaign's output would trade interference FAILs for
    stud-bore FAILs.
  - **It rose from 155 to 188 on 2026-09-18 and nothing about the building got worse** — the
    engine can see more. The joint exemption was a single bool for the PAIR, so two runs
    sharing a fitting at one end interpenetrated anywhere else unreported (+31, among them a
    3" drain 2.21" inside another 3" drain two feet from the suite stack head they share);
    and a `VentRun` resolved to solids alone, so it was in no collision system whatsoever and
    was not even a router obstacle (+2, both against the radon chase). Its riser route is now
    derived once in `resolve/vent_termination.riser_polylines` and read by both the solids and
    the envelope.
  **Suppressed in `houses/catlin/preferences.toml` with the count and the date on it**, as an
  open campaign rather than a decision: landing it red takes `haus print`, the handoff bundle
  and the CI gate with it. Working it down is what `haus route --alternatives --evaluate` and
  `haus trial` were built for. Delete the entry, run `haus check houses/catlin --only fail`,
  and the count is the score.
  - **A schematic raceway is excluded and disclosed, not graded.** A `ConduitRun` holding two
    end elevations says nothing about what it clears in between, so grading it against the
    "rises at its last point" convention reports clashes with a drawing. `ConduitRun.elevations`
    (per-vertex, project-frame absolute) now exists; catlin authors none yet, so all three of
    its raceways come back as one UNKNOWN naming them. Authoring those profiles is what closes
    "nothing can grade a duct against a conduit".
- ~~**Notching and boring limits are not covered.**~~ **Done 2026-09-17.** R502.8.1,
  R602.6 and R602.6.1 are off `mn_residential`'s not-covered list. The rules live in
  `resolve/mep_bores.py` where the router can reach them too, graded against the ACTUAL
  resolved members rather than a spacing — `W-S-SN3`, the staggered wet wall, bores 11 studs
  at its axis and 5 two inches north of it, which is the number a rule applied to "the wall"
  cannot produce. Oracled by `houses/catlin/notes/framing_bore_limits.md`. An engineered
  member is UNKNOWN and never graded; a penetration as wide as the member is a framed
  opening and not a bore, and **nothing in this engine grades the header over one** — that
  is the next hole in this area.
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
- **Second-floor drain noise is solved by LAYOUT, and the numbers are here so nobody
  re-measures them** (2026-09-19). Horizontal pipe in the second-floor cavity, by the room
  below (`out/model.json`): RM-M-MUDROOM 13.2 LF drain / 7.2 vent; **RM-M-STUDY 7.9 / 5.9**;
  RM-M-LAUNDRY 7.1 / —; RM-M-MUD-CLOSET 3.0 / 3.0; RM-M-CLOSET 2.8 / —; **RM-M-LIVING 0 /
  46.0**. **Not one water-closet drain crosses a quiet room** — the three WC legs land over
  the mudroom, mud-closet, laundry and closet, and `RM-M-BED` is at y=6' while every drain
  leg is at y >= 16'. The study's 7.9 LF is `PR-M-S-SUITE-TUB-DRAIN` (5.8) and `-LAV-DRAIN`
  (2.1), the two quietest drains in the house; the 46 LF over the living room is all vent —
  dry pipe — over a ceiling already on resilient channel (`CR-LIVING-CEIL-RC`). If it is
  ever wanted, the cheapest fix is a second `ConstructionRule` scoped to `RM-M-STUDY`,
  reusing the `floor:ceiling_channel` finder beside `CR-LIVING-CEIL-RC` at
  `plan/assemblies.py:4674` — zero engine code, three lines, and `resilient-channel` is
  already priced. It is **not** the HoldRite Silencer system, and the marketing is why: the
  "87% quieter" claim is ~8.9 dB, measured in 2006 by an unnamed lab, against a *bare steel
  J-hook*, on *copper water tube*; against the plastic stud inserts a competent plumber
  already uses the delta is 5.7-7.4 dB; ISO 3822 is a standard for taps and valves in water
  SUPPLY installations, not for pipe supports or DWV; and the clamps carry 25 lb, so they
  are isolators, not supports. The one genuinely independent dataset (CMHC 02-117, MJM
  Acoustical) says the **gypsum enclosure alone is worth 15-17 dBA** — more than any product
  in the category and already in this build — and that cast iron beats PVC by 8 dBA on the
  path that dominates.
- **"IRC P2604" still appears in finding prose and comments, and Minnesota deleted it**
  (2026-09-19). Minn. R. 1309.0010 subp. 3.D strikes IRC chapters 25-33 and P2604 is in
  chapter 26. The PERMIT CITATION was fixed — `checks/code/mn_residential/profile.py`'s
  "Pipe below and beside concrete" line now cites UPC 314.1 / 314.4 via Minn. R. 4714.0050,
  with the 45 SR 1007 repeal history on it — but six other sites still say P2604 in prose:
  `checks/mep/plumbing_concrete.py` (x5, including two finding STRINGS a reviewer can read),
  `resolve/mep_sleeves.py` (x2), `houses/catlin/plan/mep_sleeves.py` (x2),
  `houses/catlin/plan/mep_drainage.py`, `houses/catlin/notes/garage_hydrant.md` and
  `packages/engine/tests/test_hydrant.py`. Descriptions rather than citations, which is why
  they were left; a sweep is one commit and should say "UPC 314.1" where it says "P2604.3's
  45 degree influence line".
- **Nothing grades pipe SUPPORT spacing, and the profile now says so out loud.** `PipeRun`
  carries no support, hanger or guide field, so there is no spacing to measure. The governing
  rule in Minnesota is **UPC Table 313.3 via Minn. R. 4714.0313**, which Minnesota reprints
  amended: hubless cast iron at every other joint and every joint on a run over 4 ft, and
  Schedule 40 PVC with mid-story guides plus a 30 ft expansion interval against the new
  Minnesota-only Table 313.3.1. Building the check is a feature — a `support_spacing_in` on
  `PipeRun` plus a `mep.pipe_support` reading the material off the run — and is not needed to
  make the permit story honest.

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
- Figure out a space for a cat litter box.

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
