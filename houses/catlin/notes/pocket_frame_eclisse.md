# Pocket frames — Eclisse steel cassettes

**House:** catlin
**Structure:** `D-M-LAUN` (2x4, `W-M-HS3`/`W-M-HS4`) and `D-B-BATH` (2x6, `W-B-BA-E`/`W-B-HALL-W`),
both `DT-POCKET-INT-36` with `pocket_frame="eclisse"`.
**Written:** 2026-10-09.

## Why

Both pockets were Johnson kits: the 1500PF and the 1560. Their steel split studs arrive loose,
and the framer cuts and nails them to the floor and the header, so how flat the pocket ends up
depends on the framer. Eclisse ships a factory-assembled galvanized steel cassette with a
removable track. It is stiffer and much less sensitive to framer skill. It is **not cheaper**:
EKC3680 lists at $342–465 against the 1500PF's ~$149, and the 2x6 EKQ series is around $695 and
special order. The owner chose it for durability.

## What the tech sheet fixes

From ECLISSE Single 2x4-2x6, technical sheet 11/2022 (eclisse.us, Support → Single):

| term | value |
|---|---|
| frame size F.S., 36" leaf | 74" x 83" (H1, from finished floor) |
| rough opening | F.S. + 1/2" wide, H1 + 1/4" high: **74 1/2" x 83 1/4"** |
| wall | 3 1/2" (2x4) or 5 1/2" (2x6) structure, same RO |
| door | to 1 3/4" thick, 220 lb (330 lb on request) |
| drywall screws over the pocket | #7 x 1", "do not use screws longer than 1"" |

The RO is 1 1/2" wider than the commodity 2W + 1" (73"), so each pocket runs **38 1/2"** past
the opening, not 37". The engine reads the table off the kit record
(`StructuralHardware.rough_opening_in_by_length_in`). `D-M-LAUN` closes at x=15'-4 1/2" and
`D-B-BATH` at y=16'-5 9/16". Both still fit their collinear runs, and `mep.pocket_occupancy`
guards the longer bands. The 1" fastener limit is unchanged (`POCKET_MAX_FASTENER`).

## Not modelled

- **RO height.** The framing solver heads every door at the leaf height (80"). Eclisse wants
  83 1/4" from **finished** floor; set the header to that, not to the drawing.
- **The frame goes in at finished-floor level**, not on the subfloor, so the leaf needs no
  trimming. Over `D-B-BATH`'s tile, shim the frame to the tile height.
- **The 2x6 part number.** EKQ is the 2x6 series and 36 x 80 is on the sheet, but no retail
  listing was found, so the BOM bills it by family (`POCKET-FRAME-ECLISSE-2X6`). Confirm the
  SKU with the dealer and order it early.
- The split studs are still drawn as wood `2-1x4`/`2-1x6` members for clearances, but the
  kit supplies them, so they no longer bill as lumber (`FramedMember.supplied_by`).

## Sources

- ECLISSE Single 2x4-2x6 technical sheet, 11/2022; Assembly 2x4 instructions, 11/2021
  (https://www.eclisse.us/en-us/support/product/single/).
- Home Depot listing EKC3680, $341.94, 2026-10-09; Ferguson EKQ3084 (2x6), $695, special order.
