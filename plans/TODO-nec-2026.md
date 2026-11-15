# TODO: 2026 NEC residue (decision #120)

Open items only (delete done ones). The rows in `docs/code-notes/nec-2026-paraphrase.md` (index)
are read in the printed code (2026-11-13/14); each doc's **Engine** lines list the rules no check
grades. `UNCONFIRMED` in `model/nec.py` is empty. Rewritten 2026-11-14 after the nine-lane pass
(decisions #120, #134): what is left waits on EG4, the AHJ, Xcel, the electrician, the printed
book or a future tub. Catlin: 0 FAIL, 146 UNKNOWN (162 before).

## EG4 (send; also `houses/catlin/notes/backup_power.md` §12)

1. Grid-port maximum OCPD: 63 A or 80 A for one 12kPV, and what decides it (63 A is authored).
2. GRID/LOAD/GEN terminal rating, 60 °C or 75 °C (`CKT-ESS-GRID` is #6 Cu on the 60 °C column).
3. With the grid breaker open, can the GRID terminals be energized (705.20(F) warning, the
   conditional 404.8(C) backfeed label)?
4. Island mode: does the load port bond neutral to ground (250.30, 702.7(B) sign; `ED-B-BACKUP-PANEL`
   is authored isolated as the reversible default)? Open-phase protection (705.30(E), 408.36(D))?
5. Does the LOAD port carry its own OCPD for the load-port conductors (705.60/705.30), or does
   `ED-B-BACKUP-PANEL` need a 50 A main?
6. Restart after an off-grid overload shutdown: automatic or manual (702.4(A)(3))?
7. External RSD switch NO or NC on the current board (the manual/QSG and the Hybrid RSD Wiring
   Guide disagree)?
8. Does the WallMount breaker open both + and − (706.15(D)(1))?
9. The UL 9540 certificate naming the 12kPV plus one WallMount Indoor. Also the 702.6 signal means
   (inverter display, HA) — unmodelled.

## Electrician / product labels

- Review every proposed conductor size (`circuits*.py`, "engine's proposal"), including voltage
  drop on long runs (which would trigger 250.122(D)).
- **`ED-T-PANEL` bus rating** off the label: the QO154M200P sheet publishes only 200 A. The model
  assumes 225 A; at 200 A the 120% rule allows 240 A against 241.25 A and 705.12 fails.
- FS140 In off its label (230.67(E) UNKNOWN), and where a Type 2 lands at the CL320 (load side
  of a main). HOM2175SB label wording ("type 1" vs "type II"; 10 kA taken as In).
- HOM290 terminal temperature (75 °C allows #3 on `CKT-GAR-FEEDER`); a 90 A plug-on in the
  HOM2040M200PC; HOM1224M100PRB ambient 23-104 °F in the unheated garage; its ground bar kit;
  the short undrawn stub-up into `ED-G-PANEL`.
- Square D QO1PAF lock-off fit on the QO GFCI/AFCI breakers of `CKT-FH-BATH1/2` (424.19).
- DU222RB date code (Schneider PRB-207512, 1401-1803) on delivery.
- `CD-B-INV-BACKUP` conductor sizing; final PV wire and EGC (10 AWG PV 2000 V proposed).

## AHJ readings

- 406.9(C)(1): the Bask outlet `ED-M-BATH2-TUB-RC` sealed in the tub deck box as a fixed barrier;
  is the studio shower glass a barrier for `ED-A-STUBATH-GFCI` (2.2 ft)?
- 210.52(A)(2): a rafter plate under 5'-0" of head is not wall space (owner's reading, R304.3).
- 210.70(C)(1): a door into a room with no other door is not an "entry" (D-B-ESS).
- 210.63(A): does the ERV count as HVAC equipment?
- 480.7(B) below 60 V (the derived EMERGENCY DISCONNECT label is conditional); `RM-B-ESS` as a
  battery room (480.10(E)); 706.15(D) not graded.
- Q9c `CD-B-SPA` EMT cast into `W-SG-W1` (300.7(A)(3), burial UNKNOWN); Q9e a fire-rated assembly
  for 300.23.
- 625.43(C) "remote" (no longer derived: the EV breaker is in `ED-G-PANEL`); 690.31(D)(2) label
  count on concealed lengths.
- Ufer earth contact: footings on 7 in. washed stone over geotextile (`code.NEC_250_52_ufer`
  UNKNOWN), at the footing inspection.

## Xcel

- Available fault current at the meter (`available_fault_current_a`): `electrical.panel_sccr`
  (5 panels) and 440.10. Lateral size: past 500 kcmil Al / 350 Cu it raises the water bond to 1/0.

## Owner

- Meter-main product (CL320 class): 230.71(B)(4) separate compartments; backup panel make (its
  SPD In and SCCR, `CKT-SPD-BACKUP`).
- Foyer soffit `SF-M-MUD-DRAIN` vs leaving `PR-M-S-BATH1-TUB-DRAIN` exposed (`Room.exposed_services`).
- Plant heater on the Eve Energy plug: 12.5 A continuous is 83% of its 15 A; run at a low setting
  or confirm continuous duty.
- Garage temperature sensor for an HA alert (a published Zigbee/Thread part rated to -20 °F), and
  whether the hardwired `AL-G-HEAT` stays: check the printed basis of `code.R315_garage_alarms`
  (it cites R315.2.2 with no source in the repo).
- EV holster placement (42 in. beside the Grizzl-E, a reversible default).
- Spa: the whip from `ED-B-SPA-DISC` to a future tub (680.7/680.14 UNKNOWN); the tub's own 680
  rules when a tub is chosen (`notes/grounding_bonding.md` §10).
- Datasheet gaps: `internal_clamps` on RACO 232/192 and Carlon B122A/BH235A/B520A; `rear_projection`
  for the GFCI and smart-switch types; PureEdge `CR-M-LAUNDRY-24V` cable OD; Schluter floor-heat
  lead ODs (4 runs, raceway fill UNKNOWN); `CD-M-DATA-ENTRY` elevations and cables.
- Q11b-d: PoE classes and bundle count (no check uses them); LED-driver output cable listing
  (722.140(A)(3)) and Class 2 marking (721.30): OMNIDRIVE X 60 W and PureEdge PSB-40W are Class 2,
  Mean Well HLG-100H-24A and IKEA TRADFRI 30 W state none, the 200 W OMNIDRIVE is not (unplaced);
  the TS24M-2C rail publishes no ampere rating.
- Revisit Class C SPGFCI for `CKT-HP1-3` after the NFPA Standards Council (2026-12-15/16).

## Engine gaps (not graded)

- 110.26 door swing (no enclosure door leaf or egress path); 314.16(B)(6) terminal blocks;
  raceway supports (Tables 344.30(B), 352.30(B), 358.30); 440.10; 706.15(D); 705.12 (A), (B)(5),
  (B)(6); 702.6 signals; 411.2/411.6(A)/411.7(B) listing facts; 210.70(C)(3) sensor kind.
- Whole-service 120.82 never counts garage general circuits (the floor area excludes the garage).
- Raceway fill counts a neutral on every 2-pole circuit (conservative); feeder neutral full size.
- 250.122(D) needs Chapter 9 Table 8; Al GECs graded only against 250.66(A).

## Still to read in print

Each entry names what the printed text decides.

- **210.52(A)(2)** wall-space definition (the attic plate reading); **210.52(I)** remaining
  wording (fixed cabinets as breaks); **210.70(A)(2)(3)** distance for "at each floor level"
  (10 ft is the engine's reading); **(C)(1) Ex. 1** what the 12"/18" setback is measured from.
- **225.10** the full method list (is ENT on it?); **225.30(A)** full text (no single-listing EVSE
  exception); **215.2(A)(1)** and **220.61** neutral reduction; **430.22, 430.24, 440.6** (the
  120.11(A) cross-references); **240.4(D)(2)/(3)**; **Chapter 9 Table 8**.
- **250.94** IBT bonding-conductor size; **250.53(B)** tail (bonded electrodes as one system);
  **250.24** lettering; **250.64** (B) protection and routing.
- **705.3-705.4** (PCS listing scope, Q3e); **702.4(A)(2)(b)** and **130.70** (an export-limit
  setting as an EMS/PCS control setting); **705.81** onward (microgrid).
- **721.30** Class 2 source limits; **Table 723.20** body (Chapter 9 fill for communications
  cable); **724.46** (722.15(K)); **725.127** (411.8(A)); **722.2(B)**: is "Wet Location rated per
  UL 83" the same as listed and marked; **690.31** PV wire inside a building in a raceway.
- **300.2-300.3** (one circuit per raceway, mixed systems); **300.9(A)(2)-300.21**; **300.25(C)**
  onward (plenums).
- **410.154** past "two supports" (the PureEdge rail); **680.27(B)-680.33**; **406.9(B)** opening,
  rest of **406.14**, **408.4**, **406.30(C) Ex.**, **406.48-406.50 vs 404.20** numbering.
- The sauna heater's article and listing rule; **Table 625.52(B)(1)**; **230.4(B)-(D)**,
  **230.93** onward; minor PV (690.3, .5, .10, .14, .35-.40, .46, .48-.55); **Article 445** past
  445.12.
