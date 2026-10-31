# Smart home: local-only, Home Assistant first

**Decided 2026-10-30** (owner brief, `plans/TODO.md`; owner 2026-10-29: Matter is nice to have,
not required; Zigbee, Z-Wave and Wi-Fi are all fine, and a dongle can be added as needed).
Every connected device runs in Home Assistant (HA) with no vendor cloud at runtime. One app
session at setup is allowed. Instances: `plan/smart_home.py`; types and products:
`plan/smart_home_types.py`. Product facts were read 2026-10-30 and each `source=` names its page.

## Rules

1. **Local first.** A device reaches HA through Matter, a core integration with a local IoT
   class, ESPHome, Z-Wave JS or ZHA. A HACS integration is allowed only where no core path
   exists, and this note names it: OCPP for the EVSE (`lbbrhzn/ocpp`), and the EG4 web
   monitor in local Modbus mode.
2. **Radios.**
   - The HA Connect ZBT-2 runs **Thread** (Sense Pro lock, SmartWings shades). It cannot run
     Thread and Zigbee at once (Nabu Casa FAQ), so Zigbee (wanted since 2026-10-31: the
     GL-C-001P controllers and the PIRs) runs on a second dongle, a Zigbee coordinator on ZHA.
   - A Z-Wave 800 LR stick serves the leak valve and its sensors.
   - No vendor hubs: no MyQ, no DIRIGERA, no Reolink Home Hub, no YoLink hub.
3. **Safety stands alone.** These work with HA down; HA observes them and may notify:
   - the alarm interconnect;
   - the leak shutoff, through its wired probe;
   - the sump alarm;
   - the sauna controller.

   HA never closes a safety loop that the device does not already close itself.
4. **Network.**
   - An IoT VLAN whose WAN is blocked after setup.
   - HA has a leg on that VLAN for mDNS and IPv6 (Matter needs both).
   - Local NTP is allowed.
   - The PoE switch in `ED-B-NET-PATCH` budgets at least 150 W (E-603 totals the draw), and
     HA must be able to turn a port's PoE off locally (rule 6). Named by capability only.
   - The router is named by capability only (VLANs, per-VLAN firewall, mDNS reflector),
     never by brand.
5. **These never join Wi-Fi.**
   - LG ThinQ appliances: LG's HA integration is cloud-only.
   - The Broan hood.
   - The Harvia sauna: remote start of a 9 kW heater is a safety question, not a feature.
6. **On battery, HA sheds the cameras** (owner, 2026-10-30). When the EG4 reports the grid
   gone, HA turns off the PoE ports of `ED-M-DOORBELL`, `ED-M-CAM-PORCH` and
   `ED-BW-CAM-CANOPY`, and turns them back on when the grid returns. The APs stay up. During
   an outage there is no doorbell and no recording. Modelled as `CKT-HA.backup_shed_poe`; it
   is what lets one strong solar day per 48 h carry the always-on tier
   ([backup_power.md](backup_power.md)). The water heater's Heat-Pump-Only switch is the same
   kind of automation.

## Register

"Setup cloud" means a one-time app session; "fallback" is what still works with HA down.

