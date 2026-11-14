# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

Sourcing quotes, construction todo doesn't belong in this document, this is just softwared and house design todo. Quotes, supplier confirmations, dry-fits, site measurements and commissioning go in `houses/catlin/notes/construction_holds.md`.

We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
Our general goals are decent longevity and quality at a reasonable price, avoiding premium items unless clearly a major improvement for our needs.
Note that many of the pinned decisions in the code base here aren't as fixed as they sometimes claim, the "fixed" decisions were usually fixed in a narrower context, and can be changed for sufficiently good reasons.

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

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

### Lighting Residuals

- **Lighting confirms left after 2026-11-07** (`houses/catlin/notes/smart_home.md`): the Omvi 3i
  is not on HA's `reolink` list (RTSP works, ONVIF unlisted); the garage GL-C-208M's Wi-Fi/Matter
  VLAN is unplanned; MITTLED
  counts one piece per run until `LightRun.modules` / `stock_length` carries its SKUs. E4 coves
  stay ~102 lm/ft per white channel (no 12 mm RGB+CCT tape reaches 250; owner accepts).
- **Owner: move the indoor cove controllers to the Matter GL-C-208M too?** The coves are the
  only Zigbee devices; doing it retires the second ZBT-2.

### MEP residuals

Live campaign record: `houses/catlin/preferences.toml`; `haus check houses/catlin --no-suppress`
is the unsuppressed score. `mep.run_interference` (2026-11-08) and `mep.riser_through_deck`
(2026-10-26) are closed with no suppressions. Supplier and utility asks for these items are in
`houses/catlin/notes/construction_holds.md`.

**Owner decisions**

**System 1 air handler in the attic** (`RM-A-EAST-UNFIN`, 2026-11-11,
`notes/flexx_ultra_geometry.md`). The room stays conditioned while it holds the unit; only its
finished area drops out.

- [ ] The emergency pan is declared (`secondary_drain_pan`, float switch stopping `EQ-M-HP1-OD`)
  but not drawn. Its rails raise the cabinet about 1", which the connectors take up.
- [ ] The lineset and control cable from `EQ-M-HP1-OD` are not routed, because refrigerant
  piping is not an engine element.
- [ ] No check grades the passageway from `D-A-STUDY` or the level service space; they exist
  only in `mep_hvac.py` prose.

**ERV**

- [ ] **`DU-ERV-EA`'s drain tee is capped** (`notes/erv_static_budget.md` §10.28): no gravity
  line reaches a receptor. Choose: the radon sump (~2 ft, gas-tight trap entry), a condensate
  pump over the lane to `PR-B-ERV-COND`, or keep emptying it by hand.
- [ ] **EQ-B-ERV's trapeze rods graze three runs** by under 1/4" in the solids audit: rod 1
  `DU-B-ERV-R-GYM`, rod 2 `DU-ERV-EA`'s wrap, rod 3 / strut 2 `PR-B-ERV-COND`. No check grades
  `equipment_hangers` against runs; add one (or route them through `run_interference`) and
  nudge the rods, rather than leave it to the crew.

**Plumbing**

- [ ] **Basement backwater protection, before under-slab rough-in.** Once the upstream
  manhole-cover elevation is known (construction holds), compare it with the basement fixture
  floors under UPC 710.1 and protect only the affected low branches.
  [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- [ ] **Water-heater thermal expansion.** After the SPRWS answer (construction holds), model a
  listed expansion tank on the heater's cold inlet downstream of `PA-B-WH-STOP-CW`, plus a PRV
  if static pressure is over 80 psi. `PipeAccessoryKind` has neither kind yet.
  `PA-G-HYD-BFP` serves only the hydrant, so the meter set is the only possible check valve
  (`notes/water_service.md` §4).
- [ ] **Condensate pump.** There is no element for one (`PipeAccessoryKind` has no pump).
  `PR-B-COND-HP2-GYM` is pumped from the head's lineset cover. Pick a UL 778 unit, give it
  power and a float cut-out, and add a `CONDENSATE_PUMP` kind.

**Engine**

- [ ] `REG-S-HP-RET`'s 24x12 filter box is authored as its 15 1/8" neck run (decision #129
  terminal drop), not as a drawn drop. The sweep now draws a vertical rectangle at its true
  hu×hv, so modelling the box itself is a separate redesign, not an engine fix.
