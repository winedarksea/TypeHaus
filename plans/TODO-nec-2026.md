# TODO: 2026 NEC residue (decision #120)

Open items only (delete done ones). Moved out of `plans/TODO.md` 2026-11-14 to keep it under 500
lines. The rows in `docs/code-notes/nec-2026-paraphrase.md` (index) are read in the printed code
(2026-11-13/14); each doc's **Engine** lines list the rules no check grades. `UNCONFIRMED` in
`model/nec.py` is empty. Latest batch: `docs/code-notes/nec-2026-paraphrase-followup.md`.

## Owner questions (Catlin)

1. **Continuous loads.** `CKT-SPA` 11.5 kW (59.9 A at 125% against a 50 A breaker) and
   `CKT-WORKSHOP-240` 4,800 VA (a 25 A load on 20 A; a capacity allowance, and 210.21(B)(2) caps
   two receptacles on 20 A at 16 A): continuous (3 h or more) or not? Decides FAIL or PASS in
   `electrical.continuous_load_circuit`.
2. **Author conductor sizes and types on circuits** (`Circuit.conductor_awg`, material, `egc_awg`).
   It unblocks the 705.30 ceiling, 215.4(A)(2)/(B)/(C), raceway fill for the 27 UNKNOWN runs,
   705.60, `CKT-ESS-GRID`'s #8 Cu, and a general EGC advisory (250.122, 250.122(D)). 215.5 holds by
   hand (169.6 A and 150.9 A at 125% of the two feeders, under 200 A).
3. **EG4 (ask).** (a) Maximum grid-breaker OCPD for the 12kPV; `CKT-ESS-GRID`'s 50 A clears the
   41.25 A floor (45 A standard size). (b) Does opening the RSD loop also stop the load port and
   the battery contactor (706.15(B))? Today `backup_power.md` §8 says "closed loop, supported
   batteries" only. (c) With `CKT-ESS-GRID` open, can the grid-port terminals stay energized
   (705.20(F) warning)? (d) `CKT-ESS-GRID` is slot 40 of 54 with ten spaces below: "the opposite
   end" to the AHJ (705.12(B)(2)(a)), or move it (the last row cannot take a 2-pole)? 241.25 A of
   270 A (33 A, rounded per 705.28(A)). (e) Is the 12kPV listed as a PCS (UL 3141), what is its
   control setting, and is reconnection after an overload shutdown nonautomatic (702.4(A)(3))?
   Capacity is met (8 kW against 5,649 VA, largest `CKT-HP3` 1,850 VA);
   `electrical.standby_capacity` is UNKNOWN until `EquipmentType.pcs_listed` is authored. (f)
   705.60: do the 12kPV load-port conductors to `ED-B-BACKUP-PANEL` (41.25 A) have an inverter
   output OCPD, or does the backup panel need a main (`ED-T-BACKUP-PANEL` states no bus or main)?
   (g) 702.7(B)/250.30: does the load port bond its neutral to ground in island mode, and is the
   grounding sign then needed? Also the 705.30(D) line/load marking of the plug-on breaker and
   whether open-phase protection excuses the 408.36(D) hold-down (705.30(E)).
4. **Labels, one item** (none is modelled): 690.12(D) building label at `ED-M-METER` and the
   (D)(2) switch wording on or within 3 ft of `ED-M-RSD-INIT`; the 705.10 plaque with its
   emergency phone; 230.70(B)(1)/(2) "SERVICE DISCONNECT"/"EMERGENCY DISCONNECT" and the
   230.70(D)/225.41(B)/(C) plaque of other-source disconnects; 702.7(A)(1) placard at the
   meter-main; 702.6 signals (malfunction, carrying load: the inverter display and HA, unauthored);
   705.12(B)(2)(b) warning at `ED-B-PANEL`; 690.7(D) 384 V label and 690.31(D)(2) "PHOTOVOLTAIC
   POWER SOURCE" every 10 ft; 706.15(C) "ENERGY STORAGE SYSTEM DISCONNECT", 480.7(F) nominal
   voltage near the battery; 404.8(C) backfeed signs (ESS, V2H); 424.47 on `ED-B-PANEL` slots 29
   and 33; 625.43(C) plaque locating `CKT-EV-1450`'s breaker (it is remote from the EVSE).
