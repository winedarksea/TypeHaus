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
  - plan/assemblies.py ROOF
  - params/roof_trim.py
---

## Sheet notes

### General
- Roof: 11-7/8" TJI 230 at 24" o.c., LSSR hangers to a structural ridge beam.
- Bay: 5" ccSPF on the deck, R-30C batt below. The foam is the air and vapour barrier; paint-only ceiling.
- Deck: 5/8" CDX, 40/20, oversailing the rafter ends to the girt face.
- Butyl membrane, 240 F min, full field. 24 ga standing seam on floating clips.
- Wall: 2x6, 1/2" sheathing, 4" ccSPF around 3-ply blocks, 1/2" vent gap, 1-1/2" KDAT girts at 24", 1-1/4" PBR. No WRB.

### Keyed
- [K1] Birdsmouth seat: beveled web stiffeners per APA D710 10h; H2.5A each rafter.
- [K2] Foam first lift 1-1/2" min. Lap onto ridge beam and hanger flanges in one pass.
- [K3] 2x6 eave block on edge on the plate, every bay. ccSPF over it.
- [K4] Roof-to-wall foam angle: closed-cell fill. No high-expansion foam.
- [K5] Formed drip edge, one piece: flange 2" on the deck at 6:12, nose over the deck edge.
- [K6] Lap the membrane over the drip. Nothing else reaches that plane.
- [K7] 6" box gutter, rim 2.76" below the deck datum, back sheet behind the drip face.
- [K8] Drip face 4" over the wall panel heads, kick into the gutter. No fascia, no soffit.
- [K9] 2x6 girt on 3-2x6 standoffs, 2 TLOK08 each. Gutter hanger at each standoff.

### Spec 07 21 00
- Hold point: plywood under 16% MC, bay by bay, before foam.
- Hold point: inspect every bay for voids before the batts go in.

### Spec 07 61 00
- Measure every eave offset off the drip edge face, 1-1/4" outside the panel face.
- Build order: block, girt, deck, gutter, drip edge, membrane, standing seam. Insulate from inside after.

# Notes

**FLASH-AND-BATT.** What follows
is the current stack. `notes/roof_flash_and_batt.md` §Why carries the arithmetic and the code
path that replaced the prior nailbase stack. **Read that note before
changing anything here** — several of the rules it retired look like rules you would want to
reinstate, and each of them was load-bearing only for the stack it belonged to.

- Roof framing: 11-7/8" **TJI 230 at 24" o.c.** on the double top plate;
  birdsmouth seat cut with beveled bearing stiffeners (APA D710
  10h) or a beveled plate (D710 10q, extra uplift fasteners). Structural ridge beam per D710
  10c — not a rafter-tie roof. **6:12**, zero overhang. The spacing is NOT FINAL: the printed
  TJ-4000 table assumes bearing at the high end and these joists hang off the ridge on LSSR
  hangers, so ForteWEB owns the last word. See `notes/roof_flash_and_batt.md` §8.

- Cavity, upper: **5" of closed-cell spray foam in direct contact with the deck underside.**
  Minimum 1.5" first lift, full adhesion, no voids. It laps continuously onto the ridge
  beam's side faces and over the hanger flanges IN THE SAME PASS — the most awkward
  air-barrier junction in the roof, free if specified and the detail most likely to be
  skipped. **Moisture-meter hold point: verify the plywood under 16% MC, bay by bay, before
  spraying.** After the batts go in, the deck underside is invisible for the life of the
  house.

- Cavity, lower: **R-30C cathedral batt (8-1/4" nominal) compressed into the remaining
  6-7/8"** — about R-26. It arrives oversized on purpose: friction-fits the flange pockets,
  held tight by the drywall, so there is no sag void over a 20' run of 6:12 slope. The bay is
  packed SOLID; there is no unfilled remainder, and the "condensation margin" a remainder
  would have provided is the foam's own R (see the code path below).

- AIR + VAPOUR barrier: **the ccSPF itself**, bonded and seamless, ~0.32 perm at 5" — a Class
  II retarder, which is what IRC/MSRC R806.5 item 4 requires of an air-impermeable layer in
  climate zones 5-8.
  **The interior is PAINT ONLY**: no ceiling poly, no smart membrane, no
  vapour-retarder primer. That is not a preference here, it is R806.5 item 2 — a Class I
  retarder on the ceiling side of an unvented assembly is prohibited.

- Deck: **5/8" CDX plywood**, smooth (the best bed an adhered membrane and an oil-canning-
  prone pan can have), span-rated 40/20, dries several times faster than OSB and recovers
  strength after wetting. **It oversails the last rafter at each eave and spans the wall
  girts** — the panel clips land on it out to the roof edge. That cantilever is not graded by
  anything in the engine and belongs in the PE scope.

- Membrane: **high-temp self-adhered BUTYL over the whole deck** (>= 240 F; Grace Ultra /
  Henry Blueskin PE200HT class). Full field, not an eave band. Butyl rather than SBS because
  it self-seals around a fastener, and ~1,160 standing-seam clip screws through the field are
  this roof's actual water risk — not pipes, not curbs, and not the 48 non-penetrating S-5!
  PV clamps. **Do NOT substitute a permeable synthetic to save the difference**: there is no
  drying path to protect and no foam sealed on two faces, and the cheap sheet is a mechanically-fastened,
  non-self-sealing water layer under every one of those screws.

