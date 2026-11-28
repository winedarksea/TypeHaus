# Attic air handler access (IMC 306.3) — hand-worked basis

**House:** catlin
**Structure:** `EQ-S-HP1-AH` (System 1 air handler) in `RM-A-EAST-UNFIN`, reached from `D-A-STUDY`.
**Written:** 2026-11-27, by hand, from plan-source dimensions, before comparing with the check.
**Oracle for:** `checks/mep/appliance_access.py`, reported by `mep.attic_appliance_access`;
reproduced by `tests/test_attic_appliance_access.py`.
**Companions:** `notes/flexx_ultra_geometry.md` — the cabinet and its ports;
`electrical.equipment_space_lighting` grades the light and switch of IMC 306.3.1.
**What is asked of the reviewer:** section 5, the route length (it is the clause with the
least margin, 25 in. under 20 ft).

> Code text: the 2018 IMC section 306.3 as read on UpCodes (Minnesota Rules ch. 1346 adopts
> chapters 2-15 of the 2018 IMC in part 1346.0050). Part 1346.0306 amends only 306.5 (roof
> equipment), so 306.3 is the model code's own. Paraphrase below, not the text.

---

## 1. The clauses, in the form graded

| clause | limit |
|---|---|
| opening | at least 20 x 30 in., and large enough to remove the largest appliance |
| passageway | at least 30 in. high, 22 in. wide, large enough to remove the largest appliance |
| length | at most 20 ft on the centreline; 50 ft where 6 ft high and 22 in. wide throughout |
| flooring | continuous and solid, at least 24 in. wide along the passageway |
| service space | level, at least 30 in. deep x 30 in. wide, at the side that needs access |

The service space is measured from the appliance's base: the cabinet, its pad, and the
refrigerant stub piped to the front face where it crosses the Gree 24 in. service zone.

## 2. Inputs, from plan source

| item | source | value |
|---|---|---|
| deck top, `FS-ATTIC` | `storeys/attic.py` base_elevation 20'-0.75" | 240.75 in. |
| room face, south (door wall) | `W-A-SN` axis y = 9'-0" + half of a 4.5 in. wall | y = 110.25 in. |
| door `D-A-STUDY` centre | `N-A-C2` x = 18'-0" + 22.25 in. along `W-A-SN` | x = 238.25 in. |
| door clear passage | `DT-INT-BOOKCASE30` `clear_passage_width` 24.25; RO 82 less sill and head | 24.25 x 80.5 in. |
| cabinet | `mep_hvac.py` position (272.25, 339.1875), 43.5 x 21.25 in., rotation 0 | x 250.5-294, y 328.5625-349.8125 |
| cabinet height | mount 7.3125 in. + 18.125 in. body | 18.125 in. high |
| pad `SL-A-HP1-PLATFORM` | 3 in. past the cabinet each way, 4.25 in. thick | y from 325.5625 |
| service side | rotation 0: front south; Gree zone 24 in. deep | zone x 250.5-294, y 304.56-328.56 |
| lineset stub | `PR-A-RFG-HP1`: x = 279.75, drop at y = 322, bundle 3.125 in. | front extent y = 322 - 1.5625 = 320.4375 |
| floor register `REG-A-HP-EAST` | 19'-4", 11'-4", flange 13.375 x 7.375 in. | x 225.3125-238.6875, y 132.3125-139.6875 |
| roof | gable 6:12, ridge x = 18'-0"; rafter 11.875 in.; lining 5/8 in. gypsum | see 4 |

The lineset stub is where the base's front is. Its drop is the line's own connection to the
front ports, 8 in. inside the Gree 24 in. zone; measuring from the cabinet face instead
would put a 3 in. pipe in the first 8 in. of the square, so the base is taken as piped.

## 3. Service space

