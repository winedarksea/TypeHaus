---
title: "Water service, heater envelope, thermal expansion and the tank's floor"
applied_to:
  - equipment: EQ-B-WH
  - equipment_type: EQ-T-WATER-HEATER
  - pipe_run: PR-G-HYDRANT-CW
  - pipe_run: PR-B-CW-TRUNK
tags:
  - plumbing
  - water-supply
  - water-heater
source:
  - plan/mep_hvac.py
  - plan/mep_supply.py
  - plan/mep_drainage.py
---

# Notes

Written 2026-10-29. Research only where it says so: **no expansion device is modelled and no
price row exists for one.**

## 1. The heater, as Rheem publishes it (PROPH80 T2 RH400-30)

Sources: the RH400-30 spec sheet (Quick Start Connection Guide, rheem.com related document
436312), HP-400-SO 07/24 (the PROPH80's sheet), the Use & Care manual p.5-12. The dimension-sheet
link in the old TODO is dead (404); the same lettered dimensions are on both sheets above.

| letter | what | PROPH80 |
|---|---|---|
| A | tank height | 74 3/16" |
| B | tank diameter | 24 1/4" |
| C | condensate connection (3/4" NPT female) | 59" |
| D | cold inlet and drain (side connects) | 3 7/8" |
| E | hot outlet and T&P (side) | 42 3/8" |
| F x G | plan envelope incl. T&P / fittings | 29 1/2" x 24 5/8" |
| H | overall height, **ducted** (8" elbow on top) | 91" |
| K | overall height, not ducted (to the top nipples) | 76 13/16" |

- The model is **76 13/16" high, not 91"**: 91" is the duct-ready unit and this house does not
  duct it. Top nipples are at K, **scaled off the top-view drawing**: hot 4 1/8" left of the
  axis and 1 1/2" toward the back, cold 4 1/8" right and 1 1/2" forward (+-0.3").
- Clearances: **min 0" rear and sides, 6" above for the washable filter** (6" all round "for
  easier serviceability"); non-ducted exhaust 6" off any wall or hard surface; 2" off the T&P
  side for its release. Room > 1200 ft3 needs no louvres (this room is ~1,250 ft3).
- **Fit under the 96 15/16" ceiling:** 76 13/16" + 6" = 82 13/16" fits with 14 1/8" in hand. The
  91" ducted unit + 6" = 97" would **not** (0.06" short): ducting is closed by the ceiling.
- **Rotation 0 now** (was 180). The published hot nipple is the product's left one, so rotation
  0 puts hot west and cold east exactly as before, and puts the front (display, condensate)
  south, onto `PR-B-ERV-COND`'s lane. T&P is west (the old `PR-B-WH-TPR` side) at 42 3/8".
- **Open, binding numbers.** (a) The slot between the ERV case's east face (93.03") and the
  east foundation wall (117.125") is 24.095"; the tank is 24.25". The body is flush to the wall
  and laps the case by 0.155" (the case hangs at 54", so only the 16-gon's equator corner
  meets it). (b) The sheet's 29 1/2" plan envelope does not fit that slot either way round: the
  T&P valve and its 2" release land on the ERV case side. They are at 42", under the case
  (54"), so it clears in section, but a plan clearance zone cannot say so (it read as a conflict
  and was dropped). (c) **The air exhaust faces the east wall at 0"**, against Rheem's 6" for a
  non-ducted unit. Closing it means ducting (the ceiling rules that out, above) or a louvre /
  exhaust redirect; or turning the unit, which puts the front on the wall or the ERV. **Owner
  decision needed**; modelled as a RECOMMENDED zone that the wall does not report.

Hot trunk: it crosses the tank at 6'-6 5/16" (the 69.5" level cannot pass a 76 13/16" tank),
then drops in the round tank's empty corner (x 93.7") to 5'-9 1/2", where it must stay to pass
under `DU-B-ERV-RET-TRUNK`'s rising leg; going over that duct hits the extract plenum.

## 2. Condensate

`PR-B-WH-COND`: 3/4" PVC from the port (59") down 10 5/8" and 3" south onto `PR-B-ERV-COND`'s
y=340" leg (48.19" up there), which already falls to the `FX-B-BATH-LAV` air gap. Rheem: pitch
>= 1/8"/ft, 3/4" minimum, never into the heater's own pan, trap only if it meets a sewer
(it does not: it ends at an air gap). `mep.drain_slope` and `mep.drain_tie_in` pass. The ERV
line now carries both appliances; a heat-pump water heater makes roughly 1/2-1 gal a day in
summer, so the allowance is a rounding error against the ERV core's.

## 3. The service lateral

