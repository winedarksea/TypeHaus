# Box supports: how each catlin box holds to its framing (decision #149)

Read 2026-11-21. [D] means a dimensioned drawing, [T] spec-sheet or catalog text, and [R] a retailer or distributor listing.
The `BoxRow.support` rows in `plan/device_boxes.py` come from this note. Where a datasheet gives no section or ear size, the drawn value is representative and says so.

| Row | Product | Mount | Range and basis | Source |
|---|---|---|---|---|
| flush 1-4 gang, luminaire-round | Carlon B122A, BH235A/353A/464A, B520A | `stud_side`: captive nails through molded ears on one side | - | Carlon GM-19 catalog [T]: https://cdn.shopify.com/s/files/1/0586/3306/0405/files/FTEXT004.pdf. ABB e-catalog: https://empower.abb.com/ecatalog/ec/EN_NA/p/B122A-UPC. No published ear thickness, nail positions or set-back; drawn 1/8" ear, front 1/2" proud of the stud. |
| flush_raceway | RACO 235 (was the plain 232) | `stud_side`: TS side bracket, about 7.01" overall | - | https://hubbellcdn.com/specsheet/RACO-8235-SPEC-EN.pdf [D]. The 232 is "No Bracket", so this row now uses its bracketed twin (same 30.3 in3). |
| bracket (new) | RACO 601 on Arlington SL18 | `stud_span`, SL18 billed apart | 12-18" on centres | SL18 instruction sheet [T]: https://www.aifittings.com/media/instruction-sheets/SL18.pdf ("Works with Studs 12" to 18" on-center", bar 10 3/16"-16 7/8"). Catalog page: "Can mount a steel box via the pilot holes on the bar". RACO 601: https://hubbellcdn.com/specsheet/RACO-601-SPEC-EN.pdf (3 x 2 x 3-1/2, 18.0 in3, NMSC L clamps). |
| ceiling | Appleton FFS561LDNBH | `joist_span`: telescoping flat bar, box hung under it | 16-24", read as centres | Appleton OB/SB-1 page [T]: https://rexel-cdn.com/products/appleton-ceilingfanboxes.pdf?i=2DDE8A78-35CE-4FD8-9AB0-F8D28D999860 ("NBH, 16" to 24""). The basis is not printed; centres is the reading by analogy with RACO and Arlington. The bar section is unpublished. |
| fan | RACO 929 | `joist_span`: two telescoping rectangular channels, flanged barbed ends | "fits 16"-24" o.c." | https://hubbellcdn.com/salesdrawings/RTB_929_CUSTDWG_EN.pdf [D]. The bar adjusts 14 1/8"-22 1/2" (clear). Channels, not a tube; drawn 7/8 x 3/4. |
| air-sealed-fan | Arlington FBR415F | `joist_span`: adjustable plated-steel bracket, toothed end tabs, 2 #12 screws per end | "16" to 24" on centers" | https://www.aifittings.com/media/line-drawings/FBR415F.pdf [D]. A spanning bracket, not a one-side one. |
| fan, surface | Bell PRCF57550BZ | `member_under`: integrated galvanized bracket, 7.5" | - | https://hubbellcdn.com/specsheet/BELL-PRCF57550BZ-SPEC-EN.pdf [T]. |
| weatherproof | Bell 5361-0 | `member_under`: mounting lugs | - | Die-cast box screwed under the member; lug size drawn representative. |
| air-sealed, air-sealed round | Lessco / Airfoil | `stud_side` (assumed nail-on) | - | **Unconfirmed.** airfoilinc.com fails TLS. Lessco's site describes an enclosure fastened to the framing with its box. CONFIRM on the submittal. |
| surface rows, handy, recessed | RACO 232/192/674, Arlington DVFR1W | none (Tapcon to concrete, pocket back) or `block_profile` | - | Unchanged. |

**Spanning candidates.** Arlington SliderBar is the only retail stud-to-stud bar found that takes a 1- or 2-gang box by dedicated holes.
Its own SLB101 is 17.0 in3, too small for a through-fed 12 AWG device; hence the RACO 601. Arlington says "Mounts a Plastic or Metal Box".
No stud-to-stud bracket exists for a 4" round box. Carlon B620K (bar hanger, 14.38"-22.50") is the ceiling equivalent.
nVent CADDY TSGB/TB brackets are made for steel boxes, and plastic-box fit is unconfirmed. No owner pick was needed: one candidate survived.

**Review fan-out (211 moved devices, four zones).**
- **Bracketed (9):** the B-BATH, M-BATH2 and S-BATH1 mirror lights, the PLAY-N up/down pair (SCONCE5/6), MUDROOM-SCONCE, PANTRY-SW, STUDIO-RC6 and SUITE-RC7. The M-BATH1, SUITEBATH and STUBATH mirror lights keep nail-on seats: each box lands under 1 3/8" off its light, inside the canopy, so the light stays put.
- **Re-stationed onto the other stud:**
  - WORKSHOP-SW3, latch side.
  - G-RC-W, symmetric about the heater.
  - STUDY-SCONCE2: 16" rhythm.
  - STUDY-RC1 and STUDIO-RC1: the gable 6' rule.
  - STUDY2-NOOK-SW: off the SEKTION.
  - SUITE-RC2: off the dresser.
  - M-STAIR-SW: banks with SW2.
  - S-STUDY2-STAIR-SW: off the bookcase.
- **Faults fixed:**
  - A-POCKET-SW lowered 2" below the raked king's top.
  - M-STUDY-RC3 raised to 21" on stud-000.
  - S-SUITEBATH-RC1 to 18" (review of #149) on stud-002: seated east of stud-004 it stood 2'-9" from the tub, inside the 3 ft zone; the bay between holds the WC vent.
  - GYM-RC3, LIVING-RC2 and BED1-RC2 on the stud faces that keep the 6' rule.
- **Ceiling fixtures moved into a bay their bar spans:** WORKSHOP-LT6, FURNACE-STRIP2, PLANT-LT, PLANT-TUBE1/2 and GDO-RC.
- **Considered and left:**
  - The vanity sconces: their bays are 8-9" on centres, under SL18's minimum. They keep nail-on seats under 3/4".
  - SUITE-LAMP: an 8" bay. Seated 2" off the bed centre.
  - The ESS lid's boxes bear on its 2x4 furring at 16" o.c.
