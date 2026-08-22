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

- Concrete-substrate case (`SAUNA_LINER_ON_CONCRETE`, `SAUNA_LINER_ON_BASEMENT_8_GARDEN`): on the east face (the center bearing wall) and the south face (the sunken-garden foundation wall) there is no stud bay behind the liner — the 1/2" plywood furring is fastened to the pour itself, so use masonry fasteners with an embedment verified for the substrate rather than the R703.15.2 table cited above, which is written for framing. Layer order, thickness and taping are otherwise identical to the framed case. Consequences to draw: the south wall's rough jamb is 11 1/2" deep — the 8" pour plus the 3 1/2" liner — rather than the bare 8", so the window buck deepens with it (it was 15 1/2" until the 2026-08-21 thinning took the pour from 12" to 8"), and the foil facing returns into that jamb per `TR-CATLIN-SAUNA-OPENING` rather than dying at the opening. The liner stops at the room's 7'-6" ceiling on the south face (authored as a `LayerExtent` off the wall top) because the foundation wall runs its full storey height — 9'-4" since the 2026-08-21 basement-ceiling overhaul, which took the basement storey down 4" so the house could carry a 12 5/8" deck and keep its headroom. The `LayerExtent` is measured off the wall *top*, so it followed the wall down and the liner still stops at 7'-6" with nothing edited. The revisit that clause invited has happened: the basement ceiling is joists over the gym and the whole west half now — the sauna included, since it sits at x 8'-10" to 18', west of the band — and drywalled everywhere.

- **Settled 2026-08-21 — the note and the model now agree, at 8".** The "Foundation: 10" concrete wall" line below predated the model and was flagged stale while the model carried 12" on every basement perimeter segment. The 12" was chosen to seat a cast deck; after the basement-ceiling overhaul only `SL-M-DECK` is still cast, and it lands on the east wall and the centre line, not on this one. The south wall is 8" now (`CATLIN_BASEMENT_8_GARDEN`, and `SAUNA_LINER_ON_BASEMENT_8_GARDEN` here) with `#6 @ 48" o.c.` vertical steel, which IRC Table R404.1.2(8) requires at 8" against 45 psf/ft GM soil on a 10' unsupported wall retaining 7' — where 12" and 10" both read NR. The line below is corrected to match; the 20"x8" footing under it is unchanged and the 8" pour now sits inside its own strip with a 2" toe each side instead of overhanging the inside edge.

- Support framing: 2x4 wall framed against concrete supports the dropped 2x4 ceiling. **Resolved 2026-08-21:** the primary structure above this room is joists, not a deck — `FS-M-WEST`, 11 7/8" I-joists at 16" o.c. spanning east-west. Hang the drop framing from the joists, which is the easier of the two cases the line above left open (the concrete band is east of x=18' and does not reach this room). The section draws it either way now: `emit/draw/detail_components/sauna.py::ceiling_underside_over` reads a joist soffit as readily as a slab's, where it used to ask only about slabs and silently drew no drop ceiling at all the moment the deck went to wood.

- Benches + heater (Law of Löyly): show two-tier bench (≈18" + ≈36" heights). Heater low and near airflow path; maintain clearances per manufacturer.

- Base: 6" fiber cement baseboard (or tile backer) at bottom of walls replaces T&G and furring. Provide flashing from polyiso over baseboard at top edge. Liquid floor membrane extends up the fiber cement baseboard.

- Floor: 4" concrete slab over R-10 XPS (≥25 psi) and 10 mil (min) polyethylene sheet (radon/vapor barrier). Top of slab: liquid membrane plus removable duckboards on rubber feet; stainless fasteners.

- Thermal break / isolation joint: 1" XPS with 1/2" polyurethane sealant around sauna slab perimeter (shown schematically).

- Electrical: supply 240V, 50A GFCI breaker and wiring to sauna heater (max 10.5 kW). For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: IP65-rated LED strips concealed under lower bench lips + one waterproof wall sconce; keep drivers/transformers outside hot zone.

- Ventilation: include HRV/ERV connections with adjustable cedar vent registers; intake low and away from heater, exhaust high above/near heater. Keep plastic vent pipe behind insulation.

- Indicators: provide an exterior “in use” light, tied to heater control or via current-sensing relay.

- Foundation: 8" concrete wall with #6 @ 48" o.c. vertical reinforcement, bearing on 20"×8" footing per IRC Table R403.1 (confirm local requirements). Footing concrete 5000 psi. Footing bears on 6" compacted washed stone aggregate (wider than footing) with French drain located in the wider area, not under the footing.

