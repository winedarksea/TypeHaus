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
- **The tree moved on 2026-08-18** and every row above the concrete one is still measured
  against the old baseline. `concrete:slab` was pricing the suspended main-floor deck at the
  slab-on-grade rate; giving it its own key took the construction total from
  $274,206 – $562,712 to **$307,330 – $627,774**. That is a correction to what the house
  already costs, not a change to the house — no geometry moved.
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

### Basement ceiling: 9" suspended concrete deck → 11-7/8" I-joists at 16" o.c.
`concrete:slab:CATLIN_DECK_9_INT`, 34.26 cy / 1,233 SF, plus the main floor's finish —
**point estimate ~$21,300 saved, likely $16,100 – $27,700.**

Researched 2026-08-18. The largest single downgrade on this list by a factor of four, and
the only one that changes the structural system rather than a product selection.

| | concrete deck | I-joist floor |
|---|---|---|
| structure, all-in installed | $31,862 – $60,298 (~$26 – $49/SF) | $13,045 – $25,819 ($10.58 – $20.94/SF) |
| main-floor finish, 996 SF | sealer $996 – $2,989 | LVP $3,487 – $9,963 |
| **total** | **$32,858 – $63,287** | **$16,532 – $35,782** |
| point estimate | $46,381 ($36/SF deck, $2 sealer) | $25,089 ($15.50/SF system, $6 LVP) |

**Why the concrete number is so much larger than the estimate used to say.** Until today
`concrete:slab` priced this deck at $175 – $280/cy — the slab-on-grade rate, which is
ready-mix plus placement and nothing else. SL-M-DECK is not poured on the ground. It is
cast 9'-0" in the air and carries formwork, ~10' shoring on a one-month rental minimum
(ACI 347 keeps the shores until strength is verified), 2.0 – 2.7 tons of reinforcing, a
boom pump, a polish-ready trowel finish, a small-job/commercial-sub mobilization premium,
and a structural engineer's stamp. The old rate worked out to $4.86 – $7.78/SF for a
suspended structural deck against a published range of $20 – $40 and $25 – $50/SF. It was
low by 3-5x. The joist side needs none of that: the layout comes free with the EWP package
from the supplier, and there is no formwork, no shoring, no cure and no crane.

**The three bearing lines already exist.** `W-B-CN` / `W-B-CS` / `W-B-CS2` at x=18' plus the
east and west foundation walls are what the concrete deck bears on now, so the joists bear
on the same lines at the same 18' clear span the second and attic floors already run. This
is a like-for-like swap of FS-SECOND onto the basement, not a new structural scheme.

**Spec note, and it matters.** At 11-7/8" and 16" o.c. over 18'-0" clear, a **TJI 110 fails
outright** — 17'-8" max, short of the span even at code's L/360. **TJI 210 is the minimum
that works** (19'-3" at L/480). Spec the **230** anyway: it is ~$650 more over this deck and
buys real margin on a floor with finished rooms below. Do not let a supplier value-engineer
this to a 110.

**Two things that are NOT extra cost, and are commonly over-budgeted:**
- *Fire protection.* IRC/MN R501.3 wants a 1/2" gypsum membrane under I-joists. The 5/8"
  basement ceiling in the build-up above already exceeds it by a thickness step. No Flak
  Jacket, no intumescent coating, **$0**.
- *Bridging.* Weyerhaeuser: "TJI joist floor framing does not require bridging or mid-span
  blocking." Web stiffeners are not triggered at this span either. **$0.**

**What the range means.** The two ends are like-for-like — both options lean, then both
options rich. The full envelope is −$3,100 (the swap costs slightly *more*) to $46,900, but
the losing end needs the concrete to land at $25.68/SF *and* the joist floor to take union
labor, TJI-brand stock, sound batts and resilient channel all at once. The concrete low end
is the shakier of the two: most residential concrete subs will not bid a suspended deck at
all, and a commercial sub's job minimum is in the $25k – $50k range, so $32,660 may simply
not be obtainable. Treat the downside as unlikely and the upside as real.

**Sensitivity — polish, not sealer.** The table prices the concrete floor as a penetrating
densifier/sealer on the trowel finish ($1 – $3/SF), which is what `floor_finishes`
`sealed-concrete` actually is. If the intent was ever a genuinely *polished* floor, that is
a separate specialty contract at $4 – $8/SF for a Level 1-2 finish on a job this small, and
the saving grows by a further **$3,000 – $5,000**.

**Not priced, and a real further upside:** the deck is 112.5 psf of dead load before live
load. Losing it may let the foundation walls and footings shed reinforcement. Nobody has
asked the engineer, so it is not in the number.

**Cost of the cut** — this is the row with the most non-dollar consequence on the list:
- **Acoustics.** A 9" slab between the basement and the main floor is a level of impact and
  airborne isolation a wood floor does not reach. The $0 – $2,950 of batts and resilient
  channel at the high end of the joist column narrows the gap and does not close it.
- **Thermal mass.** 34 cy of concrete inside the thermal envelope, under the south glazing
  the whole facade is composed around. Deleting it changes how the house rides a sunny
  January day, and no line in prices.toml sees that.
- **Basement head height.** 9'-0" floor-to-floor less a 9" deck is 8'-3" clear today. Less
  11-7/8" of joist, 3/4" of subfloor and 5/8" of ceiling it is **7'-10 3/4"** — 5 1/4" gone.
  Still well over R305.1's minimum, and the duct soffits that a joist bay would make
  unnecessary are deliberately *not* credited here, so the real loss under the ducts is
  smaller than this. But the general ceiling does drop.
- **The in-slab radiant embed.** `FH-M-DINING` (232 LF) and `FH-M-BATH2` (37 LF) carry
  `embed=in_slab(0.5)`. There is no slab to embed in; both become mat-under-LVP and have to
  be re-authored. Roughly a wash in dollars.
- **The sauna liner extent comes off.** `assemblies.py` already anticipates this in prose:
  `_SAUNA_CEILING_EXTENT` bounds the liner at WALL_TOP − 1'-6" and says "if the basement
  ever goes to a joist ceiling running the full width, the liner would run the wall's whole
  height and this extent should come back off."

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
