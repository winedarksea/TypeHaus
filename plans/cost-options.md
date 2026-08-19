# Cost options — priced upgrades and downgrades

Started 2026-08-08. A running list of swaps we could make **if the number comes in tight**,
each with the line it actually moves in `houses/catlin/prices.toml`, so a decision is a
decision about dollars rather than about taste.

Rules for this file:

- Every row cites the estimate line it changes and the delta at both ends of the range.
  A swap with no number in it does not belong here yet — it belongs in TODO.md's
  "Potential cost cutting" list until someone prices it.
- **Nothing here is decided.** The plan as authored is the plan. This is the menu.
- Deltas are against the 2026-08-08 estimate (construction total $284,966 – $586,391).
  They are material-basis like the rest of prices.toml, so a real bid moves them.
- A swap that changes what the house *does* — not just what it costs — says so under
  **Cost of the cut**. Those are not free money.

## Downgrades (money back)

### Post bases: ABU66SS stainless → ABU66Z/RZ ZMAX galvanized
`hardware:ABU66SS`, 10 ea — **$1,500 – $2,300 → ~$550. Saves ~$950 – $1,750.**

Confirmed 2026-08-08 as genuinely stainless because the posts are exposed outdoors, and
kept for now. ZMAX is the standard exterior answer and is fine in most exposed locations;
stainless is what you buy for splash zones, coastal air, and pressure-treated contact you
expect to stay wet.

**Cost of the cut:** service life at the one detail nobody re-does without jacking the
structure. This is the wrong $1,000 to save unless everything else has already been cut.

### Exterior guards: Trex Signature → builder-grade aluminium
`railings:RAILING-EXT-ALUMINUM-FASCIA`, 74.6 LF — **$2,835 – $5,222 → ~$1,492 – $2,611 at
$20-35/LF. Saves ~$1,343 – $2,611.**

Twice the run it was written against: since 2026-08-18 this line carries both the balcony
guard (38.3 LF) and RL-SG-PORCH (36.3 LF), which replaced the porch's masonry parapet. They
are the same product and would be downgraded together, or the two levels stop matching.

**Cost of the cut:** these are the guards you see from the sunken garden, from both levels
at once now, and the powder-coat finish is most of what you are buying.

### Basement brick veneer: delete
`wall_structure:BASEMENT_BRICK_VENEER`, 1.37 cy — **$1,233 – $2,603.**

**Cost of the cut:** the one masonry note on the basement wall.

### Stair treads: red oak → carpet on all three flights
`framing:deck 11x1.5` + `tapered tread` + `deck 44.625x1.5` — **$2,668 – $5,544 → roughly
$1,200 – $2,800. Saves ~$1,400 – $2,700.**

The basement flight (ST-B2M) is already carpet by decision. Extending that to ST-M2S and
ST-S2A is the cheapest finish change in the house per dollar.

**Cost of the cut:** oak treads are a main-stair item you look at every day.

### System 3: Gree Sapphire → Vireo/Livo single-zone
`placeables:EQ-T-GREE-SAPPHIRE-9` + `-OD` — **$2,600 – $3,450 → ~$1,600 – $2,200. Saves
~$1,000 – $1,250.**

**Cost of the cut:** real, and structural. The Sapphire is on this circuit *because* its
true VFD inverter soft-starts, which is what lets it run off the battery — a hard-starting
compressor is what a battery inverter cannot carry (see plan/electrical.py). Swapping it
means giving up backup heat on that zone, or resizing the inverter. Do not treat this as a
like-for-like $1,000.

## Taken

### Sunken-garden arch → column, beams and a metal railing — **done 2026-08-18**
Measured against the tree immediately before the change, not estimated:
**$282,561 – $580,402 → $277,166 – $569,145. Saved $5,395 – $11,257.**

| line | before | after |
|---|---|---|
| `wall_structure` | $47,822 – $94,192 | $43,630 – $85,180 (**−$4,191 – −$9,012**) |
| `envelope_layers` | $56,568 – $116,051 | $55,497 – $113,843 (**−$1,070 – −$2,208**) |
| `footing_bedding` | $4,435 – $8,387 | $3,670 – $6,944 (**−$764 – −$1,443**) |
| `concrete` | $19,974 – $32,346 | $19,233 – $31,181 (**−$741 – −$1,166**) |
| `railings` | $3,125 – $6,551 | $4,505 – $9,092 (**+$1,379 – +$2,541**) |
| `hardware` | $8,606 – $15,454 | $8,598 – $15,485 (−$8 – +$31) |

The `wall_structure` line is exactly the $4,191 – $9,012 this row was written against —
`SUNKEN_GARDEN_ARCH_16` (3.31 cy) and `PORCH_RAILING_MASONRY` (3.15 cy) both deleted. The
rest was not in the original estimate and is why the real saving is a third larger again:
`FT-SG-ARCH` and its 42" aggregate bed went with the wall it carried, and the parapet took
its brick/CMU/stucco face area out of `envelope_layers`.

What was bought back: `RL-SG-PORCH`, 36.3 LF of the same fascia-mount guard as the balcony,
which is the whole `railings` increase; `PT-SG-FCOL` (0.53 cy) and its footing;
`BM-SG-FRW`/`FRE`; and about 17 LF of extra 6x6, because five of the six balcony pillars now
start at a concrete wall top or the decking rather than 42" up on masonry.

Curved formwork was the expensive part, as this row predicted — the yard of concrete was
always the cheap part.

## Upgrades (money out)

### Oak flooring in the LVP rooms
`floor_finishes:lvp` 1,272 SF at **$2,544 – $5,724** → oak at the `oak` rate is
**$5,088 – $10,176. Costs ~$2,500 – $4,500.**

Rooms: living, study, second-floor hall, and the two upstairs baths (the baths are the
reason this is not an obvious swap — oak in a bathroom is a maintenance decision).

## Not yet priced

Ideas from TODO.md's cost-cutting list that still need a number before they can move here:

- Remove the attic level, switch to truss + blown-in insulation. Touches framing,
  envelope_layers, floor_finishes, stairs and the ST-S2A guard at once; needs a variant,
  not an arithmetic estimate. `haus variants compare` is the tool.
- Standing seam → architectural asphalt. `envelope_layers:standing-seam` is 6,327 SF over
  two rows at **$15,817 – $37,961**, the single largest material line in the house, so
  this is the biggest lever on the list — and the one most likely to change the building.
