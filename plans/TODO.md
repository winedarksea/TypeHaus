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

- **System 1 in the attic (2026-11-11), what is still open.** The air handler is on
  `RM-A-EAST-UNFIN`'s deck (`houses/catlin/notes/flexx_ultra_geometry.md`):
  - The emergency pan and its float switch (IMC 307.2.3 item 3) are unmodelled; the cabinet
    sits on SL-A-HP1-PLATFORM and the pan's rails lift it about 1" more on site.
  - Lineset and control cable from `EQ-M-HP1-OD` to the attic are unrouted.
  - Attic service provisions: a passageway from `D-A-STUDY`, a level service space, a
    light switched at the entry and a receptacle near the unit (IRC M1305.1.3 / IMC 306.3).
  - Measure the delivered cabinet's return aperture (modelled as 20x16, inferred) and the
    supply opening setback before the necks are built.
  - `RM-A-EAST-UNFIN` must stay inside the thermal envelope while it holds the air
    handler. This matters for the "don't count the attic lofts as conditioned" item below.
  - Engine: there is no PLENUM equipment kind. Passive shop boxes ride `MIXING_BOX`.

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
- [ ] DuctStandard residue (decisions #114/#121, `houses/catlin/plan/ducts.py`): an Imperial submittal for laying lengths and boot heights (the 12.25" stacked GV0821+GV0811 reducer is a stand-in), a proofread of IMC 2018 §603.10 / Table 603.4 against the printed code, and `_ATTIC_DECK_Z` derived from the deck rather than authored (optional). Linx's public catalog gives the E90 only as rC ≈ 1.5 d1, no dimension A (REV11 p.13; ask a Linx rep for the dimensioned submittal); STUBATH's drop is a 45 deg ramp since 2026-11-11. Broan's manual says insulated ducts "must have the same diameter as the ports to ensure proper drainage" against its own 6-to-8 transition advice: ask Broan.
- [ ] ERV OA/EA/RET hold (C4 E2/E9, C2 E13): EA and RET start on each other's Broan ports (cross-wired); EQ-B-ERV stays at rotation 0. The 270 deg rotate-and-swap does not close (`houses/catlin/notes/erv_static_budget.md` §10.9-§10.13, **§10.18**, 2026-11-11): an EXACT OA port charges Broan's 6-to-8 transition and bent 8" flex (+0.077"), so any 270 layout reads ~0.509" / 200.5 cfm against 203.0 (FAIL) unless the supply trunk and plenum inlet go to 8" (-0.027", ~201.9 cfm, the UNKNOWN band). The OA/EA crossing over the dry-fire lane is bound by PR-B-SAUNA-VENT's x=51.5" furnace-room leg and CD-B-KITCHEN / CD-B-DATA-MEDIA at 92.7", not by CD-B-GARAGE; the OA/EA riser swap needs a chase through RM-S-BATH1 and puts a main-floor hood 3-4 ft from the intake (10 ft required). Owner: (1) re-lane that vent loop and both conduits and take the 8" trunk, (2) the 66" lane notch (declined 2026-11-11), or (3) keep the 0 deg cross-wiring. Draft: branch `wip/erv-270-layout-x-not-landed`. Still behind it: EA drain-back (M1-114), the OA chase lid (no ledger element in the engine), and the basement radials' fitting gaps (DU-B-ERV-R-PLAY 7.2" vs 12.1", DU-B-ERV-RET-TRUNK; SAUNA-SUP's jogs went with its 2026-11-11 re-path), which any rotation redraws.
- Replace the Custom 12×28 air filter: reconsider a stock 12×24 MERV 13 filter and matching grille. Catalog options exist, but pressure drop and noise need checking before substitution. [Manufacturer data](https://zephyrfiltration.com/wp-content/uploads/2025/03/ZEP25252-VGP-MERV-13-Product-Spec-Sheet-Updates-V2.pdf
- Attic level heat pump outlet grills don't seem to have modeled duct connects.

### Performance / energy follow-ups

- **Compare the ERV/air-handler interlock's annual fan energy with dedicated ERV supplies.**
  `EQ-B-ERV.blower_interlock_ref` calls `EQ-S-HP1-AH` so ventilation reaches remote rooms
  while the heat pump is off (`houses/catlin/plan/mep_erv_l3.py`). Measure incremental
  ventilation-only watts and annual runtime, then price a balanced dedicated supply
  alternative. Preserve room delivery and backdraft protection. `mep.erv_blower_interlock`
  grades the present arrangement but does not compare operating energy or lifecycle cost.

- **PV residue after the R324.6 re-lay** (18 x Aptos DNA-108-BF10-410W bifacial, portrait, one
  row per plane, 18.0" hull ridge setback, 36" north-rake pathway; `code.R324_rooftop_pv_access`
  passes). Published PVKIT grab-capacity lookup is complete (EdgeGrab 353 lbf / MidGrab 861 lbf;
  see `houses/catlin/notes/pvkit_rake_review.md`). Open: actual grab/frame engagement and
  Aptos-approved clamp zones, current evaluation/applicability, site rake-zone uplift reactions
  and complete PV-to-roof load path, the DLI roof load table for 873 lb of modules,
  AHJ acceptance of a rake-end pathway, the PV homerun path (keep it out of the pathway). The
  R324 text is read off [MN DLI's sheet](https://www.dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf); confirm with St Paul DSI.
  `plans/cost-options.md` lines 94 and 402 still say 5.28 kW.

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
- Make sure all handrail brackets are stock, avoid custom needs. Remaining: titanium railing brackets (aim to use standard as much as possible).
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- W-BW-SCREEN's shear role is already redundant with the garage path (graded 100%). Relaxing its 4″ edge nailing needs the reviewer to accept `canopy_garage_diaphragm.md`'s 'garage takes the whole load'.
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- Plant-room reservoir (2026-11-11): manual-fill tank, two independently timed shelf-pot circuits, one packaged wired WaterWatcher cutoff and automatic M8000-NO/RIBU1C low-water permission; shared geometry/BOM and 11.75-gal spill budget updated. Itemized provisional hardware $1,026.61 against $1,200 target/$1,500 ceiling. Still open: WaterWatcher revision/humidity/load/recovery qualification, commodity supplier SKUs/quotes and NPT/NPSM sealing interface, plumber-approved removable fill, supply-sizing basis, physical containment, electrical/hydraulic commissioning and ten-day trial. See `houses/catlin/notes/plant_reservoir.md` and its procurement CSV.
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Geometry review round 2 (2026-11-05): [report](geometry-review/REPORT.md) §1 ranks the open escalations; detail in `geometry-review/2026-11-04/adjudicated/C1..C5.md`. 0 FAIL kept. Open, by rank:
  - [ ] `D-B-SUNKEN` band header (structural project): load takedown for the stacked D-S-BALCONY/D-M-PORCH jamb packs, their bearing interfaces, LVL ply fastening, and the edge I-joist filler/backer connections (`notes/sunken_door_band_header.md` §4).
- The balcony backing's nail schedule back to the joists is undrawn (`houses/catlin/notes/balcony_fascia_mounts.md`).
  - [ ] DWV: `PR-M-BATH2-WC-VENT` runs level under the FS-M-WEST joist 016/017 + FS-M-MECH 000 seam at -13 1/2" (MN 905.3, under the bowl's real rim too; `mep.vent_connection` ADVISORY, C4 E11). A 45-degree climb is 0.21" short (7.69" of flange footprint vs 7.475" of web-zone travel), so no WC position along W-M-HS1 helps. Owner: WC to W-M-W3 bay 13-14 on a 1/4" offset flange (measured, [note](../houses/catlin/notes/bath2_vent_move_options.md) option 2: costs the floor-heat bite, the washlet outlet, the window centring), or an engineered chase.
  - [ ] ERV level 2 flat trunk residue (2026-11-08, `notes/erv_static_budget.md` §10.14): the 8x4 trunk and 6x4 neck are shop-fabricated, so `mep.fitting_pattern` stays UNKNOWN on their elbows until a shop drawing gives the throat radius, and the static budget charges each turn ASHRAE Fitting 3-5's r/W 1.0 equivalent length (59", on `DUCT-T-GALV-RECT-10`). STUDY and BED keep short straights (LIVING's cleared when it teed off BED, 2026-11-11); `DU-M-ERV-R-PLANT`'s 3 1/4x8 stack elbow is shop-made too between their tier ramps and elbows (`fitting_pattern` UNKNOWN). Both truss decks' pocket stations rest on an assumed 24" pitch until TrimJoist's and TRIFORCE's shop layouts.
  - [ ] Ceiling-collar drops (2026-11-10, `resolve/terminal_drops.py`) cover only square, plain round collars on ROUND runs. Not yet: rectangular ceiling necks (`REG-S-HP-RET`, still 4.8" off its run's end in plan and graded by the 36" plan reach) and component/inlet terminals (already on `end_terminal_ref`). The main-floor drops sit under the stamped elbow's 6" (BED 5.2", BATH1/MUD/RET3 5.6", BATH2 4.2"): `fitting_pattern` UNKNOWN until the elbow's real 1.0 D radius is read into the `DuctStandard` (STUDY climbs to 4.76" on the adjustable, `adjustable_elbows`).
  - [ ] S-102's drift trusses (from `engineering/snow_drift.drift_reach`, the function `structural.truss_reactions` grades by) carry no per-truss mark on the plan; the note names them `TRUSS-000`/`-001` (2 of 13).
  - [ ] Header residue (decision #116, `houses/catlin/notes/header_spans_r602_7.md` §5): the `5.25x7 LVL` row in `prices.toml` is an estimate ($13-24/LF material, off the house's own LVL $/bf); replace it with a retail number, ordered as a beam (R/L, probably special order; sold as a column it runs about twice that). `RL-A-HANDRAIL`'s new return beside WIN-S-STUDY3 is tight (end plate 5/8" off the RO, bar about 0.7" off the bookcase): field check. The moved FO-A-STAIR trimmer lands on the plate just past WIN-S-STUDY3's north king, ungraded. D-B-GYM's north king stands 1.2" past W-B-CS3's end on W-B-CS2's line.
  - [ ] D-M-LAUN after the 2026-11-07 move (review of 8b1cf155d). Owner: (1) **washer** (done 2026-11-07): valves behind the tower in W-M-CLN; the washer drains into the laundry tub (Minn. R. 4714.1001's adjacent-washer exception). Confirm with the AHJ against 4714.0804. The tower stands 0" off W-M-CLN against LG's 4" (guide p.14), so it needs 90-degree inlet hoses; name the washer valves at order. (2) **tub access**: 20" of the tub stands behind the strike wall; it is reached through the opening's west 8 1/4" and the 13 3/4" strip in front of the tower (pinned in `test_mep_plumbing.py`). (3) **36' width**: the header reads Boise p.4's 32' column (the widest) plus a load comparison; the literal 36' cell is p.9 Floor Beams 8'-0": 3 1/2 x 9 1/2, 2 trimmers, i.e. a 2-ply 9 1/2" LVL on doubled jacks (the engine frames one jack here; `WIN-M-DINING-E` reads its 32' column the same way). (4) **W-S-SN3's uniform load into W-M-HS3**: `resolve/stacked_ladder.py` records the FS-S-WEST line (W-S-SN2/SN3 over W-M-HS3/HS4, 256/272 bay) and lays nothing on an open-web deck; `structural.stacked_line_ladder` is UNKNOWN until TrimJoist's shop layout carries the line (a blocking panel or a truss over the wall), and the header reads "assumes a ladder in FS-S-WEST". `P-S-SN3-SQUASH` still carries BM-S-BATH-E's point. Still open: neither header nor PublishedSpan grades the guide's structure width against the derived building width.
  - [ ] Construction-set residue after items 12–19 (REPORT §1.12–19): Open: bay-cut rim conditions with no floor (A-570.x); C1 E2 interior guard fascia mount spec; LSSR2.37Z catalog name; A-301/A-204 level labels clip on ledger; MDO layer undrawn on A-508. Overprints found in review: E-101's northwest device-tag cluster (B-INV-BACKUP / B-PV-INV / B-SPARE-CHASE and neighbours), the B&B door detail's K5 leader crossing the K2 bubble (old A-514), and the old A-531's air/water/thermal continuity tags over the detail head (both renumbered into the A-560 series 2026-11-06). Detail sheets were renumbered into decimal series (`emit/draw/callouts.py` `DERIVED_SERIES`, 2026-11-06), so a family grows without overflowing A-599. The renumbering noted G-002's permit note index lists full-set-only sheets (the `permit_drop`/`permit_add` decimal-prefix catch and `visitSheets`'s string sort are fixed).
  - [ ] Owner decisions left open by the 2026-11-06 fit pass (REPORT §1.20-32): the titanium handrail fittings (no published load read; the EZA200 projection and load rating are unpublished too); C4 E8 runs vs backing; C4 E14 supply items; O2-110 pocket head (Eclisse detail). Backing bands: the owner kept BK-M-S1-HP2-BED, BK-M-S2-HP2-LIVING and BK-M-N2-HP3-STAIR.
  - [ ] Fit residue after the 2026-11-06 fit pass: no readable DensShield price (`gwb-glass-mat` unpriced, ~99 SF billed since the review); Sterling drain 8 1/4" (see the second-floor tub drain item); FX-S-SUITE-WC tank 1.09" off (flange held); Uponor LF2821050 A 14.95" (submittal) vs 14.675" carried; 8 flush boxes still on studs (`advisory.box_on_stud`); `mep_hvac.py` ~350 plant-room negative-pressure prose at 25 cfm, now 5; seat beams: the LUS26-2Z now hangs on an 11/32" filler notched round the CBSTQ strap (end gap 0.1055" vs note m's 1/8"; `notes/canopy_west_band.md` 2026-11-06 (b)). Simpson publishes no filler installation, so ask Simpson to confirm. It does not gate gravity (the beam bears on the pack); the fallback is a cast-in HETA20Z pair.
  - [ ] System 1 return relief (follows #21, b90360591): at the owner's 1/2"-3/4" undercut rule, RM-S-BED1/2/3 hold 9.7 Pa (RM-S-SUITE closed 2026-11-09 by a ducted return), RM-A-STUDIO 3.8, RM-S-PLANT 19.0 (at its 1/2"), RM-A-EAST-UNFIN 4.8 against 3 Pa, and RM-M-BED nets 5 cfm in behind sealed D-M-BED2 (`mep.door_transfer_air` ADVISORY). Choose transfer grilles, jump ducts or room returns (`notes/system1_return_path.md`). **Owner, 2026-11-07: deferred to a later pass.** Also: steel/sauna slabs are modelled cut 1/8" (steel may need ordering to size); the library interior types and the plan door symbol still use the 45 mm schematic leaf.
  - [ ] `blocking_parts.run_bands` gives a rectangular duct radius 0, so `pass_through_box` frames around its centreline: DU-S-HP-SUITE-RET's cheeks at `bearing-block-1-016` leave a 1" slot where about 8.5" is needed (66 in³ solids overlap), and the bottom-rail test ignores the duct's depth (precedent DU-S-HP-SOUTH).
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
- Autorouter open items (2026-11-11 pass; `docs/routing.md` Limitations):
  - [ ] `--tree PR-M-S-SUITE-DRAIN` (tree:second) refuses all three now that falling runs respect D pockets: WC (no plan lane; D12 held by PR-A-HW-STUBATH, D8 by DU-M-ERV-R-STUDY), TUBSH (D13 held by PR-B-CW-SUITE), LAV (head short 0.025"). The authored tub drain passes; the router cannot reach its lane because the barrel tie sits at its head (115.5") and PR-A-HW-STUBATH's inflated prism stands at 115.18"-120.43". Open: a barrel tie below its head and the router's 1/2" clearance vs the authored lane (`framing_bore_limits.md` §13).
  - [ ] `--group BATH2` lays the SH arm, 3" wet vent and dry vent and refuses TUB (held to its own vent) and WC (no tie: the wye inlets at y 262/271 on PR-B-MAIN-DRAIN block y 254-279); the partial lay grades 2 FAIL and 1 illegal bore. The authored three-vent design stands; vent-free 908.2 groups are an AHJ question.
  - [ ] Supply trunk proposals keep their finished-volume FAILs (PR-A-BAR-LAV-CW 8.96 ft in RM-S-SUITEBATH; PR-A-STUBATH-SH-CW 5.19 + 1.63 ft; PR-B-LAV-TERMINAL-CW under RM-B-BATH's ceiling): the SUPPLY-GATE band reads no room ceiling and the attic legs fall outside it. A storey-banded wall-cover gate is the tested lead (27 -> 20 FAILs, search 98 -> 180 s; `mep_supply_trunk_basis.md` §5a). Proposals through exterior bays now carry `mep.supply_freeze_exposure` FAILs (12 on trunk:CW): the router prices a bay, not the pipe's depth in it.
  - [ ] Search U-turns: `shortest_route` keys its state on the axis, not the signed heading, so a sub-inch back-step costs no turn and buys a PEX bend (23 bend-180s on the scorecard, none at a port). A search change; drain basis §4 pins its expansions.
  - [ ] Same-size I-joist siblings in one tree group do not see each other's holes (`ijoist_bores_ok` is build-time), and P8's re-lay world is built without `laid`.
  - [ ] `--lift` refuses a supply whose unlifted branch tees on its first leg (deferred: no catlin lift hits it). Fix: hold the head and search the middle (`mep_tree_ripup_basis.md` L7).
  - [ ] DU-S-ERV-HP-FEED: three 12.5" straights against two stamped 90s' 18" and a 3.4" jog (`mep.fitting_pattern` UNKNOWN). Linx publishes only rC ≈ 1.5 d, no centre-to-face (catalog REV11 p.13). Adjustable elbows were declined (0.432 -> 0.447"); Linx's die-stamped ER 90 (rC ≈ 1.0 d) is the untried option, its loss C unread.
- Air-distribution products (specified 2026-10-31, [note](../houses/catlin/notes/air_distribution_products.md)); still open:
  - Owner: the 1.1 cfm residual under 205, or the 10" hoods (needs RenewAire FA10 test data and a plate fit check) — `notes/erv_static_budget.md` §10.4, §10.6.
  - Owner/AHJ: which floor area MN 1322 R403.5 means. The engine grades finish-face room area (195 cfm required); centreline gave 205, exterior dimensions give 214, past the 210 cfm machine — `notes/erv_static_budget.md` §10.6.
  - Engine, deferred: an insulation-vs-R403.2.1 check; per-segment duct insulation; M1506.3's 3 ft exception and the operable-opening distance; checking an insulation spec's thickness against its R-value; grading a damper actuator inside a duct; an in-line damper part (`DuctPartKind` has none), so `DU-B-ERV-R-BENCH`'s 4" balancing damper (2026-11-11) is a comment, neither drawn nor billed.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
- Consider 1/2" advantech for walls sheathing, maybe 1/2" osb and tape the seams
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- Fixture connections (stations applied 2026-11-07, `houses/catlin/plan/wet_ports.py`). Still open:
  - [x] Five shower assemblies aligned (2026-11-09): shared controls/heads and approximate
    side hubs; sauna centred on its east wall, BATH2 at 48", attic arrivals above vents,
    BATH1's WC tee retained. `mep.shower_assembly_alignment` grades position and axis
    independently of manufacturer certainty. See `houses/catlin/notes/shower_assemblies.md`.
  - [ ] Sauna wet-wall release: 1/2" Durock replaces shiplap under the tiled spans, with
    packing, a local valve pocket and Delta's 2 3/4" stringer setback. **BLOCKED** pending
    documented temperature compatibility of the complete waterproofing, tape, mortar,
    collars and sealants, and the sealed foil/pan-liner transitions. Durock suitability
    alone is not system approval.
  - [ ] FS-M-WEST joist 012 (y=192") clashes, found by `scripts/render_bath2_shower_drain.py`'s
    section and graded by nothing: `PR-B-CW-TRUNK` (x 57..200") and `PR-B-CW-BATH2` run
    *inside* its web at 100 5/8" bsmt, and every branch tees there; `PR-B-CW-BATH` does the
    same along FS-M-WEST `sister-1-0` at y=243". The hot lanes at 97 7/16" bsmt
    (`PR-B-HW-BATH2`/`-KITCH`/`-SAUNA` and their y=188" legs) sit 1/8" under the joist
    underside, so the 5/8" PEX is in the bottom flange and the ceiling board, and their
    x=90/93/95" crossings plus the SH hot at 96.4" are too close to bore (ESR-1153 2x hole).
    Needs a lane redesign, plus two check gaps: `run_member_crossing` reads the centreline,
    not the envelope, and no check sees a run lying along a member.
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
- **2026 NEC residue (decision #120).** Confirm the 11 `typehaus.model.nec.UNCONFIRMED` rows
  against the printed NFPA 70-2026 (read so far only in NFPA drafts or secondary sources; the
  caveat stays until then). 120.82(C)'s resistance-heat item numbers are contested, so prose cites 120.82(C).
  690.12(C)(1)(b): the rapid-shutdown initiation device must be outdoors. Catlin models none; confirm with EG4
  what initiates shutdown on the 12kPV (does opening the CL320 meter-main do it while backing
  up the house?), then place the device. Revisit Class C SPGFCI for CKT-HP1-3 after the
  NFPA Standards Council (2026-12-15/16, ACCA/AHRI appeals); they are Class A breakers meanwhile.
- **Exterior darks are black** (2026-11-07, `houses/catlin/plan/exterior_palette.py`, `notes/exterior_darks.md`). The engine's `RAINSCREEN_BASE_Z` text still calls the base strip aluminium.
- `haus print3d --colour-groups`: per-piece colour components bucketed from `Material.color`, matched to a sample exported from Bambu Studio before shipping.
- Promote the leafless passage's drywall wrap (#122) to a `ResolvedModel.passage_wraps` record so emitters can draw the returns.
- **Consider a strongback on `FS-S-WEST`** (TrimJoist J12 at 16" o.c. now reads its own published row, `J12_FLOOR_SPAN`).
- **W-B-N2 wall-top restraint (Minn. R. 1309.0404).** `FO-M-STAIR` fills the first three joist spaces against W-B-N2 for x 10'-3"..17'-8 3/4", so no footnote f blocking can stand there and `code.MN_1309_0404_wall_top` reports UNKNOWN. 400 plf x 8' = 3,200 lb goes into the well's edge framing spanning flat between the headers: get the EOR's approved-equivalent detail (a flat strongback or a landing strut) and author it. Basis note `houses/catlin/notes/main_floor_truss_basis.md` §4.
- Aiming to keep floor transitions flush, looks like ~3/4" thickness makes this easiest. Ditra XL or Ditra Heat + Thinset + 8 mm Tile (Ditra Heat PS 5.5 mm + 3.5 mm thinset (3/8" by 3/8" notch trowel) + 10 mm tile OR Ditra Heat Duo peel and stick (PS) + 2.5 mm thinset (1/4" x 3/8" trowel) + 9 mm tile OR 1.5 mm thinset (compressed by 1/4" by 1/4" trowel) + ditra heat 5.5 mm + 2.5 mm thinset + 9.5 mm tile) == 1/2" plywood (nominal) + 7 mm LVP == 1/2" exacor (12 mm actual) + 7 mm LVP == 1/2" gypsum underlayment (fiberrock) + 6.5 mm LVP == 5/8" actual (Fiberock) underlayment + 3 mm sheet vinyl == 16 mm exacor + feather finish + 2.8 to 3 mm sheet vinyl == 3/4" hardwood ~= 7/16" pad + 1/2" pile carpet (carpet squishes at edges)
- Is TypeHaus organized such that a contractor building typehaus could hand their chatbot/llm of choice the github repo link and easily get answers they need on the design?
- Reverse osmosis sink?
- Reduce the number of LED strip controllers, ideally one or two for the soffits, not six (Zigbee vs Matter: see the cove-controller item above).
- Pantry shelves have a middle support that would ideally only go half depth (sticking to north half), right now it is rather restricting access to the west end of the pantry.
- drywall window returns need to have a paint layer (matching the room, ideally)
- Drywall returns on the rough openings that aren't doors (doors have jambs, and windows mostly have the drywall returns modeled).
- ED-B-BATH-CAN1 is placed inside the soffit
- Robot training (light switches correspond, doors open)
- Camera in ESS Room and Plant Room (for keeping an eye on them while on vacation). Something cheap, effective, and works well with the rest of the camera system
- [ ] Final canopy ColorGard sizing: check the drift-loaded tributary wedge including garage snowpack, rail/end reactions and panel attachments. Four clamps total 3,452 lbf allowable, below the 3,839 lbf wedge screening demand even with ideal sharing; one modeled row remains provisional.
- [ ] Roof N Mini wind-clamp design: check applicable product revision/design basis, corner-zone uplift demand and panel/fastener load path using the published Image II 24 ga test data. Test-data lookup is complete; clamp count and omission at the ColorGard corner still need wind justification.
- The house has four grounding rods, which might be overkill?
- Eave and gutter hardware: Select the gutter bracket and outlet, and finish the splice, fastener, and sealant details. The eave sealant product and its compatibility with the roof and membrane also need confirmation. [Eave detail (line 153)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/roof_wall_eave_detail.md:153)
- Plant-room reservoir: close WaterWatcher qualification, exact supplier SKUs/quotes and NPT/NPSM adapter seals before purchasing. Itemized estimate $1,026.61; target $1,200 plus $300 contingency under $1,500. Confirm attended removable potable filling and complete commissioning/ten-day trial. [Reservoir note](../houses/catlin/notes/plant_reservoir.md).
- Interior selections: Remaining checks include the Aquia IV height suffix, SP bowl projection, Delta stainless-stock availability, the neo-angle shower’s door opening, and whether the studio wet bar needs a stainless bowl. Bath 2’s selected surface colors still need physical-chip checks. [Interior selections (line 336)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/interior_selections.md:336)
- Other order confirmations: The Williams railing panel SKU is inferred; the Breezeway guard package, Simpson HHUS410 fastener/coating, and titanium handrail fittings still need product or order details. [Construction holds (line 29)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/construction_holds.md:29)
- Radon fan power: the future-fan junction box exists but has no specified supply circuit. The checker can pass based on a nearby box alone. Minnesota requires an actual circuit terminating at the anticipated fan location. [Rule](https://www.revisor.mn.gov/rules/1303.2402/) and we also need to double check how the exterior parts of the vent and the junction boxes are mounted to the siding (perhaps the power box can be mounted above a girt, recessed, then flashed and trimmed cutout in siding, or just surface mount)
- Replace the Custom foundation-coating color: stock Concrete Grey preserves the coating system if you accept the color change
- Replace the Fabricated plant-room service hatch: a catalog gasketed hatch may work, subject to opening, actuator-access, and membrane-seal checks. Or just clean up the duct arrangement for no service hatch (just sidewall above door?). The entire HVAC duct work to the plant room looks awkward and overly complex right now.
- **EQ-B-HP2-GYM has no condensate line.** On the south wall since 2026-11-09, its drain (~79"
  AFF, ~80 1/2" at the most Gree's 6" ceiling clearance allows) is below D-B-SUNKEN's 83" head
  4" to its west, so no gravity lane reaches the sauna floor drain, and PR-B-COND's overhead
  head still sits over the head's old station. Options worked 2026-11-11: re-site the head
  on W-B-CS3 (gravity, ~6 ft in the wall, +15 ft lineset) or a mini pump in its lineset cover.
- Attic suite simplified to unfinished space: the goal to reduce the taxable and ERV bedroom count by 1, and reduce the sq foot (leaving just the small attic study in the habitable sq footage), although likely still keeping an ERV terminal of some sort in the attic suite, and likely still basic rough in stubs for plumbing so we can realize this design later. We would still want to keep the current products used for it in the library, and a clear set of notes so we could swap these items into the design easily.
- Try to keep most interior doors as 1/2" factory undercut or privacy doors where decided
- Shower in sauna?

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


- [ ] Complete W-BW-SCREEN metal cassette engineering, support/trim details, complete loads and fabrication estimate; rerun structural and 87° door checks including all hardware. See houses/catlin/notes/entry_screen_metal_cassettes.md.
