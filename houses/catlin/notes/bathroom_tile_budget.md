# Bathroom tile budget — updated 2026-11-10

BATH1 is economy tile. The first substitutes were too expensive: Jeffrey Court
hex was $14.90/SF versus the original MSI's $9.79/SF; TileBar Carrara was $6.40/SF
versus the original HDC's $1.97/SF. They are superseded, not current selections.

| Room | Original tile | Current tile | Tile-only increase |
|---|---:|---:|---:|
| RM-M-BATH2 | MSI CALGLD-2HEXMC $9.79/SF | Lifeproof Limestone 12x24 LP521224HD1P6 $37.27/15.6-SF case = $2.39/SF | -$7.40/SF, -75.6% |
| RM-S-BATH1 | HDC NHDCAR2424P $1.97/SF | Lifeproof Limestone 12x24 LP521224HD1P6 $2.39/SF | $0.42/SF, 21.3% |
| RM-S-VANITY | Sunwings Flower Blue glass mosaic $7.69-9.09/SF | Ivy Hill Jume Onyx Blue 23.62x47.24 EXT3RD107036, owner allowance $8/SF | -$1.09 to +$0.31/SF |

**2026-11-10: BATH2 and BATH1 share one floor, Lifeproof Limestone 12x24 matte**, replacing
Selene Opera Blue (BATH2, which did not work in the room) and Florida Tile Carrara (BATH1).
Straight grid, long axis along plan Y, 3/16-inch joints (the listing's suggestion; a half
offset, as the product photos show, should be avoided on a 12x24). The listing was read from
third-party copies because Home Depot blocked direct reads: 8 mm vs 5/16 inch, rectification
unconfirmed, DCOF listed at both >=0.42 and >0.60, each clearing the 0.42 wet floor line. Its
"not for shower floors" note does not bite, both showers being on prefabricated bases. Verify
on the delivered box.

Grout on these two floors is MAPEI Ultracolor Plus FA #5014 Biscuit (Lowe's, 10 lb, joints
1/16 to 3/4 inch, sealing typically not required), for Haystack's warm tan; MAPEI makes no
Haystack and no cross-reference is published, so confirm against a cured sample on a tile.
#5015 Bone is the paler fallback. Mapesil T Plus #5014 at changes of plane. Do not run the
floor heat until the grout has cured.

**2026-10-29: the vanity floor went to polished onyx-look porcelain**, platinum epoxy grout at
1/16-inch rectified joints, replacing the Sunwings glass mosaic. It originally used Agua Linda;
the owner replaced it with Jume Onyx Blue on 2026-11-06. Jume lists DCOF <0.42 and no
shower-floor compatibility; the selection remains confined to the sinks-only vanity room. Large
format needs a substrate flat to 1/8 inch in 10 ft (ANSI A108.02); VANITY drops the mosaic's
cement backer for a 1/8-inch uncoupling membrane, and saves the mosaic's setting labour.

## Current takeoff and purchasing arithmetic

As of 2026-11-10, `floor_finish_rows` gives one Limestone row, **98.7 SF net / 114 SF order**
for RM-M-BATH2 and RM-S-BATH1 together at 15%, and **19.8 SF net / 24 SF order** for
RM-S-VANITY at the 20% large-format waste allowance, each with takeoff order-area rounding. These quantities
exclude the full master tub enclosure and prefabricated shower/tub bases;
tile remains beneath the vanity and toilet. Companion membranes use the same
net and order areas. RM-S-SUITEBATH is 34.2 SF net / 40 SF order; the attic
neo-angle shower leaves 28.4 SF of sheet vinyl. The sauna's concrete sealer
continues beneath its base.

The earlier 75/83 SF order quantities included flooring beneath bathing fixtures.

Purchasing whole listed packages gives a different comparison:

| Room | Original packages | Current packages | Difference |
|---|---:|---:|---:|
| RM-M-BATH2 + RM-S-BATH1 | 4 x 14.85-SF MSI cases at $145.35 + 5 x 16-SF HDC cases at $31.52 = $739.00 | 8 x 15.6-SF Limestone cases at $37.27 = $298.16 | **-$440.84** |

Eight cases (124.8 SF) cover the 114 SF order. The Opera Blue and Carrara order this replaces
came to $682.14, so the swap saves $383.98 tile-only.

RM-S-VANITY buys **2 x 15.49-SF Jume cases = 30.98 SF**. At the owner's $8/SF
allowance this is **$247.84 tile-only**, about $155 more than the retired two-case
Agua Linda order ($92.44). Home Depot's listing read 2026-11-06 shows $9.19/SF /
$142.29 per case, or **$284.58 for two cases**; retain $8/SF as the owner budget,
not a verified checkout quote. The $/SF takeoff applies waste and area rounding;
whole-case purchasing is additional rounding, not another waste multiplier.

Jume has 16 print faces, actual dimensions 23.62 x 47.24 inches, and conflicting
10/10.5 mm thickness fields. The floor stack provisionally takes 10.5 mm tile,
1/8-inch membrane and ~0.212-inch combined mortar to stay at 3/4 inch above
subfloor. Verify thickness and bedding with the setter. Platinum epoxy grout
and the 1/16-inch grid remain.

The hex baseline uses the original
MSI's equivalent case SKU CALGLD-2HEXMC. Do not treat the whole-case comparison as a guaranteed
landed-cost premium. Prices checked 2026-10-22; tax, shipping, promotions and
supplier availability can change.

`prices.toml` retains installed-cost estimates, separately from these tile-only
quotes: finish materials include setting supplies and grout; membranes and the
existing heat cable remain in their respective scopes. The 24x48 rows carry large-format
labour ($10-18/SF). No separate grout charge is added.

Sources:
- [Original MSI, equivalent case](https://www.homedepot.com/p/326448203)
- [Current Lifeproof Limestone, LP521224HD1P6](https://www.homedepot.com/p/308500679) (third-party copies read 2026-11-10)
- [Retired Ivy Hill Selene Opera Blue, EXT3RD101601](https://www.homedepot.com/p/312191271) (read 2026-10-29)
- [Current Jume Onyx Blue, EXT3RD107036](https://www.homedepot.com/p/318355007) (read 2026-11-06)
- [Retired MSI Agua Linda, NHDAGULIN2448PC](https://www.homedepot.com/p/330291351) (read 2026-10-29)
- [Original HDC Carrara](https://www.homedepot.com/p/305849487)
- [Retired economy matte Carrara](https://www.homedepot.com/p/308323204)
- [Florida Tile brochure](https://images.thdstatic.com/catalog/pdfImages/9b/9b836d67-5679-42c6-a86c-da1be26efe2d.pdf)
