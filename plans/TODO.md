# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs. Revit/SketchUp import-readiness research, fixes, and open items: `plans/revit-sketchup-readiness.md`.

Sourcing quotes, construction todo doesn't belong in this document, this is just softwared and house design todo.
We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
Our general goals are decent longevity and quality at a reasonable price, avoiding premium items unless clearly a major improvement for our needs.

## Needs your decision

## Remaining Work

- **Owner call: `PR-M-DRYER-COND` could retire.** It is now one stock 90 in 3/4" PVC (graded).
  LG's drain-hose connector into `PR-M-WASH-STANDPIPE` would replace the run outright.

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

- **HPWH clearances (owner call).** `EQ-B-WH` is now the Rheem RH400-30 non-ducted unit, 24 1/4"
  round x 76 13/16" (`notes/water_service.md`). Its air exhaust faces the east wall at 0" against
  Rheem's 6" for a non-ducted unit (ducting is ruled out: 91" + 6" top clearance is 0.06" over the
  ceiling), and the 24.25" tank laps the hung ERV case by 0.155" in a 24.095" slot.
- **Determine basement backwater protection before under-slab rough-in.** Add the next
  upstream manhole-cover elevation on the survey datum, compare it with basement fixture
  floors under UPC 710.1, and protect only affected low branches if required. The existing
  sewer-permit task records invert, not cover elevation. [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- **Water-heater thermal expansion: ask SPRWS** (Engineering 651-266-6270) whether the meter set
  carries a check valve and what the static pressure at the main is. Then model a listed expansion
  tank on the heater inlet (and a PRV over 80 psi). Also settle the hydrant branch order: if
  `PA-G-HYD-BFP` stays in series on `PR-B-CW-TRUNK`, the house is closed regardless and the 3/4"
  device throttles a 1 1/4" trunk. `notes/water_service.md` §4.

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
- **Sauna vents: confirm the Finnmark 713H ships to the US** (UK retailer, GBP 25.99) or name a
  US-sold closeable wood vent with a 100 mm collar; `PROD-FINNMARK-SAUNA-VENT-100`.
- **`mep.run_in_finished_volume`'s terminal grace is blind to leg length** (decision #94): a
  fixture's whole first or last leg is excused however far it runs. Measure what tightening it
  raises before deciding.
- **Seven runs in `RM-A-STUDIO`'s west eave are ungraded, and named in an UNKNOWN** (#94: under
  5'-0" of head is not graded, but there are no knee walls, so it is finished room).
  `PR-A-STUBATH-LAV-ARM`/`-CW`/`-HW` jog 1"-3" proud of `W-A-STU-W`'s studio face at 19"-32" AFF
  to pass `DU-A-ERV-R-STUBATH`'s riser in that cavity: exposed pipe, box it or reroute.
  `DU-A-ERV-R-ATTIC`/`-BED3`/`-STUBATH` and `DU-S-ERV-HP-FEED` ride the "boxed floor chase"
  `mep_erv_l1.py` declares and nothing models: author it (a Soffit) so the check can see it.
- **Router port stub is unpriced** (decision #95): its length and bend are not in a proposal's
  cost terms, and the 2" fitting allowance is a stated value, not a datasheet one.
- **`test_routing_perf_guard` (slow) is red at HEAD**: `DU-B-ERV-R-SAUNA-SUP` nominates 376,101
  lattice nodes against the 350,000 cap (measured 2026-10-29 on the committed tree).

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
- The study light switch ED-A-STUDY-SW (x=260⅜", 48" up) now sits under the east casing leg, and haus check flags it as an advisory. It needs to move (perhaps to the bottom of the stairs and against the centerline wall)
- ED-M-PORCH-FLOOD: shielded adjustable 60° flood beneath the balcony front, aimed into the sunken garden; shared 3D geometry in viewer/GLB/IFC. However it seems to be a recessed light, not one that is angled at the sunken garden.
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Sconce ED-S-STUDY2-STAIR-SC1 is a bit close to the floor, perhaps it should go at the top of the stairs on the wall, still on the same circuit but in the room above?
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- Flashing geometry and visibility implemented 2026-10-15: west-draining fitted cap on SB-BW-BAND's exposed 2×6 sill above W-BW-SCREEN; metal heads and concealed perimeter/sill flashing at exterior windows and doors; one Flashing 3D hide/isolate control. [Modeling basis and limits](../houses/catlin/notes/flashing_model.md).
- Possibly swap the concrete canopy stairway (SL-BW-TIER*) to pressure treated wood and composite treads or with brick stairs.
- W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_garage_diaphragm.md`'s 'garage takes the whole load'.
- Make the countertop (and quartz window stools) a "ready to send to manufacturer" design and export. Include rounding corners
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- Window/door quotes (products named 2026-10-21): get Drutex (DAKAM, Chicago), Andersen 400 and Cascadia quotes and close `notes/window_and_door_procurement.md` §2.6 — Alucover nail fin + NAFS DP, the 14" tilt-only minimum, Drutex sill rail height (re-strike the 2.953" stools), Andersen triple-pane in MN and frame depth, the Cascadia double-door NFRC label and thresholds, dark-colour warranties.
- [ ] Before fabricating RM-M-STUDY: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking connections, and record any dimensional changes in the bench spec.
- Plant room needs review on bottom of wall detail (switch to a flash cove capable vinyl?) and also a review on if plumbing or drainage is present.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- The bottoms of 3d modeled windows are a bit glitchy in 3d movement.
- Do passes to confirm geometry and dimensions of select products all align together correctly for real world build dimensions. Major items to check: stairs, doors and windows (and their trim/flashing), framing, cabinets, trusses.
- Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger revision, clip/washer and rail access, full hose stroke, cleanout clearance, vent fitting/bore envelopes and the inward tilt-turn window sweep (full turn likely obstructed). See houses/catlin/notes/kitchen_sink_installation.md; product/connection specification is complete, physical fit is not released.
- Lets get the BOM showing all IKEA SEKTION parts needed (knobs, scribes, hinges, feet, etc), and soft close pieces too.
- Can we widen D-M-BATH2 to 36"? Not sure if/how the casing would work as that puts it into the shower area (the casing).
- A couple of options to reduce echo in the gym. One is swapping drywall for drop ceiling tile framing (perhaps with some fiberglass in the cavity above). Another was vulcanized recycled crumb-rubber rolls or 4'x6' stall mats for the floor. A third was W-B-CE losing its south side drywall and having fabric plus simple wood slats (ie 1x2 finger jointed pine) as an effectively slat wall arrangement.
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- [x] Model a coffee machine and kettle — SEVERIN WK 3422 and Arctic White De’Longhi Rivelia EXAM44055W on the north kitchen counter (2026-10-25); see DESIGN-LOG for the accepted overhead-clearance shortfall.
- Check the basement stair carpet, and swap the carpet from the theater with an partial coverage area rug in the theater (technically not installed with tack strips or glue)
- [ ] Before ordering LVP/pouring the cap: confirm Quincy Oak sample and local delivered quote, measure the installed plank and coating stack, and set the flush movement/edge joint from those samples.
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- Basement surface wiring open items ([note](../houses/catlin/notes/basement_surface_wiring.md#open-items)): the six PLAY-N sconce canopies must cover a 4" square surface box; ED-B-SPA-RC (outdoors, sunken garden) wants a weatherproof box and in-use cover; confirm RACO 809C and the 3-1/4" flush box depth.
- D-B-PATIO: separate brick reveal, widened RO, 5-1/2 inch concrete seat, composite returns, one blind curb-skin recess and XMN5 sill extension are modeled. Sill/approach/pan intersections pass; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete concrete reinforcement/development, support root and cross-bearer bearing, field membrane bonds, installed pan/sweep/hinge sections, and assembled-unit label/warranty evidence. Standard rainproofing only; drainage/sump back up the revised concrete curb. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- D-S-DECK-E: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards. BE365 adapter F is documented; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete house-root connections and cross-bearer bearing, installed pan/sweep/hinge sections and the flexible flashing-end application; confirm assembly dimensions/label/warranty. Complete preferred/Tru-Defense prices remain unavailable publicly. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- Research most commonly failed residential code items and make sure checks or tests exist for those here.
- Metal trim kit ([notes/metal_trim_kit.md](../houses/catlin/notes/metal_trim_kit.md)): supplier confirmation only: the 13 in step cover part number and the Cobra vented closure's net free area. R806.2 also needs the garage soffit's net free area, which is not authored; until then `code.R806_2_attic_ventilation` stays UNKNOWN for the garage.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- Add the eased edges and rounded corners to the shown tabletop model.
- D-B-PATIO has a MASA connector sprouting up in the middle, plus it's got some sort of awkward trim around the brick veneer (the brick IS the trim there, the door itself has a more utilitarian trim into the main house wall behind). Looks like previous door work accidentally bumped the brick arch up too high. It should partially obscure the door top.
- Look up a guide to how plumbers and such route, then make sure the autorouter follows that, and also code for it
- Specify the products for the ducts and duct vents
- Consider have the oven/range in the kitchen island across from the sink
- Consider making W-M-BATH1-W operable. Switch that small operable window type we have to the Aluprof MB-Slimline / MB-79N CSF or Aliplast Max Light Modern ultra slim aluminum for maximum light area (looks like around 2.75" frame is possible there) triple glazed.
- Possibly poplar 1x12 as stair skirt boards, if not already specified, painted white. Likely installed tight to wall framing/drywall prior to installation of finish treads and risers.
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
- Probably around the windows, the flashing should come out and over the girts (covering the buck and girt then) that box in the window. ccspf should come out and around the outie buck as well up to the girt there. That would bury the KDAT girt completely in foam and flashing. Perhaps instead the gap should remain on the back of the girt, but the full outer face and top and bottom is flashed (just back clear to dry backwards into cavity?)
- Make door and window pieces (trim, jamb, etc) selectable in the UI as separate pieces (but all still hidden by the same view toggle). Such pieces should have their product name shown in the UI when selected. Generally something like the drip edge should be one piece (even if multiple faces) so the garage drip edge at the eaves is something that has gone too far in being split out, and gutters are another thing where the back, bottom and front should all be shown as one piece.
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- Pick a soffit product and close the garage attic ventilation grading, and the corrugated soffit to sill junction detailed. Also fix the garage soffit end detail (north and south gable ends) where the sofit is too flat and isn't inline with the roof slope there
- SL-SG-STAIRPAD is a slightly different finished height than SL-WK-D. They should have the same finished height.
- D-B-PATIO has too short a threshold, it needs to go out over the foam gap. And it has some weird top flashing that isn't needed here it seems.
- Might be worth writing up ICF in cost options as an alternative exterior wall setup (for the house) something like the Quadlock 'plus' form which with 4.25" of EPS on each side delivers R-38.
- Check the modeling of the baseboard/tile surround in tile rooms. Is it fully and correctly detailed?
- Properly model the drywall channels used (ie corners, and especially for the LED light strips)
- Make sure the plumbing matches fixtures to their right locations on their connections
- Make sure sizing and dimensions and placement are correct for junction boxes (ie for LED power supplies), with specified product.
- Double check the calculations for accuracy of BTU heating and cooling load.
- Rainscreen closures (2026-10-29): close the supplier questions in `houses/catlin/notes/metal_trim_kit.md` "Open with suppliers" (Metal Sales x4, the membrane maker, the screen supplier) and the owner's EPDM-pads-vs-painted call. The panel bottoms are still drawn to the seat, not on the raised strip.
- Make sure sealed cut ends are specified in instructions for KDAT usage
- Review the pantry shelving, we want something easy to construct (alongside our custom glue up panels), strong, and with good lighting
- Make sure the railing and guard rail products are named when clicked on in the UI, and that the assembly of them is correctly modeled (especially how they are mounted)
- Let's try to get modeled numbers in the BOM for fasteners, where not already. Our primary concern are on the 'special' or 'upgrade' types of fasteners (ie stainless steel, ringshank, galvanized, etc) so contractors are told exactly what to quote (we don't want to get accidentally cheaped out on these), but we don't need to truly model every screw and nail.
- Generally our goal is to have every piece of the house linked to a named product (or a standard or commodity size, like a 2x4) so we can confirm every piece fits together correctly.
- Ceiling mounted curtain rods for the living room and main floor master bedroom. This was given as an example https://www.amazon.com/dp/B0FW4XVJ84 (aluminum white ceiling track, probably just a single track needed), which might need. Thes goal is a more 'hidden track' (but not likely actually recessed, just slim in the ceiling with the curtain itself up a around it a bit). The curtains can be used alongside cellular shades. The general goal is to use standard (ie fairly cheap) curtain materials and curtain tracks, in such a way to keep the air stagnate when curtains are closed to improve the insulation value.
- We might want motorized cellular blinds in some of the upstairs south facing windows that don't have an overhang. Probably the battery with solar panel kind and either matter or zigbee control.
- Make sure our entire smart home setup is Home Assistant friendly, with no corporate cloud required to run it (a brief cloud connection for setup is fine, just not deployed).
- We likely won't be getting a home backup battery when we first power the house (too expensive alongside everything else) but we will have solar and we want it easy to add a battery (possibly using an EV as the backup battery, that is becoming more common, but ideally specified in a way that might work with various brands of car in the future, not just one short term supported product). Separately, home assistant (likely hardwired LAN into the main router) and the router are probably on a smaller more standard computer backup battery. With all of these things, our main goal is being able to make sure the batteries never start on fire, and if they do start on fire, that the fire is contained in a manageable area.
- Possibly the ESS closet can just be wood studs (metal studs seeming silly as an extra spec for just a small amount) with a Fire-Retardant Spray over the studs.
- Let's do a pass to remove any pricing allowances that might be removed by directly modeled parts.
- Let's use haiku subagents to hunt for items that look to be overpriced, either due to bad estimates or bad product choices (some items were the "only one that fit all criteria" when in reality we could have loosened one criteria and got a much cheaper, almost as good solution)

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
