# Air-distribution products — ducts, terminals, hoods (specification basis)

**House:** catlin
**Structure:** every air terminal (`REG-*`, 36), the two outdoor hoods
(`EQ-M-ERV-HOOD-OA`, `EQ-S-ERV-HOOD-EA`), their wall seals (`SP-M-ERV-OA-SEAL`,
`SP-S-ERV-EA-SEAL`), the outdoor legs' insulation (`DU-ERV-OA`/`-EA`) and the System 1
rectangular trunks.
**Written:** 2026-10-31, from web research (sources at the end) before the types were authored.
**Oracle for:** the face, neck and loss data on `plan/air_terminal_types.py` and
`plan/products_air.py`; the static budget arithmetic is `notes/erv_static_budget.md` §10.
**Companions:** `notes/erv_static_budget.md` — pressure; `notes/erv_service_access.md` —
reaching the dampers; `notes/plant_room.md` — why the plant room's pair is dampered.
**What is asked of the reviewer:** confirm each basis-of-design row against its source
(§2-§11). Trimless was declined (§12): the standard flanged family is modelled and priced.

> ⚠ **Every type is a PERFORMANCE SPEC plus a basis of design, "or equal"** (owner,
> 2026-10-30): commodity sizes any maker fits. A substitute must meet the face, the neck depth
> and the loss curve the type carries — not merely the nominal size.
>
> ⚠ **Several numbers are not published and are marked so.** No retailer page for the
> RenewAire FA8, the H&C 531SA or the Snappy boots could be read; where a face or depth is a
> planning figure the type's `source` says "estimated" and §13 names what to confirm on the
> submittal. Prices are in `prices.toml` only, as estimates (#28).

---

## 1. One family, and the rule for the geometry

White powder-coated metal wherever it makes sense: **100 mm steel disc valves** on the ERV
(supply and extract patterns), **extruded aluminium** grilles and registers on System 1. Each
type's `footprint`/`height` is the published FACE (a wall type authors face width and
projection, with the face height in `height`); its `TerminalNeck` is the part in the cavity
(boot, collar, damper box), drawn behind the face and graded by `mep.terminal_neck_fit`.

## 2. ERV disc valves — `REG-T-ERV-VALVE-SUP` / `-EXH` / `-EXH-WALL`, `-SUP-125`

| term | basis of design | or equal | value | source |
|---|---|---|---|---|
| valve, 100 mm | Vents-US AM 100 VRF (collar included) | Trox LVS/TVS 100, Lindab KU/KK 100, Zehnder ComfoValve 100 | face Ø 5 1/16" (128.5 mm), overall H 1 3/4", $19 | hvacdirect.com AM series sheet |
| spigot | 98 mm (3 7/8") | Trox LVS 100 ØD 99 mm | slips into a 4" snap-lock collar (101.6 mm ID) with ~1/8" play: **UL 181B-M mastic and 181B-FX foil tape** (metal duct, IMC 603.9), no adapter | inference, both sheets |
| loss, fully open (+5 mm) | — | Trox LVS 100, PD-02/2022 | 8 / 19 / 33 / 52 Pa at 10 / 15 / 20 / 25 L/s; <15 dB(A) to 15 L/s | Trox quick-sizing table |
| valve, 125 mm | Vents-US AM 125 class | Trox LVS 125 | face Ø 162 mm; 9 / 15 / 24 / 35 Pa at 15-30 L/s | Trox table |

- **The types carry Trox's curve, not the basis-of-design's**: Vents-US publishes none.
  Holding the or-equal to the Trox ceiling is the spec; ask Vents-US (888-640-0925) for theirs.
  Below 10 L/s (most terminals here) the curve is the published row's own K, so it is an
  extrapolation and is labelled as one.
- **Valves run near fully open**; balancing is at the plenum collar dampers (§8 of the
  budget). A valve is cleaned by pulling it from its collar; the lock ring keeps the setting.
- **Wall valves** use the ceiling collar screwed to bay blocking: nobody sells a sidewall
  collar. `REG-A-STUBATH-EXH` projects 1 3/4" (A117 §307.2 limit 4").
