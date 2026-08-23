---
title: "Backup Power — the ESS microgrid"
applied_to:
  - room: RM-B-ESS
  - equipment: EQ-B-ESS-BATT
  - equipment: EQ-B-ESS-INV
  - device: ED-B-BACKUP-PANEL
  - device: ED-B-BACKUP-ENCL
tags:
  - electrical
  - energy-storage
  - solar
  - backup
  - fire-separation
source:
  - plan/circuits.py
  - plan/electrical.py
  - plan/mep.py
  - plan/storeys/basement.py
  - plan/assemblies.py
  - params/solar.py
---

# Notes

2026-08-02. The backup power system stopped being a flag on six circuits and became a real
microgrid: an EG4 12kPV hybrid inverter, one 14.3 kWh battery in its own closet, the rooftop
array landing on the inverter instead of backfeeding on its own, and a subpanel that stays
live when the grid does not.

## The topology, and why it is a subpanel

The 12kPV's grid port lands on a 50A 2-pole breaker in ED-B-PANEL (`CKT-ESS-GRID`, slot 40 —
the position the old `CKT-PV` backfeed already held, at the opposite end of the bus from the
main). Its *dedicated load output* feeds a new 12-space subpanel, `ED-B-BACKUP-PANEL`, and
the six backup circuits moved off the main panel onto it.

That move is the design, not bookkeeping. A hybrid inverter's load port is physically a
separate bus that stays energized through an outage; putting the backup circuits anywhere
else means an interlock and a story about which breakers you are allowed to leave on. Two
side effects worth stating: the main panel went from 52 spaces used of 54 to 46, so it has
eight spare instead of two; and `electrical.panel_spaces` now reconciles two panels, which is
what makes the subpanel's own capacity a checked number rather than an assumption.

`CKT-BACKUP-FEED` is retired. It fed the DIN enclosure from the *grid* side, which is exactly
backwards once the enclosure's gear lives downstream of the inverter.

## The two tiers

| Tier | Circuits | What it is |
|---|---|---|
| `ALWAYS_ON` | `CKT-FRIDGE`, `CKT-HA`, `CKT-LT-BACKUP` | Food, network, and light in the kitchen and the mechanical room. Rides the whole outage. |
| `SHED` | `CKT-HP3`, `CKT-WH-240`, `CKT-SUMP` | Comfort and convenience. Dropped by a relay when the battery is low and the sun is not out. |

The tier is authored on the circuit (`Circuit.backup_tier`) and nothing infers it: whether a
load is worth carrying through an outage is an owner decision, not a property of the load.
The switching hardware follows from the tier — relay-driven contactors for all three shed
circuits now (the 2-pole heat pump, the 20A sump, and — since 2026-08-15 — the 2-pole water
heater), with the Pro 4PM relay still bought to drive the contactor coils even though no
circuit switches through one of its channels directly.

**The water heater (2026-08-15).** `CKT-WH-HP` is gone. This house has one water heater — an
80-gal Rheem ProTerra hybrid HPWH on one 240V/4,500 VA circuit — not the 120V-compressor /
240V-element two-tank split this note used to describe; that split modelled a single
product's two internal power draws as two appliances. `CKT-WH-240` now carries the whole
unit on the SHED tier, and its 500 VA backup contribution — the same figure `CKT-WH-HP` used
to carry — is enforced by `LM-WH` (`plan/circuits.py`): a Home Assistant automation
(ESPHome's `esphome-econet`, bridging the unit's EcoNet API) forces Heat-Pump-Only mode
whenever the house is on battery, so the number every calc below rests on is unchanged even
though the modelling that produces it is now honest about there being one appliance, not two.

## Does the 12kPV carry it?

This was the TODO's actual question, and `takeoff/backup_calc.py` answers it rather than a
comment asserting it. As authored today:

- **Storage** 12.87 kWh usable of 14.3 nameplate (90% DoD).
- **Autonomy, no sun** 53.0 h on the always-on tier alone.
- **48-hour cycle** one strong solar day puts in 15.84 kWh (5.28 kW array × 3.0 kWh/kW,
  haircut for the E/W split off a N-S ridge) against 11.7 kWh of always-on load over two
  days (net **+4.19 kWh**) — so the always-on tier rides indefinitely on sun every other
  day. Both tiers together take 46.45 kWh over the same 48 h and do **not** ride
  (net −30.61 kWh), which is what the shed tier exists to answer. Battery alone, both
  tiers running, is 13.3 h.
- **Peak** 4,658 VA of backup load against 8 kW continuous, and the largest shed-tier motor
  start (1,500 VA × 3 for a soft-started VFD = 4,500 VA) against 16 kW surge — comfortable
  on both.

Verdict: **one battery and the 12kPV are enough** for what the two tiers promise. Note the
12kPV puts out **8 kW AC continuous**; the "12k" in the name is its 12 kW *PV input*.

