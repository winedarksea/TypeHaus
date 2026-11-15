# TODO: 2026 NEC residue (decision #120)

Open items only (delete done ones). The rows in `docs/code-notes/nec-2026-paraphrase.md` (index)
are read in the printed code (2026-11-13/14); each doc's **Engine** lines list the rules no check
grades. `UNCONFIRMED` in `model/nec.py` is empty. Rewritten 2026-11-14 after the nine-lane pass
(decisions #120, #134): design and software items, the printed book and a future tub.
Catlin: 0 FAIL, 146 UNKNOWN (162 before).

## Off the model

EG4, Square D, electrician, AHJ and Xcel questions, label reads on delivery and the plant-heater
plug setting are holds, not design: `houses/catlin/notes/construction_holds.md` (supplier
confirmations, AHJ readings, Utilities, Delivered parts, Commissioning). An answer that changes
the model comes back here.

## Owner

- Meter-main product (CL320 class): 230.71(B)(4) separate compartments; backup panel make (its
  SPD In and SCCR, `CKT-SPD-BACKUP`).
- Foyer soffit `SF-M-MUD-DRAIN` vs leaving `PR-M-S-BATH1-TUB-DRAIN` exposed (`Room.exposed_services`).
- Garage temperature sensor for an HA alert (a published Zigbee/Thread part rated to -20 °F), and
  whether the hardwired `AL-G-HEAT` stays: check the printed basis of `code.R315_garage_alarms`
  (it cites R315.2.2 with no source in the repo).
- EV holster placement (42 in. beside the Grizzl-E, a reversible default).
- Spa: the whip from `ED-B-SPA-DISC` to a future tub (680.7/680.14 UNKNOWN); the tub's own 680
  rules when a tub is chosen (`notes/grounding_bonding.md` §10).
- PoE classes and the `ED-B-NET-PATCH` bundle count: author only if a check grades 722.140(B)(2).
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