`PR-G-HYDRANT-CW` **is** the service lateral: the buried line from the entry (11', 48'-6") to
the house at (11', 35'-6"), 6' under grade. It was authored 3/4" serving only the yard hydrant,
so `PR-B-CW-TRUNK` (1 1/4", 39 WSFU) had no feeder and the router refused. It is now 1 1/4"
and carries the trunk's whole load plus the hydrant, so the trunk's tee derives it as parent.
The **street main, curb stop and meter are Saint Paul's and are not runs in this model.**

Its two sleeves, `SP-B-N3-HYD` (wall) and `SP-GF-S-HYD` (garage footing), were resized with
it to 2 1/2" and 3" for the 1 1/4" PEX (1.375" OD) in `plan/mep_sleeves.py`.
`PA-G-HYD-BFP` (3/4" dual check) sits **on the trunk riser**: if it really is in series with the
house, the house is a closed system and the 3/4" part throttles a 1 1/4" trunk. The device
comment says the hydrant branch order is unresolved; resolve it with the question below.

## 4. Thermal expansion (research; nothing modelled)

**What the code says.** Minn. R. 4714.0050 adopts the **2018 UPC**, Chapters 2-11, 16, 17.
Minn. R. 4714.0608 (the part titled "Water pressure, pressure regulators, pressure relief
valves...") amends **only 608.5**, the discharge piping; it does not touch 608.2 or 608.3, so
both apply as printed (revisor.mn.gov/rules/4714.0608, read 2026-10-29).
- UPC 608.2 (secondary source, not read in the 2018 text): static pressure over 80 psi needs
  a pressure-reducing valve, on the street side of the meter in West St. Paul's own handout.
- UPC 608.3 (IAPMO 2018 UPC Illustrated Training Manual, Codes Spotlight 2018-08-16): a system
  with "a check valve, backflow preventer, or other normally closed device" needs "an approved,
  listed, and adequately sized expansion tank" on the **building side** of that device. It does
  not name the meter.

**What I could not find.** I found **no Saint Paul Regional Water Services statement** of (a)
whether its meter sets carry a check or dual check, or (b) a typical or maximum static pressure.
The SPRWS water supply plan lists five pressure zones and ~94,000 Neptune meters and gives no
psi; its FAQ pages did not load. Generic sources put US homes at 40-80 psi, which is no
evidence for this parcel. (West St. Paul is a different utility.) **Ask SPRWS Engineering,
651-266-6270 / water service desk 651-266-6350**, two questions: does the meter set include a
check valve, and what is the static pressure at the (still unchosen) parcel's main.

**Reading of the model.** Today it has no PRV, no meter check and no expansion device. The
only checks drawn are dual checks on small branches (`PA-B-BFP-BATH`, `-SAUNA`, 1/2") and
`PA-G-HYD-BFP` (above). If the meter has a check, or `PA-G-HYD-BFP` is in series, the heater is
on a closed system.

**Recommendation.** Do **not** rely on the T&P: it is for temperature/pressure runaway, and
Rheem's own manual (p.10) says to fit an expansion tank where the system is closed. Assume
closed until SPRWS says otherwise and put a **listed potable expansion tank on the cold feed at
the tank inlet, downstream of the stop `PA-B-WH-STOP-CW`**, with its air charge set to the
measured static pressure. An 80 gal tank heated roughly 50 to 130 F expands by about 1.3 gal,
so a 2 gal class tank at 40-60 psi is the usual size (verify against the maker's table). If
measured static pressure is over 80 psi add a PRV ahead of the meter set. Add the device to the
model and to `prices.toml` only after the answer: both are deliberately absent.

## 5. The floor under the tank: no plinth

The tank stays on the slab (`MountKind.FLOOR`, `elevation=None`).
- No stand: the 18" ignition rule is for fuel-fired units in garages; a heat-pump unit has
  none. Rheem asks only for a floor that takes the filled weight (about 950 lb: 281 shipped + 80 gal) and a vibration
  kit only on non-concrete floors.
- No pan: UPC/Rheem want a pan only where a leak damages the area below or adjacent. This
  tank stands on the basement slab; nothing is below it. Its own T&P discharge and the
  heater's LeakGuard-class sensor (not on the RH400-30; optional AP19134) are the protection.
  Condensate must **not** drain into a pan (Rheem), which is one more reason not to add one.
- Flood: the exposure is a burst pipe or tank failure, not groundwater, and the room walks out
  onto a drained court with a 7 1/4" threshold. A 4" pad would buy a few inches against a
  slow leak and would move the 76 13/16" top nipples, every literal quoting them and the 6"
  filter clearance; not worth it. Closed.
