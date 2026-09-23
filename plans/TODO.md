# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

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

- **~220 sf of gypsum is still billed through the joist band** on every storey-line partition.
  `resolve/partition_top.py` deliberately moves only the FRAMING top: cutting the body at the
  joist soffit as well costs four FAILs (`code.R312_1_1_stair_open_side` on `ST-S2A`,
  `mep.wet_wall_occupancy` x3 on the basement and suite risers). Answering it means moving
  `W-S-SS2`'s guard coverage and re-authoring three riser extents — a design pass.

- **Open `haus check` FAILs (17 on 2026-09-23), each needing a structural, fabricator or owner call:**
  - `structural.post_base_interference`: `BM-BW-HOUSE-SEAT`/`-GARAGE-SEAT` sit in the ABU66SS
    standoff of `PT-BW-CW`/`-CNW`. Author a real pedestal (the retired one had no post geometry).
  - `structural.member_in_masonry`: `ST-B2M`'s lower stringer and landing rim stand inside
    `W-B-CN`'s concrete; the stair is laid out to the wall centreline, not its face.
  - `code.R311_3_exterior_landing`: `FS-SG-DECK` now resolves tilted and stands 3.92" above
    `D-S-DECK-E`'s threshold (2.42" above `RM-S-STUDY2`'s floor). Lower the balcony datum
    ~2 3/8" or step the deck at the door.
  - `VR-M-RADON-VENT` (4): the radon/vent pair spreads 2.4" either side of its chase point and
    no station fits between `FO-M-ERV-OA`'s north trimmer pack, the 34'-8" truss and the ERV
    risers. Reframe the chase (one big opening), or give the engine a spread-direction option.
  - Floor-truss conflicts in `FS-S-WEST` (fabricator): `PR-M-S-BATH1-DRAIN` and `PR-B-HW-SBATH`
    on the 26'-8" truss; `DU-ERV-EA` and `DU-M-ERV-EXH-TRUNK` on the 34'-8" truss.
    `PR-B-HW-SBATH` has no station in `W-M-STOS2`'s 2x4 cavity (retype 2x6 or move the truss).
  - `PR-B-KITCH-DRAIN` runs inside `FO-M-STAIR`'s north trimmer; its lane is that opening's edge.
  - `CD-M-DATA-KITCH` runs inside `FO-S-STAIR`'s truss trimmer; no routable bay north of the well.
  - `mep.run_through_plate`: `PR-A-STUBATH-DRAIN` (W-S-DC2) and `DU-M-ERV-R-LAUNDRY` (W-M-CLN2)
    each want an owner-authored `PlateTie` (R602.6.1).

- **Concrete spec UNKNOWNs (8) wait on the mix submittal and a soil test:** cement standard/type,
  chloride per ASTM C1218, the aggregate's C1293/C1260 result plus a C1778 structure class, and
  a soil sulfate test (ASTM C1580). Galvashield XPX anodes for the salt-splash court walls are
  undecided. Curing, cold-weather placement and slab joint layout exist only in prose.

- **Column cover is 2", not the 3" wanted.** 2 1/2" and 3" pull the north-entry pad dowels
  under ACI 25.4.3.2's 6db spacing (ψ_r 1.6, ℓdh 11.38" in a 12" pad): 6 FAILs. The way back
  to 3" is 15" moment-pier pads, or hook ties through the pad (`BarSpec.hook_ties` can't sit
  on a `dowels` row yet). `balcony_moment_columns.md` §14.

- **No bar crosses the court's W1|W2 / E1|E2 joint at y −132".** Winter tension (§11m.2,
  0.571 on 6 #4) holds only if it is one pour; a construction joint there needs bars lapped
  through.

- **No sheet-layout engine**, so nothing checks a sheathing break landing on a stud. L corners
  now carry `ResolvedJunction.sheathing_through`, which a layout pass would read. Cladding, WRB,
  foam and finish layers still bill off the node axis.

- **New checks sit on no inspection:** `mep.run_through_floor_member`, `mep.run_in_joist_flange`,
  `mep.erv_blower_interlock` and the five `structural.concrete_*` checks are not on any
  `mn_residential/inspections.py` list (the concrete UNKNOWNs would block the footing one).

