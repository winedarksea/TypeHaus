# System 1's return path, and the door undercuts that are the whole of it

**Design and decision note — 2026-09-04; re-graded 2026-11-06.** `mep.door_transfer_air`
now computes this table from the model (`checks/mep/door_transfer_air.py`, pinned in
`tests/test_door_undercut.py`). The 2026-09-04 answer, six doors cut 1 1/4"-1 3/4", is
**withdrawn**: interior doors are stock prehungs cut down on site, and an undercut stays in
1/2"-3/4" (owner, 2026-11-06; `TRIM-STANDARD.door_undercut`). See "Re-graded at 3/4"" below.

## The condition

System 1 (`EQ-S-HP1-AH`, 750 cfm) has **two** returns: `REG-S-HP-RET`, a 28 x 12 filter-back
grille in `SF-S-HP1`'s underside at (20'-11 1/2", 29'-1 1/4"), in `RM-S-HALL`, drawing 570
cfm of room air, and since 2026-11-09 `REG-S-HP-SUITE-RET`, the suite's ducted 80 cfm (below).
Every other System 1 terminal is a supply. So the supply air delivered to a
room behind a closed door has to get back to that hall through the door.

The ERV does not help. Its second-storey bedroom pickups (`REG-S-RET-BED1/2/3`) run at
**5 cfm each** (`plan/erv_balance.py`) — they are stale-air tokens on a 210 cfm balanced machine, not a return path.

## The arithmetic

A door undercut is a sharp-edged slot. The relation used here is the one Building America
and the ACCA literature use for exactly this geometry:

    Q (cfm) = 1.07 x A (in^2) x sqrt( dP (Pa) )

Sanity check on the figure everyone quotes: a 1" undercut on a 30" leaf is 30 in^2, and
1.07 x 30 x sqrt(3) = **55.6 cfm at 3 Pa** — the familiar "about 50 cfm".

The criterion is **3 Pa (0.012 in. w.g.)** across a closed bedroom door, which is ACCA
Manual D's figure, ASHRAE's, and the one ENERGY STAR and Building America both enforce.
Rearranged, the free area a room needs is `A = Q / 1.853`.

## What each door would have to be (2026-09-04, withdrawn)

| Room | System 1 supply | Door | Leaf | A at 3 Pa | Undercut | dP as cut |
|---|---|---|---|---|---|---|
| `RM-S-BED1` | 80 cfm | `D-S-BED1` | 30" | 43.2 in^2 | 1 1/2" | 2.76 Pa |
| `RM-S-BED2` | 80 cfm | `D-S-BED2` | 30" | 43.2 in^2 | 1 1/2" | 2.76 Pa |
| `RM-S-BED3` | 80 cfm | `D-S-BED3` | 30" | 43.2 in^2 | 1 1/2" | 2.76 Pa |
| `RM-S-SUITE` | 100 cfm | `D-S-SUITE` | 32" | 54.0 in^2 | 1 3/4" | 2.79 Pa |
| `RM-A-STUDY` | 100 cfm | `D-A-STUDY` | 30" | 54.0 in^2 | 1 3/4" | 2.92 Pa |
| `RM-A-STUDIO` | 75 cfm | `D-A-HALVES` | 32" | 40.5 in^2 | 1 1/4" | 2.98 Pa |

## Re-graded at 3/4" (2026-11-06)

Every relief door (the privacy types, `D-B-FURN`, `D-B-PLAY`) now hangs at 3/4", the top of
the range; every other leaf at the factory 1/2". The check nets each zone's terminals (the
ERV's 5 cfm bedroom pickups come off the supply), folds a dead-end bath or closet into the
room it opens from, and treats the zone a stair reaches as the house:

