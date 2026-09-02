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

- Above-grade wall: 2x6 framing (LSL recommended) with R-19 cavity insulation and continuous exterior insulation totaling 4".
  - **The CI is sprayed, and the stand-off is horizontal.** `CATLIN_EXT_2X6` is a **catlin truss**: 4" of 2 lb closed-cell spray foam around two tiers of flat horizontal 2x4 girts at 24" o.c., each course bearing on 3-1/2" blocks at the 16" stud module — inner girt SPF and buried in the foam, outer girt KDAT standing in a 1/2" vent gap, with the cladding on the outer girt. **There is no WRB** — the foam is the water plane — and the cladding face stands 6-1/2" proud of the sheathing. See `notes/outie_window_truss_detail.md`, which carries the build order: the window bucks go in BEFORE the foam is sprayed, and band A is sprayed BEFORE the inner girts (foam cannot reach behind a flat girt).

- Foundation waterproofing / air barrier: liquid-applied membrane on sheathing and on concrete foundation wall; maintain continuity at the sill/rim transition with overlap, sealant, and/or additional liquid membrane as needed.

- Basement CI: 4" XPS in two layers with staggered seams; tape seams on the outer layer. Use lower water-absorption XPS types (most are) and confirm compressive strength / below-grade suitability.

- Exposed XPS (top portion above grade): protect with appropriate elastomeric coating or rigid metal/PVC trim per manufacturer.

- **The exposed band is modelled, not only drawn.** The north, east and west basement walls stand 2'-10" out of the ground and that much XPS is exposed on each. The band is authored off the GRADE datum rather than as a height, so a grade change grows it without the assembly being edited. `CATLIN_BASEMENT_12` and `CATLIN_BASEMENT_8` therefore carry a fifth layer — a 1/2" aluminium-faced protection panel (`foundation-protection-panel`, the house's one exterior dark, #1c1f24) — with a `Layer.extent` running from 6" *below* grade up to the top of the wall (order ~374 SF). Six inches below so no foam edge shows at the soil line and the shovel hits panel, not XPS. Because it is a real layer with a real band, the drawing, the 3D model, the IFC export (as an `IfcBuildingElementPart` aggregated to its wall) and the order all read the same area; the detail component no longer derives a second band of its own beside it.

- **There is no parge coat on any wall in this house.** `W-B-S1`/`W-B-S4` — the buried ends either side of the excavation — carry the same grade-banded protection panel: 6'-4" of fill with 2'-2 9/16" standing out of it is exactly a grade band. The court segments carry no skin at all: their XPS is inside `W-B-BRICK`'s ventilated cavity. The banded walls carry 4.55" outboard of the concrete face over the band and 4.05" below it; `N-B-BRICK-W`/`-E`'s 4.55" stand-off did not move — the veneer's clear cavity is 1-1/2", up from 1".

- **The pour stops at the bearing seat, -13 7/16", and this detail's junction is there.** The top of the concrete and the bottom of the framed wall are 13 7/16" apart: the pour tops out on one flat seat all the way round, the framed wall above still starts at the storey datum (the house-wide datum convention is a known split — see `plans/TODO.md`), and the 13 7/16" between them is the mudsill, its gasket, and the 11 7/8" rim band the joists die into. The L-flashing, the Z-flashing with its drip, the bug screen and the sill gasket all draw on the concrete rather than a foot above it.

- **The sill is one board and it is shared.** The I-joists and rim bear on the same 2x6 mudsill the framed wall above stands on. One rule takes the **union** of the two runs, on the seat, and it bills 370.0 LF. There is no second rule and there must not be: two rules over one board is a double-bill.

- **The pour is 8" everywhere the detail applies, and the steel is `#5 @ 41" o.c.`** This detail is the wood-over-concrete transition: the I-joists and rim bear on the same 2x6 mudsill the framed wall above stands on, and an 8" wall carries that sill with 2" to spare. The north, west and south perimeter is 8" (`CATLIN_BASEMENT_8`, `CATLIN_BASEMENT_8_GARDEN`, `SAUNA_LINER_ON_BASEMENT_8_GARDEN`) with `#5 @ 41" o.c.` vertical steel, which IRC Table R404.1.2(8) requires at 8" where 12" reads NR. Only `SL-M-DECK` is still a cast deck, and it lands on the east wall and the centre line — neither of which this detail draws. The walls align on `face("concrete-ext")`, so the exterior face, the 4" of XPS and its hand-off to the framed wall's 4" of CI all stand exactly where they are drawn, and the 4" came off the inside face where the sill has room to spare.