Base front: y = 320.4375 in. (the stub; the pad's edge at 325.56 is behind it).
Square: y 290.4375-320.4375, 30 in. wide, centred at x between 265.5 and 279 (zone edge
+ 15 in. to zone edge - 15 in.). Nothing stands in it: the nearest items are the stub itself
(on its edge), the condensate line `PR-A-COND-HP1` at x = 299.5 (19 in. beyond) and the disconnect on
the west wall (x 219-223, 48 in. up). Floor: one deck, no step. **Clear, 30 x 30 in.** The
nearest centre to the door is x = 265.5, y = 305.4375 (G).

## 4. Headroom

Deck plane of the roof: z(x) = 363.53 - 0.5 (x - 216) in., the one number read from the
model (`ridge_z_m`); it agrees with the plan: at the plate x = 432 the rafter underside is
255.53 - 13.28 = 242.25 in., 1.5 in. under the plate top (240.75 + 3), the birdsmouth seat.
Underside at x = 265.5: 363.53 - 24.75 = 338.78; less the rafter's plumb depth
11.875 x sqrt(1 + 0.5^2) = 13.28 -> 325.50; less the lining 0.625 x 1.118 = 0.70 -> 324.80.

Headroom at G: 324.80 - 240.75 = **84.05 in.**, and it falls with x, so this is the lowest
point of a route whose largest x is 265.5. Headroom is 72 in. out to x = 289.6, so the whole
route is also 6 ft high (the 50 ft exception would apply; it is not needed).

## 5. Route

Start D = (238.25, 110.25), on the room face at the door. West of the door the wall nook is
45.5 in. wide (x 219.25-264.75). The only thing between D and G is the flush floor register,
which is an opening in the flooring: a 24 in. wide floor needs the path 12 in. off it.
The grille's south-east corner is C = (238.6875, 132.3125); D to C is 22.07 in., G to C is
175.19 in.

Shortest path, wrapped on the east of the 12 in. circle about C:

| leg | working | in. |
|---|---|---|
| D to tangent | sqrt(22.07^2 - 12^2) | 18.52 |
| arc | angle 29.2 deg x 12 | 6.1 |
| tangent to G | sqrt(175.19^2 - 12^2) | 174.78 |
| path D to G | | 199.4 |
| square's near half | 30 / 2 | 15.0 |
| **opening to base** | | **214.4 in. = 17.9 ft** |

Limit 20 ft = 240 in.; margin 25.6 in. The check's path starts 11 in. inside the face (its
disc rule for the first point) and reads 214.9 in.; half an inch of difference is that lead-in.
Width: a 22 in. disc fits wherever the path runs: it is the nook (45.5 in.) and then open deck
to G (the room is 207 in. wide); the register is the only obstruction and the path clears it by
12 in. Flooring: no void within 12 in. of the path except the register itself.

## 6. Opening and removal

Opening 24.25 x 80.5 in. against 20 x 30 in.: passes. Largest appliance is the cabinet,
43.5 x 21.25 x 18.125 in.: carried on its end it presents 21.25 x 18.125 in., which fits the
door (24.25 wide) with 3 in. to spare and the passageway (22 in. wide, 84.05 in. high) with
0.75 in. to spare in width.

| quantity | hand | check |
|---|---|---|
| path length, opening to base | 214.4 in. (17.9 ft) | 214.9 in. (17.9 ft) |
| lowest headroom on the route | 84.05 in. | 84.1 in. |
| passageway width | at least 22 in. (22 in. disc fits) | route exists on a 22 in. disc |
| flooring width | at least 24 in. | route exists 12 in. off every void |
| service space | 30 x 30 in. clear | clear |

## 7. What is NOT graded here

- The door leaf. D-A-STUDY is an 8.25 in. deep bookcase door that swings into the room; its
  open leaf stands along the west side beside the register and is not subtracted.
- Exception 1 (appliance serviced and removed through the opening alone).
- 306.3.1: the switched light at the opening and the receptacle at the appliance
  (`electrical.equipment_space_lighting`, NEC 210.70(C)).
- The stair up to the study, and moving the cabinet along it.
- The Gree 24 in. zone against the lineset stub (`mep.air_handler_coordination`).

## Sources

- 2018 International Mechanical Code section 306.3 (via UpCodes), as adopted by Minn. R. 1346.0050.
- Minn. R. 1346.0306 (amends 306.5 only).
- `houses/catlin/plan/mep_hvac.py`, `mep_linesets.py`, `mep_registers_attic.py`, `storeys/attic.py`, `storeys/main.py`.