5. **480.7(B), AHJ reading.** For a dwelling it reads as an outdoor battery disconnect or remote
   control labelled EMERGENCY DISCONNECT with no 60 V condition (the ~51 V WallMount is under 60 V,
   so (A) asks for no dc disconnect). If it applies, can `ED-M-RSD-INIT` be the remote control (it
   must open the battery) and carry that label, not only "PV rapid shutdown"? 690.12(C)(2)(a)
   makes "off" shut down PV only; a remote-operated disconnect under it needs 705.20(C)(3)
   (opens by itself on loss of control power, not a shunt trip). 706.15(D): is the WallMount's own
   breaker the disconnect within sight of the field-serviced battery (EG4's listing)? 480.10(E)
   door hardware if the AHJ calls `RM-B-ESS` a battery room. Battery voltage is not authored
   (14.3 kWh / 280 Ah is about 51 V).
6. **Repoint `CD-B-ATTIC-RISER`**: it names `ED-B-PANEL` as `from_ref`; PV dc runs to the inverter.
7. **210.63(A):** do the ERV (`EQ-B-ERV`, 4.9 ft from `ED-B-UTIL-RC1`) and refrigeration count as
   HVAC equipment needing a service receptacle? The text names heating, air-conditioning and
   refrigeration.
8. **Grade more of 210?** 210.52(E)(1), (H), (I) (cheap checks, also (F) laundry and 210.11(C)(4)
   garage circuit); and 210.70(A)(2)(3): does `ST-M2S`'s main-floor start have its own switch
   (`ED-M-STAIR-SW` names the basement lights)? Grading it needs a luminaire-to-stair link.
9. **Article 300.** (a) `SL-WK-C` carries no vehicles? Its west edge is 3-3.5 in. short of the 6 in.
   the walk row needs, so the buried EV (`CD-B-GAP-EV`, 14.2 in. under the walk) and V2H
   (`CD-B-V2H-GAP`, 13.8 in.) legs read 18 in. required: widen the walk, move the runs east, or
   bury 4 in. deeper? (b) Buried EMT needs approved corrosion protection that is also approved for
   the condition (358.10(B)(1); aluminium EMT 358.10(B)(2)): which, and which wet-rated conductor?
   Is the V2H PVC Schedule 80 throughout (352.10(K); the model holds only `pvc`)? (c) Is
   `CD-B-SPA`, cast into `W-SG-W1`, acceptable to the inspector? (d) A seal at the warm end of each
   raceway leaving the house (300.9(A)(1))? (e) A modelled fire-resistance-rated assembly for 300.23
   (the ESS closet is an owner standard).
10. **Service.** (a) Is the CL320 meter-main a metering center with each 200 A main in its own
    compartment (230.71(B)(4); one shared enclosure is allowed only for existing equipment)? (b)
    The FS140's UL 1449 In (230.67(E), 10 kA; also 215.18(E)): add it to the type next to
    `surge_ka`. (c) A switch at `D-B-FURN` (`electrical.equipment_space_lighting` UNKNOWN for
    `RM-B-FURNACE`/`RM-B-WORKSHOP`: nearest switch 7 ft / 9.5 ft off, 210.70(C)(1)).
11. **Article 722.** (a) Outdoor cable for `CD-M-RSD-INIT`, `CD-M-DATA-PORCH`,
    `CD-M-DATA-CAM-PORCH`, `CD-M-DATA-CAM-CANOPY` (722.2(B), UNKNOWN today; `CD-M-DATA-ENTRY` is
    schematic): wet-listed outdoor Cat 6A and a wet-marked 16 AWG Class 2 pair for the RSD
    initiator, or metal-sheathed? (b) PoE class of the doorbell, cameras and APs and the bundle
    count at `ED-B-NET-PATCH` (Table 722.140(B)(2) cannot bind below 92 cables; 24 AWG 60 degC);
    author `poe_class` only if a check is wanted. (c) Do the LED-driver output cables carry a
    CL2/CL3 listing (722.140(A)(3))? (d) Are the 24 V drivers marked Class 2 (721.30(A)/(C);
    411.6(A), PoE labels)? The 200 W `ED-T-LT-PSU-200` (no instance placed) exceeds the 100 VA
    a Class 2 source holds to. And what is the PureEdge TS24M-2C rail's ampere rating (410.150(B):
    the 40 W supply is 1.7 A at 24 V; the two heads draw 0.9 A)? A `limited_energy_class` field
    beside `output_voltage` would let a check grade 721.30; not built.
