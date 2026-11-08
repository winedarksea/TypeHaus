---
title: "Plant-room drip reservoir (RM-S-PLANT): float fill over an air gap, no drain"
applied_to:
  - room: RM-S-PLANT
  - appliance: APPL-S-PLANT-RESERVOIR
  - pipe_accessory: PA-S-PLANT-RESERVOIR-STOP
  - door: D-S-PLANT
  - electrical_device: ED-S-PLANT-RC6
tags:
  - plumbing
  - backflow
  - irrigation
  - plant-room
source:
  - plan/plant_reservoir.py
  - plan/plant_reservoir_types.py
  - plan/mep_supply_plant.py
  - plan/doorway_transitions.py
  - plan/mep_electrical.py
---

# Notes

Owner, 2026-11-07: design the reservoir. It replaces `PA-S-PLANT-WATER-STUB` (the capped
hose-thread stop) as the room's water. Why not a sink: every tie on `PR-M-S-SUITE-DRAIN` is
within 4.75" of an inlet, no cavity holds a 1 1/4" vent within 42", an outdoor sidewall vent
fails UPC 906.2 at the south windows, and AAVs are banned (Minn. Stat. 326B.43 subd. 6)
(`plans/TODO.md`, 2026-11-07).

## 1. The design

```text
PR-M-CW-PLANT-STUB (1/2" PEX, 14" AFF, in W-S-S1)
  -> PA-S-PLANT-RESERVOIR-STOP  1/4-turn straight stop, 1/4" comp. outlet, recessed box
  -> 1/4" needle valve (rate limit, section 5), 4 ft of 1/4" poly line
  -> float valve (Dial 4154), SPOUT 2" ABOVE THE TANK RIM   <- the air gap, UPC 603.3.1
  -> 10 gal BRUTE tank, no drain, no overflow pipe
  -> 12 V diaphragm pump on the floor beside it, drawing from the tank
  -> drip tubing and drippers to the stands and baskets
```

- **Nothing downstream of the valve touches the water supply.** The tank is the break. The
  pump draws from it; no irrigation line is hard-piped to the house (P2902.5.3's PVB/RPZ
  case does not arise; the earlier stub note's warning is retired).
- **No drain, no vent, no trap.** The 10 gal tank is the whole worst-case release (section 3).
- **Where.** Tank centre (166", 16.1") 1/2" off W-S-S1's finished face, rotation 180 so the
  float valve is on the wall side, west rim, 11" from the stop. East of the hydrant's bay
  (145"-158"), 12" clear of D-S-PLANT's swing (x >= 186"), under WIN-S-PLANT4's 32" sill (the 17 1/8"
  tank clears it). The pump and its supply stand on the floor between the tank and
  `ED-S-PLANT-RC6` (x 184", 16" AFF); they are in the parts list, not the model.
- **`PA-S-PLANT-WATER-STUB` is retired** (retagged `PA-S-PLANT-RESERVOIR-STOP`, kind SHUTOFF,
  same uid). The run `PR-M-CW-PLANT-STUB` is unchanged, so the routing tests that name it
  still hold.

## 2. Code reading

Minnesota adopts the **2018 UPC** (Minn. R. 4714.0050; `notes/mep_group_wet_vent_basis.md`),
chapters 2-11, with Minnesota amendments. **The 2018 text is paywalled and was not read.**
Wording below is from secondary sources (open-exam-prep's UPC study guide; the Illinois
adoption of Table 603.3.1; CPC commentary) and from the Minnesota rule text. Have the AHJ
confirm the numbers against the adopted book before rough-in.

