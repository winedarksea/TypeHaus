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

- Footing shown as 12"×6" compacted stone footing per IRC R403.1 and R403.4.1 (confirm soil bearing and local acceptance). Footing drain tile recommended.

- Exposed ICF EPS above grade requires protective coating on BOTH interior and exterior sides. Exterior: elastomeric coating, PVC trim, or rigid aluminum sheeting. Interior: 15-minute thermal barrier per IRC R316.4 (5/8" exterior-rated gypsum or approved intumescent coating).

- Grade: IRC R401.3 requires minimum 6" fall within first 10 feet from foundation.

- Slab: minimum 3.5" thick, ≥3,500 psi per IRC R506.1. Slab must be sloped (typically toward overhead door).

- Wood wall (REBUILT 2026-08-31; what stood here before that date was 2×6 @16" o.c. with 1.5" Zip-R continuous sheathing, Method CS-G, and empty bays): 2×6 studs **@24" o.c.**, **5/8" CDX** sheathing, **2" of 2 lb closed-cell spray foam in the bays**, **7/8" corrugated 26 ga PVDF exposed-fastener steel panel** in the house white, screwed through its crowns into the studs with #9 × 1-1/2" 316 stainless gasketed panel screws. Interior finish: 5/8" drywall. Whole-wall R-13.2 (`haus explain GARAGE_WALL_2X6 --card`), roughly double the honest R-7–8 the empty-bay Zip-R wall carried — the R-14.3 that assembly's card used to read was an artifact of billing an uninsulated 5.5" stud bay as solid SPF.

- **No WRB, and that is a decision rather than an omission.** IRC R703.2's exception releases an unconditioned detached accessory building from the water-resistive barrier, and this is one (`RM-GARAGE` is `conditioned=False`). The ccSPF is the air, water and vapour plane; the CDX is structure and nailbase only. Build order follows from that, exactly as it does on the house: **bucks before foam.**

- **The corrugation is the rainscreen.** There is no furring layer. A 7/8" corrugated sheet screwed to a flat face leaves a continuous open flute behind every panel — more free area than the 3/8" 1×4 vertical furring this wall carried before 2026-08-20 ever gave it. What makes it work rather than making it a trough is the closures: a **vented (inside) closure strip at the base**, so the cavity drains and vents while nothing insect-sized gets in, and a **solid (outside) closure under the head and the rake**, so wind-driven rain and snow do not enter over the top. ~192 LF, both courses. Neither is optional.

- **24" o.c. is deliberate, and there is no 16" zone at the overhead door.** W-G-E is nonbearing — the ridge runs E–W and the trusses bear on W-G-S/W-G-N — and the 16'-0" opening is carried by its own 2-ply 14" LVL on jamb packs sized from the opening, not from field spacing. Field studs beside a nonbearing opening carry nothing extra. The garage's window pair and its service door were re-stationed onto the 24" grid the same day; D-G-OVERHEAD stays where it is and its off-module advisory is a recorded decision (`preferences.toml [checks] suppress`), because every legal station moves the ICF grade beam and makes the two brick piers 5'-0" and 3'-0".

- **Brick ties get cheaper above the datum, but the soldier coursing makes the SPACING the problem.** Corrugated ties are valid only where the brick back is within 1" of framing. Across the old 1.5" Zip-R it was not, so the wainscot wanted screw-on adjustable two-piece ties into studs (IRC R703.8.4). Behind 5/8" CDX the back **is** within 1", so the cheaper corrugated tie is valid above the garage datum. ICF ties below it, unchanged.

  What changed on 2026-09-02 is that the wainscot units now stand on end. A tie has to land in a horizontal **bed joint**, and a soldier field has bed joints only at **-2'-8" (the shelf), -0'-8" and +1'-4"**. The vertical spacing is therefore pinned at 24" — R703.8.4's maximum, not a choice — and 2.67 sf per tie then forces **16" o.c. horizontally**. The wall's studs are at 24" o.c. and cannot give it (24 x 24 = 4.0 sf, 50% over). The old 2" running-bond coursing had a bed joint every 2" and bought the same 2.67 sf at 16" v x 24" h; that option went with the coursing.

  **The fix is blocking, not restudding.** Flat 2x6 blocking fitted in the stud bays at the two bed-joint elevations above the datum (-0'-8" and +1'-4") lets a corrugated tie land at any horizontal station, so the schedule becomes 16" o.c. horizontal in all three joints. That is ~8 lf of blocking per pier against re-framing 25' of east wall at 16" o.c. Below the datum the ICF's webs already allow any station. **The tie row in the TOP joint is mandatory**: without it the upper 24" of soldier is a cantilever off the mid-height row.

- **Take the pier's 5/8" of horizontal slop in the head joints.** Each pier's brick face is 52 5/8" and the soldier module is 2", so a pier is 26 units plus 5/8". Spread across 26 head joints that is ~0.024" apiece and invisible; put it in one place and it is a sliver cut beside a door jamb. The 4'-0" returns divide exactly (24 units) and need none of this.

- Sill: pressure treated sill board over sill gasket and capillary break; provide code-required anchor bolts detailed per IRC R403.1.6 (3"x3" plate washers). Sealed with sealant.

- Top plate must be sealed (e.g., with spray foam or sealant) to create continuous air barrier between interior drywall and exterior sheathing.

- Provide Z-flashing / drip edge at base of exterior wall (liquid flashing recommended) to direct water out over the foundation / protective coating.

- Stem and framing are flush on the outside: the wood wall's SHEATHING face (5/8" CDX since 2026-08-31, 1.5" Zip-R before it — the wall's own `alignment` puts whichever it carries on the node line) and the ICF's exterior EPS face are the same plane, so the only thing standing proud at the base of the wall is the 7/8" of corrugated panel, which drips clear. The stem must NOT stand out past the sheathing — a 6" core (11" section) is what makes the two reconcile while keeping 4 1/2" of the 5 1/2" PT sill plate bearing on concrete. The leftover 3 3/8" of section shows up on the *inside* as a curb below the drywall, which is where a curb belongs in a garage.

- Cap the curb: an up-turned metal flashing tucked behind the wood wall's interior drywall, sloped back into the room, with a drip at the inboard edge. Water running down the stud wall's interior face (splash, a hosed-down wall, condensation) is diverted out onto the curb top and into the garage instead of tracking down behind the drywall and into the ICF's board joint below.

- Roof: gable trusses **@24" o.c.** (16" until 2026-08-31 — a 24'-span 2×4 fink is an essentially unchanged truss at either spacing, so this is ~33% fewer trusses of the same design) with drip edge, fascia board + trim and vented soffit (coated aluminum recommended). OSB sheathing + underlayment (e.g., synthetic or self-adhering) + metal roofing (optional rainscreen mesh). Metal roofing shown with 16" o.c. support spacing per manufacturer system. Vented ridge not shown.

- ICF brick ledge forms may be used per manufacturer guidelines for heavy sidings.

- Expansion joint recommendation: 1" XPS foam covered with 1/2" traffic-rated polyurethane sealant to separate garage slab from driveway.

- Seal for 1 hour fire rating (UL listed or as per IBC table 722.6.2(1) and table 722.6.2(2), sealed Type X 5/8" drywall and seal penetrations with ASTM E814 rated sealants) or use listed 1-hr wall (e.g. UL U301). Confirm per R302.6 if garage near dwelling.

