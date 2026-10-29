# Basement surface wiring, device boxes and conduit

Owner decision 2026-10-28; modelled 2026-10-29 (decision #93). Boxes come from
`plan/device_boxes.py`'s `BoxStandard`; the workshop and theater raceways are
`plan/electrical_branches.py`. Code: 2026 NEC, in force in Minnesota since August 2026;
Saint Paul DSI inspects.

## What is installed

The basement perimeter and the 12" cross walls are bare concrete inside (4" XPS outboard, no
room lining). About twenty devices sit on that concrete.

- **Default: NM-B in a 3/4" EMT sleeve.** NM-B runs overhead in the joists. A vertical 3/4"
  EMT sleeve drops from the ceiling to the top knockout of a surface steel box, with a
  nonmetallic bushing at the top and an offset connector at the box. There is no top box,
  no THHN and no horizontal run on the wall. The engine derives the sleeve
  (`resolve/device_drops.py`); nobody authors it.
- **Surface box:** RACO 232, 4" square × 2-1/8" (30.3 in³), under a 1/2"-raised RACO 808C
  (1 Decorator) or 809C (2 Decorator) cover. The device sits on the cover, 2-5/8" off the wall.
- **Flush box:** in a framed cavity, a deep nonmetallic new-work box. A 1-gang is 22.5 in³
  (Carlon B122A) and a 2-gang is 35 in³ (B235A), both taken as 3-1/4" deep. The box goes
  through furring and any membrane behind the finish to the studs, sealed at the membrane.
- **Flush box a raceway reaches:** RACO 232 with a RACO 768 1-device ring. This covers the
  three floor-heat thermostats, the study data jack, the kitchen GFCI the CD-B-KITCHEN trunk
  feeds, and the EV receptacle.
