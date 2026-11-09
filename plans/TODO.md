# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

Sourcing quotes, construction todo doesn't belong in this document, this is just softwared and house design todo. Quotes, supplier confirmations, dry-fits, site measurements and commissioning go in `houses/catlin/notes/construction_holds.md`.

We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
Our general goals are decent longevity and quality at a reasonable price, avoiding premium items unless clearly a major improvement for our needs.
Note that many of the pinned decisions in the code base here aren't as fixed as they sometimes claim, the "fixed" decisions were usually fixed in a narrower context, and can be changed for sufficiently good reasons.

## Needs your decision

- **Budget policy (pricing review 2026-10-29):** `site-general-conditions` is $35–80k on an
  owner-GC build (cash items alone look like $15–30k), and `[contingency]` 10% also applies on
  top of the lump-sum allowances, which already carry wide spreads (~$15–36k at stake).
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

- **Low-voltage devices still unmodelled:** the doorbell, both cameras, the leak probe and
  the lock exist (`plan/smart_home.py`); an outdoor weather station and any access reader
  do not, if wanted. Place them before drywall, on the AP rollout's pattern (type,
  placement, PoE budget re-check). -- DEFERRED

### MEP / lighting residuals

**The open MEP campaigns' live record is `houses/catlin/preferences.toml`**, not this file:
the itemised web crossings, each with its count and a dated note. `haus check houses/catlin
--no-suppress` is the score with every suppression lifted. (`mep.run_interference` closed
2026-10-08; `test_catlin_erv_clearance.py` holds it at zero bar its two ERV level-2 `_ON_HOLD`
pairs. `mep.riser_through_deck` has no suppression: 0 FAIL, 53 UNKNOWN under the 4" drill
allowance.)

- **Lighting confirms left after 2026-11-07** (`houses/catlin/notes/smart_home.md`): the Omvi 3i
  is not on HA's `reolink` list (RTSP works, ONVIF unlisted); the garage GL-C-208M's Wi-Fi/Matter
  VLAN is unplanned; MITTLED
  counts one piece per run until `LightRun.modules` / `stock_length` carries its SKUs. E4 coves
  stay ~102 lm/ft per white channel (no 12 mm RGB+CCT tape reaches 250; owner accepts).
- **Owner: move the indoor cove controllers to the Matter GL-C-208M too?** The coves are the
  only Zigbee devices; doing it retires the second ZBT-2.
