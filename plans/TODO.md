# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

## Needs your decision

- **2D-edit sync** — a PatchOp rewrites one constructor; derived data recomputes but authored
  cross-references don't. `retype_placeable` already re-anchors wall-fitted placeables and
  scans tag references. Still open (~3-4 days if approved): authored refs + advisory checks
  for geometry-coupled consumers, promote retype warnings to review findings, route opening
  retypes through a centre-holding macro. Re-affirmed deferred 2026-08-07.
## Remaining Work

- **Separate nominal door leaf sizes from modeled opening voids.** Ordinary door type
  dimensions currently feed both `_opening_size` and swing clearance. The cased product
  appearance fits inside that existing void; it does not guarantee the catalog's nominal
  leaf width or clear passage. Define leaf/rough-opening sizing together with framing and
  clearance before changing these envelopes (`plans/default-door-appearance.md`).

- **Order the canopy and garage trusses from a fabricator who seals them** — the last four
  canopy UNKNOWNs (`rafter/RF-BW-CANOPY`, `rafter/RF-GARAGE`, `structural.truss_reactions`,
  `structural.uplift_capacity`) close only on those drawings. The ask is `AN-G-TRUSS-ORDER` in
  `houses/catlin/plan/storeys/garage.py`: reactions per bearing with their snow/drift/wind
  basis, the five drift trusses, the canopy's open south-end truss out of plane, and the N-S
  chord with its 0.03" splice slip. On receipt, author `Roof.published_reactions` on both
  roofs and record the component seal in `engineering.toml`. Also confirm the retail price
  ranges for AC6Z / ACE6Z / A35Z / CBSQ66-SDS2 in `prices.toml` (marked UNCONFIRMED).

- **Two drain turns are boxed in:** `PR-B-SINK2-DRAIN`'s 70.8-degree turn (a 60 needs the turn
  in FS-M-WEST's joist band, where the leg cuts I-joist flanges; a 90 drops it into the x=2'-0"
  ERV corridor), and `PR-M-DRYER-COND`'s 58 degrees in 3/4" PVC (every squared-off version
  reads as a run hanging in RM-M-LAUNDRY). Both stay `mep.fitting_pattern` UNKNOWNs.

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

**The open MEP campaigns' live record is `houses/catlin/preferences.toml`**, not this file:
`mep.riser_through_deck` (undrawn holes) and the itemised web crossings, each with its count
and a dated note. `haus check houses/catlin --no-suppress` is the score with every
suppression lifted. (`mep.run_interference` closed 2026-10-08 and is ratcheted at zero.)