12. **Model the spa tub as `Equipment` kind `SPA`** (footprint, `spa_self_contained`, in-ground vs
    listed aboveground (the 680.42(B) waiver), rim height, perimeter paving, metal within 5 ft:
    `W-SG-W1`, railings; `CKT-SPA`'s EGC and wiring method, 680.7/680.14, today EMT). It unblocks
    680.13 (`ED-B-SPA-DISC`), 680.22/.41(B) distances, 680.26 bonding, 411.6(B) (lighting 10 ft
    from the water) and 722.135(B)/680.11 (data within 5 ft). `code.NEC_680_spa` grades `CKT-SPA`
    now (Class A GFCI PASS, 680.41(A) N/A).
13. **V2H** (`CD-B-V2H-SPARE`/`-GAP`): a bidirectional EVSE must be listed and marked (UL 9741) and
    follow 702 or 705 (625.48); a second source on the backup side brings 705.76; 625.50 holster
    height (18 in. indoors, the Grizzl-E is mounted 42 in. AFF) needs
    `ElectricalDeviceType.connector_holster_height`.
14. **Name the NEMA on two generic receptacle types** (`ED-T-RECEPTACLE-SINGLE-GANG` behind
    `ED-M-LIVING-RC16` on `CKT-KITCH-SA1`; `ED-T-LEV-GFCI-DF` behind `ED-G-GDO-GFCI` on `CKT-LT-MAIN`)
    so `electrical.multi_receptacle_rating` (210.21(B)(3)) can pass them. 210.23(B)(2) (fastened
    equipment at most 50% of a mixed circuit) needs fastened-vs-plugged on `Equipment`; `CKT-WH` is
    1,440 VA on 15 A, exactly the 80% cord-and-plug cap (210.23(B)(1)).
15. **215.18 per panel** (read 2026-11-14): all three feeder panels hold a plug-on Type 2 SPD
    breaker (PASS). Confirm each plug-on's marked In (10 kA or more, 215.18(E)) and listing
    (C); the model has no field for either.

## Other open Catlin items

- **Water bond.** The 250.104(A) bond `BC-B-WATER` is #4 Cu, under Table 250.102(C)(1) on every
  basis: **#2 Cu** for a 320 A service (310.12(A) at 83%: 300 Cu / 400 Al; also 2 x 4/0 Al
  summed), **#1/0 Cu** only if the service counts as 400 A; a larger utility lateral raises it
  (3/0 Cu cap). The GECs meet 250.66(A)/(B). Open: the lateral's size (Xcel/electrician).
- **Art. 440.** `electrical.hvac_disconnect` is UNKNOWN for `EQ-S-HP1-AH` (no disconnect on
  `CKT-HP1-AH`: integral, or a service switch in the attic?). Author HP2's and HP3's MCA and
  maximum OCPD (30 A, 15 A breakers) on the equipment types from the Gree submittals to grade
  440.4(B)/440.22/440.35. Lockable or tool-opened enclosures for `ED-M-HP1/2/3-DISC` (440.11);
  an ampere rating on `ED-T-DISCONNECT-3R` for 440.12(A)(1); available fault current for 440.10.
- **Art. 424.** Lock-off or service-disconnect reading for the heating breakers (424.19); the
  Schluter thermostat as disconnect (424.20(A)).
- **404/406/408.** `electrical.bath_receptacle_zone` UNKNOWN for `ED-M-BATH2-TUB-RC` (the Bask
  outlet, inside the 3 ft zone, 406.9(C)(1): AHJ question) and `ED-A-STUBATH-GFCI` (is the shower
  glass a fixed barrier?). Mark `ED-S-PLANT-HEAT-RC` (on a D315S relay) "controlled" (406.11(D)).
  Receptacle types need `weather_resistant`/`in_use_cover` fields (406.9(B)(1)). 408.6 needs an
  available fault current at the service and SCCRs for the panels.
- **110.26 not graded:** the door-swing sentence, (D) lighting (`RM-B-FURNACE` has four luminaires
  on plain switches; no typed marker for automatic-only control), and the (E)(2) outdoor zone of the
  meter-main.