- **125 mm on the one 30 cfm terminal** (`REG-B-SUP2`): a 100 mm valve lost 17.1 Pa there and
  governed the machine; the 125 mm on a 4x5 increaser loses 8.2 Pa (budget §10.2).
- Not found: a stainless or aluminium valve sold retail (the plant room takes the
  powder-coated steel valve and a yearly clean), and supply-pattern published curves.

## 3. ERV floor extracts — `REG-T-ERV-EXH-FLOOR` (5)

A disc valve cannot go in a floor. **Reggio 412-AH** 2 1/4x10 aluminium floor grille (~$30),
or equal Reggio G412 / Shoemaker AFP, on a **2 1/4x10x4 stamped 90° boot** (Snappy P13-204 or
equal). Face 12 x 3 1/2" outside (Ferguson 412-AH listing, 2026-10-31); the boot's 5" height
is still an estimate — confirm it on the submittal (§13). Long side along the joist bay. Free area ~22 in² against the
duct's 12.6, so the grille is not the restriction; loss stays the derived K 5.

## 4. System 1 aluminium family

| type | basis of design | or equal | face | neck | price read |
|---|---|---|---|---|---|
| `REG-T-HP-SIDE-1206` (4) | TRUaire A220VO 12X06, double deflection, OBD | H&C HVD, Shoemaker 904-O | 13 3/4 x 7 3/4 | 12x6x2 11/16 (H&C HVD 3 7/16" overall less face) | $79.80 hvacquick |
| `REG-T-HP-STAIR-SIDE` (1) | A220VO 12X06 + TH-HP-STAIR-BOX-01 | | 13 3/4 x 7 3/4 | 12x6x4, centred 4in back collar | allowance |
| `REG-T-HP-STUDY-SIDE` (1) | TRUaire A220VO 08X06 | H&C HVD 8x6 | 9 3/4 x 7 3/4 | 8x6x2 11/16 | $68.60 |
| `REG-T-HP-FLOOR-0612` (3) | H&C 531SA 6x12, multi-shutter | Reggio, Shoemaker 600 | 13 3/8 x 7 3/8 (est.) | 12x6x2 (est.; TRUaire 150 is 2") | not read |
| `REG-T-HP-CEIL-DAMPERED` (1) | A220V 12X06, no OBD + ZD12X6TZ (§7) | | 13 3/4 x 7 3/4 | multipart boot, damper, collar and service hatch | allowance |

The sidewall faces are centred on the duct axis (faces grew 6" → 7 3/4", so every mount
elevation dropped 7/8"). Oak-match flush in RM-A-STUDY is a note only. Caution read on
Pace Supply: one listing calls the 220VO steel; order the **aluminium** A220 line.

The stair supply has an [explicit 4in branch and named register box](stair_supply_connection.md).

## 5. The return filter grille — `REG-T-HP-RET-FILTER`

**12x28x1 is not a stocked filter size** (Filterbuy, Filter King, AllFilters, Home Depot).
**No stocked size fits EQ-S-ERV-MIX's opening and clears 300 fpm:** 12x30x1 is stocked but
its 30" grille needs a 30" hole and the plenum is boxed in at 29 1/4" by the cabinet and
BED3's collar; 12x24x1 fits but runs 650 cfm over ~270 in² of media = **347 fpm**. So the
28x12 grille stays (H&C 673 class, hinged, or equal TRUaire 190RF / Shoemaker 620FG) and the
**filter is ordered as a custom 12x28x1 MERV 13** online — a standard order, not a quote.
336 in² at 650 cfm is 279 fpm (Manual D §4-10: 300). The rung that crossed the hole is now
headed off (`AO-S-HP1-RET`).

## 6. The mudroom transfer — `REG-T-TRANSFER-PAIR-1210`

A pair of 12x10 aluminium fixed-bar return grilles (TRUaire A170 class, or equal H&C A650) on
a lined sleeve through `W-M-STRW`'s bay. Acoustic alternative: Tamarack RAPR (baffled; no
published STC or free area found). `CD-M-DATA-DOORBELL` was moved 1/2" north to clear it.

`REG-T-TRANSFER-0606` (2026-11-03) is D-S-BATH1's offset pair: one 6x6 grille of the same
family on each face of `W-S-BD-N`'s lined west bay. The steel 170 6x6 lists 0.17 sf (~24 in^2)
effective; the aluminium A170's figure is unpublished. 20 cfm at 3 Pa needs 10.8 in^2.

## 7. Dampers, balancing and connectors

| item | basis of design | or equal | note |
|---|---|---|---|
| plant extract, 4" 24 VAC | EWC 4RSD spring-return (~$177) | Duro Dyne NSPRD024-4, Zonefirst RDSC | **at `DU-M-ERV-R-PLANT`'s start collar on the level-2 plenum in RM-M-MECH**, not behind the valve: serviced with no access panel in the humid liner; RH sensor local |
| plant HP supply, 12x6, 24 VAC | Honeywell Home ZD12X6TZ | dimensionally compatible equal | vertical airflow, west actuator, fabricated 26ga end boot; [dimensioned connection and service sequence](plant_supply_connection.md) |
| 4"/6" branch balancing | Imperial GV0851 / GV0853 spin collar with damper (DuctStandard) | Speedi AC-VDQ with quadrant | LSCD6 was a flanged starting collar, listed discontinued; locking quadrant not confirmed on the GV085x |
| air-handler connector | Duro Dyne MFN metal-fabric-metal | | NFPA 90A / 701 fabric; 3" fabric (suggested, not a code number) |
| mastic / tape | Hardcast Versa-Grip 181 (UL 181A-M/B-M) | Nashua 324A tape (UL 181A-P/B-FX), 3M 3340 | Iron-Grip 601 is B-M only; 3M 3381 is not UL 181 |

The plant supply now uses the ZD series' published 4" body and the M847D motor envelope.
The extract damper still needs its body and actuator dimensions confirmed (§13).

## 8. Hoods — `EQ-T-ERV-HOOD-8` / `-8-EXH`

RenewAire **FA8-P** (102409, paintable galvanneal, 1/4" metal screen, no damper) on both
legs, **no backdraft damper on either** (2026-11-05, C4 E3): Broan's manual §2.4 forbids one on
the discharge ("it can freeze in winter") and the ERV's own motorized port dampers close the
legs; the BD8 (102401) is dropped, its 8 Pa with it. Or equal: Fantech FML8 (white powder-coat aluminium, 9 x 9 plate) with its bug
screen swapped for 1/4" mesh — no curve published. 1/4" screen and not insect mesh, so frost
does not blind it. Published loss (chart end points, Q² scaled): **intake 23.3 Pa, discharge
14.8 Pa at 210 cfm** (budget §10.1, §10.10). FA8 plate and projection are unpublished: the model keeps
the 12 x 12 x 12 envelope, which is larger than either hood, so every clearance it passed
still holds. Painted to the north-face cladding. **10" option**: budget §10.4.

## 9. Outdoor legs: insulation and the wall line

- **Insulation:** two 1" layers of closed-cell elastomeric sheet, **AP Armaflex** (or equal
  K-Flex Insul-Sheet), joints staggered, Armaflex 520 adhesive, R-4.2 per layer = **R-8.4**,
  its own vapour retarder, over the whole of both legs. Two layers and not one 2" sheet:
  plain AP is 25/50-rated only through 1", and 2" FS reads ~R-7.1. 12" OD on an 8" duct,
  the OD every clearance was already graded at. Duct joints mastic-sealed first. **Kept over
  FSK fibreglass wrap** (owner, 2026-10-31; the ~$600-1,200 option is in
  `plans/cost-options.md` §1).
- **Through-wall detail, no bare metal** (owner, 2026-10-30), sequence:
  1. the duct is set and sealed before the ccSPF pass, through a 9" hole in the sheathing;
  2. the sprayer sprays the 4" ccSPF tight to the duct outboard of the sheathing;
  3. the mechanical sub then foams the sheathing annulus from inside with **low-expansion
     window-and-door PU** (Great Stuff Pro W&D or equal — it will not bow the duct) and
     carries the elastomeric through the gypsum into the stud bay, stopping 1-2" short of
     the sheathing, its end taped to the foam;
  4. the hood plate is sealed over the RO on the cladding.
- Modelled: `SP-M-ERV-OA-SEAL` / `SP-S-ERV-EA-SEAL` (`serves_duct`) bill `wall-seal-8in`
  kits; `mep.duct_penetration_fit` grades bare 8" + a 1/4" foam annulus in the 9" RO
  (1/4" spare each way); the wrap solid stops at the sheathing.

## 10. Retained stall fan nozzle option — `REG-T-NOZZLE-DAMPER-4`

The BATH2 dryer installation was removed 2026-11-02; this specification remains for reuse.

Shoemaker **1202-4** 4" aluminium spot nozzle ($119, hvacquick), or equal Schako DSARR-V, with
a 4" gravity backdraft damper in the duct above. No maker publishes a wet rating; aluminium is
the corrosion answer. The intake keeps its filter grille.

## 11. Ducts

- **ERV radials**: 4" galvanized snap-lock with stamped adjustable elbows (already billed).
  **30 ga**, from the DuctStandard (the library rows no longer name a gauge): IRC 2018 Table
  M1601.1.1 (= IMC 2018 Table 603.4, Minn. R. 1346) asks 0.013" for round to 14" at 1/2" w.g.
- **Trunks and risers**: 6"/8" galvanized; every seam UL 181B-M mastic or 181B-FX foil tape
  (IMC 2018 603.9; 181A is the fibrous-glass class). House-air ducts bare; OA/EA per §9.
- **System 1 rectangular trunks** (`DU-S-HP-SUP` 18x8, `-RET` 10x18, `-SUITE` 10x8,
  `-SOUTH`/`-SOUTH-RISE` 10x6): `material="galvanized"` now, matched to the gauge band rows
  `DUCT-T-GALV-RECT-*` (IMC 2018 Table 603.4 = IRC Table M1601.1.1, 1/2" w.g. column): **26 ga** for the 18"
  sides, **30 ga** for the 10" ones, printed on the duct schedule. Shop-fabricated,
  mastic-sealed, no liner (cleanability), canvas connectors at the air handler.

## 12. Trimless — declined (owner, 2026-10-31)

**Decision: no trimless terminals. Flanged everywhere, as modelled.** The study below is
kept as the record of what was weighed.

| candidate | product | installed $ vs standard (est.) | sequencing | access / cleaning | static / sound |
|---|---|---|---|---|---|
| `REG-M-SUP1` (living, ERV 4" supply) | disc valve with plaster-in frame (Lindab VGU + Airy, Trox Z-LVS subframe) | +$40-120 | frame in the 104 mm hole before taping; the duct stub must land exactly | disc twists out | same valve, no penalty |
| `REG-M-RET5` (living, ERV 4" extract) | same | +$40-120 | same | same | none |
| `REG-M-XFER-MUD` (12x10 wall) | mud-in flush cover (Invisagrille-type, magnetic face) | +$60-200 plus finishing | framed 12x10 opening and sleeve before board | face lifts off | free-area loss on a passive transfer: unpublished, the riskiest one |
| `REG-M-SUP3` (bedroom, ERV 4" supply) | plaster-in valve frame | +$40-120 | as SUP1 | as SUP1 | none |
| former stall-fan intake (removed 2026-11-02; retained 10" filter option) | **not recommended** | +$100-250 | no standard mud-in filter frame | the filter comes out every change | filter + reduced face: a real penalty |
| `REG-S-HP-STAIR` (12x6 sidewall in SF-S-DUCT's lining) | mud-in supply (Invisagrille 6x10 class; no 12x6 found) or a mud-in slot diffuser | +$100-250 plus finishing | frame set before the soffit is boarded; the boot flange meets the board face | magnetic face, damper behind | throw unverified at 50 cfm; free area unpublished |

**Likely total: about $400-1,100 over the standard family for the five that fit**, mostly
finishing labour. The disc valves (SUP1, RET5, SUP3) are the cheap, natural fit — a
plaster frame for the same valve; the EU frames need a US source confirmed before board.
The return `REG-S-HP-RET` is a poor fit: the hinged face is what reaches the filter, and a
mud-in face cannot hold one. (Whether the stairway request covered that return is moot now.)

## 13. Fit sign-off (Step 6a)

| item | governing clearance | result | from |
|---|---|---|---|
| hoods vs `EQ-M-HP3-OD`, `D-M-ENTRY`, `ED-M-HP3-DISC` | 12" envelope unchanged; intake base +4'-6" over the 110.26 space at +4'-3 1/2" | PASS (unchanged) | model; FA8/FML8 plates ≤ 12" |
| ROs 9" in the stud bays | bare 8" + 1/4" foam each side, 1/4" spare | PASS `mep.duct_penetration_fit` | model |
| EA off-centre bay, wrapped 12" | `framing_envelope` against the studs | PASS (unchanged) | model |
| girt courses at both ROs | unchanged ROs | PASS `structural.girt_course_spacing` | model |
| 33 ceiling/wall/floor necks vs framing and runs | ≥ 1/8" | PASS `mep.terminal_neck_fit` after the moves below | model + §2-§6 |
| `REG-B-SUP1` | collar on an FS-M-EAST joist | moved 4" to y=13'-4" (GYM leg with it) | |
| `REG-M-EXH2`, `REG-M-RET-MUD` | collar into the 8" exhaust trunk | moved 2" / 3.6" east | |
| `REG-M-RET3` | collar under `DU-M-ERV-R-STUDY` | onto its own radial's line, +2" | |
| `REG-M-RET-STUDY` | collar on a `W-M-CLN2` stud | over its riser, +4" | |
| `REG-S-HP-BED3` | 12x6 box on D-S-BED3's king | +2 3/4" north | |
| `REG-S-HP-SUITE` + `DU-S-HP-SUITE` | **the 10x8 branch ran through the cripple over D-S-SUITE** | both 7" north into the next cripple bay (7" off the door centre) | |
| `REG-S-HP-STAIR` | 12x6 box on a SF-S-DUCT ladder stud | 5 3/8" south | |
| `REG-S-HP-RET` | a ladder rung across the return face | `AO-S-HP1-RET` heads it off; grille +1", plenum +1/4" | |
| `REG-S-ERV-PLANT-EXH` | collar in W-S-C1's top plate | 1 3/4" lower, surface valve on the liner | |
| `REG-A-STUBATH-EXH` | collar under the two vents | 1" lower (36" → 35") | |
| `REG-A-HP-STUDY` / `-WEST` | damper box on FS-ATTIC joists | bay-centred, +1" / −1 7/8" | |
| `REG-M-XFER-MUD` | sleeve vs the doorbell conduit | conduit +1/2" | |
| A117 §307.2 at `REG-A-STUBATH-EXH` | 1 3/4" ≤ 4" | PASS | AM 100 overall H |
| motorised damper bodies, floor boot heights, FA8 plate | not published | **confirm on submittal** | §7, §3, §8 |

Not graded: a damper actuator inside a duct (no element), the canvas connector length, and
hanger space on the rectangular trunks (`mep.duct_soffit_occupancy` keeps its 2" gap).

## DuctStandard (decision #114, read 2026-11-05)

`plan/ducts.py` authors it; the engine derives every part off the resolved runs. This section is
the oracle for the hanger and seam arithmetic (`tests/test_duct_standard.py`).

**Class and gauge.** 1/2 in. w.g. Round to 14": 0.013" galvanized, 30 ga (IRC 2018 Table
M1601.1.1, Seattle SRC ch. 16 copy; IMC 2018's own text was not readable; Minnesota's old
amendment is repealed, 44 SR 1085). The 30/28/26 ga to thickness match is SMACNA App. A.1.

**Elbows.** No retail die-stamped elbow exists (Imperial, Speedi, Master Flow, H&C read: every
round 90 is a 4-piece adjustable or corrugated). With the adjustable's ASHRAE Fitting 3-2 loss
(4-piece: C 0.50 / 0.37 / 0.27 at r/D 0.75 / 1.0 / 1.5) R403.5 delivered 197.8 / 200.1 / 202.2
cfm against 203.0, so (owner, 2026-11-05) a 90 or 45 turn is a commercial **Linx E90/E45
die-stamped** elbow (li-hvac.com: "Die stamped", 3-12", "1.5-inch or 1.0-inch radius"; 1.0 D
taken), Fitting 3-1 C 0.22 at r/D 1.0, and any other turn is a **C.L. Ward adjustable 90** set
down (dimension A 4.75/6/7" read as centre-to-face: to the far side it would put the 8"
radius under D/2), C 0.37. The static budget takes C x the angle factor K per turn (Fitting
3-1/3-2: 0.45 at 30, 0.60 at 45, 1.00 at 90). The stamped laying length is unpublished; 1.5 D
stands in for `mep.fitting_pattern`, whose FAIL floor is two take-offs at R = D/2.

**Parts.** Plenum collars: Imperial GV0851 4" spin collar with damper (13: 12 collars, 1
take-off); the 8" trunk spigot is the plenum's own. Take-offs: GV0979 4" saddle on the 8"
level-2 extract trunk (9), GV0853 6" spin collar on the System 1 trunks (4). Boots: disc valves,
the stair box, the suite-bath box and neckless vents take the duct on their own collar; the
2-1/4x10 floor grilles take a Snappy P13-204 (or Imperial GV0602); 12x6 sidewalls on 6" a GV0671
end boot; REG-B-SUP2's 125 mm valve a GV0766 4-to-5 increaser (M4-120); every rectangular boot,
the 10x8 branch, the 6" tee and both reducers are shop-fabricated. Imperial prints SKUs and
gauges, no dimensions, so every part is drawn at its envelope.

**Port kits.** Broan B210E75RT manual pp. 10-11: "If using 8-in. ducts, install 6-in. to 8-in.
transitions on the ports, and secure using duct tape only. If rigid ducting is used, install a
12-in. section of flexible duct between the transition and the rigid ducting." "Do not use
screws to connect the ducts or transitions to the ports." Kit: GV0772 6-to-8 increaser (C 0.22,
the sudden 6/8 in. contraction bound 0.5(1 - 0.5625)) + 12" JP Lamborn MHP-45R8 (UL 181 Class 1,
R-8) on outdoor/exhaust; 12" flex on supply/return; a Duro Dyne MFN at the air handler. Only the
supply port is EXACT today, so only its flex is derived (1.2 Pa); the rest follows E2. **Open:**
the same manual says insulated ducts "must have the same diameter as the ports to ensure proper
drainage", which contradicts its own 8" advice: ask Broan.

**Supports.** SMACNA HVAC DCS 1995 + Add. 1 (law.resource.org): round to 10", 12' max, 1" x 22
ga strap (Table 4-2); rectangular to 30" half-perimeter, 10', 1" x 22 ga (Table 4-1; every trunk
here is P/2 <= 28"); flex 5' (S3.35); one within 2' of each elbow (S4.1; branches allow 4', 2' is
used for both). Per horizontal leg: one hanger 2' in from each end, then even gaps within the
spacing; a leg under 1' rides on its fittings; risers take none.
*Worked:* `DU-M-ERV-EXH-TRUNK` rises 12.8" (no hanger) then runs 331.6" = 27.63' level. End
hangers at 2' and 25.63': 23.63' between, ceil(23.63 / 12) = 2 gaps, **3 hangers**; the model
places 3. House: 139 hangers, 18 with no framing within 48" above or 16" beside (the attic
radials on the deck, the HP feed and one riser-exhaust leg): detail a saddle (`mep.duct_supports`).

**Seams.** Tape (Nashua 324A, 2.5" x 60 yd = 180') on the longitudinal seams: one per round
run, four per rectangular, over developed length. Mastic (Hardcast Versa-Grip 181, 11 oz, 130 LF
per cartridge at a 1/8" bead, the only bead rate published) on transverse joints: one girth per
5' stick, plus two per elbow and per billed part, each pi D or the perimeter.
*Worked:* `DU-M-ERV-EXH-TRUNK`, 8" (girth pi x 8/12 = 2.094'), 28.7 LF: tape 28.7'; joints
ceil(28.7/5) = 6 x 2.094 = 12.57', its 1 elbow 2 x 2.094 = 4.19', its 10 billed parts (9
saddles, 1 reducer) 20 x 2.094 = 41.89': 58.6' of mastic seam. House: 888.7' tape, 4.94 rolls,
**5**; 795.2' mastic, 6.12 cartridges, **7**. The take-off joint is counted at the main's girth,
which overstates it.

**Not read** (TODO): any laying length or boot height; a 4" collar damper with a locking
quadrant; a retail 1" x 22 ga strap (MARS 3/4" x 20 ga is the nearest); a metal-seam mastic
rate; IMC 2018 §603.10 / Table 603.4 verbatim; a 6x6x6 tee and an 8-to-4 reducer SKU; Linx
gauges and dimensions (login).

## Sources

- Vents-US AM series specification (hvacdirect.com/hvac/pdf/AM-Series-Specification.pdf) and
  AM 100 VRF listing, $19.00, read 2026-10-31.
- TROX LVS product data sheet PD-02/2022 (airfoil.com.au distributor copy) — LVS 100/125
  quick-sizing and dimension tables.
- RenewAire "Hoods and Dampers" (renewaire.com/wp-content/uploads/2025/09/Hoods-Dampers-.pdf):
  FA8-G 102406, FA8-P 102409, BD8 102401, pressure-drop charts.
- Fantech FML spec card (homelectrical.com FTH-45150Spec.pdf): FML 8, 9 x 9 plate.
- hvacquick.com TRUaire A220 series (A220VO 12X06 $79.80, 08X06 $68.60) and Shoemaker 1202-4.
- Hart & Cooley HVD, 531SA, 673 (43533) listings (firstsupply.com, ecmdi.com, howdybrewer.com).
- Filterbuy and Filter King 12x30x1 MERV 13 listings (actual 11 7/8 x 29 7/8 / 11.5 x 29.5).
- Reggio Registers 412-AH (fergusonhome.com); Snappy P13-204 (firstsupply.com).
- Tamarack RAPR (supplyhouse.com).
- EWC 4RSD / 6RSD, Honeywell ARD6TZ, Duro Dyne MFN listings (supplyhouse.com, bgshowrooms.com).
- Armacell AP Armaflex sheet data (cdn.bakerdist.com/armacell_aps_en_ss.pdf).
- Great Stuff Pro Window & Door (hemlockhardware.com); Nashua 324A (hdsupplysolutions.com).
- IRC 2018 Table M1601.1.1 (as reproduced in Seattle 2018 SRC ch. 16) — duct thickness.
- Best Access Doors Invisagrille; Lindab VGU frame (ahlsell.dk); Trox Z-LVS subframe — §12.