| Device | Model ref | Product | Transport, HA integration (IoT class) | Setup cloud | Fallback | Open verification |
|---|---|---|---|---|---|---|
| Entry deadbolt | `D-M-ENTRY` hardware | Schlage Sense Pro BE889WB 622 | Matter/Thread via ZBT-2 (local push); PIN codes local | none | keypad works offline; USB-C jumpstart | Century trim is bundle-only: check the 622 escutcheon against the Latitude lever |
| French-door locks | `DT-*` French hardware | Schlage BE365 | not connected | none | keyed keypad | none |
| Doorbell | `ED-M-DOORBELL` | Reolink D340P, PoE | core `reolink` (local push) | one Reolink app session | the chime rings locally | rated to 14 F, accepted; talk is app-only |
| Backyard camera | `ED-M-CAM-PORCH` | RLC-833A class 4K turret | core `reolink` (local polling/push) | none | records to microSD | RLC-833A is discontinued: buy the current turret |
| Canopy camera | `ED-BW-CAM-CANOPY` | Reolink Duo 3 PoE | core `reolink` | none | records to microSD | none |
| Garage opener | `APPL-G-GDO` | LiftMaster 8550W (Security+ 2.0) + ratgdo32 | ESPHome (local push) | none; MyQ never set up | wall button and remotes | head size; the manual's headroom figure |
| Smoke/CO/heat | `AL-*` (13) | Kidde hardwired interconnect | relay dry contacts into an isolated input in `ED-B-BACKUP-ENCL` | none | interconnect sounds every alarm | confirm part numbers on kidde.com |
| EVSE | `APPL-G-EVSE` | Grizzl-E Smart 40 A, hardwired | OCPP 1.6J to HACS `ocpp` (local push) | none | charges at the DIP-set amps | the Smart's own UL file; 1.6J vs 1.6 |
| HP1 thermostat | `ED-S-HP-STAT` | Aqara W200 | Matter over Wi-Fi (local push) | Aqara app for firmware | runs its schedule standalone | aux staging in HA (below) |
| HP2/HP3 heads | `EQ-*-HP2-*`, `EQ-M-HP3-STAIR` | Gree built-in Wi-Fi | core `gree` (local polling) | Gree+ once, then WAN blocked | IR remote | GCM-encrypted firmware may not pair |
| ERV boost | `EQ-B-ERV` | Shelly relay on the Broan dry-contact aux input (manual §3.2.2) | Shelly core (local push) | none | Broan wall control | read the terminal names before wiring |
| Floor heat (3 zones) | `ED-*-FH-STAT` | Warmup 7iE | Matter over Wi-Fi (local push) | Warmup app for firmware | own schedule, own sensor | Schluter warranty letter |
| Leak shutoff | `APPL-S-PLANT-VALVE` | Zooz ZAC36 Titan (Z-Wave LR) + ZSE42 | Z-Wave JS (local push) | none | wired probe closes the valve | confirm the stub valve is a lever ball valve |
| Water heater | `EQ-B-WH` | Rheem ProTerra EcoNet port | ESPHome `esphome-econet` over RS-485 | Wi-Fi module never registered | tank controls | mode control on the ProTerra |
| Inverter/battery | `EQ-B-ESS-INV` | EG4 12kPV | EG4 web monitor, local Modbus (HACS) | none | inverter runs itself | firmware support for local mode |
| Lighting | `ED-T-LEV-MATTER*` | Leviton D215S / D2ELV / companion | Matter (local push) | one My Leviton session (D215S firmware) | paddles | confirm companion `DD0SR-DLZ` |
| Shades | `plan/window_coverings.py` | SmartWings, Matter/Thread | Matter via ZBT-2 | none | wand and remote | none |
| Scene keypad | `ED-M-LIVING-KEYPAD` | Zooz ZEN32 | Z-Wave JS on the 800 LR stick (local push) | none | does nothing | set scene-only (relay unwired) |
| Tape controllers (12) | `ED-M-LIVING-LT-CTRL`/`-E`, `ED-M-DINING-LT-CTRL`/`-E`, `ED-S-HALL-LT-CTRL`/`-CTRL2`, `ED-G-EAVE-W/-W2/-E/-E2-CTRL`, `ED-G-GABLE-N/-N2-CTRL` | Gledopto GL-C-001P | Zigbee, ZHA (local push) | none | its power-on state | set power-on to "previous" |
| Closet and kitchen tape | `ED-M-CLOSET-LT-PSU`, `ED-M-KITCH-LT-PSU` (MITTLED) | IKEA TRADFRI 30 W | unpaired, or Zigbee on ZHA to dim | none | powers on lit | bench-test power-on unpaired |
| Night-light motion (8) | not modelled: one per bath, one at the basement stair | PIR sensor (to select), battery | Zigbee, ZHA | none | relay paddles | select the product |
| HA host | `ED-B-UTIL-RC1` / `CKT-HA` | mini PC + ZBT-2 + Z-Wave 800 LR stick + Zigbee coordinator dongle | wired LAN | none | none | UPS: the backup-battery TODO |

Lighting, the fan and the RF-remote fixtures: `notes/workshop_receptacles.md`. Shades:
`notes/window_coverings.md`. Water heater shedding: `notes/backup_power.md`. Plant-room water:
`notes/plant_room.md`.

## Device notes

