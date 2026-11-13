# System 1's return path, and the door undercuts that are the whole of it

**Design and decision note — 2026-09-04; re-graded 2026-11-06.** `mep.door_transfer_air`
now computes this table from the model (`checks/mep/door_transfer_air.py`, pinned in
`tests/test_door_undercut.py`). The 2026-09-04 answer, six doors cut 1 1/4"-1 3/4", is
**withdrawn**: interior doors are stock prehungs cut down on site, and an undercut stays in
1/2"-3/4" (owner, 2026-11-06; `TRIM-STANDARD.door_undercut`). See "Re-graded at 3/4"" below.

## The condition

System 1 (`EQ-S-HP1-AH`, 750 cfm) has **four** returns: `REG-S-HP-RET`, a 24 x 12 filter-back
grille (stock 12x24x1) in `SF-S-DUCT`'s underside at (19'-11", 29'-11 1/2") since 2026-11-11 (framed hole
`AO-S-DUCT-RET`; it was in the retired `SF-S-HP1`), in `RM-S-HALL`, drawing 455
cfm of room air; since 2026-11-09 `REG-S-HP-SUITE-RET`, the suite's ducted 80 cfm; since
2026-11-11 `REG-S-HP-BED3-RET`, BED3's ducted 80 cfm; and since 2026-11-12
`REG-A-HP-EAST-RET`, the east attic room's 35 cfm (all below). (The ERV's 100 joins them in the
mixing box.)
Every other System 1 terminal is a supply. So the supply air delivered to a
room behind a closed door has to get back to that hall through the door.

The ERV does not help. Its second-storey bedroom pickups (`REG-S-RET-BED1/2`; BED3's went
2026-11-11) run at **5 cfm each** (`plan/erv_balance.py`) — they are stale-air tokens on a 210 cfm balanced machine, not a return path.

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
| `RM-S-BED1/2` | 75 cfm out | 30" x 3/4" | 22.5 in^2 | **9.7 Pa** | 40 in^2 |
| `RM-S-BED3` | 0 (75 cfm out until its ducted return, 2026-11-11, below) | `D-S-BED3` 30" x 1/2" | - | balanced | - |
| `RM-S-SUITE` (+ suite bath, closet) | 0 (80 cfm out until its ducted return, 2026-11-09, below) | `D-S-SUITE` 32" x 1/2", sealed | - | balanced (9.7 Pa before) | - |
| `RM-A-STUDIO` (+ studio bath, ERV closet) | 50 cfm out | `D-A-HALVES` 32" x 3/4" | 24.0 in^2 | **3.8 Pa** | 27 in^2 |
| `RM-S-PLANT` | 0 (70 cfm out until sealed, 2026-11-12) | `D-S-PLANT`, sealed steel | - | no System 1 air | - |
| `RM-A-EAST-UNFIN` | 0 (35 cfm out until its ducted return, 2026-11-12, below) | `D-A-STUDY`, sealed | - | balanced (4.8 Pa before) | - |
| `RM-A-STUDY` | 100 cfm | open to the stair well | - | pass | - |

`RM-A-STUDY` is at the attic stair head, so its own air leaves down the well; the old table
sent it through the bookcase door. `RM-A-EAST-UNFIN` is graded through `D-A-STUDY` because
the model holds no opening between it and the well. It no longer needs to be: the bookcase door
passes no air (sealed, 2026-11-12) and the room has its own return.

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

* **`D-S-PLANT` (`RM-S-PLANT`).** Sealed since 2026-11-12: no System 1 supply, no ERV extract;
  the room vents to Study 2 through its own transfer pair (`notes/plant_room.md`). Study 2's
  supply is now two 75 cfm grilles (`REG-S-HP-STUDY2`, `-S`) and leaves through the cased
  `D-S-STUDY2`.
* **`D-S-STUDY2`.** `is_door=False` — a cased opening with no leaf. `RM-S-STUDY2`'s 75 cfm
  has a permanently open path.
* **`RM-A-EAST-UNFIN` (35 cfm).** Returns through its own grille at the air handler (below);
  the Murphy door passes no air, so it has no undercut to cut.
* **Every bathroom.** They are extract terminals at 20 cfm; makeup *in* under a conventional
  3/4" undercut is 0.36" worth of free area. Nothing to do.

## Sealed doors (owner, 2026-11-03)

Five leaves are sealed at the bottom; each needs a named path for the air it would have
passed. Per-door detail: `notes/interior_door_schedule.md`.

| Door | Seal | Air that must move | Path | A at 3 Pa |
|---|---|---|---|---|
| `D-S-BATH1` | kerf seal + sweep, no undercut | `REG-S-EXH1` 20 cfm in | `REG-S-XFER-VANITY` → lined bay → `REG-S-XFER-BATH1`, 6x6 each (~24 in^2) | 10.8 in^2 |
| `D-M-BED2` | kerf seal + automatic bottom | `REG-M-SUP3` 15 cfm out | under `D-M-BATH2` (32" x 3/4" = 24 in^2) to `REG-M-EXH2`; **keep that undercut** | 8.1 in^2 |
| `D-B-SHOP` | weatherstrip + sweep, no undercut | `REG-B-RET1` 6 cfm in | under `D-B-FURN` (36" x 3/4" = 27 in^2) from the furnace room; **keep that undercut** | 3.2 in^2 |
| `D-B-SAUNA` | insulated sauna door | none | supply and exhaust balanced 20/20 (`notes/erv_static_budget.md` §10.8) | - |
| `D-S-PLANT` | steel prehung, compression seal + sill (2026-11-12) | none from System 1 | the room's own high/low transfer pair to Study 2, hand-set 5-13 cfm (`plant_room_moisture_budget.md`) | - |

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
* `DU-S-HP-SUITE-RET`: 6x4 in FS-ATTIC's y 176-192" bay, x 104" -> 254", at 232 1/4"
  absolute, through a derived pass-through box at the x=18' bearing line (5/8" over its
  bottom rail).
