# RM-M-BATH2's lighting — a 5000 K day layer and a 2700 K evening layer

**House:** catlin
**Structure:** `ED-M-BATH2-CAN1`, `-CAN2`, `-CAN-SH` (B1), `-CAN-SH-EVE` (B2), `-MIRROR` (P3),
`-MIRROR-HALO` (P4), `LR-M-BATH2-TOEKICK` / `-CAB` / `-TUB-CLG` (E3), `ED-M-BATH2-PSU`,
`ED-M-BATH2-SW-DAY` / `-SW-EVE`, `ED-M-BATH2-RC1`, `BK-M-W3-MID` / `-HIGH`.
**Written:** 2026-10-12; mirror selection and controls amended 2026-10-22 (`mirror_selections.md`).
**Oracle for:** nothing. A **decision record**: no engine module computes melanopic light,
and none is proposed. It follows `notes/TEMPLATE.md`'s shape so each choice can be re-argued.
**Companions:** `notes/bath2_shower.md` (the stall, its glass and the drying fan that shares
the 15'-4" ceiling bay); `notes/interior_selections.md` (the house's 3000 K standard and the
CCT rule this note amends).
**What is asked of the reviewer:** §5's product confirms. Nothing here is ordered until each
one is closed.

> ⚠ **No install-time selectable module anywhere in this room.** Every can and the make-up
> task light uses FIXED-CCT replaceable bulbs, one schedule mark per CCT. Only the halo mirror adjusts, and it
> does so on its own live control (allowed since 2026-10-12). Swapping in a 5CCT DIP-switch
> part to "save a SKU" undoes the rule this room was built on.

---

## 1. The rule change

Until 2026-10-12 the house banned anything not fixed-CCT. The owner narrowed it:

- **Banned:** install-time selectable modules (a 5CCT DIP switch). It is set once, blind, by
  the electrician, and is wrong constantly; a dedicated phosphor also gives better R9.
- **Allowed:** a user-adjustable fixture with a live control (tunable white, RGB). Its type
  records the working CCT in `cct_k` and its range in `source`.

Rewritten in `plan/lighting_types.py` (mark A1), `plan/products_lighting.py` and
`notes/interior_selections.md`.

## 2. The two layers