**Entry lock.** The keyless Sense Pro is accepted (owner, 2026-10-30). The Encode Plus has
no Matter and no local HA path, and the Yale Assure 2 Wi-Fi (`PROD-YALE-ASSURE-2-WIFI`,
defined and never placed) is deleted. With the Sense Pro's batteries dead you get in through
the USB-C jumpstart, or through a French door (a BE365 with a key). Run lithium AA cells:
alkalines fall off below 0 F, and lithium is rated to -40 F. Outside body -31..151 F; the
inside body is in a heated house. Keep the plain exterior deadbolts keyed alike at purchase.

**Doorbell.** It sits on the latch side, in the first stud bay of `W-M-N2` between the strike
blocks. Its raceway `CD-M-DATA-DOORBELL` leaves the pull box that ends `CD-M-DATA-KITCH-TRUNK`
in RM-M-MECH's ceiling:
1. east in FS-S-WEST's last truss bay;
2. down `W-M-STRW`'s cavity;
3. north through the corner into `W-M-N2`.

It has no path from below: `W-M-N2` stands on the basement wall's concrete, and its band is
FO-M-STAIR's trimmer. Nor from above: FO-S-STAIR's trimmer truss fills the bay. Ring through a
Reolink plug-in chime or an HA announcement; there is no mechanical chime.

**Cameras.** Both record to their own microSD, and HA keeps events through the core
integration. There is no NVR; Frigate is optional later.
- The backyard turret hangs under the balcony joists, south of the screen's front track, so
  its IR does not flare off the mesh. Its Cat 6A is the second cable in `CD-M-DATA-PORCH`, and
  `CD-M-DATA-CAM-PORCH` then bores the balcony joists at mid-depth, so nothing crosses under
  the track.
- The canopy camera is the second cable in `CD-M-DATA-KITCH`. It leaves through `W-M-N1`
  east of WIN-M-KITCH at 5'-9", between girts, by a sealed LB, and runs on EMT to
  `BM-BW-RE`'s soffit. It needed no mounting block. The model has no cable count: a drop
  bills per `data_outlet`, so nine drops now (three APs, three jacks, three cameras).
- **Fill.** Standard Cat 6A (0.30-0.35" OD) fits. From the data riser to the pull box the
  raceway is `CD-M-DATA-KITCH-TRUNK`, 1" EMT (0.864 in^2, 40% for 3 cables): the AP, the
  doorbell and the canopy camera fill 25% at 0.30" and 33% at 0.35". Past the box,
  `CD-M-DATA-KITCH` is 3/4" EMT (0.533 in^2) with two cables: 27% and 36% (the 31% two-cable
  figure of Table 1 is not binding on communications cable). The model has no cable count to
  grade it.

**Garage opener.** It must be a yellow-button Security+ 2.0 unit. Not Security+ 3.0 (white
button: ratgdo cannot speak it), and not the 8500/RJ020 jackshaft. The head is 11' back on the
door's centreline, hung on straps. It plugs into `ED-G-GDO-RC`, on `CKT-LT-MAIN` behind the
blank-face GFCI `ED-G-GDO-GFCI` by the light switch (2026-10-30). The ceiling is 10'-1" above the slab, so there is 3'-1" over the 7'-0" door:
room for a standard-lift track and a trolley rail. The 8550W manual's own headroom figure is
not yet read.

**Smoke/CO/heat.** One Kidde hardwired line, every unit with a sealed backup, all on
`CKT-LT-BACKUP`. Kidde wants every interconnected unit on one branch. The line is:
- 30CUA10-V combos;
- the 20SA10 photoelectric (the P4010 sealed-battery models are discontinued);
- HD135F heat alarms, which take a 9 V cell rather than a sealed battery.

The SM120X relay trips on smoke only, so the CO120X carries CO. Both sit under the backup
enclosure (`ED-B-ALARM-RELAY-*`), and their contacts land on two isolated inputs of a Shelly or
ESPHome board inside it. `Alarm` has no `product_ref`, so the line is named here and in the
alarm price row.

**EVSE.** The Emporia has no local API and no OCPP, and OpenEVSE appears not to be UL-listed.
The Grizzl-E Smart is listed and speaks OCPP. Keep it off the internet, and point its OCPP
server at HA. It is an `Appliance`, hardwired from the `ED-G-EV-1450` box (plug removed, per its manual), with
backing `BK-G-S-EVSE`; its own CCID is the ground-fault protection
([workshop_receptacles.md](workshop_receptacles.md), Garage).

