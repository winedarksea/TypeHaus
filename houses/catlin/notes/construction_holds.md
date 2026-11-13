# Construction holds

Quotes, supplier confirmations, order-time choices, dry-fits, site measurements and
commissioning: work done off the model, by a person, with a supplier or on site. Moved out
of `plans/TODO.md` (2026-11-07), which is design and software only. An answer that changes
the model goes back to `plans/TODO.md` as a design item.

## Quotes and prices

- **Cotton Oak LVP (Karndean AKP-RL38):** get a local quote (the `lvp` row in `prices.toml` is
  still Quincy's placeholder) and check a sample in the house light against the model's
  `#d6cebb` (`notes/lvp_flooring.md`).
- Versadeck / Last-Deck / LockDry quotes for FS-SG-BALCONY, and Ultralox's written OK for
  SD04964 over 1" PVC fascia (and for the FM244390 corner's fastening)
  (`notes/balcony_fascia_mounts.md`).
- PV: incremental installed pricing and site-specific production estimates for the second-row
  study (`params/solar.py`).
- A Metal Sales price for 8243100 (upgrade fasteners, decision #105).

## Supplier and manufacturer confirmations

- **Gree FXU24HP230V1R32AH:** obtain the dimensioned drawing for the ordered cabinet
  revision. The 2026-01-27 model-specific submittal and current generic indoor manual
  disagree on cabinet dimensions. Need the return aperture, supply setback, refrigerant
  and condensate fitting stations/projections, electrical/control knockouts, and the
  internal heat-kit envelope. `notes/flexx_ultra_geometry.md` records the model basis;
  do not fabricate transitions or drain rough-ins from its schematic port stations.

- **Sconce J/J1 (WAC Sprig BL-23210-BK):** confirm it can be hardwired. Output drops from
  623 lm to 287 lm compared with the Stretch it replaced.
- The garage GL-C-208M's electrical and temperature figures come from a manual mirror
  (unconfirmed) (`notes/smart_home.md`).
- WIN-B-SAUNA: the 93 mm Alucover fixed unit stands 0.16" proud of the garden wall's 4.06" foam
  buck (0.56" back dam); A-602 flags it. DAKAM/installer: confirm the proud set or a 3/8" dam
  strip.
- Confirm the Williams 36" Colonial level panel's model/SKU (CP252306B is inferred,
  `library/railings.py`) and its 36" surface post kit at order.
- **FS-M-NE truss order (decision #112).** 16" o.c. is a published TRIFORCE OJ418S read (p. 5,
  40/25 psf L/480, 18'-0"), so this is a stock order plus confirmation. Send the supplier
  `notes/main_floor_truss_basis.md` §2-§3: L/720 live on the order, the web layout (p.4's 24"
  o.c. diagonals and which end takes the 34 1/8" OSB panel; the modelled pocket stations are
  assumed, `notes/open_web_truss_geometry.md` §4), the doubled trusses on the 316 and 332 lines,
  the peninsula point loads (confirm both pairs: doubled, the hand bound is still 1.02-1.10x the
  row's moment) and the fridge/freezer and partition loads; also the blocking panel for the
  `W-B-N1` bays and the two strongbacks (cuts at y 180/196/292/414).
- **Ridge plate, before foam (TJ-4000 R14W):** inspect every LSTA18 and its twelve 10d, the plate's
  straightness along the wall, and full foam contact on the closures and bevel faces. The strap
  is primary structure and is invisible once sprayed.
- Rainscreen closures (2026-10-29): close the supplier questions in `notes/metal_trim_kit.md`
  "Open with suppliers" (Metal Sales x4, the membrane maker, the screen supplier).
- Exterior darks (`notes/exterior_darks.md`): Clopay Black at R-12.9 (dealer),
  order chips, Metal Sales Rogers stock of Matte Black 106, Drutex's RAL 9017 warranty.
- House eave/gutter: confirm strip-in width (provisional 9") with GCP, and Image II + deck +
  membrane acceptance with Metal Sales; deck bearing is 2.036" vs 2" min, provisional.
- Air-distribution products (`notes/air_distribution_products.md`): Vents-US AM 100/125 loss
  curves; FA8 plate and projection; floor-boot and Snappy P13-204 heights; motorised damper
  body and actuator sizes; H&C 531SA 6x12 face; a 125 mm retail valve; prices marked "not read"
  in `prices.toml`.
- Supplier holds from the 2026-11-05 geometry review:
  - Metal Sales / SFS: Profile Vent NFA under the 1" Image II clip, and per foot or per strip
    (R806 passes 562 vs 553 in2); a lower BBD75 panel stopped 1" short of the Transition Trim
    seat; a stock gable end closure for the 7" cover; Profile Vent width; a 4x3 1/2-to-4" round
    adapter.
  - Windows (`notes/window_profile_measurements.md`): DAKAM confirms the ordered adaptor
    (54123/54113 add 30 mm; 50114 adds 50 mm), unit-height datum and stool-bearing rail; fixed
    stools keep the provisional 75 mm rail. Andersen dealer confirms the architectural
    dimensions for the selected triple-pane unit and basic-frame depth. Max Light fabricator:
    §2.6 items 11-13 of `notes/window_and_door_procurement.md`. MMI: Z0364688R sill crest
    (ST-G-SERVICE tops at the +1.5" envelope).
  - Murphy Door: confirm the custom 32 x 82 RO flush-mount as modelled (FF datum, legs 78.0",
    body 28 3/4 x 78 1/2 x 8 1/4, casing 36 1/2, passage 24 1/4), price/lead time. Frigidaire:
    TTDRRVFRKIT vs TTDRRVFRKIT2.
  - Broan: the derived 9 3/4" port 3-4 spacing; 8" flex on those centres. Weyerhaeuser: TJI 230
    row assumes a glue-nailed subfloor. BuildBlock: BB600 course height vs the 64" stem.
  - Frigidaire TWINSPAIRKIT 1/8" seam; LG LDTS5552S side-mount with no sub-top. Carpet backing
    thickness (Z-bar answer holds to 0.10"); Mohawk on the 3/8" pad. WAC Roland on a flat 753
    cover; DVFR1W trim stand-off. Bypass/bifold 1/2" head allowance.
  - Plumber: the attic WC's 1 1/2" vent (UPC 904.1); basement WC re-route under the slab to
    W-B-BA-E.
- Duct and air-distribution submittals (`houses/catlin/plan/ducts.py`, decisions #114/#121/#124):
  Imperial laying lengths and boot heights (the 12.25" GV0821+GV0811 reducer is a stand-in);
  GV0772's length (drawn at M&M's 7" stand-in; confirm the SKU too, since listings name the 6x8
  increaser GV1360, §10.28); Linx's dimensioned E90/E45 submittal (centre-to-face, which `radius_m()`
  reads first; 1.0 D assumed). Broan: insulated ducts "same diameter as the ports" vs its own
  6-to-8 transition advice, and top-port drainage (draft at
  `notes/air_distribution_products.md` :331). `REG-T-HP-PLANT-SIDE`'s throw (unread).
  The ERV trapeze: a published hanging rating for a strut-bridge lag into a TJI 230 flange
  (245 lb is TB-808's design example) and the 3/8" rod's 730 lb (B-Line, not MSS SP-58).
  ICC's own IMC 2018 Table 603.4 text (proofread on UpCodes; codes.iccsafe.org refused the fetch).
  `DU-ERV-EA`'s capped drain tap (`PROD-DUCT-DRAIN-TAP-8`): no SKU read; open it into a pail
  each winter until a drain route is chosen (§10.28).
  AAF PerfectPleat HC M8 (nominal 10x10x1) actual size vs the bath-2 stall-dryer's grille holder.
- ERV level 2 flat trunk (`notes/erv_static_budget.md` §10.14): a shop drawing confirming the
  rectangular elbows at r/W 1.0; TrimJoist's and TRIFORCE's shop layouts for the deck pocket
  stations, which assume a 24" pitch.
- Product/cost review holds (2026-11-04, `plans/catlin-product-cost-review/REPORT.md`):
  - 03-004 Simpson: HHUS410 fastener option and coating.
  - 07-001 Breezeway: the 5.9 LF guard package (product, posts, price).
  - 05-001 Metal Sales: PBR jamb sticks, gutter end caps and straps (unpriced joins).
  - 13-002 Installer/AHJ: confirm the APsmart transmitter/receiver pairing for NEC 690.12.

## Image II eave sealing

See [roof_eave_rib_end_sealing.md](roof_eave_rib_end_sealing.md). The software records and bills
the treatment; none of these has been done.

- **Metal Sales 64032XX:** confirm chemistry, package, color and technical data, including
  compatibility with PVDF/galvanized panel and the butyl membrane and tape.
- **Rib fill depth:** the 1-1/2" is an allowance; the guide gives none.
- **Mock-up before installation:** two adjacent panels, one joined seam, real plug, hem bead,
  tape, strip-in and gutter back, at 6:12; add a 4:12 garage sample if its attachment differs.
  The eave is sealed with no secondary outlet by decision; this confirms it. Show pan runoff to
  the gutter. Put dyed water on the strip-in under the pan, upslope of the tape and beside a
  plugged seam, hold a day or two, then take it apart. **Pass:** deck edge, wall head and behind
  the eave face dry; no dye under the membrane or strip-in laps; tape and hem bead intact and
  bonded; the plug bonds nothing that must move. **Fail:** revise the strip-in detail; do not
  cut weeps or reopen ribs. Photograph finished rib ends and record product and batch. This is
  an installation check, not a certified wind-driven rain, ice-dam or durability test.

## Utilities

- **SPRWS** (Engineering 651-266-6270): does the meter set carry a check valve, and what is the
  static pressure at the main? This decides the expansion tank and PRV
  (`notes/water_service.md` §4).
- **Sewer:** the next upstream manhole-cover elevation on the survey datum (Public Works
  651-266-6234; the `site/sewer-permit` task asks only for invert). This feeds the UPC 710.1
  backwater item in `plans/TODO.md`.

## Delivered parts, dry-fits and site measurements

- **Confirm the delivered parts:** on the PROPH80 T0 RH120-MSO, the scaled T&P outlet (~46",
  front-left, under the ERV case's 54" bottom), the HydroBoost riser's projection (r ~15", 2 1/4"
  off `D-B-CLOSET`'s 75-degree sweep) and the cord's length (`notes/water_service.md` §1); and the
  ProSaunas vent hatch's cutout and free area (unpublished; (844) 565-1113).
- Test-fit one A19 in the Soren 50910BK (P6) before ordering the set (`notes/smart_home.md`).
- Before fabricating RM-M-STUDY-CLOSET: complete the 60-minute seating mock-up, verify occupied
  cushion height, lumbar fit and bracket/blocking connections, and record any dimensional
  changes in the bench spec.
- Kitchen sink fabrication hold: dry-fit KHU100-32 / Bolden KPF-1610SFS / Badger 5 / Dearborn
  P9703WBG in the 36-inch SEKTION. Verify delivered Badger revision, clip/washer and rail
  access, full hose stroke, cleanout clearance, vent fitting/bore envelopes and the inward
  tilt-turn window sweep (full turn likely obstructed). See `notes/kitchen_sink_installation.md`;
  product/connection specification is complete, physical fit is not released.
- Plant supply hold: confirm the EWC 6RSD (or equal) body and actuator size, and that its
  actuator can be reached through the grille opening, before W-S-C1's liner is closed. Not read.
  See `notes/plant_supply_connection.md`.
- Measure Glacier Bay QL033Y and SUNNERSTA on site; confirm the Chulton as one-hole.

## Commissioning

- **Meter the EG4's real overhead.** `takeoff/backup_calc.py` counts the 12kPV's datasheet idle
  (<55 W standby) and 94% maximum efficiency; both flatter a ~250 W outage load. Measure
  islanded idle and low-load efficiency at commissioning, with the backup duty cycles and the 13
  alarms' standby, and re-author them. See `notes/backup_power.md` §6.