* `DU-S-HP-SUITE-RET-LANE`: drops into `SF-S-DUCT`'s east lane at (254", 184") and runs north
  at 225 3/8" absolute to y=344". `DU-S-HP-BED2`/`-BED3` were lowered 3/4" so it clears
  their crowns by 1". Since 2026-11-11 it rises to the FS-ATTIC bay there and
  `DU-S-HP-SUITE-RET-UP` carries it east, up through `FO-A-HP1-SUITE-RET` into
  `EQ-S-ERV-MIX` on the attic deck.

Balance, by hand:

    in   REG-S-HP-SUITE            100 cfm
    out  suite bath extract          20 cfm
    out  REG-S-HP-SUITE-RET          80 cfm   -> net 0: D-S-SUITE carries nothing
    6x4 = 24 in^2 = 0.1667 ft^2:   80 / 0.1667 = 480 fpm (a return branch)
    12x12 face = 1.0 ft^2:         80 fpm
    hall grille 288 in^2 = 2.0 ft^2 at 750 - 100 (ERV) - 80 (suite) - 80 (BED3) - 35 (east) = 455 cfm:
    228 fpm (< 300)   [570 until BED3's return, 2026-11-11; 490 until the east return, 2026-11-12]

`D-S-SUITE` is `DT-INT-SWING32-PRIV-SOLID-SEALED` at the stock 1/2" undercut, kerf seal and a
sweep; `mep.door_transfer_air` reads the zone "balanced".

**Commissioning.** With the door sealed the suite's pressure follows the damper setting and
the hall filter's loading. Set the damper to 80 cfm and lock it; re-check at every filter
change. With System 1's fan off, the bath's 20 cfm makes up backward through this duct.

## RM-S-BED3: a ducted return, door at 1/2" (owner, 2026-11-11)

BED3's 5 cfm ERV pickup rode `DU-A-ERV-R-BED3`, about 55 LF and six elbows round the attic.
It is gone, and BED3 returns to System 1 directly:

* `REG-S-HP-BED3-RET`: 12x12 filter-back CEILING grille (`REG-T-HP-RET-FILTER-1212`, MERV 13
  12x12x1) at (26'-5 1/2", 32'-8"), in the room's north part, 6'-7" north of the supply so
  the return does not draw on the supply's own air. A locked balancing damper is at the
  boot. (It was a sidewall grille on `W-S-BW4` feeding a take-off on `DU-S-HP-RET` until
  the air handler moved to the attic the same day.)
* `DU-S-HP-BED3-RET`: 12x6, up through `FO-A-HP1-BED3-RET` and south on the attic deck
  (invert on the deck) into `EQ-S-ERV-MIX`'s north end.

Balance, by hand:

    in   REG-S-HP-BED3             80 cfm
    out  REG-S-HP-BED3-RET         80 cfm   -> net 0: D-S-BED3 carries nothing
    12x6 = 72 in^2 = 0.5 ft^2:     80 / 0.5 = 160 fpm
    12x12 face = 1.0 ft^2:         80 fpm
    hall grille 288 in^2 = 2.0 ft^2 at 750 - 100 (ERV) - 80 - 80 - 35 = 455 cfm: 228 fpm (< 300)

`D-S-BED3` is `DT-INT-SWING30-PRIV-STOCK`, the factory 1/2" undercut, not sealed. Ventilation:
BED3 keeps its fixed windows and gets ERV air through System 1's mixing box. With the
fan off it has no extract, and no check asks a bedroom for one (BEDROOM is not a stale
occupancy). **Sound:** the grille is about 3' of duct from the mixing box and a few feet
from the blower. Lining the 12x6 is an open item.

## Owner decisions 2026-11-12

* **`RM-S-BED1/2`: 9.7 Pa accepted.** 75 cfm out through a 30" x 3/4" door, no new returns. The
  `mep.door_transfer_air` ADVISORYs stand as decided.
* **`RM-A-STUDIO`: 3.8 Pa accepted** (`D-A-HALVES` 32" x 3/4", 50 cfm net out).
* **`RM-S-PLANT`: closed 2026-11-12.** Sealed; its supply moved to Study 2's south grille.
* **`D-A-STUDY` is sealed** (`DT-INT-BOOKCASE30.bottom_seal`): a bookcase door passes no air.
  `RM-A-STUDY` stays PASS because it is open to the stair.
* **`RM-A-EAST-UNFIN` gets a return at the air handler.** `REG-A-HP-EAST-RET` is the stock
  `REG-T-HP-RET-FILTER-1212-WALL` (12x12x1 MERV 13), 14" AFF on the **south face of
  `EQ-S-ERV-MIX`** (x 298-325.5", y 329-368"), through the 6" stub `DU-A-HP1-EAST-RET`, set to
  35 cfm. **The balancing damper is what makes it work.** The plenum's returns are in
  parallel and pull on the same static; an open 12x12 sits at the plenum and would draw far
  more than its 35 cfm from the room, starving the hall and bedroom returns. Lock the damper
  at 35 cfm and re-check at filter changes. The grille and its filter are reached from the room.
  Hall grille, with the 35 gone from it, is **455 cfm** (was 490).

    in   REG-A-HP-EAST            35 cfm
    out  REG-A-HP-EAST-RET        35 cfm   -> net 0: D-A-STUDY carries nothing
    12x12 face = 1.0 ft^2:         35 fpm

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
