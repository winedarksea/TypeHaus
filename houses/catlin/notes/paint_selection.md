# Interior paint selection (decision #113)

2026-11-03. Model: `plan/paint.py` (`PAINT-STANDARD`), `plan/products_paint.py` (systems and
products), `plan/interior_palette.py` (the one white). Printed on A-604, cited on A-603, billed
in `[envelope_layers]` / `[trim_paint]`.

## 1. Owner decisions (settled)

- A `PaintStandard`, like the trim, box and drywall standards.
- Wet-room paint covers the bathrooms and the laundry, walls and ceilings (eggshell).
- Three accepted brand lines with Benjamin Moore as the basis of design, because a painter
  sticks to one brand: each BM product names its SW and Home Depot equal (`Product.equals`).
- One house white, BM Chantilly Lace OC-65, tinted in whichever line is bought.
- The paint price row is split, and trim and doors are priced from quantities.
- Corian stays Glacier White. Out of scope: gallons, and the Scuff-X mudroom wainscot
  (TODO, reserved for it).

## 2. Systems

Products are chosen on chemistry per dollar, not brand. BM Ultra Spec 500 and SW ProMar 200 HP
are chemistry twins (acrylic, ~42% volume solids, MPI 52 / 145, contractor price well under
Regal Select).

| Mark | Use / sheen | BM (basis of design) | SW | Home Depot |
|---|---|---|---|---|
| PR-1 | Drywall primer | Ultra Spec 500 primer N534 (acrylic, 30% VS) | ProMar 200 Zero VOC primer B28W02600 (25.8 perm published) | **TBD**: Behr drywall primer, data sheet still to read |
| PT-1 | Walls, eggshell | Ultra Spec 500 eggshell N538 | ProMar 200 HP Zero VOC eggshell | Behr Ultra Scuff Defense eggshell (100% acrylic, 38% VS) |
| PT-2 | Ceilings, flat | Ultra Spec 500 flat N536 | ProMar 200 Zero flat (vinyl acrylic; fine on a ceiling) | Behr Ultra Scuff Defense flat (44% VS, MPI 53) |
| PT-3 | Baths + laundry, eggshell | Ultra Spec 500 eggshell N538 (mildewcide) | Duration Home satin A97 | Zinsser Perma-White eggshell |
| PT-4 | Trim, doors, frames, semi-gloss | ADVANCE semi-gloss 793 (waterborne alkyd, MPI 168) | Emerald Urethane Trim Enamel | Behr Urethane Alkyd semi-gloss (confirm the current data sheet; the one in hand is 2019) |
| PT-5 | Accent wall, RM-S-BED1 | Ultra Spec 500 eggshell N538, custom spruce (#2e4a44) | as PT-1 | as PT-1 |

PT-4 is semi-gloss in all three lines so one sheen reads across the house; walls are eggshell
and ceilings flat, so the sheen separates the surfaces, not the colour. PT-5's colour code is
still to be chosen from a physical chip.

ADVANCE and Emerald Urethane cure slowly: 5-7 days before rehanging doors or loading shelves,
and up to 30 days to full hardness. `tasks.toml` carries `cure_days = 7` on the paint visit's
trim checkpoint.

Ruled out:

| Product | Reason |
|---|---|
| Rodda Super II | Not sold in MN; a Pacific Northwest brand |
| PPG / Pittsburgh (Manor Hall, UltraLast, Break-Through) | Sold to AIP in Dec 2024 and mid-rebrand. Manor Hall has no MPI listing; Break-Through has no satin data sheet |
| PPG Permanizer | Exterior only |
| BM "Aura Bath & Kitchen" | Does not exist. Aura Bath & Spa is matte-only at about 3x the price |
| SW Pro Industrial epoxy | About 14 perm, so not actually low-perm; its data sheet bars continuously wet surfaces; 8 h recoat |
| Behr "extra-high TiO2" claim | Unsupported: the SDS gives 15-40%, overlapping every other product |
| Duration / Emerald / Regal on walls | Premium price, no chemistry gain |
| Scuff-X | Scuff technology undisclosed; held for the mudroom wainscot TODO, not trim |

Data sheets: the SW primer sheet read for §3 is the ProMar 200 Zero VOC Interior Latex Primer
product data sheet (B28W02600; a copy at
<https://spreckelsmd.specialdistrict.org/files/aaae18ec3/PRIMER+INTERIOR+DRYWALL+-++ProMar-200-Zero-VOC-Interior-Latex-Primer-Product-Data-1608537.pdf>).
The other figures above are from the 2026-11-03 research runs; their data-sheet URLs were not
carried into this note and should be added when the products are confirmed at order.

## 3. Vapour basis

The engine's `latex-paint` authored 5.0 perm, citing a "published 3-10 perm spread". The
makers' own values are higher: SW primer 25.8; ProMar 200 HP 27.6; ProMar 200 54.2; Emerald
15.9; ProMar 200 flat 70.8. BM and Behr publish none.

Read 2026-11-03: the SW primer sheet gives "WVP Perms (US) 25.8 grains/(hr ft2 in Hg)" beside
"350-400 sq ft/gal @ 4 mils wet; 1.0 mils dry", and states **no test method and no coat
count**. So the per-coat series value (1/(1/25.8 + 2/27.6) = 9.0 perm for primer + two HP coats;
about 13 with standard ProMar 200) cannot be authored as a published result.

Decision: keep **5.0**, rewritten as a value inside IRC R702.7.1's prescriptive Class III band
(latex paint on gypsum is the code's own Class III listing), not a test. The library
`latex-paint` source and the catlin PT-1/2/3 materials say so.

Sensitivity, `haus check houses/catlin --only all` with the paint at 25 perm: **no grade
moves** (3167 pass / 0 fail, identical). The only change is the message on
`building_science.condensation` for `EXT_2X6` and `EXT_2X6_BOARD_BATTEN` ("no rated warm-side
vapour retarder" instead of "Class III"); the tightest plane stays the spray foam at 74% RH,
106 Pa below saturation, in December. The ccSPF governs these walls, not the paint.

## 4. Colour

**BM Chantilly Lace OC-65: one white for walls, ceilings and trim.**

- LRV 90.0 (BM). Hex #F4F6F1 is an aggregator's; BM publishes none.
- Matches AXSTAD's NCS S 0300-N in lightness (aggregator ~#F6F4F0, LRV ~89.9; NCS publishes
  no sRGB).
- No cream: stays clean under 2700 K and suits MSI Frost White ("White-Cool", MSI).
- Corian Glacier White LRV is unverified: request bulletin K-25970LRV.
- Backup: SW Extra White 7006 (#EEEFEA, LRV 85.9) — `interior_palette.WHITE` is the switch.
- Avoid White Dove, Greek Villa, Pure White and Simply White: they cream under 2700 K and
  make AXSTAD and the quartz read cold or grey.
- Before buying: a draw-down of Chantilly Lace beside real AXSTAD and quartz samples under
  2700 K. A cheap owner check, not an approval gate.

The AXSTAD fronts carry no Material (the SEKTION symbols colour them), so the NCS hex lives in
the palette only; MSI, Corian and PAX hexes there are marked placeholders.

## 5. Billing

- `[envelope_layers]` `paint-wall` / `paint-ceiling` / `paint-wet` replace `latex-paint`;
  the split sums to the old 13,785.9 SF. Primer rides in each rate (a primer layer with no
  sourced perm would turn the Glaser walk UNKNOWN).
- `[trim_paint]` `paint-enamel`: painted base and casing by the LF (stock with
  `wood_surface="painted"`; oak, cherry, locust and cedar stay out; skirts and the suite
  battens carry paint in their own rates).
- `[envelope_layers]` `paint-enamel`: interior door leaves and frames, both faces, glass out,
  plus D-M-ENTRY's inside face (`door-paint-white` folded in).
- `[allowances]` `paint-trim-residual` keeps what is still underived: window aprons and
  returns, caulk, fill and mobilisation. `paint-trim-and-doors` is deleted.