| Zone | Net | Door | Free area | dP | Needs at 3 Pa |
|---|---|---|---|---|---|
| `RM-S-BED1/2/3` | 75 cfm out | 30" x 3/4" | 22.5 in^2 | **9.7 Pa** | 40 in^2 |
| `RM-S-SUITE` (+ suite bath, closet; ducted return since 2026-11-09, below) | 80 cfm out | `D-S-SUITE` 32" x 3/4" | 24.0 in^2 | **9.7 Pa** | 43 in^2 |
| `RM-A-STUDIO` (+ studio bath, ERV closet) | 50 cfm out | `D-A-HALVES` 32" x 3/4" | 24.0 in^2 | **3.8 Pa** | 27 in^2 |
| `RM-S-PLANT` | 70 cfm out | `D-S-PLANT` 30" x 1/2" | 15.0 in^2 | **19.0 Pa** (8.5 at 3/4") | 38 in^2 |
| `RM-A-EAST-UNFIN` | 35 cfm out | `D-A-STUDY` 30" x 1/2" | 15.0 in^2 | **4.8 Pa** (2.1 at 3/4") | 19 in^2 |
| `RM-A-STUDY` | 100 cfm | open to the stair well | - | pass | - |

`RM-A-STUDY` is at the attic stair head, so its own air leaves down the well; the old table
sent it through the bookcase door. `RM-A-EAST-UNFIN` is graded through `D-A-STUDY` because
the model holds no opening between it and the well; if it is open to the void, that row goes.

**No undercut inside the owner's range carries this air.** The bedrooms and the suite need
about 1.8x the free area 3/4" gives. Closing it is an owner decision: a transfer grille
pair or a jump duct per room (each about 20 in^2 net free area more), or a ducted return in
the room. Until then the rows above stand as `mep.door_transfer_air` ADVISORYs; the suite's is closed.

**What it was.** A conventional 3/4" undercut on a 30" leaf is 22.5 in^2. At 80 cfm that is

    dP = ( 80 / (1.07 x 22.5) )^2 = 11.0 Pa

— 3.7x the criterion. `RM-A-STUDY` is the worst in the house: 100 cfm through the same
22.5 in^2 is **17.3 Pa**. At those pressures the room does not receive its authored cfm at
all; the fan sees the extra external static and the balance moves elsewhere.

## What is deliberately NOT on the list

* **`D-S-PLANT` (`RM-S-PLANT`, 75 cfm).** Its supply is `REG-T-HP-SUP-DAMPERED`, interlocked
  with `REG-S-ERV-PLANT-EXH`; the room is meant to sit neutral-to-slightly-negative and the
  damper is what makes that true (`notes/plant_room.md`). A large undercut works *against*
  that — it is a leak path in the one room whose pressure is a design output. Leave it
  conventional.
* **`D-S-STUDY2`.** `is_door=False` — a cased opening with no leaf. `RM-S-STUDY2`'s 75 cfm
  has a permanently open path.
* **`RM-A-EAST-UNFIN` (35 cfm).** Open to the stair void; no door to cut.
* **Every bathroom.** They are extract terminals at 20 cfm; makeup *in* under a conventional
  3/4" undercut is 0.36" worth of free area. Nothing to do.

## Sealed doors (owner, 2026-11-03)

Four leaves are sealed at the bottom; each needs a named path for the air it would have
passed. Per-door detail: `notes/interior_door_schedule.md`.

| Door | Seal | Air that must move | Path | A at 3 Pa |
|---|---|---|---|---|
| `D-S-BATH1` | kerf seal + sweep, no undercut | `REG-S-EXH1` 20 cfm in | `REG-S-XFER-VANITY` → lined bay → `REG-S-XFER-BATH1`, 6x6 each (~24 in^2) | 10.8 in^2 |
| `D-M-BED2` | kerf seal + automatic bottom | `REG-M-SUP3` 15 cfm out | under `D-M-BATH2` (32" x 3/4" = 24 in^2) to `REG-M-EXH2`; **keep that undercut** | 8.1 in^2 |
| `D-B-SHOP` | weatherstrip + sweep, no undercut | `REG-B-RET1` 6 cfm in | under `D-B-FURN` (36" x 3/4" = 27 in^2) from the furnace room; **keep that undercut** | 3.2 in^2 |
| `D-B-SAUNA` | insulated sauna door | none | supply and exhaust balanced 20/20 (`notes/erv_static_budget.md` §10.8) | - |

**Re-graded 2026-11-06:** `RM-M-BED` supplies 15 cfm and its bath draws 20, so the pair nets
5 cfm *in*, and with `D-M-BED2` sealed and the closet a dead end nothing feeds it
(`mep.door_transfer_air` ADVISORY: 3 in^2 needed). `RM-S-BATH1`'s grille pair is UNKNOWN to
the check: `RegisterType` states no free area.

`D-B-PLAY` takes gaskets and an astragal but keeps its 3/4" undercut for its 30 cfm supply
(16.2 in^2 needed, 45 in^2 under a 60" pair); `D-M-BATH1` keeps 3/4" for its 20 cfm exhaust.
The bath pair is 6x6 because the bath face of `W-S-BD-N`'s west bay is clear only between the
SEKTION rail backing (top 97 1/4") and the top plate (104 3/8"), 7 1/4" wide.

## RM-S-SUITE: a ducted return, door sealed (owner, 2026-11-09)

A north-wall transfer in `W-S-SN2` (one usable bay, a cut stud, a moved switch, beside the
bed) and a passive jump duct (about 7 Pa sealed) were compared and set aside. The suite
returns to System 1 through its own duct instead:

* `REG-S-HP-SUITE-RET`: 12x12 filter-back ceiling grille at (104", 184"), MERV 13 12x12x1
  (stocked), a locked balancing damper at its boot.
* `DU-S-HP-SUITE-RET`: 6x4 in FS-ATTIC's y 176-192" bay, x 104" -> 254", through a derived
  pass-through box at the x=18' bearing line.
* `DU-S-HP-SUITE-RET-LANE`: drops into `SF-S-DUCT`'s east lane at (254", 184"), runs north at
  225 3/8" absolute to `EQ-S-ERV-MIX`'s south face at y=335". `DU-S-HP-BED2`/`-BED3` were
  lowered 3/4" so it clears their crowns by 1".

Balance, by hand:

    in   REG-S-HP-SUITE            100 cfm
    out  suite bath extract          20 cfm
    out  REG-S-HP-SUITE-RET          80 cfm   -> net 0: D-S-SUITE carries nothing
    6x4 = 24 in^2 = 0.1667 ft^2:   80 / 0.1667 = 480 fpm (a return branch)
    12x12 face = 1.0 ft^2:         80 fpm
    hall grille 336 in^2 = 2.333 ft^2 at 750 - 100 (ERV) - 80 = 570 cfm: 244 fpm (< 300)

`D-S-SUITE` is `DT-INT-SWING32-PRIV-SOLID-SEALED` at the stock 1/2" undercut, kerf seal and a
sweep; `mep.door_transfer_air` reads the zone "balanced".

**Commissioning.** With the door sealed the suite's pressure follows the damper setting and
the hall filter's loading. Set the damper to 80 cfm and lock it; re-check at every filter
change. With System 1's fan off, the bath's 20 cfm makes up backward through this duct.

## The two honest costs

1. **Sound.** `W-S-BW1/2/3` are `INT_2X4_RC` — resilient channel, chosen for acoustic
   isolation. An undercut is a straight acoustic leak under the door and gives back a
   real part of what the channel buys. A transfer grille or a jump duct would be worse still
   (a jump duct in an `FS-ATTIC` bay is the only option that keeps the wall intact), so the
   undercut is the cheapest point on that curve, not a free one. Light and privacy go the
   same way.
2. **Carpet.** `RM-S-BED1/2/3` are carpeted (the suite is oak), and an undercut is specified to
   the *finished* floor. Pile throttles the gap, so the effective free area is below the
   geometric figure — perhaps 20-25% below. The table above is the geometric minimum. If the
   balance report shows more than 3 Pa at a closed door, the next step is a jump duct or a transfer
   grille: 2" is outside the owner's range.

## The duty-cycle mitigation, stated honestly

The heat pump **cycles**; the ERV runs **continuously**. So the 11 Pa condition exists only
while the compressor is calling, and the long-run average imbalance is smaller than the
peak. That is a real mitigation and it is why this is a comfort and delivery problem rather
than an envelope one — but a design is sized for the condition that occurs, not for its
duty cycle, so the table stands.

## What the model holds now

`DoorType.undercut` (else `TrimStandard.door_undercut.hung`) hangs the leaf; resolve derives
the site cut off the stock slab (`DoorSizing.leaf_cut_m`); A-601 prints both in its
Undercut column; `advisory.door_undercut` grades every leaf against 1/2"-3/4"; and
`mep.door_transfer_air` grades the table above.
