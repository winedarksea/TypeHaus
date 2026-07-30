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

# Notes

- Intent: schematic section for a combined sauna + shower room in a basement on slab. Confirm all dimensions, waterproofing, and structural requirements with the project drawings and manufacturers.

- Room size: 12'×8'. Shower is the 4' end (4'×8'). Primary entry door is on the shower from the long (12') side wall (not shown in section).

- **Revised 2026-07-30 — curbed pan plus a floor drain, not one curbless recess.** The 4' shower end is now two things: a 36"×36" *curbed* shower pan in the north-east corner (`FX-B-SAUNA-SH`, its two closed sides on the north liner at y=13'-6 3/16" and the east liner at x=17'-2 1/2"), and a floor drain at (13'-6", 12'-9") (`FX-B-SAUNA-FD`) taking the rest of the wet floor. The three bullets below are superseded where they conflict; the wall, glass, electrical, lighting and ventilation notes still stand.

- Slabs: both sauna and shower are slab-on-grade over vapor barrier and foam, with a thermal break around the perimeter of the combined room. **The 4" recess is dropped:** with a curb around the pan and a floor drain outside it, the slab stays flat across the whole room and the pan is built up on top of it. That also removes the step at the sauna/shower line the old scheme needed a threshold detail for.

- Sauna floor: slopes 1/8" per foot down toward the floor drain — now 11'-9" of run to (13'-6", 12'-9") rather than 8', so ~1 1/2" total rather than 1". Detail shown as sloped slab schematically. The wet floor outside the pan slopes to the same drain, so there is one low point in the room and no dam between the two zones.

- Shower floor: finish is built up using foam tile backer (GoBoard or other polyiso-based board preferred) and wedges. **Inside the pan**, slope to the pan drain at IRC P2708.1's 1/4"–1/2" per foot, built up over the flat slab. Coordinate with drain height and waterproofing membrane. Neither slope is carried in the model — `Slab` and `FinishZone` have no slope field — so these numbers and the plan-source comments in `plan/fixtures.py` are the record.

- Curb: around the pan's two *open* sides only (south and west). The closed sides are finished wall. The plan symbol draws a single curb bar; build both.

- Drains: the pan's is centred in the 36"×36" pan. The floor drain sits 8 1/2" west of the pan's curb and 12" south of the north liner — against the wall, not mid-floor, because that corner is where the boxed chase carrying `PR-B-COND`'s air-gap drop comes down (the heat-pump condensate terminates over this drain since FX-1 was retired), and it is east of `D-B-SAUNA`'s leaf, which sweeps only to x=11'-1 13/16". Both drains run under the slab on `PR-B-SAUNA-DRAIN` (2", 4 DFU) and vent through `PR-B-SAUNA-VENT`, whose riser stands in `W-B-CS`'s liner build-up at x=17'-4" — in the pan's own east wall, so nothing is cut through the sauna partition's foil-faced vapour barrier.

- Shower walls: foam tile backer board to ceiling (polyiso backer preferred for heat tolerance); finish with tile system and compatible waterproofing.

- Partition: glass shower enclosure wall + 36" glass divider door between shower and sauna. Partition is elevated leaving a 1" gap at bottom for air + water flow. Use 1/2" tempered glass with 2–3 spigots (sealant anchor method) and ≥1" standoff; maintain cleanable, durable edges at the floor.

- Electrical: supply 240V, 50A GFCI breaker and wiring to sauna heater (max 10.5 kW). For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: IP65-rated LED strips concealed under lower bench lips + one waterproof wall sconce; keep drivers/transformers outside hot zone.

- Ventilation: include HRV/ERV connections with adjustable cedar vent registers; intake low and away from heater, exhaust high above/near heater. Keep plastic vent pipe behind insulation.

- Coordinate: thresholds (now flush throughout — see the slab note), the pan curb's two open sides, slip resistance, and transitions between sauna membrane/duckboards and shower tile.

