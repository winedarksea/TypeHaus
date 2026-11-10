---
title: "Water service, heater envelope, thermal expansion and the tank's floor"
applied_to:
  - equipment: EQ-B-WH
  - equipment_type: EQ-T-WATER-HEATER
  - pipe_run: PR-G-HYDRANT-CW
  - pipe_run: PR-G-SERVICE-CW
  - pipe_run: PR-B-CW-TRUNK
  - equipment: EQ-B-HW-HEADER
  - pipe_run: PR-B-HW-TRUNK
tags:
  - plumbing
  - water-supply
  - water-heater
source:
  - plan/mep_hvac.py
  - plan/mep_supply.py
  - plan/mep_drainage.py
  - plan/mep_supply_header.py
---

# Notes

Written 2026-10-29. Research only where it says so: **no expansion device is modelled and no
price row exists for one.**

## 1. The heater, as Rheem publishes it (PROPH80 T0 RH120-MSO)

The 120 V, element-free plug-in (`notes/backup_power.md` §5), 2026-11-02. Sources: spec sheet
RH-PIHP-SC-SO Rev. 7 (03/25) p.2; Use & Care p.11 (typical installation) and p.34.

| letter | what | PROPH80 |
|---|---|---|
| A | tank height (top, filter grille) | 74 3/16" |
| B | tank diameter | 24 1/4" |
| C | condensate (3/4" NPT female) | 59" |
| D | drain valve / bottom of the HydroBoost riser | 3 7/8" |
| E | hot outlet, top fitting of the riser | 42 3/8" |
| F x I | plan envelope incl. T&P and riser | 29 1/2" x 29" |
| G | top of the riser cover | 54 5/16" |
| H | overall height, **ducted** | 91" |
| J | ducted plan depth | 27 3/8" |
| K | cold inlet | 5 1/16" |

3/4" NPT hot and cold, "use MIP fittings". Factory cord "plugs directly into a standard wall
outlet" (grounded; not a circuit already loaded past half its breaker). Clearances 0" rear and
sides, 6" above for the filter, 6" all round for service, 2" for the T&P release, non-ducted
exhaust 6" off any wall. Heat trap 6" min on the cold; flexible connections recommended (here
copper or listed stainless flex: UPC 604.13 bars PEX in the first 18").

**Ports (model, `EQ-T-WATER-HEATER`).** Heights published except the T&P's; every plan
position SCALED off p.2 (+-1"). Tank at (137 1/2", 201 3/8") in `RM-B-WORKSHOP`'s north-east
corner since 2026-11-09, open in the room, back on `W-B-CW2` (0" allowed), riser lobe 14" off
`W-B-HALL-W`; rotation -40: front (display) south-west over the 30x30 working space, the
side exhaust south-east.

| port | product frame | world (x, y, z AFF) |
|---|---|---|
| hot (E) | ~70 deg right of front, r ~15" | (145.0", 188.4", 42 3/8") |
| cold (K) | ~42 deg right of front, r ~16", riser foot | (138.0", 185.4", 5 1/16") |
| T&P outlet | ~20 deg left of front, r ~15.4", ~46" scaled | (124.1", 193.7", ~46") |
| condensate (C) | front-left shoulder | (124.7", 197.8", 59") |
| top inlet (`air-in`) | top centre, under Rheem's adapter and elbow | (137.5", 201.4", 74 3/16") |
| side exhaust (`air-out`) | ~70 deg right of front, 65 1/2" (scaled) | (143.6", 190.9", 65 1/2"), points south-east |

The riser cover is drawn as a lobe on the footprint, south-south-east in plan, full height
though it stops at G. Model height is A, 74 3/16". Filter (top) wants 6" over the tank.

**Why here (owner, 2026-11-09).** The workshop keeps its area and gains no walls or door;
both air connections are ducted through `W-B-HALL-W` to two grilles in the stair hall, so the
chill and the evaporator's air are the hall's and the shop's dust stays off the filter. The
under-stair closet (its home for part of that day) left the condensate line in
`D-B-CLOSET`'s doorway, looped the exhaust and could not take a ducted inlet; `D-B-CLOSET`
is plain storage again, the full-height way in to `PA-B-MAIN-SHUTOFF`.

**Air.** Both ducted, `plan/mep_hpwh_air.py`: Rheem's rules, parts and holds are in
`notes/basement_winter_heat.md` "Air connections".

**Pan.** None, as §5: UPC 507.5 / IRC P2801.6 want one only where a leak would damage the
building; this tank stands on the slab with nothing below, and `AL-B-WH-LEAK` sits beside
its riser foot.

**Runs** (developed lengths off the model):
- `PR-B-HW-TRUNK` (7.2 ft, was 19.3): a 3" stub on the hot tap's axis, a 90 to x=12'-9 3/4",
  up to 95 1/2", north and east, and down into `EQ-B-HW-HEADER`'s inlet beside the tank.
- `PR-B-CW-WH` (9.0 ft, was 30.8): tees off `PR-B-CW-TRUNK` over the tank and drops on the
  inlet's axis 3" off the tap. The full-height drop is the heat trap; `PA-B-WH-STOP-CW` is on
  it at 48". `PR-B-CW-BATH` tees off the trunk's x=4'-9" leg now.
- `PR-B-WH-TPR`: full-size 3/4" copper, a 2" stub pitched down, then straight down beside
  the tank to an air gap 6" over the workshop slab. Never into the condensate.

## 2. Condensate

`PR-B-WH-COND` (5.3 ft): 3/4" PVC off the port's axis, west along the tank's side, north at
x=9'-8" through `W-B-CW3`, and down to its own air gap 13" over `FX-B-UTIL-SINK`'s rim, 6"
from `PR-B-ERV-COND`'s. Every leg >= 1/4"/ft. Rheem: pitch >= 1/8"/ft, 3/4" minimum, never
into the heater's own pan, trap only if it meets a sewer (it ends at an air gap). It crosses
no doorway or swing. A heat-pump water heater makes roughly 1/2-1 gal a day in summer, a
rounding error against the ERV core's.

## 3. The service lateral and the hydrant branch

**The hydrant tees off the trunk (owner, 2026-10-29).** `PR-G-SERVICE-CW` (1 1/4" PEX) is the
lateral, street entry (11'-4", 48'-6") to the house at (11'-4", 35'-6"), 6' under grade, through
`SP-GF-S-SVC` (3", under `FT-GF-S-DR`) and `SP-B-N2-SVC` (2 1/2", `W-B-N2`). It feeds
`PR-B-CW-TRUNK` alone, which rises past `PA-B-MAIN-SHUTOFF` (3'-0") 6" inboard at y=35'-0"
(2026-10-31: on the 35'-6" line the riser, tee and dual check stood 2" inside `W-B-N2`'s
concrete; 35'-0" is a bay between `ST-B2M`'s landing joists, so no joist is cut). `PR-G-HYDRANT-CW` (3/4")
tees off that riser at 4'-0", carries `PA-G-HYD-BFP` (3/4" dual check, 3'-0", beside the main
shutoff), leaves through `SP-B-N3-HYD` (back to 1 1/2") and runs 4" west of the lateral to the
yard hydrant through `SP-GF-S-HYD` (back to 2"). The **house trunk is open**: the dual check
guards the hydrant branch only, and the main shutoff isolates the hydrant too. The **street
main, curb stop and meter are Saint Paul's and are not runs in this model.**

The lateral passes 4" east of the hydrant's buried valve, inside its weep stone
(`DRW-G-HYDRANT`), and the street utility line moved to x=11'-4" with it (`plan/site.py`).
`mep.hydrant_freeze_depth` now ignores a vertex inside a conditioned room (the branch's tee and
drop, the trunk), since a warm high point is not a freeze point; the buried legs hold 72".

### Fixture branches (2026-10-31)

Every WC stop, shower and tub valve body and the dishwasher has a branch reaching its port
(`plan/mep_supply_branches.py`, all 1/2" PEX except the hall bath's 3/4" shower cold, which
also feeds its WC: 5.5 WSFU). WCs get an angle stop each. Three are floor-fed: `FX-M-BATH2-WC`
(its wall bay is `FX-M-BATH1-WC`'s DuoFit carrier), `FX-S-BATH1-WC` (owner: no pipe in exterior
`W-S-W1`; the stop tees off the shower cold in the chase and runs through `FS-S-WEST`) and
`FX-B-BATH-WC`'s is wall-fed but off the trunk, because the x=10'-0" bearing line's blocking
closes the bath's own riser off. The hall bath's shower pair runs north in `FS-ATTIC`'s webs and
drops down `W-S-CH-W`: `DU-M-ERV-EXH-TRUNK` fills `FS-S-WEST`'s depth between the risers and the
chase. `PA-M-DW-WHA-HW` is on the dishwasher's own stub. The sauna's stubs were swapped so hot
meets the R10000's hot-left inlet. Updated 2026-11-09: all five showers now have axial
side-hub arrivals from shared assemblies. The sauna is centred on the east wall; BATH1's
WC tee stays at its original chase drop, and the attic elbows move into the hub plane above
the vents. [Shower assembly coordination](shower_assemblies.md) records the stations,
BATH2's retained hot/drain clearance, and the outstanding sauna material qualification.

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
only checks drawn are dual checks on branches (`PA-B-BFP-BATH`, `-SAUNA`, 1/2";
`PA-G-HYD-BFP`, 3/4", hydrant only since 2026-10-29), none in series with the heater. So the
heater is on a closed system only if the meter set has a check: **still to confirm with
SPRWS.**

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
  heater's LeakGuard sensor are the protection.
  Condensate must **not** drain into a pan (Rheem), which is one more reason not to add one.
- Flood: the exposure is a burst pipe or tank failure, not groundwater, and the room walks out
  onto a drained court with a 7 1/4" threshold. A 4" pad would buy a few inches against a
  slow leak and would move every port literal and the 6" filter clearance; not worth it.
  Closed.

## 6. The hot side: a header, not a trunk with tees (owner, 2026-11-03; modelled 2026-11-04)

**The study** (2026-11-03, prices are ranges, no quotes). A full PEX home-run with a
two-sided manifold came out about level with the trunk-and-branch it would replace
(~$7.3-12.3k against ~$7.2-11.9k): catlin is already PEX-A, so the labour a home-run saves on
fittings is mostly already saved, MN 4714.0610 holds every branch to 1/2" (no 3/8" lav runs),
and ~26 tubes would have to rise through cavities that are already tight. A hot-side header
alone is ~$0.3-0.7k cheaper and cuts the wait for hot water; the cold side has nothing to
gain and stays a trunk. No recirculation is modelled and the header makes one unnecessary,
which suits a heat-pump heater that should not be fed a recirc loop's return.

**What is built.** `PR-B-HW-TRUNK` (1" copper) ends at `EQ-B-HW-HEADER`, an Uponor
LF2821050: 1" copper body, 1" sweat supply, eight 1/2" ProPEX LF brass outlets on 1 1/2"
centres (Uponor submittal "ProPEX (type L) copper branch manifolds", read 2026-11-04;
SupplyHouse lists the 10-outlet LF2831050 at $202.82 the same day, and Uponor's sheet calls
the line made to order). `PR-B-HW-SBATH` (5.25 WSFU) and `PR-B-HW-SUITE` (6.75 WSFU: it
carries the studio) need 3/4" by `mep.pipe_sizing`, and a 1/2" outlet cannot feed them, so
both tee off the trunk ahead of the header. 1/2" lines need no insulation (N1103.4.2 starts
at 3/4").

**The header beside the heater (2026-11-09).** With the tank in the workshop's north-east
corner the header hangs right beside it (x=13'-4", outlets down at 86 1/8"), and the trunk is
7.2 ft instead of 19.3. A foot of 1" copper holds what 4.7 ft of 1/2" PEX does, so the
shortest trunk is the shortest wait. Branch lanes: `plan/mep_supply_header.py`.

**Volumes, worked by hand** (gal/ft from the inside diameter: 1" type L copper, ID 1.025",
0.0429; 1/2" PEX-A, ID 0.475", 0.0092; 3/4" PEX-A, ID 0.681", 0.0189; 3/4" type L copper, ID
0.785", 0.0251). Developed lengths off the model, tap to fixture stub, each with the whole
trunk (conservative for the two 3/4" tees): 19.3 ft x 0.0429 = 0.83 gal before, 7.2 ft x
0.0429 = 0.31 gal now.

| fixture | branch ft (closet) | gal (closet) | branch ft (now) | gal (now) |
| --- | --- | --- | --- | --- |
| kitchen sink, `PR-B-HW-KITCH` | 57.0 | 1.35 | 42.9 | 0.71 |
| main bath shower, `PR-B-BATH2-SH-HW` | 17.1 | 0.99 | 14.5 | 0.44 |
| main bath tub, `PR-B-FILLER-HW` | 12.5 | 0.94 | 12.4 | 0.43 |
| main bath sink, `PR-B-HW-BATH2` | 22.1 | 1.03 | 22.6 | 0.52 |
| laundry, `PR-B-HW-WASH` | 16.5 | 0.98 | 12.9 | 0.43 |
| sauna shower, `PR-B-HW-SAUNA` | 32.1 | 1.12 | 19.7 | 0.49 |
| powder lav, `PR-B-HW-BATH1` | 12.8 | 0.95 | 20.8 | 0.50 |
| basement lav, `PR-B-HW-BATH` | 15.8 | 0.97 | 14.2 | 0.44 |
| suite and attic (`PR-B-HW-SUITE`, 3/4" PEX) | 41.0 | 1.60 | 25.6 | 0.80 |
| hall bath upstairs (`PR-B-HW-SBATH`, 3/4" copper) | 21.8 | 1.37 | 39.7 | 1.31 |

At 1.5 gpm the kitchen waits ~28 s (was ~54 s in the closet). Only the powder lav's branch
got longer (it now crosses from the workshop), and it still waits less: the trunk it
shares is 12 ft shorter. The hall bath upstairs is the longest wait left; a ninth outlet
cannot feed it (3/4" by `mep.pipe_sizing`).

**Pressure on the 1/2" kitchen branch, by hand (2026-11-08).** Hazen-Williams, C = 150, ID
0.475": psi/100 ft = 0.433 x 0.2083 x (100/150)^1.852 x Q^1.852 / 0.475^4.8655. Length was
`PR-B-HW-KITCH`'s 57.3 ft off the model (42.9 ft since 2026-11-09, so these losses fall by a quarter), plus 15% for fittings (an allowance) = 66 ft. Lift
is 86.1" to 129.4", 3.6 ft = 1.6 psi.

| case | Q | loss | with lift | velocity |
| --- | --- | --- | --- | --- |
| sink alone | 1.5 gpm | 3.37 psi/100 ft, 2.2 psi | 3.8 psi | 2.7 ft/s |
| sink + dishwasher filling (1.5 gpm assumed) | 3.0 gpm | 12.2 psi/100 ft, 8.0 psi | 9.6 psi | 5.4 ft/s |

The basin (`PR-B-HW-BATH1`, 12.8 ft, 1.2 gpm) loses under 0.5 psi. So the sink holds a 15 psi
fixture minimum (the usual UPC 608 figure, not read here) with about 25 psi at the header, even
with both running. Against the still-unmeasured street pressure above, that is the number to
compare. The 3.0 gpm case is worst-case; the dishwasher's fill rate is an assumption.

**BATH2 drain bay coordination, 2026-11-09.** The new y=186-inch TJI requires the BATH2-lavatory
and sauna hot turns at y=188 inches. The sauna hot crosses at x=195 to
separate its web bore from the x=200 cold trunk. The shower hot riser is y=189.5 and its
48-inch valve station stays fixed. `notes/bath2_shower.md` §5 gives the drain and framing
setout; manifold outlets and branch diameters are unchanged.

`mep.water_manifold_ports` holds one run per outlet. `haus route houses/catlin --manifold
EQ-B-HW-HEADER` re-lays the eight together; per-branch proposals for the workshop header ran
branches through `W-B-HALL-W`'s cavity and around the furnace room, so the lanes were drawn by
hand (fixture-end legs kept) and graded by `haus check` (0 FAIL).