- Revisit Class C SPGFCI for `CKT-HP1-3` after the NFPA Standards Council (2026-12-15/16,
  ACCA/AHRI appeals); they are Class A breakers meanwhile.

## Engine gaps (not graded)

- Not modelled: 120.11(A) motor treatment inside 120.6; 120.7(C)(2) minimum operating current for
  a PCS that also monitors noncontrolled loads; 120.5(B) rounding; 314.16(B)(2)/(3)/(6) box-fill
  allowances; 314.24(B) projection add-ons; raceway supports, fittings and strap points
  (Tables 344.30(B), 352.30(B), 358.30); a 225.10 check on undrawn outdoor branch wiring.
- Checks that read a printed rule loosely (audit 2026-11-13): `receptacle_spacing` credits a
  receptacle on a wall's other face and breaks wall space at a stationary appliance only beside a
  cabinet (no fireplace break); (C)(1) Ex. 1 breaks the wall line only where the appliance
  touches it, not at 12"/18"; `island_receptacle` skips peninsulas, has no (C)(3) 20" window and
  FAILs where (C)(2) provisions would do; (D) measures to the vanity, not each bowl, and accepts a
  free-standing receptacle; `appliance_receptacles` never traces an appliance's own circuit; the
  AFCI occupancy table reads STORAGE as closets and omits STAIR and a UTILITY room holding
  laundry; (G)(1) treats an unset mount as the floor; `code.NEC_250_94_ibt` is N/A without a data
  entry and models no terminal count, external mount or building-disconnect IBT; `gec_size` grades
  only the 250.66(A)/(B) caps; the water bond is graded for connection, not size; no field states
  250.24(B) neutral isolation; 705.12 tries (B)(1)/(B)(2)(a) only; `code.NEC_250_32_separate_buildings`
  traces circuits, not feeders (a garage subpanel reads N/A) and not the EGC;
  `rod_electrodes` skips 250.53(A)(4) drive and (B)/(D); no service conductor size, so Table
  250.66's general rows and 250.64(D) stay ungraded.
- 625.47 if a V2H charger takes its own feeder; 411.2, 411.6(A) and 411.7(B) are listing facts;
  210.70(C)(3) needs a sensor device kind.

## Still to read in print

Each entry names what the printed text decides for Catlin or the engine.

- **410.154** past "two supports": how the PureEdge rail is supported (410.150(B) question in Q11d).
- **300.2-300.3**: conductors of one circuit in one raceway; mixed-system separation for the data
  and RSD runs (Q11).
- **300.9(A)(2)-300.21**: support, boxes at splices, free conductor length, securing and fill;
  what lane G's `ConduitRun` seal field and the raceway checks must grade.
- **300.25(C)** onward: plenum/air-handling spaces, for runs through the soffit plenums.
- **Tables 344.30(B), 352.30(B), 358.30**: raceway supports and strap points (an engine gap; no
  rows in any paraphrase doc).
- **680.27(B)-680.33**: covers and other pool equipment; whether any applies to a future tub.
- **250.64**: GEC protection and routing, for `gec_size` and the meter-main GEC path.
- **250.53(A)(4)**: rod drive (depth, angle), for `rod_electrodes`.
- **406.9(B)** opening, rest of **406.14**, **408.4**, **406.30(C) Ex.**, and the **406.48-406.50 vs
  404.20** numbering: weather-resistant/in-use scope, panel circuit directory, switch marking and
  electronic switches (lane E's device fields).
- **The sauna heater's article and listing rule** (not in 424 as printed): what grades the sauna
  circuit and its controls.
- **705.3-705.4**: other-article scope and listing, for the PCS/inverter questions (Q3e).
- **705.81** onward: microgrid rules, whether island mode makes Catlin a microgrid.
- **Table 625.52(B)(1)**: ventilation for indoor charging, if the garage EVSE needs it.
- **230.4(B)-(D)** and **230.93** onward: service conductor sizing and service-equipment
  protection; unblocks Table 250.66's general rows and 250.64(D).
- **Minor PV** (690.3, .5, .10, .14, .35-.40, .46, .48-.55): no known Catlin question; confirm.
- **725.127** (411.8(A)): Class 2 lighting circuit wiring.
- **Article 445** beyond 445.12: if a portable generator inlet is ever added.
- **Table 723.20**'s body and **724.46** (722.15(K)): limited-energy cable substitutions (Q11).
