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

**REBUILT 2026-08-31 — FLASH-AND-BATT, AND EVERY OUTSULATION LAYER DELETED.** What follows
is the current stack. The nine-layer version this note described (taped ZIP -> self-adhered
deck vapour barrier -> 3" + 3" polyiso -> 5/8" OSB nailbase on 10" SDWH screws -> permeable
synthetic underlayment -> 1/4" vent mat) is recorded in `notes/roof_flash_and_batt.md` §Why,
along with the arithmetic and the code path that replaced it. **Read that note before
changing anything here** — several of the rules it retired look like rules you would want to
reinstate, and each of them was load-bearing only for the stack it belonged to.

- Roof framing: 11-7/8" **TJI 230 at 24" o.c.** on the double top plate (was an unspecified
  11-7/8" I-joist at 16" o.c.); birdsmouth seat cut with beveled bearing stiffeners (APA D710
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
  packed SOLID; there is no unfilled remainder any more, and the "condensation margin" that
  remainder used to be is now the foam's own R (see the code path below).

- AIR + VAPOUR barrier: **the ccSPF itself**, bonded and seamless, ~0.32 perm at 5" — a Class
  II retarder, which is what IRC/MSRC R806.5 item 4 requires of an air-impermeable layer in
  climate zones 5-8. The taped ZIP that used to be the air barrier is gone with the ZIP.
  **The interior is still PAINT ONLY**: no ceiling poly, no smart membrane, no
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
  PV clamps. **Do NOT substitute a permeable synthetic to save the difference**: the
  reasoning that used to require one is inverted now (there is no drying path to protect and
  no foam sealed on two faces), and the cheap sheet is a mechanically-fastened,
  non-self-sealing water layer under every one of those screws.

- **No vent mat, and no permeable underlayment.** They were one decision, not two: above the
  underlayment sits a 0-perm metal panel, so the only thing a 20-perm sheet could dry into
  was the gap the mat made. Delete either and the other stops earning its cost. The
  condensation criterion is IRC/MSRC **R806.5 item 5.3** instead — air-impermeable insulation
  in direct contact with the sheathing at the Table R806.5 R-value (R-25 zone 6, R-30 zone 7;
  5" of ccSPF is R-32.5 and clears both), with the air-permeable insulation directly under
  it — under which outward drying is not required. `code.R806_5_unvented_roof` grades it and
  the condensation gate defers to it by name.

- Roofing: 24 ga architectural standing seam, mechanically field-seamed, concealed floating clips.

- Eave bay blocking: close every rafter bay over the top plate with rigid foam blocking set in the plane of the wall sheathing, sealed to the joist webs and the plate with canned foam. This is what carries the air barrier across the eave from the wall sheathing up to the ROOF BAY'S OWN FOAM — the plane it hands off to changed on 2026-08-31, the job did not. With a paint-only interior there is no second line of defence inboard of it, and an unblocked bay now vents the ceiling into the joist bay itself.

- Wall: 2x6 studs (LSL on the main storey), 1/2" sheathing, then **4" of closed-cell spray foam around an intermittent 2x4 truss** — a flat block on the sheathing, a 1/2" plywood tab, a KDAT 2x4 outrigger on edge at 16" o.c. — and standing-seam cladding clipped to the outriggers. Class III interior paint on drywall. **No WRB:** the foam is the water plane (2026-08-23; was a liquid membrane over the sheathing under 2" polyiso + 2" EPS and 1/2" furring). The cladding face is 5-1/2" proud of the sheathing, not 5.02", which is what `params/roof_trim.py::_WALL_OUTBOARD_IN` carries and what moved the whole eave water chain out with it.

- Foam interface: leave the angled mismatch between roof foam and wall foam; fill with closed-cell spray polyurethane foam. Avoid high-expansion foams — they lift the roof foam off the deck barrier.

- Drip edge: its flange lies ON the structural deck (underside at 0.70" vertical above the deck datum since 2026-08-31, was 7.55" over the nailbase), running 1-1/2" back onto the deck from the roof edge, with the adhered membrane lapped OVER it. Nothing ELSE in the eave chain may reach that plane — the underlayment has to ride over exactly one thing to bond to the deck. The turn-down hangs at the trough mid-width, throwing runoff into the middle of the gutter rather than down the wall behind it.

- Gutter: 6" box gutter, back sheet tucked a lap BEHIND the corner trim's formed face — behind the sheet itself, not merely inboard of the 1.25" of plan depth it hangs at the end of. Rim 2.76" BELOW the deck datum since 2026-08-31 (it was 4.38" above it), because the 4" trim leg it laps under now hangs 3.26" below a roofing underside only 0.74" up, a lap under the trim's lower edge (the trim's leg is 4", not the 2" this chain was first derived from). Downspout steadied with conduit pipe clamps (not primary support).

- No fascia and no soffit: roof and wall are one continuous standing-seam skin over a flush zero-overhang edge, so the resolver draws a corner trim angle instead. Every eave offset is measured off that trim's face.

- Build order (water laps downhill, so the eave chain is the part that gets built backwards): frame and block the eave bays -> 5/8" CDX deck, oversailing the girts -> **moisture-meter hold point, < 16% MC** -> DRIP EDGE -> adhered butyl membrane lapped OVER the drip, full field -> standing seam -> gutter, back sheet behind the trim; then, from inside, 5" ccSPF against the deck underside -> **void inspection, every bay** -> R-30C batt -> 5/8" gypsum -> paint. The drip edge still goes on before the membrane, not after. **The insulation is now an INTERIOR operation and follows the roof being closed in**, which is the single biggest sequencing change from the nailbase stack: the deck can be dried in on day one and the foam sprayed against a dry deck weeks later.
