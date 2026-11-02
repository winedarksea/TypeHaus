# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

Sourcing quotes, construction todo doesn't belong in this document, this is just softwared and house design todo.
We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
Our general goals are decent longevity and quality at a reasonable price, avoiding premium items unless clearly a major improvement for our needs.
Note that many of the pinned decisions in the code base here aren't as fixed as they sometimes claim, the "fixed" decisions were usually fixed in a narrower context, and can be changed for sufficiently good reasons.

## Needs your decision

- **Budget policy (pricing review 2026-10-29):** `site-general-conditions` is $35–80k on an
  owner-GC build (cash items alone look like $15–30k), and `[contingency]` 10% also applies on
  top of the lump-sum allowances, which already carry wide spreads (~$15–36k at stake).
- **Sconce J/J1 (WAC Sprig BL-23210-BK):** confirm it can be hardwired. Output drops from
  623 lm to 287 lm compared with the Stretch it replaced.
- **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now (`maximum_opening_degrees`): clear opening 24.3" vs 29.3" at 90°.

## Remaining Work

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

### MEP / lighting residuals

**The open MEP campaigns' live record is `houses/catlin/preferences.toml`**, not this file:
`mep.riser_through_deck` (undrawn holes) and the itemised web crossings, each with its count
and a dated note. `haus check houses/catlin --no-suppress` is the score with every
suppression lifted. (`mep.run_interference` closed 2026-10-08 and is ratcheted at zero.)

- **Lighting review confirms (2026-10-31, houses/catlin DESIGN-LOG "Lighting review").** Before
  ordering: SuperLightingLED RGB+CCT white-channel CRI and lm/ft, and 12 mm in the 5/8" reveal;
  the Fleurco MHAP4236's CRI (swap if under 90); choose the P6 vanity and J2 bed sconces (vanity
  backplate <= 4 1/2"); CentricHOME R9 and enclosed/damp rating; Waveform tubes are Type B
  double-ended; GL-C-001P cold rating in the garage; power-on state of the D215S relays, the
  dining pendant and the six-plus controllers; the Zigbee dongle and the bath PIR sensors;
  MITTLED's US article numbers, lengths and connector cords (the order list counts one piece
  per run until `stock_length` is set); Mean Well HLG-100H-24A's Class 2 marking.
- **Determine basement backwater protection before under-slab rough-in.** Add the next
  upstream manhole-cover elevation on the survey datum, compare it with basement fixture
  floors under UPC 710.1, and protect only affected low branches if required. The existing
  sewer-permit task records invert, not cover elevation. [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- **Water-heater thermal expansion: ask SPRWS** (Engineering 651-266-6270) whether the meter set
  carries a check valve and what the static pressure at the main is. Then model a listed expansion
  tank on the heater inlet (and a PRV over 80 psi). `PA-G-HYD-BFP` is on the hydrant branch only
  since 2026-10-29, so the meter set is the only possible check. `notes/water_service.md` §4.
- **Confirm the delivered parts:** the RH400-30's T&P projection (4 1/2" to `W-B-ESS-S` on that
  side) and the ProSaunas vent hatch's cutout and free area (unpublished; (844) 565-1113).

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
- **The ERV SUPPLY manifold still has no drawn feed, and the radon pipe is not the blocker.**
  Measured 2026-10-29: the radon is the NORTH pipe of `VR-M-STACK`'s pair and sits west of every
  gate. The binding gate is 2.7" between the EXH riser crown (y 409.8") and `DU-ERV-EA`'s wrap
  (y 412.5"), with the radon moved 2 1/2" or not; also 5.5" between the SUP and EXH risers (three
  conduits in it), 1.4" south of EXH, 0.9" north of EA. A 6" stock duct needs 6". Levers:
  relocate `EQ-M-ERV-MAN-SUP`, or re-pack the EA/EXH/conduit column.
- **`mep.run_in_finished_volume`'s terminal grace is blind to leg length** (decision #94): a
  fixture's whole first or last leg is excused however far it runs. Measure what tightening it
  raises before deciding.