| Section | What it says (secondary) | How the design answers |
|---|---|---|
| **603.3.1 Air gap** | "the unobstructed vertical distance through the free atmosphere" between the lowest supply opening and the flood-level rim of the receptacle | Dial 4154's spout stands 2" over the BRUTE's rim. The rim IS the flood level: no overflow pipe, no weir. |
| **Table 603.3.1** | Effective opening <= 1/2": 1" clear of a wall, **1 1/2" if a wall is within 3x the opening**; <= 3/4": 1 1/2" / 2 1/4"; <= 1": 2" / 3"; over 1": 2x / 3x. Gaps under 1" only as a listed assembly. | 1/4" compression valve, orifice ~0.2" (assumed): 1" / 1 1/2". **Built 2"**: the spout is near the wall, so 1 1/2" governs and the margin is 1/2". |
| **603.5.5 Inlets to tanks, vats, sumps, pools** | An air gap, or a listed vacuum breaker 6" up on the discharge side of the last valve, or a backflow preventer suited to the hazard | The air gap is the first of the three. No device to test, tag or log. |
| **603.5.2 Tank ballcock** | critical level 1" over the overflow's full opening | Not our case (a toilet tank). The BRUTE has no overflow pipe, so the rim is the overflow. |
| **603.2 / 603.5.23** (Minn. R. 4714.0603 subps. 1, 5) | An approved device before install; testable assemblies are tested yearly by an ASSE 5000 tester | Not triggered: an air gap is not a device or an assembly. This is the practical reason to prefer it. |
| **603.5.7** | A backflow preventer or vacuum breaker at every hose thread | The old capped hose-thread stop would have carried it. The 1/4" compression outlet is not a hose thread. |

Minnesota's amendments to chapter 6 (4714.0603: 603.2, 603.5.4 heat exchangers, 603.5.12
beverage dispensers, 603.5.17 yard hydrants, 603.5.22 barometric loop, 603.5.23 testable
assemblies) do not touch 603.3.1, Table 603.3.1 or 603.5.5.

**One thing the code does not give us:** the effective opening of the Dial valve. It is not
published. 0.2" is a bench estimate; anything up to 1/2" keeps the same 1" / 1 1/2" row, so the
2" gap holds to a 3/4" opening. Measure the delivered valve.

## 3. Spill arithmetic (oracle for `test_plant_reservoir.py`)

RM-S-PLANT's clear floor is 204.17" x 97.17" = 19,838 sq in = **137.77 sf** (the resolved
`area_m2`, 12.7995 m2). The sheet vinyl and its sealed 4" rubber base hold water; the room has
no drain; the one door is D-S-PLANT.

| Quantity | Hand work | Result |
|---|---|---|
| Held at 1/4" | 137.77 sf x (0.25/12) ft = 2.870 cu ft x 7.4805 | **21.5 gal** (21.3 less the tank's footprint, 1.33 sf) |
| Held to the stop, 0.38" | 137.77 x (0.38/12) = 4.363 cu ft x 7.4805 | **32.6 gal** |
| A whole 10 gal tank on the floor | 10/7.4805 = 1.337 cu ft / (137.77 - 1.33) sf = 0.0098 ft | **0.118"**, under the 4" base by 34x and under the stop by 3x |
| Margin at the stop | 32.6 / 10 | 3.3 tanks |

So the answer to "does it spill out" is no, for a single tank release. The 21 gal the TODO
carried is right (21.5).

**The stop is the dam.** `plan/doorway_transitions.py` now authors a `water-stop riser` part in
D-S-PLANT's solid-surface profile: top at **0.38"** over the vinyl (`PLANT_RISER_IN`), the oak
plane. It is cut from the same 12 mm piece as the slope and landing, so there is no joint
under the profile for water to track. Seal: one silicone bead at the toe, both ends and the
jamb returns (as `notes/floor_heights.md`). 0.38" over the 1/4" the room is sized to leaves
0.13" of freeboard. The section is schematic (`section_documented`, supplier PENDING); the
slope stops 3/8" short of the oak plane to make the riser's face.

## 4. The unbounded case is the float

A tank cannot overflow if its float closes. If it sticks, the feed runs until someone shuts
the stop: the owner dropped the leak shutoff on 2026-11-03 and nothing in this design adds
one. **Every number in section 3 is a single release; a stuck float is not.** The house is
40-80 psi. Hand estimate, Darcy-Weisbach, 4 ft of 1/4" OD poly (ID ~0.17"), f = 0.027:
~1 gpm costs ~10 psi, so a 1/4" line unthrottled passes **~2 gpm at 50 psi**. The tank is full,
so all of it is overflow: **11 min to 21.5 gal, 16 min to the stop**. Containment buys minutes.

