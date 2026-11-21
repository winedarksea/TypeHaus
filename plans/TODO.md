# TODO
Reminder: all items should design around clean export to Revit/Sketchup/IFC (follow industry standards where practical), and also be coded in accessible, "vibe code friendly" library configs.

Sourcing quotes, construction todo doesn't belong in this document, this is just softwared and house design todo. Quotes, supplier confirmations, dry-fits, site measurements and commissioning go in `houses/catlin/notes/construction_holds.md`.

We generally want exact products specified (or standard/commodity sizes) so we can verify everything works together correctly.
Our general goals are decent longevity and quality at a reasonable price, avoiding premium items unless clearly a major improvement for our needs.
Note that many of the pinned decisions in the code base here aren't as fixed as they sometimes claim, the "fixed" decisions were usually fixed in a narrower context, and can be changed for sufficiently good reasons.

+X: east, +Y: north, +Z: vertical/up. Will need to support rotating the house off axis in
the future.

## Needs your decision

(none open)

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
  VLAN is unplanned. E4 coves
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

- [ ] No check grades the passageway from `D-A-STUDY` or the level service space; they exist
  only in `mep_hvac.py` prose.

**ERV**

- [ ] **`DU-ERV-EA`'s drain tee is capped** (`notes/erv_static_budget.md` §10.28): no gravity
  line reaches a receptor. Choose: the radon sump (~2 ft, gas-tight trap entry), a condensate
  pump over the lane to `PR-B-ERV-COND`, or keep emptying it by hand.

**Plumbing**

- [ ] **Basement backwater protection, before under-slab rough-in.** Once the upstream
  manhole-cover elevation is known (construction holds), compare it with the basement fixture
  floors under UPC 710.1 and protect only the affected low branches.
  [UPC 710.1 guidance](https://forms.iapmo.org/email_marketing/codespotlight/2019/Oct17.htm)
- [ ] **Water-heater PRV, pending SPRWS pressure.** `PA-B-WH-XTANK` (Amtrol ST-12 class) is
  modelled. After SPRWS's static-pressure answer (construction holds), author a
  `PipeAccessoryKind.PRV` ahead of the meter set if static pressure is over 80 psi (UPC 608.2),
  and re-check the tank row (`notes/water_service.md` §4).

**Engine**

- [ ] `REG-S-HP-RET`'s 24x12 filter box is authored as its 15 1/8" neck run (decision #129
  terminal drop), not as a drawn drop. The sweep now draws a vertical rectangle at its true
  hu×hv, so modelling the box itself is a separate redesign, not an engine fix.
- [ ] A run inside a sloped (`FollowRoof`) lining is not graded; flat ceilings are
  (`checks/mep/routing_board.py`).

**Autorouter.** `docs/routing.md` Limitations covers the rest (trunk `-END` riser in W-M-E1's bay,
branch overlaps, ERV trunk/flex/ERV-R-BATH refusals, wall-hung port stub, WC arm, search U-turns,
`--lift` on a first-leg tee). Open holds:

- [ ] `--tree PR-M-S-SUITE-DRAIN` refuses TUBSH and WC at every rung: real holds (trusses y=224/240
  leave only D13, held by PR-B-CW-SUITE; D14 likewise; the WC's D12 is PR-A-HW-STUBATH's).
- [ ] `--group BATH2` refuses TUB (held to its own vent) and WC (the wye inlets at y 262/271 on
  PR-B-MAIN-DRAIN block y 254-279). The authored three-vent design stands; 908.2 is an AHJ question.

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