- **Router port stub is unpriced** (decision #95): its length and bend are not in a proposal's
  cost terms, and the 2" fitting allowance is a stated value, not a datasheet one.

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

- **Meter the EG4's real overhead.** `takeoff/backup_calc.py` now counts the 12kPV's
  datasheet idle (<55 W standby) and 94% maximum efficiency; both flatter a ~400 W outage
  load. Measure islanded idle and low-load efficiency at commissioning, with the backup duty
  cycles, and re-author them. See `houses/catlin/notes/backup_power.md` §6.

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

- **Is a silt fence required at all?** The owner doubts it on a flat, small residential lot.
  It is drawn on the W/E lot lines for now (`houses/catlin/plan/site.py`); ask St Paul DSI at permit.
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
- The theater, RM-B-PLAY-N is specified as carpet, and should have a heating strip under the carpet near the sofa where feet are, likely just plugged in to a regular outlet
- Extra light switches by beds: done for RM-M-BED (J2 sconces switch at the fixture) and RM-S-SUITE (2026-10-31); RM-S-BED1-3 still open.
- A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairwells. Some options: 1/2" Type C, Paper-Faced 1/2" AR (e.g., Gold Bond Hi-Abuse or USG Sheetrock AR), LP SmartSide 38 Series Panel 7/16" (Sidings Used Indoors), 1/2" MDF (4x8 Sheets with V-Groove or Batten Strips), 1/2" MDO (Medium Density Overlay) Plywood
- Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam or standard elastomeric latex caulk ), Best Seamless Durability Upgrade (~+$0.45/sq ft): 1/2" Paper-Faced Abuse-Resistant (AR) Drywall, Best "Skip-the-Taper" Durable Wall (~$1.30/sq ft material, $0 mudding): 4x8 Pre-Primed MDF Shiplap Panels (or LP SmartSide 38 Series), The Winner for General Bath Walls: 1/2" Mold-Resistant Paper-Faced Drywall ("Purple Board" / USG Mold Tough, although not strictly needed on well ventilated walls with good high-resin paint), The Bathroom Ceiling Secret: 1/2" Interior Soffit Board (Sag-Resistant), Best Value for Speed & Zero-Fail Waterproofing behind tile: 1/2" Polyisocyanurate Foam Board (Johns Manville GoBoard), Places where 5/8" may still make sense: floor to floor ceilings (Type X), garage walls (5/8" AR Type X). Apparently the resonant frequency of 1/2" Type C drywall is one of the more ideal for household noises (being higher than the others)
- Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above the walking surface probably). Around the mudroom we want highest abuse resistant with something like wainscot (shiplap there carries the idea already, can be improved further possibly like LP Smartside). Some walls likely worth abuse resistance on a side: W-M-WELL, W-M-HS2/HS3/HS4, W-M-BAE, W-M-C1/C2/C3 and walls facing RM-S-HALLWAY and next to stair landings. A reviewer also said that we should focus STC drywall/framing upgrades strictly for the solid walls without undercut doors (as they say doors bypass sound so much they make upgrades not worth the price, although doors that are weatherstripped, solid, and with no undercut do have better STC), based on this we can perhaps remove resilient channel assemblies from W-S-SBS and W-S-BW1/BW2/BW3
- Open (drywall overhaul): kids' bedroom and kids' room hall faces are NOT on the abuse-resistant swap list; decide whether they take `gwb-ar` (the owner's list omits them).
- Open (drywall overhaul): mudroom wainscot could be LP SmartSide 38 Series 7/16" (sidings used indoors) instead of the shiplap; the shiplap stays until someone prices it.
- Check whether `RF-BW-CANOPY`'s 190 plf and `RF-GARAGE`'s 167.5 plf diaphragm rows already carry SDPWS-2015 Table 4.2A's specific-gravity factor (0.92) for their SPF trusses; neither source string says so
- D-M-STUDY for the small study booth might make more sense as a bifold glass door, or some sort of tracked panel door. A simpler option is probably to just make sure the hinge can open to close to 180 degrees so the door can be flat against the wall, out of the way of the walking space.
- Gold foil trim or panel accent somewhere
- Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible). Also attic rail, bracket 7 needs a rethink, ideally to an off the shelf part.
- The study light switch ED-A-STUDY-SW (x=260⅜", 48" up) now sits under the east casing leg, and haus check flags it as an advisory. It needs to move (perhaps to the bottom of the stairs and against the centerline wall)
- ED-M-PORCH-FLOOD: shielded adjustable 60° flood beneath the balcony front, aimed into the sunken garden; shared 3D geometry in viewer/GLB/IFC. However it seems to be a recessed light, not one that is angled at the sunken garden.
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Sconce ED-S-STUDY2-STAIR-SC1 is a bit close to the floor, perhaps it should go at the top of the stairs on the wall, still on the same circuit but in the room above?
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- Flashing geometry and visibility implemented 2026-10-15: west-draining fitted cap on SB-BW-BAND's exposed 2×6 sill above W-BW-SCREEN; metal heads and concealed perimeter/sill flashing at exterior windows and doors; one Flashing 3D hide/isolate control. [Modeling basis and limits](../houses/catlin/notes/flashing_model.md).
- Possibly swap the concrete canopy stairway (SL-BW-TIER*) to pressure treated wood and composite treads or with brick stairs.
- W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_garage_diaphragm.md`'s 'garage takes the whole load'.
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- Window/door quotes (products named 2026-10-21): get Drutex (DAKAM, Chicago), Andersen 400 and Cascadia quotes and close `notes/window_and_door_procurement.md` §2.6 — Alucover nail fin + NAFS DP, the 14" tilt-only minimum, Drutex sill rail height (re-strike the 2.953" stools), Andersen triple-pane in MN and frame depth, the Cascadia double-door NFRC label and thresholds, dark-colour warranties.
- [ ] Before fabricating RM-M-STUDY: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking connections, and record any dimensional changes in the bench spec.
- Plant room needs review on bottom of wall detail (switch to a flash cove capable vinyl?) and also a review on if plumbing or drainage is present.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Window bottoms in 3D: the cause (stool top coplanar with a frame drawn 5.44" deep) is fixed in engine and viewer (geometry review O4-001); confirm by eye in the viewer, then delete this line.
- Geometry & dimensional-accuracy review 2026-10-31 done: [report](geometry-review/REPORT.md) (244 findings; ~84 fixed). Open escalations, ranked (detail in `geometry-review/adjudicated/`):
  - [ ] Follow-ups from closing items 1-7: A-592 (now `TR-CATLIN-RAKE`) has no rake recipe, so no Image II / 52126XX leaders; A-105 roof outline/ridge/eave strings (D1-004's roof-plan part, `roofplan.py`); the FULL set's G-001 index still overflows on ledger (44 unlisted); `D-B-PATIO` band header: bearing under the stacked D-S-DECK-E/D-M-BALC jamb packs is ungraded and the LVL plies' attachment to the edge I-joist (filler/backer) isn't modelled (`notes/patio_band_header.md` §4); library panel widths 20" vs Square D's 14.25"; `CD-B-ATTIC-RISER` clears `DU-ERV-RISER-SUP` by ~0.01" (moving the riser breaks its pull chain into `CD-A-PV-EAST`).
  - [ ] Garage sill 3 5/8" of 5 1/2" on the ICF core (C3-E8).
  - [ ] RF-HOUSE birdsmouth notches the TJI 230 flange (C3-E5).
  - [ ] HU28-2Z on a single 2x8 -> LUS28Z (C3-E11).
  - [ ] Canopy truss bearing 2 3/4", heel lift, north-entry seat-beam hangers and shim pack (C3-E6/E7/E12-E14).
  - [ ] C3-E3 follow-up: the three exterior doors (D-M-ENTRY, D-M-BALC, D-S-DECK-E) keep their RO base on the joist top, 3/4" under the subfloor the walls now stand on (decision #110); their sill pans, thresholds and landings are coordinated off that datum, and moving D-S-DECK-E onto the subfloor broke its catalog installation (6 FAILs). Owner: confirm the subfloor is cut back for each sill, or re-derive the three installations off the subfloor.
- Left open by the 2026-11-01 fit and product-data pass (REPORT items 14-24; plan `make-a-plan-to-warm-otter`):
  - [ ] ERV OA/EA/RET still leave the case at service level: under Broan's 2x2 port grid they cannot all reach the two basement plenums in 21.3" of headroom (8" ducts at 12" wrapped OD, OA/EA wraps overlap 2 1/4"). Owner held it; options are rearranging the plenums or moving the ERV (C6-E1). `erv_static_budget` stays 0.441" > 0.4".
  - [ ] 13 drain fixtures have no 3D vent (`mep.trap_arm_developed` ADVISORY worklist): basement bath WC/sauna, BATH2 WC/SH/TUB/laundry, hall-bath WC/SH, suite WC/LAV/TUBSH, attic SH. Owner: plumber-led layout pass, wet or individual vents case by case. Before switching it to the CODE `mep.trap_arm_length`, grade UPC 908's wet-vent limits in `checks/mep/trap_arm.py` (C6-E7).
  - [ ] TB-SG-W1/E1 closure boards are 8" while FT-B-S2/S3 are now 10": 2" x 32" of strip faces the court footing with no board. Extend to 10" (moves §11l and test_thermal_break) or accept.
  - [ ] Doorway transitions: D-A-STUDY / D-A-POCKET open onto unfinished subfloor (`compatible_finish_pairs` can't name it); D-M-MECH's floor varies across its doorway.
  - [ ] Leader straps bill twice: `CN-A-LEADER-*` (SS316 standoff strap #13, sized for the old 4" round) and the leader's 58110XX. Pick one product for the 4x3 1/2 leader on the ribbed panel.
  - [ ] `plan/wind_clamps.py` CN-G-WIND-RFSW/SE-1..3 sit over the canopy but name RF-GARAGE, 8.4" off the canopy's seams since the seam register.
  - [ ] 13 wall-light types state no `LuminaireType.canopy` (one combined `electrical.canopy_covers_box` UNKNOWN).
  - [ ] No check grades a run passing through a room's `ceiling_lining` layers (found at the sauna; design: `mep.run_in_ceiling_lining`, runs below the FURRING cavity bottom FAIL, terminal drops exempt, ~60 lines reusing `routing_ceiling._segment_rows`); no check grades a backing band's face against its body's side; BK-M-HS1-BASIN overlaps BK-M-HS1-GRAB.
  - [ ] Window stools pass through the buck jambs (`framing|window_stool`, 34 pairs): notch in `geometry_millwork.window_stool_ring`. ST-G-SERVICE riser-004 overlaps D-G-SERVICE's sill support (90 cm3).
  - [ ] FB-B-CS bedding's drain-tile ring (CFB011AAAA-DT-00/02) runs under FT-B-S2/S3 to y=0: 1" clear before, 1" into them since S2/S3 went to 10" (`drain_tile|footing`, blessed as known). Clip a bedding ring at adjacent footing faces in `resolve/drain_tile.py`.
  - [ ] `notes/garage_service_door_outswing.md` §2 pivot-inset table is the 90° sweep; at the 81° stop the insets read 0 → −0.114 (ties), 0.5 → 0.381, 1 → 0.876, 2 → 1.366.
  - [ ] BATH2 surround backer: the wall layer is `gwb-mr`; `notes/bath2_shower.md` §6 specifies glass-mat.
  - [ ] Over 500 lines: `resolve/framing/furring.py` (706), `checks/code/mn_residential/stairs.py` (522).
- Supplier holds from the same pass:
  - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 1" short of the Transition Trim seat; a stock gable end closure for the 7" cover; Profile Vent width; a 4x3 1/2-to-4" round adapter.
  - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). MMI: Z0364688R sill crest (ST-G-SERVICE tops at the +1.5" envelope).
  - Murphy Door: the custom 32 x 82 RO flush-mount (FF datum, body 28 3/4 x 78 1/2 x 8 1/4, casing 36 1/2, passage 24 1/4, price/lead time).
  - **Engineer hold, 14" north-entry pier cage (C3-E21):** PT-BW-W/-GW and PT-BW-PE/-PNE (`PIER_CONCRETE_14`, (4) #5) are 0.806% of gross, under ACI 318-19 §10.6.1.1's 1%; met only on §10.3.1.2's reduced area (0.770 in2 on 76.97 in2). EOR to confirm the basis or go to (6) #5. `notes/north_entry_piers.md` §13.
  - Broan: the derived 9 3/4" port 3-4 spacing; 8" flex on those centres. Weyerhaeuser: TJI 230 row assumes a glue-nailed subfloor. BuildBlock: BB600 course height vs the 64" stem.
  - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/8" pad. WAC Roland on a flat 753 cover; DVFR1W trim stand-off. Bypass/bifold 1/2" head allowance.
  - Plumber: the attic WC's 1 1/2" vent (UPC 904.1); basement WC re-route under the slab to W-B-BA-E; moving BATH2's supplies and PR-B-HW-TRUNK for a vent lane; a hall-bath WC vent in exterior W-S-W1.
- Generally our goal is to have every piece of the house linked to a named product (or a standard or commodity size, like a 2x4) so we can confirm every piece fits together correctly.
- Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger revision, clip/washer and rail access, full hose stroke, cleanout clearance, vent fitting/bore envelopes and the inward tilt-turn window sweep (full turn likely obstructed). See houses/catlin/notes/kitchen_sink_installation.md; product/connection specification is complete, physical fit is not released.
- Can we widen D-M-BATH2 to 36"? Not sure if/how the casing would work as that puts it into the shower area (the casing).
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- Check the basement stair carpet, and swap the carpet from the theater with an partial coverage area rug in the theater (technically not installed with tack strips or glue)
- [ ] Before ordering LVP/pouring the cap: confirm Quincy Oak sample and local delivered quote, measure the installed plank and coating stack, and set the flush movement/edge joint from those samples.
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- D-B-PATIO: separate brick reveal, widened RO, 5-1/2 inch concrete seat, composite returns, and one blind curb-skin recess are modeled (XMN5 dropped 2026-11-01). Sill/approach/pan intersections pass; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete concrete reinforcement/development, support root and cross-bearer bearing, field membrane bonds, installed pan/sweep/hinge sections, and assembled-unit label/warranty evidence. Standard rainproofing only; drainage/sump back up the revised concrete curb. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- D-S-DECK-E: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards. BE365 adapter F is documented; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete house-root connections and cross-bearer bearing, installed pan/sweep/hinge sections and the flexible flashing-end application; confirm assembly dimensions/label/warranty. Complete preferred/Tru-Defense prices remain unavailable publicly. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- Research most commonly failed residential code items and make sure checks or tests exist for those here.
- Metal trim kit ([notes/metal_trim_kit.md](../houses/catlin/notes/metal_trim_kit.md)): the garage soffit's net free area is still unauthored; authoring it would give R806.2 real margin through the 1/300 balanced route.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- Add the eased edges and rounded corners to the shown tabletop model.
- Look up a guide to how plumbers and such route, then make sure the autorouter follows that, and also code for it
- Plant supply fabrication hold: dry-fit A220V / ZD12X6TZ / TH-HP-PLANT-BOOT-01 and gasketed
  service hatch, including actuator fasteners, hand/tool access, seams/supports and the
  approximately 3/8-inch deck margin. Geometry and connection are specified; see
  houses/catlin/notes/plant_supply_connection.md.
- Air-distribution products (specified 2026-10-31, [note](../houses/catlin/notes/air_distribution_products.md)); still open:
  - Owner: trimless for RM-M-LIVING / RM-M-BED / the stair hall (note §12), and whether "the heat pump over the stairway" includes the 28x12 return.
  - Owner: the 1.1 cfm residual under 205, or the 10" hoods (needs RenewAire FA10 test data and a plate fit check) — `notes/erv_static_budget.md` §10.4, §10.6.
  - Owner/AHJ: which floor area MN 1322 R403.5 means. The engine grades finish-face room area (195 cfm required); centreline gave 205, exterior dimensions give 214, past the 210 cfm machine — `notes/erv_static_budget.md` §10.6.
  - Supplier confirmations: Vents-US AM 100/125 loss curves; FA8 plate and projection; floor-boot and Snappy P13-204 heights; motorised damper body and actuator sizes; H&C 531SA 6x12 face; a 125 mm retail valve; prices marked "not read" in `prices.toml`.
  - Engine, deferred: an insulation-vs-R403.2.1 check; per-segment duct insulation; M1506.3's 3 ft exception and the operable-opening distance; checking an insulation spec's thickness against its R-value; grading a damper actuator inside a duct.
- Consider have the oven/range in the kitchen island across from the sink
- Consider making W-M-BATH1-W operable. Switch that small operable window type we have to the Aluprof MB-Slimline / MB-79N CSF or Aliplast Max Light Modern ultra slim aluminum for maximum light area (looks like around 2.75" frame is possible there) triple glazed.
- [x] Roof sheathing: 19/32" 40/20 plywood, CDX house and Structural I garage/canopy. [Assessment](../houses/catlin/notes/roof_sheathing_and_membranes.md): Image II acceptance, eave cantilevers, narrow/single-span panels and 24-1/8" transition engineering remain open.
- [x] Roof membranes at installed thickness, near-black under Flashing: house butyl 30 mil, garage/canopy HT rubberized asphalt 40 mil. House unvented/full-coverage product confirmation remains open; see the roof assessment.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
  - Confirm strip-in width (provisional 9") with GCP, and Image II + deck + membrane acceptance with Metal Sales; deck bearing is 2.036" vs 2" min, provisional.
  - Build a physical mock-up (two panels, wall rib/closure, membrane, gutter, two supports, a corner).
- [x] Compared 5/8" AdvanTech roof sheathing; retain plywood. Reconsider as a construction-moisture upgrade after local quotes and product/connection review; see the roof assessment.
- Consider 1/2" advantech for walls sheathing
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- Pick a soffit product and close the garage attic ventilation grading, and the corrugated soffit to sill junction detailed. Also fix the garage soffit end detail (north and south gable ends) where the sofit is too flat and isn't inline with the roof slope there
- [x] SL-SG-STAIRPAD matches SL-WK-D at −2′-9″ finished height.
- D-B-PATIO has too short a threshold, it needs to go out over the foam gap. And it has some weird top flashing that isn't needed here it seems.
- D-B-PATIO has an STHD14 connector sprouting up in the middle.
- Might be worth writing up ICF in cost options as an alternative exterior wall setup (for the house) something like the Quadlock 'plus' form which with 4.25" of EPS on each side delivers R-38.
- Fixture connections (audit 2026-10-30): every fixture and appliance now declares ports and
  `mep.fixture_port_connection` grades them (`--only all`). Still open:
  - Datasheets that would make the APPROXIMATE stations EXACT: Delta R10000-UNBX inlet spacing
    and height, the TOTO supply inlets, LG WashTower and LDTS5552 connection stations and hose
    lengths, Glacier Bay QL033Y, Kohler Chulton, SUNNERSTA, Moen 4794 stub depth. The washer's
    real valves are mid-run tees, which the endpoint grade cannot see.
- Make sure sizing and dimensions and placement are correct for junction boxes (ie for LED power supplies), with specified product.
- Double check the calculations for accuracy of BTU heating and cooling load.
- Rainscreen closures (2026-10-29): close the supplier questions in `houses/catlin/notes/metal_trim_kit.md` "Open with suppliers" (Metal Sales x4, the membrane maker, the screen supplier). The panel bottoms are still drawn to the seat, not on the raised strip (in `resolve/board_batten.py`), and so are the wide outside corners (`cladding_trim/mixed_corners.py`, off the same layer band): both pass through the raised trim foot and the base strip, and `integrity.rainscreen_cavity` cannot see a panel surface, so it grades the slot open regardless. At the four outside corners the base and band strips also run into the corner trim and the adjoining wall's base trim; stop them at the corner once the corners land on the trim.
- Make sure sealed cut ends are specified in instructions for KDAT usage
- Make sure the railing and guard rail assembly is correctly modeled (especially how they are mounted). `ST-SG-PORCH`'s raked guard posts are drawn at the path ends and middle, all on riser lines (the plan wanted them on treads): the foot base straddles the lowest riser, the head post is centred on W-SG-E1's east face, and the head posts overlap `RL-SG-PTHRESH-S/N`'s end posts by 1/4" (centres 2 3/4" apart). Decide where each cast base lands (one shared base at the head; two posts would stop `RL-SG-PSTAIR-HR` short of the end risers). `code.R311_7_1_stair_width` now reads every guard's posts over a flight (fascia ones once they state `fascia_face_offset`); see the next item.
- **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimmer pack (19'-0 1/8"..20'-0", south of the well edge), and `RL-A-STAIR`'s surface posts (since 2026-10-31) stand ~1 1/8" south of its bracket line: the junction needs detailing, and the surface bases need blocking under the pack (4 GRK RSS, SG >= 0.50).
- **SL-M-DECK end bearing (decision #107).** It bears 6" on `W-B-E1`/`-E2` and `W-B-CS2`/`-CN`. Its rib bars hook 180° into both bearings and a bond break goes on the LSL rim (2026-10-31, `houses/catlin/notes/rebar_layout_basis.md` §5). No hook develops fy at the face in 6": ldh 14.77" against 5.25". ACI 318-19 §9.8.1.6's joist integrity bar is still unmet, needing about 15 1/2" of bearing or the bar carried into the support. Get BuildDeck's end-bearing detail and author it as `published_span.min_bearing_in` plus the bar ends. Nothing in the engine grades bar development at a slab support.
- Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing and subfloor nailing, fascia/trim screws, window-install screws, and the HL angles' site-length through-bolts. Open: a Metal Sales price for 8243100.
- Smart home (`houses/catlin/notes/smart_home.md`), still to verify:
  - Schluter's written answer on whether the heating-cable warranty survives the Warmup 7iE stats.
  - Pair one Gree head (Sys 2/3) with HA's `gree` integration first: GCM-encrypted firmware may not pair (fallback is the RS485 wired controller).
  - Bench one Aqara W200 on EQ-S-HP1-AH: aux staging and what HA actually exposes.
  - Sense Pro trim: Century is bundle-only. Match the 622 escutcheon to the Latitude lever.
- Backup battery, still open (`houses/catlin/notes/backup_power.md` §10-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; whether the 12kPV's load port backs up from PV alone with no battery (ask EG4); declare future storage on the Xcel application; DSI's position on a UL 9540 3rd-ed. DC ESS battery; a freeze drain-down plan; a small LFP UPS for Home Assistant, the router and the leak valve. Model the V2H rough-in — a 1 1/2" spare and a 1" data conduit panel-to-garage beside `CD-B-GARAGE`, a reserved 2-pole space, wall room by the meter — as its own routing pass. The one-battery always-on tier is a ~32 h countdown, not a steady state (§6): decide between more array, a second battery, or a leaner always-on tier.
- Let's make sure all the charcoal gray and black details of the house exterior (various metal trim, window frames, foundation insulation cover) show real manufacturer colors. We are using this to determine if we should switch all to more gray or more black.
- `haus print3d --colour-groups`: per-piece colour components bucketed from `Material.color`, matched to a sample exported from Bambu Studio before shipping.
- Check the door handle specification, interior doors. Make sure bathroom doors are simple locks.
- Do an outlet and light switch placement review pass
- Trim bbd-transition-trim still isn't showing the white color for some reason in the 3d viewer, despite being named as such already.
- O-S-VANITY and D-S-STUDY2, both openings (not true doors) seem to get ignored, improperly showing baseboard, sill plates, and non-continuous flooring, they likely just need to reuse some of the existing door handling logic which generally works
- Edit the door swing icon in 2d so it shows a frame (right now the 2d door swing might be a bit too big, versus actual leaf swing)
- Make SL-M-DECK a wood joist design, removing the concrete deck and the concrete centerline wall. Use open web trusses (not I joists) perhaps at tighter OC for extra strength (and maybe ask for a 60 psf or 100 psf truss design, if that is easy to source) to support large format tile well. Make sure the joists are anchored properly using simpson connectors to the concrete. The structural concrete (BuildDeck) is kept in the library but retired from use.
- Acoustics for the theater ceiling: resilient channels (1" or 1 1/8" screws to avoid short circuiting into the wood). Painter's caulk in gap between ceiling and walls. No ceiling lights.
- Aiming to keep floor transitions flush, looks like ~3/4" thickness makes this easiest. Ditra XL or Ditra Heat + Thinset + 8 mm Tile (Ditra Heat PS 5.5 mm + 3.5 mm thinset (3/8" by 3/8" notch trowel) + 10 mm tile OR Ditra Heat Duo peel and stick (PS) + 2.5 mm thinset (1/4" x 3/8" trowel) + 9 mm tile OR 1.5 mm thinset (compressed by 1/4" by 1/4" trowel) + ditra heat 5.5 mm + 2.5 mm thinset + 9.5 mm tile) == 1/2" plywood (nominal) + 7 mm LVP == 1/2" exacor (12 mm actual) + 7 mm LVP == 1/2" gypsum underlayment (fiberrock) + 6.5 mm LVP == 5/8" actual (Fiberock) underlayment + 3 mm sheet vinyl == 16 mm exacor + feather finish + 2.8 to 3 mm sheet vinyl == 3/4" hardwood ~= 7/16" pad + 1/2" pile carpet (carpet squishes at edges)
- Delete the shower blow dryer fan from RM-M-BATH2 (but keep in library)
- Specify paint in detail
- Specify leak detectors, in useful places, linked to Home Assitant
- REG-S-EXH3-NECK is on the floor right in front of the sink. Seams a great way to suck water into the ERV system. Probably better if that was moved.

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

- [ ] Confirm Image II eave rib-end treatment: installation guide pp. 20–22 calls for sealant or field-closed rib ends; current hot-roof design keeps rib ends open without a vent closure.
