---
title: "Detached Garage Wall Detail (Side View) Notes"
applied_to:
  - detail: garage_wall_detail_side
tags:
  - garage
  - wall
  - foundation
  - icf
  - roof
source:
  - garage_wall_detail_side.py
---

# Notes

- ICF stem wall: 42" below grade to frost level with minimum 6" stem wall above grade (goal: 22" above grade here). Total ICF stem wall height should not exceed 8' per IRC Table R404.1.4.2. and ICF forms must conform to ASTM E2634 and be installed per manufacturer instructions.

- **The 22" is not a concrete rule and RAISING IT IS NOT THE LEVER for anything.** R404.1.4.2 is an 8'-0" *maximum* and R403 a 6" *minimum*; 22" is an owner goal inside that window. What pins it is that `GARAGE_STEM_REVEAL` **is the garage storey datum** — the wood walls bear on the stem top — so raising it lifts the plates, the trusses, the ridge, the window sills and the service door's step count, and breaks `test_garage_overhead_door_opens_from_the_slab_at_grade`. Raising it only at the door piers puts a 48" concrete curb *inside* the garage and splits W-G-E three ways. Nothing wants it: a veneer needs a *ledge*, not a stem, and the metal wainscot needs neither.

- Footing shown as 12"×6" compacted stone footing per IRC R403.1 and R403.4.1 (confirm soil bearing and local acceptance). Footing drain tile recommended.

- **Exposed ICF EPS above grade requires protective covering on BOTH faces, and BOTH HALVES ARE NOW BUILT** (the exterior half was missing until 2026-09-02). Interior: 15-minute thermal barrier per IRC R316.4 — the `gwb-stem` band, 5/8" exterior-rated gypsum from grade up. Exterior: the `coil-gap` + `coil-ext` band, PVDF-painted aluminium flat sheet from **2" below grade to the stem top**, on a 1/4" vented standoff, fixed with #9 316 stainless gasketed screws into the ICF webs. The standoff is not optional and is not drainage alone: a painted sheet is **0 perms**, and laid flat on the EPS it is a Class I retarder on the cold side of the stem — `building_science.condensation` found a January dew point at the concrete against a monthly *mean*. The gap restores the outward drying path. It also keeps aluminium off damp foam and out of contact with the concrete, which matters independently: **alkali strips aluminium's oxide film**, so this metal must never touch concrete or fresh mortar.

- Grade: IRC R401.3 requires minimum 6" fall within first 10 feet from foundation.

- Slab: minimum 3.5" thick, ≥3,500 psi per IRC R506.1. Slab must be sloped (typically toward overhead door).

- Wood wall (REBUILT 2026-08-31; what stood here before that date was 2×6 @16" o.c. with 1.5" Zip-R continuous sheathing, Method CS-G, and empty bays): 2×6 studs **@24" o.c.**, **5/8" CDX** sheathing, **2" of 2 lb closed-cell spray foam in the bays**, **7/8" corrugated 26 ga PVDF exposed-fastener steel panel** in the house white, screwed through its crowns into the studs with #9 × 1-1/2" 316 stainless gasketed panel screws. Interior finish: 5/8" drywall. Whole-wall R-13.2 (`haus explain GARAGE_WALL_2X6 --card`), roughly double the honest R-7–8 the empty-bay Zip-R wall carried — the R-14.3 that assembly's card used to read was an artifact of billing an uninsulated 5.5" stud bay as solid SPF.

- **No WRB, and that is a decision rather than an omission.** IRC R703.2's exception releases an unconditioned detached accessory building from the water-resistive barrier, and this is one (`RM-GARAGE` is `conditioned=False`). The ccSPF is the air, water and vapour plane; the CDX is structure and nailbase only. Build order follows from that, exactly as it does on the house: **bucks before foam.**

- **The corrugation is the rainscreen.** There is no furring layer. A 7/8" corrugated sheet screwed to a flat face leaves a continuous open flute behind every panel — more free area than the 3/8" 1×4 vertical furring this wall carried before 2026-08-20 ever gave it. What makes it work rather than making it a trough is the closures: a **vented (inside) closure strip at the base**, so the cavity drains and vents while nothing insect-sized gets in, and a **solid (outside) closure under the head and the rake**, so wind-driven rain and snow do not enter over the top. ~192 LF, both courses. Neither is optional.

- **24" o.c. is deliberate, and there is no 16" zone at the overhead door.** W-G-E is nonbearing — the ridge runs E–W and the trusses bear on W-G-S/W-G-N — and the 16'-0" opening is carried by its own 2-ply 14" LVL on jamb packs sized from the opening, not from field spacing. Field studs beside a nonbearing opening carry nothing extra. The garage's window pair and its service door were re-stationed onto the 24" grid the same day; D-G-OVERHEAD stays where it is and its off-module advisory is a recorded decision (`preferences.toml [checks] suppress`), because every legal station moves the ICF grade beam and makes the two wainscot piers 5'-0" and 3'-0".

- **THE WAINSCOT IS METAL, NOT BRICK, SINCE 2026-09-02 — and there are no ties, no weeps and no blocking to build.** The two 4'-0" piers flanking the overhead door, plus a 4'-0" return around each of the SE/NE corners, carry PVDF-painted aluminium flat sheet on a 1-1/2" drained and vented cavity of vertical KDAT furring (12" o.c. through the lower band, 16" above it), hung on concealed cleats with hemmed top and bottom edges and a #9 316 stainless gasketed perimeter fixing. From a hemmed drip **2" below grade** to a top **46" above** it — one uncut 48" x 120" stock sheet per pier, brake-bent around the corner with **no corner joint** (pier face 49 9/16" + 48" return = 97 9/16" of girth) — capped by formed metal at a round **4'-0" above grade**.

  It replaced 4'-4" of Glen-Gery Columbia Roman Maximus soldier brick. **Why:** the driveway apron is plowed and salted, and brick is the *absorptive* choice in the one place chloride slush is thrown at the wall — the unit is Grade SW and survives, but salt enters the mortar and base course and returns as subflorescence. **What went with it, all of it work no longer on the job:** the mid-stack ICF brick-ledge form, the 20" -> 24" footing widening on four stem segments, through-wall flashing and weeps at the base, a second through-wall flashing under the cap, corrugated ties in three bed joints at a 16" o.c. horizontal spacing the wall's 24" o.c. studs could not give, and the ~8 lf per pier of flat 2x6 tie blocking bought to reach that spacing.

  **THE ONE NEW RULE IS A CORROSION RULE.** The corrugated panel above is 26 ga PVDF-coated **steel** and this wainscot is **aluminium**. The cap flashing and the Z-flash behind it must both be aluminium, and the two panels must never lap metal-to-metal — sealant or EPDM between, the Z's upper leg behind the corrugated. In a salted splash zone that contact line is where the detail fails, and nothing in the engine grades dissimilar metals. On site the corrugated terminates at the cap with its vented base closure moved up; the model bills it full height behind the band, as it did behind the brick.

- Sill: pressure treated sill board over sill gasket and capillary break; provide code-required anchor bolts detailed per IRC R403.1.6 (3"x3" plate washers). Sealed with sealant.

- Top plate must be sealed (e.g., with spray foam or sealant) to create continuous air barrier between interior drywall and exterior sheathing.

- Provide Z-flashing / drip edge at base of exterior wall (liquid flashing recommended) to direct water out over the foundation / protective coating. **Aluminium, not steel** — it lands on the aluminium stem band, and see the wainscot note above on why that contact matters here.

- Stem and framing are flush on the outside: the wood wall's SHEATHING face (5/8" CDX since 2026-08-31, 1.5" Zip-R before it — the wall's own `alignment` puts whichever it carries on the node line) and the ICF's exterior EPS face are the same plane, so the only thing standing proud at the base of the wall is the 7/8" of corrugated panel, which drips clear. The stem must NOT stand out past the sheathing — a 6" core (11" section) is what makes the two reconcile while keeping 4 1/2" of the 5 1/2" PT sill plate bearing on concrete. The leftover 3 3/8" of section shows up on the *inside* as a curb below the drywall, which is where a curb belongs in a garage.

