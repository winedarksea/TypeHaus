---
title: "Water service, heater envelope, thermal expansion and the tank's floor"
applied_to:
  - equipment: EQ-B-WH
  - equipment_type: EQ-T-WATER-HEATER
  - pipe_run: PR-G-HYDRANT-CW
  - pipe_run: PR-G-SERVICE-CW
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
position SCALED off p.2 (+-1"). Tank at (8'-9", 29'-5"), rotation -90: front west, right south
(exhaust), left north, back east on `W-B-STR3`.

| port | product frame | world (x, y, z AFF) |
|---|---|---|
| hot (E) | ~70 deg right of front, r ~15" | (99.9", 338.9", 42 3/8") |
| cold (K) | ~42 deg right of front, r ~16", riser foot | (93.1", 342.3", 5 1/16") |
| T&P outlet | ~20 deg left of front, r ~15.4", ~46" scaled | (90.5", 358.3", ~46") |
| condensate (C) | front-left shoulder | (94", 360.5", 59") |

The riser cover is drawn as a lobe on the footprint, 40-75 deg right of front at r 15" (south-
west in plan), full height though it stops at G. Model height is A, 74 3/16": the top nipples
are gone and nothing sits on top. Filter clearance: the nearest thing over the top is
`DU-B-ERV-R-GYM` / `-R-PLAY` at 82" (7 13/16").

**What it clears.**
- `D-B-CLOSET` (75-degree stop): its sweep stays 2 1/4" off the riser lobe and 2.95" off the hot
  tap's centreline. Scaled +-1", so this is the number to check on the delivered unit.
- ERV case: 0.04" at the tank (unchanged). The T&P outlet sits under its 54" bottom, ~8" below
  it (scaled); the valve faces west-north-west into open air under the case, its 2" release
  clear (`PR-B-WH-COND` is ~4" away).
- `W-B-ESS-S`: 4 1/2" body-to-wall, nothing of the heater on that side now. `ED-B-WH-RC`
  (CKT-WH, GFCI at the device) is on its south face at x 8'-4", 77"-81", 3" above the tank top:
  the cord leaves the top front-left and never crosses the south exhaust zone.

**Runs.**
- `PR-B-HW-TRUNK`: west from the hot tap at 42 3/8" along the riser face to x=94", up to
  5'-9 1/2", west under `DU-B-ERV-RET-TRUNK` (bottom 72 5/8") to the x=83" riser, then its old
  route. 5.9" off that duct's rising leg.
- `PR-B-CW-WH`: ceiling leg to (93 1/2", 27'-11 1/2"), 3.3" outside the door's sweep and south of
  the extract plenum; falls to 5 1/16" and runs 6 3/4" north onto the tap. The full-height drop
  is the heat trap. `PA-B-WH-STOP-CW` is on the drop; `PR-B-CW-BATH` now tees off the ceiling
  leg at x=7'-0".
- `PR-B-WH-TPR`: full-size 3/4" copper, a 2" stub pitched down, then straight down to an air gap
  6" over the slab under the ERV case. Not threaded at its end, never into the condensate.

## 2. Condensate

`PR-B-WH-COND`: 3/4" PVC from the port (59", facing the ERV case) straight down to 52 1/2", then
6 7/8" north past the tank's NW corner onto `PR-B-ERV-COND` behind it (51.6" there, 1.5"/ft).
That line runs east through the tank's 4 1/2" north gap and `W-B-STR3`, across the under-stair
storage, west inside `W-B-BA-N` and down `W-B-STR2`'s mech face to the `FX-B-UTIL-SINK` air gap
(>= 0.33"/ft). Rheem: pitch >= 1/8"/ft, 3/4" minimum, never into the heater's own pan, trap only
if it meets a sewer (it ends at an air gap). `mep.drain_slope` and `mep.drain_tie_in` pass. A
heat-pump water heater makes roughly 1/2-1 gal a day in summer, a rounding error against the
ERV core's.

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
meets the R10000's hot-left inlet.

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
