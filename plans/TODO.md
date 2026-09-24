# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **`Room.clear_face` is not the wall's finish face** — it's inset from the wall AXIS by one
  uniform `_lining_inset` (0.635"), not each wall's own resolved layer polygons, so a room
  polygon doesn't move when a liner or a retype does (`RM-M-STUDY`: published 19.3 sf vs a
  measured 15.4 sf clear box). Fixtures are now guarded
  (`test_catlin_contract_m3.py::test_wall_referenced_fixtures_stand_against_a_finish_face_not_inside_the_studs`);
  millwork still must not be sized off `clear_face` — use `out/model.json`'s wall layer
  polygons. The real fix is a second `ResolvedRoom` polygon that IS the finish face, and it
  moves every room's area at once (279 references across 51 engine modules + tests + houses +
  ui). **DEFERRED.** Details: the `clear-face-is-not-the-finish-face` memory note.

- **2D-edit sync** — a PatchOp rewrites one constructor; derived data recomputes but authored
  cross-references don't. `retype_placeable` already re-anchors wall-fitted placeables and
  scans tag references. Still open (~3-4 days if approved): authored refs + advisory checks
  for geometry-coupled consumers, promote retype warnings to review findings, route opening
  retypes through a centre-holding macro. Re-affirmed deferred 2026-08-07.
## Remaining Work

- **~220 sf of gypsum is still billed through the joist band** on every storey-line partition.
  `resolve/partition_top.py` deliberately moves only the FRAMING top: cutting the body at the
  joist soffit as well costs four FAILs (`code.R312_1_1_stair_open_side` on `ST-S2A`,
  `mep.wet_wall_occupancy` x3 on the basement and suite risers). Answering it means moving
  `W-S-SS2`'s guard coverage and re-authoring three riser extents — a design pass.

- **Router proposals drop `pull_points`**, so re-routing a boxed raceway loses its authored
  boxes; and conduit elbows and pull boxes are unbilled.

- **Concrete spec UNKNOWNs (8) wait on the mix submittal and a soil test:** chloride x4
  (ASTM C1218), ASR x2 (the aggregate's C1293/C1260 result plus a C1778 structure class), SCM
  x1 (cement standard/type), sulfate x1 (soil test, ASTM C1580). They sit on the permit
  checklist's non-blocking "Concrete materials for the exposure class" line, not on an
  inspection. Galvashield XPX anodes for the salt-splash court walls are undecided. Curing,
  cold-weather placement and slab joint layout exist only in prose.

- **No sheet-layout engine**, so nothing checks a sheathing break landing on a stud. L corners
  now carry `ResolvedJunction.sheathing_through`, which a layout pass would read. Cladding, WRB,
  foam and finish layers still bill off the node axis.

- **Follow-ups from the outer-stringer inset (2026-09-23):**
  - `ST-SG-PORCH`'s rail lines (`RL-SG-PSTAIR-S/N`, y −108"/−72") still sit on the stair
    edges, so a 1 1/2" post now oversails its stringer's outer face by 3/4". Moving both 3/4"
    in (`params/sunken_garden.py` `PORCH_STAIR_RAILS`) re-centres them; clear width ~33" ->
    31 1/2", still over the 27" minimum.
  - `ST-G-SERVICE`'s stringer heads bill 2 LSSR on `FS-BW-GARAGE`'s north-edge 2x8, and no
    catalogued LSSR row suits it: the 2x12 heads hang 4 1/2" below the 2x8, and the 36" flight
    is wider than the ~31" landing framing (one stringer lands 3" past `BM-BW-FE`). Needs a
    full-width carrier or a stair-stringer connector (LSC class).

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

