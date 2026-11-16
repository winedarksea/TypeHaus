# Second-storey study: two soffit sidewall supplies

`RM-S-STUDY2` takes two 75 cfm grilles on SF-S-DUCT, both 8x6 double-deflection with an
opposed-blade damper (`REG-T-HP-STUDY-SIDE`), both off DU-S-HP-SOUTH (owner, 2026-11-12;
redesigned 2026-11-15).

- **`REG-S-HP-STUDY2`, east face** (owner-approved 2026-10-04; wall-width revision 2026-10-23;
  moved one ladder bay north 2026-11-15): x=21'-8 3/4", y=4'-10 5/8", the bay between the
  50 5/8" and 66 5/8" ladder studs, throwing east across the study. Its 8x6 face runs 94 5/8" to
  100 5/8" AFF on the 10x6's 99 1/8" centreline (storey datum; the finished floor is 1 1/2" up).
  A 6" round `DU-S-HP-STUDY2` leaves the 10x6's east face through the east lining into a
  6"-to-8x6 straight boot.
- **`REG-S-HP-STUDY2-S`, south end face** (2026-11-12, the plant room's former 75 cfm): y=2'-10",
  x=20'-9", ~34" off the south wall and near the line of `D-S-BALCONY` (x=21'-4"). Fed by
  `DU-S-HP-STUDY2-S`, a 6" round off the 10x6's east face at y=3'-3 1/2" (19" south of the east
  collar), ending in the 6"-to-8x6 boot that turns onto the face (`mep.register_reach` 6.0" plan
  / 0" z).

## Topology (2026-11-15)

```
18x8 DU-S-HP-SUP cap (x=19'-6", y=9'-10")
  -> 18" flat-bottomed offset transition (centre 7 1/2" west)
  -> 10x6 DU-S-HP-SOUTH, x=18'-10 1/2", 99 1/8" storey, y=8'-4" to 2'-11 1/2", cap
       east collar y=4'-10 5/8"   -> DU-S-HP-STUDY2   -> REG-S-HP-STUDY2   (75)
       east collar y=3'-3 1/2"    -> DU-S-HP-STUDY2-S -> REG-S-HP-STUDY2-S (75)
       top collar (18'-10", 3'-4") -> DU-S-HP-STUDY-BOOT, 6" rise -> 6x12x6 boot
                                      -> REG-A-HP-STUDY (100)
```

Every collar sits on a straight face (`mep.takeoff_collar_fit`). The rise passes the soffit's
open top into FS-ATTIC's y 32-48 bay, inside its 13 11/16" clear width.

The soffit remains a lined enclosure, not an air plenum.

## Selection basis

Titus 300R is the performance basis, not a purchased product:
https://www.titus-hvac.com/file/1010/300.301Rperf_300_350_2017.pdf (H17, H22). The 8x6 row
at 78 cfm, 300 fpm core and zero spread lists 5/9/16 ft throw at 150/100/50 fpm. The 6" boot
carries 75 cfm at ~382 fpm.

**East grille:** a narrow eastward jet aimed slightly up toward the ceiling, ~6" over the face.

**South grille: a glass wash.** Spread the vanes east-west and aim them up, never straight at
`D-S-BALCONY`'s glass. The jet runs along W-S-C1, past and parallel to `D-S-PLANT`, never into
it. That is what makes the plant room's open-door summer fallback work: with the door held
open, this air reaches the plant room (`plant_room_moisture_budget.md` §6). Throw caveat: the
face is only ~34" off the south wall, so set it spread and up and confirm on site.

Catalogue throw is isothermal; balance each to 75 cfm and set vanes on site. Do not aim either
back toward `D-S-STUDY2`.

## Seasonal trim

One thermostat runs the whole zone and the study's own load is small, so the two OBDs are the
seasonal trim: close the south one down first.

## Branch consequences

DU-S-HP-SOUTH carries 250 cfm (600 fpm in 10x6): 75 east + 75 south + 100 up to the attic
desk. System 1 stays at 750 and the air handler and
its return arithmetic are unchanged. `D-S-STUDY2` is a cased opening with no leaf, so the
study's 150 cfm leaves to the hall (`mep.door_transfer_air` passes the hall group).
