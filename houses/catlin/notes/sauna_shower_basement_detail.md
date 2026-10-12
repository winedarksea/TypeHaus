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

**Seating revision, 2026-10-11:** [sauna_seating.md](sauna_seating.md) supersedes earlier
bench layouts and heights. Independent 42/24-inch levels, a 78 × 28-inch lying
bench, south reading recliner and removable service decks are now modeled. Finished ceiling
is 82 13/16 inches AFF; use that surface for headroom and heater checks.

# Notes

- Intent: schematic section for a combined sauna + shower room in a basement on slab. Confirm all dimensions, waterproofing, and structural requirements with the project drawings and manufacturers.

- Current clear room: approximately 7'-3" east–west by 8'-10 11/16" north–south; use the resolved polygon for the north-wall jog. The main west liner face is x=122 13/16 inches, east face x=209 3/4 inches, south face y=9 1/2 inches and north face y=116 3/16 inches. The 36 × 36-inch curbed shower occupies the north-east corner. Current seating and finished ceiling are defined in [sauna_seating.md](sauna_seating.md).

- Entry from the gym through `D-B-SAUNA` in the east wall. The door swings out; use the current opening coordinates rather than historical room-layout stations.

- **Curbed pan plus a floor drain, not one curbless recess.** The wet end has two separate receptors: a 36"×36" *curbed* shower pan in the north-east corner (`FX-B-SAUNA-SH`, its two closed sides on the north liner at y=9'-8 3/16" and the east liner at x=17'-5 3/4"), and a floor drain at (13'-6", 8'-2 3/16") (`FX-B-SAUNA-FD`) taking the rest of the wet floor, on the pan's own centre line, 8 3/4" clear west of the curb; `PR-B-SAUNA-DRAIN`, both condensate air gaps and `SP-B-SAUNA-FD` sit with it. The three bullets below are superseded where they conflict; the wall, glass, electrical, lighting and ventilation notes still stand.

- Slabs: both sauna and shower are slab-on-grade over vapor barrier and foam, with a thermal break around the perimeter of the combined room. **The 4" recess is dropped:** with a curb around the pan and a floor drain outside it, the slab stays flat across the whole room and the pan is built up on top of it. That also removes the step at the sauna/shower line the old scheme needed a threshold detail for.

- Sauna floor: slopes 1/8" per foot down toward the floor drain at (13'-6", 8'-2 3/16") — about 8'-6" of run from the room's far south-west corner, so ~1 1/8" total. Detail shown as sloped slab schematically. The wet floor outside the pan slopes to the same drain, so there is one low point in the room and no dam between the two zones.

- Shower floor: finish is built up using foam tile backer (GoBoard or other polyiso-based board preferred) and wedges. **Inside the pan**, slope to the pan drain at IRC P2708.1's 1/4"–1/2" per foot, built up over the flat slab. Coordinate with drain height and waterproofing membrane. Neither slope is carried in the model — `Slab` and `FinishZone` have no slope field — so these numbers and the plan-source comments in `plan/fixtures.py` are the record.

- Curb: around the pan's two *open* sides only (south and west). The closed sides are finished wall. The plan symbol draws a single curb bar; build both.

- Drains: the pan drain is centered in the 36 × 36-inch pan. The separate 6 × 6-inch floor grate is centered at (162, 98 3/16) inches, 18 inches south of the north liner and 8 3/4 inches clear west of the pan's west curb. It is beneath `FURN-B-SAUNA-LOWER`, with removable deck panels and an open frame. Both condensate drops descend in the north-wall cavity and run beneath the deck, ending 9 inches AFF over the floor grate at x=162 and x=160 inches. Both sanitary receptors connect below the slab to `PR-B-SAUNA-DRAIN`; the vent riser remains in the east-wall liner. Keep all access panels and the aisle cleanout cap reachable; see sauna_seating.md.

- Shower walls: foam tile backer board to ceiling (polyiso backer preferred for heat tolerance); finish with tile system and compatible waterproofing.

- Partition: glass shower enclosure wall + 36" glass divider door between shower and sauna. Partition is elevated leaving a 1" gap at bottom for air + water flow. Use 1/2" tempered glass with 2–3 spigots (sealant anchor method) and ≥1" standoff; maintain cleanable, durable edges at the floor.

- Electrical: supply 240V, **60A** 2-pole breaker and wiring to a 10.5 kW sauna heater (Harvia Cilindro PC110E). NEC 424.3(B) makes this a continuous load at 125%: 43.75 A x 1.25 = 54.7 A, which a 50A breaker will not carry — the "50A / 10.5 kW max" this note used to print was never arithmetic that closed. Pull **#6 THHN in conduit**, not #8 NM-B: NEC 334.80 caps NM-B at the 60 °C column, making #8 a 40 A conductor. **No GFCI on the heater** — 210.8(A) governs receptacles, 210.8(D)'s appliance list excludes sauna heaters, and the manufacturers advise against it in writing because moisture in the elements' magnesium-oxide fill causes nuisance trips; a 2–4 hour dry burn-in before final inspection is the fix, and a 30 mA GFPE is the fallback if the AHJ insists. The sauna **lights** do take GFCI under 210.8(A)(5), which is why they are a separate circuit. For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: Heat-rated 24V LED tape on the new framing rails at 16 inches AFF; no line voltage inside the hot room. Keep drivers/transformers outside it.

- Ventilation: retain the modeled ERV supply above the heater and the low west-wall exhaust at 4 inches AFF; both terminals are adjustable. Keep plastic vent pipe behind insulation.

- **The room floor is sealed concrete, not tile.** `FX-B-SAUNA-SH` is a curbed *liner* pan: it brings its own waterproof floor inside the curb, so there is no tile bed to lay there and no reason to tile the wet floor outside it either. `RM-B-SAUNA.floor_finish` is `sealed-concrete` — densifier plus two coats on `SL-B-FLOOR`, which already slopes 1/8" per foot to `FX-B-SAUNA-FD`. The tile that remains in this room is `WP-B-SAUNA-SPLASH`, the pan's two closed wall sides, unchanged. The "shower tile" and "foam tile backer" bullets above are superseded for the *floor*; the wall build-up still stands. Duckboards over the sealed slab in the hot zone remain an owner option and are not modelled.

- Coordinate: thresholds (now flush throughout — see the slab note), the pan curb's two open sides, slip resistance, and transitions between the sealed slab, any duckboards, and the pan curb.
