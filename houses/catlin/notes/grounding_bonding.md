# Grounding, bonding, surge and lightning hooks (decision #123, 2026-11-10)

Model: `plan/electrical_grounding.py` (elements), `plan/grounding_types.py` (parts),
`params/foundations.py` (`_ELECTRODE`, the Ufer bar). Engine: `resolve/grounding.py`,
`checks/mep/electrical_grounding*.py`, `takeoff/grounding.py`. Article 250 numbers were read
in the printed 2026 NEC (2026-11-13; `docs/nec-2026-paraphrase.md`); every NFPA 780 number
here is unread first-hand.

## 1. Owner decisions (2026-11-10)

- **Electrodes:** a Ufer in FT-B-W1/W2 plus two rods at the meter-main.
- **Lightning:** design hooks only — a counterpoise with two corner terminals, a PV down-lead,
  coordinated SPDs, single-point entry with an IBT. No air terminals.
- **No Faraday cage** (§5). **No resistor/diode/capacitor between grounds** (§6).

## 2. What was wrong before

- The old comment in `plan/electrical.py` claimed a Ufer, but no footing authored any bar. The
  galvanized #4 in the basement walls sits behind exterior XPS, so it is not in contact with
  earth (250.52(A)(3)).
- It landed the GEC at `ED-B-PANEL`. `ED-M-METER` is a Class 320 **meter-main**, so it is the
  service disconnect: the GECs and the main bonding jumper land there (250.24). `ED-B-PANEL`
  is a feeder panel with an isolated neutral.
- The garage is a separate building fed by seven branch circuits: it needs its own electrode
  system (250.32). The court has no circuit filed in its own building (`ED-B-SPA-DISC` is on
  the basement storey), so `code.NEC_250_32_separate_buildings` finds nothing to require there.

## 3. Hand oracle