**HP1 thermostat.** 24 VAC with a C-wire from `EQ-S-HP1-AH`'s board. Wire `L` (leak) and
`H1/H2` per the Gree quick-start, and keep aux staging in the thermostat. HA likely sees only
setpoint and mode, so bench one unit on the AH before buying more. It sits on the hall face of
`W-S-BW2` at a 54" centre.

**Floor heat.** The Warmup 7iE has a 15 A load and an integral Class A GFCI, which meets NEC
424.44 at the device; the breakers stay GFCI as well (`plan/circuits.py`). It replaces the
library stat on all three zones and uses its own floor sensor. Ask Schluter in writing whether
the cable warranty survives a non-Schluter thermostat.

**Leak shutoff.** It replaces YoLink. See [plant_room.md](plant_room.md).

**Recording, alarms, UPS.** No cloud recording plans. The HA host, router and PoE switch share
`CKT-HA` (ALWAYS_ON); a small UPS for them is the separate backup-battery TODO. On battery the
doorbell and cameras are shed (rule 6).

## Lighting scenes

RM-M-LIVING's lights (2026-10-31, `plan/lighting_living.py`). The engine models no scenes; this
table is the HA configuration. Every load is a Leviton D215S relay (on/off) except the coves,
which dim and colour at their Gledopto GL-C-001P controllers (RGBCCT mode).

| Group | Loads | Control |
|---|---|---|
| A accents | gimbals `ED-M-LIVING-CAN2`-`4` (mantel, curtains) | `ED-M-LIVING-SW-ACCENT` |
| B downlights | `ED-M-LIVING-LT`, `-CAN5`, `-CAN6` | `ED-M-LIVING-SW` |
| C day | `ED-M-LIVING-CAND1`/`2`, 5000 K over the puzzle table | `ED-M-LIVING-SW-DAY` |
| D coves | lounge `LR-M-LIVING-W`/`-E` and dining `LR-M-DINING-W`/`-E`, E4 RGB+CCT | `ED-M-LIVING-SW-COVE` (all four Class 2 drivers) + lounge `ED-M-LIVING-LT-CTRL`/`-CTRL-E`, dining `ED-M-DINING-LT-CTRL`/`-CTRL-E` |
| Pendant | `ED-M-DINING-PEND` (dims by its own remote) | `ED-M-DINING-SW` |
| Kitchen | perimeter `ED-M-KITCH-CAN1`/`2`/`3`/`5`/`9`/`10`; peninsula `-CAN4`/`6`/`7`/`8` | `ED-M-KITCH-SW` / `ED-M-KITCH-SW-PEN` |
| Under-cabinet | MITTLED on its TRADFRI's switched outlet `ED-M-KITCH-UC-RC` | `ED-M-KITCH-SW-UC` |

| Scene | A | B | C | Lounge coves | Dining coves | Pendant | Kitchen / peninsula / UC |
|---|---|---|---|---|---|---|---|
| Fireplace | on | off | off | 2200 K, 15% | off | off | off / off / off |
| Evening | on | off | off | 2700 K, 40% | 2700 K, 25% | low | off / off / on |
| Dinner | on | off | off | 2700 K, 20% | 2700 K, 50% | on | off / off / on |
| Social | on | on | off | 3000 K, 60% | 3000 K, 60% | on | off / on / on |
| Day / work | off | on | on | 5000 K, 100% | 5000 K, 60% | off | unchanged |
| Cooking | unchanged | unchanged | unchanged | unchanged | unchanged | unchanged | on / on / on |
| Night path | off | off | off | amber, 5% | amber, 5% | off | off / off / off |
| Party | on | off | off | colour, slow fade | colour, slow fade | low | off / on / on |

- **Keypad** `ED-M-LIVING-KEYPAD` (Zooz ZEN32, beside the kitchen switches on `W-M-C3`): big
  button Evening, double-tap all lounge and dining off; small buttons Fireplace, Dinner,
  Social, Day/work; a double-tap on Fireplace is Party, on Day/work Night path. Cooking stays
  on the kitchen paddles. It joins the existing Z-Wave 800 LR stick (Z-Wave JS, local); its
  relay is unwired, so set it to scene-only.
- **The coves need Zigbee.** The GL-C-001P is a Zigbee controller, so the coves take the second
  dongle rule 2 allows, on ZHA. MITTLED's TRADFRI driver can pair there too to dim; no DIRIGERA.
- **Leave `ED-M-LIVING-SW-COVE` on.** The controllers do on/off, so a scene has no boot lag;
  the paddle is the hard off. Set all four controllers' power-on state to "previous".