- **The router cannot root a supply run on an equipment port.** `PR-B-HW-TRUNK` now reads its
  tie-in from `EQ-B-WH.hot`, but `haus route` refuses and asks for `--via`.

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
  bases on the storey datum. The water heater is the real case, with `EQ-B-SAUNA-HTR` the only
  other floor-based
  unit and a sauna stove wanting to be at floor level anyway. **What to research
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

### MEP / lighting residuals

**The MEP interference campaign's live record is `houses/catlin/preferences.toml`**, not this
file. It carries the count, the class table that sums to its own headline, and a dated note per
class. This file used to restate it across ~290 lines and drifted to arguing about 145-150
pairs while the house said 67. Re-open the campaign with
`haus check houses/catlin --no-suppress`, which is the score with every suppression lifted.

- **No `Equipment` field records a filter or access panel anywhere.** `REG-T-HP-RET` is the
  only serviceable face on System 1; the model knows it only as a rectangle with a port.
- **ERV condensate shares `FX-B-SAUNA-FD`** rather than `PR-B-COND` — no gravity connection
  exists (main is at 85"+ where it crosses x=13'-6", best a 21.6" unit can manage under the
  basement ceiling is ~75"). The mechanical-room-sink alternative still has no drain.
- **The FS-S-WEST truss panel layout is a PROVISIONAL placeholder and the owner replaces it.**
  `params/second_deck.py` authors `web_panel_pitch=24"`, `web_opening_width=15"`,
  `web_panel_offset=12"` on FS-S-WEST, derived in its own `#:` from an ordinary Warren
  layout rather than read off a submittal. Until 2026-09-19 nothing narrowed an open-web
  member ALONG its span, so the engine read the truss as a continuous 8 7/8" chase and
  thirteen ducts crossing one 41" band all passed. Ask the truss fabricator for the panel
  drawing, replace all three numbers, and re-measure `mep.open_web_panel` and
  `mep.run_member_crossing` that day — both entries in `preferences.toml` say so.
- **`REG-S-HP-PLANT` throw is 11'-7" across an 18'x9' room** (deliberate — see
  `plan/mep_registers.py`), leaving the west 14' unswept by the room's only moisture-removal
  extract. A middle station (~x 12'-6") would halve the duct run if the saving is wanted.
- **The ERV SUPPLY manifold has no drawn feed and cannot have one where it stands.** Its
  extract twin got `DU-M-ERV-EXH-FEED` on 2026-09-20. RM-M-MECH's true inside faces are
  **63"x23"** (the prose's "39"x31"" reads off wall AXES), the supply riser sits west of the
  exhaust riser, and every gate to it measures 3 7/8" or less against a 6" duct — proved by
  eroding the free plan at four elevations and by `haus route`, not asserted. **The fix is to
  move `VR-M-RADON-VENT` ~2 1/2" north**, which opens the gate to 6 1/8" and still clears
  W-M-N3B. That is a drainage decision. A flat 3"x8" section threads, but
  `mep.erv_static_budget` matches on `nominal_diameter` and would go blind — a feed that
  blinds the budget it exists to sharpen is not a trade.
- **`mep.run_through_header` reports 6 UNKNOWNs and `haus print` gates on UNKNOWN.** New
  2026-09-20: holes through headers nobody had looked at (`2-2x8`s carrying drains and ERV
  ducts). IRC publishes no bore table for a header, so UNKNOWN is the honest verdict — but the
  house has to decide whether to suppress it, engineer it, or move the runs.

### Structural/framing residuals

- **`FT-SG-*` frost cover (12"-21" vs 42" required) routes to UNKNOWN**, not FAIL —
  IRC R404.4 makes a retaining excavation an engineered design, same as
  `structural.foundation_unbalanced_fill`. Permit checklist's "Foundation frost depth" is
  UNKNOWN because of it; pinned by `test_catlin_contract_m3.py`.
- **French drains could be a form-a-drain product** (doubles as footing form); we probably also have more drains than needed.
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

- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists. (desired but not as explicitly modeled)
- **`RM-S-PLANT`'s clear face doesn't know about its liner** — `_lining_inset` uses one uniform
  figure (0.635") rather than each wall's own resolved lining, so the room polygon doesn't move
  when a liner does. Confirmed worse on `RM-M-STUDY`: published 19.3 sf vs a measured 15.4 sf
  clear box (14.4 sf to the wainscot face) — retyping two walls thicker didn't move
  `clear_face` at all. Fixing it moves every room's area at once, so it's its own change; until
  then, don't size millwork off `Room.clear_face` — use `out/model.json`'s wall layer polygons.
- Make sure all desired access panels are in — deferred pending more design settling.
- **`TR-SG-LEADER-SE`'s outlet needs a shoe.** Closing the apron's north notches on 2026-09-12 put `W-RG-EAST-BALCONY` under the leader, crest 6" below the outlet, so 200 sf of balcony discharge lands on the cap of a dry-stacked segmental wall unless the outlet turns south. A cast elbow and a 1'-0" shoe to y -11'-3" is the detail; `Downspout` is a vertical run with one outlet elevation, so the model cannot hold it and nothing in `haus check` grades a downspout against a landscape wall. It has to reach the drawings from `params/raised_garden.py`.
- Kitchen has lights stuck above cabinets. Might want to swap some cans for under counter lighting. **Still open, and the geometry under it moved 2026-09-11:** the uppers are 15" deep hung at 53", not 13" at 54", so their fronts are 2" further into the room and 1" lower than whatever this item was last looked at against. The five under-cabinet tape runs moved with them.
 - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row reads "GCP Bituthene 3000". `Material.product_ref` can only be set where the material is authored; the material has to live in `library/materials.py` because a LIBRARY assembly (`FOUNDATION_WALL_XPS4_OUTBOARD`) references it; and a library material may not name a house-owned `Product` tag — `Library.products` is populated from `plan/products.py` and every other house would resolve it to `None`. There is no override path: `PlanModel.material()` returns the FIRST match, so a house appending a duplicate tag is shadowed for geometry while WINNING in `product_labels`, which is worse than not doing it. The identity lives in the material's `source` and in the `prices.toml` selection note instead. Closing it properly means either a house-level material-override mechanism or moving the foundation tail out of the library.
 - Model a rain garden to the west of the garage gathering water with drain tile from TR-G-LEADER-W and TR-RF-LEADER-W
 - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
   bathroom ceiling should be open. That is a design question, not a cleanup.
 - **Rebar (~5 tons, $10,000-18,000) is deliberately inside the `[concrete]` $/cy rates.** If
  it's ever authored as real elements, cut the concrete rates the same day. We may want to model rebar so it is clearly shown as a model element (selectable separately from concrete in the 3d view)
 - Add trim/baseboard — we're generally trimless (clean lines, drywall), but maybe a flush-with-drywall baseboard.
- Orientation-tuned glass, particularly second-story south-facing windows.
- Make it easier to "hop" into a given room for 3d viewing and rotate in spot, perhaps with a "fish eye" lens view rendering
- Possibly in second floor study, a bookshelf continuing hallways to make an alcove under the stairs
- **`W-B-CW3`/`W-B-STR2` are over-specified** (steel-stud ESS-closet assembly, closet is gone)
  — deliberately not re-specified; would widen each 2" and re-open condition coverage on a
  line nothing else asked about. Revisit only if that wall line opens for another reason.
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
- **Plan lettering residue:** at 1/4" a few small rooms still touch a tag (PANTRY/D8,
  STUDY/D13, MECH's "CHASE TYP. OF 2"), and on the 11x17 reduced check print the 12 pt room
  names spill past small rooms' walls.

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
* **A calendar.** There is no calendar because there are no engine-computed dates; if one
  arrives it renders authored `scheduled` values and nothing more.
* **Show the backside of the house as the main bid image** (so the design reads cheaper).
* **Local-first sync** (drive, S3, or Cloudflare Workers) for anything the phone writes.

Firstly design a house (with permit checks, building science review, floorplan editing in the 2d UI, 3d review, cost reduction and BOM review).
Secondly gather bids, organize the timeline (inspection gates, etc), then track completed progress.
Thirdly use the house design as a reference (ie for agents understanding live data on home assistant in context), potentially with feedback loop of updating the design or later running a remodel