- Cap the curb: an up-turned metal flashing tucked behind the wood wall's interior drywall, sloped back into the room, with a drip at the inboard edge. Water running down the stud wall's interior face (splash, a hosed-down wall, condensation) is diverted out onto the curb top and into the garage instead of tracking down behind the drywall and into the ICF's board joint below.

- Roof: gable trusses **@24" o.c.** (16" until 2026-08-31 — a 24'-span 2×4 fink is an essentially unchanged truss at either spacing, so this is ~33% fewer trusses of the same design) with drip edge, fascia board + trim and vented soffit (coated aluminum recommended). OSB sheathing + underlayment (e.g., synthetic or self-adhering) + metal roofing (optional rainscreen mesh). Metal roofing shown with 16" o.c. support spacing per manufacturer system. Vented ridge not shown.

- ICF brick ledge forms may be used per manufacturer guidelines for heavy sidings.

- Expansion joint recommendation: 1" XPS foam covered with 1/2" traffic-rated polyurethane sealant to separate garage slab from driveway.

- Seal for 1 hour fire rating (UL listed or as per IBC table 722.6.2(1) and table 722.6.2(2), sealed Type X 5/8" drywall and seal penetrations with ASTM E814 rated sealants) or use listed 1-hr wall (e.g. UL U301). Confirm per R302.6 if garage near dwelling.