- **Workshop: one large raceway, one small.**
  - Large: CD-B-WORKSHOP is 1" EMT + THHN from ED-B-PANEL-2 to ED-B-WORKSHOP-JB, a box
    recessed in the gypsum ceiling over the bench. It carries CKT-WORKSHOP-240. The 1" size
    leaves room for later circuits or a 60–100 A subpanel feeder (#3 + #8 THHN fits at 40%).
  - Drops: 3/4" EMT + THHN runs from that box to RC1 (CKT-WORKSHOP-240) and RC2. CKT-RC-BSMT's
    NM enters the box for RC2.
  - Small: the existing 3/4" CD-B-DATA-SHOP stays as the data raceway.
- **Theater:** CD-B-PLAY-SPARE is a 3/4" EMT capped spare with a pull string. It runs from
  ED-B-PANEL to ED-B-PLAY-N-JB, a surface box on the ceiling over the TV. The ceiling there
  is gypsum hung on SL-M-DECK's concrete band, so the box cannot be recessed. CD-B-PLAY-N-RC1
  is 3/4" EMT + THHN from that box to ED-B-PLAY-N-RC1, and CKT-RC-BSMT's NM enters the box.
  There is no new circuit, because the panel is nearly full. A dedicated AV circuit can be
  pulled into the spare later without opening the ceiling.
- **Floor heat:** each zone names its thermostat (`FloorHeat.thermostat_ref`). Each zone gets
  two separate raceways, as both Schluter and Warmup/WarmlyYours require.
  - **Sensor:** 1/2" ENT down the stud bay and through the plate, capped. Under a DITRA-HEAT
    mat it ends at the plate's foot, and the mat's own sensor sleeve carries on from there:
    a 0.84" tube has no room in a 3/4" tile-and-mat build-up. On FH-M-DINING it is 3/4" ENT
    cast into the concrete band out to the `stat` point.
  - **Cold lead:** 1/2" ENT down to the top of the bottom plate.

## Code basis

| Item | 2026 NEC |
|---|---|
| NM on a basement wall, protected in a raceway, nonmetallic bushing at entry | 334.15(B), (C) |
| A protective sleeve is outside the Chapter 9 fill tables | Chapter 9, Note 2 to the tables |
| The sleeve needs no bonding of its own: the box is bonded by the NM's ground | 250.86 Ex. 2 |
| Power and data never share a raceway | 800.133, 725.136 |
| Bends between pull points ≤ 360° | 358.26 (EMT), 362.26 (ENT), 352.26 (PVC) |
| EMT support: within 3 ft of each termination, then every 10 ft | 358.30 |
| ENT support: within 3 ft of each box, then every 3 ft | 362.30 |
| Box fill | 314.16(A), (B) |
| A concrete crossing is sleeved before the pour | house rule; `mep.sleeve_coverage` |

## Cost comparison

These are rough estimates per surface device, with a 6 ft drop and a 40 ft average run to
the panel. They use the `[conduit]`, `[conduit_fittings]` and `[conductors]` rates in
`prices.toml`. They are not quotes.

| Method | Roughly | Why not everywhere |
|---|---|---|
| NM-B overhead + 3/4" EMT sleeve (chosen) | $35–70 for the sleeve and its parts, plus the NM the house already buys | — |
| EMT + THHN from the panel | $250–450 | Every device gets its own pipe across the ceiling, and the panel end is already crowded. Kept only where re-pulling matters (workshop, theater). |
| MC home run | $140–280 | Wins only on an orphaned long run or a pass too narrow for EMT. None was found (see the audit below). |

## Box fill (hand-worked oracle for `electrical.box_fill`)

The model counts the conductors as through-fed: two cables of the circuit's insulated
conductors, plus 2 volumes per yoke, plus 1 for all the grounds. The one exception is a
receptacle that is its circuit's only load, which is end-fed with one cable. Volumes per
conductor come from Table 314.16(B): 14 AWG 2.00 in³, 12 AWG 2.25 in³, 10 AWG 2.50 in³.

1. **ED-B-WORKSHOP-RC2:** quad, surface 2-gang, CKT-RC-BSMT 20 A, so 12 AWG.
   - Conductors: 2 cables × 2 + 2 yokes × 2 + 1 = 9.
   - Volume: 9 × 2.25 = **20.25 in³**, in a RACO 232 of 30.3 in³. PASS.
2. **A 15 A switch** in a flush 1-gang box, 14 AWG.
   - Conductors: 2 × 2 + 1 × 2 + 1 = 7.
   - Volume: 7 × 2.00 = **14.0 in³**, in a 22.5 in³ box. PASS.
3. **ED-B-WORKSHOP-RC1:** 6-20R + 5-20R, a 2-pole circuit with a neutral, alone on
   CKT-WORKSHOP-240, so end-fed.
   - Conductors: 1 × 3 + 2 × 2 + 1 = 8.
   - Volume: 8 × 2.25 = **18.0 in³**, in 30.3 in³. PASS.

`tests/test_device_boxes.py::test_box_fill_oracle` pins all three. Raised covers and rings
are credited 0 in³, because none of the selected covers is marked with a volume.

## MC audit (derived drops)

Length is box top to sleeve top. "Nearest" is the plan clearance from the drop's surface to
the nearest other run in its height band.

| Drop | Length | Nearest |
|---|---|---|
| ED-B-UTIL-RC1 | 45.9" | 1.08" to CD-B-DATA-SHOP |
| ED-B-SUMP-RC | 18.1" | stops under DU-ERV-EA at −3'-4 3/8" |
| ED-B-GYM-RC5 / RC6 / RC7 | 77.6" each | > 6 ft |
| ED-B-STAIR-RC1 / RC2 | 24.6" / 17.2" | stop under CD-B-GARAGE at −1'-6 7/8" |
| ED-B-PLAY-N-SCONCE1..6 | 8.9" each | ≥ 9.6" |
| ED-B-PLAY-N-SW | 38.8" | stops under DU-B-ERV-R-PLAY at −1'-9 3/16" |

None qualifies for MC. Every drop is short and vertical with room around it, and no run is
orphaned. No MC is modelled.

## Drops that stop under a run

Where a trunk or duct hugs the wall across the drop's line, the sleeve stops 1/2" under it.
The NM continues over that run to the joists. This applies to SUMP-RC, STAIR-RC1/RC2 and
PLAY-N-SW.

Open item for the electrician: confirm on site that the NM above the sleeve is shielded by
the run. Otherwise, offset the sleeve around the run with a bend.

## Open items

- The six PLAY-N sconce canopies must cover a 4" square surface box. See
  `plans/lighting-products.md`.
- Confirm the RACO 809C catalog number for the 2-Decorator raised cover.
- Confirm the depth of the flush nonmetallic boxes. 3-1/4" is assumed, and it fits every
  cavity in the house.
- ED-B-SPA-RC is outdoors on the sunken-garden concrete. It derives a surface box but no
  sleeve, because it is outside a room. It wants a weatherproof box and an in-use cover,
  which is the same reasoning as the `ED-T-LEV-GFCI-WR` type. This is a type change for the
  owner to make.
- **Pull boxes.**
  - CD-B-PLAY-SPARE: in the hall ceiling at x 16'-2 3/4", y 19'-2 3/4", and in RM-B-PLAY-N.
  - The workshop and theater: their ceiling boxes.
  - All of these are accessible through blank covers.
