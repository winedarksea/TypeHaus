# Pocket frames — Eclisse steel cassettes

**House:** catlin
**Structure:** `D-M-LAUN` (2x4, `W-M-HS3`/`W-M-HS4`), `D-M-PANTRY` (2x4,
`W-M-PAN-S`), and `D-B-BATH` (2x6, `W-B-BA-E`/`W-B-HALL-W`),
all `DT-POCKET-INT-36` with `pocket_frame="eclisse"`.
**Written:** 2026-10-09.

## Why

The original laundry and basement-bath pockets were Johnson kits: the 1500PF and the 1560. Their steel split studs arrive loose,
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

The RO height is modelled too (2026-10-29, `plans/door-sizing.md`): the kit record carries
`rough_opening_head_over_leaf_in = 3.25`, and `resolve/door_sizing` heads a derived pocket
at 83 1/4" over the finished floor, plus that floor's build-up over the subfloor.
`D-M-PANTRY`, `D-M-LAUN` and (since 2026-10-29) `D-B-BATH` frame to it.

## What the head needs (2026-10-29)

Read from the 2x6 assembly instructions (11/2021) and the 11/2022 tech sheet: the kit carries
its own steel **pocket header (d)**, and the **top beam with track (e)** clicks into it and is
screwed to it (#8 x 3/8"). The assembled cassette is then fixed into the surrounding framing,
square and plumb, at the RO (step 9; screws not supplied). So the track hangs from the kit's
own header and bears on no wood. The wood head only has to give a straight, flat underside at
the RO height and sound wood for the fixings. Neither document asks for a bearing header or
says anything against a notch in the wood above. A notch off the top of a nonbearing head is
therefore harmless to the kit, provided its underside stays whole.

`D-B-BATH` therefore takes R602.7.4's flat 2x6 in `W-B-BA-E` (nonbearing, owner), and
`DU-B-ERV-R-GYM` rose 1/2" to clear it rather than notch it. `DU-B-ERV-R-PLAY` clears too.

The track nailer is a property of the kit (2026-10-29, owner: "per kit, drop for Eclisse"):
`StructuralHardware.pocket_track_nailer`, `False` on both Eclisse records, so none of the
three heads carries the generic flat 2x6 a Johnson-style kit screws its track into. That
lowered each head by 1 1/2": `D-B-BATH`'s flat head now tops out at 84 7/8" (was 86 3/8"),
which leaves `DU-B-ERV-R-GYM`'s envelope (86 1/2") 1 5/8" over it rather than 1/8". The
duct was not lowered back.

## Pantry — 2026-10-20

The refrigerator stands in front of about 23 inches of the old western 30-inch bypass
opening even when closed. The replacement 36 x 80 EKC3680 parks west and exposes the
usable east approach. The pantry and stock SEKTION cabinets retain their positions.

The entire RO is x=218 3/4..293 1/4 inches, with the nominal doorway at
257 1/4..293 1/4 and the pocket allocation at 218 3/4..257 1/4. It exactly spans the
perpendicular stud faces. `Door.frame_end_supports` explicitly connects the low end to
`W-M-C5B` and high end to `W-M-PAN-E`. The west junction gets full-height LSL backing in
place of its finish ladder rungs; the east return reuses its solid corner studs. Neither
end gets a separate jamb pack inside the cassette. Support validation fails closed.

Set the frame at intended finished-floor level and the RO head at 83 1/4 inches above
that level. Keep every drywall fastener over the cassette at 1 inch maximum. Anchor
through the cassette's specified fixing points into the perpendicular framing; no
cabinet, pipe, device box, shelf cleat, or added blocking may enter the cassette.

The light moves to the actual west wall, in the 8-inch strip ahead of the shelves.
Pantry and undercabinet controls share a two-gang installation on the east return at
46 inches, with manual pantry control. The two shelf bays and structural gable remain;
western storage is reached sideways from the east opening.

## Not modelled

- **The frame goes in at finished-floor level**, not on the subfloor, so the leaf needs no
  trimming. Over `D-B-BATH`'s tile, shim the frame to the tile height.
- **The 2x6 part number.** EKQ is the 2x6 series and 36 x 80 is on the sheet, but no retail
  listing was found, so the BOM bills it by family (`POCKET-FRAME-ECLISSE-2X6`). Confirm the
  SKU with the dealer and order it early.
- The split studs are still drawn as wood `2-1x4`/`2-1x6` members for clearances, but the
  kit supplies them, so they no longer bill as lumber (`FramedMember.supplied_by`).

## Sources

- ECLISSE Single 2x4-2x6 technical sheet, 11/2022; Assembly 2x4 instructions, 11/2021;
  Assembly 2x6 instructions, 11/2021, steps 5 and 9
  (https://www.eclisse.us/en-us/support/product/single/).
- Home Depot listing EKC3680, $341.94, 2026-10-09; Ferguson EKQ3084 (2x6), $695, special order.
