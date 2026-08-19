---
title: "Sauna Basement Wall Detail Notes"
applied_to:
  - detail: sauna_basement_wall_detail
tags:
  - basement
  - sauna
  - slab
  - waterproofing
  - insulation
source:
  - sauna_basement_wall_detail.py
---

# Notes

- Detail intent: schematic section showing sauna interior finishes, slab, and foundation bearing. Confirm all dimensions with the project plan set.

- Interior sauna liner (walls + ceiling): 2" foil-faced polyiso (taped seams). Polyiso is held in place with 1/2" plywood furring strips; fasten per IRC Table R703.15.2 (table is for exterior cladding attachment—verify applicability and embedment for interior concrete/framing substrates).

- Interior finish over furring: 5/4 tongue-and-groove boards (1" actual). Use low thermal conductivity species such as American basswood, Canadian poplar, or aspen.

- Wall/ceiling junction: detail as continuous layers (insulation meets insulation, wood meets wood). Tape/flash seams as required for vapor control and durability.

- Concrete-substrate case (`SAUNA_LINER_ON_CONCRETE`, `SAUNA_LINER_ON_BASEMENT_12_GARDEN`): on the east face (the center bearing wall) and the south face (the sunken-garden foundation wall) there is no stud bay behind the liner — the 1/2" plywood furring is fastened to the pour itself, so use masonry fasteners with an embedment verified for the substrate rather than the R703.15.2 table cited above, which is written for framing. Layer order, thickness and taping are otherwise identical to the framed case. Consequences to draw: the south wall's rough jamb is now 15 1/2" deep, not 12", so the window buck deepens with it, and the foil facing returns into that jamb per `TR-CATLIN-SAUNA-OPENING` rather than dying at the opening. The liner stops at the room's 7'-6" ceiling on the south face (authored as a `LayerExtent` off the wall top) because the foundation wall runs 9'-0" — revisit if the basement ever gets a full-width joist ceiling.

- **Stale, flagged not corrected:** the "Foundation: 10" concrete wall" line below predates the model, which carries 12" on every basement perimeter segment. Reconcile the note to the model (or the model to a re-checked footing design) before this detail goes to a drawing set.

- Support framing: 2x4 wall framed against concrete supports the dropped 2x4 ceiling. Primary structure above may be joists or concrete deck; hang drop framing accordingly.

- Benches + heater (Law of Löyly): show two-tier bench (≈18" + ≈36" heights). Heater low and near airflow path; maintain clearances per manufacturer.

- Base: 6" fiber cement baseboard (or tile backer) at bottom of walls replaces T&G and furring. Provide flashing from polyiso over baseboard at top edge. Liquid floor membrane extends up the fiber cement baseboard.

- Floor: 4" concrete slab over R-10 XPS (≥25 psi) and 10 mil (min) polyethylene sheet (radon/vapor barrier). Top of slab: liquid membrane plus removable duckboards on rubber feet; stainless fasteners.

- Thermal break / isolation joint: 1" XPS with 1/2" polyurethane sealant around sauna slab perimeter (shown schematically).

- Electrical: supply 240V, 50A GFCI breaker and wiring to sauna heater (max 10.5 kW). For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: IP65-rated LED strips concealed under lower bench lips + one waterproof wall sconce; keep drivers/transformers outside hot zone.

- Ventilation: include HRV/ERV connections with adjustable cedar vent registers; intake low and away from heater, exhaust high above/near heater. Keep plastic vent pipe behind insulation.

- Indicators: provide an exterior “in use” light, tied to heater control or via current-sensing relay.

- Foundation: 10" concrete wall bearing on 20"×8" footing per IRC Table R403.1 (confirm local requirements). Footing concrete 5000 psi. Footing bears on 6" compacted washed stone aggregate (wider than footing) with French drain located in the wider area, not under the footing.

