---
title: "Roof-to-Wall Eave Detail Notes"
applied_to:
  - detail: roof_wall_eave_detail
tags:
  - roof
  - wall
  - eave
  - air-barrier
  - vapor-barrier
  - insulation
source:
  - plan/assemblies.py CATLIN_ROOF
  - params/roof_trim.py
---

# Notes

- Roof framing: 11-7/8" I-joists at 16" o.c. on the double top plate; birdsmouth seat cut with beveled bearing stiffeners (APA D710 10h) or a beveled plate (D710 10q, extra uplift fasteners). Structural ridge beam per D710 10c — not a rafter-tie roof. 4:12, zero overhang.

- Cavity: R-19 fiberglass batt (6-1/4") held to the ceiling side. The remaining ~5-5/8" is left open deliberately — the exterior foam keeps the sheathing above dew point, so that depth is condensation margin, not a shortfall.

- AIR barrier: 1/2" ZIP sheathing, seams taped, lapping the wall sheathing membrane for continuity.

- VAPOR barrier: self-adhered sheet over the taped ZIP, under the foam. NOT OPTIONAL — ZIP is Class III (2 perm) and does not replace it. Without this layer the dew point lands inside the polyiso. With it, every control layer is outboard of the structure and the interior finish is PAINT ONLY: no ceiling poly, no smart membrane, no vapour-retarder primer.

- Roof CI: two courses of 3" polyiso, 6" total. STAGGER the seams between courses and tape each course — a single 6" board leaves a joint running unbroken from deck to deck.

- Nailbase top deck: 5/8" OSB screwed through the foam into the rafters on a 16" x 24" grid. 7.165" of penetration + 1-1/2" embedment = 10" SDWH191000DB. The 8" SDWS used on the walls is short here.

- Field underlayment: vapour-PERMEABLE synthetic, NOT peel-and-stick. Full-field self-adhered (0.05 perm) matches the deck vapour barrier and seals the foam and OSB on both faces with no way to dry. Self-adhered ice barrier still runs at eaves and valleys per MN code — that band is narrow enough not to close the field's drying path.

- Vent mat: ~1/4" ventilated nylon-matrix mat, panel clips screwed through it into the top deck. Not a furring strip, and not optional — standing seam is vapour-impermeable, so this is the assembly's only outward drying path.

- Roofing: 24 ga architectural standing seam, mechanically field-seamed, concealed floating clips.

- Eave bay blocking: close every rafter bay over the top plate with rigid foam blocking set in the plane of the wall sheathing, sealed to the joist webs and the plate with canned foam. This is what carries the air barrier across the eave from the wall sheathing up to the roof ZIP. With a paint-only interior there is no second line of defence inboard of it, so an unblocked bay vents the ceiling straight into the vent mat.

- Wall: 2x6 studs (LSL on the main storey), 1/2" sheathing taped over a liquid membrane air barrier, continuous CI 2" polyiso + 2" EPS (outer layer taped), 1/2" furring, standing-seam cladding. Class III interior paint on drywall.

- Foam interface: leave the angled mismatch between roof foam and wall foam; fill with closed-cell spray polyurethane foam. Avoid high-expansion foams — they lift the roof foam off the deck barrier.

- Drip edge: its flange lies ON the top deck (underside at 7.55" vertical above the deck datum), running 1-1/2" back onto the deck from the roof edge, with the field underlayment lapped OVER it. Nothing ELSE in the eave chain may reach that plane — the underlayment has to ride over exactly one thing to bond to the deck. The turn-down hangs at the trough mid-width, throwing runoff into the middle of the gutter rather than down the wall behind it.

- Gutter: 6" box gutter, back sheet tucked a lap BEHIND the corner trim's formed face — behind the sheet itself, not merely inboard of the 1.25" of plan depth it hangs at the end of. Rim 4.38" above the deck datum, a lap under the trim's lower edge (the trim's leg is 4", not the 2" this chain was first derived from). Downspout steadied with conduit pipe clamps (not primary support).

- No fascia and no soffit: roof and wall are one continuous standing-seam skin over a flush zero-overhang edge, so the resolver draws a corner trim angle instead. Every eave offset is measured off that trim's face.

- Build order (water laps downhill, so the eave chain is the part that gets built backwards): frame and block the eave bays -> ZIP, taped -> deck vapour barrier -> polyiso course 1, taped -> polyiso course 2, staggered and taped -> OSB top deck on the 10" screws -> ice barrier at eaves and valleys only -> DRIP EDGE -> field underlayment lapped OVER the drip -> vent mat -> standing seam -> gutter, back sheet behind the trim. The drip edge goes on before the field underlayment, not after.