- [ ] A leg running along a joist bay inside the ceiling-board plane is graded by nothing when the
  room declares `exposed_services` (found 2026-11-13: `PR-B-HW-SUITE`'s old y=204" leg sat in the
  stair hall's board). Decide whether exposed services pardon a run inside the board itself.

**Autorouter.** `docs/routing.md` Limitations covers the open supply-trunk finished-volume and
freeze FAILs, search U-turns, stack-rung refusal cost, and `--lift` on a first-leg tee. Two
items have details that are recorded only here:

- [ ] `--tree PR-M-S-SUITE-DRAIN` lays the LAV on the stack (rung 107.875, `mep_tree_ripup_basis.md`
  §6) but refuses TUBSH and WC at every rung. Both are real holds: trusses y=224/240 leave only D13,
  held by PR-B-CW-SUITE (§13), D14 likewise, and the WC's D12 is PR-A-HW-STUBATH's. The authored tub
  lane (west in the 241.75..254.25 bay, north through the y=256 truss's D13) is never reached: the stack
  column is bracketed by PR-M-KITCH-VENT and W-M-CLN's plates, and no single blocking prism is pinned.
  The LAV proposal still starts at the fixture floor (120") rather than its port (141.5").
- [ ] `--group BATH2` refuses TUB (held to its own vent) and WC (no tie: the wye inlets at
  y 262/271 on PR-B-MAIN-DRAIN block y 254-279). The partial lay grades 2 FAIL and 1 illegal
  bore. The authored three-vent design stands; vent-free 908.2 groups are an AHJ question.

  The strongest findings, in priority order:
1. High: PEX bends can overlap despite each passing clearance checks. The search checks each bend independently, without tracking straight length between bends. A small reproduction priced two 4″-radius bends separated by only 1″ as valid field bends; their tangent lengths require 8″. Track distance since the previous turn and enforce combined take-offs, including room for fittings when field bends cannot fit. [search.py (line 215)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/routing/search.py:215)
2. High: later alternatives lose gravity metadata. Repricing returns a fresh Route when coordinates match, dropping the searched start elevation, vent take-off, vent context, and condensate grade. Those values affect proposal geometry and vent construction. I reproduced the metadata loss. Preserve the original route and replace only its pricing fields. [alternatives.py (line 102)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/routing/alternatives.py:102)
3. High: saved proposals omit cleanouts included in evaluation. Console rendering and candidate grading include DrainCleanout elements, but JSON serialization and saved proposed.py omit them. I reproduced this discrepancy: accepting the saved source produces a different design from the one graded. Serialize all proposed elements through one shared path. [route_report.py (line 55)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/cli/route_report.py:55)
4. High: the scorecard discards evaluation refusals. It extracts only .introduced from the evaluation. A candidate that cannot resolve consequently supplies an empty finding list, allowing zero evaluation FAILs/UNKNOWNs to conceal an ungradable result. I confirmed this with a mocked resolver refusal. Preserve evaluation status and coverage, and make an evaluation refusal fail regression checks. [route_scorecard.py (line 108)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/cli/route_scorecard.py:108)
5. Major selection improvement: grading cannot change the campaign winner. Campaigns rank by refusals, skips, and cost, then evaluate only the winner. A cheaper network with construction failures can therefore win without a cleaner alternative being graded. Evaluate a bounded shortlist and distinguish complete, constructible networks from provisional ones before comparing cost. [cmd_route_house.py (line 127)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/cli/cmd_route_house.py:127)
6. Medium: room penalties depend on midpoint sampling. An entire edge is charged—or exempted—according to whether its midpoint lies inside a room. This can misprice substantial travel through finished space and change the preferred lane. Charge the actual intersection length with each room’s volume. [graph.py (line 432)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/routing/graph.py:432)
7. Medium: duct alternatives share a cumulative label cutoff. Separate alternative searches reuse one refusal report, whose cumulative reached count controls termination. Earlier searches consume later searches’ budgets, while elapsed-time budgets restart independently. Separate per-search limits from aggregate diagnostic counts. [duct_search.py (line 215)](/Users/colincatlin/Documents-NoCloud/TypeHaus/packages/engine/src/typehaus/routing/duct_search.py:215)
For your real-world objective, I would fix those correctness issues before tuning weights. Then prioritize the documented U-turn problem and finished-volume/freeze failures. Construction violations should determine candidate eligibility; fitting, penetration, access-panel, and support costs should distinguish the eligible routes.

For token efficiency, --summary is a useful foundation, but it retains all evaluation messages and most refusal details. Add a bounded decision view containing:
- Completion and grading status.
- FAIL/UNKNOWN counts grouped by check and blocker.
- A few representative findings, with references into the full artifact.
- Length, fittings, penetrations, cleanouts, and unresolved construction obligations.
That would let subagents compare candidates without repeatedly reading geometry or duplicated diagnostic prose.

### Performance / energy follow-ups

- **PV residue after the R324.6 re-lay** (18 x Aptos DNA-108-BF10-410W bifacial, portrait, one
  row per plane, 18.0" hull ridge setback, 36" north-rake pathway; `code.R324_rooftop_pv_access`
  passes). Published PVKIT grab-capacity lookup is complete (EdgeGrab 353 lbf / MidGrab 861 lbf;
  see `houses/catlin/notes/pvkit_rake_review.md`). Open: actual grab/frame engagement and
  Aptos-approved clamp zones, current evaluation/applicability, site rake-zone uplift reactions
  and complete PV-to-roof load path, the DLI roof load table for 873 lb of modules,
  AHJ acceptance of a rake-end pathway, the PV homerun path (keep it out of the pathway). The
  R324 text is read off [MN DLI's sheet](https://www.dli.mn.gov/sites/default/files/pdf/fs_res_solar.pdf); confirm with St Paul DSI.
  `plans/cost-options.md` lines 94 and 402 still say 5.28 kW.

### Someday (low value)

- **Derive a fixture-supplied box** (Bantam's JB-0501) so SCONCE-STAIR can state its canopy.
- **Pipe support spacing is ungraded** (UPC Table 313.3 via Minn. R. 4714.0313, plus MN Table
  313.3.1); the profile says so. Needs a `support_spacing_in` on `PipeRun` and a
  `mep.pipe_support` check. Field-inspected, not a permit gap.
- [ ] Deferred checks: insulation vs R403.2.1; per-segment duct insulation; M1506.3's 3 ft
  exception and the operable-opening distance; an insulation spec's thickness vs its R-value;
  a damper actuator inside a duct.

## Questions

- **Is a silt fence required at all?** The owner doubts it on a flat, small residential lot.
  It is drawn on the W/E lot lines for now (`houses/catlin/plan/site.py`); ask St Paul DSI at permit.
- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists. (desired but not as explicitly modeled)
 - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
   bathroom ceiling should be open. That is a design question, not a cleanup.
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
- Plant-room reservoir: close WaterWatcher qualification, exact supplier SKUs/quotes and NPT/NPSM adapter seals before purchasing. Itemized estimate $1,026.61; target $1,200 plus $300 contingency under $1,500. Confirm attended removable potable filling and complete commissioning/ten-day trial. [Reservoir note](../houses/catlin/notes/plant_reservoir.md).
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Geometry review round 2 (2026-11-05): [report](geometry-review/REPORT.md) §1 ranks the open escalations; detail in `geometry-review/2026-11-04/adjudicated/C1..C5.md`. 0 FAIL kept. Open, by rank:
- The balcony backing's nail schedule back to the joists is undrawn (`houses/catlin/notes/balcony_fascia_mounts.md`).
  - [ ] DWV: `PR-M-BATH2-WC-VENT` runs level under the FS-M-WEST joist 016/017 + FS-M-MECH 000 seam at -13 1/2" (MN 905.3, under the bowl's real rim too; `mep.vent_connection` ADVISORY, C4 E11). A 45-degree climb is 0.21" short (7.69" of flange footprint vs 7.475" of web-zone travel), so no WC position along W-M-HS1 helps. Owner: WC to W-M-W3 bay 13-14 on a 1/4" offset flange (measured, [note](../houses/catlin/notes/bath2_vent_move_options.md) option 2: costs the floor-heat bite, the washlet outlet, the window centring), or an engineered chase.
  - [ ] Header residue (decision #116, `houses/catlin/notes/header_spans_r602_7.md` §5): the `5.25x7 LVL` row in `prices.toml` is an estimate ($13-24/LF material, off the house's own LVL $/bf); replace it with a retail number, ordered as a beam (R/L, probably special order; sold as a column it runs about twice that). `RL-A-HANDRAIL`'s new return beside WIN-S-STUDY3 is tight (end plate 5/8" off the RO, bar about 0.7" off the bookcase): field check. The moved FO-A-STAIR trimmer lands on the plate just past WIN-S-STUDY3's north king, ungraded. D-B-GYM's north king stands 1.2" past W-B-CS3's end on W-B-CS2's line.
  - [ ] D-M-LAUN after the 2026-11-07 move (review of 8b1cf155d). Owner: (1) **washer** (done 2026-11-07): valves behind the tower in W-M-CLN; the washer drains into the laundry tub (Minn. R. 4714.1001's adjacent-washer exception). Confirm with the AHJ against 4714.0804. The tower stands 0" off W-M-CLN against LG's 4" (guide p.14), so it needs 90-degree inlet hoses; name the washer valves at order. (2) **tub access**: 20" of the tub stands behind the strike wall; it is reached through the opening's west 8 1/4" and the 13 3/4" strip in front of the tower (pinned in `test_mep_plumbing.py`). (3) **36' width**: the header reads Boise p.4's 32' column (the widest) plus a load comparison; the literal 36' cell is p.9 Floor Beams 8'-0": 3 1/2 x 9 1/2, 2 trimmers, i.e. a 2-ply 9 1/2" LVL on doubled jacks (the engine frames one jack here; `WIN-M-DINING-E` reads its 32' column the same way). (4) **W-S-SN3's uniform load into W-M-HS3**: `resolve/stacked_ladder.py` records the FS-S-WEST line (W-S-SN2/SN3 over W-M-HS3/HS4, 256/272 bay) and lays nothing on an open-web deck; `structural.stacked_line_ladder` is UNKNOWN until TrimJoist's shop layout carries the line (a blocking panel or a truss over the wall), and the header reads "assumes a ladder in FS-S-WEST". `P-S-SN3-SQUASH` still carries BM-S-BATH-E's point. Still open: neither header nor PublishedSpan grades the guide's structure width against the derived building width.
  - [ ] Owner decisions left open by the 2026-11-06 fit pass (REPORT §1.20-32): the titanium handrail fittings (no published load read; the EZA200 projection and load rating are unpublished too); C4 E8 runs vs backing; C4 E14 supply items; O2-110 pocket head (Eclisse detail). Backing bands: the owner kept BK-M-S1-HP2-BED, BK-M-S2-HP2-LIVING and BK-M-N2-HP3-STAIR.
  - [ ] Fit residue after the 2026-11-06 fit pass: no readable DensShield price (`gwb-glass-mat` unpriced, ~99 SF billed since the review); Sterling drain 8 1/4" (kept by owner, 2026-11-08; `notes/framing_bore_limits.md` §12); FX-S-SUITE-WC tank 1.09" off (flange held); Uponor LF2821050 A 14.95" (submittal) vs 14.675" carried; 8 flush boxes still on studs (`advisory.box_on_stud`); seat beams: the LUS26-2Z now hangs on an 11/32" filler notched round the CBSTQ strap (end gap 0.1055" vs note m's 1/8"; `notes/canopy_west_band.md` 2026-11-06 (b)). Simpson publishes no filler installation, so ask Simpson to confirm. It does not gate gravity (the beam bears on the pack); the fallback is a cast-in HETA20Z pair.
  - [ ] Smaller open items, by cluster file: C1 E11 (O1-102 relief doors), O2-110 pocket head (Eclisse detail); C2 E12 rest; C3 I4-004/005; E8, E14. SCONCE-CANDLE (Livex 4451-04, no published backplate) and SCONCE-STAIR (see `BoxRow` shape) state no `LuminaireType.canopy`; `place_box` centres a wall-light box on the body's mid-height, not its canopy; the WAC LINE's in-box transformer is not in `electrical.box_fill`; no check grades a run through a room's `ceiling_lining`.
  - [ ] TB-SG-W1/E1 closure boards 8" vs FT-B-S2/S3 at 10" (F5-104); FB-B-CS drain-tile ring 1" into FT-B-S2/S3 (F5-105); 14" north-entry pier cage 0.806% (engineer hold, C2 E6).
- **Max Light's 35 mm sill face cannot clear the 1 1/2" pan back dam** (`resolve/flashing_config.back_dam_m`; Andersen's 1⅛" rail had the same clash until 2026-11-13): the nine escape units' stools still pass through the dam and its support (the `opening_sill_pan|window_stool` ratchet pairs). Get Słowińscy's sill section and back-dam detail, then lower the dam for those openings, shim the unit, or seat the stool above it.
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X) (Scuff-X is held for this item; the house paint systems are decision #113, houses/catlin/notes/paint_selection.md), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- [ ] Exterior doors, after the 2026-11-13 no-cantilever pass (approaches rest at both ends: `notes/french_door_catalog_installation.md` §2/§6, `notes/exterior_door_structural_mount.md`):
  - **Engineer the girt sill course's block connection** under the approaches of D-S-BALCONY, D-M-PORCH and D-M-ENTRY. Each block hangs on one TimberLOK in shear through a 6" stack. ESR-1078 Table 4 needs 5" of main-member penetration (this gets 1 1/2") and leaves NDS lateral design out of scope. A first NDS pass gives ~120 lb per screw at wet service against the notes' 300 lb point load. Options: more blocks/screws per door, a heavier dowel, or accept a uniform-only basis for a landing (R301.5's 300 lb governs stair treads).
  - Supplier holds (no inquiries by scope): installed pan/sweep/hinge sections; D-S-BALCONY's XXXXW nose 1.46" past the girt course and a prehung 4-9/16" jamb on the 5-5/8" ZAI5625FN; the main doors' approach plate sections; assembled-unit label/warranty; the 06-002 submittal (CPD, NFRC/NAFS, astragal, Endura sill, PanoLock+); Proglaze ETA flashing-end application; D-B-SUNKEN's PVC sheet / drainage board / sealant compatibility. Complete preferred/Tru-Defense prices remain unavailable publicly.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
- Consider 1/2" advantech for walls sheathing, maybe 1/2" osb and tape the seams
- Pg 288 of the book has a roof eave detail where the roof and drip flashing alone extend out about an inch (no metal or sheathing).
- Fixture connections (stations applied 2026-11-07, `houses/catlin/plan/wet_ports.py`). Still open:
  - [ ] Sauna wet-wall release: 1/2" Durock replaces shiplap under the tiled spans, with
    packing, a local valve pocket and Delta's 2 3/4" stringer setback. **BLOCKED** pending
    documented temperature compatibility of the complete waterproofing, tape, mortar,
    collars and sealants, and the sealed foil/pan-liner transitions. Durock suitability
    alone is not system approval.
  - APPL-LG-DISHWASHER: a Product and price row for the 48" braided 3/8" supply its `hose_length` assumes.
  - The floor-fed WC stops (FX-M-BATH2-WC, FX-S-BATH1-WC) are house setout, APPROXIMATE.
  - The washer's real valves are mid-run tees, which the endpoint grade cannot see.
- Electrical placement residue: `ED-S-NCLOSET-SW` has no clear bay on W-S-CLN-S (west lands in the door opening, east in W-S-BW3), so it stays over a king with the advisory unless the door or switch moves. HLG-100H AC splice boxes (RACO 232) are billed, not drawn. `notes/basement_surface_wiring.md` lines 133 and 147 still place `ED-B-PLAY-N-SW` on its old wall. Bench-pair the DAWSC-1BW to the flood's D315S before the board goes up.
- Block load residual (verified against the hand notes 2026-11-08: 30,183 Btu/h heating, 16,522 sensible + 6,076 latent, no engine bug): the wall load uses the card R-43.6 against the R-39.8 to 37.9 oracle, and the ERV SRE is rated at 83 cfm against about 204 delivered. Together about +3 to 4% heating, no equipment change (`houses/catlin/notes/block_load_basis.md` §10).
- Rainscreen closures: at the four outside corners the base and band strips run into the corner trim and the adjoining wall's base trim; stop them at the corner now that the corners land on the strip top (`resolve/rainscreen_closures.panel_bottom_z`).
- **`RL-A-FLIGHT-GUARD` newel junction (not graded).** Near the 25'-5 1/8" newel its post (top 20'-2 1/4") and top rail run into `FO-A-STAIR`'s trimmer pack (19'-0 1/8"..20'-0", south of the well edge), and `RL-A-STAIR`'s surface posts (since 2026-10-31) stand ~1 1/8" south of its bracket line: the junction needs detailing, and the surface bases need blocking under the pack (4 GRK RSS, SG >= 0.50).
- Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing and subfloor nailing, fascia/trim screws, window-install screws, and the HL angles' site-length through-bolts.
- Backup battery, still open (`houses/catlin/notes/backup_power.md` §11-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; how the 12kPV's load port behaves on its "No Battery" setting (ask EG4); its GEN port rating; declare future storage and V2H on the Xcel application; DSI's position on a UL 9540 3rd-ed. DC ESS battery; a freeze drain-down plan; a small LFP UPS for Home Assistant, the router and the leak valve. After the 2026-11-02 trim the always-on tier passes summer's 48 h and the bridge (0.28 kWh margin) and still fails December's cycle (§6).
- V2H spare raceway (routed 2026-11-07, `backup_power.md` §10): add PVC 2" rows to `prices.toml [conduit_fittings]`; the ICF supplier/engineer details rebar round the three 6" CD-GAR sleeve boxouts in W-B-N2 and W-GF-S2. `CD-B-GAP-EV` ends at +5'10" abs while `ED-G-EV-1450` is at 48" AFF (+14" abs): an existing over-rise to check.
- **2026 NEC residue (decision #120).** The rows in `docs/nec-2026-paraphrase.md` are read in
  the printed code (2026-11-13/14); its **Engine** lines list the rules no check grades. The
  rest of `model/nec.py` is still unread (below), though `UNCONFIRMED` is empty.
  - Catlin, owner to decide: the 250.104(A) water bond BC-B-WATER is #4 Cu, under Table
    250.102(C)(1) on every basis (printed table read): **#2 Cu** for a 320 A service (310.12(A)
    at 83%: 300 Cu / 400 Al; also 2 x 4/0 Al summed), **#1/0 Cu** only if the service counts as
    400 A (400 Cu / 600 Al); a larger utility lateral raises it (3/0 Cu cap). The GECs (#6 rods,
    #4 Ufer) meet 250.66(A)/(B) on every basis. Open: the lateral's size (Xcel/electrician).
  - The 4/0 Al SER feeders (180 A at 75 degC) behind the 200 A mains are permitted by 240.4(B)
    (Table 240.6(A): no 180 A, 200 A next); 310.12(B) cannot size them. Loads 136 A, 121 A.
  - **ESS, Articles 706/480 (read; `docs/nec-2026-paraphrase-480-706.md`), owner questions:**
    (1) 706.15(B) wants an outdoor initiation device that stops all ESS export; `ED-M-RSD-INIT`
    is the candidate, but `backup_power.md` section 8 says it opens the ESS only "with supported
    EG4 batteries in closed loop", unverified, and not whether the load port (backup panel) and
    battery contactor drop too: ask EG4. (2) 480.7(B) reads, for a dwelling, as an outdoor
    battery disconnect or remote control labelled EMERGENCY DISCONNECT with no 60 V condition
    (the ~51 V WallMount is under 60 V, so (A) asks for no dc disconnect): AHJ question; if
    it applies, `ED-M-RSD-INIT` could be the remote control (it must open the battery) and
    must then carry the EMERGENCY DISCONNECT label, not only "PV rapid shutdown". (3) 706.15(D)
    wants a disconnect within sight of the separate, field-serviced battery: none is modelled;
    is the WallMount's own breaker it (EG4's listing)? Also unmodelled: 706.15(C) "ENERGY
    STORAGE SYSTEM DISCONNECT" label, 480.7(F) nominal-voltage label near the battery,
    480.10(E) door hardware if the AHJ calls `RM-B-ESS` a battery room. Battery voltage is not
    authored (14.3 kWh / 280 Ah is about 51 V). **Printed 690/705 (2026-11-14) does not settle
    (1) or (2):** 690.12(C)(2)(a) makes "off" shut down the PV systems only; if a remote-operated
    disconnect is ever put under that switch, 705.20(C)(3) wants one that opens by itself on loss
    of control power (not a shunt trip); 705.20(F) and 404.8(C) are the backfeed warnings;
    705.10/480.7(G) put any battery disconnect's location on the service plaque.
  - **Art. 440 (read; `docs/nec-2026-paraphrase-440.md`):** `electrical.hvac_disconnect` passes
    the three outdoor units' disconnects (in plan sight) and is UNKNOWN for `EQ-S-HP1-AH`
    (no disconnect on `CKT-HP1-AH`: integral, or a service switch in the attic?). HP2's and
    HP3's nameplate MCA and maximum OCPD (30 A, 15 A breakers) are not authored: add
    `min_circuit_ampacity_a` and `max_overcurrent_a` to the equipment types from the Gree
    submittals to grade 440.4(B)/440.22/440.35. 440.8 bath zone: `electrical.bath_hvac_zone`
    passes (nearest unit 6.1 ft). Owner questions: lockable or tool-opened enclosures for the
    outdoor `ED-M-HP1/2/3-DISC` (440.11); give `ED-T-DISCONNECT-3R` an ampere rating for
    440.12(A)(1) (115% of the MCA/RLA); available fault current for 440.10 (440.4(B) Ex. 3
    exempts dwellings from marking a rating). No room A/C or generator exists (Part VII, 445).
  - **Art. 424 (read; `docs/nec-2026-paraphrase-424.md`):** `electrical.space_heat_circuit`
    passes all eight heating circuits (125% and GFCI on both floor-heat cables). Owner
    questions: lock-off or service-disconnect reading for the heating breakers (424.19), the
    Schluter thermostat as disconnect (424.20(A)), and a 424.47 label on `ED-B-PANEL` slots 29
    and 33. The GFPE floor-heat item is closed (2026 asks for GFCI).
  - **Arts. 404/406/408 (partial; `docs/nec-2026-paraphrase-404-408.md`):**
    `electrical.bath_receptacle_zone` is UNKNOWN for `ED-M-BATH2-TUB-RC` (the Bask outlet,
    inside the 3 ft zone, 406.9(C)(1): AHJ question) and `ED-A-STUBATH-GFCI` (is the shower
    glass a fixed barrier?). `ED-S-PLANT-HEAT-RC` is on a D315S relay: mark it "controlled"
    (406.11(D)). Receptacle types need `weather_resistant`/`in_use_cover` fields for
    406.9(B)(1). 408.6 needs an available fault current at the service and SCCRs for the
    panels (none authored); 404.8(C) backfeed signs (ESS/V2H) are unmodelled.
  - 625.43(C): `CKT-EV-1450`'s only disconnect is its breaker in the basement, remote from the
    EVSE; a plaque on the unit locating it is not modelled (`electrical.evse_circuit`
    advisory). 625.40/.41/.54 pass or are N/A. A V2H charger (`CD-B-V2H-SPARE`) needs 625.48
    (listed and marked; Article 702 or 705; 625.47 if it takes its own feeder).
  - 110.26 not graded: the door-swing sentence (doors open to 90 degrees leave 24 in. x 6 1/2
    ft), (D) lighting (the panels' room `RM-B-FURNACE` has four luminaires on plain switches;
    no typed marker for an automatic-only control) and the (E)(2) outdoor zone of the
    meter-main (nothing foreign authored within 6 ft).
  - 310.15(C)(1) / 334.80(A): `electrical.nm_sleeve_ampacity` passes all 12 derived EMT NM
    sleeves (77 in. worst, four conductors at 80%: 24 A capped at 20 A on a 20 A breaker, no
    margin). Overhead NM bundles are not modelled.
  - Revisit Class C SPGFCI for CKT-HP1-3 after the NFPA Standards Council (2026-12-15/16,
    ACCA/AHRI appeals); they are Class A breakers meanwhile.
  - Not modelled: 120.11(A) motor treatment inside 120.6, 120.7(C)(2) minimum operating
    current for a PCS that also monitors noncontrolled loads, 314.16(B)(2)/(3)/(6) box-fill
    allowances (clamps, support fittings, terminal blocks), 314.24(B) projection add-ons.
  - Engine checks that read the printed rule loosely (audit 2026-11-13):
    `receptacle_spacing` credits a receptacle on the other face of a wall and breaks wall space
    at a stationary appliance only beside a cabinet (no fireplace break); (C)(1) Ex. 1 breaks
    the wall line only where the appliance touches it, not at 12"/18"; `island_receptacle`
    skips peninsulas, has no (C)(3) 20" window and FAILs where (C)(2) provisions would do;
    (D) measures to the vanity, not each bowl, and accepts a free-standing receptacle;
    `appliance_receptacles` never traces an appliance's own circuit; the AFCI occupancy table
    reads STORAGE as closets and omits STAIR and a UTILITY room holding laundry; (G)(1) treats
    an unset mount as the floor; `code.NEC_250_94_ibt` is N/A without a data entry and models
    no terminal count, external mount or building-disconnect IBT; `gec_size` grades only the
    250.66(A)/(B) caps; the water bond is graded for connection, not size; no field states
    250.24(B) neutral isolation; 705.12 tries (B)(1)/(B)(2)(a) only and cannot see the
    opposite-end placement or label; `code.NEC_250_32_separate_buildings` traces circuits, not
    feeders (a garage subpanel reads N/A) and not the EGC; `rod_electrodes` skips 250.53(A)(4)
    drive and (B)/(D); 250.64 protection is unread; no service conductor size, so Table 250.66's
    general rows and 250.64(D) stay ungraded.
  - Cheap checks still missing: 210.52(F) laundry, 210.52(H) hallways, 210.11(C)(4) garage
    circuit.
  - **Still to read in print.** For each one: paraphrase it, and either confirm the
    `model/nec.py` row or put it in `UNCONFIRMED`. Numbers not yet in `nec.py` are 2023
    numbers, to be confirmed.
    - Cited and graded: 110.26(A)/(E)(1) (`electrical_panel_space`); 215.18 (SPD);
      240.24(A), 404.10(A)(2) (`electrical_panel_height`); 300.24 and 352/358/362.26
      (`conduit_bends`); 300.6, 300.7(A)-(G), 300.8(A)(3), 300.9(A) (`conduit_burial`, `conduit_damage`); 334.15(B)/(C); 210.70(A)(3); 130.2 (PCS listing).
      (690.12, 690.47, 705.10, 705.20 and 710.10 are read: `docs/nec-2026-paraphrase-690-705-710.md`.)
    - PV, interconnection and stand-alone, **still to read in print**: 690.1-690.9(A)
      (incl. 690.7 voltage, 690.8 circuit current), 690.13-690.43 apart from what is read
      (690.15(B) onward, 690.31, 690.41, the start of 690.43), 705.1-705.4, the end of
      705.25(C), 705.28 (circuit sizing), 705.30 (overcurrent), 705.40 onward, 710.12 onward.
    - **Owner questions, Articles 690/705 (2026-11-14):** (1) EG4: does opening the 12kPV RSD
      loop stop the load port and the battery contactor too (706.15(B))? (2) 480.7(B): AHJ
      reading, and can `ED-M-RSD-INIT` be the emergency disconnect's remote control? (3) EG4:
      with `CKT-ESS-GRID` open, can the grid-port terminals stay energized (705.20(F) warning)?
      (4) 705.12(B)(2)(a): `CKT-ESS-GRID` is at slot 40 of 54 with ten spaces below it; is that
      "the opposite end" to the AHJ, or move it (the last row cannot take a 2-pole)? 241.7 A
      of 270 A. (5) Author the labels (690.12(D) building label at `ED-M-METER`, the (D)(2)
      switch wording, the 705.10 plaque with its emergency phone, the 705.12(B)(2)(b) warning
      at `ED-B-PANEL`)? None is modelled. (6) Which device is the 690.13 PV system disconnect
      (the 12kPV's DC switch: lockable, marked)? Does the 12kPV carry a listed PV arc-fault
      interrupter (690.11, strings 383.8 V cold)? What is each module receiver's listed
      shutdown voltage (690.12(B)(1) wants 30 V in 30 s outside the array boundary)?
    - Cited but used by nothing (read them, or drop the constant): 120.5(C),
      120.41, 342.26, 344.26, Table 352.30, 358.30, 362.30, 410.10(D), Ch. 9
      Table 4 and Note 2.
    - Not cited, but Catlin triggers them:
      - Art. 680 spa (read 680.1-680.27(A), 680.34-680.54; 680.27(B)-680.33 unread):
        `code.NEC_680_spa` grades `CKT-SPA` (Class A GFCI PASS, 680.41(A) N/A). The tub is not
        modeled, so 680.13 (`ED-B-SPA-DISC`), 680.22/.41(B) distances and 680.26 bonding are
        UNKNOWN. Catlin must author: an `EquipmentKind.SPA` with footprint and
        `spa_self_contained`; in-ground vs listed aboveground (the 680.42(B) waiver), rim
        height, perimeter paving; metal within 5 ft (`W-SG-W1`, railings); `CKT-SPA`'s EGC and
        wiring method (680.7, 680.14; today EMT). See `docs/nec-2026-paraphrase-680.md`.
      - 225.41, 230.70: no field marks an emergency disconnect, its marking or a
        short-circuit rating, so an indoor service disconnect stays UNKNOWN. Also ungraded:
        230.70(B) marking and (D) plaque for the PV/ESS disconnects, 230.71 count, 230.82
        supply-side list, 230.90 Ex. 5, and 225.30/225.31/225.33-225.39 (see the garage bullet).
      - The sauna heater's article and listing rule: not in Article 424 as printed, still
        unlocated.
      - 210.63 (service receptacle). Art. 440 is read in full; Article 445 only to 445.12(B).
      - 422.13 and 422.31: water heater and fastened appliances.
      - The opening of 406.9(B), the rest of 406.14 and 408.4, and the 406.30(C) Ex.
        electronic-switch rule: unread. A page prints switch marking and electronic switches as
        406.48/406.50 while 404.20 prints the same marking text: the numbering is unresolved.
      - Article 300 (read 2026-11-14, `docs/nec-2026-paraphrase-300.md`; renumbered: damage is
        300.6, underground 300.7, firestop 300.23): **still to read** 300.2-300.3; 300.9(A)(2)
        through 300.21 (support, boxes at splices, free conductor length, securing, raceway
        fill); 300.25(C) onward; 358.10 (Table 300.7(A) Note 6) and the per-raceway
        bend sections. **Owner questions:** (1) `SL-WK-C` carries no vehicles? With its west edge
        3-3.5 in. short of the 6 in. the walk row needs, the buried EV (`CD-B-GAP-EV`, 14.2 in.
        under the walk) and V2H (`CD-B-V2H-GAP`, 13.8 in.) legs read 18 in. required: widen the
        walk, move the runs east, or bury 4 in. deeper? (2) buried EMT: which corrosion
        protection, which conductor type (wet-rated), and is the V2H pipe Schedule 80 throughout
        (the model holds only `pvc`)? (3) is `CD-B-SPA`, cast into `W-SG-W1`, acceptable to the
        inspector? (4) a seal at the warm end of each raceway leaving the house (300.9(A)(1))?
        (5) a modelled fire-resistance-rated assembly for 300.23 (ESS closet is an owner standard).
      - 210.70(A)(2) stair switching, 210.19/210.20 continuous loads.
- **Rapid-shutdown initiator** (`ED-M-RSD-INIT`, `backup_power.md` §8): confirm the IMO
  ESS-RSD01's UL 508i listing and file number, and its rating (IMO 48 VDC vs the Fronius
  42,0440,0338 listing's 96 VDC) before buying; confirm with EG4 what initiates shutdown on the
  12kPV and whether the RSD loop is normally closed (wiring guide) or open (QSG v1.3.2), then
  wire to the delivered board; route the Class 2 pair from the `CD-M-RSD-INIT` stub to
  `EQ-B-ESS-INV` (fished by the electrician; `haus route` found no lane); label the switch
  with the printed 690.12(D)(2) wording, on or within 3 ft of it. Printed 690.12(C)(1)(b) is
  read and graded (`code.NEC_690_12_initiation`, PASS: outdoors); (C)(1)(a) wants a kind the
  12kPV instructions name, and the 690.12(D) building label at `ED-M-METER` is also owed.
- `ED-B-PLAY-N-RC2`..`RC5` (theater, 2026-11-13) were placed to close the 210.52(A) gaps
  between the sconces and tapestries; confirm against the AV and seating layout.
- `test_electrical_circuits.py`: `test_catlin_panel_schedule_is_derived`,
  `test_catlin_panel_spaces_fits_the_54_space_enclosure` and
  `test_model_json_carries_the_electrical_takeoff` expect 44 circuits / 40 slots; catlin has
  45 / 41 since a recent circuit was added. Update the counts with that circuit's reason.
- `haus print3d --colour-groups`: per-piece colour components bucketed from `Material.color`, matched to a sample exported from Bambu Studio before shipping.
- Promote the leafless passage's drywall wrap (#122) to a `ResolvedModel.passage_wraps` record so emitters can draw the returns.
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
- The house has four grounding rods, which might be overkill? Also the grounding junctions may be in the wrong spots.
- Eave and gutter hardware: Select the gutter bracket and outlet, and finish the splice, fastener, and sealant details. The eave sealant product and its compatibility with the roof and membrane also need confirmation. [Eave detail (line 153)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/roof_wall_eave_detail.md:153)
- Interior selections: Remaining checks include the Aquia IV height suffix, SP bowl projection, Delta stainless-stock availability, the neo-angle shower’s door opening, and whether the studio wet bar needs a stainless bowl. Bath 2’s selected surface colors still need physical-chip checks. [Interior selections (line 336)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/interior_selections.md:336)
- Titanium handrail fittings: the tube is 42.0 mm, stock fittings are 42.4 mm. Measure each against the tube and buy fittings rated >= 0.9 kN before ordering. `notes/titanium_handrail_backsplash.md` §2.
- Attic suite simplified to unfinished space. Done 2026-11-11: the bedroom count (RM-A-STUDIO is `Occupancy.HOBBY`, a craft room, so R403.5 drops 15 cfm) and a finished-area report that already leaves out RM-A-EAST-UNFIN and RM-A-POCKET (4,021 sf finished vs 4,898 CFA). Still open, if wanted: take the suite itself out of the finished area (leaving just the small attic study), although likely still keeping an ERV terminal of some sort in the attic suite, and likely still basic rough in stubs for plumbing so we can realize this design later. We would still want to keep the current products used for it in the library, and a clear set of notes so we could swap these items into the design easily.
- Try to keep most interior doors as 1/2" factory undercut or privacy doors where decided
- Door residue: the steel and sauna slabs are modelled cut down 1/8" (the steel may need ordering to size); the library interior types and the plan door symbol still use the 45 mm schematic leaf.
- Shower in sauna?
- ED-B-CLOSET-LT has a more expensive reading light than that utility closet needs for lighting
- Improve the 3d model of the sump
- Improve the 3d model of the french drains
- Improve the 3d model of the EQ-S-PLANT-HEATER
- Improve the 3d model of the AD-SG-COURT area drains (may need a product search)
- Improve the 3d model of the EQ-T-SAUNA-HEATER

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