- **Determine basement backwater protection before under-slab rough-in.** Add the next
  upstream manhole-cover elevation on the survey datum, compare it with basement fixture
  floors under UPC 710.1, and protect only affected low branches if required. The existing
  sewer-permit task records invert, not cover elevation. [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- **Water-heater thermal expansion: ask SPRWS** (Engineering 651-266-6270) whether the meter set
  carries a check valve and what the static pressure at the main is. Then model a listed expansion
  tank on the heater inlet (and a PRV over 80 psi). `PA-G-HYD-BFP` is on the hydrant branch only
  since 2026-10-29, so the meter set is the only possible check. `notes/water_service.md` §4.

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
  The radon is the NORTH pipe of `VR-M-STACK`'s pair and sits west of every gate. Gates
  re-measured 2026-11-07 (`erv_static_budget.md` §10.13): 2.70" between the EXH riser crown and
  `DU-ERV-EA`'s wrap, 5.50" between the SUP and EXH risers (three conduits in it), 1.18" south of
  EXH, 1.00" north of EA. A 6" stock duct needs 6"; even pushed to the walls the stack is 0.75"
  short, and a 1" EA wrap opens it on paper. Levers: relocate `EQ-M-ERV-MAN-SUP`, or re-pack the
  EA/EXH/conduit column.
- **`mep.run_in_finished_volume`'s terminal grace is blind to leg length** (decision #94): a
  fixture's whole first or last leg is excused however far it runs. Measured 2026-11-07: a 24" or
  48" cap newly raises the same two, PR-M-CW-COLDSTORE-STUB (5.03 ft) and PR-M-DW-HW (4.12 ft),
  both in RM-M-LIVING; they clear only above ~60". Owner: cap it (and chase those two) or keep
  the grace.

### Performance / energy follow-ups

- **Compare the ERV/air-handler interlock's annual fan energy with dedicated ERV supplies.**
  `EQ-B-ERV.blower_interlock_ref` calls `EQ-S-HP1-AH` so ventilation reaches remote rooms
  while the heat pump is off (`houses/catlin/plan/mep_erv_l3.py`). Measure incremental
  ventilation-only watts and annual runtime, then price a balanced dedicated supply
  alternative. Preserve room delivery and backdraft protection. `mep.erv_blower_interlock`
  grades the present arrangement but does not compare operating energy or lifecycle cost.

- **PV residue after the R324.6 re-lay** (18 x Aptos DNA-108-BF10-410W bifacial, portrait, one
  row per plane, 18.0" hull ridge setback, 36" north-rake pathway; `code.R324_rooftop_pv_access`
  passes). Open: S-5 PVKIT uplift capacity at the rake (south module sits in the edge zone, hand
  estimate only), the Aptos short-edge clamp zone, the DLI roof load table for 873 lb of modules,
  AHJ acceptance of a rake-end pathway, the PV homerun path (keep it out of the pathway). The
  R324 text is read off [MN DLI's sheet](https://www.dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf); confirm with St Paul DSI.
  `plans/cost-options.md` lines 94 and 402 still say 5.28 kW.

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
- **`ResolvedRoom.head_limited_area_m2` and `room_area.countable_floor` are two derivations**
  of R304.3's countable floor; `resolve/roof_geometry` should return the polygon both read.
- **Derive a fixture-supplied box** (Bantam's JB-0501) so SCONCE-STAIR can state its canopy.
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
- **Plan lettering residue:** on the 24x36 set PANTRY, the attic STUDY and the chase captions are clear. D1-109 is closed: MUD CLOSET abbreviates through `Room.short_label`, and a void caption now keeps its room a slot for its name, so MECH stacks over CHASE (cff89ae74). STUDY CLOSET and ESS still spill into the next room without overprinting. On the 11x17 reduced check print most small rooms still spill or overprint, which is what 3/32" scale does to them.
- A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairwells. Some options: 1/2" Type C, Paper-Faced 1/2" AR (e.g., Gold Bond Hi-Abuse or USG Sheetrock AR), LP SmartSide 38 Series Panel 7/16" (Sidings Used Indoors), 1/2" MDF (4x8 Sheets with V-Groove or Batten Strips), 1/2" MDO (Medium Density Overlay) Plywood
- Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam or standard elastomeric latex caulk ), Best Seamless Durability Upgrade (~+$0.45/sq ft): 1/2" Paper-Faced Abuse-Resistant (AR) Drywall, Best "Skip-the-Taper" Durable Wall (~$1.30/sq ft material, $0 mudding): 4x8 Pre-Primed MDF Shiplap Panels (or LP SmartSide 38 Series), The Winner for General Bath Walls: 1/2" Mold-Resistant Paper-Faced Drywall ("Purple Board" / USG Mold Tough, although not strictly needed on well ventilated walls with good high-resin paint), The Bathroom Ceiling Secret: 1/2" Interior Soffit Board (Sag-Resistant), Best Value for Speed & Zero-Fail Waterproofing behind tile: 1/2" Polyisocyanurate Foam Board (Johns Manville GoBoard), Places where 5/8" may still make sense: floor to floor ceilings (Type X), garage walls (5/8" AR Type X). Apparently the resonant frequency of 1/2" Type C drywall is one of the more ideal for household noises (being higher than the others)
- Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above the walking surface probably). Around the mudroom we want highest abuse resistant with something like wainscot (shiplap there carries the idea already, can be improved further possibly like LP Smartside). Some walls likely worth abuse resistance on a side: W-M-WELL, W-M-HS2/HS3/HS4, W-M-BAE, W-M-C1/C2/C3 and walls facing RM-S-HALLWAY and next to stair landings. A reviewer also said that we should focus STC drywall/framing upgrades strictly for the solid walls without undercut doors (as they say doors bypass sound so much they make upgrades not worth the price, although doors that are weatherstripped, solid, and with no undercut do have better STC), based on this we can perhaps remove resilient channel assemblies from W-S-SBS and W-S-BW1/BW2/BW3
- Open (drywall overhaul): kids' bedroom and kids' room hall faces are NOT on the abuse-resistant swap list; decide whether they take `gwb-ar` (the owner's list omits them).
- Open (drywall overhaul): mudroom wainscot could be LP SmartSide 38 Series 7/16" (sidings used indoors) instead of the shiplap; the shiplap stays until someone prices it.
- Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible).
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_garage_diaphragm.md`'s 'garage takes the whole load'.
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- Plant-room reservoir (owner chose it over a sink, 2026-11-07; `notes/plant_reservoir.md`): 10 gal BRUTE, Dial 4154 float fill 2" over the rim (UPC 603.3.1/603.5.5, Table 603.3.1 read from secondary sources), SEAFLO 12 V drip pump on `ED-S-PLANT-RC6`, D-S-PLANT riser at 0.38" (21.5 gal held at 1/4", 32.6 gal to the stop). Open: (1) a stuck float is unbounded without a shutoff (needle valve at ~0.1 gpm gives ~3.6 h to 21.5 gal): owner; (2) no check grades a tank inlet or air gap; (3) no WSFU row for the tank, so `PR-M-CW-PLANT-STUB` can't name it in `serves` without `mep.pipe_sizing` going UNKNOWN (a permit item); (4) timer vs. the RC6 in-use cover; (5) drip regulator/emitter pick; (6) `prices.toml` rows for the eight new `PROD-*` tags.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Geometry review round 2 (2026-11-05): [report](geometry-review/REPORT.md) §1 ranks the open escalations; detail in `geometry-review/2026-11-04/adjudicated/C1..C5.md`. 0 FAIL kept. Open, by rank:
  - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply fastening, and the edge I-joist filler/backer connections (`notes/sunken_door_band_header.md` §4).
  - [ ] DuctStandard residue (decisions #114/#121, `houses/catlin/plan/ducts.py`): an Imperial submittal for laying lengths and boot heights (the 12.25" stacked GV0821+GV0811 reducer is a stand-in), a proofread of IMC 2018 §603.10 / Table 603.4 against the printed code, and `_ATTIC_DECK_Z` derived from the deck rather than authored (optional). STUBATH's deck-to-high-tier drop is 5.7" against two stamped 90s' 12" (`mep.fitting_pattern` UNKNOWN): the 12" is the 1.5D stand-in for the stamped E90's unread dimension A, not a set-down gap; read Linx E90's A, or draw it as a 45/45 jog (fits: 4.97" of 8.2"). Broan's manual says insulated ducts "must have the same diameter as the ports to ensure proper drainage" against its own 6-to-8 transition advice: ask Broan.
  - [ ] ERV OA/EA/RET hold (C4 E2/E9, C2 E13): EA and RET start on each other's Broan ports (cross-wired). Re-siting the EA riser does not close it (2026-11-05): OA/EA (12" wrapped) cannot cross under the joists, RET must cross to the south plenum under MAN-SUP's 10.4", and lowering the ERV is blocked by the condensate's ~3.8" of fall. The layout that closes it: rotate EQ-B-ERV to 270 deg (OA/EA leave west on separate rows), swap the basement supply/extract plenums N-S, re-route the six radials and both risers, then make all four ports EXACT so the DuctStandard's Broan kits derive (12" flex + 6-to-8 transition). Also slope or drain-back EA's leg (M1-114) and give `DU-ERV-OA` a ledgered lid in the FO-M-ERV-OA chase. Findings: `houses/catlin/notes/erv_static_budget.md` §10.9. **2026-11-07 (wave 3):** the kit gate closes (the flex lead bends at R = D, `notes/flex_lead_bend_basis.md`; leg 5.96" under FS-M-MECH's joists), and the condensate now runs exposed to the utility sink with the case 1.7" lower (up to 3.3" more available; the supply trunk's flex shortfall is closed). The rotation still does NOT close on routing (`erv_static_budget.md` §10.12): at 270 deg OA's port is north of EA's but OA's riser is south-east of EA's foot, so the two 12" wraps must cross; the only window is 72"-96.94" over the dry-fire lane, 0.47" per side. It closes if OA and EA swap riser sides, which moves EA's level-2 end and hood (held). Owner: allow the swap, or a thinner OA wrap / relaxed lane / moved EXH riser. Each bent 8" lead also costs 0.059" (supply 0.489", extract 0.459" against the 0.4" rating; supply ~201.5 cfm vs 203.0 required), so something else must give. Still blocked behind it: the MAN-SUP feed (EA's x=58.5" north leg leaves 5.1" for a 6" duct), EA drain-back, and the OA chase lid (no ledger element in the engine). **2026-11-07 study G (`erv_static_budget.md` §10.13):** the 24.94" crossing window assumed an empty ceiling; CD-B-GARAGE (91.0" AFF), CD-B-DATA-MEDIA and CD-B-KITCHEN (92.7") cut it to 20.7". The 270 deg layout routes without the swap if (a+) OA takes 1" AP Armaflex (OD 10") and CD-B-GARAGE leaves x 53-68 over y 341-361 (1.47"/side, +285 Btu/h; R1's feed gap 7.0" -> 12.9"), or (b) the dry-fire lane takes a 66" x 38" notch at y 341.5-380 (clean in a sandbox, 0.54"/side). Moving the EXH riser does not help (9 FAILs for a 6" gap). Recommended: a+, else b. Router bug: re-rooting `DU-ERV-OA` at the 270 deg port fails at the origin inside AO-M-ERV-OA, which already names it in `penetration_for`.
- The balcony backing's nail schedule back to the joists is undrawn (`houses/catlin/notes/balcony_fascia_mounts.md`).
  - [ ] DWV: `PR-M-BATH2-WC-VENT` runs level under the FS-M-WEST joist 016/017 + FS-M-MECH 000 seam at -13 1/2" (MN 905.3, under the bowl's real rim too; `mep.vent_connection` ADVISORY, C4 E11). A 45-degree climb is 0.21" short (7.69" of flange footprint vs 7.475" of web-zone travel), so no WC position along W-M-HS1 helps. Owner: WC to W-M-W3 bay 13-14 on a 1/4" offset flange (measured, [note](../houses/catlin/notes/bath2_vent_move_options.md) option 2: costs the floor-heat bite, the washlet outlet, the window centring), or an engineered chase.
  - [ ] ERV level 2 flat trunk residue (2026-11-08, `notes/erv_static_budget.md` §10.14): the 8x4 trunk and 6x4 neck are shop-fabricated, so `mep.fitting_pattern` stays UNKNOWN on their elbows until a shop drawing gives the throat radius, and the static budget charges each turn ASHRAE Fitting 3-5's r/W 1.0 equivalent length (59", on `DUCT-T-GALV-RECT-10`). STUDY, LIVING and BED keep short straights between their tier ramps and elbows (`fitting_pattern` UNKNOWN). Both truss decks' pocket stations rest on an assumed 24" pitch until TrimJoist's and TRIFORCE's shop layouts.
  - [ ] S-102's drift trusses (from `engineering/snow_drift.drift_reach`, the function `structural.truss_reactions` grades by) carry no per-truss mark on the plan; the note names them `TRUSS-000`/`-001` (2 of 13).
  - [ ] Header residue (decision #116, `houses/catlin/notes/header_spans_r602_7.md` §5): the `5.25x7 LVL` row in `prices.toml` is an estimate ($13-24/LF material, off the house's own LVL $/bf); replace it with a retail number, ordered as a beam (R/L, probably special order; sold as a column it runs about twice that). `RL-A-HANDRAIL`'s new return beside WIN-S-STUDY3 is tight (end plate 5/8" off the RO, bar about 0.7" off the bookcase): field check. The moved FO-A-STAIR trimmer lands on the plate just past WIN-S-STUDY3's north king, ungraded. D-B-GYM's north king stands 1.2" past W-B-CS3's end on W-B-CS2's line.
  - [ ] D-M-LAUN after the 2026-11-07 move (review of 8b1cf155d). Owner: (1) **washer** (done 2026-11-07): valves behind the tower in W-M-CLN; the washer drains into the laundry tub (Minn. R. 4714.1001's adjacent-washer exception). Confirm with the AHJ against 4714.0804. The tower stands 0" off W-M-CLN against LG's 4" (guide p.14), so it needs 90-degree inlet hoses; name the washer valves at order. (2) **tub access**: 20" of the tub stands behind the strike wall; it is reached through the opening's west 8 1/4" and the 13 3/4" strip in front of the tower (pinned in `test_mep_plumbing.py`). (3) **36' width**: the header reads Boise p.4's 32' column (the widest) plus a load comparison; the literal 36' cell is p.9 Floor Beams 8'-0": 3 1/2 x 9 1/2, 2 trimmers, i.e. a 2-ply 9 1/2" LVL on doubled jacks (the engine frames one jack here; `WIN-M-DINING-E` reads its 32' column the same way). (4) **W-S-SN3's uniform load into W-M-HS3**: `resolve/stacked_ladder.py` records the FS-S-WEST line (W-S-SN2/SN3 over W-M-HS3/HS4, 256/272 bay) and lays nothing on an open-web deck; `structural.stacked_line_ladder` is UNKNOWN until TrimJoist's shop layout carries the line (a blocking panel or a truss over the wall), and the header reads "assumes a ladder in FS-S-WEST". `P-S-SN3-SQUASH` still carries BM-S-BATH-E's point. Still open: neither header nor PublishedSpan grades the guide's structure width against the derived building width.
  - [ ] Construction-set residue after items 12–19 (REPORT §1.12–19): Open: bay-cut rim conditions with no floor (A-570.x); C1 E2 interior guard fascia mount spec; LSSR2.37Z catalog name; A-301/A-204 level labels clip on ledger; MDO layer undrawn on A-508. Overprints found in review: E-101's northwest device-tag cluster (B-INV-BACKUP / B-PV-INV / B-SPARE-CHASE and neighbours), the B&B door detail's K5 leader crossing the K2 bubble (old A-514), and the old A-531's air/water/thermal continuity tags over the detail head (both renumbered into the A-560 series 2026-11-06). Detail sheets were renumbered into decimal series (`emit/draw/callouts.py` `DERIVED_SERIES`, 2026-11-06), so a family grows without overflowing A-599. The renumbering noted G-002's permit note index lists full-set-only sheets (the `permit_drop`/`permit_add` decimal-prefix catch and `visitSheets`'s string sort are fixed).
  - [ ] Owner decisions left open by the 2026-11-06 fit pass (REPORT §1.20-32): the titanium handrail fittings (no published load read; the EZA200 projection and load rating are unpublished too); C4 E8 runs vs backing; C4 E14 supply items; O2-110 pocket head (Eclisse detail). Backing bands: the owner kept BK-M-S1-HP2-BED, BK-M-S2-HP2-LIVING and BK-M-N2-HP3-STAIR.
  - [ ] Fit residue after the 2026-11-06 fit pass: no readable DensShield price (`gwb-glass-mat` unpriced, ~99 SF billed since the review); Sterling drain 8 1/4" (see the second-floor tub drain item); FX-S-SUITE-WC tank 1.09" off (flange held); Uponor LF2821050 A 14.95" (submittal) vs 14.675" carried; 8 flush boxes still on studs (`advisory.box_on_stud`); `mep_hvac.py` ~350 plant-room negative-pressure prose at 25 cfm, now 5; seat beams: the LUS26-2Z now hangs on an 11/32" filler notched round the CBSTQ strap (end gap 0.1055" vs note m's 1/8"; `notes/canopy_west_band.md` 2026-11-06 (b)). Simpson publishes no filler installation, so ask Simpson to confirm. It does not gate gravity (the beam bears on the pack); the fallback is a cast-in HETA20Z pair.
  - [ ] System 1 return relief (follows #21, b90360591): at the owner's 1/2"-3/4" undercut rule, RM-S-BED1/2/3 and RM-S-SUITE hold 9.7 Pa, RM-A-STUDIO 3.8, RM-S-PLANT 19.0 (at its 1/2"), RM-A-EAST-UNFIN 4.8 against 3 Pa, and RM-M-BED nets 5 cfm in behind sealed D-M-BED2 (`mep.door_transfer_air` ADVISORY). Choose transfer grilles, jump ducts or room returns (`notes/system1_return_path.md`). **Owner, 2026-11-07: deferred to a later pass.** Also: steel/sauna slabs are modelled cut 1/8" (steel may need ordering to size); the library interior types and the plan door symbol still use the 45 mm schematic leaf.
  - [ ] Smaller open items, by cluster file: C1 E11 (O1-102 relief doors), O2-110 pocket head (Eclisse detail); C2 E12 rest; C3 I4-004/005; C4 E5 (EQ-M-ERV-MAN-SUP unfed) and the ERV flex/transition terms, E8, E14. SCONCE-CANDLE (Livex 4451-04, no published backplate) and SCONCE-STAIR (see `BoxRow` shape) state no `LuminaireType.canopy`; `place_box` centres a wall-light box on the body's mid-height, not its canopy; the WAC LINE's in-box transformer is not in `electrical.box_fill`; no check grades a run through a room's `ceiling_lining`.
  - [ ] TB-SG-W1/E1 closure boards 8" vs FT-B-S2/S3 at 10" (F5-104); FB-B-CS drain-tile ring 1" into FT-B-S2/S3 (F5-105); 14" north-entry pier cage 0.806% (engineer hold, C2 E6).
- **Andersen's 1⅛" stool rail cannot coexist with the 1 1/2" pan back dam** (`resolve/flashing_config.back_dam_m`, [window profiles](../houses/catlin/notes/window_profile_measurements.md)): the nine egress casements' stools pass through the dam (18 solid overlaps, ~139 in³, blessed 2026-11-07 so the ratchet can track the rest). Read Andersen's installation guide for its back-dam / sill-pan detail, then lower the dam for those openings, shim the unit, or raise the stool clear of the crank operator.
- Generally our goal is to have every piece of the house linked to a named product (or a standard or commodity size, like a 2x4) so we can confirm every piece fits together correctly.
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X) (Scuff-X is held for this item; the house paint systems are decision #113, houses/catlin/notes/paint_selection.md), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- D-B-SUNKEN: separate brick reveal, widened RO, 5-1/2 inch concrete seat and a foam-bed Trex tread with fascia box sides (2026-11-04, §6 of the note) are modeled; the section-intersection check passes against every nearby solid. Still open: the tread's drain-slot outlet (its outer edge sits ~1/2" under W-SG-BRKBM's top), the PVC water sheet's laps and the box sides' seal to the brick, installed pan/sweep/hinge sections, and assembled-unit label/warranty evidence. Submittal (06-002): CPD and NFRC/NAFS label, astragal, Endura sill and PanoLock+. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- D-S-BALCONY: catalog coordination replaces the schematic plate/wrapped trim with a digitized ZAI outline, composite returns and short AridDek boards. BE365 adapter F is documented; crest heights come from the [engine-generated review](../houses/catlin/notes/french_door_catalog_installation.md#3-height-and-geometry-review). Complete house-root connections and cross-bearer bearing, installed pan/sweep/hinge sections and the flexible flashing-end application; confirm assembly dimensions/label/warranty, plus the 06-002 submittal (CPD, NFRC/NAFS, astragal, Endura sill, PanoLock+). Complete preferred/Tru-Defense prices remain unavailable publicly. See notes/french_door_catalog_installation.md; installation remains UNKNOWN.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- Autorouter open items (plumber's-rules pass, 2026-11-03; drain basis §13, `docs/routing.md`; perf guard and `--manifold` done 2026-11-04):
  - [ ] tree:second's TUBSH lays only through D13, shared with PR-B-CW-SUITE (`open_web_panel`). (tree:main's kitchen refusal stays: the 1" sink move's 1.5" lane bores FS-M-MECH I-joists at 1.74" spacing, crosses the FS-M-STAIR LVL trimmer and needs two cleanouts, while the authored 2" lane grades clean; W3-KITCH, 2026-11-07.)
  - [ ] `--group BATH2` lays nothing: the refusal is now head (SH step 4.3"-4.5" short at FS-M-MECH y 309/325), because `cmd_route_group._tie_stations` offers only the three highest in-band stations on PR-B-MAIN-DRAIN, north of the FS-M-WEST/FS-M-MECH seam. Ties near y 212-230 lay SH to WC, but the TUB then has no take-off (x 97" block flange) and the WC is unlaid. Needs a tie-offer fix plus a design question; no fixture move helps (BATH2 note). `--group SUITEBATH` stays the authored three-vent design. Vent-free 908.2 groups are an AHJ question.
  - [ ] `--lift` lays all three supply re-lays on tree:main (CW-WH, CW-BATH, HW-KITCH) and keeps their tees (`mep_tree_ripup_basis.md` §3 L6-L9). Residue: CW-WH's re-lay drops to inlet height early and runs 5" off the basement slab, ungraded, so CW-BATH climbs back (`run_route_efficiency` 4.27); HW-KITCH-PROPOSED makes a 180 deg at the heater port (`fitting_pattern` UNKNOWN); its D11 pocket share closed with B2's one-run-per-pocket rule. A branch teeing on a lifted run's first leg still refuses.
  - [ ] Supply trunk (`--topology trunk`, 0 refusals) evaluates 3 fails, all `mep.run_in_finished_volume` in RM-M-LAUNDRY (PR-A-STUBATH-WC-CW, PR-S-SUITE-TUBSH-CW, PR-M-WASH-CW): a house chase. `tree:CW-TRUNK` shows the same 3. Since wave 1 both rows put 3.87 ft in exterior cavities (PR-S-BATH1-WC-CW 1.25 ft in W-M-W1/W-S-W1, the trunk's end 2.62 ft in W-M-N1): exterior cavities are priced, not refused, and a MN cold line there wants a reason. Drain campaigns (`route_propose`, `route_tree_group`) are not yet fed laid-run holes (`build_space(laid=)`); a branch may still cross a tee-list run it cannot host.
  - [ ] PR-B-BATH-VENT finds no route at margins 4/6/8 (since `MAX_LATTICE_NODES` 650k it builds): its root lanes are blocked by PR-B-BATH-DRAIN, and the counterfactual says re-routing the drain alone opens none. Its far terminal reports standing inside 18 elements from FT-B-W1 to FS-ATTIC, which looks like a full-height pardon at the stack tie.
  - [ ] Fitting gaps left by hand after 2026-11-07: DU-B-ERV-R-PLAY (a 30 deg ramp breaks SF-B-BATH's soffit), DU-B-ERV-R-SAUNA-SUP, DU-A-ERV-R-STUBATH, DU-S-ERV-HP-FEED, DU-B-ERV-RET-TRUNK (port side, with the ERV hold); the router's duct proposals redraw them exposed.
- Air-distribution products (specified 2026-10-31, [note](../houses/catlin/notes/air_distribution_products.md)); still open:
  - Owner: the 1.1 cfm residual under 205, or the 10" hoods (needs RenewAire FA10 test data and a plate fit check) — `notes/erv_static_budget.md` §10.4, §10.6.
  - Owner/AHJ: which floor area MN 1322 R403.5 means. The engine grades finish-face room area (195 cfm required); centreline gave 205, exterior dimensions give 214, past the 210 cfm machine — `notes/erv_static_budget.md` §10.6.
  - Engine, deferred: an insulation-vs-R403.2.1 check; per-segment duct insulation; M1506.3's 3 ft exception and the operable-opening distance; checking an insulation spec's thickness against its R-value; grading a damper actuator inside a duct.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
- Consider 1/2" advantech for walls sheathing, maybe 1/2" osb and tape the seams
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- D-B-SUNKEN has some weird top flashing that isn't needed here it seems (the threshold now reaches over the foam gap: the foam-bed tread, 2026-11-04).
- D-B-SUNKEN has an STHD14 connector sprouting up in the middle.
- Fixture connections (stations applied 2026-11-07, `houses/catlin/plan/wet_ports.py`). Still open:
  - BATH2/BATH1 R10000 supplies stub straight in at the finished face. BATH2's hot riser is elbowed
    6 3/4" north (riser y 185, not the cold's 1 1/2"); at hub + 1 1/2" it FAILs `run_interference`
    on PR-B-SH2-DRAIN, which moving the SH2 arm tee, its vent leg and CO-M-SH2-HEAD 2" north
    (tee y 182.5) clears with 0 FAIL (owner, BATH2 note option 1); BATH1's cold drop doubles as the WC tee, so an
    along-wall arrival moves the drop and tee to y >= 413" in W-S-CH-W.
  - Sauna R10000: the W-B-CS stubs stop at mid-stud, 4 1/4" behind the hubs, which sit inside
    the 2" foil-polyiso layer. Decide stub depth and how the supplies pass the vapour layer.
  - APPL-LG-DISHWASHER: a Product and price row for the 48" braided 3/8" supply its `hose_length` assumes.
  - The floor-fed WC stops (FX-M-BATH2-WC, FX-S-BATH1-WC) are house setout, APPROXIMATE.
  - The washer's real valves are mid-run tees, which the endpoint grade cannot see.
- Electrical placement residue: `ED-S-NCLOSET-SW` has no clear bay on W-S-CLN-S (west lands in the door opening, east in W-S-BW3), so it stays over a king with the advisory unless the door or switch moves. HLG-100H AC splice boxes (RACO 232) are billed, not drawn. `notes/basement_surface_wiring.md` lines 133 and 147 still place `ED-B-PLAY-N-SW` on its old wall. Bench-pair the DAWSC-1BW to the flood's D315S before the board goes up.
- Block load residual (verified against the hand notes 2026-11-08: 30,183 Btu/h heating, 16,522 sensible + 6,076 latent, no engine bug): the wall load uses the card R-43.6 against the R-39.8 to 37.9 oracle, and the ERV SRE is rated at 83 cfm against about 204 delivered. Together about +3 to 4% heating, no equipment change (`houses/catlin/notes/block_load_basis.md` §10).
- Rainscreen closures (2026-10-29): the panel bottoms are still drawn to the seat, not on the raised strip (in `resolve/board_batten.py`), and so are the wide outside corners (`cladding_trim/mixed_corners.py`, off the same layer band): both pass through the raised trim foot and the base strip, and `integrity.rainscreen_cavity` cannot see a panel surface, so it grades the slot open regardless. At the four outside corners the base and band strips also run into the corner trim and the adjoining wall's base trim; stop them at the corner once the corners land on the trim.
- **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimmer pack (19'-0 1/8"..20'-0", south of the well edge), and `RL-A-STAIR`'s surface posts (since 2026-10-31) stand ~1 1/8" south of its bracket line: the junction needs detailing, and the surface bases need blocking under the pack (4 GRK RSS, SG >= 0.50).
- Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing and subfloor nailing, fascia/trim screws, window-install screws, and the HL angles' site-length through-bolts.
- Backup battery, still open (`houses/catlin/notes/backup_power.md` §11-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; how the 12kPV's load port behaves on its "No Battery" setting (ask EG4); its GEN port rating; declare future storage and V2H on the Xcel application; DSI's position on a UL 9540 3rd-ed. DC ESS battery; a freeze drain-down plan; a small LFP UPS for Home Assistant, the router and the leak valve. After the 2026-11-02 trim the always-on tier passes summer's 48 h and the bridge (0.28 kWh margin) and still fails December's cycle (§6).
- V2H spare raceway (routed 2026-11-07, `backup_power.md` §10): add PVC 2" rows to `prices.toml [conduit_fittings]`; the ICF supplier/engineer details rebar round the three 6" CD-GAR sleeve boxouts in W-B-N2 and W-GF-S2. `CD-B-GAP-EV` ends at +5'10" abs while `ED-G-EV-1450` is at 48" AFF (+14" abs): an existing over-rise to check.
- **2026 NEC residue (decision #120).** Confirm every `typehaus.model.nec.UNCONFIRMED` row against
  the printed NFPA 70-2026; get 110.26(A)'s door text before grading door swings. Not graded:
  210.12(B)(14) bathroom lighting AFCI, 210.11(C)(3), SPD coverage, 690.12(C)'s outdoor
  initiation device, 705.11/705.20 source OCP. Revisit Class C SPGFCI for CKT-HP1-3 after the
  NFPA Standards Council (2026-12-15/16); they are Class A breakers meanwhile.
  Confirm the full 2026 210.8(D) item list (microwave, disposer, water heater are ungraded);
  `model/electrical.py`'s 314.16(A)(1) marked-volume cite is unverified.
  `prices.toml`'s `electrical-spd-plug-on` keys on a 2-pole, non-source circuit with no load: give
  `Circuit` a kind (or SPD a type) before another load-less 2-pole circuit bills as an SPD.
- **Exterior darks are black** (2026-11-07, `houses/catlin/plan/exterior_palette.py`, `notes/exterior_darks.md`). The engine's `RAINSCREEN_BASE_Z` text still calls the base strip aluminium.
- `haus print3d --colour-groups`: per-piece colour components bucketed from `Material.color`, matched to a sample exported from Bambu Studio before shipping.
- Promote the leafless passage's drywall wrap (#122) to a `ResolvedModel.passage_wraps` record so emitters can draw the returns.
- **Consider a strongback on `FS-S-WEST`** (TrimJoist J12 at 16" o.c. now reads its own published row, `J12_FLOOR_SPAN`).
- **W-B-N2 wall-top restraint (Minn. R. 1309.0404).** `FO-M-STAIR` fills the first three joist spaces against W-B-N2 for x 10'-3"..17'-8 3/4", so no footnote f blocking can stand there and `code.MN_1309_0404_wall_top` reports UNKNOWN. 400 plf x 8' = 3,200 lb goes into the well's edge framing spanning flat between the headers: get the EOR's approved-equivalent detail (a flat strongback or a landing strut) and author it. Basis note `houses/catlin/notes/main_floor_truss_basis.md` §4.
- **Tile medallions: not this pass (review 2026-11-01).** Any tile forces an underlay under all the LVP (~0.47" more finish: re-derive ST-M2S/ST-B2M risers, every main-floor door, toe kicks and appliance openings). (a) Dining table, ~8'x6': DEFER, lean don't — the table hides it and the joint lands under the pulled-out chairs; worth it only for heat underfoot (~700-900 W Ditra-Heat). (b) Peninsula stool strip, ~6'x22": DEFER, lean don't — glides and a mat do the job; a narrow LVP-tile-LVP strip reads least intentional. (c) East range border, ~36"x6': DON'T — a walkway that merges with (a). Instead: felt glides, a rug under the table, stool tips; if heat is wanted later, a rug-sized film under a removable rug. Revisit only as one (a)+(c) feature, priced with the re-derivation. The 16" o.c. L/480 trusses with the 25 psf dead column are still tile-ready either way (ceramic over Ditra). The flush stacks considered: Ditra/Ditra-Heat + thinset + 8-10 mm tile = 1/2" ply/Exacor/Fiberock + 6.5-7 mm LVP (~3/4").
- Aiming to keep floor transitions flush, looks like ~3/4" thickness makes this easiest. Ditra XL or Ditra Heat + Thinset + 8 mm Tile (Ditra Heat PS 5.5 mm + 3.5 mm thinset (3/8" by 3/8" notch trowel) + 10 mm tile OR Ditra Heat Duo peel and stick (PS) + 2.5 mm thinset (1/4" x 3/8" trowel) + 9 mm tile OR 1.5 mm thinset (compressed by 1/4" by 1/4" trowel) + ditra heat 5.5 mm + 2.5 mm thinset + 9.5 mm tile) == 1/2" plywood (nominal) + 7 mm LVP == 1/2" exacor (12 mm actual) + 7 mm LVP == 1/2" gypsum underlayment (fiberrock) + 6.5 mm LVP == 5/8" actual (Fiberock) underlayment + 3 mm sheet vinyl == 16 mm exacor + feather finish + 2.8 to 3 mm sheet vinyl == 3/4" hardwood ~= 7/16" pad + 1/2" pile carpet (carpet squishes at edges)
- Is TypeHaus organized such that a contractor building typehaus could hand their chatbot/llm of choice the github repo link and easily get answers they need on the design?
- Reverse osmosis sink?
- See if we can reduce the remove/reduce the RM-S-SUITE door (such that a switch to a solid door makes sense too)
- Reduce the number of LED strip controllers, ideally one or two for the soffits, not six (Zigbee vs Matter: see the cove-controller item above).

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


- [ ] Complete W-BW-SCREEN metal cassette engineering, support/trim details, complete loads and fabrication estimate; rerun structural and 81° door checks including all hardware. See houses/catlin/notes/entry_screen_metal_cassettes.md.
