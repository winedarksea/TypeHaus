# Exterior darks: the black family

2026-11-07 (owner): **every exterior dark follows the "more black" family.** Each one takes its
name and colour from `plan/exterior_palette.py`, except the stock Concrete Grey foundation
coating selected 2026-11-12. `METAL` recolours all exterior metal and
everything matched to it, and `WINDOW` recolours the Drutex caps, the Max Light frames and the
canopy powder coat. Tags name the product, never the colour, so a swap moves no price row, test
or golden key. Hexes are the makers' own chips or published sRGB, never pre-darkened (the
viewer crushes a dark, it does not lift it). No maker here publishes LRV. Screen colour is
approximate, and a physical sample governs.

## Why black

Black is the only family that every product line can follow. Andersen 400 (retired
2026-11-13) had no grey, and Una-Clad stocks no dark grey at the band's 0.050". Both were already black, and both are fixed
by the egress and corrosion decisions, not by colour. Heat gain is a wash: Matte Black is
SR 0.27 / SRI 26 and Slate Grey is SR 0.30 / SRI 30. Metal Sales sells no charcoal in 24 ga.
Charcoal (17) and Black (06) are Colorfast45 SMP, made in 26 and 29 ga only, and the owner's
rule for siding and roofing is 24 ga or heavier, PVDF.

## The switches

| Switch | Now | Options kept in the file |
|---|---|---|
| `METAL` | Metal Sales 24 ga PVDF **Matte Black (106)** `#2c2829`, SR 0.27 / SRI 26 | Slate Grey (W38) `#515055` 0.30/30 · Medium Bronze (H4) `#3b2e25` 0.30/31 · Dark Bronze (50) `#2c2217` 0.30/30 |
| `WINDOW` | RAL **9017** Traffic black `#262625` | 7016 `#3b4044` · 7021 `#323537` · 9005 `#131516` |

RAL 9017 is the closest RAL to Matte Black (106), at CIEDE2000 ΔE 3.5 between the chips. 9005
is much blacker (ΔE 7.5). Matte Black is **not** marked low gloss on the 24 ga guide, while
Slate Grey is.

## Each product

| Element | Tag | Product and colour | Hex | Source |
|---|---|---|---|---|
| Roof edge chain, trim coil, casings, guards and railing metal, garage fascia | `metal-dark-exterior` | Metal Sales 24 ga PVDF Matte Black (106) | `#2c2829` | 24 ga guide chip |
| Rainscreen base Z, balcony base flashings | `metal-flat-sheet` | Metal Sales PVDF Galvalume flat, Matte Black (106) | `#2c2829` | as above |
| K-style gutters and leaders | `metal-dark-kstyle` | aluminium gutter coil, matched to 106 (no maker named; Metal Sales has no gutter line) | `#2c2829` | matched |
| Canopy steel-post powder coat | `steel-hss-duplex` | powder coat `POWDER_RAL`, the RAL nearest `METAL`: RAL 9017 matt | `#262625` | RAL |
| Basement XPS band coating | `foundation-coating-acrylic-tinted` | Styro Industries Tuff II, stock Concrete Grey (darkest stock) | `#8e8f8c` | library display approximation; physical sample governs |
| Entry door paint; entry, service and French-door frames | `door-paint-exterior` | site paint matched to a 106 chip | `#2c2829` | matched |
| French-door composite frame (`frame_material_ref`) | `composite-door-frame` | Therma-Tru composite, site-painted as above | `#2c2829` | matched |
| 29 Drutex caps | `drutex-alucover-cap` | Alucover RAL 9017 matt powder coat | `#262625` | RAL |
| 12 Max Light frames (3 14x24s, 9 escape units since 2026-11-13) | `aliplast-maxlight-powder` | Aliplast RAL 9017 matt powder coat | `#262625` | RAL |
| Garage stem band and stem-top Z | `aluminum-flat-pvdf` | Una-Clad PVDF aluminium Matte Black (fixed; not on `METAL`) | `#2d2d2e` | Una-Clad chip |
| French-door returns and casing | `captivate-sheet` | AZEK Captivate Midnight Black | `#222120` | AZEK swatch |
| Overhead door | `clopay-classic-steel` | Clopay Classic Steel Charcoal, GDU293 R-12.9 (fixed) | `#535353` | Clopay chip; **open** |

