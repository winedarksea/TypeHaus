# RM-S-PLANT moisture and heat budget (2026-11-12)

Hand oracle for the sealed plant room: `mep.room_heat_source` on `RM-S-PLANT`
(`tests/test_room_heat_source.py`), the transfer pair's sizing, the shade rule and the summer
fallback. Room: 137.8 sf clear, 9'-0" to the liner ceiling (~1,240 ft3), held at 75 F / 70% RH.
Neighbours: Study 2 (east, `W-S-C1`), the suite and hall (north, `W-S-PS1`/`-PS2`); the main
floor below and the attic above are conditioned. Outdoors: two walls (`W-S-S1` south,
`W-S-W4` west).

Psychrometrics at 14.696 psia, W = 0.622 pw / (p - pw):

| state | psat (psia) | pw | W (lb/lb) | dew point |
|---|---|---|---|---|
| plant 75 F / 70% | 0.4298 | 0.3009 | 0.01300 | 64.6 F |
| Study 2 winter 70 F / 35% | 0.3633 | 0.1272 | 0.00543 | |
| Study 2 summer 75 F / 50% | 0.4298 | 0.2149 | 0.00925 | |

## 1. Moisture sources and sinks

- **Source:** irrigation only. The reservoir caps it at 0.7 gal/day (`notes/plant_reservoir.md`)
  = 5.84 lb/day = 0.243 lb/h. Nearly all of it leaves the leaves as evapotranspiration; with
  ~15% held in growth and soil, **~0.20 lb/h** (0.24 if all of it).
- **No other source:** no humidifier, no shower, no System 1 or ERV air since 2026-11-12.
- **Sinks:** exchange with Study 2 (the transfer pair plus the door's residual leakage), and
  diffusion through the Class I liner (negligible).

## 2. Allowed exchange

Moisture removed = 4.5 lb/h per cfm x (W_plant - W_study):

    winter: cfm = 0.20 / (4.5 x (0.01300 - 0.00543)) = 0.20 / 0.03407 = 5.9 cfm   (0.24 lb/h: 7.1)
    summer: cfm = 0.20 / (4.5 x (0.01300 - 0.00925)) = 0.20 / 0.01688 = 11.8 cfm  (study at 45%: 9.5)

So the room affords **5-7 cfm in winter, 10-13 in summer**, the door's leakage included. Less
and RH climbs to the glass's dew point; more and the room dries toward Study 2.

## 3. The vent is the humidity control

The glass is the coldest surface. At -15 F design, centre of glass (U 0.14, 0.68 interior film):
75 - 0.14 x 0.68 x 90 = 66.4 F, **1.8 F above the 64.6 F dew point**
(`building_science.glazing_dew_point` reads 1.9). The frame edge runs 5-8 F colder, so on a
design night at 70% the edge condenses. Hence the operating rule, which needs a room T/RH
sensor with alerts (`notes/smart_home.md`):

- RH > 75%: open the pair further. RH < 60%: close it down (or add pebble trays).
- Below +10 F outdoors, run 55-60% by opening the vent: at 60% the dew point is 60.0 F and the
  edge (66.4 - 8 = 58.4 F at design) is the only surface still marginal.

## 4. The transfer pair, by buoyancy

Two 10x6 grilles (~42 in2 free each; plant face with OBD), one high, one low, in `W-S-C1`'s
y 64 3/4".."79 1/4" bay (`REG-S-XFER-PLANT-HI`/`-LO`). Centres 87.25" and 13.25" above the datum:
h = 74" = 6.17 ft. Two openings in series: A_eff = A / sqrt(2) = 0.278 / 1.414 = 0.196 ft2;
Cd 0.6; dT 5 F (75 vs 70); T 530 R.

    v = sqrt(2 g h dT / T) = sqrt(2 x 32.2 x 6.17 x 5 / 530) = sqrt(3.748) = 1.936 ft/s
    Q = 0.6 x 0.196 x 1.936 = 0.228 ft3/s = 13.7 cfm   (fully open)

Winter's 5-7 cfm wants about 45% of that (Q scales with open area): the working range is a
narrow band of the damper. In summer the pair runs near fully open. The steel door with
compression seals and a bottom sill adds ~1 cfm at the pair's ~0.3 Pa stack.

## 5. Winter heat loss and heat

UA from the assemblies:

| element | area (sf) | U | UA (Btu/h F) |
|---|---|---|---|
| windows, 3 x WT-3048-HP + WT-2754-HP (unit) | 30.0 + 10.3 = 40.3 | 0.14 | 5.64 |
| exterior wall, PLANT_EXT_2X6_HUMID, 18' + 9' x 9' gross less glass | 243 - 40.3 = 202.7 | 0.026 | 5.27 |
| **envelope** | | | **10.91** |
| interior partitions to 70 F rooms (C1 81 sf at U 0.04, PS1/PS2 162 sf at 0.06) | 243 | | 12.96 |

The wall U is the house's honest R-37.9 (`EXT_2X6` with girt screws counted, CLAUDE.md
"Shell"), taking no credit for the liner's PVC and air gap or for mineral wool over fibreglass;
both only lower it.