| layer | control | fixtures | CCT | CRI |
|---|---|---|---|---|
| **day** | `ED-M-BATH2-SW-DAY`, plain toggle, no dimmer | B1 x3: CAN1 (2'-6", 15'-4"), CAN2 over the tub (5'-6", 19'-6"), CAN-SH inside the glass (5'-8", 15'-4"); P3 Karlie 54623CM over the mirror head | 5000 K (P3 may be up to 6000 K) | 90 (cans), **>= 95 with R9 published** (P3) |
| **evening** | `ED-M-BATH2-SW-EVE`, dimmer | B2 CAN-SH-EVE (7'-0", 15'-4"); E3 x3 off `ED-M-BATH2-PSU` | 2700 K | 90 |

The evening wall dimmer controls the warm shower can and three low-voltage runs. The
MHAP2436 mirror has its own touch dimmer at 2700 K, independently powered at full line
voltage. Its lit border and wall glow are both accepted by the owner. The tape runs light
the floor from under the vanity and over-toilet cabinet, plus the ceiling over the tub
(`LR-M-BATH2-TUB-CLG`, replacing the deck-nosing run on 2026-10-22: no LEDs near the floor).
The separate 5000 K Karlie remains the daytime task light.

## 3. Geometry

| item | where | why there |
|---|---|---|
| every can | y = 15'-4" bay (176"-192") or the tub at 19'-6" | CAN1 sat on the y=192" truss chord at 16'-0"; the bay centre clears both chords |
| shower cans and nozzle | x 5'-8" / 6'-4" / 7'-0" | `REG-M-BATH2-DRY-OUT` between them, 3.4" clear of each |
| P4 halo mirror | `W-M-W3`, 24" x 36", 3'-6" to 6'-6", centred on the basin at y=14'-5 3/8" | 30" is all the wall south of the basin centre allows to `W-M-BDN1`'s face; 24" leaves 3" |
| P3 Karlie task light | 80" body bottom, 87 1/2" top, 2" over mirror head | same uid, 54623CM + three 80795-SU bulbs |
| `ED-M-BATH2-RC1` | moved 85" -> 74" along `W-M-W3`, now y=16'-2", 44" | the mirror's glass would have buried it (the BATH1 lesson) |
| mirror backing | `BK-M-W3-MID` (44") and `-HIGH` (72"), stud face 76 3/4" to 107 1/4" | whole bays between the 76" and 108" studs; a free end FAILs `advisory.wall_backing_bearing` |
| E3 runs | toe kick 3" behind the vanity face (46"); `FURN-M-BATH2-CAB`'s front edge at 4'-0" (43.5"); the ceiling over the tub, 2" off `W-M-BA2E` (66", 2026-10-22) | 13.0 ft x 3 W/ft = 39 W on a 60 W supply: 154% (>= 125%), unchanged |
| `ED-M-BATH2-PSU` | ceiling at (2'-6", 16'-8"), in the 192"-208" bay | outside the shower zone, off the extract trunk |

**Controls.** The old single switch on `W-M-BDN1` (box x 17.7"-21.7", uid kept, now
`-SW-DAY`) gains a second gang 4" west for the dimmer. A third gang does not fit:
`ED-M-BATH2-FH-STAT` is at x 9 3/4"-13 3/4", and `D-M-BATH2`'s casing starts about 22", so
the stall fan's countdown timer `ED-M-BATH2-SW-DRY` went on `W-M-W3` at y=16'-8", 6" north of
RC1, outside the shower zone.

## 4. Evening light and sleep

Brown et al. (2022) recommend **<= 10 lux melanopic EDI** at the eye in the 3 h before bed,
and >= 250 lux melanopic EDI in the day. A 2700 K LED's melanopic DER is about 0.45, against
~0.85 for 5000 K. The evening layer is dimmed and indirect, so the eye sees a few tens of
photopic lux at most, i.e. ~10 lux melanopic or less at the dimmer's low end. The day layer
goes the other way: four 5000 K sources and the window. Neither number is computed by the
engine, and neither is graded.

## 5. What is NOT decided here (the confirms)

1. **B1 / B2 SKUs.** Lotus publishes 5000 K and 2700 K in its round LL4R line; the square
   regressed LL4SR was only read at 3000 K. Confirm `LL4SR-50K-WH` and `LL4SR-27K-WH`, or take
   the LL4R round in those CCTs with the white trim.
2. **P3 closed 2026-10-22.** Hinkley Karlie 54623CM with three fixed-5000 K Sunlite
   80795-SU E26 bulbs, CRI 95 and published R9 82. Delivered fixture lumens unpublished;
   bulb output is 3 × 800 source lumens. Verify exact-bulb availability before ordering.
3. **P4 closed 2026-10-22.** Fleurco **MHAP2436** Halo Plus, 24 × 36, 70 W total,
   published ETL certification, own touch dimmer and defogger. Unswitched plug supply on
   the existing GFCI-protected bathroom branch; no wall dimmer or hardwire conversion.
   See `mirror_selections.md` for the outlet and factory controls. CRI unpublished.
4. **E3 tape.** The Armacost COB family in 2700 K, silicone-coated for a damp room.

## Sources

- Brown, T. M. et al. (2022). Recommendations for daytime, evening, and nighttime indoor
  light exposure to best support physiology, sleep, and wakefulness in healthy adults.
  *PLOS Biology* 20(3): e3001571.
- CIE S 026/E:2018 — melanopic EDI and the melanopic daylight efficacy ratio.
- Lotus LED Lights catalog and LL4R listings (lightingsupply.com), read 2026-10-12.
- RAB Radiance vanity listing (bimobject.com); Fleurco MHA3036 Halo listings, read 2026-10-12.
- `houses/catlin/out/model.json`: `canvas_objects` (RM-M-BATH2), `walls` (`W-M-W3` studs).