- **`EQ-B-WH` on a plinth: left open (2026-09-23).** It is `MountKind.FLOOR` with
  `elevation=None`, so it bases on the storey datum. Research so far: a heat-pump water heater
  needs no stand (the 18" ignition-source rule is for fuel-fired units in garages), and a
  drain pan is mandated only where a leak would do damage, i.e. occupied space below — this
  tank stands on the basement slab. What is left is the flood question (the walk-out onto a drained court with a
  7 1/4" threshold: burst pipe or tank failure, not groundwater) and whether a 4" housekeeping
  pad is wanted anyway. **The trap if it is authored:** `EQ-B-WH.position` is quoted verbatim
  as a path endpoint by `PR-B-HW-TRUNK`, `PR-B-CW-WH` and `PR-B-HW-BATH1` and is the datum for
  `PR-B-WH-TPR` — four literals, one position, and `test_water_heater_connections.py` is what
  catches a move.

### MEP / lighting residuals

**The MEP interference campaign's live record is `houses/catlin/preferences.toml`**, not this
file. It carries the count, the class table that sums to its own headline, and a dated note per
class. Re-open the campaign with `haus check houses/catlin --no-suppress`, which is the score
with every suppression lifted.

- **Filters and access panels are recorded but not graded.** Registers carry
  `filter_nominal_size` / `filter_merv` / `service_face` (`model/types.py`
  `AirHandlingProductFacts`); `Equipment.behind_access_panel` / `access_panel_ref` exist but
  nothing in catlin sets them and nothing grades them. Open: author the panels once the design
  settles, and decide whether a reachability rule is worth a swing envelope.
- **ERV condensate shares `FX-B-SAUNA-FD`** rather than `PR-B-COND` — no gravity connection
  exists (main is at 85"+ where it crosses x=13'-6", best a 21.6" unit can manage under the
  basement ceiling is ~75"). The mechanical-room-sink alternative still has no drain.
- **The FS-S-WEST truss panel layout is a PROVISIONAL placeholder and the owner replaces it.**
  `params/second_deck.py` authors `web_panel_pitch=24"`, `web_opening_width=15"`,
  `web_panel_offset=12"` on FS-S-WEST, derived in its own `#:` from an ordinary Warren
  layout rather than read off a submittal. Ask the truss fabricator for the panel drawing,
  replace all three numbers and the two moved lines (`_LINE_MOVES`: 26'-8" -> 26'-10",
  34'-8" -> 34'-5 3/4", clearing risers), and re-measure `mep.open_web_panel` and
  `mep.run_member_crossing` that day — both entries in `preferences.toml` say so.
- **`REG-S-HP-PLANT` sits 9'-2" from the room's extract** (`REG-S-ERV-PLANT-EXH`, see
  `plan/mep_registers.py`) in an 18'x9' room, leaving the west end unswept by the room's only
  moisture-removal extract. A middle station (~x 12'-6") would shorten the duct run if the
  saving is wanted.
- **`DU-A-ERV-R-STUBATH` x `PR-A-STUBATH-VENT` is the last ERV/vent pair** (catlin,
  2026-09-24): both stand in `W-A-STU-W`'s one 5 1/2" cavity, and over the duct's elbow into
  its 4'-4" grille the vent would be in the partition's plates. Lower `REG-A-STUBATH-EXH`
  below 3'-2" (`plan/mep_registers.py`, held by another session during the reroute) and drop
  the duct's top to match; `tests/test_catlin_erv_clearance.py` then empties its `_KNOWN`.
- **The ERV SUPPLY manifold has no drawn feed and cannot have one where it stands.** Its
  extract twin got `DU-M-ERV-EXH-FEED` on 2026-09-20. RM-M-MECH's true inside faces are
  **63"x23"**, the supply riser sits west of the exhaust riser, and every gate to it measures
  4 3/4" or less against a 6" duct since the chase moved to 35'-1.3" — the conduit risers and
  `DU-ERV-EA` bind now. A flat 3"x8" does not thread either (2.87" pinch with EA's wrap), and
  shop-made duct is a last resort anyway: revisit after the reroute with stock sizes, or move
  the manifold.

- **Router follow-ups from rooting `PR-B-HW-TRUNK` on `EQ-B-WH.hot` (2026-09-23):**
  - A pipe proposal leaves a port sideways at the port's height; `ServicePort.direction`
    (straight up on the water heater) is read for ducts, not pipes.
  - The proposal drops the authored trunk's insulation, so `--evaluate` reads a NEW
    `mep.hot_water_insulation` FAIL; its riser end also lands inside `DU-M-ERV-R-BED`.
  - `haus route --run PR-B-CW-TRUNK` refuses before searching: its first vertex is the
    service entrance, and no run feeds it. The trunk was re-routed by hand under the
    `FO-M-ERV-OA` trimmer packs (TJ-9015 refuses the bore: point load, below the middle third).
  - `cli/cmd_route.py` is 571 lines, over the 500-line rule.

### Structural/framing residuals

- **`FS-BW-GARAGE`'s rims sit inside `BM-BW-FC`/`-FE`**: the landing bills rim lumber that
  stands in the carrier beams' own volume (phantom lumber).
- **Four matchers share one arithmetic but still answer at three tolerances.**
  `platform._collinear_overlap`, `stacking._axis_match`, `construction_geometry._stack_overlap`
  and `layout_lines._collinear` all route through `layout_lines.collinear_overlap` since
  2026-09-20, so the arithmetic is written once. Unifying the TOLERANCES is not a mechanical
  edit: `layout_lines` measures on the datum face and `_axis_match` on the raw node axis, and
  they differ by 43.8mm (basement) / 57.0mm (garage) — 13 stack pairs stack in one pass and
  not the other (`W-B-S1`->`W-M-S1` + 8 garage walls). All under-framed-wall pours, so nothing
  reads the difference today. The two endpoint formulations differ too and are preserved
  behind `both_ends=`.
- **A `Slab`/`FloorSystem` rim has no cladding concept.** `SL-M-DECK`'s exposed edge takes no
  fascia/trim/drip — the roof-edge machinery (`resolve/roof_edge.py`, `resolve/trim_bands.py`)
  has no horizontal-element analog.

### Schema gaps found during selections/fireplace passes

- **No `Lintel` element type.** A `Beam` stands in, and its `size` is a free string.
- **R502.10.1's single-member header allowance is sawn-lumber only, deliberately** — an
  I-joist/floor-truss deck would need a manufacturer's hung-header table this engine doesn't
  have, so catlin (all I-joist/floor-truss decks) sees no saving from it. **Still open:**
  nothing grades a single-member header against a span table at all —
  `structural.floor_opening_header` only reports past the prescriptive 8' ceiling.
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

- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists. (desired but not as explicitly modeled)
 - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row reads "GCP Bituthene 3000". `Material.product_ref` can only be set where the material is authored; the material has to live in `library/materials.py` because a LIBRARY assembly (`FOUNDATION_WALL_XPS4_OUTBOARD`) references it; and a library material may not name a house-owned `Product` tag — `Library.products` is populated from `plan/products.py` and every other house would resolve it to `None`. There is no override path: `PlanModel.material()` returns the FIRST match, so a house appending a duplicate tag is shadowed for geometry while WINNING in `product_labels`, which is worse than not doing it. The identity lives in the material's `source` and in the `prices.toml` selection note instead. Closing it properly means either a house-level material-override mechanism or moving the foundation tail out of the library.
 - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
   bathroom ceiling should be open. That is a design question, not a cleanup.
 - **Rebar is modelled and pickable now; only the price back-out is left.** The `[concrete]`
   $/cy rates still absorb the steel (`[rebar_inclusive]` in `prices.toml`). Pricing rebar as
   its own rows means cutting those rates the same day.
 - Add trim/baseboard — we're generally trimless (clean lines, drywall), but maybe a flush-with-drywall baseboard.
- Orientation-tuned glass, particularly second-story south-facing windows.
- Make it easier to "hop" into a given room for 3d viewing and rotate in spot, perhaps with a "fish eye" lens view rendering
- Possibly in second floor study, a bookshelf continuing hallways to make an alcove under the stairs
- **OPEN: `_y_in_n` is datumed off the ABOVE-GRADE cladding face, and nothing at the porch
  deck's own elevation faces cladding.** Below z=0 the house's south face is `W-B-BRICK`,
  which stands **6.435" south of that line** (cladding -7.25", brick -13.685"). The two halves
  that were closed on 2026-09-20: `house_ext_layers_in` now derives from `_WALL_OUTBOARD_IN`
  (and `gap_to_house_in` absorbs the difference, so no geometry moved), and
  `code.R311_3_exterior_landing` can now union two abutting surfaces into one landing. What
  remains is the datum question itself, and it is an owner decision rather than a nudge:
  widening the gap back to a nominal 5" pushes the court 2.25" south and FAILs D-B-PATIO.
- Figure out a space for a cat litter box.
- **A library catalog type cannot name a house-owned `Product`.** `ED-T-EV-1450` lives in
  `library/electrical.py` and the Leviton 1450R is authored in `houses/catlin/plan/products.py`,
  so the `product_ref` cannot be made: `houses/starter` would resolve it to nothing and take an
  `integrity.unknown_product_ref` ERROR. Same seam as the Bituthene selection. Needs a
  house-level catalog-override mechanism, or the type retagged house-local (which moves the
  `[placeables]` price key and four tests).
- **Door hardware still bills as one lump in catlin.** Openings rows now carry
  `DoorType.function`, but catlin hangs one commodity type (`DT-INT-SWING32`) at both a bath and
  a study, so the type has to split before a per-function allowance means anything.
- **Plan lettering residue after 96b845f4 (3/32" lettering):** at 1/4" a few small rooms still
  touch a tag (PANTRY/D8, STUDY/D13, MECH's "CHASE TYP. OF 2"), and on the 11x17 reduced check
  print the 12 pt room names spill past small rooms' walls.
- Paint is missing on a lot of interior drywall assemblies. This likely impacts pricing more than anything.
- Ceiling drywall might be worth counting as the floor above (so when we remove layers in the 3d viewer, we can see into the room)
- the dimple board of the sunken garden retaining wall should probably be moved under the concrete view toggle (because it's assembled in that lens, not because it is made of concrete).

# Project Management

**Built 2026-09-11** (decision #69, `docs/site-state-format.md`): visits, inspections,
readiness, milestones, handoff lists, and the `#/site/board` surface. `haus schedule` and
`haus inspections` are the phone-free version.

Still deferred, and each for its own reason:
* **Photos, and voice notes.** Deliberately cut from v1: the two needs this surface exists
  for are answered by derived checklists, and a photo is storage, sync and a privacy
  question before it is a feature. A visit's `note` carries text today.
* **Bids as a GC.** Bidders should see the material estimate for their own scope and not the
  costed total — that is an access-control model, not a page, and there is no auth here yet.
* **A calendar view.** Suggested dates are derived now (`schedule/timing.py`, from the
  house's `[calendar]`, durations, cures and lead times); nothing renders them as a calendar.
* **Show the backside of the house as the main bid image** (so the design reads cheaper).
* **Local-first sync** (drive, S3, or Cloudflare Workers) for anything the phone writes.

Firstly design a house (with permit checks, building science review, floorplan editing in the 2d UI, 3d review, cost reduction and BOM review).
Secondly gather bids, organize the timeline (inspection gates, etc), then track completed progress.
Thirdly use the house design as a reference (ie for agents understanding live data on home assistant in context), potentially with feedback loop of updating the design or later running a remodel
