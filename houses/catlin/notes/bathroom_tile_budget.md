# Bathroom tile budget correction — 2026-10-22, onyx floors 2026-10-29

BATH1 is economy tile. The first substitutes were too expensive: Jeffrey Court
hex was $14.90/SF versus the original MSI's $9.79/SF; TileBar Carrara was $6.40/SF
versus the original HDC's $1.97/SF. They are superseded, not current selections.

| Room | Original tile | Current tile | Tile-only increase |
|---|---:|---:|---:|
| RM-M-BATH2 | MSI CALGLD-2HEXMC $9.79/SF | Ivy Hill Selene Opera Blue 24x48 EXT3RD101601 $123/15.49-SF case = $7.94/SF | -$1.85/SF, -18.9% |
| RM-S-BATH1 | HDC NHDCAR2424P $1.97/SF | Florida Tile CHDEAJ0212X24 $2.38/SF | $0.41/SF, 20.8% |
| RM-S-VANITY | Sunwings Flower Blue glass mosaic $7.69-9.09/SF | MSI Agua Linda 24x48 NHDAGULIN2448PC ~$46.22/16-SF case = $2.89/SF | -$4.80 to -$6.20/SF |

BATH1 changes from 24-inch squares to 12x24 rectangles to preserve the economical
intent while retaining a matte Carrara look and published wet DCOF >=0.42.
White epoxy grout stays, at the brochure's recommended 1/8-inch joint. Its
manufacturer brochure gives 9 mm thickness; the retailer specifications conflict,
so verify the delivered thickness before setting beds.

**2026-10-29: both blue-room floors went to 24x48 polished onyx-look porcelain**,
platinum epoxy grout at 1/16-inch rectified joints, replacing the Qube Calacatta Gold hex
(BATH2) and the Sunwings glass mosaic (VANITY). Opera Blue's listing gives wet DCOF >=0.42
as read by the owner; TileBar sells the same print as "Lumina Onyx Opera Blue" at "<.42",
so verify on the delivered box. Agua Linda's listing gives <0.42 and recommends dry areas;
the owner accepts it for a sinks-only room. Large format needs a substrate flat to 1/8 inch
in 10 ft (ANSI A108.02); VANITY drops the mosaic's cement backer for a 1/8-inch uncoupling
membrane, and saves the mosaic's setting labour.

## Current takeoff and purchasing arithmetic

As of 2026-10-29, `floor_finish_rows` gives **39.5 SF net / 48 SF order** for
RM-M-BATH2 and **19.3 SF net / 24 SF order** for RM-S-VANITY, at the 20% large-format
waste allowance, and **59.9 SF net / 69 SF order** for RM-S-BATH1 at 15%, each with
takeoff order-area rounding. These quantities
exclude the full master tub enclosure and prefabricated shower/tub bases;
tile remains beneath the vanity and toilet. Companion membranes use the same
net and order areas. RM-S-SUITEBATH is 34.2 SF net / 40 SF order; the attic
neo-angle shower leaves 28.4 SF of sheet vinyl. The sauna's concrete sealer
continues beneath its base.

At those order quantities, BATH2 and BATH1 tile-only come to about **$61 less** than the
original selections: -$89 for Opera Blue, +$28 for Carrara.
The earlier 75/83 SF order quantities included flooring beneath bathing fixtures.

Purchasing whole listed packages gives a different comparison:

| Room | Original packages | Current packages | Difference |
|---|---:|---:|---:|
| RM-M-BATH2 | 4 x 14.85-SF MSI cases at $145.35 = $581.40 | 4 x 15.49-SF Opera Blue cases at $123 = $492.00 | -$89.40 |
| RM-S-BATH1 | 5 x 16-SF HDC cases at $31.52 = $157.60 | 6 x 13.3-SF Florida Tile cases at $31.69 = $190.14 | +$32.54 |
| Combined | $739.00 | $682.14 | **-$56.86** |

RM-S-VANITY buys 2 x 16-SF Agua Linda cases, ~$92. The hex baseline uses the original
MSI's equivalent case SKU CALGLD-2HEXMC. Do not treat the whole-case comparison as a guaranteed
landed-cost premium. Prices checked 2026-10-22; tax, shipping, promotions and
supplier availability can change.

`prices.toml` retains installed-cost estimates, separately from these tile-only
quotes: finish materials include setting supplies and epoxy grout; membranes and the
existing heat cable remain in their respective scopes. The 24x48 rows carry large-format
labour ($10-18/SF). No separate epoxy grout charge is added.

Sources:
- [Original MSI, equivalent case](https://www.homedepot.com/p/326448203)
- Current Ivy Hill Selene Opera Blue, Home Depot EXT3RD101601 (read 2026-10-29)
- Current MSI Agua Linda, Home Depot NHDAGULIN2448PC (read 2026-10-29)
- [Original HDC Carrara](https://www.homedepot.com/p/305849487)
- [Current economy matte Carrara](https://www.homedepot.com/p/308323204)
- [Florida Tile brochure](https://images.thdstatic.com/catalog/pdfImages/9b/9b836d67-5679-42c6-a86c-da1be26efe2d.pdf)
