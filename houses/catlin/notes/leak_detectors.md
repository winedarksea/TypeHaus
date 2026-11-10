# Leak detectors (2026-11-08)

HA observes; nothing depends on the Zigbee sensors. **Plant-room exception, owner
2026-11-10:** separate wired FloodStop and WS-1 controls shut down reservoir fill and
irrigation, with local manual reset. `AL-S-PLANT-LEAK` still only notifies; see
[reservoir safety and commissioning](plant_reservoir.md).

## Product

**SONOFF SNZB-05P**, Zigbee 3.0 water-leak sensor (`PROD-SONOFF-SNZB-05P`, retail, no quote):
48 x 48 x 21.6 mm, one CR2477, -10..60 C, contacts on the underside plus an optional cable
probe. Why this one:

- **Radio already in use.** The house runs Zigbee on the second ZBT-2 under ZHA (the six
  GL-C-001P cove controllers are mains routers). No new dongle, no vendor app, no cloud;
  ZHA exposes `water_leak` and battery. Matter-leak sensors are rare and Thread is the other
  ZBT-2's.
- Cheap enough (~$10-16) to put one at every wet point.
- Battery: CR2477, years of life; HA alerts on low battery (automation below).

## Where (`AlarmKind.LEAK`, tags `AL-*-LEAK`, floor points; no circuit)

| Tag | Room | Risk |
|---|---|---|
| `AL-B-WH-LEAK` | RM-B-WORKSHOP | HPWH (`EQ-B-WH`), beside the HydroBoost riser foot (drain valve, cold inlet), 3" off the tank |
| `AL-B-HDR-LEAK` | RM-B-WORKSHOP | hot-water header, floor below it (NE corner, beside the tank) |
| `AL-B-UTIL-LEAK` | RM-B-FURNACE | utility sink, the ERV/WH condensate receptor |
| `AL-B-SUMP-LEAK` | RM-B-FURNACE | sump pit overflow (sealed lid), south of the pit |
| `AL-B-MAIN-LEAK` | RM-B-STAIR | main shutoff `PA-B-MAIN-SHUTOFF` (water entry) |
| `AL-B-BATH-LEAK` | RM-B-BATH | basement lav and WC |
| `AL-M-LAUNDRY-LEAK` | RM-M-LAUNDRY | washer tower, gap beside it (no drain pan) |
| `AL-M-KITCH-LEAK` | RM-M-LIVING | sink base floor, 4 1/2" (cabinet bottom): sink, disposal, dishwasher hoses |
| `AL-M-BATH1-LEAK`, `AL-M-BATH2-LEAK` | main baths | lav/WC; tub side in BATH2 |
| `AL-S-BATH1-LEAK`, `AL-S-VANITY-LEAK`, `AL-S-SUITEBATH-LEAK` | second-floor baths | over finished ceilings |
| `AL-S-PLANT-LEAK` | RM-S-PLANT | 10 gal reservoir: notifications supplement independent wired fill/pump protection |
| `AL-A-STUBATH-LEAK`, `AL-A-STUDIO-LEAK` | attic | guest bath, studio bar sink |

16 sensors. Instances are in `plan/smart_home.py` (basement, main, second) and
`plan/electrical_attic.py` (attic). An `Alarm` has no product field, so the product is this
table and `SMART_HOME_PRODUCTS`; unpriced in the estimate (~$160 retail; add a `[allowances]`
row if the owner wants it counted). Positions are the nearest clear floor point to the
fixture; shift on site to the lowest point of the floor.

## Not covered, on purpose

- The dishwasher alone: the sink-base sensor shares its drain and inlet. LG's own float switch
  is the primary protection.
- Heat-pump condensate: the HP1 air handler (attic/second) and ERV condensate leave through
  `FX-B-UTIL-SINK`; its sensor is the catch.
- Roof/gutter, hydrants and the court's drainage are outdoors and not a sensor's job.

## HA setup (owner)

1. Pair each to ZHA (hold the button 5 s); name `binary_sensor.leak_<tag>`.
2. One automation: any leak `on` -> persistent notification + phone push (companion app, local
   notify) + the Reolink chime/HA speaker; reminder every 30 min until `off`.
3. Battery < 20% -> notification; check all 16 each spring.
4. Zigbee reach: end devices need a mains router. The cove controllers are routers on the
   main/second floors; the basement furnace room is beside the host's ZBT-2, but the north
   basement (bath, sump) and attic sensors may need one **mains Zigbee plug or relay as a
   router** (any ZHA-supported plug on an unswitched outlet). Check LQI after install before
   adding routers.
