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

## Sheet notes

### General
- Framed wall: 2x6 at 16" o.c., R-19 bays, 4" continuous exterior.
- Basement wall: 8" pour, #5 at 41" o.c., aligned on the concrete face.
- Basement CI: 4" XPS in two layers, seams staggered, outer layer taped.
- Exposed XPS band: 1/8" acrylic coating over mesh, 276.3 SF. Head at the wall top, foot 6" below grade.
- Bearing seat: pour tops at -13 7/16", then gasket, mudsill and 11 7/8" rim.
- Sill: one shared 2x6 PT mudsill, 370.0 LF, on 1/16" compressed EPDM.
- Slab: 3-1/2" at 3,500 psi on 3" XPS at 40 psi, 10 mil poly, 4" gravel.
- Footing drain: 4" perforated pipe in lined stone beside the footing.

### Keyed
- [K1] Liquid membrane on sheathing and concrete, lapped across sill and rim.
- [K2] Z-flashing with drip at the outrigger base, set to the 1" vent, not 3-1/2".
- [K3] Insect mesh above it, stapled to the outriggers and run behind the flashing.
- [K4] L-flashing from sheathing base onto the foam; seal its outer end.
- [K5] Mudsill anchors per IRC R403.1.6. Plate joint peel-and-stick on the envelope.
- [K6] Slab perimeter: 1" XPS thermal break with 1/2" polyurethane sealant.
- [K7] Veneer: 2" EPS on the backup wall, 4" clear air, weeps at the beam. Two-piece adjustable anchors through the full 6".

### Spec 07 21 00
- Use XPS with published low water absorption; confirm compressive strength for below-grade use.
- Bond the basement XPS to the damp-proofing with foam-compatible mastic. Do not anchor it.
- Fill each remaining void and transition with low-expansion foam for air-barrier continuity.

### Spec 04 21 13
- Keep the veneer cavity clear of mortar droppings.
- Leave a soft joint at each end of the veneer against the retaining wall; do not anchor there.

# Notes

- Detail intent: schematic section showing basement exterior wall and transition to wood-framed exterior wall above.

- Above-grade wall: 2x6 framing (LSL recommended) with R-19 cavity insulation and continuous exterior insulation totaling 4".
  - **The CI is sprayed, and the stand-off is horizontal.** `CATLIN_EXT_2X6` is a **catlin truss**: 4" of 2 lb closed-cell spray foam around two tiers of flat horizontal 2x4 girts at 24" o.c., each course bearing on 3-1/2" blocks at the 16" stud module — inner girt SPF and buried in the foam, outer girt KDAT standing in a 1/2" vent gap, with the cladding on the outer girt. **There is no WRB** — the foam is the water plane — and the cladding face stands 6-1/2" proud of the sheathing. See `notes/outie_window_truss_detail.md`, which carries the build order: the window bucks go in BEFORE the foam is sprayed, and band A is sprayed BEFORE the inner girts (foam cannot reach behind a flat girt).

- Foundation waterproofing / air barrier: liquid-applied membrane on sheathing and on concrete foundation wall; maintain continuity at the sill/rim transition with overlap, sealant, and/or additional liquid membrane as needed.

- Basement CI: 4" XPS in two layers with staggered seams; tape seams on the outer layer. Use lower water-absorption XPS types (most are) and confirm compressive strength / below-grade suitability.

- Exposed XPS (top portion above grade): protect with appropriate elastomeric coating or rigid metal/PVC trim per manufacturer. **This house takes the coating** — see the band paragraph below; the trim is recorded as the named alternate.

- **The exposed band is modelled, not only drawn.** The north, east and west basement walls stand 2'-10" out of the ground and that much XPS is exposed on each. The band is authored off the GRADE datum rather than as a height, so a grade change grows it without the assembly being edited. `CATLIN_BASEMENT_12` and `CATLIN_BASEMENT_8` therefore carry a fifth layer — a 1/8" trowel-applied acrylic coating over reinforcing mesh (`foundation-coating-acrylic`, a stock grey) — with a `Layer.extent` running from 6" *below* grade up to the top of the wall. **Order 276.3 SF**, which is the live figure; the "~374 SF" this note carried until 2026-09-04 was stale. Six inches below so no foam edge shows at the soil line and the shovel hits coating, not XPS. Because it is a real layer with a real band, the drawing, the 3D model, the IFC export (as an `IfcBuildingElementPart` aggregated to its wall) and the order all read the same area; the detail component no longer derives a second band of its own beside it.

- **The coating is specified over the 1/2" protection board because the board could not be graded.** A butted, unsealed board's installed permeance is dominated by its joints, no manufacturer in that class publishes an ASTM E96 number for it, and `building_science.condensation` therefore reported UNKNOWN on *both* basement assemblies for as long as it was authored. A mesh-reinforced trowel lamina is monolithic and seamless, a published band describes it, and both walls now PASS the January gate with the tightest plane 69-73 Pa below saturation. The board is kept as the **named alternate** — its material and its price row both stay live — and going back to it is one `material_ref` edit. Note what it is *not*: cheaper. Installed, the coating bills alongside the board, not under it. The reason for the swap is the verdict.