**Ufer length (250.52(A)(3), 20 ft min).** FT-B-W1 runs y 18'..36' and FT-B-W2 y 0..18', each
216". One #4 bar per strip on the bottom at 3" cover each end: 216 - 2(3) = 210" per strip.
The splice bar across the cold joint (50.1") is a lap and is not counted.
Qualifying = 210 + 210 = **420" = 35'-0"**, which passes. W1 alone (17'-6") would fail, which is why
the bar continues into W2.
Rebar added: 210 + 210 + 50.1 = 470.1" = 39.2 ft x 0.668 lb/ft = **26.2 lb #4 HDG**.

**Service basis (`SE-M-SERVICE`, 2026-11-14).** The Xcel lateral lands on the meter-main's
lugs and its size is unknown, so the basis is 310.12(A) on 320 A: 0.83 x 320 = 266 A, 300 kcmil
Cu (285 A) or 400 kcmil Al (270 A) at 75 C. Both sit in the "over 3/0-350 Cu / over 250-500 Al"
row. The 250.64(D)(1) summed basis, 2 x 4/0 Al = 2 x 211.6 = 423 kcmil, is the same row.
Table 250.66 and Table 250.102(C)(1) both give **#2 Cu** there. A lateral over 500 kcmil Al
(350 Cu) would move the water bond to 1/0 Cu (3/0 cap): ask Xcel for the lateral size.

**GEC sizes (250.66).** The row gives #2 Cu, but a sole connection to rods needs no more than
#6 Cu (250.66(A)) and to a concrete-encased electrode no more than #4 Cu (250.66(B)).
- `BC-M-GEC-ROD` is #6 Cu, 9.7 ft.
- `BC-M-GEC-UFER` is **#2 Cu**, 10.4 ft, over the #4 cap: the water bond lands on its stub, and
  250.104(A)(1) lets it land on an electrode only if that GEC is as large as the bond. It is
  insulated through the rim and inside the wall.
- Garage (250.32(E)): largest supply conductor #6 Cu (`CKT-EV-1450`) gives #8 Cu; `BC-G-GEC` is #6.

**Water bonds (250.104(A)(1)).** Table 250.102(C)(1) on the basis above: **#2 Cu** for
`BC-B-WATER`, `BC-B-WATER-WH` and `BC-B-WATER-BATH` (each is the only bond path for the
copper it reaches).

**Rods (250.53).**
- Both rods are 8 ft. House rods are at (-31", 20'-0") and (-31", 34'-4"): 172" = 14'-4" apart, at
  least 6 ft. Garage rods are at (3'-4", 50'-0") and (3'-4", 66'-0"): 16'-0" apart.
- Every rod top is 24" below grade (-58" absolute), clear above the 3 ft power lateral at y=18'.
- The rods are a backstop: the Ufer's earth contact is the AHJ's call (§4), and the rods qualify
  either way.

**Conductors billed.**
- 1/0 Al: 41.5 LF.
- #2 Cu: 130.7 LF (counterpoise, PV tail, `BC-M-GEC-UFER` and the three water bonds).
- #6 Cu: 35.0 LF (with the garage IBT bond).
- No slack is added. Water bonds, the IBT bond and the garage GEC are straight-line (the
  electrician routes them).

## 4. Open: earth contact (AHJ question)

FT-B-W1/W2 bear on 7" of washed #57 over non-woven geotextile, with 4" side foam
(`FootingBedding`). NEC asks for "direct contact with the earth". Whether a drained stone bed
counts is the inspector's reading, so `code.NEC_250_52_ufer` is UNKNOWN until it is asked. Ask at
the footing inspection. The two rods make the electrode system complete whatever the answer.

## 5. Pour-deadline items (footing inspection hold)

1. Tie the #4 HDG electrode bar on chairs at 3" in FT-B-W1, and splice it into FT-B-W2 with a class
   lap past the cold joint.
2. Stub it up inside W-B-W1's face at the panel bay (13", 28'-0"), between the two panels' 110.26
   working spaces, 13" above the slab. Fit the
   listed clamp (`GND-UFER-CLAMP`) after the pour.
3. **No cathodic anodes on any bonded mat.** An anode tied to a grounded system discharges into
   the earth, not into the steel it protects. Re-read this before adding Galvashield anywhere.

## 6. Rejected: tying grounds through resistors, diodes or capacitors

The idea was to isolate the lightning path from the power ground with a resistor, diode or
capacitor between them. It is rejected and must not be re-proposed:

- **Code.** NEC 250.106 requires the LPS grounding to be bonded to the building's electrode
  system. NFPA 780 4.14 requires a common grounding. Both require a solid conductor.
- **Physics.** About 30 kA through 5 Ω puts about 150 kV across the part, so it flashes over at
  the first stroke. A stroke carries 10^5 to 10^7 J against a component pulse rating on the order
  of 0.7 mJ.
- **It inverts the goal.** Two grounds held apart develop the very potential difference that
  causes side flash and equipment damage. A bond equalises them. `code.NEC_250_106_lps_bond`
  grades by graph connectivity for exactly this reason.

## 7. Rejected: the metal skin as a Faraday cage

The Galvalume skin is not electrically continuous:
- painted laps;
- EPDM-washered screws;
- concealed-clip B&B over KDAT girts.

Making it a cage would mean bonding every panel and running down conductors at every corner,
which amounts to a full NFPA 780 system. It would also do nothing for the surge that enters on
the service and data conductors, which is the realistic damage path here. That path is handled
by the coordinated SPDs and single-point entry with an IBT.

## 8. Lightning hooks

- **Counterpoise:** bare #2 Cu, 24" deep. It runs from `GE-B-LPS-SW` north along the west wall
  through both service rods, round the NW corner at y=39'-10", and east to `GE-B-LPS-NE`
  (diagonally opposite).
  - It clears the entry piers (y <= 38'-3"), the garage pads (y >= 41'-6"), both HP pads, the
    sewer (8 ft deep) and the water service (6 ft).
- **PV down-lead:** 1/0 aluminium on seam clips from SP-A-PV-W9, north to the rake, down the rake
  and the NW corner trim. It transitions to bare Cu 18" above grade (Al within 18" of earth is not
  permitted, NFPA 780 4.4.1) and lands on GE-B-ROD-1.
  - Copper is never used on the Galvalume.
  - Confirm the S-5 PVKIT's UL 2703 bonding.
  - Owner to judge the lead's look on the NW corner from a render.
- **SPDs:**
  - Type 1 `ED-M-SPD` beside the meter-main (230.67).
  - PV DC SPDs at `ED-A-PV-JB` (`ED-A-PV-SPD`) and at the EG4 inverter (`ED-B-INV-SPD`), because
    the EG4's DC surge rating is unpublished.
  - Type 2 `ED-G-SPD` beside the garage EV outlet.
- The PV DC runs (`CD-B-ATTIC-RISER`, `CD-A-PV-EAST`, `CD-B-PV-INV`) carry `Service.POWER_DC` and
  are continuous EMT.
- **Single-point entry:** power and data enter on W-M-W1 within 3 ft. `ED-M-DATA-ENTRY` feeds
  `CD-M-DATA-ENTRY` to the patch panel, and the IBT (`ED-M-IBT`) is bonded to the meter-main (250.94).
- **IBTs (250.94(A)):** `ED-M-IBT` at the service and `ED-G-IBT` beside `ED-G-GND-JB` in the
  garage (a building branch circuits supply needs one at its disconnect). The nVent ERICO IBTB
  sheet: five bonding connectors (#14-#6) plus a #6-#2 GEC lay-in.
- **Neutral (250.24):** the main bonding jumper is in the meter-main; `ED-B-PANEL`,
  `ED-B-PANEL-2` and `ED-B-BACKUP-PANEL` keep their neutral bars isolated (bonding screw out).
  Whether the EG4 bonds N-G in island mode is the inverter's question (702.7(B)/250.30).
- **Water bonds:** #2 Cu from the Ufer stub to the copper cold at the heater, with jumpers to the
  copper HW trunk and the bath branch (250.104(A)). The PEX service (`PR-G-SERVICE-CW`) is not an
  electrode.

## 9. NFPA 780 to read first-hand before a full lightning system

The items to check, all UNCONFIRMED:
- the Class I conductor sizes (Cu/Al, main and bonding);
- the ground-ring depth and offset from the foundation (4.13.4);
- the 18" aluminium rule;
- common grounding (4.14);
- surge protection (4.20);
- whether the 24 ga panels may serve as strike termination devices.

## 10. Spa rough-in: what a future tub must meet (owner, 2026-11-14)

No hot tub is set at construction. `CKT-SPA` (50 A 2-pole Class A GFCI, `ED-B-PANEL-2`) is
built to `ED-B-SPA-DISC` on `W-SG-W1` through `CD-B-SPA` and carries `rough_in_only=True`; its
11.5 kW stays in the service load calc. `code.NEC_680_spa` reads 680.13, the distances and
680.26 as N/A from that statement, and still grades the circuit (680.44(A)/680.5(B) GFCI;
680.7/680.14 UNKNOWN until conductors and EGC are authored). Before a tub is set, model it as an
`Equipment` of kind `SPA` (footprint, `spa_self_contained`), clear `rough_in_only`, and meet
(2026 NEC, paraphrases in `docs/nec-2026-paraphrase-680.md`, `-411-230.md`, `-722.md`):

- **680.13:** `ED-B-SPA-DISC` at least 5 ft horizontally from the water's edge (or a permanent
  barrier giving a 5 ft reach), within sight of the tub, readily accessible. Site the tub so
  the existing can qualifies, or move the can.
- **680.22(A)/680.41(B):** no receptacle within 6 ft; at least one general receptacle 6-20 ft,
  under 6 ft 6 in. up (`ED-B-SPA-RC` qualifies only if it lands in that band); every
  receptacle within 20 ft GFCI. Other equipment over the low-voltage limit (disconnects,
  panels, boxes) 5 ft away unless walled off or the tub is listed self-contained. Indoors,
  680.43 stands in.
- **680.22(B)-(F), 411.6(B):** luminaires within 5 ft at least 12 ft over the water; GFCI in the
  5-10 ft band unless 5 ft up and rigidly fixed; low-voltage lighting 10 ft from the water;
  switches 5 ft; data and signal outlets 10 ft by cord path.
- **680.26:** equipotential bonding of the shell, the perimeter surface 3 ft out, and fixed metal
  within 5 ft horizontally or 12 ft above the water (`W-SG-W1` rebar, door frames, railings,
  `CD-B-SPA`, the disconnect enclosure), 8 AWG solid Cu. **680.42(B)** waives the perimeter only
  for a listed self-contained aboveground tub, not indoor-only, on or above grade, rim at least
  28 in. over every perimeter surface within 30 in.
- **680.11, 722.135(B):** wiring within 5 ft of the inside wall is RMC, IMC, rigid PVC, RTRC,
  burial-listed jacketed MC, or burial-listed LFNC/LFMC; nothing under the tub unless it serves
  it. **680.42(A):** a packaged or self-contained unit may take liquidtight flex or a 15 ft GFCI
  cord. **680.7/680.14:** insulated Cu EGC per 250.122 (12 AWG minimum); EMT is not on the
  corrosive-location list, so the whip from the can is liquidtight or PVC.
