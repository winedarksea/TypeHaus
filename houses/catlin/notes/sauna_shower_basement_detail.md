---
title: "Sauna + Shower Basement Detail Notes"
applied_to:
  - detail: sauna_shower_basement_detail
tags:
  - basement
  - sauna
  - shower
  - slab
  - waterproofing
source:
  - sauna_shower_basement_detail.py
---

**2026-11-25 basement replan:** the shower and its tile splash left this room. `RM-B-BATH`
(north of the sauna, behind `W-B-SA-N`) took the 36 x 36 curbed pan (`FX-B-BATH-SH`), the
wet-wall build-up and the valve; the sauna keeps its floor drain, the condensate air gap and a
**smaller dish** (below). `FX-B-SAUNA-SH`, `WP-B-SAUNA-SPLASH`, `BK-B-SAUNA-VALVE`, the glass
partition and the Durock/valve-pocket detail are retired; the shower history is in
[shower_assemblies.md](shower_assemblies.md). Seating: [sauna_seating.md](sauna_seating.md)
(two 80 9/16 x 28 decks, finished ceiling 84 1/16 inches AFF).

# Notes

- Intent: schematic section for a sauna in a basement on slab. Confirm all dimensions, waterproofing, and structural requirements with the project drawings and manufacturers.

- Current clear room: x 122 1/2 inches to 210 inches, y 9 1/4 inches to 90 3/4 inches (about 7'-3 1/2" east-west by 6'-9 1/2" north-south). The north liner is `W-B-SA-N`, 2x6, the bath's wet wall; its bath face is glass-mat board and carries the shower, WC and lav. Current seating and finished ceiling are defined in [sauna_seating.md](sauna_seating.md).

- Entry from the gym through `D-B-SAUNA` in the east wall (`W-B-CS`, y 51"..75"). The door swings out; use the current opening coordinates rather than historical room-layout stations.

- **One floor drain, no pan.** `FX-B-SAUNA-FD` (6 x 6 grate, centre (196", 84"), x 193-199") stands in the open east aisle, NE corner, 3" north of the step. It takes the aisle's wet floor and the condensate air gap (`PR-B-COND`, `PR-B-COND-HP2-GYM`, which drop in `W-B-SA-N`'s 198 3/4"-211 3/4" bay and end 9" AFF over the grate), which keeps its trap wet. `PR-B-SAUNA-FD-DROP` (2") runs 12 3/4" north under the partition onto the bath's shared 3" `PR-B-SAUNA-DRAIN`, vent tee 6" downstream. The cleanout is a floor cap in the bath (`CO-B-SAUNA-HEAD`). The decks stand west of the aisle and need no service panel over the drain.

- Slab: slab-on-grade over vapor barrier and foam, with a thermal break around the perimeter. The slab stays flat across the room except the aisle dish (below); there is no pan, curb or threshold step inside the sauna.

- Sauna floor: dishes at 1/8" per foot to the floor drain; see "Dished floor (decision #148)" below.

- Shower and wet-wall items (pan, curb, glass partition, tile, Durock, valve pocket): **retired here**, now `RM-B-BATH` (`WP-B-BATH-SURR`, the kit's QWALL-2 surround on the glass-mat board; [shower_assemblies.md](shower_assemblies.md)). The sauna's own liner on `W-B-SA-N` is the dry, foil-faced wood liner; the glass-mat board is on the bath face.

- Electrical: supply 240V, **60A** 2-pole breaker and wiring to a 10.5 kW sauna heater (Harvia Cilindro PC110E). 2026 NEC 424.5 makes this a continuous load at 125%: 43.75 A x 1.25 = 54.7 A, which a 50A breaker will not carry — the "50A / 10.5 kW max" this note used to print was never arithmetic that closed. Pull **#6 THHN in conduit**, not #8 NM-B: NEC 334.80 caps NM-B at the 60 °C column, making #8 a 40 A conductor. **No GFCI on the heater** — 210.8(A) governs receptacles, 210.8(D)'s appliance list excludes sauna heaters, and the manufacturers advise against it in writing because moisture in the elements' magnesium-oxide fill causes nuisance trips; a 2–4 hour dry burn-in before final inspection is the fix, and a 30 mA GFPE is the fallback if the AHJ insists. The sauna **lights** are on a separate circuit; 2026 210.8(A)(6) (basements) covers receptacles, not them, so their protection follows the luminaire listing. For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: Heat-rated 24V LED tape on the new framing rails at 16 inches AFF; no line voltage inside the hot room. Keep drivers/transformers outside it.

- Ventilation: the ERV supply is a ceiling hatch over the heater (`REG-B-SUP3`, (199 3/4", 20 1/2"), a drop from `DU-B-ERV-R-SAUNA-SUP`), Harvia's inlet-near-heater layout restored with the 2026-11-25 replan (was the north end over the upper bench since 2026-11-11). The low west-wall exhaust stays at 4 inches AFF (`REG-B-EXH2`); both terminals are adjustable closeable wood vents, balanced behind the sealed door. Keep plastic vent pipe behind insulation.

- **The room floor is sealed concrete, not tile.** `RM-B-SAUNA.floor_finish` is `sealed-concrete`: densifier plus two coats on `SL-B-FLOOR`, which dishes 1/8" per foot to `FX-B-SAUNA-FD`. With the shower gone the sauna has no tile at all. Duckboards over the sealed slab in the hot zone remain an owner option and are not modelled.

- Coordinate: thresholds (flush at `D-B-SAUNA`), slip resistance, and transitions between the sealed slab and any duckboards.

## Wet-wall revision — 2026-11-09 (RETIRED 2026-11-25)

Superseded: the sauna has no wet wall. The Durock/packing build-up, valve pocket, stringer and
the sauna-temperature waterproofing qualification belonged to the shower that moved to
`RM-B-BATH`, where the wall is an ordinary 2x6 with glass-mat board and a solid-surface surround
(no temperature qualification is needed there). See [shower_assemblies.md](shower_assemblies.md).

## Dished floor (decision #148)

- **Rim level, flush with the gym.** The walls, liner foot and D-B-SAUNA threshold stay where they were. The rim is the pour's edge. FT-B-S2 (south 11 3/4" strip) and FT-B-CS (east 6 1/2" strip) are poured first, flush and flat, so those strips stay level.
- **Aisle only.** The dish is x 179 1/4"..203 1/2", y 21"..90 3/4" (the east aisle); the decks stand on flat floor west of x=179 1/4".
- **Four planes to the drain.** Screed each one from the dish edge down to the drain at (196", 84"). The south plane is the long one, 63", and it sets the drop: 1/8" x 63" / 12 = **0.657" (21/32")**. The other three planes are steeper.
- **Constant 3 1/2" slab.** Dish the capillary stone and the 2" XPS under the aisle by the same amount. The vapour retarder follows the stone.
- **Drain body 0.657" low.** Set the FX-B-SAUNA-FD strainer flush at the bottom of the dish. PR-B-SAUNA-FD-DROP starts at -0.65".
- **Decks on the rim, step in the dish.** The decks stand on flat floor and need no scribing. The step (x 179 1/4"..193 1/4", y 68"..78") lies inside the dish, so scribe its feet to it (under 0.66").
