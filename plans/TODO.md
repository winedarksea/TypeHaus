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
- **Cotton Oak LVP (Karndean AKP-RL38):** get a local quote (the `lvp` row in `prices.toml` is
  still Quincy's placeholder) and check a sample in the house light against the model's
  `#d6cebb` (`houses/catlin/notes/lvp_flooring.md`).
- **D-G-SERVICE swing limited by W-BW-SCREEN after the canopy-beam move — owner to revisit (slide door, rebuild screen face).** Stopped at 81° for now (`maximum_opening_degrees`): clear opening 24.3" vs 29.3" at 90°.

## Remaining Work

- **Blind ROs export as full-depth IFC voids** (`AO-BW-MDO-TIE-RELIEF`, `AO-M-FIRE-NICHE`,
  the hydrant bores): the elevation honours `depth_from` via `geometry_walls.cuts_layer`, the
  IFC void (`emit/ifc/architectural._opening_profile`) and its diff adapter do not.

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

- **Low-voltage devices still unmodelled:** the doorbell, both cameras, the leak probe and
  the lock exist (`plan/smart_home.py`); an outdoor weather station and any access reader
  do not, if wanted. Place them before drywall, on the AP rollout's pattern (type,
  placement, PoE budget re-check). -- DEFERRED

### MEP / lighting residuals

**The open MEP campaigns' live record is `houses/catlin/preferences.toml`**, not this file:
`mep.riser_through_deck` (undrawn holes) and the itemised web crossings, each with its count
and a dated note. `haus check houses/catlin --no-suppress` is the score with every
suppression lifted. (`mep.run_interference` closed 2026-10-08 and is ratcheted at zero.)