- **The panel's head is the Z-flashing below.** The band tops out at the top of the basement wall, -13 7/16", which is where the framed wall's mudsill sits, and the rainscreen's 1-1/2" corrugated bug screen sits in the vented part of the outrigger band and where the Z-flashing with its drip is drawn. (That vent is 1" deep — the outrigger band is 3-1/2" but its back 2-1/2" is packed with the foam, so the screen closes 1", not 3-1/2".) The panel tucks under that flashing; nothing new is fastened for the tie, and the flashing is what sheds water clear of the panel head.

- **The sill is treated PT lumber in the BOM, and the gasket is a named product.** `resolve/construction_sills.py` returns `material_ref="kdat"` on the sill record, whose take-off category is `pt-sill-plate` and whose rule cites IRC R317.1; no dollar moves with it — `construction_returns` is not in `QUALIFIED_KEY_FIELD`, so that column is reported and not priced on, and the `pt-sill-plate` rate stays the *delta* over the SPF board `[framing]` already bills. `FramingSpec.sill_gasket` is the compressed in-place thickness, and a second field says WHICH seal — plain closed-cell foam where the plate joint is only a capillary/air break, peel-and-stick where it is the air barrier crossing onto the foundation, resolved from whether the framed wall carries a cladding layer. It reaches the BOM as its own `[sill_gaskets]` table (240 LF peel-and-stick on the envelope, 130 LF foam on the interior lines), and the $0.15-0.30/LF sealer is priced there rather than hidden inside the `pt-sill-plate` delta.

- **This detail draws the envelope crossing only, and there are two interior walls on the same plate that it does not draw.** `W-B-STR`/`W-B-STR3`, the stair shaft's west line, are 2x6 bearing stud walls on footings. They take the same PT plate, the same anchors and the same capillary break — but the plain-foam seal, not the peel-and-stick, because nothing about that joint is on the air barrier. Their detail is the ordinary framed-wall-on-slab base, and `plan/storeys/basement.py` carries the alignment reasoning.

- Sill: include sill gasket and treated mudsill. **The stack is 1/16" of compressed EPDM gasket under a 1 1/2" PT 2x6, and those two numbers are structural, not trim**: the bearing seat is derived as joist depth + mudsill + gasket below the storey datum (`params/main_deck.py::BEARING_SEAT`), so the EPS deck beside it was deepened to land on the same plane. Substituting a thicker gasket or a 2x8 laid flat moves the seat and `structural.mixed_deck_bearing_seat` FAILs the build until the deck follows. Prioritize air sealing at sill plate (sealant + spray foam at gaps). Use mudsill anchors (e.g., MASAP) as required (not shown).

- Flashings: provide stainless (preferred) or thick aluminum Z-flashing with drip edge at the bottom of the rainscreen — i.e. at the bottom of the **outriggers**, and set to the 1" vent in front of the foam rather than to a 3-1/2" band. Install insect barrier mesh/strip (Cor-A-Vent or SS screen) just above flashing. Mesh can be stapled to the outriggers, run behind the flashing, and into the layer between basement and wall foam.

- Interface flashing: provide L-flashing from bottom of sheathing down onto the top of basement foam. Terminate within the insulation plane and seal the outer end with spray foam (Pestblock) to avoid an exterior thermal bridge. This is meant as a foam layer insect barrier. The "insulation plane" it terminates within is the wall's own sprayed foam rather than a board course, so the seal is foam to foam — bonded, not lapped.

- Drainage: 4" perforated french drain in geotextile-lined washed stone (wider area, not under footing). Additional compacted aggregate in front of footing (equal to footing height, geotextile-lined). River rock trench (geotextile-lined) against foundation for top of soil.
  - **"French drain" here and "drain tile" in the model are the same article, with no
    duplication.** There is no `FrenchDrain` element kind and no such element
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
  - `CATLIN_SLAB_FLOOR` is 3 1/2" concrete over **3" XPS, R-15 at 40 psi**, and carries
    a 10 mil polyethylene vapour barrier and a 4" compacted open-graded gravel base as
    layers, matching this note; `GARAGE_SLAB_ON_GRADE` carries the same two layers.

- Grading: soil must slope away from foundation at minimum 6" per 10' for first 10' (IRC R401.3).

- All gaps: fill voids and transitions with low-expansion spray foam as needed for air sealing and continuity.