- **One HA light group per zone.** Each cove half has its own Class 2 driver and controller
  (owner, 2026-10-31), so the lounge is two controllers (`ED-M-LIVING-LT-CTRL` W,
  `-CTRL-E` E) and the dining two (`ED-M-DINING-LT-CTRL`, `-CTRL-E`). Join each pair as one
  HA light group; the scenes above set the group, so both sides always match.
- **Night path is the warm layer**: amber at 5% only, never a white channel. The day layer is
  the 5000 K cans plus the coves' white channels at 5000 K.
- **Check items.** The dining pendant must come back at its last state when its relay powers
  it, or a scene "on" leaves it dark; bench it before the trim-out. Confirm each D215S's
  power-on behaviour after an outage.
- **HA down**: every D215S paddle still switches its group; the keypad does nothing; the coves
  return at their last setting. Kitchen and under-cabinet ride `CKT-LT-BACKUP`; the lounge does not.

## Bath night lights

Added 2026-10-31. Every bath has one, all built the same way: E5 2200 K tape (`ED-T-LT-STRIP24-NIGHT`, about 70 lm/ft, damp-rated, fixed CCT) in a frosted channel under the vanity. Each bath has its own `ED-T-LT-PSU-20` (Mean Well LPV-20-24) and its own D215S relay (`ED-T-LEV-MATTER`, Matter over Wi-Fi). Each relay sits on the same circuit as that bath's other lights.

| Bath | Run | PSU | Relay |
|---|---|---|---|
| B-BATH | `LR-B-BATH-NIGHT` | `ED-B-BATH-NL-PSU` | `ED-B-BATH-SW-NL`, on `CKT-LT-BACKUP` |
| M-BATH1 | `LR-M-BATH1-NIGHT`, on the wall under the basin | `ED-M-BATH1-NL-PSU` | `ED-M-BATH1-SW-NL` |
| M-BATH2 | `LR-M-BATH2-TOEKICK` | `ED-M-BATH2-NL-PSU` | `ED-M-BATH2-SW-NL` |
| S-VANITY | `LR-S-VANITY-NIGHT` | `ED-S-VANITY-NL-PSU` | `ED-S-VANITY-SW-NL` |
| S-SUITEBATH | `LR-S-SUITEBATH-NIGHT` | `ED-S-SUITEBATH-NL-PSU` | `ED-S-SUITEBATH-SW-NL` |
| S-BATH1 | `LR-S-BATH1-NIGHT` | `ED-S-BATH1-NL-PSU` | `ED-S-BATH1-SW-NL` |
| A-STUBATH | `LR-A-STUBATH-NIGHT` | `ED-A-STUBATH-NL-PSU` | `ED-A-STUBATH-SW-NL` |

- **The motion sensor.** Each bath gets one battery PIR on the Zigbee dongle (ZHA). It is not modelled. Mount it high, aimed at the door and the vanity, and keep it out of the shower's view.
- **The automation** is one HA automation per bath:
  - **Turn on** when motion is seen between 22:00 and 07:00.
  - **Turn off** after 3 minutes with no motion.
  - If the bath's main switch comes on, the night light stays on and still times out.
- **When HA is down**, the relay paddle still switches the night light by hand. Set each relay's power-on state to "off", so the tape doesn't light the whole night after an outage.
- **Nothing dims.** E5 is fixed at its low output, and the PSU only switches.

## Other lighting automations

- **Second-floor hall cove** (`LR-S-HALL-GAP`, E6 tunable): after dark HA recalls a low 2700 K night preset on both halves' controllers (`ED-S-HALL-LT-CTRL`, `-CTRL2`, one HA group). The 3-way relays `ED-S-HALL-SW`/`-SW2` cut the drivers' 120 V, so set both controllers' power-on state to "previous".
- **Garage linear** (W, RGBW): HA turns `ED-G-SOFFIT-SW` on at dusk and off at a curfew (owner sets the time); the W channel at 3000 K is the default, a holiday colour is a scene on the six garage controllers.
- **Entry and garage door lights**: `ED-M-ENTRY-SW` and `ED-G-EXT-SW` come on at dusk and on arrival (the entry lock, the opener), then time out.
- **Basement stair at night**: no night lights (owner, 2026-10-31); the railing tape on the stair 3-way and the landing guide-light receptacles light it.
