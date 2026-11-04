# Receptacles and devices

Leviton Decora, white (`-W`), tamper-resistant (NEC 2023 406.12) house-wide. Owner decisions
2026-10-27. Applied to the model the same day: types in `plan/device_types.py` (`ED-T-LEV-*`,
`ED-T-LUT-*`), instances retyped, `CKT-SUMP` breaker no longer GFCI, pantry sensor moved inside.
Rating follows the circuit's breaker (15 A circuits get 15 A devices, e.g. `CKT-HA`,
`CKT-BATH2-TUB`, `CKT-LT-*`); device GFCI stays only where the breaker is not GFCI.

**Still open:** box sizes below are standard catalogue envelopes, not a chosen product; the
steel box, raised cover and Matter-switch prices are estimates (`prices.toml`).

## Device schedule

- **Rating matches the circuit.** 15 A breakers: `CKT-RC-ATTIC`, `CKT-HA` (basement utility
  outlet), `CKT-BATH2-TUB` and `CKT-LT-*` (e.g. the closet strip outlet on `CKT-LT-MAIN`).
  `CKT-RC-MAIN`/`-SECOND` stay 20 A because they carry bath lav receptacles (NEC 210.11(C)(3)).
  Kitchen, other basement, laundry, bath and garage circuits are 20 A.
- **Ordinary duplex:** Lever Edge `E5825-W` (20 A); `E5325-W` (15 A) on the 15 A circuits above.
- **GFCI at the breaker by default**, with plain Lever Edge devices. Device GFCI `GFTR2-W`
  (`GFTR1-W` at 15 A) only where more practical: sink-reach outlets on a non-GFCI circuit
  (e.g. `ED-M-BED-RC8`) and the two washlet outlets (`plan/circuits.py` convention).
  - `ED-B-SUMP-RC`: audible-alarm GFCI `GFTA2-W` (NEC 2023 210.8(A)(5)); breaker not GFCI.
  - `ED-S-PLANT-RC1`..`RC5`: weather-resistant GFCI `GFWT2-W` under in-use covers.
- **60 W USB-C PD** `T5836-W`: `ED-M-LIVING-RC13` and `-RC3` only. Deep boxes.
- **Surge duplex** `T5380-W` (20 A TR; replaces the discontinued `T7380-W`): `ED-B-PLAY-N-RC1` behind
  `FURN-B-PLAY-TV`, and `ED-M-BED-RC4` at the desk.