At design (75 F in, -15 F out, dT 90):

    envelope        10.91 x 90                                 =   982 Btu/h
    infiltration    0.15 ACH x 1,240 ft3 / 60 = 3.1 cfm x 1.08 x 90 =   301
    partitions      12.96 x 5                                  =    65
    transfer air    6 cfm x 1.08 x 5                           =    32
    total                                                      = 1,380 Btu/h = 404 W

0.15 ACH is the house's 3.0 ACH50 over 20. The engine's room-scoped `estimate_block_load`
reads 1,309 Btu/h (5% under this; it attributes infiltration by volume share). Sources:
the grow lights ~180 W during the photoperiod only, and **the 1500 W fan heater
(5,118 Btu/h), 3.7x the loss**. The heater carries the room on a design night with the lights
off. `mep.room_heat_source` passes on that margin.

No mini-split: 400 W of loss does not justify a head, and a head's coil would wring out the
very water the room keeps. No radiant floor: the floor is the spill pan.

## 6. Summer float temperature

Peak afternoon gains: west glass 10.3 sf x 0.39 x ~200 Btu/h sf = 803; south 30 sf x 0.39 x
~60 = 702; **~1,500 Btu/h**. Evapotranspiration takes ~0.2 lb/h x 1,050 = 210 Btu/h of it.
Steady state at 90 F outdoors, Study 2 at 75 F:

    (1,500 - 210) + 10.91 (90 - T) = (12.96 + 1.08 Q) (T - 75)

| case | Q (cfm) | T |
|---|---|---|
| no shades, pair open | 12 | 115 F |
| shades closed (white/reflective roller, ~0.5 x the glass gain) | 12 | 94 F |
| door held open to Study 2, no shades | 150 | 83 F |
| door held open, shades closed | 150 | 79 F |

These are steady-state upper bounds: the soil, water and plants damp the swing. Still, the
shades alone do not hold ~85 F at peak; **the summer fallback is the door held open** on its
hold-open closer to Study 2's 150 cfm (`REG-S-HP-STUDY2`, `-S`), and the south grille's jet
running past `D-S-PLANT` is what feeds it.

**Moisture cost of an open hour:** 4.5 x 150 x (0.01300 - 0.00925) = **2.5 lb/h**, about 12 h
of the room's evapotranspiration. RH falls toward Study 2's within the hour; close the door
and water to recover.

## 7. When the shades may close

A closed shade traps a layer of room air against colder glass. Take the interior resistance
as film 0.68 + shade and trapped air ~0.8 = 1.48, and the frame edge 8 F under the glass:

    T_glass = 75 - 0.14 x 1.48 x (75 - T_out);  T_glass - 8 >= 64.6
    0.2072 (75 - T_out) <= 2.4   ->   T_out >= 63.4 F

So **close only when sun is on the glass, the room is over setpoint and outdoors >= 63 F**;
otherwise open, and always open on heating-season nights. Sun on the glass only warms it, so
the rule errs safe.
