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

## 2. ERV disc valves — `REG-T-ERV-VALVE-SUP` / `-EXH`, `-EXH-WALL` / `-SUP-WALL`, `-SUP-125-WALL`

Both basement supplies are sidewall valves since 2026-11-10 (the ceiling collar takes its
run from above on a stock 90, `resolve/terminal_drops.py`).

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
- **Wall valves** use the ceiling collar screwed to bay blocking. The clearance envelope
  retains 1 3/4" of projection. The 3D trim uses the
  [Vents-US AM 100 VRF drawing](https://images.thdstatic.com/catalog/pdfImages/01/01631271-ed42-4a7d-918a-0440ebcf5e0e.pdf)
  for the 2 15/16" center disc. The larger valve uses the
  [TROX LVS 125 drawing](https://www.trox.be/en/downloads/5664c8e9bd27129a/LVS_PD_2026_07_09_DE_en.pdf)
  for the profile. Installed relief at the center, re-read 2026-11-21 (the terminals read too
  flat in the viewer): the AM-VR table gives H 1 3/4" against H1 2 1/16", a 5/16" face; the
  LVS 125 table gives L1 9 mm, opened to its +5 mm setting. Each formed disc domes about 3/8"
  more (estimated off both drawings), so the meshes carry **1"** (AM 100) and **0.9"**
  (LVS 125), up from 5/8" and 0.55". The 1 3/4" fit envelope is unchanged. Both meshes show
  the rounded rim and the open annular gap around the center disc.
- **125 mm on the one 30 cfm terminal** (`REG-B-SUP2`): a 100 mm valve lost 17.1 Pa there and
  governed the machine; the 125 mm on a 4x5 increaser loses 8.2 Pa (budget §10.2).
- Not found: a stainless or aluminium valve sold retail (the plant room takes the
  powder-coated steel valve and a yearly clean), and supply-pattern published curves.

## 3. ERV floor extracts — `REG-T-ERV-EXH-FLOOR`

A disc valve cannot go in a floor. **Reggio 412-AH** 2 1/4x10 aluminium floor grille (~$30),
or equal Reggio G412 / Shoemaker AFP, on a **2 1/4x10x4 stamped 90° boot** (Snappy P13-204 or
equal). The [Reggio 412 drawing](https://s3.amazonaws.com/rb-production/rgo/spec-sheet-cast-scroll.pdf)
gives a 12 x 3 1/2" face and 3/16" cast plate. The visible face sits on the finished floor,
with simplified scroll openings based on the drawing. The boot's 5" height is still an
estimate to confirm on the submittal (§13). The long side follows the joist bay. The loss
allowance remains the derived K 5.

## 4. System 1 aluminium family

| type | basis of design | or equal | face | neck | price read |
|---|---|---|---|---|---|
| `REG-T-HP-SIDE-1206` (3) | TRUaire A220VO 12X06, double deflection, OBD | H&C HVD, Shoemaker 904-O | 13 3/4 x 7 3/4 | 12x6x2 11/16 (H&C HVD 3 7/16" overall less face) | $79.80 hvacquick |
| `REG-T-HP-SUITE-CHEVRON` (1) | Reggio Chevron 6x12, 3/16" laser-cut aluminium, Sun Gold + Reggio 814-BL louver | any laser-cut 6x12 meeting the free area | 14 x 8 overall | 12x6x2 11/16 (the 814-BL's 2 5/16" fits the 6" box) | not published; estimate |
| `REG-T-HP-STAIR-SIDE` (1) | A220VO 12X06 + TH-HP-STAIR-BOX-01 | | 13 3/4 x 7 3/4 | 12x6x4, centred 4in back collar | allowance |
| `REG-T-HP-STUDY-SIDE` (1) | TRUaire A220VO 08X06 | H&C HVD 8x6 | 9 3/4 x 7 3/4 | 8x6x2 11/16 | $68.60 |
| `REG-T-HP-FLOOR-0612` (3) | H&C 531SA 6x12, multi-shutter | Reggio, Shoemaker 600 | 13 3/8 x 7 3/8 (est.) | 12x6x2 (est.; TRUaire 150 is 2") | not read |
| `REG-T-HP-PLANT-SIDE` (1) | A220V 12X06, no OBD + 6in 24 VAC RH damper (§7) | | 13 3/4 x 7 3/4 | 12x6x2 11/16 on the stock 6x12x6 end boot; damper behind the grille | allowance |

The sidewall faces are centred on the duct axis (faces grew 6" → 7 3/4", so every mount
elevation dropped 7/8"). Oak-match flush in RM-A-STUDY is a note only. Caution read on
Pace Supply: one listing calls the 220VO steel; order the **aluminium** A220 line.

**RM-S-SUITE's Chevron (owner, 2026-11-19).** The suite's supply (`REG-S-HP-SUITE`, 100 cfm)
is a Reggio Chevron in Sun Gold, to match the room's Reggio steel Decora plates; BED1-3, the
stair and Study 2 keep the adjustable A220VO, and returns and transfers stay fixed bar.
- Made to order (4-6 wk), 8 x 14" overall on a 6x12 duct. A fixed face throws straight with no
  aim; a jet this near the ceiling stays attached to it.
- Price basis: no price is published at this size. Reggio's cut-steel 6x12 lines read $69.95
  (Royal) to $92.95 (Basketweave), so the grille is carried at $70-110, plus the 814-BL louver
  ($35.95, Ferguson): key-set at commissioning, 2 5/16" deep, inside the straight 12x6x6 box.
- **Open submittal item: free area.** None is published; the suite needs >= 29 in2 to hold
  500 fpm at 100 cfm.
- Quote: Reggio, 800-880-3090 (code ONCEAYEAR26 until 2026-11-29).

The stair supply has an [explicit 4in branch and named register box](stair_supply_connection.md).

## 5. The return filter grille — `REG-T-HP-RET-FILTER`

The hall grille is a 24x12 hinged filter-back (H&C 673 class, or equal TRUaire 190RF /
Shoemaker 620FG) taking a **stock 12x24x1 MERV 13** (owner, 2026-11-12). The custom 12x28x1
this section used to carry is retired. The rung that crossed the hole is headed off
(`AO-S-HP1-RET`).

**Why 12x24 and not 14x25x1.** 14x25x1 is the largest stock size that would otherwise fit
`SF-S-DUCT`, and was tried first (187 fpm, ~0.20" clean). It cannot stand in the hole: the
`FS-ATTIC` joists leave 13 11/16" clear in the y 352-368 bay and the soffit's north end takes
2 1/8" of it, so the neck has **12.5" in y**, and `mep.terminal_neck_fit` refused a 14" neck
(0.91" into the joist, 0.62" into `soffit-end-n`). The short side stays at 12".

**Design airflow (2026-11-12).** `EQ-S-HP1-AH` is 760 cfm at 0.5" ESP, speed 3 (Gree FXU24
submittal); the plan runs 750. The hall grille carries 750 - 100 (ERV) - 80 (suite) - 80 (BED3)
- 35 (east room, `REG-A-HP-EAST-RET`) = **455 cfm** (490 before the east return; 570 before
BED3's, 2026-11-11).

**The filter.** Zephyr VGP MERV 13 data sheet (`ZEP25252-VGP-MERV-13-Product-Spec-Sheet-Updates-V2.pdf`,
zephyrfiltration.com, 2025): 1" depth at **300 fpm** is 0.32" w.g. initial and **1.0" w.g.
final**; 12x24x1 is stocked, actual 11.38 x 23.38, capacity 600 cfm (= 300 fpm on the 2.0 sf
nominal face).

| | 12x24x1 at 455 cfm |
|---|---|
| nominal face | 2.0 sf |
| face velocity | 228 fpm (246 on the actual 1.85 sf); Manual D 300 |
| initial drop, scaled linearly from 0.32" at 300 fpm | ~0.24" |
| final drop (published) | 1.0" (~0.76" scaled) |

The 0.24" is scaled from the sheet's one published point, not read from it, and the sheet
publishes no "recommended change" drop.

**System 1 static budget (2026-11-12), at 455 cfm through the hall grille, against 0.5" ESP:**

| term | w.g. |
|---|---|
| hall grille face | 0.02" |
| return duct, filter box and plenum (`DU-S-HP-RET`, `EQ-S-ERV-MIX`) | 0.06" |
| supply side (`DU-S-HP-SUP`, trunk, boots, registers) | 0.15" |
| filter, clean | 0.24" |
| **total, clean** | **0.47" vs 0.5"** |

The coil is **internal** to the unit's ESP rating, so the budget carries no coil term;
that waits on the Gree submittal's rating conditions (open). The loss terms are hand
estimates, not measured.

* **Change out at a 0.27" filter drop.** That is 0.5" less the 0.23" of everything else; a
  clean filter leaves 0.03". Read it from a manometer across the
  filter at commissioning and at each change, not from the calendar. At 0.76" scaled final
  the filter is far past it, so the limit is the change-out drop, not the sheet's final.
* **The reserve is the speed-4 tap.** The unit's fan table (Gree submittal) gives the
  delivered cfm at each tap and ESP; the number is **to be read from that table**, not assumed
  here. It is what the system leans on once the filter loads past 0.27".
* **The IOM (§2.5) shows a possible internal 16x20x1 filter slot** at the cabinet's return
  opening. If the delivered cabinet has one populated it is a **second** filter in series
  and adds its own drop (~0.36" at 750 cfm: 337 fpm on its 2.22 sf, scaled from the same sheet): leave it empty, or the budget
  above is wrong. Confirm on the delivered unit.

**The box takes a side inlet (2026-11-21).** `REG-T-HP-RET-FILTER`'s neck is the 1" rack plus
the shop filter box, 25 1/8" from the soffit face to `DU-S-HP-RET`'s top in the FS-ATTIC bay.
The 12x10 run comes west along the bay and enters the box's east face, top-aligned
(`TerminalNeckInlet`, centre 20 1/8" up, 1/2" north of the box centre so the run stays on the
bay's line); the box's collar bills as `boot-12x10-12x10`. Until then the box was a 15 1/8"
neck under a terminal drop, because a drop needs the arriving run to be the neck's section and
a 24x12 run does not fit the 14 1/4" bay. The return path's turns are unchanged: the riser
elbow at the mixing box and the run's entry into the box (a drop before, a side entry now),
so the 0.06" term stands.

**RM-S-SUITE's return — `REG-T-HP-RET-FILTER-1212` (2026-11-09).** A 12x12 hinged
filter-back grille (H&C 673 class, or equal TRUaire 190RF / Shoemaker 620FG) on a
shop-fabricated 6x4 boot with a locking balancing damper. It lands in the plenum behind the
hall filter, so it carries its own: **12x12x1 MERV 13, a stocked size**. 144 in² at 80 cfm is
80 fpm. Face estimated as the 24x12's (+2 5/8"). Balance and commissioning:
`notes/system1_return_path.md`.

**RM-A-EAST-UNFIN's return — `REG-T-HP-RET-FILTER-1212-WALL` (2026-11-12).** The same stock
12x12x1 MERV 13 and 12x12 grille, turned to a wall face (service face front, no neck: the
plenum is the host), 14" AFF on the south face of `EQ-S-ERV-MIX`, 35 fpm at 35 cfm. A locked
balancing damper in the stub (`DU-A-HP1-EAST-RET`, `boot-12x12-none`) holds 35 cfm: the
plenum's returns are in parallel, so an open grille would pull far more than its share from
the room. `integrity.wall_mount_on_face` cannot host a wall register on equipment, so that
check is suppressed for this one tag (`preferences.toml`). Balance: `notes/system1_return_path.md`.

## 6. The mudroom transfer — `REG-T-TRANSFER-MUD-1210`

One 12x10 aluminium fixed-bar return grille (TRUaire A170 class, or equal H&C A650)
on the stair face of `W-M-STRW`. `AO-M-XFER-MUD` cuts only the painted 1/2in MDO
back panel; the coat nook behind is open. No sleeve and no second grille. The existing
location and nominal free-area basis remain. `CD-M-DATA-DOORBELL` stays at its shifted location.

`REG-T-TRANSFER-0606` (2026-11-03) is D-S-BATH1's offset pair: one 6x6 grille of the same
family on each face of `W-S-BD-N`'s lined west bay. The steel 170 6x6 lists 0.17 sf (~24 in^2)
effective; the aluminium A170's figure is unpublished. 20 cfm at 3 Pa needs 10.8 in^2.

## 7. Dampers, balancing and connectors

| item | basis of design | or equal | note |
|---|---|---|---|
| plant extract, 4" 24 VAC | EWC 4RSD spring-return (~$177) | Duro Dyne NSPRD024-4, Zonefirst RDSC | **at `DU-M-ERV-R-PLANT`'s start collar on the level-2 plenum in RM-M-MECH**, not behind the valve: serviced with no access panel in the humid liner; RH sensor local |
| plant HP supply, 6" round, 24 VAC | EWC 6RSD (family of the 4RSD; **not read**) | Duro Dyne NSPRD024-6, Zonefirst RDSC | in the register box's collar behind the A220V, reached by pulling the grille; no hatch in the liner ([connection](plant_supply_connection.md)) |
| 4"/6" branch balancing | Imperial GV0851 / GV0853 spin collar with damper, 28 ga (DuctStandard) | M&M 504MSD4 (locking handle) | LSCD6 was a flanged starting collar, listed discontinued. **The damper must lock** (Minn. R. 1346.0603 subp. 10 → IMC 603.18.3): the GV085x submittal or a sample must show a locking handle, otherwise buy the M&M 504MSD4 |
| 4"/6" in-line balancing | retail round volume damper, locking quadrant, galvanized (`PROD-AIR-DAMPER-4-MANUAL` / `-6-MANUAL`, DuctStandard `damper` rows); SKU at order | any locking-quadrant round damper | 4": `DU-B-ERV-R-BENCH`. 6": `DU-S-ERV-HP-FEED`'s north deck leg, set to 115 cfm into `EQ-S-ERV-MIX` with the AH running, then locked. Charged fully open at C 0.34 ([static §10.29](erv_static_budget.md)). No backdraft damper on that feed (owner, 2026-11-17) |
| air-handler connector | Duro Dyne MFN metal-fabric-metal | | NFPA 90A / 701 fabric; 3" fabric (suggested, not a code number) |
| mastic / tape | Hardcast Versa-Grip 181 (UL 181A-M/B-M) | Nashua 324A tape (UL 181A-P/B-FX), 3M 3340 | Iron-Grip 601 is B-M only; 3M 3381 is not UL 181 |

Both plant dampers (the 4" extract, the 6" supply) still need their body and actuator dimensions confirmed (§13).

## 8. Hoods — `EQ-T-ERV-HOOD-8` / `-8-EXH`

RenewAire **FA8-P** (102409, paintable galvanneal, 1/4" metal screen, no damper) on both
legs, **no backdraft damper on either** (2026-11-05, C4 E3): Broan's manual §2.4 forbids one on
the discharge ("it can freeze in winter") and the ERV's own motorized port dampers close the
legs; the BD8 (102401) is dropped, its 8 Pa with it. Or equal: Fantech FML8 (white powder-coat aluminium, 9 x 9 plate) with its bug
screen swapped for 1/4" mesh — no curve published. 1/4" screen and not insect mesh, so frost
does not blind it. Published loss (chart end points, Q² scaled): **intake 23.3 Pa, discharge
14.8 Pa at 210 cfm** (budget §10.1, §10.10). FA8 plate and projection are unpublished: the model keeps
the 12 x 12 x 12 envelope, which is larger than either hood, so every clearance it passed
still holds. The `renewaire-fa8-wall-hood` symbol follows the sloping folded hood in
RenewAire's product photo: mounting flange, triangular cheeks, rain cover and an open
downward-facing 1/4" wire screen, with no damper. Its 10.5" shell width, 7.5" projection,
12" plate and sheet thickness are visual estimates, pending a dimensioned submittal;
they do not replace the clearance envelope. The existing 8" duct models the wall neck.
Painted to match the north-face cladding's grey model colour. **10" option**: budget §10.4.

## 9. Outdoor legs: insulation and the wall line

- **Insulation:** one 1" layer of closed-cell elastomeric sheet, **AP Armaflex** (or equal
  K-Flex Insul-Sheet), Armaflex 520 adhesive, **R-4.2**, its own vapour retarder, over the
  whole of both legs (2026-11-11, budget §10.4a; was two layers, R-8.4). 10" OD on an 8" duct.
  Code asks R-3.3 and a vapour retarder (`notes/duct_insulation.md`); the surface holds 58.2 F
  against a 50.5 F dew point at 70 F / 50% RH. Duct joints mastic-sealed first. **Kept over
  FSK fibreglass wrap** (owner, 2026-10-31; the option is in `plans/cost-options.md` §1).
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
  **30 ga**, from the DuctStandard (the library rows no longer name a gauge): IMC 2018 Table
  603.4 (Minn. R. 1346.0050) asks 0.013" for round to 14" at 1/2" w.g.
- **Trunks and risers**: 6"/8" galvanized; every seam UL 181B-M mastic or 181B-FX foil tape
  (IMC 2018 603.9; 181A is the fibrous-glass class). House-air ducts bare; OA/EA per §9.
- **System 1 rectangular trunks** (`DU-S-HP-SUP` 18x8, `-RET` 10x18,
  `-SOUTH` 10x6; `-SUITE` is a 6" round since 2026-11-16): `material="galvanized"` now, matched to the gauge band rows
  `DUCT-T-GALV-RECT-*` (IMC 2018 Table 603.4, 1/2" w.g. column): **26 ga** for the 18"
  sides, **30 ga** for the 10" ones, printed on the duct schedule. Shop-fabricated,
  mastic-sealed, no liner (cleanability), canvas connectors at the air handler.

## 12. Trimless — declined (owner, 2026-10-31)

**Decision: no trimless terminals. Flanged everywhere, as modelled.** The study below is
kept as the record of what was weighed.

| candidate | product | installed $ vs standard (est.) | sequencing | access / cleaning | static / sound |
|---|---|---|---|---|---|
| `REG-M-SUP1` (living, ERV 4" supply) | disc valve with plaster-in frame (Lindab VGU + Airy, Trox Z-LVS subframe) | +$40-120 | frame in the 104 mm hole before taping; the duct stub must land exactly | disc twists out | same valve, no penalty |
| `REG-M-RET5` (living, ERV 4" extract) | same | +$40-120 | same | same | none |
| `REG-M-XFER-MUD` (12x10 wall) | mud-in flush cover (Invisagrille-type, magnetic face) | +$60-200 plus finishing | 12x10 cut in MDO before painting | face lifts off | free-area loss on a passive transfer: unpublished, the riskiest one |
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
| `REG-M-XFER-MUD` | former sleeve vs the doorbell conduit (sleeve removed) | conduit +1/2" | |
| A117 §307.2 at `REG-A-STUBATH-EXH` | 1 3/4" ≤ 4" | PASS | AM 100 overall H |
| motorised damper bodies, floor boot heights, FA8 plate | not published | **confirm on submittal** | §7, §3, §8 |

Not graded: a damper actuator inside a duct (no element), the canvas connector length, and
hanger space on the rectangular trunks (`mep.duct_soffit_occupancy` keeps its 2" gap).

## DuctStandard (decision #114, read 2026-11-05)

`plan/ducts.py` authors it; the engine derives every part off the resolved runs. This section is
the oracle for the hanger and seam arithmetic (`tests/test_duct_standard.py`).

**Class and gauge** (re-read 2026-11-07). 1/2 in. w.g. Round to 14": 0.013" galvanized, 30 ga.
The law is **IMC 2018 Table 603.4**, adopted by Minn. R. 1346.0050 ("Chapters 2 to 15 of the
2018 edition of the International Mechanical Code"); Minn. R. 1309.0010 subp. 3.C deletes the
IRC's mechanical chapters, so IRC Table M1601.1.1 is not law here (same values). **Minn. R.
1346.0603 is not wholly repealed**: subps. 1-7 and 9 are (34 SR 537; 44 SR 1085), subp. 8
(603.8.4) and **subp. 10** stand. Subp. 10 adds IMC 603.18.3: "Volume dampers shall be adjusted
to the required airflow of the system and locked in place. In finished or inaccessible
locations, a friction-type register box may be used." (revisor.mn.gov). The 30/28/26 ga to
thickness match is SMACNA App. A.1.

*Transcribed from UpCodes MN mirror (up.codes/viewer/minnesota/imc-2018/chapter/6/duct-systems);
proofread against codes.iccsafe.org before printing* (ICC returned 403 on 2026-11-07):
- **603.4** "Metallic ducts shall be constructed as specified in the SMACNA HVAC Duct
  Construction Standards—Metal and Flexible. Exception: Ducts installed within single dwelling
  units shall have a minimum thickness as specified in Table 603.4."
- **Table 603.4** (single dwelling units, min. thickness in.), round, 1/2" w.g. galv / 1" w.g.
  galv: < 12 0.013 / 0.013; 12-14 0.013 / 0.016; 15-17 0.016 / 0.019; 18 0.016 / 0.024; 19-20
  0.019 / 0.024. Rectangular, 1/2" w.g. galv: <= 8 0.013; 9-10 0.013; 11-12 0.016; 13-16 0.019;
  17-18 0.019; 19-20 0.024. Note a: over 20" or over 1" w.g., SMACNA.
- **603.10** "Ducts shall be supported in accordance with SMACNA HVAC Duct Construction
  Standards—Metal and Flexible. Flexible and other factory-made ducts shall be supported in
  accordance with the manufacturer's instructions."

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

**Parts.** Plenum collars: Imperial GV0851 4" spin collar with damper, **28 ga** (Imperial
PP1142 Aug 2026 p.17; the old 24 ga was wrong) (13: 12 collars, 1 take-off). The catalog says
only "(With Damper)": under 603.18.3 the submittal or a sample must show a locking handle, or
the collar is an **M&M 504MSD4** (28 ga, 5.50" overall, "damper with steel hardware & locking
handle", mmmfg.com 504MSD submittal) (owner, 2026-11-07); the 8" trunk spigot is the plenum's own. Take-offs: GV0979 4" saddle on the 8"
level-2 extract trunk (9), GV0853 6" spin collar on the System 1 trunks (4). Boots: disc valves,
the stair box, the three valve stack boxes (suite bath, study closet, student bath; notes/suitebath_extract.md) and neckless vents take the duct on their own collar; the
2-1/4x10 floor grilles take a Snappy P13-204 90 (collar on the long side; or Imperial GV0602) or,
fed along the long side, a Snappy P17C-204 center end boot; a 6" run on a 12x6 neck's normal
takes a Master Flow RB12X6X6 straight register box (30 ga), and one arriving across it the GV0671
end boot (2026-11-16, matched by entry); REG-B-SUP2's 125 mm valve a GV0766 4-to-5 increaser (M4-120). The 6x6x6 tee is an
**Imperial GV0893** full-flow tee, 30 ga (p.19), the GV0890's sibling. The 4x4x4 tee where
`DU-M-ERV-R-RET3` leaves `DU-M-ERV-R-LAUNDRY` is a **Master Flow (GAF) T4X4X4** (Home Depot
100131692, about $16; owner, 2026-11-10): gauge and dimensions unpublished, drawn at its
estimated envelope. Imperial makes no 8-to-4
reducer, so it is a stacked **GV0821 8-to-6 (28 ga) + GV0811 6-to-4 (30 ga)** (p.15), one
billed set (`PROD-DUCT-REDUCER-8-4`), drawn 12.25" long: a stand-in off M&M's 400 round reducer
(1.75" collar + 2.50-3.50" taper + 1.75" collar, mmmfg.com 400 submittal, no per-size table)
at its 7.0" maximum, twice, less one engaged 1.75" collar. Every rectangular boot and the
rectangular reducer stay shop-fabricated. Imperial prints SKUs and gauges, no
dimensions, so every part is drawn at its envelope (owner, 2026-11-07, "shop-made duct is a
last resort").

**Port kits.** Broan B210E75RT manual pp. 10-11: "If using 8-in. ducts, install 6-in. to 8-in.
transitions on the ports, and secure using duct tape only. If rigid ducting is used, install a
12-in. section of flexible duct between the transition and the rigid ducting." "Do not use
screws to connect the ducts or transitions to the ports." Kit: GV0772 6-to-8 increaser (C 0.22,
the sudden 6/8 in. contraction bound 0.5(1 - 0.5625)) + 12" JP Lamborn MHP-45R8 (UL 181 Class 1,
R-8) on outdoor/exhaust; 12" flex on supply/return; a Duro Dyne MFN at the air handler. All four
ports are EXACT since 2026-11-11 (`erv_static_budget.md` §10.22): OA/EA take the increaser and a
straight flex under an adjustable 90 (3.9 + 0.3 Pa); SUP/RET's flex bends at R = 1D (22.2 Pa). **Open
(owner, 2026-11-07: keep the kit as modelled pending Broan's answer):** p.11 says insulated
ducts "must have the same diameter as the ports to ensure proper drainage of water that may
accumulate in ducts"; its figures are side-port cases and the RT is top-port, so a vertical
increaser may simply drain back into the port, but only Broan can say so. Question to send:
*"B210E75RT (top ports): p.10 says to use 6-to-8 transitions for 8" ducts; p.11 says insulated
ducts must be the same diameter as the ports for drainage. On a top-port unit with a vertical
6->8 increaser and 12" of insulated 8" flex rising on R >= 3", is that acceptable, or must the
insulated OA/EA legs stay 6" up to the transition?"* Keeping 6" flex off the ports would cost
static on the 0.4" budget.

**Supports.** SMACNA HVAC DCS 1995 + Add. 1 (law.resource.org): round to 10", 12' max, 1" x 22
ga strap (Table 4-2); rectangular to 30" half-perimeter, 10', 1" x 22 ga (Table 4-1; every trunk
here is P/2 <= 28"); one within 2' of each elbow (S4.1; branches allow 4', 2' is used for both).
Flex follows its maker (IMC 603.10): JP Lamborn Installation Guidelines Rev. 11-16, "supported
at 4' maximum intervals by means of min 1.5" wide straps" (SMACNA S3.35's 5' is the outer
bound); today only the 12" port leads are flex, between two support joints. The strap is
**DiversiTech 710-005 (DS-221)**, 1" x 100' galvanized, 22 ga (TDS DOC134521, read off a
reseller CDN copy); the Home Depot 710-001 is 26 ga and is not it. Per horizontal leg: one
hanger 2' in from each end, then even gaps within the spacing; a leg under 1' rides on its
fittings; risers take none.
*With no framing in reach* (owner, 2026-11-07) the station takes a **saddle**: the same 1" x 22
ga band over the duct, screwed to the deck each side. This is **house practice, not a SMACNA
detail**: SMACNA has no figure for a duct borne from below (Fig. 4-4 hangs a band from above;
the Table 4-2 note sends saddles to the Round Industrial standard, not read), and S4.1 only
asks supports "installed as required to maintain alignment". It grades PASS only where the duct
bears on a floor deck, its invert within 1/4" of the deck top, with both band feet (half the
duct plus the band thickness either side) on the deck and off its voids. A slab is never a
saddle host (left UNKNOWN on purpose). Failing that, a **bracket** to a parallel wall within 2"
whose length the station faces (Fig. 4-8, "locate ducts against wall or maximum of 2" away").
*Worked (the 8" round trunk, retired 2026-11-08 for the flat 8x4):* `DU-M-ERV-EXH-TRUNK` rises 12.8" (no hanger) then runs 331.6" = 27.63' level. End
hangers at 2' and 25.63': 23.63' between, ceil(23.63 / 12) = 2 gaps, **3 hangers**; the model
places 3. House (2026-11-07): 136 stations, 118 hung from framing and 18 saddles on FS-ATTIC's
deck (the four attic radials' deck legs, two on the HP feed, one on the riser-exhaust leg; 15 at
4", 3 at 6"); no wall bracket qualifies, the attic chase being open deck under the rake. The 4"
radials' deck legs are authored at +2 3/4" (`_ATTIC_DECK_Z`, the 3/4" deck top plus the radius)
so they bear; the 6" ducts' +4" leaves them 1/4" up, at the tolerance.

**Seams.** Tape (Nashua 324A, 2.5" x 60 yd = 180') on the longitudinal seams: one per round
run, four per rectangular, over developed length. Mastic (Hardcast Versa-Grip 181, **billed by the
gallon**, 304138 = case of (4) 1-gal pails, white) on transverse joints at the TDS's UL 181B-M
pail rate, "20- to 30-mil wet film thickness at 3" wide", coverage "up to 320 lin. ft. at 3"
width, 20-mil thickness" (Carlisle TDS 0124, read 2026-11-07). Billed at the 30 mil end, not the
best case: 320 x 20/30 = **213 LF/gal**. The cartridge's 130 LF at a 1/8" bead is not a metal-seam rate (the B-M cartridge
rate is "bead that completely covers joint", no LF). One girth per 5' stick, plus two per elbow
and per billed part, each pi D or the perimeter.
*Worked (the 8" round trunk, retired 2026-11-08 for the flat 8x4):* `DU-M-ERV-EXH-TRUNK`, 8" (girth pi x 8/12 = 2.094'), 28.7 LF: tape 28.7'; joints
ceil(28.7/5) = 6 x 2.094 = 12.57', its 1 elbow 2 x 2.094 = 4.19', its 10 billed parts (9
saddles, 1 reducer) 20 x 2.094 = 41.89': 58.6' of mastic seam. House (2026-11-07): 888.0' tape,
4.93 rolls, **5**; 788.8' mastic, 788.8 / 213 = 3.70 gal, **4 gal** (one case of 4). The take-off
joint is counted at the main's girth, which overstates it.

**Not read** (TODO): any Imperial laying length or boot height (the 2026 catalog prints none;
Imperial US, Alton IL, for a submittal); whether the GV0851 damper locks (sample or submittal);
the Snappy P13-204 height; a published B-M LF rate per cartridge; ICC's own rendering of IMC
2018 ch. 6 (403); SMACNA Round Industrial's saddle detail; a retail 1-1/2" flex strap; Linx
gauges and dimensions (login). Answer from Broan on the port-diameter question above.

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
- IMC 2018 §603.4 / Table 603.4 / §603.10 / §603.18, UpCodes Minnesota mirror
  (up.codes/viewer/minnesota/imc-2018/chapter/6/duct-systems), read 2026-11-07; Minn. R.
  1346.0050, 1346.0603, 1309.0010 (revisor.mn.gov), read 2026-11-07 — duct thickness, supports,
  locked dampers. (IRC 2018 Table M1601.1.1, Seattle SRC ch. 16, the earlier read: same values.)
- Imperial PP1142 Galvanized Duct, Pipe & Fittings, Aug 2026 (imperialgroup.s3.amazonaws.com/
  site/PP1142-Galvanized-Catalogue-En-2026-August-2026-08-18-03.45-PM.pdf), pp. 15, 17, 19.
- M&M Mfg. submittals 400 (round reducer) and 504MSD (spin collar with locking damper),
  mmmfg.com, read 2026-11-07.
- DiversiTech TDS DOC134521, 710-004/-005 strapping (cdn.shopify.com reseller copy), read 2026-11-07.
- Carlisle Hardcast Versa-Grip 181 TDS 0124 (dam.carlisle.com), read 2026-11-07.
- JP Lamborn Installation Guidelines Rev. 11-16 (sylvane.com copy), read 2026-11-07 — flex supports.
- SMACNA HVAC DCS 1995 (law.resource.org) S4.1, Figs. 4-4 / 4-8, Table 4-2.
- Broan B210E75RT installation guide 1107081WEB rev. E (broan-nutone.com), pp. 10-11.
- Best Access Doors Invisagrille; Lindab VGU frame (ahlsell.dk); Trox Z-LVS subframe — §12.

**Ventilator alternates (2026-11-11).** The Broan B210E75RT stays the designated unit. Ranked by
15-yr cost basis: Fantech ATMO 300E-EC ~$4.5k, Lifebreath 267 MAX ~$5.4k, RenewAire EV Premium+ L
~$5.5k, Broan ~$6.5k, Zehnder Q ~$8.2k+. The Lifebreath 267 MAX (mirrored ports) is the named
alternate: recirculation defrost and auto-balance, like the Broan. Fantech and RenewAire L were
not chosen (exhaust-only defrost or none, no constant airflow); Aldes InspirAIR and Zehnder Q are
named but out on cost; Panasonic is out (130 cfm cap below 23 F). Twin units on one hood pair are
an unmeasured fallback. The Broan's RS (side-port) sibling was screened: the same handedness, plus
a 90 on every horizontal lead (§10.22).