Two things bound that without an actuator, both in the parts list:

1. **A 1/4" needle valve** (Dial 94045) ahead of the float, set at ~0.1 gpm (6 gph) with a
   graduated cylinder: stuck-float time to 21.5 gal becomes **~3.6 h**, to the stop **~5.4 h**.
   The drip draw is a few gallons a day (section 6), so a 6 gph refill never starves it.
2. **A local leak sensor** (Zigbee or Matter, any, on the floor beside the tank) that only
   notifies through Home Assistant, as `notes/smart_home.md` already treats leaks: HA
   observes, nothing depends on it. Not modelled, not priced; the owner's call.

Neither makes an absence of days safe. If the owner wants that, it is a second float valve in
series on a short stand-pipe above the first, or the shutoff the owner already declined.

## 5. Parts (retail; no quotes, no approvals, per `product-selection-preferences`)

Prices are for `prices.toml`, which the coordinator owns; rows below are proposals.

| Part | Choice | Read | Note |
|---|---|---|---|
| Reservoir | Rubbermaid Commercial **BRUTE FG261000GRAY**, 10 gal, 15 5/8" dia x 17 1/8" | retailer listings | Rim is the flood level. A fitted lid with a 1" notch for the valve arm keeps algae and mosquitoes down at 70% RH; not modelled. |
| Float valve | **Dial 4154**, 1/4" brass compression, Home Depot #100560907 | HD listing, $16.18 | Mount on an angle bracket clamped to the rim; spout 2" over it; bend the arm to close 1" below the rim. |
| Rate limit | **Dial 94045**, 1/4" compression needle valve, HD #100175352 | HD listing, $10.98 | Section 4. |
| Stop | **BrassCraft G2PS04X-C1**, 1/2" push x 1/4" comp. quarter-turn straight stop, HD #306206261 | search result only | Push-connect onto the 1/2" PEX stub. |
| Pump | **SEAFLO SFDP1-012-035-21**, 12 V DC, 1.2 GPM, 35 psi, self-priming, dry-run tolerant | retailer listings; maker sheet not seen | Why not a submersible: Active Aqua AAPW250 lists 5.9 ft of static head, AAPW550 7.9 ft; the top shelf's pots stand at 75" AFF (6.25 ft) and a dripper wants head on top of that. |
| Pump supply | 12 V DC, >= 5 A, UL-listed plug-in | generic | Model to the shelf. |
| Pressure | 25 psi drip regulator at the pump | generic | The pump shuts off at 35 psi; 1/4" tubing and compression fittings want less. |
| Drip kit | Rain Bird **DRIPKITBAG**, HD #326977353 | HD listing, $28.12 | 1/4" tubing and drippers; check the kit's emitter type against the regulator's output. 14 drippers: 12 pots, 2 baskets. |
| Timer | **Woods 50015WD**, 15 A 7-day outdoor plug-in | HD listing, $15.85 | Pump supply plugs into it. No hub, no cloud. |
| Receptacle | `ED-S-PLANT-RC6`: the room's WR GFCI (`ED-T-LEV-GFCI-WR`), `CKT-RC-SECOND` | house standard | One more outlet on the room's circuit; the pump is ~48 W. |

**Open on the receptacle.** The room's in-use bubble cover does not close over a plug-in timer.
Options: a damp-location flip cover (NEC 406.9(A), if the AHJ treats this wall as damp rather
than wet; I did not read the 2026 text), or no timer and a smart plug on HA (local only,
nothing safety-critical depends on it). The model carries the same WR GFCI either way.

**Open on the drippers.** The pump's 35 psi needs a regulator; pressure-compensating
drippers need ~10+ psi to work and non-compensating ones flow with height. The 75" shelf is
at the far end of the line; set each dripper by eye on first run. No hydraulic calculation was
made; this is a purchased kit.

