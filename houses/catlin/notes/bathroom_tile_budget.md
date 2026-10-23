# Bathroom tile budget correction — 2026-10-22

BATH1 is economy tile. The first substitutes were too expensive: Jeffrey Court
hex was $14.90/SF versus the original MSI's $9.79/SF; TileBar Carrara was $6.40/SF
versus the original HDC's $1.97/SF. They are superseded, not current selections.

| Room | Original tile | Current tile | Tile-only increase |
|---|---:|---:|---:|
| RM-M-BATH2 | MSI CALGLD-2HEXMC $9.79/SF | Qube Bode nominal 3-inch hex $9.49/0.84-SF sheet = $11.30/SF | $1.51/SF, 15.4% |
| RM-S-BATH1 | HDC NHDCAR2424P $1.97/SF | Florida Tile CHDEAJ0212X24 $2.38/SF | $0.41/SF, 20.8% |

BATH1 changes from 24-inch squares to 12x24 rectangles to preserve the economical
intent while retaining a matte Carrara look and published wet DCOF >=0.42.
White epoxy grout stays, at the brochure's recommended 1/8-inch joint. Its
manufacturer brochure gives 9 mm thickness; the retailer specifications conflict,
so verify the delivered thickness before setting beds.

The gold hex keeps nominal 3-inch matte porcelain: actual chips are listed as
2.86 x 2.86 inches, 0.26 inch thick. The larger chips avoid the original nominal
2-inch format ambiguity over DITRA-HEAT. The seller describes floor/wall and
pool/shower use but supplies no numeric DCOF. Confirm application and stock.

## Current takeoff and purchasing arithmetic

`floor_finish_rows` gives 64.9 SF net / **75 SF order** for RM-M-BATH2 and
71.8 SF net / **83 SF order** for RM-S-BATH1, including the existing 15% waste
allowance and takeoff order-area rounding.

At those order quantities, comparing tile-only rates gives about **$147 more**
than the original selections: $113 for hex plus $34 for Carrara. This replaces
about $751 of premium from the first substitutes, a reduction of about $604.

Purchasing whole listed packages gives a different comparison:

| Room | Original packages | Current packages | Difference |
|---|---:|---:|---:|
| RM-M-BATH2 | 6 x 14.85-SF MSI cases at $145.35 = $872.10 | 90 x 0.84-SF Qube sheets at $9.49 = $854.10 | -$18.00 |
| RM-S-BATH1 | 6 x 16-SF HDC cases at $31.52 = $189.12 | 7 x 13.3-SF Florida Tile cases at $31.69 = $221.83 | +$32.71 |
| Combined | $1,061.22 | $1,075.93 | **+$14.71** |

The hex baseline uses the original MSI's equivalent case SKU CALGLD-2HEXMC;
original single-sheet pricing was not displayed, and buying sheets instead may
reduce its baseline. Do not treat the whole-case comparison as a guaranteed
landed-cost premium. Prices checked 2026-10-22; tax, shipping, promotions and
supplier availability can change. Qube charges project shipping separately;
obtain the delivered quote before purchase and reject freight that defeats the
budget comparison. Free sample shipping does not mean free tile shipping.

`prices.toml` retains installed-cost estimates, separately from these tile-only
quotes: finish materials include setting supplies and epoxy grout; membranes,
backer, and the existing heat cable remain in their respective scopes. Labour
allowances are unchanged. No separate epoxy grout charge is added.

Sources:
- [Original MSI, equivalent case](https://www.homedepot.com/p/326448203)
- [Current Qube Bode hex](https://qubetiles.com/products/calacatta-gold-marble-look-mosaic-porcelain-hexagon)
- [Original HDC Carrara](https://www.homedepot.com/p/305849487)
- [Current economy matte Carrara](https://www.homedepot.com/p/308323204)
- [Florida Tile brochure](https://images.thdstatic.com/catalog/pdfImages/9b/9b836d67-5679-42c6-a86c-da1be26efe2d.pdf)
