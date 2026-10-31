---
title: "Backup Power — the ESS microgrid"
applied_to:
  - room: RM-B-ESS
  - equipment: EQ-B-ESS-BATT
  - equipment: EQ-B-ESS-INV
  - device: ED-B-BACKUP-PANEL
  - device: ED-B-BACKUP-ENCL
  - door: D-B-ESS
  - fixture: FX-B-UTIL-SINK
tags:
  - electrical
  - energy-storage
  - solar
  - backup
  - fire-separation
source:
  - plan/circuits.py
  - plan/electrical.py
  - plan/mep_hvac.py
  - plan/storeys/basement.py
  - plan/door_types.py
  - plan/mep_lavatories.py
  - plan/mep_drainage.py
  - params/solar.py
---

# Notes

The backup system is an EG4 12kPV hybrid inverter, one 14.3 kWh EG4 WallMount Indoor
battery in its own Type X closet, the rooftop array landing on the inverter's MPPTs, and a
subpanel (`ED-B-BACKUP-PANEL`) on the inverter's load port that stays live when the grid
does not. The battery may be deferred; everything below is written so that adding it later,
or a different battery, or a car, is a swap and not a redesign.

## 1. The inverter decision (owner, 2026-10-30)

**Keep the EG4 12kPV.** It is a grid-tied hybrid with UL 1741 SA/SB, so it keeps net
metering, and it runs with or without a battery. Rejected:

| Alternative | Why not |
|---|---|
| Off-grid all-in-one with AC input | Loses ~$250-500/yr of net metering and needs a ~20 kWh battery on day one |
| Victron | No UL 1741 SB; its 2x120 V model cannot make 240 V off-grid |
| Luxpower | The same Lux OEM as EG4, with thinner US support |
| MidNite | ~85 W idle and no third-party UL 9540 listing |
| Sol-Ark 15K | +$2.3k for nothing this house uses |