- **The XPS is bonded, and nothing anchors it.** Foam-compatible mastic to the liquid-applied damp-proofing, per the membrane manufacturer, and that is the whole attachment. It is sufficient because the band is captured mechanically at both ends regardless: its head tucks under the rainscreen Z-flashing at the bearing seat, and its foot is buried 6" in soil, with backfill holding everything below. It also gives up nothing — the board it replaces was pinned into the *foam*, never through to the concrete, so no version of this band has ever had an anchor in the wall. There is no hardware line for it and there should not be: the mastic rides in the `xps:2.0` labour rate, which is what an unfastened layer means.

- **There is no parge coat on any wall in this house.** `W-B-S1`/`W-B-S4` — the buried ends either side of the excavation — carry the same grade-banded coating: 6'-4" of fill with 2'-2 9/16" standing out of it is exactly a grade band. The court segments carry no skin at all: their foam is inside `W-B-BRICK`'s ventilated cavity, and since 2026-09-05 that foam is 4" XPS plus a 2" EPS board, 6.05" outboard of the concrete face. The banded walls carry 4.175" outboard over the band and 4.05" below it, unchanged. `N-B-BRICK-W`/`-E` did **not** follow the *band* and still do not — those nodes stand over the court segments, which have never carried a skin — but they did follow the court segments' own new EPS face to -6.05". Two different faces; do not conflate them.

- **The veneer's cavity is 4" of air behind 6" of foam, and the 6" it sits in is a foundation dimension rather than a rainscreen one.** The wythe does not bear on the house any more. Until 2026-09-05 it stood on `FT-B-BRICK`, a plinth cast on `FT-B-S2`/`FT-B-S3`'s own projecting toe, which put 129 SF of brick — exposed on **both** faces at the bottom of an open court, so at outdoor temperature all winter — in direct series with the footings whose underside is level with the court floor. The break meant to interrupt that was ordered twice and placed never: the plinth's `FOOTING_FPSF_20` billed 16.0 SF of 2" XPS that no geometry ever held, and its bedding dug a 2" undercut for the same space that billed as washed crushed stone, with a `cast_foam_in_aggregate` flag beside it carrying no thickness at all. Nothing grades a thermal break for continuity, so the condition sat at 0 FAIL. The veneer now bears on `W-SG-BRKBM`, a 12" x 17 3/4" grade beam spanning the court's 19'-0" between `W-SG-W1` and `W-SG-E1`, whose north face carries a **2" 40 psi XPS isolation board** — the same cut `DW-SG-W1/E1-FOAM` already makes at the porch footings, spelled as an assembly Layer so it has a polygon, a face and an order that a test can pin. It faced the house footing's trimmed toe flush until 2026-09-05, when all four south strips retreated to -4" so the porch closure could have its own 2" across a full 84" joint; the board now works across 4" of bedding stone in series with itself, which is no weaker. The beam's concrete can reach y = -10" and no further, which is what sets the wythe at -10.05"..-13 5/8" and leaves a fixed 6" slot behind it. **That slot is split 2" foam / 4" air.** The 2" is an ASTM C578 Type II EPS board on the backup wall — set before the mason starts and held by the veneer anchors — taking the court walls to R-45.0 framed and R-29.3 at the curb; the 4" that remains is the drainage cavity, four times IRC R703.8.4's 1" minimum and still inside its 4-1/2" ceiling, with weeps at the beam and the cavity kept clear of droppings. EPS rather than more XPS so the wall can dry outward into that cavity instead of gaining a second vapour shutter behind 4" of XPS it already cannot dry through. **The anchors are still an engineered item under TMS 402**, not because of the airspace — 4" is inside the tables — but because the beam holds the wythe ~10" off the sheathing and no prescriptive table reaches that far; specify a two-piece adjustable anchor and confirm the manufacturer publishes the full 6" insulation thickness. The board is held to 2" by the wall above, whose cladding face is at -7.25": the basement skin's head tucks UNDER that rainscreen's Z-flashing, and a thicker board stands proud of it and turns the lap into an upward-facing ledge. IRC R703.15's 4" foam limit does not apply: it excepts anchored masonry veneer to R703.8, and this wythe carries its own weight to the beam rather than hanging on its fasteners. **The two ends take a soft joint against `W-SG-W1`/`W-SG-E1`, never an anchor** — brick grows, concrete shrinks, and BIA TN 18 puts about 0.15" of movement across an 18'-8" run. See `notes/sunken_garden_veneer_beam.md`. The cavity was 6" of bare air for one day, 1-1/2" under the plinth, and 1" before that.

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
