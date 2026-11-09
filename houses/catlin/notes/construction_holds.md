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
- Rainscreen closures (2026-10-29): close the supplier questions in `notes/metal_trim_kit.md`
  "Open with suppliers" (Metal Sales x4, the membrane maker, the screen supplier).
- Exterior darks (`notes/exterior_darks.md`): Clopay Black at R-12.9 (dealer), the Tuff II tint
  limit, order chips, Metal Sales Rogers stock of Matte Black 106, Drutex's RAL 9017 warranty.
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
- Plant supply fabrication hold: dry-fit A220V / ZD12X6TZ / TH-HP-PLANT-BOOT-01 and gasketed
  service hatch, including actuator fasteners, hand/tool access, seams/supports and the
  approximately 3/8-inch deck margin. Geometry and connection are specified; see
  `notes/plant_supply_connection.md`.
- Measure Glacier Bay QL033Y and SUNNERSTA on site; confirm the Chulton as one-hole.

## Commissioning

- **Meter the EG4's real overhead.** `takeoff/backup_calc.py` counts the 12kPV's datasheet idle
  (<55 W standby) and 94% maximum efficiency; both flatter a ~250 W outage load. Measure
  islanded idle and low-load efficiency at commissioning, with the backup duty cycles and the 13
  alarms' standby, and re-author them. See `notes/backup_power.md` §6.
