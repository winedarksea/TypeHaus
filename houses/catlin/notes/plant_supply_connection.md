# Plant-room heat-pump supply connection

> **SUPERSEDED 2026-11-12.** RM-S-PLANT is sealed and takes no System 1 air; `REG-S-HP-PLANT`,
> `DU-S-HP-PLANT` and the RH damper are deleted and the 75 cfm went to Study 2's south grille
> (`system1_study_supply.md`). Kept as a record; see `plant_room.md`.

Revised 2026-11-12 (owner: sidewall supply over the door, no service hatch). Replaces the
ceiling boot at x=14'8", y=3'3" with its 12x6 ZD damper, fabricated boot and PVC hatch.

`REG-S-HP-PLANT`: 75 cfm, a **TRUaire A220V 12X06** (no OBD) high sidewall grille on
`W-S-C1`'s plant face at y=41", face centre 99 1/8" storey (219 1/8" absolute), throwing
west down the room. It sits in the clear cripple bay above `D-S-PLANT`'s header: head
cripples at y=33" and 49" leave 14 1/2", the 12" opening has 1 1/4" each side; header top
92 1/2", grille face 95 1/4"..103", top-plate underside 105 1/8".

## Feed

`DU-S-HP-PLANT`: stock 6" round galvanized, a take-off west off `DU-S-HP-SOUTH-RISE`'s last 2"
inside `SF-S-DUCT` at the riser's own 99 1/8" centreline, through the soffit's west lining and
the wall's hall face into the cripple bay, 382 fpm at 75 cfm. The stock 6x12x6 end boot
(Imperial GV0671, DuctStandard) turns it into the register box. The riser carries 250 =
`REG-S-HP-STUDY2` 75 + this 75 + 100 to `DU-S-HP-SOUTH`, now a 12" stub capped past the attic
study's take-off (it used to run 4'4" west over the plant room at 175 cfm).

## Damper and service

The RH interlock is a **6" 24 VAC spring-return damper (EWC 6RSD class, not read)** in the
box's collar behind the grille, reached by pulling the grille, the way the extract's 4" damper
is reached by pulling its valve. **There is no hatch**: nothing is opened in the liner, and
the ceiling's membrane has no penetration for this terminal. What the model does not show:
the damper's body length and actuator size (confirm on the submittal), and whether a hand
reaches the actuator through a 12x6 opening in a 5 1/2" cavity. If it does not, the fallback is
the same damper at the take-off inside the soffit with a 12x12 access panel in the hall
soffit's underside, which is not drawn.

## Humid-room seal

Flanged box, flange taped with butyl to the Class I membrane, mastic round the collar, the
3/4" furring and PVC panel cut to the box (the extract boot's detail, `plan/mep_erv_l2.py`).
The duct itself is behind the membrane, on the dry hall side.

## Throw

Not catalogued: no throw for the A220V at 12x6 is recorded in this house's notes, and none was
read, so none is claimed. Core velocity at the 12x6 nominal opening is 150 fpm. The far wall is 17' off;
verify the vane setting on site against the plants and the south glass. Do not aim it at
the door.

Sources: [TRUaire A220 family](https://rectorseal.com/hvac/a220-adjustable-double-deflection/).