- **Correct the HPWH envelope and connections.** `EQ-T-WATER-HEATER` / `EQ-B-WH` model
  24×24×68 in. Rheem's dimension sheet distinguishes the 74 3/16-in. tank from the full
  91-in.-high, 29½×24⅝-in. unit. Use the ordered-unit drawing to set the complete envelope,
  top-port datums, connected runs and service clearances. [Rheem dimension sheet](https://files.myrheem.com/webpartners/ProductDocuments/915C4E4F-0D9A-4591-AAED-454B9A202B66.pdf)
- **Set the sauna's occupied ventilation basis.** The selected Harvia HPCS11U1H manual calls
  for adjustable low inlet / opposite upper outlet vents and 5 air changes per hour; the
  modeled 20-cfm exhaust is about 2.7 ACH in the ~450-ft³ room, with the vents reversed.
  Confirm the accepted arrangement, makeup air and ERV balance before changing terminals.
  [Harvia manual](https://www.kbauthority.com/files/PDF/Harvia/HPCS11U1H%20Manual%20Sheet.pdf)
- **Determine basement backwater protection before under-slab rough-in.** Add the next
  upstream manhole-cover elevation on the survey datum, compare it with basement fixture
  floors under UPC 710.1, and protect only affected low branches if required. The existing
  sewer-permit task records invert, not cover elevation. [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- **Route `EQ-B-WH` condensate.** Rheem places its condensate outlet 59 in. above the floor;
  no run serves it, and the existing collector is higher. Draw a falling route to an
  approved receptor or a pump discharge; include it in the existing condensate/pump allowance.
  [Rheem specification](https://files.myrheem.com/webpartners/ProductDocuments/D4653184-5800-421C-92EE-9517A74AE244.pdf)
- **Resolve water-heater thermal expansion.** Confirm the service, meter, PRV and
  `PA-G-HYD-BFP` topology. If they close the system at the heater, add and price a listed,
  properly sized expansion-control device on the heater side; otherwise record the open-system
  basis. [UPC 608.3 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2018/aug16.htm)

- **Filter and service access is only partly resolved; no reachability rule grades it.**
  System 1's 28x12x1 MERV 13 return filter is typed and reachable from the hall floor;
  the Broan ERV's exposed service door, published clearances, and high outdoor screen's ladder
  access are recorded in `houses/catlin/notes/erv_service_access.md`. Gree wall-head screens
  are front-access; three high heads require a ladder. The bath-2 stall-dryer intake now
  specifies an AAF PerfectPleat HC M8, nominal 10x10x1 filter; verify its actual dimensions
  against the selected grille holder. A ladder below the high intake screen temporarily
  occupies part of the HP3 disconnect's working-width; confirm that maintenance-time overlap
  or relocate the disconnect.
  General open item: grade filter-change/service envelopes and decide
  whether a reachability rule is worth a swing envelope; `Equipment.behind_access_panel` /
  `access_panel_ref` remain unused in catlin.
- **ERV condensate shares `FX-B-SAUNA-FD`** rather than `PR-B-COND` — no gravity connection
  exists (main is at 85"+ where it crosses x=13'-6", best a 21.6" unit can manage under the
  basement ceiling is ~75"). The mechanical-room-sink alternative still has no drain.
- **The FS-S-WEST truss panel layout is a PROVISIONAL placeholder and the owner replaces it.**
  Owner confirmed on 2026-09-29 that no fabricator panel drawing is available yet. The six
  remaining `mep.run_member_crossing` errors stay open until the actual panel geometry arrives.
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

### Performance / energy follow-ups

- **Compare the ERV/air-handler interlock's annual fan energy with dedicated ERV supplies.**
  `EQ-B-ERV.blower_interlock_ref` calls `EQ-S-HP1-AH` so ventilation reaches remote rooms
  while the heat pump is off (`houses/catlin/plan/mep_erv_l3.py`). Measure incremental
  ventilation-only watts and annual runtime, then price a balanced dedicated supply
  alternative. Preserve room delivery and backdraft protection. `mep.erv_blower_interlock`
  grades the present arrangement but does not compare operating energy or lifecycle cost.

- **Pressure-check smaller hot-water branches before rough-in.** `PR-B-HW-BATH1` is a
  ¾-inch copper branch serving one basin (8.8 ft); `PR-B-HW-KITCH` is ¾-inch copper for the
  kitchen sink and dishwasher (49.5 ft). Price ½-inch alternatives and check fixture demand,
  pressure, developed length, simultaneous use and the selected pipe's internal diameter.
  Approximate copper volume falls from 0.22 to 0.11 gal at the basin and 1.24 to 0.60 gal in
  the kitchen. Shorter waits and less cooled water may save energy; quantify with actual use
  and HPWH performance. Do not resize shared bath/tub trunks without a separate demand
  calculation. [EPA hot-water distribution guidance](https://www.epa.gov/watersense/watersense-labeled-homes-hot-water).

- **Make the PV layout comply with roof access, then study a second row.** `params/solar.py`
  calls 12 modules / 5.28 kW a maximum, but generates one row on each slope. Verify the
  current 1 ft ridge clearance, access pathways and array coverage against MN R324 and final
  roof geometry; pathways run eave-to-ridge across the slope, not along the ridge. DLI
  guidance calls for 36-inch pathways and, under the ordinary rule, an 18-inch ridge setback
  below 33% coverage or 36 inches above it. Study five modules along the ridge and a second
  row down each slope (20 modules / 8.8 kW as a geometric candidate), checking access, shade,
  attachments, structural loads and exact 12kPV string/current limits before treating this
  as feasible. Request incremental installed pricing and site-specific production estimates.
  [MN DLI solar guidance](https://www.dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf).

- **Include inverter overhead in backup runtime.** `takeoff/backup_calc.py` applies usable
  battery capacity directly to circuit-average AC watts; it does not model inverter idle
  draw or conversion loss. Measure the EG4's grid-connected and islanded overhead and
  low-load efficiency, then update runtime without double-counting losses. This matters
  against the always-on tier's small average load and should inform commissioning and any
  later battery decision; peak-capacity checking remains separate. See
  `houses/catlin/notes/backup_power.md` for current assumptions and verdict.

- **Resolve the dining radiant floor's operating schedule.** The 58 ft², 700 W
  `FH-M-DINING` zone supplements heat-pump space heating. `houses/catlin/notes/room_heat_loss_baths.md`
  already flags warm-up lag and the undecided setback schedule. Test a meal-time/preheat
  schedule and floor limit with a simple override; compare metered energy and comfort over
  representative weeks. Keep this tied to the existing note rather than duplicating its
  heat-output analysis.

### Structural/framing residuals

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
 - **`Material.product_ref` was NOT set, and it is not an oversight.** The plan called for a `Product` record naming the GCP datasheet so the BOM row reads "GCP Bituthene 3000". `Material.product_ref` can only be set where the material is authored; the material has to live in `library/materials/` because a LIBRARY assembly (`FOUNDATION_WALL_XPS4_OUTBOARD`) references it; and a library material may not name a house-owned `Product` tag — `Library.products` is populated from `plan/products.py` and every other house would resolve it to `None`. There is no override path: `PlanModel.material()` returns the FIRST match, so a house appending a duplicate tag is shadowed for geometry while WINNING in `product_labels`, which is worse than not doing it. The identity lives in the material's `source` and in the `prices.toml` selection note instead. Closing it properly means either a house-level material-override mechanism or moving the foundation tail out of the library.
 - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
   bathroom ceiling should be open. That is a design question, not a cleanup.
- Orientation-tuned glass, particularly second-story south-facing windows.
- **OPEN: `_y_in_n` is datumed off the ABOVE-GRADE cladding face, and nothing at the porch
  deck's own elevation faces cladding.** Below z=0 the house's south face is `W-B-BRICK`,
  which stands **6.435" south of that line** (cladding -7.25", brick -13.685"). The two halves
  that were closed on 2026-09-20: `house_ext_layers_in` now derives from `_WALL_OUTBOARD_IN`
  (and `gap_to_house_in` absorbs the difference, so no geometry moved), and
  `code.R311_3_exterior_landing` can now union two abutting surfaces into one landing. What
  remains is the datum question itself, and it is an owner decision rather than a nudge:
  widening the gap back to a nominal 5" pushes the court 2.25" south and FAILs D-B-PATIO.
- Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space for a self emptying litter box.
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
- Several of the interior 2x4 wall types do not yet bill paint (or perhaps paint for them is estimated elsewhere?). We want paint on main rooms and exterior wall interiors, but for rooms like the basement mechanical room or unfinished attic it is not necessary.
- **Author interior paint at library level, then retire `takeoff/derived_paint.py` to a check.**
  Today bare gypsum facing a used room is *billed* paint by derivation (≈7,000 SF on catlin:
  the STC presets and every deck `ceiling_below`). Authoring would let the house say colour,
  sheen and vapour class, and the derived predicate would become "exposed gypsum in used
  space has no finish authored". Blockers: (1) a coating layer still adds depth —
  `resolve/topology._added_thicknesses` counts it though `Material.coating` says readers treat
  it as 0.0, and the 1/8" silicate wash / foundation coating alignments depend on that depth;
  (2) a wall coating draws a plane (polygonOffset, see the wash); (3) whether paint belongs in
  an STC preset's tested core; (4) authored paint makes gypsum Class III, which moves Glaser.
- The theater, RM-B-PLAY-N is specified as carpet, and should have a heating strip under the carpet near the sofa where feet are, likely just plugged in to a regular outlet
- PR-A-STUBATH-VENT_RUN goes right through the middle of the bathroom RM-A-STUBATH
- PR-B-ERV-COND-RUN runs right though blocking D-B-SHOP door
- Extra light switches by beds
- A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairwells. Some options: 1/2" Type C, Paper-Faced 1/2" AR (e.g., Gold Bond Hi-Abuse or USG Sheetrock AR), LP SmartSide 38 Series Panel 7/16" (Sidings Used Indoors), 1/2" MDF (4x8 Sheets with V-Groove or Batten Strips), 1/2" MDO (Medium Density Overlay) Plywood
- Let's maybe color the drywall by type, purple mold board is 'purple', for example. If we do this, it will need to be accompanied by some sort of mechanism to reduce the "glitching" that occurs here when two items are around the same thickness (the problem is, as the viewer pans, it sort of glitches between the two colors)
- Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam or standard elastomeric latex caulk ), Best Seamless Durability Upgrade (~+$0.45/sq ft): 1/2" Paper-Faced Abuse-Resistant (AR) Drywall, Best "Skip-the-Taper" Durable Wall (~$1.30/sq ft material, $0 mudding): 4x8 Pre-Primed MDF Shiplap Panels (or LP SmartSide 38 Series), The Winner for General Bath Walls: 1/2" Mold-Resistant Paper-Faced Drywall ("Purple Board" / USG Mold Tough, although not strictly needed on well ventilated walls with good high-resin paint), The Bathroom Ceiling Secret: 1/2" Interior Soffit Board (Sag-Resistant), Best Value for Speed & Zero-Fail Waterproofing behind tile: 1/2" Polyisocyanurate Foam Board (Johns Manville GoBoard), Places where 5/8" may still make sense: floor to floor ceilings (Type X), garage walls (5/8" AR Type X). Apparently the resonant frequency of 1/2" Type C drywall is one of the more ideal for household noises (being higher than the others)
- Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above the walking surface probably). Around the mudroom we want highest abuse resistant with something like wainscot (shiplap there carries the idea already, can be improved further possibly like LP Smartside). Some walls likely worth abuse resistance on a side: W-M-WELL, W-M-HS2/HS3/HS4, W-M-BAE, W-M-C1/C2/C3 and walls facing RM-S-HALLWAY and next to stair landings. A reviewer also said that we should focus STC drywall/framing upgrades strictly for the solid walls without undercut doors (as they say doors bypass sound so much they make upgrades not worth the price, although doors that are weatherstripped, solid, and with no undercut do have better STC), based on this we can perhaps remove resilient channel assemblies from W-S-SBS and W-S-BW1/BW2/BW3
- Open (drywall overhaul): kids' bedroom and kids' room hall faces are NOT on the abuse-resistant swap list; decide whether they take `gwb-ar` (the owner's list omits them).
- Open (drywall overhaul): mudroom wainscot could be LP SmartSide 38 Series 7/16" (sidings used indoors) instead of the shiplap; the shiplap stays until someone prices it.
- Check whether `RF-BW-CANOPY`'s 190 plf and `RF-GARAGE`'s 167.5 plf diaphragm rows already carry SDPWS-2015 Table 4.2A's specific-gravity factor (0.92) for their SPF trusses; neither source string says so
- D-M-STUDY for the small study booth might make more sense as a bifold glass door, or some sort of tracked panel door. A simpler option is probably to just make sure the hinge can open to close to 180 degrees so the door can be flat against the wall, out of the way of the walking space.
- Gold foil trim or panel accent somewhere
- Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible). Also attic rail, bracket 7 needs a rethink, ideally to an off the shelf part.
- Spec sand or gravel backfill around house
- The study light switch ED-A-STUDY-SW (x=260⅜", 48" up) now sits under the east casing leg, and haus check flags it as an advisory. It needs to move (perhaps to the bottom of the stairs and against the centerline wall)
- Make W-BW-SCREEN's east passage face prettier (currently 5/8" MDO, not the west structural CDX). [Finish comparison, elevations, quantities, and sample instructions](bw-screen-finish-comparison.md) completed 2026-10-14: natural black locust slats over matte black lead; visible stainless screws preferred. Shiplap and ornamental panels compared. West header symmetry implemented 2026-10-14 (6⅛″ south extension, paired AC6Z); comparison now shows the stairs and landing. Physical samples, actual door/closer clearance, and decorative finish construction/model implementation remain pending. Another option to consider is a thin brick over foam or cement backer board or lath (ASTM C1088 Exterior Grade brick, Polyurethane Construction Adhesive, Polymer-Modified Mortar), possibly thin brick ordered, or saw cut from extra brick from the other brick work.
- ED-M-PORCH-FLOOD: shielded adjustable 60° flood beneath the balcony front, aimed into the sunken garden; shared 3D geometry in viewer/GLB/IFC. However it seems to be a recessed light, not one that is angled at the sunken garden.
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Sconce ED-S-STUDY2-STAIR-SC1 is a bit close to the floor, perhaps it should go at the top of the stairs on the wall, still on the same circuit but in the room above?
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- Flashing geometry and visibility implemented 2026-10-15: west-draining fitted cap on SB-BW-BAND's exposed 2×6 sill above W-BW-SCREEN; metal heads and concealed perimeter/sill flashing at exterior windows and doors; one Flashing 3D hide/isolate control. [Modeling basis and limits](../houses/catlin/notes/flashing_model.md).
- Possibly swap the concrete canopy stairway (SL-BW-TIER*) to pressure treated wood and composite treads or with brick stairs.
- Consider adding a gutter along the entryway canopy gable in the narrow space between canopy and house, the goal is for this to mostly fill the space, if it can do so in a way that is buildable and not causing any problems. A more minimal fix might be flashing on the exposed south glulam beam end. 
- Related to the above, beams of the canopy, BM-BW-RE and BM-BW-RW might be able to be extended into the garage framing to provide more structural strength to the canopy (possibly allowing us to drop the sheathing bracing need on the W-BW-SCREEN). Downsides are that it puts the garage itself more on engineered terms and is a weakness in the garage weather seal.
- Make the countertop (and quartz window stools) a "ready to send to manufacturer" design and export. Include rounding corners
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps grab bars.
- Window/door quotes (products named 2026-10-21): get Drutex (DAKAM, Chicago), Andersen 400 and Cascadia quotes and close `notes/window_and_door_procurement.md` §2.6 — Alucover nail fin + NAFS DP, the 14" tilt-only minimum, Drutex sill rail height (re-strike the 2.953" stools), Andersen triple-pane in MN and frame depth, the Cascadia double-door NFRC label and thresholds, dark-colour warranties.
- [ ] Before fabricating RM-M-STUDY: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking connections, and record any dimensional changes in the bench spec.
- Plant room needs review on bottom of wall detail (switch to a flash cove capable vinyl?) and also a review on if plumbing or drainage is present.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Bedroom carpet provisionally selected 2026-10-23: Sweet Spot I Romano (warm ivory/cream), Future Foam 8 lb/ft³ 7/16-in cushion; light warm greige alternative. [Specification and purchasing checks](../houses/catlin/notes/bedroom_carpet.md). Confirm sample, current local quote, cushion acceptance/warranty and roll/seam layout; measure the installed assembly and reconcile plywood, transitions, door clearances and affected elevations. The existing 3/4-in model depth remains provisional.
- The bottoms of 3d modeled windows are a bit glitchy in 3d movement.
- Do passes to confirm geometry and dimensions of select products all align together correctly for real world build dimensions. Major items to check: stairs, doors and windows (and their trim/flashing), framing, cabinets, trusses.
- Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger revision, clip/washer and rail access, full hose stroke, cleanout clearance, vent fitting/bore envelopes and the inward tilt-turn window sweep (full turn likely obstructed). See houses/catlin/notes/kitchen_sink_installation.md; product/connection specification is complete, physical fit is not released.
- Lets get the BOM showing all IKEA SEKTION parts needed (knobs, scribes, hinges, feet, etc), and soft close pieces too.
- Can we widen D-M-BATH2 to 36"? Not sure if/how the casing would work as that puts it into the shower area (the casing).
- A couple of options to reduce echo in the gym. One is swapping drywall for drop ceiling tile framing (perhaps with some fiberglass in the cavity above). Another was vulcanized recycled crumb-rubber rolls or 4'x6' stall mats for the floor. A third was W-B-CE losing its south side drywall and having fabric plus simple wood slats (ie 1x2 finger jointed pine) as an effectively slat wall arrangement.
- Improve the wainscot of the mudrooms
- Oksana wants an elm slab sofa table
- Trial a countertop microwave in the east-counter cave (KGF4) vs the pantry east bay (RC1); pick one and record it.
- [x] Model a coffee machine and kettle — SEVERIN WK 3422 and Arctic White De’Longhi Rivelia EXAM44055W on the north kitchen counter (2026-10-25); see DESIGN-LOG for the accepted overhead-clearance shortfall.
- Check the basement stair carpet, and swap the carpet from the theater with an partial coverage area rug in the theater (technically not installed with tack strips or glue)
- Update the LVP to https://coretecfloors.com/en-us/products/coretec-pro-classics/quincy-oak-vv017-01018
- [x] Move D-M-MECH and D-M-MUDC 8" east within the existing walls (owner-approved instead of a full stud bay); relocate the three switches to W-M-MUDC-E.
- [x] Add factory-laminated glass with an internal security interlayer for all main-floor windows to the supplier quote request (2026-10-26): [window sourcing notes §2.6, item 10](../houses/catlin/notes/window_and_door_procurement.md#26-claimed-not-yet-in-hand). Availability, cost, lead time and performance remain pending with the window/door quotes.
- Conduit for floor thermostats for heated floor
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Fix the missing horizontal trim of the board and batten (instructions says max panel length of around 20', no end lapping, so needs to have a mid point 'board' trim likely)
- Seam clamps as minor snow retainer?
- Some 240V options to consider: 240V power supplies for electronics.
- D-B-PATIO: separate brick reveal, widened RO, 5-1/2 inch concrete seat, composite returns, one blind curb-skin recess and XMN5 sill extension are modeled. Sill/approach/pan intersections pass; nominal crest is 7.397 inches above court (7.647 with allowance). Complete concrete reinforcement/development, support root and cross-bearer bearing, field membrane bonds, installed pan/sweep/hinge sections, and assembled-unit label/warranty evidence. Standard rainproofing only; drainage/sump back up the revised concrete curb. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- D-S-DECK-E: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards. BE365 adapter F is documented; nominal crest is 0.397 inches above oak and 0.988 above landing (+0.250 allowance). Complete house-root connections and cross-bearer bearing, installed pan/sweep/hinge sections and the flexible flashing-end application; confirm assembly dimensions/label/warranty. Complete preferred/Tru-Defense prices remain unavailable publicly. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- Research most commonly failed residential code items and make sure checks or tests exist for those here.

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

- [ ] Confirm S-5-S compatibility and loads for Metal Sales Image II 1" snap-seam with the S-5! configurator / Metal Sales; verify Aptos 440 W clamp zones for the seam-snapped PVKIT columns.
- [ ] Confirm Image II eave rib-end treatment: installation guide pp. 20–22 calls for sealant or field-closed rib ends; current hot-roof design keeps rib ends open without a vent closure.