- **No vent mat, and no permeable underlayment.** They were one decision, not two: above the
  underlayment sits a 0-perm metal panel, so the only thing a 20-perm sheet could dry into
  was the gap the mat made. Delete either and the other stops earning its cost. The
  condensation criterion is IRC/MSRC **R806.5 item 5.1.3** instead — air-impermeable insulation
  in direct contact with the sheathing at the Table R806.5 R-value (R-25 zone 6, R-30 zone 7;
  5" of ccSPF is R-32.5 and clears both), with the air-permeable insulation directly under
  it — under which outward drying is not required. `code.R806_5_unvented_roof` grades it and
  the condensation gate defers to it by name.

- Roofing: 24 ga architectural standing seam, mechanically field-seamed, concealed floating clips.

- Eave bay blocking: a **2x6 on edge in every rafter bay**, standing on the rafter plate with its outer face tight to the wall sheathing band (`Roof.eave_blocking`). It restrains each rafter laterally at its bearing and is the back-nailer the gutter girt screws into. It fills only the lower 5-1/2" of the 11-7/8" bay, so the cold upper corner stays wood-free and the ccSPF fills over the block, sealing to the webs, the deck and the sheathing. **The air barrier across the eave is the sheathing band plus that foam**, not the block. With a paint-only interior there is no second line of defence inboard of it, and an unsealed bay vents the ceiling into the joist bay itself.

- Wall: 2x6 studs (LSL on the main storey), 1/2" sheathing, then **4" of closed-cell spray foam around three-ply KDAT blocks**, a 1/2" vent gap, one tier of 1-1/2" KDAT girts at 24" courses, and 1-1/4" PBR panel screwed to the girts. Class III interior paint on drywall. **No WRB:** the foam is the water plane. The cladding face is 7-1/4" proud of the sheathing (`params/roof_trim.py::_WALL_OUTBOARD_IN`), and the eave water chain is set out from it.

- Gutter support (`notes/eave_gutter_girt.md`): a flat 2x6 KDAT girt in the girt layer at the eave, on a 3-2x6 standoff at every rafter bay centre, two TLOK08 per standoff through girt, standoff and sheathing into the 2x6 eave block. The gutter hangs on a hidden hanger at each standoff (24" o.c., inside the usual 36" max), screwed through the panel into the girt. **The hanger is drawn, not modelled or billed.**

- Foam interface: leave the angled mismatch between roof foam and wall foam; fill with closed-cell spray polyurethane foam. Avoid high-expansion foams — they lift the roof foam off the deck barrier.

- Drip edge (since 2026-09-26 ONE formed piece per edge, derived by `resolve/roof_drip_edge.py` from `RF-HOUSE.eave_trim.drip_edge`; it replaced both the level authored drip and the corner trim): a flange lying ON the structural deck at the 6:12 pitch (underside 0.70" vertical above the deck datum at the edge), bearing 2" on the plywood inboard of the deck edge (the deck stops at the girt face, 1-1/4" inside the cladding face), with the adhered membrane lapped OVER it; a nose bent over the deck edge, clearing the wall panel heads; a face 1-1/4" outside the panel face with a 4" leg down over the panel heads; and a 1/2" kick out and down into the trough. The same piece runs up both rakes, where it is the barge board.

- Gutter: 6" box gutter, back sheet tucked a lap BEHIND the drip edge's face — behind the sheet itself, not merely inboard of the 1.25" of plan depth it hangs at the end of. Rim 2.76" BELOW the deck datum, because the 4" leg it laps under hangs 3.26" below a roofing underside only 0.74" up. Downspout steadied with conduit pipe clamps (not primary support).

- No fascia and no soffit: roof and wall are one continuous standing-seam skin over a flush zero-overhang edge. Every eave offset is measured off the drip edge's face.

- Build order (water laps downhill, so the eave chain is the part that gets built backwards): frame and block the eave bays -> 5/8" CDX deck, oversailing the girts -> **moisture-meter hold point, < 16% MC** -> gutter, back sheet up behind where the drip face will hang -> DRIP EDGE -> adhered butyl membrane lapped OVER the drip, full field -> standing seam; then, from inside, 5" ccSPF against the deck underside -> **void inspection, every bay** -> R-30C batt -> 5/8" gypsum -> paint. The drip edge goes on before the membrane, not after. **The insulation is an INTERIOR operation and follows the roof being closed in**: the deck can be dried in on day one and the foam sprayed against a dry deck weeks later.

- Eave references (2026-09-16), what set the drip and gutter:
  - Best Buy Metals, *Standing Seam Architectural Install Guide* p.26, "Eave Detail (with gutter)": extended eave drip edge on the deck, panel hemmed around its kick, gutter back flange up behind the drip face, hidden hanger fixed at the fascia line.
  - Western States Metal Roofing WSD-D4 "Eave with Gutter": pre-hung box gutter with an 8" back sheet whose 6" flange runs onto the deck, a gutter eave trim over it (6" flange, 3-1/8" face into the trough, 1/2" hem), joggle cleat, strap at 1/2" clear for thermal movement.
  - Weyerhaeuser TJ-4000: beveled bearing plate and beveled web stiffeners both sides above 1/4:12; roof joists laterally restrained at end bearings (the 2x6 eave block).
  - Gutter hangers at 36" o.c. max is the common industry rule (SMACNA *Architectural Sheet Metal Manual* governs; not read directly). Catlin's 24" follows the standoffs.
