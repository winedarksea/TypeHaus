# Second-storey study: two soffit sidewall supplies

`RM-S-STUDY2` takes two 75 cfm grilles on SF-S-DUCT, both 8x6 double-deflection with an
opposed-blade damper (`REG-T-HP-STUDY-SIDE`), both off DU-S-HP-SOUTH-RISE (owner, 2026-11-12).

- **`REG-S-HP-STUDY2`, east face** (owner-approved 2026-10-04; wall-width revision 2026-10-23):
  x=21'-8 3/4", y=3'-7 1/2", throwing east across the study. Its 8x6 face runs 94 5/8" to 100 5/8"
  AFF on the soffit leg's 99 1/8" centreline (storey datum; the finished floor is 1 1/2" up).
  A drawn 6" boot `DU-S-HP-STUDY2` leaves the riser through the east lining.
- **`REG-S-HP-STUDY2-S`, south end face** (2026-11-12, the plant room's former 75 cfm): y=2'-10",
  x=20'-9", ~34" off the south wall and near the line of `D-S-BALCONY` (x=21'-4"). Fed by
  `DU-S-HP-STUDY2-S`, a 6" round off the riser's last bay just south of the east boot, ending
  in the 6"-to-8x6 boot that turns onto the face (`mep.register_reach` 3.7" plan / 0" z).

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

DU-S-HP-SOUTH-RISE carries 250 cfm: 75 east + 75 south + 100 on to the attic desk on
DU-S-HP-SOUTH, a stub capped past the riser. System 1 stays at 750 and the air handler and
its return arithmetic are unchanged. `D-S-STUDY2` is a cased opening with no leaf, so the
study's 150 cfm leaves to the hall (`mep.door_transfer_air` passes the hall group).