Proposed `prices.toml` rows (unit prices left to the coordinator): `PROD-RUBBERMAID-FG261000GRAY`,
`PROD-DIAL-4154`, `PROD-DIAL-94045`, `PROD-BRASSCRAFT-G2PS04X-C1`, `PROD-SEAFLO-SFDP1-012-035-21`,
`PROD-PUMP-PSU-12V`, `PROD-RAINBIRD-DRIPKITBAG`, `PROD-WOODS-50015WD`, plus a 4 ft 1/4" poly line.
The takeoff bills them as `install_parts` strings on `APPL-S-PLANT-RESERVOIR`; the old
`ro_stub` row (`PA-S-PLANT-WATER-STUB`) becomes a `shutoff` row.

## 6. Water budget

14 drippers at 1 gph, 15 min a day: 3.5 gal/day, a third of the tank. The float refills at
6 gph (section 4) in 35 min. Evaporation from a 15 5/8" open tank in a 70% RH room is small;
with the lid, negligible. The tank is a break and a buffer, not the day's supply.

## 7. What the engine does not grade (the gap register)

Each of these is a missing check, not a pass. None was faked.

1. **The air gap.** `mep.backflow_prevention` reads hydrants only (`plan_symbol == "hydrant"`).
   Nothing reads a tank inlet (603.5.5) or Table 603.3.1. The gap is authored on
   `ServicePort` `supply` (z over the height) and pinned only by `test_plant_reservoir.py`.
2. **A float valve is nobody's.** No `PipeAccessoryKind` for it; it rides `install_parts`.
3. **The WSFU table has no row for the tank.** `mep.pipe_sizing` goes UNKNOWN on an appliance
   with no `WSFU_BY_SYMBOL` row (`resolve/fixture_units.py`), and that check is a permit item
   ("Drain and supply pipe sizing"), so naming the tank in `PR-M-CW-PLANT-STUB.serves` would
   block `haus print`. The run therefore does not name it, and `mep.fixture_port_connection`
   does not grade the float inlet. With `serves` set I measured it passing: inlet 10.77" from
   the stub end on a 48" line.
4. **Spill containment.** Nothing reads a room with no drain: its floor area, its stop height
   or a release volume. Section 3 is by hand; the test pins it.
5. **The pump's cord.** No check ties an appliance's POWER port to a receptacle; RC6's
   proximity is by authoring.
6. **A stuck float.** Not gradeable: the model has no failure mode.

## 8. Sources

- [Minn. R. 4714.0603](https://www.revisor.mn.gov/rules/4714.0603/): the chapter 6 amendments.
- [DLI: the 2018 UPC adoption](https://www.dli.mn.gov/node/5291); effective 2021-12-17.
- [UPC 603.3.1 / Table 603.3.1 / 603.5.5 study guide](https://open-exam-prep.com/study-guides/wa-plumber/backflow-prevention-cross-connection/air-gaps-vacuum-breakers) (secondary).
- [Illinois Table 603.3.1 adoption](https://regulations.justia.com/states/illinois/title-77/part-890/subpart-m/appendix-a/table-c) (secondary; same row values).
- Parts: [Dial 4154](https://www.homedepot.com/p/p/100560907), [Dial 94045](https://homedepot.com/p/DIAL-1-4-in-x-1-4-in-Evaporative-Cooler-Compression-Needle-Valve-94045/100175352), [BrassCraft G2PS04X-C1](https://homedepot.com/p/BrassCraft-1-2-in-Push-Connect-x-1-4-in-Compression-1-4-turn-Straight-Stop-G2PS04X-C1/306206261), [Rain Bird DRIPKITBAG](https://homedepot.com/p/Rain-Bird-Drip-System-Expansion-and-Repair-Kit-in-a-bag-DRIPKITBAG/326977353), [Woods 50015WD](https://www.homedepot.com/p/Woods-15-Amp-7-Day-Outdoor-Plug-In-Dual-Outlet-Digital-Timer-Black-50014WD/301133241), [SEAFLO 21 series](https://www.campingworld.com/seaflo-21-series-12v-1.2-gpm-water-pump-118492.html), [Active Aqua AAPW250](https://1000bulbs.com/product/97301/GROW-AAPW250.html), [BRUTE 10 gal](https://www.katom.com/007-2610G.html).