- **Lighting review confirms (2026-10-31, houses/catlin DESIGN-LOG "Lighting review").** Before
  ordering: SuperLightingLED RGB+CCT white-channel CRI and lm/ft, and 12 mm in the 5/8" reveal;
  the Fleurco MHAP4236's CRI (swap if under 90); the Soren 50910BK's UL damp label and box
  offset (P6, 2026-11-02); CentricHOME R9 (the 2026-11-02 sheet says > 80, not 90+) and
  enclosed/damp rating; Waveform tubes are Type B double-ended; GL-C-001P cold rating in the
  garage; power-on state of the D315S relays and the six-plus controllers; the Zigbee
  dongle; the Omvi 3i on HA's `reolink` integration (else RTSP/ONVIF); the TCL 98QM8L's VESA in its manual;
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
- **Confirm the delivered parts:** on the PROPH80 T0 RH120-MSO, the scaled T&P outlet (~46",
  front-left, under the ERV case's 54" bottom), the HydroBoost riser's projection (r ~15", 2 1/4"
  off `D-B-CLOSET`'s 75-degree sweep) and the cord's length (`notes/water_service.md` §1); and the
  ProSaunas vent hatch's cutout and free area (unpublished; (844) 565-1113).

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
  datasheet idle (<55 W standby) and 94% maximum efficiency; both flatter a ~250 W outage
  load. Measure islanded idle and low-load efficiency at commissioning, with the backup duty
  cycles and the 13 alarms' standby, and re-author them. See
  `houses/catlin/notes/backup_power.md` §6.

### Structural/framing residuals

- **Court stems as a two-way plate (owner option, 2026-11-02).** A screening PyNite MITC4 plate
  model (±5%) of W2/S/E2 with W1's braced top reads base moments 0.50–0.51× the cantilever
  `retaining_wall` grades, enough for `#5 @ 18"` (~295 lb HDG, $380–640 below today's
  `#5 @ 10"`). Waits on: an engine calc for a two-way wall (none exists), a PE, and the corner
  horizontals going borderline (0.148 vs 0.15 in²/ft) with a rotating footing. Free body §6c.

- **Four matchers share one arithmetic but still answer at three tolerances.**
  `platform._collinear_overlap`, `stacking._axis_match`, `construction_geometry._stack_overlap`
  and `layout_lines._collinear` all route through `layout_lines.collinear_overlap` since
  2026-09-20, so the arithmetic is written once. Unifying the TOLERANCES is not a mechanical
  edit: `layout_lines` measures on the datum face and `_axis_match` on the raw node axis, and
  they differ by 43.8mm (basement) / 57.0mm (garage) — 13 stack pairs stack in one pass and
  not the other (`W-B-S1`->`W-M-S1` + 8 garage walls). All under-framed-wall pours, so nothing
  reads the difference today. The two endpoint formulations differ too and are preserved
  behind `both_ends=`.

### Schema gaps found during selections/fireplace passes

- **No `Lintel` element type.** A `Beam` stands in, and its `size` is a free string.
- **R304.2's 7'-0" minimum room dimension is ungraded.** `code.R304_1_floor_area` and
  R305's sloped path grade area only, so a 3'-wide ribbon of floor would pass.
- **A `floor:ceiling_channel` rule adds no ceiling depth.** `RM-B-PLAY-N`'s resilient channel
  (`CR-PLAY-CEIL-RC`) bills LF only; the finished ceiling is ~1/2" lower than R305 and the
  register/ceiling-plane checks read (`houses/catlin/notes/theater_ceiling_acoustics.md`).
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
  which stands **2.375" south of that line** (cladding -7.25", brick -9.625" since 2026-11-04;
  the porch deck now stops on the brick's face). The two halves
  that were closed on 2026-09-20: `house_ext_layers_in` now derives from `_WALL_OUTBOARD_IN`
  (and `gap_to_house_in` absorbs the difference, so no geometry moved), and
  `code.R311_3_exterior_landing` can now union two abutting surfaces into one landing. What
  remains is the datum question itself, and it is an owner decision rather than a nudge:
  widening the gap back to a nominal 5" pushes the court 2.25" south and FAILs D-B-SUNKEN.
- Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space for a self emptying litter box.
- **A library catalog type cannot name a house-owned `Product`.** `ED-T-EV-1450` lives in
  `library/electrical.py` and the Leviton 1450R is authored in `houses/catlin/plan/products.py`,
  so the `product_ref` cannot be made: `houses/starter` would resolve it to nothing and take an
  `integrity.unknown_product_ref` ERROR. Same seam as the Bituthene selection. Needs a
  house-level catalog-override mechanism, or the type retagged house-local (which moves the
  `[placeables]` price key and four tests).
- **Plan lettering residue after 96b845f4 (3/32" lettering):** at 1/4" a few small rooms still
  touch a tag (PANTRY/D8, STUDY/D13, MECH's "CHASE TYP. OF 2"), and on the 11x17 reduced check
  print the 12 pt room names spill past small rooms' walls.
- The theater, RM-B-PLAY-N is specified as carpet, and should have a heating strip under the carpet near the sofa where feet are, likely just plugged in to a regular outlet
- Extra light switches by beds: done for RM-M-BED (J1 WAC Sprigs switch at the fixture) and RM-S-SUITE (2026-10-31); RM-S-BED1-3 still open.
- A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairwells. Some options: 1/2" Type C, Paper-Faced 1/2" AR (e.g., Gold Bond Hi-Abuse or USG Sheetrock AR), LP SmartSide 38 Series Panel 7/16" (Sidings Used Indoors), 1/2" MDF (4x8 Sheets with V-Groove or Batten Strips), 1/2" MDO (Medium Density Overlay) Plywood
- Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam or standard elastomeric latex caulk ), Best Seamless Durability Upgrade (~+$0.45/sq ft): 1/2" Paper-Faced Abuse-Resistant (AR) Drywall, Best "Skip-the-Taper" Durable Wall (~$1.30/sq ft material, $0 mudding): 4x8 Pre-Primed MDF Shiplap Panels (or LP SmartSide 38 Series), The Winner for General Bath Walls: 1/2" Mold-Resistant Paper-Faced Drywall ("Purple Board" / USG Mold Tough, although not strictly needed on well ventilated walls with good high-resin paint), The Bathroom Ceiling Secret: 1/2" Interior Soffit Board (Sag-Resistant), Best Value for Speed & Zero-Fail Waterproofing behind tile: 1/2" Polyisocyanurate Foam Board (Johns Manville GoBoard), Places where 5/8" may still make sense: floor to floor ceilings (Type X), garage walls (5/8" AR Type X). Apparently the resonant frequency of 1/2" Type C drywall is one of the more ideal for household noises (being higher than the others)
- Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above the walking surface probably). Around the mudroom we want highest abuse resistant with something like wainscot (shiplap there carries the idea already, can be improved further possibly like LP Smartside). Some walls likely worth abuse resistance on a side: W-M-WELL, W-M-HS2/HS3/HS4, W-M-BAE, W-M-C1/C2/C3 and walls facing RM-S-HALLWAY and next to stair landings. A reviewer also said that we should focus STC drywall/framing upgrades strictly for the solid walls without undercut doors (as they say doors bypass sound so much they make upgrades not worth the price, although doors that are weatherstripped, solid, and with no undercut do have better STC), based on this we can perhaps remove resilient channel assemblies from W-S-SBS and W-S-BW1/BW2/BW3
- Open (drywall overhaul): kids' bedroom and kids' room hall faces are NOT on the abuse-resistant swap list; decide whether they take `gwb-ar` (the owner's list omits them).
- Open (drywall overhaul): mudroom wainscot could be LP SmartSide 38 Series 7/16" (sidings used indoors) instead of the shiplap; the shiplap stays until someone prices it.
- Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible). Also attic rail, bracket 7 needs a rethink, ideally to an off the shelf part.
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_garage_diaphragm.md`'s 'garage takes the whole load'.
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- [ ] Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied cushion height, lumbar fit and bracket/blocking connections, and record any dimensional changes in the bench spec.
- Plant-room sink (replaces `PA-S-PLANT-WATER-STUB`): feasibility test reported 2026-11-03, awaiting the owner; `haus route --fixture` crashes on an empty goal set (`routing/gravity_search.py` `_heuristic`) when every tie on the suite stack is spaced out.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Window bottoms in 3D: fixed for every window but `WIN-B-SAUNA`, which has no resolved seat (its frame is drawn 80 mm on the axis, the stool assumes 93 mm; A-602 prints "UNRESOLVED"). Fix that pair, confirm by eye, then delete this line.
- Geometry review round 2 (2026-11-05): [report](geometry-review/REPORT.md) §1 ranks the open escalations; detail in `geometry-review/2026-11-04/adjudicated/C1..C5.md`. 0 FAIL kept. Open, by rank:
  - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply fastening, and the edge I-joist filler/backer connections (`notes/sunken_door_band_header.md` §4).
  - [ ] DuctStandard residual reads (decision #114, `houses/catlin/plan/ducts.py`): laying lengths of the Imperial reducers/increasers/spin collars, boot heights, a 4" collar damper with a locking quadrant, a retail 1" x 22 ga strap, Versa-Grip's metal-seam coverage (130 LF/tube is the bead rate), IMC 2018 §603.10 and Table 603.4 verbatim, a 6x6x6 tee and 8-to-4 reducer SKU (shop-made today). 20 attic/chase hangers have no framing within reach (`mep.duct_supports`): detail a saddle or trapeze. Broan's manual also says insulated ducts "must have the same diameter as the ports to ensure proper drainage" against its own 6-to-8 transition advice: ask Broan.
  - [ ] ERV OA/EA/RET hold (C4 E2/E9, C2 E13): EA and RET start on each other's Broan ports (cross-wired). Re-siting the EA riser does not close it (2026-11-05): OA/EA (12" wrapped) cannot cross under the joists, RET must cross to the south plenum under MAN-SUP's 10.4", and lowering the ERV is blocked by the condensate's ~3.8" of fall. The layout that closes it: rotate EQ-B-ERV to 270 deg (OA/EA leave west on separate rows), swap the basement supply/extract plenums N-S, re-route the six radials and both risers, then make all four ports EXACT so the DuctStandard's Broan kits derive (12" flex + 6-to-8 transition). Also slope or drain-back EA's leg (M1-114) and give `DU-ERV-OA` a ledgered lid in the FO-M-ERV-OA chase. Findings: `houses/catlin/notes/erv_static_budget.md` §10.9.
- Get Versadeck / Last-Deck / LockDry quotes for FS-SG-BALCONY, and Ultralox's written OK for SD04964 over 1" PVC fascia (and for the FM244390 corner's fastening); the balcony backing's nail schedule back to the joists is undrawn (`houses/catlin/notes/balcony_fascia_mounts.md`).
- Price an interior-only stair guard against RAILING-INT-STAIR-GUARD ($111–163/LF).
  - [ ] DWV: `PR-M-BATH2-WC-VENT` runs level under TJI 16/17 and the CMFS01/03 seam joist at -13 1/2" (MN 905.3, under the bowl's real rim too); no 45-degree path crosses them to W-M-HS1. A headered chase in that band, or move the fixture or wall. `mep.vent_connection` stays ADVISORY until it closes (C4 E11).
  - [ ] `PR-M-S-BATH1-TUB-DRAIN`'s arm crosses FO-S-ERV-CHASE's 2-1.75x11.875 LVL header at x 33-36 1/2" (`mep.run_through_floor_member` UNKNOWN): maker's hole chart or a re-route.
  - [ ] Exterior doors D-M-ENTRY / D-M-PORCH / D-S-BALCONY keep their RO base on the joist top, 3/4" under the subfloor (decision #110); the model keeps the subfloor under the sills, A-513.2 draws it cut back. Owner: confirm the cut-back and model a deck void per sill, or re-derive the installations (C1 E1).
  - [ ] Holes through floor framing: `PR-S-SUITEBATH-VENT` bores 9 TJI 230s 10.7" from support vs ESR-1153 Table A's 18" (move to x <= 100.7", add the rule); the 8" `DU-M-ERV-EXH-TRUNK` through 23 FS-S-WEST trusses has 0.25-0.44" spare: fabricator submittal or a 7" / twin-6" trunk (C2 E3/E4, C4 E6/E7).
  - [ ] S-102.1/.2 snow note prints 35 psf at Ct 1.0 for the unheated garage and canopy; the basis is 42 psf (Ct 1.2) + drift (C5 #3).
  - [ ] Interior stair guards (incl. RL-A-STAIR) are authored 1.5" below the finished oak with no mount spec; the corrected datum puts RL-A-STAIR's east post 1.0" into the roof underside; bases need blocking (C1 E2).
  - [ ] Header sizing: span-only ladder, nothing grades IRC Table R602.7(1) (C2 E5).
  - [ ] Sheets: label overprints and K-bubbles without targets on ~30 detail sheets (one `annotation_layout` pass); missing schedule rows (LVL band header, pier cages, ridge hardware, backing bands, S-601 material); opening details per kind; plan chains drop bearing walls; plumbing/electrical sheet content; rim-band captions (C5 #1, #2, #4-#8; C1 E8).
  - [ ] Fit: exterior door 0" head gaps (C1 E3); interior door RO 81.51" vs 82-82 7/16" prehungs and no undercut (C1 E5); Uponor header inlet and 6" bend supports (C4 E10); fridge hinge 5/16" off W-M-PAN-S (C3 I1-101); BATH2 shower backer gwb-mr vs §6 glass-mat (C3 I2-105); hall-bath nailers 81-84.5" vs 71-76.5" (C3 I2-101); 1/2" "gwb-x" is Firecode C (C3 I4-103); entry-screen wall end in the garage cladding (C3 E2-101).
  - [ ] Smaller open items, by cluster file: C1 E4/E6/E7 (ST-M2S on LVP, trim residue incl. 4" rubber base, window stools through the buck jambs), E10/E11, Murphy datum; C2 E7-E12 (backing vs runs and overlaps incl. BK-M-HS1-BASIN/GRAB, backing face check, seat beams vs CBSQ66 strap, CBSTQ66Z part number, IUS sizing); C3 I2-102, E2-104, I3-108, I4-107 (D-A-STUDY/D-A-POCKET onto unfinished subfloor), I4-004/005; C4 E3 (BD8 damper Broan forbids, owner), E4, E5 (EQ-M-ERV-MAN-SUP unfed), E8, E14-E17. 12 wall-light types (29 lights) still state no `LuminaireType.canopy`; no check grades a run through a room's `ceiling_lining`.
  - [ ] TB-SG-W1/E1 closure boards 8" vs FT-B-S2/S3 at 10" (F5-104); FB-B-CS drain-tile ring 1" into FT-B-S2/S3 (F5-105); 14" north-entry pier cage 0.806% (engineer hold, C2 E6).
- Supplier holds from the same pass:
  - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 1" short of the Transition Trim seat; a stock gable end closure for the 7" cover; Profile Vent width; a 4x3 1/2-to-4" round adapter.
  - DAKAM: Alucover operable sill rail height and sash overlap (author `WindowType.sill_rail_height` / `sash_overlap`). Andersen dealer: the 400 casement's frame vs sash face split (only unit − 4.40" glass is published), to author `frame_face_width`/`sash_face_width` on the egress types. Max Light fabricator: §2.6 items 11-13 of `notes/window_and_door_procurement.md`. MMI: Z0364688R sill crest (ST-G-SERVICE tops at the +1.5" envelope).
  - Murphy Door: the custom 32 x 82 RO flush-mount (FF datum, body 28 3/4 x 78 1/2 x 8 1/4, casing 36 1/2, passage 24 1/4, price/lead time).
  - **Engineer hold, 14" north-entry pier cage (C3-E21):** PT-BW-W/-GW and PT-BW-PE/-PNE (`PIER_CONCRETE_14`, (4) #5) are 0.806% of gross, under ACI 318-19 §10.6.1.1's 1%; met only on §10.3.1.2's reduced area (0.770 in2 on 76.97 in2). EOR to confirm the basis or go to (6) #5. `notes/north_entry_piers.md` §13.
  - Broan: the derived 9 3/4" port 3-4 spacing; 8" flex on those centres. Weyerhaeuser: TJI 230 row assumes a glue-nailed subfloor. BuildBlock: BB600 course height vs the 64" stem.
  - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/8" pad. WAC Roland on a flat 753 cover; DVFR1W trim stand-off. Bypass/bifold 1/2" head allowance.
  - Plumber: the attic WC's 1 1/2" vent (UPC 904.1); basement WC re-route under the slab to W-B-BA-E.
  - Product/cost review holds (2026-11-04, `plans/catlin-product-cost-review/REPORT.md`):
    - 03-004 Simpson: HHUS410 fastener option and coating.
    - 07-001 Breezeway: the 5.9 LF guard package (product, posts, price).
    - 07-002 Porch: curtain track, carriers and panel system.
    - 15-001 Sauna: tile-on-shiplap substrate and membrane detail.
    - 05-001 Metal Sales: PBR jamb sticks, gutter end caps and straps (unpriced joins).
    - 01-001 DSI: does Saint Paul's 6" concrete / 4" aggregate driveway guidance apply to the modeled 4/8 section?
    - 04-001 S-5!: ColorGard calculator layout (both-end clamps, spacing, rows), then replace the 2-unit row.
    - 08-002 HVAC: suite-bath fabricated boot vs the ten-terminal allowance.
    - 13-002 Installer/AHJ: confirm the APsmart transmitter/receiver pairing for NEC 690.12.
    - Tax: site is Saint Paul (9.875%) if confirmed; prices.toml keeps Hennepin 8.525% by owner call 2026-11-04.
- Generally our goal is to have every piece of the house linked to a named product (or a standard or commodity size, like a 2x4) so we can confirm every piece fits together correctly.
- Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn P9703WBG in the 36-inch SEKTION. Verify delivered Badger revision, clip/washer and rail access, full hose stroke, cleanout clearance, vent fitting/bore envelopes and the inward tilt-turn window sweep (full turn likely obstructed). See houses/catlin/notes/kitchen_sink_installation.md; product/connection specification is complete, physical fit is not released.
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X) (Scuff-X is held for this item; the house paint systems are decision #113, houses/catlin/notes/paint_selection.md), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- D-B-SUNKEN: separate brick reveal, widened RO, 5-1/2 inch concrete seat and a foam-bed Trex tread with fascia box sides (2026-11-04, §6 of the note) are modeled; the section-intersection check passes against every nearby solid. Still open: the tread's drain-slot outlet (its outer edge sits ~1/2" under W-SG-BRKBM's top), the PVC water sheet's laps and the box sides' seal to the brick, installed pan/sweep/hinge sections, and assembled-unit label/warranty evidence. Submittal (06-002): CPD and NFRC/NAFS label, astragal, Endura sill and PanoLock+. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards. BE365 adapter F is documented; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete house-root connections and cross-bearer bearing, installed pan/sweep/hinge sections and the flexible flashing-end application; confirm assembly dimensions/label/warranty, plus the 06-002 submittal (CPD, NFRC/NAFS, astragal, Endura sill, PanoLock+). Complete preferred/Tru-Defense prices remain unavailable publicly. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- Add the eased edges and rounded corners to the shown tabletop model.
- Autorouter open items (plumber's-rules pass, 2026-11-03; drain basis §13, `docs/routing.md`; perf guard and `--manifold` done 2026-11-04):
  - [ ] FX-M-KITCH-SINK refuses in the main tree at 1.5" (151k labels, tightest PR-B-CW-WH across the fall band); the authored run stands. Owner: move the cold feed. `haus route --run PR-B-CW-WH` (2026-11-04) only offers a lane along the furnace-room floor at 5", which is not acceptable; the lane needs hand authoring out of the sink branch's fall band. tree:second's TUBSH branch refuses too.
  - [ ] FX-M-BATH2-SH refuses in the main tree and walks the whole 1.5M-label budget (~139 s of tree:main's ~150 s search, 2026-11-04). Its tightest blocker is now PR-B-HW-KITCH (97 7/16" along y=15'-6", the old lane, kept by the header re-plumb). The §13 reachability pass (graph-distance head floor) prunes nothing here: the labels are head-feasible and band-fragmented. Likely needs BATH2-WC laid lower or KITCH's crossing moved; the tree rip-up (plan 3a) is not built.
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
- [x] Roof sheathing: 19/32" 40/20 plywood, CDX house and Structural I garage/canopy. [Assessment](../houses/catlin/notes/roof_sheathing_and_membranes.md): Image II acceptance, eave cantilevers, narrow/single-span panels and 24-1/8" transition engineering remain open.
- [x] Roof membranes at installed thickness, near-black under Flashing: house butyl 30 mil, garage/canopy HT rubberized asphalt 40 mil. House unvented/full-coverage product confirmation remains open; see the roof assessment.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
  - Confirm strip-in width (provisional 9") with GCP, and Image II + deck + membrane acceptance with Metal Sales; deck bearing is 2.036" vs 2" min, provisional.
- Consider 1/2" advantech for walls sheathing, maybe 1/2" osb and tape the seams
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- D-B-SUNKEN has some weird top flashing that isn't needed here it seems (the threshold now reaches over the foam gap: the foam-bed tread, 2026-11-04).
- D-B-SUNKEN has an STHD14 connector sprouting up in the middle.
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
- **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimmer pack (19'-0 1/8"..20'-0", south of the well edge), and `RL-A-STAIR`'s surface posts (since 2026-10-31) stand ~1 1/8" south of its bracket line: the junction needs detailing, and the surface bases need blocking under the pack (4 GRK RSS, SG >= 0.50).
- Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing and subfloor nailing, fascia/trim screws, window-install screws, and the HL angles' site-length through-bolts. Open: a Metal Sales price for 8243100.
- Backup battery, still open (`houses/catlin/notes/backup_power.md` §11-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; how the 12kPV's load port behaves on its "No Battery" setting (ask EG4); its GEN port rating; declare future storage and V2H on the Xcel application; DSI's position on a UL 9540 3rd-ed. DC ESS battery; a freeze drain-down plan; a small LFP UPS for Home Assistant, the router and the leak valve. After the 2026-11-02 trim the always-on tier passes summer's 48 h and the bridge (0.28 kWh margin) and still fails December's cycle (§6).
- **Route the V2H spare raceway** (`backup_power.md` §10): one empty 2" Sch 80 PVC with a pull string, inverter area on `W-B-N4` to the garage, along `CD-B-GARAGE`'s corridor (north-wall ceiling lane, the `W-B-N2` sleeve, the buried gap leg). Use the `route-run` skill; check `mep.run_interference` and the sleeve. If `SP-B-N2-CD-GAR2` cannot take a second 2" raceway, upsize the sleeve, don't reroute `CD-B-GARAGE`.
- **Engine-wide: is the AHJ on the 2026 NEC?** `plan/circuits.py` already says MN adopted it for permits filed on or after 2026-08-17 (Minn. R. 1315.0200); many checks still cite 2023 sections (230.85 is gone in 2026). Settle the citation basis; not fixed piecemeal.
- Let's make sure all the charcoal gray and black details of the house exterior (various metal trim, window frames, foundation insulation cover) show real manufacturer colors. We are using this to determine if we should switch all to more gray or more black.
- `haus print3d --colour-groups`: per-piece colour components bucketed from `Material.color`, matched to a sample exported from Bambu Studio before shipping.
- Do an outlet and light switch placement review pass
- O-S-VANITY and D-S-STUDY2, both openings (not true doors) seem to get ignored, improperly showing baseboard, sill plates, and non-continuous flooring, they likely just need to reuse some of the existing door handling logic which generally works
- **FS-M-NE truss order (decision #112).** 16" o.c. is a published TRIFORCE OJ418S read (p. 5, 40/25 psf L/480, 18'-0"), so this is a stock order plus confirmation. Send the supplier `houses/catlin/notes/main_floor_truss_basis.md` §2-§3: L/720 live on the order, `FS-S-WEST`'s 24"/13"/12" web layout, the doubled trusses on the 316 and 332 lines, the peninsula point loads (confirm both pairs: doubled, the hand bound is still 1.02-1.10x the row's moment) and the fridge/freezer and partition loads; also the blocking panel for the `W-B-N1` bays and the two strongbacks (cuts at y 180/196/292/414).
- **Consider the same row and a strongback on `FS-S-WEST`** (11 7/8" open-web at 16" o.c.; today it rests on a borrowed I-joist table, advisory only).
- **W-B-N2 wall-top restraint (Minn. R. 1309.0404).** `FO-M-STAIR` fills the first three joist spaces against W-B-N2 for x 10'-3"..17'-6", so no footnote f blocking can stand there and `code.MN_1309_0404_wall_top` reports UNKNOWN. 400 plf x 8' = 3,200 lb goes into the well's edge framing spanning flat between the headers: get the EOR's approved-equivalent detail (a flat strongback or a landing strut) and author it. Basis note `houses/catlin/notes/main_floor_truss_basis.md` §4.
- **Tile medallions: not this pass (review 2026-11-01).** Any tile forces an underlay under all the LVP (~0.47" more finish: re-derive ST-M2S/ST-B2M risers, every main-floor door, toe kicks and appliance openings). (a) Dining table, ~8'x6': DEFER, lean don't — the table hides it and the joint lands under the pulled-out chairs; worth it only for heat underfoot (~700-900 W Ditra-Heat). (b) Peninsula stool strip, ~6'x22": DEFER, lean don't — glides and a mat do the job; a narrow LVP-tile-LVP strip reads least intentional. (c) East range border, ~36"x6': DON'T — a walkway that merges with (a). Instead: felt glides, a rug under the table, stool tips; if heat is wanted later, a rug-sized film under a removable rug. Revisit only as one (a)+(c) feature, priced with the re-derivation. The 16" o.c. L/480 trusses with the 25 psf dead column are still tile-ready either way (ceramic over Ditra). The flush stacks considered: Ditra/Ditra-Heat + thinset + 8-10 mm tile = 1/2" ply/Exacor/Fiberock + 6.5-7 mm LVP (~3/4").
- Aiming to keep floor transitions flush, looks like ~3/4" thickness makes this easiest. Ditra XL or Ditra Heat + Thinset + 8 mm Tile (Ditra Heat PS 5.5 mm + 3.5 mm thinset (3/8" by 3/8" notch trowel) + 10 mm tile OR Ditra Heat Duo peel and stick (PS) + 2.5 mm thinset (1/4" x 3/8" trowel) + 9 mm tile OR 1.5 mm thinset (compressed by 1/4" by 1/4" trowel) + ditra heat 5.5 mm + 2.5 mm thinset + 9.5 mm tile) == 1/2" plywood (nominal) + 7 mm LVP == 1/2" exacor (12 mm actual) + 7 mm LVP == 1/2" gypsum underlayment (fiberrock) + 6.5 mm LVP == 5/8" actual (Fiberock) underlayment + 3 mm sheet vinyl == 16 mm exacor + feather finish + 2.8 to 3 mm sheet vinyl == 3/4" hardwood ~= 7/16" pad + 1/2" pile carpet (carpet squishes at edges)
- Specify leak detectors, in useful places, linked to Home Assitant
- Is TypeHaus organized such that a contractor building typehaus could hand their chatbot/llm of choice the github repo link and easily get answers they need on the design?
- Reverse osmosis sink?
- See if we can reduce the remove/reduce the RM-S-SUITE door (such that a switch to a solid door makes sense too)
- See if we can switch the LED strips to HA compatible Matter/Thread (or if to stay Zigbee). Also ideally reduce the number, ie just one or two for the soffits, not six
- The extra furring on the stairs, C-B-CN, seems a little ridiculous. Should we just go to wider stairs?
- Items that seem too expensive: 12" concrete basement (thought we were down to narrower), FX-SHOWER-36-THERMO-COMBO, FX-TUBSHOWER-60-DIVERTED, RAILING-EXT-ALUMINUM-FASCIA, 5/8" ceiling listed twice
- basement gym heat pump pointed down towards theater. Return vent in wall in mechanical room

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

- [ ] Complete W-BW-SCREEN metal cassette engineering, support/trim details, complete loads and fabrication estimate; rerun structural and 81° door checks including all hardware. See houses/catlin/notes/entry_screen_metal_cassettes.md.
