# Receptacles and devices

Leviton Decora, white (`-W`), tamper-resistant (NEC 2023 406.12) house-wide. Owner decisions
2026-10-27; not yet applied to the model.

## Device schedule

- **Rating matches the circuit.** `CKT-RC-ATTIC` is the only 15 A general circuit;
  `CKT-RC-MAIN`/`-SECOND` stay 20 A because they carry bath lav receptacles (NEC 210.11(C)(3)).
  Kitchen, basement, laundry, bath and garage are 20 A.
- **Ordinary duplex:** Lever Edge `E5825-W` (20 A); `E5325-W` on `CKT-RC-ATTIC`.
- **GFCI at the breaker by default**, with plain Lever Edge devices. Device GFCI `GFTR2-W`
  (`GFTR1-W` at 15 A) only where more practical: sink-reach outlets on a non-GFCI circuit
  (e.g. `ED-M-BED-RC9`) and the two washlet outlets (`plan/circuits.py` convention).
  - `ED-B-SUMP-RC`: audible-alarm GFCI `GFTA2-W` (NEC 2023 210.8(A)(5)); breaker not GFCI.
  - `ED-S-PLANT-RC1`..`RC5`: weather-resistant GFCI `GFWT2-W` under in-use covers.
- **60 W USB-C PD** `T5836-W`: `ED-M-LIVING-RC13` and `-RC3` only. Deep boxes.
- **Surge duplex** `T5380-W` (20 A TR; replaces the discontinued `T7380-W`): `ED-B-PLAY-N-RC1` behind
  `FURN-B-PLAY-TV`, and `ED-M-BED-RC4` at the desk.
- **Guide-light duplex** `T6525-W`, 12" AFF: new receptacles on the `ST-B2M` half-landings
  (`CKT-RC-BSMT`), `ST-M2S` (`CKT-RC-MAIN`) and the `ST-S2A` head (`CKT-RC-ATTIC`), plus
  `ED-B-HALL-RC1`. 15 A on a 20 A circuit is allowed (NEC 210.21(B)(3)). Wall stations open.
- **Mudroom:** `ED-M-MUDROOM-SW` becomes a Leviton `DOS02-LW` PIR occupancy sensor (auto
  on/off), same gang. 150 W LED, neutral optional; three cans and a sconce are well under it.
- **Pantry:** PIR-only Leviton `ODS10-IDW` (10 A, LED-rated, no neutral needed) replaces `ED-M-PANTRY-SW` for `ED-M-PANTRY-LT`, shortest timeout. Inside face of
  `W-M-PAN-E`, in the 8" strip ahead of the shelves: plate centre ~4 1/2" north of the south
  wall finish, >= 2" off the door jamb, box centre ~56" AFF (clears the kitchen-side box at
  46" in the same bay). No ultrasonic, which sees through the open door; mask the lens's
  south half so it sees along the shelves, not the kitchen. The kitchen-side 2-gang becomes
  1-gang (`ED-M-KITCH-SW-UC` only).
- **Heavy outlets** (confirm each against the appliance plug): EV 14-50R `1450W`, range
  14-50R `1450R`, dryer 14-30R `278`, EV 6-20 `T5461-W`, disposer TR single 5-20R `T5020-W`.
- **Kettle:** same as workshop RC1, a 2-gang `T5461-W` + `E5825-W`.

## Switches and dimmers

- **Plain switches:** Lever Edge `E5601-W` single-pole, `E5603-W` 3-way (`5604-2W` 4-way if one
  appears; none today). Fixtures that dim themselves (dining pendant, stair chandelier, mirrors,
  DC fans) stay on plain switches.
- **Dimmers, two Lutron Diva only**, each under its own Lutron Claro plate:
  - `ED-B-PLAY-N-SW`, theatre sconces: `DVCL-153P`.
  - `ED-M-BED-SW` / `-SW2`, main bedroom cans: one `DVCL-153P` + one `E5603-W` 3-way.
- **Become plain switches:** `ED-M-BED-LAMP-SW`, `ED-S-SUITE-SW`, `ED-S-STUDY2-NOOK-SW`,
  `ED-M-LIVING-SW-DAY`.
- **Smart control is Matter, local through Home Assistant**, never a vendor cloud. Leviton
  Decora Smart 2nd Gen on Wi-Fi: commission from the strap QR straight into HA, no My Leviton
  account, block the devices' internet at the router. Matter is enabled by a firmware update
  out of the box, so plan one app session before cutting them off. Neutral required.
- **Every LED tape gets a Matter switch on the 120 V side of its driver**, and either the
  paddle or HA turns it on or off (last command wins; no lockout). `D215S-1BW` is a 15 A
  relay, 600 W LED; the OMNIDRIVE X has no minimum load, so it is happy behind a relay.
  - `ED-M-KITCH-SW-UC` (kitchen tape), `ED-M-BATH2-SW-EVE` (toe kick, cabinet, tub tape),
    `ED-M-LAUNDRY-SW` (PureEdge), `ED-M-CLOSET-SW` (PAX strips), `ED-M-LIVING-SW` (coves +
    cans): `D215S-1BW`.
  - 3-ways with tape: `ED-S-HALL-SW`/`-SW2` (gap strip + cans) and `ED-B-STAIR-SW` /
    `ED-M-STAIR-SW` (rail strip + cans): one `D215S-1BW` + one Leviton wired companion
    (`DD0SR-DLZ` class, confirm).
  - `ED-B-SAUNA-SW`: `D2ELV-1BW`, Matter, reverse-phase by default, replacing the Diva
    `DVELV-300P`. Confirm HA sees it as a dimmer and not only on/off.
  - **Exception:** `ED-M-PANTRY-LT` stays on its `ODS10-IDW` occupancy sensor (not Matter).
- **Garage soffit** `ED-G-SOFFIT-SW` (eave + rake runs, ~215 W, 120 V integral drivers):
  `D215S-1BW` in the existing third gang, scheduled in HA. The paddle is spare, not required.
- **Grow lights** `ED-S-PLANT-SW-TIMER` (two 6' tubes + spot, non-dimmable): `D215S-1BW`,
  scheduled in HA.
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

## Boxes and covers

- **Basement concrete walls:** EMT surface conduit to 4x4 steel boxes with raised Decora
  industrial covers (2-gang at RC1/RC2). Size for fill and device depth; bond box and raceway.
- **Exterior:** clear `5980-UCL` extra-duty in-use cover, which closes over a plugged-in cord
  through its cord ports.

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
| Smart switch, Matter | [D215S-1BW](https://www.leviton.com/en/products/d215s-1bw) |
| Smart dimmer, ELV, Matter | [D2ELV-1BW](https://www.leviton.com/en/products/D2ELV-1BW) |
| EV 14-50R | [1450W](https://leviton.com/products/1450w) |
| Range 14-50R | [1450R](https://leviton.com/products/1450r) |
| Dryer 14-30R | [278](https://leviton.com/products/278) |
