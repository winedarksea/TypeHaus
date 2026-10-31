# Exterior darks: one palette, two switches

2026-10-30. Every dark on the exterior takes its name and colour from
`plan/exterior_palette.py`. `METAL` recolours all exterior metal and everything matched to it,
and `WINDOW` recolours the Drutex caps. Swap the facade there; tags name the product, never
the colour, so a swap moves no price row, test or golden key. Hexes are the makers' own chips
or published sRGB, never pre-darkened (the viewer crushes a dark, it does not lift it).
Screen colour is approximate; a physical sample governs.

## The switches

| Switch | Standard | Options in the file |
|---|---|---|
| `METAL` | Metal Sales 24 ga PVDF **Slate Grey (W38)** `#4d4b50`, SR 0.30 / SRI 30 | Matte Black (106) `#252122` 0.27/26 · Medium Bronze (H4) `#3a2c1a` 0.30/31 · Dark Bronze (50) `#372c22` 0.30/30 |
| `WINDOW` | RAL **7016** Anthracite grey `#3b4044` | 7021 Black grey `#323537` · 9005 Jet black `#131516` |

**Why Slate Grey and not Charcoal (17).** Siding and roofing are 24 ga or heavier (owner).
Charcoal (17) and Black (06) are Metal Sales Colorfast45 (SMP) colours, sold in 26 and 29 ga
only. Slate Grey is the darkest grey in the 24 ga PVDF line, and on Metal Sales' own printed
guide it reads darker than Charcoal (17) (`#4d4b50` vs `#65646b`). The SR is the same: Charcoal
(17) is 0.30 / SRI 31 on the 26 ga guide and 0.29 / 29 on the 01/2025 29 ga Eastern guide.
Black (06) is 0.30 / 31 on the 26 ga guide but 0.20 / 17 on the 29 ga Eastern one.

## What follows `METAL`

| Element | Tag | How it follows |
|---|---|---|
| Roof edge chain, trim coil, casings, guards, garage fascia | `metal-dark-exterior` | the colour itself |
| BBD75 band, Transition Trim 55536XX | `bbd-transition-trim` | the colour itself |
| Rainscreen base Z, balcony base flashings | `metal-flat-sheet` | Metal Sales PVDF flat, the colour itself |
| Garage stem band and stem-top Z | `aluminum-flat-pvdf` | **does not follow**: fixed Una-Clad Matte Black `#2d2d2e` aluminium |
| K-style gutters and leaders | `metal-dark-kstyle` | coil colour-matched; Metal Sales publishes no gutter line |
| Canopy steel-post powder coat | `steel-hss-duplex` | matched |
| Basement XPS band coating | `foundation-coating-acrylic-tinted` | custom Tuff II tint (no stock dark) |
| Entry door paint; entry, service and French door frames | `door-paint-exterior` | matched site paint |
| 9 escape casements | `andersen-400-exterior` | by family: Black (grey, black) or Dark Bronze; Andersen 400 has no grey |
| French-door returns/casing | `captivate-sheet` | by family: Dark Shale `#5c5b5e`, Midnight Black `#20201f`, Warm Coffee `#776956` |
| Overhead door | `clopay-classic-steel` | fixed Charcoal `#535353`; Clopay Black is R-6.5 only |

## Trade-offs recorded

- **The garage stem band and its Z are aluminium; the rainscreen base Z is Galvalume.** All
  three went to Metal Sales steel for one maker. The band and the stem-top Z then went back
  to aluminium the same day, because aluminium's oxide re-forms in chloride at the plowed,
  salted apron. Metal Sales sells no aluminium flat sheet, so these two are Una-Clad
  (Elevate), which is made in Anoka, MN: 3105-H14 in 48" x 120" sheet, 0.050" for the band
  and 0.040" for the Z, and Matte Black is stocked in both gauges. Una-Clad's Charcoal Gray
  stops at 0.040" and its Slate Gray is lighter than W38, so black was the closest stocked
  dark. Hems are open (2T/3T minimum radius). Where the Galvalume corrugated panel oversails
  the Z, put sealant or EPDM between them.
- **The MMI service-door leaf** is not repainted by the palette; its frame is.

## Sources

Metal Sales 24 ga colour guide, 02/2026 Impact Steel Buildings edition (swatches), the H&H
Metals copy of the 24 ga guide (SR/TE/SRI), the 26 ga guide (goroofitright.com copy) and the
29 ga Eastern guide 01/2025 (Colorfast45 SR); Metal Sales PVDF flat-stock data sheet; the
ral-farben.de colour list; Andersen's black and dark-bronze swatches; the AZEK Captivate 2025
swatch set; Clopay paint-colour chips; Una-Clad colour selection chart 1185 03/2026 (swatch
and gauge grid) and Elevate TIS 2016 (2026-08-11). All read 2026-10-30.