Ratings on `EQ-T-EG4-12KPV`, from the spec sheet v1.0.9
([EG4](https://eg4electronics.com/wp-content/uploads/2024/05/EG4%C2%AE-12kPV-Spec-Sheet.pdf),
read 2026-10-31): 8,000 W continuous AC (the "12k" is PV *input*), 16 kW for 0.5 s surge,
**idle <55 W** ("standby mode"), **94% maximum battery-to-grid efficiency**, 96.4% CEC.
Both of the last two are authored as `inverter_idle_w=55`, `inverter_efficiency=0.94` and
both flatter a ~400 W outage load: 94% is the peak of the curve, and an islanded inverter
may idle above its standby figure. Meter both at commissioning.

The sheet also gives a 4,000 W maximum per line (leg). Every always-on circuit is 120 V and
together they connect 3,025 VA, so they fit one leg even unbalanced; balance them anyway.

## 2. The listing reality, and the battery spec

The Pylon CAN protocol lets a third-party battery *talk* to the 12kPV. Talking is not the
code question. IRC R327.2 (and NEC 706.5) want a **UL 9540** listing, and UL 9540 lists a
*system*: inverter + battery model + count. EG4's product page lists the WallMount Indoor
under UL 9540 with the 12kPV, 18kPV and FlexBOSS21
([EG4](https://eg4electronics.com/categories/batteries/eg4-wallmount-indoor-280ah-lithium-battery/));
third-party packs (Pylon, Pytes, Fortress) are "ongoing". The decoupling route is the UL
9540 3rd edition "DC ESS" battery-only listing (effective 2025-08-29). It is unconfirmed
for the WallMount, and no AHJ has a position on it yet.

So the **battery spec** (on `EQ-T-ESS-BATT`'s comment) for any first, second or
replacement pack is:

1. on EG4's current UL 9540 list for the 12kPV, **or** a UL 9540 3rd-ed. DC ESS listing the
   AHJ (St Paul DSI) accepts in writing;
2. closed-loop comms (Lux or Pylon CAN), never open-loop voltage charging;
3. a BMS with its own contactor;
4. a UL 9540A test report.

The WallMount Indoor's sheet: 36.4 x 18.1 x 9.6 in (H x W x D), **282 lb** (the model had
24 x 10 and "300 lb"), UL 1973 + UL 9540A, RS485 closed loop. The type now carries the real
18.1 x 9.6 x 36.4 body; the owner's 3'-0" separation zone is still drawn off the old 24 x 10
envelope, so the cabinet gets 39" at its sides and 36" front and back.

## 3. The closet: fire containment first

The owners rank containment first. The research behind the build:

- One 280 Ah LFP cell vents 165-221 L of gas, 36-44% of it hydrogen. The ~3 m³ closet
  sits near the lower flammable limit from **one** cell. A sealed box concentrates that gas,
  which is why there is no steel cabinet and no NEMA 3R box (3R carries no fire rating).
- Water is the only agent shown to stop cell-to-cell spread. Hence the sink outside the
  door (below), with a hose.

**The enclosure is UL Design U305**: wood studs, one layer of 5/8" Type X on each face
(1-hour; the build USG SA924 cites for `INT_2X4_PARTITION`). Steel studs and a fire-retardant
spray were both declined (the TODO's "wood studs vs spray" question is closed): the tested
build is also the cheap one.

| Side | Element | Build |
|---|---|---|
| North | `W-B-N3` | 8" cast concrete (mass; the battery hangs on it) |
| East | `W-B-STR` | 2x6 with a 5/8" Type X leaf on the closet face |
| South | `W-B-ESS-S` | `INT_2X4_PARTITION`, both gwb layers swapped to `gwb-x` |
| West | `W-B-ESS-W` | `INT_2X6_BRG`, both gwb layers to `gwb-x`, `NONBEARING` |
| Lid | `RM-B-ESS.ceiling_lining` | two 5/8" Type X on 3 1/2" furring, face 7'-8 13/16" |

No new tag: the library partitions with `layer_materials` (decision #72). `W-B-ESS-W` is a
2x6 because `PR-B-KITCH-DRAIN` crosses it at y=35'-0", 95"-97 1/2" AFF, and a 2 3/8" bore
is 68% of a 3 1/2" stud against R602.6's 60%; in a 2x6 it is 43%. The two steel assemblies
left the house catalog; the library keeps them.

**The lid is furred down** so the PVC kitchen drain runs above it, outside the box, rather
than as plastic pipe inside it. `PA-B-ESS-SEAL-W` and `-E` firestop that drain where it
passes `W-B-ESS-W` and `W-B-STR` (intumescent sealant, Hilti FS-ONE MAX or equal). The
conduits that enter the closet — the battery's DC run through `W-B-ESS-W` and
`CD-B-GARAGE`, which crosses the closet under the lid — get the same sealant at each wall;
a `ConduitRun` takes no accessory, so those two are prose, not BOM rows.

`advisory.ess_enclosure` grades all of it off the **resolved** wall layers (so the swap
counts) and the room's resolved ceiling; take the swap off `W-B-ESS-S`, or the lid off the
room, and it fails (`test_energy_storage.py`).

**The door**, `DT-INT-STEEL24-LITE`: a cheap 24x80 hollow-metal leaf in a knock-down steel
frame, a small tempered vision lite (R308.4.1), spring hinges (`self_closing`), and no fire
rating — the owner declined a rated door. 24" steel is a special order (stock KD frames
start at 32"): a door distributor item. It swings into the closet and sits 18 7/8" off the
SW corner, on the wood stud module. The engine has no partial-lite leaf, so the viewer draws
it all glass.

**Detection**: `AL-B-ESS-SMOKE` and `AL-B-ESS-HEAT` inside the closet, on `CKT-LT-BACKUP`.
Neither is required by the adopted code (section 7). The 2021 R328.7 asks for the smoke alarm,
and a heat detector only where a smoke alarm's listing bars one. The heat alarm is the
owner's standard: it is cheap and senses the cabinet.

**Declined for now**: a combustible-gas detector and an exhaust fan to outdoors.

## 4. The utility sink and the condensate

`FX-B-UTIL-SINK` stands in the furnace room's SE corner, back on `W-B-STR2`, clear of the
dry-fire lane, the ESS zone, the panel working space and `D-B-CLOSET`'s swing. It is the
same Glacier Bay QL033Y as the laundry, typed `FX-UTILITY-SINK-24` because on a slab the trap
sits in the cabinet: its 1 1/2" arm runs 5" into `W-B-STR2` and tees under
`PR-B-BATH-VENT`'s riser — vent first, then the drop (no S-trap) — through `SP-B-SLAB-USINK`
and 20 3/4" south under the slab onto `PR-B-BATH-DRAIN`. `CO-B-USINK` is its sink-line
cleanout. Stubs tee off the bath branches' `W-B-STR2` drops; `PR-B-CW-BATH` went to 3/4"
for the extra 1.25 WSFU, and its stop with it. `PR-B-BATH-VENT`'s riser moved 1 1/2" south
to y=19'-1 1/2" for it; at 19'-3" it stood in stud-001. `PR-B-HW-BATH`'s drop stood in the
same stud at 19'-4 1/2" and moved to 18'-8 1/2" (2026-10-31): north of the stud
`DU-B-ERV-R-PLAY` fills the bay, and the vent and `PR-B-LSINK-DRAIN`'s crossing sit between.
The sink's hot stub drops there, 13 1/2" from the cold.

The bundled faucet ships with a garden-hose adapter (Home Depot Q&A,
[listing](https://www.homedepot.com/p/questions/Glacier-Bay-24-in-W-x-21-in-D-x-34-in-L-Stainless-Steel-Laundry-Utility-Sink-with-Faucet-and-Cabinet-in-White-QL033Y/206057007/4));
the laundry declines it, this sink uses it. A hose thread on a potable line needs an ASSE
1011 hose-connection vacuum breaker (UPC 603.5.7): `PA-B-USINK-VB`, a Woodford 34HD (~$32,
[Consolidated Supply](https://www.consolidatedsupply.com/Product/15289)) or Watts 8A
(ASSE 1011, [Macomb](https://www.macombgroup.com/2335247/product/Watts-0061877)). No separate
hose bib. **Confirm the adapter's thread (3/4" GHT assumed) on the delivered carton.**

`PR-B-ERV-COND` now ends over this basin, 44 1/4" up — a 10" air gap over the 34" rim, above
the faucet's 43" box. The W-B-STR2 bore and the bath-lavatory termination are gone;
`PR-B-WH-COND` still tees in behind the tank. The TPR stays piped to the floor.

No receptacle stands within 6' of the sink, so E3902's sink rule adds nothing here.

## 5. The tiers

| Tier | Circuits | What it is |
|---|---|---|
| `ALWAYS_ON` | `CKT-FRIDGE`, `CKT-HA`, `CKT-LT-BACKUP`, `CKT-SUMP` | Food, network, light in the kitchen and mechanical room, the sump |
| `SHED` | `CKT-HP3`, `CKT-WH-240` | Fallback heat into the open stair; hot water |

**The sump moved to ALWAYS_ON** (2026-10-30). A SHED relay drops on low battery with no sun —
exactly the long stormy night the sump must run. Its start is now graded with the motors.

**Winter outage**: the water heater goes to off/vacation (80 gal of stored water rides a day
or two, and its compressor would be cooling a basement the battery cannot heat); HP3 is the
fallback heat. **The battery cannot do freeze protection** — that needs a drain-down plan.

`CKT-FRIDGE` is the fridge plus the upright freezer column beside it. `CKT-HA` sheds the
doorbell's and cameras' PoE ports on battery (`backup_shed_poe`, 42.0 W at the outlet).

## 6. The numbers — the hand oracle for `takeoff/backup_calc.py`

Every average rests on an authored `duty_cycle` — the softest numbers in the model. **Meter
and revise.** A circuit with none is an unknown contributor, never zero; so is an inverter
with no idle or efficiency.

**AC load (connected VA x duty, less shed PoE):**

| Circuit | VA | Duty | Average |
|---|---|---|---|
| `CKT-FRIDGE` | 800 | 0.13 | 104.0 W |
| `CKT-HA` | 300 | 0.44 | 132.0 - 42.0 = 90.0 W |
| `CKT-LT-BACKUP` | 579 | 0.15 | 86.9 W |
| `CKT-SUMP` | 1,000 | 0.05 | 50.0 W |
| **always-on** | 2,679 | | **330.9 W** |
| `CKT-HP3` | 1,500 | 0.4 | 600.0 W |
| `CKT-WH-240` | 500 (`backup_va`) | 0.15 | 75.0 W |
| **shed** | 2,000 | | **675.0 W** |

**Battery-side draw** = AC / 0.94 + 55 W idle:

- always-on: 330.9 / 0.94 + 55 = 352.0 + 55 = **407.0 W** (436.7 W at 765 VA earlier on
  2026-10-31; 462.2 W before the twenty backup cans went from 14.5 W modules to 6.5 W PAR20s).
  The lighting review the same day took 765 -> 579 VA: the workshop panels left for
  `CKT-LT-BSMT` (-120), the kitchen's 200 VA OMNIDRIVE became a 30 W TRADFRI for MITTLED
  (-170), the A4 task cans and two new kitchen cans (+38.8), the pantry PSU 60 W OMNIDRIVE
  -> 96 W Class 2 HLG (+36), the ESS closet light (+9) and the basement bath night-light
  driver (+20).
- both tiers: (330.9 + 675.0) / 0.94 + 55 = 1,070.1 + 55 = **1,125.1 W**.

**Storage**: 14.3 kWh x 0.90 DoD = **12.87 kWh** usable.

**Autonomy, no sun**: 12,870 / 407.0 = **31.6 h** always-on; 12,870 / 1,125.1 = **11.4 h**
both tiers.

**48-hour cycle** (one strong day in two; array 12 x 440 W = 5.28 kW):

- 48 h of always-on: 0.4070 x 48 = **19.54 kWh**; both tiers 1.1251 x 48 = 54.00 kWh.
- Summer strong day, 3.0 kWh/kW: 15.84 kWh -> always-on net **-3.70 kWh**.
- December strong day, 1.5 kWh/kW (`WINTER_STRONG_DAY_KWH_PER_KW`): 7.92 kWh -> net
  **-11.62 kWh**. A low-pitch E/W split loses more of December than of June.

Solar is counted at the DC side and all load at 94%, which errs heavy: PV-to-battery is
99.9%, and daytime loads run PV-to-AC near 97.5%.

**Darkness bridge**: the battery alone must carry the always-on tier from one evening's last
sun through a dark day and the longest night after it. St Paul (44.98 N) at the winter
solstice: cos H = (sin -0.833 - sin 44.98 sin -23.44) / (cos 44.98 cos -23.44)
= (-0.01454 + 0.28118) / 0.64897 = 0.4109, H = 65.74°, day = 8.77 h, **night = 15.23 h** (`longest_night_hours`, from the site's own
latitude). Needs 0.4070 x (24 + 15.23) = **15.97 kWh**; has 12.87.

**Peak**: 4,679 VA connected on the microgrid against 8 kW continuous; the largest motor start
(HP3, 1,500 VA x 3 for a soft-started VFD = 4,500 VA) against 16 kW. Both fit. The calc's 3x
does not describe the sump, an across-the-line motor: at 6x it starts at 6,000 VA, also well
inside 16 kW, but nothing in the engine grades that figure.

**Verdict (`backup_calc`)**: one strong summer day does not cover 48 h of even the always-on
tier, and one battery does not bridge a December dark day. The idle draw alone (55 W x 48 h
= 2.64 kWh) took the +0.12 kWh margin of the old calc to about -2.5; efficiency and the sump
do the rest. Read it as: **the always-on tier is a 32-hour countdown, not a steady state.**
The levers, in order of cost: meter the duty cycles and the real idle; shed `CKT-LT-BACKUP`
lighting harder; the second PV row (`plans/TODO.md`); a second battery (28.6 kWh bridges at
16.0). The verdict says "add array" rather than "not battery" because both are short.

A system with zero usable storage used to report "sustains" (the cycle never looked at the
battery). `sustains_*` and `bridges` now require usable storage > 0.

## 7. Code: what the adopted book actually says

Minnesota's residential code is the 2018 IRC (MN Rules ch. 1309; no R327 amendment found).
Its **R327** is code change RB171-16 as modified
([ICC monograph](https://www.floridabuilding.org/fbc/commission/FBC_0618/Code_Mod/TC-with-Monograph/IRC/IRC-Building-Electrical-Linked-With-Monograph.pdf);
[ICC summary](https://cdn-web.iccsafe.org/wp-content/uploads/Energy-Storage-Systems-Fire-Safety-Concepts-in-the-2018-IFC-and-IRC.pdf)):

- R327.1 scope; **R327.2** UL 9540 listing (under 1 kWh exempt) — `code.R327_ess_listing`;
- **R327.3** per the manufacturer's instructions and listing, and *not within the habitable
  space of a dwelling unit* — `code.R327_ess_location` (new);
- R327.4 NFPA 70, inverter UL 1741 or part of the UL 9540 listing;
- R327.5 ventilation only for batteries that gas hydrogen while charging (not LFP);
- R327.6 vehicle-impact barriers.

**No kWh caps, no location list, no detection rule.** The old checks cited "R327.5" for the
20/40 kWh caps and "R327.7" for detection; those are the **2021 IRC R328.5 and R328.7**
(from NFPA 855). They now grade as `advisory.ess_capacity` (20 kWh per unit, 40 indoor,
80 in a garage) and `advisory.ess_detection` (smoke per R328.7; the heat alarm graded as the
owner standard, uncited), citing the 2021 book as the code the next adoption brings. MN's fire code (2018 IFC base) reaches lithium ESS only above 20 kWh.

## 8. Rapid shutdown

The Aptos 440 W module is Voc 39.03 V at STC, -0.25%/°C, so **44.40 V** at the -30 °C design
low; two sum to 88.8 V against NEC 690.12(B)(2)'s 80 V. Every module gets its own SunSpec
transmitter. `code.NEC_690_12_rapid_shutdown` computes that from `voc_cold`; rated Voc
would say 78.1 V for a pair and pass, which is why `voc_cold` is the only voltage it reads.

## 9. Wiring as built

`CKT-ESS-GRID` (50 A 2-pole, slot 40 of `ED-B-PANEL`) is the 12kPV's grid port; its load
port feeds the 12-space `ED-B-BACKUP-PANEL`. The three raceways (`CD-B-PV-INV`,
`CD-B-INV-PANEL`, `CD-B-INV-BACKUP`) were re-laid 2026-10-30 onto the inverter where it
hangs, on `W-B-N4` west of the closet: each rises into the case bottom at its own height
(30", 26", 22" AFF), north of the dry-fire lane, then down `W-B-W1` with one conduit body
each. The battery's DC run is ~5 ft through `W-B-ESS-W`.

## 10. The V2H seam (rough-in, recorded here)

No V2H product integrates with a 48 V hybrid inverter. A car lands as **its own system at
the service entrance** (a bidirectional charger plus a microgrid interconnection device),
not on `ED-B-BACKUP-PANEL`. NEC 705.12 leaves 20 A on the main bus (225 x 1.2 - 200 = 70 A
allowed, 50 A used). On the EG4 path the MID is the **EG4 GridBOSS** (200 A transfer switch,
up to three 12kPV/18kPV/FlexBOSS21, generator and smart-load ports;
[EG4](https://eg4electronics.com/categories/inverters/eg4-gridboss/)).

Rough-in to build now:

- a 1 1/2" spare conduit, panel to garage, sized for a 100 A feeder;
- a 1" data conduit beside it;
- a reserved 2-pole space in `ED-B-PANEL`;
- ~30 x 36" of clear wall by the meter for a gateway or MID.

**Not modelled.** A `ConduitRun` can express an empty raceway (`CD-B-SPARE-CHASE`), but the
panel-to-garage path is `CD-B-GARAGE`'s corridor — the north-wall ceiling lane, the
`W-B-N2` sleeve and the buried gap leg, routed 3/8" off the drain — and two more raceways
in it are a routing pass of their own (`plans/TODO.md`).

**Moving the ESS to the garage** was rejected: unheated, -20 F.

## 11. Deferring the battery

The 12kPV runs without a battery, but EG4 does not document its load port working from PV
alone, so **ask EG4** before counting on PV-only backup. With zero storage the calc now
reports no usable storage rather than "sustains". A small LFP UPS (separate from the ESS)
should carry Home Assistant, the router and the leak valve regardless.

## 12. Open

- EG4's ETL/UL 9540 certificate naming **12kPV + WallMount Indoor** by model and count.
- What EG4 means by the WallMount's "fire arrestors".
- Declare future storage on the Xcel interconnection application now.
- St Paul DSI's position on a UL 9540 3rd-ed. DC ESS listing.
- The declined gas detector and exhaust fan, if the owners revisit containment.
- A freeze drain-down plan (the battery cannot hold the house above freezing).
- A small LFP UPS for HA, the router and the leak valve.
- Meter the 12kPV's islanded idle and low-load efficiency; revise the duty cycles.
- Confirm the QL033Y hose adapter's thread; source the 24" steel door.
