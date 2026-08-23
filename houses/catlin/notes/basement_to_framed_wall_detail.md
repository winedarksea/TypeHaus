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

- **The exposed band is modelled now, not only drawn (2026-08-18).** The 2026-08-18 lift put grade at -2'-6", and the 2026-08-21 basement-ceiling overhaul took it to -2'-10", so the north, east and west basement walls stand 2'-10" out of the ground and that much XPS is exposed on each. The band is authored off the GRADE datum rather than as a height, so both lifts grew it (and the panel order, ~324 SF to ~374 SF) without the assembly being edited. `CATLIN_BASEMENT_12` and `CATLIN_BASEMENT_8` therefore carry a fifth layer — a 1/2" aluminium-faced protection panel (`foundation-protection-panel`, the house's one exterior dark, #1c1f24) — with a `Layer.extent` running from 6" *below* grade up to the top of the wall. Six inches below so no foam edge shows at the soil line and the shovel hits panel, not XPS. Because it is a real layer with a real band, the drawing, the 3D model, the IFC export (as an `IfcBuildingElementPart` aggregated to its wall) and the order all read the same area; the detail component no longer derives a second band of its own beside it.

- **The parge coat is off these three walls and stays on the south one.** The full-height parge added 2026-08-01 was there for the *south* wall, which the sunken garden opens to the air over its whole 9', and it landed on all four sides only because a layer had no way to say "only here". The south wall keeps it, in its own assembly (`CATLIN_BASEMENT_8_GARDEN`) — a grade-datum band cannot describe a face whose exposure runs from -9'-0" to 0'-0". Every one of these assemblies still carries exactly 4.55" outboard of the concrete face, which is what `N-B-BRICK-W`/`-E`'s stand-off is measured from.

- **The pour is 8" everywhere the detail applies (2026-08-21).** This detail is the wood-over-concrete transition, and 12" was only ever earned where a *cast concrete deck* lands on the wall top beside the sill plate and needs its own bearing seat inboard of it. Wood does not: the I-joists and rim bear on the same 2x6 mudsill the framed wall above stands on, and an 8" wall carries that sill with 2" to spare. After the 2026-08-21 basement-ceiling overhaul the only cast deck left is `SL-M-DECK`, which lands on the east wall and the centre line — neither of which this detail draws. So the north, west and south perimeter is 8" (`CATLIN_BASEMENT_8`, `CATLIN_BASEMENT_8_GARDEN`, `SAUNA_LINER_ON_BASEMENT_8_GARDEN`) with `#6 @ 48" o.c.` vertical steel, which IRC Table R404.1.2(8) requires at 8" where 12" reads NR. Nothing in the drawn transition changed: the walls align on `face("concrete-ext")`, so the exterior face, the 4" of XPS and its hand-off to the framed wall's 4" of CI all stand exactly where they did, and the 4" came off the inside face where the sill has room to spare.

- **The panel's head is the Z-flashing below.** The band tops out at 0'-0", which is the top of the basement wall and the base of the framed wall above — exactly where the rainscreen's 1-1/2" corrugated bug screen sits in the furring band and where the Z-flashing with its drip is drawn. The panel tucks under that flashing; nothing new is fastened for the tie, and the flashing is what sheds water clear of the panel head.

- Sill: include sill gasket and treated mudsill. Prioritize air sealing at sill plate (sealant + spray foam at gaps). Use mudsill anchors (e.g., MASAP) as required (not shown).

- Flashings: provide stainless (preferred) or thick aluminum Z-flashing with drip edge at bottom of rainscreen furring. Install insect barrier mesh/strip (Cor-A-Vent or SS screen) just above flashing. Mesh can be stapled to furring strips, run behind the flashing, and into the layer between basement and wall foam.

- Interface flashing: provide L-flashing from bottom of sheathing down onto the top of basement foam. Terminate within the insulation plane and seal the outer end with spray foam (Pestblock) to avoid an exterior thermal bridge. This is meant as a foam layer insect barrier.

- Drainage: 4" perforated french drain in geotextile-lined washed stone (wider area, not under footing). Additional compacted aggregate in front of footing (equal to footing height, geotextile-lined). River rock trench (geotextile-lined) against foundation for top of soil.
  - **"French drain" here and "drain tile" in the model are the same article — checked
    2026-08-22, no duplication.** There is no `FrenchDrain` element kind and no such element
    in the plan; the pipe this line describes is what `FootingBedding.drain_tile_spec`
    models, and its length agrees to 0.1 LF across two independent tables (`[concrete]`
    `drain_tile` 761.4 LF by its SF-per-foot conversion, `[footing_bedding]` 515.3 + 246.0 =
    761.3 by its own). If a `FrenchDrain` element is ever authored, THAT is the moment a
    duplicate can appear — a second element over the same trench billing the same stone
    twice.

- Interior slab: 3 1/2" concrete slab (min. 3,500 psi, IRC R506.1) over R-15 XPS insulation
  (3", 40 psi), 10 mil (min) polyethylene vapor barrier (ASTM E1745 Class A), and 4"
  compacted open-graded gravel base. Provide 1" XPS thermal break with 1/2" polyurethane
  sealant at foundation wall perimeter.
  - **Reconciled against the model 2026-08-22.** This line read 4" concrete over R-10 XPS at
    ≥25 psi; `CATLIN_SLAB_FLOOR` is 3 1/2" concrete over **3" XPS, R-15 at 40 psi**. The
    model wins on both — 40 psi is the slab-bearing grade rather than the lighter
    foundation-wall grade, and the extra R was a deliberate choice, so the note was simply
    stale and this text prints into the detail SVGs. The **note** won on the polyethylene and
    the gravel, which it had called for all along and which the assembly did not carry at
    all; they are layers of `CATLIN_SLAB_FLOOR` now, and of `GARAGE_SLAB_ON_GRADE` with them.

- Grading: soil must slope away from foundation at minimum 6" per 10' for first 10' (IRC R401.3).

- All gaps: fill voids and transitions with low-expansion spray foam as needed for air sealing and continuity.

