# System 1's return path, and the door undercuts that are the whole of it

**Design and decision note — 2026-09-04.** No calculation is pinned to this file and no test
reproduces it. It records why six doors in this house carry an undercut larger than a
carpenter would cut on his own, and what happens if they do not.

## The condition

System 1 (`EQ-S-HP1-AH`, 750 cfm) has **one** return: `REG-S-HP-RET`, a 28 x 12 filter-back
grille in `SF-S-HP1`'s underside at (20'-11 1/2", 29'-1 1/4"), in `RM-S-HALL`, drawing 650
cfm of room air. Every other System 1 terminal is a supply. So the supply air delivered to a
room behind a closed door has to get back to that hall through the door.

The ERV does not help. Its second-storey bedroom pickups (`REG-S-RET-BED1/2/3`) run at
**2 cfm each** — they are stale-air tokens on a 210 cfm balanced machine, not a return path.

## The arithmetic

A door undercut is a sharp-edged slot. The relation used here is the one Building America
and the ACCA literature use for exactly this geometry:

    Q (cfm) = 1.07 x A (in^2) x sqrt( dP (Pa) )

Sanity check on the figure everyone quotes: a 1" undercut on a 30" leaf is 30 in^2, and
1.07 x 30 x sqrt(3) = **55.6 cfm at 3 Pa** — the familiar "about 50 cfm".

The criterion is **3 Pa (0.012 in. w.g.)** across a closed bedroom door, which is ACCA
Manual D's figure, ASHRAE's, and the one ENERGY STAR and Building America both enforce.
Rearranged, the free area a room needs is `A = Q / 1.853`.

## What each door has to be

| Room | System 1 supply | Door | Leaf | A at 3 Pa | Undercut | dP as cut |
|---|---|---|---|---|---|---|
| `RM-S-BED1` | 80 cfm | `D-S-BED1` | 30" | 43.2 in^2 | **1 1/2"** | 2.76 Pa |
| `RM-S-BED2` | 80 cfm | `D-S-BED2` | 30" | 43.2 in^2 | **1 1/2"** | 2.76 Pa |
| `RM-S-BED3` | 80 cfm | `D-S-BED3` | 30" | 43.2 in^2 | **1 1/2"** | 2.76 Pa |
| `RM-S-SUITE` | 100 cfm | `D-S-SUITE` | 32" | 54.0 in^2 | **1 3/4"** | 2.79 Pa |
| `RM-A-STUDY` | 100 cfm | `D-A-STUDY` | 30" | 54.0 in^2 | **1 3/4"** | 2.92 Pa |
| `RM-A-STUDIO` | 75 cfm | `D-A-HALVES` | 32" | 40.5 in^2 | **1 1/4"** | 2.98 Pa |

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

## The two honest costs

1. **Sound.** `W-S-BW1/2/3` are `INT_2X4_RC` — resilient channel, chosen for acoustic
   isolation. A 1 1/2" undercut is a straight acoustic leak under the door and gives back a
   real part of what the channel buys. A transfer grille or a jump duct would be worse still
   (a jump duct in an `FS-ATTIC` bay is the only option that keeps the wall intact), so the
   undercut is the cheapest point on that curve, not a free one. Light and privacy go the
   same way.
2. **Carpet.** `RM-S-BED1/2/3` and `RM-S-SUITE` are carpeted, and an undercut is specified to
   the *finished* floor. Pile throttles the gap, so the effective free area is below the
   geometric figure — perhaps 20-25% below. The table above is the geometric minimum. If the
   balance report shows more than 3 Pa at a closed door, the next step is 2" or a jump duct,
   not a larger grille.

## The duty-cycle mitigation, stated honestly

The heat pump **cycles**; the ERV runs **continuously**. So the 11 Pa condition exists only
while the compressor is calling, and the long-run average imbalance is smaller than the
peak. That is a real mitigation and it is why this is a comfort and delivery problem rather
than an envelope one — but a design is sized for the condition that occurs, not for its
duty cycle, so the table stands.

## What the model cannot hold

**`Opening` carries no `undercut` field.** This table lives here, in `plan/mep_registers.py`,
and nowhere the builder reads: the A-601 opening schedule prints Mark / Tag / Kind / Type /
Nominal footprint and has no column for it. **A door with no undercut on its schedule gets
cut at 3/4".** Closing that means adding the field to `Opening` and a column to
`emit/draw/schedules/architectural.py::_write_opening_schedule`; until then this note is the
only record and it has to be carried onto the door schedule by hand.
