# TODO: 2026 NEC residue (decisions #120, #134, #135)

Open items only (delete done ones). Rewritten 2026-11-14 after the residue pass: what is left
waits on the owner, a supplier, the NFPA Standards Council or the printed book. Standing limits
(what the engine deliberately leaves ungraded) are listed in
`docs/code-notes/nec-2026-paraphrase.md`, not here. Catlin: 0 FAIL, 148 UNKNOWN (143 before:
+5 visible fact-gated rows, -1 for the backup SPD).

## Off the model

EG4, Square D, electrician, AHJ and Xcel questions, label reads on delivery and the plant-heater
plug setting are holds: `houses/catlin/notes/construction_holds.md`. The rows now graded and
waiting on them: 440.10 (Gree nameplate SCCR, Xcel's available fault current), 706.15(D)(1)
(what the WallMount's breaker opens), 702.6 (a carrying-load signal; HA alert likely), 411.2 /
411.6(A) / 411.7(B) (TRADFRI listing; the Diode 200 W and HLG-100H-24A are not shown Class 2, so
their concealed 24 V wiring needs a Chapter 3 method or a Class 2 swap).

## Owner

- **110.26 access at `W-B-W1` (design finding).** With every enclosure door open at 90 degrees,
  no hinge assignment leaves 24 in. at `ED-B-BACKUP-PANEL`: the best is 23.87 in. between
  `ED-B-PANEL-2`'s north leaf and its own (PANEL-2 must hinge north to clear itself). Move the
  backup panel or PANEL-2 about 1/4 in. apart, or confirm the doors' hinge sides and leaf widths;
  then wire `access_findings` (`checks/mep/electrical_panel_doors.py`) into the check.
- **Meter-main pick** (230.71(B)(4) separate compartments, Xcel §4.11 approved lever bypass,
  ringless). Shortlist, 2026-11-14: (1) Eaton 400 A meter breaker, X (Xcel) bypass code,
  compartmented 200 A mains (brochure PA003034EN; exact catalog number from a distributor);
  (2) Siemens MK0402L1400RLM, two 200 A mains "in their own individual compartments", 22 kA,
  but Siemens is not on Xcel's named bypass list (ask Xcel); (3) Milbank U6601-X-2/200-BL,
  Xcel-listed bypass, 22 kA, compartment separation unconfirmed. Authoring `ED-T-METER` and a
  230.71(B)(4) row wait on the pick.
- **EV holster height**: 42 in. beside the Grizzl-E is kept (passes 625.50's 18 in.); say so if
  it should move.
- **Spa**: the tub's own 680 rules, the whip from `ED-B-SPA-DISC` and 680.14 wait on a tub
  (`notes/grounding_bonding.md` §10); 680.7(A)'s EGC size already passes.
- **Class C SPGFCI on `CKT-HP1-3`**: revisit after the NFPA Standards Council (2026-12-15/16).
- **`CKT-GAR-240`** counts as EV load at 100% in 120.82 because its description says "backup EV
  charging" (about 2.3 kVA more than as a tool receptacle). Conservative; left as is.

## Print questions: load-bearing

Each answer changes a graded result or the model.

- **210.52(A)(2)**: does an attic knee plate or rafter plate count as wall space? Yes/no; yes
  adds receptacle runs in the attic rooms.
- **210.70(A)(2)(3)**: what distance, in feet, makes a stair landing "at each floor level"? The
  engine reads 10 ft.
- **210.52(C)(1) Ex. 1**: is the 12 in./18 in. setback measured from the sink or range centre or
  from its edge? Changes the counter spacing on `CT-M-KIT-N`.
- **120.41**: does the general lighting unit load take in the 210.52(G) garage receptacles and
  210.70 garage lighting outlets? Yes means 120.82 is right to count nothing for
  `CKT-RC-GARAGE` / `CKT-LT-GARAGE`; no adds them to the service calc.
- **Table 250.66, aluminium column**: the conductor size per band. Opens grading an Al GEC.
- **225.10**: is ENT on the list of methods for a branch circuit on the outside of a building?
  Yes would clear `mep.raceway_use`'s ENT branch.
- **722.2(B)**: is "Wet Location rated per UL 83" the same as listed and marked for wet
  locations? Yes/no; decides `electrical.limited_energy_wiring` for the data entry.
- **Table 723.20 body**: does communications cable take Chapter 9 fill, and at what percent?
  Changes `mep.raceway_fill` on the data runs (held to Table 1 today).
- **702.4(A)(2)(b) and 130.70**: is an export-limit setting an EMS/PCS control setting? Yes
  would let `electrical.standby_capacity` grade the setting.
- **215.2(A)(1) / 120.61**: may the feeder neutral be reduced, and by what rule? Yes lifts the
  full-size neutral standing limit.

## Print questions: documentary

Answers refine a paraphrase or a citation; no graded result moves.

- 210.52(I) remaining wording (fixed cabinets as breaks); 225.30(A) full text (single-listing
  EVSE exception?); 430.22, 430.24, 440.6 (the 120.11(A) cross-references); 240.4(D)(2)/(3).
- 250.94 IBT bonding-conductor size; 250.53(B) tail (bonded electrodes as one system); 250.24
  lettering; 250.64(B) protection and routing.
- 705.3-705.4 (PCS listing scope); 705.81 onward (microgrid).
- 721.30 Class 2 source limits; 724.46 (722.15(K)); 725.127 (411.8(A)); 690.31 PV wire inside a
  building in a raceway.
- 300.2-300.3 (one circuit per raceway, mixed systems); 300.9(A)(2)-300.21; 300.25(C) onward.
- 410.154 past "two supports" (the PureEdge rail); 680.27(B)-680.33; 406.9(B) opening, rest of
  406.14, 408.4, 406.30(C) Ex., 406.48-406.50 vs 404.20 numbering.
- The sauna heater's article and listing rule; Table 625.52(B)(1); 230.4(B)-(D), 230.93 onward;
  minor PV (690.3, .5, .10, .14, .35-.40, .46, .48-.55); Article 445 past 445.12.