Every one of those numbers rests on an authored `duty_cycle` per circuit, and those are the
softest estimates in the model — 800 VA on the fridge circuit is a breaker allowance, not a
draw, and the calc multiplies it by 0.15 to get the ~120 W two modern appliances actually
average. **Meter it and revise.** A circuit with no `duty_cycle` is reported as an unknown
contributor and never as zero, so the calc cannot quietly flatter itself.

## The closet

`RM-B-ESS` is a 3'-3 5/8" × 4'-1 5/8" closet in the **NE** corner of the furnace room
(x 6'-0"–10'-0", y 31'-0"–36'-0" on the node lines): concrete on its north and east — the 8"
`W-B-N3` and the 12" `W-B-STR`, both existing — two `INT_ESS_CLOSET_STEEL` partitions on its
south and west (steel studs, 5/8" Type X both faces), and a 2'-0" door in the west partition
opening onto the room's open floor.

**It stood in the SE corner until 2026-08-23.** The move is the one plans/TODO.md had
recorded as BLOCKED: `EQ-B-WH`, the 24"×24" water heater, stood in the NE corner itself, and
the battery's REQUIRED ±48"/±41" separation zone has no room or wall exemption, so no
position in that corner cleared it. The owner's answer was to move the tank, which went to
(5'-6", 24'-0") — south of `EQ-B-ERV`, north of `D-B-FURN`'s swing, and east of the 36" NEC
110.26 working space in front of the panel wall. `advisory.ess_clearance` PASSES; put the
tank back and it FAILs naming `EQ-B-WH`, which is the check that the move is what unblocked
it.

Two things the relocation cost, both worth knowing:

- **Both concrete sides had to be split**, because a partition dying against the middle of an
  unsplit wall leaves a one-edge node and `integrity.wall_loop_open` (an ERROR) reports it.
  `W-B-N3` split at x=6'-0" into `W-B-N3` + `W-B-N4`, and `W-B-STR` at y=31'-0" into
  `W-B-STR` + `W-B-STR3`. The x=6'-0" line is `N-M-MECH3`, where the main storey already
  breaks, so that pair stacks one-to-one; the east wall has no such line and `W-M-STRW`
  crosses the split. `FO-M-STAIR.bearing_refs` had to gain `W-B-STR3` — without it the
  resolver emitted a 9'-0" LVL header over the stair well, which is precisely the failure
  the old comment on those refs warned about.
- **The DC run got ~10' longer.** `EQ-B-ESS-INV` and `ED-B-BACKUP-PANEL` did not move. On an
  EG4 12kPV that is a real voltage-drop question and it is the one argument that could send
  this decision back.

And one it gained: the battery hangs on **cast concrete** again (`W-B-N3`, 8"), rather than
on the steel studs the 2026-08-21 overhaul left it on. 300 lb wants that.

Smoke *and* heat alarms (`AL-B-ESS-SMOKE`, `AL-B-ESS-HEAT`), both inside the closet, both on
`CKT-LT-BACKUP` so they ride the always-on tier — an alarm that dies with the grid is the
wrong alarm for the thing that carries the house when the grid dies.

Neither the steel studs nor the Type X is code. IRC R327 permits an ESS in an ordinary
utility closet; this is owner hardening, which is why `advisory.ess_enclosure` grades it and
no CODE check does.

## Rapid shutdown: an outcome, not a preference

plans/TODO.md hoped for a transmitter on every other module. The Aptos 440 W module is
Voc 39.03 V at STC with a −0.25%/°C coefficient, so at the −30 °C design low it is **44.40 V**
— two of them sum to 88.8 V against NEC 690.12(B)(2)'s 80 V limit. Every module gets its own
SunSpec transmitter. `code.NEC_690_12_rapid_shutdown` computes that from `voc_cold` rather
than being written around the answer: a future module with a lower Voc would change the
verdict without changing the check.

Rated Voc would have said 78.1 V for a pair and passed. That is why `voc_cold` is the only
voltage the rule may read.

## Future seams

- **V2H (car as the battery).** The car becomes a second *source* on the system. The
  clean landing is another `source=True` circuit — but `code.NEC_705_12_interconnection`
  currently applies the *service* main to any panel carrying a source, because the model has
  no feeder element. A source on `ED-B-BACKUP-PANEL` needs that feeder first. The 705.12
  headroom is there: 225 × 1.2 − 200 = 70A allowed, 50A used, 20A spare on the main bus.
  `LM-EV` stays the load-management hook on the charging side.
- **Moving the ESS to the garage.** Still open, and now a bigger change than it was: the
  closet is two partitions and two wall splits, not a `room=` string.
  `code.R327_ess_capacity` already exempts garage rooms
  from the 40 kWh indoor aggregate (R327.4 treats a garage as its own permitted location),
  so the move is: re-room `EQ-B-ESS-BATT`, re-run the two conduits, move the two alarms.
  No check changes.
- **A second battery.** 28.6 kWh indoors is still inside R327.5's 40 kWh; a third is 42.9
  and fails. That article, not the closet, is the ceiling.
- **Not modeled yet:** the high-flow spigot near the battery and mechanical ventilation from
  the cabinet direct to exterior. Both are in plans/TODO.md and neither has an element to
  author against today.
