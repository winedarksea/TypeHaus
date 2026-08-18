---
title: "Basement to Wood-Framed Wall Transition Detail Notes"
applied_to:
  - detail: basement_to_framed_wall_detail
tags:
  - basement
  - foundation
  - wall
  - insulation
  - air-barrier
source:
  - basement_to_framed_wall_detail.py
---

# Notes

- Detail intent: schematic section showing basement exterior wall and transition to wood-framed exterior wall above.

- Above-grade wall: 2x6 framing (LSL recommended) with R-19 cavity insulation and continuous exterior CI totaling 4". Above-grade CI shown as 2" polyiso + 2" EPS; seams staggered, outer layer taped.

- Foundation waterproofing / air barrier: liquid-applied membrane on sheathing and on concrete foundation wall; maintain continuity at the sill/rim transition with overlap, sealant, and/or additional liquid membrane as needed.

- Basement CI: 4" XPS in two layers with staggered seams; tape seams on the outer layer. Use lower water-absorption XPS types (most are) and confirm compressive strength / below-grade suitability.

- Exposed XPS (top portion above grade): protect with appropriate elastomeric coating or rigid metal/PVC trim per manufacturer.

- **The exposed band is modelled now, not only drawn (2026-08-18).** The 2026-08-18 lift put grade at -2'-6", so the north, east and west basement walls stand 2'-6" out of the ground and that much XPS is exposed on each. `CATLIN_BASEMENT_12` therefore carries a fifth layer — a 1/2" aluminium-faced protection panel (`foundation-protection-panel`, the house's one exterior dark, #1c1f24) — with a `Layer.extent` running from 6" *below* grade up to the top of the wall. Six inches below so no foam edge shows at the soil line and the shovel hits panel, not XPS. Because it is a real layer with a real band, the drawing, the 3D model, the IFC export (as an `IfcBuildingElementPart` aggregated to its wall) and the order all read the same 324 SF; the detail component no longer derives a second band of its own beside it.

- **The parge coat is off these three walls and stays on the south one.** The full-height parge added 2026-08-01 was there for the *south* wall, which the sunken garden opens to the air over its whole 9', and it landed on all four sides only because a layer had no way to say "only here". The south wall keeps it, in its own assembly (`CATLIN_BASEMENT_12_GARDEN`) — a grade-datum band cannot describe a face whose exposure runs from -9'-0" to 0'-0". Both assemblies still carry exactly 4.55" outboard of the concrete face, which is what `N-B-BRICK-W`/`-E`'s stand-off is measured from.

- **The panel's head is the Z-flashing below.** The band tops out at 0'-0", which is the top of the basement wall and the base of the framed wall above — exactly where the rainscreen's 1-1/2" corrugated bug screen sits in the furring band and where the Z-flashing with its drip is drawn. The panel tucks under that flashing; nothing new is fastened for the tie, and the flashing is what sheds water clear of the panel head.

- Sill: include sill gasket and treated mudsill. Prioritize air sealing at sill plate (sealant + spray foam at gaps). Use mudsill anchors (e.g., MASAP) as required (not shown).

- Flashings: provide stainless (preferred) or thick aluminum Z-flashing with drip edge at bottom of rainscreen furring. Install insect barrier mesh/strip (Cor-A-Vent or SS screen) just above flashing. Mesh can be stapled to furring strips, run behind the flashing, and into the layer between basement and wall foam.

- Interface flashing: provide L-flashing from bottom of sheathing down onto the top of basement foam. Terminate within the insulation plane and seal the outer end with spray foam (Pestblock) to avoid an exterior thermal bridge. This is meant as a foam layer insect barrier.

- Drainage: 4" perforated french drain in geotextile-lined washed stone (wider area, not under footing). Additional compacted aggregate in front of footing (equal to footing height, geotextile-lined). River rock trench (geotextile-lined) against foundation for top of soil.

- Interior slab: 4" concrete slab (min. 3,500 psi, IRC R506.1) over R-10 XPS insulation (≥25 psi), 10 mil (min) polyethylene vapor barrier, and 4" compacted gravel base. Provide 1" XPS thermal break with 1/2" polyurethane sealant at foundation wall perimeter.

- Grading: soil must slope away from foundation at minimum 6" per 10' for first 10' (IRC R401.3).

- All gaps: fill voids and transitions with low-expansion spray foam as needed for air sealing and continuity.

