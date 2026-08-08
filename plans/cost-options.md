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

### Balcony guard: Trex Signature → builder-grade aluminium
`railings:RAILING-EXT-ALUMINUM-FASCIA`, 38.3 LF — **$1,455 – $2,681 → ~$770 – $1,340 at
$20-35/LF. Saves ~$700 – $1,340.**

**Cost of the cut:** it is the guard you see from the sunken garden, and the powder-coat
finish is most of what you are buying.

### Sunken-garden arch: 16" curved concrete → metal railing on wood beam and columns
`wall_structure:SUNKEN_GARDEN_ARCH_16`, 3.31 cy — **$1,986 – $3,972**, plus whatever
`PORCH_RAILING_MASONRY` (3.15 cy, **$2,205 – $5,040**) goes with it. Together **$4,191 –
$9,012** against a framed-and-railed alternative in the low thousands.

Already in TODO.md as an idea; this is the number behind it. Curved formwork is the
expensive part — the yard of concrete is the cheap part.

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
