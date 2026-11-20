# Porch fan box (ED-M-PORCH-FAN), 2026-11-20

Owner-approved: a weatherproof, fan-rated box screwed under a bare balcony joist.

## Where it hangs

- The porch has no ceiling. Its overhead is `FS-SG-BALCONY`: bare 2x12 KDAT joists at 12" o.c.
  running E-W, under the watertight aluminium plank. Joist `joist-0-005` sits on y = -5'-5 1/4",
  with its underside at about 8'-11" above datum.
- The fan was at y = -5'-6", on the joist's south edge. It moved **3/4" north**, onto the joist
  centreline, so the bracket's screws go into the middle of the 1 1/2" face. The mount dropped
  1 1/2" (7'-5" -> 7'-3 1/2"), so the canopy hangs from the box face and not from the joist.
- How the engine reads it (decision #140): a ceiling fixture with no lined face over it takes a
  `surface` box on the underside of the framing member whose footprint covers its point
  (`resolve/remote_feed_box.member_under`). A point in a joist bay gets no box and stays UNKNOWN
  in `box_fill`.

## Location class

The plank is watertight, so under NEC Art. 100 the porch is a roofed open porch, which is a
**damp** location. It is still exposed to wind-driven snow, which is why the fan is wet-listed
(`PROD-CRAFTMADE-FXL60DGT3`). The box gets the same margin: NEMA 3R, threaded hubs with
closure plugs, and an included rain collar. 314.15 asks for this in damp locations, and
314.27(C) asks for a box listed for fan support.

## Product: Bell (Hubbell) PRCF57550BZ, Outdoor Comforts

The basis is Hubbell's spec sheets:

- <https://hubbellcdn.com/specsheet/BELL-PRCF57550BZ-SPEC-EN.pdf> (REV 8/2026)
- <https://hubbellcdn.com/specsheet/PRCF57550BZ.pdf> (2019)
- the gray twin's sheet, BELL-PRCF57550GY-SPEC-EN

| | |
|---|---|
| Body | Polycarbonate, with an integrated galvanized steel support bracket; UL Listed; NEMA 3R |
| Size | 4.28" wide, 1.5" deep, 7.5" over the bracket |
| Capacity | 16 (the unit is not printed; we read it as in3) |
| Fan rating | 70 lb |
| Fixture rating | 150 lb |
| Mounting | Surface; parallel, perpendicular or 45 deg to a joist |
| Entries | Five 3/4" threaded entries, four plugs and three 3/4-1/2 reducers; no internal clamps |
| Accessories | Rain collar included ("required for use with weatherproof fan") |
| Retail | Menards p-12148367795339860, Lowe's 1002540966 |

Bronze was chosen to go with the Dark Graphite fan. A gray (-GY) and a white (-WH) are also
made.

Fan: Craftmade FXL60DGT3 spec sheet
(<https://data.craftmade.com/CraftPIM/ProductData/Specs/FXL60DGT3_SpecSheet.pdf>) gives
20.06 lb against the 70 lb rating, and a 5.98" canopy that covers the 4.28" box.

## Fill oracle (NEC 314.16)

The box is through-fed with 12/2 on CKT-LT-MAIN:

- 4 insulated conductors at 2.25 = 9.00
- 1 EGC allowance = 2.25
- no clamps, no yoke (a luminaire)
- total **11.25 in3** in 16.0 in3

`haus check` reports the same: "11.25 in³ of through-fed 12 AWG in 16 in³".

## Rejected

| Option | Why |
|---|---|
| RACO 929, Carlon BH525H / B620KR-CFB bar hangers | Need 16-24" joist spacing; these joists are 12" o.c. (10 1/2" clear) |
| Arlington FB415 | Saddle box set in 1/2-5/8" drywall, and only 10.3 in3; there is no board here |
| FBS415 (steel) | Fits under a joist, but it is an indoor box |
| FB442 side-mount | Would move the fan 6" into the bay; the box face is not weatherproof |
| RACO 295 pancake | About 6 in3; through-fed 12/2 needs 11.25 |

## Open

- The capacity unit is not printed on the sheet. Read the marked volume on the box at order.
- Hubbell store item 19640579, the owner's link, refused automated fetch. Its colour code is
  not confirmed; 19640580 is the gray PRCF57550GY.