- **Radon exhaust vs WIN-A-N1: confirm with the AHJ/MDH.** Minn. R. 1303.2402 subp. 5.A reads
  10 ft from any window, unqualified. The radon leg is ~1'-2" from WIN-A-N1 in plan;
  `checks/code/mn_residential/radon.py:170-177` passes it on IRC AF103's 2-ft-above
  allowance (exhaust 2'-3" over the head). No design change unless they refuse it.
- **Radon fan power: confirm with the AHJ/MDH.** MDH's post-mitigation checklist wants an
  exterior fan hardwired with a disconnect in sight; `ED-A-RADON-RC` is a WR GFCI receptacle
  (cord-and-plug as the disconnect). No design change unless they refuse it.
- **Is a silt fence required at all?** The owner doubts it on a flat, small residential lot.
  It is drawn on the W/E lot lines for now (`houses/catlin/plan/site.py`); ask St Paul DSI at permit.
- **Cavity "canary" RH sensors** wanted in a south and west stud bay (no liner redundancy
  otherwise); no sensor element kind exists. (desired but not as explicitly modeled)
 - **`SF-B-BATH` stays, and not for want of numbers** — its three runs clear the 6'-8"
   headroom line by ~7 1/2" and a declaration on `RM-B-BATH` would pass. Nobody has decided a
   bathroom ceiling should be open. That is a design question, not a cleanup.
- Porch datum (2026-11-15): the court's north line is `W-B-BRICK`'s south face less a stated 3/8" (`_COURT_SETBACK_IN`), -10" as before; `gap_to_house_in` is gone and the cladding gap is 3.25". Closing the 3/8" (deck to the brick) is an owner decision, not taken.
- Figure out a space for a cat litter box. Options: either a cat door on the current vanity planned (no change) or a wall mounted sink leaving space for a self emptying litter box.
- A reviewer suggested 1/2" drywall as the standard otherwise, with cheaper end 'abuse' resistant drywall 1/2" for major Hallways, Kids' Rooms, Stairwells. Some options: 1/2" Type C, Paper-Faced 1/2" AR (e.g., Gold Bond Hi-Abuse or USG Sheetrock AR), LP SmartSide 38 Series Panel 7/16" (Sidings Used Indoors), 1/2" MDF (4x8 Sheets with V-Groove or Batten Strips), 1/2" MDO (Medium Density Overlay) Plywood
- Best Cheap STC Upgrade (~+$0.12/sq ft): 1/2" Type C Drywall (also staggered stud framing which we use in some places, cheap low-expansion spray foam or standard elastomeric latex caulk ), Best Seamless Durability Upgrade (~+$0.45/sq ft): 1/2" Paper-Faced Abuse-Resistant (AR) Drywall, Best "Skip-the-Taper" Durable Wall (~$1.30/sq ft material, $0 mudding): 4x8 Pre-Primed MDF Shiplap Panels (or LP SmartSide 38 Series), The Winner for General Bath Walls: 1/2" Mold-Resistant Paper-Faced Drywall ("Purple Board" / USG Mold Tough, although not strictly needed on well ventilated walls with good high-resin paint), The Bathroom Ceiling Secret: 1/2" Interior Soffit Board (Sag-Resistant), Best Value for Speed & Zero-Fail Waterproofing behind tile: 1/2" Polyisocyanurate Foam Board (Johns Manville GoBoard), Places where 5/8" may still make sense: floor to floor ceilings (Type X), garage walls (5/8" AR Type X). Apparently the resonant frequency of 1/2" Type C drywall is one of the more ideal for household noises (being higher than the others)
- Around bathrooms and bedrooms we want higher STC. Around major hallways and stairs we want abuse resistance (but only need it on the lower 4' above the walking surface probably). Around the mudroom we want highest abuse resistant with something like wainscot (shiplap there carries the idea already, can be improved further possibly like LP Smartside). Some walls likely worth abuse resistance on a side: W-M-WELL, W-M-HS2/HS3/HS4, W-M-BAE, W-M-C1/C2/C3 and walls facing RM-S-HALL and next to stair landings. A reviewer also said that we should focus STC drywall/framing upgrades strictly for the solid walls without undercut doors (as they say doors bypass sound so much they make upgrades not worth the price, although doors that are weatherstripped, solid, and with no undercut do have better STC), Status 2026-11-15: the listed abuse-resistant faces are already swapped to `gwb-ar`, and the channels came off W-S-SBS and W-S-BW1-BW4 on 2026-10-23. Still open: abuse resistance on the lower 4' only (needs a banded assembly) and the bedroom-side faces in the next item.
- Open (drywall overhaul): kids' bedroom and kids' room hall faces are NOT on the abuse-resistant swap list; decide whether they take `gwb-ar` (the owner's list omits them).
- Wall W-A-GC-S and it's matching south pair should have bookshelves against them, likely custom to fix the short triangle present there. In between them a linen floor mattress on tatami mats.
- Perhaps mount the espalier posts on sonotubes to increase the lifespan of the posts.
- [ ] W-BW-SCREEN lower timber end nails (`houses/catlin/notes/entry_screen_mdo.md`): read the S10ACN's bending yield strength from Simpson (graded 0.51 at an assumed 60 ksi floor; passes down to 16 ksi) and confirm C_eg 0.67 against NDS 2018 §12.5.2 in print.
- Plan limited mobility bathroom use on the main floor. Looks like full wheelchair clearance won't work, but look what we can add to make limited mobility practical there. Perhaps a vertical grab bar between the toilet and the tub, serving both.
- Plant-room reservoir (2026-11-11): manual-fill tank, two independently timed shelf-pot circuits, one packaged wired WaterWatcher cutoff and automatic M8000-NO/RIBU1C low-water permission; shared geometry/BOM and 11.75-gal spill budget updated. Itemized provisional hardware $1,026.61 against $1,200 target/$1,500 ceiling. Still open: WaterWatcher revision/humidity/load/recovery qualification, commodity supplier SKUs/quotes and NPT/NPSM sealing interface, plumber-approved removable fill, supply-sizing basis, physical containment, electrical/hydraulic commissioning and ten-day trial. See `houses/catlin/notes/plant_reservoir.md` and its procurement CSV.
- Plant-room reservoir: close WaterWatcher qualification, exact supplier SKUs/quotes and NPT/NPSM adapter seals before purchasing. Itemized estimate $1,026.61; target $1,200 plus $300 contingency under $1,500. Confirm attended removable potable filling and complete commissioning/ten-day trial. [Reservoir note](../houses/catlin/notes/plant_reservoir.md).
- Maybe add a lighting view to the UI (lights generate cast lighting effect, background otherwise goes to full shadow/black)
- Geometry review round 2 (2026-11-05): [report](geometry-review/REPORT.md) §1 ranks the open escalations; detail in `geometry-review/2026-11-04/adjudicated/C1..C5.md`. 0 FAIL kept. Open, by rank:
- The balcony backing's nail schedule back to the joists is undrawn (`houses/catlin/notes/balcony_fascia_mounts.md`).
  - [ ] DWV: `PR-M-BATH2-WC-VENT` runs level under the FS-M-WEST joist 016/017 + FS-M-MECH 000 seam at -13 1/2" (MN 905.3, under the bowl's real rim too; `mep.vent_connection` ADVISORY, C4 E11). A 45-degree climb is 0.21" short (7.69" of flange footprint vs 7.475" of web-zone travel), so no WC position along W-M-HS1 helps. Option 2 (WC to W-M-W3 bay 13-14) FAILS UPC 402.5: re-measured 2026-11-15, the bowl front stands 23.06" off the tub deck's Corian apron against 24" (0.94" short; the engine does not grade it, the deck is walls). No WASHLET+-ready bowl found at <= 27.34" deep ([note](../houses/catlin/notes/bath2_vent_move_options.md) addendum). The vent stays ADVISORY pending an engineered chase.
  - [ ] Header residue (decision #116, `houses/catlin/notes/header_spans_r602_7.md` §5): the `5.25x7 LVL` row in `prices.toml` is an estimate ($13-24/LF material, off the house's own LVL $/bf); replace it with a retail number, ordered as a beam (R/L, probably special order; sold as a column it runs about twice that). The moved FO-A-STAIR trimmer lands on the plate just past WIN-S-STUDY3's north king, ungraded. D-B-GYM's north king stands 1.2" past W-B-CS3's end on W-B-CS2's line.
  - [ ] D-M-LAUN after the 2026-11-07 move (review of 8b1cf155d). Owner: (1) **washer** (done 2026-11-07): valves behind the tower in W-M-CLN; the washer drains into the laundry tub (Minn. R. 4714.1001's adjacent-washer exception). Confirm with the AHJ against 4714.0804. The tower stands 0" off W-M-CLN against LG's 4" (guide p.14), so it needs 90-degree inlet hoses; name the washer valves at order. (2) **tub access**: 20" of the tub stands behind the strike wall; it is reached through the opening's west 8 1/4" and the 13 3/4" strip in front of the tower (pinned in `test_mep_plumbing.py`). (3) **36' width**: the header reads Boise p.4's 32' column (the widest) plus a load comparison; the literal 36' cell is p.9 Floor Beams 8'-0": 3 1/2 x 9 1/2, 2 trimmers, i.e. a 2-ply 9 1/2" LVL on doubled jacks (the engine frames one jack here; `WIN-M-DINING-E` reads its 32' column the same way). (4) **W-S-SN3's uniform load into W-M-HS3**: `resolve/stacked_ladder.py` records the FS-S-WEST line (W-S-SN2/SN3 over W-M-HS3/HS4, 256/272 bay) and lays nothing on an open-web deck; `structural.stacked_line_ladder` is UNKNOWN until TrimJoist's shop layout carries the line (a blocking panel or a truss over the wall), and the header reads "assumes a ladder in FS-S-WEST". `P-S-SN3-SQUASH` still carries BM-S-BATH-E's point. Still open: neither header nor PublishedSpan grades the guide's structure width against the derived building width.
  - [ ] Owner decisions left open by the 2026-11-06 fit pass (REPORT §1.20-32): C4 E8 runs vs backing; C4 E14 supply items; O2-110 pocket head (Eclisse detail). Backing bands: the owner kept BK-M-S1-HP2-BED, BK-M-S2-HP2-LIVING and BK-M-N2-HP3-STAIR.
  - [ ] Fit residue after the 2026-11-06 fit pass: no readable DensShield price (`gwb-glass-mat` unpriced, ~99 SF billed since the review); Sterling drain 8 1/4" (kept by owner, 2026-11-08; `notes/framing_bore_limits.md` §12); FX-S-SUITE-WC tank 1.09" off (flange held); Uponor LF2821050 A 14.95" (submittal) vs 14.675" carried; 8 flush boxes still on studs (`advisory.box_on_stud`); seat beams: the LUS26-2Z now hangs on an 11/32" filler notched round the CBSTQ strap (end gap 0.1055" vs note m's 1/8"; `notes/canopy_west_band.md` 2026-11-06 (b)). Simpson publishes no filler installation, so ask Simpson to confirm. It does not gate gravity (the beam bears on the pack); the fallback is a cast-in HETA20Z pair.
  - [ ] Smaller open items, by cluster file: C1 E11 (O1-102 relief doors), O2-110 pocket head (Eclisse detail); C2 E12 rest; C3 I4-004/005; E8, E14. SCONCE-CANDLE (Livex 4451-04, no published backplate) and SCONCE-STAIR (see `BoxRow` shape) state no `LuminaireType.canopy`; `place_box` centres a wall-light box on the body's mid-height, not its canopy; the WAC LINE's in-box transformer is not in `electrical.box_fill`.
  - [ ] TB-SG-W1/E1 closure boards 8" vs FT-B-S2/S3 at 10" (F5-104); FB-B-CS drain-tile ring 1" into FT-B-S2/S3 (F5-105); 14" north-entry pier cage 0.806% (engineer hold, C2 E6).
- **Max Light sill adaptor is PROVISIONAL** (2026-11-15): all twelve Max Light units carry a modelled 30 mm sill adaptor (Drutex's 54123 figure) that lifts the 1" stool about 6 mm over the 1 1/2" pan back dam; it costs the escape units 30 mm of estimated clear height (smallest 6.00 sf vs 5.7). Replace it with Słowińscy's sill section and back-dam detail (`notes/window_and_door_procurement.md` §2.6 item 11).
- Improve the wainscot of the mudrooms (the wainscot should be tall—typically 54" to 66" high (or roughly two-thirds of the wall height), mid-to-dark tone (e.g., muddy green, slate blue, warm mushroom, or charcoal), Satin or Semi-Gloss finish using a high-end urethane alkyd enamel (like Sherwin-Williams Emerald Urethane or Benjamin Moore Scuff-X) (Scuff-X is held for this item; the house paint systems are decision #113, houses/catlin/notes/paint_selection.md), 1x6 or 1x8 Cellular PVC board for the bottom baseboard, smooth 1/4" MDF panel backers (if walls are textured) with 1x3 Primed Poplar (for impact resistance) or Primed MDF (for lowest cost) for the vertical battens (or shiplap))
- Oksana wants an elm slab sofa table
- See if we can practically use the fleur de lis molds on the top of PT-BW-PE and PT-BW-PNE https://historystones.com/collections/business-industrial-construction-building-materials-supplies-marble-tile-stone/products/fluer-de-lys-tuscany-column-insert
- Workshop receptacles: RC1's 120/240 V circuit and RC2's 120 V quad are modeled, with their boxes, covers and raceway. Resolve the required tamper-resistant listings and the field wiring before installation; see [workshop receptacles](../houses/catlin/notes/workshop_receptacles.md).
- [ ] Exterior doors, after the 2026-11-17 sill-beam pass (`notes/exterior_door_sill_beam.md`):
  - **Supplier:** Wahoo publishes no AridDek plank-to-wall gap; FS-SG-BALCONY's rear edge stands 1 1/8" off the house cladding (2026-11-18).
  - **Billing:** the HLGM10 row in `prices.toml` is an estimate (no retail read); ENTRY's two 1/2" seat fillers bill as an 8' "0.5x11.875 LSL" stock line but are resawn from rim offcut (`JoistReinforcement` has no stock profile).
  - **Engine:** Short plies (sill-seat backers, PORCH LVL plies, FS-ATTIC hall trimmers) split a floor's edge bay along its whole length (conservative). TJ-8000 p.4's 2D spacing between adjacent rim holes is ungraded.
  - **Supplier holds:** one prehung submittal, ZAI5625FN + XXXXW on the 4 9/16" jamb for the three pairs and the ENTRY single (installed sections, ratings), and Endura's confirmation that the nose bears on the beam; the self-adhered membrane pan under the sill (the prehanger's acceptance); the Endura adjustable cap's travel and factory setting (raising the cap raises the crest one for one); PORCH's cover product, slip rating and seat drawing; Trex's acceptance of the FRP plate under D-B-SUNKEN's tread; installed sweep/hinge sections; assembled-unit label/warranty; the 06-002 submittal (CPD, NFRC/NAFS, astragal, PanoLock+); Proglaze ETA flashing-end application; D-B-SUNKEN's PVC sheet / drainage board / sealant compatibility. Complete preferred/Tru-Defense prices remain unavailable publicly.
- House K2 base flashing and wall-top closures now derive, bill and receive coverage checks; coordinate the garage Sill to Soffit panel break and installation order, which the fit check records UNKNOWN. See the trim note for the selected aluminium section, isolation and quantities.
- [ ] House eave/gutter, remaining after the geometry pass ([plan](roof-wall-eave-detail.md), [note](../houses/catlin/notes/roof_wall_eave_detail.md)):
  - Supports: select the gutter bracket, draw a section through a support, seal or move the fixing above the crest (screw now 4.7" below it), rework the eave girt for edge distance.
  - Joints: eave and gutter splices, thermal movement, sealant/fastener schedule.
  - Real outlet fitting and the north tail.
  - Snow protection: gutter front is about 2" above the snow-slide line.
- Eave and gutter hardware: Select the gutter bracket and outlet, and finish the splice, fastener, and sealant details. The eave sealant product and its compatibility with the roof and membrane also need confirmation. [Eave detail (line 153)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/roof_wall_eave_detail.md:153)
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
- Upgrade fasteners still uncounted (decision #105 covers panel screws, connector schedules, treated framing, roof/screen sheathing): wall sheathing and subfloor nailing, fascia/trim screws, window-install screws, and the HL angles' site-length through-bolts.
- Backup battery, still open (`houses/catlin/notes/backup_power.md` §11-§12): EG4's UL 9540 certificate naming 12kPV + WallMount Indoor; how the 12kPV's load port behaves on its "No Battery" setting (ask EG4); its GEN port rating; declare future storage and V2H on the Xcel application; DSI's position on a UL 9540 3rd-ed. DC ESS battery; a freeze drain-down plan; a small LFP UPS for Home Assistant, the router and the leak valve. After the 2026-11-02 trim the always-on tier passes summer's 48 h and the bridge (0.28 kWh margin) and still fails December's cycle (§6).
- V2H spare raceway (routed 2026-11-07, `backup_power.md` §10): add PVC 2" rows to `prices.toml [conduit_fittings]`; the ICF supplier/engineer details rebar round the three 6" CD-GAR sleeve boxouts in W-B-N2 and W-GF-S2. `CD-B-GAP-EV` ends at +5'10" abs while `ED-G-EV-1450` is at 48" AFF (+14" abs): an existing over-rise to check.
- **2026 NEC residue (decision #120): moved to `plans/TODO-nec-2026.md`** (owner questions for the Catlin electrical, engine gaps, and the list still to read in print).
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
- **W-B-N2 wall-top restraint (Minn. R. 1309.0404).** `FO-M-STAIR` fills the first three joist spaces against W-B-N2 for x 10'-3"..17'-8 3/4", so no footnote f blocking can stand there and `code.MN_1309_0404_wall_top` reports UNKNOWN. 400 plf x 8' = 3,200 lb goes into the well's edge framing spanning flat between the headers: get the EOR's approved-equivalent detail (a flat strongback or a landing strut) and author it. Basis note `houses/catlin/notes/main_floor_truss_basis.md` §4.
- Aiming to keep floor transitions flush, looks like ~3/4" thickness makes this easiest. Status 2026-11-15: tile and oak already total 3/4"; the open coverings are LVP (0.28"), the sheet vinyls (0.12", 0.37") and carpet (1.0"). Owner deferred 2026-11-14. Original note: Ditra XL or Ditra Heat + Thinset + 8 mm Tile (Ditra Heat PS 5.5 mm + 3.5 mm thinset (3/8" by 3/8" notch trowel) + 10 mm tile OR Ditra Heat Duo peel and stick (PS) + 2.5 mm thinset (1/4" x 3/8" trowel) + 9 mm tile OR 1.5 mm thinset (compressed by 1/4" by 1/4" trowel) + ditra heat 5.5 mm + 2.5 mm thinset + 9.5 mm tile) == 1/2" plywood (nominal) + 7 mm LVP == 1/2" exacor (12 mm actual) + 7 mm LVP == 1/2" gypsum underlayment (fiberrock) + 6.5 mm LVP == 5/8" actual (Fiberock) underlayment + 3 mm sheet vinyl == 16 mm exacor + feather finish + 2.8 to 3 mm sheet vinyl == 3/4" hardwood ~= 7/16" pad + 1/2" pile carpet (carpet squishes at edges)
- Is TypeHaus organized such that a contractor building typehaus could hand their chatbot/llm of choice the github repo link and easily get answers they need on the design?
- Reverse osmosis sink?
- Reduce the number of LED strip controllers, ideally one or two for the soffits, not six (Zigbee vs Matter: see the cove-controller item above).
- Pantry shelves have a middle support that would ideally only go half depth (sticking to north half), right now it is rather restricting access to the west end of the pantry.
- Robot training (light switches correspond, doors open)
- Camera in ESS Room and Plant Room (for keeping an eye on them while on vacation). Something cheap, effective, and works well with the rest of the camera system
- [ ] Canopy ColorGard: clamps graded (3,182 lbf drift wedge vs 4 x 863, d/c 0.922, `structural.snow_retention_capacity`, ideal sharing). Open: ColorGard 2.0 rail bending/end reactions and the Image II panel attachment drag (need S-5! rail allowables and Metal Sales clip/fastener values).
- [ ] Roof N Mini wind-clamp design: check applicable product revision/design basis, corner-zone uplift demand and panel/fastener load path using the published Image II 24 ga test data. Test-data lookup is complete; clamp count and omission at the ColorGard corner still need wind justification.
- The house has four grounding rods, which might be overkill? Also the grounding junctions may be in the wrong spots.
- Interior selections: Remaining checks include the Aquia IV height suffix, SP bowl projection, Delta stainless-stock availability, the neo-angle shower’s door opening, and whether the studio wet bar needs a stainless bowl. Bath 2’s selected surface colors still need physical-chip checks. [Interior selections (line 336)](/Users/colincatlin/Documents-NoCloud/TypeHaus/houses/catlin/notes/interior_selections.md:336)
- Titanium fittings: measure delivered parts against the tube; the fit is per `notes/titanium_handrail_backsplash.md` §2.
- `RL-A-FLIGHT-GUARD`'s newel (x=27'-1 1/2"): its fascia bracket screws into stringer-0 under the study ceiling; the skirt-to-newel fixing is undrawn.
- Attic suite simplified to unfinished space. Done 2026-11-11: the bedroom count (RM-A-STUDIO is `Occupancy.HOBBY`, a craft room, so R403.5 drops 15 cfm) and a finished-area report that already leaves out RM-A-EAST-UNFIN and RM-A-POCKET (4,021 sf finished vs 4,898 CFA). Still open, if wanted: take the suite itself out of the finished area (leaving just the small attic study), although likely still keeping an ERV terminal of some sort in the attic suite, and likely still basic rough in stubs for plumbing so we can realize this design later. We would still want to keep the current products used for it in the library, and a clear set of notes so we could swap these items into the design easily.
- Try to keep most interior doors as 1/2" factory undercut or privacy doors where decided
- Door residue: the steel and sauna slabs are modelled cut down 1/8" (the steel may need ordering to size); the library interior types and the plan door symbol still use the 45 mm schematic leaf.
- Shower in sauna?
- AD-SG-COURT connection: resolve the bottom-drop adapter/product; the named [NDS 1200](https://www.adspipe.com/nds/products/drainage/catch-basins-and-grates/square-catch-basins/1200-12-in-square-catch-basin-drain-with-2-openings) has lateral outlets. Geometry remains representative, within the authored nominal envelope.
- ED-M-FIRE-RC: measure the delivered RACO 862 handy-box cover. It must be no wider than the pocket's 2 3/8" strip (nominal 2 5/16"; Hubbell's table reads 2.425").
- ERV terminals don't come out of the walls/floors/surfaces quite clearly enough, likely they protrude just a bit more
- ERV likely blocks D-B-CLOSET, and its condensate also blocks
- Sauna needs a slope to concrete floor

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
