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

- Interior finish over furring: 5/4 **shiplap** boards (1" actual), rabbeted lap, 5-1/2" face over 5" coverage. Use low thermal conductivity species such as American basswood, Canadian poplar, or aspen — **the species is the burn-safety spec and does not change with the profile.** The lap is a simpler knife grind for the mill and a profile that moves more forgivingly through a 60 F to 190 F cycle than a tongue-and-groove profile would; it changes the board-feet ordered (a lap buries more face width than a tongue) and nothing else: same species, same 5/4 stock, same wall area, same installed $/SF.

- Wall/ceiling junction: detail as continuous layers (insulation meets insulation, wood meets wood). Tape/flash seams as required for vapor control and durability.

- Concrete-substrate case (`SAUNA_LINER_ON_CONCRETE`, `SAUNA_LINER_ON_BASEMENT_8_GARDEN`): on the east face (the center bearing wall) and the south face (the sunken-garden foundation wall) there is no stud bay behind the liner — the 1/2" plywood furring is fastened to the pour itself, so use masonry fasteners with an embedment verified for the substrate rather than the R703.15.2 table cited above, which is written for framing. Layer order, thickness and taping are otherwise identical to the framed case. Consequences to draw: the south wall's rough jamb is 11 1/2" deep — the 8" pour plus the 3 1/2" liner — rather than the bare 8", so the window buck deepens with it, and the foil facing returns into that jamb per `TR-CATLIN-SAUNA-OPENING` rather than dying at the opening. The liner stops at the room's 7'-6" ceiling on the south face (authored as a `LayerExtent` off the wall top) because the foundation wall runs its full storey height — 9'-4", so the basement storey can carry a 12 5/8" deck and keep its headroom. The `LayerExtent` is measured off the wall *top*, so it follows the wall down and the liner stops at 7'-6" with nothing edited. The basement ceiling is joists over the gym and the whole west half — the sauna included, since it sits at x 8'-10" to 18', west of the band — and drywalled everywhere.

- **The south wall is 8".** A 12" pour is needed only to seat a cast concrete deck; the only cast deck in the house, `SL-M-DECK`, lands on the east wall and the centre line, not this one. The south wall (`CATLIN_BASEMENT_8_GARDEN`, and `SAUNA_LINER_ON_BASEMENT_8_GARDEN` here) carries `#6 @ 48" o.c.` vertical steel, which IRC Table R404.1.2(8) requires at 8" against 45 psf/ft GM soil on a 10' unsupported wall retaining 7' — where 12" and 10" both read NR. The 20"x8" footing under it sits inside its own strip with a 2" toe each side.

- Support framing: 2x4 wall framed against concrete supports the dropped 2x4 ceiling. The primary structure above this room is joists, not a deck — `FS-M-WEST`, 11 7/8" I-joists at 16" o.c. spanning east-west. Hang the drop framing from the joists (the concrete band is east of x=18' and does not reach this room). `emit/draw/detail_components/sauna.py::ceiling_underside_over` reads a joist soffit as readily as a slab's.

- Benches + heater (Law of Löyly): show two-tier bench (≈18" + ≈36" heights). Heater low and near airflow path; maintain clearances per manufacturer.

- Base: 6" fiber cement baseboard (or tile backer) at bottom of walls replaces T&G and furring. Provide flashing from polyiso over baseboard at top edge. Liquid floor membrane extends up the fiber cement baseboard.

- Floor: 4" concrete slab over R-10 XPS (≥25 psi) and 10 mil (min) polyethylene sheet (radon/vapor barrier). Top of slab: liquid membrane plus removable duckboards on rubber feet; stainless fasteners.

- Thermal break / isolation joint: 1" XPS with 1/2" polyurethane sealant around sauna slab perimeter (shown schematically).

- Electrical: supply 240V, 50A GFCI breaker and wiring to sauna heater (max 10.5 kW). For gas/wood appliances, reference MPC Section 615 and the appliance listing.

- Lighting: IP65-rated LED strips concealed under lower bench lips + one waterproof wall sconce; keep drivers/transformers outside hot zone.

- Ventilation: include HRV/ERV connections with adjustable cedar vent registers; intake low and away from heater, exhaust high above/near heater. Keep plastic vent pipe behind insulation.

- Indicators: provide an exterior “in use” light, tied to heater control or via current-sensing relay.

- Foundation: 8" concrete wall with #6 @ 48" o.c. vertical reinforcement, bearing on 20"×8" footing per IRC Table R403.1 (confirm local requirements). Footing concrete 5000 psi. Footing bears on 6" compacted washed stone aggregate (wider than footing) with French drain located in the wider area, not under the footing. (Same pipe the model calls drain tile — see `basement_to_framed_wall_detail.md`; the two names do not describe two runs.)