## Open

- **Clopay Black at R-12.9.** clopaydoor.com/classic lists Black only as a premium colour,
  "available on select models". Home Depot's Black SKU (GDU266) is R-6.5. Ask the Clopay
  dealer for Black on GDU293. Until then the door stays Charcoal, the one dark outside the
  family.
- **Physical chips.** Put Metal Sales 106, RAL 9017 matt and Una-Clad Matte Black side by side
  before ordering.
- **Stock.** Ask the Rogers, MN branch (800.328.9316) whether it stocks 106 in 24 ga. The guide
  says "not all colors stocked at all branches".
- **Drutex warranty.** Get the dark-colour warranty for RAL 9017 on Alucover in writing
  ([procurement §2.6](window_and_door_procurement.md) item 6).

## Trade-offs recorded

- **The garage stem band and its Z are aluminium; the rainscreen base Z is Galvalume.** All
  three went to Metal Sales steel on 2026-10-30, for one maker. The band and the stem-top Z
  went back to aluminium the same day, because aluminium's oxide re-forms in chloride at the
  plowed, salted apron. Metal Sales sells no aluminium flat sheet, so those two are Una-Clad
  (Elevate), made in Anoka, MN: 3105-H14 in 48" x 120" sheet, 0.050" for the band and 0.040"
  for the Z. Matte Black is stocked in both gauges (ΔE 2.9 from 106). Hems are open (2T/3T
  minimum radius). Where the Galvalume corrugated panel oversails the Z, put sealant or EPDM
  between them.
- **Foundation coating: darkest stock colour (owner, 2026-11-12).** Use Styro Industries
  Tuff II **Concrete Grey** over Sticky Mesh HD, two 1/16" coats. Styro's colour sheet lists
  Concrete Grey and White as stock; Foundation Grey, Overcast and the other swatches are
  special order. This replaces the custom match to Metal Sales 106 and closes the custom
  dark-tint confirmation. The foundation colour stays independent of `METAL`. The existing
  `foundation-coating-acrylic-tinted` tag is a retained join key, not a custom-tint requirement.
  `#8e8f8c` is the library's approximate display grey, not a measured product chip.
- **The MMI service-door leaf** is not repainted by the palette. Its frame is.

## Sources

All read 2026-11-07 unless dated. Copies are in the Wave 4 research downloads.

- Metal Sales 24 Gauge Color Guide, PVDF, 9/2026: p.1 swatch fills (read as PDF vector fills),
  p.2 SR/TE/SRI and low-gloss table, metalsales.us.com/wp-content/uploads/2026/09/24-Gauge-Color-Guide_Digital_2026-09.pdf.
  26 ga Eastern guide 9/2026 for Charcoal (17) and Black (06), which are Colorfast45 SMP.
- RAL hexes: ral-farben.de/en/all-ral-colours (9017 `#262625`).
- Drutex IGLO Energy Alucover: the configurator offers the full RAL palette (213 colours) for
  the cap, standard "lakierowanie RAL mat", drutex.com/en-us/products/iglo-energy-alu-cover.html.
- Aliplast: any RAL, Qualicoat 1518, matt, professionals.aliplast.com/en/colour-palette.
- Una-Clad Metal Color Selection 1185 03/2026, pp.1-2 (chip and gauge grid), and Elevate
  TIS 2016 (2026-08-11).
- Andersen black swatch (andersenwindows.com, exterior-colors/black-exterior-80x80.jpg), and
  the help-center page "Exterior Colors for Andersen Windows and Patio Doors".
- AZEK Captivate swatch, azekexteriors.com/products/trim-moulding/prefinished/ (sampled).
- Clopay Classic colours, clopaydoor.com/classic (Charcoal chip read 2026-10-30).
- Styro Tuff II TDS (Home Depot-hosted copies; styro.net now redirects elsewhere).

- Styro Industries Tuff II colour sheet, stock versus special-order colours (read 2026-11-12):
  https://images.thdstatic.com/catalog/pdfImages/9e/9ecc5d27-5094-4503-b1f4-d88cefa6b450.pdf.