- **Guide-light duplex** `T6525-W`, 12" AFF: new receptacles on the `ST-B2M` half-landings
  (`CKT-RC-BSMT`) and `ST-M2S` (`CKT-RC-MAIN`), plus
  `ED-B-HALL-RC1`. 15 A on a 20 A circuit is allowed (NEC 210.21(B)(3)). Modelled in
  `plan/electrical_stair_ext.py`, all on the landing's north wall: `ED-B-STAIR-RC1` (lower/east
  landing, x 15'-8") and `-RC2` (upper/west, x 12'-1", 7 5/16" higher), and `ED-M-STAIR-RC1`
  (x 14'-6", east of the heat-pump head). `ED-A-STAIR-RC1` is now a standard 15 A duplex
  on the study's east face of `W-A-C1`, 60" from the wall start,
  12" AFF (`CKT-RC-ATTIC`).
- **Mudroom:** `ED-M-MUDROOM-SW` becomes a Leviton `DOS02-LW` PIR occupancy sensor (auto
  on/off), same gang. 150 W LED, neutral optional; three cans and a sconce are well under it.
- **Pantry:** PIR-only Leviton `ODS10-IDW` (10 A, LED-rated, no neutral needed) replaces `ED-M-PANTRY-SW` for `ED-M-PANTRY-LT`, shortest timeout. Inside face of
  `W-M-PAN-E`, in the 8" strip ahead of the shelves: plate centre ~4 1/2" north of the south
  wall finish, >= 2" off the door jamb, box centre ~56" AFF (clears the kitchen-side box at
  46" in the same bay). No ultrasonic, which sees through the open door; mask the lens's
  south half so it sees along the shelves, not the kitchen (the mask is in the type's name,
  `ED-T-LEV-OCC-PANTRY`; no geometry). The kitchen-side 2-gang becomes
  1-gang (`ED-M-KITCH-SW-UC` only).
- **Heavy outlets** (confirm each against the appliance plug): range 14-50R `1450R`, dryer 14-30R `278`, EV 6-20 `T5461-W`, disposer TR single 5-20R `T5020-W`.
- **Kettle:** same as workshop RC1, a 2-gang `T5461-W` + `E5825-W`.

## Switches and dimmers

- **Plain switches:** Lever Edge `E5601-W` single-pole, `E5603-W` 3-way (`5604-2W` 4-way if one
  appears; none today). Fixtures that dim themselves (stair chandelier, mirrors, DC fans) stay
  on plain switches, the dining pendant included (2026-11-03).
- **Dimmers, two Lutron Divas**, each under its own Lutron Claro plate:
  - `ED-B-PLAY-N-SW`, theatre sconces: `DVCL-153P`.
  - `ED-B-SAUNA-SW`, the sauna tape's OMNIDRIVE X: `DVELV-300P`, reverse-phase (on Diode LED's
    OMNIDRIVE X recommended-dimmer list). Never the forward-phase `DVCL-153P`.
- **Plain since 2026-10-31:** `ED-M-BED-SW` / `-SW2` (two `E5603-W`; the bed sconces switch
  at the fixture), `ED-S-SUITE-SW`, `ED-S-STUDY2-NOOK-SW`.
- **Smart control is Matter, local through Home Assistant**, never a vendor cloud. Leviton
  Decora Smart `D315S-1BW` (the discontinued D215S's successor), Matter out of the box:
  commission from the strap QR straight into HA, no My Leviton account, block the devices'
  internet at the router. Neutral required. 15 A relay, 3 A LED (about 360 W), 1/3 HP.
- **Smart only where it pays (owner, 2026-11-03): 11 relays, no companions, no Matter dimmer.**
  Exterior: `ED-M-ENTRY-SW`, `ED-G-EXT-SW`, `ED-M-PORCH-SW` (fan-light + sconce, 33 W; set the
  fan off at its own control), `ED-M-PORCH-FLOOD-SW` (20 W). Plant photoperiod:
  `ED-S-PLANT-SW-TIMER` (two grow bars + spot, 185 W). Gym routines: `ED-B-GYM-SW` (cans,
  26 W), `-SW2` (four T8 strips, 144 W). Lounge: `ED-M-LIVING-SW-ACCENT`, `-SW-DAY`,
  `ED-M-LIVING-SW`, `ED-M-KITCH-SW-PEN`. Every load is well under 360 W. Scenes:
  [smart_home.md](smart_home.md).
- **Everything else is a plain paddle.** A controller-fed run (E4, E6, W) dims and colours at
  its GL-C-001P, so its paddle is a hard off left on: `ED-M-LIVING-SW-COVE`, `ED-G-SOFFIT-SW`,
  the hall 3-ways `ED-S-HALL-SW`/`-SW2`. The IKEA drivers need no relay: `ED-M-KITCH-SW-UC`
  and `ED-M-CLOSET-SW` are plain hard offs. Also plain: `ED-M-DINING-SW`, `ED-M-KITCH-SW`,
  `ED-M-LAUNDRY-SW`, `ED-M-BATH2-SW-EVE`, and the stair 3-ways `ED-B-STAIR-SW`/`ED-M-STAIR-SW`.
- **Bath night lights** are the vanity receptacle's dusk guide light (2026-11-03): GFNL2-W
  where the device is the GFCI, the plain `T6525-W` where the breaker is.
- **Exception:** `ED-M-PANTRY-LT` stays on its `ODS10-IDW` occupancy sensor (not Matter).
- **BATH2 shower fan** `ED-M-BATH2-SW-DRY`: Lutron Maestro `MA-T51` countdown, 5-60 min.

## Workshop (west wall bench)

RC1 and RC2 stay at their stations, 42" AFF over the 34" benches, surface-mounted on concrete.

- **RC1** (`CKT-WORKSHOP-240`, panel 2 positions 17/19, two-pole common-trip GFCI): a 2-gang box
  with a 6-20R ([`T5461-W`](https://leviton.com/products/t5461-w), probable) beside a 5-20R
  duplex. Bring both hots, neutral and ground. Both voltages share the 20 A breaker; 4,800 VA is
  a planning allowance, not a nameplate. Its schematic envelope gets replaced with the real box
  projection once the hardware is chosen.
- **RC2** (`CKT-RC-BSMT`): quad, as a 2-gang box with two TR 5-20R duplexes. Four sockets add
  no capacity.

The kitchen kettle outlet (`CKT-KETTLE`) uses the same arrangement; its 120 V half also needs a
neutral.

## Garage (NEC 210.52(G)(1), simplified 2026-10-30)

The 16' door makes two vehicle bays; each needs a receptacle no higher than 5'-6"
(`code.NEC_210_52_G_garage_receptacles` grades it). The bench group moved to the south end of
`W-G-W` beside `ST-G-SERVICE`, 2'-2" north of the stair foot; everything else is on `W-G-S`,
near the feeder's stub-up at x 16'-0".

- **Bench group, `W-G-W`** (bench centre y 52'-2 5/8"): `EQ-G-HEATER` over the bench centre
  (180" from the NW corner), `ED-G-RC-W` (20 A duplex, 48" AFF, 156") and `ED-G-RC-240`
  (single 6-20R, 48" AFF, 204"), mid-bay either side of it.
- **West bay: `ED-G-RC-W`**, **east bay: `ED-G-RC-E`** (`W-G-S`, x 25'-0", 48" AFF). Both are on
  `CKT-RC-GARAGE`, the 120 V 20 A GFCI circuit 210.11(C)(4) asks for, and nothing else is: "no
  other outlets". Lights and the heater are elsewhere (`CKT-LT-MAIN`, `CKT-GAR-HEAT`).
- **Opener outlet `ED-G-GDO-RC`** (ceiling, 9'-11 1/4") is on `CKT-LT-MAIN` (owner, 2026-10-30),
  on the load side of `ED-G-GDO-GFCI`, a Leviton GFRBF-W blank-face GFCI beside `ED-G-SW`.
  210.8(A)(2) wants it GFCI with a reset in reach; the blank face protects only the opener, so a
  trip never takes the lights.
- **`ED-G-RC-240`: one 6-20R alone on `CKT-GAR-240`** (2-pole 20 A GFCI, 210.8(A)(2)). Two hots
  and ground, no neutral, no 120 V device; it is not a counting receptacle. It was a 6-20R
  beside a 5-20R duplex, which put a 210.52(G) outlet on a circuit with another outlet and
  needed a neutral.
- **EVSE hardwired.** The Grizzl-E Smart manual documents removing the 14-50P. `ED-G-EV-1450`
  (kept tag, centre of the south wall's EV station) is now the 240 V junction box
  `ED-T-EVSE-JB` behind the unit; `CD-B-GARAGE`/`CD-B-GAP-EV` still end on it. With no
  receptacle, 210.8(A)(2) and 625.54 do not apply; the charger's own CCID protects. 625.43 wants
  no disconnect (240 V split-phase is 120 V to ground, under 60 A). `CKT-EV-1450` stays a plain
  50 A 2-pole, 40 A charge.
- **Option, not taken: drop the 6-20R.** The notes call it a general-use point and backup
  charger, not dispensable. Removing it saves a 2-pole GFCI breaker, a device and ~25 ft of
  12/2 and frees panel-2 slot 13.

## Boxes and covers

Boxes are no longer on the types. The house's `BoxStandard` derives them from the face each
device lands on (`plan/device_boxes.py`, decision #93; method, fill and costs in
[basement surface wiring](basement_surface_wiring.md)). On basement concrete that is a RACO
232 4" square box under a raised Decora cover (1- or 2-Decorator), fed by NM in a derived
3/4" EMT sleeve. RC1 and RC2 are fed instead by 3/4" EMT + THHN drops from the bench pull
box on the 1" CD-B-WORKSHOP trunk. The kettle's `ED-T-LEV-620-FLUSH` is flush in drywall.

- **Exterior:** clear `5980-UCL` extra-duty in-use cover, which closes over a plugged-in cord
  through its cord ports. `ED-M-FRONT-RC1` (north face of `W-M-N2`, x 16'-6", on the entry
  bridge) and `ED-M-REAR-RC1` (south face of `W-M-S2`, x 24'-7"), 18" AFF, WR GFCI `GFWT2-W` on
  `CKT-RC-MAIN` (NEC 210.8(A)(3), 210.52(E)).

## Product links

| Use | Model |
|---|---|
| Duplex, Lever Edge | [E5825-W](https://leviton.com/products/e5825-w) 20 A, [E5325-W](https://leviton.com/products/e5325-w) 15 A |
| GFCI | [GFTR2-W](https://leviton.com/products/gftr2-w), [GFTR1-W](https://leviton.com/products/gftr1-w) |
| Audible GFCI | [GFTA2-W](https://leviton.com/products/gfta2-w) |
| WR GFCI | [GFWT2-W](https://leviton.com/products/gfwt2-w) |
| USB-C 60 W | [T5836-W](https://leviton.com/products/t5836-w) |
| Guide light | [T6525-W](https://leviton.com/products/t6525-w) |
| Surge | [T5380-W](https://leviton.com/products/t5380) |
| Single 5-20R, TR | T5020-W |
| 6-20R | [T5461-W](https://leviton.com/products/t5461-w) |
| In-use cover | [5980-UCL](https://leviton.com/products/5980-ucl) |
| Occupancy sensor, mudroom | [DOS02-LW](https://leviton.com/products/dos02-lw) |
| Occupancy sensor, pantry | [ODS10-IDW](https://leviton.com/products/ODS10-IDW) |
| Countdown timer, BATH2 fan | Lutron MA-T51 |
| Switch, Lever Edge | [E5601-W](https://leviton.com/products/e5601-w) 1-pole, [E5603-W](https://leviton.com/products/e5603-w) 3-way |
| Dimmer, LED cans/sconces | Lutron DVCL-153P |
| Smart switch, Matter | [D315S-1BW](https://www.leviton.com/products/d315s-1bw) |
| Dimmer, ELV (sauna) | Lutron DVELV-300P |
| GFCI with guide light, bath vanities | [GFNL2-W](https://leviton.com/products/gfnl2-w) |
| Range 14-50R | [1450R](https://leviton.com/products/1450r) |
| Dryer 14-30R | [278](https://leviton.com/products/278) |
